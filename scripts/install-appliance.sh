#!/usr/bin/env bash
set -euo pipefail

SOURCE_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TARGET_ROOT="${TARGET_ROOT:-/}"
INSTALL_PACKAGES=0
BUILD_WIZARD_IMAGE=1
START_SERVICES=0
NOS_VERSION="${NOS_VERSION:-0.1.0-milestone1}"

usage() {
  cat <<'USAGE'
Usage: install-appliance.sh [options]

Options:
  --install-packages       Install appliance dependencies with dnf on the target VM.
  --no-build-image         Skip Podman wizard image build.
  --start-services         Enable and start kdx-agent and kdx-wizard.
  --help                   Show this help.

Environment:
  TARGET_ROOT=/path        Install into a staged root instead of /.

Examples:
  TARGET_ROOT=/tmp/kdx-rootfs ./scripts/install-appliance.sh
  sudo ./scripts/install-appliance.sh --install-packages --start-services
USAGE
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --install-packages)
      INSTALL_PACKAGES=1
      ;;
    --no-build-image)
      BUILD_WIZARD_IMAGE=0
      ;;
    --start-services)
      START_SERVICES=1
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

install_dir() {
  local path="$1"
  local mode="$2"
  install -d -m "$mode" "${TARGET_ROOT%/}${path}"
}

copy_tree() {
  local src="$1"
  local dest="$2"
  rm -rf "${TARGET_ROOT%/}${dest}"
  install -d -m 0755 "${TARGET_ROOT%/}${dest}"
  cp -a "${SOURCE_ROOT}/${src}/." "${TARGET_ROOT%/}${dest}/"
}

require_root_for_real_install() {
  if [[ "$TARGET_ROOT" == "/" && "$(id -u)" -ne 0 ]]; then
    echo "Run as root for a real appliance install, or set TARGET_ROOT for staging." >&2
    exit 1
  fi
}

install_packages() {
  if [[ "$TARGET_ROOT" != "/" ]]; then
    echo "Package installation skipped for staged TARGET_ROOT=${TARGET_ROOT}."
    return
  fi

  if ! command -v dnf >/dev/null 2>&1; then
    echo "dnf not found. Package installation is only supported on Rocky/RHEL-like systems." >&2
    exit 1
  fi

  dnf install -y git python3 python3-pip ansible-core podman firewalld xfsprogs jq openssl
}

check_real_install_commands() {
  local missing=()
  local command_name

  for command_name in python3 podman systemctl openssl; do
    if ! command -v "$command_name" >/dev/null 2>&1; then
      missing+=("$command_name")
    fi
  done

  if [[ "${#missing[@]}" -gt 0 ]]; then
    echo "Missing commands: ${missing[*]}" >&2
    echo "Run with --install-packages on Rocky Linux 9, or install dependencies manually." >&2
    exit 1
  fi
}

install_agent_python_env() {
  if [[ "$TARGET_ROOT" != "/" ]]; then
    echo "Agent Python environment skipped for staged TARGET_ROOT=${TARGET_ROOT}."
    return
  fi

  python3 -m venv /opt/kronosdx/agent/.venv
  /opt/kronosdx/agent/.venv/bin/python -m pip install --disable-pip-version-check -r /opt/kronosdx/agent/requirements.txt
}

build_wizard_image() {
  if [[ "$BUILD_WIZARD_IMAGE" -eq 0 ]]; then
    echo "Wizard image build skipped."
    return
  fi

  if [[ "$TARGET_ROOT" != "/" ]]; then
    echo "Wizard image build skipped for staged TARGET_ROOT=${TARGET_ROOT}."
    return
  fi

  podman build -t localhost/kdx-wizard:latest /opt/kronosdx/wizard
}

install_systemd_units() {
  cp /opt/kronosdx/systemd/kdx-identity.service /etc/systemd/system/kdx-identity.service
  cp /opt/kronosdx/systemd/kdx-agent.service /etc/systemd/system/kdx-agent.service
  cp /opt/kronosdx/systemd/kdx-wizard.service /etc/systemd/system/kdx-wizard.service
  systemctl daemon-reload
  systemctl enable kdx-identity.service
}

start_services() {
  if [[ "$START_SERVICES" -eq 0 ]]; then
    echo "Services not started. Use --start-services after dependencies and wizard image are ready."
    return
  fi

  systemctl enable kdx-identity.service
  systemctl enable kdx-agent.service
  systemctl enable kdx-wizard.service
  systemctl start kdx-identity.service
  systemctl restart kdx-agent.service
  systemctl restart kdx-wizard.service
  sleep 2
  systemctl --no-pager --full status kdx-agent.service kdx-wizard.service || true
  if command -v ss >/dev/null 2>&1 && ! ss -tln | grep -q ':8443 '; then
    echo "Warning: kdx-wizard is not listening on TCP port 8443 yet. Check journalctl -u kdx-wizard -n 80 --no-pager." >&2
  fi
}

write_version_file() {
  local version_file="${TARGET_ROOT%/}/etc/kronosdx/version.yml"
  local installed_at
  local source_revision="unknown"

  installed_at="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

  if command -v git >/dev/null 2>&1 && [[ -d "${SOURCE_ROOT}/.git" ]]; then
    source_revision="$(git -C "$SOURCE_ROOT" rev-parse --short HEAD 2>/dev/null || printf "unknown")"
  fi

  cat > "$version_file" <<EOF
product: NAR Object Storage
short_name: NOS
version: ${NOS_VERSION}
birth_moment: ${installed_at}
source_revision: ${source_revision}
install_layout: appliance
config_schema: 1
EOF
  chmod 0644 "$version_file"
}

require_root_for_real_install

if [[ "$INSTALL_PACKAGES" -eq 1 ]]; then
  install_packages
fi

if [[ "$TARGET_ROOT" == "/" ]]; then
  check_real_install_commands
fi

echo "Preparing NAR Object Storage appliance layout under ${TARGET_ROOT}"

install_dir /opt/kronosdx 0755
install_dir /etc/kronosdx 0700
install_dir /etc/kronosdx/secrets 0700
install_dir /var/lib/kronosdx 0755
install_dir /var/lib/kronosdx/agent 0750
install_dir /var/lib/kronosdx/wizard 0750
install_dir /var/lib/kronosdx/logs 0750
install_dir /kdx-data 0755

copy_tree ansible /opt/kronosdx/ansible
copy_tree agent /opt/kronosdx/agent
copy_tree wizard /opt/kronosdx/wizard
copy_tree scripts /opt/kronosdx/scripts
copy_tree systemd /opt/kronosdx/systemd
chmod 0755 "${TARGET_ROOT%/}/opt/kronosdx/scripts/"*.sh

install_agent_python_env

KDX_ETC="${TARGET_ROOT%/}/etc/kronosdx" KDX_STATE="${TARGET_ROOT%/}/var/lib/kronosdx" \
  bash "${SOURCE_ROOT}/scripts/initialize-appliance-identity.sh"

write_version_file

if [[ "$TARGET_ROOT" == "/" ]]; then
  install_systemd_units
  build_wizard_image
  start_services
else
  echo "Staging install complete. Systemd installation skipped for TARGET_ROOT=${TARGET_ROOT}."
fi

echo "Challenge key path: ${TARGET_ROOT%/}/etc/kronosdx/challenge.key"
echo "Version file path: ${TARGET_ROOT%/}/etc/kronosdx/version.yml"
