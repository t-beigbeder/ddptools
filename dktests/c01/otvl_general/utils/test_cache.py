import datetime

import pytest

from . import cache


@pytest.fixture
def get_ifs(tmp_path):
    def _gif(if_name):
        ifn = tmp_path / if_name
        with open(ifn, "w") as if_:
            if_.write(f"{if_name}\n")
        return str(ifn)

    return [_gif("i" + n) for n in ["1", "2", "3", "4", "5"]]


def test_get_cache_path_for():
    assert cache.get_cache_path_for("that/name", "this_category").endswith(
        "/otvl/data/this_category/867/183db61a257cb6bd228ac2eb092f101e41ec6c4216921b18a07ea62556848"
    )


def test_cache_basic_text(get_ifs):
    for el in cache.stream_cache("i1", open(get_ifs[0]), suffix=".txt"):
        assert el == "i1\n"


def test_cache_path_basic(get_ifs):
    cf = cache.stream_cache_path("i1", open(get_ifs[0]), suffix=".txt")
    with open(cf, "r") as f:
        for el in f:
            assert el == "i1\n"


def test_cache_basic_binary_first(get_ifs):
    for el in cache.stream_cache(
        "i2", open(get_ifs[1], mode="rb"), mode="rb", suffix=".bin"
    ):
        assert el == bytes("i2\n", "utf-8")


def test_cache_basic_binary_twice(get_ifs):
    for el in cache.stream_cache(
        "i2", open(get_ifs[1], mode="rb"), mode="rb", suffix=".two"
    ):
        assert el == bytes("i2\n", "utf-8")


def test_cache_text_sh_ok(get_ifs):
    cat = str(datetime.datetime.now().timestamp())
    hashes = {"sha256": "", "sha1": "33612ead0bcdafe66c732254350cb599f3d90395"}
    for el in cache.stream_cache(
        "i3", open(get_ifs[2]), suffix=".txt", hashes=hashes, category=cat
    ):
        assert el == "i3\n"
    assert (
        hashes["sha256"]
        == "b6c609d2929873be3a0051ba81f8a28c99ba8aef0e75bd874dcd639b5e81abef"
    )
    assert hashes["sha1"] == "33612ead0bcdafe66c732254350cb599f3d90395"


def test_cache_text_sh_err(get_ifs):
    cat = str(datetime.datetime.now().timestamp())
    hashes = {"sha256": "", "sha1": "z9e1db1ee5c12caf17797b34dd4809622d393fd66"}
    with pytest.raises(cache.HashError):
        _ = cache.stream_cache(
            "i4", open(get_ifs[3]), suffix=".txt", hashes=hashes, category=cat
        )


def test_cache_binary_sh_ok(get_ifs):
    cat = str(datetime.datetime.now().timestamp())
    hashes = {"sha256": "", "sha1": "efe1acd057539c9aaf949b76581501011baa9845"}
    for el in cache.stream_cache(
        "i5", open(get_ifs[4]), suffix=".bin", hashes=hashes, category=cat
    ):
        assert el == "i5\n"
    assert (
        hashes["sha256"]
        == "fd1d893c838fedfdfb981e09d6defb74927f2113de14d032ae8c725b37143288"
    )
    assert hashes["sha1"] == "efe1acd057539c9aaf949b76581501011baa9845"


def test_cache_text_file(get_ifs):
    cat = str(datetime.datetime.now().timestamp())
    for el in cache.file_cache("i1", get_ifs[0], suffix=".txt", category=cat):
        assert el == "i1\n"


def test_cache_path_text_file(get_ifs):
    cat = str(datetime.datetime.now().timestamp())
    cf = cache.file_cache_path("i1", get_ifs[0], suffix=".txt", category=cat)
    with open(cf, "r") as f:
        for el in f:
            assert el == "i1\n"


def test_cache_binary_file(get_ifs):
    cat = str(datetime.datetime.now().timestamp())
    for el in cache.file_cache(
        "i2", get_ifs[1], mode="rb", suffix=".bin", category=cat
    ):
        assert el == bytes("i2\n", "utf-8")


def test_cache_path_binary_file(get_ifs):
    cat = str(datetime.datetime.now().timestamp())
    cf = cache.file_cache_path("i1", get_ifs[0], mode="rb", suffix=".bin", category=cat)
    with open(cf, "rb") as f:
        for el in f:
            assert el == bytes("i1\n", "utf-8")


def test_get_cache_or_stream_text(get_ifs):
    def gsfn():
        return open(get_ifs[0], mode="r")

    def gsfnerr():
        raise Exception("yes")

    cat = str(datetime.datetime.now().timestamp())
    with cache.get_cache_or_stream(get_ifs[0], gsfn, cat) as f:
        for el in f:
            assert el == "i1\n"
    with cache.get_cache_or_stream(get_ifs[0], gsfnerr, cat) as f:
        for el in f:
            assert el == "i1\n"


def test_get_cache_or_stream_bin(get_ifs):
    def gsfn():
        return open(get_ifs[0], mode="rb")

    def gsfnerr():
        raise Exception("yes")

    cat = str(datetime.datetime.now().timestamp())
    hashes = {"sha256": "", "sha1": "ceae43b0f8d97d8360ef9bb4e23b93b632a8ec3e"}
    with cache.get_cache_or_stream(get_ifs[0], gsfn, cat, "rb", hashes=hashes) as f:
        for el in f:
            assert el == bytes("i1\n", "utf-8")
            assert (
                hashes["sha256"]
                == "e319bc242f9f5b2231a65ea66c2d4e11bbd66ccd0127f30ac22fae994b55ea06"
            )
            assert hashes["sha1"] == "ceae43b0f8d97d8360ef9bb4e23b93b632a8ec3e"
    with cache.get_cache_or_stream(get_ifs[0], gsfnerr, cat, "rb") as f:
        for el in f:
            assert el == bytes("i1\n", "utf-8")
