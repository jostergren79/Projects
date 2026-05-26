# EdgarWolf — Live State

**Updated every session.** Stable context, rules, and the start/end session sequences are in **`CLAUDE.md`** (auto-loaded). This file holds only the volatile state: metrics, active priorities, the next-session plan, and a current-state note.

Current version: **v1.7.2** (2026-05-26) — 60s shared Stripe re-verify cache across `/auth/whoami` + `/watchlist`; also formally releases the per-device `?internal=1` analytics guard (deployed 2026-05-25). Release history in `CHANGELOG.md`.

---

## Current metrics

_Refreshed May 26. **Numbers below are external-only** — Jason's 4 own IPs (`71.34.14.90`, `97.116.24.43`, + 2 IPv6) are filtered out. Note `71.34.14.90` is the **home-network public IP shared by ≥2 people** (Jason + Sam, via NAT). As of May 25 the durable filter is the per-device `?internal=1` opt-out (the static IP list leaked on rotating cellular/IPv6 — see current-state note); IP filter is now legacy/historical fallback. Two $0 comp Pro+ accounts (`cus_UUN2ChsZV2aaRC`, Sam `cus_UZVNfwfk7hlPBv`); Stripe confirms $0 real revenue._

| Metric | Value | Updated |
|--------|-------|---------|
| MRR | $0 | May 22, 2026 |
| Paying users | 0 (+2 comp Pro+: `cus_UUN2ChsZV2aaRC` + Sam `cus_UZVNfwfk7hlPBv` — both $0 MRR; Sam = "Founder Discount" 100% off forever) | May 24, 2026 |
| Free signups (digest) | 0 external (a May 23 `digest_signup` was on the home IP = internal) | May 25, 2026 |
| External engaged visitors (PostHog, 7d) | ~22 people / 2 countries (US, FR); **today (May 26) = 2 external, both homepage landers** (traffic quiet) | May 26, 2026 |
| External funnel (7d) | 31 page_views (21 ppl) → 2 company_views → 4 searches; the 1 `upgrade_modal_open` + 1 `checkout_start` were **Sam's comp checkout on Verizon cellular IPv6**, not external | May 26, 2026 |
| Real external conversions | 0; the 3 `subscription_success` in the 7d window are all **pre-fix** (May 21–22, before the 03:25 UTC May 23 conversion fix) = comp/duplicate fires, not real customers. After the fix = **0** | May 26, 2026 |
| Countries | 2: US, France (Philippines aged out of the 7d window) | May 26, 2026 |
| Top referrers (7d, external) | direct 13, google 8, t.co (X) 3, edgarwolf.com 1; **LinkedIn still = 0** (no `lnkd.in`/`linkedin.com` referrals) | May 26, 2026 |
| X followers / combined 2nd-degree reach | 4 / ~10.3k combined (Ann Barbour 6.8k, Ashton ~2.3k) | May 21, 2026 |
| Last X post | Day 14 Contrarian/Green — $TTWO turnaround + same-day GTA VI hook (GTA VI was due today, now Nov 19; net income −$125M→+$389M YoY, rev +68%, 2 straight profitable qtrs; net-income-arc 4:5 card + `?cik=0000946581`). ~11 X likes but **0 site click-throughs** at ~2h | May 26, 2026 |
| Last LinkedIn post | Build-in-public retrospective (15 days / 17 releases) — tested channel, ambivalent on continuing; watching referrals | May 25, 2026 |

---

## Active priorities

_Replace completed items each session. Keep this list short._

