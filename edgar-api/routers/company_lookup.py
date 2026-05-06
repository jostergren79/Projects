"""
Lookup endpoints:
    GET /company?ticker=AAPL
        Returns CIK, company metadata, and last filing dates by ticker.

    GET /company/search?name=apple&limit=10
        Returns best ticker/company matches by company name.

    GET /company/resolve?q=nike
        Smart resolver that accepts ticker OR company name and returns best match.

    GET /company/object/{cik}
        Consolidated company object (metadata + filing snapshot + fact coverage).
"""

import re
from fastapi import APIRouter, HTTPException, Query
from edgar_client import get_ticker_map, get_submissions, get_company_facts, pad_cik
from routers.financial_metrics import (
    _select_best_concept_with_rows,
    REVENUE_CONCEPTS,
    GROSS_PROFIT_CONCEPTS,
    OPERATING_INCOME_CONCEPTS,
    NET_INCOME_CONCEPTS,
    EPS_DILUTED_CONCEPTS,
)

router = APIRouter()

LEGAL_SUFFIXES = {
    "INC", "INCORPORATED", "CORP", "CORPORATION", "CO", "COMPANY", "PLC",
    "LTD", "LIMITED", "LLC", "LP", "NV", "AG", "SA", "HOLDINGS", "HOLDING",
}


def _normalize(text: str) -> str:
    """Normalize to alphanumeric only, preserving word boundaries."""
    return " ".join(re.sub(r"[^A-Z0-9]+", " ", text.upper()).split())


def _normalize_with_hyphens(text: str) -> str:
    """Normalize but keep hyphens within words for fuzzy matching."""
    # First, collapse multiple hyphens/spaces into single hyphens
    text = re.sub(r"[-\s]+", "-", text.upper().strip())
    # Remove only truly invalid chars, keep alphanumerics and hyphens
    text = re.sub(r"[^A-Z0-9\-]", "", text)
    return text


def _tokens(text: str) -> list:
    return [t for t in _normalize(text).split() if t and t not in LEGAL_SUFFIXES]


def _levenshtein_distance(s1: str, s2: str) -> int:
    """Calculate Levenshtein distance for fuzzy token matching."""
    if len(s1) < len(s2):
        return _levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    
    prev_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        curr_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = prev_row[j + 1] + 1
            deletions = curr_row[j] + 1
            substitutions = prev_row[j] + (c1 != c2)
            curr_row.append(min(insertions, deletions, substitutions))
        prev_row = curr_row
    
    return prev_row[-1]


def _fuzzy_token_match(q_token: str, title_tokens: list, max_distance: int = 2) -> bool:
    """Check if query token is close to any title token (fuzzy match)."""
    for t_token in title_tokens:
        dist = _levenshtein_distance(q_token, t_token)
        if dist <= max_distance and dist < len(q_token) / 2:
            return True
    return False


def _score_entry(query: str, entry: dict):
    """Return tuple(score, reason) or (None, None) for non-matches."""
    q_raw = query.strip().upper()
    q_norm = _normalize(q_raw)
    q_tokens = _tokens(q_raw)

    ticker = str(entry.get("ticker", "")).upper()
    title = str(entry.get("title", "")).upper()
    title_norm = _normalize(title)
    title_tokens = _tokens(title)

    if not q_norm:
        return None, None

    # Strongest signals: exact matches
    if q_raw == ticker:
        return 300, "exact_ticker"
    if q_norm == title_norm:
        return 280, "exact_name"
    if title_norm.startswith(q_norm + " "):
        return 260, "name_prefix"

    if q_tokens:
        # Strong signal: every query token exists in company tokens.
        if all(t in title_tokens for t in q_tokens):
            bonus = max(0, 20 - (len(title_tokens) - len(q_tokens)) * 2)
            return 240 + bonus, "all_tokens_match"
        
        # Fuzzy token matching: allow close matches (typos, variations)
        fuzzy_matches = sum(1 for t in q_tokens if t in title_tokens or _fuzzy_token_match(t, title_tokens))
        if fuzzy_matches == len(q_tokens):
            # All query tokens found (exact or fuzzy)
            bonus = max(0, 15 - (len(title_tokens) - len(q_tokens)) * 2)
            return 235 + bonus, "fuzzy_all_tokens"
        if fuzzy_matches > 0:
            # Some tokens found via fuzzy match
            return 175 + fuzzy_matches * 12, "fuzzy_partial_tokens"
        
        # Partial token overlap for cases like "chick" in "chick-fil-a"
        overlap = len(set(q_tokens) & set(title_tokens))
        if overlap > 0:
            return 180 + overlap * 10, "partial_tokens"

    if q_norm in title_norm:
        return 170, "name_contains"
    if ticker.startswith(q_raw):
        return 160, "ticker_prefix"
    if q_raw in ticker:
        return 150, "ticker_contains"

    return None, None


async def _company_payload(entry: dict) -> dict:
    cik10 = pad_cik(entry["cik_str"])
    subs = await get_submissions(cik10)

    filings = subs.get("filings", {}).get("recent", {})
    forms   = filings.get("form", [])
    dates   = filings.get("filingDate", [])

    last_10k = next((dates[i] for i, f in enumerate(forms) if f == "10-K"), None)
    last_10q = next((dates[i] for i, f in enumerate(forms) if f == "10-Q"), None)

    return {
        "ticker":      entry["ticker"].upper(),
        "cik":         cik10,
        "name":        subs.get("name"),
        "sic":         subs.get("sic"),
        "sic_description": subs.get("sicDescription"),
        "state":       subs.get("stateOfIncorporation"),
        "fiscal_year_end": subs.get("fiscalYearEnd"),
        "last_10k":    last_10k,
        "last_10q":    last_10q,
    }


