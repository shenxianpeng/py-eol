import datetime
import re
from typing import Optional
import yaml
from py_eol._eol_data import EOL_DATES
from packaging.specifiers import SpecifierSet
from packaging.version import Version


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


def days_until_eol(version: str) -> int:
    """Return the number of days until EOL (negative if already EOL)."""
    eol_date = get_eol_date(version)
    delta = eol_date - datetime.date.today()
    return delta.days


def is_eol_soon(version: str, warn_before_days: int) -> bool:
    """Check if the given Python version will be EOL within the specified days."""
    days = days_until_eol(version)
    return 0 < days <= warn_before_days


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


def _min_required_version(specifier_str: str) -> Optional[str]:
    """Return the minimum required Python version from a specifier string.

    Takes the highest lower-bound among >=, ==, and ~= specifiers.
    Returns None if no lower-bound specifier is found.
    """
    lower_bounds = [
        Version(spec.version)
        for spec in SpecifierSet(specifier_str)
        if spec.operator in (">=", "==", "~=")
    ]
    if not lower_bounds:
        return None
    return str(max(lower_bounds))


def _normalize_version(version: str) -> str:
    """Normalize version strings like '3.12.0' to '3.12' for EOL lookup."""
    text = str(version).strip()
    match = re.match(r"^(\d+)\.(\d+)(?:\.\d+)?$", text)
    if match:
        major, minor = match.group(1), match.group(2)
        return f"{major}.{minor}"
    return text


def _check_version_status(
    version: str,
    file_path: str = "",
    line_num: int = 0,
    warn_before_days: int = 0,
) -> bool:
    """Check version EOL status and print appropriate warning. Returns True if action needed."""
    try:
        normalized_version = _normalize_version(version)
        if is_eol(normalized_version):
            _print_eol_warning(normalized_version, file_path, line_num)
            return True
        elif warn_before_days > 0 and is_eol_soon(normalized_version, warn_before_days):
            _print_eol_soon_warning(normalized_version, file_path, line_num)
            return True
        else:
            _print_supported_warning(normalized_version, file_path, line_num)
    except ValueError:
        pass
    return False


def _check_github_actions(file_path: str, warn_before_days: int = 0) -> bool:
    """Check if any Python version in the GitHub Actions workflow is EOL."""
    with open(file_path, "r") as f:
        content = f.read()
        workflow = yaml.safe_load(content)

    found_eol = False
    jobs = workflow.get("jobs", {})
    for job_name, job in jobs.items():
        strategy = job.get("strategy", {})
        matrix = strategy.get("matrix", {})
        python_versions = matrix.get("python-version", [])
        for version in python_versions:
            version_str = str(version)
            if "x" in version_str:
                continue
            normalized_version = _normalize_version(version_str)
            line_num = _find_line_in_file(content, version_str)
            if _check_version_status(
                normalized_version, file_path, line_num, warn_before_days
            ):
                found_eol = True

        steps = job.get("steps", [])
        for step in steps:
            if "uses" in step and "actions/setup-python" in step["uses"]:
                python_version = step.get("with", {}).get("python-version")
                if python_version:
                    python_version_str = str(python_version)
                    if "x" in python_version_str:
                        continue
                    normalized_python_version = _normalize_version(python_version_str)
                    line_num = _find_line_in_file(content, python_version_str)
                    if _check_version_status(
                        normalized_python_version,
                        file_path,
                        line_num,
                        warn_before_days,
                    ):
                        found_eol = True
    return found_eol


def _check_pyproject_toml(file_path: str, warn_before_days: int = 0) -> bool:
    """Check if the Python version specified in pyproject.toml is EOL."""
    with open(file_path, encoding="utf-8") as f:
        content = f.read()
    match = re.search(r'requires-python\s*=\s*"(.*?)"', content)
    if not match:
        return False

    min_version = _min_required_version(match.group(1))
    if not min_version:
        return False
    line_num = _find_line_in_file(content, match.group(0))
    return _check_version_status(min_version, file_path, line_num, warn_before_days)


