import pytest

from .adapters import file_streamer, stream_reader
from .s3utils import delete, download, exists, upload


@pytest.fixture
def get_ifs(tmp_path):
    def _gif(if_name):
        ifn = tmp_path / if_name
        with open(ifn, "w") as if_:
            if "i1" in if_name:
                if_.write(f"{if_name}\n")
            else:
                for c in range(10000):
                    if_.write(f"{if_name}: count is {c}\n")
        return str(ifn)

    return [_gif("i" + n) for n in ["1", "2"]]


def test_object_up(get_ifs) -> None:
    delete("otvl-tests", "test_s3utils/test_object_up/i1", "otvl-tests")
    delete("otvl-tests", "test_s3utils/test_object_up/i2", "otvl-tests")
    assert not exists("otvl-tests", "test_s3utils/test_object_up/i1", "otvl-tests")

    i1 = get_ifs[0]
    upload(
        file_streamer(i1), "otvl-tests", "test_s3utils/test_object_up/i1", "otvl-tests"
    )
    assert exists("otvl-tests", "test_s3utils/test_object_up/i1", "otvl-tests")
    i2 = get_ifs[1]
    upload(
        file_streamer(i2), "otvl-tests", "test_s3utils/test_object_up/i2", "otvl-tests"
    )


def _read_all_by(rr, size) -> bytes:
    bs = bytes()
    while True:
        chunk = rr.read(size)
        if len(chunk) == 0:
            if size == 8192:
                pass
            return bs
        bs += chunk


def test_object_down(get_ifs) -> None:
    delete("otvl-tests", "test_s3utils/test_object_up/i1", "otvl-tests")
    delete("otvl-tests", "test_s3utils/test_object_up/i2", "otvl-tests")

    i1 = get_ifs[0]
    upload(
        file_streamer(i1), "otvl-tests", "test_s3utils/test_object_up/i1", "otvl-tests"
    )
    sr1a = stream_reader(
        download("otvl-tests", "test_s3utils/test_object_up/i1", "otvl-tests")
    )
    with open(i1, "rb") as fd:
        assert fd.read() == _read_all_by(sr1a, 8192)

    i2 = get_ifs[1]
    upload(
        file_streamer(i2), "otvl-tests", "test_s3utils/test_object_up/i2", "otvl-tests"
    )
    sr2a = stream_reader(
        download("otvl-tests", "test_s3utils/test_object_up/i2", "otvl-tests")
    )
    with open(i2, "rb") as fd:
        assert fd.read() == _read_all_by(sr2a, 8192)
