"""
GET /feed/recent
Returns companies that recently filed 10-Q or 10-K with SEC EDGAR.
Used by the frontend signal board to discover fresh filers for trend scoring.
"""

import logging
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query
from edgar_client import fetch_recent_filers

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/feed/recent")
async def recent_filers(
    days:  int = Query(14, ge=1, le=90,  description="Look-back window in calendar days"),
    limit: int = Query(30, ge=1, le=100, description="Maximum companies to return"),
):
    logger.info("Feed request: days=%d limit=%d", days, limit)
    try:
        filings = await fetch_recent_filers(days=days, limit=limit)
    except Exception as exc:
        logger.error("Feed fetch failed: %s", exc)
        raise HTTPException(status_code=502, detail=f"Feed fetch failed: {exc}")

    return {
        "filings":      filings,
        "count":        len(filings),
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
