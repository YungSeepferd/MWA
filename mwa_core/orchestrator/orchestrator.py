"""
Enhanced Orchestrator coordinates scraping, persistence, and notifications using the new notifier system.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from mwa_core.scraper import ScraperEngine, Listing
from mwa_core.storage import get_storage_manager
from mwa_core.notifier import NotificationManager, NotificationChannel, NotificationPriority
from mwa_core.config import get_settings, Settings

logger = logging.getLogger(__name__)


class Orchestrator:
    """
    Enhanced high-level coordinator for scraping runs with integrated notification system.
    """

    def __init__(
        self,
        scraper: ScraperEngine | None = None,
        storage_manager = None,
        notification_manager: NotificationManager | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.scraper = scraper or ScraperEngine()
        self.storage = storage_manager or get_storage_manager()
        self.notification_manager = notification_manager
        # Defer Settings instantiation to avoid validation errors in tests
        self._settings = settings

    @property
    def settings(self) -> Settings:
        if self._settings is None:
            self._settings = get_settings()
        return self._settings

    def run(self, enabled_providers: List[str], config: Dict[str, Any]) -> int:
        """
        Execute a full scraping cycle with notifications.

        Returns
        -------
        int
            Number of new listings inserted.
        """
        logger.info(f"[Orchestrator] Starting run at {datetime.utcnow().isoformat()}")
        
        # Initialize notification manager if not provided
        if not self.notification_manager and self.settings.notification:
            self.notification_manager = self._create_notification_manager()
        
        # Create scraping job record
        job_id = None
        if len(enabled_providers) == 1:
            job_id = self.storage.create_scraping_job(enabled_providers[0])
        
        try:
            listings = self.scraper.scrape_all(enabled_providers, config)
            logger.info(f"[Orchestrator] Scraped {len(listings)} total listings.")

            new_count = 0
            new_listings = []
            
            for listing in listings:
                if self.storage.add_listing(listing.__dict__):
                    new_count += 1
                    new_listings.append(listing.__dict__)

            logger.info(f"[Orchestrator] Inserted {new_count} new listings.")

            # Send notifications for new listings
            if new_count > 0 and self.notification_manager:
                asyncio.run(self._send_new_listings_notification(new_listings, enabled_providers))

            # Send contact discovery notifications if enabled
            if self.settings.contact_discovery.enabled and self.notification_manager:
                asyncio.run(self._send_contact_discovery_notifications(listings))

            # Update job status if we created one
            if job_id:
                self.storage.update_scraping_job(
                    job_id=job_id,
                    status="completed",
                    listings_found=len(listings),
                    new_listings=new_count
                )
            
            return new_count
            
        except Exception as e:
            logger.error(f"[Orchestrator] Scraping failed: {e}")
            
            # Send error notification
            if self.notification_manager:
                asyncio.run(self._send_error_notification("Scraping Failed", str(e), {
                    "providers": enabled_providers,
                    "error_type": type(e).__name__
                }))
            
            if job_id:
                self.storage.update_scraping_job(
                    job_id=job_id,
                    status="failed",
                    errors=[str(e)]
                )
            raise

    async def _send_new_listings_notification(self, new_listings: List[Dict[str, Any]], providers: List[str]):
        """Send notification for new listings."""
        if not self.notification_manager or not new_listings:
            return

        try:
            # Determine which channels to use
            channels = self._get_notification_channels()
            
            # Create notification
            title = f"New Listings Found ({len(new_listings)})"
            if len(providers) == 1:
                title += f" from {providers[0].title()}"
            
            results = await self.notification_manager.send_new_listings(
                listings=new_listings,
                channels=channels,
                title=title,
                priority=NotificationPriority.NORMAL
            )
            
            # Log results
            successful = sum(1 for r in results if r.is_successful)
            logger.info(f"Sent new listings notification: {successful}/{len(results)} successful")
            
        except Exception as e:
            logger.error(f"Failed to send new listings notification: {e}")

    async def _send_contact_discovery_notifications(self, listings: List[Listing]):
        """Send notifications for discovered contacts."""
        if not self.notification_manager:
            return

        try:
            # Collect all discovered contacts
            all_contacts = []
            source_urls = set()
            
            for listing in listings:
                if hasattr(listing, 'contacts') and listing.contacts:
                    all_contacts.extend(listing.contacts)
                    source_urls.add(listing.url)
            
            if not all_contacts:
                return
            
            # Filter high-confidence contacts
            high_confidence_contacts = [
                contact for contact in all_contacts
                if contact.get('confidence', 0) >= 70
            ]
            
            if not high_confidence_contacts:
                return
            
            # Send notification
            channels = self._get_notification_channels()
            source_url = list(source_urls)[0] if len(source_urls) == 1 else f"{len(source_urls)} listings"
            
            results = await self.notification_manager.send_contact_discovery(
                contacts=high_confidence_contacts,
                source_url=source_url,
                channels=channels,
                priority=NotificationPriority.NORMAL
            )
            
            # Log results
            successful = sum(1 for r in results if r.is_successful)
            logger.info(f"Sent contact discovery notification: {successful}/{len(results)} successful")
            
        except Exception as e:
            logger.error(f"Failed to send contact discovery notification: {e}")

    async def _send_error_notification(self, error_type: str, error_details: str, context: Dict[str, Any] = None):
        """Send error notification."""
        if not self.notification_manager:
            return

        try:
            channels = self._get_notification_channels()
            
            results = await self.notification_manager.send_system_alert(
                error_type=error_type,
                error_details=error_details,
                context=context,
                channels=channels,
                priority=NotificationPriority.HIGH
            )
            
            # Log results
            successful = sum(1 for r in results if r.is_successful)
            logger.info(f"Sent error notification: {successful}/{len(results)} successful")
            
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")

    def _get_notification_channels(self) -> List[NotificationChannel]:
        """Get notification channels based on configuration."""
        if not self.settings.notification:
            return []
        
        # Get enabled channels from configuration
        channels = []
        
        # Check legacy configuration
        if hasattr(self.settings.notification, 'provider'):
            provider = self.settings.notification.provider
            if provider == 'discord':
                channels.append(NotificationChannel.DISCORD)
            elif provider == 'telegram':
                channels.append(NotificationChannel.TELEGRAM)
            elif provider == 'email':
                channels.append(NotificationChannel.EMAIL)
        
        # Check new notifier configuration
        if hasattr(self.settings, 'notifiers'):
            for notifier_config in self.settings.notifiers.values():
                if isinstance(notifier_config, dict) and 'channel' in notifier_config:
                    try:
                        channel = NotificationChannel(notifier_config['channel'])
                        channels.append(channel)
                    except ValueError:
                        logger.warning(f"Unknown notification channel: {notifier_config['channel']}")
        
        # Default to Discord if no channels specified
        if not channels:
            channels = [NotificationChannel.DISCORD]
        
        return channels

    def _create_notification_manager(self) -> NotificationManager:
        """Create notification manager from settings."""
        # Build notifier configuration
        notifier_config = {}
        
        # Add legacy notification config if available
        if self.settings.notification:
            notifier_config['notification'] = self.settings.notification.dict()
        
        # Add new notifier config if available
        if hasattr(self.settings, 'notifiers'):
            notifier_config['notifiers'] = self.settings.notifiers
        
        return NotificationManager(notifier_config)

    def test_notifications(self, channels: List[str] = None) -> Dict[str, bool]:
        """
        Test notification configuration by sending test messages.
        
        Args:
            channels: Optional list of channel names to test
            
        Returns:
            Dictionary with test results by channel
        """
        if not self.notification_manager:
            logger.warning("No notification manager configured")
            return {}
        
        results = {}
        
        # Test each configured notifier
        for name, notifier in self.notification_manager.notifiers.items():
            if channels and notifier.get_channel_type().value not in channels:
                continue
            
            try:
                if hasattr(notifier, 'test_webhook'):
                    success = notifier.test_webhook()
                    results[notifier.get_channel_type().value] = success
                    logger.info(f"Tested {notifier.get_channel_type().value} notifier: {'SUCCESS' if success else 'FAILED'}")
                elif hasattr(notifier, 'test_connection'):
                    success = notifier.test_connection()
                    results[notifier.get_channel_type().value] = success
                    logger.info(f"Tested {notifier.get_channel_type().value} notifier: {'SUCCESS' if success else 'FAILED'}")
                else:
                    logger.warning(f"No test method available for {notifier.get_channel_type().value} notifier")
                    
            except Exception as e:
                logger.error(f"Failed to test {notifier.get_channel_type().value} notifier: {e}")
                results[notifier.get_channel_type().value] = False
        
        return results

    def get_notification_stats(self) -> Dict[str, Any]:
        """
        Get notification delivery statistics.
        
        Returns:
            Dictionary with notification statistics
        """
        if not self.notification_manager:
            return {"enabled": False}
        
        stats = self.notification_manager.get_delivery_stats()
        stats["enabled"] = True
        stats["configured_channels"] = [
            notifier.get_channel_type().value 
            for notifier in self.notification_manager.notifiers.values()
        ]
        
        return stats

    def enable_notifications(self):
        """Enable notifications."""
        if self.notification_manager:
            self.notification_manager.enable()
            logger.info("Notifications enabled")

    def disable_notifications(self):
        """Disable notifications."""
        if self.notification_manager:
            self.notification_manager.disable()
            logger.info("Notifications disabled")

    async def retry_failed_notifications(self, max_age_hours: int = 24) -> int:
        """
        Retry failed notifications.
        
        Args:
            max_age_hours: Maximum age of failed notifications to retry
            
        Returns:
            Number of notifications retried
        """
        if not self.notification_manager:
            return 0
        
        results = await self.notification_manager.retry_failed_notifications(max_age_hours)
        return len(results)


# Legacy compatibility
def create_orchestrator_with_notifications(
    scraper: ScraperEngine = None,
    storage_manager = None,
    settings: Settings = None
) -> Orchestrator:
    """Create an orchestrator with notification support."""
    return Orchestrator(
        scraper=scraper,
        storage_manager=storage_manager,
        settings=settings
    )