# Changelog

All notable changes to EdgarWolf are documented here.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning follows [Semantic Versioning](https://semver.org/):
- **Major** — breaking changes or complete platform overhauls
- **Minor** — new user-facing features (bumped each session)
- **Patch** — bug fixes and hotfixes between sessions

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
7. Deploy on Render.
