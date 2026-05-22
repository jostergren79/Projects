# EdgarWolf — Live State

**Updated every session.** Stable context, rules, and the start/end session sequences are in **`CLAUDE.md`** (auto-loaded). This file holds only the volatile state: metrics, active priorities, the next-session plan, and a current-state note.

Current version: **v1.6.0** (2026-05-19). Release history in `CHANGELOG.md`.

---

## Current metrics

| Metric | Value | Updated |
|--------|-------|---------|
| MRR | $0 | May 20, 2026 |
| Paying users | 0 | May 20, 2026 |
| Free signups | 0 | May 20, 2026 |
| X-attributed visits (PostHog, week 1) | 25 distinct visitors | May 21, 2026 |
| Countries (rolling 500-event window) | 4: US, Germany, France, Philippines | May 21, 2026 |
| First upgrade modal open | 1 (Minneapolis, iPhone, $AAPL page, May 17 8:12 AM CT) | May 18, 2026 |
| X followers / combined 2nd-degree reach | 4 followers / ~10.3k combined (Ann Barbour 6.8k, Ashton ~2.3k, others ~1.2k) | May 21, 2026 |
| Day 7 Builder Update post on X | posted May 19 evening | May 20, 2026 |
| Day 8 Methodology post on X | posted May 20 morning ($CAG Q3 FY26, 4 flags, 2-yr op margin trajectory) | May 20, 2026 |
| Day 9 Retrospective post on X | posted May 21 afternoon (3 lessons: "live" ≠ "tested", silent failures, show your work) | May 21, 2026 |

---

## Active priorities

_Replace completed items each session. Keep this list short._

**▶ NEXT SESSION — order of operations (planned May 21, for Fri May 22 AM):**
1. [ ] **Ship v1.6.1 auth-verify upsert fix** — ~3 lines in `routers/auth_router.py:verify_endpoint`: after validating the token + confirming the Stripe sub, call `upsert_user(customer_id, email, tier_from_stripe)`. Bump VERSION→1.6.1, CHANGELOG, commit, tag, push.
2. [ ] Wait for Railway deploy Active; confirm `/openapi.json` shows 1.6.1.
3. [ ] Re-trigger auth flow to backfill Jason's user row: `POST /auth/request` → click magic link → `GET /auth/verify`. Confirm `upsert_user` fires in logs.
4. [ ] Verify `users.tier` row exists in prod (temp `/admin/whoami-debug` endpoint or one-time log line; tear down after).
5. [ ] Trigger `run_alert_check()` (next top-of-hour M–F cron, or one-off script). Confirm `EVENT alert_check_start entries>=1` → `EVENT alert_sent` for $CAG → email lands + renders + click-through works.
6. [ ] Once validated, flip the Pro+ email-alert status to LIVE — here in STATE.md and the caveat in `CLAUDE.md` (§1 Product, §3 Pricing).
7. [ ] Then parked items: MAGIC_LINK_SECRET rotation decision, dual-key vs sessions-table+Sentry, analytics 400 trace, Stripe-per-page cache.
8. [ ] Distribution: Day 10 X post (Sector Sweep — re-opens rotation), 4 replies/day, Substack outreach, r/SecurityAnalysis check.

**v1.6.0 deploy — CLOSED OUT May 21:**
- [x] **Deploy live.** v1.6.0 confirmed via `/openapi.json` on May 20 afternoon. Railway queue cleared.
- [x] **Smoke test (automated items):** `/health` ok + cache healthy ✅. `/auth/whoami` without cookie → `{"tier":"standard","label":"Standard"}` ✅. `/auth/request` with unknown email → `{"ok":true}` ✅. All 4 new auth endpoints present; all 3 deprecated `/subscription/*` endpoints removed ✅.
- [x] **Magic-link round-trip — VERIFIED May 21.** New Resend key was Active. `POST /auth/request` for jason.ostergren79@gmail.com → Stripe customer lookup 200 → active sub on `cus_UUN2ChsZV2aaRC` 200 → `EVENT magic_link_sent email=j***@gmail.com`. Jason clicked link in inbox → `/auth/verify` returned 303 to `/?signed_in=1` with `ew_session` cookie set (HttpOnly, Secure, SameSite=Lax, 30-day Max-Age). `EVENT auth_verified customer_id=cus_UUN2ChsZV2aaRC` fired. Curl with cookie jar: `/auth/whoami` → `{"tier":"pro_plus","label":"Pro+"}`, `/watchlist` → `{"items":[],"count":0,"limit":50}`. Full auth chain working end-to-end.
- [x] Railway env vars set May 20: `SEC_REQUIRE_EXPLICIT_USER_AGENT=true`, `SEC_USER_AGENT=EdgarWolf/1.6.0 jason@edgarwolf.com`. SEC-backed endpoints returning real data.
- [ ] Postman collection regeneration — still references `/subscription/restore`, `/subscription/status*`, and `X-Customer-Id`. Separate commit, low priority.

