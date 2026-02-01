import argparse
from concurrent import futures
import logging
import os
import sys
import tempfile
import threading
import time

from ddpbasics import gllk
import grpc

from sfegrpc import estore_pb2_grpc, ope_pb2_grpc, stfl_pb2_grpc

from . import estore_server, estoredb, ope_server, s3sqix, stfl_server


logger = logging.getLogger("sfe_svr")
VERSION = "0.13-future"


class Server:
    def __init__(self, server: grpc.Server) -> None:
        self.server = server

    def shutdown(self, delay: float) -> None:
        def _batch():
            logger.info(f"shutdown: sleeping {delay}")
            time.sleep(delay)
            self.server.stop(None)

        logger.info(f"shutdown: start thread waiting {delay}")
        t = threading.Thread(target=_batch, daemon=True)
        t.start()


def serve(
    host="localhost", port="8080", db_service=None, ixf_service=None, ixe_service=None
):
    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10), options=(("grpc.so_reuseport", 0),)
    )
    estore_pb2_grpc.add_EstoreServicer_to_server(
        estore_server.Estore(db_service, ixf_service, ixe_service, logger), server
    )
    stfl_pb2_grpc.add_StateServicer_to_server(stfl_server.State(logger), server)
    stfl_pb2_grpc.add_FlowServicer_to_server(stfl_server.Flow(logger), server)
    ope_pb2_grpc.add_OpeServicer_to_server(
        ope_server.Ope(VERSION, Server(server), logger), server
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
    logger.setLevel(os.getenv("LOG_LEVEL", "INFO"))

    logger.info(f"main: listen {host}:{port} DB {db_server} {db_name}")
    db_service = estoredb.PgService(db_server, db_name)
    td = tempfile.TemporaryDirectory(delete=False)
    ixf_service = s3sqix.S3SqixFileService(bucket, td.name, db_name, args.s3_profile)
    ixe_service = s3sqix.S3SqixEntryService(bucket, args.s3_profile)
    gllk.initialize()
    serve(
        host,
        port,
        db_service=db_service,
        ixf_service=ixf_service,
        ixe_service=ixe_service,
    )


if __name__ == "__main__":
    main()
