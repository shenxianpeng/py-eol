import calendar
import datetime
import requests
from pathlib import Path

EOL_API_URL = "https://peps.python.org/api/release-cycle.json"
OUTPUT_FILE = Path(__file__).parent / "_eol_data.py"


def fetch_py_eol_data():
    """Fetch Python EOL data from peps.python.org API."""
    response = requests.get(EOL_API_URL)
    response.raise_for_status()
    return response.json()


def generate_eol_data_content(data):
    """Generate the content for _eol_data.py."""
    lines = ["import datetime", "", "EOL_DATES = {"]
    for version, entry in data.items():
        eol_date_str = entry.get("end_of_life")
        if not eol_date_str:
            continue  # skip if no EOL date

        try:
            eol_date = datetime.datetime.strptime(eol_date_str, "%Y-%m-%d").date()
        except ValueError:
            try:
                # Handle year-month only format (e.g. "2028-10") by using last day of month
                dt = datetime.datetime.strptime(eol_date_str, "%Y-%m")
                last_day = calendar.monthrange(dt.year, dt.month)[1]
                eol_date = datetime.date(dt.year, dt.month, last_day)
            except ValueError:
                continue  # skip invalid date formats

        line = f'    "{version}": datetime.date({eol_date.year}, {eol_date.month}, {eol_date.day}),'
        lines.append(line)

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
