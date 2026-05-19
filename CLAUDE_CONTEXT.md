# EdgarWolf — Claude Context Doc

**Current version: v1.5.4** (2026-05-18) — see `CHANGELOG.md` for full release history.

Paste this file at the start of every Claude conversation to restore full context.
Update metrics, version, and priorities at the end of every relevant session.

---

## 1. Product & Stack

**Product:** EdgarWolf (www.edgarwolf.com)
SEC EDGAR financial data and anomaly detection tool. Flags statistical deviations in margins, revenue growth, and filing behavior for any US public company.

**Key features:**
- Signal board (Strengthening / Weakening — on-demand, 5–25 companies per column)
- Z-score exception flags (gross margin, operating margin, net margin, revenue YoY)
- Filing Stress Score (0–100 composite)
- Watchlist — server-side for Pro/Pro+ (SQLite, keyed by Stripe customer_id), localStorage for Standard
- Peer comparison, CSV/JSON export, Metric Trust panel, natural language summary
- Analytics via PostHog (US Cloud, project 424339) + Railway logs. Session recordings, heatmaps on.
- Stripe: Pro $19.00/mo, Pro+ $99/mo (LIVE). Customer Portal live.
- Email alerts — LIVE for Pro+. Hourly M–F 8 AM–6 PM ET. Fires on new 10-Q/10-K/8-K + anomaly signal.
- Free-tier digest capture — email + welcome via Resend. Weekly digest send job not yet built.

**Stack:** FastAPI (Python) + static HTML/JS, Railway service
**Live URL:** https://www.edgarwolf.com
**Repo:** github.com/jostergren79/Projects

**Key files:**
- `edgar-api/main.py` — FastAPI app
- `edgar-api/cache.py` — SQLite cache, watchlists, users
- `edgar-api/routers/financial_metrics.py` — XBRL, YTD normalization, margins
- `edgar-api/routers/dashboard.py` — aggregated endpoint
- `edgar-api/routers/checkout.py` — Stripe
- `edgar-frontend/edgar.html` — entire frontend
- `METHODOLOGY.md` — spec for all derived metrics and scoring

---

## 2. Founder Situation

**Name:** Jason Ostergren | Minneapolis, MN
**Income target:** $8k/month to replace current salary
**Decision rule (May 15, 2026):** Take the full-time job no matter which company offers first. EdgarWolf is parallel side-income. Re-evaluate full-time only when EdgarWolf reliably exceeds $8k/month for several consecutive months.
**Backup:** Job offer from Post Consumer Brands (in final stages)

**Background:** IT systems thinker, NOT a finance professional. 20+ years enterprise IT, Sr BSA, SQL/Snowflake, SAFe PO, Full Stack Web Dev cert (U of Minnesota). Built EdgarWolf to scratch his own itch reading SEC filings as an outsider. This "outsider builder" angle is the honest founder story — never imply years of financial analysis experience.

---

## 3. Pricing Model

| Tier | Price | Features |
|------|-------|----------|
| Standard | $0 | Signal board, company search, KPI grid, narrative summary, 8-quarter charts, data table. Unlimited lookups. |
| Pro | $19.00/mo | Everything free + Exception Flags, Filing Stress Score, Filing Signals, peer comparison, segment breakdown, source filing, watchlist (server-side), CSV/JSON export. |
| Pro+ | $99/mo | Everything Pro + email alerts (LIVE). |

Feature gating LIVE as of May 10, 2026. Differentiation is feature depth only, not access.

---

## 4. Current Metrics

_Update these at the end of every session._

| Metric | Value | Updated |
|--------|-------|---------|
| MRR | $0 | May 18, 2026 |
| Paying users | 0 | May 18, 2026 |
| Free signups | 0 | May 18, 2026 |
| X-attributed visits | 20+ (US, Germany, France, UK, Philippines) | May 18, 2026 |
| First upgrade modal open | 1 (Minneapolis, iPhone, $AAPL page, May 17 8:12 AM CT) | May 18, 2026 |

