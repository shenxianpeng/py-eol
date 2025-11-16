import requests
import datetime
from pathlib import Path

PEP_API_URL = "https://peps.python.org/api/release-cycle.json"
EOL_API_URL = "https://endoflife.date/api/python.json"
OUTPUT_FILE = Path(__file__).parent / "_eol_data.py"


def fetch_py_eol_data():
    """Fetch Python EOL data from PEP API, falling back to endoflife.date API."""
    # Try PEP API first
    try:
        response = requests.get(PEP_API_URL, timeout=10)
        response.raise_for_status()
        data = response.json()
        # If data is valid, return it in normalized format
        return normalize_pep_data(data)
    except Exception:
        # Fall back to endoflife.date API
        response = requests.get(EOL_API_URL, timeout=10)
        response.raise_for_status()
        return response.json()


def normalize_pep_data(data):
    """Normalize PEP API data to match endoflife.date format."""
    # The PEP API format may differ, so we normalize it
    # Expected PEP format: list of dicts with version info and end_of_life
    normalized = []
    for entry in data:
        # Handle different possible field names
        version = entry.get("version") or entry.get("cycle")
        eol_date = entry.get("end_of_life") or entry.get("eol")
        
        if version and eol_date:
            normalized.append({
                "cycle": str(version),
                "eol": str(eol_date)
            })
    
    return normalized


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
