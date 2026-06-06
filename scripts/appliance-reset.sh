#!/usr/bin/env bash
set -euo pipefail

KDX_ETC="${KDX_ETC:-/etc/kronosdx}"
KDX_STATE="${KDX_STATE:-/var/lib/kronosdx}"
KDX_DATA_ROOT="${KDX_DATA_ROOT:-/kdx-data}"
CONFIRM_PHRASE="RESET NAR OBJECT STORAGE"
DESTROY_DATA=0
CONFIG_ONLY=0
CONFIRM_VALUE=""

usage() {
  cat <<'USAGE'
Usage: appliance-reset.sh [--config-only | --destroy-data --confirm "RESET NAR OBJECT STORAGE"]

Modes:
  --config-only       Reset first-boot config and logs. Storage data is preserved.
  --destroy-data      Stop the backend and remove NAR Object Storage data and secrets.

Safety:
  --destroy-data requires:
    --confirm "RESET NAR OBJECT STORAGE"

Environment:
  KDX_ETC=/path       Default: /etc/kronosdx
  KDX_STATE=/path     Default: /var/lib/kronosdx
  KDX_DATA_ROOT=/path Default: /kdx-data
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

stop_backend() {
  run_optional systemctl stop rustfs.service
  run_optional systemctl disable rustfs.service
  if command -v podman >/dev/null 2>&1; then
    run_optional podman rm -f nar-object-storage
    run_optional podman rm -f rustfs
  fi
}

reset_config_state() {
  rm -f "${KDX_ETC}/config.yml"
  rm -f "${KDX_ETC}/firstboot.state"
  rm -f "${KDX_STATE}/last-deploy.log"
  rm -f "${KDX_STATE}/storage-plan.yml"
  rm -f "${KDX_STATE}/logs/"*.log

  rm -f "${KDX_ETC}/challenge.key"
  KDX_ETC="$KDX_ETC" KDX_STATE="$KDX_STATE" /opt/kronosdx/scripts/initialize-appliance-identity.sh
}

storage_mountpoints() {
  if [[ -f "${KDX_STATE}/storage-plan.yml" ]]; then
    awk '/^[[:space:]]*mount: / {print $2}' "${KDX_STATE}/storage-plan.yml"
  fi
  find "$KDX_DATA_ROOT" -maxdepth 1 -type d -name 'disk[0-9][0-9]' 2>/dev/null | sort
}

remove_fstab_entries() {
  if [[ ! -f /etc/fstab ]]; then
    return
  fi
  awk -v root="$KDX_DATA_ROOT" '$2 !~ "^" root "/disk[0-9][0-9]$" {print}' /etc/fstab > /etc/fstab.kdx-reset
  cat /etc/fstab.kdx-reset > /etc/fstab
  rm -f /etc/fstab.kdx-reset
}

destroy_data() {
  local mountpoint

  stop_backend

  while read -r mountpoint; do
    [[ -n "$mountpoint" ]] || continue
    rm -rf "${mountpoint}/rustfs"
    if command -v findmnt >/dev/null 2>&1 && findmnt --mountpoint "$mountpoint" >/dev/null 2>&1; then
      run_optional umount "$mountpoint"
    fi
  done < <(storage_mountpoints)

  rm -rf "${KDX_STATE}/rustfs-single"
  rm -f "${KDX_ETC}/secrets/nar-object-storage.env"
  rm -f "${KDX_ETC}/secrets/rustfs.env"
  remove_fstab_entries
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --config-only)
      CONFIG_ONLY=1
      ;;
    --destroy-data)
      DESTROY_DATA=1
      ;;
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

if [[ "$CONFIG_ONLY" -eq "$DESTROY_DATA" ]]; then
  echo "Choose exactly one mode: --config-only or --destroy-data." >&2
  usage >&2
  exit 1
fi

if [[ "$DESTROY_DATA" -eq 1 && "$CONFIRM_VALUE" != "$CONFIRM_PHRASE" ]]; then
  echo "Refusing destructive reset. Re-run with: --confirm \"${CONFIRM_PHRASE}\"" >&2
  exit 1
fi

stop_backend

if [[ "$DESTROY_DATA" -eq 1 ]]; then
  destroy_data
fi

reset_config_state
run_optional systemctl restart kdx-agent.service
run_optional systemctl restart kdx-wizard.service

echo "Appliance reset complete."
echo "Challenge key path: ${KDX_ETC}/challenge.key"
