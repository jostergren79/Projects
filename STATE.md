# EdgarWolf — Live State

**Updated every session.** Stable context, rules, and the start/end session sequences are in **`CLAUDE.md`** (auto-loaded). This file holds only the volatile state: metrics, active priorities, the next-session plan, and a current-state note.

Current version: **v1.7.5** (2026-06-02) — conversion-focused frontend release: digest banner now surfaces after a company loads (new copy + "Send me Sunday's" CTA), landing subhead rewritten to the anomaly value prop, and the upgrade modal names the viewed company. (v1.7.3 = XBRL `(start_date, fp)` differencing fix + dynamic per-CIK OG images.) Release history in `CHANGELOG.md`.

---

## Current metrics

_Refreshed Jun 5. **Numbers below are external-only** — Jason's IPs filtered. Per-device `?internal=1` opt-out is the durable filter. Two $0 comp Pro+ accounts (`cus_UUN2ChsZV2aaRC`, Sam `cus_UZVNfwfk7hlPBv`); Stripe confirms $0 real revenue._

| Metric | Value | Updated |
|--------|-------|---------|
| MRR | $0 | Jun 5, 2026 |
| Paying users | 0 (+2 comp Pro+: `cus_UUN2ChsZV2aaRC` + Sam `cus_UZVNfwfk7hlPBv` — both $0 MRR) | Jun 5, 2026 |
| Free signups (digest) | 0 external | Jun 5, 2026 |
| External engaged visitors | Jun 3: 8 external events (1 company_view, 1 digest_banner_view, 3 page_view). Jun 4–5: 0 new. | Jun 5, 2026 |
| Real external conversions | 0 | Jun 5, 2026 |
| Countries | 2: US, France | Jun 5, 2026 |
| Top referrers (7d, external) | google, direct — t.co = 0 | Jun 5, 2026 |
| X followers / combined 2nd-degree reach | 4 / ~10.3k combined (Ann Barbour 6.8k, Ashton ~2.3k) | May 21, 2026 |
| Last X post | Day 20 — $VSCO Q2 2026 turnaround card; revenue +15.3% YoY (3 SD above avg), gross margin 37.5% 8-qtr high, $48M NI after 4 straight loss quarters, FSS 82/100, 8-K 3 days before 10-Q; posted Jun 10 | Jun 10, 2026 |
| Daily post automation | Cowork runs at 8 AM daily — generates post copy + data card automatically | Jun 10, 2026 |

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

1. [x] **Stripe Dashboard action** — `customer.subscription.created` + `customer.subscription.updated` added to webhook endpoint Jun 10, 2026. All 5 events now configured: checkout.session.completed, customer.subscription.created/deleted/updated, invoice.payment_failed.
2. [ ] **Watch VSCO + GME engagement** — monitor replies/impressions; reply with filing data to anyone engaging.
3. [ ] **Watch conversion metrics** — check if funnel looks healthier post-fixes. Baseline: 1 upgrade-modal open / 0 convert.
4. [ ] **Ongoing distribution** — reply threads into high-impression accounts. Daily post + card now automated via Cowork (8 AM).

**Tech debt / soon:**
- [ ] Submit to SaaSWorthy, Product Hunt, G2, Capterra, AlternativeTo. **AlternativeTo: account created Jun 10; eligible to submit Jun 17, 2026.**
- [x] Expand sitemap to /privacy and /terms. Done Jun 10, 2026.
- [ ] Chart.js defensive fix: `responsive: true, maintainAspectRatio: false` + sized wrappers.
- [ ] `/test/run-alert-check` 403 with `DEV_SECRET` — reconcile deployed value vs `railway variables`. Non-blocking.
- [x] ~~PostHog internal-traffic filter leak~~ — fixed May 25. "Enable filter on all new insights" confirmed ON Jun 10. Note: IP address filter in PostHog is set as inclusive (shows only matching IP) rather than exclusive — low priority since device-flag (`?internal=1`) is the primary filter.

---

## Current state — Jun 10, 2026

_Session history lives in `CHANGELOG.md` + git log; settled decisions in `DECISIONS_ARCHIVE.md`. This note keeps only the latest 1–2 sessions._

_**Jun 10 session (Tuesday) — config + cleanup, no code shipped. $0 MRR, 0 paying. (1) X post (Day 20):** $VSCO Q2 2026 turnaround card posted — revenue +15.3% YoY (3 SD above avg), gross margin 37.5% (8-qtr high), $48M NI after 4 straight loss quarters, FSS 82/100, 8-K filed 3 days before 10-Q. CIK 0001856437. **(2) Stripe webhook:** `customer.subscription.created` + `customer.subscription.updated` added to Stripe Dashboard endpoint config — now fully wired. **(3) PostHog filter fixed:** removed inclusive IP address chip from internal-user filter; "Enable filter on all new insights" confirmed ON; dashboards now show real external traffic. 2 unique external visitors in last 7 days (Jun 3 + Jun 6). **(4) Sitemap:** /privacy.html + /terms.html added. **(5) AlternativeTo:** account created Jun 10; eligible to submit Jun 17. **(6) Cowork:** 8 AM daily automation live — generates post copy + data card automatically._

_**Jun 5 session (Friday) — start-only, no code shipped, no posts.** PostHog Jun 3: 8 external events. Prod v1.7.5 healthy. Stripe webhook config was still open._
