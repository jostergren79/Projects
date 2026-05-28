# EdgarWolf — Live State

**Updated every session.** Stable context, rules, and the start/end session sequences are in **`CLAUDE.md`** (auto-loaded). This file holds only the volatile state: metrics, active priorities, the next-session plan, and a current-state note.

Current version: **v1.7.4** (2026-05-28) — conversion-focused frontend release: digest banner now surfaces after a company loads (new copy + "Send me Sunday's" CTA), landing subhead rewritten to the anomaly value prop, and the upgrade modal names the viewed company. (v1.7.3 = XBRL `(start_date, fp)` differencing fix + dynamic per-CIK OG images.) Release history in `CHANGELOG.md`.

---

## Current metrics

_Refreshed May 28. **Numbers below are external-only** — Jason's 4 own IPs (`71.34.14.90`, `97.116.24.43`, + 2 IPv6) are filtered out. Note `71.34.14.90` is the **home-network public IP shared by ≥2 people** (Jason + Sam, via NAT). As of May 25 the durable filter is the per-device `?internal=1` opt-out; IP filter is now legacy/historical fallback. Two $0 comp Pro+ accounts (`cus_UUN2ChsZV2aaRC`, Sam `cus_UZVNfwfk7hlPBv`); Stripe confirms $0 real revenue._

| Metric | Value | Updated |
|--------|-------|---------|
| MRR | $0 | May 28, 2026 |
| Paying users | 0 (+2 comp Pro+: `cus_UUN2ChsZV2aaRC` + Sam `cus_UZVNfwfk7hlPBv` — both $0 MRR) | May 28, 2026 |
| Free signups (digest) | 0 external | May 28, 2026 |
| External engaged visitors (24h) | Quiet — 5 external pageviews May 26–28 (Google + direct). 0 t.co referrals; Day 14 ($TTWO) and Day 15 ($AZO) posts confirmed 0 site click-throughs. One direct `?cik=0000789019` (MSFT) visit May 26 — source unknown. 0 upgrade modals, 0 conversions. | May 28, 2026 |
| Real external conversions | 0 | May 28, 2026 |
| Countries | 2: US, France | May 28, 2026 |
| Top referrers (7d, external) | direct, google — **t.co = 0 this week, LinkedIn = 0** | May 28, 2026 |
| X followers / combined 2nd-degree reach | 4 / ~10.3k combined (Ann Barbour 6.8k, Ashton ~2.3k) | May 21, 2026 |
| Last X post | Day 15 — $AZO op-margin compression card (revenue +8% YoY, op income fell, 21%→16% margin over 2 yrs); also replied $NOW thread (34K-impression parent, +22% rev YoY, 75% GM, stress quiet) | May 27, 2026 |
| Last LinkedIn post | Build-in-public retrospective (15 days / 17 releases) + DM sent to Allie K. Miller | May 27, 2026 |

---

## Active priorities

_Replace completed items each session. Keep this list short._

**✅ Shipped (May 28) — v1.7.4 (conversion-focused, frontend-only):**
- [x] **Digest banner gated to post-company-view** — shows after a dashboard loads (not cold landing); copy → "Every Sunday: the 10 most-flagged S&P 100 filings…", CTA "Subscribe" → "Send me Sunday's". `digest_banner_view` now fires deeper in the funnel — track view→signup *rate*, not raw views.
- [x] **Landing subhead → anomaly value prop** — "…See where its margins, revenue, and filing behavior break from the norm." Matches the X data-card promise. Chip lead-in → "Try a live example:".
- [x] **Upgrade modal context-aware** — subhead names the viewed company ("…for {company}. Cancel anytime."); `upgrade_modal_open` tagged with `company`. Trailing-period strip fixes the "Apple Inc.." double-period.
- [x] Verified on real devices (iPhone 14 Pro Max 430px + iPhone SE 375px): no horizontal overflow; banner, landing, modal all clean.

**▶ NEXT SESSION:**

