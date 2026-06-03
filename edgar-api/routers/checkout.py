"""
Stripe Checkout integration.

POST /checkout/session      — creates a hosted Stripe Checkout session and returns
                              the redirect URL. Called by the frontend upgrade buttons.

GET  /success               — Stripe redirects here after a successful payment.
                              Looks up the checkout session, sets the magic-link
                              session cookie, and renders the welcome page.

POST /webhook/stripe        — receives Stripe webhook events. Persists the user
                              record on checkout.session.completed and triggers
                              the welcome email.

POST /billing/portal        — opens the Stripe Customer Portal. Reads the
                              authenticated customer_id from the session cookie.

Environment variables required (set in Railway Variables panel, never in code):
  STRIPE_SECRET_KEY        sk_live_...
  STRIPE_WEBHOOK_SECRET    whsec_...
  STRIPE_PRO_PRICE_ID      price_1TWTJz1C3cijZqBOyfX4VwHC   ($19.00/mo)
  STRIPE_PRO_PLUS_PRICE_ID price_1TVNfH1C3cijZqBOyp7Y5qJH   ($99/mo)
"""

import json as _json
import logging
import os
import stripe
import resend
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from auth import mask_email, read_session_customer_id, set_session_cookie
from cache import upsert_user

router = APIRouter()
logger = logging.getLogger(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

PRICE_IDS = {
    "pro":      os.getenv("STRIPE_PRO_PRICE_ID",      "price_1TWTJz1C3cijZqBOyfX4VwHC"),
    "pro_plus": os.getenv("STRIPE_PRO_PLUS_PRICE_ID", "price_1TVNfH1C3cijZqBOyp7Y5qJH"),
}

APP_URL = os.getenv("APP_URL", "https://www.edgarwolf.com")


def _tier_from_price_id(price_id: str) -> str:
    if price_id == PRICE_IDS["pro_plus"]:
        return "pro_plus"
    if price_id == PRICE_IDS["pro"]:
        return "pro"
    return ""


@router.post("/checkout/session")
async def create_checkout_session(request: Request):
    body = await request.json()
    tier = body.get("tier", "")

    if tier not in PRICE_IDS:
        raise HTTPException(status_code=400, detail=f"Unknown tier '{tier}'")

    if not stripe.api_key:
        raise HTTPException(status_code=503, detail="Payments not configured")

    try:
        session = stripe.checkout.Session.create(
            mode="subscription",
            line_items=[{"price": PRICE_IDS[tier], "quantity": 1}],
            success_url=f"{APP_URL}/success?session_id={{CHECKOUT_SESSION_ID}}&tier={tier}",
            cancel_url=f"{APP_URL}/?upgrade=cancelled",
            allow_promotion_codes=True,
            metadata={"tier": tier},
        )
        logger.info("Checkout session created for tier=%s session=%s", tier, session.id)
        return {"url": session.url}
    except stripe.StripeError as e:
        logger.error("Stripe error creating checkout session: %s", e)
        raise HTTPException(status_code=502, detail="Failed to create checkout session")


@router.post("/billing/portal")
async def billing_portal(request: Request):
    """Create a Stripe Customer Portal session.

    The customer_id is read from the authenticated session cookie — never
    from the request body — so a third party cannot open the portal for an
    arbitrary customer.
    """
    customer_id = read_session_customer_id(request)
    if not customer_id:
        raise HTTPException(status_code=401, detail="Sign in required")
    if not stripe.api_key:
        raise HTTPException(status_code=503, detail="Payments not configured")
    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=f"{APP_URL}/",
        )
        return {"url": session.url}
    except stripe.StripeError as e:
        logger.error("Stripe portal error for customer %s: %s", customer_id, e)
        raise HTTPException(status_code=502, detail="Failed to create portal session")


