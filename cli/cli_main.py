import argparse
import json
import logging
import os
import signal
import sys
import time

from utils import programs

from utils.logger import get_logger, configure_logger
from utils.permissions import copy_with_permissions
from utils.config import load_config, apply_cli_overrides
from utils.transfer_control import TransferControl
from utils.restore import generate_restore_script

PRESET_DIR = os.path.expanduser("~/.migration-assistant/presets")

logger = get_logger(__name__)

def _path_size(path: str) -> int:
    """Return file or directory size in bytes."""
    if os.path.isdir(path):
        total = 0
        for root, _, files in os.walk(path):
            for f in files:
                fp = os.path.join(root, f)
                try:
                    total += os.path.getsize(fp)
                except OSError:
                    pass
        return total
    try:
        return os.path.getsize(path)
    except OSError:
        return 0

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
        size = _path_size(path)
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


def select_items_cli() -> list[str] | None:
    """Interactively select multiple files or folders."""
    print("Enter file or directory paths. Leave blank when done.")
    selections: list[str] = []
    while True:
        path = input("Path: ").strip().strip('"')
        if not path:
            break
        if not os.path.exists(path):
            print("Path does not exist. Try again.")
            continue
        selections.append(path)
        size = sum(_path_size(p) for p in selections)
        print(f"Current total size: {size} bytes")
    if not selections:
        print("No items selected.")
        return None
    confirm = input("Use these selections? (y/n): ").strip().lower()
    if confirm != "y":
        return None
    return selections


def save_preset(name: str, paths: list[str]) -> str:
    """Save the selected paths as a preset and return the file path."""
    os.makedirs(PRESET_DIR, exist_ok=True)
    if not name.endswith(".json"):
        name += ".json"
    preset_path = os.path.join(PRESET_DIR, name)
    with open(preset_path, "w", encoding="utf-8") as f:
        json.dump(paths, f, indent=2)
    return preset_path


def load_preset_file(path: str) -> list[str]:
    """Load file paths from a preset."""
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Preset must contain a list of paths")
    return [str(p) for p in data]


def _print_progress(copied: int, total: int, start: float, *, accessible: bool = False) -> None:
    """Print a progress indicator to stdout."""
    percent = copied / total * 100 if total else 100
    bar_len = 30
    filled = int(bar_len * percent / 100)
    bar = '#' * filled + '-' * (bar_len - filled)
    speed = copied / max(time.time() - start, 1e-3)
    eta = (total - copied) / speed if speed > 0 else 0
    msg = f"[{bar}] {percent:5.1f}% {copied}/{total} bytes ETA {eta:0.1f}s"
    if accessible:
        print(msg)
    else:
        sys.stdout.write("\r" + msg)
        sys.stdout.flush()

def _print_retry(remaining: int, *, accessible: bool = False) -> None:
    msg = f"Retrying in {remaining}s..."
    if accessible:
        print(msg)
    else:
        sys.stdout.write(f"\r{msg}     ")
        sys.stdout.flush()


def copy_items(
    sources: list[str],
    dst_root: str,
    config,
    control: TransferControl,
) -> bool:
    """Copy multiple files or directories to a destination root."""
    total_size = sum(_path_size(p) for p in sources)
    copied_total = 0
    start = time.time()

    def make_update(offset: int):
        return lambda c, t: _print_progress(offset + c, total_size, start, accessible=config.accessible)

    for src in sources:
        if control.cancel.is_set():
            return False
        if os.path.isdir(src):
            base = os.path.basename(src.rstrip(os.sep))
            for root, _, files in os.walk(src):
                for f in files:
                    if control.cancel.is_set():
                        return False
                    src_file = os.path.join(root, f)
                    rel = os.path.relpath(src_file, src)
                    dst = os.path.join(dst_root, base, rel)
                    os.makedirs(os.path.dirname(dst), exist_ok=True)
                    file_size = os.path.getsize(src_file)
                    cb = make_update(copied_total)
                    if not copy_with_permissions(
                        src_file,
                        dst,
                        cli=True,
                        progress_cb=cb,
                        retry_cb=lambda r: _print_retry(r, accessible=config.accessible),
                        timeout=config.timeout,
                        chunk_size=config.chunk_size,
                        control=control,
                    ):
                        return False
                    copied_total += file_size
        else:
            dst = os.path.join(dst_root, os.path.basename(src))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            file_size = os.path.getsize(src)
            cb = make_update(copied_total)
            if not copy_with_permissions(
                src,
                dst,
                cli=True,
                progress_cb=cb,
                retry_cb=lambda r: _print_retry(r, accessible=config.accessible),
                timeout=config.timeout,
                chunk_size=config.chunk_size,
                control=control,
            ):
                return False
            copied_total += file_size
    print()  # newline after progress bar
    return True

