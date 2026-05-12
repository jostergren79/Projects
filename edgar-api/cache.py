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
from typing import Optional
import os
from pathlib import Path

CACHE_PATH = Path(__file__).parent / "data" / "edgar_cache.db"
TTL_SECONDS = 6 * 60 * 60  # 6 hours
SESSION_TTL_SECONDS = 60 * 60  # 1 hour

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
    conn.execute("""
        CREATE TABLE IF NOT EXISTS session_tier_cache (
            session_id TEXT PRIMARY KEY,
            tier       TEXT NOT NULL,
            cached_at  INTEGER NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            customer_id TEXT PRIMARY KEY,
            email       TEXT NOT NULL,
            tier        TEXT NOT NULL DEFAULT 'standard',
            created_at  INTEGER NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS watchlists (
            customer_id TEXT NOT NULL,
            cik         TEXT NOT NULL,
            ticker      TEXT NOT NULL DEFAULT '',
            name        TEXT NOT NULL DEFAULT '',
            added_at    INTEGER NOT NULL,
            PRIMARY KEY (customer_id, cik)
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


# ── Session tier cache (Stripe verification result, 1-hour TTL) ─────────────

def get_cached_session_tier(session_id: str) -> Optional[str]:
    conn = open_cache_connection()
    try:
        row = conn.execute(
            "SELECT tier, cached_at FROM session_tier_cache WHERE session_id = ?",
            (session_id,),
        ).fetchone()
    finally:
        conn.close()
    if not row:
        return None
    tier, cached_at = row
    if time.time() - cached_at > SESSION_TTL_SECONDS:
        return None
    return tier


def store_cached_session_tier(session_id: str, tier: str) -> None:
    with _write_lock:
        conn = open_cache_connection()
        try:
            conn.execute(
                """INSERT OR REPLACE INTO session_tier_cache (session_id, tier, cached_at)
                   VALUES (?, ?, ?)""",
                (session_id, tier, int(time.time())),
            )
            conn.commit()
        finally:
            conn.close()


# ── Watchlist CRUD ────────────────────────────────────────────────────────────

def get_watchlist(customer_id: str) -> list:
    """Return all watchlist items for a customer, newest first."""
    conn = open_cache_connection()
    try:
        rows = conn.execute(
            "SELECT cik, ticker, name, added_at FROM watchlists WHERE customer_id = ? ORDER BY added_at DESC",
            (customer_id,),
        ).fetchall()
    finally:
        conn.close()
    return [{"cik": r[0], "ticker": r[1], "name": r[2], "saved_at": r[3]} for r in rows]


def add_to_watchlist(customer_id: str, cik: str, ticker: str, name: str) -> None:
    """Insert a company into a customer's watchlist. No-op if already present."""
    with _write_lock:
        conn = open_cache_connection()
        try:
            conn.execute(
                """INSERT OR IGNORE INTO watchlists (customer_id, cik, ticker, name, added_at)
                   VALUES (?, ?, ?, ?, ?)""",
                (customer_id, cik, ticker, name, int(time.time())),
            )
            conn.commit()
        finally:
            conn.close()


def remove_from_watchlist(customer_id: str, cik: str) -> None:
    """Remove a company from a customer's watchlist."""
    with _write_lock:
        conn = open_cache_connection()
        try:
            conn.execute(
                "DELETE FROM watchlists WHERE customer_id = ? AND cik = ?",
                (customer_id, cik),
            )
            conn.commit()
        finally:
            conn.close()


# ── User registry ─────────────────────────────────────────────────────────────

def upsert_user(customer_id: str, email: str, tier: str) -> None:
    """Insert or update a user record. Preserves original created_at on update."""
    with _write_lock:
        conn = open_cache_connection()
        try:
            conn.execute(
                """INSERT INTO users (customer_id, email, tier, created_at)
                   VALUES (?, ?, ?, ?)
                   ON CONFLICT(customer_id) DO UPDATE SET email=excluded.email, tier=excluded.tier""",
                (customer_id, email, tier, int(time.time())),
            )
            conn.commit()
        finally:
            conn.close()


def get_user_email(customer_id: str) -> Optional[str]:
    """Return email for a customer_id, or None if not found."""
    conn = open_cache_connection()
    try:
        row = conn.execute(
            "SELECT email FROM users WHERE customer_id = ?", (customer_id,)
        ).fetchone()
    finally:
        conn.close()
    return row[0] if row else None
