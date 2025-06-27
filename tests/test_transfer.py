import os
from pathlib import Path

from utils.transfer import copy_file_resumable, sha256_of_file


def _random_file(path: Path, size: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "wb") as f:
        f.write(os.urandom(size))


def test_copy_file_resumable_new_file(tmp_path: Path) -> None:
    src = tmp_path / "src" / "data.bin"
    dst = tmp_path / "dst" / "data.bin"
    _random_file(src, 2 * 1024 * 1024 + 123)

    assert copy_file_resumable(str(src), str(dst))
    assert sha256_of_file(str(src)) == sha256_of_file(str(dst))


def test_copy_file_resumable_resume(tmp_path: Path) -> None:
    src = tmp_path / "src" / "data.bin"
    dst = tmp_path / "dst" / "data.bin"
    _random_file(src, 3 * 1024 * 1024 + 555)

    dst.parent.mkdir(parents=True, exist_ok=True)
    # write partial data to simulate interrupted transfer
    with open(src, "rb") as sf, open(dst, "wb") as df:
        df.write(sf.read(1024 * 1024))

    assert copy_file_resumable(str(src), str(dst))
    assert sha256_of_file(str(src)) == sha256_of_file(str(dst))


def test_copy_file_resumable_hash_mismatch(tmp_path: Path) -> None:
    src = tmp_path / "src" / "data.bin"
    dst = tmp_path / "dst" / "data.bin"
    _random_file(src, 512 * 1024)

    dst.parent.mkdir(parents=True, exist_ok=True)
    with open(dst, "wb") as f:
        f.write(b"corrupt")

    assert not copy_file_resumable(str(src), str(dst))
