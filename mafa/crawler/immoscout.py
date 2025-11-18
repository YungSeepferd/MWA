"""
ImmoScout24 scraper for MAFA.

Uses the ``SeleniumDriver`` context manager to obtain a head‑less Chrome
instance, navigates to the ImmoScout24 search page, extracts title and price
for each result, and returns a list of listing dictionaries.
"""

from datetime import datetime
from typing import List, Dict

from mafa.driver import SeleniumDriver
from selenium.webdriver.common.by import By

IMMOBILIENSCOUT24_URL = (
    "https://www.immobilienscout24.de/Suche/de/bayern/muenchen/wohnung-mieten"
)


def scrape_immobilienscout24() -> List[Dict]:
    """
    Scrape listings from ImmobilienScout24.

    Returns
    -------
    List[Dict]
        A list of dictionaries with keys: ``title``, ``price``, ``source``,
        and ``timestamp``.
    """
    listings: List[Dict] = []

    # Use the driver context manager – it handles driver installation,
    # headless configuration and proper cleanup.
    with SeleniumDriver() as driver:
        driver.get(IMMOBILIENSCOUT24_URL)

        try:
            items = driver.find_elements(By.CLASS_NAME, "result-list-entry")
            for item in items:
                title = item.find_element(By.CSS_SELECTOR, "h5").text.strip()
                price = item.find_element(By.CLASS_NAME, "price").text.strip()
                listings.append(
                    {
                        "title": title,
                        "price": price,
                        "source": "ImmobilienScout24",
                        "timestamp": datetime.now().isoformat(),
                    }
                )
        except Exception as e:
            # In production we would use structured logging; for now a simple print.
            print(f"Error scraping ImmobilienScout24: {e}")

    return listings