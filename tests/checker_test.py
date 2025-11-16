import datetime
import pytest
import tempfile
import os
from py_eol import (
    is_eol,
    get_eol_date,
    supported_versions,
    eol_versions,
    latest_supported_version,
)
from py_eol.checker import (
    _check_pyproject_toml,
    _check_setup_py,
    _check_github_actions,
    _find_line_in_file,
    _print_eol_warning,
    _print_supported_warning,
)


def test_is_eol_known_version():
    assert is_eol("2.7") is True
    assert is_eol("3.7") is True
    assert isinstance(is_eol("3.12"), bool)


def test_is_eol_unknown_version():
    with pytest.raises(ValueError):
        is_eol("4.0")


def test_get_eol_date():
    date = get_eol_date("3.6")
    assert isinstance(date, datetime.date)


def test_get_eol_date_unknown_version():
    with pytest.raises(ValueError, match="Unknown Python version"):
        get_eol_date("4.0")


def test_supported_versions_not_empty():
    versions = supported_versions()
    assert isinstance(versions, list)
    assert all(isinstance(v, str) for v in versions)


def test_eol_versions_not_empty():
    versions = eol_versions()
    assert isinstance(versions, list)
    assert all(isinstance(v, str) for v in versions)


def test_latest_supported_version():
    version = latest_supported_version()
    assert isinstance(version, str)


def test_latest_supported_version_no_supported(monkeypatch):
    # Monkeypatch EOL_DATES so all versions are EOL
    import py_eol.checker as checker

    old_eol_dates = checker.EOL_DATES.copy()
    try:
        all_past = {k: datetime.date(2000, 1, 1) for k in checker.EOL_DATES}
        monkeypatch.setattr(checker, "EOL_DATES", all_past)
        with pytest.raises(RuntimeError, match="No supported Python versions found."):
            checker.latest_supported_version()
    finally:
        monkeypatch.setattr(checker, "EOL_DATES", old_eol_dates)


def test_find_line_in_file():
    content = "line 1\nline 2\nline 3 with text\nline 4"
    assert _find_line_in_file(content, "text") == 3
    assert _find_line_in_file(content, "line 1") == 1
    assert _find_line_in_file(content, "not found") == 0


def test_print_eol_warning_no_file(capsys):
    _print_eol_warning("3.7")
    captured = capsys.readouterr()
    assert "⚠️ Python 3.7 is already EOL" in captured.out
    assert "2023-06-27" in captured.out


def test_print_eol_warning_with_file(capsys):
    _print_eol_warning("3.7", "test.py")
    captured = capsys.readouterr()
    assert "test.py: ⚠️ Python 3.7 is already EOL" in captured.out


def test_print_eol_warning_with_file_and_line(capsys):
    _print_eol_warning("3.7", "test.py", 42)
    captured = capsys.readouterr()
    assert "test.py:42: ⚠️ Python 3.7 is already EOL" in captured.out


def test_print_supported_warning(capsys):
    _print_supported_warning("3.12")
    captured = capsys.readouterr()
    assert "✅ Python 3.12 is still supported" in captured.out


def test_check_pyproject_toml_eol(capsys):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write('[project]\nrequires-python = ">=3.7"\n')
        f.flush()
        temp_file = f.name

    try:
        result = _check_pyproject_toml(temp_file)
        assert result is True
        captured = capsys.readouterr()
        assert "⚠️ Python 3.7 is already EOL" in captured.out
        assert temp_file in captured.out
        assert ":2:" in captured.out
    finally:
        os.unlink(temp_file)


def test_check_pyproject_toml_supported(capsys):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write('[project]\nrequires-python = ">=3.12"\n')
        f.flush()
        temp_file = f.name

    try:
        result = _check_pyproject_toml(temp_file)
        assert result is False
        captured = capsys.readouterr()
        assert "EOL" not in captured.out
    finally:
        os.unlink(temp_file)


def test_check_pyproject_toml_no_requires_python():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".toml", delete=False) as f:
        f.write('[project]\nname = "test"\n')
        f.flush()
        temp_file = f.name

    try:
        result = _check_pyproject_toml(temp_file)
        assert result is False
    finally:
        os.unlink(temp_file)


def test_check_setup_py_eol(capsys):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            'from setuptools import setup\nsetup(\n    python_requires=">=3.7"\n)\n'
        )
        f.flush()
        temp_file = f.name

    try:
        result = _check_setup_py(temp_file)
        assert result is True
        captured = capsys.readouterr()
        assert "⚠️ Python 3.7 is already EOL" in captured.out
        assert temp_file in captured.out
    finally:
        os.unlink(temp_file)


def test_check_setup_py_supported(capsys):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(
            'from setuptools import setup\nsetup(\n    python_requires=">=3.12"\n)\n'
        )
        f.flush()
        temp_file = f.name

    try:
        result = _check_setup_py(temp_file)
        assert result is False
        captured = capsys.readouterr()
        assert "EOL" not in captured.out
    finally:
        os.unlink(temp_file)


def test_check_setup_py_no_python_requires():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write('from setuptools import setup\nsetup(name="test")\n')
        f.flush()
        temp_file = f.name

    try:
        result = _check_setup_py(temp_file)
        assert result is False
    finally:
        os.unlink(temp_file)


def test_check_github_actions_eol_matrix(capsys):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write("""name: CI
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.7", "3.12"]
    steps:
      - uses: actions/checkout@v2
""")
        f.flush()
        temp_file = f.name

    try:
        result = _check_github_actions(temp_file)
        assert result is True
        captured = capsys.readouterr()
        assert "⚠️ Python 3.7 is already EOL" in captured.out
        assert temp_file in captured.out
    finally:
        os.unlink(temp_file)


def test_check_github_actions_eol_setup_python(capsys):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write("""name: CI
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: "3.7"
""")
        f.flush()
        temp_file = f.name

    try:
        result = _check_github_actions(temp_file)
        assert result is True
        captured = capsys.readouterr()
        assert "⚠️ Python 3.7 is already EOL" in captured.out
    finally:
        os.unlink(temp_file)


def test_check_github_actions_supported(capsys):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write("""name: CI
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.12", "3.13"]
    steps:
      - uses: actions/checkout@v2
""")
        f.flush()
        temp_file = f.name

    try:
        result = _check_github_actions(temp_file)
        assert result is False
        captured = capsys.readouterr()
        assert "EOL" not in captured.out
    finally:
        os.unlink(temp_file)


def test_check_github_actions_with_x_version(capsys):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write("""name: CI
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.x"]
    steps:
      - uses: actions/checkout@v2
""")
        f.flush()
        temp_file = f.name

    try:
        result = _check_github_actions(temp_file)
        assert result is False
    finally:
        os.unlink(temp_file)


def test_check_github_actions_with_x_in_setup_python(capsys):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write("""name: CI
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: "3.x"
""")
        f.flush()
        temp_file = f.name

    try:
        result = _check_github_actions(temp_file)
        assert result is False
    finally:
        os.unlink(temp_file)


def test_check_github_actions_no_python_version():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        f.write("""name: CI
on: push
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
""")
        f.flush()
        temp_file = f.name

    try:
        result = _check_github_actions(temp_file)
        assert result is False
    finally:
        os.unlink(temp_file)
