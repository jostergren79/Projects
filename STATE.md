# EdgarWolf — Live State

**Updated every session.** Stable context, rules, and the start/end session sequences are in **`CLAUDE.md`** (auto-loaded). This file holds only the volatile state: metrics, active priorities, the next-session plan, and a current-state note.

Current version: **v1.7.5** (2026-06-02) — conversion-focused frontend release: digest banner now surfaces after a company loads (new copy + "Send me Sunday's" CTA), landing subhead rewritten to the anomaly value prop, and the upgrade modal names the viewed company. (v1.7.3 = XBRL `(start_date, fp)` differencing fix + dynamic per-CIK OG images.) Release history in `CHANGELOG.md`.

---

## Current metrics

_Refreshed Jun 2. **Numbers below are external-only** — Jason's IPs filtered (added `97.116.28.254` as confirmed internal this session). Per-device `?internal=1` opt-out is the durable filter. Two $0 comp Pro+ accounts (`cus_UUN2ChsZV2aaRC`, Sam `cus_UZVNfwfk7hlPBv`); Stripe confirms $0 real revenue._

| Metric | Value | Updated |
|--------|-------|---------|
| MRR | $0 | Jun 2, 2026 |
| Paying users | 0 (+2 comp Pro+: `cus_UUN2ChsZV2aaRC` + Sam `cus_UZVNfwfk7hlPBv` — both $0 MRR) | Jun 2, 2026 |
| Free signups (digest) | 0 external | Jun 2, 2026 |
| External engaged visitors | 0 external events Jun 2. `97.116.28.254` (LinkedIn referrer → Apple CIK) confirmed internal this session. | Jun 2, 2026 |
| Real external conversions | 0 | Jun 2, 2026 |
| Countries | 2: US, France | Jun 2, 2026 |
| Top referrers (7d, external) | google, direct — t.co = 0 | Jun 2, 2026 |
| X followers / combined 2nd-degree reach | 4 / ~10.3k combined (Ann Barbour 6.8k, Ashton ~2.3k) | May 21, 2026 |
| Last X post | Day 19 — $GME Q1 FY2026 earnings card; eBay derivatives angle ("proposed acquisition of eBay" from risk factors); posted Jun 2 | Jun 2, 2026 |
| Last LinkedIn post | Build-in-public retrospective (15 days / 17 releases) + DM sent to Allie K. Miller | May 27, 2026 |

---

## Active priorities

_Replace completed items each session. Keep this list short._

**✅ Distribution (Jun 1):**
- [x] Day 18 — $LOW Lowe's card posted (Mon pre-market): gross margin 32.7%, 3.0 SD below its own 8-qtr avg; divergence angle ("sales accelerating, margin compressing"); rev $23.1B +10% YoY. Card pre-built + SEC-verified from prior session.

**✅ Code (Jun 2) — v1.7.5:**
- [x] `subscription_success` added to `_ALLOWED_EVENTS` — 400s stop, Railway logs now capture it
- [x] Webhook self-heal — `_sync_subscription()` helper added; `customer.subscription.created`/`updated` now upsert tier to DB
- [x] Day 19 — $GME Q1 FY2026 card posted: record $389.6M NI, eBay derivative play ($268.4M unrealized gain, $1B collateral, "proposed acquisition" from risk factors)

**▶ NEXT SESSION:**

1. [ ] **Stripe Dashboard action** — add `customer.subscription.created` + `customer.subscription.updated` to webhook endpoint event list (code shipped, Stripe won't send them until configured).
2. [ ] **Watch GME engagement** — monitor replies/impressions; reply with filing data to anyone engaging. eBay angle may drive thread activity.
3. [ ] **Watch conversion metrics** — check if funnel looks healthier post-fixes. Baseline: 1 upgrade-modal open / 0 convert.
4. [ ] **Ongoing distribution** — next X post; reply threads into high-impression accounts.
5. [ ] **LinkedIn — revisit if Allie K. Miller replies** (DM sent May 27; parked until then).

**Tech debt / soon:**
- [ ] Submit to SaaSWorthy, Product Hunt, G2, Capterra, AlternativeTo.
- [ ] Expand sitemap to /privacy and /terms.
- [ ] Chart.js defensive fix: `responsive: true, maintainAspectRatio: false` + sized wrappers.
- [ ] `/test/run-alert-check` 403 with `DEV_SECRET` — reconcile deployed value vs `railway variables`. Non-blocking.
- [x] ~~PostHog internal-traffic filter leak~~ — fixed May 25. **Still open:** flip PostHog's "Enable filter on all new insights" ON; filter localhost.

---

## Current state — Jun 2, 2026

_Session history lives in `CHANGELOG.md` + git log; settled decisions in `DECISIONS_ARCHIVE.md`. This note keeps only the latest 1–2 sessions._

_**Jun 2 session (Tuesday) — code + distribution: shipped v1.7.5 (two backend fixes), posted Day 19 $GME card. $0 MRR, 0 external paying.** **(1) Code shipped:** `subscription_success` added to analytics allowlist (was 400ing on Railway); webhook self-heal added for `customer.subscription.created`/`updated` via `_sync_subscription()` — Stripe Dashboard still needs event types added. **(2) X post (Day 19):** $GME Q1 FY2026 earnings card — biggest post to date. Record $389.6M net income (highest quarter in company history); $268.4M from unrealized eBay derivatives; $1B collateral pledged; risk factors disclose "proposed acquisition of eBay Inc." PNG at `~/Desktop/edgarwolf_GME_card.png`, card HTML at `cards/gme_q1fy26.html`. **(3) PostHog Jun 2:** 0 external events. `97.116.28.254` (LinkedIn referrer → Apple CIK) confirmed as Jason's internal IP — added to known list. **(4) Prod health:** v1.7.5 deployed, Railway healthy._

_**Jun 1 session (Monday) — distribution-only: posted Day 18 $LOW Lowe's card; no code shipped.** Gross margin 32.7%, 3.0 SD below 8-qtr avg; rev $23.1B +10% YoY. PNG at `~/Desktop/edgarwolf_LOW_card.png`._
