import hmac
import json
import os
import subprocess
from pathlib import Path
from typing import Any

import yaml
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="KronosDX Agent")

KDX_ETC = Path(os.environ.get("KDX_ETC", "/etc/kronosdx"))
KDX_OPT = Path(os.environ.get("KDX_OPT", "/opt/kronosdx"))
KDX_STATE = Path(os.environ.get("KDX_STATE", "/var/lib/kronosdx"))


class ChallengeRequest(BaseModel):
    challenge_key: str


class DeployRequest(BaseModel):
    hostname: str
    node_fqdn: str = ""
    admin_user: str = "nosadmin"
    management_interface: str
    management_ip: str
    management_prefix: int
    gateway: str
    dns: list[str] = Field(default_factory=list)
    ntp: list[str] = Field(default_factory=list)
    management_vlan_id: int | None = None
    data_network_mode: str = "shared"
    data_interface: str = ""
    data_ip: str = ""
    data_prefix: int | None = None
    data_vlan_id: int | None = None
    cluster_mode: str
    cluster_name: str = ""
    cluster_domain: str = ""
    expected_nodes: int | None = None
    join_endpoint: str = ""
    disks: list[str]


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


def _has_mountpoint(device: dict[str, Any]) -> bool:
    mountpoints = device.get("mountpoints") or []
    if any(mountpoints):
        return True

    return any(_has_mountpoint(child) for child in device.get("children", []))


def _deployment_config(payload: DeployRequest) -> dict[str, Any]:
    data_network_separate = payload.data_network_mode == "separate"
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
            "mfa_enabled": False,
        },
    }
