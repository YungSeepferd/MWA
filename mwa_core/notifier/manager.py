"""
Notification manager for coordinating multiple notifiers and handling delivery tracking.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set
from uuid import uuid4

from .base import (
    BaseNotifier,
    NotificationMessage,
    NotificationResult,
    NotificationStatus,
    NotificationChannel,
    NotificationPriority,
    NotificationType,
    NotificationFormatter
)
from .factory import NotifierFactory

logger = logging.getLogger(__name__)


class NotificationManager:
    """Manages multiple notifiers and coordinates notification delivery."""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Initialize the notification manager.
        
        Args:
            config: Configuration dictionary for notifiers
        """
        self.config = config or {}
        self.notifiers: Dict[str, BaseNotifier] = {}
        self.delivery_history: List[NotificationResult] = []
        self.pending_notifications: Dict[str, NotificationMessage] = {}
        self.failed_notifications: Dict[str, NotificationResult] = {}
        self.rate_limiter = RateLimiter()
        self.deduplicator = NotificationDeduplicator()
        self.enabled = True
        
        # Initialize notifiers from config
        self._initialize_notifiers()
        
    def _initialize_notifiers(self):
        """Initialize notifiers from configuration."""
        try:
            notifiers = NotifierFactory.create_notifiers_from_config(self.config)
            for notifier in notifiers:
                self.register_notifier(notifier)
        except Exception as e:
            logger.error(f"Failed to initialize notifiers: {e}")
    
    def register_notifier(self, notifier: BaseNotifier, name: str = None):
        """
        Register a notifier instance.
        
        Args:
            notifier: The notifier to register
            name: Optional name for the notifier (defaults to notifier name)
        """
        name = name or notifier.name
        self.notifiers[name] = notifier
        logger.info(f"Registered notifier: {name} ({notifier.get_channel_type().value})")
    
    def unregister_notifier(self, name: str):
        """
        Unregister a notifier instance.
        
        Args:
            name: Name of the notifier to unregister
        """
        if name in self.notifiers:
            del self.notifiers[name]
            logger.info(f"Unregistered notifier: {name}")
    
    def get_notifier(self, name: str) -> Optional[BaseNotifier]:
        """
        Get a registered notifier by name.
        
        Args:
            name: Name of the notifier
            
        Returns:
            The notifier instance or None if not found
        """
        return self.notifiers.get(name)
    
    def get_notifiers_by_channel(self, channel: NotificationChannel) -> List[BaseNotifier]:
        """
        Get all notifiers for a specific channel.
        
        Args:
            channel: The notification channel
            
        Returns:
            List of notifiers for the channel
        """
        return [
            notifier for notifier in self.notifiers.values()
            if notifier.get_channel_type() == channel
        ]
    
    async def send_notification(
        self,
        message: NotificationMessage,
        channels: List[NotificationChannel] = None,
        notifiers: List[str] = None,
        skip_rate_limit: bool = False,
        skip_deduplication: bool = False
    ) -> List[NotificationResult]:
        """
        Send a notification through specified channels/notifiers.
        
        Args:
            message: The notification message to send
            channels: Optional list of channels to use (uses all if None)
            notifiers: Optional list of specific notifier names to use
            skip_rate_limit: Whether to skip rate limiting
            skip_deduplication: Whether to skip deduplication
            
        Returns:
            List of notification results
        """
        if not self.enabled:
            logger.warning("Notification manager is disabled")
            return []
        
        # Deduplication
        if not skip_deduplication and self.deduplicator.is_duplicate(message):
            logger.info(f"Skipping duplicate notification: {message.id}")
            return []
        
        # Select notifiers
        selected_notifiers = self._select_notifiers(channels, notifiers)
        
        if not selected_notifiers:
            logger.warning("No notifiers available for notification")
            return []
        
        # Rate limiting
        if not skip_rate_limit:
            await self.rate_limiter.wait_if_needed(len(selected_notifiers))
        
        # Send notifications
        results = []
        tasks = []
        
        for notifier in selected_notifiers:
            task = asyncio.create_task(self._send_single_notification(notifier, message))
            tasks.append(task)
        
        # Wait for all notifications to complete
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            processed_results = []
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"Notification task failed: {result}")
                    # Create a failed result for the exception
                    failed_result = NotificationResult(
                        message_id=message.id,
                        status=NotificationStatus.FAILED,
                        channel=message.channel,
                        error_message=str(result)
                    )
                    processed_results.append(failed_result)
                else:
                    processed_results.append(result)
            
            results = processed_results
        
        # Store delivery history
        self.delivery_history.extend(results)
        
        # Track failed notifications for retry
        for result in results:
            if result.is_failed:
                self.failed_notifications[result.message_id] = result
        
        return results
    
    async def _send_single_notification(self, notifier: BaseNotifier, message: NotificationMessage) -> NotificationResult:
        """Send a notification through a single notifier."""
        try:
            # Update message channel to match notifier
            message.channel = notifier.get_channel_type()
            
            # Send with retry logic
            result = await notifier.send_with_retry(message)
            
            # Log result
            if result.is_successful:
                logger.info(f"Notification sent successfully via {notifier.name}")
            else:
                logger.warning(f"Notification failed via {notifier.name}: {result.error_message}")
            
            return result
            
        except Exception as e:
            logger.error(f"Exception sending notification via {notifier.name}: {e}")
            return NotificationResult(
                message_id=message.id,
                status=NotificationStatus.FAILED,
                channel=notifier.get_channel_type(),
                error_message=f"Exception: {str(e)}"
            )
    
    def _select_notifiers(self, channels: List[NotificationChannel], notifiers: List[str]) -> List[BaseNotifier]:
        """Select notifiers based on channels and specific names."""
        selected = []
        
        if notifiers:
            # Use specific notifiers by name
            for name in notifiers:
                notifier = self.get_notifier(name)
                if notifier and notifier.enabled:
                    selected.append(notifier)
        elif channels:
            # Use notifiers by channel
            for channel in channels:
                channel_notifiers = self.get_notifiers_by_channel(channel)
                selected.extend([n for n in channel_notifiers if n.enabled])
        else:
            # Use all enabled notifiers
            selected = [n for n in self.notifiers.values() if n.enabled]
        
        return selected
    
    async def send_new_listings(
        self,
        listings: List[Dict[str, Any]],
        channels: List[NotificationChannel] = None,
        title: str = "New Apartment Listings",
        priority: NotificationPriority = NotificationPriority.NORMAL
    ) -> List[NotificationResult]:
        """
        Send notification for new apartment listings.
        
        Args:
            listings: List of apartment listings
            channels: Optional channels to use
            title: Notification title
            priority: Notification priority
            
        Returns:
            List of notification results
        """
        if not listings:
            logger.info("No listings to notify about")
            return []
        
        try:
            message = NotificationFormatter.format_listings_message(listings, title)
            message.priority = priority
            
            return await self.send_notification(message, channels)
            
        except Exception as e:
            logger.error(f"Failed to send listings notification: {e}")
            return []
    
    async def send_contact_discovery(
        self,
        contacts: List[Dict[str, Any]],
        source_url: str,
        channels: List[NotificationChannel] = None,
        priority: NotificationPriority = NotificationPriority.NORMAL
    ) -> List[NotificationResult]:
        """
        Send notification for discovered contacts.
        
        Args:
            contacts: List of discovered contacts
            source_url: URL where contacts were discovered
            channels: Optional channels to use
            priority: Notification priority
            
        Returns:
            List of notification results
        """
        if not contacts:
            logger.info("No contacts to notify about")
            return []
        
        try:
            message = NotificationFormatter.format_contact_discovery_message(contacts, source_url)
            message.priority = priority
            
            return await self.send_notification(message, channels)
            
        except Exception as e:
            logger.error(f"Failed to send contact discovery notification: {e}")
            return []
    
    async def send_system_alert(
        self,
        error_type: str,
        error_details: str,
        context: Dict[str, Any] = None,
        channels: List[NotificationChannel] = None,
        priority: NotificationPriority = NotificationPriority.HIGH
    ) -> List[NotificationResult]:
        """
        Send system alert notification.
        
        Args:
            error_type: Type of error
            error_details: Detailed error information
            context: Additional context
            channels: Optional channels to use
            priority: Notification priority
            
        Returns:
            List of notification results
        """
        try:
            message = NotificationFormatter.format_error_message(error_type, error_details, context)
            message.priority = priority
            
            return await self.send_notification(message, channels)
            
        except Exception as e:
            logger.error(f"Failed to send system alert: {e}")
            return []
    
    async def retry_failed_notifications(self, max_age_hours: int = 24) -> List[NotificationResult]:
        """
        Retry failed notifications that are within the specified age.
        
        Args:
            max_age_hours: Maximum age of failed notifications to retry
            
        Returns:
            List of retry results
        """
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        results = []
        
        # Find failed notifications to retry
        to_retry = []
        for message_id, failed_result in list(self.failed_notifications.items()):
            if failed_result.sent_at >= cutoff_time:
                # Find the original message
                if message_id in self.pending_notifications:
                    message = self.pending_notifications[message_id]
                    to_retry.append((message, failed_result))
        
        if not to_retry:
            logger.info("No failed notifications to retry")
            return results
        
        logger.info(f"Retrying {len(to_retry)} failed notifications")
        
        # Retry each notification
        for message, failed_result in to_retry:
            try:
                # Find the notifier that failed
                notifier_name = None
                for name, notifier in self.notifiers.items():
                    if notifier.get_channel_type() == failed_result.channel:
                        notifier_name = name
                        break
                
                if notifier_name:
                    retry_results = await self.send_notification(
                        message,
                        notifiers=[notifier_name],
                        skip_rate_limit=True,
                        skip_deduplication=True
                    )
                    results.extend(retry_results)
                    
                    # Remove from failed list if successful
                    if retry_results and retry_results[0].is_successful:
                        del self.failed_notifications[message_id]
                        
            except Exception as e:
                logger.error(f"Failed to retry notification {message_id}: {e}")
        
        return results
    
    def get_delivery_stats(self) -> Dict[str, Any]:
        """
        Get delivery statistics.
        
        Returns:
            Dictionary with delivery statistics
        """
        total = len(self.delivery_history)
        if total == 0:
            return {
                "total_sent": 0,
                "successful": 0,
                "failed": 0,
                "success_rate": 0.0,
                "by_channel": {},
                "by_type": {}
            }
        
        successful = sum(1 for r in self.delivery_history if r.is_successful)
        failed = sum(1 for r in self.delivery_history if r.is_failed)
        
        # Stats by channel
        by_channel = {}
        for result in self.delivery_history:
            channel = result.channel.value
            if channel not in by_channel:
                by_channel[channel] = {"total": 0, "successful": 0, "failed": 0}
            by_channel[channel]["total"] += 1
            if result.is_successful:
                by_channel[channel]["successful"] += 1
            elif result.is_failed:
                by_channel[channel]["failed"] += 1
        
        # Stats by type (from message metadata)
        by_type = {}
        # This would require storing message type with results
        
        return {
            "total_sent": total,
            "successful": successful,
            "failed": failed,
            "success_rate": successful / total,
            "by_channel": by_channel,
            "by_type": by_type,
            "recent_failures": [
                {
                    "message_id": r.message_id,
                    "channel": r.channel.value,
                    "error": r.error_message,
                    "sent_at": r.sent_at.isoformat()
                }
                for r in self.delivery_history[-10:] if r.is_failed
            ]
        }
    
    def cleanup_old_history(self, max_age_days: int = 30):
        """
        Clean up old delivery history.
        
        Args:
            max_age_days: Maximum age of history to keep
        """
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        old_count = len(self.delivery_history)
        
        self.delivery_history = [
            result for result in self.delivery_history
            if result.sent_at >= cutoff_time
        ]
        
        new_count = len(self.delivery_history)
        logger.info(f"Cleaned up delivery history: {old_count - new_count} entries removed")
    
    def enable(self):
        """Enable the notification manager."""
        self.enabled = True
        logger.info("Notification manager enabled")
    
    def disable(self):
        """Disable the notification manager."""
        self.enabled = False
        logger.info("Notification manager disabled")
    
    def __str__(self) -> str:
        """String representation of the manager."""
        return f"NotificationManager(notifiers={len(self.notifiers)}, history={len(self.delivery_history)})"


