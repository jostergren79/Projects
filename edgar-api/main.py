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

import io
import logging
import collections
import os
import pathlib
import re
import time
from contextlib import asynccontextmanager

from dotenv import load_dotenv
load_dotenv()

import sentry_sdk
_sentry_dsn = os.getenv("SENTRY_DSN", "")
if _sentry_dsn:
    sentry_sdk.init(
        dsn=_sentry_dsn,
        traces_sample_rate=0.1,
        send_default_pii=False,
    )
    logging.getLogger(__name__).info("Sentry error monitoring enabled")

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

# Resolve the frontend directory.
# Repo layout: edgar-api/ and edgar-frontend/ are siblings at the repo root.
# __file__ = <repo-root>/edgar-api/main.py → parent.parent = repo root.
_PUBLIC = pathlib.Path(__file__).parent.parent / "edgar-frontend"

from cache import cache_health_check
from scheduler import alert_scheduler


@asynccontextmanager
async def lifespan(app: FastAPI):
    alert_scheduler.start()
    logger.info("Alert scheduler started — Pro+ filing alerts active M-F 08:00-18:00 ET")
    yield
    alert_scheduler.shutdown(wait=False)
    logger.info("Alert scheduler stopped")


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
    digest,
    auth_router,
)

app = FastAPI(title="EDGAR Financial Metrics API", version="1.7.5", lifespan=lifespan)

# ---------------------------------------------------------------------------
# Per-IP rate limiting middleware
# Sliding window: max N requests per IP per window_seconds.
# Configurable via env: APP_RATE_LIMIT_REQUESTS, APP_RATE_LIMIT_WINDOW_SECONDS.
# Only applies to /company/* routes; health and static pages are exempt.
# ---------------------------------------------------------------------------
_RATE_LIMIT_REQUESTS = int(os.getenv("APP_RATE_LIMIT_REQUESTS", "200"))
_RATE_LIMIT_WINDOW   = float(os.getenv("APP_RATE_LIMIT_WINDOW_SECONDS", "60"))
_ip_windows: dict[str, collections.deque] = {}
_cleanup_counter = 0
_CLEANUP_INTERVAL = 10_000

# Paths subject to per-IP rate limiting.
_RATE_LIMITED_PREFIXES = ("/company", "/feed")
_RATE_LIMITED_EXACT    = {"/digest/subscribe", "/auth/request", "/auth/verify"}


@app.middleware("http")
async def request_logger(request: Request, call_next):
    start = time.monotonic()
    response = await call_next(request)
    elapsed = time.monotonic() - start
    logger.info("%s %s %d %.3fs", request.method, request.url.path, response.status_code, elapsed)
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Strict-Transport-Security"] = "max-age=63072000; includeSubDomains"
    return response


@app.middleware("http")
async def per_ip_rate_limit(request: Request, call_next):
    global _cleanup_counter
    path = request.url.path
    rate_limited = any(path.startswith(p) for p in _RATE_LIMITED_PREFIXES) or path in _RATE_LIMITED_EXACT
    if rate_limited:
        ip = request.client.host if request.client else "unknown"
        now = time.monotonic()
        window = _ip_windows.setdefault(ip, collections.deque())
        # Drop timestamps outside the window.
        while window and now - window[0] > _RATE_LIMIT_WINDOW:
            window.popleft()
        if not window:
            _ip_windows.pop(ip, None)
            window = _ip_windows.setdefault(ip, collections.deque())
        if len(window) >= _RATE_LIMIT_REQUESTS:
            retry_after = int(_RATE_LIMIT_WINDOW - (now - window[0])) + 1
            logger.warning("Rate limit hit for IP %s on %s", ip, path)
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests. Please slow down."},
                headers={"Retry-After": str(retry_after)},
            )
        window.append(now)
        # Periodically evict IPs whose last request was over two windows ago.
        _cleanup_counter += 1
        if _cleanup_counter >= _CLEANUP_INTERVAL:
            _cleanup_counter = 0
            cutoff = now - _RATE_LIMIT_WINDOW * 2
            stale = [k for k, v in list(_ip_windows.items()) if not v or v[-1] < cutoff]
            for k in stale:
                _ip_windows.pop(k, None)
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
app.include_router(digest.router)
app.include_router(auth_router.router)


