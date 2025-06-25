import hashlib
import os
from typing import Iterator

from utils.logger import get_logger

logger = get_logger(__name__)


def _file_chunks(path: str, chunk_size: int) -> Iterator[bytes]:
    """Yield file chunks of given size."""
    with open(path, "rb") as f:
        while True:
            data = f.read(chunk_size)
            if not data:
                break
            yield data


def sha256_of_file(path: str, chunk_size: int = 1024 * 1024) -> str:
    """Return SHA-256 hex digest for the given file."""
    h = hashlib.sha256()
    for chunk in _file_chunks(path, chunk_size):
        h.update(chunk)
    return h.hexdigest()


def copy_file_resumable(src: str, dest: str, chunk_size: int = 1024 * 1024) -> bool:
    """Copy a file with resume support and verify integrity.

    Returns True if the transfer succeeded and hashes match.
    """
    os.makedirs(os.path.dirname(dest) or ".", exist_ok=True)
    offset = 0
    if os.path.exists(dest):
        offset = os.path.getsize(dest)
    logger.info("Resuming transfer from %s to %s at offset %d", src, dest, offset)
    with open(src, "rb") as sf, open(dest, "ab") as df:
        sf.seek(offset)
        for chunk in iter(lambda: sf.read(chunk_size), b""):
            df.write(chunk)
    src_hash = sha256_of_file(src, chunk_size)
    dest_hash = sha256_of_file(dest, chunk_size)
    if src_hash == dest_hash:
        logger.info("Transfer verified successfully for %s", src)
        return True
    logger.error("Hash mismatch for %s", src)
    return False
