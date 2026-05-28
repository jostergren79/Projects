# EdgarWolf — Live State

**Updated every session.** Stable context, rules, and the start/end session sequences are in **`CLAUDE.md`** (auto-loaded). This file holds only the volatile state: metrics, active priorities, the next-session plan, and a current-state note.

Current version: **v1.7.3** (2026-05-27) — 60s shared Stripe re-verify cache across `/auth/whoami` + `/watchlist`; also formally releases the per-device `?internal=1` analytics guard (deployed 2026-05-25). Release history in `CHANGELOG.md`.

---

## Current metrics

_Refreshed May 27. **Numbers below are external-only** — Jason's 4 own IPs (`71.34.14.90`, `97.116.24.43`, + 2 IPv6) are filtered out. Note `71.34.14.90` is the **home-network public IP shared by ≥2 people** (Jason + Sam, via NAT). As of May 25 the durable filter is the per-device `?internal=1` opt-out; IP filter is now legacy/historical fallback. Two $0 comp Pro+ accounts (`cus_UUN2ChsZV2aaRC`, Sam `cus_UZVNfwfk7hlPBv`); Stripe confirms $0 real revenue._

| Metric | Value | Updated |
|--------|-------|---------|
| MRR | $0 | May 27, 2026 |
| Paying users | 0 (+2 comp Pro+: `cus_UUN2ChsZV2aaRC` + Sam `cus_UZVNfwfk7hlPBv` — both $0 MRR) | May 27, 2026 |
| Free signups (digest) | 0 external | May 27, 2026 |
| External engaged visitors (24h) | Quiet — no signups, no upgrades. Multiple /terms reads from different IPs (due diligence or bots). Pro+ alert cron running clean hourly (3 watchlist entries). | May 27, 2026 |
| Real external conversions | 0 | May 27, 2026 |
| Countries | 2: US, France | May 27, 2026 |
| Top referrers (7d, external) | direct, google, t.co (X) 3; **LinkedIn still = 0** | May 27, 2026 |
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

1. [ ] **Re-check $AZO** when Q3 10-Q ingests — Q3 results announced May 26 (stock −10%); Q2 filing already showed 21%→16% op margin compression. Post a data-forward Spotlight once the Q3 XBRL lands.
2. [ ] **Methodology-post idea** — "the model stayed quiet on UNH, Boeing, Intel" (fresh data, 0 flags despite headlines). Flag deviations, not headlines — strong differentiation angle.
3. [ ] **Sanity-check $EL** (Estée Lauder) — 37.5% op margin looks artifactual from prior session. Verify before using in a post.
4. [ ] **Confirm device-flagging** — did Jason + Sam visit `?internal=1` on every device/browser? Still unconfirmed. Household cellular/IPv6 leaks until done.
5. [ ] **LinkedIn channel decision** — DM sent to Allie K. Miller (May 27); still 0 referrals from the May 25 build post. Watch for reply + referrals; decide whether to keep posting.
6. [ ] **Webhook self-heal:** handle `customer.subscription.created`/`updated` so dashboard-created subs self-heal without requiring sign-in.
7. [ ] Trace `POST /analytics/event 400` (fires twice/page after auth) — `routers/analytics.py` validation.
8. [ ] **Ongoing distribution:** 4 replies/day target. $AZO card ready to post. Reply threads (high-impression fintwit/investing accounts) are the proven reach driver.

**Tech debt / soon:**
- [ ] Submit to SaaSWorthy, Product Hunt, G2, Capterra, AlternativeTo.
- [ ] Expand sitemap to /privacy and /terms.
- [ ] Chart.js defensive fix: `responsive: true, maintainAspectRatio: false` + sized wrappers.
- [ ] `/test/run-alert-check` 403 with `DEV_SECRET` — reconcile deployed value vs `railway variables`. Non-blocking.
- [x] ~~PostHog internal-traffic filter leak~~ — fixed May 25. **Still open:** flip PostHog's "Enable filter on all new insights" ON; filter localhost.

---

## Current state — May 27, 2026

_Session history lives in `CHANGELOG.md` + git log; settled decisions in `DECISIONS_ARCHIVE.md`. This note keeps only the latest 1–2 sessions._

_**May 27 session — shipped v1.7.3 (XBRL fix + dynamic OG images); distribution work; no revenue change ($0 MRR, 0 external paying).** **(1) 24h log check:** quiet overnight — no signups, no upgrades. Multiple /terms reads from different external IPs (due diligence or bots, no conversion). Pro+ cron running clean. **(2) XBRL cumulative-to-quarter fix:** `fy_fp_map` was keyed by `(fy, fp)` — EDGAR re-uses these labels for prior-year comparative periods in later 10-Q filings, causing the wrong cumulative base to be used for differencing (Micron showed ~$3.3B/qtr instead of ~$2.8B). Fixed by keying on `(start_date, fp)` — YTD rows within the same fiscal year always share the same FY start date, so pairing is unambiguous. 7/7 tests green, Apple sanity-checked. **(3) Dynamic OG images:** Pillow-based 1200×630 PNG per CIK, served at `/og/{cik}.png`, cached in memory. `root()` / `edgar_page()` inject dynamic og/twitter meta when `?cik=` present. nixpacks change caused first build failure (wrong phase format); reverted to font fallback only — `load_default(size=)` works fine on Railway. Validated live: $NOW shows correctly in X composer. **(4) Distribution:** Day 15 $AZO card built (op margin 21%→16% over 2 years, revenue +8% but op income fell — stock −10% on Q3 miss). Replied $NOW thread (34K-impression parent, +22% YoY revenue, 75% GM, stress quiet). DM sent to Allie K. Miller on LinkedIn (builder story + Claude angle). X analytics review: $MSFT post 1.4K impressions = top performer; reply-into-large-threads is the growth lever; posts without external links outperform 14:1 on engagement rate. **(5) Version:** bumped to v1.7.3; committed + tagged; Railway auto-deploys._

_**May 26 PM session (distribution) — shipped Day 14 X post + 3 replies; no code. $TTWO Contrarian/Green card (GTA VI delay hook, net income −$125M→+$389M YoY). 3 replies on $NVDA + $TTWO threads. Found $MU XBRL bug (fixed May 27). Day 14 post ~11 likes, 0 click-throughs at 2h.**_