@app.get("/.well-known/cf-custom-hostname-challenge/{token}")
def cf_hostname_challenge(token: str):
    """Cloudflare custom hostname HTTP verification — must return token as plain text."""
    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(token)


@app.get("/config.js")
def config_js():
    """Public client-side config: exposes the PostHog project key (safe by design)
    from the POSTHOG_KEY env var. Returns an empty key when unset so PostHog
    init becomes a no-op (useful for local dev).

    Cache-Control: no-store — config values must reflect env var changes
    immediately. Without this header Cloudflare caches the file for 4 hours
    by default, which causes stale config to be served after an env var update.
    """
    import json as _json
    from fastapi.responses import Response
    key = os.getenv("POSTHOG_KEY", "")
    body = f"window.POSTHOG_KEY = {_json.dumps(key)};"
    return Response(
        content=body,
        media_type="application/javascript",
        headers={"Cache-Control": "no-store, max-age=0"},
    )


# ---------------------------------------------------------------------------
# Dynamic OG image generation
# ---------------------------------------------------------------------------
_og_cache: dict = {}               # cik10 → PNG bytes
_OG_CACHE_MAX = 500
_html_content = None               # cached edgar.html text


async def _fetch_company_og_info(cik: str):
    """Return (name, ticker) for a CIK via the lightweight EDGAR submissions endpoint."""
    try:
        cik10 = cik.zfill(10)
        url = f"https://data.sec.gov/submissions/CIK{cik10}.json"
        async with httpx.AsyncClient(timeout=5.0) as client:
            r = await client.get(url, headers={"User-Agent": "EdgarWolf contact@edgarwolf.com"})
        if r.status_code != 200:
            return None
        data = r.json()
        name = data.get("name", "")
        tickers = data.get("tickers", [])
        ticker = tickers[0] if tickers else ""
        return name, ticker
    except Exception:
        return None


def _build_og_image(name: str, ticker: str, cik10: str) -> bytes:
    """Generate a 1200×630 branded OG image with Pillow."""
    from PIL import Image, ImageDraw, ImageFont

    W, H = 1200, 630
    BG      = (15,  17,  23)   # --bg
    SURFACE = (26,  29,  39)   # --surface
    ACCENT  = (79,  142, 247)  # --accent
    TEXT    = (232, 234, 246)  # --text
    MUTED   = (139, 144, 184)  # --muted
    BORDER  = (46,  51,  82)   # --border

    def _font(size: int, bold: bool = True) -> ImageFont.ImageFont:
        candidates = [
            f"/usr/share/fonts/truetype/dejavu/DejaVuSans-{'Bold' if bold else ''}.ttf",
            f"/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-{'Bold' if bold else ''}.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
        ]
        for p in candidates:
            if os.path.exists(p):
                try:
                    return ImageFont.truetype(p, size)
                except Exception:
                    pass
        return ImageFont.load_default(size=size)

    img  = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Top bar
    draw.rectangle([(0, 0), (W, 72)], fill=SURFACE)
    draw.line([(0, 72), (W, 72)], fill=BORDER, width=1)
    draw.text((48, 22), "EdgarWolf", font=_font(28), fill=ACCENT)
    draw.text((W - 48, 26), "SEC filing anomaly detection", font=_font(18, bold=False), fill=MUTED, anchor="ra")

    # Company name + ticker
    display_name = (name[:42] + "...") if len(name) > 42 else name
    draw.text((48, 130), display_name, font=_font(54), fill=TEXT)
    if ticker:
        draw.text((48, 206), f"${ticker}", font=_font(40), fill=ACCENT)

    # Divider
    draw.line([(48, 280), (W - 48, 280)], fill=BORDER, width=1)

    # Tagline block
    draw.text((48, 308), "Know what's in the filing before the market does.", font=_font(28), fill=TEXT)
    draw.text((48, 358), "Z-score anomaly flags  ·  Filing Stress Scores  ·  8-quarter trends", font=_font(19, bold=False), fill=MUTED)

    # Bottom bar
    draw.rectangle([(0, H - 60), (W, H)], fill=SURFACE)
    draw.line([(0, H - 60), (W, H - 60)], fill=BORDER, width=1)
    draw.text((48, H - 30), f"edgarwolf.com/?cik={cik10}", font=_font(19, bold=False), fill=ACCENT, anchor="lm")

    buf = io.BytesIO()
    img.save(buf, "PNG", optimize=True)
    return buf.getvalue()


