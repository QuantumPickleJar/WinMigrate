import argparse
import os
import sys
import time

from utils import programs

from utils.logger import get_logger
from utils.transfer import copy_file_resumable
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


def _print_progress(copied: int, total: int, start: float) -> None:
    """Print a simple progress bar to stdout."""
    percent = copied / total * 100 if total else 100
    bar_len = 30
    filled = int(bar_len * percent / 100)
    bar = '#' * filled + '-' * (bar_len - filled)
    speed = copied / max(time.time() - start, 1e-3)
    eta = (total - copied) / speed if speed > 0 else 0
    msg = f"\r[{bar}] {percent:5.1f}% {copied}/{total} bytes ETA {eta:0.1f}s"
    sys.stdout.write(msg)
    sys.stdout.flush()

def run_cli(args=None) -> None:
    """Entry point for the CLI mode."""
    parser = argparse.ArgumentParser(description="WinMigrate CLI")
    parser.add_argument('--option', help='Placeholder option')
    parser.add_argument(
        '--transfer', nargs=2, metavar=('SRC', 'DST'),
        help='Transfer file from SRC to DST'
    )
    parser.add_argument(
        '--installed-report', nargs='?', metavar='DIR', const='',
        help='Generate installed programs report in DIR (prompt if omitted)'
    )
    parsed_args = parser.parse_args(args)

    logger.info("Running CLI with args: %s", parsed_args)
    print("=== WinMigrate CLI ===")

    if parsed_args.installed_report is not None:
        output_dir = parsed_args.installed_report
        if not output_dir:
            output_dir = input('Enter output directory for report: ').strip()
        if output_dir:
            path = programs.generate_report(output_dir)
            print(f'Report generated at {path}')
    elif parsed_args.transfer:
        src, dst = parsed_args.transfer
        start = time.time()
        progress = lambda c, t: _print_progress(c, t, start)
        success = copy_with_permissions(src, dst, cli=True, progress_cb=progress)
        print()  # newline after progress bar
        if success:
            print("Transfer completed. See winmigrate.log for details.")
        else:
            print("Transfer failed or canceled. See winmigrate.log for details.")
    else:
        path = select_directory()
        if path:
            logger.info("User confirmed directory: %s", path)

if __name__ == '__main__':
    run_cli()
