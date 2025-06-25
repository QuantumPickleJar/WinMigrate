import argparse

from cli.cli_main import run_cli
from gui.gui_main import launch_gui


def main() -> None:
    parser = argparse.ArgumentParser(description="WinMigrate")
    parser.add_argument('--gui', action='store_true', help='Launch the GUI')
    args, remaining = parser.parse_known_args()

    if args.gui:
        launch_gui()
    else:
        run_cli(remaining)


if __name__ == '__main__':
    main()
