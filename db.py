from flask import g
import psycopg2
from psycopg2.extras import DictCursor

# password = salt + hash


def global_connect(db_url):
    conn = psycopg2.connect(db_url, cursor_factory=DictCursor)
    conn.autocommit = True
    g.db = conn
    g.cur = conn.cursor()


def get_connection(db_url):
    conn = psycopg2.connect(db_url, cursor_factory=DictCursor)
    conn.autocommit = True
    return conn
