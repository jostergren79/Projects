"""
edgar_client.py — thin async wrapper around the SEC EDGAR APIs.

Endpoints used:
  - https://www.sec.gov/files/company_tickers.json                 (ticker → CIK map)
  - https://data.sec.gov/submissions/{CIK10}.json                  (company metadata + filings)
  - https://data.sec.gov/api/xbrl/companyfacts/{CIK10}.json        (all XBRL financial facts)
  - https://efts.sec.gov/LATEST/search-index?forms=10-Q,10-K&...   (recent filers feed)

SEC rate-limit guidance: max 10 req/s, identify yourself via User-Agent.

Protections implemented here:
  1. Token-bucket outbound rate limiter (default 4 req/s, env-configurable).
  2. 429 cooldown: when SEC returns 429, all outbound requests pause for a
     configurable window before the retry attempt, signalling we have backed off.
  3. In-flight deduplication: concurrent requests for the same cache key share
     one upstream fetch; the result is stored once and fanned out to all waiters.
"""

import httpx
import logging
import os
import asyncio
import time
from cache import load_cached_json, load_stale_cached_json, store_cached_json

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Identity / config helpers
# ---------------------------------------------------------------------------

def _user_agent() -> str:
    explicit = os.getenv("SEC_USER_AGENT", "").strip()
    if explicit:
        return explicit
    app_name = os.getenv("SEC_APP_NAME", "edgar-api/0.1").strip()
    contact = os.getenv("SEC_CONTACT_EMAIL", "contact@example.com").strip()
    return f"{app_name} {contact}"


def _truthy(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _validate_user_agent_config() -> None:
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
BASE_EFTS = "https://efts.sec.gov"

HTTP_TIMEOUT_SECONDS      = float(os.getenv("SEC_HTTP_TIMEOUT_SECONDS", "20"))
HTTP_MAX_RETRIES          = max(0, int(os.getenv("SEC_HTTP_MAX_RETRIES", "3")))
HTTP_RETRY_BASE_SECONDS   = float(os.getenv("SEC_HTTP_RETRY_BASE_SECONDS", "0.5"))
HTTP_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}

# Rate-limiter: max outbound SEC requests per second.
SEC_RATE_LIMIT_RPS        = float(os.getenv("SEC_RATE_LIMIT_RPS", "4"))
# How long to pause all outbound SEC fetches after receiving a 429.
SEC_429_COOLDOWN_SECONDS  = float(os.getenv("SEC_429_COOLDOWN_SECONDS", "30"))


# ---------------------------------------------------------------------------
# Protection 1 — token-bucket outbound rate limiter + 429 cooldown
# ---------------------------------------------------------------------------

class _SecRateLimiter:
    """
    Token-bucket rate limiter for outbound SEC requests.

    Tokens refill at `rate` per second up to a burst cap of `rate` tokens.
    A 429 response triggers a cooldown that blocks all outbound fetches for
    `cooldown_seconds`, giving SEC's throttle time to clear before we retry.
    """

    def __init__(self, rate: float, cooldown_seconds: float) -> None:
        self._rate = rate
        self._cooldown_seconds = cooldown_seconds
        self._tokens = rate
        self._last_refill = time.monotonic()
        self._cooldown_until: float = 0.0
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()

            # Honor 429 cooldown before consuming a token.
            if now < self._cooldown_until:
                wait = self._cooldown_until - now
                await asyncio.sleep(wait)
                now = time.monotonic()

            # Refill tokens based on elapsed time.
            elapsed = now - self._last_refill
            self._tokens = min(self._rate, self._tokens + elapsed * self._rate)
            self._last_refill = now

            if self._tokens >= 1.0:
                self._tokens -= 1.0
            else:
                wait = (1.0 - self._tokens) / self._rate
                await asyncio.sleep(wait)
                self._tokens = 0.0
                self._last_refill = time.monotonic()

    def notify_429(self) -> None:
        """Call when SEC returns 429; suspends all outbound fetches for the cooldown window."""
        self._cooldown_until = time.monotonic() + self._cooldown_seconds


_rate_limiter = _SecRateLimiter(
    rate=SEC_RATE_LIMIT_RPS,
    cooldown_seconds=SEC_429_COOLDOWN_SECONDS,
)


# ---------------------------------------------------------------------------
# Protection 2 — in-flight request deduplication
# ---------------------------------------------------------------------------

# Maps cache_key → asyncio.Future for the in-flight fetch result.
# Concurrent callers waiting on the same key share one upstream request.
_inflight: dict[str, asyncio.Future] = {}


def _retry_delay_seconds(attempt: int) -> float:
    return min(4.0, HTTP_RETRY_BASE_SECONDS * (2 ** attempt))


def _is_retryable_status_code(status_code: int) -> bool:
    return status_code in HTTP_RETRYABLE_STATUS_CODES


# ---------------------------------------------------------------------------
# Core fetch — rate-limited, deduplicated, cached
# ---------------------------------------------------------------------------

