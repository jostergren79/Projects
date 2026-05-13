"""
scheduler.py — Hourly Pro+ alert polling job.

Schedule: every 60 minutes, Monday–Friday, 08:00–18:00 US/Eastern.
For each Pro+ user's watchlist, checks SEC EDGAR for new 10-Q, 10-K, or 8-K
filings. If a new filing is found and anomaly signals are present (z-score
MEDIUM/HIGH or Filing Stress Score ELEVATED), sends an alert via Resend.

See METHODOLOGY.md §13–15 for the full spec.
"""

import asyncio
import logging
import os

import resend
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from cache import (
    get_all_pro_plus_watchlists,
    get_last_checked,
    set_last_checked,
    has_alert_been_sent,
    log_alert_sent,
    clear_cached_json,
)
from edgar_client import fetch_company_submissions, normalize_cik_to_10_digits

logger = logging.getLogger(__name__)

# Material filing types that warrant an anomaly re-check.
_MATERIAL_FORMS = {"10-Q", "10-K", "8-K"}

# Seconds to wait between company checks to stay well under SEC rate limits.
_INTER_COMPANY_DELAY = 2.0


def _build_alert_html(
    ticker: str,
    name: str,
    form_type: str,
    filing_date: str,
    stress_score: int,
    stress_status: str,
    flags: list,
) -> str:
    severity_color = {"HIGH": "#e53e3e", "MEDIUM": "#f6ad55"}.get
    stress_color = "#e53e3e" if stress_status == "ELEVATED" else "#f6ad55" if stress_status == "MODERATE" else "#48bb78"

    flag_rows = ""
    for f in flags:
        color = severity_color(f["severity"], "#e53e3e")
        flag_rows += (
            f'<tr><td style="padding:6px 0;color:#555">{f["metric"]}</td>'
            f'<td style="text-align:right;font-weight:700;color:{color}">'
            f'{f["note"]}</td></tr>'
        )

    display = ticker if ticker else name
    url = f"https://www.edgarwolf.com/?cik={name}"

    return f"""
    <div style="font-family:sans-serif;max-width:560px;margin:0 auto;color:#1a1a1a">
      <h2 style="color:#2b6cb0;margin-bottom:4px">&#9888; Filing Alert: {name} ({display})</h2>
      <p style="color:#555;font-size:13px;margin-top:0">
        New <strong>{form_type}</strong> filing accepted {filing_date}
      </p>
      <hr style="border:none;border-top:1px solid #eee;margin:16px 0">
      <table style="width:100%;border-collapse:collapse;font-size:14px">
        <tr>
          <td style="padding:6px 0;color:#555">Filing Stress Score</td>
          <td style="text-align:right;font-weight:700;color:{stress_color}">
            {stress_score} / 100 {stress_status}
          </td>
        </tr>
        {flag_rows}
      </table>
      <hr style="border:none;border-top:1px solid #eee;margin:16px 0">
      <a href="https://www.edgarwolf.com" style="display:inline-block;background:#2b6cb0;color:#fff;padding:10px 20px;border-radius:4px;text-decoration:none;font-size:14px;font-weight:600">
        View on EdgarWolf →
      </a>
      <p style="font-size:11px;color:#aaa;margin-top:24px">
        EdgarWolf Pro+ &middot; You're receiving this because {name} is on your watchlist.
      </p>
    </div>
    """


