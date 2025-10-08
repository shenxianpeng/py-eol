# py-eol

[![main](https://github.com/shenxianpeng/py-eol/actions/workflows/ci.yml/badge.svg)](https://github.com/shenxianpeng/py-eol/actions/workflows/ci.yml)
[![PyPI - Version](https://img.shields.io/pypi/v/py-eol)](https://pypi.org/project/py-eol/)
[![codecov](https://codecov.io/gh/shenxianpeng/py-eol/graph/badge.svg?token=7B23E012SN)](https://codecov.io/gh/shenxianpeng/py-eol)

Check if a Python version is **End-Of-Life (EOL)**.

## Why py-eol?

* Programmatically check if a Python version is supported or EOL
* Works both as a Python module and a CLI tool
* Useful for local checks, automation scripts, and CI/CD pipelines
* Helps teams avoid using unsupported Python versions

## Installation

```bash
pip install py-eol
```

## Usage

### As a Python module

```python
from py_eol import is_eol, get_eol_date, supported_versions, eol_versions, latest_supported_version

print(is_eol("3.7")) # True
print(get_eol_date("3.8")) # 2024-10-07
print(supported_versions()) # ['3.14', '3.13', '3.12', '3.11', '3.10', '3.9']
print(eol_versions()) # ['3.8', '3.7', '3.6', '3.5', '3.4', '3.3', '3.2', '2.7', '3.1', '3.0', '2.6']
print(latest_supported_version()) # 3.14
```

### As a CLI tool

```
py-eol --help
usage: py-eol [-h] [--list] [--json] [--check-self] [--refresh] [--version] [versions ...]

Check if a Python version is EOL (End Of Life).

positional arguments:
  versions      Python versions to check, e.g., 3.11 3.12

options:
  -h, --help    show this help message and exit
  --list        List all supported Python versions
  --json        Output result in JSON format
  --check-self  Check the current Python interpreter version
  --refresh     Refresh the EOL data from endoflife.date
  --version     Show the version of the tool
```

Examples

```bash
# Check a specific version
py-eol 3.9

# Check multiple versions
py-eol 3.7 3.8 3.11

# Check current Python interpreter
py-eol --check-self

# List all currently supported versions
py-eol --list

# Output result in JSON format
py-eol 3.8 3.9 --json

# Refresh the latest EOL data
py-eol --refresh
```

## License

[MIT License](https://github.com/shenxianpeng/py-eol/blob/main/LICENSE)
