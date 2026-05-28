# EdgarWolf — Live State

**Updated every session.** Stable context, rules, and the start/end session sequences are in **`CLAUDE.md`** (auto-loaded). This file holds only the volatile state: metrics, active priorities, the next-session plan, and a current-state note.

Current version: **v1.7.3** (2026-05-27) — XBRL cumulative-to-quarter differencing fix (`fy_fp_map` keyed by `(start_date, fp)`) + dynamic per-CIK OG images (`GET /og/{cik}.png`). (v1.7.2 = 60s shared Stripe re-verify cache across `/auth/whoami` + `/watchlist` + the per-device `?internal=1` analytics guard.) Release history in `CHANGELOG.md`.

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

**✅ Shipped (May 27) — v1.7.3:**
- [x] **XBRL cumulative-to-quarter differencing fix** — `fy_fp_map` now keyed by `(start_date, fp)` instead of `(fy, fp)`. Fixes bad per-quarter values on any filer (e.g. Micron) where EDGAR re-tags prior-year comparative periods with the current filing's `fy` label. 7/7 tests green.
- [x] **Dynamic OG images per CIK** — `GET /og/{cik}.png` generates branded 1200×630 PNG (company name, ticker, EdgarWolf wordmark) using Pillow; cached in memory. `root()` / `edgar_page()` now inject dynamic og/twitter meta tags when `?cik=` is present. Validated live on prod — ServiceNow shows correctly in X composer.

**▶ NEXT SESSION:**

1. [ ] **$AZO Q3 Spotlight** — Q3 XBRL **not yet ingested as of May 28** (latest period still Feb 2026 / Q2). Day 15 post used Q2 data (21%→16% op margin compression). Watch for Q3 ingestion; post a fresh Spotlight once the data lands.
2. [ ] **Methodology-post idea** — "the model stayed quiet on UNH, Boeing, Intel" (fresh data, 0 flags despite headlines). Flag deviations, not headlines — strong differentiation angle.
3. [x] ~~**Sanity-check $EL** (Estée Lauder)~~ — ✅ **Done May 28.** Confirmed: 37.5% figure was XBRL artifact, fixed by v1.7.3. Actual margins are 10–12% op, 54–56% gross, trending down. Not a post candidate.
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

_**May 28 session — health check + start sequence only; no code, no posts. (1) Prod:** v1.7.3 live, cache healthy. **(2) PostHog:** 5 external pageviews May 26–28 (Google + direct only). 0 t.co referrals confirmed — Day 14 ($TTWO, GTA VI hook) and Day 15 ($AZO, margin compression) both generated 0 site click-throughs. One direct ?cik=0000789019 (MSFT) visit May 26 — source unknown. 0 upgrade modals, 0 conversions, $0 MRR. **(3) $AZO Q3:** latest EDGAR period still Feb 2026 (Q2); Q3 10-Q not yet ingested. Card on hold. **(4) $EL sanity check:** confirmed closed — 37.5% op margin was XBRL artifact fixed by v1.7.3; actual is 10–12% op / 54–56% gross, trending down, not a post candidate. **(5) LinkedIn:** 0 reply from Allie K. Miller yet; 0 referrals from May 25 build post. **(6) CLAUDE.md + DECISIONS_ARCHIVE.md:** uncommitted changes from May 27 session still pending; Jason will commit from another session._

_**May 27 session — shipped v1.7.3 (XBRL fix + dynamic OG images); distribution work; no revenue change ($0 MRR, 0 external paying). XBRL `fy_fp_map` re-keyed by `(start_date, fp)`. Dynamic OG images at `/og/{cik}.png`. Day 15 $AZO card posted. DM sent to Allie K. Miller (LinkedIn). X analytics: $MSFT post 1.4K impressions = top performer; replies into large threads = growth lever.**_
