# EdgarWolf — Live State

**Updated every session.** Stable context, rules, and the start/end session sequences are in **`CLAUDE.md`** (auto-loaded). This file holds only the volatile state: metrics, active priorities, the next-session plan, and a current-state note.

Current version: **v1.7.0** (2026-05-22). Release history in `CHANGELOG.md`.

---

## Current metrics

_Refreshed May 22 (session start). PostHog showed 6 `subscription_success` (pro_plus) since May 20 — but Stripe confirms all are the single comp account, not new customers (the event over-fires from authenticated page state; see tech debt). Real revenue unchanged._

| Metric | Value | Updated |
|--------|-------|---------|
| MRR | $0 | May 22, 2026 |
| Paying users | 0 (+1 comp Pro+: `cus_UUN2ChsZV2aaRC`, $0 MRR) | May 22, 2026 |
| Free signups (digest) | 0 (9 banner views, 0 signups) | May 22, 2026 |
| X-attributed visits (PostHog, week 1) | 25 distinct visitors | May 21, 2026 |
| Countries (rolling 500-event window) | 4: US, Germany, France, Philippines | May 21, 2026 |
| First upgrade modal open | 1 (Minneapolis, iPhone, $AAPL page, May 17 8:12 AM CT) | May 18, 2026 |
| X followers / combined 2nd-degree reach | 4 / ~10.3k combined (Ann Barbour 6.8k, Ashton ~2.3k) | May 21, 2026 |
| Last X post | Day 10 Sector Sweep — RF/analog semis ($SWKS/$QRVO/$ADI/$ON/$MCHP), 7 tweets | May 22, 2026 |

---

## Active priorities

_Replace completed items each session. Keep this list short._

**✅ v1.7.0 — SHIPPED (May 22): weekly digest, all tiers.**
- [x] `run_weekly_digest()` Sunday 08:00 ET cron — scans S&P 100, keeps names that filed a 10-Q/10-K/8-K in the last 7 days, ranks top-10 by FSS, emails active `digest_subscribers` with one-click unsubscribe. The send job that never existed before; subscribers had been promised a Sunday email and it now ships. (METHODOLOGY §16.)
- [x] Digest banner opened to **all tiers**: standard/anonymous → email form; signed-in Pro/Pro+ → one-click "Get the weekly digest" (`POST /digest/subscribe-me`, email resolved server-side from session — never crosses the wire). `/auth/whoami` now returns `digest_subscribed`.
- [x] Validated locally on live SEC data (AAPL/NVDA 100, UNH 92, GE 70, JPM 62; HTML render + 401 guard + cache helpers all pass).
- [x] Deployed + verified May 22: prod `/openapi.json` = 1.7.0, `/health` ok, `/digest/subscribe-me` live. **Still pending:** first real Sunday send (next Sunday 08:00 ET) — watch for `EVENT digest_sent` in `railway logs`.

