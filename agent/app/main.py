import hmac
import json
import os
import subprocess
from pathlib import Path
from typing import Any, Optional

import yaml
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="KronosDX Agent")

KDX_ETC = Path(os.environ.get("KDX_ETC", "/etc/kronosdx"))
KDX_OPT = Path(os.environ.get("KDX_OPT", "/opt/kronosdx"))
KDX_STATE = Path(os.environ.get("KDX_STATE", "/var/lib/kronosdx"))
NAR_CREDENTIALS_FILE = Path(os.environ.get("NAR_CREDENTIALS_FILE", "/etc/kronosdx/secrets/nar-object-storage.env"))
LEGACY_RUSTFS_CREDENTIALS_FILE = Path("/etc/kronosdx/secrets/rustfs.env")


class ChallengeRequest(BaseModel):
    challenge_key: str


class DeployRequest(BaseModel):
    hostname: str
    node_fqdn: str = ""
    admin_user: str = "nosadmin"
    admin_password: str = ""
    management_interface: str
    management_ip: str
    management_prefix: int
    gateway: str
    dns: list[str] = Field(default_factory=list)
    ntp: list[str] = Field(default_factory=list)
    management_vlan_id: Optional[int] = None
    data_network_mode: str = "shared"
    data_interface: str = ""
    data_ip: str = ""
    data_prefix: Optional[int] = None
    data_vlan_id: Optional[int] = None
    cluster_mode: str
    cluster_name: str = ""
    cluster_domain: str = ""
    expected_nodes: Optional[int] = None
    join_endpoint: str = ""
    disks: list[str]


class OperationRequest(BaseModel):
    command_id: str


OPERATION_COMMANDS = {
    "services": {
        "label": "Service status",
        "command": ["systemctl", "status", "kdx-agent.service", "kdx-wizard.service", "rustfs.service", "--no-pager", "--full"],
    },
    "backend-logs": {
        "label": "NAR backend logs",
        "command": ["journalctl", "-u", "rustfs.service", "-n", "160", "--no-pager"],
    },
    "wizard-logs": {
        "label": "Wizard logs",
        "command": ["journalctl", "-u", "kdx-wizard.service", "-n", "120", "--no-pager"],
    },
    "agent-logs": {
        "label": "Agent logs",
        "command": ["journalctl", "-u", "kdx-agent.service", "-n", "120", "--no-pager"],
    },
    "ports": {
        "label": "Listening ports",
        "command": ["ss", "-tlnp"],
    },
    "containers": {
        "label": "Containers",
        "command": ["podman", "ps"],
    },
    "firewall": {
        "label": "Firewall ports",
        "command": ["firewall-cmd", "--list-ports"],
    },
}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/challenge/verify")
def verify_challenge(payload: ChallengeRequest) -> dict[str, bool]:
    challenge_path = KDX_ETC / "challenge.key"
    try:
        expected = challenge_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        return {"valid": False}

    return {"valid": hmac.compare_digest(payload.challenge_key.strip(), expected)}


@app.get("/discover/network")
def discover_network() -> dict[str, list[dict[str, Any]]]:
    data = _run_json(["ip", "-j", "addr", "show"])
    interfaces = []

    for item in data:
        name = item.get("ifname", "")
        if not name or name == "lo":
            continue

        ipv4 = [
            address.get("local")
            for address in item.get("addr_info", [])
            if address.get("family") == "inet" and address.get("local")
        ]
        interfaces.append(
            {
                "name": name,
                "state": item.get("operstate", "UNKNOWN"),
                "mac": item.get("address", ""),
                "ipv4": ipv4,
            }
        )

    return {"interfaces": interfaces}


@app.get("/discover/disks")
def discover_disks() -> dict[str, list[dict[str, Any]]]:
    data = _run_json(
        [
            "lsblk",
            "-J",
            "-b",
            "-o",
            "NAME,PATH,TYPE,SIZE,MODEL,SERIAL,MOUNTPOINTS,RO,RM",
        ]
    )
    disks = []

    for item in data.get("blockdevices", []):
        if item.get("type") != "disk":
            continue
        if item.get("ro") or _has_mountpoint(item):
            continue

        disks.append(
            {
                "name": item.get("name", ""),
                "path": item.get("path", ""),
                "size": item.get("size", 0),
                "model": (item.get("model") or "").strip(),
                "serial": (item.get("serial") or "").strip(),
                "removable": bool(item.get("rm")),
            }
        )

    return {"disks": disks}


