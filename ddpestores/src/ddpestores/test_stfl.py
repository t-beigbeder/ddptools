from concurrent import futures
import logging
import socket
import threading
import time

import grpc
import pytest

from sfegrpc import stfl_pb2
from sfegrpc import stfl_pb2_grpc
from . import stfl_server
from ddpbasics import gllk


gllk.initialize()


@pytest.fixture
def free_port():
    sock = socket.socket()
    sock.bind(("", 0))
    return sock.getsockname()[1]


@pytest.fixture
def server_port_stfl(free_port):

    def _wait_for_server():
        server.wait_for_termination()

    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10), options=(("grpc.so_reuseport", 0),)
    )
    state = stfl_server.State(None)
    stfl_pb2_grpc.add_StateServicer_to_server(state, server)
    flow = stfl_server.Flow(None)
    stfl_pb2_grpc.add_FlowServicer_to_server(flow, server)
    server.add_insecure_port(f"localhost:{free_port}")
    server.start()

    t = threading.Thread(target=_wait_for_server, daemon=True)
    t.start()
    yield server, free_port, state, flow
    server.stop(None)
    t.join()


@pytest.fixture
def grpc_stub(server_port_stfl):
    server, port, state, flow = server_port_stfl
    with grpc.insecure_channel(f"localhost:{port}") as channel:
        st_stub = stfl_pb2_grpc.StateStub(channel)
        fl_stub = stfl_pb2_grpc.FlowStub(channel)
        yield dict(
            server=server,
            port=free_port,
            state=state,
            st_stub=st_stub,
            flow=flow,
            fl_stub=fl_stub,
        )


def test_basic(grpc_stub):
    _TP = "the_topic"

    stub = grpc_stub["st_stub"]
    _ = stub.Put(stfl_pb2.KeyValue(key="k", value="v".encode()))
    ex_resp = stub.Exists(stfl_pb2.Key(key="k"))
    assert ex_resp.value
    v_resp = stub.Get(stfl_pb2.Key(key="k"))
    assert v_resp.value.decode() == "v"
    _ = stub.Delete(stfl_pb2.Key(key="k"))
    ex_resp = stub.Exists(stfl_pb2.Key(key="k"))
    assert not ex_resp.value

    stub = grpc_stub["fl_stub"]
    ex_resp = stub.Exists(stfl_pb2.Topic(topic=_TP))
    assert not ex_resp.value
    _ = stub.Create(stfl_pb2.TopicConfig(topic=_TP, size=10, max_value_size=10))
    ex_resp = stub.Exists(stfl_pb2.Topic(topic=_TP))
    assert ex_resp.value
    _ = stub.Put(stfl_pb2.TopicValue(topic=_TP, value="the_value".encode()))
    _ = stub.Put(stfl_pb2.TopicValue(topic=_TP, value="the_val2".encode()))
    vg1 = stub.Get(stfl_pb2.Topic(topic=_TP))
    vg2 = stub.Get(stfl_pb2.Topic(topic=_TP))
    assert vg1.value == "the_value".encode()
    assert vg2.value == "the_val2".encode()
    _ = stub.Shutdown(stfl_pb2.ShutdownRequest(topic=_TP, immediate=True))
    vge = stub.Get(stfl_pb2.Topic(topic=_TP))
    assert vge.is_none
    d_resp = stub.Delete(stfl_pb2.Topic(topic=_TP))
    assert d_resp.value