1. [ ] **$AZO Q3 Spotlight** — Q3 XBRL **not yet ingested as of May 28** (latest period still Feb 2026 / Q2). Day 15 post used Q2 data (21%→16% op margin compression). Watch for Q3 ingestion; post a fresh Spotlight once the data lands.
2. [ ] **Methodology-post idea** — "the model stayed quiet on UNH, Boeing, Intel" (fresh data, 0 flags despite headlines). Flag deviations, not headlines — strong differentiation angle.
3. [ ] **Watch v1.7.4 conversion metrics** — did the gated digest banner lift signups (view→signup *rate*)? Did the company-named upgrade modal lift `upgrade_modal_open`→checkout? Baseline to beat: 22 banner views / 0 signups, 1 modal open / 0 convert.
4. [ ] **Confirm device-flagging** — did Jason + Sam visit `?internal=1` on every device/browser? Still unconfirmed. Household cellular/IPv6 leaks until done.
5. [ ] **LinkedIn channel decision** — DM sent to Allie K. Miller (May 27); still 0 referrals from the May 25 build post. Watch for reply + referrals; decide whether to keep posting.
6. [ ] **Webhook self-heal:** handle `customer.subscription.created`/`updated` so dashboard-created subs self-heal without requiring sign-in.
7. [ ] Trace `POST /analytics/event 400` (fires twice/page after auth) — `routers/analytics.py` validation.
8. [ ] **Ongoing distribution:** 4 replies/day target. $AZO Day 15 card posted (May 27). Reply threads (high-impression fintwit/investing accounts) are the proven reach driver.

**Tech debt / soon:**
- [ ] Submit to SaaSWorthy, Product Hunt, G2, Capterra, AlternativeTo.
- [ ] Expand sitemap to /privacy and /terms.
- [ ] Chart.js defensive fix: `responsive: true, maintainAspectRatio: false` + sized wrappers.
- [ ] `/test/run-alert-check` 403 with `DEV_SECRET` — reconcile deployed value vs `railway variables`. Non-blocking.
- [x] ~~PostHog internal-traffic filter leak~~ — fixed May 25. **Still open:** flip PostHog's "Enable filter on all new insights" ON; filter localhost.

---

## Current state — May 28, 2026

_Session history lives in `CHANGELOG.md` + git log; settled decisions in `DECISIONS_ARCHIVE.md`. This note keeps only the latest 1–2 sessions._

_**May 28 session — shipped v1.7.4 (conversion-focused frontend release) + doc cleanup; no revenue change ($0 MRR, 0 external paying).** **(1) Conversion levers (v1.7.4, `edgar-frontend/edgar.html` only):** PostHog showed traffic arriving (mostly Google) but not converting — 22 digest-banner views / 0 signups, 1 upgrade-modal open that bailed. Fixed three leak points: (a) digest banner now surfaces AFTER a company dashboard loads (gated on `currentCompany`, re-invoked from `renderDashboard`), not on cold landing; copy → "Every Sunday: the 10 most-flagged S&P 100 filings…", CTA "Subscribe" → "Send me Sunday's"; (b) landing subhead → anomaly value prop matching the X cards; (c) upgrade-modal subhead names the viewed company, `upgrade_modal_open` tagged with `company`. **(2) Verification:** JS `node --check`; headless + real-device (iPhone 14 Pro Max 430px & iPhone SE 375px via DevTools device mode) — no horizontal overflow, all three surfaces clean. The "clipping" chased in headless was a layout-viewport-vs-canvas artifact (`innerWidth` pinned ~500 regardless of `--window-size`), proven by in-page `scrollWidth == innerWidth`. Caught + fixed an em-dash in banner copy (house style) and a double-period bug ("Apple Inc.." → trailing-period strip). **(3) Doc cleanup (committed earlier this session, 75d03fe):** CLAUDE.md trigger phrases (`claude start` / `claude end session`) + hardened session sequences; DECISIONS_ARCHIVE 3 stale sections (Stripe auth model, OG image, Postman count); METHODOLOGY XBRL §2 pairing. **(4) Health/PostHog:** prod healthy; May 28 quiet — 0 conversions, 0 signups, 0 upgrade modals. **(5) $AZO Q3** not yet ingested (latest Feb 2026 / Q2); **$EL** confirmed XBRL-artifact, closed. **(6) LinkedIn:** 0 reply from Allie K. Miller, 0 referrals from the May 25 build post._

_**May 27 session — shipped v1.7.3 (XBRL fix + dynamic OG images); distribution work; no revenue change ($0 MRR, 0 external paying). XBRL `fy_fp_map` re-keyed by `(start_date, fp)`. Dynamic OG images at `/og/{cik}.png`. Day 15 $AZO card posted. DM sent to Allie K. Miller (LinkedIn). X analytics: $MSFT post 1.4K impressions = top performer; replies into large threads = growth lever.**_
