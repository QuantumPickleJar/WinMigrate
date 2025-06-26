import argparse
import configparser
import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    yaml = None

PROJECT_DIR = os.path.dirname(os.path.dirname(__file__))

DEFAULT_CONFIG_PATHS = [
    os.path.expanduser("~/.migration-assistant/config.json"),
    os.path.join(PROJECT_DIR, "config.json"),
]

@dataclass
class Config:
    timeout: int = 300
    verbosity: str = "INFO"
    chunk_size: int = 1024 * 1024
    log_path: str = os.path.join(os.getcwd(), "winmigrate.log")


def _read_config(path: str) -> Dict[str, Any]:
    ext = os.path.splitext(path)[1].lower()
    with open(path, "r", encoding="utf-8") as f:
        if ext == ".json":
            return json.load(f)
        if ext in (".yaml", ".yml"):
            if yaml is None:
                raise RuntimeError("PyYAML is not installed")
            return yaml.safe_load(f) or {}
        if ext == ".ini":
            parser = configparser.ConfigParser()
            parser.read_file(f)
            section = parser.sections()[0] if parser.sections() else "DEFAULT"
            return dict(parser[section])
    return {}


def load_config(path: Optional[str] = None) -> Config:
    cfg = Config()
    config_path = None
    if path:
        config_path = path
    else:
        for p in DEFAULT_CONFIG_PATHS:
            if os.path.exists(p):
                config_path = p
                break
    if config_path and os.path.exists(config_path):
        try:
            data = _read_config(config_path)
        except Exception:
            data = {}
        if "timeout" in data:
            cfg.timeout = int(data["timeout"])
        if "verbosity" in data:
            cfg.verbosity = str(data["verbosity"]).upper()
        if "chunk_size" in data:
            cfg.chunk_size = int(data["chunk_size"])
        if "chunk-size" in data:
            cfg.chunk_size = int(data["chunk-size"])
        if "log_path" in data:
            cfg.log_path = str(data["log_path"])
        if "log-path" in data:
            cfg.log_path = str(data["log-path"])
    return cfg


def apply_cli_overrides(cfg: Config, args: argparse.Namespace) -> Config:
    if getattr(args, "timeout", None) is not None:
        cfg.timeout = args.timeout
    if getattr(args, "verbosity", None) is not None:
        cfg.verbosity = str(args.verbosity).upper()
    if getattr(args, "chunk_size", None) is not None:
        cfg.chunk_size = args.chunk_size
    if getattr(args, "log_path", None) is not None:
        cfg.log_path = args.log_path
    return cfg
