# EdgarWolf — Claude Context Doc

**Current version: v1.5.2** (2026-05-14) — see `CHANGELOG.md` for full release history.

Paste this file at the start of every Claude conversation to restore full context.
Update metrics, version, and priorities at the end of every relevant session.

---

## 1. Product & Stack

**Product:** EdgarWolf (www.edgarwolf.com)
SEC EDGAR financial data and anomaly detection tool. Pulls data directly from public SEC filings and flags statistical deviations in margins, revenue growth, and filing behavior for any US public company.

**Key features:**
- Signal board (Strengthening / Weakening — on-demand, user picks 5–25 companies per column)
- Z-score exception flags (gross margin, operating margin, net margin, revenue YoY)
- Filing Stress Score (0–100 composite filing stress signal)
- Watchlist — server-side for Pro/Pro+ (SQLite, keyed by Stripe customer_id), localStorage for Standard
- Peer comparison, CSV/JSON export
- Metric Trust panel (reported vs. derived vs. stale labeling)
- Natural language summary (rules-based, not AI-generated)
- Analytics event tracking via PostHog (US Cloud) + Railway log redundancy. Autocapture, heatmaps, web vitals, session recordings all on. Stripe customer_id used for identify.
- Stripe payment integration — Pro $19.00/mo, Pro+ $99/mo (LIVE)
- Stripe Customer Portal — self-serve cancel/manage for paid users (LIVE)
- Email alerts — LIVE for Pro+ users. Hourly polling M–F 8 AM–6 PM ET. Fires on new 10-Q/10-K/8-K + anomaly signal.
- Free-tier email capture — dismissable banner offering weekly Filing Stress digest. Captures email + sends welcome via Resend. Weekly digest send job not yet built.

**Stack:** FastAPI (Python) backend + static HTML/JS frontend, single Railway service
**Live URL:** https://www.edgarwolf.com
**Repo:** github.com/jostergren79/Projects
**Railway service:** edgar-api-production-eff0.up.railway.app (public temp URL while DNS propagates)
**Email:** jason@edgarwolf.com (Microsoft 365 via GoDaddy)

**Key files:**
- `edgar-api/main.py` — FastAPI app, middleware, routing
- `edgar-api/edgar_client.py` — SEC EDGAR HTTP client, rate limiter, stale cache fallback
- `edgar-api/cache.py` — SQLite cache + watchlists + users tables, thread-safe
- `edgar-api/routers/financial_metrics.py` — XBRL concept selection, YTD normalization, margins
- `edgar-api/routers/dashboard.py` — aggregated single-call endpoint
- `edgar-api/routers/anomaly_flags.py` — z-score exception flags
- `edgar-api/routers/feed.py` — recent SEC filers for signal board (limit up to 200)
- `edgar-api/routers/analytics.py` — event logging endpoint
- `edgar-api/routers/checkout.py` — Stripe checkout, webhook, subscription status, billing portal
- `edgar-api/routers/watchlist.py` — server-side watchlist CRUD (Pro/Pro+ only, X-Customer-Id gated)
- `edgar-api/routers/alerts.py` — dev-only test alert send via Resend
- `edgar-api/routers/digest.py` — free-tier email capture + welcome email + unsubscribe page
- `edgar-frontend/edgar.html` — entire frontend (single file)
- `railway.toml` — Railway deployment config (repo root)
- `METHODOLOGY.md` — documents every derived metric and scoring formula

---

## 2. Founder Situation

**Name:** Jason Ostergren
**Income target:** $8k/month take home to replace current salary
**Users needed:** 80 paying users at $99/month
**Backup:** Job offer from Post Consumer Brands (in final stages)
**Decision rule:** 5+ paying users by end of week 4 = pursue EdgarWolf full time. Fewer = take the job, build nights and weekends.
**Audience:** Zero — recently created personal X account (not yet posted)
**Network:** Crypto friends (potential early beta users)

