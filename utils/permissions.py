import os
import shutil
import tkinter as tk
from tkinter import messagebox

from .logger import get_logger

logger = get_logger(__name__)


def take_ownership(path: str) -> bool:
    """Attempt to take ownership by changing permissions."""
    try:
        os.chmod(path, 0o777)
        logger.info("Took ownership of %s", path)
        return True
    except Exception as exc:
        logger.error("Failed to take ownership of %s: %s", path, exc)
        return False


def _retry_copy(src: str, dst: str) -> bool:
    """Attempt to copy again, returning success."""
    try:
        shutil.copy(src, dst)
        logger.info("Copied %s to %s", src, dst)
        return True
    except PermissionError as exc:
        logger.error("Permission error after retry: %s", exc)
    except Exception as exc:
        logger.error("Unexpected error after retry: %s", exc)
    return False


def handle_permission_cli(src: str, dst: str) -> None:
    """Handle permission errors in CLI mode with prompts."""
    while True:
        response = input(
            f"Access to {src} denied. Retry as administrator? (y/n/t for take ownership): "
        ).strip().lower()
        if response == 'y':
            logger.info("User chose to retry as administrator for %s", src)
            if _retry_copy(src, dst):
                return
        elif response == 't':
            if take_ownership(src) and _retry_copy(src, dst):
                return
        else:
            logger.info("User canceled operation for %s", src)
            return


def handle_permission_gui(root: tk.Tk, src: str, dst: str) -> None:
    """Handle permission errors in GUI mode using dialogs."""
    retry = messagebox.askyesno(
        "Permission Denied",
        f"Access to {src} denied. Retry as administrator?",
        parent=root
    )
    if retry:
        logger.info("User chose to retry as administrator for %s", src)
        if _retry_copy(src, dst):
            return
    take = messagebox.askyesno(
        "Take Ownership",
        f"Take ownership of {src}?",
        parent=root
    )
    if take and take_ownership(src):
        _retry_copy(src, dst)
    else:
        logger.info("User canceled operation for %s", src)


def copy_with_permissions(src: str, dst: str, cli: bool = True, root: tk.Tk | None = None) -> None:
    """Copy a file handling permission errors for CLI or GUI."""
    try:
        shutil.copy(src, dst)
        logger.info("Copied %s to %s", src, dst)
    except PermissionError:
        logger.warning("Permission denied when copying %s", src)
        if cli:
            handle_permission_cli(src, dst)
        else:
            if root is None:
                root = tk.Tk()
                root.withdraw()
            handle_permission_gui(root, src, dst)
    except Exception as exc:
        logger.error("Failed to copy %s to %s: %s", src, dst, exc)
