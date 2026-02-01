import argparse
from concurrent import futures
import logging
import queue
import sys
import tempfile
import threading
from typing import Generator
import uuid

import grpc

from sfegrpc import estore_pb2
from sfegrpc import estore_pb2_grpc
from . import estoredb
from . import s3sqix


logger = logging.getLogger("server")


class _Entity:
    # already selected per category, key is key provided by Entity message in RecordEntities
    def __init__(
        self,
        key: str,
        content: bytes | None,
        ct_ref: str | None,
        additional_content: bytes | None = None,
    ) -> None:
        self.key = key
        self.content = content
        self.ct_ref = ct_ref
        self.additional_content = additional_content


class _EntsPack:
    # entities must be selected per category in case we are using an ixf_service
    # db_name/category/sqix
    def __init__(self, category: str, ixf_file: s3sqix.S3SqixFileCreation) -> None:
        self.category = category  # for information only
        self.entities: list[_Entity] = []
        self.ixf_file = ixf_file

    def __str__(self) -> str:
        return f"_EntsPack {self.category} len {len(self.entities)} bucket {self.ixf_file.bucket} path {self.ixf_file.object_path}"


class _EstoreManager:
    def __init__(
        self,
        db_service: estoredb.PgService | None = None,
        ixf_service: s3sqix.S3SqixFileService | None = None,
    ) -> None:
        self.db_service = db_service
        self.ixf_service = ixf_service
        self.entities_lock = threading.Lock()
        self.ents_packs: dict[str, _EntsPack] = {}
        self.eq: queue.Queue = queue.Queue(3)
        self.is_initialized = False
        self.bt: threading.Thread | None = None

    def set_db_service(self, db_service) -> None:
        self.db_service = db_service

    def set_ixf_service(self, ixf_service) -> None:
        self.ixf_service = ixf_service

    def _do_flush(self, ents_pack: _EntsPack) -> None:
        self.eq.put(ents_pack)

    def _persist(self, ents_pack: _EntsPack) -> None:
        try:
            if self.db_service is None or self.ixf_service is None:
                return
            ents_pack.ixf_file.close()
            values = [(v.key, v.content, v.ct_ref) for v in ents_pack.entities]
            self.db_service.create_entities(ents_pack.category, values)
        except Exception as e:
            logger.error(
                f'_EstoreManager._persist: error pack {ents_pack}: error "{e}"'
            )

    def _batch(self) -> None:
        logger.info("_EstoreManager._batch: started")
        while True:
            ents_pack: _EntsPack | None = self.eq.get()
            self.eq.task_done()
            if ents_pack is None:
                logger.info("_EstoreManager._batch: processing last pack done")
                return
            logger.info(f"_EstoreManager._batch: processing pack {ents_pack}")
            self._persist(ents_pack)

    def add_entity(
        self,
        category: str,
        key: str,
        content: bytes | None,
        additional_content: bytes | None,
    ) -> None:
        if self.db_service is None or self.ixf_service is None:
            return
        with self.entities_lock:
            ac = additional_content if additional_content is not None else bytes()
            if category not in self.ents_packs:
                ixf_file = self.ixf_service.new_s3sqix_file(category)
                self.ents_packs[category] = _EntsPack(category, ixf_file)
            ents_pack = self.ents_packs[category]
            if not ents_pack.ixf_file.has_room(len(ac)):
                self._do_flush(ents_pack)
                ixf_file = self.ixf_service.new_s3sqix_file(category)
                ents_pack = _EntsPack(category, ixf_file)
                self.ents_packs[category] = ents_pack
            ixf_file = ents_pack.ixf_file
            ix = ixf_file.add_entry(ac)
            ct_ref = f"{ixf_file.bucket}/{ixf_file.object_path}/{ix}"
            ents_pack.entities.append(_Entity(key, content, ct_ref))

    def flush(self, category: str) -> None:
        if (
            self.db_service is None
            or self.ixf_service is None
            or category not in self.ents_packs
        ):
            return
        with self.entities_lock:
            self._do_flush(self.ents_packs[category])
            del self.ents_packs[category]

    def initialize(self) -> None:
        if self.is_initialized:
            return
        self.is_initialized = True
        self.bt = threading.Thread(target=self._batch, daemon=True)
        self.bt.start()
        logger.info("_EstoreManager.initialize: batch started")

    def finalize(self) -> None:
        if self.bt is None:
            return
        logger.info("_EstoreManager.finalize: batch stopping")
        self.eq.put(None)
        self.bt.join()
        self.is_initialized = False
        self.bt = None
        logger.info("_EstoreManager.finalize: batch stopped")


