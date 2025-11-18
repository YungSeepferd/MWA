from typing import List, Dict, Protocol

class BaseProvider(Protocol):
    """Protocol that all scraper providers must implement."""

    def scrape(self) -> List[Dict]:
        """Return a list of listing dictionaries."""
        ...