"""
POST /analytics/event

Fire-and-forget event logging for usage analytics.
Events are emitted as structured JSON log lines — queryable in Render's log stream
via: grep '"EVENT"' or filter by logger name 'routers.analytics'.

No PII is stored. Only event names and public company identifiers.
"""

import json
import logging
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

router = APIRouter()
logger = logging.getLogger(__name__)

_ALLOWED_EVENTS = {
    "page_view",
    "search",
    "company_view",
    "signal_board_click",
    "signal_board_skip",
    "watchlist_add",
    "export",
    "upgrade_modal_open",
    "checkout_start",
    "pro_gate_hit",
}


@router.post("/analytics/event", include_in_schema=False)
async def log_event(request: Request):
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"ok": False})

    event = str(body.get("event", "")).strip()
    if not event or event not in _ALLOWED_EVENTS:
        return JSONResponse(status_code=400, content={"ok": False})

    props = body.get("props") or {}
    if not isinstance(props, dict):
        props = {}
    # Keep only scalar values; reject anything that could be PII.
    safe = {k: v for k, v in props.items()
            if isinstance(v, (str, int, float, bool)) and len(str(v)) < 256}

    logger.info("EVENT %s %s", event, json.dumps(safe))
    return {"ok": True}
