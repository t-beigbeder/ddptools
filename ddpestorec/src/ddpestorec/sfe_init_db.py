import argparse
import logging
import sys

import grpc

from sfegrpc import estore_pb2_grpc, estore_pb2
from . import main


logger = logging.getLogger("sfe_init_db")


def run(host: str, port: str, drop: bool):
    logger.info(f"run: calling CreateRequest on {host}:{port} drop {drop}")
    with grpc.insecure_channel(f"{host}:{port}") as channel:
        stub = estore_pb2_grpc.EstoreStub(channel)
        stub.Create(
            estore_pb2.CreateRequest(exist_ok=True, drop=drop, ddl="")
        )
    logger.info("run: exiting")


def _parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--drop")


def _doer(
    _: logging.Logger, host: str, port: str, args: argparse.Namespace
) -> int:
    run(host, port, main.is_drop_set(args))
    return 0


if __name__ == "__main__":
    status = main.main(logger, _parser, _doer)
    sys.exit(status)
