import array

import pytest

from .sqix import (
    SqixFileConsumption,
    SqixFileCreation,
    SqixFileError,
    SqixFileMaxEntriesError,
    SqixFileMaxLenError,
)


def test_sqix_base(tmp_path):
    path = str(tmp_path / "sqix1")
    with SqixFileCreation(path) as sf:
        assert sf.add_entry("entry#1".encode()) == 0
        assert sf.len() == 7
        assert sf.add_entry("2nd entry".encode()) == 1
        assert sf.len() == 16
    with SqixFileConsumption(path) as sf:
        assert sf.read_entry(0) == "entry#1".encode()
        assert sf.read_entry(1) == "2nd entry".encode()


def test_sqix_no_cm(tmp_path):
    path = str(tmp_path / "test_sqix_no_cm")
    sf = SqixFileCreation(path)
    assert sf.add_entry("entry#1".encode()) == 0
    assert sf.len() == 7
    assert sf.add_entry("2nd entry".encode()) == 1
    assert sf.len() == 16
    sf.close()
    sf = SqixFileConsumption(path)
    assert sf.read_entry(0) == "entry#1".encode()
    assert sf.read_entry(1) == "2nd entry".encode()
    sf.close()


def test_sqix_max_num(tmp_path):
    path = str(tmp_path / "sqix_maxn")
    with SqixFileCreation(path) as sf:
        for i in range(sf.MAX_ENTRIES):
            assert sf.add_entry(f"entry number {i}".encode()) == i
    with SqixFileConsumption(path) as sf:
        for i in range(sf.MAX_ENTRIES):
            assert sf.read_entry(i) == f"entry number {i}".encode()


def test_sqix_max_size(tmp_path):
    path = str(tmp_path / "sqix_maxs")
    with SqixFileCreation(path) as sf:
        for i in range(sf.MAX_ENTRIES):
            assert sf.add_entry(array.array("B", bytes(1024))) == i
    with SqixFileConsumption(path) as sf:
        for i in range(sf.MAX_ENTRIES):
            assert len(sf.read_entry(i)) == 1024


def test_sqix_overmax_num(tmp_path):
    path = str(tmp_path / "sqix_overmaxn")
    with SqixFileCreation(path) as sf:
        for i in range(sf.MAX_ENTRIES):
            assert sf.has_room(1)
            assert sf.add_entry(f"entry number {i}".encode()) == i
        with pytest.raises(SqixFileMaxEntriesError):
            sf.add_entry(f"entry number {i+1}".encode())
        assert not sf.has_room(1)
    with SqixFileConsumption(path) as sf:
        for i in range(sf.MAX_ENTRIES):
            assert sf.read_entry(i) == f"entry number {i}".encode()


def test_sqix_overmax_size1(tmp_path):
    path = str(tmp_path / "sqix_overmaxs1")
    with SqixFileCreation(path) as sf:
        for i in range(sf.MAX_ENTRIES - 1):
            assert sf.has_room(1024)
            assert sf.add_entry(array.array("B", bytes(1024))) == i
        assert sf.has_room(1024)
        assert not sf.has_room(1025)
        with pytest.raises(SqixFileMaxLenError):
            sf.add_entry(array.array("B", bytes(1025)))
    with SqixFileConsumption(path) as sf:
        for i in range(sf.MAX_ENTRIES - 1):
            assert len(sf.read_entry(i)) == 1024


def test_sqix_overmax_size2(tmp_path):
    path = str(tmp_path / "sqix_overmaxs2")
    with SqixFileCreation(path) as sf:
        assert sf.add_entry(array.array("B", bytes(sf.MAX_ENTRY_LEN))) == 0
        with pytest.raises(SqixFileMaxLenError):
            sf.add_entry(array.array("B", bytes(1)))
    with SqixFileConsumption(path) as sf:
        assert len(sf.read_entry(0)) == sf.MAX_ENTRY_LEN


def test_sqix_random_errors(tmp_path):
    path = str(tmp_path / "sqix_rnd_errs1")
    with SqixFileCreation(path) as sf:
        with pytest.raises(SqixFileError):
            sf.add_entry(bytes(sf.MAX_ENTRY_LEN + 1))
        with pytest.raises(SqixFileError):
            sf.has_room(sf.MAX_ENTRY_LEN + 1)
        assert sf.add_entry(bytes(1)) == 0
    with SqixFileConsumption(path) as sf:
        assert len(sf.read_entry(0)) == 1
        assert len(sf.read_entry(1)) == 0
        assert len(sf.read_entry(sf.MAX_ENTRIES - 1)) == 0
        with pytest.raises(SqixFileError):
            sf.read_entry(sf.MAX_ENTRIES)
