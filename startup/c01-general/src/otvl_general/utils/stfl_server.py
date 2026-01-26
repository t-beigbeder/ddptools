import logging

from otvl_general.utils import stfl_pb2
from otvl_general.utils import stfl_pb2_grpc
from otvl_general.utils import gllk


logger = logging.getLogger("stfl-server")


class State(stfl_pb2_grpc.StateServicer):
    def __init__(self, logger_: logging.Logger | None = None) -> None:
        global logger
        if logger_ is not None:
            logger = logger_

    def Put(self, request, context):
        logger.info(f"State.Put: {request.key} {len(request.value)}")
        gllk.GlDict().put(request.key, request.value)
        return stfl_pb2.Bool(value=True)

    def Exists(self, request, context):
        logger.info(f"State.Exists: {request.key}")
        return stfl_pb2.Bool(value=gllk.GlDict().exists(request.key))

    def Get(self, request, context):
        logger.info(f"State.Get: {request.key}")
        return stfl_pb2.Value(value=gllk.GlDict().get(request.key))

    def Delete(self, request, context):
        logger.info(f"State.Delete: {request.key}")
        gllk.GlDict().delete(request.key)
        return stfl_pb2.Bool(value=True)


class Flow(stfl_pb2_grpc.FlowServicer):
    def __init__(self, logger_: logging.Logger | None = None) -> None:
        global logger
        if logger_ is not None:
            logger = logger_

    def Create(self, request, context):
        logger.info(f"Flow.Create: {request.topic} {request.size}")
        gllk.GlQueue().create(request.topic, request.size, request.max_value_size)
        return stfl_pb2.Bool(value=True)

    def Delete(self, request, context):
        logger.info(f"Flow.Delete: {request.topic}")
        gllk.GlQueue().delete(request.topic)
        return stfl_pb2.Bool(value=True)

    def Exists(self, request, context):
        logger.info(f"Flow.Exists: {request.topic}")
        return stfl_pb2.Bool(value=gllk.GlQueue().exists(request.topic))

    def Shutdown(self, request, context):
        logger.info(f"Flow.Shutdown: {request.topic} {request.immediate}")
        gllk.GlQueue().shutdown(request.topic, request.immediate)
        return stfl_pb2.Bool(value=True)

    def Put(self, request, context):
        logger.info(f"Flow.Put: {request.topic} {len(request.value)}")
        gllk.GlQueue().put(request.topic, request.value)
        return stfl_pb2.Bool(value=True)

    def IsEmpty(self, request, context):
        logger.info(f"Flow.IsEmpty: {request.topic}")
        return stfl_pb2.Bool(value=gllk.GlQueue().is_empty(request.topic))

    def Get(self, request, context):
        logger.info(f"Flow.Get: {request.topic}")
        von = gllk.GlQueue().get(request.topic)
        is_none = von is None
        if von is None:
            von = bytes()
        logger.debug(f"Flow.Get: {request.topic} {is_none} {von}")
        return stfl_pb2.ValueOrNone(value=von, is_none=is_none)

    def Join(self, request, context):
        logger.info(f"Flow.Join: {request.topic}")
        gllk.GlQueue().join(request.topic)
        return stfl_pb2.Bool(value=True)
