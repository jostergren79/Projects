"""
GET /company/{cik}/summary
Generates a rules-based natural language summary of the latest quarter's
financial performance based on the metrics data.
"""

import logging
import re
from fastapi import APIRouter, HTTPException
from edgar_client import fetch_company_facts, normalize_cik_to_10_digits
from routers.financial_metrics import (
    _select_best_concept_rows, _map_period_to_value,
    _calculate_margin_pct, _calculate_yoy_growth_pct,
    _prefer_quarterly_filing_rows,
    _find_prior_year_comparable_period,
    REVENUE_CONCEPTS,
    GROSS_PROFIT_CONCEPTS,
    OPERATING_INCOME_CONCEPTS,
    NET_INCOME_CONCEPTS,
    EPS_DILUTED_CONCEPTS,
)
from datetime import date

router = APIRouter()
logger = logging.getLogger(__name__)


def _validate_cik(cik: str) -> None:
    if not re.match(r"^\d{1,10}$", cik.strip()):
        raise HTTPException(status_code=400, detail=f"Invalid CIK '{cik}': must be 1–10 digits")


def _fmt_currency(val, unit="M"):
    """Format large dollar values into readable strings, preserving sign."""
    if val is None:
        return "N/A"
    sign = "-" if val < 0 else ""
    if unit == "B" or abs(val) >= 1_000_000_000:
        return f"{sign}${abs(val)/1_000_000_000:.1f}B"
    return f"{sign}${abs(val)/1_000_000:.0f}M"


def _fmt_pct(val, decimals=1):
    if val is None:
        return "N/A"
    sign = "+" if val >= 0 else ""
    return f"{sign}{val:.{decimals}f}%"


def _direction(val, positive_word="grew", negative_word="declined"):
    if val is None:
        return "was flat"
    return positive_word if val >= 0 else negative_word


def _magnitude(val):
    if val is None:
        return ""
    abs_val = abs(val)
    if abs_val < 1:
        return "slightly"
    if abs_val < 5:
        return "modestly"
    if abs_val < 15:
        return "meaningfully"
    return "significantly"


def _margin_commentary(current, prior):
    if current is None or prior is None:
        return None
    delta = current - prior
    if abs(delta) < 0.3:
        return "relatively stable"
    direction = "expanded" if delta > 0 else "contracted"
    return f"{direction} {abs(delta):.1f}pp year-over-year to {current:.1f}%"


@router.get("/company/{cik}/summary")
async def company_summary(cik: str):
    _validate_cik(cik)
    cik10 = normalize_cik_to_10_digits(cik)
    logger.info("Summary request for CIK %s", cik10)
    try:
        facts = await fetch_company_facts(cik10)
    except Exception as e:
        logger.error("EDGAR facts fetch failed for CIK %s: %s", cik10, e)
        raise HTTPException(status_code=502, detail=f"EDGAR fetch failed: {e}")

    rev_rows = _prefer_quarterly_filing_rows(_select_best_concept_rows(facts, REVENUE_CONCEPTS))
    gp_rows  = _prefer_quarterly_filing_rows(_select_best_concept_rows(facts, GROSS_PROFIT_CONCEPTS))
    oi_rows  = _prefer_quarterly_filing_rows(_select_best_concept_rows(facts, OPERATING_INCOME_CONCEPTS))
    ni_rows  = _prefer_quarterly_filing_rows(_select_best_concept_rows(facts, NET_INCOME_CONCEPTS))
    eps_rows = _prefer_quarterly_filing_rows(_select_best_concept_rows(facts, EPS_DILUTED_CONCEPTS))

    rev_idx = _map_period_to_value(rev_rows)
    gp_idx  = _map_period_to_value(gp_rows)
    oi_idx  = _map_period_to_value(oi_rows)
    ni_idx  = _map_period_to_value(ni_rows)
    eps_idx = _map_period_to_value(eps_rows)

    if not rev_rows:
        raise HTTPException(status_code=404, detail="Insufficient financial data to generate summary")

    # Latest and prior-year period
    latest = rev_rows[0]
    period = latest["period"]
    rev    = rev_idx.get(period)

    try:
        d = date.fromisoformat(period)
        period_label = f"Q{(d.month - 1) // 3 + 1} {d.year}"
    except Exception:
        period_label = period

    prior_period = _find_prior_year_comparable_period(period, list(rev_idx.keys()))
    prior_rev = rev_idx.get(prior_period) if prior_period else None
    prior_gp  = gp_idx.get(prior_period) if prior_period else None
    prior_oi  = oi_idx.get(prior_period) if prior_period else None

    rev_yoy   = _calculate_yoy_growth_pct(rev, prior_rev)
    gm        = _calculate_margin_pct(gp_idx.get(period), rev)
    prior_gm  = _calculate_margin_pct(prior_gp, prior_rev)
    om        = _calculate_margin_pct(oi_idx.get(period), rev)
    prior_om  = _calculate_margin_pct(prior_oi, prior_rev)
    ni        = ni_idx.get(period)
    eps       = eps_idx.get(period)

    name = facts.get("entityName", "The company")

    # Build sentences
    sentences = []

    # 1. Revenue headline
    if rev is not None:
        rev_str = _fmt_currency(rev)
        if rev_yoy is not None:
            mag = _magnitude(rev_yoy)
            verb = _direction(rev_yoy)
            sentences.append(
                f"{name} reported {rev_str} in net revenue for {period_label}, "
                f"which {verb} {mag} {_fmt_pct(rev_yoy)} year-over-year."
            )
        else:
            sentences.append(f"{name} reported {rev_str} in net revenue for {period_label}.")

    # 2. Gross margin
    gm_comment = _margin_commentary(gm, prior_gm)
    if gm is not None:
        if gm_comment:
            sentences.append(f"Gross margin {gm_comment}.")
        else:
            sentences.append(f"Gross margin was {gm:.1f}%.")

    # 3. Operating margin
    om_comment = _margin_commentary(om, prior_om)
    if om is not None:
        if om_comment:
            sentences.append(f"Operating margin {om_comment}.")
        else:
            sentences.append(f"Operating margin was {om:.1f}%.")

    # 4. Net income / net loss + EPS
    if ni is not None:
        if ni < 0:
            ni_clause = f"Net loss was {_fmt_currency(abs(ni))}"
        else:
            ni_clause = f"Net income was {_fmt_currency(ni)}"
        if eps is not None:
            eps_str = f"{'-' if eps < 0 else ''}${abs(eps):.2f}"
            sentences.append(f"{ni_clause}, or {eps_str} per diluted share.")
        else:
            sentences.append(f"{ni_clause}.")

    # 5. Outlook tone
    if rev_yoy is not None and gm is not None:
        if rev_yoy >= 5 and (gm_comment and "expanded" in (gm_comment or "")):
            sentences.append("Overall, the quarter reflected strong top-line momentum with improving profitability.")
        elif rev_yoy < -5:
            sentences.append("The quarter reflected revenue pressure, with top-line results below prior-year levels.")
        elif rev_yoy >= 0:
            sentences.append("Results were broadly stable relative to the prior year.")
        else:
            sentences.append("The quarter reflected modest revenue headwinds relative to the prior year.")

    return {
        "cik":     cik10,
        "name":    name,
        "period":  period,
        "summary": " ".join(sentences),
        "data": {
            "revenue":          rev,
            "revenue_yoy_pct":  rev_yoy,
            "gross_margin_pct": gm,
            "operating_margin_pct": om,
            "net_income":       ni,
            "eps_diluted":      eps,
        },
    }
