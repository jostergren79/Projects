# Derived Metric Methodology

This document catalogs every instance where this application applies its own logic
to transform, derive, or classify financial data beyond what SEC EDGAR reports directly.
It exists so that users and developers can evaluate the methodology and understand
exactly what they are looking at.

**Rule of thumb:** if a field in the API or UI says "Derived", "Stale", or carries a
trend arrow or classification label, its source and logic are described here.

---

## 1. XBRL Concept Selection

**File:** `edgar-api/routers/financial_metrics.py` — `_select_best_concept_with_rows()`

SEC filers use different XBRL tag names for the same underlying line item. For example,
revenue may be tagged as `Revenues`, `RevenueFromContractWithCustomerExcludingAssessedTax`,
`SalesRevenueNet`, or several others depending on the company and filing year.

**What we do:** For each metric (revenue, gross profit, operating income, net income, EPS),
we evaluate a priority list of known XBRL concepts and select the best available one using
this scoring order:

1. Recency — concept has data within the last 550 days
2. 10-Q coverage — concept appears in quarterly filings (not only annuals)
3. Row volume — more data points preferred

If no recent concept is found, we fall back to the most recent stale concept and label
the metric `reported_stale`.

**Priority lists used:**

| Metric | Concepts tried (in order) |
|--------|--------------------------|
| Revenue | `Revenues`, `RevenueFromContractWithCustomerExcludingAssessedTax`, `SalesRevenueNet`, `RevenueFromContractWithCustomerIncludingAssessedTax`, `SalesRevenueGoodsNet`, `RegulatedAndUnregulatedOperatingRevenue`, `RealEstateRevenueNet` |
| Gross Profit | `GrossProfit` |
| Cost of Revenue | `CostOfGoodsAndServicesSold`, `CostOfRevenue`, `CostOfGoodsSold`, `CostOfProductsSold` |
| Operating Income | `OperatingIncomeLoss`, `IncomeLossFromContinuingOperationsBeforeIncomeTaxesExtraordinaryItemsNoncontrollingInterest` |
| Net Income | `NetIncomeLoss`, `ProfitLoss` |
| EPS Diluted | `EarningsPerShareDiluted`, `DilutedEarningsPerShare` |

---

## 2. Quarterly Normalization (YTD Differencing)

**File:** `edgar-api/routers/financial_metrics.py` — `_normalize_row_to_quarter_value()`

Some filers report Q2 and Q3 in their 10-Q as cumulative year-to-date totals (6-month,
9-month) rather than standalone quarter amounts. SEC EDGAR stores whatever the filer
submitted, so a mix of formats can appear in the same company's history.

**What we do:** When a Q2 or Q3 row's duration exceeds 120 days (the heuristic for
"this looks cumulative"), we subtract the preceding period:

- Q2 standalone = Q2 YTD − Q1
- Q3 standalone = Q3 YTD − Q2 YTD

A row is considered a single quarter when its inclusive day span falls between 70 and
120 days. Rows that cannot be normalized (e.g., missing the prior period for differencing)
are excluded rather than shown with potentially wrong values.

---

## 3. Gross Profit Derivation

**File:** `edgar-api/routers/financial_metrics.py` — main metrics loop, `gross_profit_source`

Some companies do not file a `GrossProfit` XBRL concept (common in industries such as
financial services, real estate, and some technology companies). When direct gross profit
is unavailable for a given period, we derive it:

```
gross_profit = revenue − cost_of_revenue
```

This value is labeled `derived_from_cost_of_revenue` in the `metric_sources` field of
the API response and shown as "Derived" in the Metric Trust panel on the dashboard.
When this label appears, the gross margin figure is our calculation, not a reported value.

---

## 4. Margin Calculations

**File:** `edgar-api/routers/financial_metrics.py` — `_calculate_margin_pct()`

All percentage margin fields are computed by this service:

```
gross_margin_pct      = gross_profit      / revenue × 100
operating_margin_pct  = operating_income  / revenue × 100
net_margin_pct        = net_income        / revenue × 100
```

These are standard financial ratios. The inputs (revenue, gross profit, etc.) come from
SEC EDGAR; only the division and rounding are applied here. If any input is unavailable
the margin is returned as `null` rather than estimated.