**Background (important for positioning):**
Jason is an IT systems thinker, NOT a finance or investing professional. Background: 20+ years enterprise IT, Senior Business Systems Analyst, SQL/Snowflake, SAFe Product Owner, Full Stack Web Dev cert (U of Minnesota). Recently started looking at SEC filings — built EdgarWolf to scratch his own itch as an outsider who wanted to understand what was actually in the filings. This "outsider builder" angle is the honest founder story and should inform all marketing copy. Do NOT write posts implying years of financial analysis experience.

---

## 3. Pricing Model

| Tier | Price | Features |
|------|-------|----------|
| Standard | $0 | Signal board (on-demand), company search, KPI grid (latest quarter), narrative summary, 8-quarter charts, quarterly data table. Unlimited lookups. |
| Pro | $19.00/month | Everything free + Exception Flags (z-score), Filing Stress Score, Filing Signals, peer comparison, segment breakdown, source filing, watchlist (server-side synced), CSV/JSON export. |
| Pro+ | $99/month | Everything in Pro + email alerts (LIVE — hourly M–F 8 AM–6 PM ET, fires on new 10-Q/10-K/8-K + anomaly signal). |

**Feature gating is LIVE** as of May 10, 2026. Frontend gates Pro sections with upgrade cards. No backend lookup limit — differentiation is purely by feature depth, not access.

---

## 4. Current Metrics

_Update these at the end of every session._

| Metric | Value | Updated |
|--------|-------|---------|
| MRR | $0 | May 12, 2026 |
| Paying users | 0 | May 12, 2026 |
| Free signups | 0 | May 12, 2026 |

---

## 5. Marketing Assets

**Example 1 — $CAG (Conagra)**
- Gross, operating, and net margin all 3+ standard deviations below 8-quarter historical average (HIGH flags)
- Revenue declining from $3.2B to $2.4B over 8 quarters
- Filing Stress Score: 70/100 ELEVATED

**Example 2 — $GIS (General Mills)**
- Filing Stress Score: 100/100 ELEVATED
- Filing Velocity: ELEVATED — 4 eight-K filings within 2 days
- Revenue YoY growth 3.3 standard deviations below historical average (HIGH flag)
- Revenue declining from $5.2B to $3.8B over 8 quarters
- Margins showing cliff drop in most recent quarters

**Example 3 — $STEM (Stem Inc, CIK 0001758766)**
- Net revenue $29M Q1 2026, down -10.8% YoY
- Gross margin expanded 5.0pp YoY to 37.4%
- Good "here's the data, Pro shows why" upgrade hook

**Target channels:**
- r/SecurityAnalysis — post drafted and ready, waiting on mod approval (requested May 10)
- X (Twitter) — **PRIMARY PLATFORM.** Personal account (branded to Jason, not EdgarWolf brand account). Kickoff post drafted but not yet posted. Strategy: honest outsider builder angle, lead with real data ($GIS Filing Stress Score 100/100), use cashtags $GIS $CAG $CPB + hashtags #FinTwit #SECFilings. Follow up same day with replies on active $GIS/$CAG/$CPB threads.
- Finance Substack writers — free Pro access in exchange for a mention
- Crypto friends — free beta access, honest feedback
- StockTwits — not yet done

**Google Search Console:** Verified and active for www.edgarwolf.com. Meta verification tag deployed in edgar.html. Sitemap not yet submitted.

---

## 6. Active Priorities

_Replace completed items each session. Keep this list short._

**Immediate (next session):**
- [ ] Post on r/SecurityAnalysis when mod approval comes through
- [ ] Send beta invites to 2–3 crypto friends with free Pro access
- [ ] Identify 10 finance Substack writers and send personal outreach emails
- [ ] Continue X thread replies (3 posted May 13 on $HSY threads — target 4/day)
- [ ] Decommission Render service (manual: delete from render.com dashboard — no code references remain)

**Soon:**
- [ ] **Build the actual weekly digest send job** — Sunday cron that picks top 10 Filing Stress companies from the past week and emails all active `digest_subscribers`. Must include unsubscribe link in every send.
- [ ] Expand sitemap to include /privacy and /terms URLs

---

## 7. Key Decisions Made

_Running log of important decisions so we don't relitigate them._

