import pytest

from . import estoredb


@pytest.fixture
def t_pgs() -> str:
    return "t-db-pgs"


def test_conn(t_pgs):
    with estoredb.pg_conn(t_pgs) as conn:
        _ = conn


def test_cur(t_pgs):
    with estoredb.pg_conn(t_pgs) as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM pg_catalog.pg_database WHERE datname = 'postgres'"
            )
            exists = cur.fetchone()
            assert exists


def test_has_db(t_pgs):
    assert estoredb.pg_drop_db(t_pgs, "estore_pytest_one", True)
    assert not estoredb.pg_has_db(t_pgs, "estore_pytest_one")


def test_create_db_no_ddl(t_pgs):
    assert estoredb.pg_drop_db(t_pgs, "estore_pytest_one", True)
    assert estoredb.pg_create_db(t_pgs, "estore_pytest_one")
    assert estoredb.pg_has_db(t_pgs, "estore_pytest_one")
    assert estoredb.pg_drop_db(t_pgs, "estore_pytest_one", True)


def test_drop_db(t_pgs):
    assert estoredb.pg_drop_db(t_pgs, "estore_pytest_one", True)
    assert estoredb.pg_create_db(t_pgs, "estore_pytest_one")
    assert estoredb.pg_drop_db(t_pgs, "estore_pytest_one")
    assert not estoredb.pg_has_db(t_pgs, "estore_pytest_one")


def test_drop_nok(t_pgs):
    assert estoredb.pg_drop_db(t_pgs, "estore_pytest_one", True)
    with pytest.raises(estoredb.DspgError):
        assert estoredb.pg_drop_db(t_pgs, "estore_pytest_one", False)


def test_create_db_ddl(t_pgs):
    assert estoredb.pg_drop_db(t_pgs, "estore_pytest_one", True)
    assert estoredb.pg_create_db(t_pgs, "estore_pytest_one", ddl=estoredb.BASIC_DDL)
    assert estoredb.pg_has_db(t_pgs, "estore_pytest_one")


def test_create_category(t_pgs):
    assert estoredb.pg_drop_db(t_pgs, "estore_pytest_one", True)
    assert estoredb.pg_create_db(t_pgs, "estore_pytest_one", ddl=estoredb.BASIC_DDL)
    assert estoredb.pg_create_category(t_pgs, "estore_pytest_one", "lb1") is not None


def test_create_entity(t_pgs):
    assert estoredb.pg_drop_db(t_pgs, "estore_pytest_one", True)
    assert estoredb.pg_create_db(t_pgs, "estore_pytest_one", ddl=estoredb.BASIC_DDL)
    assert estoredb.pg_create_category(t_pgs, "estore_pytest_one", "lb1") is not None
    assert (
        estoredb.pg_create_entity(
            t_pgs, "estore_pytest_one", "lb1", "key1", "rue de prés".encode("utf-8")
        )
        is not None
    )


def test_create_and_read_entity(t_pgs):
    assert estoredb.pg_drop_db(t_pgs, "estore_pytest_one", True)
    assert estoredb.pg_create_db(t_pgs, "estore_pytest_one", ddl=estoredb.BASIC_DDL)
    assert estoredb.pg_create_category(t_pgs, "estore_pytest_one", "lb1") is not None
    _ = estoredb.pg_create_entity(
        t_pgs, "estore_pytest_one", "lb1", "key1", "rue de prés".encode("utf-8")
    )
    ct, ct_ref = estoredb.pg_read_entity(t_pgs, "estore_pytest_one", "lb1", "key1")
    assert ct == "rue de prés".encode("utf-8")
    assert ct_ref is None