**✅ Shipped (May 26 AM) — v1.7.2:**
- [x] **60s shared Stripe re-verify cache** — `/auth/whoami` used to hit Stripe on every uncached call; it now reads/writes the same `session_tier_cache` entry as `/watchlist` (key `cust:{id}` via new `session_tier_cache_key()` in `cache.py`). `SESSION_TTL_SECONDS` cut 1h→60s, so a page-load burst collapses to one Stripe call and a lapsed sub loses access within ~1 min. Verified in-process (TestClient + monkeypatch): 2 whoami calls = 1 Stripe call; watchlist then served from the shared entry with 0 Stripe calls; no-cookie → standard. `test_gating.py` 7/7 green. Files: `cache.py`, `routers/auth_router.py`, `routers/watchlist.py`.
- [x] **Postman collection regenerated** — dropped the dead `/subscription/*` group + the `X-Customer-Id` header bypass (auth is the `ew_session` cookie now); added an `Auth` group (whoami/request/verify/logout); rebuilt Watchlist as cookie-only 401-gate tests. 11 groups / 37 requests, JSON valid. (`/analytics/event` kept — it's `include_in_schema=False`, so absent from OpenAPI but live.)

**▶ NEXT SESSION:**

_New from the May 26 PM (distribution) session:_
- [ ] **Micron ($MU) data bug** — dashboard returns impossible XBRL values (+257.6% rev, $28.8B/qtr, 76.6% gross margin); the +3.74 revenue z-flag fires on garbage input. Audit XBRL normalization for non-standard filers; sanity-check Estée Lauder ($EL, 37.5% op margin looks artifactual). Credibility risk if anyone clicks a `?cik=` link to a hot ticker.
- [ ] **Re-check Day 14 post → click-through** — ~11 X likes drove 0 site visits at ~2h (no t.co referrals, no `direct_cik`/CIK 946581 clicks, 0 company_views). Re-pull PostHog next AM to see if clicks lag or the link itself is the leak.
- [ ] **Re-check $AZO** when its Q3 10-Q ingests — reported a Q3 revenue miss May 26 (stock −10%); EdgarWolf only has the Feb 2026 quarter (already −4pp op margin / −3.6 SD). Timely Spotlight if the new quarter confirms it.
- [ ] **Methodology-post idea** — "the model stayed quiet on UNH, Boeing, Intel" (fresh data, 0 flags despite the headlines; Intel's −23.1% op margin / $3B loss didn't even register). Flag deviations, not headlines.

_Carried over:_
1. [ ] **Confirm device-flagging** — did Jason + Sam visit `?internal=1` on each device? Still unconfirmed as of May 26. Until they do, un-flagged household cellular/IPv6 leaks into "external." Can't verify from data alone — both known household IPs (Sam's `2600:1014:b090:...`, home `2607:fb90:9983:...`) have been quiet since May 23, so there's no recent traffic to test against.
2. [ ] **LinkedIn looks like a dead channel** — 0 `lnkd.in`/`linkedin.com` referrals 24h after the May 25 build-in-public retrospective. Decide whether to keep posting there or drop it.
3. [ ] **Webhook self-heal:** handle `customer.subscription.created`/`updated` so dashboard-created subs self-heal without requiring sign-in.
4. [ ] **`/test/run-alert-check` 403** with `DEV_SECRET` via `X-Dev-Secret` — reconcile deployed value vs `railway variables`. Non-blocking (cron path works).
5. [ ] Trace `POST /analytics/event 400` (fires twice/page after auth) — `routers/analytics.py` validation.
6. [ ] **Ongoing distribution:** 4 replies/day, beta invites, finance Substack writers, r/SecurityAnalysis when mod approves. **`?cik=` company posts are the only proven engagement driver** (6/6 external company views came from direct company-link entries; homepage landers convert at ~0). Keep every company post CIK-linked; CPB + MSFT proven draws.

**Tech debt / soon:**
- [ ] Submit to SaaSWorthy, Product Hunt, G2, Capterra, AlternativeTo.
- [ ] Expand sitemap to /privacy and /terms.
- [ ] Chart.js defensive fix: `responsive: true, maintainAspectRatio: false` + sized wrappers.
- [x] ~~PostHog internal-traffic filter leak~~ — fixed via per-device `?internal=1` opt-out (May 25). **Still open:** flip PostHog's "Enable filter on all new insights" ON; filter localhost.

---

## Current state — May 26, 2026

_Session history lives in `CHANGELOG.md` + git log; settled decisions in `DECISIONS_ARCHIVE.md`. This note keeps only the latest 1–2 sessions; older logs were trimmed May 25 (recoverable via git log)._

