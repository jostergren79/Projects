# EdgarWolf — Claude Context Doc

**Current version: v1.6.0** (2026-05-19) — see `CHANGELOG.md` for full release history.

Paste this file at the start of every Claude conversation to restore full context.
Update metrics, version, and priorities at the end of every relevant session.

---

## 1. Product & Stack

**Product:** EdgarWolf (www.edgarwolf.com)
SEC EDGAR financial data and anomaly detection tool. Flags statistical deviations in margins, revenue growth, and filing behavior for any US public company.

**Key features:**
- Signal board (Strengthening / Weakening — on-demand, 5–25 companies per column)
- Z-score exception flags (gross margin, operating margin, net margin, revenue YoY)
- Filing Stress Score (0–100 composite)
- Watchlist — server-side for Pro/Pro+ (SQLite, keyed by Stripe customer_id), localStorage for Standard
- Peer comparison, CSV/JSON export, Metric Trust panel, natural language summary
- Analytics via PostHog (US Cloud, project 424339) + Railway logs. Session recordings, heatmaps on.
- Stripe: Pro $19.00/mo, Pro+ $99/mo (LIVE). Customer Portal live.
- Email alerts (Pro+) — code-complete and scheduled (hourly M–F 8 AM–6 PM ET, fires on new 10-Q/10-K/8-K + anomaly signal). **Never actually exercised in prod** — no Pro+ user has had a watchlist until May 20. See §6 validation task.
- Free-tier digest capture — email + welcome via Resend. Weekly digest send job not yet built.

**Stack:** FastAPI (Python) + static HTML/JS, Railway service
**Live URL:** https://www.edgarwolf.com
**Repo:** github.com/jostergren79/Projects

**Key files:**
- `edgar-api/main.py` — FastAPI app
- `edgar-api/cache.py` — SQLite cache, watchlists, users
- `edgar-api/routers/financial_metrics.py` — XBRL, YTD normalization, margins
- `edgar-api/routers/dashboard.py` — aggregated endpoint
- `edgar-api/routers/checkout.py` — Stripe
- `edgar-frontend/edgar.html` — entire frontend
- `METHODOLOGY.md` — spec for all derived metrics and scoring

---

## 2. Founder Situation

**Name:** Jason Ostergren | Minneapolis, MN
**Income target:** $8k/month to replace current salary
**Decision rule (May 15, 2026):** Take the full-time job no matter which company offers first. EdgarWolf is parallel side-income. Re-evaluate full-time only when EdgarWolf reliably exceeds $8k/month for several consecutive months.
**Backup:** Job offer from Post Consumer Brands (in final stages)

**Background:** IT systems thinker, NOT a finance professional. 20+ years enterprise IT, Sr BSA, SQL/Snowflake, SAFe PO, Full Stack Web Dev cert (U of Minnesota). Built EdgarWolf to scratch his own itch reading SEC filings as an outsider. This "outsider builder" angle is the honest founder story — never imply years of financial analysis experience.

---

## 3. Pricing Model

| Tier | Price | Features |
|------|-------|----------|
| Standard | $0 | Signal board, company search, KPI grid, narrative summary, 8-quarter charts, data table. Unlimited lookups. |
| Pro | $19.00/mo | Everything free + Exception Flags, Filing Stress Score, Filing Signals, peer comparison, segment breakdown, source filing, watchlist (server-side), CSV/JSON export. |
| Pro+ | $99/mo | Everything Pro + email alerts (code-complete, prod-untested — see §6). |

Feature gating LIVE as of May 10, 2026. Differentiation is feature depth only, not access.

---

## 4. Current Metrics

_Update these at the end of every session._

| Metric | Value | Updated |
|--------|-------|---------|
| MRR | $0 | May 20, 2026 |
| Paying users | 0 | May 20, 2026 |
| Free signups | 0 | May 20, 2026 |
| X-attributed visits (PostHog, week 1) | 25 distinct visitors | May 21, 2026 |
| Countries (rolling 500-event window) | 4: US, Germany, France, Philippines | May 21, 2026 |
| First upgrade modal open | 1 (Minneapolis, iPhone, $AAPL page, May 17 8:12 AM CT) | May 18, 2026 |
| X followers / combined 2nd-degree reach | 4 followers / ~10.3k combined (Ann Barbour 6.8k, Ashton ~2.3k, others ~1.2k) | May 21, 2026 |
| Day 7 Builder Update post on X | posted May 19 evening | May 20, 2026 |
| Day 8 Methodology post on X | posted May 20 morning ($CAG Q3 FY26, 4 flags, 2-yr op margin trajectory) | May 20, 2026 |
| Day 9 Retrospective post on X | posted May 21 afternoon (3 lessons: "live" ≠ "tested", silent failures, show your work) | May 21, 2026 |

