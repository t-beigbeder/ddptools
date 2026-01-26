import os

from otvl_general.utils.cache import get_cache_path_for
from otvl_general.utils.s3sqix import (
    S3SqixEntryService,
    S3SqixFileConsumption,
    S3SqixFileCreation,
    S3SqixFileService,
)


def test_s3sqix_base(tmp_path):
    td = str(tmp_path)
    path = "tmp/test_s3sqix_base.sqix"
    with S3SqixFileCreation(
        "otvl-tests", td, path, category="test_s3sqix", profile_name="otvl-tests"
    ) as sf:
        assert sf.add_entry("entry#1".encode()) == 0
        assert sf.len() == 7
        assert sf.add_entry("2nd entry".encode()) == 1
        assert sf.len() == 16
    with S3SqixFileConsumption(
        "otvl-tests", path, category="test_s3sqix", profile_name="otvl-tests"
    ) as sf:
        assert sf.read_entry(0) == "entry#1".encode()
        assert sf.read_entry(1) == "2nd entry".encode()


def test_s3sqix_nocm(tmp_path):
    td = str(tmp_path)
    path = "tmp/test_s3sqix_nocm.sqix"
    sf = S3SqixFileCreation(
        "otvl-tests", td, path, category="test_s3sqix", profile_name="otvl-tests"
    )
    assert sf.add_entry("entry#1".encode()) == 0
    assert sf.len() == 7
    assert sf.add_entry("2nd entry".encode()) == 1
    assert sf.len() == 16
    sf.close()
    sf = S3SqixFileConsumption(
        "otvl-tests", path, category="test_s3sqix", profile_name="otvl-tests"
    )
    assert sf.read_entry(0) == "entry#1".encode()
    assert sf.read_entry(1) == "2nd entry".encode()


def test_s3sqix_force(tmp_path):
    td = str(tmp_path)
    path = "tmp/test_s3sqix_force.sqix"
    with S3SqixFileCreation(
        "otvl-tests", td, path, category="test_s3sqix", profile_name="otvl-tests"
    ) as sf:
        assert sf.add_entry("entry#1".encode()) == 0
        assert sf.len() == 7
        assert sf.add_entry("2nd entry".encode()) == 1
        assert sf.len() == 16
    os.remove(get_cache_path_for(path, "test_s3sqix", ".sqix"))
    with S3SqixFileConsumption(
        "otvl-tests", path, category="test_s3sqix", profile_name="otvl-tests"
    ) as sf:
        assert sf.read_entry(0) == "entry#1".encode()
        assert sf.read_entry(1) == "2nd entry".encode()


def test_s3sqix_max_num_base(tmp_path):
    td = str(tmp_path)
    path = "tmp/test_s3sqix_max_num_base.sqix"
    with S3SqixFileCreation(
        "otvl-tests", td, path, category="test_s3sqix", profile_name="otvl-tests"
    ) as sf:
        for i in range(sf.MAX_ENTRIES):
            assert sf.add_entry(f"entry number {i}".encode()) == i
    with S3SqixFileConsumption(
        "otvl-tests", path, category="test_s3sqix", profile_name="otvl-tests"
    ) as sf:
        for i in range(sf.MAX_ENTRIES):
            assert sf.read_entry(i) == f"entry number {i}".encode()


def test_s3sqix_max_num_force(tmp_path):
    td = str(tmp_path)
    path = "tmp/test_s3sqix_max_num_force.sqix"
    with S3SqixFileCreation(
        "otvl-tests", td, path, category="test_s3sqix", profile_name="otvl-tests"
    ) as sf:
        for i in range(sf.MAX_ENTRIES):
            assert sf.add_entry(f"entry number {i}".encode()) == i
    os.remove(get_cache_path_for(path, "test_s3sqix", ".sqix"))
    with S3SqixFileConsumption(
        "otvl-tests", path, category="test_s3sqix", profile_name="otvl-tests"
    ) as sf:
        for i in range(sf.MAX_ENTRIES):
            assert sf.read_entry(i) == f"entry number {i}".encode()


def test_s3sqix_file_service(tmp_path):
    td = str(tmp_path)
    with S3SqixFileService("otvl-tests", td, "dummy_dbn", "otvl-tests").new_s3sqix_file(
        "test_s3sqix"
    ) as sf:
        for i in range(sf.MAX_ENTRIES):
            assert sf.add_entry(f"entry number {i}".encode()) == i
    ses = S3SqixEntryService("otvl-tests", "otvl-tests")
    for i in range(sf.MAX_ENTRIES):
        assert (
            ses.read_s3sqix_entry("dummy_dbn/test_s3sqix/0", "test_s3sqix", i)
            == f"entry number {i}".encode()
        )
