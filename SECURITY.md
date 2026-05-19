# Security Posture

This document describes the security controls in place for EdgarWolf as of **v1.6.0 (2026-05-19)**. It is intended as an honest, current reference — not a marketing claim. Changes and audits are tracked in `CHANGELOG.md`; this document describes the steady state.

---

## 1. Transport & browser

- **HTTPS only.** All traffic terminates at Cloudflare with TLS; HTTP is redirected.
- **HSTS.** `Strict-Transport-Security: max-age=63072000; includeSubDomains` is set on every response — browsers refuse to downgrade to HTTP for two years after first contact.
- **Content Security Policy.** Set via `<meta http-equiv="Content-Security-Policy">` in the frontend HTML. Restricts script and connect sources to a small allowlist (self, jsdelivr CDN for Chart.js, Cloudflare Insights, PostHog endpoints). Note: `'unsafe-inline'` is currently permitted for compatibility with the SPA's inline scripts — output encoding (§2) is the primary XSS control, with CSP as defense-in-depth for third-party resource loading.
- **Clickjacking protection.** `X-Frame-Options: DENY` on every response — the site cannot be embedded in a frame on any other origin.
- **MIME-sniffing protection.** `X-Content-Type-Options: nosniff` on every response.
- **Referrer leakage control.** `Referrer-Policy: strict-origin-when-cross-origin` — full URLs (which contain ticker/CIK query parameters) are never sent to third-party sites.

## 2. API hardening

- **Per-IP rate limiting.** Sliding-window limit of 200 requests/minute per IP on company data, signal-board feed, digest signup, and auth (magic-link request and verify) endpoints. uvicorn is configured with `--proxy-headers --forwarded-allow-ips='*'` so Railway's `X-Forwarded-For` header is honored — the real visitor IP is used for bucketing, not the load balancer.
- **CORS fail-closed.** `CORS_ALLOW_ORIGINS` defaults to empty; cross-origin browser requests are rejected unless an origin is explicitly whitelisted via env var.
- **Input validation at every entrypoint.** CIK parameters are regex-validated (`^\d{1,10}$`) before any database or upstream call. Tickers, names, and search queries are length-bounded and normalized.
- **Parameterized queries everywhere.** All SQLite access uses `?`-placeholder binding. No SQL injection surface.
- **Output encoding.** Frontend HTML interpolation runs through `escapeAttr()` for every value sourced from API responses — including SEC EDGAR fields, computed flags, segment names, provenance metadata, and quarterly table cells. Server-rendered HTML (Pro+ alert emails, the `/success` page) escapes operator-controlled fields (company name, ticker, XBRL concept names, flag notes) via `html.escape` / `_script_safe_json`.

## 3. Payment & subscription security

- **No card data on our servers.** All payment collection happens on Stripe's hosted Checkout. We never see, store, or proxy card numbers, CVCs, expiry dates, or 3DS data.
- **Webhook signature verification.** All Stripe webhook events are verified against `STRIPE_WEBHOOK_SECRET` using `stripe.Webhook.construct_event`. Requests with invalid signatures are rejected with HTTP 400. If the secret is missing, the server **fails closed** with HTTP 500 — there is no path to accept unverified events.
- **Subscription state verified live.** When validating a subscription, the server queries Stripe directly for the active subscription list. The tier is never derived from client-supplied state.
- **Tier gating server-side.** Pro+ features (watchlist read/write, email alerts, billing portal) re-validate the customer's active subscription on every request. Frontend hiding of paid features is cosmetic; enforcement is API-side.
- **Customer lookup uses `stripe.Customer.list(email=...)`**, not `stripe.Customer.search(query=...)`. The search API takes a Lucene-style string; the list API takes a structured email parameter, removing any query-injection surface.

## 4. Authentication & authorization

