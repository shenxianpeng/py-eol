import calendar
import datetime
import requests
from pathlib import Path

EOL_API_URL = "https://peps.python.org/api/release-cycle.json"
OUTPUT_FILE = Path(__file__).parent / "_eol_data.py"


def _load_existing_release_dates() -> dict:
    """Load existing release dates from _eol_data.py as a fallback."""
    try:
        from py_eol._eol_data import PYTHON_VERSIONS

        return {
            version: info["release_date"]
            for version, info in PYTHON_VERSIONS.items()
            if "release_date" in info
        }
    except Exception:
        return {}


def fetch_py_eol_data():
    """Fetch Python EOL data from peps.python.org API."""
    response = requests.get(EOL_API_URL)
    response.raise_for_status()
    return response.json()


def _parse_date(date_str: str) -> datetime.date:
    """Parse a date string that is either YYYY-MM-DD or YYYY-MM (last day of month)."""
    try:
        return datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        dt = datetime.datetime.strptime(date_str, "%Y-%m")
        last_day = calendar.monthrange(dt.year, dt.month)[1]
        return datetime.date(dt.year, dt.month, last_day)


def generate_eol_data_content(data, existing_release_dates=None):
    """Generate the content for _eol_data.py."""
    if existing_release_dates is None:
        existing_release_dates = {}
    lines = ["import datetime", "", "PYTHON_VERSIONS = {"]
    for version, entry in data.items():
        eol_date_str = entry.get("end_of_life")
        if not eol_date_str:
            continue

        try:
            eol_date = _parse_date(eol_date_str)
        except ValueError:
            continue

        release_date = None
        release_date_str = entry.get("release")
        if release_date_str:
            try:
                release_date = _parse_date(release_date_str)
            except ValueError:
                pass

        # Fall back to the existing release date if the API didn't provide one
        if release_date is None and version in existing_release_dates:
            release_date = existing_release_dates[version]

        lines.append(f'    "{version}": {{')
        if release_date is not None:
            lines.append(
                f'        "release_date": datetime.date'
                f"({release_date.year}, {release_date.month}, {release_date.day}),"
            )
        lines.append(
            f'        "eol_date": datetime.date'
            f"({eol_date.year}, {eol_date.month}, {eol_date.day}),"
        )
        lines.append("    },")

    lines.append("}")
    lines.append("")
    lines.append('EOL_DATES = {k: v["eol_date"] for k, v in PYTHON_VERSIONS.items()}')
    lines.append("")
    return "\n".join(lines)


def save_eol_data(content: str):
    """Save generated content to _eol_data.py."""
    OUTPUT_FILE.write_text(content, encoding="utf-8")
    print(f"✅ Updated {OUTPUT_FILE}")


def sync_data() -> bool:
    """Sync the data to generate _eol_data.py."""
    try:
        existing_release_dates = _load_existing_release_dates()
        data = fetch_py_eol_data()
        content = generate_eol_data_content(data, existing_release_dates)
        save_eol_data(content)
        return True
    except Exception:
        return False
