import os
import tkinter as tk
from tkinter import messagebox
from typing import Callable, Optional
import time

from .logger import get_logger

logger = get_logger(__name__)


ProgressCallback = Optional[Callable[[int, int], None]]


def copy_file_with_progress(
    src: str,
    dst: str,
    callback: ProgressCallback = None,
    start: int = 0,
) -> int:
    """Copy a file while invoking a progress callback.

    Returns the number of bytes copied.
    """
    total = os.path.getsize(src)
    copied = start
    mode = 'ab' if start else 'wb'
    with open(src, 'rb') as fsrc, open(dst, mode) as fdst:
        fsrc.seek(start)
        if start:
            fdst.seek(start)

        while True:
            chunk = fsrc.read(1024 * 1024)
            if not chunk:
                break
            fdst.write(chunk)
            copied += len(chunk)
            if callback:
                callback(copied, total)
    return copied

def _countdown(delay: int, cb: Optional[Callable[[int], None]]) -> None:
    for remaining in range(delay, 0, -1):
        if cb:
            cb(remaining)
        time.sleep(1)

def copy_file_with_timeout_retry(
    src: str,
    dst: str,
    callback: ProgressCallback = None,
    timeout: int = 300,
    retry_cb: Optional[Callable[[int], None]] = None,
) -> bool:
    """Copy handling transient network errors with timeout and retry."""
    total = os.path.getsize(src)
    copied = 0
    start_time = time.time()
    attempt = 0
    while copied < total:
        try:
            copied = copy_file_with_progress(src, dst, callback, start=copied)
        except OSError as exc:
            logger.warning('Network error: %s', exc)
            if time.time() - start_time >= timeout:
                logger.error('Transfer timed out after %s seconds', timeout)
                return False
            attempt += 1
            delay = min(2 ** attempt, 60)
            logger.info('Retrying in %s seconds', delay)
            _countdown(delay, retry_cb)
            continue
    return True


def take_ownership(path: str) -> bool:
    """Attempt to take ownership by changing permissions."""
    try:
        os.chmod(path, 0o777)
        logger.info("Took ownership of %s", path)
        return True
    except Exception as exc:
        logger.error("Failed to take ownership of %s: %s", path, exc)
        return False


def _retry_copy(
    src: str,
    dst: str,
    callback: ProgressCallback = None,
    timeout: int = 300,
    retry_cb: Optional[Callable[[int], None]] = None,
) -> bool:
    """Attempt to copy again, returning success."""
    try:
        copy_file_with_timeout_retry(src, dst, callback, timeout, retry_cb)
        logger.info("Copied %s to %s", src, dst)
        return True
    except PermissionError as exc:
        logger.error("Permission error after retry: %s", exc)
    except Exception as exc:
        logger.error("Unexpected error after retry: %s", exc)
    return False


def handle_permission_cli(
    src: str,
    dst: str,
    callback: ProgressCallback = None,
    timeout: int = 300,
    retry_cb: Optional[Callable[[int], None]] = None,
) -> bool:
    """Handle permission errors in CLI mode with prompts."""
    while True:
        response = input(
            f"Access to {src} denied. Retry as administrator? (y/n/t for take ownership): "
        ).strip().lower()
        if response == 'y':
            logger.info("User chose to retry as administrator for %s", src)
        if _retry_copy(src, dst, callback, timeout, retry_cb):
                return True
        elif response == 't':
            if take_ownership(src) and _retry_copy(src, dst, callback, timeout, retry_cb):

                return True
        else:
            logger.info("User canceled operation for %s", src)
            return False


def handle_permission_gui(
    root: tk.Tk,
    src: str,
    dst: str,
    callback: ProgressCallback = None,
    timeout: int = 300,
    retry_cb: Optional[Callable[[int], None]] = None,
) -> bool:
    """Handle permission errors in GUI mode using dialogs."""
    retry = messagebox.askyesno(
        "Permission Denied",
        f"Access to {src} denied. Retry as administrator?",
        parent=root
    )
    if retry:
        logger.info("User chose to retry as administrator for %s", src)
        if _retry_copy(src, dst, callback, timeout, retry_cb):
            return True
    take = messagebox.askyesno(
        "Take Ownership",
        f"Take ownership of {src}?",
        parent=root
    )
    if take and take_ownership(src
        return _retry_copy(src, dst, callback, timeout, retry_cb)
    logger.info("User canceled operation for %s", src)
    return False


def copy_with_permissions(
    src: str,
    dst: str,
    cli: bool = True,
    root: Optional[tk.Tk] = None,
    progress_cb: ProgressCallback = None,
    timeout: int = 300,
    retry_cb: Optional[Callable[[int], None]] = None,
) -> bool:
    """Copy a file handling permission errors for CLI or GUI."""
    try:
        copy_file_with_timeout_retry(src, dst, progress_cb, timeout, retry_cb)
        logger.info("Copied %s to %s", src, dst)
        return True
    except PermissionError:
        logger.warning("Permission denied when copying %s", src)
        if cli:
            return handle_permission_cli(src, dst, progress_cb, timeout, retry_cb)
        if root is None:
            root = tk.Tk()
            root.withdraw()
        return handle_permission_gui(root, src, dst, progress_cb, timeout, retry_cb)
    except Exception as exc:
        logger.error("Failed to copy %s to %s: %s", src, dst, exc)
        return False
