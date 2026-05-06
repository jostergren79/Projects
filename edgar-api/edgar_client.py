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
import asyncio
from cache import load_cached_json, store_cached_json


def _user_agent() -> str:
    # Prefer a full SEC_USER_AGENT override for exact compliance strings.
    explicit = os.getenv("SEC_USER_AGENT", "").strip()
    if explicit:
        return explicit

    app_name = os.getenv("SEC_APP_NAME", "edgar-api/0.1").strip()
    contact = os.getenv("SEC_CONTACT_EMAIL", "contact@example.com").strip()
    return f"{app_name} {contact}"


def _truthy(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _validate_user_agent_config() -> None:
    # Optional strict mode for production: fail fast when SEC identity is not explicit.
    require_explicit = _truthy(os.getenv("SEC_REQUIRE_EXPLICIT_USER_AGENT", "false"))
    explicit = os.getenv("SEC_USER_AGENT", "").strip()
    if require_explicit and not explicit:
        raise RuntimeError(
            "SEC_REQUIRE_EXPLICIT_USER_AGENT=true requires SEC_USER_AGENT to be set"
        )


_validate_user_agent_config()


HEADERS = {
    "User-Agent": _user_agent(),
    "Accept-Encoding": "gzip, deflate",
}

BASE_DATA = "https://data.sec.gov"
BASE_WWW  = "https://www.sec.gov"

HTTP_TIMEOUT_SECONDS = float(os.getenv("SEC_HTTP_TIMEOUT_SECONDS", "20"))
HTTP_MAX_RETRIES = max(0, int(os.getenv("SEC_HTTP_MAX_RETRIES", "3")))
HTTP_RETRY_BASE_SECONDS = float(os.getenv("SEC_HTTP_RETRY_BASE_SECONDS", "0.5"))
HTTP_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}


def _retry_delay_seconds(attempt: int) -> float:
    # Exponential backoff, capped to avoid unbounded wait times.
    return min(4.0, HTTP_RETRY_BASE_SECONDS * (2 ** attempt))


def _is_retryable_status_code(status_code: int) -> bool:
    return status_code in HTTP_RETRYABLE_STATUS_CODES


async def fetch_json_with_optional_cache(url: str, cache_key=None) -> dict:
    if cache_key:
        cached = load_cached_json(cache_key)
        if cached is not None:
            return cached

    async with httpx.AsyncClient(headers=HEADERS, timeout=HTTP_TIMEOUT_SECONDS) as client:
        for attempt in range(HTTP_MAX_RETRIES + 1):
            try:
                response = await client.get(url)
                response.raise_for_status()
                data = response.json()
                break
            except httpx.HTTPStatusError as exc:
                if attempt < HTTP_MAX_RETRIES and _is_retryable_status_code(exc.response.status_code):
                    await asyncio.sleep(_retry_delay_seconds(attempt))
                    continue
                raise
            except (httpx.TimeoutException, httpx.RequestError):
                if attempt < HTTP_MAX_RETRIES:
                    await asyncio.sleep(_retry_delay_seconds(attempt))
                    continue
                raise

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
