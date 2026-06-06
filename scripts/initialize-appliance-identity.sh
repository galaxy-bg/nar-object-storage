#!/usr/bin/env bash
set -euo pipefail

KDX_ETC="${KDX_ETC:-/etc/kronosdx}"
KDX_STATE="${KDX_STATE:-/var/lib/kronosdx}"

install_secret() {
  local path="$1"
  local bytes="$2"

  if [[ -f "$path" ]]; then
    return
  fi

  openssl rand -hex "$bytes" > "$path"
  chmod 0600 "$path"
}

install -d -m 0700 "$KDX_ETC"
install -d -m 0700 "${KDX_ETC}/secrets"
install -d -m 0755 "$KDX_STATE"
install -d -m 0750 "${KDX_STATE}/logs"

install_secret "${KDX_ETC}/challenge.key" 16
install_secret "${KDX_ETC}/secrets/agent.token" 32
install_secret "${KDX_ETC}/secrets/maintenance.key" 32

if [[ ! -f "${KDX_ETC}/firstboot.state" ]]; then
  printf "pending\n" > "${KDX_ETC}/firstboot.state"
  chmod 0600 "${KDX_ETC}/firstboot.state"
fi
