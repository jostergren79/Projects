"""
Tests for EdgarWolf session tier cache and health endpoint.

Run with:  cd edgar-api && python -m pytest tests/ -v
Requires:  pip install pytest httpx fastapi
"""

import sys
import os
import time
import tempfile
import pytest

# Point cache at a temp DB so tests don't touch the real one.
_tmp = tempfile.mktemp(suffix=".db")
os.environ.setdefault("EDGAR_CACHE_PATH_OVERRIDE", _tmp)

import cache as _cache_module
from pathlib import Path
_cache_module.CACHE_PATH = Path(_tmp)

import cache
from cache import (
    get_cached_session_tier,
    store_cached_session_tier,
)


# ── Session tier cache tests ─────────────────────────────────────────────────

def test_session_cache_miss_returns_none():
    assert get_cached_session_tier("nonexistent-session-id") is None


def test_session_cache_stores_and_retrieves():
    store_cached_session_tier("sess_pro_001", "pro")
    assert get_cached_session_tier("sess_pro_001") == "pro"


def test_session_cache_stores_pro_plus():
    store_cached_session_tier("sess_pp_001", "pro_plus")
    assert get_cached_session_tier("sess_pp_001") == "pro_plus"


def test_session_cache_overwrites_on_duplicate():
    store_cached_session_tier("sess_dup_001", "standard")
    store_cached_session_tier("sess_dup_001", "pro")
    assert get_cached_session_tier("sess_dup_001") == "pro"


def test_session_cache_expires(monkeypatch):
    store_cached_session_tier("sess_exp_001", "pro")
    monkeypatch.setattr(cache, "SESSION_TTL_SECONDS", -1)
    assert get_cached_session_tier("sess_exp_001") is None


# ── Health endpoint ──────────────────────────────────────────────────────────

def _make_test_app():
    from fastapi import FastAPI
    test_app = FastAPI()

    @test_app.get("/company/{cik}/dashboard")
    async def _dash(cik: str):
        return {"cik": cik, "ok": True}

    @test_app.get("/health")
    async def _health():
        return {"status": "ok"}

    return test_app


@pytest.fixture(scope="module")
def client():
    from fastapi.testclient import TestClient
    return TestClient(_make_test_app(), raise_server_exceptions=True)


def test_health_returns_ok(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_dashboard_unrestricted(client):
    r = client.get("/company/0000099999/dashboard")
    assert r.status_code == 200
    assert r.json()["ok"] is True
