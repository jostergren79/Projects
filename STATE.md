# EdgarWolf — Live State

**Updated every session.** Stable context, rules, and the start/end session sequences are in **`CLAUDE.md`** (auto-loaded). This file holds only the volatile state: metrics, active priorities, the next-session plan, and a current-state note.

Current version: **v1.7.1** (2026-05-24); prod also carries one unreleased analytics-guard change — the per-device `?internal=1` opt-out, deployed 2026-05-25, no version bump. Release history in `CHANGELOG.md`.

---

## Current metrics

_Refreshed May 25. **Numbers below are external-only** — Jason's 4 own IPs (`71.34.14.90`, `97.116.24.43`, + 2 IPv6) are filtered out. Note `71.34.14.90` is the **home-network public IP shared by ≥2 people** (Jason + Sam, via NAT). As of May 25 the durable filter is the per-device `?internal=1` opt-out (the static IP list leaked on rotating cellular/IPv6 — see current-state note); IP filter is now legacy/historical fallback. Two $0 comp Pro+ accounts (`cus_UUN2ChsZV2aaRC`, Sam `cus_UZVNfwfk7hlPBv`); Stripe confirms $0 real revenue._

| Metric | Value | Updated |
|--------|-------|---------|
| MRR | $0 | May 22, 2026 |
| Paying users | 0 (+2 comp Pro+: `cus_UUN2ChsZV2aaRC` + Sam `cus_UZVNfwfk7hlPBv` — both $0 MRR; Sam = "Founder Discount" 100% off forever) | May 24, 2026 |
| Free signups (digest) | 0 external (a May 23 `digest_signup` was on the home IP = internal) | May 25, 2026 |
| External engaged visitors (PostHog, 7d) | 22 people / 3 countries (US 20, FR 1, PH 1); **last 24h = 1** (traffic quiet) | May 25, 2026 |
| External funnel (7d) | 31 page_views (22 ppl) → 3 company_views → 4 searches; the 1 `upgrade_modal_open` + 1 `checkout_start` were **Sam's comp checkout on Verizon cellular IPv6**, not external | May 25, 2026 |
| Real external conversions | 0; `subscription_success` after the conversion fix (03:25 UTC May 23) = **0** — fix now observed suppressing Sam's post-fix comp checkout correctly | May 25, 2026 |
| Countries | 3: US, France, Philippines (Germany aged out of the 7d window) | May 25, 2026 |
| Top referrers (3d, external) | google 14 hits/7 ppl, t.co (X) 3, direct 3; **LinkedIn = 0** (post ~2h old — watch next session) | May 25, 2026 |
| X followers / combined 2nd-degree reach | 4 / ~10.3k combined (Ann Barbour 6.8k, Ashton ~2.3k) | May 21, 2026 |
| Last X post | Day 13 Company Spotlight/Methodology — $AAP earnings-quality flip (flat $24M net income YoY; operating income −$131M→+$69M; 4:5 card + `?cik=0001158449`) | May 25, 2026 |
| Last LinkedIn post | Build-in-public retrospective (15 days / 17 releases) — tested channel, ambivalent on continuing; watching referrals | May 25, 2026 |

---

## Active priorities

_Replace completed items each session. Keep this list short._

**✅ Shipped this session (May 25):**
- [x] **Day 13 X post** — $AAP earnings-quality-flip data card (flat $24M net income YoY, operating income −$131M→+$69M, gross margin +2.2pp→45.1%; quarter ended Apr 26 2026, 10-Q filed May 21). All figures verified vs prod `reported` XBRL; built via the headless-Chrome pipeline (`aap_card.html`→`aap_quality_flip.png`, 1080×1350, legibility-checked at 400px), sentence-case caption, `?cik=0001158449`. Posted live.
- [x] **PostHog filter-leak fix** — per-device `?internal=1` opt-out (sets `localStorage.edgarwolf_internal`; frontend then skips PostHog init + `trackEvent` no-ops → device emits zero events; `?internal=0` clears). IP-independent, so it survives the cellular/IPv6 rotation that defeated the 4-IP filter (mirrors the localhost guard). Verified end-to-end (node --check + headless set/persist/clear vs access log); committed `93559b2`, pushed, **deployed live** (no version bump — analytics guard; CHANGELOG `[Unreleased]`).

