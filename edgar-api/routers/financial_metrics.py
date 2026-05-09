"""
GET /company/{cik}/metrics
Returns up to 8 quarters of revenue, gross profit, operating income,
net income, EPS (diluted), and derived margins + YoY growth rates.

XBRL concept mapping (us-gaap):
  Revenue:         Revenues | RevenueFromContractWithCustomerExcludingAssessedTax | SalesRevenueNet
  Gross profit:    GrossProfit
  Operating income: OperatingIncomeLoss
  Net income:      NetIncomeLoss
  EPS diluted:     EarningsPerShareDiluted
"""

import logging
import re
from fastapi import APIRouter, HTTPException, Query
from edgar_client import fetch_company_facts, normalize_cik_to_10_digits
from datetime import date
from typing import Optional

router = APIRouter()
logger = logging.getLogger(__name__)


def _validate_cik(cik: str) -> None:
    if not re.match(r"^\d{1,10}$", cik.strip()):
        raise HTTPException(status_code=400, detail=f"Invalid CIK '{cik}': must be 1–10 digits")

# Ordered preference list — first concept that has data wins.
# This list is intentionally broad because filers vary by preferred XBRL tags.
REVENUE_CONCEPTS = [
    "Revenues",
    "RevenueFromContractWithCustomerExcludingAssessedTax",
    "SalesRevenueNet",
    "RevenueFromContractWithCustomerIncludingAssessedTax",
    "SalesRevenueGoodsNet",
    "RegulatedAndUnregulatedOperatingRevenue",
    "RealEstateRevenueNet",
]

GROSS_PROFIT_CONCEPTS = [
    "GrossProfit",
]

COST_OF_REVENUE_CONCEPTS = [
    "CostOfGoodsAndServicesSold",
    "CostOfRevenue",
    "CostOfGoodsSold",
    "CostOfProductsSold",
]

OPERATING_INCOME_CONCEPTS = [
    "OperatingIncomeLoss",
    "IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest",
]

NET_INCOME_CONCEPTS = [
    "NetIncomeLoss",
    "ProfitLoss",
]

EPS_DILUTED_CONCEPTS = [
    "EarningsPerShareDiluted",
    "DilutedEarningsPerShare",
]

# Roughly six fiscal quarters; used to reject stale concept selections.
MAX_CONCEPT_AGE_DAYS = 550


def _is_quarterly_or_annual_form(form: str) -> bool:
    """Accept base and amended periodic filings (10-Q, 10-Q/A, 10-K, 10-K/A)."""
    if not form:
        return False
    f = str(form).upper()
    return f.startswith("10-Q") or f.startswith("10-K")


def _normalize_form_label(form: str) -> str:
    f = str(form or "").upper()
    if f.startswith("10-Q"):
        return "10-Q"
    if f.startswith("10-K"):
        return "10-K"
    return f


def _parse_date(d: str):
    try:
        return date.fromisoformat(d)
    except Exception:
        return None


def _inclusive_day_span(start: str, end: str):
    s = _parse_date(start)
    e = _parse_date(end)
    if not s or not e:
        return None
    # Inclusive duration gives closer quarter lengths for SEC contexts.
    return (e - s).days + 1


def _looks_like_single_quarter_duration(days: Optional[int]) -> bool:
    if days is None:
        return False
    return 70 <= days <= 120


def _dedupe_by_context_keep_latest_filing(rows: list[dict]) -> list[dict]:
    """Deduplicate rows by SEC context identity and keep latest filed value."""
    latest = {}
    for r in rows:
        key = (r["period"], r.get("fy"), r.get("fp"), r.get("form"), r.get("frame"))
        prev = latest.get(key)
        if prev is None or (r.get("filed") or "") > (prev.get("filed") or ""):
            latest[key] = r
    return list(latest.values())


