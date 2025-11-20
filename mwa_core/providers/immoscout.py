"""
Enhanced ImmoScout24 provider for MWA Core.
Implements the Provider protocol using Selenium with robust error handling.
"""

import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, WebDriverException

from mwa_core.scraper.base import Provider, Listing
from mafa.driver import SeleniumDriver, SeleniumDriverError

logger = logging.getLogger(__name__)


class ImmoScoutProvider(Provider):
    """
    Enhanced scraper for ImmoScout24 with improved error handling and retry logic.
    """

    def __init__(self, base_url: str | None = None) -> None:
        self.base_url = base_url or (
            "https://www.immobilienscout24.de/Suche/de/bayern/muenchen/wohnung-mieten"
        )
        self.max_retries = 3
        self.retry_delay = 2  # seconds

    def fetch_listings(self, config: Dict[str, Any]) -> List[Listing]:
        """
        Fetch listings from ImmoScout24 with enhanced error handling.

        Parameters
        ----------
        config : dict
            Optional overrides:
            - base_url: str
            - headless: bool (default True)
            - timeout: int (default 30)
            - user_agent: str (optional)

        Returns
        -------
        list[Listing]
            Canonical listing objects.
        """
        base_url = config.get("base_url", self.base_url)
        headless = config.get("headless", True)
        timeout = config.get("timeout", 30)
        user_agent = config.get("user_agent")
        max_retries = config.get("max_retries", self.max_retries)

        listings: List[Listing] = []
        last_error = None

        for attempt in range(max_retries):
            try:
                logger.info(f"ImmoScout scraping attempt {attempt + 1}/{max_retries}")
                
                with SeleniumDriver(headless=headless, timeout=timeout, user_agent=user_agent) as driver:
                    logger.debug(f"Navigating to: {base_url}")
                    driver.get(base_url)
                    
                    # Wait for page to load with more specific selectors
                    wait = WebDriverWait(driver, timeout)
                    
                    # Try multiple selectors as fallback - using proper CSS selectors
                    selectors = [
                        ".result-list-entry",
                        "[data-testid='result-list-entry']",
                        ".listing-card",
                        "div[role='listitem']",
                        ".search-result"
                    ]
                    
                    items = None
                    for selector in selectors:
                        try:
                            logger.debug(f"Trying selector: {selector}")
                            items = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector)))
                            if items and len(items) > 0:
                                logger.info(f"Found {len(items)} elements with selector: {selector}")
                                break
                        except TimeoutException:
                            continue
                    
                    if not items or len(items) == 0:
                        logger.warning("No listing elements found on the page")
                        return listings
                    
                    listing_items = items
                    
                    logger.info(f"Processing {len(listing_items)} listing items")
                    
                    for i, item in enumerate(listing_items):
                        try:
                            # Extract data with multiple fallback selectors
                            title = self._extract_text_with_fallback(item, [
                                "h5", ".result-list-entry__title",
                                "h2", "h3", ".title"
                            ])
                            
                            price = self._extract_text_with_fallback(item, [
                                ".price", ".result-list-entry__price",
                                ".listing-price", "[data-testid='price']"
                            ])
                            
                            url = self._extract_url_with_fallback(item, [
                                "a", "a[href]", ".listing-link"
                            ])
                            
                            # Only add if we have at least a title
                            if title and title.strip():
                                listing = Listing(
                                    title=title.strip(),
                                    price=price.strip() if price else "",
                                    source="ImmobilienScout24",
                                    url=url or "",
                                    timestamp=datetime.utcnow(),
                                )
                                listings.append(listing)
                                logger.debug(f"Extracted listing {i + 1}: {title[:50]}...")
                            else:
                                logger.warning(f"Skipping item {i + 1} - missing title")
                                
                        except Exception as e:
                            logger.warning(f"Error extracting data from item {i + 1}: {e}")
                            continue
                    
                    logger.info(f"Successfully extracted {len(listings)} listings from ImmoScout")
                    return listings
                    
            except SeleniumDriverError as e:
                last_error = e
                logger.error(f"Driver error on attempt {attempt + 1}: {e}")
                
            except Exception as e:
                last_error = e
                logger.error(f"Scraping error on attempt {attempt + 1}: {e}")
            
            # Wait before retry
            if attempt < max_retries - 1:
                wait_time = self.retry_delay * (2 ** attempt)  # Exponential backoff
                logger.info(f"Retrying in {wait_time} seconds...")
                time.sleep(wait_time)
        
        logger.error(f"All attempts failed. Last error: {last_error}")
        return listings

    def _extract_text_with_fallback(self, item, selectors: List[str]) -> str:
        """Extract text from element using multiple selector fallbacks."""
        for selector in selectors:
            try:
                element = item.find_element(By.CSS_SELECTOR, selector)
                text = element.text.strip()
                if text:
                    return text
            except NoSuchElementException:
                continue
        return ""

    def _extract_url_with_fallback(self, item, selectors: List[str]) -> str:
        """Extract URL from element using multiple selector fallbacks."""
        for selector in selectors:
            try:
                element = item.find_element(By.CSS_SELECTOR, selector)
                url = element.get_attribute("href")
                if url and url.strip():
                    return url.strip()
            except NoSuchElementException:
                continue
        return ""