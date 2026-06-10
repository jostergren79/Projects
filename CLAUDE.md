# EdgarWolf — Claude Code Project Guide

**Auto-loaded every session.** Holds stable context, durable rules, and the start/end session sequences. Live state (metrics, priorities, next-session plan) lives in **`STATE.md`** — read it at the start of every session.

Current version: see `VERSION` (release history in `CHANGELOG.md`).

---

## Document map

| File | Role | Changes |
|------|------|---------|
| `CLAUDE.md` (this file) | Stable context, rules, session sequences. Auto-loads. | Rarely |
| `STATE.md` | Live metrics, active priorities, NEXT SESSION plan, current-state note. | Every session |
| `CHANGELOG.md` | Release history — what shipped, per version. | Per release |
| `DECISIONS_ARCHIVE.md` | Settled decisions (the why), once they leave active rotation. | Occasionally |
| `METHODOLOGY.md` | Spec for every derived metric + scoring rule. | Alongside any logic change |
| `SECURITY.md` | Canonical security posture. | Per security release |
| `README.md` | Public-facing project overview. | Occasionally |

---

## Trigger phrases

- **`claude start`** — Jason types this to open a session. Immediately and automatically run the full start-of-session sequence below. No confirmation needed; just execute all steps and present the summary.
- **`claude end session`** — Jason types this to close a session. Immediately and automatically run the full end-of-session sequence below. Do not skip steps even for distribution-only sessions (no code shipped). Never close a session without completing this sequence.

## Start-of-session sequence

Run all steps automatically when Jason types `claude start`:

1. **Read `STATE.md`** — current metrics, active priorities, and the NEXT SESSION plan. (This file, `CLAUDE.md`, auto-loads.)
2. **Pull live metrics from PostHog** (project 424339, US Cloud — see Active Decisions). Compare against the STATE.md metrics table; note anything new (visits, countries, upgrade-modal opens, signups, conversions).
3. **Check prod health:** `GET /health` (expect ok + cache healthy) and `GET /openapi.json` (confirm deployed version vs `VERSION`).
4. **Note pending externals:** r/SecurityAnalysis mod approval; Railway deploy-queue state.
5. **Restate the NEXT SESSION plan** from STATE.md and confirm the focus with Jason before diving in.

## End-of-session sequence

Run all steps automatically when Jason types `claude end session`. Required even for distribution-only sessions — STATE.md must always reflect what happened:

1. **Update `STATE.md`** — metrics table (pull fresh PostHog if not already done), active priorities (mark completed items done, remove them), the NEXT SESSION order-of-operations, and the current-state note. The current-state note must read cold: a future session should resume with zero extra context. Include X posts made, replies sent, any engagement data Jason provides.
2. **If anything shipped:** add a `CHANGELOG.md` entry; bump `VERSION` + the frontend footer + `main.py` `version=`. (Skip the bump for metadata-only changes — copy, analytics guards, JSON-LD.)
3. **If scoring / classification / polling / trigger logic changed:** update `METHODOLOGY.md` in the same change.
4. **Save durable memory** — any new user / feedback / project / reference facts worth carrying to future sessions.
5. **Commit:** `git commit`, `git tag` if it's a release, `git push` (`--tags`). Railway auto-deploys on push to `main`.

---

## 1. Product & stack

