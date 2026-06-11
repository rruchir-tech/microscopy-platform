#!/usr/bin/env bash
# MicroCount — build the frontend and run the single-server app (backend serves
# the built SPA). Usage:
#   ./start.sh build   # install deps + build frontend/dist
#   ./start.sh         # run the server on $PORT (default 8000)
set -euo pipefail
cd "$(dirname "$0")"

if [ "${1:-run}" = "build" ]; then
  python -m pip install -r backend/requirements.txt
  npm --prefix frontend install
  npm --prefix frontend run build
  exit 0
fi

exec uvicorn backend.app.main:app --host 0.0.0.0 --port "${PORT:-8000}"
