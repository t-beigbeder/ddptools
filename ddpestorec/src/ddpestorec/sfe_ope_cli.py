import argparse
import logging
import os
import sys

import grpc

from sfegrpc import ope_pb2_grpc, ope_pb2


logger = logging.getLogger("sfe_ope_cli")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--host")
    parser.add_argument("-p", "--port")
    parser.add_argument("--ready", action=argparse.BooleanOptionalAction)
    parser.add_argument("--shutdown")
    parser.add_argument("--version", action=argparse.BooleanOptionalAction)
    args = parser.parse_args()
    host = args.host if args.host else "localhost"
    port = args.port if args.port else "8080"
    logging.basicConfig(
        format="%(asctime)s %(name)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stderr,
    )
    logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))
    with grpc.insecure_channel(f"{host}:{port}") as channel:
        stub = ope_pb2_grpc.OpeStub(channel)
        if args.ready:
            r_resp = stub.Ready(ope_pb2.Empty())
            logger.info(f"main: Ready {r_resp.value}")
        elif args.shutdown:
            s_resp = stub.Shutdown(ope_pb2.Value(value=args.shutdown))
            logger.info(f"main: Shutdown {s_resp.value}")
        elif args.version:
            v_resp = stub.Version(ope_pb2.Empty())
            logger.info(f"main: Version {v_resp.value}")


if __name__ == "__main__":
    main()
