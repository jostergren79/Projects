"""
GET /company/{cik}/segments
Extracts named segment revenue from the most recent 10-Q by parsing
the XBRL R-file (rendered HTML tables) from the SEC filing archive.

Flow:
  submissions/{CIK}.json  → get latest 10-Q accession number
  Archives/.../R{n}.htm   → scan for the segment revenue table
  parse HTML table        → extract named segments + values
"""

from fastapi import APIRouter, HTTPException
from edgar_client import fetch_company_submissions, normalize_cik_to_10_digits
import httpx
import re
from html import unescape

router = APIRouter()

HEADERS = {
    "User-Agent": "edgar-api/0.1 contact@example.com",
    "Accept-Encoding": "gzip, deflate",
}

BASE_ARCHIVES = "https://www.sec.gov/Archives/edgar/data"


def _strip_tags(html: str) -> str:
    return re.sub(r"<[^>]+>", "", html)


def _parse_number(s: str):
    """Parse a financial string like '1,103.8' or '(2.8)' into a float."""
    s = unescape(s).replace("\xa0", "").replace(",", "").replace("$", "").strip()
    if not s or s in ("—", "&#8212;", "&#160;", ""):
        return None
    negative = s.startswith("(") and s.endswith(")")
    s = s.strip("()")
    try:
        val = float(s)
        return -val if negative else val
    except ValueError:
        return None


def _parse_segment_table(html: str):
    """
    Parse an R-file HTML table and extract segment names + Net Sales values.
    Returns None if the table doesn't look like a segment revenue table.
    """
    rows = re.findall(r"<tr[^>]*>(.*?)</tr>", html, re.DOTALL)
    parsed_rows = []
    for row in rows:
        cells = re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", row, re.DOTALL)
        cleaned = [unescape(_strip_tags(c)).replace("\xa0", " ").strip() for c in cells]
        cleaned = [c for c in cleaned if c and c != "&#160;"]
        if cleaned:
            parsed_rows.append(cleaned)

    for i, row in enumerate(parsed_rows):
        # Candidate segment header row: 3+ cells, purely text, no numbers
        if (
            len(row) >= 3
            and all(not re.search(r"[\d$]", c) for c in row)
            and any(len(c) > 3 for c in row)
            and not any(kw in " ".join(row).lower() for kw in ["ended", "months", "fiscal", "quarter", "period"])
        ):
            # Look for a nearby row with enough dollar values
            for j in range(i + 1, min(i + 6, len(parsed_rows))):
                value_row = parsed_rows[j]
                nums = [_parse_number(c) for c in value_row]
                nums = [n for n in nums if n is not None]
                names = [n for n in row if n.lower() != "total"]
                if len(nums) >= len(names) >= 2:
                    return [
                        {"name": n, "value": round(v * 1_000_000, 0)}
                        for n, v in zip(names, nums[:len(names)])
                    ]
    return None


async def _get_rfile(url: str) -> str:
    async with httpx.AsyncClient(headers=HEADERS, timeout=15) as client:
        r = await client.get(url)
        if r.status_code != 200:
            return ""
        return r.text


@router.get("/company/{cik}/segments")
async def company_segments(cik: str):
    cik10 = normalize_cik_to_10_digits(cik)

    try:
        subs = await fetch_company_submissions(cik10)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"EDGAR submissions fetch failed: {e}")

    filings = subs.get("filings", {}).get("recent", {})
    forms = filings.get("form", [])
    accessions = filings.get("accessionNumber", [])
    dates = filings.get("filingDate", [])

    idx = next((i for i, f in enumerate(forms) if f == "10-Q"), None)
    if idx is None:
        raise HTTPException(status_code=404, detail="No 10-Q found for this company")

    accn = accessions[idx]
    filing_date = dates[idx]
    accn_nodash = accn.replace("-", "")
    cik_int = str(int(cik10))
    base_url = f"{BASE_ARCHIVES}/{cik_int}/{accn_nodash}"

    for n in range(1, 71):
        html = await _get_rfile(f"{base_url}/R{n}.htm")
        if not html:
            break

        text = _strip_tags(html)
        if "egment" not in text:
            continue
        if not any(kw in text for kw in ("Net Sales", "Net sales", "Revenue", "revenue")):
            continue
        if "$" not in text:
            continue

        segments = _parse_segment_table(html)
        if segments and len(segments) >= 2:
            total = sum(s["value"] for s in segments)
            return {
                "cik":        cik10,
                "name":       subs.get("name"),
                "accession":  accn,
                "filed":      filing_date,
                "segments": [
                    {**s, "share_pct": round(s["value"] / total * 100, 1) if total else None}
                    for s in segments
                ],
                "total": total,
            }

    raise HTTPException(
        status_code=404,
        detail="No named segment revenue data found. Company may not report segments or XBRL tagging varies."
    )
