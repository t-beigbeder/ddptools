from hashlib import sha256
from random import randbytes
from typing import Generator

import pytest

from . import cache, gllk


# Use cases
# open bz2 url as decompressed bytes stream
# open s3 object as bytes stream (todo in ddpestores)


@pytest.fixture
def get_ifs(tmp_path):
    def _gif(if_name):
        ifn = tmp_path / if_name
        with open(ifn, "wb") as if_:
            if_.write(f"{if_name}\n".encode())
        return str(ifn)

    return [_gif("i" + n) for n in ["1", "2", "3", "4", "5"]]


@pytest.fixture
def get_xlf(tmp_path):
    sh = sha256()
    ifn = tmp_path / "xlf"
    with open(ifn, "wb") as if_:
        for _ in range(10):
            bs = randbytes(1024 * 1024)
            sh.update(bs)
            if_.write(bs)
    return str(ifn), sh.digest().hex()


def _local_streamer(tn: str, fp: str) -> Generator[bytes]:
    ref = f"{tn}:{fp}"
    d = gllk.GlDict()
    if not d.exists(ref):
        d.put(ref, 1)
    else:
        d.put(ref, d.get(ref) + 1)
    with open(fp, "rb") as fd:
        while True:
            bs = fd.read(128 * 1024)
            if not len(bs):
                return
            yield bs


def test_get_cache_path_for():
    assert cache.get_cache_path_for("that/name", "this_category").endswith(
        "/otvl/data/this_category/867/183db61a257cb6bd228ac2eb092f101e41ec6c4216921b18a07ea62556848"
    )


def test_files_cache(tmp_path, monkeypatch, get_ifs) -> None:
    d = gllk.GlDict()
    xdg_cad = str(tmp_path / "xdg_cad")
    monkeypatch.setenv("XDG_CACHE_HOME", xdg_cad)
    for i, if_ in enumerate(get_ifs):
        streamer = _local_streamer("cnt0", if_)
        bs = bytearray()
        for ck in cache.cache_streamer(if_, "cat0", "", streamer):
            bs.extend(ck)
        assert bs.decode() == f"i{i + 1}\n"
    for i, if_ in enumerate(get_ifs):
        assert d.get(f"cnt0:{if_}") == 1
    for i, if_ in enumerate(get_ifs):
        streamer = _local_streamer("cnt0", if_)
        bs = bytearray()
        for ck in cache.cache_streamer(if_, "cat0", "", streamer):
            bs.extend(ck)
        assert bs.decode() == f"i{i + 1}\n"
    for i, if_ in enumerate(get_ifs):
        assert d.get(f"cnt0:{if_}") == 1


def test_large_file_cache(tmp_path, monkeypatch, get_xlf) -> None:
    d = gllk.GlDict()
    xdg_cad = str(tmp_path / "xdg_cad")
    monkeypatch.setenv("XDG_CACHE_HOME", xdg_cad)
    streamer = _local_streamer("cnt1", get_xlf[0])
    h = sha256()
    for bs in cache.cache_streamer("xlf", "cat1", "", streamer):
        h.update(bs)
    assert h.digest().hex() == get_xlf[1]
    assert d.get(f"cnt1:{get_xlf[0]}") == 1

    h = sha256()
    for bs in cache.cache_streamer("xlf", "cat1", "", streamer):
        h.update(bs)
    assert d.get(f"cnt1:{get_xlf[0]}") == 1
    assert h.digest().hex() == get_xlf[1]
