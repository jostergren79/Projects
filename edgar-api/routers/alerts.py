import os
import resend
from fastapi import APIRouter, HTTPException, Request
from cache import upsert_user, add_to_watchlist, get_all_pro_plus_watchlists

router = APIRouter()

def _is_dev(request: Request) -> bool:
    host = request.client.host if request.client else ""
    return host in ("127.0.0.1", "::1", "localhost")


@router.post("/test/send-alert")
async def send_test_alert(request: Request):
    if not _is_dev(request):
        raise HTTPException(status_code=403, detail="Dev-only endpoint")

    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="RESEND_API_KEY not set")

    resend.api_key = api_key

    # RESEND_FROM: switch to alerts@edgarwolf.com once domain is verified in Resend.
    # RESEND_TEST_TO: switch to jason@edgarwolf.com once domain is verified.
    from_addr = os.getenv("RESEND_FROM", "EdgarWolf <onboarding@resend.dev>")
    to_addr   = os.getenv("RESEND_TEST_TO", "jason.ostergren79@gmail.com")

    params: resend.Emails.SendParams = {
        "from": from_addr,
        "to": [to_addr],
        "subject": "[Test] EdgarWolf Alert — $GIS Filing Stress Score 100/100",
        "html": """
        <div style="font-family:sans-serif;max-width:560px;margin:0 auto;color:#1a1a1a">
          <h2 style="color:#e53e3e;margin-bottom:4px">&#9888; Filing Alert: General Mills ($GIS)</h2>
          <p style="color:#555;font-size:13px;margin-top:0">This is a test alert from your local EdgarWolf dev environment.</p>
          <hr style="border:none;border-top:1px solid #eee;margin:16px 0">
          <table style="width:100%;border-collapse:collapse;font-size:14px">
            <tr><td style="padding:6px 0;color:#555">Filing Stress Score</td><td style="text-align:right;font-weight:700;color:#e53e3e">100 / 100 ELEVATED</td></tr>
            <tr><td style="padding:6px 0;color:#555">Revenue YoY Growth</td><td style="text-align:right;font-weight:700;color:#e53e3e">-3.3σ below average</td></tr>
            <tr><td style="padding:6px 0;color:#555">Gross Margin</td><td style="text-align:right;font-weight:700;color:#f6ad55">-2.1σ below average</td></tr>
            <tr><td style="padding:6px 0;color:#555">Filing Velocity</td><td style="text-align:right;font-weight:700;color:#e53e3e">ELEVATED — 4 filings in 2 days</td></tr>
          </table>
          <hr style="border:none;border-top:1px solid #eee;margin:16px 0">
          <a href="https://www.edgarwolf.com" style="display:inline-block;background:#2b6cb0;color:#fff;padding:10px 20px;border-radius:4px;text-decoration:none;font-size:14px;font-weight:600">View on EdgarWolf →</a>
          <p style="font-size:11px;color:#aaa;margin-top:24px">EdgarWolf Pro+ &middot; Manage alerts at edgarwolf.com</p>
        </div>
        """,
    }

    email = resend.Emails.send(params)
    return {"ok": True, "id": email.get("id")}


@router.post("/test/seed-alert-user")
async def seed_alert_test_user(request: Request):
    """Insert a Pro+ test user + GIS watchlist entry for local alert testing."""
    if not _is_dev(request):
        raise HTTPException(status_code=403, detail="Dev-only endpoint")
    upsert_user("cus_test_proplus", "jason.ostergren79@gmail.com", "pro_plus")
    add_to_watchlist("cus_test_proplus", "0000040987", "GIS", "General Mills Inc")
    return {"ok": True, "customer_id": "cus_test_proplus", "watchlist": ["GIS (0000040987)"]}


@router.post("/test/run-alert-check")
async def trigger_alert_check(request: Request):
    """Manually trigger one alert check cycle. Returns a summary of what ran."""
    if not _is_dev(request):
        raise HTTPException(status_code=403, detail="Dev-only endpoint")
    from scheduler import run_alert_check
    entries_before = get_all_pro_plus_watchlists()
    await run_alert_check()
    return {"ok": True, "entries_checked": len(entries_before)}
