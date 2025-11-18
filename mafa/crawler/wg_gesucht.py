"""
WG‑Gesucht scraper for MAFA.

Leverages the ``SeleniumDriver`` context manager to launch a head‑less Chrome
instance, visits the WG‑Gesucht search page for Munich, extracts the title and
price of each listing, and returns a list of dictionaries.
"""

from datetime import datetime
from typing import List, Dict

from mafa.driver import SeleniumDriver
from selenium.webdriver.common.by import By

WG_GESUCHT_URL = "https://www.wg-gesucht.de/wg-gesucht/muenchen.html"


def scrape_wg_gesucht() -> List[Dict]:
    """
    Scrape listings from WG‑Gesucht.

    Returns
    -------
    List[Dict]
        A list of dictionaries with keys: ``title``, ``price``, ``source``,
        and ``timestamp``.
    """
    listings: List[Dict] = []

    with SeleniumDriver() as driver:
        driver.get(WG_GESUCHT_URL)

        try:
            items = driver.find_elements(By.CLASS_NAME, "listing")
            for item in items:
                title = item.find_element(By.TAG_NAME, "h2").text.strip()
                price = item.find_element(By.CLASS_NAME, "price").text.strip()
                listings.append(
                    {
                        "title": title,
                        "price": price,
                        "source": "WG Gesucht",
                        "timestamp": datetime.now().isoformat(),
                    }
                )
        except Exception as e:
            print(f"Error scraping WG Gesucht: {e}")

    return listings