#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../wizard"
exec python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8443
