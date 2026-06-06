#!/usr/bin/env bash
set -euo pipefail

KDX_ETC="${KDX_ETC:-/etc/kronosdx}"
CHALLENGE_KEY_FILE="${KDX_ETC}/challenge.key"
MAINTENANCE_KEY_FILE="${KDX_ETC}/secrets/maintenance.key"
VERSION_FILE="${KDX_ETC}/version.yml"
RESET_SCRIPT="/opt/kronosdx/scripts/appliance-reset.sh"
GOLDEN_IMAGE_SCRIPT="/opt/kronosdx/scripts/prepare-golden-image.sh"

require_root() {
  if [[ "$(id -u)" -ne 0 ]]; then
    echo "Run as root from the appliance console." >&2
    exit 1
  fi
}

read_secret_file() {
  local path="$1"
  if [[ ! -f "$path" ]]; then
    echo "Missing required file: ${path}" >&2
    exit 1
  fi
  cat "$path"
}

show_version() {
  if [[ -f "$VERSION_FILE" ]]; then
    cat "$VERSION_FILE"
  else
    echo "Version file not found: ${VERSION_FILE}"
  fi
}

show_first_boot_challenge() {
  echo "First-boot challenge key:"
  read_secret_file "$CHALLENGE_KEY_FILE"
}

generate_maintenance_response() {
  local key
  local challenge
  local response

  key="$(read_secret_file "$MAINTENANCE_KEY_FILE")"
  challenge="$(openssl rand -hex 16)"
  response="$(printf "%s" "$challenge" | openssl dgst -sha256 -hmac "$key" -hex | awk '{print $2}')"

  cat <<EOF
Maintenance challenge:
  ${challenge}

Maintenance response:
  ${response}

Use this response only from a trusted local console workflow.
EOF
}

disabled_action() {
  local action="$1"
  cat <<EOF
${action} is not enabled in this milestone.

Planned controls:
- local console only
- challenge/response verification
- explicit confirmation phrase
- audited kdx-agent action
EOF
}

factory_reset_menu() {
  cat <<EOF
Factory reset options:

Config-only reset:
  ${RESET_SCRIPT} --config-only

Destroy NAR Object Storage data and reset:
  ${RESET_SCRIPT} --destroy-data --confirm "RESET NAR OBJECT STORAGE"

Run these commands only from a trusted local console.
EOF
}

golden_image_menu() {
  cat <<EOF
Golden image preparation:

  ${GOLDEN_IMAGE_SCRIPT} --confirm "PREPARE NAR GOLDEN IMAGE"

Run this immediately before shutting down the VM and converting it to a template.
EOF
}

menu() {
  cat <<'EOF'
NAR Object Storage Console

1. Show version information
2. Show first-boot challenge key
3. Generate maintenance challenge response
4. Factory reset appliance
5. Prepare golden image
6. Reset root password (disabled)
0. Exit
EOF
}

require_root

while true; do
  menu
  printf "\nSelect: "
  read -r choice
  echo

  case "$choice" in
    1) show_version ;;
    2) show_first_boot_challenge ;;
    3) generate_maintenance_response ;;
    4) factory_reset_menu ;;
    5) golden_image_menu ;;
    6) disabled_action "Root password reset" ;;
    0) exit 0 ;;
    *) echo "Invalid selection." ;;
  esac
  echo
done
