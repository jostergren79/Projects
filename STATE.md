# EdgarWolf — Live State

**Updated every session.** Stable context, rules, and the start/end session sequences are in **`CLAUDE.md`** (auto-loaded). This file holds only the volatile state: metrics, active priorities, the next-session plan, and a current-state note.

Current version: **v1.7.0** (2026-05-22). Release history in `CHANGELOG.md`.

---

## Current metrics

_Refreshed May 22 (late session, post-analytics pass). **Numbers below are external-only** — Jason's 4 own IPs (`71.34.14.90`, `97.116.24.43`, + 2 IPv6) are now filtered out in PostHog (Settings → internal/test users). PostHog's 6 `subscription_success` are still over-fire — Stripe confirms all are the single comp account, $0 real revenue (see current-state note)._

| Metric | Value | Updated |
|--------|-------|---------|
| MRR | $0 | May 22, 2026 |
| Paying users | 0 (+1 comp Pro+: `cus_UUN2ChsZV2aaRC`, $0 MRR) | May 22, 2026 |
| Free signups (digest) | 0 (22 external banner views, 0 signups) | May 22, 2026 |
| External engaged visitors (PostHog, Jason's IPs filtered, 30d) | 21 people / 4 countries; 18 in last 7 days | May 22, 2026 |
| External funnel (30d) | 22 page_views → 6 company_views → 3 searches; 0 upgrade-modal, 0 watchlist | May 22, 2026 |
| Upgrade-modal opens / watchlist adds (external) | 0 / 0 — all 6 modal opens + 5 adds were Jason's own IPs; the May 17 "first modal open" was self-generated, not a real signal | May 22, 2026 |
| Countries | 4: US, Germany, France, Philippines | May 22, 2026 |
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
- [x] Same-day banner hotfix: dismissal now expires after **7 days** (was a permanent `digest_dismissed='1'` flag that never returned, even in incognito within a session). Stored as a timestamp; legacy `'1'` values parse as epoch → already expired → banner re-surfaces for everyone. Frontend-only, no version bump.

**▶ NEXT SESSION:**
1. [ ] **Webhook gap follow-up:** also handle `customer.subscription.created`/`updated` so dashboard-created subs self-heal without requiring sign-in (auth-verify covers the sign-in path; this covers the rest).
2. [ ] **`/test/run-alert-check` returned 403** with the Railway `DEV_SECRET` via `X-Dev-Secret` — reconcile deployed value vs `railway variables`. Non-blocking (the cron path works; only the manual trigger is affected).
3. [ ] Trace `POST /analytics/event 400` (fires twice/page after auth) — `routers/analytics.py` validation.
4. [ ] Short-TTL (60s) cache for the per-page Stripe re-verify in `/auth/whoami` + `/watchlist` (2 Stripe calls/page; fine at 0 users, v1.7.x ticket).
5. [ ] Postman collection regen (still references removed `/subscription/*` + `X-Customer-Id`).
6. [ ] **Ongoing distribution:** 4 replies/day, beta invites to crypto friends, 10 finance Substack writers, r/SecurityAnalysis when mod approves. **Data-backed (May 22 analytics):** `?cik=` company posts are the *only* engagement driver — 6/6 external company views came from direct company-link entries; signal-board/homepage landers (15) produced **0** click-throughs. Keep every company post CIK-linked; **CPB + MSFT are proven draws.** Open Q worth a cheap test: why do homepage landers bounce without drilling into a company?

**Tech debt / soon:**
- [ ] Submit to SaaSWorthy, Product Hunt, G2, Capterra, AlternativeTo.
- [ ] Expand sitemap to /privacy and /terms.
- [ ] Chart.js defensive fix: `responsive: true, maintainAspectRatio: false` + sized wrappers.
- [ ] PostHog: internal-user IP filter now configured (Jason's 4 IPs; IPv6 truncation typo fixed). **Remaining:** flip "Enable this filter on all new insights" ON so it auto-applies (analysis-level; historical events stay stored). Also still filter localhost.

---

## Current state — May 23, 2026

_Session history lives in `CHANGELOG.md` + git log; settled decisions in `DECISIONS_ARCHIVE.md`._

_**May 23 session — Day 11 X post shipped; `MAGIC_LINK_SECRET` rotation killed (both docs-only, no code).** Posted the Day 11 Company Spotlight: a methodology-forward $ENPH read (Q1 2026 — gross margin 35.5% = -3.8σ HIGH vs its own trailing 8-quarter history; operating margin -4.9% = -2.2σ MEDIUM; FSS 62 MODERATE; revenue $283M, -20.6% YoY; net loss, EPS -$0.06). Built as a single image-led **4:5 portrait data card** (EdgarWolf dark palette, rendered via headless Chrome, legibility verified at ~400px mobile + ~510px desktop) with a **sentence-case** caption + `?cik=0001463101` link. Locked a strategy shift now in CLAUDE.md: own-content = single image-led posts, not multi-tweet threads; case by job (sentence case for own posts, lowercase in replies). Separately ruled out weekly `MAGIC_LINK_SECRET` rotation as theater — never implemented in code, no SECURITY.md claim; settled in DECISIONS_ARCHIVE.md (if revocation is ever needed: `jti` sessions table + Sentry hook on auth errors, not rotation). Prod healthy v1.7.0; external PostHog traffic flat (2 people, US only, 0 conversions) as of May 23. Flagged a real bug to a separate task: narrative summary renders a net loss as positive net income ($ENPH showed "$7M" for a -$7.4M loss). No code shipped → no version bump._

_**v1.7.0 shipped May 22: the weekly Filing Stress digest, now offered to all tiers.** The Sunday 08:00 ET cron (`run_weekly_digest` in `scheduler.py`) scans the S&P 100, keeps names that filed a 10-Q/10-K/8-K in the last 7 days, scores each by FSS, and emails the top 10 to active `digest_subscribers` with a per-recipient one-click unsubscribe. The capture form had been collecting emails against a "each Sunday you'll get…" promise with no job behind it — now there is one. The banner is no longer hidden from paid users: standard/anonymous get the email form, signed-in users get a one-click subscribe (`/digest/subscribe-me`) that resolves their email server-side from the session cookie (never crosses the wire). `/auth/whoami` returns `digest_subscribed` so the banner renders the right state. Validated locally end-to-end on live SEC data; METHODOLOGY §16 documents the selection. Committed + tagged `v1.7.0` + pushed; Railway deployed and verified live (prod on 1.7.0, `/digest/subscribe-me` present, `/health` ok)._

_**Session-start verification.** Prod was healthy on v1.6.1. PostHog showed 6 `subscription_success` (pro_plus) events since May 20 that looked like new customers — Stripe confirmed all are the single comp account (`cus_UUN2ChsZV2aaRC`, $0 invoiced/paid). **Fixed same session:** `subscription_success` no longer fires from the whoami tier-check. The `/success` page now sets a one-time `edgarwolf_pending_conversion` flag (gated on a Stripe-verified *active* sub, so comps/trials are excluded), and the app fires the event once via `fireConversionIfPending()` then clears the flag — so PostHog now counts genuine conversions only. Analytics-guard change, no version bump. Real revenue unchanged: **$0 MRR, 0 external paying users.** Pro+ email alerts remain LIVE (validated May 22; see CLAUDE.md)._

_All three of this session's pushes are deployed + verified live: **v1.7.0** (digest + all-tier banner + one-click subscribe), the **`subscription_success` conversion fix** (fires once on Stripe-verified checkout, no bump), and the **7-day banner-dismissal TTL** (no bump). **Watch next:** the first real Sunday digest send (next Sunday 08:00 ET) — `EVENT digest_sent` in `railway logs`; and treat `subscription_success` as accurate only **after the conversion fix deployed (22:25 CDT May 22 = 03:25 UTC May 23)** — all 6 events to date predate it (latest pair 08:46 CDT / 13:46 UTC May 22) and are the comp account / over-fire, so the fix's post-deploy behavior is **still unobserved** (no real checkout has occurred since). Don't read those 6 as the fix failing._

_**End-of-day verification-only check-in (22:58 CDT May 22), no code changed:** re-confirmed prod healthy on v1.7.0 (`/health` ok, `/openapi.json` = 1.7.0), all commits pushed. Independently re-verified revenue via Stripe — only 2 subscriptions ever exist, both the comp account `cus_UUN2ChsZV2aaRC` (1 active $99, 1 canceled May 10); **still $0 real MRR, 0 external paying customers.** Nothing new in PostHog since the prior session._

_**Late-night analytics pass (May 22): PostHog filtered to external-only + a real-traffic read.** Configured PostHog's internal/test-user filter to exclude Jason's 4 IPs (`71.34.14.90`, `97.116.24.43`, 2 IPv6). First attempt pasted truncated IPv6 strings (literal `...`) that matched 0 events — fixed with the full addresses. Filter is analysis-level (events still stored); **"Enable on all new insights" toggle still needs flipping ON.** **External reality (Jason's IPs excluded, 30d):** 21 engaged people / 4 countries, 18 in the last 7 days — the X push is bringing real, recent humans. Funnel is shallow: 22 page_views → 6 company_views → 3 searches; **0 external upgrade-modal opens, 0 watchlist adds, 0 digest signups** (22 banner views). **Correction:** all `upgrade_modal_open` (6) + `watchlist_add` (5) came from Jason's own IPs — the May 17 "first upgrade modal open" logged as an external signal was self-generated. The 3 "external" `subscription_success` are pre-fix over-fire, not real (Stripe = $0). **Engagement-source finding (most actionable):** there is NO `company_view` tracking gap — the `?cik=` path fires it correctly (`edgar-frontend/edgar.html:1456`, inside `_loadByCikInline`; data confirms 6 `direct_cik` landers = 6 `company_views`). Landing split by `page_view.source`: **6 direct-company (`?cik=`) vs 15 signal-board/homepage** — and ALL 6 company views came from the direct-company entries; the 15 homepage landers produced **0 click-throughs**. Referrer split of the 6: **4 from X/t.co (CPB×2, MSFT×2)**, 2 "direct" (AAPL, UNH — likely X mobile, referrer stripped). **Takeaway: `?cik=` company posts are the sole engagement driver; the signal-board/homepage converts cold traffic at ~0. Keep every company post CIK-linked.**_

_Still open (carried, not addressed in this analytics pass): close the `customer.subscription.created/updated` webhook gap (sign-in covers it for now); reconcile the `/test/run-alert-check` 403 (cron unaffected); the `/analytics/event 400`. Non-product: still watching for any reply from ai_eng@spacex.com._
