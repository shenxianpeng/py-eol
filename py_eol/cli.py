from pathlib import Path
import sys
import argparse
import json
from py_eol.checker import (
    is_eol,
    get_eol_date,
    supported_versions,
    _check_pyproject_toml,
    _check_setup_py,
    _check_github_actions,
    _print_eol_warning,
    _print_supported_warning,
)
from py_eol.sync_data import sync_data
from importlib.metadata import version as __version__


def check_versions(versions, output_json=False):
    results = []

    for version in versions:
        try:
            eol_date = get_eol_date(version)
            status = "EOL" if is_eol(version) else "Supported"
            results.append(
                {
                    "version": version,
                    "status": status,
                    "eol_date": eol_date.isoformat(),
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
            else:
                print(f"❌ Error checking {r['version']}: {r['error']}")

    if any(r["status"] == "Unknown" for r in results):
        sys.exit(2)
    elif any(r["status"] == "EOL" for r in results):
        sys.exit(1)
    else:
        sys.exit(0)


def list_supported_versions(output_json=False):
    versions = supported_versions()
    if output_json:
        print(json.dumps(versions, indent=2))
    else:
        print("✅ Supported Python versions:")
        for v in versions:
            print(f"  - {v}")
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

    # files command
    parser_files = subparsers.add_parser(
        "files", help="Check files for Python versions"
    )
    parser_files.add_argument(
        "files",
        nargs="+",
        help="Files to check for Python versions, e.g., pyproject.toml, setup.py, GitHub Actions workflow files",
    )

    # list command
    parser_list = subparsers.add_parser(
        "list", help="List all supported Python versions"
    )
    parser_list.add_argument(
        "--json", action="store_true", help="Output result in JSON format"
    )

    # check-self command
    parser_check_self = subparsers.add_parser(
        "check-self", help="Check the current Python interpreter version"
    )
    parser_check_self.add_argument(
        "--json", action="store_true", help="Output result in JSON format"
    )

    # refresh command
    subparsers.add_parser("refresh", help="Refresh the EOL data from endoflife.date")

    args = parser.parse_args()

    if args.command == "versions":
        check_versions(args.versions, output_json=args.json)
    elif args.command == "files":
        eol_found = False
        for file_path in args.files:
            file = Path(file_path)
            if file.name == "pyproject.toml":
                if _check_pyproject_toml(file):
                    eol_found = True
            elif file.name == "setup.py":
                if _check_setup_py(file):
                    eol_found = True
            elif file.suffix in (".yml", ".yaml") and ".github/workflows" in str(file):
                if _check_github_actions(file):
                    eol_found = True
        if eol_found:
            sys.exit(1)
    elif args.command == "list":
        list_supported_versions(output_json=args.json)
    elif args.command == "check-self":
        check_self(output_json=args.json)
    elif args.command == "refresh":
        refresh_data()
    else:
        parser.print_help()
        sys.exit(0)
