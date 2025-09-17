import requests
import datetime
from pathlib import Path

EOL_API_URL = "https://endoflife.date/api/python.json"
OUTPUT_FILE = Path(__file__).parent / "_eol_data.py"


def fetch_py_eol_data():
    """Fetch Python EOL data from endoflife.date API."""
    response = requests.get(EOL_API_URL)
    response.raise_for_status()
    return response.json()


def generate_eol_data_content(data):
    """Generate the content for _eol_data.py."""
    lines = ["import datetime", "", "EOL_DATES = {"]
    for entry in data:
        version = entry["cycle"]
        eol_date_str = entry["eol"]
        if not eol_date_str:
            continue  # skip if no EOL date

        try:
            eol_date = datetime.datetime.strptime(eol_date_str, "%Y-%m-%d").date()
            line = f'    "{version}": datetime.date({eol_date.year}, {eol_date.month}, {eol_date.day}),'
            lines.append(line)
        except ValueError:
            continue  # skip invalid date formats

    lines.append("}")
    lines.append("")
    return "\n".join(lines)


def save_eol_data(content: str):
    """Save generated content to _eol_data.py."""
    OUTPUT_FILE.write_text(content, encoding="utf-8")
    print(f"✅ Updated {OUTPUT_FILE}")


def sync_data() -> bool:
    """Sync the data to generate _eol_data.py."""
    try:
        data = fetch_py_eol_data()
        content = generate_eol_data_content(data)
        save_eol_data(content)
        return True
    except Exception:
        return False
