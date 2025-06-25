import argparse

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

if __name__ == '__main__':
    run_cli()
