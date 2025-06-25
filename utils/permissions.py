import os
import tkinter as tk
from tkinter import messagebox
from typing import Callable, Optional

from .logger import get_logger

logger = get_logger(__name__)


ProgressCallback = Optional[Callable[[int, int], None]]


def copy_file_with_progress(src: str, dst: str, callback: ProgressCallback = None) -> None:
    """Copy a file while invoking a progress callback."""
    total = os.path.getsize(src)
    copied = 0
    with open(src, 'rb') as fsrc, open(dst, 'wb') as fdst:
        while True:
            chunk = fsrc.read(1024 * 1024)
            if not chunk:
                break
            fdst.write(chunk)
            copied += len(chunk)
            if callback:
                callback(copied, total)


def take_ownership(path: str) -> bool:
    """Attempt to take ownership by changing permissions."""
    try:
        os.chmod(path, 0o777)
        logger.info("Took ownership of %s", path)
        return True
    except Exception as exc:
        logger.error("Failed to take ownership of %s: %s", path, exc)
        return False


def _retry_copy(src: str, dst: str, callback: ProgressCallback = None) -> bool:
    """Attempt to copy again, returning success."""
    try:
        copy_file_with_progress(src, dst, callback)
        logger.info("Copied %s to %s", src, dst)
        return True
    except PermissionError as exc:
        logger.error("Permission error after retry: %s", exc)
    except Exception as exc:
        logger.error("Unexpected error after retry: %s", exc)
    return False


def handle_permission_cli(src: str, dst: str, callback: ProgressCallback = None) -> bool:
    """Handle permission errors in CLI mode with prompts."""
    while True:
        response = input(
            f"Access to {src} denied. Retry as administrator? (y/n/t for take ownership): "
        ).strip().lower()
        if response == 'y':
            logger.info("User chose to retry as administrator for %s", src)
            if _retry_copy(src, dst, callback):
                return True
        elif response == 't':
            if take_ownership(src) and _retry_copy(src, dst, callback):
                return True
        else:
            logger.info("User canceled operation for %s", src)
            return False


def handle_permission_gui(root: tk.Tk, src: str, dst: str, callback: ProgressCallback = None) -> bool:
    """Handle permission errors in GUI mode using dialogs."""
    retry = messagebox.askyesno(
        "Permission Denied",
        f"Access to {src} denied. Retry as administrator?",
        parent=root
    )
    if retry:
        logger.info("User chose to retry as administrator for %s", src)
        if _retry_copy(src, dst, callback):
            return True
    take = messagebox.askyesno(
        "Take Ownership",
        f"Take ownership of {src}?",
        parent=root
    )
    if take and take_ownership(src):
        return _retry_copy(src, dst, callback)
    logger.info("User canceled operation for %s", src)
    return False


def copy_with_permissions(
    src: str,
    dst: str,
    cli: bool = True,
    root: Optional[tk.Tk] = None,
    progress_cb: ProgressCallback = None,
) -> bool:
    """Copy a file handling permission errors for CLI or GUI."""
    try:
        copy_file_with_progress(src, dst, progress_cb)
        logger.info("Copied %s to %s", src, dst)
        return True
    except PermissionError:
        logger.warning("Permission denied when copying %s", src)
        if cli:
            return handle_permission_cli(src, dst, progress_cb)
        if root is None:
            root = tk.Tk()
            root.withdraw()
        return handle_permission_gui(root, src, dst, progress_cb)
    except Exception as exc:
        logger.error("Failed to copy %s to %s: %s", src, dst, exc)
        return False
