#!/usr/bin/env bash
set -euo pipefail

NODES="${RUSTFS_NODES:-node1,node2,node3,node4}"
DISKS_PER_NODE="${RUSTFS_DISKS_PER_NODE:-4}"
PORT="${RUSTFS_PORT:-9000}"
DATA_PREFIX="${RUSTFS_DATA_PREFIX:-/data/rustfs}"

IFS=',' read -r -a NODE_ARRAY <<< "$NODES"

if [[ "${#NODE_ARRAY[@]}" -lt 4 ]]; then
  echo "RustFS distributed planning should use at least 4 nodes for the baseline test." >&2
  exit 1
fi

if [[ "$DISKS_PER_NODE" -lt 1 ]]; then
  echo "RUSTFS_DISKS_PER_NODE must be at least 1." >&2
  exit 1
fi

volumes=()
for node in "${NODE_ARRAY[@]}"; do
  for ((disk = 0; disk < DISKS_PER_NODE; disk++)); do
    volumes+=("http://${node}:${PORT}${DATA_PREFIX}${disk}")
  done
done

volume_expression="$(IFS=' '; echo "${volumes[*]}")"

cat <<EOF
RustFS multi-node planning output

Nodes:
  ${NODES}

Disks per node:
  ${DISKS_PER_NODE}

Port:
  ${PORT}

Per-node directory plan:
EOF

for node in "${NODE_ARRAY[@]}"; do
  echo "  ${node}:"
  for ((disk = 0; disk < DISKS_PER_NODE; disk++)); do
    echo "    ${DATA_PREFIX}${disk}"
  done
done

cat <<EOF

Environment draft:

RUSTFS_VOLUMES="${volume_expression}"
RUSTFS_ADDRESS=":${PORT}"
RUSTFS_CONSOLE_ENABLE=true
RUST_LOG=error

Notes:
- This script does not install or start RustFS.
- Ensure DNS or /etc/hosts resolves every node name on every node.
- Ensure time synchronization is active on every node.
- Ensure each storage path is backed by the intended XFS disk mount.
EOF
