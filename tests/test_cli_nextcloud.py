import builtins
from unittest import mock

import cli.cli_main as cm


def test_link_nextcloud_cli_success():
    with mock.patch.object(
        cm, "input", side_effect=["https://example.com", "alice"]
    ), mock.patch.object(
        cm.getpass, "getpass", return_value="token"
    ), mock.patch.object(
        cm.nextcloud, "validate_credentials", return_value=True
    ) as m_valid, mock.patch.object(
        cm.nextcloud,
        "get_storage_usage",
        return_value={"used": 1, "available": 2},
    ) as m_usage, mock.patch.object(
        cm.nextcloud, "save_credentials"
    ) as m_save, mock.patch.object(builtins, "print") as m_print:
        cm.link_nextcloud_cli()
        m_valid.assert_called_once_with("https://example.com", "alice", "token")
        m_save.assert_called_once_with("https://example.com", "alice", "token")
        m_usage.assert_called_once()
        m_print.assert_any_call("Linked alice. Used 1 of 2 bytes.")
