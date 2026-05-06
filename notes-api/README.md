# notes-api

This folder currently contains the public-facing static pages for the Notes surface and a smoke script for public mode behavior.

## Tracked Files

- public/edgar.html
- public/index.html
- public/query.html
- public/sop.html
- package.json
- server.js
- scripts/smoke-public-mode.sh

## Local Preview

Serve static pages directly:

```bash
cd notes-api/public
python3 -m http.server 3001
```

Open:

- http://127.0.0.1:3001/index.html
- http://127.0.0.1:3001/edgar.html

Run the lightweight local runtime (used by smoke tests):

```bash
cd notes-api
npm run dev
```

Public-mode smoke check:

```bash
cd notes-api
bash scripts/smoke-public-mode.sh
```

## Generated (Untracked) Artifacts

These are expected locally but should not be committed:

- node_modules/
- dist/
- dist/data/*.db

## Important

The current repository tracks public assets and smoke verification only. If full notes-api runtime source is required in this monorepo, add and document the canonical source files and package manifest before relying on build artifacts.