- **Pricing:** $99/month justified only once email alerts are live. Without alerts it's a $19.00/month product.
- **No CRM yet:** Spreadsheet is sufficient until 80+ users. CRM is premature.
- **No scaling/automation yet:** First 30 days is manual everything. Find 10 paying users by hand before building infrastructure.
- **Filing Stress Score:** Renamed from "Upheaval Score" — better resonance with finance audience.
- **Distribution first:** Product is good enough to charge for. Distribution is the only job right now.
- **Sale target ($500k) is not realistic short term.** Realistic near-term goal is replacing income.
- **Railway deployment:** Migrated from Render free tier to Railway $5/month Hobby plan. `railway.toml` at repo root, start command `cd edgar-api && uvicorn main:app --host 0.0.0.0 --port $PORT`. Root directory in Railway set to blank (full repo deployed so `edgar-frontend` is accessible). Railway Cloudflare one-click integration used for custom domain — manages hostname verification automatically.
- **Canonical domain:** `www.edgarwolf.com` is the intended primary. `edgarwolf.com` will redirect to www via Cloudflare redirect rule (pending). Both added as Railway custom domains.
- **Cloudflare setup:** Railway one-click integration manages DNS. Do NOT manually change CNAME proxy status — Railway owns that configuration. HTTP challenge handler at `/.well-known/cf-custom-hostname-challenge/{token}` is in `main.py`.
- **Folder structure:** `notes-api/` renamed to `edgar-frontend/`. `edgar-frontend/public/` flattened to `edgar-frontend/`. `scripts/` removed, `clean.sh` at repo root.
- **Analytics via Railway logs:** Events emitted as structured log lines (grep 'EVENT' in Railway log tab). No external analytics service needed.
- **Watchlist keyed by CIK:** Ticker is unreliable (empty for many EDGAR companies). CIK is always present.
- **Server-side watchlist (v1.3.0):** Pro/Pro+ users get watchlist persisted in SQLite (`watchlists` table, keyed by Stripe customer_id). Standard users stay on localStorage. syncWatchlistFromServer() runs once per session, merges server→local and pushes local-only items up. Identity anchor = Stripe customer_id (already verified, no new auth needed).
- **SQLite persistence on Railway:** Requires a persistent volume mounted at `/app/data`. Without it, SQLite resets on every redeploy. Volume setup pending — ~$0.02/month on Railway Hobby plan.
- **Resend email domain:** edgarwolf.com DKIM + SPF + MX all verified. FROM = `EdgarWolf <alerts@edgarwolf.com>`. Test alert delivered end-to-end. Alert trigger logic (watch company → send on anomaly) not yet built.
- **DNS migration:** Moving from GoDaddy direct CNAME → Cloudflare for CNAME flattening at root domain. GoDaddy nameservers will point to Cloudflare. Railway custom domain target: `gjkthu0r.up.railway.app`.
- **Domain:** edgarwolf.com purchased. DNS migrating to Cloudflare (in progress as of May 12).
- **Email:** jason@edgarwolf.com via Microsoft 365 + GoDaddy. All public-facing email references updated.
- **Stripe session-based auth:** Without user login, subscription status is verified by storing Stripe session_id (and customer_id) in localStorage and checking against the Stripe API on load (cached 1 hour). Full per-user auth needed long-term.
- **Pro+ email alerts (v1.4.0):** Hourly APScheduler job (M–F 08:00–18:00 ET). Fires when new 10-Q/10-K/8-K found AND anomaly signals present. Deduped by accession number in `alert_log` table. `alert_checks` table tracks last_checked_at per (customer_id, cik). See METHODOLOGY.md §13–15.
- **Upgrade modal (v1.4.0):** Shows both Pro and Pro+ plan cards. Context-aware: Standard → both plans, Pro → Pro+ only. bfcache fix prevents stuck Loading... buttons after returning from Stripe.
- **Pro price updated to $19.00 (v1.4.0):** New Stripe price ID `price_1TWTJz1C3cijZqBOyfX4VwHC`. Old $19.99 price archived in Stripe.
- **Methodology doc rule:** Always update METHODOLOGY.md before or alongside any new scoring, polling, classification, or trigger logic.
- **Postman QA suite:** `edgar-api/postman/` contains the full collection (40 requests, 66 assertions), Local + Production environment files, and `run_qa.sh` (Newman runner). Run locally with `./run_qa.sh` — requires `npm install -g newman`.
- **Dev tier toggle:** Amber button in top-right header, visible only on localhost. Toggles between Standard → Pro → Pro+ instantly without page reload or re-fetch.
- **OG image:** 1200×630 PNG at `/og-image.png`, served via FastAPI route. Shows $GIS example data (Filing Stress Score 100/100, 3 exception flags, revenue trend). Regenerate with `edgar-api/generate_og_image.py`.
- **Free tier lookup limit:** Decided to keep unlimited lookups. Differentiation is feature depth only, not access.
- **Feature gating shipped May 10, 2026:** Frontend gates 6 Pro sections with upgrade cards. No backend lookup limit.
- **Free tier value-first design:** 8-quarter charts and quarterly data table are free. Pro gates the analytical layer.
- **Signal board is on-demand:** User clicks "Load Signal Board" and picks per-column count (5–25, default 10).
- **Stripe Customer Portal enabled:** Self-serve cancel/manage flow live. "Manage" button in header for paid users.
- **Terminology locked:** Upheaval Score → Filing Stress Score. Anomaly Signals → Filing Signals. Metric Trust & Sources → Data Quality & Sources. Filing Provenance → Source Filing.
- **Founder positioning:** Jason is an IT/systems thinker who recently started reading SEC filings — NOT a finance professional. All marketing copy should reflect this honest "outsider builder" angle. Never imply years of financial analysis experience. The story is: systems brain + public data = anyone can read the filings.
- **X marketing strategy:** Personal account (not brand account). Lead with real anomaly data, not product pitches. Use cashtags to reach active discussions on the specific stock. Tone: builder sharing a tool, not marketer selling a product.
- **Google Search Console:** Verified May 2026 via meta tag in edgar.html. Sitemap submission pending.

