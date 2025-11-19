"""
Slack notifier for MWA Core with rich formatting and webhook support.
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


class SlackNotifier(BaseNotifier):
    """Slack notifier with rich block formatting and webhook support."""
    
    def __init__(self, config: Dict[str, Any], name: str = None):
        """
        Initialize Slack notifier.
        
        Args:
            config: Configuration dictionary
            name: Optional name for this notifier instance
        """
        super().__init__(config, name)
        self.webhook_url = config.get("webhook_url")
        self.channel = config.get("channel")
        self.username = config.get("username", "MWA Bot")
        self.icon_emoji = config.get("icon_emoji", ":robot_face:")
        self.icon_url = config.get("icon_url")
        self.use_blocks = config.get("use_blocks", True)
        self.color_map = {
            "low": "#36a64f",      # Green
            "normal": "#3498db",   # Blue
            "high": "#f39c12",     # Orange
            "urgent": "#e74c3c",   # Red
        }
        
    def validate_config(self) -> bool:
        """Validate Slack notifier configuration."""
        if not self.webhook_url:
            logger.error("Slack webhook URL is required")
            return False
        
        if not self.webhook_url.startswith("https://hooks.slack.com/services/"):
            logger.error("Invalid Slack webhook URL format")
            return False
        
        return True
    
    def get_channel_type(self) -> NotificationChannel:
        """Get the notification channel type."""
        return NotificationChannel.SLACK
    
    async def send_notification(self, message: NotificationMessage) -> NotificationResult:
        """
        Send a notification to Slack.
        
        Args:
            message: The notification message to send
            
        Returns:
            NotificationResult with delivery status
        """
        try:
            payload = self._build_payload(message)
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(self.webhook_url, json=payload)
                
                if response.status_code == 200:
                    return NotificationResult(
                        message_id=message.id,
                        status=NotificationStatus.DELIVERED,
                        channel=message.channel,
                        delivered_at=datetime.now(),
                        response_data={"status_code": response.status_code}
                    )
                elif response.status_code == 429:
                    # Rate limited
                    retry_after = int(response.headers.get("Retry-After", 60))
                    return NotificationResult(
                        message_id=message.id,
                        status=NotificationStatus.FAILED,
                        channel=message.channel,
                        error_message=f"Rate limited. Retry after {retry_after} seconds",
                        response_data={"status_code": response.status_code, "retry_after": retry_after}
                    )
                else:
                    # Other error
                    error_msg = f"Slack API error: {response.status_code} - {response.text}"
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
            logger.error(f"Slack notification failed: {e}")
            return NotificationResult(
                message_id=message.id,
                status=NotificationStatus.FAILED,
                channel=message.channel,
                error_message=str(e)
            )
    
    def _build_payload(self, message: NotificationMessage) -> Dict[str, Any]:
        """Build Slack webhook payload."""
        payload = {
            "username": self.username,
            "text": "",  # Fallback text
        }
        
        # Add icon
        if self.icon_emoji:
            payload["icon_emoji"] = self.icon_emoji
        elif self.icon_url:
            payload["icon_url"] = self.icon_url
        
        # Add channel override if specified
        if self.channel:
            payload["channel"] = self.channel
        
        if self.use_blocks:
            payload["blocks"] = self._build_blocks(message)
            payload["text"] = self._build_fallback_text(message)
        else:
            payload["text"] = self._format_plain_text(message)
            payload["attachments"] = [self._build_attachment(message)]
        
        return payload
    
    def _build_blocks(self, message: NotificationMessage) -> List[Dict[str, Any]]:
        """Build Slack blocks for rich formatting."""
        blocks = []
        
        # Header block
        header_text = message.title or "MWA Notification"
        blocks.append({
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": header_text,
                "emoji": True
            }
        })
        
        # Context block with type and priority
        context_elements = [
            {
                "type": "mrkdwn",
                "text": f"*Type:* {message.type.value.replace('_', ' ').title()}"
            },
            {
                "type": "mrkdwn",
                "text": f"*Priority:* {message.priority.value.title()}"
            }
        ]
        
        if message.metadata and "listings_count" in message.metadata:
            context_elements.append({
                "type": "mrkdwn",
                "text": f"*Count:* {message.metadata['listings_count']}"
            })
        
        blocks.append({
            "type": "context",
            "elements": context_elements
        })
        
        # Divider
        blocks.append({"type": "divider"})
        
        # Main content
        if message.content:
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": self._format_slack_markdown(message.content)
                }
            })
        
        # Type-specific blocks
        if message.type == "new_listings":
            blocks.extend(self._build_listings_blocks(message))
        elif message.type == "contact_discovery":
            blocks.extend(self._build_contact_blocks(message))
        elif message.type == "system_alert":
            blocks.extend(self._build_alert_blocks(message))
        
        # Metadata section
        if message.metadata:
            blocks.append({"type": "divider"})
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": self._format_metadata_markdown(message.metadata)
                }
            })
        
        # Footer
        blocks.append({"type": "divider"})
        blocks.append({
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": f"Sent at {message.created_at.strftime('%Y-%m-%d %H:%M:%S')} • Message ID: {message.id[:8]}..."
                }
            ]
        })
        
        return blocks
    
    def _build_listings_blocks(self, message: NotificationMessage) -> List[Dict[str, Any]]:
        """Build blocks for new listings."""
        blocks = []
        
        if "listings" in message.template_data:
            listings = message.template_data["listings"][:5]  # Limit to first 5
            
            for i, listing in enumerate(listings, 1):
                title = listing.get("title", "No title")
                price = listing.get("price", "Price not specified")
                address = listing.get("address", "Address not specified")
                url = listing.get("url", "")
                
                # Create accessory (button) if URL is available
                accessory = None
                if url:
                    accessory = {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "View Listing",
                            "emoji": True
                        },
                        "url": url,
                        "style": "primary"
                    }
                
                # Build section
                section = {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*{i}. {title}*\n💰 *Price:* {price}\n📍 *Address:* {address}"
                    }
                }
                
                if accessory:
                    section["accessory"] = accessory
                
                blocks.append(section)
            
            # Add "and more..." if there are more listings
            total_listings = len(message.template_data["listings"])
            if total_listings > 5:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"_...and {total_listings - 5} more listings_"
                    }
                })
        
        return blocks
    
    def _build_contact_blocks(self, message: NotificationMessage) -> List[Dict[str, Any]]:
        """Build blocks for contact discovery."""
        blocks = []
        
        if "contacts" in message.template_data:
            contacts = message.template_data["contacts"][:3]  # Limit to first 3
            
            for contact in contacts:
                name = contact.get("name", "Unknown")
                email = contact.get("email", "")
                phone = contact.get("phone", "")
                confidence = contact.get("confidence", 0)
                
                contact_text = f"👤 *{name}*"
                if email:
                    contact_text += f"\n📧 {email}"
                if phone:
                    contact_text += f"\n📞 {phone}"
                contact_text += f"\n🎯 Confidence: {confidence}%"
                
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": contact_text
                    }
                })
        
        return blocks
    
    def _build_alert_blocks(self, message: NotificationMessage) -> List[Dict[str, Any]]:
        """Build blocks for system alerts."""
        blocks = []
        
        if message.metadata:
            # Error type
            if "error_type" in message.metadata:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"⚠️ *Error Type:* {message.metadata['error_type']}"
                    }
                })
            
            # Error details
            if "error_details" in message.metadata:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Details:* {message.metadata['error_details']}"
                    }
                })
            
            # Context
            if "context" in message.metadata:
                blocks.append({
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Context:* {message.metadata['context']}"
                    }
                })
        
        return blocks
    
    def _build_attachment(self, message: NotificationMessage) -> Dict[str, Any]:
        """Build legacy attachment format."""
        attachment = {
            "color": self.color_map.get(message.priority.value, "#3498db"),
            "title": message.title or "MWA Notification",
            "text": message.content or "",
            "footer": f"MWA Core • {message.type.value.replace('_', ' ').title()}",
            "ts": int(message.created_at.timestamp())
        }
        
        # Add fields based on message type
        if message.type == "new_listings" and "listings_count" in message.metadata:
            attachment["fields"] = [
                {
                    "title": "Total Listings",
                    "value": str(message.metadata["listings_count"]),
                    "short": True
                }
            ]
        
        return attachment
    
    def _build_fallback_text(self, message: NotificationMessage) -> str:
        """Build fallback text for notifications that don't support blocks."""
        parts = []
        
        if message.title:
            parts.append(f"*{message.title}*")
        
        if message.content:
            parts.append(message.content)
        
        # Add basic metadata
        if message.metadata:
            parts.append("---")
            for key, value in message.metadata.items():
                if key in ["listings_count", "contacts_count"]:
                    parts.append(f"*{key.replace('_', ' ').title()}:* {value}")
        
        return "\n".join(parts)
    
    def _format_plain_text(self, message: NotificationMessage) -> str:
        """Format message as plain text for Slack."""
        parts = []
        
        if message.title:
            parts.append(f"*{message.title}*")
        
        if message.content:
            parts.append(message.content)
        
        # Add metadata
        if message.metadata:
            parts.append("---")
            for key, value in message.metadata.items():
                parts.append(f"*{key.replace('_', ' ').title()}:* {value}")
        
        return "\n".join(parts)
    
    def _format_slack_markdown(self, content: str) -> str:
        """Format content for Slack markdown."""
        # Convert basic formatting to Slack markdown
        content = content.replace("🏠", "*🏠*")
        content = content.replace("💰", "*💰*")
        content = content.replace("📍", "*📍*")
        content = content.replace("🔗", "*🔗*")
        content = content.replace("📧", "*📧*")
        content = content.replace("📞", "*📞*")
        content = content.replace("👥", "*👥*")
        content = content.replace("🎯", "*🎯*")
        
        return content
    
    def _format_metadata_markdown(self, metadata: Dict[str, Any]) -> str:
        """Format metadata as Slack markdown."""
        parts = []
        
        for key, value in metadata.items():
            if key in ["listings_count", "contacts_count"]:
                parts.append(f"*{key.replace('_', ' ').title()}:* {value}")
            elif key == "avg_confidence":
                parts.append(f"*Average Confidence:* {value:.1f}%")
            elif key == "source_url":
                parts.append(f"*Source:* {value}")
        
        return "\n".join(parts)
    
    async def send_listings(self, listings: List[Dict[str, Any]]) -> NotificationResult:
        """
        Send new listings notification (legacy compatibility).
        
        Args:
            listings: List of apartment listings
            
        Returns:
            NotificationResult
        """
        if not listings:
            return NotificationResult(
                message_id="",
                status=NotificationStatus.CANCELLED,
                channel=NotificationChannel.SLACK,
                error_message="No listings to send"
            )
        
        message = NotificationFormatter.format_listings_message(listings)
        message.channel = NotificationChannel.SLACK
        
        return await self.send_with_retry(message)
    
    def test_webhook(self) -> bool:
        """
        Test the Slack webhook configuration.
        
        Returns:
            True if webhook is valid and accessible
        """
        try:
            import httpx
            
            test_payload = {
                "text": "🔧 *MWA Slack Notifier Test*\nWebhook configuration is working correctly!",
                "username": self.username,
                "icon_emoji": self.icon_emoji
            }
            
            response = httpx.post(self.webhook_url, json=test_payload, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Slack webhook test failed: {e}")
            return False


# Convenience function for quick Slack setup
def create_slack_notifier(webhook_url: str, **kwargs) -> SlackNotifier:
    """Create a Slack notifier with the given webhook URL."""
    config = {
        "webhook_url": webhook_url,
        "channel": kwargs.get("channel"),
        "username": kwargs.get("username", "MWA Bot"),
        "icon_emoji": kwargs.get("icon_emoji", ":robot_face:"),
        "icon_url": kwargs.get("icon_url"),
        "use_blocks": kwargs.get("use_blocks", True),
        "enabled": kwargs.get("enabled", True),
        "max_retries": kwargs.get("max_retries", 3),
        "retry_delay": kwargs.get("retry_delay", 1.0),
        "timeout": kwargs.get("timeout", 30),
        "rate_limit_delay": kwargs.get("rate_limit_delay", 0),
    }
    return SlackNotifier(config, kwargs.get("name"))