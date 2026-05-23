"""
Magic-link authentication routes.

  POST /auth/request   — email → silent Stripe verify → send magic link
  GET  /auth/verify    — token → set session cookie → redirect to /
  POST /auth/logout    — clear session cookie
  GET  /auth/whoami    — read session cookie → return tier (and confirm via Stripe)

POST /auth/request always returns {"ok": true} regardless of whether the
email matched an active subscription. That silence is intentional —
distinguishing "found" from "not found" lets an attacker enumerate paying
customers.

Environment variables:
  MAGIC_LINK_SECRET    HMAC signing key (required — fail fast on first token op)
  STRIPE_SECRET_KEY    sk_live_...
  RESEND_API_KEY       re_...
  APP_URL              https://www.edgarwolf.com — used for the magic-link URL
"""

import logging
import os
import re

import resend
import stripe
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from auth import (
    clear_session_cookie,
    mask_email,
    mint_magic_link_token,
    read_session_customer_id,
    set_session_cookie,
    verify_token,
)
from cache import get_user_email, is_digest_subscriber, upsert_user

router = APIRouter()
logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

_PRICE_IDS = {
    "pro":      os.getenv("STRIPE_PRO_PRICE_ID",      "price_1TWTJz1C3cijZqBOyfX4VwHC"),
    "pro_plus": os.getenv("STRIPE_PRO_PLUS_PRICE_ID", "price_1TVNfH1C3cijZqBOyp7Y5qJH"),
}

APP_URL = os.getenv("APP_URL", "https://www.edgarwolf.com")


def _active_tier_for_customer(customer_id: str) -> str:
    """Return 'pro_plus', 'pro', or '' for the given Stripe customer_id."""
    if not customer_id or not stripe.api_key:
        return ""
    try:
        subs = stripe.Subscription.list(
            customer=customer_id, status="active", limit=5,
            expand=["data.items.data.price"],
        )
        sub_list = subs.get("data", []) if isinstance(subs, dict) else subs.data
        for sub in sub_list:
            items = (sub.get("items", {}).get("data", []) if isinstance(sub, dict)
                     else sub.items.data)
            if not items:
                continue
            p = items[0].get("price", {}) if isinstance(items[0], dict) else items[0].price
            price_id = p.get("id", "") if isinstance(p, dict) else p.id
            if price_id == _PRICE_IDS["pro_plus"]:
                return "pro_plus"
            if price_id == _PRICE_IDS["pro"]:
                return "pro"
        return ""
    except stripe.StripeError as exc:
        logger.error("Stripe error in tier lookup: %s", exc)
        return ""


def _find_paying_customer_id(email: str) -> str:
    """Return the Stripe customer_id of an active Pro/Pro+ sub on this email,
    or "" if there isn't one.

    Uses stripe.Customer.list(email=...) instead of stripe.Customer.search(query=...)
    — the search API takes a Lucene-like query string and would let an attacker
    smuggle additional filter terms through the email field.
    """
    if not stripe.api_key:
        return ""
    try:
        customers = stripe.Customer.list(email=email, limit=10)
        cust_list = customers.get("data", []) if isinstance(customers, dict) else customers.data
        for customer in cust_list:
            customer_id = customer.get("id") if isinstance(customer, dict) else customer.id
            if _active_tier_for_customer(customer_id):
                return customer_id
        return ""
    except stripe.StripeError as exc:
        logger.error("Stripe error in customer lookup: %s", exc)
        return ""


def _send_magic_link_email(to_email: str, token: str) -> None:
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        logger.error("RESEND_API_KEY not set — cannot send magic link")
        return
    resend.api_key = api_key
    from_addr = os.getenv("RESEND_FROM", "EdgarWolf <alerts@edgarwolf.com>")
    link = f"{APP_URL}/auth/verify?token={token}"

    html = f"""
    <div style="font-family:sans-serif;max-width:560px;margin:0 auto;color:#1a1a1a">
      <h2 style="color:#2b6cb0;margin-bottom:4px">Sign in to EdgarWolf</h2>
      <p style="color:#555;line-height:1.6">
        Click the link below to access your subscription. It expires in 15 minutes.
      </p>
      <a href="{link}" style="display:inline-block;background:#2b6cb0;color:#fff;padding:10px 20px;border-radius:4px;text-decoration:none;font-size:14px;font-weight:600;margin:16px 0">
        Sign in to EdgarWolf →
      </a>
      <p style="color:#555;line-height:1.6;font-size:13px">
        If you didn't request this, you can ignore the email — no one can access
        your account without clicking the link.
      </p>
      <p style="font-size:12px;color:#aaa;margin-top:24px">
        Questions? Reply to this email or reach us at jason@edgarwolf.com.
      </p>
    </div>
    """
    try:
        resend.Emails.send({
            "from": from_addr,
            "to": [to_email],
            "subject": "Sign in to EdgarWolf",
            "html": html,
        })
        logger.info("EVENT magic_link_sent email=%s", mask_email(to_email))
    except Exception as exc:
        logger.error("Failed to send magic link to %s: %s", mask_email(to_email), exc)