async def _check_company(customer_id: str, email: str, cik: str, ticker: str, name: str) -> None:
    cik10 = normalize_cik_to_10_digits(cik)

    # Force a fresh submissions fetch — bypass the 6-hour cache for alert polling.
    clear_cached_json(f"submissions:{cik10}")

    try:
        subs = await fetch_company_submissions(cik10)
    except Exception as e:
        logger.warning("Alert check: submissions fetch failed for CIK %s: %s", cik10, e)
        return  # Don't update last_checked; retry on next cycle.

    filings = subs.get("filings", {}).get("recent", {})
    forms      = filings.get("form", [])
    accessions = filings.get("accessionNumber", [])
    accept_dts = filings.get("acceptanceDateTime", [])
    dates      = filings.get("filingDate", [])

    last_checked = get_last_checked(customer_id, cik10)

    # Find the most recent material filing newer than last_checked.
    new_filing = None
    for i, form in enumerate(forms):
        if form not in _MATERIAL_FORMS:
            continue
        acc = accessions[i] if i < len(accessions) else None
        accept_dt_str = accept_dts[i] if i < len(accept_dts) else None
        filing_date = dates[i] if i < len(dates) else "unknown"
        if not acc or not accept_dt_str:
            continue

        # Parse acceptance timestamp to unix seconds for comparison.
        try:
            from datetime import datetime, timezone
            dt = datetime.strptime(accept_dt_str, "%Y-%m-%dT%H:%M:%S.%fZ").replace(tzinfo=timezone.utc)
            accept_ts = int(dt.timestamp())
        except ValueError:
            continue

        if accept_ts > last_checked:
            new_filing = {"form": form, "accession": acc, "date": filing_date, "ts": accept_ts}
            break  # Most recent first — only need the newest.

    set_last_checked(customer_id, cik10)

    if new_filing is None:
        return

    if has_alert_been_sent(customer_id, cik10, new_filing["accession"]):
        return

    # New filing found — run anomaly checks.
    try:
        # Import here to avoid circular imports at module load.
        from routers.anomaly_flags import company_flags
        from routers.company_lookup import company_anomalies

        flags_result = await company_flags(cik10)
        anomalies_result = await company_anomalies(cik10)
    except Exception as e:
        logger.warning("Alert check: anomaly fetch failed for CIK %s: %s", cik10, e)
        return

    flags = flags_result.get("flags", [])
    stress_score = anomalies_result.get("filing_stress_score", 0)
    stress_status = anomalies_result.get("status", "LOW")

    # Alert only when at least one signal is present.
    has_flags = any(f["severity"] in ("MEDIUM", "HIGH") for f in flags)
    has_stress = stress_status == "ELEVATED"

    if not has_flags and not has_stress:
        logger.info(
            "Alert check: new %s filing for %s (CIK %s) but no anomalies — skipping",
            new_filing["form"], name, cik10,
        )
        return

    # Send alert.
    api_key = os.getenv("RESEND_API_KEY")
    if not api_key:
        logger.error("Alert check: RESEND_API_KEY not set — cannot send alert")
        return

    resend.api_key = api_key
    from_addr = os.getenv("RESEND_FROM", "EdgarWolf <alerts@edgarwolf.com>")
    subject = f"[EdgarWolf] New {new_filing['form']} filing — {name} ({ticker or cik10})"

    html = _build_alert_html(
        ticker=ticker,
        name=name,
        form_type=new_filing["form"],
        filing_date=new_filing["date"],
        stress_score=stress_score,
        stress_status=stress_status,
        flags=flags,
    )

    try:
        result = resend.Emails.send({
            "from": from_addr,
            "to": [email],
            "subject": subject,
            "html": html,
        })
        log_alert_sent(customer_id, cik10, new_filing["accession"])
        logger.info(
            "EVENT alert_sent customer_id=%s cik=%s form=%s accession=%s resend_id=%s",
            customer_id, cik10, new_filing["form"], new_filing["accession"],
            result.get("id"),
        )
    except Exception as e:
        logger.error("Alert check: Resend send failed for %s → %s: %s", name, email, e)


async def run_alert_check() -> None:
    """Main polling job — iterates all Pro+ watchlist entries."""
    entries = get_all_pro_plus_watchlists()
    if not entries:
        logger.debug("Alert check: no Pro+ watchlist entries")
        return

    logger.info("EVENT alert_check_start entries=%d", len(entries))
    sent = 0
    for entry in entries:
        await _check_company(
            customer_id=entry["customer_id"],
            email=entry["email"],
            cik=entry["cik"],
            ticker=entry["ticker"],
            name=entry["name"],
        )
        sent += 1
        if sent < len(entries):
            await asyncio.sleep(_INTER_COMPANY_DELAY)

    logger.info("EVENT alert_check_done entries=%d", len(entries))


alert_scheduler = AsyncIOScheduler(timezone="America/New_York")
alert_scheduler.add_job(
    run_alert_check,
    CronTrigger(
        day_of_week="mon-fri",
        hour="8-18",
        minute="0",
        timezone="America/New_York",
    ),
    id="pro_plus_alerts",
    name="Pro+ filing alerts",
    max_instances=1,  # Never overlap if a run takes longer than 60 min.
    misfire_grace_time=300,
)