def _check_setup_py(file_path: str, warn_before_days: int = 0) -> bool:
    """Check if the Python version specified in setup.py is EOL."""
    with open(file_path, encoding="utf-8") as f:
        content = f.read()
    match = re.search(r"python_requires\s*=\s*['\"](.*?)['\"]", content)
    if not match:
        return False

    min_version = _min_required_version(match.group(1))
    if not min_version:
        return False
    line_num = _find_line_in_file(content, match.group(0))
    return _check_version_status(min_version, file_path, line_num, warn_before_days)


def _check_python_version_file(file_path: str, warn_before_days: int = 0) -> bool:
    """Check if the Python version in .python-version file is EOL."""
    with open(file_path, encoding="utf-8") as f:
        content = f.read().strip()
    match = re.match(r"^(\d+\.\d+)", content)
    if not match:
        return False
    version = match.group(1)
    return _check_version_status(version, file_path, 1, warn_before_days)


def _check_tox_ini(file_path: str, warn_before_days: int = 0) -> bool:
    """Check if any Python version in tox.ini envlist is EOL."""
    content = open(file_path).read()
    found_eol = False
    match = re.search(r"envlist\s*=\s*(.+?)(?:\n\s*\n|\Z)", content, re.DOTALL)
    if not match:
        return False
    envlist_str = match.group(1)
    for env_match in re.finditer(r"py(\d)(\d+)", envlist_str):
        major = env_match.group(1)
        minor = env_match.group(2)
        version = f"{major}.{minor}"
        line_num = _find_line_in_file(content, env_match.group(0))
        if _check_version_status(version, file_path, line_num, warn_before_days):
            found_eol = True
    return found_eol


def _check_dockerfile(file_path: str, warn_before_days: int = 0) -> bool:
    """Check if the Python version in Dockerfile FROM instructions is EOL."""
    content = open(file_path).read()
    found_eol = False
    for match in re.finditer(r"FROM\s+python:(\d+\.\d+)", content, re.IGNORECASE):
        version = match.group(1)
        line_num = _find_line_in_file(content, match.group(0))
        if _check_version_status(version, file_path, line_num, warn_before_days):
            found_eol = True
    return found_eol


def _find_line_in_file(content: str, search_text: str) -> int:
    """Find the line number where search_text appears in content."""
    lines = content.split("\n")
    for i, line in enumerate(lines, start=1):
        if search_text in line:
            return i
    return 0


def _print_eol_warning(version: str, file_path: str = "", line_num: int = 0):
    """Print a warning if the given Python version is EOL."""
    eol_date = get_eol_date(version)
    msg = f"⚠️ Python {version} is already EOL since {eol_date.isoformat()}"
    if file_path and line_num:
        msg = f"{file_path}:{line_num}: {msg}"
    elif file_path:
        msg = f"{file_path}: {msg}"
    print(msg)


def _print_eol_soon_warning(version: str, file_path: str = "", line_num: int = 0):
    """Print a warning if the given Python version will be EOL soon."""
    eol_date = get_eol_date(version)
    days = days_until_eol(version)
    msg = f"⏰ Python {version} will be EOL on {eol_date.isoformat()} ({days} days remaining)"
    if file_path and line_num:
        msg = f"{file_path}:{line_num}: {msg}"
    elif file_path:
        msg = f"{file_path}: {msg}"
    print(msg)


def _print_supported_warning(version: str, file_path: str = "", line_num: int = 0):
    """Print a message if the given Python version is still supported."""
    eol_date = get_eol_date(version)
    msg = f"✅ Python {version} is still supported until {eol_date.isoformat()}"
    if file_path and line_num:
        msg = f"{file_path}:{line_num}: {msg}"
    elif file_path:
        msg = f"{file_path}: {msg}"
    print(msg)
