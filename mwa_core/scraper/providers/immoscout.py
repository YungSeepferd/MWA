"""
ImmoScout24 provider for MWA Core.

Implements the BaseProvider protocol to scrape apartment listings
from ImmoScout24.de.
"""

from datetime import datetime
import logging
import time
from typing import List, Dict, Any

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from mwa_core.scraper.providers.base import BaseProvider, Listing
from mafa.driver import SeleniumDriver

logger = logging.getLogger(__name__)


class ImmoScoutProvider:
    """
    Scrapes listings from ImmoScout24.de.
    
    This provider uses Selenium WebDriver to navigate and extract
    apartment listings from ImmoScout24.
    """
    
    def __init__(self, base_url: str | None = None) -> None:
        """
        Initialize the ImmoScout provider.
        
        Args:
            base_url: Custom base URL for ImmoScout searches
        """
        self.base_url = base_url or (
            "https://www.immobilienscout24.de/Suche/de/bayern/muenchen/wohnung-mieten"
        )
    
    def get_provider_name(self) -> str:
        """Get the provider name."""
        return "immoscout"
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate provider-specific configuration.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            True if configuration is valid
        """
        # Basic validation - can be extended
        if not isinstance(config, dict):
            return False
        
        # Check for valid boolean values
        headless = config.get("headless", True)
        if not isinstance(headless, bool):
            return False
        
        return True
    
    def fetch_listings(self, config: Dict[str, Any]) -> List[Listing]:
        """
        Fetch listings from ImmoScout24.
        
        Parameters
        ----------
        config : dict
            Provider configuration including:
            - headless: bool (default True) - Run browser in headless mode
            - timeout: int (default 30) - Page load timeout
            - user_agent: str - Custom user agent
            - request_delay: float (default 1.0) - Delay between requests
            - max_retries: int (default 3) - Maximum retry attempts
            - base_url: str - Override base search URL
            
        Returns
        -------
        list[Listing]
            Canonical listing objects extracted from ImmoScout24.
        """
        base_url = config.get("base_url", self.base_url)
        headless = config.get("headless", True)
        timeout = config.get("timeout", 30)
        request_delay = config.get("request_delay", 1.0)
        max_retries = config.get("max_retries", 3)
        user_agent = config.get("user_agent")
        
        listings: List[Listing] = []
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                logger.info(f"Starting ImmoScout scraping (attempt {retry_count + 1})")
                
                with SeleniumDriver(headless=headless, user_agent=user_agent) as driver:
                    driver.set_page_load_timeout(timeout)
                    
                    # Navigate to search page
                    logger.debug(f"Navigating to: {base_url}")
                    driver.get(base_url)
                    
                    # Wait for results to load
                    wait = WebDriverWait(driver, timeout)
                    wait.until(EC.presence_of_element_located((By.CLASS_NAME, "result-list-entry")))
                    
                    # Add delay to respect rate limiting
                    time.sleep(request_delay)
                    
                    # Extract listings
                    items = driver.find_elements(By.CLASS_NAME, "result-list-entry")
                    logger.info(f"Found {len(items)} listing elements")
                    
                    for item in items:
                        try:
                            listing = self._extract_listing(item)
                            if listing:
                                listings.append(listing)
                        except Exception as e:
                            logger.warning(f"Error extracting individual listing: {e}")
                            continue
                    
                    logger.info(f"Successfully extracted {len(listings)} listings")
                    break  # Success, exit retry loop
                    
            except TimeoutException:
                retry_count += 1
                logger.warning(f"Timeout on attempt {retry_count}, retrying...")
                if retry_count < max_retries:
                    time.sleep(request_delay * retry_count)  # Exponential backoff
                else:
                    logger.error("Max retries exceeded for ImmoScout scraping")
                    raise
                    
            except Exception as e:
                retry_count += 1
                logger.error(f"Error on attempt {retry_count}: {e}")
                if retry_count >= max_retries:
                    logger.error("Max retries exceeded for ImmoScout scraping")
                    raise
                time.sleep(request_delay * retry_count)  # Exponential backoff
        
        return listings
    
    def _extract_listing(self, item_element) -> Listing | None:
        """
        Extract listing data from a single result element.
        
        Args:
            item_element: Selenium WebElement for the listing
            
        Returns:
            Listing object or None if extraction fails
        """
        try:
            # Extract title
            title_elem = item_element.find_element(By.CSS_SELECTOR, "h5")
            title = title_elem.text.strip() if title_elem else "Unknown Title"
            
            # Extract price
            price_elem = item_element.find_element(By.CLASS_NAME, "price")
            price = price_elem.text.strip() if price_elem else "Price not specified"
            
            # Extract URL
            link_elem = item_element.find_element(By.TAG_NAME, "a")
            url = link_elem.get_attribute("href") if link_elem else ""
            
            # Extract additional details
            description = ""
            try:
                desc_elem = item_element.find_element(By.CLASS_NAME, "result-list-entry__criteria")
                description = desc_elem.text.strip() if desc_elem else ""
            except NoSuchElementException:
                pass
            
            # Extract address
            address = ""
            try:
                address_elem = item_element.find_element(By.CLASS_NAME, "result-list-entry__address")
                address = address_elem.text.strip() if address_elem else ""
            except NoSuchElementException:
                pass
            
            # Extract size and rooms if available
            size = ""
            rooms = ""
            try:
                criteria_elems = item_element.find_elements(By.CLASS_NAME, "criteria")
                for criteria in criteria_elems:
                    text = criteria.text.strip()
                    if "m²" in text:
                        size = text
                    elif "Zimmer" in text or "Zi." in text:
                        rooms = text
            except NoSuchElementException:
                pass
            
            # Extract images
            images = []
            try:
                img_elems = item_element.find_elements(By.TAG_NAME, "img")
                images = [img.get_attribute("src") for img in img_elems if img.get_attribute("src")]
            except NoSuchElementException:
                pass
            
            # Extract external ID from URL if possible
            external_id = ""
            if url and "expose/" in url:
                try:
                    parts = url.split("expose/")
                    if len(parts) > 1:
                        external_id = parts[1].split("/")[0]
                except (IndexError, AttributeError):
                    pass
            
            # Store raw data for debugging
            raw_data = {
                "html_content": item_element.get_attribute("outerHTML")[:1000],  # Truncate for storage
                "extracted_at": datetime.utcnow().isoformat()
            }
            
            return Listing(
                title=title,
                price=price,
                source="ImmobilienScout24",
                url=url,
                timestamp=datetime.utcnow(),
                external_id=external_id or None,
                description=description or None,
                images=images if images else None,
                address=address or None,
                size=size or None,
                rooms=rooms or None,
                raw_data=raw_data
            )
            
        except Exception as e:
            logger.error(f"Error extracting listing data: {e}")
            return None