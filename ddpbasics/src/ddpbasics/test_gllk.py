import logging
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


def test_glqueue_seq() -> None:
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


def test_glqueue_concurrent_pc() -> None:
    _T = "test_glqueue_concurrent"
    initialize()
    q = GlQueue()
    q.create(_T, 4, 10)
    assert q.exists(_T)

    def _cons(ix):
        logger = logging.getLogger(f"_cons#{ix}")
        while True:
            logger.info("get")
            val = q.get(_T)
            logger.info(f"got: {val}")
            if val is None:
                return

    def _prod():
        logger = logging.getLogger("_prod")
        for i in range(1000):
            val = f"val{i}"
            logger.info(f"put {val}")
            q.put(_T, f"{val}")
        q.shutdown(_T, False)

    tp = threading.Thread(target=_prod, daemon=True)
    tp.start()
    tcs = []
    for i in range(10):
        tcs.append(threading.Thread(target=_cons, daemon=True, args=(i,)))
        tcs[-1].start()
    tp.join()
    for i in range(10):
        tcs[i].join()


def test_glqueue_concurrent_cp() -> None:
    _T = "test_glqueue_concurrent_cp"
    initialize()
    q = GlQueue()
    q.create(_T, 4, 10)
    assert q.exists(_T)

    def _cons(ix):
        logger = logging.getLogger(f"_cons#{ix}")
        while True:
            logger.info("get")
            val = q.get(_T)
            logger.info(f"got: {val}")
            if val is None:
                return

    def _prod():
        logger = logging.getLogger("_prod")
        for i in range(1000):
            val = f"val{i}"
            logger.info(f"put {val}")
            q.put(_T, f"{val}")
        q.shutdown(_T, False)
    tcs = []
    for i in range(10):
        tcs.append(threading.Thread(target=_cons, daemon=True, args=(i,)))
        tcs[-1].start()

    tp = threading.Thread(target=_prod, daemon=True)
    tp.start()
    tp.join()

    for i in range(10):
        tcs[i].join()


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
