import argparse
import os
import shutil

from utils.logger import get_logger

logger = get_logger(__name__)

def run_cli(args=None) -> None:
    """Entry point for the CLI mode."""
    parser = argparse.ArgumentParser(description="WinMigrate CLI")
    parser.add_argument('--option', help='Placeholder option')
    parsed_args = parser.parse_args(args)

    logger.info("Running CLI with args: %s", parsed_args)
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
