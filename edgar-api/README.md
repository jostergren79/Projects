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
- GET / and GET /edgar — serves edgar.html frontend directly from FastAPI
- GET /company?ticker=AAPL
- GET /company/search?name=apple&limit=10
- GET /company/resolve?q=nike&suggestions=5
- GET /company/object/{cik}
- GET /company/{cik}/metrics
- GET /company/{cik}/segments
- GET /company/{cik}/flags
- GET /company/{cik}/summary
- GET /company/{cik}/anomalies — filing cadence and XBRL anomaly signals with upheaval score
- GET /company/{cik}/dashboard — aggregated single call: metrics + segments + flags + summary + anomalies

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

- SEC_REQUIRE_EXPLICIT_USER_AGENT
  - When true, startup fails unless SEC_USER_AGENT is set.
  - Recommended: true in production.

- SEC_HTTP_TIMEOUT_SECONDS
  - Timeout per upstream SEC request in seconds.

- SEC_HTTP_MAX_RETRIES
  - Number of retries for transient upstream failures (429/5xx, timeout, connection errors).

- SEC_HTTP_RETRY_BASE_SECONDS
  - Base delay for exponential backoff between retries.

- SEC_RATE_LIMIT_RPS
  - Outbound SEC request rate cap in requests per second (token-bucket).
  - Stay well below SEC's 10 req/s ceiling. Default: 4.

- SEC_429_COOLDOWN_SECONDS
  - Seconds to pause all outbound SEC fetches after receiving a 429 response.
  - Default: 30.

- APP_RATE_LIMIT_REQUESTS
  - Per-IP sliding window request cap for /company/* routes.
  - Default: 60.

- APP_RATE_LIMIT_WINDOW_SECONDS
  - Duration of the per-IP sliding window in seconds.
  - Default: 60.

## Derived Metric Methodology

This service applies its own logic to transform, derive, and classify financial data
in several places. The full methodology — including every formula, heuristic, and
limitation — is documented in:

**[METHODOLOGY.md](../METHODOLOGY.md)**

That document covers: XBRL concept selection, quarterly normalization, gross profit
derivation, margin calculations, YoY matching, profitability profile classification,
metric source labels, z-score exception flags, upheaval score, natural language
summary rules, recent filers discovery, and the signal board scoring model.

## Upstream resilience behavior

- Transient upstream failures are retried with exponential backoff.
- Upstream timeout errors are surfaced as HTTP 504.
- Upstream request/connection errors are surfaced as HTTP 502.
- SEC 429 responses are surfaced as HTTP 503.

## Deploy

Render config is in render.yaml.
