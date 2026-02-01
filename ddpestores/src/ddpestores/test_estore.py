from concurrent import futures
import socket
import threading
from typing import Generator
import os

import grpc
import grpc._channel
import pytest

from . import estore_server, stfl_server
from sfegrpc import estore_pb2
from sfegrpc import estore_pb2_grpc
from sfegrpc import stfl_pb2_grpc

from . import estoredb
from . import s3sqix
from ddpbasics import sqix
from ddpbasics import gllk


gllk.initialize()


@pytest.fixture
def free_port():
    sock = socket.socket()
    sock.bind(("", 0))
    return sock.getsockname()[1]


@pytest.fixture
def server_port_estore(free_port):

    def _wait_for_server():
        server.wait_for_termination()

    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10), options=(("grpc.so_reuseport", 0),)
    )
    estore = estore_server.Estore()
    estore_pb2_grpc.add_EstoreServicer_to_server(estore, server)
    state = stfl_server.State(None)
    stfl_pb2_grpc.add_StateServicer_to_server(state, server)
    server.add_insecure_port(f"localhost:{free_port}")
    server.start()

    t = threading.Thread(target=_wait_for_server, daemon=True)
    t.start()
    yield server, free_port, estore
    server.stop(None)
    t.join()


@pytest.fixture
def grpc_stub(server_port_estore):
    server, port, estore = server_port_estore
    with grpc.insecure_channel(f"localhost:{port}") as channel:
        stub = estore_pb2_grpc.EstoreStub(channel)
        yield dict(server=server, estore=estore, stub=stub)


@pytest.fixture
def estore_session(grpc_stub) -> Generator:
    stub = grpc_stub["stub"]
    uuid_: estore_pb2.UUID = stub.StartSession(estore_pb2.Empty())
    grpc_stub["uuid"] = uuid_.uuid
    yield grpc_stub
    resp = stub.EndSession(estore_pb2.UUID(uuid=uuid_.uuid))
    _ = resp


@pytest.fixture
def basic_entities(estore_session):
    def _gen():
        uuid_sent = False
        for i in range(10):
            entity = estore_pb2.Entity(content=f"entity #{i}".encode())
            if not uuid_sent:
                entity.session_uuid = estore_session["uuid"]
                entity.category = "cat1"
                uuid_sent = True
            yield entity

    estore_session["gen"] = _gen
    yield estore_session


def test_basic(basic_entities):
    stub = basic_entities["stub"]
    rec_resp = stub.RecordEntities(basic_entities["gen"]())
    _ = rec_resp


def test_bad_uuid(estore_session):
    def _gen():
        uuid_sent = False
        for i in range(2):
            entity = estore_pb2.Entity(content=f"entity #{i}".encode())
            if not uuid_sent:
                entity.session_uuid = "bad_uuid"
                entity.category = "cat1"
                uuid_sent = True
            yield entity

    stub = estore_session["stub"]
    with pytest.raises(grpc._channel._InactiveRpcError) as ei:
        rec_resp = stub.RecordEntities(_gen())
        _ = rec_resp
    assert ei.value.code() == grpc.StatusCode.INVALID_ARGUMENT
    assert "bad_uuid" in ei.value.details()


@pytest.fixture
def db_service():
    svc = estoredb.PgService("t-db-pgs", "estore_pytest")
    svc.create_db(True, True, ddl=estoredb.BASIC_DDL)
    svc.create_category("default")
    svc.create_category("cat1", "for additional tests")
    yield svc


@pytest.fixture
def ixf_service(tmp_path):
    td = str(tmp_path)
    ixf_service = s3sqix.S3SqixFileService(
        "otvl-tests", td, "estore_pytest", "otvl-tests"
    )
    yield ixf_service


@pytest.fixture
def ixe_service():
    ixe_service = s3sqix.S3SqixEntryService("otvl-tests", "otvl-tests")
    yield ixe_service


def test_service_base(estore_session, db_service, ixf_service, ixe_service):
    estore = estore_session["estore"]
    estore.set_db_service(db_service)
    estore.set_ixf_service(ixf_service)
    estore.set_ixe_service(ixe_service)


