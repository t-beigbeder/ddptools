import pytest

from otvl_general.utils.files import cat, read_creds_file, read_pass_file


@pytest.fixture
def get_ifs(tmp_path):
    def _gif(if_name):
        ifn = tmp_path / if_name
        with open(ifn, "w") as if_:
            if_.write(f"{if_name}\n")
        return str(ifn)
    return [_gif("i" + n) for n in ["1", "2"]]


def test_cat_two(tmp_path, get_ifs):
    i1 = get_ifs[0]
    i2 = get_ifs[1]
    co = tmp_path / "of"
    cat(str(co), i1, i2)
    with open(co) as cf:
        cc = cf.read()
        assert cc == "i1\ni2\n"


def test_cat_zero(tmp_path):
    co = tmp_path / "of"
    cat(str(co))
    with open(co) as cf:
        cc = cf.read()
        assert cc == ""


def _pf(pfp, eol=True):
    sf = '\n' if eol else ''
    with open(pfp, "w") as of:
        of.write(f"password{sf}")
    return str(pfp)


def _ef(pfp):
    with open(pfp, "w"):
        pass
    return str(pfp)


def test_read_pass_file_eol(tmp_path):
    assert read_pass_file(_pf(tmp_path / "eol")) == "password"


def test_read_pass_file_no_eol(tmp_path):
    assert read_pass_file(_pf(tmp_path / "no_eol", False)) == "password"


def test_read_pass_file_no_line(tmp_path):
    assert read_pass_file(_ef(tmp_path / "no_line")) is None


def test_read_pass_file_ko(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_pass_file(str(tmp_path / "ko"))


def _cf(pfp, eol=True):
    sf = '\n' if eol else ''
    with open(pfp, "w") as of:
        of.write(f"user:password{sf}")
    return str(pfp)


def test_read_creds_file_eol(tmp_path):
    assert read_creds_file(_cf(tmp_path / "eol")) == ("user", "password")


def test_read_creds_file_no_eol(tmp_path):
    assert read_creds_file(_cf(tmp_path / "no_eol", False)) == ("user", "password")


def test_read_creds_file_no_line(tmp_path):
    assert read_creds_file(_ef(tmp_path / "no_line")) is None


def test_read_creds_file_no_creds(tmp_path):
    with pytest.raises(ValueError):
        read_creds_file(_pf(tmp_path / "no_eol", False))


def test_read_creds_file_ko(tmp_path):
    with pytest.raises(FileNotFoundError):
        read_creds_file(str(tmp_path / "ko"))