class RateLimiter:
    """Simple rate limiter for notifications."""
    
    def __init__(self, max_requests: int = 10, time_window: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests per time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: List[datetime] = []
    
    async def wait_if_needed(self, request_count: int = 1):
        """
        Wait if rate limit would be exceeded.
        
        Args:
            request_count: Number of requests to make
        """
        now = datetime.now()
        
        # Clean up old requests
        cutoff = now - timedelta(seconds=self.time_window)
        self.requests = [req_time for req_time in self.requests if req_time >= cutoff]
        
        # Check if we need to wait
        if len(self.requests) + request_count > self.max_requests:
            # Calculate wait time
            oldest_request = min(self.requests)
            wait_time = (oldest_request + timedelta(seconds=self.time_window) - now).total_seconds()
            
            if wait_time > 0:
                logger.info(f"Rate limiting: waiting {wait_time:.1f} seconds")
                await asyncio.sleep(wait_time)
        
        # Record new requests
        for _ in range(request_count):
            self.requests.append(now)


class NotificationDeduplicator:
    """Deduplicates notifications to prevent spam."""
    
    def __init__(self, deduplication_window: int = 300):
        """
        Initialize deduplicator.
        
        Args:
            deduplication_window: Time window in seconds for deduplication
        """
        self.deduplication_window = deduplication_window
        self.recent_notifications: List[tuple] = []
    
    def is_duplicate(self, message: NotificationMessage) -> bool:
        """
        Check if a notification is a duplicate.
        
        Args:
            message: The notification message
            
        Returns:
            True if the message is a duplicate
        """
        now = datetime.now()
        cutoff = now - timedelta(seconds=self.deduplication_window)
        
        # Clean up old entries
        self.recent_notifications = [
            (timestamp, key) for timestamp, key in self.recent_notifications
            if timestamp >= cutoff
        ]
        
        # Create deduplication key
        dedup_key = self._create_deduplication_key(message)
        
        # Check for duplicate
        for _, existing_key in self.recent_notifications:
            if existing_key == dedup_key:
                return True
        
        # Add to recent notifications
        self.recent_notifications.append((now, dedup_key))
        return False
    
    def _create_deduplication_key(self, message: NotificationMessage) -> str:
        """Create a deduplication key for the message."""
        # Simple key based on type and content
        key_parts = [
            message.type.value,
            message.title or "",
            message.content[:100] or "",  # First 100 chars of content
        ]
        
        # Add metadata for specific types
        if message.type == NotificationType.NEW_LISTINGS and "listings_count" in message.metadata:
            key_parts.append(str(message.metadata["listings_count"]))
        
        return "|".join(key_parts)


# Convenience functions
async def create_notification_manager(config: Dict[str, Any] = None) -> NotificationManager:
    """Create a notification manager with the given configuration."""
    return NotificationManager(config)


async def send_notification(
    message: NotificationMessage,
    config: Dict[str, Any] = None,
    channels: List[NotificationChannel] = None
) -> List[NotificationResult]:
    """Send a notification using a temporary notification manager."""
    manager = NotificationManager(config)
    return await manager.send_notification(message, channels)