- **Magic-link sign-in.** Users prove email ownership by clicking a short-lived (15-minute) signed link delivered via Resend. `POST /auth/request` accepts an email, verifies an active Pro/Pro+ subscription on that email via Stripe, mints an HMAC-SHA256 token, and sends the link. The endpoint **always returns `{"ok": true}`** regardless of whether the email matched — silence is the only signal an attacker gets, which prevents customer enumeration.
- **Session cookie.** `GET /auth/verify` validates the magic-link token and sets `ew_session` — an `httpOnly`, `Secure` (in production), `SameSite=Lax`, 30-day cookie containing a separate HMAC-signed session token. Cookies are inaccessible to JavaScript, so XSS cannot exfiltrate the session, and `SameSite=Lax` blocks CSRF on state-changing POSTs while allowing the magic-link click itself.
- **Customer ID never reaches the client.** The Stripe `customer_id` lives only in the signed cookie and in server-side storage. The frontend cannot read it, cannot guess valid IDs, and cannot impersonate another user by replaying one.
- **Token signing.** Magic-link and session tokens are HMAC-SHA256 over a JSON payload (`sub`, `iat`, `exp`, `use`) with `MAGIC_LINK_SECRET`. Signatures are compared with `hmac.compare_digest` (constant-time). Distinct `use` values prevent a session token from being replayed as a magic link or vice versa.
- **Post-checkout cookie issuance.** `GET /success` looks up the Stripe checkout session, confirms it is `complete` with an active subscription, and sets the session cookie before rendering. The frontend never carries the customer_id even briefly.
- **Validation caching.** Active-subscription results cached server-side for 1 hour in SQLite (TTL is server-controlled, not client-controlled) to reduce Stripe API load without weakening verification.
- **No password-based auth.** There are no user accounts with passwords. There are no password hashes to leak, no credential-stuffing surface, no password-reset flow to exploit.

## 5. Data handling

- **Database.** SQLite on a Railway persistent volume. WAL journal mode with a serializing write lock for concurrency safety. The database file is not exposed on any public port — only the API process reads it.
- **PII minimization in analytics.** Behavioral events (PostHog + Railway logs) carry only event names, public company identifiers (ticker, CIK), and tier strings. Email addresses are never attached to behavioral events.
- **Email masking in server logs.** Every `EVENT` log line that previously recorded a full email (`digest_signup`, `subscription_started`, `welcome_email_sent`, `alert_sent`, `magic_link_sent`, `digest_welcome_sent`, `digest_unsubscribe`) now records the masked form `j***@gmail.com`. The domain is preserved for routing analysis; the local part is not. Reduces the blast radius of any Railway log export.
- **Sentry.** Error monitoring is configured with `send_default_pii=False`. Stack traces and request paths are captured; request bodies, user identifiers, and headers are not.
- **Public data only.** The product reads SEC EDGAR — a fully public dataset. There is no proprietary user-generated data beyond watchlist contents (themselves just lists of public company CIKs).

## 6. Dev surface protection

- **Dev test endpoints gated.** `/test/send-alert`, `/test/seed-alert-user`, and `/test/run-alert-check` require either a localhost-origin request OR a `X-Dev-Secret` header matching the `DEV_SECRET` env var. With `--proxy-headers` enabled, external requests can never present as `127.0.0.1`.
- **Debug parameters gated client-side.** The `?debug=true` query parameter (which causes the API to include internal row context and concept-mapping diagnostics) is only sent by the frontend when running on `localhost`/`127.0.0.1`. Production browsers never request it.
- **Dev tier bypass localized.** The `?dev_tier=pro` URL parameter that lets developers preview paid-tier UI only takes effect when the page is served from `localhost`. The production frontend ignores it.

## 7. Secrets management

- **No secrets in source.** All API keys, webhook secrets, and tokens are loaded from environment variables. The repository contains no `.env` file, no hardcoded credentials, and no committed `.envrc`.
- **Railway env vars.** Production secrets (Stripe keys, Resend API key, Sentry DSN, dev secret) live in Railway's environment-variable panel and are injected at runtime.
- **`/config.js` is intentionally minimal.** The only client-side config exposed is `POSTHOG_KEY`, which is a public project key per PostHog's standard model. No server-side secret is ever sent to a browser.

## 8. Operational

- **Sentry** captures unhandled exceptions with sampled distributed tracing.
- **Health endpoint.** `GET /health` reports API and cache status — used by Railway for liveness probes and restart decisions.
- **Failure isolation.** Upstream SEC EDGAR errors (timeout, 4xx, 5xx, rate-limited) are caught at the API boundary and converted to specific 502/503/504 responses with safe detail messages. Stack traces are never returned to clients.
- **Stale-cache fallback.** When SEC EDGAR is unavailable, the API serves stale cached data with appropriate logging — degraded service rather than full outage.

## 9. What we don't do (by design)

- **No user accounts with passwords** — authentication is Stripe-mediated end-to-end.
- **No file uploads** — there is no upload surface to abuse.
- **No arbitrary code execution** — the API reads SEC EDGAR data and runs deterministic Python calculations. No `eval`, no `exec`, no shell-out, no user-supplied templating.
- **No user-generated public content** — there are no comments, profiles, posts, or messages that could carry stored XSS to other users.

---

## Reporting a vulnerability

If you believe you've found a security issue, please email **jason@edgarwolf.com** with details and reproduction steps. Please do not publicly disclose until we've had a chance to investigate and remediate.

We appreciate good-faith research and will respond as quickly as possible.

---

_Last reviewed: 2026-05-19 — v1.6.0_
