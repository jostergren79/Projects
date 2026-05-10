# EdgarWolf — Claude Context Doc

Paste this file at the start of every Claude conversation to restore full context.
Update metrics and priorities at the end of every relevant session.

---

## 1. Product & Stack

**Product:** EdgarWolf (www.edgarwolf.com)
SEC EDGAR financial data and anomaly detection tool. Pulls data directly from public SEC filings and flags statistical deviations in margins, revenue growth, and filing behavior for any US public company.

**Key features:**
- Signal board (Strengthening / Weakening — scored on recent SEC filers, auto-loads on home page)
- Z-score exception flags (gross margin, operating margin, net margin, revenue YoY)
- Upheaval Score (0–100 composite filing stress signal)
- Watchlist (localStorage, visible panel on signal board, keyed by CIK)
- Peer comparison, CSV/JSON export
- Metric Trust panel (reported vs. derived vs. stale labeling)
- Natural language summary (rules-based, not AI-generated)
- Analytics event tracking (log-based via Render logs, 8 events including upgrade_modal_open, checkout_start)
- Stripe payment integration — Pro $19/mo, Pro+ $99/mo (LIVE)
- Email alerts — NOT YET BUILT (next major feature after usage gating)

**Stack:** FastAPI (Python) backend + static HTML/JS frontend, single Render service
**Live URL:** https://www.edgarwolf.com
**Repo:** github.com/jostergren79/Projects
**Render service:** sectracker.onrender.com (internal), www.edgarwolf.com (public)
**Email:** jason@edgarwolf.com (Microsoft 365 via GoDaddy)

**Key files:**
- `edgar-api/main.py` — FastAPI app, middleware, routing
- `edgar-api/edgar_client.py` — SEC EDGAR HTTP client, rate limiter, stale cache fallback
- `edgar-api/cache.py` — SQLite cache, thread-safe, stale fallback support
- `edgar-api/routers/financial_metrics.py` — XBRL concept selection, YTD normalization, margins
- `edgar-api/routers/dashboard.py` — aggregated single-call endpoint
- `edgar-api/routers/anomaly_flags.py` — z-score exception flags
- `edgar-api/routers/feed.py` — recent SEC filers for signal board
- `edgar-api/routers/analytics.py` — event logging endpoint
- `edgar-api/routers/checkout.py` — Stripe checkout, webhook, subscription status
- `notes-api/public/edgar.html` — entire frontend (single file)
- `METHODOLOGY.md` — documents every derived metric and scoring formula

---

## 2. Founder Situation

**Name:** Jason Ostergren
**Income target:** $8k/month take home to replace current salary
**Users needed:** 80 paying users at $99/month
**Backup:** Job offer from Post Consumer Brands (in final stages)
**Decision rule:** 5+ paying users by end of week 4 = pursue EdgarWolf full time. Fewer = take the job, build nights and weekends.
**Audience:** Zero — no Twitter, no following anywhere
**Network:** Crypto friends (potential early beta users)

---

## 3. Pricing Model

| Tier | Price | Features |
|------|-------|----------|
| Standard | $0 | Currently fully open — no hard limits enforced yet |
| Pro | $19/month | Stripe live, checkout works, no feature gating yet |
| Pro+ | $99/month | Stripe live, checkout works, no feature gating yet |

**Important:** Stripe checkout and subscription verification are LIVE but feature gating (e.g. rate limits per tier, locked endpoints) is NOT yet implemented. Anyone can use everything for free right now. Enforcement is the next technical priority after marketing push.

---

## 4. Current Metrics

_Update these at the end of every session._

| Metric | Value | Updated |
|--------|-------|---------|
| MRR | $0 | May 10, 2026 |
| Paying users | 0 | May 10, 2026 |
| Free signups | 0 | May 10, 2026 |

---

## 5. Marketing Assets

**Example 1 — $CAG (Conagra)**
- Gross, operating, and net margin all 3+ standard deviations below 8-quarter historical average (HIGH flags)
- Revenue declining from $3.2B to $2.4B over 8 quarters
- Upheaval Score: 70/100 ELEVATED

**Example 2 — $GIS (General Mills)**
- Upheaval Score: 100/100 ELEVATED
- Filing Velocity: ELEVATED — 4 eight-K filings within 2 days
- Revenue YoY growth 3.3 standard deviations below historical average (HIGH flag)
- Revenue declining from $5.2B to $3.8B over 8 quarters
- Margins showing cliff drop in most recent quarters