def test_service_db(estore_session, db_service, ixf_service):
    estore = estore_session["estore"]
    estore.set_db_service(db_service)
    estore.set_ixf_service(ixf_service)
    stub = estore_session["stub"]
    assert stub.Exists(estore_pb2.Empty())
    assert stub.Drop(estore_pb2.DropRequest(miss_ok=False))
    assert stub.Create(
        estore_pb2.CreateRequest(exist_ok=False, drop=False, ddl=estoredb.BASIC_DDL)
    )
    rsp = stub.CreateCategory(
        estore_pb2.CreateCategoryRequest(
            label="cat_test_service_db", content="just to test"
        )
    )
    _ = rsp


@pytest.mark.parametrize(
    "entities_number, with_keys_only, keys_num",
    [
        (10, False, 0),
        (100, False, 0),
        (100, True, 0),
        (100, True, 50),
        (2 * sqix.SqixFileBase.MAX_ENTRIES, False, 0),
    ],
)
def test_service_e2e_write(
    grpc_stub,
    db_service,
    ixf_service,
    ixe_service,
    entities_number,
    with_keys_only,
    keys_num,
):

    def _bcont(i):
        return (f"this is a small message for the entity #{i}").encode()

    def _get_entity(uuid_: str, category: str):
        uuid_sent = False
        for i in range(entities_number):
            entity = estore_pb2.Entity(
                key=str(i),
                content=f"entity #{i}".encode(),
                additional_content=_bcont(i),
            )
            if not uuid_sent:
                entity.session_uuid = uuid_
                entity.category = category
                uuid_sent = True
            yield entity

    if entities_number > 100 and os.getenv("PYTEST_FAST"):
        pytest.skip(
            f"entities_number {entities_number} > 100 and env PYTEST_FAST {os.getenv('PYTEST_FAST')}"
        )
    estore = grpc_stub["estore"]
    estore.set_db_service(db_service)
    estore.set_ixf_service(ixf_service)
    estore.set_ixe_service(ixe_service)
    stub = grpc_stub["stub"]
    ss_resp = stub.StartSession(estore_pb2.Empty())
    rec_resp = stub.RecordEntities(_get_entity(ss_resp.uuid, "cat1"))
    _ = rec_resp
    cls_resp = stub.EndSession(estore_pb2.UUID(uuid=ss_resp.uuid))
    _ = cls_resp
    db = estoredb.PgService("t-db-pgs", "estore_pytest")
    ent = db.read_entity("cat1", "0")
    for ent in db.read_entities("cat1"):
        _ = ent
    if entities_number < 100:
        for i in range(entities_number):
            re_resp = stub.ReadEntity(
                estore_pb2.ReadEntityRequest(
                    category="cat1", key=str(i), with_additional_content=True
                )
            )
            _ = re_resp
    else:
        if keys_num > 0:
            keys = [str(k) for k in range(keys_num)]
        else:
            keys = None
        count = 0
        for e in stub.ReadEntities(
            estore_pb2.ReadEntitiesRequest(
                category="cat1",
                with_additional_content=not with_keys_only,
                with_keys_only=with_keys_only,
                keys=keys,
            )
        ):
            _ = e
            count += 1
        assert (keys_num > 0 and count == keys_num) or (
            keys_num == 0 and count == entities_number
        )


