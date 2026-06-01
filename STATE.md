# EdgarWolf — Live State

**Updated every session.** Stable context, rules, and the start/end session sequences are in **`CLAUDE.md`** (auto-loaded). This file holds only the volatile state: metrics, active priorities, the next-session plan, and a current-state note.

Current version: **v1.7.4** (2026-05-28) — conversion-focused frontend release: digest banner now surfaces after a company loads (new copy + "Send me Sunday's" CTA), landing subhead rewritten to the anomaly value prop, and the upgrade modal names the viewed company. (v1.7.3 = XBRL `(start_date, fp)` differencing fix + dynamic per-CIK OG images.) Release history in `CHANGELOG.md`.

---

## Current metrics

_Refreshed May 31. **Numbers below are external-only** — Jason's 4 own IPs (`71.34.14.90`, `97.116.24.43`, + 2 IPv6) are filtered out. Note `71.34.14.90` is the **home-network public IP shared by ≥2 people** (Jason + Sam, via NAT). As of May 25 the durable filter is the per-device `?internal=1` opt-out; IP filter is now legacy/historical fallback. Two $0 comp Pro+ accounts (`cus_UUN2ChsZV2aaRC`, Sam `cus_UZVNfwfk7hlPBv`); Stripe confirms $0 real revenue._

| Metric | Value | Updated |
|--------|-------|---------|
| MRR | $0 | May 31, 2026 |
| Paying users | 0 (+2 comp Pro+: `cus_UUN2ChsZV2aaRC` + Sam `cus_UZVNfwfk7hlPBv` — both $0 MRR) | May 31, 2026 |
| Free signups (digest) | 0 external | May 31, 2026 |
| External engaged visitors | 0 engaged external sessions May 30–31. May 30 = 4 homepage-only hits, all `$direct`, ≥2 from a GCP crawler IP (`104.197.69.115`) — no `company_view`, no signup, no conversion. Last real engaged session remains the May 29 TANGER INC visit (→ upgrade_modal_open → no convert). | May 31, 2026 |
| Real external conversions | 0 | May 31, 2026 |
| Countries | 2: US, France | May 31, 2026 |
| Top referrers (7d, external) | google, direct — t.co = 0, LinkedIn = 0 | May 31, 2026 |
| X followers / combined 2nd-degree reach | 4 / ~10.3k combined (Ann Barbour 6.8k, Ashton ~2.3k) | May 21, 2026 |
| Last X post | Day 17 — $HEI HEICO card (operating margin 25.5%, 3.8 SD above its own 8-qtr avg; "exception flags fire in both directions"; rev +25%, NI $234M); posted Sun May 31 | May 31, 2026 |
| Last LinkedIn post | Build-in-public retrospective (15 days / 17 releases) + DM sent to Allie K. Miller | May 27, 2026 |

---

## Active priorities

_Replace completed items each session. Keep this list short._

