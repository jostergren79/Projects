"""
cache.py — SQLite-backed HTTP response cache for EDGAR API calls.

Caches companyfacts and submissions responses to avoid hitting EDGAR
on every request. TTL: 6 hours (EDGAR updates filings infrequently).
"""

import sqlite3
import json
import time
import os
from pathlib import Path

CACHE_PATH = Path(__file__).parent / "data" / "edgar_cache.db"
TTL_SECONDS = 6 * 60 * 60  # 6 hours


def _get_conn() -> sqlite3.Connection:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(CACHE_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            key       TEXT PRIMARY KEY,
            value     TEXT NOT NULL,
            cached_at INTEGER NOT NULL
        )
    """)
    conn.commit()
    return conn


def cache_get(key: str):
    conn = _get_conn()
    row = conn.execute(
        "SELECT value, cached_at FROM cache WHERE key = ?", (key,)
    ).fetchone()
    conn.close()
    if not row:
        return None
    value, cached_at = row
    if time.time() - cached_at > TTL_SECONDS:
        return None  # expired
    return json.loads(value)


def cache_set(key: str, value: dict) -> None:
    conn = _get_conn()
    conn.execute(
        "INSERT OR REPLACE INTO cache (key, value, cached_at) VALUES (?, ?, ?)",
        (key, json.dumps(value), int(time.time()))
    )
    conn.commit()
    conn.close()


def cache_clear(key: str) -> None:
    conn = _get_conn()
    conn.execute("DELETE FROM cache WHERE key = ?", (key,))
    conn.commit()
    conn.close()
