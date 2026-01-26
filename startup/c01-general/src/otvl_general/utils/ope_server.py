import logging

from otvl_general.utils import ope_pb2
from otvl_general.utils import ope_pb2_grpc
from otvl_general.cmd import sfe_svr


logger = logging.getLogger("ope-server")


class Ope(ope_pb2_grpc.OpeServicer):
    def __init__(
        self,
        version: str,
        server: sfe_svr.Server | None = None,
        logger_: logging.Logger | None = None,
    ) -> None:
        global logger
        if logger_ is not None:
            logger = logger_
        self.version = version
        self.server = server

    def Ready(self, request, context):
        logger.info("Ope.Ready")
        return ope_pb2.Bool(value=True)

    def Version(self, request, context):
        logger.info("Ope.Version")
        return ope_pb2.Value(value=self.version)

    def Shutdown(self, request, context):
        try:
            fv = float(request.value)
        except ValueError:
            fv = 10
        logger.info(f"Ope.Shutdown {request.value}, sleeping {fv}")
        if self.server:
            self.server.shutdown(fv)
        return ope_pb2.Bool(value=True)