**▶ NEXT SESSION:**
1. [ ] **Confirm device-flagging** — did Jason + Sam visit `?internal=1` on each device? Until they do, household cellular/IPv6 still leaks into "external." Then re-read external metrics (should be cleaner).
2. [ ] **Watch LinkedIn referrals** — Jason posted a build-in-public retrospective May 25 (tested channel, ambivalent). Baseline = 0 `lnkd.in`/`linkedin.com` referrals at ~2h; check whether it drove real click-throughs.
3. [ ] **Webhook gap follow-up:** also handle `customer.subscription.created`/`updated` so dashboard-created subs self-heal without requiring sign-in.
4. [ ] **`/test/run-alert-check` 403** with `DEV_SECRET` via `X-Dev-Secret` — reconcile deployed value vs `railway variables`. Non-blocking (cron path works).
5. [ ] Trace `POST /analytics/event 400` (fires twice/page after auth) — `routers/analytics.py` validation.
6. [ ] Short-TTL (60s) cache for the per-page Stripe re-verify in `/auth/whoami` + `/watchlist`.
7. [ ] Postman collection regen (still references removed `/subscription/*` + `X-Customer-Id`).
8. [ ] **Ongoing distribution:** 4 replies/day, beta invites, finance Substack writers, r/SecurityAnalysis when mod approves. **`?cik=` company posts are the only proven engagement driver** (6/6 external company views came from direct company-link entries; homepage landers convert at ~0). Keep every company post CIK-linked; CPB + MSFT proven draws.

**Tech debt / soon:**
- [ ] Submit to SaaSWorthy, Product Hunt, G2, Capterra, AlternativeTo.
- [ ] Expand sitemap to /privacy and /terms.
- [ ] Chart.js defensive fix: `responsive: true, maintainAspectRatio: false` + sized wrappers.
- [x] ~~PostHog internal-traffic filter leak~~ — fixed via per-device `?internal=1` opt-out (May 25). **Still open:** flip PostHog's "Enable filter on all new insights" ON; filter localhost.

---

## Current state — May 25, 2026

_Session history lives in `CHANGELOG.md` + git log; settled decisions in `DECISIONS_ARCHIVE.md`. This note keeps only the latest 1–2 sessions; older logs were trimmed May 25 (recoverable via git log)._

_**May 25 session (Monday) — shipped a Day 13 X post and fixed the PostHog filter leak; no real revenue change ($0 MRR, 0 external paying).** **(1) Start-of-session catch:** PostHog appeared to show the first-ever external conversion activity (1 `upgrade_modal_open` + 1 `checkout_start`, vs 0 before). Traced it — it was **Sam's comp Pro+ checkout on a Verizon cellular IPv6** (`2600:1014:...`, not in the 4-IP filter) that completed as his $0 comp sub at 20:41 UTC May 23, not a real external customer. Also confirmed `subscription_success` after the conversion fix (03:25 UTC May 23) = **0** — the fix is now observed suppressing Sam's post-fix comp checkout correctly (previously "unobserved"). **(2) Day 13 X post (Company Spotlight/Methodology):** $AAP earnings-quality flip — net income flat at $24M YoY, but operating income swung −$131M→+$69M and gross margin +2.2pp to 45.1% (quarter ended Apr 26 2026, 10-Q filed May 21). All figures verified vs prod `reported` XBRL; card built via the headless-Chrome pipeline (`aap_card.html`→`aap_quality_flip.png`, 1080×1350, legibility-checked at 400px), sentence-case caption, `?cik=0001158449`. Posted live. **(3) Filter-leak fix shipped + deployed:** per-device `?internal=1` opt-out (localStorage flag → frontend skips PostHog init + `trackEvent` no-ops; `?internal=0` clears). IP-independent, so it beats the cellular/home-IPv6 rotation the static 4-IP list couldn't catch (mirrors the localhost guard). Verified end-to-end (node --check; headless set/persist-across-reload/clear vs the uvicorn access log), committed `93559b2`, pushed, deployed live (prod serves the new code ~110s after push; `/health` ok). No version bump (analytics guard); CHANGELOG `[Unreleased]`. **ACTION for Jason + Sam:** visit `https://www.edgarwolf.com/?internal=1` once on every device/browser, or household traffic keeps leaking; pre-May-25 events stay in PostHog so the legacy IP filter still applies to historical queries. `reference_posthog` memory updated with the new mechanism. **(4) New channel:** Jason posted a build-in-public retrospective to LinkedIn (15 days / 17 releases). Tested channel, ambivalent on continuing; asked to watch referrals. Baseline = 0 `lnkd.in` referrals at ~2h (top 3-day external referrers: google 14 hits/7 ppl, t.co 3, direct 3). Prod healthy on v1.7.1 (+ the unreleased analytics guard)._

_**May 24 (Sunday) — v1.7.1, first digest send, 2nd comp.** Shipped v1.7.1 (`46798d3`): net-loss display fix — loss-making quarters had dropped the negative sign; display-only, API always correctly signed (see CHANGELOG). Weekly digest validated in prod: first real Sunday send fired 2026-05-24 12:03:59 UTC, `digest_sent recipients=2 companies=10`; next run May 31 08:00 ET. Identified **Sam Ostergren** (`cus_UZVNfwfk7hlPBv`) as a 2nd $0 comp — family, "Founder Discount" 100% off forever, no lapse risk; a signed-in NVDA browse under the home IP `71.34.14.90` traced to him (NAT collapses all home devices to one public IP, so household activity is correctly internal). MRR unchanged: $0._
