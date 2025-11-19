"""
ScraperEngine orchestrates multiple providers and aggregates their listings.
"""

import logging
from typing import List, Dict, Any
from datetime import datetime

from .base import Listing
from .registry import ProviderRegistry
from mwa_core.storage import get_storage_manager

logger = logging.getLogger(__name__)


class ScraperEngine:
    """
    Runs all enabled providers and returns aggregated listings.
    """

    def __init__(self, registry: ProviderRegistry | None = None) -> None:
        self.registry = registry or ProviderRegistry()

    def scrape_all(self, enabled_providers: List[str], config: Dict[str, Any]) -> List[Listing]:
        """
        Fetch listings from all enabled providers.

        Parameters
        ----------
        enabled_providers : list[str]
            Names of providers to run (must be registered).
        config : dict
            Global config passed to each provider (can be overridden per provider).

        Returns
        -------
        list[Listing]
            Aggregated listings from all providers.
        """
        all_listings: List[Listing] = []
        storage = get_storage_manager()
        
        for name in enabled_providers:
            provider_cls = self.registry.get(name)
            if provider_cls is None:
                logger.warning(f"[ScraperEngine] Provider '{name}' not registered – skipping.")
                continue
            
            # Create scraping job for this provider
            job_id = storage.create_scraping_job(name)
            provider = provider_cls()
            
            try:
                start_time = datetime.utcnow()
                listings = provider.fetch_listings(config.get(name, {}))
                end_time = datetime.utcnow()
                
                all_listings.extend(listings)
                logger.info(f"[ScraperEngine] Provider '{name}' returned {len(listings)} listings.")
                
                # Update job with success
                duration = (end_time - start_time).total_seconds()
                storage.update_scraping_job(
                    job_id=job_id,
                    status="completed",
                    listings_found=len(listings),
                    performance_metrics={"duration": duration, "success": True}
                )
                
            except Exception as exc:
                logger.error(f"[ScraperEngine] Provider '{name}' failed: {exc}")
                
                # Update job with failure
                storage.update_scraping_job(
                    job_id=job_id,
                    status="failed",
                    errors=[str(exc)],
                    performance_metrics={"success": False}
                )
                
                # Continue with other providers even if one fails
                continue
        
        return all_listings