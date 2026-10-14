"""Project paths that resolve correctly in Cloudera AI engines and local dev."""

from __future__ import annotations

import os
from pathlib import Path


def project_root() -> Path:
    """Return the CAI project root without relying on the caller's ``__file__``."""
    try:
        from bootstrap_entry import discover_project_root

        return discover_project_root(None)
    except ImportError:
        pass

    for candidate in (Path.cwd(), *Path.cwd().parents):
        resolved = candidate.resolve()
        if (resolved / "data" / "schema.sql").is_file():
            return resolved
    if cdsw := os.environ.get("CDSW_PROJECT"):
        base = Path(cdsw)
        try:
            for child in base.iterdir():
                if child.is_dir() and (child / "data" / "schema.sql").is_file():
                    return child.resolve()
        except OSError:
            pass
        return base.resolve()
    try:
        return Path(__file__).resolve().parent.parent
    except NameError:
        return Path.cwd().resolve()


def schema_path() -> Path:
    return project_root() / "data" / "schema.sql"


def default_db_path() -> Path:
    """Bootstrap SQLite path (admin control plane); override with CUSTOMER360_DB_PATH."""
    raw = os.environ.get("CUSTOMER360_DB_PATH", "data/customer360.db")
    path = Path(raw)
    if not path.is_absolute():
        path = project_root() / path
    return path.resolve()


def configured_warehouse_db_path() -> Path:
    """Resolved warehouse SQLite path from admin data source (falls back to default_db_path)."""
    from customer360.data_source import resolve_sqlite_warehouse_path

    return resolve_sqlite_warehouse_path()
