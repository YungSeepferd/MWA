"""
Base provider protocol for MWA Core scrapers.

Defines the interface that all scraper providers must implement.
"""

from __future__ import annotations

from typing import Protocol, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Listing:
    """
    Canonical listing object returned by any provider.
    
    This represents a standardized apartment listing with all
    relevant information extracted from the provider.
    """
    title: str
    price: str
    source: str
    url: str
    timestamp: datetime
    external_id: str | None = None
    description: str | None = None
    images: list[str] | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    address: str | None = None
    size: str | None = None  # e.g., "85 m²"
    rooms: str | None = None  # e.g., "3.5"
    available_from: str | None = None
    raw_data: Dict[str, Any] | None = None  # provider-specific payload for debugging


class BaseProvider(Protocol):
    """
    Protocol that all scraper providers must implement.
    
    This defines the standard interface for scraping apartment
    listings from different websites.
    """
    
    def fetch_listings(self, config: Dict[str, Any]) -> List[Listing]:
        """
        Fetch listings from the provider.
        
        Parameters
        ----------
        config : dict
            Provider-specific configuration including:
            - headless: bool (default True) - Run browser in headless mode
            - timeout: int (default 30) - Request timeout in seconds
            - user_agent: str - User agent string
            - request_delay: float (default 1.0) - Delay between requests
            - max_retries: int (default 3) - Maximum retry attempts
            - base_url: str - Override base URL for provider
            
        Returns
        -------
        list[Listing]
            Canonical listing objects extracted from the provider.
            
        Raises
        ------
        Exception
            If scraping fails or provider is unavailable.
        """
        ...
    
    def get_provider_name(self) -> str:
        """
        Get the name of this provider.
        
        Returns
        -------
        str
            Provider name (e.g., "immoscout", "wg_gesucht")
        """
        ...
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate provider-specific configuration.
        
        Parameters
        ----------
        config : dict
            Configuration to validate
            
        Returns
        -------
        bool
            True if configuration is valid
        """
        ...