**▶ NEXT SESSION:**
1. [ ] **Ratify the `MAGIC_LINK_SECRET` rotation decision** (see Open design question below). Drop rotation → v1.6.2 = server-side sessions table (jti revocation) + Sentry hook on auth/email errors. Keep → dual-key fallback (`MAGIC_LINK_SECRET_PREVIOUS`).
2. [ ] **Webhook gap follow-up:** also handle `customer.subscription.created`/`updated` so dashboard-created subs self-heal without requiring sign-in (auth-verify covers the sign-in path; this covers the rest).
3. [ ] **`/test/run-alert-check` returned 403** with the Railway `DEV_SECRET` via `X-Dev-Secret` — reconcile deployed value vs `railway variables`. Non-blocking (the cron path works; only the manual trigger is affected).
4. [ ] Trace `POST /analytics/event 400` (fires twice/page after auth) — `routers/analytics.py` validation.
5. [ ] Short-TTL (60s) cache for the per-page Stripe re-verify in `/auth/whoami` + `/watchlist` (2 Stripe calls/page; fine at 0 users, v1.7.x ticket).
6. [ ] Postman collection regen (still references removed `/subscription/*` + `X-Customer-Id`).
7. [ ] **Day 11 X post — Company Spotlight, methodology-forward (QUEUED for tomorrow; don't draft until then).** Use ONE company as the vehicle to explain *how* EdgarWolf reads a filing: z-scores vs the company's OWN trailing 8-quarter history (MEDIUM ≥2σ, HIGH ≥3σ, fires in BOTH directions), and the Filing Stress Score as a composite — margin z-scores + filing velocity (8-K clustering / 8-K-before-10-Q timing) + XBRL coverage + peer context, not margins alone. Lead candidate: $ENPH (gross margin -3.8σ HIGH, clean data pulled May 22), but confirm against fresh data tomorrow. Pull live numbers + cross-check METHODOLOGY.md before drafting. (Builder Update + Retrospective both recently used — skip them.)
8. [ ] **Ongoing distribution:** 4 replies/day, beta invites to crypto friends, 10 finance Substack writers, r/SecurityAnalysis when mod approves.

**Open design question (parked — Jason to ratify):**
- **Q:** Is weekly `MAGIC_LINK_SECRET` rotation the right security control?
- **Claude's read:** rotation is security theater at current scale (secret never leaves Railway env). Better controls, in order: (1) server-side sessions table keyed by `jti` for revocation (sessions are currently unrevokable JWTs); (2) Sentry/email hook on `auth.py` errors (would have caught the silent Resend-key invalidity); (3) rate-limit anomaly log line. If ratified, drop rotation and make v1.6.2 the sessions-table + Sentry hook rather than the dual-key fallback.

**Tech debt / soon:**
- [ ] **`subscription_success` over-fires** — it fires from authenticated `pro_plus` page state on load (`checkSubscriptionStatus` whoami branch), not just at checkout return, so PostHog over-counts conversions (the 6 events since May 20 were all the comp account, 0 real). Stripe is the source of truth for revenue. Gate the event to the actual checkout-return path.
- [ ] Submit to SaaSWorthy, Product Hunt, G2, Capterra, AlternativeTo.
- [ ] Expand sitemap to /privacy and /terms.
- [ ] Chart.js defensive fix: `responsive: true, maintainAspectRatio: false` + sized wrappers.
- [ ] Filter localhost from PostHog dashboards (Settings → Project → Test accounts).

---

## Current state — May 22, 2026

_Session history lives in `CHANGELOG.md` + git log; settled decisions in `DECISIONS_ARCHIVE.md`._

_**v1.7.0 shipped this session: the weekly Filing Stress digest, now offered to all tiers.** The Sunday 08:00 ET cron (`run_weekly_digest` in `scheduler.py`) scans the S&P 100, keeps names that filed a 10-Q/10-K/8-K in the last 7 days, scores each by FSS, and emails the top 10 to active `digest_subscribers` with a per-recipient one-click unsubscribe. The capture form had been collecting emails against a "each Sunday you'll get…" promise with no job behind it — now there is one. The banner is no longer hidden from paid users: standard/anonymous get the email form, signed-in users get a one-click subscribe (`/digest/subscribe-me`) that resolves their email server-side from the session cookie (never crosses the wire). `/auth/whoami` returns `digest_subscribed` so the banner renders the right state. Validated locally end-to-end on live SEC data; METHODOLOGY §16 documents the selection. Committed + tagged `v1.7.0` + pushed; Railway deployed and verified live (prod on 1.7.0, `/digest/subscribe-me` present, `/health` ok)._

_**Session-start verification.** Prod was healthy on v1.6.1. PostHog showed 6 `subscription_success` (pro_plus) events since May 20 that looked like new customers — Stripe confirmed all are the single comp account (`cus_UUN2ChsZV2aaRC`, $0 invoiced/paid). The event over-fires from authenticated page state (logged as tech debt). Real revenue unchanged: **$0 MRR, 0 external paying users.** Pro+ email alerts remain LIVE (validated May 22; see CLAUDE.md)._

_Still open (carried): ratify the MAGIC_LINK_SECRET rotation decision; close the `customer.subscription.created/updated` webhook gap (sign-in covers it for now); reconcile the `/test/run-alert-check` 403 (cron unaffected). Post-deploy: confirm `/openapi.json` = 1.7.0 and watch for the first real Sunday digest send. Non-product: still watching for any reply from ai_eng@spacex.com._