---

## 5. Year-Over-Year Revenue Growth

**File:** `edgar-api/routers/financial_metrics.py` — `_find_prior_year_comparable_period()`, `_calculate_yoy_growth_pct()`

**What we do:** For each quarterly period, we locate the best same-quarter prior-year
period to compare against. Because fiscal quarter-end dates can shift by a few days
year over year (e.g., 2026-03-28 vs 2025-03-29), we use a ±10-day tolerance window
centered on exactly one year prior.

```
revenue_yoy_pct = (current_revenue − prior_revenue) / |prior_revenue| × 100
```

If no prior-year comparable period is found within the tolerance window, the YoY field
is returned as `null` rather than using a mismatched period.

---

## 6. Profitability Profile Classification

**File:** `edgar-api/routers/financial_metrics.py` — `_build_profitability_profile()`

To guide display decisions on the frontend, we classify each company into a profitability
model:

| Condition | Primary metric shown | Reason label |
|-----------|---------------------|--------------|
| Gross margin data is available | `gross_margin_pct` | `gross_margin_available` |
| Entity name contains BANK, BANC, FINANCIAL, CAPITAL, INSURANCE, or TRUST | `operating_margin_pct` | `financial_model_or_non_cogs_reporter` |
| No cost-of-revenue concept found | `operating_margin_pct` | `cost_of_revenue_not_reported` |
| Gross margin unavailable for other reasons | `operating_margin_pct` | `gross_margin_unavailable_for_recent_periods` |

This classification is heuristic. The keyword list for financial entities is a
best-effort approximation and will not catch every bank holding company or insurance
group.

---

## 7. Metric Source Labels

**File:** `edgar-api/routers/financial_metrics.py` — `_label_metric_source()`

Every metric in the API response carries a `metric_sources` field that indicates how
the value was obtained:

| Label | Meaning |
|-------|---------|
| `reported` | Value taken directly from the company's SEC filing |
| `derived_from_cost_of_revenue` | Gross profit computed as revenue minus cost of revenue (see §3) |
| `reported_stale` | Reported value, but the latest period is more than 550 days old |
| `not_available` | No usable data found for this metric and period |

The 550-day threshold (roughly 6 fiscal quarters) is our judgment of when data is
too old to be reliable for trend analysis.

---

## 8. Statistical Exception Flags (Z-Score)

**File:** `edgar-api/routers/anomaly_flags.py`

**What we do:** For the most recent quarter, we compute how many standard deviations
each margin metric is from the company's own trailing 8-quarter mean.

```
z = (latest_value − mean_of_trailing_history) / stdev_of_trailing_history
```

A minimum of 4 historical data points is required before a z-score is computed.

| |z| threshold | Severity label |
|---|---|
| ≥ 2.0 and < 3.0 | MEDIUM |
| ≥ 3.0 | HIGH |

**Metrics flagged:** Gross Margin %, Operating Margin %, Net Margin %, Revenue Growth YoY %

This is a purely statistical test against the company's own history — it does not
compare to industry peers or any external benchmark. A HIGH flag means the latest
quarter is an unusual result for *this company*, not necessarily for its sector.

---

## 9. Filing Stress Score

**File:** `edgar-api/routers/company_lookup.py` — `_build_anomaly_signals()`

A composite 0–100 score that aggregates structural signals from SEC filing metadata
and XBRL coverage. It is **not** a financial performance score — it measures how
unusual the company's filing posture and data coverage appear.

**Scoring formula:**

| Signal | Condition | Points |
|--------|-----------|--------|
| Base | Always | 20 |
| Filing Velocity | 2+ 8-K filings within 10 days, or 8-K filed within 14 days of a 10-Q | +30 |
| XBRL Concept Count | ≥ 450 concepts | +10 |
| | ≥ 300 concepts | +5 |
| | < 300 concepts | +0 |
| Key Concept Coverage | All core concepts present | +15 |
| | One or more missing | +7 |
| Normalized Mapping | 4 or 5 of 5 core concepts mapped | +15 |
| | Fewer than 4 mapped | +6 |
| Peer Context | SIC code and exchange both present | +10 |