**Target channels:**
- r/SecurityAnalysis — Reddit post with CAG + GIS screenshots
- Finance Substack writers — free Pro access in exchange for a mention
- Crypto friends — free beta access, honest feedback

---

## 6. Active Priorities

_Replace completed items each session. Keep this list short._

**Immediate (next session):**
- [ ] Post on r/SecurityAnalysis — CAG + GIS examples with screenshots
- [ ] Send beta invites to 2–3 crypto friends with free Pro access
- [ ] Add feature gating — enforce tier limits (free gets N lookups/day, Pro+ gets everything)
- [ ] Build email alerts — watchlist + z-score threshold triggers email notification (Pro+ differentiator)

**Soon:**
- [ ] Identify 10 finance Substack writers and send personal outreach emails
- [ ] Add user login / account system (required for proper per-user subscription enforcement)

---

## 7. Key Decisions Made

_Running log of important decisions so we don't relitigate them._

- **Pricing:** $99/month justified only once email alerts are live. Without alerts it's a $19/month product.
- **No CRM yet:** Spreadsheet is sufficient until 80+ users. CRM is premature.
- **No scaling/automation yet:** First 30 days is manual everything. Find 10 paying users by hand before building infrastructure.
- **Upheaval Score rename:** Consider renaming to "Filing Stress Score" for finance audience.
- **Distribution first:** Product is good enough to charge for. Distribution is the only job right now.
- **Sale target ($500k) is not realistic short term.** Realistic near-term goal is replacing income.
- **Render-only deployment:** Netlify removed. FastAPI serves the frontend directly from Render.
- **Analytics via Render logs:** Events emitted as structured log lines (grep 'EVENT' in Render log tab). No external analytics service needed.
- **Watchlist keyed by CIK:** Ticker is unreliable (empty for many EDGAR companies). CIK is always present.
- **Domain:** edgarwolf.com purchased, www.edgarwolf.com live via CNAME to sectracker.onrender.com.
- **Email:** jason@edgarwolf.com via Microsoft 365 + GoDaddy. All public-facing email references updated.
- **Stripe session-based auth:** Without user login, subscription status is verified by storing the Stripe session_id in localStorage and checking it against the Stripe API on load (cached 1 hour). This breaks if user clears localStorage or switches browsers. Full per-user auth is needed to solve this properly.
- **Feature gating deferred:** Stripe is live but no limits are enforced yet. Ship marketing first, gate features after first paying users.

---

## 8. Technical State (as of May 10, 2026)

**What's solid:**
- Rate limiting: 200 req/min per IP on /company/* and /feed/* (analytics excluded)
- Stale cache fallback (SEC outage serves expired data instead of 502)
- Cache thread-safety (WAL + threading.Lock)
- CIK input validation on all endpoints
- Structured request + error logging throughout
- Dashboard returns HTTP 207 + has_errors flag on partial failures
- Content-Security-Policy header on frontend
- Health endpoint probes SQLite cache

**Stripe integration (LIVE):**
- `POST /checkout/session` — creates Stripe Checkout session, returns redirect URL
- `POST /webhook/stripe` — handles checkout.session.completed, customer.subscription.deleted, invoice.payment_failed
- `GET /subscription/status?session_id=...` — verifies active subscription against Stripe API, returns tier/label
- `GET /success` — post-payment HTML page, stores tier in localStorage
- Upgrade modal in header: Pro card (blue) and Pro+ card (green), selectable, defaults to Pro
- Header badge shows ✓ Pro (blue) or ✓ Pro+ (green) after verification; Standard shows Upgrade button
- Stripe env vars in Render: STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET (both sync:false / set manually)
- Stripe webhook endpoint registered at https://www.edgarwolf.com/webhook/stripe
- Price IDs: Pro = price_1TVNfH1C3cijZqBOyp7Y5qJH, Pro+ = price_1TVNeQ1C3cijZqBOkOX1IoJj

**Known limitations (acceptable for now):**
- SQLite cache resets on Render redeploy (ephemeral filesystem on free tier) — recovers automatically
- No user authentication — subscription status tied to localStorage session_id only
- No feature gating yet — all tiers can access everything
- Render free tier spins down after inactivity — first request after sleep is slow

---

_Last updated: May 10, 2026_
