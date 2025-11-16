import datetime
import re
import yaml
from py_eol._eol_data import EOL_DATES
from packaging.specifiers import SpecifierSet


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


def _check_github_actions(file_path: str) -> bool:
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
            if "x" in str(version):
                continue
            if is_eol(version):
                line_num = _find_line_in_file(content, str(version))
                _print_eol_warning(version, file_path, line_num)
                found_eol = True

        steps = job.get("steps", [])
        for step in steps:
            if "uses" in step and "actions/setup-python" in step["uses"]:
                python_version = step.get("with", {}).get("python-version")
                if python_version:
                    if "x" in str(python_version):
                        continue
                    if is_eol(python_version):
                        line_num = _find_line_in_file(content, str(python_version))
                        _print_eol_warning(python_version, file_path, line_num)
                        found_eol = True
    return found_eol


def _check_pyproject_toml(file_path: str) -> bool:
    """Check if the Python version specified in pyproject.toml is EOL."""
    content = open(file_path).read()
    match = re.search(r'requires-python\s*=\s*"(.*?)"', content)
    if not match:
        return False

    specifier = SpecifierSet(match.group(1))
    min_version = min(specifier).version
    if is_eol(min_version):
        line_num = _find_line_in_file(content, match.group(0))
        _print_eol_warning(min_version, file_path, line_num)
        return True
    return False


def _check_setup_py(file_path: str) -> bool:
    """Check if the Python version specified in setup.py is EOL."""
    content = open(file_path).read()
    match = re.search(r"python_requires\s*=\s*['\"](.*?)['\"]", content)
    if not match:
        return False

    specifier = SpecifierSet(match.group(1))
    min_version = min(specifier).version
    if is_eol(min_version):
        line_num = _find_line_in_file(content, match.group(0))
        _print_eol_warning(min_version, file_path, line_num)
        return True
    return False


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


def _print_supported_warning(version: str):
    """Print a message if the given Python version is still supported."""
    eol_date = get_eol_date(version)
    print(f"✅ Python {version} is still supported until {eol_date.isoformat()}")
