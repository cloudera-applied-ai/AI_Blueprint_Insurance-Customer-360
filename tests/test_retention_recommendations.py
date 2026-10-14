"""Retention queue recommendations API."""

from __future__ import annotations

import sqlite3

import pytest

from customer360.api.retention_playbook import fetch_retention_playbook
from customer360.churn.scoring import churn_scores_populated


def test_playbook_queue_has_no_inline_actions(conn: sqlite3.Connection) -> None:
    if not churn_scores_populated(conn):
        pytest.skip("churn scores not populated (install ML deps from requirements-dev.txt)")
    data = fetch_retention_playbook(conn, limit=5)
    assert data["items"]
    assert all(item["recommended_action"] is None for item in data["items"])
