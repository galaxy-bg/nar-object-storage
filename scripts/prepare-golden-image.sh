#!/usr/bin/env bash
set -euo pipefail

KDX_ETC="${KDX_ETC:-/etc/kronosdx}"
KDX_STATE="${KDX_STATE:-/var/lib/kronosdx}"
CONFIRM_PHRASE="PREPARE NAR GOLDEN IMAGE"
CONFIRM_VALUE=""

usage() {
  cat <<'USAGE'
Usage: prepare-golden-image.sh --confirm "PREPARE NAR GOLDEN IMAGE"

Prepares a clone-safe NAR Object Storage golden image by removing node-specific
identity, secrets, runtime state, containers, logs, SSH host keys, and machine-id.

The installed code, Python environment, systemd units, and wizard image are kept.
Shutdown the VM after this script completes, then convert it to a template.
USAGE
}

require_root() {
  if [[ "$(id -u)" -ne 0 ]]; then
    echo "Run as root from the appliance console." >&2
    exit 1
  fi
}

run_optional() {
  "$@" >/dev/null 2>&1 || true
}

storage_mountpoints() {
  if [[ -f "${KDX_STATE}/storage-plan.yml" ]]; then
    awk '/^[[:space:]]*mount: / {print $2}' "${KDX_STATE}/storage-plan.yml"
  fi
  find /kdx-data -maxdepth 1 -type d -name 'disk[0-9][0-9]' 2>/dev/null | sort
}

remove_fstab_entries() {
  if [[ ! -f /etc/fstab ]]; then
    return
  fi
  awk '$2 !~ "^/kdx-data/disk[0-9][0-9]$" {print}' /etc/fstab > /etc/fstab.kdx-golden
  cat /etc/fstab.kdx-golden > /etc/fstab
  rm -f /etc/fstab.kdx-golden
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --confirm)
      if [[ $# -lt 2 ]]; then
        echo "--confirm requires a value." >&2
        exit 1
      fi
      CONFIRM_VALUE="${2:-}"
      shift
      ;;
    --help)
      usage
      exit 0
      ;;
    *)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 1
      ;;
  esac
  shift
done

require_root

if [[ "$CONFIRM_VALUE" != "$CONFIRM_PHRASE" ]]; then
  echo "Refusing golden image preparation. Re-run with: --confirm \"${CONFIRM_PHRASE}\"" >&2
  exit 1
fi

run_optional systemctl stop rustfs.service
run_optional systemctl stop kdx-wizard.service
run_optional systemctl stop kdx-agent.service

if command -v podman >/dev/null 2>&1; then
  run_optional podman rm -f kdx-wizard
  run_optional podman rm -f nar-object-storage
  run_optional podman rm -f rustfs
fi

rm -f "${KDX_ETC}/config.yml"
rm -f "${KDX_ETC}/firstboot.state"
rm -f "${KDX_ETC}/challenge.key"
rm -f "${KDX_ETC}/secrets/agent.token"
rm -f "${KDX_ETC}/secrets/maintenance.key"
rm -f "${KDX_ETC}/secrets/nar-object-storage.env"
rm -f "${KDX_ETC}/secrets/rustfs.env"
rm -f "${KDX_STATE}/last-deploy.log"
rm -f "${KDX_STATE}/storage-plan.yml"
rm -f "${KDX_STATE}/logs/"*.log
rm -rf "${KDX_STATE}/rustfs-single"

while read -r mountpoint; do
  [[ -n "$mountpoint" ]] || continue
  rm -rf "${mountpoint}/rustfs"
  if command -v findmnt >/dev/null 2>&1 && findmnt --mountpoint "$mountpoint" >/dev/null 2>&1; then
    run_optional umount "$mountpoint"
  fi
done < <(storage_mountpoints)
remove_fstab_entries

rm -f /etc/ssh/ssh_host_*_key
rm -f /etc/ssh/ssh_host_*_key.pub

if [[ -f /etc/machine-id ]]; then
  : > /etc/machine-id
fi
rm -f /var/lib/dbus/machine-id

rm -f /root/.bash_history
find /home -maxdepth 2 -name .bash_history -type f -delete 2>/dev/null || true

if command -v journalctl >/dev/null 2>&1; then
  run_optional journalctl --rotate
  run_optional journalctl --vacuum-time=1s
fi

run_optional systemctl disable rustfs.service
run_optional systemctl enable kdx-identity.service
run_optional systemctl enable kdx-agent.service
run_optional systemctl enable kdx-wizard.service

cat <<EOF
Golden image preparation complete.

Next steps:
1. Shutdown this VM now.
2. Convert it to a template/golden image.
3. On cloned VMs, kdx-identity.service will regenerate appliance identity on boot.
EOF
