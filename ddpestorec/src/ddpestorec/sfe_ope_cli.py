import argparse
import logging
import sys

import grpc

from sfegrpc import ope_pb2_grpc, ope_pb2
from ddpestorec import main


logger = logging.getLogger("sfe_ope_cli")


def run(host: str, port: str, ready: bool, shutdown: str | None, version: bool) -> None:
    with grpc.insecure_channel(f"{host}:{port}") as channel:
        stub = ope_pb2_grpc.OpeStub(channel)
        if ready:
            r_resp = stub.Ready(ope_pb2.Empty())
            logger.info(f"main: Ready {r_resp.value}")
        elif shutdown:
            s_resp = stub.Shutdown(ope_pb2.Value(value=shutdown))
            logger.info(f"main: Shutdown {s_resp.value}")
        elif version:
            v_resp = stub.Version(ope_pb2.Empty())
            logger.info(f"main: Version {v_resp.value}")


def _parser(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--ready", action=argparse.BooleanOptionalAction)
    parser.add_argument("--shutdown")
    parser.add_argument("--version", action=argparse.BooleanOptionalAction)


def _doer(
    _: logging.Logger, host: str, port: str, args: argparse.Namespace
) -> int:
    run(host, port, args.ready, args.shutdown, args.version)
    return 0


if __name__ == "__main__":
    status = main.main(logger, _parser, _doer)
    sys.exit(status)