def _normalize_row_to_quarter_value(row: dict, fy_fp_map: dict) -> Optional[float]:
    """
    Normalize SEC fact rows to quarter-level values.

    Some filers publish Q2/Q3 in 10-Q as cumulative YTD values (6M/9M).
    In those cases we back out the quarter amount by differencing Q1/Q2.
    """
    fp = row.get("fp")
    days = row.get("duration_days")
    val = row.get("value")
    if val is None:
        return None

    if fp == "Q1":
        return val

    if fp in ("Q2", "Q3"):
        # If Q2/Q3 looks cumulative, derive true quarter amount from prior fp.
        if days is not None and days > 120:
            prev_fp = "Q1" if fp == "Q2" else "Q2"
            prev = fy_fp_map.get((row.get("fy"), prev_fp))
            if prev and prev.get("value") is not None:
                return val - prev["value"]
            return None
        return val

    if fp == "FY":
        # FY contexts are typically annual; keep only if duration is clearly quarterly.
        return val if _looks_like_single_quarter_duration(days) else None

    # Fallback for missing/odd fp: accept if duration itself is quarter-like.
    if _looks_like_single_quarter_duration(days):
        return val
    return None


def _score_concept_candidate(rows: list[dict]) -> tuple:
    """Higher is better: prioritize recency, then 10-Q coverage, then volume."""
    if not rows:
        return (0, "0000-00-00", 0, 0)

    latest_period = rows[0]["period"]
    latest_dt = _parse_date(latest_period)
    recent = 0
    if latest_dt is not None:
        recent = 1 if (date.today() - latest_dt).days <= 900 else 0

    ten_q_count = sum(1 for r in rows if r.get("form") == "10-Q")
    return (recent, latest_period, ten_q_count, len(rows))


def _latest_period_age_in_days(rows: list[dict]) -> Optional[int]:
    if not rows:
        return None
    d = _parse_date(rows[0].get("period"))
    if d is None:
        return None
    return (date.today() - d).days


def _is_recent_concept(rows: list[dict], max_age_days: int = MAX_CONCEPT_AGE_DAYS) -> bool:
    age = _latest_period_age_in_days(rows)
    if age is None:
        return False
    return age <= max_age_days


def _prefer_quarterly_filing_rows(rows: list[dict]) -> list[dict]:
    ten_q = [r for r in rows if r.get("form") == "10-Q"]
    return ten_q if ten_q else rows

def _extract_quarterly_rows_for_concept(facts: dict, concept: str) -> list:
    """
    Pull and normalize SEC fact rows to quarter-level values for a us-gaap concept.

    Handles mixed EDGAR contexts where some 10-Q values are cumulative YTD instead
    of standalone quarter amounts, and where rows may be embedded in 10-K filings.

    Returns list sorted newest-first with normalized quarter values:
      {period, start, value, form, filed, fy, fp, frame, duration_days}
    """
    try:
        usgaap = facts.get("facts", facts).get("us-gaap", {})
        units = usgaap[concept]["units"]
        # Most financial concepts use USD; EPS uses USD/shares
        unit_data = units.get("USD") or units.get("USD/shares") or []
    except KeyError:
        return []

    rows = []
    for item in unit_data:
        form = item.get("form")
        if not _is_quarterly_or_annual_form(form):
            continue
        period = item.get("end")
        if not period:
            continue
        start = item.get("start")
        rows.append({
            "period": period,
            "start":  start,
            "value":  item.get("val"),
            "form":   _normalize_form_label(form),
            "filed":  item.get("filed"),
            "accn":   item.get("accn"),
            "fy":     item.get("fy"),
            "fp":     item.get("fp"),
            "frame":  item.get("frame"),
            "duration_days": _inclusive_day_span(start, period),
        })

    if not rows:
        return []

    rows = _dedupe_by_context_keep_latest_filing(rows)

    # Build lookup for cumulative-to-quarter differencing by fiscal-year period.
    fy_fp_map = {}
    for r in rows:
        fy = r.get("fy")
        fp = r.get("fp")
        if fy is None or fp is None:
            continue
        key = (fy, fp)
        prev = fy_fp_map.get(key)
        if prev is None or (r.get("filed") or "") > (prev.get("filed") or ""):
            fy_fp_map[key] = r

    normalized = []
    for r in rows:
        qv = _normalize_row_to_quarter_value(r, fy_fp_map)
        if qv is None:
            continue
        normalized.append({**r, "value": qv})

    # Collapse to one row per quarter-end, preferring 10-Q and latest filed.
    best_by_period = {}
    for r in normalized:
        period = r["period"]
        prev = best_by_period.get(period)
        if prev is None:
            best_by_period[period] = r
            continue

        prev_key = (1 if prev.get("form") == "10-Q" else 0, prev.get("filed") or "")
        curr_key = (1 if r.get("form") == "10-Q" else 0, r.get("filed") or "")
        if curr_key > prev_key:
            best_by_period[period] = r

    output = list(best_by_period.values())

    # Sort newest first
    output.sort(key=lambda x: x["period"], reverse=True)
    return output