async def _serve_cik_html(cik: str):
    """Return HTMLResponse with dynamic OG tags for the given CIK."""
    import html as _html
    from fastapi.responses import HTMLResponse

    global _html_content
    if _html_content is None:
        _html_content = (_PUBLIC / "edgar.html").read_text(encoding="utf-8")

    info = await _fetch_company_og_info(cik)
    if not info:
        return FileResponse(_PUBLIC / "edgar.html")

    name, ticker = info
    cik10  = cik.zfill(10)
    label  = f"{_html.escape(name)} ({_html.escape(ticker)})" if ticker else _html.escape(name)
    og_title = f"{label} — EdgarWolf Filing Analysis"
    og_desc  = f"Z-score anomaly flags, Filing Stress Score, and 8-quarter trends for {_html.escape(name)} from SEC EDGAR."
    og_image = f"https://www.edgarwolf.com/og/{cik10}.png"
    og_url   = f"https://www.edgarwolf.com/?cik={cik10}"

    page = _html_content
    page = re.sub(r'(<meta property="og:url"\s+content=")[^"]*(")', rf'\g<1>{og_url}\g<2>', page)
    page = re.sub(r'(<meta property="og:title"\s+content=")[^"]*(")', rf'\g<1>{og_title}\g<2>', page)
    page = re.sub(r'(<meta property="og:description"\s+content=")[^"]*(")', rf'\g<1>{og_desc}\g<2>', page)
    page = re.sub(r'(<meta property="og:image"\s+content=")[^"]*(")', rf'\g<1>{og_image}\g<2>', page)
    page = re.sub(r'(<meta name="twitter:title"\s+content=")[^"]*(")', rf'\g<1>{og_title}\g<2>', page)
    page = re.sub(r'(<meta name="twitter:description"\s+content=")[^"]*(")', rf'\g<1>{og_desc}\g<2>', page)
    page = re.sub(r'(<meta name="twitter:image"\s+content=")[^"]*(")', rf'\g<1>{og_image}\g<2>', page)

    return HTMLResponse(content=page)


@app.get("/og/{cik}.png")
async def og_image_for_cik(cik: str):
    from fastapi.responses import Response
    cik10 = cik.removesuffix(".png").zfill(10)
    if cik10 not in _og_cache:
        info = await _fetch_company_og_info(cik10)
        if not info:
            return FileResponse(_PUBLIC / "og-image.png", media_type="image/png")
        name, ticker = info
        png = _build_og_image(name, ticker, cik10)
        if len(_og_cache) >= _OG_CACHE_MAX:
            _og_cache.pop(next(iter(_og_cache)))
        _og_cache[cik10] = png
    return Response(
        content=_og_cache[cik10],
        media_type="image/png",
        headers={"Cache-Control": "public, max-age=3600"},
    )


@app.get("/og-image.png")
def og_image():
    return FileResponse(_PUBLIC / "og-image.png", media_type="image/png")

@app.get("/sitemap.xml")
def sitemap():
    return FileResponse(_PUBLIC / "sitemap.xml", media_type="application/xml")

@app.get("/robots.txt")
def robots():
    return FileResponse(_PUBLIC / "robots.txt", media_type="text/plain")

@app.get("/favicon.ico")
def favicon_ico():
    return FileResponse(_PUBLIC / "favicon-32.png", media_type="image/png")

@app.get("/favicon.png")
def favicon():
    return FileResponse(_PUBLIC / "favicon.png", media_type="image/png")

@app.get("/favicon-32.png")
def favicon_32():
    return FileResponse(_PUBLIC / "favicon-32.png", media_type="image/png")


@app.get("/")
async def root(cik: str = None):
    if cik:
        return await _serve_cik_html(cik)
    return FileResponse(_PUBLIC / "edgar.html")


@app.get("/edgar")
async def edgar_page(cik: str = None):
    if cik:
        return await _serve_cik_html(cik)
    return FileResponse(_PUBLIC / "edgar.html")


@app.get("/privacy")
def privacy_page():
    return FileResponse(_PUBLIC / "privacy.html")


@app.get("/terms")
def terms_page():
    return FileResponse(_PUBLIC / "terms.html")


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
