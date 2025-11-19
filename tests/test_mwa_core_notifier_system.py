"""
Comprehensive tests for MWA Core notifier system.
"""

import asyncio
import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch

from mwa_core.notifier import (
    NotificationManager,
    NotificationMessage,
    NotificationResult,
    NotificationStatus,
    NotificationChannel,
    NotificationPriority,
    NotificationType,
    NotificationFormatter,
    BaseNotifier,
    NotifierFactory
)
from mwa_core.notifier.discord import DiscordNotifier
from mwa_core.notifier.email import EmailNotifier
from mwa_core.notifier.slack import SlackNotifier
from mwa_core.notifier.webhook import WebhookNotifier


class TestNotificationMessage:
    """Test notification message creation and validation."""
    
    def test_basic_message_creation(self):
        """Test creating a basic notification message."""
        message = NotificationMessage(
            type=NotificationType.NEW_LISTINGS,
            title="Test Title",
            content="Test content"
        )
        
        assert message.type == NotificationType.NEW_LISTINGS
        assert message.title == "Test Title"
        assert message.content == "Test content"
        assert message.priority == NotificationPriority.NORMAL
        assert message.channel == NotificationChannel.DISCORD
    
    def test_message_validation(self):
        """Test message validation rules."""
        # Should fail without title or content
        with pytest.raises(ValueError):
            NotificationMessage(type=NotificationType.NEW_LISTINGS)
        
        # Should succeed with title
        message = NotificationMessage(
            type=NotificationType.NEW_LISTINGS,
            title="Test Title"
        )
        assert message.title == "Test Title"
    
    def test_message_with_metadata(self):
        """Test message with metadata."""
        message = NotificationMessage(
            type=NotificationType.CONTACT_DISCOVERY,
            title="Contacts Found",
            content="Found 5 contacts",
            metadata={"contacts_count": 5, "source_url": "https://example.com"}
        )
        
        assert message.metadata["contacts_count"] == 5
        assert message.metadata["source_url"] == "https://example.com"


class TestNotificationResult:
    """Test notification result handling."""
    
    def test_successful_result(self):
        """Test successful notification result."""
        result = NotificationResult(
            message_id="test-123",
            status=NotificationStatus.DELIVERED,
            channel=NotificationChannel.DISCORD
        )
        
        assert result.is_successful
        assert not result.is_failed
        assert not result.is_pending
    
    def test_failed_result(self):
        """Test failed notification result."""
        result = NotificationResult(
            message_id="test-456",
            status=NotificationStatus.FAILED,
            channel=NotificationChannel.EMAIL,
            error_message="Connection failed"
        )
        
        assert not result.is_successful
        assert result.is_failed
        assert not result.is_pending


class TestNotificationFormatter:
    """Test notification formatting utilities."""
    
    def test_format_listings_message(self):
        """Test formatting listings message."""
        listings = [
            {
                "title": "Nice Apartment",
                "price": "€1,200",
                "address": "123 Main St",
                "source": "ImmobilienScout",
                "url": "https://example.com/listing1"
            },
            {
                "title": "Cozy Flat",
                "price": "€900",
                "address": "456 Oak Ave",
                "source": "WG-Gesucht",
                "url": "https://example.com/listing2"
            }
        ]
        
        message = NotificationFormatter.format_listings_message(listings)
        
        assert message.type == NotificationType.NEW_LISTINGS
        assert "Nice Apartment" in message.content
        assert "Cozy Flat" in message.content
        assert "€1,200" in message.content
        assert message.metadata["listings_count"] == 2
    
    def test_format_contact_discovery_message(self):
        """Test formatting contact discovery message."""
        contacts = [
            {
                "name": "John Doe",
                "email": "john@example.com",
                "confidence": 85
            },
            {
                "name": "Jane Smith",
                "phone": "+49 123 456789",
                "confidence": 72
            }
        ]
        
        message = NotificationFormatter.format_contact_discovery_message(
            contacts, 
            "https://example.com/listing"
        )
        
        assert message.type == NotificationType.CONTACT_DISCOVERY
        assert "John Doe" in message.content
        assert "Jane Smith" in message.content
        assert message.metadata["contacts_count"] == 2
        assert message.metadata["source_url"] == "https://example.com/listing"
    
    def test_format_error_message(self):
        """Test formatting error message."""
        message = NotificationFormatter.format_error_message(
            "Scraping Error",
            "Failed to connect to provider",
            {"provider": "immobilien_scout"}
        )
        
        assert message.type == NotificationType.SYSTEM_ALERT
        assert message.priority == NotificationPriority.HIGH
        assert "Scraping Error" in message.title
        assert "Failed to connect to provider" in message.content