class _Session:
    # key is uuid provided by the StartSession service
    def __init__(self) -> None:
        self.entities_count = 0
        self.categories: set[str] = set()


class _EstoreAdmin:
    def __init__(
        self,
        db_service: estoredb.PgService | None = None,
        ixf_service: s3sqix.S3SqixFileService | None = None,
    ) -> None:
        self.db_service = db_service
        self.ixf_service = ixf_service

    def set_db_service(self, db_service) -> None:
        self.db_service = db_service

    def set_ixf_service(self, ixf_service) -> None:
        self.ixf_service = ixf_service

    def exists(self) -> bool:
        if self.db_service is None or self.ixf_service is None:
            return False
        return self.db_service.exists()

    def drop_db(self, miss_ok=False) -> bool:
        if self.db_service is None or self.ixf_service is None:
            return False
        return self.db_service.drop_db(miss_ok)

    def create_db(self, exist_ok=False, drop_db=False, ddl="") -> bool:
        if self.db_service is None or self.ixf_service is None:
            return False
        return self.db_service.create_db(exist_ok, drop_db, ddl)

    def create_category(self, label="", content=None) -> None:
        if self.db_service is None or self.ixf_service is None:
            return
        self.db_service.create_category(label, content)


class _EstoreReader:
    def __init__(
        self,
        db_service: estoredb.PgService | None = None,
        ixe_service: s3sqix.S3SqixEntryService | None = None,
    ) -> None:
        self.db_service = db_service
        self.ixe_service = ixe_service

    def set_db_service(self, db_service) -> None:
        self.db_service = db_service

    def set_ixe_service(self, ixe_service) -> None:
        self.ixe_service = ixe_service

    def _read_ct_ref(self, ct_ref: str, category: str, with_ac) -> bytes | None:
        if self.ixe_service is None or not with_ac:
            return None
        # otvl-tests/estore_main_test/mw-articles/478/2389
        fields = ct_ref.split("/")
        if len(fields) < 3:
            raise Exception(f"invalid ct_ref in DB: {ct_ref}")
        return self.ixe_service.read_s3sqix_entry(
            "/".join(fields[1:-1]), category, int(fields[-1])
        )

    def read(self, category: str, key: str, with_ac: bool) -> _Entity | None:
        if self.db_service is None or self.ixe_service is None:
            return None
        content, ct_ref = self.db_service.read_entity(category, key)
        return _Entity(
            key, content, ct_ref, self._read_ct_ref(str(ct_ref), category, with_ac)
        )

    def read_all(
        self, category: str, with_ac: bool, with_keys_only: bool, keys: list[str] | None
    ) -> Generator[_Entity]:
        if self.db_service is None or self.ixe_service is None:
            return
        for key, content, ct_ref in self.db_service.read_entities(
            category, with_keys_only, keys
        ):
            yield _Entity(
                key, content, ct_ref, self._read_ct_ref(str(ct_ref), category, with_ac)
            )


class _EstoreReadSession:
    def __init__(
        self,
        category: str,
        with_ac: bool,
        with_keys_only: bool,
        es_reader: _EstoreReader,
    ) -> None:
        self.category = category
        self.with_ac = with_ac
        self.with_keys_only = with_keys_only
        self.es_reader = es_reader
        self.bt: threading.Thread | None = None
        self.eq: queue.Queue = queue.Queue(1024)

    def _batch(self) -> None:
        logger.info("_EstoreReadSession._batch: started")
        for e in self.es_reader.read_all(
            self.category, self.with_ac, self.with_keys_only, None
        ):
            self.eq.put(e)
        self.eq.shutdown()

    def initialize(self) -> None:
        if self.bt is not None:
            return
        self.bt = threading.Thread(target=self._batch, daemon=True)
        self.bt.start()
        logger.info("_EstoreReadSession.initialize: batch started")

    def read_on_session(self) -> Generator[_Entity]:
        while True:
            try:
                e = self.eq.get()
                self.eq.task_done()
                yield e
            except queue.ShutDown:
                return

    def finalize(self) -> None:
        if self.bt is None:
            return
        logger.info("_EstoreReadSession.finalize: batch stopping")
        self.eq.shutdown(immediate=True)
        self.bt.join()
        self.bt = None
        logger.info("_EstoreReadSession.finalize: batch stopped")


