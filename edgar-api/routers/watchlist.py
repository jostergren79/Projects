"""
Watchlist API — server-side persistence for Pro/Pro+ users.

Endpoints:
  GET    /watchlist              → fetch all items for the signed-in customer
  POST   /watchlist              → add a company
  DELETE /watchlist/{cik}        → remove a company
  POST   /watchlist/sync         → bulk-sync from localStorage (first Pro login)

Authentication: customer_id is read from the signed httpOnly session cookie
set by /auth/verify or /success. The Stripe subscription is verified on the
first request and the result is cached in SQLite for 60 seconds (shared with
/auth/whoami) — so Stripe is not hit on every call.

Note: /watchlist/sync no longer accepts an `email` field. The user's email
is set canonically via the Stripe webhook (checkout.session.completed); the
old email-override path was an alert-reroute attack surface.
"""

import logging
import os

import stripe
from fastapi import APIRouter, HTTPException, Request

from auth import read_session_customer_id
from cache import (
    add_to_watchlist,
    get_cached_session_tier,
    get_watchlist,
    get_watchlist_count,
    remove_from_watchlist,
    session_tier_cache_key,
    store_cached_session_tier,
)

router = APIRouter()
logger = logging.getLogger(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

_PRICE_IDS = {
    "pro":      os.getenv("STRIPE_PRO_PRICE_ID",      "price_1TWTJz1C3cijZqBOyfX4VwHC"),
    "pro_plus": os.getenv("STRIPE_PRO_PLUS_PRICE_ID", "price_1TVNfH1C3cijZqBOyp7Y5qJH"),
}

WATCHLIST_LIMIT = 50


def _require_customer(request: Request) -> str:
    """Read the signed session cookie and return the customer_id.

    Raises 401 if no cookie is present, 403 if the customer no longer has an
    active Pro/Pro+ subscription, 502 if Stripe is unreachable.
    """
    customer_id = read_session_customer_id(request)
    if not customer_id:
        raise HTTPException(status_code=401, detail="Sign in required")

    cache_key = session_tier_cache_key(customer_id)
    cached = get_cached_session_tier(cache_key)
    if cached:
        return customer_id

    if not stripe.api_key:
        logger.warning("No STRIPE_SECRET_KEY — skipping customer validation in dev")
        store_cached_session_tier(cache_key, "pro")
        return customer_id

    try:
        subs = stripe.Subscription.list(
            customer=customer_id,
            status="active",
            limit=5,
            expand=["data.items.data.price"],
        )
        sub_list = subs.get("data", []) if isinstance(subs, dict) else subs.data
        for sub in sub_list:
            items = (
                sub.get("items", {}).get("data", [])
                if isinstance(sub, dict)
                else sub.items.data
            )
            if not items:
                continue
            p = items[0].get("price", {}) if isinstance(items[0], dict) else items[0].price
            price_id = p.get("id", "") if isinstance(p, dict) else p.id
            if price_id == _PRICE_IDS["pro_plus"]:
                store_cached_session_tier(cache_key, "pro_plus")
                return customer_id
            if price_id == _PRICE_IDS["pro"]:
                store_cached_session_tier(cache_key, "pro")
                return customer_id

        raise HTTPException(status_code=403, detail="No active Pro or Pro+ subscription")

    except HTTPException:
        raise
    except stripe.StripeError as exc:
        logger.error("Stripe error validating customer %s: %s", customer_id, exc)
        raise HTTPException(status_code=502, detail="Could not verify subscription")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/watchlist")
async def watchlist_get(request: Request):
    """Return all watchlist items for the authenticated customer."""
    customer_id = _require_customer(request)
    items = get_watchlist(customer_id)
    return {"items": items, "count": len(items), "limit": WATCHLIST_LIMIT}


@router.post("/watchlist")
async def watchlist_add(request: Request):
    """Add a company to the watchlist."""
    customer_id = _require_customer(request)
    body = await request.json()
    cik    = str(body.get("cik",    "")).strip()
    ticker = str(body.get("ticker", "")).strip()
    name   = str(body.get("name",   "")).strip()
    if not cik:
        raise HTTPException(status_code=400, detail="cik is required")
    if get_watchlist_count(customer_id) >= WATCHLIST_LIMIT:
        raise HTTPException(
            status_code=422,
            detail=f"Watchlist limit of {WATCHLIST_LIMIT} companies reached. Contact support to increase.",
        )
    add_to_watchlist(customer_id, cik, ticker, name)
    logger.info("watchlist_add customer=%s cik=%s ticker=%s", customer_id, cik, ticker)
    return {"ok": True}


@router.delete("/watchlist/{cik}")
async def watchlist_remove(cik: str, request: Request):
    """Remove a company from the watchlist."""
    customer_id = _require_customer(request)
    remove_from_watchlist(customer_id, cik)
    logger.info("watchlist_remove customer=%s cik=%s", customer_id, cik)
    return {"ok": True}


@router.post("/watchlist/sync")
async def watchlist_sync(request: Request):
    """Bulk-sync localStorage items to the server.

    Called once when a user first signs in on a new device or after upgrading.
    Items already on the server are skipped (INSERT OR IGNORE semantics).

    The user's email is NOT taken from the request body — it is set canonically
    by the Stripe webhook on checkout.session.completed.
    """
    customer_id = _require_customer(request)
    body  = await request.json()
    items = body.get("items", [])

    if not isinstance(items, list):
        raise HTTPException(status_code=400, detail="items must be a list")

    existing_ciks = {i["cik"] for i in get_watchlist(customer_id)}
    synced = 0
    for item in items:
        cik = str(item.get("cik", "")).strip()
        if not cik or cik in existing_ciks:
            continue
        add_to_watchlist(
            customer_id,
            cik,
            str(item.get("ticker", "")).strip(),
            str(item.get("name",   "")).strip(),
        )
        synced += 1

    logger.info("watchlist_sync customer=%s synced=%d", customer_id, synced)
    return {"ok": True, "synced": synced}
