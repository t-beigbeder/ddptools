import threading

import pytest

from .gllk import GlDict, GlQueue, initialize


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


def test_glnamedlock() -> None:
    def _task():
        for c in range(10):
            ln = f"test_glnamedlock:{c % 3}"
            nl = None
            try:
                nl = d.named_lock_get(ln)
            finally:
                if nl:
                    d.named_lock_delete(ln)

    initialize()
    d = GlDict()
    ts = []
    for i in range(10):
        t = threading.Thread(target=_task)
        ts.append(t)
        t.start()
    for t in ts:
        t.join()
