# EdgarWolf — Live State

**Updated every session.** Stable context, rules, and the start/end session sequences are in **`CLAUDE.md`** (auto-loaded). This file holds only the volatile state: metrics, active priorities, the next-session plan, and a current-state note.

Current version: **v1.6.1** (2026-05-22). Release history in `CHANGELOG.md`.

---

## Current metrics

_Not refreshed this session — pull PostHog (project 424339) at next session start._

| Metric | Value | Updated |
|--------|-------|---------|
| MRR | $0 | May 22, 2026 |
| Paying users | 0 (+1 comp Pro+: `cus_UUN2ChsZV2aaRC`, $0 MRR) | May 22, 2026 |
| Free signups | 0 | May 20, 2026 |
| X-attributed visits (PostHog, week 1) | 25 distinct visitors | May 21, 2026 |
| Countries (rolling 500-event window) | 4: US, Germany, France, Philippines | May 21, 2026 |
| First upgrade modal open | 1 (Minneapolis, iPhone, $AAPL page, May 17 8:12 AM CT) | May 18, 2026 |
| X followers / combined 2nd-degree reach | 4 / ~10.3k combined (Ann Barbour 6.8k, Ashton ~2.3k) | May 21, 2026 |
| Last X post | Day 9 Retrospective | May 21, 2026 |

---

## Active priorities

_Replace completed items each session. Keep this list short._

**✅ v1.6.1 — SHIPPED + PRO+ ALERTS LIVE (May 22):**
- [x] Auth-verify upsert fix shipped (`a3dbfa1`, v1.6.1), deployed to prod (`/openapi.json` = 1.6.1).
- [x] Signed in via magic link → `/auth/verify` upserted `users.tier=pro_plus` for `cus_UUN2ChsZV2aaRC`.
- [x] **Pro+ email alerts confirmed LIVE.** The scheduled 14:00 ET cron (May 22) ran `entries=2` and sent a real $CAG 8-K alert (`resend_id 00d9f152…`) to jason.ostergren79@gmail.com. Also proven locally end-to-end before the push — the pipeline that had never fired in prod now works. ($AAPL correctly didn't alert — no anomaly signal.)

**▶ NEXT SESSION:**
1. [ ] **Ratify the `MAGIC_LINK_SECRET` rotation decision** (see Open design question below). Drop rotation → v1.6.2 = server-side sessions table (jti revocation) + Sentry hook on auth/email errors. Keep → dual-key fallback (`MAGIC_LINK_SECRET_PREVIOUS`).
2. [ ] **Webhook gap follow-up:** also handle `customer.subscription.created`/`updated` so dashboard-created subs self-heal without requiring sign-in (auth-verify covers the sign-in path; this covers the rest).
3. [ ] **`/test/run-alert-check` returned 403** with the Railway `DEV_SECRET` via `X-Dev-Secret` — reconcile deployed value vs `railway variables`. Non-blocking (the cron path works; only the manual trigger is affected).
4. [ ] Trace `POST /analytics/event 400` (fires twice/page after auth) — `routers/analytics.py` validation.
5. [ ] Short-TTL (60s) cache for the per-page Stripe re-verify in `/auth/whoami` + `/watchlist` (2 Stripe calls/page; fine at 0 users, v1.7.x ticket).
6. [ ] Postman collection regen (still references removed `/subscription/*` + `X-Customer-Id`).
7. [ ] **Distribution:** Day 10 X post (Sector Sweep), 4 replies/day, beta invites to crypto friends, 10 finance Substack writers, r/SecurityAnalysis when mod approves.

**Open design question (parked — Jason to ratify):**
- **Q:** Is weekly `MAGIC_LINK_SECRET` rotation the right security control?
- **Claude's read:** rotation is security theater at current scale (secret never leaves Railway env). Better controls, in order: (1) server-side sessions table keyed by `jti` for revocation (sessions are currently unrevokable JWTs); (2) Sentry/email hook on `auth.py` errors (would have caught the silent Resend-key invalidity); (3) rate-limit anomaly log line. If ratified, drop rotation and make v1.6.2 the sessions-table + Sentry hook rather than the dual-key fallback.

**Tech debt / soon:**
- [ ] Build weekly digest send job — Sunday cron, top 10 FSS companies, emails all `digest_subscribers`, unsubscribe link required.
- [ ] Submit to SaaSWorthy, Product Hunt, G2, Capterra, AlternativeTo.
- [ ] Expand sitemap to /privacy and /terms.
- [ ] Chart.js defensive fix: `responsive: true, maintainAspectRatio: false` + sized wrappers.
- [ ] Filter localhost from PostHog dashboards (Settings → Project → Test accounts).

---

## Current state — May 22, 2026

_Session history lives in `CHANGELOG.md` + git log; settled decisions in `DECISIONS_ARCHIVE.md`._

_**Two things shipped this session.** (1) Restructured the Claude Code docs: stable context + the start/end session sequences now live in auto-loaded `CLAUDE.md`, and this `STATE.md` holds only live state (commit `1c1d7b2`). (2) **v1.6.1** (`a3dbfa1`): `/auth/verify` now fetches tier + email from Stripe and calls `upsert_user` on sign-in, so dashboard-created subs (comps/enterprise/manual) are no longer invisible to the Pro+ alert cron._

_**Pro+ email alerts are now LIVE.** Validated locally first (real $CAG 8-K email landed in inbox, confirmed), then in prod: after sign-in upserted Jason's row, the scheduled 14:00 ET cron ran `entries=2` and sent a real $CAG alert (`resend_id 00d9f152…`). The pricing-critical pipeline that had never once fired in prod is working end-to-end. Both commits + tag `v1.6.1` pushed; Railway deployed 1.6.1._

_Still open: ratify the MAGIC_LINK_SECRET rotation decision; close the `customer.subscription.created` webhook gap (sign-in covers it for now); reconcile the `/test/run-alert-check` 403 (cron unaffected). Non-product: still watching for any reply from ai_eng@spacex.com._
