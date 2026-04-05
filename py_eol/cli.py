from pathlib import Path
import sys
import argparse
import json
from datetime import date
from py_eol.checker import (
    is_eol,
    get_eol_date,
    is_eol_soon,
    supported_versions,
    all_versions,
    get_version_info,
    _check_pyproject_toml,
    _check_setup_py,
    _check_github_actions,
    _check_python_version_file,
    _check_tox_ini,
    _check_dockerfile,
    _print_eol_warning,
    _print_eol_soon_warning,
    _print_supported_warning,
)
from py_eol.sync_data import sync_data
from importlib.metadata import version as __version__


def check_versions(versions, output_json=False, warn_before_days=0):
    results = []

    today = date.today()

    for version in versions:
        try:
            eol_date = get_eol_date(version)
            days_until_eol = (eol_date - today).days
            eol = is_eol(version)
            soon = (
                not eol
                and warn_before_days > 0
                and is_eol_soon(version, warn_before_days)
            )
            if eol:
                status = "EOL"
            elif soon:
                status = "EOL_SOON"
            else:
                status = "Supported"
            results.append(
                {
                    "version": version,
                    "status": status,
                    "eol_date": eol_date.isoformat(),
                    "days_until_eol": days_until_eol,
                }
            )
        except ValueError as e:
            results.append(
                {
                    "version": version,
                    "status": "Unknown",
                    "error": str(e),
                }
            )

    if output_json:
        print(json.dumps(results, indent=2))
    else:
        for r in results:
            if r["status"] == "Supported":
                _print_supported_warning(r["version"])
            elif r["status"] == "EOL":
                _print_eol_warning(r["version"])
            elif r["status"] == "EOL_SOON":
                _print_eol_soon_warning(r["version"])
            else:
                print(f"❌ Error checking {r['version']}: {r['error']}")

    if any(r["status"] == "Unknown" for r in results):
        sys.exit(2)
    elif any(r["status"] in ("EOL", "EOL_SOON") for r in results):
        sys.exit(1)
    else:
        sys.exit(0)


def list_supported_versions(output_json=False, show_all=False):
    versions = all_versions() if show_all else supported_versions()
    if output_json:
        rows = []
        for v in versions:
            try:
                info = get_version_info(v)
                rows.append(
                    {
                        "version": info["version"],
                        "release_date": info["release_date"].isoformat(),
                        "eol_date": info["eol_date"].isoformat(),
                        "is_eol": info["is_eol"],
                        "days_until_eol": info["days_until_eol"],
                    }
                )
            except ValueError:
                rows.append({"version": v})
        print(json.dumps(rows, indent=2))
    else:
        title = "All Python versions" if show_all else "Supported Python versions"
        print(f"{title}:")
        print(f"  {'Version':<10}{'Release Date':<15}{'EOL Date':<13}{'Status'}")
        print(f"  {'-' * 7:<10}{'-' * 12:<15}{'-' * 10:<13}{'-' * 9}")
        for v in versions:
            try:
                info = get_version_info(v)
                status = "EOL" if info["is_eol"] else "Supported"
                rel = info["release_date"].isoformat()
                eol = info["eol_date"].isoformat()
            except ValueError:
                status = "Unknown"
                rel = eol = "?"
            print(f"  {v:<10}{rel:<15}{eol:<13}{status}")
        if not show_all:
            print()
            print("  Tip: run with --all to include EOL versions.")
    sys.exit(0)


def show_version_info(version: str, output_json=False):
    """Show full lifecycle info for a single Python version (like endoflife.date)."""
    try:
        info = get_version_info(version)
    except ValueError as e:
        print(f"❌ {e}")
        sys.exit(2)

    if output_json:
        print(
            json.dumps(
                {
                    "version": info["version"],
                    "release_date": info["release_date"].isoformat(),
                    "eol_date": info["eol_date"].isoformat(),
                    "is_eol": info["is_eol"],
                    "days_until_eol": info["days_until_eol"],
                },
                indent=2,
            )
        )
    else:
        status = "EOL" if info["is_eol"] else "Supported"
        days = info["days_until_eol"]
        days_str = f"{abs(days)} days ago" if days < 0 else f"{days} days remaining"
        print(f"Python {info['version']}")
        print(f"  Release Date:   {info['release_date'].isoformat()}")
        print(f"  EOL Date:       {info['eol_date'].isoformat()}")
        print(f"  Days Until EOL: {days_str}")
        print(f"  Status:         {status}")
    sys.exit(0)


