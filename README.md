# EdgarWolf

SEC EDGAR financial data and anomaly detection tool. Pulls data directly from public SEC filings and flags statistical deviations in margins, revenue growth, and filing behavior for any US public company.

**Live:** https://www.edgarwolf.com
**Version:** see [`VERSION`](VERSION) — release history in [`CHANGELOG.md`](CHANGELOG.md)

---

## Features

- **Signal board** — Strengthening / Weakening columns, 5–25 companies per side, on-demand
- **Exception flags** — Z-score deviations on gross margin, operating margin, net margin, revenue YoY
- **Filing Stress Score** — 0–100 composite of margin, growth, and filing-behavior signals
- **Peer comparison, segment breakdown, source-filing links, natural-language summary**
- **Watchlist** — server-side for Pro/Pro+ (SQLite, keyed by Stripe `customer_id` resolved server-side from the session cookie), localStorage for Standard
- **Magic-link sign-in** — paying users restore access from any device via a short-lived signed email link; session is an httpOnly cookie, customer_id never reaches the frontend
- **CSV / JSON export** (Pro/Pro+)
- **Email alerts** — hourly M–F 8 AM–6 PM ET, fires on new 10-Q / 10-K / 8-K + anomaly signal (Pro+, LIVE)
- **Free-tier weekly digest** — email capture live; Sunday send job pending
- **Product analytics** — PostHog (US Cloud, project 424339) with session replay; Stripe webhook → welcome email via Resend

See [`METHODOLOGY.md`](METHODOLOGY.md) for every derived metric and scoring formula.

---

## Pricing tiers

| Tier | Price | Gated features |
|------|-------|----------------|
| Standard | $0 | Signal board, search, KPI grid, narrative summary, 8-quarter charts, data table |
| Pro | $19/mo | + Exception flags, Filing Stress Score, peer comparison, segment breakdown, source filing, watchlist, CSV/JSON export |
| Pro+ | $99/mo | + Email alerts |

Feature gating is enforced server-side via Stripe `customer_id` lookup; the dev tier bypass `?dev_tier=pro` works on localhost only.

---

## Architecture

Single Railway service: FastAPI backend (`edgar-api/`) serving a static HTML/JS frontend (`edgar-frontend/`).

```
edgar-api/         Python FastAPI app — API, Stripe, watchlist, alerts, caching
edgar-frontend/    Static frontend — single-file HTML/JS/CSS + legal pages
railway.toml       Railway deployment config
nixpacks.toml      Nixpacks start command override
requirements.txt   Points to edgar-api/requirements.txt (nixpacks detection)
```

---

## Local development

```bash
cd edgar-api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000 --proxy-headers --forwarded-allow-ips='*'
```

Or use the launcher script (starts server + opens browser with dev tier):

```bash
./dev.sh [standard|pro|pro_plus]
```

Then open http://127.0.0.1:8000. Dev tier bypass: `?dev_tier=pro` (localhost only). Amber toggle button is in the header.

---

## Key files

### Backend (`edgar-api/`)

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app, middleware, security headers, rate limiter, routing |
| `cache.py` | SQLite cache + `watchlists`, `users`, `digest_subscribers` tables |
| `auth.py` | Magic-link HMAC token mint/verify + session cookie helpers + `mask_email` |
| `edgar_client.py` | SEC EDGAR HTTP client, rate limiter, explicit User-Agent |
| `scheduler.py` | Hourly email-alert job (Pro+) — new filings + anomaly signal |
| `routers/financial_metrics.py` | XBRL concept selection, YTD normalization, margins |
| `routers/anomaly_flags.py` | Z-score exception flags |
| `routers/dashboard.py` | Aggregated single-call endpoint |
| `routers/checkout.py` | Stripe checkout, webhooks, post-payment cookie issuance, billing portal |
| `routers/auth_router.py` | Magic-link auth — `/auth/request`, `/auth/verify`, `/auth/logout`, `/auth/whoami` |
| `routers/watchlist.py` | Server-side watchlist CRUD (Pro/Pro+ only, cookie-authenticated) |
| `routers/alerts.py` | Pro+ email-alert preferences |
| `routers/digest.py` | Free-tier digest signup, welcome email, unsubscribe |
| `routers/feed.py` | Recent SEC filers for signal board |
| `routers/company_lookup.py` | Ticker → CIK + entity-type detection |
| `routers/narrative_summary.py` | Plain-English company summary |
| `routers/segment_breakdown.py` | Segment-level revenue (Pro/Pro+) |
| `routers/analytics.py` | Event logging endpoint (mirrors to PostHog) |

