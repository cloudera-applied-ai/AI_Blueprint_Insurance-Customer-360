"""Preserve admin control-plane rows across warehouse rebuild (same SQLite file)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

ADMIN_PRESERVE_TABLES = (
    "APP_ADMIN_DATA_SOURCE",
    "APP_ADMIN_LOCALIZATION",
    "APP_ADMIN_LLM",
    "APP_ADMIN_KPI_BENCHMARK",
)


def backup_admin_state(db_path: Path) -> dict[str, list[sqlite3.Row]] | None:
    if not db_path.is_file():
        return None
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    backup: dict[str, list[sqlite3.Row]] = {}
    try:
        for table in ADMIN_PRESERVE_TABLES:
            exists = conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?",
                (table,),
            ).fetchone()
            if not exists:
                continue
            backup[table] = conn.execute(f"SELECT * FROM {table}").fetchall()
    finally:
        conn.close()
    return backup if backup else None


def restore_admin_state(db_path: Path, backup: dict[str, list[sqlite3.Row]] | None) -> None:
    if not backup or not db_path.is_file():
        return
    conn = sqlite3.connect(db_path)
    try:
        for table, rows in backup.items():
            if not rows:
                continue
            cols = rows[0].keys()
            col_list = ", ".join(cols)
            placeholders = ", ".join("?" for _ in cols)
            conn.execute(f"DELETE FROM {table}")
            conn.executemany(
                f"INSERT INTO {table} ({col_list}) VALUES ({placeholders})",
                [tuple(row[c] for c in cols) for row in rows],
            )
        conn.commit()
    finally:
        conn.close()
