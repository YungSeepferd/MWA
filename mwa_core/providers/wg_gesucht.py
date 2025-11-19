"""
WG-Gesucht provider for MWA Core.
Implements the Provider protocol using Selenium.
"""

from datetime import datetime
from typing import List, Dict, Any

from selenium.webdriver.common.by import By
from mwa_core.scraper.base import Provider, Listing
from mafa.driver import SeleniumDriver


class WGGesuchtProvider(Provider):
    """
    Scrapes listings from WG-Gesucht.
    """

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url or "https://www.wg-gesucht.de/wg-gesucht/muenchen.html"

    def fetch_listings(self, config: Dict[str, Any]) -> List[Listing]:
        """
        Fetch listings from WG-Gesucht.

        Parameters
        ----------
        config : dict
            Optional overrides:
            - base_url: str
            - headless: bool (default True)

        Returns
        -------
        list[Listing]
            Canonical listing objects.
        """
        base_url = config.get("base_url", self.base_url)
        headless = config.get("headless", True)

        listings: List[Listing] = []

        with SeleniumDriver(headless=headless) as driver:
            driver.get(base_url)
            try:
                items = driver.find_elements(By.CLASS_NAME, "listing")
                for item in items:
                    title = item.find_element(By.TAG_NAME, "h2").text.strip()
                    price = item.find_element(By.CLASS_NAME, "price").text.strip()
                    url = item.find_element(By.TAG_NAME, "a").get_attribute("href") or ""
                    listings.append(
                        Listing(
                            title=title,
                            price=price,
                            source="WG Gesucht",
                            url=url,
                            timestamp=datetime.utcnow(),
                        )
                    )
            except Exception as e:
                print(f"[WGGesuchtProvider] Error scraping: {e}")

        return listings