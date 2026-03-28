# py-eol

[![main](https://github.com/shenxianpeng/py-eol/actions/workflows/ci.yml/badge.svg)](https://github.com/shenxianpeng/py-eol/actions/workflows/ci.yml)
[![PyPI - Version](https://img.shields.io/pypi/v/py-eol)](https://pypi.org/project/py-eol/)
[![codecov](https://codecov.io/gh/shenxianpeng/py-eol/graph/badge.svg?token=7B23E012SN)](https://codecov.io/gh/shenxianpeng/py-eol)

Check if a Python version is **End-Of-Life (EOL)**.

## Table of Contents

- [Why py-eol?](#why-py-eol)
- [Installation](#installation)
- [Usage](#usage)
  - [As a Python module](#as-a-python-module)
  - [As a CLI tool](#as-a-cli-tool)
  - [As a GitHub Action](#as-a-github-action)
  - [As a pre-commit hook](#as-a-pre-commit-hook)
- [License](#license)

## Why py-eol?

* Programmatically check if a Python version is supported or EOL
* Works as a Python module, CLI tool, GitHub Action, and pre-commit hook
* Detects Python versions in `pyproject.toml`, `setup.py`, `.python-version`, `tox.ini`, `Dockerfile`, and GitHub Actions workflow files
* Early warning with `--warn-before DAYS` before a version reaches EOL
* Useful for local checks, automation scripts, and CI/CD pipelines

## Installation

```bash
pip install py-eol
```

## Usage

### As a Python module

```python
from py_eol import is_eol, get_eol_date, days_until_eol, is_eol_soon
from py_eol import supported_versions, eol_versions, latest_supported_version

print(is_eol("3.7"))                    # True
print(is_eol("3.12"))                   # False
print(get_eol_date("3.8"))              # 2024-10-07
print(days_until_eol("3.12"))           # e.g. 960 (days remaining)
print(is_eol_soon("3.10", 365))         # True if EOL within 365 days
print(supported_versions())             # ['3.14', '3.13', '3.12', '3.11', '3.10']
print(eol_versions())                   # ['3.9', '3.8', '3.7', ...]
print(latest_supported_version())       # 3.14
```

### As a CLI tool

```
py-eol --help
usage: py-eol [-h] [--version] {versions,files,list,check-self,refresh} ...

Check if a Python version is EOL (End Of Life).

positional arguments:
  {versions,files,list,check-self,refresh}
                        sub-command help
    versions            Check specific Python versions
    files               Check files for Python versions
    list                List all supported Python versions
    check-self          Check the current Python interpreter version
    refresh             Refresh the EOL data from peps.python.org

options:
  -h, --help            show this help message and exit
  --version             Show the version of the tool
```

**Examples**

```bash
# Check specific versions
py-eol versions 3.9
py-eol versions 3.7 3.8 3.11

# Warn if a version will be EOL within 180 days
py-eol versions 3.10 --warn-before 180

# Check files for EOL Python versions (shows file:line information)
# Supported: pyproject.toml, setup.py, .python-version, tox.ini, Dockerfile, GitHub Actions workflows
py-eol files pyproject.toml setup.py .python-version tox.ini Dockerfile .github/workflows/ci.yml

# Also warn about versions expiring within 90 days
py-eol files pyproject.toml Dockerfile --warn-before 90

# Check current Python interpreter
py-eol check-self

# List all currently supported versions
py-eol list

# Output result in JSON format (includes days_until_eol field)
py-eol versions 3.8 3.9 --json

# Refresh the latest EOL data from peps.python.org
py-eol refresh
```

**Exit codes**

| Code | Meaning |
|------|---------|
| `0` | All versions are supported |
| `1` | One or more versions are EOL (or EOL soon when `--warn-before` is set) |
| `2` | Unknown version encountered |

**Example output**

```
# Already EOL
⚠️ Python 3.9 is already EOL since 2025-10-31

# EOL soon (with --warn-before 400)
⏰ Python 3.10 will be EOL on 2026-10-31 (229 days remaining)

# Still supported
✅ Python 3.12 is still supported until 2028-10-31

# JSON output (py-eol versions 3.7 3.12 --json)
[
  {
    "version": "3.7",
    "status": "EOL",
    "eol_date": "2023-06-27",
    "days_until_eol": -993
  },
  {
    "version": "3.12",
    "status": "Supported",
    "eol_date": "2028-10-31",
    "days_until_eol": 960
  }
]
```

### As a GitHub Action

Add `py-eol` to your workflow to automatically check for EOL Python versions on every push or pull request:

```yaml
- name: Check Python EOL
  uses: shenxianpeng/py-eol@main
```

**With options:**

```yaml
- name: Check Python EOL
  uses: shenxianpeng/py-eol@main
  with:
    # Specific files to check (auto-detects common files if not set)
    files: "pyproject.toml .python-version Dockerfile .github/workflows/ci.yml"
    # Warn if a version will be EOL within 90 days
    warn-before: "90"
```

**Auto-detected files** (when `files` input is not set):
`pyproject.toml`, `setup.py`, `.python-version`, `tox.ini`, `Dockerfile`, `.github/workflows/*.yml`

**Full workflow example:**

```yaml
name: Check Python EOL

on:
  push:
  schedule:
    - cron: "0 8 * * 1"  # Every Monday

jobs:
  eol-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check Python EOL
        uses: shenxianpeng/py-eol@main
        with:
          warn-before: "180"
```

### As a pre-commit hook

> [!NOTE]
> This hook checks Python versions in `pyproject.toml`, `setup.py`, `.python-version`, `tox.ini`, `Dockerfile`, and GitHub Actions workflow files.
> When an EOL version is found, it reports the exact file and line number for easy identification.

Add the following to your `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/shenxianpeng/py-eol
    rev:  # Use the ref you want to point at
    hooks:
      - id: py-eol
```

Example output:

```
Check Python version EOL.................................................Failed
- hook id: py-eol
- exit code: 1

pyproject.toml:9: ⚠️ Python 3.7 is already EOL since 2023-06-27
.github/workflows/ci.yml:16: ⚠️ Python 3.9 is already EOL since 2025-10-31
Dockerfile:1: ⚠️ Python 3.8 is already EOL since 2024-10-07
```

## License

[MIT License](https://github.com/shenxianpeng/py-eol/blob/main/LICENSE)
