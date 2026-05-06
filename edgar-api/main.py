"""
edgar-api — main FastAPI application
Routes:
  GET /company?ticker=AAPL         → CIK lookup + company metadata
  GET /company/{cik}/metrics       → 8-quarter financial metrics
  GET /company/{cik}/segments      → segment revenue breakdown
  GET /company/{cik}/flags         → exception flags (metrics outside historical norms)
"""

from fastapi import FastAPI
from fastapi import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import httpx
import os

from routers import (
    company_lookup,
    financial_metrics,
    segment_breakdown,
    anomaly_flags,
    narrative_summary,
)

app = FastAPI(title="EDGAR Financial Metrics API", version="0.1.0")

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
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(company_lookup.router)
app.include_router(financial_metrics.router)
app.include_router(segment_breakdown.router)
app.include_router(anomaly_flags.router)
app.include_router(narrative_summary.router)


@app.get("/health")
def health():
    return {"status": "ok"}


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