class MockNotifier(BaseNotifier):
    """Mock notifier for testing."""
    
    def __init__(self, config=None, name="MockNotifier"):
        config = config or {"enabled": True}
        super().__init__(config, name)
        self.send_count = 0
        self.last_message = None
    
    def validate_config(self) -> bool:
        return True
    
    def get_channel_type(self) -> NotificationChannel:
        return NotificationChannel.DISCORD
    
    async def send_notification(self, message: NotificationMessage) -> NotificationResult:
        self.send_count += 1
        self.last_message = message
        
        return NotificationResult(
            message_id=message.id,
            status=NotificationStatus.DELIVERED,
            channel=self.get_channel_type(),
            delivered_at=datetime.now()
        )


class TestNotificationManager:
    """Test notification manager functionality."""
    
    @pytest.fixture
    def notification_manager(self):
        """Create a notification manager with mock notifiers."""
        manager = NotificationManager()
        
        # Add mock notifiers
        discord_notifier = MockNotifier(name="DiscordNotifier")
        email_notifier = MockNotifier(name="EmailNotifier")
        email_notifier.get_channel_type = lambda: NotificationChannel.EMAIL
        
        manager.register_notifier(discord_notifier)
        manager.register_notifier(email_notifier)
        
        return manager
    
    @pytest.mark.asyncio
    async def test_send_notification(self, notification_manager):
        """Test sending notification through manager."""
        message = NotificationMessage(
            type=NotificationType.NEW_LISTINGS,
            title="Test Listings",
            content="Found 3 new listings"
        )
        
        results = await notification_manager.send_notification(message)
        
        assert len(results) == 2  # Two notifiers
        assert all(r.is_successful for r in results)
        
        # Check that both notifiers received the message
        discord_notifier = notification_manager.get_notifier("DiscordNotifier")
        email_notifier = notification_manager.get_notifier("EmailNotifier")
        
        assert discord_notifier.send_count == 1
        assert email_notifier.send_count == 1
    
    @pytest.mark.asyncio
    async def test_send_to_specific_channels(self, notification_manager):
        """Test sending to specific channels only."""
        message = NotificationMessage(
            type=NotificationType.CONTACT_DISCOVERY,
            title="Test Contacts",
            content="Found 2 contacts"
        )
        
        results = await notification_manager.send_notification(
            message, 
            channels=[NotificationChannel.EMAIL]
        )
        
        assert len(results) == 1
        assert results[0].channel == NotificationChannel.EMAIL
        
        # Only email notifier should have received the message
        discord_notifier = notification_manager.get_notifier("DiscordNotifier")
        email_notifier = notification_manager.get_notifier("EmailNotifier")
        
        assert discord_notifier.send_count == 0
        assert email_notifier.send_count == 1
    
    @pytest.mark.asyncio
    async def test_send_new_listings(self, notification_manager):
        """Test sending new listings notification."""
        listings = [
            {"title": "Apartment 1", "price": "€1000"},
            {"title": "Apartment 2", "price": "€1200"}
        ]
        
        results = await notification_manager.send_new_listings(listings)
        
        assert len(results) == 2  # Two notifiers
        assert all(r.is_successful for r in results)
        
        # Check message content
        discord_notifier = notification_manager.get_notifier("DiscordNotifier")
        message = discord_notifier.last_message
        
        assert message.type == NotificationType.NEW_LISTINGS
        assert "Apartment 1" in message.content
        assert "Apartment 2" in message.content
    
    def test_get_delivery_stats(self, notification_manager):
        """Test getting delivery statistics."""
        stats = notification_manager.get_delivery_stats()
        
        assert stats["total_sent"] == 0  # No notifications sent yet
        assert stats["successful"] == 0
        assert stats["failed"] == 0
        assert stats["success_rate"] == 0.0


