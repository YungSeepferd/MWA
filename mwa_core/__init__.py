"""
MWA Core – Modular Scraping & Notification Framework

This package provides a modular architecture for apartment scraping
and notification systems, with support for multiple providers,
configurable notifications, and robust data persistence.
"""

__version__ = "0.2.0"

# Core modules
from .config import Settings, get_settings
from .storage import StorageManager, get_storage_manager
from .scraper import ScraperEngine, Listing
from .orchestrator import Orchestrator

# Provider modules
from .scraper.providers import BaseProvider, ImmoScoutProvider, WgGesuchtProvider

# Backward compatibility imports
try:
    # Try to import legacy modules for backward compatibility
    from mafa.config.settings import Settings as LegacySettings
    from mafa.db.manager import ListingRepository as LegacyListingRepository
    LEGACY_MODE = True
except ImportError:
    LEGACY_MODE = False

__all__ = [
    # Core classes
    "Settings",
    "get_settings",
    "StorageManager", 
    "get_storage_manager",
    "ScraperEngine",
    "Listing",
    "Orchestrator",
    
    # Provider classes
    "BaseProvider",
    "ImmoScoutProvider",
    "WgGesuchtProvider",
    
    # Version info
    "__version__",
    "LEGACY_MODE",
]


def create_legacy_adapter():
    """
    Create an adapter for backward compatibility with legacy MAFA code.
    
    Returns
    -------
    dict
        Dictionary containing legacy-compatible objects
    """
    if not LEGACY_MODE:
        return {}
    
    return {
        "settings": LegacySettings.load(),
        "repository": LegacyListingRepository(),
    }


def migrate_from_legacy():
    """
    Migrate data and configuration from legacy MAFA system to MWA Core.
    
    This function provides a migration path for existing MAFA installations
    to transition to the new MWA Core architecture.
    """
    if not LEGACY_MODE:
        logger.warning("Legacy modules not available for migration")
        return
    
    try:
        # Load legacy settings
        legacy_settings = LegacySettings.load()
        
        # Create new settings object with migrated data
        new_settings = get_settings()
        
        # Migrate personal profile
        new_settings.personal_profile = legacy_settings.personal_profile
        
        # Migrate search criteria
        new_settings.search_criteria = legacy_settings.search_criteria
        
        # Migrate notification settings
        new_settings.notification.provider = legacy_settings.notification.provider
        new_settings.notification.discord_webhook_url = legacy_settings.notification.discord_webhook_url
        new_settings.notification.telegram_bot_token = legacy_settings.notification.telegram_bot_token
        new_settings.notification.telegram_chat_id = legacy_settings.notification.telegram_chat_id
        
        # Save migrated settings
        new_settings.save()
        
        logger.info("Successfully migrated settings from legacy MAFA system")
        
        # Migrate data from legacy database
        legacy_repo = LegacyListingRepository()
        new_storage = get_storage_manager()
        
        # Get all legacy listings and migrate them
        # This is a simplified migration - in practice you'd need more sophisticated logic
        legacy_listings = legacy_repo.get_all_listings()  # Assuming this method exists
        
        migrated_count = 0
        for listing in legacy_listings:
            if new_storage.add_listing(listing):
                migrated_count += 1
        
        logger.info(f"Migrated {migrated_count} listings from legacy system")
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


# Set up logging for the package
import logging

logging.getLogger(__name__).addHandler(logging.NullHandler())


def setup_logging(level: str = "INFO") -> None:
    """
    Set up logging for MWA Core.
    
    Parameters
    ----------
    level : str
        Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Set specific logger levels
    logging.getLogger("mwa_core").setLevel(getattr(logging, level.upper()))
    logging.getLogger("selenium").setLevel(logging.WARNING)  # Reduce selenium noise
    logging.getLogger("urllib3").setLevel(logging.WARNING)  # Reduce urllib3 noise


# Auto-setup logging if running as main module
if __name__ == "__main__":
    setup_logging()