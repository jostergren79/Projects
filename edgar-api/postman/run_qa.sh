#!/usr/bin/env bash
# EdgarWolf API QA runner via Newman (Postman CLI)
#
# Usage:
#   ./run_qa.sh           — run against local server (http://127.0.0.1:8000)
#   ./run_qa.sh local     — same as above
#   ./run_qa.sh production — run against https://www.edgarwolf.com
#
# Install Newman once:
#   npm install -g newman

set -euo pipefail
cd "$(dirname "$0")"

ENV=${1:-local}

if ! command -v newman &>/dev/null; then
  echo "ERROR: Newman not found."
  echo "Install it with:  npm install -g newman"
  exit 1
fi

if [ "$ENV" = "production" ]; then
  ENV_FILE="Production.postman_environment.json"
  echo "Running QA against PRODUCTION (https://www.edgarwolf.com)"
  echo "Note: Stripe endpoints require live keys. Checkout happy-path is skipped."
else
  ENV_FILE="Local.postman_environment.json"
  echo "Running QA against LOCAL (http://127.0.0.1:8000)"
  echo "Make sure the server is running:  cd edgar-api && ./dev.sh"
fi

echo ""
newman run EdgarWolf_API.postman_collection.json \
  --environment "$ENV_FILE" \
  --reporters cli,json \
  --reporter-json-export results.json \
  --bail \
  --color on

echo ""
echo "Full results saved to: edgar-api/postman/results.json"