**Open design question (parked May 21 — Claude's recommendation below, Jason to ratify next session):**
- **Q:** Is weekly `MAGIC_LINK_SECRET` rotation the right security control?
- **Claude's read:** Weekly rotation is security theater at current scale. It only defends against a leaked secret, and the secret never leaves Railway env vars. Recommended replacement controls, in order of value:
  1. **Server-side sessions table** keyed by `jti` so individual sessions are revocable on suspicion. Currently sessions are pure JWTs and unrevokable until expiry.
  2. **Sentry (or equivalent) hook on `auth.py` `RuntimeError`** — would have caught the silent Resend-key invalidity instantly. Generalize to all email failures.
  3. **Rate-limit anomaly log line** — distinct event when `/auth/request` returns rate-limited, so it's greppable/alertable.
- **Decision pending:** if Jason ratifies, drop weekly rotation as a calendar item; v1.6.1 becomes the sessions table + Sentry hook rather than dual-key fallback. Dual-key fallback drops to "only if you ever do rotate."

**v1.6.1 candidates (which one wins depends on the rotation decision above PLUS the auth-verify upsert gap below):**
- [ ] **Auth-verify upserts user record (DISCOVERED MAY 21, REAL BUG).** Only the `checkout.session.completed` webhook writes to `users.tier`. Dashboard-created subs (comps, enterprise, manual) bypass it. `/auth/verify` validates against Stripe live but never persists. Result: `users.tier` can be silently stale for any non-checkout user — and the alert cron's `WHERE u.tier='pro_plus'` filter excludes them. Fix: have `/auth/verify` call `upsert_user(customer_id, email, tier_from_stripe)` after confirming the active sub. ~3 lines in `routers/auth_router.py`. Promotes to top of v1.6.1 because it directly blocks Pro+ alert validation.
- [ ] **Dual-key fallback** — `MAGIC_LINK_SECRET_PREVIOUS` in `verify_token` (~10 lines). Only useful if weekly rotation stays.
- [ ] **Sessions table + Sentry hook** — server-side session row keyed by jti for revocation; Sentry/email alert on `auth.py` errors. Preferred if rotation is dropped.

**New tech debt surfaced May 21 (from smoke-test log review):**
- [ ] `POST /analytics/event 400 Bad Request` fires twice per page load after auth. Frontend is sending a malformed event payload somewhere. Trace via browser network tab + `routers/analytics.py` validation.
- [ ] Every `/auth/whoami` and `/watchlist` call hits Stripe to re-verify the subscription (~140ms each). 2 Stripe API calls per page. Fine at 0 users; add a short-TTL cache (60s) keyed on `customer_id` before scale. Low priority until traffic shows up but worth a v1.7.x ticket.
- [ ] **Validate Pro+ email alert pipeline end-to-end** — code-complete and scheduled, but BLOCKED on the auth-verify upsert gap above. May 21 attempt: added $CAG and $AAPL to `cus_UUN2ChsZV2aaRC` watchlist before the 22:00 UTC cron. Cron fired and "executed successfully" per apscheduler, but `EVENT alert_check_start` never logged. Root cause traced to `get_all_pro_plus_watchlists()` returning empty because `users.tier` for the comp sub is stale (never upserted). Unblocks once v1.6.1 auth-verify upsert lands and Jason's user row is backfilled. Then test on the next M-F top-of-hour cron (next opportunity: Fri May 22 8:00 AM ET). Pro+ pricing depends on this working.

**Immediate:**
- [x] Day 9 X post — Retrospective shipped May 21. 3 lessons format: "live ≠ tested", silent failures, show-your-work. Honest 0% conversion framing, terse builder voice.
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

## Current state — May 21, 2026 (late)

_Session history lives in `CHANGELOG.md` + git log; settled decisions in `DECISIONS_ARCHIVE.md`. Older narratives (May 18–20: v1.5.4/v1.5.5 security pass, v1.6.0 build/deploy, the Resend-key debug saga, Day 7/8 X posts) are in CHANGELOG._

_v1.6.0 fully verified in prod: magic-link round-trip end-to-end (Resend Active → `EVENT magic_link_sent` → browser-clicked + curl-verified → `/auth/whoami` returns `pro_plus`, `/watchlist` returns empty list with cookie auth); all security headers present. Day 9 Retrospective X post shipped; 4th X follower (~10.3k combined 2nd-degree reach). Pro+ alert validation attempted and surfaced a REAL architectural bug: neither the checkout webhook nor `/auth/verify` upserts `users.tier` for dashboard-created subs (comps/enterprise/manual), so the alert cron's `WHERE u.tier='pro_plus'` silently excludes them — that's why the 22:00 UTC cron fired but `EVENT alert_check_start` never logged. Fix is ~3 lines in `routers/auth_router.py`, top of the v1.6.1 queue (see NEXT SESSION above). Non-product side quest: sent an honest SpaceXAI engineer application to ai_eng@spacex.com from jason@edgarwolf.com — watch for a reply, don't let it disrupt the v1.6.1 push._
