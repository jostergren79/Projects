"""
edgar-api — main FastAPI application
Routes:
  GET /                            → serves edgar.html frontend
  GET /edgar                       → serves edgar.html frontend
  GET /health                      → health check
  GET /company?ticker=AAPL         → CIK lookup + company metadata
  GET /company/search?name=apple   → company name search
  GET /company/resolve?q=nike      → smart ticker-or-name resolver
  GET /company/object/{cik}        → consolidated company object + XBRL coverage
  GET /company/{cik}/metrics       → 8-quarter financial metrics
  GET /company/{cik}/segments      → segment revenue breakdown
  GET /company/{cik}/flags         → exception flags (metrics outside historical norms)
  GET /company/{cik}/summary       → rules-based natural language summary
  GET /company/{cik}/anomalies     → filing cadence + XBRL anomaly signals
  GET /company/{cik}/dashboard     → all of the above in one aggregated call
  GET /feed/recent                 → recent 10-Q / 10-K filers for signal board discovery
"""

import logging
import collections
import os
import pathlib
import time

from dotenv import load_dotenv
load_dotenv()

import httpx
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
    datefmt="%Y-%m-%dT%H:%M:%S",
)
logger = logging.getLogger(__name__)

_PUBLIC = pathlib.Path(__file__).parent.parent / "notes-api" / "public"

from cache import cache_health_check

from routers import (
    company_lookup,
    financial_metrics,
    segment_breakdown,
    anomaly_flags,
    narrative_summary,
    dashboard,
    feed,
    analytics,
    checkout,
    alerts,
    watchlist,
)

app = FastAPI(title="EDGAR Financial Metrics API", version="0.1.0")

# ---------------------------------------------------------------------------
# Per-IP rate limiting middleware
# Sliding window: max N requests per IP per window_seconds.
# Configurable via env: APP_RATE_LIMIT_REQUESTS, APP_RATE_LIMIT_WINDOW_SECONDS.
# Only applies to /company/* routes; health and static pages are exempt.
# ---------------------------------------------------------------------------
_RATE_LIMIT_REQUESTS = int(os.getenv("APP_RATE_LIMIT_REQUESTS", "200"))
_RATE_LIMIT_WINDOW   = float(os.getenv("APP_RATE_LIMIT_WINDOW_SECONDS", "60"))
_ip_windows: dict[str, collections.deque] = {}


@app.middleware("http")
async def request_logger(request: Request, call_next):
    start = time.monotonic()
    response = await call_next(request)
    elapsed = time.monotonic() - start
    logger.info("%s %s %d %.3fs", request.method, request.url.path, response.status_code, elapsed)
    return response


@app.middleware("http")
async def per_ip_rate_limit(request: Request, call_next):
    path = request.url.path
    if path.startswith("/company") or path.startswith("/feed"):
        ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window = _ip_windows.setdefault(ip, collections.deque())
        # Drop timestamps outside the window.
        while window and now - window[0] > _RATE_LIMIT_WINDOW:
            window.popleft()
        if len(window) >= _RATE_LIMIT_REQUESTS:
            retry_after = int(_RATE_LIMIT_WINDOW - (now - window[0])) + 1
            logger.warning("Rate limit hit for IP %s on %s", ip, path)
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down."},
                headers={"Retry-After": str(retry_after)},
            )
        window.append(now)
    return await call_next(request)


cors_origins_raw = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
if not cors_origins_raw:
    # Fail closed when unset. This is safer for production and still allows
    # non-browser/API-to-API usage.
    allow_origins = []
elif cors_origins_raw == "*":
    allow_origins = ["*"]
else:
    allow_origins = [o.strip() for o in cors_origins_raw.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

app.include_router(company_lookup.router)
app.include_router(financial_metrics.router)
app.include_router(segment_breakdown.router)
app.include_router(anomaly_flags.router)
app.include_router(narrative_summary.router)
app.include_router(dashboard.router)
app.include_router(feed.router)
app.include_router(analytics.router)
app.include_router(checkout.router)
app.include_router(alerts.router)
app.include_router(watchlist.router)


@app.get("/og-image.png")
def og_image():
    return FileResponse(_PUBLIC / "og-image.png", media_type="image/png")


@app.get("/")
def root():
    return FileResponse(_PUBLIC / "edgar.html")


@app.get("/edgar")
def edgar_page():
    return FileResponse(_PUBLIC / "edgar.html")


@app.get("/health")
def health():
    cache = cache_health_check()
    status = "ok" if cache["healthy"] else "degraded"
    return {"status": status, "cache": cache}


@app.exception_handler(httpx.TimeoutException)
async def handle_upstream_timeout(_request: Request, _exc: httpx.TimeoutException):
    return JSONResponse(
        status_code=504,
        content={"detail": "Upstream SEC service timed out"},
    )


@app.exception_handler(httpx.RequestError)
async def handle_upstream_request_error(_request: Request, _exc: httpx.RequestError):
    return JSONResponse(
        status_code=502,
        content={"detail": "Upstream SEC service request failed"},
    )


@app.exception_handler(httpx.HTTPStatusError)
async def handle_upstream_status_error(_request: Request, exc: httpx.HTTPStatusError):
    status_code = exc.response.status_code
    if status_code == 429:
        detail = "Upstream SEC service rate-limited the request"
        return JSONResponse(status_code=503, content={"detail": detail})

    return JSONResponse(
        status_code=502,
        content={"detail": f"Upstream SEC service returned HTTP {status_code}"},
    )
