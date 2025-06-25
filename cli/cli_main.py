import argparse
import os

from utils.logger import get_logger
from utils.permissions import copy_with_permissions


def _dir_size(path: str) -> int:
    """Return directory size in bytes."""
    total = 0
    for root, _, files in os.walk(path):
        for f in files:
            fp = os.path.join(root, f)
            try:
                total += os.path.getsize(fp)
            except OSError:
                pass
    return total


def select_directory() -> str | None:
    """Prompt the user to select a directory via text input."""
    while True:
        path = input("Enter directory path (or 'q' to cancel): ").strip().strip('"')
        if path.lower() == 'q' or not path:
            print("No directory selected.")
            return None
        if not os.path.isdir(path):
            print("Directory does not exist. Try again.")
            continue
        size = _dir_size(path)
        print(f"Selected: {path}")
        print(f"Estimated space required: {size} bytes")
        confirm = input("Use this directory? (y/n): ").strip().lower()
        if confirm == 'y':
            return path
        elif confirm == 'n':
            continue
        else:
            print("Canceled.")
            return None

logger = get_logger(__name__)

def run_cli(args=None) -> None:
    """Entry point for the CLI mode."""
    parser = argparse.ArgumentParser(description="WinMigrate CLI")
    parser.add_argument('--option', help='Placeholder option')
    parser.add_argument(
        '--transfer', nargs=2, metavar=('SRC', 'DST'),
        help='Transfer file from SRC to DST'
    )
    parsed_args = parser.parse_args(args)

    logger.info("Running CLI with args: %s", parsed_args)
    print("=== WinMigrate CLI ===")

    if parsed_args.transfer:
        src, dst = parsed_args.transfer
        copy_with_permissions(src, dst, cli=True)
    else:
        path = select_directory()
        if path:
            logger.info("User confirmed directory: %s", path)

if __name__ == '__main__':
    run_cli()
