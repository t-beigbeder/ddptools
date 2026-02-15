import pytest

from .adapters import file_streamer, stream_reader, StreamReader


@pytest.fixture
def get_ifs(tmp_path):
    def _gif(if_name):
        ifn = tmp_path / if_name
        with open(ifn, "w") as if_:
            if_.write(f"{if_name}\n")
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