def _send_welcome_email(to_email: str, tier: str) -> None:
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        logger.warning("RESEND_API_KEY not set — skipping welcome email")
        return

    resend.api_key = api_key
    from_addr = os.getenv("RESEND_FROM", "EdgarWolf <alerts@edgarwolf.com>")
    tier_label = "Pro+" if tier == "pro_plus" else "Pro"

    pro_plus_section = ""
    if tier == "pro_plus":
        pro_plus_section = """
      <div style="background:#162a1e;border:1px solid #276749;border-radius:8px;padding:16px 20px;margin:20px 0">
        <p style="margin:0 0 8px;font-weight:700;color:#34d399">Email Alerts — Active</p>
        <p style="margin:0;color:#555;font-size:13px;line-height:1.6">
          You'll receive an email whenever a company on your watchlist files a 10-Q, 10-K, or 8-K
          <em>and</em> EdgarWolf detects an anomaly signal. Alerts run hourly Monday–Friday, 8 AM–6 PM ET.
        </p>
      </div>"""

    html = f"""
    <div style="font-family:sans-serif;max-width:560px;margin:0 auto;color:#1a1a1a">
      <h2 style="color:#2b6cb0;margin-bottom:4px">Welcome to EdgarWolf {tier_label}</h2>
      <p style="color:#555;line-height:1.6">
        Your subscription is active. Here's what you now have access to:
      </p>
      <ul style="color:#555;line-height:1.8;padding-left:20px">
        <li>Exception flags — z-score deviations on margins and revenue</li>
        <li>Filing Stress Score — composite filing anomaly signal (0–100)</li>
        <li>Filing Signals — cadence and XBRL anomalies</li>
        <li>Peer comparison, segment breakdown, source filing links</li>
        <li>Server-synced watchlist + CSV/JSON export</li>
      </ul>
      {pro_plus_section}
      <a href="https://www.edgarwolf.com" style="display:inline-block;background:#2b6cb0;color:#fff;padding:10px 20px;border-radius:4px;text-decoration:none;font-size:14px;font-weight:600;margin-top:8px">
        Go to EdgarWolf →
      </a>
      <p style="font-size:12px;color:#aaa;margin-top:24px">
        Questions? Reply to this email or reach us at jason@edgarwolf.com.
      </p>
    </div>
    """

    try:
        resend.Emails.send({
            "from": from_addr,
            "to": [to_email],
            "subject": f"Welcome to EdgarWolf {tier_label}",
            "html": html,
        })
        logger.info("EVENT welcome_email_sent email=%s tier=%s", mask_email(to_email), tier)
    except Exception as e:
        logger.error("Failed to send welcome email to %s: %s", mask_email(to_email), e)


def _sync_subscription(sub, trigger: str) -> None:
    """Upsert a user record from an active Stripe subscription object.

    Used by subscription.created and subscription.updated webhooks to handle
    dashboard-provisioned subs that never go through checkout.session.completed.
    No welcome email is sent — checkout.session.completed owns that.
    """
    customer_id = sub.get("customer", "")
    items = sub.get("items", {}).get("data", [])
    if not customer_id or not items:
        return
    price_id = (items[0].get("price") or {}).get("id", "")
    tier = _tier_from_price_id(price_id)
    if not tier:
        return
    try:
        customer = stripe.Customer.retrieve(customer_id)
        email = customer.get("email", "") if isinstance(customer, dict) else customer.email
    except stripe.StripeError as exc:
        logger.error("Stripe error fetching customer=%s for %s: %s", customer_id, trigger, exc)
        return
    if not email:
        return
    try:
        upsert_user(customer_id, email, tier)
        logger.info("EVENT subscription_synced trigger=%s customer=%s tier=%s", trigger, customer_id, tier)
    except Exception as exc:
        logger.error("upsert_user failed for customer=%s: %s", customer_id, exc)


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    if not webhook_secret:
        logger.error("STRIPE_WEBHOOK_SECRET not configured — rejecting webhook")
        raise HTTPException(status_code=500, detail="Webhook not configured")

    try:
        event = stripe.Webhook.construct_event(payload, sig, webhook_secret)
    except stripe.SignatureVerificationError:
        logger.warning("Stripe webhook signature verification failed")
        raise HTTPException(status_code=400, detail="Invalid signature")

    if event.type == "checkout.session.completed":
        session = event.data.object
        customer_email = session.get("customer_details", {}).get("email", "")
        customer_id = session.get("customer", "")
        tier = session.get("metadata", {}).get("tier", "unknown")
        amount = session.get("amount_total", 0)
        logger.info(
            "EVENT subscription_started email=%s tier=%s amount=%s session=%s customer=%s",
            mask_email(customer_email), tier, amount, session.get("id"), customer_id,
        )

        if customer_id and customer_email and tier in ("pro", "pro_plus"):
            # Webhook is the canonical place to persist the user record.
            # /watchlist/sync no longer accepts an email override.
            try:
                upsert_user(customer_id, customer_email, tier)
            except Exception as exc:
                logger.error("upsert_user failed for customer=%s: %s", customer_id, exc)
            _send_welcome_email(customer_email, tier)

    elif event.type in ("customer.subscription.created", "customer.subscription.updated"):
        sub = event.data.object
        prev = event.data.get("previous_attributes") or {}
        status = sub.get("status", "")
        # For .created: sync any active sub (catches dashboard-provisioned subs).
        # For .updated: only re-sync when status or items (tier) actually changed.
        if status == "active" and (
            event.type == "customer.subscription.created"
            or "status" in prev
            or "items" in prev
        ):
            _sync_subscription(sub, event.type)

    elif event.type == "customer.subscription.deleted":
        sub = event.data.object
        logger.info("EVENT subscription_cancelled customer=%s", sub.get("customer"))

    elif event.type == "invoice.payment_failed":
        invoice = event.data.object
        logger.warning("EVENT payment_failed customer=%s", invoice.get("customer"))

    return {"ok": True}