**✅ Distribution (May 31):**
- [x] Day 17 — $HEI HEICO card posted (Sun): operating margin 25.5%, 3.8 SD above its own 8-qtr avg, highest in 3+ years; "exception flags fire in both directions" angle (follows Friday's $BA "deviation from own history" beat). SEC-verified: HEICO OM, Lowe's GM, Snowflake/HEICO/Lowe's NI+EPS all matched EDGAR XBRL exactly.

**▶ NEXT SESSION:**

1. [ ] **MONDAY (Jun 1) pre-market post** — peak window. **$LOW Lowe's card is already built + SEC-verified + ready to render** (`/tmp/card_low.html`: sales +10% but gross margin 32.7%, ~3.0 SD below its own avg — divergence angle). Just render to PNG and post. Hold for replies: Lowe's GM dip invites a "that's just tariffs/housing" debate — answer with "the model flags the deviation, not the cause."
2. [ ] **Watch conversion metrics** — `company_view` now fires in search path (fixed May 29); check if funnel looks healthier. Baseline: 1 upgrade-modal open / 0 convert. Also watch digest signup rate post-banner-fix.
3. [ ] **Trace `POST /analytics/event 400`** — confirmed cause: frontend fires `subscription_success` via `trackEvent`, but it's **missing from the backend `_ALLOWED_EVENTS` allowlist** (`routers/analytics.py:19`) → guaranteed 400 (PostHog still gets it; only the Railway-log copy is rejected). One-line fix. NOTE: this fires once post-checkout, not "twice/page after auth" — that symptom may be separate; needs a logged-in repro.
4. [ ] **Webhook self-heal** — handle `customer.subscription.created`/`updated` so dashboard-created subs activate without sign-in. Confirmed not done: webhook handles `checkout.session.completed`/`subscription.deleted`/`payment_failed` only (`routers/checkout.py:180`).
5. [ ] **LinkedIn channel decision** — DM to Allie K. Miller (May 27) still unanswered; 0 referrals. Watch for reply; decide whether to keep posting.
6. [ ] **Ongoing distribution** — 4 replies/day target; reply threads into high-impression accounts are the proven reach driver. Monday pre-market = peak window.

**Tech debt / soon:**
- [ ] Submit to SaaSWorthy, Product Hunt, G2, Capterra, AlternativeTo.
- [ ] Expand sitemap to /privacy and /terms.
- [ ] Chart.js defensive fix: `responsive: true, maintainAspectRatio: false` + sized wrappers.
- [ ] `/test/run-alert-check` 403 with `DEV_SECRET` — reconcile deployed value vs `railway variables`. Non-blocking.
- [x] ~~PostHog internal-traffic filter leak~~ — fixed May 25. **Still open:** flip PostHog's "Enable filter on all new insights" ON; filter localhost.

---

## Current state — May 31, 2026

_Session history lives in `CHANGELOG.md` + git log; settled decisions in `DECISIONS_ARCHIVE.md`. This note keeps only the latest 1–2 sessions._

_**May 31 session (Sunday) — distribution-only: posted Day 17 X card; no code shipped, no revenue change ($0 MRR, 0 external paying).** **(1) X post (Day 17):** $HEI HEICO card — "exception flags fire in both directions" angle, continuing Friday's $BA "deviation from a company's own history" beat. Operating margin 25.5%, 3.8 SD ABOVE its own 8-qtr avg (positive-direction flag), highest in 3+ years; rev +25% YoY, NI $234M / EPS $1.66. Card built from scratch in dashboard palette (no template existed), rendered headless Chrome 1080×1350 @2x, mobile-legibility verified at 400px. PNG also at `~/Desktop/edgarwolf_HEI_card.png`. **(2) Data integrity:** SEC EDGAR XBRL ground-truth cross-checks all PASSED — HEICO OM (25.47% = OI $350.4M / rev $1.376B), Lowe's GM (32.68%), and HEICO/Lowe's/Snowflake NI+EPS all matched EdgarWolf exactly. (Self-correction: I briefly suspected a Target net-income bug — it was MY misread of the prior-year comparative; EW reports Target NI $781M / EPS $1.71 correctly. NO bug. Disregard any spawned "Target bug" task.) **(3) Built but not yet posted:** $LOW Lowe's card (`/tmp/card_low.html`) — queued for Monday pre-market. **(4) PostHog May 30–31:** 0 engaged external sessions; May 30 = 4 homepage-only `$direct` hits, ≥2 from GCP crawler IP. **(5) Prod health:** v1.7.4 online, Railway healthy, tree clean/pushed (last code commit d21df56, May 29). **(6) Doc note:** AZO Spotlight already posted days ago (on Q2 FY26 data); AZO Q3 still not ingested as of May 31 (latest period = Feb 14 2026 / Q2) — no pending AZO work, removed from next-session list._

_**May 29 session (Friday) — posted Day 16 $BA X card + fixed 2 analytics tracking bugs (commit d21df56, no version bump); no revenue change. (a) `company_view` was missing from the search path (only fired on direct `?cik=` loads) — now fires in both. (b) `history.pushState` moved before `renderDashboard` so in-render events log the company URL, not homepage. PostHog: 1 engaged session (Google → TANGER INC → upgrade_modal_open → no convert).**_