---

## 5. Marketing Assets

**Filed data examples:**
- **$CAG:** All 3 margins 3+ SD below avg (HIGH). Revenue $3.2B→$2.4B. FSS 70/100 ELEVATED.
- **$GIS:** FSS 100/100. Filing velocity ELEVATED. Revenue YoY -23%, 3.3 SD below avg.
- **$UNH (May 18):** FSS 92/100 ELEVATED. 8-K filed 6 days before 10-Q. CIK 0000731766.
- **$JACK:** FSS 92/100. Net income -$25.9M, EPS -$1.35, Revenue -12.4% YoY.
- **$SOFI (May 18):** Contrarian/Green. Net income trajectory: -$267M (Q3 2023) → +$71M → +$202M → +$167M (Q1 2026). Four straight profitable quarters. XBRL revenue concepts unreliable for fintechs/banks — use bottom-line figures only.

**Channels:**
- **X (PRIMARY):** Personal account. 6 rotating themes: Company Spotlight, Methodology, Sector Sweep, Contrarian/Green, Builder Update, Retrospective. **Day 7 next: Builder Update.** 4 replies/day target. Monday pre-market = peak window. CIK-direct URL on every company-specific post.
- **StockTwits:** LIVE as of May 18. First post: $UNH Bearish. Sentiment tag required. Same data-forward format as X.
- **r/SecurityAnalysis:** Post drafted, waiting on mod approval (requested May 10).
- **Finance Substack writers:** Not started — free Pro access in exchange for mention.
- **Crypto friends:** Not started — free beta invites pending.

**Key FinTwit accounts (engaged May 17 — do NOT pitch, stay in threads with filing data):**
@Ashton_1nvests (33.2K), @JonahLupton (552K hedge fund CEO), @MikeSchiemer (195.5K)

**Google:** Search Console verified. Sitemap live (May 13). JSON-LD deployed (May 17) — Google AI Overview now surfaces EdgarWolf as primary direct link with OG thumbnail.

---

## 6. Active Priorities

_Replace completed items each session. Keep this list short._

**v1.6.0 deploy — CLOSED OUT May 21:**
- [x] **Deploy live.** v1.6.0 confirmed via `/openapi.json` on May 20 afternoon. Railway queue cleared.
- [x] **Smoke test (automated items):** `/health` ok + cache healthy ✅. `/auth/whoami` without cookie → `{"tier":"standard","label":"Standard"}` ✅. `/auth/request` with unknown email → `{"ok":true}` ✅. All 4 new auth endpoints present; all 3 deprecated `/subscription/*` endpoints removed ✅.
- [x] **Magic-link round-trip — VERIFIED May 21.** New Resend key was Active. `POST /auth/request` for jason.ostergren79@gmail.com → Stripe customer lookup 200 → active sub on `cus_UUN2ChsZV2aaRC` 200 → `EVENT magic_link_sent email=j***@gmail.com`. Jason clicked link in inbox → `/auth/verify` returned 303 to `/?signed_in=1` with `ew_session` cookie set (HttpOnly, Secure, SameSite=Lax, 30-day Max-Age). `EVENT auth_verified customer_id=cus_UUN2ChsZV2aaRC` fired. Curl with cookie jar: `/auth/whoami` → `{"tier":"pro_plus","label":"Pro+"}`, `/watchlist` → `{"items":[],"count":0,"limit":50}`. Full auth chain working end-to-end.
- [x] Railway env vars set May 20: `SEC_REQUIRE_EXPLICIT_USER_AGENT=true`, `SEC_USER_AGENT=EdgarWolf/1.6.0 jason@edgarwolf.com`. SEC-backed endpoints returning real data.
- [ ] Postman collection regeneration — still references `/subscription/restore`, `/subscription/status*`, and `X-Customer-Id`. Separate commit, low priority.