def _script_safe_json(value: str) -> str:
    """Encode a value for safe interpolation inside an HTML <script> block.

    json.dumps alone is not sufficient: it does not escape '<' or '>', so a
    string containing '</script>' will end the script tag and allow HTML
    injection. We additionally escape '<', '>', and '&' as Unicode sequences
    — JavaScript decodes these back to the original characters inside string
    literals, but the HTML parser sees them as inert data.
    """
    return (
        _json.dumps(value)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
    )


def _resolve_session_customer(session_id: str) -> tuple[str, str]:
    """Look up a Stripe checkout session and return (customer_id, tier).

    Returns ("", "") if the session is missing, not paid, or Stripe is down.
    Used by /success to set the auth cookie after a successful checkout.
    """
    if not session_id or not stripe.api_key:
        return "", ""
    try:
        session = stripe.checkout.Session.retrieve(
            session_id,
            expand=["subscription", "subscription.items.data.price"],
        )
        status = session.get("status") if isinstance(session, dict) else session.status
        if status != "complete":
            return "", ""
        customer_id = session.get("customer") if isinstance(session, dict) else session.customer
        sub = session.get("subscription") if isinstance(session, dict) else session.subscription
        if not customer_id or sub is None:
            return "", ""
        sub_status = sub.get("status") if isinstance(sub, dict) else sub.status
        if sub_status != "active":
            return "", ""
        items = (sub.get("items", {}).get("data", []) if isinstance(sub, dict)
                 else sub.items.data)
        if not items:
            return customer_id, ""
        p = items[0].get("price", {}) if isinstance(items[0], dict) else items[0].price
        price_id = p.get("id", "") if isinstance(p, dict) else p.id
        return customer_id, _tier_from_price_id(price_id)
    except stripe.StripeError as exc:
        logger.error("Stripe error in /success session lookup: %s", exc)
        return "", ""


@router.get("/success")
async def payment_success(session_id: str = "", tier: str = "pro"):
    """Stripe redirects here after a successful payment.

    On a valid completed session, sets the httpOnly session cookie containing
    the customer_id. The frontend then calls /auth/whoami to recover tier on
    subsequent loads — no client-side customer_id storage required.
    """
    if tier not in ("pro", "pro_plus"):
        tier = "pro"
    tier_label = "Pro+" if tier == "pro_plus" else "Pro"

    customer_id, verified_tier = _resolve_session_customer(session_id)
    if verified_tier in ("pro", "pro_plus"):
        tier = verified_tier
        tier_label = "Pro+" if tier == "pro_plus" else "Pro"

    # Only signal a conversion to analytics when Stripe has verified the checkout
    # session as complete with an *active* subscription. This excludes comps and
    # trials (not "active") and unverified loads, so the frontend's
    # subscription_success event reflects genuine paid conversions only.
    conversion_js = (
        f"localStorage.setItem('edgarwolf_pending_conversion', {_script_safe_json(tier)});"
        if verified_tier in ("pro", "pro_plus") else ""
    )

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Welcome to EdgarWolf {tier_label}</title>
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: #0f1117; color: #e8eaf6; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
           display: flex; align-items: center; justify-content: center; min-height: 100vh; text-align: center; padding: 24px; }}
    .card {{ background: #1a1d27; border: 1px solid #2e3352; border-radius: 12px; padding: 48px 40px; max-width: 460px; width: 100%; }}
    h1 {{ font-size: 1.6rem; font-weight: 700; margin-bottom: 12px; }}
    .check {{ font-size: 3rem; margin-bottom: 20px; }}
    p {{ color: #8b90b8; line-height: 1.6; margin-bottom: 24px; }}
    .tier {{ display: inline-block; background: #162a1e; color: #34d399; border: 1px solid #34d399;
             border-radius: 999px; padding: 4px 14px; font-size: .85rem; font-weight: 700; margin-bottom: 20px; }}
    a {{ display: inline-block; background: #4f8ef7; color: #fff; border-radius: 8px;
         padding: 12px 28px; text-decoration: none; font-weight: 600; font-size: .95rem; }}
    a:hover {{ filter: brightness(1.1); }}
  </style>
  <script>
    localStorage.setItem('edgarwolf_tier', {_script_safe_json(tier)});
    localStorage.setItem('edgarwolf_tier_label', {_script_safe_json(tier_label)});
    {conversion_js}
  </script>
</head>
<body>
  <div class="card">
    <div class="check">&#10003;</div>
    <div class="tier">{tier_label}</div>
    <h1>You're all set!</h1>
    <p>Your EdgarWolf {tier_label} subscription is active. Thank you for supporting the product.</p>
    <a href="/">Go to EdgarWolf</a>
  </div>
</body>
</html>"""

    response = HTMLResponse(content=html)
    if customer_id:
        set_session_cookie(response, customer_id)
    return response
