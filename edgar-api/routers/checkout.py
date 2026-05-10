"""
Stripe Checkout integration.

POST /checkout/session  — creates a hosted Stripe Checkout session and returns
                          the redirect URL. Called by the frontend upgrade buttons.

POST /webhook/stripe    — receives Stripe webhook events. Logs completed
                          subscriptions for analytics and future email alerts.

Environment variables required (set in Render dashboard, never in code):
  STRIPE_SECRET_KEY       sk_live_...
  STRIPE_WEBHOOK_SECRET   whsec_...  (from Stripe dashboard → Webhooks)
  STRIPE_PRO_PRICE_ID     price_1TVNfH1C3cijZqBOyp7Y5qJH
  STRIPE_PRO_PLUS_PRICE_ID price_1TVNeQ1C3cijZqBOkOX1IoJj
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
    "pro":      os.getenv("STRIPE_PRO_PRICE_ID",      "price_1TVNfH1C3cijZqBOyp7Y5qJH"),
    "pro_plus": os.getenv("STRIPE_PRO_PLUS_PRICE_ID", "price_1TVNeQ1C3cijZqBOkOX1IoJj"),
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
