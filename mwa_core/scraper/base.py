from __future__ import annotations
from typing import Protocol, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class Listing:
    """
    Canonical listing object returned by any provider.
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
    raw: Dict[str, Any] | None = None  # provider-specific payload for debugging


class Provider(Protocol):
    """
    Protocol that all scraper providers must implement.
    """

    def fetch_listings(self, config: Dict[str, Any]) -> List[Listing]:
        """
        Fetch listings from the provider.

        Parameters
        ----------
        config : dict
            Provider-specific configuration (URLs, credentials, etc.).

        Returns
        -------
        list[Listing]
            Canonical listing objects.
        """
        ...