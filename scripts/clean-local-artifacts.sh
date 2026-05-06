#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Cleaning local artifacts under: ${ROOT_DIR}"

rm -rf "${ROOT_DIR}/edgar-api/.venv"
rm -f "${ROOT_DIR}/edgar-api/data"/*.db
rm -rf "${ROOT_DIR}/notes-api/node_modules"
rm -rf "${ROOT_DIR}/notes-api/dist"

echo "Done."