async def fetch_json_with_optional_cache(url: str, cache_key=None) -> dict:
    # Fast path: already cached.
    if cache_key:
        cached = load_cached_json(cache_key)
        if cached is not None:
            return cached

    # In-flight dedup: if another coroutine is already fetching this key, wait for it.
    if cache_key and cache_key in _inflight:
        return await asyncio.shield(_inflight[cache_key])

    loop = asyncio.get_event_loop()
    future: asyncio.Future = loop.create_future()
    if cache_key:
        _inflight[cache_key] = future

    try:
        data = await _do_fetch(url)
        if cache_key:
            store_cached_json(cache_key, data)
        future.set_result(data)
        return data
    except Exception as exc:
        # Stale-cache fallback: serve expired data rather than fail hard when SEC is unreachable.
        if cache_key:
            stale = load_stale_cached_json(cache_key)
            if stale is not None:
                logger.warning("SEC fetch failed for %s; serving stale cache. Error: %s", cache_key, exc)
                future.set_result(stale)
                return stale
        future.set_exception(exc)
        raise
    finally:
        if cache_key:
            _inflight.pop(cache_key, None)


async def _do_fetch(url: str) -> dict:
    """Execute a single URL fetch with rate limiting, retries, and 429 cooldown."""
    async with httpx.AsyncClient(headers=HEADERS, timeout=HTTP_TIMEOUT_SECONDS) as client:
        for attempt in range(HTTP_MAX_RETRIES + 1):
            await _rate_limiter.acquire()
            try:
                response = await client.get(url)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                if status == 429:
                    logger.warning("SEC returned 429 for %s; entering %ss cooldown", url, SEC_429_COOLDOWN_SECONDS)
                    _rate_limiter.notify_429()
                if attempt < HTTP_MAX_RETRIES and _is_retryable_status_code(status):
                    logger.info("Retryable HTTP %d for %s; attempt %d/%d", status, url, attempt + 1, HTTP_MAX_RETRIES)
                    await asyncio.sleep(_retry_delay_seconds(attempt))
                    continue
                raise
            except (httpx.TimeoutException, httpx.RequestError) as exc:
                if attempt < HTTP_MAX_RETRIES:
                    logger.info("Transient error for %s (%s); attempt %d/%d", url, type(exc).__name__, attempt + 1, HTTP_MAX_RETRIES)
                    await asyncio.sleep(_retry_delay_seconds(attempt))
                    continue
                raise
    # Unreachable; loop always returns or raises.
    raise RuntimeError("fetch loop exited without result")  # pragma: no cover


# ---------------------------------------------------------------------------
# Public fetch helpers
# ---------------------------------------------------------------------------

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


async def fetch_recent_filers(days: int = 14, limit: int = 30) -> list:
    """
    Returns companies that recently filed 10-Q or 10-K with SEC EDGAR.

    Source: SEC EDGAR full-text search API (EFTS).
    Accession number format XXXXXXXXXX-YY-NNNNNN; the first 10 digits are the CIK.
    Results are deduplicated by CIK so each company appears at most once.
    """
    from datetime import date, timedelta
    end_dt   = date.today()
    start_dt = end_dt - timedelta(days=days)

    url = (
        f"{BASE_EFTS}/LATEST/search-index"
        f"?q=%22%22"
        f"&forms=10-Q%2C10-K"
        f"&dateRange=custom"
        f"&startdt={start_dt.isoformat()}"
        f"&enddt={end_dt.isoformat()}"
    )

    # Cache keyed by date window + limit so changing the limit never serves stale results.
    from cache import load_cached_json, store_cached_json
    cache_key = f"feed:{start_dt}:{end_dt}:n{limit}"
    cached = load_cached_json(cache_key)
    if cached is not None:
        return cached

    raw = await _do_fetch(url)
    hits = (raw.get("hits") or {}).get("hits") or []

    seen: set[str] = set()
    result: list[dict] = []

    for hit in hits:
        src = hit.get("_source") or {}

        # CIK: EFTS returns a `ciks` list; take the first entry.
        cik_list = src.get("ciks") or []
        cik10 = str(cik_list[0]).zfill(10) if cik_list else ""
        if not cik10 or cik10 == "0000000000" or cik10 in seen:
            continue
        seen.add(cik10)

        # Company name: EFTS `display_names` format is "Name  (TICKER)  (CIK XXXXXXXXXX)"
        raw_name = (src.get("display_names") or [""])[0]
        name = raw_name.split("  (")[0].strip() if raw_name else ""

        # Form type: use root_forms (the parent filing type) rather than `form`
        # which may be an exhibit code like "EX-31.4".
        form = ((src.get("root_forms") or []) + [""])[0]

        result.append({
            "cik":    cik10,
            "name":   name,
            "form":   form,
            "filed":  src.get("file_date", ""),
            "period": src.get("period_ending", ""),
        })

        if len(result) >= limit:
            break

    store_cached_json(cache_key, result)
    return result


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
