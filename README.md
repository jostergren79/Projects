# EdgarWolf

SEC EDGAR financial data and anomaly detection tool. Pulls data directly from public SEC filings and flags statistical deviations in margins, revenue growth, and filing behavior for any US public company.

**Live:** https://www.edgarwolf.com

---

## Architecture

Single Railway service: FastAPI backend (`edgar-api/`) serving a static HTML/JS frontend (`notes-api/public/edgar.html`).

```
edgar-api/        Python FastAPI app — API, Stripe, watchlist, caching
notes-api/public/ Static frontend — single-file HTML/JS/CSS
railway.toml      Railway deployment config
nixpacks.toml     Nixpacks start command override
requirements.txt  Points to edgar-api/requirements.txt (nixpacks detection)
```

---

## Local Development

```bash
cd edgar-api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Or use the launcher script (starts server + opens browser with dev tier):

```bash
./dev.sh [standard|pro|pro_plus]
```

Then open: http://127.0.0.1:8000

---

## Key Files

| File | Purpose |
|------|---------|
| `edgar-api/main.py` | FastAPI app, middleware, routing |
| `edgar-api/cache.py` | SQLite cache, watchlists, users tables |
| `edgar-api/edgar_client.py` | SEC EDGAR HTTP client, rate limiter |
| `edgar-api/routers/financial_metrics.py` | XBRL concept selection, margins, YoY |
| `edgar-api/routers/anomaly_flags.py` | Z-score exception flags |
| `edgar-api/routers/dashboard.py` | Aggregated single-call endpoint |
| `edgar-api/routers/checkout.py` | Stripe checkout, webhooks, subscription status |
| `edgar-api/routers/watchlist.py` | Server-side watchlist CRUD (Pro/Pro+ only) |
| `edgar-api/routers/feed.py` | Recent SEC filers for signal board |
| `notes-api/public/edgar.html` | Entire frontend (single file) |
| `METHODOLOGY.md` | Every derived metric and scoring formula |

---

## Environment Variables

Set in Railway Variables panel. See `edgar-api/.env.production.example` for the full list. Never commit real secrets.

---

## QA

Postman collection with 28 requests and 49 assertions:

```bash
cd edgar-api/postman
./run_qa.sh [local|production]   # requires: npm install -g newman
```
