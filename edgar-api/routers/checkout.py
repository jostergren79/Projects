"""
Stripe Checkout integration.

POST /checkout/session      — creates a hosted Stripe Checkout session and returns
                              the redirect URL. Called by the frontend upgrade buttons.

GET  /subscription/status   — verifies a Stripe session ID against the live Stripe API
                              and returns the user's active tier. Cached client-side.

POST /webhook/stripe        — receives Stripe webhook events. Logs completed
                              subscriptions for analytics and future email alerts.

Environment variables required (set in Railway Variables panel, never in code):
  STRIPE_SECRET_KEY       sk_live_...
  STRIPE_WEBHOOK_SECRET   whsec_...  (from Stripe dashboard → Webhooks)
  STRIPE_PRO_PRICE_ID     price_1TWTJz1C3cijZqBOyfX4VwHC   ($19.00/mo)
  STRIPE_PRO_PLUS_PRICE_ID price_1TVNfH1C3cijZqBOyp7Y5qJH  ($99/mo)
"""

import logging
import os
import stripe
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

router = APIRouter()
logger = logging.getLogger(__name__)

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

PRICE_IDS = {
    "pro":      os.getenv("STRIPE_PRO_PRICE_ID",      "price_1TWTJz1C3cijZqBOyfX4VwHC"),
    "pro_plus": os.getenv("STRIPE_PRO_PLUS_PRICE_ID", "price_1TVNfH1C3cijZqBOyp7Y5qJH"),
}

APP_URL = os.getenv("APP_URL", "https://www.edgarwolf.com")


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
        )
        logger.info("Checkout session created for tier=%s session=%s", tier, session.id)
        return {"url": session.url}
    except stripe.StripeError as e:
        logger.error("Stripe error creating checkout session: %s", e)
        raise HTTPException(status_code=502, detail="Failed to create checkout session")


@router.get("/subscription/status")
async def subscription_status(session_id: str = ""):
    """
    Verify a Stripe checkout session and return the active subscription tier.
    Returns {"tier": "standard"|"pro"|"pro_plus", "label": "Standard"|"Pro"|"Pro+"}.
    """
    if not session_id or not stripe.api_key:
        return {"tier": "standard", "label": "Standard"}

    try:
        session = stripe.checkout.Session.retrieve(
            session_id,
            expand=["subscription", "subscription.items.data.price"],
        )
        sub = session.get("subscription") if isinstance(session, dict) else session.subscription
        if sub is None:
            return {"tier": "standard", "label": "Standard"}

        status = sub.get("status") if isinstance(sub, dict) else sub.status
        if status != "active":
            return {"tier": "standard", "label": "Standard"}

        items = (sub.get("items", {}).get("data", []) if isinstance(sub, dict)
                 else sub.items.data)
        price_id = ""
        if items:
            p = items[0].get("price", {}) if isinstance(items[0], dict) else items[0].price
            price_id = p.get("id", "") if isinstance(p, dict) else p.id

        customer_id = session.get("customer") if isinstance(session, dict) else session.customer

        if price_id == PRICE_IDS["pro_plus"]:
            return {"tier": "pro_plus", "label": "Pro+", "customer_id": customer_id or ""}
        if price_id == PRICE_IDS["pro"]:
            return {"tier": "pro", "label": "Pro", "customer_id": customer_id or ""}

        return {"tier": "standard", "label": "Standard", "customer_id": ""}

    except stripe.StripeError as e:
        logger.error("Stripe error checking subscription status: %s", e)
        return {"tier": "standard", "label": "Standard", "customer_id": ""}


@router.get("/subscription/restore")
async def restore_subscription(email: str = ""):
    """
    Look up an active subscription by customer email.
    Returns {tier, label, customer_id} so the frontend can store the customer_id
    and re-verify on future loads without the original checkout session_id.
    """
    if not email or not stripe.api_key:
        return {"tier": "standard", "label": "Standard", "customer_id": ""}

    try:
        customers = stripe.Customer.search(query=f"email:'{email.strip()}'", limit=5)
        results = customers.get("data", []) if isinstance(customers, dict) else customers.data
        if not results:
            return {"tier": "standard", "label": "Standard", "customer_id": ""}

        for customer in results:
            customer_id = customer.get("id") if isinstance(customer, dict) else customer.id
            subs = stripe.Subscription.list(customer=customer_id, status="active", limit=5,
                                            expand=["data.items.data.price"])
            sub_list = subs.get("data", []) if isinstance(subs, dict) else subs.data
            for sub in sub_list:
                items = (sub.get("items", {}).get("data", []) if isinstance(sub, dict)
                         else sub.items.data)
                if not items:
                    continue
                p = items[0].get("price", {}) if isinstance(items[0], dict) else items[0].price
                price_id = p.get("id", "") if isinstance(p, dict) else p.id
                if price_id == PRICE_IDS["pro_plus"]:
                    return {"tier": "pro_plus", "label": "Pro+", "customer_id": customer_id}
                if price_id == PRICE_IDS["pro"]:
                    return {"tier": "pro", "label": "Pro", "customer_id": customer_id}

        return {"tier": "standard", "label": "Standard", "customer_id": ""}

    except stripe.StripeError as e:
        logger.error("Stripe error restoring subscription: %s", e)
        return {"tier": "standard", "label": "Standard", "customer_id": ""}