def test_create_entities(t_pgs):
    assert estoredb.pg_drop_db(t_pgs, "estore_pytest_one", True)
    assert estoredb.pg_create_db(t_pgs, "estore_pytest_one", ddl=estoredb.BASIC_DDL)
    assert estoredb.pg_create_category(t_pgs, "estore_pytest_one", "lb1") is not None
    lt = estoredb.pg_create_entities(
        t_pgs,
        "estore_pytest_one",
        "lb1",
        (
            ("key1", "1 rue de prés".encode("utf-8"), None),
            ("key2", "2 rue de prés".encode("utf-8"), None),
        ),
    )
    assert len(lt) == 2 and lt[0] > 0


def test_create_many_entities(t_pgs):
    def gen():
        for i in range(10000):
            yield f"key{i+1}", f"{i+1} rue des prés".encode("utf-8"), None

    assert estoredb.pg_drop_db(t_pgs, "estore_pytest_one", True)
    assert estoredb.pg_create_db(t_pgs, "estore_pytest_one", ddl=estoredb.BASIC_DDL)
    assert estoredb.pg_create_category(t_pgs, "estore_pytest_one", "lb1") is not None
    lt = estoredb.pg_create_entities(
        t_pgs,
        "estore_pytest_one",
        "lb1",
        gen(),
    )
    assert len(lt) == 10000 and lt[0] > 0


@pytest.mark.parametrize(
    "with_keys_only, keys",
    [
        (False, None),
        (True, None),
        (False, ['key1', 'key2', 'key4', 'key8', 'key16'])
    ],
)
def test_read_many_entities(t_pgs, with_keys_only, keys):
    TSZ = 10000

    def gen():
        for i in range(TSZ):
            yield f"key{i+1}", f"{i+1} rue des prés".encode("utf-8"), str(i + 1)

    assert estoredb.pg_drop_db(t_pgs, "estore_pytest_one", True)
    assert estoredb.pg_create_db(t_pgs, "estore_pytest_one", ddl=estoredb.BASIC_DDL)
    assert estoredb.pg_create_category(t_pgs, "estore_pytest_one", "lb1") is not None
    lt = estoredb.pg_create_entities(
        t_pgs,
        "estore_pytest_one",
        "lb1",
        gen(),
    )
    assert len(lt) == TSZ and lt[0] > 0
    count = 0
    for row in estoredb.pg_read_entities(
        t_pgs, "estore_pytest_one", "lb1", with_keys_only, keys
    ):
        count += 1
        if count % 1000 == 0:
            key, content, ct_ref = row
            if not with_keys_only:
                assert key == f"key{ct_ref}"
                assert content == f"{ct_ref} rue des prés".encode("utf-8")
    if not keys:
        assert count == TSZ
    else:
        assert count == 5


def test_service(t_pgs):
    TSZ = 1000

    def gen():
        for i in range(TSZ):
            yield f"key{i+1}", f"{i+1} rue des prés".encode("utf-8"), str(i + 1)

    svc = estoredb.PgService(t_pgs, "estore_pytest")
    assert svc.drop_db(True)
    assert svc.create_db()
    assert svc.drop_db()
    assert svc.create_db(ddl=estoredb.BASIC_DDL)
    assert svc.create_category("lb1")
    assert svc.create_category("lb2", "verbose")
    assert svc.create_category("lb3", "the third")
    assert svc.create_entity("lb1", "key1", "rue de prés".encode("utf-8")) is not None
    lt = svc.create_entities(
        "lb2",
        (
            ("key1", "1 rue de prés".encode("utf-8"), None),
            ("key2", "2 rue de prés".encode("utf-8"), None),
        ),
    )
    assert len(lt) == 2 and lt[0] > 0
    lt = svc.create_entities(
        "lb3",
        gen(),
    )
    assert len(lt) == TSZ and lt[0] > 0
    assert svc.read_entity("lb2", "key2")[0] == "2 rue de prés".encode("utf-8")
    count = 0
    for row in svc.read_entities("lb3"):
        count += 1
        if count % 100 == 0:
            key, content, ct_ref = row
            assert key == f"key{ct_ref}"
            assert content == f"{ct_ref} rue des prés".encode("utf-8")
    assert count == TSZ
