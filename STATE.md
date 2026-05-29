# EdgarWolf — Live State

**Updated every session.** Stable context, rules, and the start/end session sequences are in **`CLAUDE.md`** (auto-loaded). This file holds only the volatile state: metrics, active priorities, the next-session plan, and a current-state note.

Current version: **v1.7.4** (2026-05-28) — conversion-focused frontend release: digest banner now surfaces after a company loads (new copy + "Send me Sunday's" CTA), landing subhead rewritten to the anomaly value prop, and the upgrade modal names the viewed company. (v1.7.3 = XBRL `(start_date, fp)` differencing fix + dynamic per-CIK OG images.) Release history in `CHANGELOG.md`.

---

## Current metrics

_Refreshed May 29. **Numbers below are external-only** — Jason's 4 own IPs (`71.34.14.90`, `97.116.24.43`, + 2 IPv6) are filtered out. Note `71.34.14.90` is the **home-network public IP shared by ≥2 people** (Jason + Sam, via NAT). As of May 25 the durable filter is the per-device `?internal=1` opt-out; IP filter is now legacy/historical fallback. Two $0 comp Pro+ accounts (`cus_UUN2ChsZV2aaRC`, Sam `cus_UZVNfwfk7hlPBv`); Stripe confirms $0 real revenue._

| Metric | Value | Updated |
|--------|-------|---------|
| MRR | $0 | May 29, 2026 |
| Paying users | 0 (+2 comp Pro+: `cus_UUN2ChsZV2aaRC` + Sam `cus_UZVNfwfk7hlPBv` — both $0 MRR) | May 29, 2026 |
| Free signups (digest) | 0 external | May 29, 2026 |
| External engaged visitors (24h) | 1 session at ~1:20 AM UTC May 29 — Google → homepage → searched → TANGER INC (CIK 0000899715) → upgrade_modal_open → no conversion. 1 digest_banner_view (no signup). 0 t.co referrals. | May 29, 2026 |
| Real external conversions | 0 | May 29, 2026 |
| Countries | 2: US, France | May 29, 2026 |
| Top referrers (7d, external) | google, direct — t.co = 0, LinkedIn = 0 | May 29, 2026 |
| X followers / combined 2nd-degree reach | 4 / ~10.3k combined (Ann Barbour 6.8k, Ashton ~2.3k) | May 21, 2026 |
| Last X post | Day 16 — $BA methodology card (exception flags 0 vs FSS 100/100; "two signals, two questions") posted May 29 | May 29, 2026 |
| Last LinkedIn post | Build-in-public retrospective (15 days / 17 releases) + DM sent to Allie K. Miller | May 27, 2026 |

---

## Active priorities

_Replace completed items each session. Keep this list short._

**✅ Shipped (May 29) — analytics tracking fixes (no version bump — analytics plumbing):**
- [x] **`company_view` tracking gap fixed** — event was only firing on direct `?cik=` loads; search-path arrivals (the majority of organic Google traffic) were invisible to funnel analytics. Now fires in both paths.
- [x] **`digest_banner_view` URL corrected** — `history.pushState` moved before `renderDashboard` in search flow; in-render events now capture company URL instead of homepage URL.

**✅ Distribution (May 29):**
- [x] Day 16 — $BA methodology card posted: exception flags 0 vs FSS 100/100, "two signals, two questions" angle. No replies (Friday).

**▶ NEXT SESSION:**

1. [ ] **Watch conversion metrics** — `company_view` now fires in search path; next session check if funnel data looks healthier. v1.7.4 baseline: 1 upgrade modal open / 0 convert. Also watch digest signup rate post-banner-fix.
2. [ ] **$AZO Q3 Spotlight** — Q3 XBRL **not yet ingested** (latest period still Feb 2026 / Q2). Watch for ingestion; post fresh Spotlight once data lands.
3. [ ] **Trace `POST /analytics/event 400`** — fires twice/page after auth — `routers/analytics.py` validation.
4. [ ] **Webhook self-heal** — handle `customer.subscription.created`/`updated` so dashboard-created subs activate without requiring sign-in.
5. [ ] **LinkedIn channel decision** — DM to Allie K. Miller (May 27) still unanswered; 0 referrals. Watch for reply; decide whether to keep posting.
6. [ ] **Ongoing distribution** — 4 replies/day target; reply threads into high-impression accounts are the proven reach driver. Monday pre-market = peak window.

**Tech debt / soon:**
- [ ] Submit to SaaSWorthy, Product Hunt, G2, Capterra, AlternativeTo.
- [ ] Expand sitemap to /privacy and /terms.
- [ ] Chart.js defensive fix: `responsive: true, maintainAspectRatio: false` + sized wrappers.
- [ ] `/test/run-alert-check` 403 with `DEV_SECRET` — reconcile deployed value vs `railway variables`. Non-blocking.
- [x] ~~PostHog internal-traffic filter leak~~ — fixed May 25. **Still open:** flip PostHog's "Enable filter on all new insights" ON; filter localhost.

---

## Current state — May 29, 2026

_Session history lives in `CHANGELOG.md` + git log; settled decisions in `DECISIONS_ARCHIVE.md`. This note keeps only the latest 1–2 sessions._

_**May 29 session (Friday, light) — posted Day 16 X card + fixed 2 analytics tracking bugs; no revenue change ($0 MRR, 0 external paying).** **(1) X post:** Boeing $BA methodology card — "two signals, two questions" angle (exception flags 0 vs FSS 100/100 ELEVATED; news hook = FAA production ramp cleared May 27). Option A copy. No replies (Friday, Jason zonked). **(2) Analytics fixes (commit d21df56, no version bump):** (a) `company_view` event was missing from the search path — only fired on direct `?cik=` URL loads; any user arriving via search (majority of Google organic) was invisible to company-level funnel tracking. Fixed by adding `trackEvent('company_view', ...)` to `search()` in `edgar-frontend/edgar.html`. (b) `history.pushState` was running after `renderDashboard`, so in-render events like `digest_banner_view` logged the homepage URL instead of the company URL. Fixed by moving `pushState` + back-bar display before `renderDashboard`. **(3) PostHog (May 29):** 1 external engaged session early AM — Google → TANGER INC via search → upgrade_modal_open (company: TANGER INC) → no conversion; 0 signups. Session was pre-fix so company_view still showed 0. **(4) Prod health:** v1.7.4 online, Railway healthy._

_**May 28 session — shipped v1.7.4 (conversion-focused frontend release) + doc cleanup; no revenue change ($0 MRR, 0 external paying). Digest banner gated post-company-view; landing subhead → anomaly value prop; upgrade modal names viewed company. PostHog: 22 banner views / 0 signups, 1 modal open / 0 convert (baseline). $AZO Q3 not yet ingested. LinkedIn: 0 reply from Allie K. Miller.**_