def test_queue_with_threads(grpc_stub):
    _TP = "the_topic"
    _DL = 0.250

    def _prod(stub):
        logger = logging.getLogger("_prod")
        time.sleep(_DL)
        for i in range(10):
            logger.debug("put")
            _ = stub.Put(stfl_pb2.TopicValue(topic=_TP, value=str(i).encode()))
        for i in range(10):
            logger.debug("put")
            _ = stub.Put(stfl_pb2.TopicValue(topic=_TP, value=str(i + 10).encode()))
        logger.debug("join")
        stub.Join(stfl_pb2.Topic(topic=_TP))
        time.sleep(_DL)
        logger.debug("shutdown")
        stub.Shutdown(stfl_pb2.ShutdownRequest(topic=_TP, immediate=True))

    def _cons(stub, ix):
        if ix == 0:
            logger = logging.getLogger("_cons#0")
            logger.debug("get")
            vg1 = stub.Get(stfl_pb2.Topic(topic=_TP))
            logger.debug(f"got {vg1.value}")
        elif ix == 1:
            logger = logging.getLogger("_cons#1")
            for i in range(9):
                logger.debug("get")
                vg2 = stub.Get(stfl_pb2.Topic(topic=_TP))
                logger.debug(f"got {vg2.value}")
        else:
            logger = logging.getLogger("_cons#2")
            for i in range(10):
                logger.debug("get")
                vg3 = stub.Get(stfl_pb2.Topic(topic=_TP))
                logger.debug(f"got {vg3.value}")
            logger.debug("get")
            vg3 = stub.Get(stfl_pb2.Topic(topic=_TP))
            logger.debug(f"got {vg3.is_none} {vg3.value}")

    stub = grpc_stub["fl_stub"]
    _ = stub.Create(stfl_pb2.TopicConfig(topic=_TP, size=100, max_value_size=10))

    tp = threading.Thread(target=_prod, daemon=True, args=(stub,))
    tp.start()
    tc1 = threading.Thread(target=_cons, daemon=True, args=(stub, 0))
    tc1.start()
    time.sleep(_DL)
    tc2 = threading.Thread(target=_cons, daemon=True, args=(stub, 1))
    tc2.start()
    time.sleep(_DL)
    tc3 = threading.Thread(target=_cons, daemon=True, args=(stub, 2))
    tc3.start()

    tp.join()
    _ = stub.Shutdown(stfl_pb2.ShutdownRequest(topic=_TP, immediate=True))
    _ = stub.Delete(stfl_pb2.Topic(topic=_TP))


def test_glqueue_concurrent_pc(grpc_stub) -> None:
    _TP = "test_glqueue_concurrent_pc"
    stub = grpc_stub["fl_stub"]

    def _cons(ix) -> None:
        logger = logging.getLogger(f"_cons#{ix}")
        while True:
            logger.info("get")
            val: stfl_pb2.ValueOrNone = stub.Get(stfl_pb2.Topic(topic=_TP))
            logger.info(f"got: {val}")
            if val.is_none:
                return

    def _prod():
        logger = logging.getLogger("_prod")
        for i in range(1000):
            val = f"val{i}"
            logger.info(f"put {val}")
            stub.Put(stfl_pb2.TopicValue(topic=_TP, value=val.encode()))
        stub.Shutdown(stfl_pb2.ShutdownRequest(topic=_TP, immediate=False))

    _ = stub.Create(stfl_pb2.TopicConfig(topic=_TP, size=4, max_value_size=10))

    tp = threading.Thread(target=_prod, daemon=True)
    tp.start()
    tcs = []
    for i in range(8):
        tcs.append(threading.Thread(target=_cons, daemon=True, args=(i,)))
        tcs[-1].start()
    tp.join()
    for i in range(8):
        tcs[i].join()


def test_glqueue_concurrent_cp(grpc_stub) -> None:
    _TP = "test_glqueue_concurrent_cp"
    stub = grpc_stub["fl_stub"]

    def _cons(ix) -> None:
        logger = logging.getLogger(f"_cons#{ix}")
        while True:
            logger.info("get")
            val: stfl_pb2.ValueOrNone = stub.Get(stfl_pb2.Topic(topic=_TP))
            logger.info(f"got: {val}")
            if val.is_none:
                return

    def _prod():
        logger = logging.getLogger("_prod")
        for i in range(1000):
            val = f"val{i}"
            logger.info(f"put {val}")
            stub.Put(stfl_pb2.TopicValue(topic=_TP, value=val.encode()))
        stub.Shutdown(stfl_pb2.ShutdownRequest(topic=_TP, immediate=False))

    _ = stub.Create(stfl_pb2.TopicConfig(topic=_TP, size=4, max_value_size=10))
    tcs = []
    for i in range(8):
        tcs.append(threading.Thread(target=_cons, daemon=True, args=(i,)))
        tcs[-1].start()

    tp = threading.Thread(target=_prod, daemon=True)
    tp.start()
    tp.join()

    for i in range(8):
        tcs[i].join()
