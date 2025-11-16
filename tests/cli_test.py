import sys
import pytest
import py_eol.cli as cli_mod
from unittest.mock import MagicMock


def test_main_version(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["py-eol", "--version"])
    # The version action prints to stdout and exits, so we can't easily mock __version__.
    # Instead, we'll just check that it exits with code 0.
    with pytest.raises(SystemExit) as e:
        cli_mod.main()
    assert e.value.code == 0


def test_main_refresh(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["py-eol", "refresh"])
    monkeypatch.setattr(cli_mod, "sync_data", lambda: True)
    with pytest.raises(SystemExit) as e:
        cli_mod.main()
    out = capsys.readouterr().out
    assert "Refreshing" in out
    assert e.value.code == 0


def test_main_refresh_fail(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["py-eol", "refresh"])
    monkeypatch.setattr(cli_mod, "sync_data", lambda: False)
    with pytest.raises(SystemExit) as e:
        cli_mod.main()
    out = capsys.readouterr().out
    assert "Failed to refresh" in out
    assert e.value.code == 1


def test_main_check_self(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["py-eol", "check-self"])
    monkeypatch.setattr(
        cli_mod,
        "check_self",
        lambda output_json=False: (_ for _ in ()).throw(SystemExit(0)),
    )
    with pytest.raises(SystemExit) as e:
        cli_mod.main()
    assert e.value.code == 0


def test_main_list(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["py-eol", "list"])
    monkeypatch.setattr(
        cli_mod,
        "list_supported_versions",
        lambda output_json=False: (_ for _ in ()).throw(SystemExit(0)),
    )
    with pytest.raises(SystemExit) as e:
        cli_mod.main()
    assert e.value.code == 0


def test_main_versions(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["py-eol", "versions", "3.99"])
    monkeypatch.setattr(
        cli_mod,
        "check_versions",
        lambda versions, output_json=False: (_ for _ in ()).throw(SystemExit(0)),
    )
    with pytest.raises(SystemExit) as e:
        cli_mod.main()
    assert e.value.code == 0


def test_main_default(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["py-eol"])

    # We expect print_help to be called and exit with 0
    mock_parser = MagicMock()
    mock_parser.print_help = MagicMock()

    monkeypatch.setattr(cli_mod.argparse, "ArgumentParser", lambda *a, **k: mock_parser)

    with pytest.raises(SystemExit) as e:
        cli_mod.main()

    mock_parser.print_help.assert_called_once()
    assert e.value.code == 0


def test_check_versions_supported(monkeypatch, capsys):
    monkeypatch.setattr(
        cli_mod, "get_eol_date", lambda v: sys.modules["datetime"].date(2099, 1, 1)
    )
    monkeypatch.setattr(cli_mod, "is_eol", lambda v: False)
    monkeypatch.setattr(
        "py_eol.checker.get_eol_date",
        lambda v: sys.modules["datetime"].date(2099, 1, 1),
    )
    with pytest.raises(SystemExit) as e:
        cli_mod.check_versions(["3.99"])
    out = capsys.readouterr().out
    assert "still supported" in out
    assert e.value.code == 0


def test_check_versions_eol(monkeypatch, capsys):
    monkeypatch.setattr(
        cli_mod, "get_eol_date", lambda v: sys.modules["datetime"].date(2000, 1, 1)
    )
    monkeypatch.setattr(cli_mod, "is_eol", lambda v: True)
    monkeypatch.setattr(
        "py_eol.checker.get_eol_date",
        lambda v: sys.modules["datetime"].date(2000, 1, 1),
    )
    with pytest.raises(SystemExit) as e:
        cli_mod.check_versions(["2.7"])
    out = capsys.readouterr().out
    assert "already EOL" in out
    assert e.value.code == 1


def test_check_versions_unknown(monkeypatch, capsys):
    def raise_value_error(v):
        raise ValueError("Unknown Python version")

    monkeypatch.setattr(cli_mod, "get_eol_date", raise_value_error)
    cli_mod.is_eol = lambda v: False
    with pytest.raises(SystemExit) as e:
        cli_mod.check_versions(["4.0"])
    out = capsys.readouterr().out
    assert "Error checking" in out
    assert e.value.code == 2