**Product:** EdgarWolf (https://www.edgarwolf.com) — SEC EDGAR financial data + anomaly detection. Flags statistical deviations in margins, revenue growth, and filing behavior for any US public company.

**Stack:** FastAPI (Python) + static HTML/JS, deployed as a Railway service. Repo: github.com/jostergren79/Projects.

**Key features:**
- Signal board (Strengthening / Weakening — on-demand, 5–25 companies per column)
- Z-score exception flags (gross / operating / net margin, revenue YoY)
- Filing Stress Score (0–100 composite)
- Watchlist — server-side for Pro/Pro+ (SQLite, keyed by Stripe customer_id), localStorage for Standard
- Peer comparison, CSV/JSON export, Metric Trust panel, natural-language summary
- Analytics: PostHog (US Cloud, project 424339) + Railway logs. Session recordings + heatmaps on.
- Stripe: Pro $19/mo, Pro+ $99/mo (LIVE). Customer Portal live.
- Email alerts (Pro+): hourly M–F 8 AM–6 PM ET cron, fires on new 10-Q/10-K/8-K + anomaly signal. **LIVE — validated end-to-end in prod May 22, 2026 (scheduled cron delivered a real $CAG 8-K alert).**
- Free-tier digest capture — email + welcome via Resend. (Weekly digest send job not yet built.)

**Key files:**
- `edgar-api/main.py` — FastAPI app
- `edgar-api/cache.py` — SQLite cache, watchlists, users
- `edgar-api/auth.py` — magic-link token mint/verify, cookie helpers, mask_email
- `edgar-api/scheduler.py` — Pro+ email alert cron (apscheduler) + alert HTML build
- `edgar-api/routers/auth_router.py` — /auth/request, /verify, /logout, /whoami
- `edgar-api/routers/financial_metrics.py` — XBRL, YTD normalization, margins
- `edgar-api/routers/dashboard.py` — aggregated endpoint
- `edgar-api/routers/checkout.py` — Stripe checkout + webhook (writes users.tier)
- `edgar-api/routers/analytics.py` — event ingest
- `edgar-frontend/edgar.html` — entire frontend
- `METHODOLOGY.md` — spec for all derived metrics + scoring

## 2. Founder

**Jason Ostergren** | Minneapolis, MN. Income target: **$8k/mo** to replace current salary.
- **Decision rule (May 15, 2026):** take the full-time job no matter which company offers first; EdgarWolf is parallel side-income. Re-evaluate full-time only when EdgarWolf reliably exceeds $8k/mo for several consecutive months. Backup: offer from Post Consumer Brands (final stages).
- **Background:** IT systems thinker, **not** a finance professional. 20+ yrs enterprise IT, Sr BSA, SQL/Snowflake, SAFe PO, Full Stack Web Dev cert (U of Minnesota). Built EdgarWolf to scratch his own itch reading filings as an outsider. The **outsider-builder** angle is the honest founder story — never imply years of financial-analysis experience.

## 3. Pricing

| Tier | Price | Features |
|------|-------|----------|
| Standard | $0 | Signal board, search, KPI grid, narrative summary, 8-quarter charts, data table. Unlimited lookups. |
| Pro | $19/mo | + Exception Flags, Filing Stress Score, Filing Signals, peer comparison, segment breakdown, source filing, server-side watchlist, CSV/JSON export. |
| Pro+ | $99/mo | + email alerts (LIVE — validated in prod May 22, 2026). |

Feature gating LIVE since May 10, 2026. Differentiation is feature **depth**, not access. **$99/mo is justified only with email alerts working** — without them it's a $19 product.

## 4. Marketing assets & channels

**Filed-data examples (durable talking points):**
- **$CAG:** all 3 margins 3+ SD below avg (HIGH); revenue $3.2B→$2.4B; FSS 70/100 ELEVATED. (Q3 FY26 live data is more dramatic — see CHANGELOG.)
- **$GIS:** FSS 100/100; filing velocity ELEVATED; revenue YoY -23%, 3.3 SD below avg.
- **$UNH:** FSS 92/100 ELEVATED; 8-K filed 6 days before 10-Q. CIK 0000731766.
- **$JACK:** FSS 92/100; net income -$25.9M; EPS -$1.35; revenue -12.4% YoY.
- **$SOFI:** Contrarian/Green; four straight profitable quarters. XBRL revenue concepts unreliable for fintechs/banks — use bottom-line figures only.

**Channels:**
- **X (PRIMARY):** personal account. 6 rotating themes — Company Spotlight, Methodology, Sector Sweep, Contrarian/Green, Builder Update, Retrospective. 4 replies/day target. Monday pre-market = peak window. CIK-direct URL (`?cik=<CIK>`) on every company-specific post. **Daily post + card automation:** Cowork runs at 8 AM daily, generates the post copy and data card automatically. **Data-card pipeline:** build HTML in the dashboard palette (CSS vars in `edgar-frontend/edgar.html`) → render with headless Chrome `--screenshot --force-device-scale-factor=2` (4:5, 1080×1350) → verify legibility by downscaling to ~400px (mobile feed width) with `sips`.
- **Sector Sweeps run (log each new one here to avoid repeats):** consumer staples / packaged food; RF + analog semis ($SWKS $QRVO $ADI $ON $MCHP, May 22 2026). Verify live data per name before drafting — z-score flags fire in BOTH directions and high FSS is often filing-velocity, not margin, driven.
- **StockTwits:** live since May 18. Bearish/Bullish sentiment tag required. Same data-forward format as X.
- **r/SecurityAnalysis:** post drafted, awaiting mod approval.
- **Finance Substack writers / crypto friends:** outreach not started (free Pro / beta invites).
- **Google:** Search Console verified; sitemap live; JSON-LD deployed (AI Overview surfaces EdgarWolf as primary direct link w/ OG thumbnail).

**Key FinTwit accounts (engaged — do NOT pitch; stay in threads with filing data):** @Ashton_1nvests (33.2K), @JonahLupton (552K), @MikeSchiemer (195.5K).

## 5. Active decisions

Settled decisions live in `DECISIONS_ARCHIVE.md`.

- **Take the job** — full-time offer regardless of company; EdgarWolf = side income until $8k/mo sustained.
- **Distribution first** — product is good enough; distribution is the only job for the next 30 days. Manual everything until 10 paying users.
- **Founder angle** — outsider IT builder, not finance pro. All copy reflects this.
- **X strategy** — lead with filing data, not product pitches. CIK-direct URLs always. Borrowed-audience via reply threads is the daily driver. **Own-content (May 23): single image-led posts, not multi-tweet threads** — one screenshot-worthy data card (portrait 4:5; dominates the mobile feed, where the clicks come from); reserve threads for occasional pinned/evergreen anchors. Mid-traffic beats mega-threads for a new account (exception: still-climbing mega-threads). Never tag/DM engagement targets; never ask for RTs.
- **X writing style** — **no em-dashes** (readers spot them as LLM tells; use periods, short sentences, or ` - `). Terse, declarative, data-forward. **Case by job (May 23):** sentence case for own standalone posts (credibility on first contact for a data/finance product); lowercase-casual in replies (native, low-ego, conversational). Match Jason's own cadence.
- **StockTwits** — Bearish/Bullish tag required; same data-forward format as X.
- **Methodology-doc rule** — update `METHODOLOGY.md` before/alongside any new scoring, classification, polling, or trigger logic.
- **PostHog** — project 424339, US Cloud. Query programmatically at session start. Key events: `page_view`, `company_view`, `upgrade_modal_open`, `subscription_success`.
- **Filing-season focus** — late May/June = high-signal; prioritize posts around fresh 10-Q/10-K drops.
- **No version bump for metadata-only changes** (copy, analytics guards, JSON-LD).
- **Sector-sweep format** — one company per tweet; hits multiple cashtag feeds at once.

## 6. Dev workflow

```bash
cd edgar-api && source .venv/bin/activate && uvicorn main:app --reload --port 8000
```
Dev tier bypass: `?dev_tier=pro` (localhost only; amber toggle button in header). Session open/close steps are the sequences at the top of this file.

## 7. Technical state (v1.6.0)

Solid: proxy-aware rate limiting (200/min per real client IP, w/ memory cleanup), stale-cache fallback, WAL thread-safety, CIK validation, HTTP 207 on partial failures, full browser security headers (CSP + X-Frame-Options + X-Content-Type-Options + Referrer-Policy + HSTS), Stripe webhook signature verification (hard-fails on missing secret), full HTML output encoding (escapeAttr() + html.escape() in alert emails), debug param gated to dev, dev endpoints gated by DEV_SECRET, health endpoint, entity-type detection, robots.txt, PostHog localhost guard, `subscription_success` once per customer.

**Auth (v1.6.0):** magic-link sign-in via Resend (HMAC-SHA256, 15-min TTL) → 30-day httpOnly Secure SameSite=Lax `ew_session` cookie. customer_id never reaches the frontend. `/auth/request` always returns `{ok:true}` (anti-enumeration). Stripe lookup uses `Customer.list(email=)`, not `.search(query=)`. Email log lines masked (`j***@gmail.com`).

Stripe, Watchlist API, Pro+ email alerts (validated end-to-end in prod May 22, 2026), QA (Postman/Newman), Railway persistent volume — all live. Full security posture in `SECURITY.md`; technical decision log in `DECISIONS_ARCHIVE.md`.