---

## 8. Local Dev Workflow

**VS Code tasks (recommended):**
- `Cmd+Shift+P` → Tasks: Run Task → Start Dev Server (Pro / Standard / Pro+)
- Then `Cmd+Shift+P` → Simple Browser: Show → `http://127.0.0.1:8000`

**Or via terminal:**
```bash
cd edgar-api && source .venv/bin/activate && uvicorn main:app --reload --port 8000
```

**Dev tier bypass (`?dev_tier=`):**
Bypasses Stripe verification on `127.0.0.1`/`localhost` only — no-op on the live site. Tier persists in localStorage for 1 hour. To reset: clear localStorage or open `/?dev_tier=standard`.

**Test checklist before deploying:**
- Signal board loads with range selector
- Company search works (try AAPL, GIS)
- Pro gating shows upgrade cards for Standard users
- Pro mode shows all sections
- Mobile layout (use browser DevTools responsive mode)
- Watchlist add/remove works and syncs for Pro users

**Methodology doc rule:** Any time new scoring, classification, polling, statistical, or trigger logic is added or changed, update `METHODOLOGY.md` **before or alongside** the code — not after. The doc is the spec; the code implements it.

**End-of-session release steps:**
1. Update `CHANGELOG.md` with all changes under a new version heading
2. Bump `VERSION` file and footer version in `edgar.html` and FastAPI `version=` in `main.py`
3. Update `CLAUDE_CONTEXT.md` — version field, stack, priorities, decisions, last-updated line
4. `git commit -m "Release vX.Y.Z"`
5. `git tag -a vX.Y.Z -m "vX.Y.Z — <one-line summary>"`
6. `git push origin main --tags`
7. Deploy on Railway (push to main triggers auto-deploy)

---

## 9. Technical State (as of May 12, 2026 — v1.4.0)