def _select_best_concept_with_rows(
    facts: dict,
    candidates: list,
    prefer_quarterly: bool = True,
    max_age_days: int = MAX_CONCEPT_AGE_DAYS,
    allow_stale_fallback: bool = True,
):
    """Return (concept_name, rows) for the best available concept.

    If prefer_quarterly=True, first choose a concept containing at least one 10-Q row.
    This prevents annual-only tags from shadowing quarterly-capable tags.
    """
    best = (None, [])
    best_score = (0, "0000-00-00", 0, 0)
    stale_best = (None, [])
    stale_best_score = (0, "0000-00-00", 0, 0)

    for concept in candidates:
        rows = _extract_quarterly_rows_for_concept(facts, concept)
        if not rows:
            continue
        if not _is_recent_concept(rows, max_age_days=max_age_days):
            stale_score = _score_concept_candidate(rows)
            if stale_score > stale_best_score:
                stale_best = (concept, rows)
                stale_best_score = stale_score
            continue
        score = _score_concept_candidate(rows)
        if score > best_score:
            best = (concept, rows)
            best_score = score

    if best[0] is None and allow_stale_fallback:
        best = stale_best

    if not prefer_quarterly:
        return best

    concept, rows = best
    if not concept:
        return best

    preferred = _prefer_quarterly_filing_rows(rows)
    return concept, preferred


def _select_best_concept_rows(facts: dict, candidates: list) -> list:
    _, rows = _select_best_concept_with_rows(facts, candidates, prefer_quarterly=True)
    return rows


def _calculate_yoy_growth_pct(current, prior):
    if current is None or prior is None or prior == 0:
        return None
    return round((current - prior) / abs(prior) * 100, 2)


def _calculate_margin_pct(numerator, denominator):
    if numerator is None or denominator is None or denominator == 0:
        return None
    return round(numerator / denominator * 100, 2)


def _map_period_to_value(rows: list) -> dict:
    return {r["period"]: r["value"] for r in rows}


def _find_prior_year_comparable_period(period: str, periods: list[str], tolerance_days: int = 10) -> Optional[str]:
    """
    Find the best same-quarter prior-year period key even when fiscal quarter-end
    dates shift by a few days (e.g., 2026-03-28 vs 2025-03-29).
    """
    d = _parse_date(period)
    if d is None:
        return None

    try:
        target = d.replace(year=d.year - 1)
    except Exception:
        # Leap-day fallback
        from datetime import timedelta
        target = d - timedelta(days=365)

    best_period = None
    best_delta = None
    for p in periods:
        pd = _parse_date(p)
        if pd is None:
            continue

        year_gap = abs((d - pd).days)
        if year_gap < 330 or year_gap > 400:
            continue

        delta = abs((pd - target).days)
        if delta > tolerance_days:
            continue

        if best_delta is None or delta < best_delta:
            best_delta = delta
            best_period = p

    return best_period


def _build_row_debug_snapshot(row: dict) -> dict:
    return {
        "period": row.get("period"),
        "start": row.get("start"),
        "form": row.get("form"),
        "filed": row.get("filed"),
        "fy": row.get("fy"),
        "fp": row.get("fp"),
        "frame": row.get("frame"),
        "duration_days": row.get("duration_days"),
        "value": row.get("value"),
    }


def _build_concept_diagnostics(
    facts: dict,
    candidates: list,
    selected: Optional[str],
    max_age_days: int = MAX_CONCEPT_AGE_DAYS,
) -> list[dict]:
    diagnostics = []
    for concept in candidates:
        rows = _extract_quarterly_rows_for_concept(facts, concept)
        preferred = _prefer_quarterly_filing_rows(rows)
        latest_age_days = _latest_period_age_in_days(rows)
        is_fresh = _is_recent_concept(rows, max_age_days=max_age_days)
        rejected_reason = None
        if rows and not is_fresh:
            rejected_reason = "stale_latest_period"
        diagnostics.append({
            "concept": concept,
            "selected": concept == selected,
            "score": _score_concept_candidate(rows),
            "row_count": len(rows),
            "ten_q_count": sum(1 for r in rows if r.get("form") == "10-Q"),
            "ten_k_count": sum(1 for r in rows if r.get("form") == "10-K"),
            "latest_period": rows[0]["period"] if rows else None,
            "latest_filed": rows[0]["filed"] if rows else None,
            "latest_age_days": latest_age_days,
            "fresh_under_max_age": is_fresh,
            "selection_rejected_reason": rejected_reason,
            "sample_rows": [_build_row_debug_snapshot(r) for r in preferred[:5]],
        })
    return diagnostics