### Frontend (`edgar-frontend/`)

| File | Purpose |
|------|---------|
| `edgar.html` | Entire app (single file: HTML/CSS/JS) |
| `index.html` | Landing/redirect |
| `privacy.html`, `terms.html` | Legal pages |
| `sitemap.xml`, `robots.txt` | SEO |
| `og-image.png`, `favicon*.png` | Social/brand assets |

### Docs

| File | Purpose |
|------|---------|
| [`METHODOLOGY.md`](METHODOLOGY.md) | Every derived metric and scoring formula. Updated alongside any new scoring/classification/polling/trigger logic. |
| [`SECURITY.md`](SECURITY.md) | Canonical security posture — transport, API hardening, payments, auth, data handling, secrets, ops |
| [`CHANGELOG.md`](CHANGELOG.md) | Release history (Keep a Changelog format, SemVer) |
| [`CLAUDE.md`](CLAUDE.md) | Stable project context, rules, and the start/end session sequences (auto-loaded by Claude Code) |
| [`STATE.md`](STATE.md) | Live state for Claude Code sessions — metrics, active priorities, next-session plan |
| [`DECISIONS_ARCHIVE.md`](DECISIONS_ARCHIVE.md) | Settled architectural / product decisions |

---

## Environment variables

Set in the Railway Variables panel. See `edgar-api/.env.production.example` for the full list. Never commit real secrets.

Notable variables:

- `SEC_USER_AGENT`, `SEC_REQUIRE_EXPLICIT_USER_AGENT=true` — SEC compliance
- `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRO_PRICE_ID`, `STRIPE_PRO_PLUS_PRICE_ID`
- `MAGIC_LINK_SECRET` — HMAC key for magic-link tokens + session cookies. Generate with `python -c 'import secrets; print(secrets.token_urlsafe(48))'`
- `APP_URL` — public site URL (`https://www.edgarwolf.com` in prod). Controls magic-link URLs and the cookie `Secure` flag.
- `RESEND_API_KEY` — welcome + alert + digest + magic-link emails
- `POSTHOG_KEY` — exposed to frontend via `/config.js` (no key committed)
- `DEV_SECRET` — gates `/test/*` endpoints in production

---

## QA

Postman collection with 28 requests and 49 assertions:

```bash
cd edgar-api/postman
./run_qa.sh [local|production]   # requires: npm install -g newman
```

---

## Security

See [`SECURITY.md`](SECURITY.md) for the full posture document. Highlights as of v1.6.0:

- Magic-link sign-in (HMAC-SHA256, 15-min TTL), httpOnly Secure SameSite=Lax session cookie — customer_id never reaches the frontend

- Full browser security header set (CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, HSTS)
- Proxy-aware rate limiting (200/min per real client IP) on all public endpoints
- HTML output encoding via `escapeAttr()` on every `innerHTML` injection point
- Script-safe JSON helper on `/success` page (escapes `<`, `>`, `&` for `</script>` resistance)
- Stripe webhook signature verification (hard-fails on missing secret)
- Dev test endpoints gated by `DEV_SECRET`
- `?debug=true` gated to dev only

Report vulnerabilities per the policy in `SECURITY.md`.

---

## Deployment

Railway auto-deploys on push to `main`. End-of-session checklist:

1. Update `CHANGELOG.md`
2. Bump `VERSION`, footer in `edgar-frontend/edgar.html`, and `version=` in `edgar-api/main.py`
3. `git commit && git tag vX.Y.Z && git push --tags`
