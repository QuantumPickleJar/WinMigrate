import builtins
from unittest import mock


from utils.migration import (
    compute_hash,
    ensure_admin,
    get_installed_programs,
    resume_transfer,
    validate_path,
)


def test_compute_hash_sha256():
    data = b"hello"
    assert (
        compute_hash(data, "sha256")
        == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    )


def test_validate_path(tmp_path):
    f = tmp_path / "file.txt"
    f.write_text("hi")
    assert validate_path(str(f))
    assert not validate_path(str(f) + "_missing")


def test_resume_transfer(tmp_path):
    f = tmp_path / "data.bin"
    f.write_bytes(b"ABCDEFG")
    part = resume_transfer(str(f), 3)
    assert part == b"DEFG"


def test_ensure_admin_fallback():
    with mock.patch("utils.migration.requires_elevation", return_value=True):
        with mock.patch.object(builtins, "print") as mock_print:
            assert not ensure_admin()
            mock_print.assert_called_with("Elevation required. Falling back.")


def test_installed_program_fields():
    programs = get_installed_programs()
    assert programs, "Expected at least one program"
    for prog in programs:
        assert {"name", "version", "install_date"} <= prog.keys()
