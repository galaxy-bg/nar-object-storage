#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "install-lab.sh is deprecated. Use install-appliance.sh instead." >&2
exec "${SCRIPT_DIR}/install-appliance.sh" "$@"
