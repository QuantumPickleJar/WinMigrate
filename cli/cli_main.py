import argparse
import getpass
import os
import shutil

from utils.logger import get_logger
from utils import nextcloud

logger = get_logger(__name__)

def link_nextcloud_cli() -> None:
    """Interactively link a Nextcloud account."""
    url = input("Nextcloud URL: ").strip()
    username = input("Username: ").strip()
    password = getpass.getpass("Password or app token: ")
    if nextcloud.validate_credentials(url, username, password):
        nextcloud.save_credentials(url, username, password)
        usage = nextcloud.get_storage_usage(url, username, password)
        print(
            f"Linked {username}. Used {usage['used']} of {usage['available']} bytes."
        )
    else:
        print("Failed to validate Nextcloud credentials.")


def run_cli(args=None) -> None:
    """Entry point for the CLI mode."""
    parser = argparse.ArgumentParser(description="WinMigrate CLI")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("link-nextcloud", help="Link a Nextcloud account")
    parser.add_argument("--option", help="Placeholder option")
    parsed_args = parser.parse_args(args)

    logger.info("Running CLI with args: %s", parsed_args)
    if parsed_args.command == "link-nextcloud":
        link_nextcloud_cli()
        return
    print("=== WinMigrate CLI ===")
    print("Transfer options will be available in future versions.")


def transfer(src_dir: str, dst_dir: str) -> None:
    """Copy all files from ``src_dir`` into ``dst_dir``."""
    if not os.path.exists(dst_dir):
        os.makedirs(dst_dir, exist_ok=True)
    for root, _, files in os.walk(src_dir):
        rel_root = os.path.relpath(root, src_dir)
        dest_root = os.path.join(dst_dir, rel_root)
        os.makedirs(dest_root, exist_ok=True)
        for name in files:
            shutil.copy2(os.path.join(root, name), os.path.join(dest_root, name))

if __name__ == '__main__':
    run_cli()
