"""Simple Nextcloud integration utilities."""

from __future__ import annotations

import base64
import json
import os
from typing import Dict, Optional
from urllib import request

CONFIG_PATH = os.getenv(
    "WINMIGRATE_NEXTCLOUD_CONFIG",
    os.path.join(os.path.expanduser("~"), ".winmigrate_nextcloud.json"),
)


def _auth_header(username: str, password: str) -> str:
    token = base64.b64encode(f"{username}:{password}".encode()).decode()
    return f"Basic {token}"


def validate_credentials(url: str, username: str, password: str) -> bool:
    """Return ``True`` if the provided credentials are valid."""
    check_url = f"{url.rstrip('/')}/remote.php/dav/files/{username}/"
    req = request.Request(check_url)
    req.add_header("Authorization", _auth_header(username, password))
    try:
        with request.urlopen(req, timeout=10) as resp:
            return 200 <= getattr(resp, "status", 0) < 300
    except Exception:
        return False


def get_storage_usage(url: str, username: str, password: str) -> Dict[str, int]:
    """Return used and available space for the account."""
    info_url = f"{url.rstrip('/')}/ocs/v1.php/cloud/users/{username}?format=json"
    req = request.Request(info_url)
    req.add_header("OCS-APIRequest", "true")
    req.add_header("Authorization", _auth_header(username, password))
    with request.urlopen(req, timeout=10) as resp:
        data = json.load(resp)
    quota = data.get("ocs", {}).get("data", {}).get("quota", {})
    used = int(quota.get("used", 0))
    total = int(quota.get("total", 0))
    return {"used": used, "available": total}


def save_credentials(url: str, username: str, password: str) -> None:
    """Save credentials to ``CONFIG_PATH`` in a basic encoded form."""
    data = {
        "url": url,
        "username": username,
        "password": base64.b64encode(password.encode()).decode(),
    }
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f)


def load_credentials() -> Optional[Dict[str, str]]:
    """Return stored credentials if available."""
    if not os.path.exists(CONFIG_PATH):
        return None
    with open(CONFIG_PATH, encoding="utf-8") as f:
        data = json.load(f)
    data["password"] = base64.b64decode(data["password"]).decode()
    return data
