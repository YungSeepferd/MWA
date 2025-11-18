from datetime import datetime
from typing import List, Dict

from mafa.driver import SeleniumDriver
from selenium.webdriver.common.by import By
from .base import BaseProvider


class ImmoScoutProvider:
    """Provider for ImmobilienScout24."""

    URL = (
        "https://www.immobilienscout24.de/Suche/de/bayern/muenchen/wohnung-mieten"
    )

    def scrape(self) -> List[Dict]:
        listings: List[Dict] = []
        with SeleniumDriver() as driver:
            driver.get(self.URL)
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
                print(f"Error scraping ImmobilienScout24: {e}")
        return listings