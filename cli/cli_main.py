import argparse

from utils.logger import get_logger
from utils.transfer import copy_file_resumable

logger = get_logger(__name__)


def run_cli(args=None) -> None:
    """Entry point for the CLI mode."""
    parser = argparse.ArgumentParser(description="WinMigrate CLI")
    parser.add_argument('--source', required=True, help='Path to the source file')
    parser.add_argument('--destination', required=True, help='Destination path')
    parsed_args = parser.parse_args(args)

    logger.info("Running CLI with args: %s", parsed_args)
    success = copy_file_resumable(parsed_args.source, parsed_args.destination)
    if success:
        print("Transfer completed successfully.")
    else:
        print("Transfer failed: hash mismatch.")


if __name__ == '__main__':
    run_cli()