---

## 5. Marketing Assets

**Filed data examples:**
- **$CAG:** All 3 margins 3+ SD below avg (HIGH). Revenue $3.2B→$2.4B. FSS 70/100 ELEVATED.
- **$GIS:** FSS 100/100. Filing velocity ELEVATED. Revenue YoY -23%, 3.3 SD below avg.
- **$UNH (May 18):** FSS 92/100 ELEVATED. 8-K filed 6 days before 10-Q. CIK 0000731766.
- **$JACK:** FSS 92/100. Net income -$25.9M, EPS -$1.35, Revenue -12.4% YoY.
- **$SOFI (May 18):** Contrarian/Green. Net income trajectory: -$267M (Q3 2023) → +$71M → +$202M → +$167M (Q1 2026). Four straight profitable quarters. XBRL revenue concepts unreliable for fintechs/banks — use bottom-line figures only.

**Channels:**
- **X (PRIMARY):** Personal account. 6 rotating themes: Company Spotlight, Methodology, Sector Sweep, Contrarian/Green, Builder Update, Retrospective. **Day 7 next: Builder Update.** 4 replies/day target. Monday pre-market = peak window. CIK-direct URL on every company-specific post.
- **StockTwits:** LIVE as of May 18. First post: $UNH Bearish. Sentiment tag required. Same data-forward format as X.
- **r/SecurityAnalysis:** Post drafted, waiting on mod approval (requested May 10).
- **Finance Substack writers:** Not started — free Pro access in exchange for mention.
- **Crypto friends:** Not started — free beta invites pending.

**Key FinTwit accounts (engaged May 17 — do NOT pitch, stay in threads with filing data):**
@Ashton_1nvests (33.2K), @JonahLupton (552K hedge fund CEO), @MikeSchiemer (195.5K)

**Google:** Search Console verified. Sitemap live (May 13). JSON-LD deployed (May 17) — Google AI Overview now surfaces EdgarWolf as primary direct link with OG thumbnail.

---

## 6. Active Priorities

_Replace completed items each session. Keep this list short._

**Immediate:**
- [ ] Day 7 X post — Builder Update (plan in morning, fold in fresh PostHog data)
- [ ] 4 X replies/day — active threads, still-climbing
- [ ] Send beta invites to 2–3 crypto friends (free Pro access)
- [ ] Identify 10 finance Substack writers, send personal outreach
- [ ] Post on r/SecurityAnalysis when mod approval comes through
- [ ] Build weekly digest send job — Sunday cron, top 10 FSS companies, emails all `digest_subscribers`, unsubscribe link required
- [ ] Submit to SaaSWorthy, Product Hunt, G2, Capterra, AlternativeTo

**Soon:**
- [ ] Expand sitemap to /privacy and /terms
- [ ] Chart.js defensive fix: `responsive: true, maintainAspectRatio: false` + sized wrappers
- [ ] Filter localhost from PostHog dashboards (Settings → Project → Test accounts)

---

## 7. Key Decisions (Active — see DECISIONS_ARCHIVE.md for settled)

- **Take the job:** Accept full-time offer regardless of which company. EdgarWolf = side income until $8k/mo sustained for several months.
- **Distribution first:** Product is good enough. Distribution is the only job for the next 30 days. Manual everything until 10 paying users.
- **Founder angle:** Outsider IT builder, not finance professional. All copy reflects this.
- **X strategy:** Personal account, lead with filing data not product pitches. CIK-direct URLs on every company mention (`?cik=<CIK>`). Borrowed-audience via reply threads (10K–100K views, still climbing). Mid-traffic beats mega-threads for new accounts — exception: still-climbing mega-threads.
- **StockTwits:** Bearish/Bullish sentiment tag required. Same data-forward format as X replies.
- **$99/mo justified only with email alerts live.** Without alerts it's a $19 product.
- **Methodology doc rule:** Update METHODOLOGY.md before/alongside any new scoring, classification, polling, or trigger logic.
- **PostHog API:** Project 424339, US Cloud. Query programmatically at session start. Key events: `page_view`, `company_view`, `upgrade_modal_open`, `subscription_success`.
- **End of quarter filing season:** Late May/June = high-signal content. Prioritize posts around fresh 10-Q/10-K drops.
- **No version bump for metadata-only changes** (copy, analytics guards, JSON-LD).
- **Sector sweep thread format:** One company per tweet — hits multiple cashtag feeds simultaneously.

