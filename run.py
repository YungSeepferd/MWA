"""
Command‑line entry point for MAFA.

Usage
-----
    python run.py [--config PATH] [--dry-run]

Options
-------
    --config PATH   Path to a custom ``config.json`` file. If omitted the default
                    ``config.json`` (or ``config.example.json``) is used.
    --dry-run       Perform the crawl and generate the CSV report without
                    persisting listings to the SQLite database.
"""

import argparse
import sys
from pathlib import Path

from mafa.orchestrator import run as orchestrator_run


def main() -> None:
    parser = argparse.ArgumentParser(description="Munich Apartment Finder Assistant (MAFA)")
    parser.add_argument(
        "--config",
        type=Path,
        help="Path to a custom config.json file",
        default=None,
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without persisting to the database (useful for testing)",
    )
    args = parser.parse_args()

    # Pass the dry-run flag to the orchestrator
    orchestrator_run(config_path=args.config, dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())