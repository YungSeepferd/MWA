"""
Enhanced Discord notifier for MWA Core with rich formatting and advanced features.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx

from .base import (
    BaseNotifier,
    NotificationChannel,
    NotificationMessage,
    NotificationResult,
    NotificationStatus,
    NotificationFormatter
)

logger = logging.getLogger(__name__)


class DiscordNotifier(BaseNotifier):
    """Enhanced Discord notifier with rich embed formatting and advanced features."""
    
    def __init__(self, config: Dict[str, Any], name: str = None):
        """
        Initialize Discord notifier.
        
        Args:
            config: Configuration dictionary
            name: Optional name for this notifier instance
        """
        super().__init__(config, name)
        self.webhook_url = config.get("webhook_url")
        self.username = config.get("username", "MWA Bot")
        self.avatar_url = config.get("avatar_url")
        self.use_embeds = config.get("use_embeds", True)
        self.color_map = {
            "low": 0x00FF00,      # Green
            "normal": 0x0099FF,   # Blue
            "high": 0xFF9900,     # Orange
            "urgent": 0xFF0000,   # Red
        }
        
    def validate_config(self) -> bool:
        """Validate Discord notifier configuration."""
        if not self.webhook_url:
            logger.error("Discord webhook URL is required")
            return False
        
        if not self.webhook_url.startswith("https://discord.com/api/webhooks/"):
            logger.error("Invalid Discord webhook URL format")
            return False
        
        return True
    
    def get_channel_type(self) -> NotificationChannel:
        """Get the notification channel type."""
        return NotificationChannel.DISCORD
    
    async def send_notification(self, message: NotificationMessage) -> NotificationResult:
        """
        Send a notification to Discord.
        
        Args:
            message: The notification message to send
            
        Returns:
            NotificationResult with delivery status
        """
        try:
            payload = self._build_payload(message)
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.webhook_url, json=payload)
                
                if response.status_code == 204:
                    return NotificationResult(
                        message_id=message.id,
                        status=NotificationStatus.DELIVERED,
                        channel=message.channel,
                        delivered_at=datetime.now(),
                        response_data={"status_code": response.status_code}
                    )
                elif response.status_code == 429:
                    # Rate limited
                    retry_after = int(response.headers.get("X-RateLimit-Reset-After", 60))
                    return NotificationResult(
                        message_id=message.id,
                        status=NotificationStatus.FAILED,
                        channel=message.channel,
                        error_message=f"Rate limited. Retry after {retry_after} seconds",
                        response_data={"status_code": response.status_code, "retry_after": retry_after}
                    )
                else:
                    # Other error
                    error_msg = f"Discord API error: {response.status_code} - {response.text}"
                    return NotificationResult(
                        message_id=message.id,
                        status=NotificationStatus.FAILED,
                        channel=message.channel,
                        error_message=error_msg,
                        response_data={"status_code": response.status_code, "response_text": response.text}
                    )
                    
        except httpx.TimeoutException:
            return NotificationResult(
                message_id=message.id,
                status=NotificationStatus.FAILED,
                channel=message.channel,
                error_message="Request timeout"
            )
        except Exception as e:
            logger.error(f"Discord notification failed: {e}")
            return NotificationResult(
                message_id=message.id,
                status=NotificationStatus.FAILED,
                channel=message.channel,
                error_message=str(e)
            )
    
    def _build_payload(self, message: NotificationMessage) -> Dict[str, Any]:
        """Build Discord webhook payload."""
        payload = {
            "username": self.username,
            "content": "",
        }
        
        if self.avatar_url:
            payload["avatar_url"] = self.avatar_url
        
        if self.use_embeds:
            payload["embeds"] = [self._build_embed(message)]
        else:
            payload["content"] = self._format_plain_text(message)
        
        return payload
    
    def _build_embed(self, message: NotificationMessage) -> Dict[str, Any]:
        """Build a rich Discord embed."""
        embed = {
            "title": message.title or "MWA Notification",
            "description": message.content,
            "color": self.color_map.get(message.priority.value, 0x0099FF),
            "timestamp": message.created_at.isoformat(),
            "footer": {
                "text": f"MWA Core • {message.type.value.replace('_', ' ').title()}"
            }
        }
        
        # Add fields based on message type
        if message.type == "new_listings":
            embed.update(self._build_listings_embed(message))
        elif message.type == "contact_discovery":
            embed.update(self._build_contact_embed(message))
        elif message.type == "system_alert":
            embed.update(self._build_alert_embed(message))
        
        # Add metadata fields
        if message.metadata:
            embed["fields"] = self._build_metadata_fields(message.metadata)
        
        return embed
    
    def _build_listings_embed(self, message: NotificationMessage) -> Dict[str, Any]:
        """Build embed for new listings."""
        fields = []
        
        if "listings_count" in message.metadata:
            fields.append({
                "name": "📊 Total Listings",
                "value": str(message.metadata["listings_count"]),
                "inline": True
            })
        
        # Add first few listings as fields
        if "listings" in message.template_data:
            listings = message.template_data["listings"][:3]  # Limit to first 3
            for i, listing in enumerate(listings, 1):
                title = listing.get("title", "No title")
                price = listing.get("price", "Price not specified")
                address = listing.get("address", "Address not specified")
                url = listing.get("url", "")
                
                field_value = f"**Price:** {price}\n**Address:** {address}"
                if url:
                    field_value += f"\n[View Listing]({url})"
                
                fields.append({
                    "name": f"{i}. {title}",
                    "value": field_value,
                    "inline": False
                })
        
        return {"fields": fields}
    
    def _build_contact_embed(self, message: NotificationMessage) -> Dict[str, Any]:
        """Build embed for contact discovery."""
        fields = []
        
        if "contacts_count" in message.metadata:
            fields.append({
                "name": "👥 Contacts Found",
                "value": str(message.metadata["contacts_count"]),
                "inline": True
            })
        
        if "avg_confidence" in message.metadata:
            fields.append({
                "name": "🎯 Avg Confidence",
                "value": f"{message.metadata['avg_confidence']:.1f}%",
                "inline": True
            })
        
        if "source_url" in message.metadata:
            fields.append({
                "name": "🔗 Source",
                "value": f"[{message.metadata['source_url']}]({message.metadata['source_url']})",
                "inline": False
            })
        
        return {"fields": fields}
    
    def _build_alert_embed(self, message: NotificationMessage) -> Dict[str, Any]:
        """Build embed for system alerts."""
        fields = []
        
        if message.metadata:
            for key, value in message.metadata.items():
                if key in ["error_type", "error_details"]:
                    fields.append({
                        "name": key.replace("_", " ").title(),
                        "value": str(value),
                        "inline": False
                    })
        
        return {"fields": fields}
    
    def _build_metadata_fields(self, metadata: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Build embed fields from metadata."""
        fields = []
        
        for key, value in metadata.items():
            if key in ["listings_count", "contacts_count", "avg_confidence", "source_url"]:
                continue  # Already handled in specific embed builders
            
            fields.append({
                "name": key.replace("_", " ").title(),
                "value": str(value),
                "inline": True
            })
        
        return fields
    
    def _format_plain_text(self, message: NotificationMessage) -> str:
        """Format message as plain text for Discord."""
        parts = []
        
        if message.title:
            parts.append(f"**{message.title}**")
        
        if message.content:
            parts.append(message.content)
        
        # Add metadata
        if message.metadata:
            parts.append("---")
            for key, value in message.metadata.items():
                parts.append(f"**{key.replace('_', ' ').title()}:** {value}")
        
        return "\n".join(parts)
    
    async def send_listings(self, listings: List[Dict[str, Any]], 
                           template_name: str = None) -> NotificationResult:
        """
        Send new listings notification (legacy compatibility).
        
        Args:
            listings: List of apartment listings
            template_name: Optional template name (ignored)
            
        Returns:
            NotificationResult
        """
        if not listings:
            return NotificationResult(
                message_id="",
                status=NotificationStatus.CANCELLED,
                channel=NotificationChannel.DISCORD,
                error_message="No listings to send"
            )
        
        message = NotificationFormatter.format_listings_message(listings)
        message.channel = NotificationChannel.DISCORD
        
        return await self.send_with_retry(message)
    
    def test_webhook(self) -> bool:
        """
        Test the Discord webhook configuration.
        
        Returns:
            True if webhook is valid and accessible
        """
        try:
            import httpx
            
            test_payload = {
                "content": "🔧 **MWA Discord Notifier Test**\nWebhook configuration is working correctly!",
                "username": self.username,
            }
            
            response = httpx.post(self.webhook_url, json=test_payload, timeout=10)
            return response.status_code == 204
            
        except Exception as e:
            logger.error(f"Discord webhook test failed: {e}")
            return False


# Convenience function for quick Discord setup
def create_discord_notifier(webhook_url: str, **kwargs) -> DiscordNotifier:
    """Create a Discord notifier with the given webhook URL."""
    config = {
        "webhook_url": webhook_url,
        "username": kwargs.get("username", "MWA Bot"),
        "avatar_url": kwargs.get("avatar_url"),
        "use_embeds": kwargs.get("use_embeds", True),
        "enabled": kwargs.get("enabled", True),
        "max_retries": kwargs.get("max_retries", 3),
        "retry_delay": kwargs.get("retry_delay", 1.0),
        "timeout": kwargs.get("timeout", 30),
        "rate_limit_delay": kwargs.get("rate_limit_delay", 0),
    }
    return DiscordNotifier(config, kwargs.get("name"))