class Estore(estore_pb2_grpc.EstoreServicer):
    def __init__(
        self,
        db_service=None,
        ixf_service=None,
        ixe_service=None,
        logger_: logging.Logger | None = None,
    ) -> None:
        global logger
        if logger_ is not None:
            logger = logger_
        self.es_mgr = _EstoreManager(db_service, ixf_service)
        self.es_admin = _EstoreAdmin(db_service, ixf_service)
        self.es_reader = _EstoreReader(db_service, ixe_service)
        self.session_lock = threading.Lock()
        self.sessions: dict[str, _Session] = {}
        self.esr_sessions: dict[str, _EstoreReadSession] = {}

    def set_db_service(self, db_service) -> None:
        self.es_mgr.set_db_service(db_service)
        self.es_admin.set_db_service(db_service)
        self.es_reader.set_db_service(db_service)

    def set_ixf_service(self, ixf_service) -> None:
        self.es_mgr.set_ixf_service(ixf_service)
        self.es_admin.set_ixf_service(ixf_service)

    def set_ixe_service(self, ixe_service) -> None:
        self.es_reader.set_ixe_service(ixe_service)

    def Exists(self, request, context) -> estore_pb2.Bool:
        rsp = self.es_admin.exists()
        logger.info(f"exists: {rsp}")
        return estore_pb2.Bool(value=rsp)

    def Drop(self, request: estore_pb2.DropRequest, context) -> estore_pb2.Bool:
        rsp = self.es_admin.drop_db(request.miss_ok)
        logger.info(f"drop: {rsp}")
        return estore_pb2.Bool(value=rsp)

    def Create(self, request: estore_pb2.CreateRequest, context) -> estore_pb2.Bool:
        rsp = self.es_admin.create_db(request.exist_ok, request.drop, request.ddl)
        logger.info(f"create: {request.exist_ok}, {request.drop} -> {rsp}")
        return estore_pb2.Bool(value=rsp)

    def CreateCategory(
        self, request: estore_pb2.CreateCategoryRequest, context
    ) -> estore_pb2.Empty:
        self.es_admin.create_category(request.label, request.content)
        logger.info(f"create_category: {request.label} done")
        return estore_pb2.Empty()

    def _addSession(self, uuid_) -> None:
        with self.session_lock:
            self.sessions[uuid_] = _Session()
            self.es_mgr.initialize()

    def _add_entity(
        self,
        uuid_: str,
        category: str,
        key: str,
        content: bytes | None,
        additional_content: bytes | None,
    ) -> None:
        with self.session_lock:
            if uuid_ not in self.sessions:
                raise KeyError(uuid_)
            self.sessions[uuid_].entities_count += 1
            self.sessions[uuid_].categories.add(category)
        self.es_mgr.add_entity(category, key, content, additional_content)

    def _delSession(self, uuid_) -> None:
        flushed: set[str] = set()  # categories not owned by another session anymore
        with self.session_lock:
            for category in self.sessions[uuid_].categories:
                for other_uuid, session in self.sessions.items():
                    if other_uuid == uuid_:
                        continue
                    if category in session.categories:
                        break
                else:
                    flushed.add(category)
            for category in flushed:
                self.es_mgr.flush(category)
            del self.sessions[uuid_]
            if len(self.sessions) == 0:
                self.es_mgr.finalize()

    def StartSession(self, request, context) -> estore_pb2.UUID:
        uuid_ = str(uuid.uuid4())
        self._addSession(uuid_)
        logger.info(f"startSession: {uuid_}")
        return estore_pb2.UUID(uuid=uuid_)

    def RecordEntities(self, request_iterator, context) -> estore_pb2.Empty:
        uuid_ = None
        category = None
        logger.info("recordEntities: starting")
        for entity in request_iterator:
            err = None
            if uuid_ is None and entity.session_uuid == "":
                err = "uuid must be initially set"
            elif uuid_ is None and entity.session_uuid not in self.sessions:
                err = f"invalid session {entity.session_uuid}"
            elif uuid_ is not None and entity.category:
                err = f"invalid argument category {entity.category} after first message"
            if err is not None:
                logger.error(err)
                context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
                context.set_details(err)
                return estore_pb2.Empty()

            if uuid_ is None:
                uuid_ = entity.session_uuid
                category = entity.category
                logger.info(f"recordEntities: uuid {uuid_} category {category}")

            logger.debug(
                f"recordEntities: uuid {uuid_} category {category} key {entity.key}"
            )
            self._add_entity(
                uuid_,
                str(category),
                entity.key,
                entity.content,
                entity.additional_content,
            )

        logger.info(
            f"recordEntities: done (#{self.sessions[str(uuid_)].entities_count})"
        )
        return estore_pb2.Empty()

    def EndSession(self, request, context) -> estore_pb2.Empty:
        logger.info(f"endSession: {request.uuid}")
        self._delSession(request.uuid)
        return estore_pb2.Empty()

    def ReadEntity(self, request, context):
        ersp = self.es_reader.read(
            request.category, request.key, request.with_additional_content
        )
        lnct = len(ersp.content) if ersp.content else 0
        lnac = len(ersp.additional_content) if ersp.additional_content else 0
        logger.info(f"readEntity: {request.category} {request.key} -> {lnct} {lnac}")
        return estore_pb2.ReadEntityResponse(
            content=ersp.content,
            additional_content=ersp.additional_content,
            ct_ref=ersp.ct_ref,
        )

    def ReadEntities(self, request, context):
        logger.info(f"readEntities: {request.category} starting")
        count = 0
        for ent in self.es_reader.read_all(
            request.category,
            request.with_additional_content,
            request.with_keys_only,
            request.keys,
        ):
            count += 1
            yield estore_pb2.ReadEntityResponse(
                key=ent.key,
                content=ent.content,
                additional_content=ent.additional_content,
                ct_ref=ent.ct_ref,
            )
        logger.info(f"readEntities: {request.category} done ({count})")

    def StartReadSession(self, request, context) -> estore_pb2.UUID:
        uuid_ = str(uuid.uuid4())
        self.esr_sessions[uuid_] = _EstoreReadSession(
            request.category,
            request.with_additional_content,
            request.with_keys_only,
            self.es_reader,
        )
        logger.info(f"startReadSession: {uuid_}")
        self.esr_sessions[uuid_].initialize()
        return estore_pb2.UUID(uuid=uuid_)

    def ReadOnSession(self, request, context):
        logger.info(f"readOnSession: {request.uuid} starting")
        count = 0
        for ent in self.esr_sessions[request.uuid].read_on_session():
            count += 1
            yield estore_pb2.ReadEntityResponse(
                key=ent.key,
                content=ent.content,
                additional_content=ent.additional_content,
                ct_ref=ent.ct_ref,
            )
        logger.info(f"ReadOnSession: {request.uuid} done ({count})")

    def EndReadSession(self, request, context) -> estore_pb2.Empty:
        logger.info(f"endReadSession: {request.uuid}")
        self.esr_sessions[request.uuid].finalize()
        del self.esr_sessions[request.uuid]
        return estore_pb2.Empty()


