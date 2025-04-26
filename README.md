# python-eol

Check if a Python version is End-Of-Life (EOL).

## Installation

```bash
pip install python-eol
```

## Usage

```python
from python_eol import is_eol, get_eol_date

print(is_eol("3.7"))  # True
print(get_eol_date("3.8"))  # 2024-10-14
```

```bash
python-eol --help
usage: python-eol [-h] [--list] [--json] [--check-self] [--refresh] [versions ...]

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

Check a specific version

```bash
python-eol 3.9
```

Check multiple versions

```bash
python-eol 3.7 3.8 3.11
```

Check current Python interpreter

```bash
python-eol --check-self
```

List all currently supported versions

```bash
python-eol --list
```

Output as JSON

```bash
python-eol 3.8 3.9 --json
```

Refresh the latest EOL data

```bash
python-eol --refresh
```

## License

[MIT](LICENSE)
