import argparse

from utils.logger import get_logger
from utils.permissions import copy_with_permissions

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
        print("Transfer options will be available in future versions.")

if __name__ == '__main__':
    run_cli()
