"""FastAPI dependencies."""

from __future__ import annotations

import sqlite3
from collections.abc import Generator

from customer360.data_source import warehouse_sqlite_connect


def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = warehouse_sqlite_connect()
    try:
        yield conn
    finally:
        conn.close()
