"""
cache.py — SQLite-backed HTTP response cache for EDGAR API calls.

Caches companyfacts and submissions responses to avoid hitting EDGAR
on every request. TTL: 6 hours (EDGAR updates filings infrequently).

Thread-safety: WAL journal mode allows concurrent reads. A threading.Lock
serializes writes so concurrent async workers don't corrupt the database.
"""

import sqlite3
import json
import time
import threading
import os
from pathlib import Path

CACHE_PATH = Path(__file__).parent / "data" / "edgar_cache.db"
TTL_SECONDS = 6 * 60 * 60  # 6 hours

_write_lock = threading.Lock()


def open_cache_connection() -> sqlite3.Connection:
    CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(CACHE_PATH), check_same_thread=False)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("""
        CREATE TABLE IF NOT EXISTS cache (
            key       TEXT PRIMARY KEY,
            value     TEXT NOT NULL,
            cached_at INTEGER NOT NULL
        )
    """)
    conn.commit()
    return conn


def load_cached_json(key: str):
    """Return cached value if present and within TTL, otherwise None."""
    conn = open_cache_connection()
    try:
        row = conn.execute(
            "SELECT value, cached_at FROM cache WHERE key = ?", (key,)
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    value, cached_at = row
    if time.time() - cached_at > TTL_SECONDS:
        return None
    return json.loads(value)


def load_stale_cached_json(key: str):
    """Return cached value regardless of TTL. Used as fallback when SEC is unreachable."""
    conn = open_cache_connection()
    try:
        row = conn.execute(
            "SELECT value FROM cache WHERE key = ?", (key,)
        ).fetchone()
    finally:
        conn.close()
    return json.loads(row[0]) if row else None


def store_cached_json(key: str, value: dict) -> None:
    with _write_lock:
        conn = open_cache_connection()
        try:
            conn.execute(
                "INSERT OR REPLACE INTO cache (key, value, cached_at) VALUES (?, ?, ?)",
                (key, json.dumps(value), int(time.time()))
            )
            conn.commit()
        finally:
            conn.close()


def clear_cached_json(key: str) -> None:
    with _write_lock:
        conn = open_cache_connection()
        try:
            conn.execute("DELETE FROM cache WHERE key = ?", (key,))
            conn.commit()
        finally:
            conn.close()


def cache_health_check() -> dict:
    """Probe the SQLite cache. Returns {"healthy": bool, "detail": str}."""
    try:
        conn = open_cache_connection()
        conn.execute("SELECT 1 FROM cache LIMIT 1")
        conn.close()
        return {"healthy": True, "detail": "ok"}
    except Exception as exc:
        return {"healthy": False, "detail": str(exc)}


# Backward-compatible aliases for existing imports.
def cache_get(key: str):
    return load_cached_json(key)


def cache_set(key: str, value: dict) -> None:
    store_cached_json(key, value)


def cache_clear(key: str) -> None:
    clear_cached_json(key)
