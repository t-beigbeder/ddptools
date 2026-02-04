from concurrent import futures
import logging
import socket
import threading

import grpc
import pytest

from otvl_general.utils import ope_pb2
from otvl_general.utils import ope_pb2_grpc
from otvl_general.utils import ope_server


@pytest.fixture
def free_port():
    sock = socket.socket()
    sock.bind(("", 0))
    return sock.getsockname()[1]


@pytest.fixture
def server_port_ope(free_port):

    def _wait_for_server():
        server.wait_for_termination()

    server = grpc.server(
        futures.ThreadPoolExecutor(max_workers=10), options=(("grpc.so_reuseport", 0),)
    )
    ope = ope_server.Ope("pytest-version")
    ope_pb2_grpc.add_OpeServicer_to_server(ope, server)
    server.add_insecure_port(f"localhost:{free_port}")
    server.start()

    t = threading.Thread(target=_wait_for_server, daemon=True)
    t.start()
    yield server, free_port, ope
    server.stop(None)
    t.join()


@pytest.fixture
def grpc_stub(server_port_ope):
    server, port, ope = server_port_ope
    with grpc.insecure_channel(f"localhost:{port}") as channel:
        op_stub = ope_pb2_grpc.OpeStub(channel)
        yield dict(
            server=server,
            port=free_port,
            ope=ope,
            op_stub=op_stub,
        )


def test_basic(grpc_stub):
    stub = grpc_stub["op_stub"]
    r_resp = stub.Ready(ope_pb2.Empty())
    assert r_resp.value
    v_resp = stub.Version(ope_pb2.Empty())
    logging.getLogger("pytest").info({v_resp.value})
    assert v_resp.value == "pytest-version"
    s_resp = stub.Shutdown(ope_pb2.Value(value="15"))
    assert s_resp.value