def serve(
    host="localhost",
    port="8080",
    db_service=None,
    ixf_service=None,
    ixe_service=None,
):
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10), options=(("grpc.so_reuseport", 0),)
    )
    estore_pb2_grpc.add_EstoreServicer_to_server(
        Estore(db_service, ixf_service, ixe_service), server
    )
    server.add_insecure_port(f"{host}:{port}")
    logger.info(f"serve: starting server on {host}:{port}")
    server.start()
    server.wait_for_termination()
    logger.info(f"serve: stopped server on {host}:{port}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host")
    parser.add_argument("-p", "--port")
    parser.add_argument("--db-server", required=True)
    parser.add_argument("-d", "--db-name", required=True)
    parser.add_argument("--s3-profile")
    parser.add_argument("-b", "--bucket", required=True)
    args = parser.parse_args()
    host = args.host if args.host else "localhost"
    port = args.port if args.port else "8080"
    db_server = args.db_server
    db_name = args.db_name
    bucket = args.bucket

    logging.basicConfig(
        format="%(asctime)s %(name)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stderr,
    )
    logger.setLevel(logging.INFO)
    logger.info(f"main: listen {host}:{port} DB {db_server} {db_name}")
    db_service = estoredb.PgService(db_server, db_name)
    td = tempfile.TemporaryDirectory(delete=False)
    ixf_service = s3sqix.S3SqixFileService(bucket, td.name, db_name, args.s3_profile)
    ixe_service = s3sqix.S3SqixEntryService(bucket, args.s3_profile)
    serve(
        host,
        port,
        db_service=db_service,
        ixf_service=ixf_service,
        ixe_service=ixe_service,
    )


if __name__ == "__main__":
    main()
