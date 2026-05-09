# Projects Monorepo

This repository contains two app surfaces:

1. edgar-api: FastAPI backend for SEC EDGAR normalized data.
2. notes-api: Public static pages and smoke checks.

The repository is intentionally a single Git repo rooted at this folder.

## Start Here

If you are new to this repo, use this path-based guide:

1. Want EDGAR backend API behavior: start in edgar-api/main.py, then edgar-api/routers/.
2. Want financial metric logic: start in edgar-api/routers/financial_metrics.py.
3. Want anomaly signals or filing cadence logic: start in edgar-api/routers/anomaly_flags.py and edgar-api/routers/company_lookup.py (_build_anomaly_signals).
4. Want the aggregated dashboard endpoint: start in edgar-api/routers/dashboard.py.
5. Want the natural language summary: start in edgar-api/routers/narrative_summary.py.
6. Want public-facing HTML pages: start in notes-api/public/.
7. Want smoke validation for public mode: start in notes-api/scripts/smoke-public-mode.sh.

## Folder Naming Decision

For now, keep top-level folder names as edgar-api and notes-api.

Why:

1. They are already accurate and recognizable.
2. Renaming now creates avoidable path churn across scripts, deploy config, and local muscle memory.
3. The clearer immediate win is navigation documentation, which this README now provides.

If we later rename folders, do it as a planned migration with path updates in one commit and a short compatibility note.

## Current Tracked Scope

The tracked source of truth currently includes:

1. edgar-api application source and deployment config.
2. notes-api public HTML pages.
3. notes-api public-mode smoke script.

Build and machine-local artifacts are intentionally untracked.

## Repository Layout

- edgar-api/: Python API service
- notes-api/public/: static pages served publicly
- notes-api/scripts/: smoke scripts

## Local Setup

### 1) Python service (edgar-api)

From repository root:

```bash
cd edgar-api
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --host 127.0.0.1 --port 8000
```

Health check:

```bash
curl http://127.0.0.1:8000/health
```

### 2) Public pages (notes-api)

If you only need to preview static pages, serve notes-api/public locally:

```bash
cd notes-api/public
python3 -m http.server 3001
```

Then open:

1. http://127.0.0.1:3001/index.html
2. http://127.0.0.1:3001/edgar.html

## Production and Secrets

Use edgar-api/.env.production.example as a template for deployment values.

Never commit real secrets.

## Cleanup Rules

These paths are treated as generated or local and should remain untracked:

1. edgar-api/.venv/
2. edgar-api/data/*.db
3. notes-api/node_modules/
4. notes-api/dist/

## Next Hardening Targets

1. Add a tracked notes-api source manifest and build entrypoint if server-side runtime is required.
2. Add a single top-level launcher script once notes-api runtime source is finalized.
3. Add a clean-room verification checklist (fresh clone to successful local run).