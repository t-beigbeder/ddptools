from collections.abc import Callable
import functools
from typing import Generator, Iterable

import psycopg
import psycopg.rows
import psycopg.sql

import ddpbasics.files


class DspgError(Exception):
    pass


BASIC_DDL = """
CREATE TABLE IF NOT EXISTS category (
    id serial PRIMARY KEY,
    label text,
    content text,
    UNIQUE (label)
);
CREATE TABLE IF NOT EXISTS entity (
    id serial PRIMARY KEY,
    category_id integer REFERENCES category(id),
    key text NOT NULL,
    content bytea,
    ct_ref text,
    UNIQUE (category_id, key),
    FOREIGN KEY (category_id) REFERENCES category(id)
)
"""


@functools.cache
def pg_pass() -> str | None:
    return ddpbasics.files.read_pass_file(
        "/run/ds-pods-secrets/postgres_passwd"
    )


def pg_conninfo(host: str, db_name="") -> str:
    hi = f"host={host} " if host else ""
    if db_name == "":
        db_name = "postgres"
    return f"{hi}dbname={db_name} user=postgres password={pg_pass()}"


def pg_conn(host: str, db_name="") -> psycopg.Connection:
    return psycopg.connect(pg_conninfo(host, db_name))


def _pg_has_db(cur: psycopg.Cursor, db_name: str) -> bool:
    _ = cur.execute(
        "SELECT 1 FROM pg_catalog.pg_database WHERE datname = %s", (db_name,)
    )
    exist = cur.fetchone()
    return exist is not None


def pg_has_db(host: str, db_name: str) -> bool:
    with pg_conn(host) as conn:
        with conn.cursor() as cur:
            return _pg_has_db(cur, db_name)


def pg_drop_db(host: str, db_name: str, miss_ok=False) -> bool:
    try:
        conn = pg_conn(host)
        conn.autocommit = True
        with conn.cursor() as cur:
            if not _pg_has_db(cur, db_name):
                if not miss_ok:
                    raise DspgError(f"db {db_name} does not exist")
            else:
                cur.execute(psycopg.sql.SQL(f"DROP DATABASE {db_name}"))
    finally:
        conn.close()
    return True


def pg_create_db(
    host: str, db_name: str, exist_ok=False, drop_db=False, ddl=""
) -> bool:
    try:
        conn = pg_conn(host)
        conn.autocommit = True
        with conn.cursor() as cur:
            if _pg_has_db(cur, db_name):
                if not exist_ok:
                    raise DspgError(f"db {db_name} already exists")
                if not drop_db:
                    return True
                cur.execute(psycopg.sql.SQL(f"DROP DATABASE {db_name}"))
            cur.execute(psycopg.sql.SQL(f"CREATE DATABASE {db_name}"))
    finally:
        conn.close()
    if not ddl:
        return True
    try:
        conn = pg_conn(host, db_name)
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute(psycopg.sql.SQL(ddl))
    finally:
        conn.close()

    return True


def _pg_cursor_do_once(
    host: str,
    db_name: str,
    doer: Callable[[psycopg.Cursor], psycopg.rows.TupleRow | None],
):
    with pg_conn(host, db_name) as conn:
        with conn.cursor() as cur:
            return doer(cur)


def _pg_cursor_do_many(
    host: str,
    db_name: str,
    doer: Callable[[psycopg.Cursor], list[tuple]],
):
    with pg_conn(host, db_name) as conn:
        with conn.cursor() as cur:
            return doer(cur)


def pg_create_category(host: str, db_name: str, label="", content=None) -> int:
    def _doer(cur: psycopg.Cursor):
        cur.execute(
            "INSERT INTO category (label, content) VALUES(%(label)s, %(content)s) RETURNING id",
            dict(label=label, content=content),
        )
        return cur.fetchone()

    cid = _pg_cursor_do_once(host, db_name, _doer)
    if cid is None:
        raise DspgError(f"Internal error label {label} not inserted")
    return cid[0]