**Status thresholds:** ELEVATED ≥ 70 · MODERATE ≥ 40 · LOW < 40

**Limitation:** Filing bursts are heuristic. A legitimate restatement or voluntary
disclosure can trigger an ELEVATED score with no negative implication.

---

## 10. Natural Language Summary

**File:** `edgar-api/routers/narrative_summary.py`

The one-paragraph summary displayed under each company name is generated by
rules-based logic — it is not AI-generated or sourced from any external narrative.

**Outlook sentence logic:**

| Condition | Sentence appended |
|-----------|------------------|
| Revenue YoY ≥ +5% AND gross margin expanded YoY | "Overall, the quarter reflected strong top-line momentum with improving profitability." |
| Revenue YoY < −5% | "The quarter reflected revenue pressure, with top-line results below prior-year levels." |
| Revenue YoY ≥ 0% (and not ≥ +5% with expansion) | "Results were broadly stable relative to the prior year." |
| Revenue YoY < 0% (and not < −5%) | "The quarter reflected modest revenue headwinds relative to the prior year." |

All other sentences in the summary (revenue amount, margin direction, EPS) are
constructed by substituting computed values into fixed templates. No inference or
generation is involved.

---

## 11. Recent Filers Discovery

**File:** `edgar-api/edgar_client.py` — `fetch_recent_filers()`  
**Endpoint:** `GET /feed/recent`

**What we do:** Query the SEC EDGAR full-text search API (EFTS) for 10-Q and 10-K
filings within a configurable look-back window (default 14 days):

```
https://efts.sec.gov/LATEST/search-index
  ?q=""&forms=10-Q,10-K&dateRange=custom&startdt=...&enddt=...
```

The EFTS response returns one record per file within each filing (exhibits, cover
pages, etc.), so results are deduplicated by CIK. Company name is extracted from
the `display_names` field which takes the form `"Company Name  (TICKER)  (CIK XXXXXXXXXX)"` —
we split on `"  ("` and take the first segment.

The frontend requests up to 80 candidates (`limit=80`) to ensure enough companies
are available to fill both signal board columns.

**Limitation:** EFTS returns up to 100 records per request. With deduplication the
practical limit is roughly 30–80 unique companies per 14-day window depending on
filing volume. High-volume filing periods (e.g., earnings season) will surface more.

---

## 12. Signal Board: Strengthening / Weakening

**File:** `notes-api/public/edgar.html` — `scoreCompany()`

The two-column signal board on the home page is the only logic applied entirely
on the frontend (in the browser). It classifies each recently-filed company using
three signals derived from the most recent two quarters returned by the metrics API.

**Signal model:**

| # | Signal | Positive (+1) | Negative (−1) |
|---|--------|--------------|---------------|
| 1 | Revenue Growth YoY | `revenue_yoy_pct ≥ 0` | `revenue_yoy_pct < 0` |
| 2 | Gross Margin trend | `gross_margin_pct` rose vs. prior quarter | `gross_margin_pct` fell vs. prior quarter |
| 3 | Operating Margin trend | `operating_margin_pct` rose vs. prior quarter | `operating_margin_pct` fell vs. prior quarter |

Net score = sum of votes (range: −3 to +3).

**Classification:**

| Net Score | Column |
|-----------|--------|
| > 0 | STRENGTHENING |
| < 0 | WEAKENING |
| = 0 | Excluded (mixed signals) |

**Signals 2 and 3** compare the latest quarter to the immediately prior quarter
(not the year-ago quarter), capturing recent directional momentum rather than
cyclical or seasonal patterns.

**Display cap and ordering:**

The board fetches up to 80 recent filers from `/feed/recent`. Within each column,
companies are sorted by filing date descending (most recently filed first) and
capped at **10 per column**, giving a maximum of 20 rows total. If fewer than 10
companies score into a column during a quiet filing period, all available entries
are shown.

The chronological ordering means the board reflects the freshest available filings,
not the highest-scoring ones. Score magnitude is shown on each row for reference
but does not affect order or inclusion.

**This is a momentum signal, not a valuation.** A company in WEAKENING may be
attractively priced; a company in STRENGTHENING may already reflect good news.
Always verify with primary SEC filings before making investment decisions.
