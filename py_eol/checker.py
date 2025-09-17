import datetime
from py_eol._eol_data import EOL_DATES


def is_eol(version: str) -> bool:
    """Check if the given Python version is End-Of-Life."""
    eol_date = EOL_DATES.get(version)
    if not eol_date:
        raise ValueError(f"Unknown Python version: {version}")
    return datetime.date.today() > eol_date


def get_eol_date(version: str) -> datetime.date:
    """Get the EOL date for a given Python version."""
    eol_date = EOL_DATES.get(version)
    if not eol_date:
        raise ValueError(f"Unknown Python version: {version}")
    return eol_date


def supported_versions() -> list[str]:
    """Return a list of supported (non-EOL) Python versions."""
    today = datetime.date.today()
    return [v for v, eol in EOL_DATES.items() if today <= eol]


def eol_versions() -> list[str]:
    """Return a list of versions that are already EOL."""
    today = datetime.date.today()
    return [v for v, eol in EOL_DATES.items() if today > eol]


def latest_supported_version() -> str:
    """Return the latest supported Python version."""
    versions = supported_versions()
    if not versions:
        raise RuntimeError("No supported Python versions found.")
    return max(versions, key=lambda v: tuple(map(int, v.split("."))))
