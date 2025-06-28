import hashlib
import os
from typing import Dict, List


def compute_hash(data: bytes, algorithm: str = "sha256") -> str:
    """Return a hexadecimal digest for the provided data."""
    h = hashlib.new(algorithm)
    h.update(data)
    return h.hexdigest()


def validate_path(path: str) -> bool:
    """Return True if the given path exists on the filesystem."""
    return os.path.exists(path)


def resume_transfer(file_path: str, previous_size: int) -> bytes:
    """Read the remainder of the file starting from ``previous_size`` bytes."""
    with open(file_path, "rb") as f:
        f.seek(previous_size)
        return f.read()


def requires_elevation() -> bool:
    """Return True if the current process lacks administrative privileges."""
    try:
        return os.getuid() != 0  # type: ignore[attr-defined]
    except AttributeError:
        try:
            import ctypes  # type: ignore
            windll = getattr(ctypes, "windll", None)
            if windll is not None:
                return windll.shell32.IsUserAnAdmin() == 0
            return True
        except Exception:
            return True


def ensure_admin() -> bool:
    """Check for admin rights and prompt if elevation is required."""
    if requires_elevation():
        print("Elevation required. Falling back.")
        return False
    return True


def get_installed_programs() -> List[Dict[str, str]]:
    """Return information about installed programs (placeholder)."""
    return [
        {"name": "ExampleApp", "version": "1.0", "install_date": "2020-01-01"}
    ]
