# EdgarWolf — Claude Context Doc

**Current version: v1.6.0** (2026-05-19) — see `CHANGELOG.md` for full release history.

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

**Tomorrow:**
- [ ] **Set `MAGIC_LINK_SECRET` in Railway** before pushing v1.6.0 — generate with `python -c 'import secrets; print(secrets.token_urlsafe(48))'`. Without this env var the new auth module fails fast on every token mint.
- [ ] Confirm `SEC_REQUIRE_EXPLICIT_USER_AGENT=true` and `SEC_USER_AGENT` are set in Railway (env var check, no code change).
- [ ] After deploy, smoke-test the magic-link flow end-to-end on production: request from jason@edgarwolf.com → receive the link → click → land on `/?signed_in=1` with cookie set → watchlist GET succeeds. Then test that hitting `/auth/request` with an unknown email returns the same `{ok: true}`.

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

## 9. Technical State (v1.6.0, May 19)

Solid: proxy-aware rate limiting (200/min per real client IP, with memory cleanup), stale cache fallback, WAL thread-safety, CIK validation, HTTP 207 on partial failures, full browser security header set (CSP + X-Frame-Options + X-Content-Type-Options + Referrer-Policy + HSTS), Stripe webhook signature verification (hard-fails on missing secret), full HTML output encoding via escapeAttr() + html.escape() in alert emails, debug param gated to dev only, dev test endpoints gated by DEV_SECRET, health endpoint, entity type detection, robots.txt, PostHog localhost guard, `subscription_success` event once per customer.

**Auth (new in v1.6.0):** magic-link sign-in via Resend (HMAC-SHA256, 15-min TTL) → 30-day httpOnly Secure SameSite=Lax `ew_session` cookie. Customer_id never reaches the frontend. `/auth/request` always returns `{ok: true}` to prevent customer enumeration. Stripe customer lookup uses `Customer.list(email=)`, not `Customer.search(query=)`. Email log lines now masked (`j***@gmail.com`).

Stripe, Watchlist API, Email alerts, QA (Postman/Newman), Railway persistent volume — all LIVE. See `DECISIONS_ARCHIVE.md` for full technical decision log and `SECURITY.md` for full security posture.

---

_Last updated: May 19, 2026 — v1.6.0_

