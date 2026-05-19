"""
auth.py — Magic-link authentication helpers.

Why this exists:
  Before v1.6.0, GET /subscription/restore returned the Stripe customer_id
  to anyone who typed a Pro user's email. Combined with the unauthenticated
  email field on POST /watchlist/sync, an attacker could read the victim's
  watchlist and reroute their Pro+ filing alerts.

The auth model:
  1. User enters email on the Restore form.
  2. POST /auth/request verifies an active Stripe subscription on that email,
     then sends a short-lived signed magic link via Resend. The endpoint
     always returns 200 — silence is the only signal an attacker gets.
  3. The user clicks the link. GET /auth/verify validates the token and
     sets a long-lived httpOnly cookie containing a signed customer_id.
  4. Watchlist endpoints read customer_id from the cookie. The frontend
     never sees or stores the customer_id.

Token format:
  base64url(payload).base64url(hmac_sha256(secret, payload))
  payload = json{"sub": customer_id, "iat": int, "exp": int, "use": "magic"|"session"}
"""

import base64
import hashlib
import hmac
import json
import logging
import os
import time
from typing import Optional

logger = logging.getLogger(__name__)

MAGIC_LINK_TTL_SECONDS = 15 * 60          # 15 minutes
SESSION_TTL_SECONDS    = 30 * 24 * 3600   # 30 days
SESSION_COOKIE_NAME    = "ew_session"

# Production sets APP_URL to https://www.edgarwolf.com. Local dev points at
# http://127.0.0.1:8000. Secure-only cookies are silently dropped over plain
# HTTP, so we mirror the scheme of APP_URL.
_APP_URL = os.getenv("APP_URL", "https://www.edgarwolf.com")
_COOKIE_SECURE = _APP_URL.lower().startswith("https://")


def _secret() -> bytes:
    s = os.getenv("MAGIC_LINK_SECRET", "")
    if not s:
        raise RuntimeError(
            "MAGIC_LINK_SECRET env var is required — generate one with "
            "`python -c 'import secrets; print(secrets.token_urlsafe(48))'`"
        )
    return s.encode("utf-8")


def _b64url_encode(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b"=").decode("ascii")


def _b64url_decode(s: str) -> bytes:
    pad = "=" * (-len(s) % 4)
    return base64.urlsafe_b64decode(s + pad)


def _mint_token(customer_id: str, *, use: str, ttl_seconds: int) -> str:
    now = int(time.time())
    payload = {"sub": customer_id, "iat": now, "exp": now + ttl_seconds, "use": use}
    payload_b = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    sig = hmac.new(_secret(), payload_b, hashlib.sha256).digest()
    return f"{_b64url_encode(payload_b)}.{_b64url_encode(sig)}"


def mint_magic_link_token(customer_id: str) -> str:
    return _mint_token(customer_id, use="magic", ttl_seconds=MAGIC_LINK_TTL_SECONDS)


def mint_session_token(customer_id: str) -> str:
    return _mint_token(customer_id, use="session", ttl_seconds=SESSION_TTL_SECONDS)


def verify_token(token: str, *, expected_use: str) -> Optional[str]:
    """Return the customer_id if the token is valid, else None.

    Validates: HMAC signature (constant-time), token use (magic/session),
    expiry, and payload shape.
    """
    if not token or "." not in token:
        return None
    try:
        payload_part, sig_part = token.split(".", 1)
        payload_b = _b64url_decode(payload_part)
        sig = _b64url_decode(sig_part)
    except (ValueError, base64.binascii.Error):
        return None

    expected_sig = hmac.new(_secret(), payload_b, hashlib.sha256).digest()
    if not hmac.compare_digest(sig, expected_sig):
        return None

    try:
        payload = json.loads(payload_b.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return None

    if payload.get("use") != expected_use:
        return None
    if int(payload.get("exp", 0)) < int(time.time()):
        return None

    sub = payload.get("sub", "")
    if not isinstance(sub, str) or not sub.startswith("cus_"):
        return None
    return sub


def set_session_cookie(response, customer_id: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=mint_session_token(customer_id),
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        secure=_COOKIE_SECURE,
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response) -> None:
    response.delete_cookie(SESSION_COOKIE_NAME, path="/")


def read_session_customer_id(request) -> Optional[str]:
    """Return the authenticated customer_id from the session cookie, or None."""
    token = request.cookies.get(SESSION_COOKIE_NAME, "")
    return verify_token(token, expected_use="session")


def mask_email(email: str) -> str:
    """Mask an email for log output: jason@gmail.com → j***@gmail.com.

    Used in EVENT log lines to avoid keeping plaintext PII in Railway log
    storage. Domain is preserved for routing analysis.
    """
    if not email or "@" not in email:
        return "***"
    local, _, domain = email.partition("@")
    if len(local) <= 1:
        return f"***@{domain}"
    return f"{local[0]}***@{domain}"
