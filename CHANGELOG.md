# Changelog

All notable changes to EdgarWolf are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/):
- **Major** — breaking changes or complete platform overhauls
- **Minor** — new user-facing features (bumped each session)
- **Patch** — bug fixes and hotfixes between sessions

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
3. Add version to `CLAUDE_CONTEXT.md` (top of doc, Current Version field).
4. Commit: `git commit -m "Release vX.Y.Z"`
5. Tag: `git tag -a vX.Y.Z -m "vX.Y.Z — <one-line summary>"`
6. Push: `git push origin main --tags`
7. Deploy on Railway (push to main triggers auto-deploy).
