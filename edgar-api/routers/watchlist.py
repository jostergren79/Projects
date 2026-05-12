"""
Watchlist API — server-side persistence for Pro/Pro+ users.

Endpoints:
  GET    /watchlist              → fetch all items for a customer
  POST   /watchlist              → add a company
  DELETE /watchlist/{cik}        → remove a company
  POST   /watchlist/sync         → bulk-sync from localStorage (first Pro login)

Authentication: all endpoints require the X-Customer-Id header (Stripe customer ID,
e.g. cus_xxxxxxxx). The customer is validated against Stripe on first request and
the result is cached in SQLite for 1 hour — so Stripe is not hit on every call.
"""

import logging
import os

import stripe
from fastapi import APIRouter, HTTPException, Header, Request

from cache import (
    add_to_watchlist,
    get_cached_session_tier,
    get_watchlist,
    remove_from_watchlist,
    store_cached_session_tier,
    upsert_user,
)

router = APIRouter()
logger = logging.getLogger(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

_PRICE_IDS = {
    "pro":      os.getenv("STRIPE_PRO_PRICE_ID",      "price_1TVNeQ1C3cijZqBOkOX1IoJj"),
    "pro_plus": os.getenv("STRIPE_PRO_PLUS_PRICE_ID", "price_1TVNfH1C3cijZqBOyp7Y5qJH"),
}

# Cache key prefix — avoids collision with session-id keys in session_tier_cache
_CUST_PREFIX = "cust:"


def _validate_customer(customer_id: str) -> str:
    """
    Confirm the customer has an active Pro or Pro+ subscription.
    Returns the tier string. Raises 401/403/502 on failure.
    Result is cached in SQLite for 1 hour (reuses session_tier_cache table).
    """
    if not customer_id or not customer_id.startswith("cus_"):
        raise HTTPException(status_code=401, detail="X-Customer-Id header required")

    cache_key = f"{_CUST_PREFIX}{customer_id}"
    cached = get_cached_session_tier(cache_key)
    if cached:
        return cached

    if not stripe.api_key:
        # Dev mode — no Stripe key configured, accept any cus_ id
        logger.warning("No STRIPE_SECRET_KEY — skipping customer validation in dev")
        store_cached_session_tier(cache_key, "pro")
        return "pro"

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
                return "pro_plus"
            if price_id == _PRICE_IDS["pro"]:
                store_cached_session_tier(cache_key, "pro")
                return "pro"

        raise HTTPException(status_code=403, detail="No active Pro or Pro+ subscription")

    except HTTPException:
        raise
    except stripe.StripeError as exc:
        logger.error("Stripe error validating customer %s: %s", customer_id, exc)
        raise HTTPException(status_code=502, detail="Could not verify subscription")


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/watchlist")
async def watchlist_get(x_customer_id: str = Header(default="")):
    """Return all watchlist items for the authenticated customer."""
    _validate_customer(x_customer_id)
    items = get_watchlist(x_customer_id)
    return {"items": items}


@router.post("/watchlist")
async def watchlist_add(request: Request, x_customer_id: str = Header(default="")):
    """Add a company to the watchlist."""
    _validate_customer(x_customer_id)
    body = await request.json()
    cik    = str(body.get("cik",    "")).strip()
    ticker = str(body.get("ticker", "")).strip()
    name   = str(body.get("name",   "")).strip()
    if not cik:
        raise HTTPException(status_code=400, detail="cik is required")
    add_to_watchlist(x_customer_id, cik, ticker, name)
    logger.info("watchlist_add customer=%s cik=%s ticker=%s", x_customer_id, cik, ticker)
    return {"ok": True}


@router.delete("/watchlist/{cik}")
async def watchlist_remove(cik: str, x_customer_id: str = Header(default="")):
    """Remove a company from the watchlist."""
    _validate_customer(x_customer_id)
    remove_from_watchlist(x_customer_id, cik)
    logger.info("watchlist_remove customer=%s cik=%s", x_customer_id, cik)
    return {"ok": True}


@router.post("/watchlist/sync")
async def watchlist_sync(request: Request, x_customer_id: str = Header(default="")):
    """
    Bulk-sync localStorage items to the server.
    Called once when a user first signs in on a new device or after upgrading.
    Items already on the server are skipped (INSERT OR IGNORE semantics).
    Optionally accepts {email} to register the user record for future alert delivery.
    """
    _validate_customer(x_customer_id)
    body  = await request.json()
    items = body.get("items", [])
    email = str(body.get("email", "")).strip()

    if not isinstance(items, list):
        raise HTTPException(status_code=400, detail="items must be a list")

    # Register / update user email if provided
    if email:
        tier = get_cached_session_tier(f"{_CUST_PREFIX}{x_customer_id}") or "pro"
        upsert_user(x_customer_id, email, tier)

    existing_ciks = {i["cik"] for i in get_watchlist(x_customer_id)}
    synced = 0
    for item in items:
        cik = str(item.get("cik", "")).strip()
        if not cik or cik in existing_ciks:
            continue
        add_to_watchlist(
            x_customer_id,
            cik,
            str(item.get("ticker", "")).strip(),
            str(item.get("name",   "")).strip(),
        )
        synced += 1

    logger.info("watchlist_sync customer=%s synced=%d email=%s", x_customer_id, synced, email or "none")
    return {"ok": True, "synced": synced}
