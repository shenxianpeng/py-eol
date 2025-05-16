# py-eol

[![main](https://github.com/shenxianpeng/py-eol/actions/workflows/ci.yml/badge.svg)](https://github.com/shenxianpeng/py-eol/actions/workflows/ci.yml)
![PyPI - Version](https://img.shields.io/pypi/v/py-eol)


Check if a Python version is End-Of-Life (EOL).

## Installation

```bash
pip install py-eol
```

## Usage

Use the `py_eol` package as a module

```python
from py_eol import is_eol, get_eol_date, supported_versions, eol_versions, latest_supported_version

print(is_eol("3.7")) # True
print(get_eol_date("3.8")) # 2024-10-14
print(supported_versions()) # ['3.9', '3.10', '3.11', '3.12', '3.13', '3.14']
print(eol_versions()) # ['2.7', '3.6', '3.7', '3.8']
print(latest_supported_version()) # 3.14
```

Use the `py-eol` as a command-line tool

```bash
py-eol --help
usage: py-eol [-h] [--list] [--json] [--check-self] [--refresh] [versions ...]

Check if a Python version is EOL (End Of Life).

positional arguments:
  versions      Python versions to check, e.g., 3.11 3.12

options:
  -h, --help    show this help message and exit
  --list        List all supported Python versions.
  --json        Output result in JSON format.
  --check-self  Check the current Python interpreter version.
  --refresh     Refresh the EOL data from endoflife.date
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

[MIT](https://github.com/shenxianpeng/py-eol/blob/main/LICENSE)