@router.get("/company")
async def company_lookup(ticker: str = Query(..., description="Stock ticker symbol, e.g. AAPL")):
    ticker = ticker.upper().strip()

    tickers = await get_ticker_map()
    if ticker not in tickers:
        raise HTTPException(status_code=404, detail=f"Ticker '{ticker}' not found in SEC EDGAR")

    return await _company_payload(tickers[ticker])


@router.get("/company/search")
async def company_search(
    name: str = Query(..., description="Company name search, e.g. Apple or Post Holdings"),
    limit: int = Query(10, ge=1, le=25, description="Maximum number of matches to return")
):
    q = name.strip()
    if len(q) < 2:
        raise HTTPException(status_code=400, detail="Search text must be at least 2 characters")

    tickers = await get_ticker_map()

    # Score matches by quality, then prefer shorter cleaner names.
    scored = []
    for tkr, entry in tickers.items():
        score, reason = _score_entry(q, entry)
        if score is not None:
            title = str(entry.get("title", "")).upper()
            tkr_u = tkr.upper()
            scored.append((score, len(_tokens(title)), len(title), len(tkr_u), tkr_u, reason, entry))

    if not scored:
        raise HTTPException(status_code=404, detail=f"No companies found for '{name}'")

    scored.sort(key=lambda x: (-x[0], x[1], x[2], x[3], x[4]))
    matches = [
        {
            "ticker": item[6]["ticker"].upper(),
            "cik": pad_cik(item[6]["cik_str"]),
            "name": item[6].get("title"),
            "score": item[0],
            "reason": item[5],
        }
        for item in scored[:limit]
    ]

    return {
        "query": name,
        "count": len(matches),
        "results": matches,
    }


@router.get("/company/resolve")
async def company_resolve(
    q: str = Query(..., description="Ticker or company name, e.g. NKE or Nike"),
    suggestions: int = Query(5, ge=1, le=10, description="Number of fallback suggestions")
):
    query = q.strip()
    if len(query) < 1:
        raise HTTPException(status_code=400, detail="Query cannot be empty")

    tickers = await get_ticker_map()
    tkr = query.upper()

    if tkr in tickers:
        company = await _company_payload(tickers[tkr])
        return {
            "query": query,
            "matched_by": "ticker",
            "company": company,
            "candidates": [{"ticker": company["ticker"], "name": company["name"], "score": 300}],
        }

    search = await company_search(name=query, limit=suggestions)
    best = search["results"][0]
    best_ticker = best["ticker"].upper()
    if best_ticker not in tickers:
        raise HTTPException(status_code=500, detail="Resolver selected a ticker not present in ticker map")
    company = await _company_payload(tickers[best_ticker])

    return {
        "query": query,
        "matched_by": "name",
        "company": company,
        "candidates": search["results"],
    }


@router.get("/company/object/{cik}")
async def company_object(cik: str):
    cik10 = pad_cik(cik)
    try:
        subs = await get_submissions(cik10)
        facts = await get_company_facts(cik10)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"EDGAR fetch failed: {e}")

    filings = subs.get("filings", {}).get("recent", {})
    forms = filings.get("form", [])
    dates = filings.get("filingDate", [])
    accession = filings.get("accessionNumber", [])
    primary_docs = filings.get("primaryDocument", [])

    recent_filings = []
    for i in range(min(len(forms), 15)):
        if forms[i] in ("10-Q", "10-K", "8-K"):
            recent_filings.append({
                "form": forms[i],
                "date": dates[i] if i < len(dates) else None,
                "accession": accession[i] if i < len(accession) else None,
                "primary_document": primary_docs[i] if i < len(primary_docs) else None,
            })

    usgaap = facts.get("facts", {}).get("us-gaap", {})
    key_concepts = [
        "Revenues",
        "GrossProfit",
        "OperatingIncomeLoss",
        "NetIncomeLoss",
        "EarningsPerShareDiluted",
        "Assets",
        "Liabilities",
        "StockholdersEquity",
        "NetCashProvidedByUsedInOperatingActivities",
    ]
    concept_coverage = {k: (k in usgaap) for k in key_concepts}

    revenue_concept, _ = _select_best_concept_with_rows(facts, REVENUE_CONCEPTS)
    gross_concept, _ = _select_best_concept_with_rows(facts, GROSS_PROFIT_CONCEPTS)
    op_concept, _ = _select_best_concept_with_rows(facts, OPERATING_INCOME_CONCEPTS)
    net_concept, _ = _select_best_concept_with_rows(facts, NET_INCOME_CONCEPTS)
    eps_concept, _ = _select_best_concept_with_rows(facts, EPS_DILUTED_CONCEPTS)

    return {
        "cik": cik10,
        "name": subs.get("name") or facts.get("entityName"),
        "tickers": subs.get("tickers", []),
        "sic": subs.get("sic"),
        "sic_description": subs.get("sicDescription"),
        "state": subs.get("stateOfIncorporation"),
        "fiscal_year_end": subs.get("fiscalYearEnd"),
        "exchanges": subs.get("exchanges", []),
        "phone": subs.get("phone"),
        "website": subs.get("website"),
        "mailing_address": subs.get("addresses", {}).get("mailing", {}),
        "business_address": subs.get("addresses", {}).get("business", {}),
        "recent_filings": recent_filings,
        "xbrl": {
            "us_gaap_concepts_count": len(usgaap),
            "key_concept_coverage": concept_coverage,
            "normalized_concepts": {
                "revenue": revenue_concept,
                "gross_profit": gross_concept,
                "operating_income": op_concept,
                "net_income": net_concept,
                "eps_diluted": eps_concept,
            },
        },
    }
