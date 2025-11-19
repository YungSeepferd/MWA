from datetime import datetime
from typing import List, Dict
import time
import random

from mafa.driver import SeleniumDriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .base import BaseProvider
from ..exceptions import ProviderError, ScrapingError
from ..config.settings import Settings
from ..security import SecurityValidator


class WGGesuchtProvider:
    """Provider for WG‑Gesucht."""

    URL = "https://www.wg-gesucht.de/wg-gesucht/muenchen.html"

    def __init__(self, config: Settings | None = None):
        self.config = config
        self.max_retries = 3
        self.retry_delay = 2

    def scrape(self) -> List[Dict]:
        """Scrape listings from WG-Gesucht with retry logic and error handling."""
        listings: List[Dict] = []
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                with SeleniumDriver() as driver:
                    driver.set_page_load_timeout(30)
                    driver.get(self.URL)
                    
                    # Add random delay to avoid detection
                    time.sleep(random.uniform(2, 5))
                    
                    # Try to find listing elements
                    try:
                        items = driver.find_elements(By.CLASS_NAME, "listing", timeout=10)
                    except TimeoutException:
                        raise ScrapingError("Timeout while waiting for listings to load")
                    
                    if not items:
                        # Try alternative selectors in case the page structure changed
                        alternative_selectors = [
                            ".result-item",
                            ".offer-item",
                            ".ad-list-item"
                        ]
                        
                        for selector in alternative_selectors:
                            try:
                                items = driver.find_elements(By.CSS_SELECTOR, selector, timeout=5)
                                if items:
                                    break
                            except TimeoutException:
                                continue
                        
                        if not items:
                            raise ScrapingError("No listings found with any selector")
                    
                    # Extract listing data
                    for item in items:
                        try:
                            # Try multiple selectors for title
                            title = None
                            for title_selector in ["h2", "h3", "h4", ".title", ".headline"]:
                                try:
                                    title_elem = item.find_element(By.CSS_SELECTOR, title_selector)
                                    title = title_elem.text.strip()
                                    if title:
                                        break
                                except NoSuchElementException:
                                    continue
                            
                            # Try multiple selectors for price
                            price = None
                            for price_selector in [".price", ".rent", ".kaltmiete", ".monthly-cost"]:
                                try:
                                    price_elem = item.find_element(By.CSS_SELECTOR, price_selector)
                                    price = price_elem.text.strip()
                                    if price:
                                        break
                                except NoSuchElementException:
                                    continue
                            
                            if title and price:
                                # Sanitize and validate listing data
                                raw_listing = {
                                    "title": title,
                                    "price": price,
                                    "source": "WG Gesucht",
                                    "timestamp": datetime.now().isoformat(),
                                }
                                
                                # Apply security validation
                                sanitized_listing = SecurityValidator.sanitize_listing(raw_listing)
                                
                                # Validate that we have essential data after sanitization
                                if sanitized_listing.get('title') and sanitized_listing.get('price'):
                                    listings.append(sanitized_listing)
                                else:
                                    # Skip listings that become invalid after sanitization
                                    continue
                            else:
                                # Skip listings with missing critical data
                                continue
                                
                        except NoSuchElementException as e:
                            # Skip this item but continue processing others
                            continue
                        except Exception as e:
                            # Log error but continue processing other items
                            print(f"Error parsing WG-Gesucht listing item: {e}")
                            continue
                
                # Success - break out of retry loop
                break
                
            except ScrapingError:
                # Don't retry scraping errors - they indicate structural issues
                raise
            except Exception as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                    time.sleep(wait_time)
                    continue
                else:
                    break
        
        # If we exhausted all retries, raise the last exception
        if not listings and last_exception:
            raise ProviderError(
                provider_name="WG-Gesucht",
                message=f"Failed to scrape after {self.max_retries} attempts",
                details={"last_error": str(last_exception)}
            )
        
        return listings