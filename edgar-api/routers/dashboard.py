"""
dashboard.py — aggregated company dashboard endpoint.

GET /company/{cik}/dashboard

Returns metrics, segments, flags, and summary in a single response by
running all four fetches concurrently.  The in-flight deduplication in
edgar_client ensures that even when all four coroutines race to fetch the
same companyfacts payload, only one upstream SEC request goes out.

This reduces browser-to-server round trips from 4-5 parallel calls to 1,
improving perceived load time and reducing error-handling complexity on
the frontend.
"""

import asyncio
import logging
import re
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from routers.financial_metrics import company_metrics
from routers.segment_breakdown import company_segments
from routers.anomaly_flags import company_flags
from routers.company_lookup import company_anomalies
from routers.narrative_summary import company_summary

router = APIRouter()
logger = logging.getLogger(__name__)


def _is_error(result) -> bool:
    return isinstance(result, dict) and "error" in result


async def _safe(label: str, coro):
    """Run a coroutine; return its result or an error dict on failure."""
    try:
        return await coro
    except Exception as exc:
        logger.warning("Dashboard sub-call '%s' failed: %s", label, exc)
        return {"error": str(exc)}


@router.get("/company/{cik}/dashboard")
async def company_dashboard(
    cik: str,
    quarters: int = Query(8, ge=1, le=20),
    debug: bool = Query(False),
):
    if not re.match(r"^\d{1,10}$", cik.strip()):
        raise HTTPException(status_code=400, detail=f"Invalid CIK '{cik}': must be 1–10 digits")

    logger.info("Dashboard request for CIK %s", cik)

    metrics, segments, flags, summary, anomalies = await asyncio.gather(
        _safe("metrics",   company_metrics(cik=cik, quarters=quarters, debug=debug)),
        _safe("segments",  company_segments(cik=cik)),
        _safe("flags",     company_flags(cik=cik)),
        _safe("summary",   company_summary(cik=cik)),
        _safe("anomalies", company_anomalies(cik=cik)),
    )

    results = [metrics, segments, flags, summary, anomalies]
    error_count = sum(1 for r in results if _is_error(r))
    has_errors = error_count > 0

    if has_errors:
        logger.warning("Dashboard for CIK %s completed with %d partial error(s)", cik, error_count)

    return JSONResponse(
        status_code=207 if has_errors else 200,
        content={
            "cik":         cik,
            "metrics":     metrics,
            "segments":    segments,
            "flags":       flags,
            "summary":     summary,
            "anomalies":   anomalies,
            "has_errors":  has_errors,
            "error_count": error_count,
        },
    )
