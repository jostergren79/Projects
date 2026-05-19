"""
Weekly Filing Stress digest — free-tier email capture.

POST /digest/subscribe        → add email, send welcome
GET  /digest/unsubscribe      → mark unsubscribed, return confirmation page

Emails are stored in the `digest_subscribers` table. The actual weekly digest
job is not yet built; this captures the audience first.
"""

import logging
import os
import re
import urllib.parse

import resend
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse

from auth import mask_email
from cache import add_digest_subscriber, remove_digest_subscriber

router = APIRouter()
logger = logging.getLogger(__name__)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
APP_URL = os.getenv("APP_URL", "https://www.edgarwolf.com")


def _send_digest_welcome(to_email: str) -> None:
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        logger.warning("RESEND_API_KEY not set — skipping digest welcome email")
        return

    resend.api_key = api_key
    from_addr = os.getenv("RESEND_FROM", "EdgarWolf <alerts@edgarwolf.com>")
    unsub_url = f"{APP_URL}/digest/unsubscribe?email={urllib.parse.quote(to_email)}"

    html = f"""
    <div style="font-family:sans-serif;max-width:560px;margin:0 auto;color:#1a1a1a">
      <h2 style="color:#2b6cb0;margin-bottom:4px">Welcome to the Filing Stress digest</h2>
      <p style="color:#555;line-height:1.6">
        You're subscribed. Each Sunday you'll get a short list of the public companies
        with the highest <strong>Filing Stress Scores</strong> from the past week —
        the same composite signal EdgarWolf uses to flag filings worth a second look.
      </p>
      <p style="color:#555;line-height:1.6">
        No spam, no upsells in the digest itself. If a company catches your eye,
        you can dig into the full picture on
        <a href="{APP_URL}" style="color:#2b6cb0">EdgarWolf</a>.
      </p>
      <hr style="border:none;border-top:1px solid #eee;margin:20px 0">
      <p style="font-size:12px;color:#888;line-height:1.6">
        Don't want this? <a href="{unsub_url}" style="color:#888">Unsubscribe in one click</a>.
        Questions? Reply to this email — it goes straight to Jason.
      </p>
    </div>
    """

    try:
        resend.Emails.send({
            "from": from_addr,
            "to": [to_email],
            "subject": "Welcome to the EdgarWolf Filing Stress digest",
            "html": html,
        })
        logger.info("EVENT digest_welcome_sent email=%s", mask_email(to_email))
    except Exception as e:
        logger.error("Failed to send digest welcome to %s: %s", mask_email(to_email), e)


@router.post("/digest/subscribe")
async def digest_subscribe(request: Request):
    body = await request.json()
    email = str(body.get("email", "")).strip().lower()
    source = str(body.get("source", "banner")).strip()[:32]

    if not email or len(email) > 254 or not _EMAIL_RE.match(email):
        raise HTTPException(status_code=400, detail="Please enter a valid email address.")

    is_new = add_digest_subscriber(email, source)
    logger.info("EVENT digest_signup email=%s source=%s new=%s", mask_email(email), source, is_new)

    if is_new:
        _send_digest_welcome(email)

    return {"ok": True, "new": is_new}


@router.get("/digest/unsubscribe")
async def digest_unsubscribe(email: str = ""):
    email = email.strip().lower()
    if email and _EMAIL_RE.match(email):
        removed = remove_digest_subscriber(email)
        logger.info("EVENT digest_unsubscribe email=%s removed=%s", mask_email(email), removed)
    else:
        removed = False

    msg = "You've been unsubscribed." if removed else "You're not currently subscribed."
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Unsubscribed — EdgarWolf</title>
  <style>
    *,*::before,*::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{ background: #0f1117; color: #e8eaf6; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
           display: flex; align-items: center; justify-content: center; min-height: 100vh; text-align: center; padding: 24px; }}
    .card {{ background: #1a1d27; border: 1px solid #2e3352; border-radius: 12px; padding: 40px; max-width: 440px; width: 100%; }}
    h1 {{ font-size: 1.3rem; margin-bottom: 12px; }}
    p {{ color: #8b90b8; line-height: 1.6; margin-bottom: 20px; }}
    a {{ display: inline-block; background: #4f8ef7; color: #fff; border-radius: 8px;
         padding: 10px 24px; text-decoration: none; font-weight: 600; font-size: .9rem; }}
  </style>
</head>
<body>
  <div class="card">
    <h1>{msg}</h1>
    <p>You won't receive any further Filing Stress digest emails.</p>
    <a href="/">Back to EdgarWolf</a>
  </div>
</body>
</html>"""
    return HTMLResponse(content=html)
