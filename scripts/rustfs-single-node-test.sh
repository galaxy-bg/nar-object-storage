#!/usr/bin/env bash
set -euo pipefail

IMAGE="${RUSTFS_IMAGE:-rustfs/rustfs:latest}"
DATA_DIR="${RUSTFS_DATA_DIR:-/var/lib/kronosdx/rustfs-single}"
CONTAINER_NAME="${RUSTFS_CONTAINER_NAME:-nos-rustfs-single}"
API_PORT="${RUSTFS_API_PORT:-9000}"
CONSOLE_PORT="${RUSTFS_CONSOLE_PORT:-9001}"
ACCESS_KEY="${RUSTFS_ACCESS_KEY:-rustfsadmin}"
SECRET_KEY="${RUSTFS_SECRET_KEY:-rustfsadmin}"

if ! command -v podman >/dev/null 2>&1; then
  echo "podman is required." >&2
  exit 1
fi

if [[ "$(id -u)" -ne 0 && "$DATA_DIR" == /var/* ]]; then
  echo "Run as root for DATA_DIR=${DATA_DIR}, or set RUSTFS_DATA_DIR to a writable test path." >&2
  exit 1
fi

install -d -m 0750 "$DATA_DIR"

if podman container exists "$CONTAINER_NAME"; then
  podman rm -f "$CONTAINER_NAME" >/dev/null
fi

echo "Starting RustFS single-node test container..."
echo "Image: ${IMAGE}"
echo "Data dir: ${DATA_DIR}"
echo "S3 API: http://127.0.0.1:${API_PORT}"
echo "Console: http://127.0.0.1:${CONSOLE_PORT}"

podman run -d \
  --name "$CONTAINER_NAME" \
  -p "${API_PORT}:9000" \
  -p "${CONSOLE_PORT}:9001" \
  -e RUSTFS_ACCESS_KEY="$ACCESS_KEY" \
  -e RUSTFS_SECRET_KEY="$SECRET_KEY" \
  -e RUSTFS_CONSOLE_ENABLE=true \
  -v "${DATA_DIR}:/data:Z" \
  "$IMAGE" \
  /data

echo
echo "Check logs:"
echo "  podman logs -f ${CONTAINER_NAME}"
echo
echo "Stop test:"
echo "  podman rm -f ${CONTAINER_NAME}"