def pg_create_entity(
    host: str,
    db_name: str,
    label="",
    key="",
    content: bytes | None = None,
    ct_ref: str | None = None,
) -> int:
    def _doer(cur: psycopg.Cursor):
        cur.execute(
            "INSERT INTO entity (category_id, key, content, ct_ref) "
            "VALUES((SELECT id FROM category WHERE label=%s), %s, %s, %s) RETURNING id",
            (label, key, content, ct_ref),
        )
        return cur.fetchone()

    eid = _pg_cursor_do_once(host, db_name, _doer)
    if eid is None:
        raise DspgError(f"Internal error entity {label} {key} not inserted")
    return eid[0]


def pg_create_entities(
    host: str,
    db_name: str,
    label="",
    values: Iterable[tuple[str, bytes | None, str | None]] = [("", None, None)],
) -> list[int]:
    def _avalues(cid: int):
        for val in values:
            yield (cid, val[0], val[1], val[2])

    def _doer(cur: psycopg.Cursor) -> list[tuple]:
        cur.execute("SELECT id FROM category WHERE label=%s", (label,))
        cid = cur.fetchone()
        if cid is None:
            raise DspgError(f"unknown label {label}")
        cur.executemany(
            "INSERT INTO entity (category_id, key, content, ct_ref) VALUES(%s, %s, %s, %s) RETURNING id",
            _avalues(cid[0]),
            returning=True,
        )
        ltr = []
        while True:
            lt = cur.fetchall()
            for t in lt:
                ltr.append(t)
            if not cur.nextset():
                break
        return ltr

    eids = _pg_cursor_do_many(host, db_name, _doer)
    return [int(eid[0]) for eid in eids]


def pg_read_entity(
    host: str,
    db_name: str,
    label="",
    key="",
) -> tuple[bytes | None, str | None]:
    def _doer(cur: psycopg.Cursor):
        sql = "SELECT content, ct_ref FROM entity WHERE category_id=(SELECT id FROM category WHERE label = %s) and key=%s"
        cur.execute(sql, (label, key))
        return cur.fetchone()

    eid = _pg_cursor_do_once(host, db_name, _doer)
    if eid is None:
        raise DspgError(f"unknown label {label} key {key}")
    return eid


def pg_read_entities(
    host: str,
    db_name: str,
    label="",
    with_keys_only=False,
    keys: list[str] | None = None,
) -> Generator[tuple[str, bytes | None, str | None]]:
    if with_keys_only:
        sql = "SELECT key, NULL, NULL FROM entity WHERE category_id=(SELECT id FROM category WHERE label = %s)"
    else:
        sql = "SELECT key, content, ct_ref FROM entity WHERE category_id=(SELECT id FROM category WHERE label = %s)"
    if keys:
        inks = ",".join(f"'{key}'" for key in keys)
        sql += f" AND key IN ({inks})"

    with pg_conn(host, db_name) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, (label,))
            while True:
                rows = cur.fetchmany()
                if len(rows) == 0:
                    return
                for row in rows:
                    yield row


class PgService:
    def __init__(self, host: str, db_name: str):
        self.host = host
        self.db_name = db_name

    def exists(self) -> bool:
        return pg_has_db(self.host, self.db_name)

    def drop_db(self, miss_ok=False) -> bool:
        return pg_drop_db(self.host, self.db_name, miss_ok)

    def create_db(self, exist_ok=False, drop_db=False, ddl="") -> bool:
        return pg_create_db(self.host, self.db_name, exist_ok, drop_db, ddl)

    def create_category(self, label="", content=None) -> int:
        return pg_create_category(self.host, self.db_name, label, content)

    def create_entity(
        self, label="", key="", content: bytes | None = None, ct_ref: str | None = None
    ) -> int:
        return pg_create_entity(self.host, self.db_name, label, key, content, ct_ref)

    def create_entities(
        self,
        label="",
        values: Iterable[tuple[str, bytes | None, str | None]] = [("", None, None)],
    ) -> list[int]:
        return pg_create_entities(self.host, self.db_name, label, values)

    def read_entity(self, label="", key="") -> tuple[bytes | None, str | None]:
        return pg_read_entity(self.host, self.db_name, label, key)

    def read_entities(
        self, label="", with_keys_only=False, keys: list[str] | None = None
    ) -> Generator[tuple[str, bytes | None, str | None]]:
        return pg_read_entities(self.host, self.db_name, label, with_keys_only, keys)