**Open design question (parked May 21 — Claude's recommendation below, Jason to ratify next session):**
- **Q:** Is weekly `MAGIC_LINK_SECRET` rotation the right security control?
- **Claude's read:** Weekly rotation is security theater at current scale. It only defends against a leaked secret, and the secret never leaves Railway env vars. Recommended replacement controls, in order of value:
  1. **Server-side sessions table** keyed by `jti` so individual sessions are revocable on suspicion. Currently sessions are pure JWTs and unrevokable until expiry.
  2. **Sentry (or equivalent) hook on `auth.py` `RuntimeError`** — would have caught the silent Resend-key invalidity instantly. Generalize to all email failures.
  3. **Rate-limit anomaly log line** — distinct event when `/auth/request` returns rate-limited, so it's greppable/alertable.
- **Decision pending:** if Jason ratifies, drop weekly rotation as a calendar item; v1.6.1 becomes the sessions table + Sentry hook rather than dual-key fallback. Dual-key fallback drops to "only if you ever do rotate."

**v1.6.1 candidates (which one wins depends on the rotation decision above PLUS the new auth-verify upsert gap below):**
- [ ] **Auth-verify upserts user record (DISCOVERED MAY 21, REAL BUG).** Only the `checkout.session.completed` webhook writes to `users.tier`. Dashboard-created subs (comps, enterprise, manual) bypass it. `/auth/verify` validates against Stripe live but never persists. Result: `users.tier` can be silently stale for any non-checkout user — and the alert cron's `WHERE u.tier='pro_plus'` filter excludes them. Fix: have `/auth/verify` call `upsert_user(customer_id, email, tier_from_stripe)` after confirming the active sub. ~3 lines in `routers/auth_router.py`. Promotes to top of v1.6.1 because it directly blocks Pro+ alert validation.
- [ ] **Dual-key fallback** — `MAGIC_LINK_SECRET_PREVIOUS` in `verify_token` (~10 lines). Only useful if weekly rotation stays.
- [ ] **Sessions table + Sentry hook** — server-side session row keyed by jti for revocation; Sentry/email alert on `auth.py` errors. Preferred if rotation is dropped.

**New tech debt surfaced May 21 (from smoke-test log review):**
- [ ] `POST /analytics/event 400 Bad Request` fires twice per page load after auth. Frontend is sending a malformed event payload somewhere. Trace via browser network tab + `routers/analytics.py` validation.
- [ ] Every `/auth/whoami` and `/watchlist` call hits Stripe to re-verify the subscription (~140ms each). 2 Stripe API calls per page. Fine at 0 users; add a short-TTL cache (60s) keyed on `customer_id` before scale. Low priority until traffic shows up but worth a v1.7.x ticket.
- [ ] **Validate Pro+ email alert pipeline end-to-end** — code-complete and scheduled, but BLOCKED on the auth-verify upsert gap above. May 21 attempt: added $CAG and $AAPL to `cus_UUN2ChsZV2aaRC` watchlist before the 22:00 UTC cron. Cron fired and "executed successfully" per apscheduler, but `EVENT alert_check_start` never logged. Root cause traced to `get_all_pro_plus_watchlists()` returning empty because `users.tier` for the comp sub is stale (never upserted). Unblocks once v1.6.1 auth-verify upsert lands and Jason's user row is backfilled. Then test on the next M-F top-of-hour cron (next opportunity: Fri May 22 8:00 AM ET). Pro+ pricing depends on this working.

**Immediate:**
- [x] Day 9 X post — Retrospective shipped May 21. 3 lessons format: "live ≠ tested", silent failures, show-your-work. Honest 0% conversion framing, terse builder voice.
- [ ] 4 X replies/day — active threads, still-climbing
- [ ] Send beta invites to 2–3 crypto friends (free Pro access)
- [ ] Identify 10 finance Substack writers, send personal outreach
- [ ] Post on r/SecurityAnalysis when mod approval comes through
- [ ] Build weekly digest send job — Sunday cron, top 10 FSS companies, emails all `digest_subscribers`, unsubscribe link required
- [ ] Submit to SaaSWorthy, Product Hunt, G2, Capterra, AlternativeTo

**Soon:**
- [ ] Expand sitemap to /privacy and /terms
- [ ] Chart.js defensive fix: `responsive: true, maintainAspectRatio: false` + sized wrappers
- [ ] Filter localhost from PostHog dashboards (Settings → Project → Test accounts)

---

## 7. Key Decisions (Active — see DECISIONS_ARCHIVE.md for settled)

- **Take the job:** Accept full-time offer regardless of which company. EdgarWolf = side income until $8k/mo sustained for several months.
- **Distribution first:** Product is good enough. Distribution is the only job for the next 30 days. Manual everything until 10 paying users.
- **Founder angle:** Outsider IT builder, not finance professional. All copy reflects this.
- **X strategy:** Personal account, lead with filing data not product pitches. CIK-direct URLs on every company mention (`?cik=<CIK>`). Borrowed-audience via reply threads (10K–100K views, still climbing). Mid-traffic beats mega-threads for new accounts — exception: still-climbing mega-threads.
- **StockTwits:** Bearish/Bullish sentiment tag required. Same data-forward format as X replies.
- **$99/mo justified only with email alerts live.** Without alerts it's a $19 product.
- **Methodology doc rule:** Update METHODOLOGY.md before/alongside any new scoring, classification, polling, or trigger logic.
- **PostHog API:** Project 424339, US Cloud. Query programmatically at session start. Key events: `page_view`, `company_view`, `upgrade_modal_open`, `subscription_success`.
- **End of quarter filing season:** Late May/June = high-signal content. Prioritize posts around fresh 10-Q/10-K drops.
- **No version bump for metadata-only changes** (copy, analytics guards, JSON-LD).
- **Sector sweep thread format:** One company per tweet, hits multiple cashtag feeds simultaneously.
- **X writing style (per Jason May 21):** No em-dashes — readers spot them as LLM tells. Use periods, short sentences, or ` - ` (space-hyphen-space) where an em-dash would fit. Match the cadence of Jason's own posts: terse, declarative, data-forward. Lowercase casual where natural. Never tag/DM engagement targets, never ask for RTs.

---

## 8. Dev Workflow

```bash
cd edgar-api && source .venv/bin/activate && uvicorn main:app --reload --port 8000
```
Dev tier bypass: `?dev_tier=pro` (localhost only). Amber toggle button in header.

**End-of-session steps:**
1. Update `CHANGELOG.md`
2. Bump VERSION + footer + `main.py` version=
3. Update this file — metrics, priorities, decisions, session note
4. `git commit`, `git tag`, `git push --tags`
5. Railway auto-deploys on push to main

---

## 9. Technical State (v1.6.0, May 19)

Solid: proxy-aware rate limiting (200/min per real client IP, with memory cleanup), stale cache fallback, WAL thread-safety, CIK validation, HTTP 207 on partial failures, full browser security header set (CSP + X-Frame-Options + X-Content-Type-Options + Referrer-Policy + HSTS), Stripe webhook signature verification (hard-fails on missing secret), full HTML output encoding via escapeAttr() + html.escape() in alert emails, debug param gated to dev only, dev test endpoints gated by DEV_SECRET, health endpoint, entity type detection, robots.txt, PostHog localhost guard, `subscription_success` event once per customer.

**Auth (new in v1.6.0):** magic-link sign-in via Resend (HMAC-SHA256, 15-min TTL) → 30-day httpOnly Secure SameSite=Lax `ew_session` cookie. Customer_id never reaches the frontend. `/auth/request` always returns `{ok: true}` to prevent customer enumeration. Stripe customer lookup uses `Customer.list(email=)`, not `Customer.search(query=)`. Email log lines now masked (`j***@gmail.com`).

Stripe, Watchlist API, Email alerts, QA (Postman/Newman), Railway persistent volume — all LIVE. See `DECISIONS_ARCHIVE.md` for full technical decision log and `SECURITY.md` for full security posture.

---

_Last updated: May 21, 2026 (late) — Big day. v1.6.0 deploy closed, Day 9 Retrospective X post shipped, 4 X followers w/ ~10.3k 2nd-degree reach noted, Pro+ alert validation attempted and surfaced a REAL bug: `/auth/verify` doesn't upsert users.tier, so dashboard-created subs (comps + future enterprise/manual) are invisible to the alert cron. Fix is ~3 lines in auth_router.py — top of the v1.6.1 queue. Side quest: drafted + sent a SpaceXAI engineer application to ai_eng@spacex.com from jason@edgarwolf.com after Elon's X post. Honest odds 15-25% response / 5-10% screen given Elevance Health WatsonX experience + 15-day EdgarWolf solo build._

_May 21 session: Short session. Confirmed Railway deploy with new Resend key was Active. Fired `POST /auth/request` for jason.ostergren79@gmail.com — logs showed full happy path: Stripe customer lookup → active sub on cus_UUN2ChsZV2aaRC → `EVENT magic_link_sent`. Jason pasted the magic-link URL from his inbox; curl'd `/auth/verify` with a cookie jar — got 303 to `/?signed_in=1`, `ew_session` cookie set with HttpOnly + Secure + SameSite=Lax + 30-day Max-Age, all security headers present. Logs confirmed `EVENT auth_verified customer_id=cus_UUN2ChsZV2aaRC`. Subsequent `/auth/whoami` returned `{"tier":"pro_plus","label":"Pro+"}` and `/watchlist` returned the empty list. v1.6.0 is fully verified in prod._

_Two side observations from the smoke-test logs (not blocking, queued as tech debt): (1) `POST /analytics/event 400` fires twice on every post-auth page load — frontend is sending a malformed event payload somewhere; trace via browser network tab + `routers/analytics.py` validation. (2) Every `/auth/whoami` and `/watchlist` call hits Stripe to re-verify the subscription (~140ms each), so each authenticated page load burns 2 Stripe API calls. Fine at 0 users but should get a short-TTL cache (60s) keyed on customer_id before scale matters._

_Discussed the `MAGIC_LINK_SECRET` rotation design question. Claude's recommendation: weekly rotation is security theater at current scale — it only defends against a leaked secret, and the secret never leaves Railway env vars. Better controls: server-side sessions table (jti-keyed) for revocation; Sentry/email alert on `auth.py` errors (would have caught the Resend-key invalidity silently lost in stdout); rate-limit anomaly log line as a distinct event. If Jason ratifies, v1.6.1 becomes sessions-table + Sentry hook rather than the dual-key fallback. Decision parked for next session — full framing captured in §6._

_Session ended early before doing X engagement (Day 9 Retrospective post). That's queued as the natural opener for the next session._

_May 21 session 2 (afternoon/evening): Picked back up after the morning. Closed out the v1.6.0 smoke test by verifying the magic-link round-trip end-to-end (Resend Active, EVENT magic_link_sent, browser-clicked + curl-verified, /auth/whoami returned pro_plus, /watchlist returned the empty list with cookie auth). Two side observations queued as tech debt: POST /analytics/event 400 twice per page after auth (frontend payload bug), and every authenticated page burns 2 Stripe API calls (~140ms each — needs short-TTL cache before scale)._

_Then a sharp side question: are email alerts fully set up for Pro+ users? Honest answer: code-complete and scheduled, but the pipeline had never sent a real email because no Pro+ user had ever had a watchlist. Updated three places in the doc (§1, §3, §6) to drop the misleading "LIVE" framing in favor of "code-complete, prod-untested." Added $CAG + $AAPL to cus_UUN2ChsZV2aaRC's watchlist to set up the test._

_While waiting on the 22:00 UTC cron, drafted Day 9 X post. First draft had 3 em-dashes — Jason flagged that as an LLM tell. Rewrote in his actual voice (periods, ` - `, short declarative sentences). Added "no em-dashes" as a permanent rule in §7. Also weighed and rejected #FinTwit hashtag (hashtags signal outsider on X, cashtags do the work). Jason posted the Retrospective as drafted. Then dropped: he gained a 4th X follower, total 2nd-degree reach now ~10.3k (Ann Barbour 6.8k, Ashton 2.3k). Updated the metrics table._

_22:00 UTC cron fired but EVENT alert_check_start never logged. Investigated root cause: get_all_pro_plus_watchlists() returns empty because users.tier for cus_UUN2ChsZV2aaRC is stale. Only routers/checkout.py writes to users.tier on checkout.session.completed — and Jason's comp sub was created in the Stripe dashboard, which fires customer.subscription.created instead (unhandled by the webhook). /auth/verify also fails to upsert. Real architectural bug, not a comp-sub edge case: any future dashboard-created sub (comps, enterprise, manual) or any webhook delivery failure would silently exclude that user from the alert cron. Promoted to top of v1.6.1 queue. Fix is ~3 lines: have /auth/verify call upsert_user with the tier it just confirmed from Stripe live._

_Side quest: Elon posted on X looking for SpaceXAI engineers ("send 3 bullets to ai_eng@spacex.com, even if you have zero AI experience"). Jason asked me to draft an honest application. First draft underplayed his background. After reading his CareerForce.docx resume, surfaced the Elevance Health WatsonX DVA work (millions of member interactions, Snowflake analytics framework, CMS-regulated, 100% of 2025 targets on time) — direct applied AI experience at Fortune 50 scale. Honest revised odds: 15-25% chance of any response, 5-10% chance of phone screen. Sent verbatim from jason@edgarwolf.com (domain self-verifies the EdgarWolf claim). Mentally closed loop on it._

_Session out: 5 open tasks in queue. Time at close: 5:35 PM CDT / 22:35 UTC._

_**FRIDAY MAY 22 MORNING — ORDER OF OPERATIONS:**_
_1. **Ship v1.6.1 auth-verify upsert fix.** ~3 lines in `routers/auth_router.py:verify_endpoint`. After validating the token + confirming the Stripe sub, call `upsert_user(customer_id, email, tier_from_stripe)`. Bump VERSION to 1.6.1, CHANGELOG entry, commit, tag, push._
_2. **Wait for Railway deploy to go Active.** Check `/openapi.json` shows 1.6.1._
_3. **Trigger the auth flow again** to backfill Jason's user row: `POST /auth/request` → click magic link → `GET /auth/verify`. Confirm via logs that `upsert_user` fires._
_4. **Verify users.tier row exists** in prod DB. Quickest path: build a temp `/admin/whoami-debug` endpoint that returns the local users row alongside the Stripe-live tier, OR add a one-time log line to /auth/verify that prints the upsert result. Tear down after verification._
_5. **Either wait for the next top-of-hour cron** (8/9/10/11... AM ET, M-F) **or manually invoke `run_alert_check()`** via a one-off script. Confirm `EVENT alert_check_start entries>=1` then `EVENT alert_sent` for $CAG. Confirm the email lands in jason.ostergren79@gmail.com, renders correctly, click-through works._
_6. **Once validated, revert the §1/§3 doc language back to "LIVE"** for Pro+ alerts — that framing becomes honest the moment the first alert sends._
_7. **Then circle back to the parked items:** MAGIC_LINK_SECRET rotation decision (§6), dual-key fallback vs sessions-table+Sentry, analytics 400 trace, Stripe-per-page cache._
_8. **Distribution side:** Day 10 X post (Sector Sweep is the natural pick — re-opens the rotation), 4 replies/day, Substack outreach, r/SecurityAnalysis check._

_Also pending from today's drop: any reply from `ai_eng@spacex.com`. If a screener email lands, surface it but don't disrupt the v1.6.1 push to chase it._

_May 19 session: Refreshed README for v1.5.5 (was last touched May 12, missed everything in v1.4.x–v1.5.5 — features section, pricing table, new routers, docs cross-refs, env vars, security highlights, deploy checklist). Posted Day 7 Builder Update on X — first upgrade_modal_open as the hook, 5 countries / first StockTwits post / 2 security releases as supporting beats, magic-link auth flagged as next ship. Then shipped v1.6.0 — full auth hardening release. New `auth.py` module (HMAC token mint/verify, cookie helpers, mask_email) + `routers/auth_router.py` (POST /auth/request, GET /auth/verify, POST /auth/logout, GET /auth/whoami). Removed `/subscription/restore`, `/subscription/status`, `/subscription/status-by-customer` — magic-link replaces the email-leak path; `/auth/whoami` replaces the tier check. `/watchlist/*` reads customer_id from the signed cookie instead of `X-Customer-Id`; the email override on `/watchlist/sync` is gone (webhook now upserts the user record on `checkout.session.completed`). `/billing/portal` reads customer_id from the cookie too. `/success` does a server-side Stripe session lookup and sets the auth cookie before rendering. Frontend stops storing `edgarwolf_customer` anywhere; watchlist fetches use `credentials: 'include'`; restore form posts to `/auth/request` and always shows the same "check your inbox" message. Bundled hygiene fixes: stripe.Customer.list(email=) instead of .search(query=) (query-injection surface), html.escape() every interpolation in scheduler.py:_build_alert_html, mask_email() applied to digest_signup / subscription_started / welcome_email_sent / alert_sent / digest_welcome_sent / digest_unsubscribe / magic_link_sent log lines, fastapi 0.111→0.128 + starlette/python-multipart/requests/urllib3 floor pins to clear pip-audit CVEs. SECURITY.md §4 rewritten to describe the magic-link + cookie model. PostHog no longer identifies by customer_id (it's not on the client anymore) — tier set as anonymous person property. Session paused mid-deploy when Railway had an outage — local commits + tag ready to push but `MAGIC_LINK_SECRET` not yet set._

_May 20 session 2: Day 8 X post — Methodology theme. Pulled live data from `/company/0000023217/dashboard` + `/flags` and confirmed Jason's read that the $CAG numbers had gotten more dramatic since the marketing-assets snapshot. Live shows 4 flags on the Q3 FY26 filing (gross 16.95% / -3.6σ HIGH, op -32.14% / -3.5σ HIGH, net -31.79% / -3.2σ HIGH, rev YoY -15.19% / -2.2σ MEDIUM), net loss -$766M, EPS -$2.20. Op margin trajectory by year: +19% → +8% → -32% — 2nd consecutive quarter with negative operating AND net margins, which is a much stronger story than the original "3 margins 3+ SD below avg" framing. Posted ~720-char version using X Premium's character room: outsider-IT hook → 4 flags as bullets → trajectory → methodology explainer (8 quarters, mean + stdev, 3σ threshold) → CIK-direct URL. Considered automating the daily X post via a scheduled remote agent; decided against auto-posting (Jason doesn't want to pay for X API access — Basic is $200/mo) but the rotation logic is documented for future revisit. Untouched themes are now down to Retrospective only — that's the natural Day 9 pick._

_Then v1.6.0 deploy went live mid-session and the smoke-test sweep started: `/health` ok, `/auth/whoami` unauthenticated returns `{tier:"standard"}`, `/auth/request` unknown-email returns `{ok:true}` (customer-enumeration defense holds), all 3 deprecated `/subscription/*` endpoints gone, all 4 new `/auth/*` endpoints present. Jason set the SEC env vars in Railway: `SEC_REQUIRE_EXPLICIT_USER_AGENT=true` and `SEC_USER_AGENT=EdgarWolf/1.6.0 jason@edgarwolf.com`. App rebooted cleanly (the import-time `_validate_user_agent_config()` would have RuntimeError'd otherwise) and SEC-backed endpoints returning real data._

_The one remaining smoke-test item — magic-link round-trip — turned into a debug rabbit hole. First attempt against jason@edgarwolf.com returned `{ok:true}` but no email arrived. Reading auth_router.py revealed that `/auth/request` only sends if `Customer.list(email=)` returns an active Pro/Pro+ subscription on that email — and at this point in EdgarWolf's life, paying users = 0. Walked Jason through creating a Pro+ comp sub on his own email (jason.ostergren79@gmail.com, which IS the Stripe email — not @edgarwolf.com): create a 100%-off Forever coupon, create or reuse the Stripe customer, attach a Pro+ subscription with the coupon. Sub came up Active on `cus_UUN2ChsZV2aaRC`, MRR contribution $0 (Stripe excludes 100%-off from MRR; also tagged with `internal=true` metadata for future analytics filtering)._

_Re-fired `/auth/request`, still no email. PostHog was a dead end — backend logging goes to Python's `logging` module → stdout → Railway logs only; PostHog is exposed to the frontend only (`/config.js`). Got Jason logged into Railway in his own terminal (after a stumble: tried RAILWAY_TOKEN and RAILWAY_API_TOKEN with a UUID-format token he generated, both rejected — the eventual fix was just `railway login` interactively in his terminal, since `~/.railway/config.json` on disk is shared across shells, my Bash tool included). Pulled logs and found the smoking gun: `ERROR routers.auth_router Failed to send magic link to j***@gmail.com: API key is invalid`. So the **Stripe lookup, customer match, and token mint were all fine** — the failure was the very last hop, Resend rejecting the API call. Jason generated a fresh Resend key with sending access scoped to edgarwolf.com, updated `RESEND_API_KEY` in Railway, but the redeploy queue was slow again. Session paused mid-debug — the new key is sitting in env vars waiting for Railway's queue to flip. Next session: confirm deploy went Active, re-trigger /auth/request, confirm `magic_link_sent` in logs, then complete the round-trip with the URL Jason pastes from his inbox._

_Lessons for the security/ops doc: (1) Resend API key invalidity was silent in production because no successful email path (welcome, alerts, digest) had been exercised before — Free signups = 0 and Paying users = 0 meant Resend had never actually been called in prod. Worth adding a startup-time validation ping to Resend, or a /test/send-alert healthcheck that exercises the email path. (2) The auth router masks emails in logs (j***@gmail.com), which is great for privacy but slightly slowed debug because we couldn't grep for the exact email — though we found it quickly because volume was low. (3) The Stripe `internal=true` metadata convention is now established for any future comp accounts._

_May 20 session: Picked back up after the Railway outage cleared. Generated a fresh `MAGIC_LINK_SECRET` (the May 19 value was in the transcript and considered burned), Jason set it in Railway Variables. Pushed `cc2cf1d` (v1.6.0) + `0c8e639` (README refresh) + tag `v1.6.0` to `main`. Live site stayed on v1.5.5 through session close — Railway's build queue was slow due to a known platform issue, push was in queue but hadn't deployed when we ended. Next session: wait for deploy, run the prod smoke test (`/auth/whoami` returns `tier=standard` without cookie, magic-link round-trip from jason@edgarwolf.com, `/auth/request` unknown-email returns `{ok: true}`), then close out the v1.6.0 deploy story. Side observations from the session: secfilings.com surfaced as a recently-relaunched competitor on a premium 1998 domain (Vercel/Next.js, no pricing/about/founder, search/aggregator model, ad-supported or unmonetized) — SEO threat at top of funnel only, not a subscription competitor. Saved as project memory. Open question to settle next session: is weekly `MAGIC_LINK_SECRET` rotation actually the right control, or should EdgarWolf invest in alternatives (audit log, anomaly alerts on /auth/*, short session TTL with server-side revocation)?_

_May 18 session: Posted $UNH on X (news-driven Company Spotlight — Berkshire sold entire stake, FSS 92/100, 8-K 6 days before 10-Q). Posted $SOFI Contrarian/Green (profitable trajectory, bottom-line only — XBRL unreliable for fintechs). First StockTwits post live ($UNH Bearish). PostHog 24hr: first upgrade_modal_open (Minneapolis iPhone, $AAPL page, May 17 8:12 AM CT — warm returning lead, came back same day), Philippines = new country, $UNH clicked same day as post. Fixed signal_board_skip analytics bug — was firing 154× per board load, now fires once with aggregate stats. Trimmed context doc, created DECISIONS_ARCHIVE.md. Day 7: Builder Update — plan tomorrow morning._

_May 18 session 2 (v1.5.4 — security hardening): Full security review of the codebase identified 10 issues across CRITICAL/HIGH/MEDIUM/LOW severity. All fixed and shipped in one release. Highlights: patched reflected XSS on the `/success` Stripe redirect page (session_id and tier were interpolated directly into a `<script>` tag); added the full standard set of browser security headers (X-Frame-Options, X-Content-Type-Options, Referrer-Policy, HSTS) on every response; fixed proxy-aware rate limiting by adding `--proxy-headers --forwarded-allow-ips='*'` to uvicorn so the real client IP is used instead of Railway's LB; expanded rate limiting to /digest/subscribe and /subscription/restore; hardened Stripe webhook to fail closed when secret is missing; added escapeAttr() to all remaining innerHTML injection points (flags, provenance panel, trust panel, quarterly table, segments); gated `?debug=true` to dev only; replaced IP-based dev endpoint check with `DEV_SECRET` env var. Created SECURITY.md as the canonical security posture document — organized by category, suitable to share with customers/partners/investors who ask about site security._

_May 18 session 3 (v1.5.5 — XSS hotfix + second-pass review): Live-site testing immediately after the v1.5.4 deploy caught an incomplete XSS fix on `/success`. The v1.5.4 patch used `json.dumps()` for the script-block interpolations, but json.dumps does not escape `<` or `>` — a payload containing `</script>` still ended the script tag and allowed HTML injection. Shipped v1.5.5 with a `_script_safe_json()` helper that additionally Unicode-escapes `<`, `>`, and `&`. Lesson recorded in CHANGELOG: always probe live with adversarial payloads after a security release._

_Then ran a second-pass review. Biggest finding: **email-based account hijack via `/subscription/restore`**. The endpoint returns the Stripe customer_id to anyone who types a Pro user's email; combined with the unauthenticated email-overwrite field in `POST /watchlist/sync`, an attacker can read the victim's watchlist and reroute their Pro+ filing alerts to a different inbox. Also noted: stripe.Customer.search query-injection surface (no email validation), full emails in plaintext logs (Railway), unescaped HTML in alert emails (low impact, but worth fixing), and 30 pip-audit findings in deps (starlette + python-multipart most relevant)._

_Decision for tomorrow: implement option 1 — magic-link auth via Resend. User enters email → server verifies Stripe has an active sub on that email → Resend sends a short-lived (15min) signed-token magic link → click sets httpOnly cookie → frontend stops storing customer_id in localStorage. Stripe stays source of truth; Customer Portal integration unchanged. Honest framing: Stripe doesn't have a built-in "user proves email ownership" primitive — Customer Portal requires us to already know the customer. The magic-link is the standard pattern and the small piece we have to build ourselves. Bundle the hygiene fixes (Stripe query-injection, log masking, email HTML escape, dep bumps) into the same release as v1.6.0._

_Site healthy at session close: v1.5.5 live, all 4 security headers verified in production, XSS payloads blocked, /health ok, smoke-test API calls returning real data._
