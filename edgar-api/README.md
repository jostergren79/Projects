# EDGAR API

FastAPI service that normalizes SEC EDGAR company facts for dashboard consumption.

## Runtime

- Python 3.9+
- FastAPI 0.111.0
- Uvicorn 0.29.0
- httpx 0.27.0
- python-dotenv 1.0.1

See pinned versions in requirements.txt.

## Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
uvicorn main:app --app-dir /absolute/path/to/edgar-api --host 127.0.0.1 --port 8000
```

Health:

```bash
curl http://127.0.0.1:8000/health
```

## Endpoints

- GET /health
- GET /company?ticker=AAPL
- GET /company/search?name=apple&limit=10
- GET /company/resolve?q=nike&suggestions=5
- GET /company/object/{cik}
- GET /company/{cik}/metrics
- GET /company/{cik}/segments
- GET /company/{cik}/flags
- GET /company/{cik}/summary

## Metrics behavior highlights

- Quarterly normalization for mixed 10-Q / 10-K contexts
- Tolerant same-quarter prior-year matching for YoY
- Gross profit fallback from cost of revenue when direct gross profit is missing
- Per-metric source labeling (reported, derived, stale, unavailable)
- Profitability profile field for sector/model-aware fallback guidance
- Optional diagnostics via query parameter:

```text
/company/{cik}/metrics?debug=true
```

## Production env vars

Use [edgar-api/.env.production.example](edgar-api/.env.production.example) as the reference template for production values.

- CORS_ALLOW_ORIGINS
  - Comma-separated list of allowed frontend origins.
  - Example: https://app.example.com,https://www.example.com

- SEC_USER_AGENT
  - Full SEC-compliant user-agent string.
  - Example: edgar-api/1.0 ops@example.com

- SEC_APP_NAME and SEC_CONTACT_EMAIL (optional)
  - Used to compose the User-Agent when SEC_USER_AGENT is not provided.

## Deploy

Render config is in render.yaml.