---

## 8. Dev Workflow

```bash
cd edgar-api && source .venv/bin/activate && uvicorn main:app --reload --port 8000
```
Dev tier bypass: `?dev_tier=pro` (localhost only). Amber toggle button in header.

**End-of-session steps:**
1. Update `CHANGELOG.md`
2. Bump VERSION + footer + `main.py` version=
3. Update this file — metrics, priorities, decisions, session note
4. `git commit`, `git tag`, `git push --tags`
5. Railway auto-deploys on push to main

---

## 9. Technical State (v1.5.4, May 18)

Solid: proxy-aware rate limiting (200/min per real client IP, with memory cleanup), stale cache fallback, WAL thread-safety, CIK validation, HTTP 207 on partial failures, full browser security header set (CSP + X-Frame-Options + X-Content-Type-Options + Referrer-Policy + HSTS), Stripe webhook signature verification (hard-fails on missing secret), full HTML output encoding via escapeAttr(), debug param gated to dev only, dev test endpoints gated by DEV_SECRET, health endpoint, entity type detection, robots.txt, PostHog localhost guard, `subscription_success` event once per customer.

Stripe, Watchlist API, Email alerts, QA (Postman/Newman), Railway persistent volume — all LIVE. See `DECISIONS_ARCHIVE.md` for full technical decision log and `SECURITY.md` for full security posture.

---

_Last updated: May 18, 2026 — v1.5.4_

_May 18 session: Posted $UNH on X (news-driven Company Spotlight — Berkshire sold entire stake, FSS 92/100, 8-K 6 days before 10-Q). Posted $SOFI Contrarian/Green (profitable trajectory, bottom-line only — XBRL unreliable for fintechs). First StockTwits post live ($UNH Bearish). PostHog 24hr: first upgrade_modal_open (Minneapolis iPhone, $AAPL page, May 17 8:12 AM CT — warm returning lead, came back same day), Philippines = new country, $UNH clicked same day as post. Fixed signal_board_skip analytics bug — was firing 154× per board load, now fires once with aggregate stats. Trimmed context doc, created DECISIONS_ARCHIVE.md. Day 7: Builder Update — plan tomorrow morning._

_May 18 session 2 (v1.5.4 — security hardening): Full security review of the codebase identified 10 issues across CRITICAL/HIGH/MEDIUM/LOW severity. All fixed and shipped in one release. Highlights: patched reflected XSS on the `/success` Stripe redirect page (session_id and tier were interpolated directly into a `<script>` tag); added the full standard set of browser security headers (X-Frame-Options, X-Content-Type-Options, Referrer-Policy, HSTS) on every response; fixed proxy-aware rate limiting by adding `--proxy-headers --forwarded-allow-ips='*'` to uvicorn so the real client IP is used instead of Railway's LB; expanded rate limiting to /digest/subscribe and /subscription/restore; hardened Stripe webhook to fail closed when secret is missing; added escapeAttr() to all remaining innerHTML injection points (flags, provenance panel, trust panel, quarterly table, segments); gated `?debug=true` to dev only; replaced IP-based dev endpoint check with `DEV_SECRET` env var. Created SECURITY.md as the canonical security posture document — organized by category, suitable to share with customers/partners/investors who ask about site security._