@router.get("/subscription/status-by-customer")
async def subscription_status_by_customer(customer_id: str = ""):
    """Verify an active subscription by Stripe customer ID (used after email-based restore)."""
    if not customer_id or not stripe.api_key:
        return {"tier": "standard", "label": "Standard"}

    try:
        subs = stripe.Subscription.list(customer=customer_id, status="active", limit=5,
                                        expand=["data.items.data.price"])
        sub_list = subs.get("data", []) if isinstance(subs, dict) else subs.data
        for sub in sub_list:
            items = (sub.get("items", {}).get("data", []) if isinstance(sub, dict)
                     else sub.items.data)
            if not items:
                continue
            p = items[0].get("price", {}) if isinstance(items[0], dict) else items[0].price
            price_id = p.get("id", "") if isinstance(p, dict) else p.id
            if price_id == PRICE_IDS["pro_plus"]:
                return {"tier": "pro_plus", "label": "Pro+"}
            if price_id == PRICE_IDS["pro"]:
                return {"tier": "pro", "label": "Pro"}
        return {"tier": "standard", "label": "Standard"}

    except stripe.StripeError as e:
        logger.error("Stripe error checking status by customer: %s", e)
        return {"tier": "standard", "label": "Standard"}


@router.post("/billing/portal")
async def billing_portal(request: Request):
    """
    Create a Stripe Customer Portal session for subscription self-management
    (cancel, update payment method, view invoices). Returns a redirect URL.
    """
    body = await request.json()
    customer_id = body.get("customer_id", "")
    if not customer_id or not stripe.api_key:
        raise HTTPException(status_code=400, detail="customer_id required")
    try:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=f"{APP_URL}/",
        )
        return {"url": session.url}
    except stripe.StripeError as e:
        logger.error("Stripe portal error for customer %s: %s", customer_id, e)
        raise HTTPException(status_code=502, detail="Failed to create portal session")


@router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature", "")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")

    if not webhook_secret:
        # No webhook secret configured — accept but log a warning.
        logger.warning("STRIPE_WEBHOOK_SECRET not set; skipping signature verification")
        try:
            event = stripe.Event.construct_from(
                __import__("json").loads(payload), stripe.api_key
            )
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Invalid payload: {e}")
    else:
        try:
            event = stripe.Webhook.construct_event(payload, sig, webhook_secret)
        except stripe.SignatureVerificationError:
            logger.warning("Stripe webhook signature verification failed")
            raise HTTPException(status_code=400, detail="Invalid signature")

    if event.type == "checkout.session.completed":
        session = event.data.object
        customer_email = session.get("customer_details", {}).get("email", "unknown")
        tier = session.get("metadata", {}).get("tier", "unknown")
        amount = session.get("amount_total", 0)
        logger.info(
            "EVENT subscription_started email=%s tier=%s amount=%s session=%s",
            customer_email, tier, amount, session.get("id")
        )

    elif event.type == "customer.subscription.deleted":
        sub = event.data.object
        logger.info("EVENT subscription_cancelled customer=%s", sub.get("customer"))

    elif event.type == "invoice.payment_failed":
        invoice = event.data.object
        logger.warning("EVENT payment_failed customer=%s", invoice.get("customer"))

    return {"ok": True}


@router.get("/success")
async def payment_success(session_id: str = "", tier: str = "pro"):
    """
    Stripe redirects here after a successful payment.
    Returns a minimal HTML page that stores the tier in localStorage
    and redirects the user back to the app.
    """
    from fastapi.responses import HTMLResponse
    tier_label = "Pro+" if tier == "pro_plus" else "Pro"
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
    localStorage.setItem('edgarwolf_tier', '{tier}');
    localStorage.setItem('edgarwolf_tier_label', '{tier_label}');
    localStorage.setItem('edgarwolf_session', '{session_id}');
  </script>
</head>
<body>
  <div class="card">
    <div class="check">✓</div>
    <div class="tier">{tier_label}</div>
    <h1>You're all set!</h1>
    <p>Your EdgarWolf {tier_label} subscription is active. Thank you for supporting the product.</p>
    <a href="/">Go to EdgarWolf</a>
  </div>
</body>
</html>"""
    return HTMLResponse(content=html)