**What's solid:**
- Rate limiting: 200 req/min per IP on /company/* and /feed/*
- Stale cache fallback (SEC outage serves expired data instead of 502)
- Cache thread-safety (WAL + threading.Lock)
- CIK input validation on all endpoints
- Structured request + error logging throughout
- Dashboard returns HTTP 207 + has_errors flag on partial failures
- Content-Security-Policy header on frontend
- Health endpoint probes SQLite cache
- Entity type detection: foreign filers (20-F/6-K) and ETFs show friendly unsupported messages
- Null guards on all gated section renders
- Metrics endpoint returns 200 + empty periods (not 404) for companies with no EDGAR data

**Stripe integration (LIVE):**
- `POST /checkout/session` — creates Stripe Checkout session
- `POST /billing/portal` — creates Stripe Customer Portal session
- `POST /webhook/stripe` — handles checkout.session.completed, subscription.deleted, invoice.payment_failed
- `GET /subscription/status?session_id=...` — verifies session, returns tier/label/customer_id
- `GET /subscription/restore?email=...` — looks up active subscription by customer email
- `GET /subscription/status-by-customer?customer_id=...` — re-verifies by customer ID
- `GET /success` — post-payment HTML page, stores tier + session + customer_id in localStorage
- Stripe webhook endpoint: https://www.edgarwolf.com/webhook/stripe ✅
- Price IDs: Pro = price_1TWTJz1C3cijZqBOyfX4VwHC ($19.00/mo), Pro+ = price_1TVNfH1C3cijZqBOyp7Y5qJH ($99/mo)

**Watchlist API (LIVE as of v1.3.0):**
- `GET /watchlist` — fetch all items (X-Customer-Id required)
- `POST /watchlist` — add company {cik, ticker, name}
- `DELETE /watchlist/{cik}` — remove company
- `POST /watchlist/sync` — bulk migrate from localStorage; accepts {items, email}
- Customer validated against Stripe on first call, cached 1h in SQLite (`session_tier_cache` table, `cust:` prefix)
- Standard users: localStorage only. Pro/Pro+ users: server-synced, localStorage as display cache.

**Email alerts (FULLY LIVE as of v1.4.0):**
- APScheduler job: M–F 08:00–18:00 ET, hourly. Max 1 concurrent instance.
- Resend API key configured, domain verified (DKIM + SPF + MX all green on edgarwolf.com)
- FROM: `EdgarWolf <alerts@edgarwolf.com>`
- Trigger: new 10-Q/10-K/8-K filing found AND at least one anomaly signal (MEDIUM/HIGH z-score flag OR ELEVATED Filing Stress Score)
- Deduped by `(customer_id, cik, accession_number)` in `alert_log` table
- `alert_checks` table tracks last_checked_at per (customer_id, cik)
- Dev test endpoints: `POST /test/seed-alert-user`, `POST /test/run-alert-check` (403 in production)
- End-to-end tested locally — real email delivered to inbox

**QA automation:**
- Postman collection: `edgar-api/postman/` — 28 requests, 49 assertions
- Newman runner: `edgar-api/postman/run_qa.sh [local|production]`

**Railway deployment:**
- `railway.toml` at repo root — nixpacks build, uvicorn start, /health check
- Root Directory in Railway: blank (full repo deployed)
- Root `requirements.txt` at repo root (`-r edgar-api/requirements.txt`) — enables nixpacks Python auto-detection
- Env vars set in Railway Variables panel (not in .env)
- Persistent volume mounted at `/app/data` — SQLite survives redeploys ✅
- `DATA_DIR=/app/data` set in Railway Variables — cache.py writes to volume ✅
- Stripe webhook: `https://www.edgarwolf.com/webhook/stripe` ✅
- DNS: Cloudflare verified in Railway, `edgarwolf.com` live ✅

**Known pending items:**
- Render service decommission (Railway stable — safe to delete Render service)

---

_Last updated: May 14, 2026 — v1.5.2. PostHog analytics + session replay wired in (US Cloud, POSTHOG_KEY env var in Railway, /config.js endpoint exposes key to frontend). Pro/Pro+ UX upgrades: watchlist panel now always visible (including on company pages), action row (Watchlist + Exports) moved to top of dashboard. Privacy policy updated to disclose PostHog and Sentry. v1.5.1 (earlier today): free-tier email capture (digest banner + welcome email)._
