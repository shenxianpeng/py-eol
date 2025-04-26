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

## Update EOL Data

```bash
python src/python_eol/sync_data.py
```