_**May 26 PM session (distribution) — shipped a Day 14 X post + 3 replies; no code, no revenue change ($0 MRR, 0 external paying).** **(1) Day 14 post (Contrarian/Green):** $TTWO turnaround tied to a same-day GTA VI hook — GTA VI was originally due today (May 26 2026), now confirmed Nov 19 2026 (Rockstar newswire), so the framing is "the business turned profitable before its biggest catalyst ships." Verified reported figures: net income −$125M→+$389M YoY, operating income −$132M→+$367M, revenue +68%, two straight profitable quarters (Sep+Dec '25). Net-income-arc data card built via the headless-Chrome pipeline (`ttwo_card.html`→`ttwo_turnaround.png`, 1080×1350, legibility-checked at 400px), `?cik=0000946581`. Framed as a YoY trajectory (NOT "just filed") because TTWO's FY ends Mar 31, so EdgarWolf's latest quarterly data is Dec '25, not the May 22 10-K — see the `fiscal-year-data-staleness` memory. **(2) 3 X replies** (lowercase, data-first, no pitch): two on $NVDA (a "why down" thread + a 21x-P/E valuation thread; angle = the filings are clean, it's positioning not the numbers — backed by the news: NVDA beat-and-raise May 20 but the stock fell, 4th straight quarter) and one on $TTWO (supporting a bull thread with the pre-GTA-VI turnaround data). Held at 3 of 4 — no clean 4th target. **(3) Data-integrity finding (now a NEXT-SESSION priority):** screening volatile big-caps surfaced a **Micron ($MU) bug** — impossible XBRL values (+257.6% rev, $28.8B/qtr, 76.6% GM); normalization grabs garbage and the revenue z-flag fires on it. $EL op margin 37.5% also looks artifactual. UNH/Boeing/Intel returned fresh data but 0 flags (clean despite the headlines) → a good future Methodology post. **(4) Traffic check:** the Day 14 post's ~11 X likes drove 0 site click-throughs (no t.co referrals, no `?cik=` Take-Two clicks, 0 company_views) as of ~2h; today = 2 external visitors total, both homepage landers. Engagement ≠ traffic again; Jason to re-check later. Prod healthy on v1.7.2; STATE.md doc update only, no deploy._

_**May 26 AM session — shipped v1.7.2 (60s shared Stripe re-verify cache + Postman regen); no revenue change ($0 MRR, 0 external paying).** Focus was data-hygiene + tech debt. **(1) 60s Stripe re-verify cache:** `/auth/whoami` was hitting Stripe on every uncached call; it now shares `/watchlist`'s `session_tier_cache` entry (key `cust:{id}` via the new `session_tier_cache_key()` in `cache.py`), and `SESSION_TTL_SECONDS` dropped 1h→60s. Net: a page-load burst of tier checks collapses to one Stripe call, and a lapsed sub loses access within ~1 min (was up to 1h on watchlist; whoami was fully uncached). Verified in-process (TestClient + monkeypatch): 2 whoami calls = 1 Stripe call, watchlist then served 0-Stripe from the shared entry, no-cookie → standard; `test_gating.py` 7/7 green. Files: `cache.py`, `routers/auth_router.py`, `routers/watchlist.py`. **(2) Postman regen:** removed the dead `/subscription/*` group + the `X-Customer-Id` header bypass (auth is the `ew_session` cookie now), added an `Auth` group (whoami/request/verify/logout), rebuilt Watchlist as cookie-only 401-gate tests (11 groups / 37 requests, JSON valid). **(3) Start-of-session reads:** prod was healthy on v1.7.1 pre-deploy; PostHog 7d external = 21 ppl / 2 countries (US, FR — Philippines aged out), funnel 31 pv → 2 company_views → 4 searches, last-24h quiet (2 ppl, page_views only). The 3 `subscription_success` in the 7d window are all pre-fix (May 21–22) comp/duplicate fires, not real conversions; after the May 23 fix = 0. LinkedIn referrals = 0 a full day after the May 25 retrospective — looks like a dead channel. **(4) Open for Jason:** still no confirmation that he + Sam visited `?internal=1` on each device (NEXT-SESSION #1); un-flagged household devices keep leaking, and it can't be verified from data since both household IPs have been quiet since May 23. Committed + tagged v1.7.2 and pushed; Railway auto-deploys — verify `/openapi.json` shows 1.7.2 at the next session start._

_**May 25 session (Monday) — shipped a Day 13 X post and fixed the PostHog filter leak; no real revenue change ($0 MRR, 0 external paying).** **(1) Start-of-session catch:** PostHog appeared to show the first-ever external conversion activity (1 `upgrade_modal_open` + 1 `checkout_start`, vs 0 before). Traced it — it was **Sam's comp Pro+ checkout on a Verizon cellular IPv6** (`2600:1014:...`, not in the 4-IP filter) that completed as his $0 comp sub at 20:41 UTC May 23, not a real external customer. Also confirmed `subscription_success` after the conversion fix (03:25 UTC May 23) = **0** — the fix is now observed suppressing Sam's post-fix comp checkout correctly (previously "unobserved"). **(2) Day 13 X post (Company Spotlight/Methodology):** $AAP earnings-quality flip — net income flat at $24M YoY, but operating income swung −$131M→+$69M and gross margin +2.2pp to 45.1% (quarter ended Apr 26 2026, 10-Q filed May 21). All figures verified vs prod `reported` XBRL; card built via the headless-Chrome pipeline (`aap_card.html`→`aap_quality_flip.png`, 1080×1350, legibility-checked at 400px), sentence-case caption, `?cik=0001158449`. Posted live. **(3) Filter-leak fix shipped + deployed:** per-device `?internal=1` opt-out (localStorage flag → frontend skips PostHog init + `trackEvent` no-ops; `?internal=0` clears). IP-independent, so it beats the cellular/home-IPv6 rotation the static 4-IP list couldn't catch (mirrors the localhost guard). Verified end-to-end (node --check; headless set/persist-across-reload/clear vs the uvicorn access log), committed `93559b2`, pushed, deployed live (prod serves the new code ~110s after push; `/health` ok). No version bump (analytics guard); CHANGELOG `[Unreleased]`. **ACTION for Jason + Sam:** visit `https://www.edgarwolf.com/?internal=1` once on every device/browser, or household traffic keeps leaking; pre-May-25 events stay in PostHog so the legacy IP filter still applies to historical queries. `reference_posthog` memory updated with the new mechanism. **(4) New channel:** Jason posted a build-in-public retrospective to LinkedIn (15 days / 17 releases). Tested channel, ambivalent on continuing; asked to watch referrals. Baseline = 0 `lnkd.in` referrals at ~2h (top 3-day external referrers: google 14 hits/7 ppl, t.co 3, direct 3). Prod healthy on v1.7.1 (+ the unreleased analytics guard)._
