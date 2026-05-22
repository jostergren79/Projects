# EdgarWolf — Decisions Archive

Settled decisions that no longer need active context. Graduated from the active-decisions list in CLAUDE.md.
Read this only when something breaks or you're re-evaluating infrastructure.

---

## Deployment & Infrastructure

- **Railway:** Migrated from Render free tier. `railway.toml` at repo root, nixpacks build, uvicorn start, /health check. Root Directory in Railway: blank. `requirements.txt` at repo root (`-r edgar-api/requirements.txt`) for nixpacks Python detection. Env vars in Railway Variables panel, not .env.
- **Render decommissioned:** Deleted May 14, 2026. Railway is the only deployment target.
- **Persistent volume:** Mounted at `/app/data`. `DATA_DIR=/app/data` in Railway Variables. SQLite survives redeploys.
- **Cloudflare:** Railway one-click integration manages DNS. Do NOT manually change CNAME proxy status. HTTP challenge handler at `/.well-known/cf-custom-hostname-challenge/{token}` in `main.py`.
- **Canonical domain:** `www.edgarwolf.com` primary. `edgarwolf.com` redirects via Cloudflare. Both added as Railway custom domains. Railway target: `gjkthu0r.up.railway.app`.
- **DNS:** Migrated from GoDaddy direct CNAME → Cloudflare. GoDaddy nameservers point to Cloudflare. Verified and live.

## Email & Notifications

- **Email:** jason@edgarwolf.com via Microsoft 365 + GoDaddy.
- **Resend:** edgarwolf.com DKIM + SPF + MX all verified. FROM = `EdgarWolf <alerts@edgarwolf.com>`. End-to-end tested locally.
- **Pro+ email alerts (v1.4.0):** APScheduler, M–F 08:00–18:00 ET, hourly, max 1 concurrent. Trigger: new 10-Q/10-K/8-K AND at least one anomaly signal (MEDIUM/HIGH z-score OR ELEVATED FSS). Deduped by `(customer_id, cik, accession_number)` in `alert_log`. Dev endpoints 403 in production.

## Stripe

- **Integration:** Checkout, webhook, Customer Portal all live. Webhook at `https://www.edgarwolf.com/webhook/stripe`.
- **Price IDs:** Pro = `price_1TWTJz1C3cijZqBOyfX4VwHC` ($19.00/mo), Pro+ = `price_1TVNfH1C3cijZqBOyp7Y5qJH` ($99/mo). Old $19.99 price archived.
- **Session-based auth:** Stripe session_id + customer_id stored in localStorage, verified against Stripe API on load (cached 1h). Full per-user auth needed long-term.
- **Stale session pattern:** Recurring `/subscription/status` calls on the same `cs_live_` ID = stale browser holding old localStorage, not a new conversion.
- **bfcache fix:** Prevents stuck Loading... buttons after returning from Stripe Checkout.

## Data & Caching

- **Watchlist keyed by CIK:** Ticker unreliable (empty for many EDGAR companies). CIK always present.
- **Server-side watchlist (v1.3.0):** Pro/Pro+ in SQLite (`watchlists` table, keyed by Stripe customer_id). Standard on localStorage. syncWatchlistFromServer() runs once per session.
- **SQLite WAL + threading.Lock:** Thread-safe. Stale cache fallback on SEC outage (serves expired data instead of 502).

## Frontend & Analytics

- **Folder structure:** `notes-api/` → `edgar-frontend/`. `edgar-frontend/public/` flattened. `scripts/` removed.
- **PostHog localhost guard (May 16):** Skips init on `127.0.0.1`/`localhost`/`0.0.0.0`. Pre-existing localhost recordings remain in storage — filter via Settings → Project → Test accounts.
- **`subscription_success` event (May 16):** Fires once per customer on first paid-tier verify. Guarded by `subscription_success_fired` localStorage flag.
- **JSON-LD structured data (May 17, commit 950b3ba):** schema.org SoftwareApplication in edgar.html `<head>`. All three tiers. Google Rich Results confirmed valid within hours.
- **OG image:** 1200×630 PNG at `/og-image.png`. Shows $GIS data. Regenerate with `edgar-api/generate_og_image.py`. Static for now — dynamic per-company is a future item.
- **Digest banner copy (May 16):** Leads with weekly value (ELEVATED stress filings) + 3 concrete receipts ($GIS 100/100, $CAG triple margin, $FIG -58pp op margin).

## Content & Marketing History

- **Legal pages (May 14):** "Jason Ostergren" removed from terms.html and privacy.html. Replaced with "EdgarWolf". Contact email retained.
- **Terminology locked:** Upheaval Score → Filing Stress Score. Anomaly Signals → Filing Signals. Metric Trust & Sources → Data Quality & Sources. Filing Provenance → Source Filing.
- **X reply format:** Lead with most striking filing data point, z-score framing, acknowledge bull/bear fairly, edgarwolf.com at end as earned reference. No em dashes.
- **Reach attribution:** View counts (40K/17K/15K) refer to threads being replied to, not Jason's own posts. Strategy is borrowed audience, not building large personal following.
- **International reach (May 16):** First non-US visit — Germany, $DECK page. Session recording confirmed.
- **Mobile charts (May 16):** Germany user saw empty chart panels. Not universal — edge case (slow CDN, ad-blocker, unusual browser). Defensive fix deferred.
- **Consumer staples sector data (May 17):** $GIS 100/100 ELEVATED (Rev -23% YoY), $CPB 100/100 ELEVATED (Rev -8% YoY), $HRL 87/100 ELEVATED, $CAG 70/100 ELEVATED, $SJM 62/100 MODERATE.
- **$JACK data (May 17, CIK 0000807882):** 92/100 ELEVATED, Net income -$25.9M, EPS -$1.35, Revenue -12.4% YoY, Operating margin 5.0%, XBRL INCOMPLETE, Filing velocity ELEVATED.
- **Major FinTwit engagement (May 17):** Ashton Invests (33.2K), Jonah Lupton (552K), Mike Schiemer (195.5K) all liked posts. 780K+ combined. Do not pitch.
- **Google AI Overview (May 17):** Now leads with "EdgarWolf most commonly refers to a financial intelligence platform" and surfaces edgarwolf.com as first result with OG thumbnail.
- **Sitemap:** Submitted May 13. Status: Success. 1 page discovered.
- **Google Search Console:** Verified via meta tag in edgar.html.
- **robots.txt:** Served via FastAPI route (May 15). Allows all crawlers, points to sitemap.

## QA

- **Postman collection:** `edgar-api/postman/` — 28 requests, 49 assertions. Newman runner: `run_qa.sh [local|production]`.
- **Dev tier toggle:** Amber button in header, localhost only. Toggles Standard/Pro/Pro+ without reload.

## Decisions No Longer Relevant

- **No CRM yet:** Spreadsheet sufficient until 80+ users.
- **No scaling/automation yet:** First 30 days manual. Find 10 paying users by hand.
- **Free tier lookup limit:** Decided to keep unlimited. Differentiation is feature depth only.
- **Signal board is on-demand:** User clicks "Load Signal Board", picks 5–25 per column.
- **Sale target ($500k) not realistic short term.** Near-term goal is income replacement.
- **Vietnamese message to wife (May 17):** Drafted and translated. Optimistic framing.
