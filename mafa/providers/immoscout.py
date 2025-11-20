from datetime import datetime
from typing import List, Dict, Optional
import time
import random

from mafa.driver import SeleniumDriver
from selenium.webdriver.common.by import By
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from .base import BaseProvider
from ..exceptions import ProviderError, ScrapingError
from ..config.settings import Settings
from ..security import SecurityValidator
from ..contacts import ContactExtractor, ContactStorage, ContactValidator
from ..contacts.models import DiscoveryContext
import asyncio


class ImmoScoutProvider:
    """Provider for ImmobilienScout24."""

    URL = (
        "https://www.immobilienscout24.de/Suche/de/bayern/muenchen/wohnung-mieten"
    )

    def __init__(self, config: Settings | None = None):
        self.config = config
        self.max_retries = 3
        self.retry_delay = 2
        # Initialize contact discovery components
        self.contact_storage = None
        self.contact_validator = ContactValidator()
        self.enable_contact_discovery = True

    def scrape(self) -> List[Dict]:
        """Scrape listings from ImmobilienScout24 with retry logic and error handling."""
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
                        items = driver.find_elements(By.CLASS_NAME, "result-list-entry", timeout=10)
                    except TimeoutException:
                        raise ScrapingError("Timeout while waiting for listings to load")
                    
                    if not items:
                        # Try alternative selectors in case the page structure changed
                        alternative_selectors = [
                            ".result-item",
                            ".listing-item",
                            "[data-qa='result-item']"
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
                            for title_selector in ["h5", "h3", "h4", ".title", "[data-qa='result-item-title']"]:
                                try:
                                    title_elem = item.find_element(By.CSS_SELECTOR, title_selector)
                                    title = title_elem.text.strip()
                                    if title:
                                        break
                                except NoSuchElementException:
                                    continue
                            
                            # Try multiple selectors for price
                            price = None
                            for price_selector in [".price", ".rent", "[data-qa='result-item-price']", ".kaltmiete"]:
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
                                    "source": "ImmobilienScout24",
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
                            print(f"Error parsing listing item: {e}")
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
                provider_name="ImmoScout",
                message=f"Failed to scrape after {self.max_retries} attempts",
                details={"last_error": str(last_exception)}
            )
        
        return listings

    async def discover_contacts_for_listing(self, listing_url: str, listing_id: Optional[int] = None) -> Dict[str, int]:
        """
        Discover contact information for a specific listing.
        
        Args:
            listing_url: URL of the listing page
            listing_id: ID of the listing in database (optional)
            
        Returns:
            Dictionary with counts of discovered contacts by type
        """
        if not self.enable_contact_discovery:
            return {'emails': 0, 'phones': 0, 'forms': 0}
        
        # Initialize storage if not already done
        if self.contact_storage is None:
            from pathlib import Path
            data_dir = Path(__file__).resolve().parents[3] / "data"
            self.contact_storage = ContactStorage(data_dir / "contacts.db")
        
        contact_counts = {'emails': 0, 'phones': 0, 'forms': 0}
        
        try:
            # Create discovery context
            from urllib.parse import urlparse
            parsed_url = urlparse(listing_url)
            context = DiscoveryContext(
                base_url=listing_url,
                domain=parsed_url.netloc,
                allowed_domains=[parsed_url.netloc],
                max_depth=2
            )
            
            # Extract contacts
            async with ContactExtractor(self.config) as extractor:
                contacts, forms = await extractor.discover_contacts(listing_url, context)
                
                # Store contacts
                if contacts:
                    stored_summary = self.contact_storage.store_contacts(contacts, listing_id)
                    contact_counts['emails'] = stored_summary['stored']
                
                # Store forms
                for form in forms:
                    if self.contact_storage.store_contact_form(form, listing_id):
                        contact_counts['forms'] += 1
                
                # Validate discovered contacts (basic validation only)
                validated_contacts = await self.contact_validator.validate_contacts(contacts[:5])  # Limit to first 5
                
                logger.info(f"Contact discovery for {listing_url}: {contact_counts}")
                return contact_counts
                
        except Exception as e:
            logger.error(f"Contact discovery failed for {listing_url}: {str(e)}")
            return contact_counts