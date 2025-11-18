from datetime import datetime
from typing import List, Dict

from mafa.driver import SeleniumDriver
from selenium.webdriver.common.by import By
from .base import BaseProvider


class WGGesuchtProvider:
    """Provider for WG‑Gesucht."""

    URL = "https://www.wg-gesucht.de/wg-gesucht/muenchen.html"

    def scrape(self) -> List[Dict]:
        listings: List[Dict] = []
        with SeleniumDriver() as driver:
            driver.get(self.URL)
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