@app.get("/config")
def read_config() -> dict[str, str]:
    config_path = KDX_ETC / "config.yml"
    try:
        raw_content = config_path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return {"path": str(config_path), "content": ""}

    content = _redacted_config(raw_content)
    return {"path": str(config_path), "content": content}


@app.get("/status")
def appliance_status() -> dict[str, Any]:
    config_path = KDX_ETC / "config.yml"
    firstboot_path = KDX_ETC / "firstboot.state"
    config = _read_yaml_file(config_path)
    bind_ip = _backend_bind_ip(config)
    credential_path = NAR_CREDENTIALS_FILE if NAR_CREDENTIALS_FILE.exists() else LEGACY_RUSTFS_CREDENTIALS_FILE
    credentials = _read_env_file(credential_path)

    return {
        "product": "NAR Object Storage",
        "configured": firstboot_path.read_text(encoding="utf-8").strip() == "configured"
        if firstboot_path.exists()
        else False,
        "config_path": str(config_path),
        "credentials_path": str(credential_path),
        "access_key": credentials.get("RUSTFS_ACCESS_KEY", "nosadmin"),
        "api_url": f"http://{bind_ip}:9000" if bind_ip else "",
        "console_url": f"http://{bind_ip}:9001" if bind_ip else "",
        "backend_service": "rustfs.service",
    }


@app.get("/ops/commands")
def operation_commands() -> dict[str, list[dict[str, str]]]:
    commands = [
        {"id": command_id, "label": str(details["label"])}
        for command_id, details in OPERATION_COMMANDS.items()
    ]
    commands.extend(
        [
            {"id": "deploy-log", "label": "Deploy log"},
            {"id": "storage-plan", "label": "Storage plan"},
            {"id": "config", "label": "Redacted config"},
            {"id": "credentials-info", "label": "Credential file"},
        ]
    )
    return {"commands": commands}


@app.get("/ops/deploy-log")
def deploy_log() -> dict[str, str]:
    log_path = KDX_STATE / "last-deploy.log"
    return {
        "label": "Deploy log",
        "path": str(log_path),
        "output": _tail_file(log_path),
    }


@app.post("/ops/run")
def run_operation(payload: OperationRequest) -> dict[str, Any]:
    command_id = payload.command_id.strip()
    if command_id == "deploy-log":
        result = deploy_log()
        result.update({"command": f"tail -n 240 {result['path']}", "returncode": 0})
        return result
    if command_id == "storage-plan":
        path = KDX_STATE / "storage-plan.yml"
        return {
            "label": "Storage plan",
            "command": f"cat {path}",
            "path": str(path),
            "returncode": 0,
            "output": _tail_file(path, lines=240),
        }
    if command_id == "config":
        path = KDX_ETC / "config.yml"
        try:
            output = _redacted_config(path.read_text(encoding="utf-8"))
        except FileNotFoundError:
            output = "Config has not been written yet."
        return {
            "label": "Redacted config",
            "command": f"cat {path}",
            "path": str(path),
            "returncode": 0,
            "output": output,
        }
    if command_id == "credentials-info":
        credential_path = NAR_CREDENTIALS_FILE if NAR_CREDENTIALS_FILE.exists() else LEGACY_RUSTFS_CREDENTIALS_FILE
        credentials = _read_env_file(credential_path)
        access_key = credentials.get("RUSTFS_ACCESS_KEY", "not available")
        return {
            "label": "Credential file",
            "command": f"stat {credential_path}",
            "path": str(credential_path),
            "returncode": 0,
            "output": (
                f"Path: {credential_path}\n"
                f"Access key: {access_key}\n"
                "Secret key: stored in the file on the appliance; not displayed in the web terminal.\n"
            ),
        }

    details = OPERATION_COMMANDS.get(command_id)
    if details is None:
        raise HTTPException(status_code=400, detail="Unsupported operation command.")

    command = list(details["command"])
    result = _run_text(command)
    return {
        "label": details["label"],
        "command": " ".join(command),
        "returncode": result.returncode,
        "output": (result.stdout + result.stderr).strip() or "No output.",
    }


