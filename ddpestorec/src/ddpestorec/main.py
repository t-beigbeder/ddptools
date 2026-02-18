import argparse
import logging
import os
import sys
from typing import Callable


logger = logging.getLogger("estorec_main")


def is_drop_set(args: argparse.Namespace) -> bool:
    if os.getenv("ESTORE_DROP_DB") is None:
        drop = args.drop
    else:
        drop = os.getenv("ESTORE_DROP_DB", "0")
    return drop.lower() not in ("", "0", "false", "none") if drop else False


def parser_for_test(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--status", default="0")


def doer_for_test(
    logr: logging.Logger, host: str, port: str, args: argparse.Namespace
) -> int:
    logr.info(f"doer_for_test: host {host} port {port} args {args}")
    logr.info("doer_for_test: done")
    return int(args.status)


def main(
    logr: logging.Logger,
    arg_parser: Callable[[argparse.ArgumentParser], None],
    do_main: Callable[[logging.Logger, str, str, argparse.Namespace], int],
) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host")
    parser.add_argument("-p", "--port")
    arg_parser(parser)
    args = parser.parse_args()
    host = args.host if args.host else "localhost"
    port = args.port if args.port else "8080"
    logging.basicConfig(
        format="%(asctime)s %(name)s %(levelname)-8s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stderr,
    )
    logr.setLevel(os.getenv("LOG_LEVEL", "INFO"))
    return do_main(logr, host, port, args)


if __name__ == "__main__":
    status = main(logger, parser_for_test, doer_for_test)
    sys.exit(status)
