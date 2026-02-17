import argparse
import logging
import os
import sys

import grpc

from sfegrpc import estore_pb2_grpc, estore_pb2
from . import main


logger = logging.getLogger("sfe_init_db")


def run(host: str, port: str, drop: bool, category: str):
    logger.info(f"main: calling CreateRequest on {host}:{port} drop {drop}")
    with grpc.insecure_channel(f"{host}:{port}") as channel:
        stub = estore_pb2_grpc.EstoreStub(channel)
        stub.Create(
            estore_pb2.CreateRequest(exist_ok=True, drop=drop, ddl="")
        )
    logger.info("main: exiting")


def _parser(parser: argparse.ArgumentParser) -> None:
    drop = True if os.getenv("ESTORE_DROP_DB", "0").lower() not in ("", "0", "false") else False


def _doer(
    _: logging.Logger, host: str, port: str, args: argparse.Namespace
) -> int:
    drop = True if os.getenv("ESTORE_DROP_DB", "0").lower() not in ("", "0", "false") else False
    run(host, port, drop, args.category)
    return 0


if __name__ == "__main__":
    status = main.main(logger, _parser, _doer)
    sys.exit(status)
