import pytest

from .adapters import file_streamer, stream_reader, url_streamer


@pytest.fixture
def get_ifs(tmp_path):
    def _gif(if_name):
        ifn = tmp_path / if_name
        with open(ifn, "w") as if_:
            if ifn == "i1":
                if_.write(f"{if_name}\n")
            else:
                for c in range(10000):
                    if_.write(f"{if_name}: count is {c}\n")
        return str(ifn)

    return [_gif("i" + n) for n in ["1", "2"]]


def _read_all_by(rr, size) -> bytes:
    bs = bytes()
    while True:
        chunk = rr.read(size)
        if len(chunk) == 0:
            return bs
        bs += chunk


def test_fs_sr(get_ifs) -> None:
    i1 = get_ifs[0]
    fs1a = file_streamer(i1)
    sr1a = stream_reader(fs1a)
    with open(i1, "rb") as fd:
        assert fd.read() == sr1a.read()
    fs1b = file_streamer(i1, 2)
    sr1b = stream_reader(fs1b)
    with open(i1, "rb") as fd:
        assert fd.read() == _read_all_by(sr1b, 2)
    i2 = get_ifs[1]
    fs2a = file_streamer(i2)
    sr2a = stream_reader(fs2a)
    with open(i2, "rb") as fd:
        assert fd.read() == sr2a.read()
    fs2b = file_streamer(i2, 64 * 1024)
    sr2b = stream_reader(fs2b)
    with open(i2, "rb") as fd:
        assert fd.read() == _read_all_by(sr2b, 8192)


def test_url_sr() -> None:
    _UT = "https://blog.otvl.org"
    us = url_streamer(_UT)
    sr = stream_reader(us)
    html = sr.read().decode()
    assert "<!DOCTYPE html>" in html and "<title>Blog</title>" in html and "</html>" in html
