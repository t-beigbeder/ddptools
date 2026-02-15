import pytest

from .s3utils import delete


@pytest.fixture
def get_ifs(tmp_path):
    def _gif(if_name):
        ifn = tmp_path / if_name
        with open(ifn, "w") as if_:
            if_.write(f"{if_name}\n")
        return str(ifn)
    return [_gif("i" + n) for n in ["1", "2"]]


def test_object_up(get_ifs) -> None:
    i1 = get_ifs[0]
    with open(i1, "rb") as fd:
        while True:
            bs = fd.read(128 * 1024)
            if not len(bs):
                return
