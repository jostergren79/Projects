"""
edgar_client.py — thin async wrapper around the SEC EDGAR APIs.

Endpoints used:
  - https://www.sec.gov/files/company_tickers.json      (ticker → CIK map)
  - https://data.sec.gov/submissions/{CIK10}.json       (company metadata + filings)
  - https://data.sec.gov/api/xbrl/companyfacts/{CIK10}.json  (all XBRL financial facts)

SEC rate-limit guidance: max 10 req/s, identify yourself via User-Agent.
"""

import httpx
import os
from cache import load_cached_json, store_cached_json


def _user_agent() -> str:
    # Prefer a full SEC_USER_AGENT override for exact compliance strings.
    explicit = os.getenv("SEC_USER_AGENT", "").strip()
    if explicit:
        return explicit

    app_name = os.getenv("SEC_APP_NAME", "edgar-api/0.1").strip()
    contact = os.getenv("SEC_CONTACT_EMAIL", "contact@example.com").strip()
    return f"{app_name} {contact}"


HEADERS = {
    "User-Agent": _user_agent(),
    "Accept-Encoding": "gzip, deflate",
}

BASE_DATA = "https://data.sec.gov"
BASE_WWW  = "https://www.sec.gov"


async def fetch_json_with_optional_cache(url: str, cache_key=None) -> dict:
    if cache_key:
        cached = load_cached_json(cache_key)
        if cached is not None:
            return cached
    async with httpx.AsyncClient(headers=HEADERS, timeout=20) as client:
        r = await client.get(url)
        r.raise_for_status()
        data = r.json()
    if cache_key:
        store_cached_json(cache_key, data)
    return data


async def fetch_company_ticker_index() -> dict:
    """Returns {TICKER: {cik_str, title, ticker}} for all US public companies."""
    data = await fetch_json_with_optional_cache(
        f"{BASE_WWW}/files/company_tickers.json", cache_key="ticker_map"
    )
    return {v["ticker"].upper(): v for v in data.values()}


async def fetch_company_submissions(cik10: str) -> dict:
    """Company metadata + filing history. cik10 = zero-padded 10-digit CIK."""
    return await fetch_json_with_optional_cache(
        f"{BASE_DATA}/submissions/CIK{cik10}.json", cache_key=f"submissions:{cik10}"
    )


async def fetch_company_facts(cik10: str) -> dict:
    """All reported XBRL facts across all filings."""
    return await fetch_json_with_optional_cache(
        f"{BASE_DATA}/api/xbrl/companyfacts/CIK{cik10}.json", cache_key=f"facts:{cik10}"
    )


def normalize_cik_to_10_digits(cik) -> str:
    """Zero-pad CIK to 10 digits as required by SEC URLs."""
    return str(cik).zfill(10)


# Backward-compatible aliases for existing imports.
async def get_ticker_map() -> dict:
    return await fetch_company_ticker_index()


async def get_submissions(cik10: str) -> dict:
    return await fetch_company_submissions(cik10)


async def get_company_facts(cik10: str) -> dict:
    return await fetch_company_facts(cik10)


def pad_cik(cik) -> str:
    return normalize_cik_to_10_digits(cik)
