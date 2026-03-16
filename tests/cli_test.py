import sys
import datetime
import pytest
import py_eol.cli as cli_mod
from unittest.mock import MagicMock


def test_main_version(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["py-eol", "--version"])
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
        lambda versions, output_json=False, warn_before_days=0: (_ for _ in ()).throw(
            SystemExit(0)
        ),
    )
    with pytest.raises(SystemExit) as e:
        cli_mod.main()
    assert e.value.code == 0


def test_main_default(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["py-eol"])

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
    monkeypatch.setattr(cli_mod, "is_eol_soon", lambda v, d: False)
    monkeypatch.setattr(cli_mod, "days_until_eol", lambda v: 999)
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
    monkeypatch.setattr(cli_mod, "days_until_eol", lambda v: -1000)
    monkeypatch.setattr(
        "py_eol.checker.get_eol_date",
        lambda v: sys.modules["datetime"].date(2000, 1, 1),
    )
    with pytest.raises(SystemExit) as e:
        cli_mod.check_versions(["2.7"])
    out = capsys.readouterr().out
    assert "already EOL" in out
    assert e.value.code == 1


def test_check_versions_eol_soon(monkeypatch, capsys):
    future_date = datetime.date.today() + datetime.timedelta(days=60)
    monkeypatch.setattr(cli_mod, "get_eol_date", lambda v: future_date)
    monkeypatch.setattr(cli_mod, "is_eol", lambda v: False)
    monkeypatch.setattr(cli_mod, "is_eol_soon", lambda v, d: True)
    monkeypatch.setattr(cli_mod, "days_until_eol", lambda v: 60)
    monkeypatch.setattr("py_eol.checker.get_eol_date", lambda v: future_date)
    with pytest.raises(SystemExit) as e:
        cli_mod.check_versions(["3.99"], warn_before_days=90)
    out = capsys.readouterr().out
    assert "will be EOL on" in out
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
    monkeypatch.setattr(cli_mod, "is_eol_soon", lambda v, d: False)
    monkeypatch.setattr(cli_mod, "days_until_eol", lambda v: 999)
    with pytest.raises(SystemExit) as e:
        cli_mod.check_versions(["3.99"], output_json=True)
    out = capsys.readouterr().out
    assert out.strip().startswith("[")
    assert e.value.code == 0


def test_check_versions_json_includes_days_until_eol(monkeypatch, capsys):
    import json

    monkeypatch.setattr(
        cli_mod, "get_eol_date", lambda v: sys.modules["datetime"].date(2099, 1, 1)
    )
    monkeypatch.setattr(cli_mod, "is_eol", lambda v: False)
    monkeypatch.setattr(cli_mod, "is_eol_soon", lambda v, d: False)
    monkeypatch.setattr(cli_mod, "days_until_eol", lambda v: 999)
    with pytest.raises(SystemExit):
        cli_mod.check_versions(["3.99"], output_json=True)
    out = capsys.readouterr().out
    data = json.loads(out)
    assert "days_until_eol" in data[0]
    assert data[0]["days_until_eol"] == 999


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
        lambda v, output_json=False, warn_before_days=0: (_ for _ in ()).throw(
            SystemExit(0)
        ),
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
    monkeypatch.setattr(cli_mod, "_check_pyproject_toml", lambda f, w=0: True)
    with pytest.raises(SystemExit) as e:
        cli_mod.main()
    assert e.value.code == 1


def test_main_files_not_found(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["py-eol", "files", "pyproject.toml"])
    monkeypatch.setattr(cli_mod, "_check_pyproject_toml", lambda f, w=0: False)
    mock_exit = MagicMock()
    monkeypatch.setattr(sys, "exit", mock_exit)
    cli_mod.main()
    mock_exit.assert_not_called()


def test_main_files_multiple(monkeypatch, capsys, tmp_path):
    pyproject_file = tmp_path / "pyproject.toml"
    setup_file = tmp_path / "setup.py"
    pyproject_file.touch()
    setup_file.touch()

    monkeypatch.setattr(
        sys, "argv", ["py-eol", "files", str(pyproject_file), str(setup_file)]
    )
    monkeypatch.setattr(cli_mod, "_check_pyproject_toml", lambda f, w=0: False)
    monkeypatch.setattr(cli_mod, "_check_setup_py", lambda f, w=0: True)
    with pytest.raises(SystemExit) as e:
        cli_mod.main()
    assert e.value.code == 1


def test_main_files_github_actions(monkeypatch, capsys, tmp_path):
    workflows_dir = tmp_path / ".github" / "workflows"
    workflows_dir.mkdir(parents=True)
    workflow_file = workflows_dir / "test.yml"
    workflow_file.touch()

    monkeypatch.setattr(sys, "argv", ["py-eol", "files", str(workflow_file)])
    monkeypatch.setattr(cli_mod, "_check_github_actions", lambda f, w=0: True)
    with pytest.raises(SystemExit) as e:
        cli_mod.main()
    assert e.value.code == 1


def test_main_files_python_version(monkeypatch, capsys, tmp_path):
    pv_file = tmp_path / ".python-version"
    pv_file.write_text("3.7\n")

    monkeypatch.setattr(sys, "argv", ["py-eol", "files", str(pv_file)])
    monkeypatch.setattr(cli_mod, "_check_python_version_file", lambda f, w=0: True)
    with pytest.raises(SystemExit) as e:
        cli_mod.main()
    assert e.value.code == 1


def test_main_files_tox_ini(monkeypatch, capsys, tmp_path):
    tox_file = tmp_path / "tox.ini"
    tox_file.write_text("[tox]\nenvlist = py37\n")

    monkeypatch.setattr(sys, "argv", ["py-eol", "files", str(tox_file)])
    monkeypatch.setattr(cli_mod, "_check_tox_ini", lambda f, w=0: True)
    with pytest.raises(SystemExit) as e:
        cli_mod.main()
    assert e.value.code == 1


def test_main_files_dockerfile(monkeypatch, capsys, tmp_path):
    dockerfile = tmp_path / "Dockerfile"
    dockerfile.write_text("FROM python:3.7-slim\n")

    monkeypatch.setattr(sys, "argv", ["py-eol", "files", str(dockerfile)])
    monkeypatch.setattr(cli_mod, "_check_dockerfile", lambda f, w=0: True)
    with pytest.raises(SystemExit) as e:
        cli_mod.main()
    assert e.value.code == 1


def test_main_files_warn_before(monkeypatch, capsys, tmp_path):
    pyproject_file = tmp_path / "pyproject.toml"
    pyproject_file.touch()

    monkeypatch.setattr(
        sys, "argv", ["py-eol", "files", str(pyproject_file), "--warn-before", "90"]
    )
    captured_warn_days = []

    def mock_check(f, w=0):
        captured_warn_days.append(w)
        return False

    monkeypatch.setattr(cli_mod, "_check_pyproject_toml", mock_check)
    mock_exit = MagicMock()
    monkeypatch.setattr(sys, "exit", mock_exit)
    cli_mod.main()
    assert captured_warn_days == [90]


def test_main_versions_warn_before(monkeypatch, capsys):
    captured_args = {}

    def mock_check_versions(versions, output_json=False, warn_before_days=0):
        captured_args["warn_before_days"] = warn_before_days
        raise SystemExit(0)

    monkeypatch.setattr(
        sys, "argv", ["py-eol", "versions", "3.12", "--warn-before", "180"]
    )
    monkeypatch.setattr(cli_mod, "check_versions", mock_check_versions)
    with pytest.raises(SystemExit):
        cli_mod.main()
    assert captured_args["warn_before_days"] == 180
