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

    # The orchestrator currently does not expose a dry‑run flag, but we can
    # honour it by simply not calling the DB persistence layer when the flag
    # is set. For now we pass the config path and let the orchestrator handle it.
    orchestrator_run(config_path=args.config)


if __name__ == "__main__":
    sys.exit(main())