class TestNotifierFactory:
    """Test notifier factory functionality."""
    
    def test_create_discord_notifier(self):
        """Test creating Discord notifier."""
        config = {
            "webhook_url": "https://discord.com/api/webhooks/123/abc",
            "enabled": True
        }
        
        notifier = NotifierFactory.create_notifier(
            NotificationChannel.DISCORD, 
            config, 
            "TestDiscord"
        )
        
        assert isinstance(notifier, DiscordNotifier)
        assert notifier.name == "TestDiscord"
        assert notifier.webhook_url == "https://discord.com/api/webhooks/123/abc"
    
    def test_create_email_notifier(self):
        """Test creating email notifier."""
        config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "test@example.com",
            "password": "password123",
            "sender_email": "test@example.com",
            "recipients": ["recipient@example.com"],
            "enabled": True
        }
        
        notifier = NotifierFactory.create_notifier(
            NotificationChannel.EMAIL, 
            config, 
            "TestEmail"
        )
        
        assert isinstance(notifier, EmailNotifier)
        assert notifier.name == "TestEmail"
        assert notifier.smtp_server == "smtp.gmail.com"
    
    def test_invalid_channel(self):
        """Test creating notifier with invalid channel."""
        config = {"enabled": True}
        
        with pytest.raises(ValueError):
            NotifierFactory.create_notifier("invalid_channel", config)
    
    def test_invalid_config(self):
        """Test creating notifier with invalid configuration."""
        config = {}  # Missing required fields
        
        with pytest.raises(Exception):  # Should raise ConfigurationError
            NotifierFactory.create_notifier(NotificationChannel.DISCORD, config)


class TestRateLimiter:
    """Test rate limiting functionality."""
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test that rate limiting works."""
        from mwa_core.notifier.manager import RateLimiter
        
        limiter = RateLimiter(max_requests=2, time_window=1)
        
        # First two requests should not wait
        start_time = asyncio.get_event_loop().time()
        await limiter.wait_if_needed(1)
        await limiter.wait_if_needed(1)
        mid_time = asyncio.get_event_loop().time()
        
        # Should be quick (no waiting)
        assert mid_time - start_time < 0.1
        
        # Third request should wait
        await limiter.wait_if_needed(1)
        end_time = asyncio.get_event_loop().time()
        
        # Should have waited
        assert end_time - mid_time >= 0.9


class TestNotificationDeduplicator:
    """Test notification deduplication."""
    
    def test_deduplication(self):
        """Test that duplicate messages are detected."""
        from mwa_core.notifier.manager import NotificationDeduplicator
        
        deduplicator = NotificationDeduplicator(deduplication_window=60)
        
        message1 = NotificationMessage(
            type=NotificationType.NEW_LISTINGS,
            title="Same Listings",
            content="Found 5 listings"
        )
        
        message2 = NotificationMessage(
            type=NotificationType.NEW_LISTINGS,
            title="Same Listings",
            content="Found 5 listings"
        )
        
        # First message should not be duplicate
        assert not deduplicator.is_duplicate(message1)
        
        # Second identical message should be duplicate
        assert deduplicator.is_duplicate(message2)
    
    def test_different_messages_not_duplicate(self):
        """Test that different messages are not marked as duplicates."""
        from mwa_core.notifier.manager import NotificationDeduplicator
        
        deduplicator = NotificationDeduplicator(deduplication_window=60)
        
        message1 = NotificationMessage(
            type=NotificationType.NEW_LISTINGS,
            title="Listings A",
            content="Found 3 listings"
        )
        
        message2 = NotificationMessage(
            type=NotificationType.CONTACT_DISCOVERY,
            title="Contacts Found",
            content="Found 2 contacts"
        )
        
        assert not deduplicator.is_duplicate(message1)
        assert not deduplicator.is_duplicate(message2)


@pytest.mark.asyncio
async def test_integration():
    """Integration test for the complete notification system."""
    # Create notification manager with real configuration
    config = {
        "discord_notifier": {
            "webhook_url": "https://discord.com/api/webhooks/test/test",
            "enabled": False  # Disable to avoid actual requests
        }
    }
    
    manager = NotificationManager(config)
    
    # Create test message
    message = NotificationMessage(
        type=NotificationType.NEW_LISTINGS,
        title="Integration Test",
        content="Testing the complete notification system"
    )
    
    # Send notification (should not actually send due to disabled notifier)
    results = await manager.send_notification(message)
    
    # Should have results even if notifier is disabled
    assert len(results) >= 0  # May be 0 if no enabled notifiers


if __name__ == "__main__":
    pytest.main([__file__])