def run_cli(args=None) -> None:
    """Entry point for the CLI mode."""
    parser = argparse.ArgumentParser(description="WinMigrate CLI")
    parser.add_argument('--config', help='Path to configuration file')
    parser.add_argument('--timeout', type=int, help='Timeout duration in seconds')
    parser.add_argument('--verbosity', help='Logging verbosity level')
    parser.add_argument('--chunk-size', type=int, help='Transfer block size in bytes')
    parser.add_argument('--log-path', help='Path to log file')
    parser.add_argument('--csv-log-path', help='Path to CSV log file')
    parser.add_argument('--accessible', action='store_true', help='Accessible output for screen readers')
    parser.add_argument('--preset', help='Path to file selection preset')
    parser.add_argument(
        '--save-preset', nargs='?', const=True, metavar='NAME',
        help='Save selection as preset with NAME (prompt if NAME omitted)'
    )
    parser.add_argument(
        '--transfer', nargs='+', metavar=('SRC', 'DST'),
        help='Transfer file(s). Provide only DST when used with --preset'
    )
    parser.add_argument(
        '--installed-report', nargs='?', metavar='DIR', const='',
        help='Generate installed programs report in DIR (prompt if omitted)'
    )
    parser.add_argument('--restore-script', help='Write PowerShell restore script to PATH')
    parser.add_argument('--program-json', help='Installed programs JSON for restore script')
    parsed_args = parser.parse_args(args)

    config = load_config(parsed_args.config)
    config = apply_cli_overrides(config, parsed_args)
    level = getattr(logging, config.verbosity.upper(), logging.INFO)
    configure_logger(
        level=level,
        log_path=config.log_path,
        csv_log_path=config.csv_log_path,
        accessible=config.accessible,
    )

    control = TransferControl()

    def _handle_sigint(signum, frame):
        if control.pause.is_set():
            control.cancel.set()
            print("\nCanceling transfer...")
            return
        control.pause.set()
        print("\nTransfer paused. Resume (r) or cancel (c)? ", end="", flush=True)
        choice = sys.stdin.readline().strip().lower()
        if choice == "r":
            control.pause.clear()
        else:
            control.cancel.set()

    old_handler = signal.signal(signal.SIGINT, _handle_sigint)

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
        pairs = []
        if parsed_args.preset:
            if len(parsed_args.transfer) != 1:
                parser.error('--transfer requires DEST only when using --preset')
            dst_root = parsed_args.transfer[0]
            sources = load_preset_file(parsed_args.preset)
            success = copy_items(sources, dst_root, config, control)
            pairs = [
                (s, os.path.join(dst_root, os.path.basename(s.rstrip(os.sep))))
                for s in sources
            ]
        else:
            if len(parsed_args.transfer) != 2:
                parser.error('--transfer requires SRC and DST')
            src, dst = parsed_args.transfer
            start = time.time()
            progress = lambda c, t: _print_progress(c, t, start, accessible=config.accessible)
            success = copy_with_permissions(
                src,
                dst,
                cli=True,
                progress_cb=progress,
                retry_cb=lambda r: _print_retry(r, accessible=config.accessible),
                timeout=config.timeout,
                chunk_size=config.chunk_size,
                control=control,
            )
            pairs = [(src, dst)]
        if success:
            print(f"Transfer completed. See {config.log_path} for details.")
            if parsed_args.restore_script:
                generate_restore_script(
                    pairs,
                    parsed_args.restore_script,
                    program_json=parsed_args.program_json,
                )
                print(
                    f"Restore script written to {parsed_args.restore_script}. Review before running."
                )
        else:
            print(
                f"Transfer failed or canceled. See {config.log_path} for details."
            )
        signal.signal(signal.SIGINT, old_handler)
    else:
        if parsed_args.preset:
            sources = load_preset_file(parsed_args.preset)
        else:
            sources = select_items_cli()
            if sources and parsed_args.save_preset:
                name = parsed_args.save_preset
                if name is True:
                    name = input('Preset name: ').strip()
                if name:
                    p = save_preset(name, sources)
                    print(f'Saved preset to {p}')
        if not sources:
            return
        dst_root = input('Enter destination directory: ').strip().strip('"')
        if not dst_root:
            print('No destination specified.')
            return
        success = copy_items(sources, dst_root, config, control)
        pairs = [
            (s, os.path.join(dst_root, os.path.basename(s.rstrip(os.sep))))
            for s in sources
        ]
        if success:
            print(f"Transfer completed. See {config.log_path} for details.")
            if parsed_args.restore_script:
                generate_restore_script(
                    pairs,
                    parsed_args.restore_script,
                    program_json=parsed_args.program_json,
                )
                print(
                    f"Restore script written to {parsed_args.restore_script}. Review before running."
                )
        else:
            print(
                f"Transfer failed or canceled. See {config.log_path} for details."
            )
        signal.signal(signal.SIGINT, old_handler)
    
    if not parsed_args.transfer and not parsed_args.installed_report:
        logger.info("User confirmed directory: %s", ' '.join(sources) if parsed_args.preset or sources else '')

if __name__ == '__main__':
    run_cli()
