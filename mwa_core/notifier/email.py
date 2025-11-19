"""
Email notifier for MWA Core with HTML templates and advanced features.
"""

from __future__ import annotations

import asyncio
import logging
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from typing import Any, Dict, List, Optional
from pathlib import Path

import aiofiles
import jinja2

from .base import (
    BaseNotifier,
    NotificationChannel,
    NotificationMessage,
    NotificationResult,
    NotificationStatus,
    NotificationFormatter
)

logger = logging.getLogger(__name__)


class EmailNotifier(BaseNotifier):
    """Email notifier with HTML templates and attachment support."""
    
    def __init__(self, config: Dict[str, Any], name: str = None):
        """
        Initialize email notifier.
        
        Args:
            config: Configuration dictionary
            name: Optional name for this notifier instance
        """
        super().__init__(config, name)
        
        # SMTP Configuration
        self.smtp_server = config.get("smtp_server")
        self.smtp_port = config.get("smtp_port", 587)
        self.username = config.get("username")
        self.password = config.get("password")
        self.use_tls = config.get("use_tls", True)
        self.use_ssl = config.get("use_ssl", False)
        
        # Email Configuration
        self.sender_email = config.get("sender_email", self.username)
        self.sender_name = config.get("sender_name", "MWA Notifications")
        self.recipients = config.get("recipients", [])
        self.cc_recipients = config.get("cc_recipients", [])
        self.bcc_recipients = config.get("bcc_recipients", [])
        
        # Template Configuration
        self.template_dir = config.get("template_dir", "mwa_core/notifier/templates")
        self.default_template = config.get("default_template", "email_default.html")
        self.use_html = config.get("use_html", True)
        
        # Initialize Jinja2 environment
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(self.template_dir),
            autoescape=jinja2.select_autoescape(['html', 'xml'])
        )
        
        # Add custom filters
        self.jinja_env.filters['format_datetime'] = self._format_datetime
        self.jinja_env.filters['format_price'] = self._format_price
        
    def validate_config(self) -> bool:
        """Validate email notifier configuration."""
        if not self.smtp_server:
            logger.error("SMTP server is required")
            return False
        
        if not self.username or not self.password:
            logger.error("SMTP username and password are required")
            return False
        
        if not self.sender_email:
            logger.error("Sender email is required")
            return False
        
        if not self.recipients:
            logger.error("At least one recipient is required")
            return False
        
        # Validate email addresses
        for email in self.recipients + self.cc_recipients + self.bcc_recipients:
            if not self._is_valid_email(email):
                logger.error(f"Invalid email address: {email}")
                return False
        
        return True
    
    def get_channel_type(self) -> NotificationChannel:
        """Get the notification channel type."""
        return NotificationChannel.EMAIL
    
    async def send_notification(self, message: NotificationMessage) -> NotificationResult:
        """
        Send an email notification.
        
        Args:
            message: The notification message to send
            
        Returns:
            NotificationResult with delivery status
        """
        try:
            # Build email message
            email_message = await self._build_email_message(message)
            
            # Send email
            await self._send_email(email_message)
            
            return NotificationResult(
                message_id=message.id,
                status=NotificationStatus.DELIVERED,
                channel=message.channel,
                delivered_at=datetime.now(),
                response_data={"recipients": len(self.recipients)}
            )
            
        except smtplib.SMTPAuthenticationError as e:
            error_msg = f"SMTP authentication failed: {e}"
            logger.error(error_msg)
            return NotificationResult(
                message_id=message.id,
                status=NotificationStatus.FAILED,
                channel=message.channel,
                error_message=error_msg
            )
        except smtplib.SMTPException as e:
            error_msg = f"SMTP error: {e}"
            logger.error(error_msg)
            return NotificationResult(
                message_id=message.id,
                status=NotificationStatus.FAILED,
                channel=message.channel,
                error_message=error_msg
            )
        except Exception as e:
            error_msg = f"Email notification failed: {e}"
            logger.error(error_msg)
            return NotificationResult(
                message_id=message.id,
                status=NotificationStatus.FAILED,
                channel=message.channel,
                error_message=error_msg
            )
    
    async def _build_email_message(self, message: NotificationMessage) -> MIMEMultipart:
        """Build a complete email message."""
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = message.title or "MWA Notification"
        msg['From'] = f"{self.sender_name} <{self.sender_email}>"
        msg['To'] = ', '.join(self.recipients)
        
        if self.cc_recipients:
            msg['Cc'] = ', '.join(self.cc_recipients)
        
        # Add message ID
        msg['Message-ID'] = f"{message.id}@{self.smtp_server}"
        
        # Add priority header
        if message.priority == "urgent":
            msg['X-Priority'] = '1'
            msg['X-MSMail-Priority'] = 'High'
        elif message.priority == "high":
            msg['X-Priority'] = '2'
            msg['X-MSMail-Priority'] = 'High'
        
        # Build text content
        text_content = self._build_text_content(message)
        msg.attach(MIMEText(text_content, 'plain'))
        
        # Build HTML content if enabled
        if self.use_html:
            html_content = await self._build_html_content(message)
            msg.attach(MIMEText(html_content, 'html'))
        
        # Add attachments if any
        if message.metadata and "attachments" in message.metadata:
            for attachment in message.metadata["attachments"]:
                await self._add_attachment(msg, attachment)
        
        return msg
    
    def _build_text_content(self, message: NotificationMessage) -> str:
        """Build plain text email content."""
        parts = []
        
        # Header
        parts.append(f"MWA Notification - {message.type.value.replace('_', ' ').title()}")
        parts.append("=" * 50)
        parts.append("")
        
        # Main content
        if message.content:
            parts.append(message.content)
            parts.append("")
        
        # Metadata
        if message.metadata:
            parts.append("Details:")
            for key, value in message.metadata.items():
                if key != "attachments":  # Skip attachments in text
                    parts.append(f"  {key.replace('_', ' ').title()}: {value}")
            parts.append("")
        
        # Footer
        parts.append("---")
        parts.append(f"Sent at: {message.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        parts.append(f"Message ID: {message.id}")
        
        return "\n".join(parts)
    
    async def _build_html_content(self, message: NotificationMessage) -> str:
        """Build HTML email content."""
        try:
            # Determine template
            template_name = message.template_name or self.default_template
            
            # Check if custom template exists
            template_path = Path(self.template_dir) / template_name
            if not template_path.exists():
                # Use default template
                return self._build_default_html(message)
            
            # Load and render template
            template = self.jinja_env.get_template(template_name)
            
            # Prepare template data
            template_data = {
                "message": message,
                "title": message.title or "MWA Notification",
                "content": message.content or "",
                "html_content": message.html_content or "",
                "metadata": message.metadata or {},
                "created_at": message.created_at,
                "priority": message.priority.value,
                "type": message.type.value,
                "message_id": message.id,
            }
            
            # Add type-specific data
            if message.type == "new_listings" and "listings" in message.template_data:
                template_data["listings"] = message.template_data["listings"]
            elif message.type == "contact_discovery" and "contacts" in message.template_data:
                template_data["contacts"] = message.template_data["contacts"]
            
            # Render template
            return template.render(**template_data)
            
        except Exception as e:
            logger.warning(f"Failed to render HTML template {template_name}: {e}")
            return self._build_default_html(message)
    
    def _build_default_html(self, message: NotificationMessage) -> str:
        """Build default HTML content when template is not available."""
        html_parts = []
        
        # Header
        html_parts.append("<!DOCTYPE html>")
        html_parts.append("<html>")
        html_parts.append("<head>")
        html_parts.append("<meta charset='utf-8'>")
        html_parts.append("<meta name='viewport' content='width=device-width, initial-scale=1.0'>")
        html_parts.append(f"<title>{message.title or 'MWA Notification'}</title>")
        html_parts.append("<style>")
        html_parts.append(self._get_default_css())
        html_parts.append("</style>")
        html_parts.append("</head>")
        html_parts.append("<body>")
        
        # Container
        html_parts.append("<div class='container'>")
        
        # Header section
        html_parts.append(f"<div class='header {message.priority.value}'>")
        html_parts.append(f"<h1>{message.title or 'MWA Notification'}</h1>")
        html_parts.append(f"<p class='subtitle'>{message.type.value.replace('_', ' ').title()}</p>")
        html_parts.append("</div>")
        
        # Content section
        html_parts.append("<div class='content'>")
        
        if message.html_content:
            html_parts.append(message.html_content)
        elif message.content:
            # Convert plain text to HTML
            content_html = message.content.replace("\n", "<br>")
            html_parts.append(f"<div class='main-content'>{content_html}</div>")
        
        # Metadata section
        if message.metadata:
            html_parts.append("<div class='metadata'>")
            html_parts.append("<h3>Details</h3>")
            html_parts.append("<table>")
            for key, value in message.metadata.items():
                if key != "attachments":
                    html_parts.append(f"<tr><td><strong>{key.replace('_', ' ').title()}:</strong></td>")
                    html_parts.append(f"<td>{value}</td></tr>")
            html_parts.append("</table>")
            html_parts.append("</div>")
        
        html_parts.append("</div>")
        
        # Footer
        html_parts.append("<div class='footer'>")
        html_parts.append(f"<p>Sent on {message.created_at.strftime('%Y-%m-%d at %H:%M:%S')}</p>")
        html_parts.append(f"<p>Message ID: {message.id}</p>")
        html_parts.append("</div>")
        
        html_parts.append("</div>")
        html_parts.append("</body>")
        html_parts.append("</html>")
        
        return "\n".join(html_parts)
    
    def _get_default_css(self) -> str:
        """Get default CSS styles for HTML emails."""
        return """
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f5f5;
            margin: 0;
            padding: 20px;
        }
        .container {
            max-width: 600px;
            margin: 0 auto;
            background-color: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }
        .header {
            padding: 20px;
            color: white;
            text-align: center;
        }
        .header.low { background-color: #28a745; }
        .header.normal { background-color: #17a2b8; }
        .header.high { background-color: #ffc107; color: #333; }
        .header.urgent { background-color: #dc3545; }
        .header h1 {
            margin: 0;
            font-size: 24px;
        }
        .subtitle {
            margin: 5px 0 0 0;
            opacity: 0.9;
        }
        .content {
            padding: 20px;
        }
        .main-content {
            margin-bottom: 20px;
        }
        .metadata {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin-top: 20px;
        }
        .metadata h3 {
            margin-top: 0;
            color: #495057;
        }
        .metadata table {
            width: 100%;
            border-collapse: collapse;
        }
        .metadata td {
            padding: 5px 0;
            border-bottom: 1px solid #dee2e6;
        }
        .metadata td:first-child {
            width: 40%;
            font-weight: bold;
        }
        .footer {
            background-color: #f8f9fa;
            padding: 15px;
            text-align: center;
            color: #6c757d;
            font-size: 14px;
        }
        .footer p {
            margin: 5px 0;
        }
        """
    
    async def _send_email(self, message: MIMEMultipart) -> None:
        """Send the email message."""
        # Combine all recipients
        all_recipients = self.recipients + self.cc_recipients + self.bcc_recipients
        
        # Choose SMTP connection method
        if self.use_ssl:
            await self._send_email_ssl(message, all_recipients)
        else:
            await self._send_email_tls(message, all_recipients)
    
    async def _send_email_tls(self, message: MIMEMultipart, recipients: List[str]) -> None:
        """Send email using TLS connection."""
        loop = asyncio.get_event_loop()
        
        def _send():
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.send_message(message, to_addrs=recipients)
        
        await loop.run_in_executor(None, _send)
    
    async def _send_email_ssl(self, message: MIMEMultipart, recipients: List[str]) -> None:
        """Send email using SSL connection."""
        loop = asyncio.get_event_loop()
        
        def _send():
            with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port) as server:
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.send_message(message, to_addrs=recipients)
        
        await loop.run_in_executor(None, _send)
    
    async def _add_attachment(self, msg: MIMEMultipart, attachment: Dict[str, Any]) -> None:
        """Add an attachment to the email message."""
        try:
            filename = attachment.get("filename")
            content = attachment.get("content")
            content_type = attachment.get("content_type", "application/octet-stream")
            
            if not filename or not content:
                return
            
            # Create attachment part
            part = MIMEBase(*content_type.split('/', 1))
            part.set_payload(content)
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename="{filename}"'
            )
            
            msg.attach(part)
            
        except Exception as e:
            logger.warning(f"Failed to add attachment {filename}: {e}")
    
    def _is_valid_email(self, email: str) -> bool:
        """Basic email validation."""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _format_datetime(self, value: datetime) -> str:
        """Format datetime for templates."""
        return value.strftime('%Y-%m-%d %H:%M:%S')
    
    def _format_price(self, value: str) -> str:
        """Format price for templates."""
        if isinstance(value, str) and '€' in value:
            return value
        return f"€{value}"
    
    async def send_listings(self, listings: List[Dict[str, Any]], 
                           recipients: List[str] = None) -> NotificationResult:
        """
        Send new listings notification (legacy compatibility).
        
        Args:
            listings: List of apartment listings
            recipients: Optional list of recipients (overrides config)
            
        Returns:
            NotificationResult
        """
        if not listings:
            return NotificationResult(
                message_id="",
                status=NotificationStatus.CANCELLED,
                channel=NotificationChannel.EMAIL,
                error_message="No listings to send"
            )
        
        # Override recipients if provided
        if recipients:
            original_recipients = self.recipients
            self.recipients = recipients
        
        try:
            message = NotificationFormatter.format_listings_message(listings)
            message.channel = NotificationChannel.EMAIL
            
            result = await self.send_with_retry(message)
            return result
            
        finally:
            # Restore original recipients
            if recipients:
                self.recipients = original_recipients
    
    def test_connection(self) -> bool:
        """
        Test the email connection and authentication.
        
        Returns:
            True if connection is successful
        """
        try:
            if self.use_ssl:
                with smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=10) as server:
                    if self.username and self.password:
                        server.login(self.username, self.password)
            else:
                with smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=10) as server:
                    server.starttls()
                    if self.username and self.password:
                        server.login(self.username, self.password)
            
            return True
            
        except Exception as e:
            logger.error(f"Email connection test failed: {e}")
            return False


