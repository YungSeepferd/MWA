"""
Tests for Discord notifier implementation.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from mwa_core.notifier.discord import DiscordNotifier
from mwa_core.notifier.base import (
    NotificationMessage, 
    NotificationResult, 
    NotificationStatus,
    NotificationType,
    NotificationPriority
)


class TestDiscordNotifier:
    """Test Discord notifier functionality."""
    
    def test_initialization(self):
        """Test Discord notifier initialization."""
        config = {
            "webhook_url": "https://discord.com/api/webhooks/123/abc",
            "username": "TestBot",
            "enabled": True
        }
        
        notifier = DiscordNotifier(config, "TestDiscord")
        
        assert notifier.webhook_url == "https://discord.com/api/webhooks/123/abc"
        assert notifier.username == "TestBot"
        assert notifier.enabled is True
        assert notifier.use_embeds is True
    
    def test_validation_valid_config(self):
        """Test validation with valid configuration."""
        config = {
            "webhook_url": "https://discord.com/api/webhooks/123/abc",
            "enabled": True
        }
        
        notifier = DiscordNotifier(config)
        assert notifier.validate_config() is True
    
    def test_validation_missing_webhook(self):
        """Test validation with missing webhook URL."""
        config = {
            "enabled": True
        }
        
        notifier = DiscordNotifier(config)
        assert notifier.validate_config() is False
    
    def test_validation_invalid_webhook_format(self):
        """Test validation with invalid webhook format."""
        config = {
            "webhook_url": "https://invalid-url.com/webhook",
            "enabled": True
        }
        
        notifier = DiscordNotifier(config)
        assert notifier.validate_config() is False
    
    def test_channel_type(self):
        """Test getting channel type."""
        config = {"webhook_url": "https://discord.com/api/webhooks/123/abc"}
        notifier = DiscordNotifier(config)
        
        from mwa_core.notifier.base import NotificationChannel
        assert notifier.get_channel_type() == NotificationChannel.DISCORD
    
    @pytest.mark.asyncio
    async def test_send_notification_success(self):
        """Test successful notification sending."""
        config = {
            "webhook_url": "https://discord.com/api/webhooks/123/abc",
            "enabled": True
        }
        
        notifier = DiscordNotifier(config)
        
        # Mock successful HTTP response
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 204
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            message = NotificationMessage(
                type=NotificationType.NEW_LISTINGS,
                title="Test Notification",
                content="Test content"
            )
            
            result = await notifier.send_notification(message)
            
            assert result.status == NotificationStatus.DELIVERED
            assert result.channel == notifier.get_channel_type()
            assert result.message_id == message.id
            
            # Verify HTTP request was made
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[1]['json'] is not None
    
    @pytest.mark.asyncio
    async def test_send_notification_rate_limited(self):
        """Test handling rate limiting."""
        config = {
            "webhook_url": "https://discord.com/api/webhooks/123/abc",
            "enabled": True
        }
        
        notifier = DiscordNotifier(config)
        
        # Mock rate limited response
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 429
            mock_response.headers = {"X-RateLimit-Reset-After": "60"}
            mock_response.text = "Rate limited"
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            message = NotificationMessage(
                type=NotificationType.SYSTEM_ALERT,
                title="Test Alert",
                content="Test alert content"
            )
            
            result = await notifier.send_notification(message)
            
            assert result.status == NotificationStatus.FAILED
            assert "Rate limited" in result.error_message
            assert result.response_data["retry_after"] == 60
    
    @pytest.mark.asyncio
    async def test_send_notification_timeout(self):
        """Test handling timeout."""
        config = {
            "webhook_url": "https://discord.com/api/webhooks/123/abc",
            "enabled": True
        }
        
        notifier = DiscordNotifier(config)
        
        # Mock timeout
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post.side_effect = httpx.TimeoutException("Request timeout")
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            message = NotificationMessage(
                type=NotificationType.NEW_LISTINGS,
                title="Test Listings",
                content="Test listings content"
            )
            
            result = await notifier.send_notification(message)
            
            assert result.status == NotificationStatus.FAILED
            assert "timeout" in result.error_message.lower()
    
    def test_build_payload_with_embeds(self):
        """Test building payload with embeds enabled."""
        config = {
            "webhook_url": "https://discord.com/api/webhooks/123/abc",
            "username": "TestBot",
            "use_embeds": True
        }
        
        notifier = DiscordNotifier(config)
        
        message = NotificationMessage(
            type=NotificationType.NEW_LISTINGS,
            title="New Listings Found",
            content="Found 3 new listings",
            priority=NotificationPriority.HIGH,
            metadata={"listings_count": 3}
        )
        
        payload = notifier._build_payload(message)
        
        assert payload["username"] == "TestBot"
        assert "embeds" in payload
        assert len(payload["embeds"]) == 1
        
        embed = payload["embeds"][0]
        assert embed["title"] == "New Listings Found"
        assert embed["description"] == "Found 3 new listings"
        assert embed["color"] == notifier.color_map["high"]  # HIGH priority color
    
    def test_build_payload_without_embeds(self):
        """Test building payload without embeds."""
        config = {
            "webhook_url": "https://discord.com/api/webhooks/123/abc",
            "use_embeds": False
        }
        
        notifier = DiscordNotifier(config)
        
        message = NotificationMessage(
            type=NotificationType.CONTACT_DISCOVERY,
            title="Contacts Found",
            content="Found 5 contacts"
        )
        
        payload = notifier._build_payload(message)
        
        assert "embeds" not in payload
        assert "content" in payload
        assert payload["content"] == "Found 5 contacts"
    
    def test_build_listings_embed(self):
        """Test building embed for listings."""
        config = {"webhook_url": "https://discord.com/api/webhooks/123/abc"}
        notifier = DiscordNotifier(config)
        
        message = NotificationMessage(
            type=NotificationType.NEW_LISTINGS,
            title="New Listings",
            content="Found new listings",
            template_data={
                "listings": [
                    {
                        "title": "Nice Apartment",
                        "price": "€1,200",
                        "address": "123 Main St",
                        "url": "https://example.com/listing1"
                    }
                ]
            },
            metadata={"listings_count": 1}
        )
        
        embed = notifier._build_embed(message)
        
        assert embed["title"] == "New Listings"
        assert "fields" in embed
        assert len(embed["fields"]) > 0
        
        # Check listing field
        listing_field = embed["fields"][-1]  # Last field should be the listing
        assert "Nice Apartment" in listing_field["name"]
        assert "€1,200" in listing_field["value"]
        assert "123 Main St" in listing_field["value"]
    
    def test_build_contact_embed(self):
        """Test building embed for contact discovery."""
        config = {"webhook_url": "https://discord.com/api/webhooks/123/abc"}
        notifier = DiscordNotifier(config)
        
        message = NotificationMessage(
            type=NotificationType.CONTACT_DISCOVERY,
            title="Contacts Discovered",
            content="Found contacts",
            metadata={
                "contacts_count": 2,
                "avg_confidence": 78.5,
                "source_url": "https://example.com/listing"
            }
        )
        
        embed = notifier._build_embed(message)
        
        assert embed["title"] == "Contacts Discovered"
        assert "fields" in embed
        
        # Find contacts count field
        contacts_field = next((f for f in embed["fields"] if "Contacts Found" in f["name"]), None)
        assert contacts_field is not None
        assert contacts_field["value"] == "2"
        
        # Find confidence field
        confidence_field = next((f for f in embed["fields"] if "Avg Confidence" in f["name"]), None)
        assert confidence_field is not None
        assert confidence_field["value"] == "78.5%"
    
    def test_build_alert_embed(self):
        """Test building embed for system alerts."""
        config = {"webhook_url": "https://discord.com/api/webhooks/123/abc"}
        notifier = DiscordNotifier(config)
        
        message = NotificationMessage(
            type=NotificationType.SYSTEM_ALERT,
            title="System Error",
            content="An error occurred",
            metadata={
                "error_type": "ConnectionError",
                "error_details": "Failed to connect to provider"
            }
        )
        
        embed = notifier._build_embed(message)
        
        assert embed["title"] == "System Error"
        assert "fields" in embed
        
        # Find error type field
        error_type_field = next((f for f in embed["fields"] if f["name"] == "Error Type"), None)
        assert error_type_field is not None
        assert error_type_field["value"] == "ConnectionError"
    
    def test_format_plain_text(self):
        """Test plain text formatting."""
        config = {"webhook_url": "https://discord.com/api/webhooks/123/abc"}
        notifier = DiscordNotifier(config)
        
        message = NotificationMessage(
            type=NotificationType.NEW_LISTINGS,
            title="Test Title",
            content="Test content",
            metadata={"listings_count": 5, "source": "TestSource"}
        )
        
        text = notifier._format_plain_text(message)
        
        assert "**Test Title**" in text
        assert "Test content" in text
        assert "**Listings Count:** 5" in text
        assert "**Source:** TestSource" in text
    
    @pytest.mark.asyncio
    async def test_send_listings_legacy(self):
        """Test legacy send_listings method."""
        config = {
            "webhook_url": "https://discord.com/api/webhooks/123/abc",
            "enabled": True
        }
        
        notifier = DiscordNotifier(config)
        
        # Mock successful response
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_response = Mock()
            mock_response.status_code = 204
            mock_client.post.return_value = mock_response
            mock_client_class.return_value.__aenter__.return_value = mock_client
            
            listings = [
                {"title": "Apartment 1", "price": "€1000"},
                {"title": "Apartment 2", "price": "€1200"}
            ]
            
            result = await notifier.send_listings(listings)
            
            assert result.status == NotificationStatus.DELIVERED
            assert result.channel == notifier.get_channel_type()
    
    def test_test_webhook_success(self):
        """Test webhook testing with success."""
        config = {
            "webhook_url": "https://discord.com/api/webhooks/123/abc",
            "username": "TestBot"
        }
        
        notifier = DiscordNotifier(config)
        
        # Mock successful test response
        with patch('httpx.post') as mock_post:
            mock_response = Mock()
            mock_response.status_code = 204
            mock_post.return_value = mock_response
            
            success = notifier.test_webhook()
            
            assert success is True
            mock_post.assert_called_once()
            
            # Check that test payload was sent
            call_args = mock_post.call_args
            payload = call_args[1]['json']
            assert "Test" in payload['content']
            assert payload['username'] == "TestBot"
    
    def test_test_webhook_failure(self):
        """Test webhook testing with failure."""
        config = {
            "webhook_url": "https://discord.com/api/webhooks/123/abc"
        }
        
        notifier = DiscordNotifier(config)
        
        # Mock failed test response
        with patch('httpx.post') as mock_post:
            mock_post.side_effect = Exception("Connection failed")
            
            success = notifier.test_webhook()
            
            assert success is False


@pytest.mark.asyncio
async def test_discord_integration():
    """Integration test for Discord notifier."""
    config = {
        "webhook_url": "https://discord.com/api/webhooks/test/test",
        "enabled": False  # Disable to avoid actual requests
    }
    
    notifier = DiscordNotifier(config)
    
    message = NotificationMessage(
        type=NotificationType.NEW_LISTINGS,
        title="Integration Test",
        content="Testing Discord notifier integration"
    )
    
    # Should handle disabled notifier gracefully
    result = await notifier.send_with_retry(message)
    
    if result.status == NotificationStatus.CANCELLED:
        assert "disabled" in result.error_message.lower()
    else:
        # If enabled, should either succeed or fail gracefully
        assert result.status in [NotificationStatus.DELIVERED, NotificationStatus.FAILED]


if __name__ == "__main__":
    pytest.main([__file__])