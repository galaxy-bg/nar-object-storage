import hmac
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="KronosDX Agent")

KDX_ETC = Path(os.environ.get("KDX_ETC", "/etc/kronosdx"))


class ChallengeRequest(BaseModel):
    challenge_key: str


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


def _run_json(command: list[str]) -> Any:
    result = subprocess.run(command, check=True, capture_output=True, text=True)
    return json.loads(result.stdout)


def _has_mountpoint(device: dict[str, Any]) -> bool:
    mountpoints = device.get("mountpoints") or []
    if any(mountpoints):
        return True

    return any(_has_mountpoint(child) for child in device.get("children", []))