def test_check_versions_json(monkeypatch, capsys):
    monkeypatch.setattr(
        cli_mod, "get_eol_date", lambda v: sys.modules["datetime"].date(2099, 1, 1)
    )
    monkeypatch.setattr(cli_mod, "is_eol", lambda v: False)
    with pytest.raises(SystemExit) as e:
        cli_mod.check_versions(["3.99"], output_json=True)
    out = capsys.readouterr().out
    assert out.strip().startswith("[")
    assert e.value.code == 0


def test_list_supported_versions(monkeypatch, capsys):
    monkeypatch.setattr(cli_mod, "supported_versions", lambda: ["3.99", "3.98"])
    with pytest.raises(SystemExit) as e:
        cli_mod.list_supported_versions()
    out = capsys.readouterr().out
    assert "Supported Python versions" in out
    assert "3.99" in out
    assert e.value.code == 0


def test_list_supported_versions_json(monkeypatch, capsys):
    monkeypatch.setattr(cli_mod, "supported_versions", lambda: ["3.99"])
    with pytest.raises(SystemExit):
        cli_mod.list_supported_versions(output_json=True)
    out = capsys.readouterr().out
    assert out.strip().startswith("[")


def test_check_self(monkeypatch):
    monkeypatch.setattr(
        cli_mod,
        "check_versions",
        lambda v, output_json=False: (_ for _ in ()).throw(SystemExit(0)),
    )
    with pytest.raises(SystemExit):
        cli_mod.check_self()


def test_refresh_data_success(monkeypatch, capsys):
    monkeypatch.setattr(cli_mod, "sync_data", lambda: True)
    with pytest.raises(SystemExit) as e:
        cli_mod.refresh_data()
    out = capsys.readouterr().out
    assert "Successfully refreshed" in out
    assert e.value.code == 0


def test_refresh_data_fail(monkeypatch, capsys):
    monkeypatch.setattr(cli_mod, "sync_data", lambda: False)
    with pytest.raises(SystemExit) as e:
        cli_mod.refresh_data()
    out = capsys.readouterr().out
    assert "Failed to refresh" in out
    assert e.value.code == 1


def test_main_files_found(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["py-eol", "files", "pyproject.toml"])
    monkeypatch.setattr(cli_mod, "_check_pyproject_toml", lambda f: True)
    with pytest.raises(SystemExit) as e:
        cli_mod.main()
    assert e.value.code == 1


def test_main_files_not_found(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["py-eol", "files", "pyproject.toml"])
    monkeypatch.setattr(cli_mod, "_check_pyproject_toml", lambda f: False)
    # Since we're not raising an exception, we need to mock sys.exit
    mock_exit = MagicMock()
    monkeypatch.setattr(sys, "exit", mock_exit)
    cli_mod.main()
    mock_exit.assert_not_called()


def test_main_files_multiple(monkeypatch, capsys, tmp_path):
    # Create dummy files in temp directory
    pyproject_file = tmp_path / "pyproject.toml"
    setup_file = tmp_path / "setup.py"
    pyproject_file.touch()
    setup_file.touch()

    monkeypatch.setattr(
        sys, "argv", ["py-eol", "files", str(pyproject_file), str(setup_file)]
    )
    monkeypatch.setattr(cli_mod, "_check_pyproject_toml", lambda f: False)
    monkeypatch.setattr(cli_mod, "_check_setup_py", lambda f: True)
    with pytest.raises(SystemExit) as e:
        cli_mod.main()
    assert e.value.code == 1


def test_main_files_github_actions(monkeypatch, capsys, tmp_path):
    # Create a GitHub Actions workflow file
    workflows_dir = tmp_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)
    workflow_file = workflows_dir / "test.yml"
    workflow_file.touch()

    monkeypatch.setattr(sys, "argv", ["py-eol", "files", str(workflow_file)])
    monkeypatch.setattr(cli_mod, "_check_github_actions", lambda f: True)
    with pytest.raises(SystemExit) as e:
        cli_mod.main()
    assert e.value.code == 1
