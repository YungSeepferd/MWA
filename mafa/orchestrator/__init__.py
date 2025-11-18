"""
Orchestrator for MAFA.

Coordinates configuration loading, crawling, persistence and (future) notification.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

from loguru import logger

from mafa.config.settings import Settings
from mafa.crawler.immoscout import scrape_immobilienscout24
from mafa.crawler.wg_gesucht import scrape_wg_gesucht
from mafa.db.manager import ListingRepository
# The original implementation sent notifications via Telegram.
# For the simplified version we generate a local CSV report instead,
# so the Telegram notifier import is no longer required.

# Configure loguru – in a real project you might forward to the standard logging module.
logger.remove()
logger.add(
    sys.stderr,
    level="INFO",
    format="{time} | {level} | {message}",
)


def _price_to_int(price_str: str) -> int:
    """
    Convert a price string like \"1.200 €\" or \"€1.200\" to an integer number of euros.
    Non‑numeric characters are stripped; commas and periods are treated as thousand
    separators. Returns 0 if conversion fails.
    """
    # Remove any non‑digit characters (including currency symbols, spaces, etc.)
    cleaned = re.sub(r"[^\d]", "", price_str)
    try:
        return int(cleaned)
    except ValueError:
        return 0


def _filter_listings(listings: list[dict], criteria: Settings.search_criteria) -> list[dict]:
    """
    Filter listings according to the user's search criteria.

    - ``max_price``: keep listings with a price <= max_price.
    - ``zip_codes``: keep listings whose title contains any of the zip codes.
    - ``min_rooms``: not implemented here because the source does not expose room count.
    """
    filtered = []
    for listing in listings:
        price = _price_to_int(listing.get("price", ""))
        if price > criteria.max_price:
            continue
        # Simple zip‑code check: look for any zip code substring in the title.
        title = listing.get("title", "")
        if any(zip_code in title for zip_code in criteria.zip_codes):
            filtered.append(listing)
    return filtered


def run(config_path: Path | None = None) -> None:
    """
    Entry point for the MAFA orchestrator.

    Parameters
    ----------
    config_path : Path | None
        Optional path to a custom ``config.json`` file. If omitted the default
        location ``config.json`` (or ``config.example.json`` as a fallback) is used.
    """
    # Load settings – the Settings class handles validation and fallback.
    settings = Settings.load(path=Path(config_path) if config_path else None)

    # Initialise the SQLite repository.
    repo = ListingRepository()

    # Run both scrapers.
    immo_listings = scrape_immobilienscout24()
    wg_listings = scrape_wg_gesucht()
    all_listings = immo_listings + wg_listings

    # Persist new listings, skipping duplicates.
    new_count = repo.bulk_add(all_listings)
    logger.info(f"Persisted {new_count} new listings (out of {len(all_listings)} total).")

    # Filter listings according to the user's search criteria.
    matching = _filter_listings(all_listings, settings.search_criteria)

    # Generate a simple CSV report for the matching listings.
    if matching:
        import csv
        from datetime import datetime
        report_path = Path(__file__).resolve().parents[3] / "data" / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        try:
            with open(report_path, mode="w", newline="", encoding="utf-8") as csvfile:
                fieldnames = ["title", "price", "source", "timestamp"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                for listing in matching:
                    writer.writerow({
                        "title": listing.get("title", ""),
                        "price": listing.get("price", ""),
                        "source": listing.get("source", ""),
                        "timestamp": listing.get("timestamp", "")
                    })
            logger.info(f"Generated CSV report with {len(matching)} listings at {report_path}")
        except Exception as e:
            logger.error(f"Failed to write CSV report: {e}")
    else:
        logger.info("No new listings matched the search criteria.")