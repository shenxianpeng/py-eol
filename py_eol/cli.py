import sys
import argparse
import json
from py_eol.checker import is_eol, get_eol_date, supported_versions
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
                print(
                    f"✅ Python {r['version']} is still supported until {r['eol_date']}"
                )
            elif r["status"] == "EOL":
                print(f"⚠️  Python {r['version']} is already EOL since {r['eol_date']}")
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
        "versions", nargs="*", help="Python versions to check, e.g., 3.11 3.12"
    )
    parser.add_argument(
        "--list", action="store_true", help="List all supported Python versions"
    )
    parser.add_argument(
        "--json", action="store_true", help="Output result in JSON format"
    )
    parser.add_argument(
        "--check-self",
        action="store_true",
        help="Check the current Python interpreter version",
    )
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Refresh the EOL data from endoflife.date",
    )
    parser.add_argument(
        "--version", action="store_true", help="Show the version of the tool"
    )

    args = parser.parse_args()

    if args.version:
        print(f"py-eol {__version__('py-eol')}")
        sys.exit(0)
    if args.refresh:
        refresh_data()
    elif args.check_self:
        check_self(output_json=args.json)
    elif args.list:
        list_supported_versions(output_json=args.json)
    elif args.versions:
        check_versions(args.versions, output_json=args.json)
    else:
        parser.print_help()
        sys.exit(0)
