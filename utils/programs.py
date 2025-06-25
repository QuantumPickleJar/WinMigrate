import os
import platform
from dataclasses import dataclass
from typing import List, Optional

from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class ProgramInfo:
    name: str
    location: Optional[str] = None
    url: Optional[str] = None


def _scan_registry() -> List[ProgramInfo]:
    """Return programs listed in Windows uninstall registry keys."""
    programs: List[ProgramInfo] = []
    if platform.system() != "Windows":
        return programs

    try:
        import winreg
    except Exception as exc:  # pragma: no cover - running on non-Windows
        logger.error("winreg import failed: %s", exc)
        return programs

    hives = [
        (winreg.HKEY_LOCAL_MACHINE, r"Software\Microsoft\Windows\CurrentVersion\Uninstall"),
        (winreg.HKEY_LOCAL_MACHINE, r"Software\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"),
    ]
    for hive, path in hives:
        try:
            key = winreg.OpenKey(hive, path)
        except FileNotFoundError:
            continue
        for i in range(0, winreg.QueryInfoKey(key)[0]):
            try:
                subkey_name = winreg.EnumKey(key, i)
                subkey = winreg.OpenKey(key, subkey_name)
                name = winreg.QueryValueEx(subkey, "DisplayName")[0]
                location = winreg.QueryValueEx(subkey, "InstallLocation")[0] if winreg.QueryValueEx(subkey, "InstallLocation")[0] else None
                url = None
                try:
                    url = winreg.QueryValueEx(subkey, "URLInfoAbout")[0]
                except FileNotFoundError:
                    pass
                programs.append(ProgramInfo(name=name, location=location, url=url))
            except FileNotFoundError:
                continue
            except OSError:
                continue
    return programs


def _scan_path() -> List[ProgramInfo]:
    """Return executables found in directories on PATH."""
    programs: List[ProgramInfo] = []
    paths = os.environ.get("PATH", "").split(os.pathsep)
    seen = set()
    for dir_path in paths:
        if not os.path.isdir(dir_path):
            continue
        try:
            for entry in os.listdir(dir_path):
                if entry.lower().endswith(".exe"):
                    name = os.path.splitext(entry)[0]
                    if name not in seen:
                        seen.add(name)
                        programs.append(ProgramInfo(name=name, location=dir_path))
        except OSError:
            continue
    return programs


def scan_installed_programs() -> List[ProgramInfo]:
    """Combine registry and PATH program scans."""
    progs = _scan_registry()
    progs.extend(_scan_path())
    return progs


def generate_report(output_dir: str) -> str:
    """Generate a markdown report of installed programs."""
    os.makedirs(output_dir, exist_ok=True)
    programs = scan_installed_programs()
    lines = ["# Installed Programs", ""]
    for p in programs:
        line = f"- **{p.name}**"
        if p.location:
            line += f" - {p.location}"
        if p.url:
            line += f" ([link]({p.url}))"
        lines.append(line)
    path = os.path.join(output_dir, "installed_programs.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    logger.info("Generated installed programs report at %s", path)
    return path
