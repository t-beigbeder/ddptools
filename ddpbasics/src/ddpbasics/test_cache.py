from typing import Generator
import pytest

from . import cache


# Use cases
# open bz2 url as decompressed bytes stream
# open s3 object as bytes stream (todo in ddpestores)


@pytest.fixture
def get_ifs(tmp_path):
    def _gif(if_name):
        ifn = tmp_path / if_name
        with open(ifn, "w") as if_:
            if_.write(f"{if_name}\n")
        return str(ifn)

    return [_gif("i" + n) for n in ["1", "2", "3", "4", "5"]]


def lazy_open(fp: str) -> Generator[bytes]:
    with open(fp, "rb") as fd:
        for bs in fd:
            yield bs


def test_get_cache_path_for():
    assert cache.get_cache_path_for("that/name", "this_category").endswith(
        "/otvl/data/this_category/867/183db61a257cb6bd228ac2eb092f101e41ec6c4216921b18a07ea62556848"
    )


def test_lazy_open(get_ifs) -> None:
    bs = bytes()
    for ln in lazy_open(get_ifs[0]):
        bs += ln
    assert ln == "i1\n".encode()
