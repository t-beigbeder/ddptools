import argparse
import logging
import os
import sys

import grpc

from sfegrpc import estore_pb2_grpc, estore_pb2
from . import estoredbc


logger = logging.getLogger("sfe_init_db")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host")
    parser.add_argument("-p", "--port")
    args = parser.parse_args()
    host = args.host if args.host else "localhost"
    port = args.port if args.port else "8080"
    logging.basicConfig(
        format="%(asctime)s %(name)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stderr,
    )
    logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))
    drop = True if os.getenv("ESTORE_DROP_DB", "0").lower() not in ("", "0", "false") else False
    logger.info(f"main: calling CreateRequest on {host}:{port} drop {drop}")
    with grpc.insecure_channel(f"{host}:{port}") as channel:
        stub = estore_pb2_grpc.EstoreStub(channel)
        stub.Create(
            estore_pb2.CreateRequest(exist_ok=True, drop=drop, ddl=estoredbc.BASIC_DDL)
        )
    logger.info("main: exiting")


if __name__ == "__main__":
    main()
