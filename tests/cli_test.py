import sys
import pytest
import py_eol.cli as cli_mod


def test_main_version(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["py-eol", "--version"])
    monkeypatch.setattr(cli_mod, "__version__", lambda name: "1.2.3")
    with pytest.raises(SystemExit) as e:
        cli_mod.main()
    out = capsys.readouterr().out
    assert "1.2.3" in out
    assert e.value.code == 0


def test_main_refresh(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["py-eol", "--refresh"])
    monkeypatch.setattr(cli_mod, "sync_data", lambda: True)
    with pytest.raises(SystemExit) as e:
        cli_mod.main()
    out = capsys.readouterr().out
    assert "Refreshing" in out
    assert e.value.code == 0


def test_main_refresh_fail(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["py-eol", "--refresh"])
    monkeypatch.setattr(cli_mod, "sync_data", lambda: False)
    with pytest.raises(SystemExit) as e:
        cli_mod.main()
    out = capsys.readouterr().out
    assert "Failed to refresh" in out
    assert e.value.code == 1


def test_main_check_self(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["py-eol", "--check-self"])
    monkeypatch.setattr(
        cli_mod,
        "check_self",
        lambda output_json=False: (_ for _ in ()).throw(SystemExit(0)),
    )
    with pytest.raises(SystemExit) as e:
        cli_mod.main()
    assert e.value.code == 0


def test_main_list(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["py-eol", "--list"])
    monkeypatch.setattr(
        cli_mod,
        "list_supported_versions",
        lambda output_json=False: (_ for _ in ()).throw(SystemExit(0)),
    )
    with pytest.raises(SystemExit) as e:
        cli_mod.main()
    assert e.value.code == 0


def test_main_versions(monkeypatch, capsys):
    monkeypatch.setattr(sys, "argv", ["py-eol", "3.99"])
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

    class DummyParser:
        def add_argument(self, *a, **k):
            pass

        def parse_args(self):
            class Args:
                versions = []
                list = False
                json = False
                check_self = False
                refresh = False
                version = False

            return Args()

        def print_help(self):
            print("HELP CALLED")

    orig_parser = cli_mod.argparse.ArgumentParser
    monkeypatch.setattr(
        cli_mod.argparse, "ArgumentParser", lambda *a, **k: DummyParser()
    )
    try:
        with pytest.raises(SystemExit) as e:
            cli_mod.main()
        out = capsys.readouterr().out
        assert "HELP CALLED" in out
        assert e.value.code == 0
    finally:
        cli_mod.argparse.ArgumentParser = orig_parser


def test_check_versions_supported(monkeypatch, capsys):
    monkeypatch.setattr(
        cli_mod, "get_eol_date", lambda v: sys.modules["datetime"].date(2099, 1, 1)
    )
    monkeypatch.setattr(cli_mod, "is_eol", lambda v: False)
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