def _label_metric_source(value, source_when_present: str = "reported") -> str:
    if value is None:
        return "not_available"
    return source_when_present


def _build_profitability_profile(name: Optional[str], latest_gross_margin: Optional[float], has_cost_concept: bool) -> dict:
    entity = (name or "").upper()
    financial_hint = any(token in entity for token in ["BANK", "BANC", "FINANCIAL", "CAPITAL", "INSURANCE", "TRUST"])

    if latest_gross_margin is not None:
        return {
            "primary_metric": "gross_margin_pct",
            "reason": "gross_margin_available",
        }

    if financial_hint:
        return {
            "primary_metric": "operating_margin_pct",
            "reason": "financial_model_or_non_cogs_reporter",
        }

    if not has_cost_concept:
        return {
            "primary_metric": "operating_margin_pct",
            "reason": "cost_of_revenue_not_reported",
        }

    return {
        "primary_metric": "operating_margin_pct",
        "reason": "gross_margin_unavailable_for_recent_periods",
    }


@router.get("/company/{cik}/metrics")
async def company_metrics(
    cik: str,
    quarters: int = 8,
    debug: bool = Query(False, description="Include concept/normalization diagnostics"),
):
    _validate_cik(cik)
    cik10 = normalize_cik_to_10_digits(cik)
    logger.info("Metrics request for CIK %s (quarters=%d)", cik10, quarters)
    try:
        facts = await fetch_company_facts(cik10)
    except Exception as e:
        logger.error("EDGAR facts fetch failed for CIK %s: %s", cik10, e)
        raise HTTPException(status_code=502, detail=f"EDGAR fetch failed: {e}")

    revenue_concept, revenue_rows = _select_best_concept_with_rows(facts, REVENUE_CONCEPTS)
    gross_concept, gross_rows = _select_best_concept_with_rows(
        facts, GROSS_PROFIT_CONCEPTS, allow_stale_fallback=False
    )
    cogs_concept, cogs_rows = _select_best_concept_with_rows(
        facts, COST_OF_REVENUE_CONCEPTS, allow_stale_fallback=False
    )
    opincome_concept, opincome_rows = _select_best_concept_with_rows(facts, OPERATING_INCOME_CONCEPTS)
    netincome_concept, netincome_rows = _select_best_concept_with_rows(facts, NET_INCOME_CONCEPTS)
    eps_concept, eps_rows = _select_best_concept_with_rows(facts, EPS_DILUTED_CONCEPTS)

    rev_q = _prefer_quarterly_filing_rows(revenue_rows)[:quarters + 4]  # extra for YoY lookback

    gp_q  = _prefer_quarterly_filing_rows(gross_rows)
    cogs_q = _prefer_quarterly_filing_rows(cogs_rows)
    oi_q  = _prefer_quarterly_filing_rows(opincome_rows)
    ni_q  = _prefer_quarterly_filing_rows(netincome_rows)
    eps_q = _prefer_quarterly_filing_rows(eps_rows)

    rev_idx = _map_period_to_value(rev_q)
    gp_idx  = _map_period_to_value(gp_q)
    cogs_idx = _map_period_to_value(cogs_q)
    oi_idx  = _map_period_to_value(oi_q)
    ni_idx  = _map_period_to_value(ni_q)
    eps_idx = _map_period_to_value(eps_q)

    revenue_source_label = "reported"
    if revenue_rows and not _is_recent_concept(revenue_rows):
        revenue_source_label = "reported_stale"

    operating_income_source_label = "reported"
    if opincome_rows and not _is_recent_concept(opincome_rows):
        operating_income_source_label = "reported_stale"

    net_income_source_label = "reported"
    if netincome_rows and not _is_recent_concept(netincome_rows):
        net_income_source_label = "reported_stale"

    eps_source_label = "reported"
    if eps_rows and not _is_recent_concept(eps_rows):
        eps_source_label = "reported_stale"

    # Build output for most recent `quarters` periods
    output = []
    for row in rev_q[:quarters]:
        period = row["period"]
        rev    = rev_idx.get(period)
        gp     = gp_idx.get(period)
        cogs   = cogs_idx.get(period)
        oi     = oi_idx.get(period)
        ni     = ni_idx.get(period)
        eps    = eps_idx.get(period)

        gross_profit_source = "reported"
        if gp is None and rev is not None and cogs is not None:
            gp = rev - cogs
            gross_profit_source = "derived_from_cost_of_revenue"

        gross_margin = _calculate_margin_pct(gp, rev)
        operating_margin = _calculate_margin_pct(oi, rev)
        net_margin = _calculate_margin_pct(ni, rev)

        # Find same period 1 year prior (subtract ~365 days = period ending ~1yr ago)
        # EDGAR periods are YYYY-MM-DD; YoY = same month 1 year back
        prior_period = _find_prior_year_comparable_period(period, list(rev_idx.keys()))
        prior_rev = rev_idx.get(prior_period) if prior_period else None

        item = {
            "period":           period,
            "form":             row["form"],
            "filed":            row["filed"],
            "revenue":          rev,
            "gross_profit":     gp,
            "operating_income": oi,
            "net_income":       ni,
            "eps_diluted":      eps,
            "gross_margin_pct":    gross_margin,
            "operating_margin_pct": operating_margin,
            "net_margin_pct":      net_margin,
            "revenue_yoy_pct":     _calculate_yoy_growth_pct(rev, prior_rev),
            "metric_sources": {
                "revenue": _label_metric_source(rev, revenue_source_label),
                "gross_profit": _label_metric_source(gp, gross_profit_source),
                "gross_margin_pct": _label_metric_source(gross_margin, gross_profit_source),
                "operating_income": _label_metric_source(oi, operating_income_source_label),
                "operating_margin_pct": _label_metric_source(operating_margin, operating_income_source_label),
                "net_income": _label_metric_source(ni, net_income_source_label),
                "net_margin_pct": _label_metric_source(net_margin, net_income_source_label),
                "eps_diluted": _label_metric_source(eps, eps_source_label),
            },
        }
        if debug:
            item["debug"] = {
                "prior_period_for_yoy": prior_period,
                "prior_revenue_for_yoy": prior_rev,
                "row_context": _build_row_debug_snapshot(row),
                "cost_of_revenue": cogs,
                "gross_profit_source": gross_profit_source,
            }
        output.append(item)

    if not output:
        raise HTTPException(status_code=404, detail="No quarterly financial data found for this company")

    response = {
        "cik":    cik10,
        "name":   facts.get("entityName"),
        "periods": output,
        "concepts_used": {
            "revenue": revenue_concept,
            "gross_profit": gross_concept,
            "cost_of_revenue": cogs_concept,
            "operating_income": opincome_concept,
            "net_income": netincome_concept,
            "eps_diluted": eps_concept,
        },
        "profitability_profile": _build_profitability_profile(
            facts.get("entityName"),
            output[0].get("gross_margin_pct") if output else None,
            cogs_concept is not None,
        ),
    }

    if debug:
        response["diagnostics"] = {
            "normalization": {
                "quarter_duration_days_range": [70, 120],
                "prefer_form": "10-Q",
                "yoy_prior_match_tolerance_days": 10,
                "max_concept_age_days": MAX_CONCEPT_AGE_DAYS,
            },
            "concept_candidates": {
                "revenue": _build_concept_diagnostics(facts, REVENUE_CONCEPTS, revenue_concept),
                "gross_profit": _build_concept_diagnostics(facts, GROSS_PROFIT_CONCEPTS, gross_concept),
                "cost_of_revenue": _build_concept_diagnostics(facts, COST_OF_REVENUE_CONCEPTS, cogs_concept),
                "operating_income": _build_concept_diagnostics(facts, OPERATING_INCOME_CONCEPTS, opincome_concept),
                "net_income": _build_concept_diagnostics(facts, NET_INCOME_CONCEPTS, netincome_concept),
                "eps_diluted": _build_concept_diagnostics(facts, EPS_DILUTED_CONCEPTS, eps_concept),
            },
        }

    return response

