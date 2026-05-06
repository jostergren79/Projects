"""
GET /company/{cik}/flags
Exception flags — metrics that are statistically unusual vs. the company's
own trailing history (z-score > 2.0 or < -2.0 = flagged).

Checks: revenue growth, gross margin, operating margin, net margin.
"""

from fastapi import APIRouter, HTTPException
from edgar_client import fetch_company_facts, normalize_cik_to_10_digits
from routers.financial_metrics import (
    _select_best_concept_rows, _map_period_to_value,
    _calculate_margin_pct,
    _prefer_quarterly_filing_rows,
    _find_prior_year_comparable_period,
    REVENUE_CONCEPTS,
    GROSS_PROFIT_CONCEPTS,
    OPERATING_INCOME_CONCEPTS,
    NET_INCOME_CONCEPTS,
)
import statistics

router = APIRouter()

LOOKBACK = 8   # quarters of history to establish baseline


def _zscore(value, history):
    if len(history) < 4:
        return None
    try:
        mean = statistics.mean(history)
        stdev = statistics.stdev(history)
        if stdev == 0:
            return None
        return round((value - mean) / stdev, 2)
    except Exception:
        return None


def _flag(metric: str, period: str, value: float, z) -> dict:
    if z is None:
        return None
    severity = None
    if abs(z) >= 3.0:
        severity = "HIGH"
    elif abs(z) >= 2.0:
        severity = "MEDIUM"

    if severity is None:
        return None

    direction = "above" if z > 0 else "below"
    return {
        "metric":    metric,
        "period":    period,
        "value":     round(value, 2),
        "z_score":   z,
        "severity":  severity,
        "note":      f"{metric} is {abs(z):.1f} standard deviations {direction} historical average",
    }


@router.get("/company/{cik}/flags")
async def company_flags(cik: str):
    cik10 = normalize_cik_to_10_digits(cik)
    try:
        facts = await fetch_company_facts(cik10)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"EDGAR fetch failed: {e}")

    rev_rows = _prefer_quarterly_filing_rows(_select_best_concept_rows(facts, REVENUE_CONCEPTS))
    gp_rows  = _prefer_quarterly_filing_rows(_select_best_concept_rows(facts, GROSS_PROFIT_CONCEPTS))
    oi_rows  = _prefer_quarterly_filing_rows(_select_best_concept_rows(facts, OPERATING_INCOME_CONCEPTS))
    ni_rows  = _prefer_quarterly_filing_rows(_select_best_concept_rows(facts, NET_INCOME_CONCEPTS))

    rev_idx = _map_period_to_value(rev_rows)
    gp_idx  = _map_period_to_value(gp_rows)
    oi_idx  = _map_period_to_value(oi_rows)
    ni_idx  = _map_period_to_value(ni_rows)

    # Build time series of margins across all available quarters
    periods = sorted(rev_idx.keys(), reverse=True)[:LOOKBACK + 4]

    gross_margins = []
    op_margins    = []
    net_margins   = []
    rev_growths   = []

    series = []
    for p in periods:
        rev = rev_idx.get(p)
        gp  = gp_idx.get(p)
        oi  = oi_idx.get(p)
        ni  = ni_idx.get(p)
        if rev is None:
            continue

        gm = _calculate_margin_pct(gp, rev)
        om = _calculate_margin_pct(oi, rev)
        nm = _calculate_margin_pct(ni, rev)

        # YoY revenue growth
        prior = _find_prior_year_comparable_period(p, list(rev_idx.keys()))
        prior_rev = rev_idx.get(prior) if prior else None
        rg = round((rev - prior_rev) / abs(prior_rev) * 100, 2) if (prior_rev and prior_rev != 0) else None

        if gm is not None: gross_margins.append((p, gm))
        if om is not None: op_margins.append((p, om))
        if nm is not None: net_margins.append((p, nm))
        if rg is not None: rev_growths.append((p, rg))

    flags = []

    def check_series(labeled_series: list[tuple], metric_name: str):
        if not labeled_series:
            return
        # Use all but the most recent as history baseline
        history_vals = [v for _, v in labeled_series[1:]]
        latest_period, latest_val = labeled_series[0]
        z = _zscore(latest_val, history_vals)
        f = _flag(metric_name, latest_period, latest_val, z)
        if f:
            flags.append(f)

    check_series(gross_margins, "Gross Margin %")
    check_series(op_margins,    "Operating Margin %")
    check_series(net_margins,   "Net Margin %")
    check_series(rev_growths,   "Revenue Growth YoY %")

    return {
        "cik":        cik10,
        "name":       facts.get("entityName"),
        "flags":      flags,
        "flag_count": len(flags),
        "note":       "Flags are z-score based vs. the company's own trailing history. MEDIUM = |z|≥2, HIGH = |z|≥3.",
    }