@app.post("/deploy")
def deploy(payload: DeployRequest) -> dict[str, Any]:
    config = _deployment_config(payload)
    config_path = KDX_ETC / "config.yml"
    KDX_ETC.mkdir(parents=True, exist_ok=True)
    config_path.write_text(yaml.safe_dump(config, sort_keys=False), encoding="utf-8")
    config_path.chmod(0o600)

    KDX_STATE.mkdir(parents=True, exist_ok=True)
    try:
        result = subprocess.run(
            [
                "ansible-playbook",
                "-i",
                str(KDX_OPT / "ansible/inventory/localhost.ini"),
                str(KDX_OPT / "ansible/site.yml"),
            ],
            capture_output=True,
            text=True,
        )
        returncode = result.returncode
        stdout = result.stdout
        stderr = result.stderr
    except FileNotFoundError as exc:
        returncode = 127
        stdout = ""
        stderr = str(exc)

    log_path = KDX_STATE / "last-deploy.log"
    log_path.write_text(stdout + stderr, encoding="utf-8")
    if returncode == 0:
        (KDX_ETC / "firstboot.state").write_text("configured\n", encoding="utf-8")

    return {
        "ok": returncode == 0,
        "returncode": returncode,
        "config_path": str(config_path),
        "log_path": str(log_path),
        "stdout": stdout,
        "stderr": stderr,
    }


def _run_json(command: list[str]) -> Any:
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def _run_text(command: list[str]) -> subprocess.CompletedProcess[str]:
    try:
        return subprocess.run(command, capture_output=True, text=True, timeout=12)
    except FileNotFoundError as exc:
        return subprocess.CompletedProcess(command, 127, "", str(exc))
    except subprocess.TimeoutExpired as exc:
        output = (exc.stdout or "") + (exc.stderr or "")
        return subprocess.CompletedProcess(command, 124, str(output), "Command timed out.")


def _tail_file(path: Path, lines: int = 240) -> str:
    try:
        content = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except FileNotFoundError:
        return f"{path} does not exist yet."
    return "\n".join(content[-lines:]) or "File is empty."


def _has_mountpoint(device: dict[str, Any]) -> bool:
    mountpoints = device.get("mountpoints") or []
    if any(mountpoints):
        return True

    return any(_has_mountpoint(child) for child in device.get("children", []))


def _deployment_config(payload: DeployRequest) -> dict[str, Any]:
    data_network_separate = payload.data_network_mode == "separate"
    admin_password_hash = _hash_password(payload.admin_password) if payload.admin_password else None
    return {
        "appliance": {
            "hostname": payload.hostname,
            "fqdn": payload.node_fqdn or None,
            "admin_user": payload.admin_user,
        },
        "network": {
            "management": {
                "interface": payload.management_interface,
                "ip": payload.management_ip,
                "prefix": payload.management_prefix,
                "gateway": payload.gateway,
                "dns": payload.dns,
                "ntp": payload.ntp,
                "vlan_id": payload.management_vlan_id,
            },
            "data": {
                "mode": payload.data_network_mode,
                "interface": payload.data_interface if data_network_separate else None,
                "ip": payload.data_ip if data_network_separate else None,
                "prefix": payload.data_prefix if data_network_separate else None,
                "gateway": None,
                "vlan_id": payload.data_vlan_id if data_network_separate else None,
            },
        },
        "cluster": {
            "mode": payload.cluster_mode,
            "name": payload.cluster_name or None,
            "domain": payload.cluster_domain or None,
            "endpoint": None,
            "expected_nodes": payload.expected_nodes,
            "join_endpoint": payload.join_endpoint or None,
            "join_token_file": None,
        },
        "storage": {
            "disks": payload.disks,
            "wipe_confirmed": True,
        },
        "security": {
            "admin_password_hash": admin_password_hash,
            "mfa_enabled": False,
        },
    }


def _hash_password(password: str) -> str:
    result = subprocess.run(
        ["openssl", "passwd", "-6", "-stdin"],
        input=password,
        capture_output=True,
        check=True,
        text=True,
    )
    return result.stdout.strip()


def _redacted_config(content: str) -> str:
    try:
        config = yaml.safe_load(content) or {}
        security = config.get("security", {})
        if "admin_password_hash" in security:
            security["admin_password_hash"] = "<redacted>"
        return yaml.safe_dump(config, sort_keys=False)
    except yaml.YAMLError:
        return content


def _read_yaml_file(path: Path) -> dict[str, Any]:
    try:
        return yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except (FileNotFoundError, yaml.YAMLError):
        return {}


def _backend_bind_ip(config: dict[str, Any]) -> str:
    network = config.get("network", {})
    data = network.get("data", {})
    management = network.get("management", {})
    if data.get("mode") == "separate" and data.get("ip"):
        return str(data["ip"])
    return str(management.get("ip", ""))


def _read_env_file(path: Path) -> dict[str, str]:
    values = {}
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    except FileNotFoundError:
        pass
    return values
