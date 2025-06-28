from cli.cli_main import transfer
import hashlib


def test_transfer(tmp_path):
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    (src / "data.txt").write_bytes(b"hello")
    transfer(str(src), str(dst))
    data = (dst / "data.txt").read_bytes()
    assert hashlib.sha256(data).hexdigest() == hashlib.sha256(b"hello").hexdigest()
