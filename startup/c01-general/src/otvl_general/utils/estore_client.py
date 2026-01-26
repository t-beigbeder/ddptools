import argparse
import logging
import queue
import sys
import threading

import grpc

from otvl_general.utils import estore_pb2, estoredb
from otvl_general.utils import estore_pb2_grpc


q: queue.Queue = queue.Queue(100)
logger = logging.getLogger("client")


def get_entity(uuid_: str, category: str):
    uuid_sent = False
    while True:
        entity: estore_pb2.Entity | None = q.get()
        q.task_done()
        if entity is None:
            logger.info("get_entity: no more entries, stopping")
            return
        if not uuid_sent:
            entity.session_uuid = uuid_
            entity.category = category
            uuid_sent = True
            logger.info(f"get_entity: {entity.session_uuid}")
        logger.debug(f"get_entity: {entity}")
        yield entity


def gen_entity():
    def bcont(i):
        return (f"this is a rather large message for the entity #{i}" * 400).encode()

    # background work to provide data in a queue
    for i in range(20000):
        entity = estore_pb2.Entity(
            key=str(i), content=f"entity #{i}".encode(), additional_content=bcont(i)
        )
        q.put(entity)
    q.put(None)


def run(host="localhost", port="8080", drop=True, category="not-defined") -> None:
    threading.Thread(target=gen_entity, daemon=True).start()
    with grpc.insecure_channel(f"{host}:{port}") as channel:
        stub = estore_pb2_grpc.EstoreStub(channel)
        stub.Create(
            estore_pb2.CreateRequest(exist_ok=True, drop=drop, ddl=estoredb.BASIC_DDL)
        )
        stub.CreateCategory(
            estore_pb2.CreateCategoryRequest(label=category, content="")
        )
        ss_resp: estore_pb2.UUID = stub.StartSession(estore_pb2.Empty())
        logger.info(f"startSession answered {ss_resp.uuid}")
        rec_resp = stub.RecordEntities(get_entity(ss_resp.uuid, category))
        logger.info(f"recordEntities {rec_resp}")
        cls_resp = stub.EndSession(estore_pb2.UUID(uuid=ss_resp.uuid))
        logger.info(f"endSession {cls_resp}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host")
    parser.add_argument("-p", "--port")
    parser.add_argument("--drop", action=argparse.BooleanOptionalAction)
    parser.add_argument("-c", "--category", default="cat-default")
    args = parser.parse_args()
    host = args.host if args.host else "localhost"
    port = args.port if args.port else "8080"
    logging.basicConfig(
        format="%(asctime)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stderr,
    )
    logger.setLevel(logging.INFO)
    run(host, port, args.drop, args.category)


if __name__ == "__main__":
    main()
