"""
Base classes and enums for the MWA Core notification system.
"""

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from uuid import uuid4

from pydantic import BaseModel, Field


class NotificationStatus(str, Enum):
    """Status of a notification delivery attempt."""
    PENDING = "pending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class NotificationChannel(str, Enum):
    """Available notification channels."""
    DISCORD = "discord"
    TELEGRAM = "telegram"
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"


class NotificationPriority(str, Enum):
    """Notification priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


class NotificationType(str, Enum):
    """Types of notifications."""
    NEW_LISTINGS = "new_listings"
    CONTACT_DISCOVERY = "contact_discovery"
    VALIDATION_FAILURE = "validation_failure"
    SYSTEM_ALERT = "system_alert"
    SCRAPER_ERROR = "scraper_error"
    BACKUP_COMPLETE = "backup_complete"
    SCHEDULER_EVENT = "scheduler_event"


@dataclass
class NotificationMessage:
    """Represents a notification message to be sent."""
    
    id: str = field(default_factory=lambda: str(uuid4()))
    type: NotificationType = NotificationType.NEW_LISTINGS
    channel: NotificationChannel = NotificationChannel.DISCORD
    priority: NotificationPriority = NotificationPriority.NORMAL
    title: str = ""
    content: str = ""
    html_content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    recipients: List[str] = field(default_factory=list)
    template_name: Optional[str] = None
    template_data: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    scheduled_for: Optional[datetime] = None
    expires_at: Optional[datetime] = None
    tags: List[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Validate the notification message."""
        if not self.title and not self.content:
            raise ValueError("Notification must have either title or content")
        
        if self.scheduled_for and self.scheduled_for < self.created_at:
            raise ValueError("Scheduled time cannot be in the past")
        
        if self.expires_at and self.expires_at < self.created_at:
            raise ValueError("Expiration time cannot be in the past")


@dataclass
class NotificationResult:
    """Result of a notification delivery attempt."""
    
    message_id: str
    status: NotificationStatus
    channel: NotificationChannel
    sent_at: datetime = field(default_factory=datetime.now)
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    response_data: Dict[str, Any] = field(default_factory=dict)
    delivery_confirmation: Optional[str] = None
    
    @property
    def is_successful(self) -> bool:
        """Check if the notification was successfully delivered."""
        return self.status in [NotificationStatus.SENT, NotificationStatus.DELIVERED]
    
    @property
    def is_failed(self) -> bool:
        """Check if the notification delivery failed."""
        return self.status == NotificationStatus.FAILED
    
    @property
    def is_pending(self) -> bool:
        """Check if the notification is still pending."""
        return self.status in [NotificationStatus.PENDING, NotificationStatus.RETRYING]