@pytest.mark.parametrize(
    "entities_number, with_keys_only",
    [
        (10, False),
        (100, False),
        (100, True),
        (2 * sqix.SqixFileBase.MAX_ENTRIES, False),
    ],
)
def test_service_e2e_read_all(
    grpc_stub,
    db_service,
    ixf_service,
    ixe_service,
    entities_number,
    with_keys_only,
):

    def _bcont(i):
        return (f"this is a small message for the entity #{i}").encode()

    def _get_entity(uuid_: str, category: str):
        uuid_sent = False
        for i in range(entities_number):
            entity = estore_pb2.Entity(
                key=str(i),
                content=f"entity #{i}".encode(),
                additional_content=_bcont(i),
            )
            if not uuid_sent:
                entity.session_uuid = uuid_
                entity.category = category
                uuid_sent = True
            yield entity

    if entities_number > 100 and os.getenv("PYTEST_FAST"):
        pytest.skip(
            f"entities_number {entities_number} > 100 and env PYTEST_FAST {os.getenv('PYTEST_FAST')}"
        )
    estore = grpc_stub["estore"]
    estore.set_db_service(db_service)
    estore.set_ixf_service(ixf_service)
    estore.set_ixe_service(ixe_service)
    stub = grpc_stub["stub"]
    ss_resp = stub.StartSession(estore_pb2.Empty())
    rec_resp = stub.RecordEntities(_get_entity(ss_resp.uuid, "cat1"))
    _ = rec_resp
    cls_resp = stub.EndSession(estore_pb2.UUID(uuid=ss_resp.uuid))
    _ = cls_resp

    srs = stub.StartReadSession(
        estore_pb2.ReadSessionRequest(
            category="cat1",
            with_additional_content=not with_keys_only,
            with_keys_only=with_keys_only,
        )
    )
    count = 0
    for e in stub.ReadOnSession(estore_pb2.UUID(uuid=srs.uuid)):
        _ = e
        count += 1
    assert count == entities_number


@pytest.mark.parametrize(
    "entities_number, with_keys_only",
    [
        (10, False),
        (100, False),
        (100, True),
        (2 * sqix.SqixFileBase.MAX_ENTRIES, False),
    ],
)
def test_service_e2e_read_on_mt(
    server_port_estore,
    db_service,
    ixf_service,
    ixe_service,
    entities_number,
    with_keys_only,
):

    def _bcont(i):
        return (f"this is a small message for the entity #{i}").encode()

    def _get_entity(uuid_: str, category: str):
        uuid_sent = False
        for i in range(entities_number):
            entity = estore_pb2.Entity(
                key=str(i),
                content=f"entity #{i}".encode(),
                additional_content=_bcont(i),
            )
            if not uuid_sent:
                entity.session_uuid = uuid_
                entity.category = category
                uuid_sent = True
            yield entity

    if entities_number > 100 and os.getenv("PYTEST_FAST"):
        pytest.skip(
            f"entities_number {entities_number} > 100 and env PYTEST_FAST {os.getenv('PYTEST_FAST')}"
        )
    server, port, estore = server_port_estore
    estore.set_db_service(db_service)
    estore.set_ixf_service(ixf_service)
    estore.set_ixe_service(ixe_service)
    with grpc.insecure_channel(f"localhost:{port}") as channel:
        stub = estore_pb2_grpc.EstoreStub(channel)
        ss_resp = stub.StartSession(estore_pb2.Empty())
        rec_resp = stub.RecordEntities(_get_entity(ss_resp.uuid, "cat1"))
        _ = rec_resp
        cls_resp = stub.EndSession(estore_pb2.UUID(uuid=ss_resp.uuid))
        _ = cls_resp

        srs = stub.StartReadSession(
            estore_pb2.ReadSessionRequest(
                category="cat1",
                with_additional_content=not with_keys_only,
                with_keys_only=with_keys_only,
            )
        )

    counts = {0: 0, 1: 0}
    entsl = {0: [], 1: []}

    def _cli_run(num: int):
        with grpc.insecure_channel(f"localhost:{port}") as channel:
            stub = estore_pb2_grpc.EstoreStub(channel)
            for e in stub.ReadOnSession(estore_pb2.UUID(uuid=srs.uuid)):
                counts[num] += 1
                if entities_number < 100:
                    entsl[num].append(e)

    bts = [None, None]
    for i in range(2):
        bts[i] = threading.Thread(target=_cli_run, args=(i,), daemon=True)
        bts[i].start()
    for i in range(2):
        bts[i].join()

    with grpc.insecure_channel(f"localhost:{port}") as channel:
        stub = estore_pb2_grpc.EstoreStub(channel)
        stub.EndReadSession(estore_pb2.UUID(uuid=srs.uuid))
    assert counts[0] + counts[1] == entities_number
