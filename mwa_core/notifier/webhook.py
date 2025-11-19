"""
Generic webhook notifier for MWA Core with customizable requests.
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
    NotificationStatus
)

logger = logging.getLogger(__name__)


class WebhookNotifier(BaseNotifier):
    """Generic webhook notifier with customizable HTTP requests."""
    
    def __init__(self, config: Dict[str, Any], name: str = None):
        """
        Initialize webhook notifier.
        
        Args:
            config: Configuration dictionary
            name: Optional name for this notifier instance
        """
        super().__init__(config, name)
        
        # Webhook Configuration
        self.url = config.get("url")
        self.method = config.get("method", "POST").upper()
        self.headers = config.get("headers", {})
        self.auth = config.get("auth")  # Can be dict with username/password or token
        self.query_params = config.get("query_params", {})
        
        # Request Configuration
        self.content_type = config.get("content_type", "application/json")
        self.timeout = config.get("timeout", 30)
        self.follow_redirects = config.get("follow_redirects", True)
        self.verify_ssl = config.get("verify_ssl", True)
        
        # Payload Configuration
        self.payload_template = config.get("payload_template")
        self.use_raw_content = config.get("use_raw_content", False)
        self.custom_payload_keys = config.get("custom_payload_keys", {})
        
        # Response Configuration
        self.success_status_codes = config.get("success_status_codes", [200, 201, 202, 204])
        self.response_key_path = config.get("response_key_path")  # Path to check in response
        
        # Set default headers
        if "Content-Type" not in self.headers and not self.use_raw_content:
            self.headers["Content-Type"] = self.content_type
        
        # Setup authentication
        self._setup_authentication()
        
    def validate_config(self) -> bool:
        """Validate webhook notifier configuration."""
        if not self.url:
            logger.error("Webhook URL is required")
            return False
        
        # Validate URL format
        if not self.url.startswith(("http://", "https://")):
            logger.error("Invalid webhook URL format")
            return False
        
        # Validate HTTP method
        if self.method not in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
            logger.error(f"Unsupported HTTP method: {self.method}")
            return False
        
        # Validate authentication
        if self.auth:
            if isinstance(self.auth, dict):
                if "type" not in self.auth:
                    logger.error("Authentication type is required")
                    return False
                
                auth_type = self.auth["type"]
                if auth_type == "basic":
                    if "username" not in self.auth or "password" not in self.auth:
                        logger.error("Basic auth requires username and password")
                        return False
                elif auth_type == "bearer":
                    if "token" not in self.auth:
                        logger.error("Bearer auth requires token")
                        return False
                elif auth_type == "api_key":
                    if "key" not in self.auth or "value" not in self.auth:
                        logger.error("API key auth requires key and value")
                        return False
                else:
                    logger.error(f"Unsupported auth type: {auth_type}")
                    return False
        
        return True
    
    def get_channel_type(self) -> NotificationChannel:
        """Get the notification channel type."""
        return NotificationChannel.WEBHOOK
    
    def _setup_authentication(self):
        """Setup authentication headers based on config."""
        if not self.auth or not isinstance(self.auth, dict):
            return
        
        auth_type = self.auth.get("type")
        
        if auth_type == "basic":
            # Basic auth will be handled by httpx auth parameter
            pass
        elif auth_type == "bearer":
            self.headers["Authorization"] = f"Bearer {self.auth['token']}"
        elif auth_type == "api_key":
            key = self.auth["key"]
            value = self.auth["value"]
            header_name = self.auth.get("header_name", "X-API-Key")
            self.headers[header_name] = value
    
    async def send_notification(self, message: NotificationMessage) -> NotificationResult:
        """
        Send a notification via webhook.
        
        Args:
            message: The notification message to send
            
        Returns:
            NotificationResult with delivery status
        """
        try:
            # Build request
            request_data = await self._build_request(message)
            
            # Send request
            response = await self._send_request(request_data)
            
            # Check response
            if response.status_code in self.success_status_codes:
                # Check response content if required
                if self.response_key_path:
                    success = await self._check_response_content(response)
                    if not success:
                        return NotificationResult(
                            message_id=message.id,
                            status=NotificationStatus.FAILED,
                            channel=message.channel,
                            error_message="Response validation failed",
                            response_data={"status_code": response.status_code}
                        )
                
                return NotificationResult(
                    message_id=message.id,
                    status=NotificationStatus.DELIVERED,
                    channel=message.channel,
                    delivered_at=datetime.now(),
                    response_data={
                        "status_code": response.status_code,
                        "headers": dict(response.headers),
                        "text": response.text[:500]  # Limit response text
                    }
                )
            else:
                error_msg = f"Webhook returned status {response.status_code}: {response.text[:200]}"
                return NotificationResult(
                    message_id=message.id,
                    status=NotificationStatus.FAILED,
                    channel=message.channel,
                    error_message=error_msg,
                    response_data={
                        "status_code": response.status_code,
                        "text": response.text[:500]
                    }
                )
                
        except httpx.TimeoutException:
            return NotificationResult(
                message_id=message.id,
                status=NotificationStatus.FAILED,
                channel=message.channel,
                error_message="Request timeout"
            )
        except Exception as e:
            logger.error(f"Webhook notification failed: {e}")
            return NotificationResult(
                message_id=message.id,
                status=NotificationStatus.FAILED,
                channel=message.channel,
                error_message=str(e)
            )
    
    async def _build_request(self, message: NotificationMessage) -> Dict[str, Any]:
        """Build the HTTP request."""
        request = {
            "method": self.method,
            "url": self.url,
            "headers": self.headers.copy(),
            "params": self.query_params,
            "timeout": self.timeout,
            "follow_redirects": self.follow_redirects,
            "verify": self.verify_ssl,
        }
        
        # Add authentication
        if self.auth and isinstance(self.auth, dict):
            auth_type = self.auth.get("type")
            if auth_type == "basic":
                request["auth"] = (self.auth["username"], self.auth["password"])
        
        # Build payload
        if self.method in ["POST", "PUT", "PATCH"]:
            if self.use_raw_content:
                request["content"] = message.content
            else:
                request["json"] = self._build_payload(message)
        
        return request
    
    def _build_payload(self, message: NotificationMessage) -> Dict[str, Any]:
        """Build the request payload."""
        # Use custom template if provided
        if self.payload_template:
            return self._apply_payload_template(message)
        
        # Build standard payload
        payload = {
            "message_id": message.id,
            "type": message.type.value,
            "priority": message.priority.value,
            "channel": message.channel.value,
            "title": message.title or "",
            "content": message.content or "",
            "created_at": message.created_at.isoformat(),
        }
        
        # Add optional fields
        if message.html_content:
            payload["html_content"] = message.html_content
        
        if message.metadata:
            payload["metadata"] = message.metadata
        
        if message.template_data:
            payload["template_data"] = message.template_data
        
        if message.recipients:
            payload["recipients"] = message.recipients
        
        if message.tags:
            payload["tags"] = message.tags
        
        # Add custom payload keys
        for key, value in self.custom_payload_keys.items():
            payload[key] = value
        
        return payload
    
    def _apply_payload_template(self, message: NotificationMessage) -> Dict[str, Any]:
        """Apply custom payload template."""
        try:
            # Simple template substitution
            template_data = {
                "message_id": message.id,
                "type": message.type.value,
                "priority": message.priority.value,
                "title": message.title or "",
                "content": message.content or "",
                "html_content": message.html_content or "",
                "created_at": message.created_at.isoformat(),
                "metadata": message.metadata or {},
                "template_data": message.template_data or {},
                "recipients": message.recipients or [],
                "tags": message.tags or [],
            }
            
            # Simple string template substitution
            import json
            template_json = json.dumps(self.payload_template)
            
            for key, value in template_data.items():
                if isinstance(value, str):
                    template_json = template_json.replace(f"{{{key}}}", value)
                else:
                    template_json = template_json.replace(f'"{key}"', json.dumps(value))
            
            return json.loads(template_json)
            
        except Exception as e:
            logger.warning(f"Failed to apply payload template: {e}")
            return self._build_payload(message)  # Fallback to standard payload
    
    async def _send_request(self, request_data: Dict[str, Any]) -> httpx.Response:
        """Send the HTTP request."""
        async with httpx.AsyncClient() as client:
            method = request_data.pop("method")
            url = request_data.pop("url")
            
            if method == "GET":
                response = await client.get(url, **request_data)
            elif method == "POST":
                response = await client.post(url, **request_data)
            elif method == "PUT":
                response = await client.put(url, **request_data)
            elif method == "PATCH":
                response = await client.patch(url, **request_data)
            elif method == "DELETE":
                response = await client.delete(url, **request_data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            return response
    
    async def _check_response_content(self, response: httpx.Response) -> bool:
        """Check response content for success indicators."""
        try:
            response_data = response.json()
            
            # Navigate to the specified key path
            keys = self.response_key_path.split(".")
            current = response_data
            
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return False
            
            # Check if the value indicates success
            if isinstance(current, bool):
                return current
            elif isinstance(current, str):
                return current.lower() in ["success", "ok", "true", "1"]
            elif isinstance(current, int):
                return current == 1
            else:
                return bool(current)
                
        except Exception as e:
            logger.warning(f"Failed to check response content: {e}")
            return False
    
    async def send_listings(self, listings: List[Dict[str, Any]], 
                           custom_payload: Dict[str, Any] = None) -> NotificationResult:
        """
        Send new listings notification (legacy compatibility).
        
        Args:
            listings: List of apartment listings
            custom_payload: Optional custom payload data
            
        Returns:
            NotificationResult
        """
        if not listings:
            return NotificationResult(
                message_id="",
                status=NotificationStatus.CANCELLED,
                channel=NotificationChannel.WEBHOOK,
                error_message="No listings to send"
            )
        
        message = NotificationFormatter.format_listings_message(listings)
        message.channel = NotificationChannel.WEBHOOK
        
        # Add custom payload if provided
        if custom_payload:
            message.metadata.update(custom_payload)
        
        return await self.send_with_retry(message)
    
    def test_webhook(self) -> bool:
        """
        Test the webhook configuration.
        
        Returns:
            True if webhook is accessible
        """
        try:
            import httpx
            
            test_payload = {
                "test": True,
                "message": "MWA Webhook Notifier Test",
                "timestamp": datetime.now().isoformat()
            }
            
            response = httpx.post(self.url, json=test_payload, timeout=10)
            return response.status_code in self.success_status_codes
            
        except Exception as e:
            logger.error(f"Webhook test failed: {e}")
            return False


# Convenience function for quick webhook setup
def create_webhook_notifier(url: str, **kwargs) -> WebhookNotifier:
    """Create a webhook notifier with the given URL."""
    config = {
        "url": url,
        "method": kwargs.get("method", "POST"),
        "headers": kwargs.get("headers", {}),
        "auth": kwargs.get("auth"),
        "query_params": kwargs.get("query_params", {}),
        "content_type": kwargs.get("content_type", "application/json"),
        "timeout": kwargs.get("timeout", 30),
        "follow_redirects": kwargs.get("follow_redirects", True),
        "verify_ssl": kwargs.get("verify_ssl", True),
        "payload_template": kwargs.get("payload_template"),
        "use_raw_content": kwargs.get("use_raw_content", False),
        "custom_payload_keys": kwargs.get("custom_payload_keys", {}),
        "success_status_codes": kwargs.get("success_status_codes", [200, 201, 202, 204]),
        "response_key_path": kwargs.get("response_key_path"),
        "enabled": kwargs.get("enabled", True),
        "max_retries": kwargs.get("max_retries", 3),
        "retry_delay": kwargs.get("retry_delay", 1.0),
        "rate_limit_delay": kwargs.get("rate_limit_delay", 0),
    }
    return WebhookNotifier(config, kwargs.get("name"))