_May 19 session: Refreshed README for v1.5.5 (was last touched May 12, missed everything in v1.4.x–v1.5.5 — features section, pricing table, new routers, docs cross-refs, env vars, security highlights, deploy checklist). Posted Day 7 Builder Update on X — first upgrade_modal_open as the hook, 5 countries / first StockTwits post / 2 security releases as supporting beats, magic-link auth flagged as next ship. Then shipped v1.6.0 — full auth hardening release. New `auth.py` module (HMAC token mint/verify, cookie helpers, mask_email) + `routers/auth_router.py` (POST /auth/request, GET /auth/verify, POST /auth/logout, GET /auth/whoami). Removed `/subscription/restore`, `/subscription/status`, `/subscription/status-by-customer` — magic-link replaces the email-leak path; `/auth/whoami` replaces the tier check. `/watchlist/*` reads customer_id from the signed cookie instead of `X-Customer-Id`; the email override on `/watchlist/sync` is gone (webhook now upserts the user record on `checkout.session.completed`). `/billing/portal` reads customer_id from the cookie too. `/success` does a server-side Stripe session lookup and sets the auth cookie before rendering. Frontend stops storing `edgarwolf_customer` anywhere; watchlist fetches use `credentials: 'include'`; restore form posts to `/auth/request` and always shows the same "check your inbox" message. Bundled hygiene fixes: stripe.Customer.list(email=) instead of .search(query=) (query-injection surface), html.escape() every interpolation in scheduler.py:_build_alert_html, mask_email() applied to digest_signup / subscription_started / welcome_email_sent / alert_sent / digest_welcome_sent / digest_unsubscribe / magic_link_sent log lines, fastapi 0.111→0.128 + starlette/python-multipart/requests/urllib3 floor pins to clear pip-audit CVEs. SECURITY.md §4 rewritten to describe the magic-link + cookie model. PostHog no longer identifies by customer_id (it's not on the client anymore) — tier set as anonymous person property. Need to set `MAGIC_LINK_SECRET` in Railway env vars BEFORE pushing._

_May 18 session: Posted $UNH on X (news-driven Company Spotlight — Berkshire sold entire stake, FSS 92/100, 8-K 6 days before 10-Q). Posted $SOFI Contrarian/Green (profitable trajectory, bottom-line only — XBRL unreliable for fintechs). First StockTwits post live ($UNH Bearish). PostHog 24hr: first upgrade_modal_open (Minneapolis iPhone, $AAPL page, May 17 8:12 AM CT — warm returning lead, came back same day), Philippines = new country, $UNH clicked same day as post. Fixed signal_board_skip analytics bug — was firing 154× per board load, now fires once with aggregate stats. Trimmed context doc, created DECISIONS_ARCHIVE.md. Day 7: Builder Update — plan tomorrow morning._

_May 18 session 2 (v1.5.4 — security hardening): Full security review of the codebase identified 10 issues across CRITICAL/HIGH/MEDIUM/LOW severity. All fixed and shipped in one release. Highlights: patched reflected XSS on the `/success` Stripe redirect page (session_id and tier were interpolated directly into a `<script>` tag); added the full standard set of browser security headers (X-Frame-Options, X-Content-Type-Options, Referrer-Policy, HSTS) on every response; fixed proxy-aware rate limiting by adding `--proxy-headers --forwarded-allow-ips='*'` to uvicorn so the real client IP is used instead of Railway's LB; expanded rate limiting to /digest/subscribe and /subscription/restore; hardened Stripe webhook to fail closed when secret is missing; added escapeAttr() to all remaining innerHTML injection points (flags, provenance panel, trust panel, quarterly table, segments); gated `?debug=true` to dev only; replaced IP-based dev endpoint check with `DEV_SECRET` env var. Created SECURITY.md as the canonical security posture document — organized by category, suitable to share with customers/partners/investors who ask about site security._

_May 18 session 3 (v1.5.5 — XSS hotfix + second-pass review): Live-site testing immediately after the v1.5.4 deploy caught an incomplete XSS fix on `/success`. The v1.5.4 patch used `json.dumps()` for the script-block interpolations, but json.dumps does not escape `<` or `>` — a payload containing `</script>` still ended the script tag and allowed HTML injection. Shipped v1.5.5 with a `_script_safe_json()` helper that additionally Unicode-escapes `<`, `>`, and `&`. Lesson recorded in CHANGELOG: always probe live with adversarial payloads after a security release._

_Then ran a second-pass review. Biggest finding: **email-based account hijack via `/subscription/restore`**. The endpoint returns the Stripe customer_id to anyone who types a Pro user's email; combined with the unauthenticated email-overwrite field in `POST /watchlist/sync`, an attacker can read the victim's watchlist and reroute their Pro+ filing alerts to a different inbox. Also noted: stripe.Customer.search query-injection surface (no email validation), full emails in plaintext logs (Railway), unescaped HTML in alert emails (low impact, but worth fixing), and 30 pip-audit findings in deps (starlette + python-multipart most relevant)._

_Decision for tomorrow: implement option 1 — magic-link auth via Resend. User enters email → server verifies Stripe has an active sub on that email → Resend sends a short-lived (15min) signed-token magic link → click sets httpOnly cookie → frontend stops storing customer_id in localStorage. Stripe stays source of truth; Customer Portal integration unchanged. Honest framing: Stripe doesn't have a built-in "user proves email ownership" primitive — Customer Portal requires us to already know the customer. The magic-link is the standard pattern and the small piece we have to build ourselves. Bundle the hygiene fixes (Stripe query-injection, log masking, email HTML escape, dep bumps) into the same release as v1.6.0._

_Site healthy at session close: v1.5.5 live, all 4 security headers verified in production, XSS payloads blocked, /health ok, smoke-test API calls returning real data._
