"""
Refactored crawler module for MAFA.

This file now delegates the actual scraping logic to dedicated modules
(`mafa.crawler.immoscout` and `mafa.crawler.wg_gesucht`) and uses the
`SeleniumDriver` context manager for safe driver handling.
"""

import os
import json
from datetime import datetime

from mafa.driver import SeleniumDriver
from mafa.crawler.immoscout import scrape_immobilienscout24
from mafa.crawler.wg_gesucht import scrape_wg_gesucht

# Constants
DATA_DIR = "./data"


def create_data_directory() -> None:
    """Ensures the data directory exists."""
    os.makedirs(DATA_DIR, exist_ok=True)


def save_listings(listings: list[dict], filename: str) -> None:
    """Saves listings to a JSON file."""
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(listings, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print(f"Error saving listings: {e}")


def main() -> None:
    """Main function to run the crawlers."""
    create_data_directory()
    filename = os.path.join(
        DATA_DIR, f"listings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    )

    # Run both scrapers
    immobilienscout24_listings = scrape_immobilienscout24()
    wg_gesucht_listings = scrape_wg_gesucht()

    all_listings = immobilienscout24_listings + wg_gesucht_listings
    save_listings(all_listings, filename)
    print(f"Saved {len(all_listings)} listings to {filename}")


if __name__ == "__main__":
    main()