class BaseNotifier(ABC):
    """Abstract base class for all notifiers."""
    
    def __init__(self, config: Dict[str, Any], name: str = None):
        """
        Initialize the notifier.
        
        Args:
            config: Configuration dictionary for this notifier
            name: Optional name for this notifier instance
        """
        self.config = config
        self.name = name or self.__class__.__name__
        self.enabled = config.get("enabled", True)
        self.rate_limit_delay = config.get("rate_limit_delay", 0)
        self.max_retries = config.get("max_retries", 3)
        self.retry_delay = config.get("retry_delay", 1.0)
        self.timeout = config.get("timeout", 30)
        self._last_send_time = 0.0
        
    @abstractmethod
    async def send_notification(self, message: NotificationMessage) -> NotificationResult:
        """
        Send a notification message.
        
        Args:
            message: The notification message to send
            
        Returns:
            NotificationResult with delivery status
        """
        pass
    
    @abstractmethod
    def validate_config(self) -> bool:
        """
        Validate the notifier configuration.
        
        Returns:
            True if configuration is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def get_channel_type(self) -> NotificationChannel:
        """
        Get the notification channel type this notifier handles.
        
        Returns:
            NotificationChannel enum value
        """
        pass
    
    async def send_with_retry(self, message: NotificationMessage) -> NotificationResult:
        """
        Send a notification with retry logic and rate limiting.
        
        Args:
            message: The notification message to send
            
        Returns:
            NotificationResult with final delivery status
        """
        if not self.enabled:
            return NotificationResult(
                message_id=message.id,
                status=NotificationStatus.CANCELLED,
                channel=message.channel,
                error_message="Notifier is disabled"
            )
        
        # Rate limiting
        if self.rate_limit_delay > 0:
            await self._enforce_rate_limit()
        
        # Retry logic
        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                result = await self.send_notification(message)
                if result.is_successful:
                    return result
                last_error = result.error_message
                if attempt < self.max_retries:
                    # Exponential backoff
                    delay = self.retry_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
            except Exception as e:
                last_error = str(e)
                if attempt < self.max_retries:
                    delay = self.retry_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
        
        # All retries exhausted
        return NotificationResult(
            message_id=message.id,
            status=NotificationStatus.FAILED,
            channel=message.channel,
            error_message=f"All retry attempts failed. Last error: {last_error}",
            retry_count=self.max_retries
        )
    
    async def _enforce_rate_limit(self):
        """Enforce rate limiting between notifications."""
        current_time = time.time()
        time_since_last = current_time - self._last_send_time
        if time_since_last < self.rate_limit_delay:
            await asyncio.sleep(self.rate_limit_delay - time_since_last)
        self._last_send_time = time.time()
    
    def format_message(self, message: NotificationMessage) -> Dict[str, Any]:
        """
        Format the notification message for this channel.
        
        Args:
            message: The notification message
            
        Returns:
            Dictionary with formatted message data
        """
        return {
            "title": message.title,
            "content": message.content,
            "html_content": message.html_content,
            "metadata": message.metadata,
            "priority": message.priority.value,
            "type": message.type.value,
            "created_at": message.created_at.isoformat(),
        }
    
    def __str__(self) -> str:
        """String representation of the notifier."""
        return f"{self.name}({self.get_channel_type().value})"
    
    def __repr__(self) -> str:
        """Detailed representation of the notifier."""
        return f"{self.__class__.__name__}(name='{self.name}', enabled={self.enabled})"


class NotificationFormatter:
    """Utility class for formatting notification messages."""
    
    @staticmethod
    def format_listings_message(listings: List[Dict[str, Any]], 
                              title: str = "New Apartment Listings") -> NotificationMessage:
        """
        Create a notification message for new listings.
        
        Args:
            listings: List of apartment listings
            title: Message title
            
        Returns:
            NotificationMessage instance
        """
        if not listings:
            raise ValueError("No listings provided")
        
        content_parts = []
        html_parts = []
        
        for listing in listings:
            title = listing.get("title", "No title")
            price = listing.get("price", "Price not specified")
            address = listing.get("address", "Address not specified")
            source = listing.get("source", "Unknown source")
            url = listing.get("url", "")
            
            # Plain text content
            content_parts.append(f"🏠 {title}")
            content_parts.append(f"💰 {price}")
            content_parts.append(f"📍 {address}")
            content_parts.append(f"🔗 {source}")
            if url:
                content_parts.append(f"🔗 {url}")
            content_parts.append("---")
            
            # HTML content
            html_parts.append(f"<h3>🏠 {title}</h3>")
            html_parts.append(f"<p><strong>Price:</strong> {price}</p>")
            html_parts.append(f"<p><strong>Address:</strong> {address}</p>")
            html_parts.append(f"<p><strong>Source:</strong> {source}</p>")
            if url:
                html_parts.append(f'<p><a href="{url}">View Listing</a></p>')
            html_parts.append("<hr>")
        
        content = "\n".join(content_parts)
        html_content = "\n".join(html_parts)
        
        return NotificationMessage(
            type=NotificationType.NEW_LISTINGS,
            title=title,
            content=content,
            html_content=html_content,
            metadata={"listings_count": len(listings)},
            template_data={"listings": listings}
        )
    
    @staticmethod
    def format_contact_discovery_message(contacts: List[Dict[str, Any]], 
                                       source_url: str) -> NotificationMessage:
        """
        Create a notification message for discovered contacts.
        
        Args:
            contacts: List of discovered contacts
            source_url: URL where contacts were discovered
            
        Returns:
            NotificationMessage instance
        """
        if not contacts:
            raise ValueError("No contacts provided")
        
        content_parts = [f"📞 Discovered {len(contacts)} new contacts from {source_url}"]
        html_parts = [f"<h2>📞 Contact Discovery Results</h2>"]
        html_parts.append(f"<p>Found <strong>{len(contacts)}</strong> new contacts from <a href='{source_url}'>{source_url}</a></p>")
        
        for contact in contacts:
            name = contact.get("name", "Unknown")
            email = contact.get("email", "")
            phone = contact.get("phone", "")
            confidence = contact.get("confidence", 0)
            
            content_parts.append(f"• {name}")
            if email:
                content_parts.append(f"  📧 {email}")
            if phone:
                content_parts.append(f"  📞 {phone}")
            content_parts.append(f"  Confidence: {confidence}%")
            
            html_parts.append(f"<h4>• {name}</h4>")
            if email:
                html_parts.append(f"<p>📧 <a href='mailto:{email}'>{email}</a></p>")
            if phone:
                html_parts.append(f"<p>📞 {phone}</p>")
            html_parts.append(f"<p>Confidence: {confidence}%</p>")
        
        return NotificationMessage(
            type=NotificationType.CONTACT_DISCOVERY,
            title=f"New Contacts Discovered ({len(contacts)})",
            content="\n".join(content_parts),
            html_content="\n".join(html_parts),
            metadata={
                "contacts_count": len(contacts),
                "source_url": source_url,
                "avg_confidence": sum(c.get("confidence", 0) for c in contacts) / len(contacts)
            }
        )
    
    @staticmethod
    def format_error_message(error_type: str, error_details: str, 
                           context: Dict[str, Any] = None) -> NotificationMessage:
        """
        Create a notification message for system errors.
        
        Args:
            error_type: Type of error
            error_details: Detailed error information
            context: Additional context information
            
        Returns:
            NotificationMessage instance
        """
        context = context or {}
        
        return NotificationMessage(
            type=NotificationType.SYSTEM_ALERT,
            priority=NotificationPriority.HIGH,
            title=f"System Alert: {error_type}",
            content=f"Error Type: {error_type}\nDetails: {error_details}",
            html_content=f"""
            <h2>🚨 System Alert</h2>
            <p><strong>Error Type:</strong> {error_type}</p>
            <p><strong>Details:</strong> {error_details}</p>
            {f'<p><strong>Context:</strong> {context}</p>' if context else ''}
            """,
            metadata={
                "error_type": error_type,
                "error_details": error_details,
                "context": context
            }
        )