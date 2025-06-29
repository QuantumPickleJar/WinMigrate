import json
import os
from unittest import mock

import utils.nextcloud as nc


def test_save_and_load_credentials(tmp_path):
    path = tmp_path / "creds.json"
    with mock.patch.dict(os.environ, {"WINMIGRATE_NEXTCLOUD_CONFIG": str(path)}):
        with mock.patch.object(nc, "CONFIG_PATH", str(path)):
            nc.save_credentials("https://server", "alice", "secret")
            data = nc.load_credentials()
        assert data == {
            "url": "https://server",
            "username": "alice",
            "password": "secret",
        }


def test_validate_credentials_success():
    resp = mock.MagicMock()
    resp.__enter__.return_value = resp
    resp.status = 200
    with mock.patch("urllib.request.urlopen", return_value=resp):
        assert nc.validate_credentials("https://s", "user", "pass")


def test_get_storage_usage_parses_quota():
    sample = {"ocs": {"data": {"quota": {"used": 10, "total": 20}}}}
    resp = mock.MagicMock()
    resp.__enter__.return_value = resp
    resp.read.return_value = json.dumps(sample).encode()
    with mock.patch("urllib.request.urlopen", return_value=resp):
        usage = nc.get_storage_usage("https://s", "user", "pass")
        assert usage == {"used": 10, "available": 20}


def test_load_credentials_missing(tmp_path):
    path = tmp_path / "creds.json"
    with mock.patch.dict(os.environ, {"WINMIGRATE_NEXTCLOUD_CONFIG": str(path)}):
        with mock.patch.object(nc, "CONFIG_PATH", str(path)):
            assert nc.load_credentials() is None
