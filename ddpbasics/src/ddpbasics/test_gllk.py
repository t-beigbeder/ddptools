from .gllk import GlDict, initialize, GlQueue
import pytest


def test_gldict() -> None:
    initialize()
    GlDict().put("k", "v")
    assert GlDict().get("k") == "v"
    assert GlDict().exists("k")
    GlDict().delete("k")
    assert not GlDict().exists("k")
    with pytest.raises(KeyError):
        _ = GlDict().get("k")


def test_glqueue() -> None:
    initialize()
    q = GlQueue()
    q.create("a", 10, 10)
    assert q.exists("a")
    q.put("a", "b".encode())
    q.put("a", "c".encode())
    dq = q.get("a")
    assert dq and dq.decode() == "b"
    dq = q.get("a")
    assert dq and dq.decode() == "c"
    q.join("a")
    q.delete("a")
    assert not q.exists("a")
    q.create("a", 10, 10)
    q.shutdown("a", True)