@router.post("/auth/request")
async def auth_request(request: Request):
    """Send a magic-link to the email if it has an active Pro/Pro+ subscription.

    Always returns {"ok": true} so callers cannot distinguish "no such email"
    from "valid email, magic link sent". The user is told to check their inbox
    either way.
    """
    try:
        body = await request.json()
    except Exception:
        body = {}
    email = str(body.get("email", "")).strip().lower()

    if not email or len(email) > 254 or not _EMAIL_RE.match(email):
        return {"ok": True}

    customer_id = _find_paying_customer_id(email)
    if customer_id:
        token = mint_magic_link_token(customer_id)
        _send_magic_link_email(email, token)
    else:
        logger.info("EVENT auth_request_unknown email=%s", mask_email(email))

    return {"ok": True}


_LINK_EXPIRED_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Link expired — EdgarWolf</title>
  <style>
    *,*::before,*::after { box-sizing: border-box; margin: 0; padding: 0; }
    body { background:#0f1117; color:#e8eaf6; font-family:-apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
           display:flex; align-items:center; justify-content:center; min-height:100vh; text-align:center; padding:24px; }
    .card { background:#1a1d27; border:1px solid #2e3352; border-radius:12px; padding:40px; max-width:440px; width:100%; }
    h1 { font-size:1.3rem; margin-bottom:12px; }
    p { color:#8b90b8; line-height:1.6; margin-bottom:20px; }
    a { display:inline-block; background:#4f8ef7; color:#fff; border-radius:8px;
        padding:10px 24px; text-decoration:none; font-weight:600; font-size:.9rem; }
  </style>
</head>
<body>
  <div class="card">
    <h1>This sign-in link is no longer valid</h1>
    <p>Magic links expire 15 minutes after they're sent. Request a new one from the sign-in form.</p>
    <a href="/">Back to EdgarWolf</a>
  </div>
</body>
</html>"""


@router.get("/auth/verify")
async def auth_verify(token: str = ""):
    """Verify the magic-link token and set the session cookie.

    On success: 303 redirect to /?signed_in=1 with Set-Cookie.
    On failure (bad/expired token): 400 with an HTML error page.
    """
    customer_id = verify_token(token, expected_use="magic")
    if not customer_id:
        return HTMLResponse(content=_LINK_EXPIRED_HTML, status_code=400)

    # The checkout webhook only persists users.tier for self-serve checkouts,
    # so dashboard-created subs (comps/enterprise/manual) stay invisible to the
    # Pro+ alert cron until the user signs in. Upsert here. The magic-link token
    # carries only customer_id, so fetch the alert-recipient email from Stripe.
    tier = _active_tier_for_customer(customer_id)
    if tier:
        try:
            cust = stripe.Customer.retrieve(customer_id)
            email = (cust.get("email") if isinstance(cust, dict) else cust.email) or ""
        except stripe.StripeError as exc:
            logger.error("Stripe customer retrieve failed for %s: %s", customer_id, exc)
            email = ""
        if email:
            upsert_user(customer_id, email, tier)

    response = RedirectResponse(url="/?signed_in=1", status_code=303)
    set_session_cookie(response, customer_id)
    logger.info("EVENT auth_verified customer_id=%s tier=%s", customer_id, tier or "none")
    return response


@router.post("/auth/logout")
async def auth_logout():
    response = JSONResponse(content={"ok": True})
    clear_session_cookie(response)
    return response


@router.get("/auth/whoami")
async def auth_whoami(request: Request):
    """Return the current user's tier based on the session cookie.

    Re-checks the active subscription against Stripe so cancelled/lapsed
    subs are reflected immediately instead of waiting for the 30-day
    cookie to expire.
    """
    customer_id = read_session_customer_id(request)
    if not customer_id:
        return {"tier": "standard", "label": "Standard"}

    tier = _active_tier_for_customer(customer_id)
    if tier in ("pro_plus", "pro"):
        email = get_user_email(customer_id)
        digest_subscribed = is_digest_subscriber(email) if email else False
        label = "Pro+" if tier == "pro_plus" else "Pro"
        return {"tier": tier, "label": label, "digest_subscribed": digest_subscribed}

    # Cookie is valid but subscription is no longer active.
    response = JSONResponse(content={"tier": "standard", "label": "Standard"})
    clear_session_cookie(response)
    return response
