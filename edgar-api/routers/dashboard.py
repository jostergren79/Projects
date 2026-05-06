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
from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from routers.financial_metrics import company_metrics
from routers.segment_breakdown import company_segments
from routers.anomaly_flags import company_flags
from routers.narrative_summary import company_summary

router = APIRouter()


async def _safe(coro):
    """Run a coroutine; return its result or an error dict on failure."""
    try:
        return await coro
    except Exception as exc:
        return {"error": str(exc)}


@router.get("/company/{cik}/dashboard")
async def company_dashboard(
    cik: str,
    quarters: int = Query(8, ge=1, le=20),
    debug: bool = Query(False),
):
    metrics_task  = _safe(company_metrics(cik=cik, quarters=quarters, debug=debug))
    segments_task = _safe(company_segments(cik=cik))
    flags_task    = _safe(company_flags(cik=cik))
    summary_task  = _safe(company_summary(cik=cik))

    metrics, segments, flags, summary = await asyncio.gather(
        metrics_task, segments_task, flags_task, summary_task
    )

    return {
        "cik":      cik,
        "metrics":  metrics,
        "segments": segments,
        "flags":    flags,
        "summary":  summary,
    }
