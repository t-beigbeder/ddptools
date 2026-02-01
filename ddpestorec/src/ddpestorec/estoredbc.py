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