def check_self(output_json=False):
    current_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    check_versions([current_version], output_json=output_json)


def refresh_data():
    print("🔄 Refreshing Python EOL data...")
    success = sync_data()
    if success:
        print("🎉 Successfully refreshed EOL data.")
        sys.exit(0)
    else:
        print("❌ Failed to refresh EOL data.")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Check if a Python version is EOL (End Of Life)."
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"py-eol {__version__('py-eol')}",
        help="Show the version of the tool",
    )
    subparsers = parser.add_subparsers(dest="command", help="sub-command help")

    # versions command
    parser_versions = subparsers.add_parser(
        "versions", help="Check specific Python versions"
    )
    parser_versions.add_argument(
        "versions", nargs="+", help="Python versions to check, e.g., 3.11 3.12"
    )
    parser_versions.add_argument(
        "--json", action="store_true", help="Output result in JSON format"
    )
    parser_versions.add_argument(
        "--warn-before",
        type=int,
        default=0,
        metavar="DAYS",
        help="Warn if Python version will be EOL within DAYS days",
    )

    # files command
    parser_files = subparsers.add_parser(
        "files", help="Check files for Python versions"
    )
    parser_files.add_argument(
        "files",
        nargs="+",
        help=(
            "Files to check for Python versions, e.g., pyproject.toml, setup.py, "
            ".python-version, tox.ini, Dockerfile, GitHub Actions workflow files"
        ),
    )
    parser_files.add_argument(
        "--warn-before",
        type=int,
        default=0,
        metavar="DAYS",
        help="Warn if Python version will be EOL within DAYS days",
    )

    # list command
    parser_list = subparsers.add_parser(
        "list", help="List Python versions and their lifecycle status"
    )
    parser_list.add_argument(
        "--json", action="store_true", help="Output result in JSON format"
    )
    parser_list.add_argument(
        "--all",
        action="store_true",
        help="Include EOL versions in the listing",
    )

    # check-self command
    parser_check_self = subparsers.add_parser(
        "check-self", help="Check the current Python interpreter version"
    )
    parser_check_self.add_argument(
        "--json", action="store_true", help="Output result in JSON format"
    )

    # info command
    parser_info = subparsers.add_parser(
        "info", help="Show full lifecycle info for a Python version"
    )
    parser_info.add_argument("version", help="Python version to inspect, e.g., 3.12")
    parser_info.add_argument(
        "--json", action="store_true", help="Output result in JSON format"
    )

    # refresh command
    subparsers.add_parser("refresh", help="Refresh the EOL data from peps.python.org")

    args = parser.parse_args()

    if args.command == "versions":
        check_versions(
            args.versions, output_json=args.json, warn_before_days=args.warn_before
        )
    elif args.command == "files":
        warn_before_days = args.warn_before
        eol_found = False
        for file_path in args.files:
            file = Path(file_path)
            if file.name == "pyproject.toml":
                if _check_pyproject_toml(file, warn_before_days):
                    eol_found = True
            elif file.name == "setup.py":
                if _check_setup_py(file, warn_before_days):
                    eol_found = True
            elif file.name == ".python-version":
                if _check_python_version_file(file, warn_before_days):
                    eol_found = True
            elif file.name == "tox.ini":
                if _check_tox_ini(file, warn_before_days):
                    eol_found = True
            elif file.name.startswith("Dockerfile"):
                if _check_dockerfile(file, warn_before_days):
                    eol_found = True
            elif file.suffix in (".yml", ".yaml") and ".github/workflows" in str(file):
                if _check_github_actions(file, warn_before_days):
                    eol_found = True
        if eol_found:
            sys.exit(1)
    elif args.command == "list":
        list_supported_versions(output_json=args.json, show_all=args.all)
    elif args.command == "info":
        show_version_info(args.version, output_json=args.json)
    elif args.command == "check-self":
        check_self(output_json=args.json)
    elif args.command == "refresh":
        refresh_data()
    else:
        parser.print_help()
        sys.exit(0)