# Convenience function for quick email setup
def create_email_notifier(smtp_server: str, username: str, password: str, 
                         recipients: List[str], **kwargs) -> EmailNotifier:
    """Create an email notifier with the given SMTP settings."""
    config = {
        "smtp_server": smtp_server,
        "smtp_port": kwargs.get("smtp_port", 587),
        "username": username,
        "password": password,
        "sender_email": kwargs.get("sender_email", username),
        "sender_name": kwargs.get("sender_name", "MWA Notifications"),
        "recipients": recipients,
        "cc_recipients": kwargs.get("cc_recipients", []),
        "bcc_recipients": kwargs.get("bcc_recipients", []),
        "use_tls": kwargs.get("use_tls", True),
        "use_ssl": kwargs.get("use_ssl", False),
        "enabled": kwargs.get("enabled", True),
        "max_retries": kwargs.get("max_retries", 3),
        "retry_delay": kwargs.get("retry_delay", 1.0),
        "timeout": kwargs.get("timeout", 30),
        "rate_limit_delay": kwargs.get("rate_limit_delay", 1.0),
        "template_dir": kwargs.get("template_dir", "mwa_core/notifier/templates"),
        "default_template": kwargs.get("default_template", "email_default.html"),
        "use_html": kwargs.get("use_html", True),
    }
    return EmailNotifier(config, kwargs.get("name"))