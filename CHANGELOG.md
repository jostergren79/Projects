# Changelog

All notable changes to EdgarWolf are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/):
- **Major** — breaking changes or complete platform overhauls
- **Minor** — new user-facing features (bumped each session)
- **Patch** — bug fixes and hotfixes between sessions

---

## [1.7.4] — 2026-05-28

Conversion-focused release. PostHog showed traffic arriving (mostly via Google) but
not converting: 22 digest-banner views with 0 signups, and a single upgrade-modal open
that bailed. These changes target the three leak points — digest capture, landing
clarity, and the upgrade ask.

### Changed
- **Digest banner now surfaces after a company dashboard loads, not on cold landing.**
  `initDigestBanner()` returns early (hiding the banner) unless a company is on screen
  (`currentCompany`), and `renderDashboard()` re-invokes it — so every load path (search,
  `?cik=` deep link, dev-toggle re-render) asks for an email only *after* the visitor has
  seen real value. Copy rewritten to lead with the offer ("Every Sunday: the 10
  most-flagged S&P 100 filings…") and the CTA changed from "Subscribe" to "Send me
  Sunday's". **Measurement note:** `digest_banner_view` now fires deeper in the funnel, so
  track view→signup *rate*, not raw view counts.
- **Landing subhead rewritten to the anomaly value prop** — "Pull any US public company's
  latest SEC filing. See where its margins, revenue, and filing behavior break from the
  norm." — to match the X data-card promise instead of describing search mechanics. The
  example-chip lead-in changed to "Try a live example:".
- **Upgrade modal is now context-aware.** When opened from a company dashboard, the
  subhead names the company: "Unlock Exception Flags, Filing Stress Score, and peer
  comparison for {company}. Cancel anytime." A trailing-period strip keeps names like
  "Apple Inc." from rendering a double period. `upgrade_modal_open` now carries a
  `company` property for funnel analysis.

### Notes
- Frontend-only (`edgar-frontend/edgar.html`); no API or schema changes.
- Verified on real-device viewports (iPhone 14 Pro Max 430px + iPhone SE 375px): no
  horizontal overflow; banner, landing, and modal all render cleanly. (Apparent clipping
  in earlier headless captures was a layout-viewport-vs-canvas artifact in `--headless=new`,
  not a CSS bug — confirmed via in-page `scrollWidth == innerWidth` measurement.)

---

## [1.7.3] — 2026-05-27

### Fixed
- **XBRL cumulative-to-quarter differencing for filers with comparative re-tagged periods.**
  EDGAR re-uses the same `(fy, fp)` labels on prior-year comparative periods included in
  later 10-Q filings. This caused `fy_fp_map` to pick a comparative prior-year cumulative
  value as the differencing base, producing impossible per-quarter figures (e.g. Micron
  showed ~$3.3B/qtr instead of the correct ~$2.8B, and wildly wrong YoY %). Fixed by
  keying the map on `(start_date, fp)` instead of `(fy, fp)` — YTD cumulative rows within
  the same fiscal year always share the same fiscal-year start date, so the pairing is
  unambiguous regardless of how EDGAR tags the `fy` field on comparative rows.

### Added
- **Dynamic OG images per CIK for social link previews.** `GET /og/{cik}.png` generates
  a branded 1200×630 PNG (company name, ticker, EdgarWolf wordmark) using Pillow; result
  is cached in memory (max 500 entries). When `/?cik=` is present, the served HTML now
  injects dynamic `og:image`, `og:title`, `og:description`, `twitter:image`,
  `twitter:title`, and `twitter:description` tags, so X/LinkedIn previews show the actual
  company instead of the static General Mills default.

---

## [1.7.2] — 2026-05-26

### Changed
- **Stripe re-verify is now cached for 60s, shared across `/auth/whoami` and
  `/watchlist`.** `/auth/whoami` previously hit Stripe on every uncached call; it now
  reads/writes the same `session_tier_cache` entry as `/watchlist` (keyed by
  customer_id via `session_tier_cache_key`), so a page-load burst of tier checks
  collapses to a single Stripe call. The watchlist cache TTL dropped from 1 hour to
  60s, so a lapsed/cancelled subscription loses access within ~1 minute instead of up
  to an hour.
- **Analytics: per-device internal opt-out so household traffic stops inflating
  "external" PostHog counts.** Visiting `?internal=1` sets a `localStorage` flag;
  the frontend then skips PostHog init entirely and `trackEvent` no-ops, so that
  browser emits zero analytics events (`?internal=0` clears it). Device-based, so it
  survives the Verizon-cellular / reassigned-home-IPv6 rotation that the static 4-IP
  filter could not catch. Requires Jason + Sam to visit `?internal=1` once per device.
  (Deployed 2026-05-25 ahead of this release tag.)

### Internal
- Postman QA collection regenerated: dropped the dead `/subscription/*` group and the
  `X-Customer-Id` header bypass (auth is the `ew_session` cookie now); added an `Auth`
  group covering `/auth/whoami`, `/auth/request`, `/auth/verify`, and `/auth/logout`.

---

## [1.7.1] — 2026-05-24

### Fixed
- **Loss-making quarters showed net income/EPS without a proper negative sign,
  making a loss read like a profit.** Two halves of one display bug:
  - *Narrative summary (backend):* `_fmt_currency()` formatted with `abs()`, so a
    net loss rendered as a positive dollar figure — ENPH Q1 2026 read "Net income
    was $7M" while EPS showed the loss as "$-0.06", an internally contradictory
    sentence. The formatter now preserves sign and the bottom-line sentence reads
    "Net loss was $X" when net income is negative.
  - *Dashboard (frontend):* the KPI tile labelled a loss "Net Income" in neutral
    styling, and `fmtCurrency` placed the minus after the `$` ("$-7M"). The tile now
    reads "Net Loss" in the negative (red) color when net income is below zero, and
    `fmtCurrency` renders "-$7M". Negative EPS renders "-$0.06" (was "$-0.06") in
    both the KPI tile and the quarterly data table.

  Display-only — `data.*` / API values were already correctly signed (prod returns
  ENPH `net_income: -7406000`), so no data or API change. Verified in-browser against
  live SEC data. See METHODOLOGY.md §10.

---

## [1.7.0] — 2026-05-22

### Added
- **Weekly Filing Stress digest (Sunday 08:00 ET), now offered to every tier.**
  New `run_weekly_digest()` job scans the S&P 100 for material filings
  (10-Q/10-K/8-K) in the trailing 7 days, scores each by Filing Stress Score,
  and emails the top 10 to all active digest subscribers with a one-click
  unsubscribe link. This is the send job behind the capture form that had been
  collecting emails — subscribers were promised a Sunday email that now actually
  ships. See METHODOLOGY.md §16.
- **One-click digest subscribe for signed-in users.** `POST /digest/subscribe-me`
  resolves the subscriber's email server-side from the session cookie's
  `customer_id` (local `users` table, Stripe fallback), so Pro/Pro+ users
  subscribe without typing an address and none is exposed to the client.
  `/auth/whoami` now returns `digest_subscribed` so the banner renders the
  correct state.

### Changed
- **Digest banner is no longer hidden from paid users.** Previously gated to
  `tier === 'standard'`. The digest is now positioned as marketwide
  discovery/retention content (distinct from per-watchlist Pro+ alerts) and is
  shown to all tiers: standard/anonymous visitors get the email form, signed-in
  users get the one-click button. Banner copy updated to the S&P 100 top-10
  framing.

---

## [1.6.1] — 2026-05-21

### Fixed
- **`/auth/verify` now upserts the user record.** Before this, only the
  `checkout.session.completed` webhook wrote `users.tier`. Subscriptions created
  in the Stripe dashboard (comps, enterprise, manual) were therefore never
  persisted locally, and the Pro+ alert cron's `WHERE tier = 'pro_plus'` filter
  silently excluded them — so the hourly job started, found no Pro+ watchlists,
  and exited without ever sending. On sign-in, `/auth/verify` now fetches the
  active tier and email from Stripe and calls `upsert_user`, so any paying
  customer who signs in becomes visible to the alert pipeline. Unblocks
  end-to-end Pro+ email-alert delivery.

---

## [1.6.0] — 2026-05-19

### Security
Auth hardening release. Addresses the email-based account-hijack vector
discovered in the v1.5.5 second-pass review, plus a bundle of hygiene fixes.

- **Replaced email-only `/subscription/restore` with magic-link auth.** The old
  endpoint returned the Stripe `customer_id` to anyone who typed a Pro user's
  email — full account hijack (read/modify watchlist, reroute Pro+ alert
  emails). New flow: user enters email → server verifies an active Stripe
  subscription on that email (via `stripe.Customer.list(email=...)`) →
  Resend sends a short-lived signed magic link (HMAC-SHA256, 15-minute TTL) →
  click sets a 30-day httpOnly Secure SameSite=Lax cookie containing a signed
  customer_id. The frontend no longer stores customer_id anywhere.
  `POST /auth/request` always returns 200 — silence is the only signal an
  attacker gets, preventing customer enumeration.
- **`/watchlist/*` switched to cookie auth.** Endpoints read customer_id from
  the signed `ew_session` cookie instead of the `X-Customer-Id` header. The
  unauthenticated `email` field on `POST /watchlist/sync` is removed; the
  user's email is now set canonically via the Stripe webhook on
  `checkout.session.completed`, closing the alert-reroute path.
- **`/billing/portal` reads customer_id from the session cookie**, not the
  request body. A third party can no longer open the portal for an arbitrary
  customer.
- **`/success` sets the auth cookie server-side** after looking up the Stripe
  checkout session. The post-payment flow no longer relies on client-side
  customer_id storage.
- **Removed `/subscription/restore`, `/subscription/status`, and
  `/subscription/status-by-customer`.** Tier is now established via the new
  `GET /auth/whoami` endpoint, which reads the session cookie and re-verifies
  the active subscription against Stripe (so cancelled/lapsed subs are
  reflected immediately).
- **Replaced `stripe.Customer.search(query=...)` with
  `stripe.Customer.list(email=...)`** to remove the Lucene-style query
  injection surface in the customer lookup path.
- **Masked emails in EVENT log lines** (`digest_signup`, `subscription_started`,
  `welcome_email_sent`, `alert_sent`, `magic_link_sent`, `digest_welcome_sent`,
  `digest_unsubscribe`). Emails are now logged as `j***@gmail.com`; the domain
  is preserved for routing analysis but the local-part is not.
- **HTML-escaped every interpolation in `scheduler.py:_build_alert_html`**
  (company name, ticker, CIK, form type, filing date, stress status, flag
  metric, flag note). A maliciously-named company or crafted XBRL concept
  could previously inject HTML into Pro+ alert emails.

### Dependencies
- `fastapi` 0.111.0 → 0.128.0
- `starlette` pinned `>=0.47.0` (clears the pip-audit advisories)
- `python-multipart` pinned `>=0.0.18` (clears CVE-2024-53981)
- `requests` pinned `>=2.32.4` (clears CVE-2024-47081)
- `urllib3` pinned `>=2.5.0`

### Added
- `edgar-api/auth.py` — HMAC token mint/verify + cookie helpers + `mask_email`
- `edgar-api/routers/auth_router.py` — `/auth/request`, `/auth/verify`,
  `/auth/logout`, `/auth/whoami`
- New env var `MAGIC_LINK_SECRET` (required — generate with
  `python -c 'import secrets; print(secrets.token_urlsafe(48))'` and set in
  Railway Variables)

### Notes
- Cookie `Secure` flag follows `APP_URL` scheme: enabled when `APP_URL`
  starts with `https://`, disabled otherwise. Production stays Secure-only;
  local dev over `http://127.0.0.1` works without HTTPS.
- The frontend's `?dev_tier=pro` localhost bypass is unchanged.
- PostHog identify no longer ties events to a Stripe customer_id (the
  frontend doesn't see it anymore). Tier is set as an anonymous person
  property; we lose cross-device session stitching by customer_id in
  exchange for keeping customer_id out of client-side telemetry.

---

## [1.5.5] — 2026-05-18

### Security (hotfix)
- **Fixed incomplete XSS fix on `/success` page.** The v1.5.4 patch wrapped query-parameter values in `json.dumps()` to neutralize basic string-breakout payloads, but `json.dumps` does not escape `<` or `>`. A payload containing `</script>` would still terminate the surrounding script block and allow HTML injection. Live-site testing immediately after v1.5.4 deploy caught this. The fix is a new `_script_safe_json()` helper that additionally escapes `<`, `>`, and `&` as Unicode sequences (`<`, `>`, `&`) — JavaScript decodes these back inside string literals but the HTML parser treats them as inert data. Applied to all three `localStorage.setItem` interpolations on the success page.

---

## [1.5.4] — 2026-05-18

### Security
Comprehensive security review and hardening pass. See `SECURITY.md` for the full security posture document.

- **Fixed reflected XSS on `/success` page** — the Stripe redirect target was interpolating the `session_id` and `tier` query parameters directly into a `<script>` block. An attacker could craft a URL that executed arbitrary JavaScript in a victim's browser. All string injections now go through `json.dumps()` and `tier` is validated against an allowlist before use.
- **Browser security headers on every response** — added `X-Frame-Options: DENY` (clickjacking), `X-Content-Type-Options: nosniff` (MIME sniffing), `Referrer-Policy: strict-origin-when-cross-origin` (URL leakage), and `Strict-Transport-Security: max-age=63072000; includeSubDomains` (HTTPS pinning).
- **Proxy-aware rate limiting** — uvicorn now starts with `--proxy-headers --forwarded-allow-ips='*'`, so `request.client.host` reflects the real visitor IP instead of Railway's load balancer IP. Previously every visitor shared a single rate-limit bucket, rendering the limiter effectively useless.
- **Expanded rate-limiting coverage** — `/digest/subscribe` and `/subscription/restore` now rate-limited at 200/min per IP to prevent automated email enumeration and welcome-email spam.
- **Rate limiter no longer leaks memory** — empty per-IP windows are evicted immediately; periodic cleanup pass evicts stale IPs every 10,000 requests.
- **Stripe webhook hardened** — the dangerous fallback that accepted unverified events when `STRIPE_WEBHOOK_SECRET` was unset has been removed. Missing secret now returns HTTP 500. Webhook signature verification is now non-optional.
- **Frontend HTML escaping consistency** — applied `escapeAttr()` to all remaining `innerHTML` injection points that were missed in earlier passes: exception flag metric/note/severity (severity was being injected into a CSS class), provenance panel fields, trust-panel XBRL concept names, quarterly-table period strings, and segment names.
- **`?debug=true` no longer sent in production** — added an `isDev` guard to the three frontend fetches that included it. Internal row context and concept-mapping diagnostics no longer flow to production browsers.
- **Dev test endpoints gated by `DEV_SECRET`** — `/test/send-alert`, `/test/seed-alert-user`, and `/test/run-alert-check` now accept either localhost-origin requests OR a matching `X-Dev-Secret` header. With proxy-headers enabled, external requests can never impersonate localhost.

### Added
- **`SECURITY.md`** — full security posture document covering transport, API hardening, payments, authentication, data handling, secrets, and operational controls. Intended as a canonical reference for customers, partners, or investors asking about the site's security.

---

## [1.5.3] — 2026-05-14

### Fixed
- **`/config.js` no longer cached by Cloudflare** — added `Cache-Control: no-store, max-age=0` headers to the config endpoint. Cloudflare's default rules were caching the file for 4 hours (`max-age=14400`), which meant env var updates (like adding `POSTHOG_KEY`) didn't take effect until the cache expired or visitors hard-refreshed. Config values must always reflect current env state immediately.

---

## [1.5.2] — 2026-05-14

### Added
- **PostHog product analytics + session replay** — initialized client-side in `edgar.html` via a `GET /config.js` route that exposes `POSTHOG_KEY` from env vars (no key committed). US Cloud region (`api_host: https://us.i.posthog.com`). Autocapture, heatmaps, web vitals, session recordings all on. CSP updated to allow `us.i.posthog.com` + `us-assets.i.posthog.com` for script/connect/img/font sources.
- `trackEvent()` now mirrors every event to `posthog.capture()` while still logging to Railway (redundancy).
- `identifyToPostHog()` ties activity to the Stripe customer ID for paid users; Standard tier remains anonymous.

### Changed
- **Watchlist panel always visible for Pro/Pro+** — `renderWatchlistPanel()` previously hid the panel whenever the company dashboard was visible. Now Standard users keep the old behavior (panel only on discovery view) but Pro/Pro+ users see the panel on every page including company dashboards. Fixes the "panel disappears when navigating back-and-forth" issue.
- **Action row repositioned for Pro/Pro+** — Watchlist + Export CSV/JSON buttons now render at the top of the company dashboard (right under the company-header) for Pro and Pro+ users. Standard users keep the buttons below the Pro Analytics divider where the upgrade prompt lives. Implemented via an `#action-row-top-slot` placeholder and JS relocation in `applyTierGating()`.
- **Privacy policy updated** — removed inaccurate "no third-party analytics" claim. New "Product Analytics" section discloses PostHog + session replay + Stripe customer ID identification. PostHog and Sentry added to Third-Party Services list. "Last updated" bumped to 2026-05-14.
- **`.claude/` added to .gitignore** — local Claude Code workspace config stays out of the repo.

---

## [1.5.1] — 2026-05-14

### Added
- **Free-tier email capture** — dismissable banner under the header offering a free weekly Filing Stress digest. Inline email form with success/error states. Banner hides for paid users (already on file via Stripe) and for users who dismissed or subscribed previously.
- `POST /digest/subscribe` — validates email, stores in `digest_subscribers` table, sends Resend welcome email with a one-click unsubscribe link.
- `GET /digest/unsubscribe?email=...` — marks subscriber as unsubscribed and returns a styled confirmation page.
- `digest_subscribers` table added to SQLite schema (email PK, source, subscribed_at, unsubscribed_at).
- 3 new analytics events: `digest_banner_view`, `digest_banner_dismiss`, `digest_signup`.

### Notes
- The actual weekly digest send job is **not yet built** — this release captures the audience first. The Sunday send needs to be implemented before the list grows past trivial size.
- Welcome email send verified end-to-end against `jason@edgarwolf.com` from local dev server.

---

## [1.5.0] — 2026-05-13

### Added
- **Welcome email** — sent via Resend on `checkout.session.completed` Stripe webhook. Pro email lists features; Pro+ email includes an "Email Alerts — Active" callout. Stripe checkout session now includes `metadata={"tier": tier}` so the webhook correctly identifies the plan.
- **Privacy Policy** — served at `/privacy`, linked from app footer.
- **Terms of Service** — served at `/terms`, linked from app footer.
- **Watchlist company limit** — backend enforces 50-company cap (HTTP 422 with contact message). `GET /watchlist` now returns `count` and `limit` fields. Frontend pre-checks locally before adding, and rolls back + alerts user if the server rejects with 422.
- **Sentry error monitoring** — `sentry-sdk[fastapi]` added to requirements. Initialized in `main.py` when `SENTRY_DSN` env var is set; no-op locally. `traces_sample_rate=0.1`, `send_default_pii=False`.
- **Postman QA expansion** — 3 new folders: Watchlist (8 requests), Alerts dev-only (2 requests), Pages (2 requests). Collection grows from 28 requests / 49 assertions → 40 requests / 66 assertions. `test_customer_id=cus_test` added to Local environment.

### Fixed
- **watchlist.py stale Pro price ID** — default fallback was the old pre-$19.00 price ID (`price_1TVNeQ1C3cijZqBOkOX1IoJj`). Updated to match checkout.py (`price_1TWTJz1C3cijZqBOyfX4VwHC`). Mismatch was harmless in production (env var set) but a landmine for local dev.
- **Alert email CTA deep link** — `_build_alert_html` was constructing a URL using `name` instead of `cik`, and the variable was never wired to the button (button hardcoded the homepage). CTA now deep-links to `/?cik={cik10}` for the specific company. `cik` added as a parameter to `_build_alert_html`.

---

## [1.4.1] — 2026-05-13

### Added
- `/favicon.ico` route serving `favicon-32.png` — enables Google Search crawler to discover and display the EW favicon in search results.
- `<link rel="shortcut icon">` tag in `edgar.html` for legacy favicon discovery.
- `sitemap.xml` with homepage URL and `/sitemap.xml` FastAPI route. Submitted to Google Search Console; indexing requested.

### Changed
- Action row (Watchlist, Export CSV, Export JSON) moved below the Pro Analytics divider — users now see full free content before hitting Pro-gated buttons.
- Watchlist and Export buttons now display inline "Pro" badge instead of "(Pro)" suffix text.
- KPI grid changed from `auto-fit` to `auto-fill` — last row cards (EPS, Net Income) now match width of the 4-card rows above.
- Narrative summary box `max-width` removed — now spans full dashboard width, matching KPI grid and charts below it.
- CLAUDE_CONTEXT.md updated: founder background, X marketing strategy, Google Search Console status, email alert system marked fully live.

---

## [1.4.0] — 2026-05-12

### Added
- **Pro+ email alert system** — APScheduler background job polls SEC EDGAR hourly (M–F 08:00–18:00 ET) for new 10-Q/10-K/8-K filings across all Pro+ user watchlists. Sends email via Resend when a new filing is detected and at least one anomaly signal (MEDIUM/HIGH z-score flag or ELEVATED Filing Stress Score) is present.
- `scheduler.py` — new module with `AsyncIOScheduler` + `CronTrigger`, wired into FastAPI lifespan.
- `alert_log` table — deduplicates alerts by `(customer_id, cik, accession_number)`; same filing never triggers a second email.
- `alert_checks` table — tracks `last_checked_at` per `(customer_id, cik)` pair so each poll only looks at filings newer than the previous check.
- Dev-only endpoints: `POST /test/seed-alert-user` and `POST /test/run-alert-check` for local alert testing (403 in production).
- **Upgrade modal with Pro+ plan card** — modal now shows both Pro ($19/mo) and Pro+ ($99/mo) side by side. Context-aware: Standard users see both, Pro users see only the Pro+ upgrade.
- `tier-pro-plus` CSS class — Pro+ badge displays in green, distinct from Pro (blue).
- **EW favicon** — `favicon.png` (192×192) and `favicon-32.png` (32×32) with dark background and blue "EW" mark. Served via FastAPI routes. Replaces inline SVG data URI that Google couldn't crawl.
- `generate_favicon.py` — script to regenerate favicon assets.
- `<link rel="canonical" href="https://www.edgarwolf.com/" />` — signals www as the canonical URL for Google deduplication.
- METHODOLOGY.md §13–15: Alert Polling Schedule, Alert Trigger Conditions, Alert Log and State Management.
- Methodology doc rule added to CLAUDE_CONTEXT.md dev workflow: update METHODOLOGY.md before or alongside any new logic.

### Changed
- Pro price updated to **$19.00/mo** (new Stripe price ID `price_1TWTJz1C3cijZqBOyfX4VwHC`; old $19.99 price archived).
- FastAPI lifespan context manager added to `main.py` — scheduler starts/stops cleanly with the app.
- `apscheduler==3.10.4` added to `requirements.txt`.

### Fixed
- **bfcache bug** — `pageshow` handler resets "Get Pro →" / "Get Pro+ →" buttons that got stuck on "Loading…" after navigating back from Stripe checkout.

### Infrastructure
- Cloudflare redirect rule `apex-to-www` deployed: `edgarwolf.com` → `https://www.edgarwolf.com` (301, path + query string preserved). Both domains were previously resolving independently with no canonical redirect.

---

## [1.3.3] — 2026-05-12

### Added
- Cloudflare custom hostname HTTP challenge handler (`GET /.well-known/cf-custom-hostname-challenge/{token}`) — required for Railway's Cloudflare integration to verify domain ownership without failing during deploys.

### Fixed
- CSP updated to allow `https://static.cloudflareinsights.com` script and `https://cloudflareinsights.com` connect — eliminates console errors from Railway's Cloudflare beacon injection.
- Footer and FastAPI version strings synced to 1.3.3 (were stale at 1.3.0/1.3.2).

### Infrastructure
- Completed Railway + Cloudflare one-click integration for `edgarwolf.com` — Railway now manages hostname verification, eliminating intermittent "Service Suspended" errors on every deploy.
- `www.edgarwolf.com` added as Railway custom domain with cert provisioned.
- Cloudflare redirect rule pending: `edgarwolf.com` → `www.edgarwolf.com` (to be set in Cloudflare dashboard).
- Repo fully cleaned: removed S&OP project files, Node.js static server, Render config, `runtime.txt` files. `notes-api/` renamed to `edgar-frontend/`, `public/` nesting removed.

---

## [1.3.2] — 2026-05-12

### Removed
- `sop.html` and `query.html` — old PCB S&OP project files, unrelated to EdgarWolf
- `runtime.txt` (root and `edgar-api/`) — Render/Heroku artifact, obsolete on Railway
- `notes-api/server.js` and `notes-api/package.json` — old Node.js static server, FastAPI now serves all pages
- `notes-api/scripts/smoke-public-mode.sh` — tested the Node.js server which is now removed
- `notes-api/README.md` — stale, referenced removed files
- `notes-api/dist/` — Node.js build artifacts

### Changed
- `README.md` (root) — full rewrite reflecting current EdgarWolf architecture
- `scripts/clean-local-artifacts.sh` — removed node_modules/dist references, added WAL file cleanup
- `.gitignore` — removed obsolete `notes-api/node_modules` and `notes-api/dist` entries

---

## [1.3.1] — 2026-05-12

### Fixed
- Railway build: replaced manual `nixPkgs = ["python311"]` in nixpacks.toml with auto-detection via root `requirements.txt`. Manual nix Python install did not include pip, causing `No module named pip` build failures.
- SQLite persistence: `CACHE_PATH` in `cache.py` now reads `DATA_DIR` env var (set to `/app/data` in Railway). Previously wrote to `edgar-api/data/` which was not on the persistent volume.

### Infrastructure
- Added root `requirements.txt` (points to `edgar-api/requirements.txt`) for nixpacks Python auto-detection.
- Simplified `nixpacks.toml` to only override the start command.
- Railway persistent volume mounted at `/app/data` — SQLite now survives redeploys.
- Stripe webhook URL updated from old Render URL → `https://www.edgarwolf.com/webhook/stripe`.
- Cloudflare DNS fully verified in Railway. `edgarwolf.com` and `www.edgarwolf.com` both live on Railway.
- Render service decommissioned (pending — do after confirming Railway stable for 24h).

---

## [1.3.0] — 2026-05-12

### Added
- Server-side watchlist persistence for Pro/Pro+ users. New SQLite tables: `watchlists` (customer_id, cik, ticker, name, added_at) and `users` (customer_id, email, tier). Watchlist data now survives across devices and sessions for paid users.
- Watchlist API: `GET /watchlist`, `POST /watchlist`, `DELETE /watchlist/{cik}`, `POST /watchlist/sync`. All endpoints gated by `X-Customer-Id` header (Stripe customer ID validated + cached 1h in SQLite).
- Frontend `syncWatchlistFromServer()`: runs once per session for Pro/Pro+ users, merges server list into localStorage and pushes any localStorage-only items up. Standard users continue using localStorage only.
- `routers/alerts.py`: `POST /test/send-alert` dev-only endpoint. Sends a real HTML alert email via Resend (localhost-only, 403 in production).
- `.vscode/tasks.json` + `settings.json`: VS Code dev tooling — Start Dev Server tasks for each tier + Simple Browser support.
- `railway.toml` at repo root: Railway deployment config (nixpacks build, uvicorn start command, health check).

### Changed
- Migrated hosting from Render to Railway ($5/month Hobby plan). `railway.toml` replaces `render.yaml` as the active deploy config.
- CORS middleware now allows `POST` and `DELETE` in addition to `GET` (required for watchlist endpoints).
- `RESEND_FROM` env var set to `EdgarWolf <alerts@edgarwolf.com>` — Resend domain verified (DKIM + SPF + MX all green), test alert delivered end-to-end to gmail.
- DNS migrating from GoDaddy direct CNAME → Cloudflare (in progress — enables CNAME flattening at root domain).

### Infrastructure
- Railway persistent volume (`/app/data`) required before next deploy to persist SQLite across redeploys. Pending setup in Railway dashboard.
- Stripe webhook URL needs updating from Render URL to `https://www.edgarwolf.com/webhook/stripe` once DNS is live on Railway.

---

## [1.2.0] — 2026-05-12

### Added
- QA automation via Postman + Newman: `edgar-api/postman/` contains full collection (28 requests, 7 folders, 49 assertions). Newman runner: `edgar-api/postman/run_qa.sh [local|production]`. All 49 assertions pass.
- Dev tier toggle: amber button in header (localhost only) cycles Standard → Pro → Pro+ without page reload. Uses stored dashboard state for instant re-render.
- OG/link preview image: 1200×630 PNG at `/og-image.png`, served via FastAPI. Shows $GIS example data. `twitter:card = summary_large_image`. Regenerate with `generate_og_image.py`.
- CSP fix: API base uses `window.location.origin` on localhost so `connect-src 'self'` always matches.

### Fixed
- `showProGate()` was replacing section innerHTML and destroying child elements — `restoreGatedSections()` now resets all 6 panels at the start of every `renderDashboard` call.

---

## [1.1.0] — 2026-05-12

### Added
- Signal board is now on-demand: users click "Load Signal Board" and choose 5–25 companies per column (default 10). No more auto-load on page open, which was causing slow cold-start performance.
- Feed limit raised from 100 to 200 to support larger signal board selections.
- `dev.sh` local development launcher: kills port 8000, starts uvicorn --reload, waits for health check, opens browser. Usage: `./dev.sh [standard|pro|pro_plus]`.
- `?dev_tier=` URL parameter bypasses Stripe verification on localhost only — safe in production (hostname-gated). Enables testing all tier states without a real subscription.
- Stripe Customer Portal integration: `POST /billing/portal` creates a hosted portal session. Users can cancel, update payment method, and view invoices without contacting support.
- "Manage" button in header next to tier badge for all paid subscribers — redirects to Stripe Customer Portal.
- `GET /subscription/status` now returns `customer_id` so it is stored in localStorage immediately after checkout, enabling portal access without needing email restore first.

### Changed
- Pro price display corrected to $19.99/mo throughout (modal, docs, comments).
- Metrics endpoint (`GET /company/{cik}/metrics`) returns HTTP 200 with empty `periods` array instead of HTTP 404 when a company has no EDGAR financial data. Eliminates noisy browser console errors during signal board scoring — companies with no data are silently skipped.

### Fixed
- Signal board 422 error when selecting 20–25 companies per column: feed endpoint hard cap raised from `le=100` to `le=200`.

---

## [1.0.0] — 2026-05-10

Initial public launch with monetization live.

### Added
- Feature gating: 6 Pro sections gated behind upgrade cards (Exception Flags, Filing Signals, Peer Comparison, Segment Breakdown, Source Filing, Data Quality). Free tier retains unlimited lookups, 8-quarter charts, and quarterly data table.
- Stripe Checkout integration: Pro ($19.99/mo) and Pro+ ($99/mo) with live price IDs.
- Stripe webhook handler: `checkout.session.completed`, `customer.subscription.deleted`, `invoice.payment_failed`.
- Email-based subscription restore (`GET /subscription/restore?email=`): users who clear localStorage can recover their subscription by entering their email. Customer ID stored for future re-verification.
- Tier badge in header: ✓ Pro (blue) / ✓ Pro+ (green) after Stripe verification. Cached 1 hour in localStorage.
- Upgrade modal with single Pro card (Pro+ hidden until email alerts ship).
- Summary CTA below narrative for free users: "Want to know what's driving this? Upgrade to Pro →".
- Pro divider between free and gated sections.
- Signal board: 10 strengthening + 10 weakening companies sourced from 80 recent SEC filers, scored on revenue YoY, gross margin trend, and operating margin trend.
- Entity type detection: foreign filers (20-F/6-K) and ETFs show a friendly unsupported message instead of an empty dashboard.
- OG/meta tags for social link previews (Twitter/X, LinkedIn, Discord).
- UptimeRobot health keep-warm ping every 5 minutes (prevents Render cold starts).
- Analytics event tracking: 8 events emitted as structured log lines to Render logs.

### Fixed
- Stripe price IDs were swapped: "Get Pro" was charging $99. Corrected in `PRICE_IDS` dict.
- Mobile: Upgrade button was hidden by `display: none` on `.header-actions` at 580px breakpoint.
- Repeated company searches caused `Cannot set properties of null (setting 'innerHTML')` — null guards added to `renderTrustPanel` and `renderProvenance`.
- Loading spinner appeared below the signal board fold — now scrolls into view on search.
- False-positive entity detection flagged Walmart and other large domestic filers as unsupported due to a flawed `hasNoQuarterlyFilings` heuristic — removed, now only flags genuinely foreign or ETF entities.

---

## Release Process

At the end of each working session:
1. Update `CHANGELOG.md` with all changes under a new version heading.
2. Bump `VERSION` file.
3. Update `STATE.md` (current version, metrics, priorities) — see the end-of-session sequence in `CLAUDE.md`.
4. Commit: `git commit -m "Release vX.Y.Z"`
5. Tag: `git tag -a vX.Y.Z -m "vX.Y.Z — <one-line summary>"`
6. Push: `git push origin main --tags`
7. Deploy on Railway (push to main triggers auto-deploy).
