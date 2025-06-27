from pathlib import Path

from utils.transfer import sha256_of_file
from utils.config import _read_config, load_config
from cli.cli_main import _path_size, save_preset, load_preset_file


def test_sha256_of_file(tmp_path: Path) -> None:
    p = tmp_path / "f.txt"
    data = b"hello world"
    p.write_bytes(data)
    assert sha256_of_file(str(p)) == (
        "b94d27b9934d3e08a52e52d7da7dabfac484efe37a5380ee9088f7ace2efcde9"
    )


def test_read_config_json(tmp_path: Path) -> None:
    cfg_file = tmp_path / "cfg.json"
    cfg_file.write_text('{"timeout": 10, "verbosity": "debug"}')
    cfg = _read_config(str(cfg_file))
    assert cfg["timeout"] == 10
    assert cfg["verbosity"] == "debug"


def test_load_config_overrides(tmp_path: Path) -> None:
    cfg_file = tmp_path / "cfg.ini"
    cfg_file.write_text("""[DEFAULT]\ntimeout = 5\nchunk-size = 4096\n""")
    cfg = load_config(str(cfg_file))
    assert cfg.timeout == 5
    assert cfg.chunk_size == 4096


def test_preset_roundtrip(tmp_path: Path) -> None:
    f1 = tmp_path / "a.txt"
    f1.write_text("a")
    p = save_preset("test", [str(f1)])
    assert Path(p).is_file()
    paths = load_preset_file(p)
    assert paths == [str(f1)]


def test_path_size_dir(tmp_path: Path) -> None:
    d = tmp_path / "dir"
    d.mkdir()
    (d / "a").write_text("123")
    (d / "b").write_text("4567")
    size = _path_size(str(d))
    assert size == 3 + 4

