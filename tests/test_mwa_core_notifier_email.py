"""
Tests for Email notifier implementation.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime
from email.mime.multipart import MIMEMultipart

from mwa_core.notifier.email import EmailNotifier
from mwa_core.notifier.base import (
    NotificationMessage, 
    NotificationResult, 
    NotificationStatus,
    NotificationType,
    NotificationPriority
)


class TestEmailNotifier:
    """Test Email notifier functionality."""
    
    def test_initialization(self):
        """Test email notifier initialization."""
        config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "test@example.com",
            "password": "password123",
            "sender_email": "test@example.com",
            "sender_name": "Test Sender",
            "recipients": ["recipient@example.com"],
            "use_tls": True,
            "enabled": True
        }
        
        notifier = EmailNotifier(config, "TestEmail")
        
        assert notifier.smtp_server == "smtp.gmail.com"
        assert notifier.smtp_port == 587
        assert notifier.username == "test@example.com"
        assert notifier.password == "password123"
        assert notifier.sender_email == "test@example.com"
        assert notifier.sender_name == "Test Sender"
        assert notifier.recipients == ["recipient@example.com"]
        assert notifier.use_tls is True
        assert notifier.enabled is True
    
    def test_validation_valid_config(self):
        """Test validation with valid configuration."""
        config = {
            "smtp_server": "smtp.gmail.com",
            "username": "test@example.com",
            "password": "password123",
            "sender_email": "test@example.com",
            "recipients": ["recipient@example.com"],
            "enabled": True
        }
        
        notifier = EmailNotifier(config)
        assert notifier.validate_config() is True
    
    def test_validation_missing_smtp_server(self):
        """Test validation with missing SMTP server."""
        config = {
            "username": "test@example.com",
            "password": "password123",
            "sender_email": "test@example.com",
            "recipients": ["recipient@example.com"],
            "enabled": True
        }
        
        notifier = EmailNotifier(config)
        assert notifier.validate_config() is False
    
    def test_validation_missing_credentials(self):
        """Test validation with missing credentials."""
        config = {
            "smtp_server": "smtp.gmail.com",
            "sender_email": "test@example.com",
            "recipients": ["recipient@example.com"],
            "enabled": True
        }
        
        notifier = EmailNotifier(config)
        assert notifier.validate_config() is False
    
    def test_validation_missing_recipients(self):
        """Test validation with missing recipients."""
        config = {
            "smtp_server": "smtp.gmail.com",
            "username": "test@example.com",
            "password": "password123",
            "sender_email": "test@example.com",
            "enabled": True
        }
        
        notifier = EmailNotifier(config)
        assert notifier.validate_config() is False
    
    def test_validation_invalid_email(self):
        """Test validation with invalid email address."""
        config = {
            "smtp_server": "smtp.gmail.com",
            "username": "test@example.com",
            "password": "password123",
            "sender_email": "test@example.com",
            "recipients": ["invalid-email"],
            "enabled": True
        }
        
        notifier = EmailNotifier(config)
        assert notifier.validate_config() is False
    
    def test_channel_type(self):
        """Test getting channel type."""
        config = {
            "smtp_server": "smtp.gmail.com",
            "username": "test@example.com",
            "password": "password123",
            "sender_email": "test@example.com",
            "recipients": ["recipient@example.com"]
        }
        
        notifier = EmailNotifier(config)
        
        from mwa_core.notifier.base import NotificationChannel
        assert notifier.get_channel_type() == NotificationChannel.EMAIL
    
    @pytest.mark.asyncio
    async def test_send_notification_success(self):
        """Test successful email sending."""
        config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "test@example.com",
            "password": "password123",
            "sender_email": "test@example.com",
            "recipients": ["recipient@example.com"],
            "use_tls": True,
            "enabled": True
        }
        
        notifier = EmailNotifier(config)
        
        # Mock SMTP
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_smtp = MagicMock()
            mock_smtp_class.return_value.__enter__.return_value = mock_smtp
            
            message = NotificationMessage(
                type=NotificationType.NEW_LISTINGS,
                title="Test Email",
                content="This is a test email"
            )
            
            result = await notifier.send_notification(message)
            
            assert result.status == NotificationStatus.DELIVERED
            assert result.channel == notifier.get_channel_type()
            assert result.message_id == message.id
            
            # Verify SMTP calls
            mock_smtp.starttls.assert_called_once()
            mock_smtp.login.assert_called_once_with("test@example.com", "password123")
            mock_smtp.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_notification_ssl(self):
        """Test successful email sending with SSL."""
        config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 465,
            "username": "test@example.com",
            "password": "password123",
            "sender_email": "test@example.com",
            "recipients": ["recipient@example.com"],
            "use_ssl": True,
            "enabled": True
        }
        
        notifier = EmailNotifier(config)
        
        # Mock SMTP_SSL
        with patch('smtplib.SMTP_SSL') as mock_smtp_ssl_class:
            mock_smtp_ssl = MagicMock()
            mock_smtp_ssl_class.return_value.__enter__.return_value = mock_smtp_ssl
            
            message = NotificationMessage(
                type=NotificationType.CONTACT_DISCOVERY,
                title="SSL Test",
                content="Testing SSL connection"
            )
            
            result = await notifier.send_notification(message)
            
            assert result.status == NotificationStatus.DELIVERED
            
            # Verify SMTP_SSL calls
            mock_smtp_ssl.login.assert_called_once_with("test@example.com", "password123")
            mock_smtp_ssl.send_message.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_notification_authentication_error(self):
        """Test handling authentication errors."""
        config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "test@example.com",
            "password": "wrong_password",
            "sender_email": "test@example.com",
            "recipients": ["recipient@example.com"],
            "use_tls": True,
            "enabled": True
        }
        
        notifier = EmailNotifier(config)
        
        # Mock authentication failure
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_smtp = MagicMock()
            mock_smtp.login.side_effect = smtplib.SMTPAuthenticationError(535, b'Authentication failed')
            mock_smtp_class.return_value.__enter__.return_value = mock_smtp
            
            message = NotificationMessage(
                type=NotificationType.SYSTEM_ALERT,
                title="Auth Test",
                content="Testing authentication"
            )
            
            result = await notifier.send_notification(message)
            
            assert result.status == NotificationStatus.FAILED
            assert "authentication failed" in result.error_message.lower()
    
    @pytest.mark.asyncio
    async def test_send_notification_smtp_error(self):
        """Test handling SMTP errors."""
        config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "test@example.com",
            "password": "password123",
            "sender_email": "test@example.com",
            "recipients": ["recipient@example.com"],
            "use_tls": True,
            "enabled": True
        }
        
        notifier = EmailNotifier(config)
        
        # Mock SMTP error
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_smtp = MagicMock()
            mock_smtp.send_message.side_effect = smtplib.SMTPException("SMTP error")
            mock_smtp_class.return_value.__enter__.return_value = mock_smtp
            
            message = NotificationMessage(
                type=NotificationType.NEW_LISTINGS,
                title="SMTP Error Test",
                content="Testing SMTP error handling"
            )
            
            result = await notifier.send_notification(message)
            
            assert result.status == NotificationStatus.FAILED
            assert "SMTP error" in result.error_message
    
    def test_build_text_content(self):
        """Test building plain text email content."""
        config = {
            "smtp_server": "smtp.gmail.com",
            "username": "test@example.com",
            "password": "password123",
            "sender_email": "test@example.com",
            "recipients": ["recipient@example.com"]
        }
        
        notifier = EmailNotifier(config)
        
        message = NotificationMessage(
            type=NotificationType.NEW_LISTINGS,
            title="Test Email",
            content="This is test content",
            metadata={"listings_count": 5, "source": "TestSource"},
            created_at=datetime(2023, 12, 1, 10, 30, 0)
        )
        
        text_content = notifier._build_text_content(message)
        
        assert "Test Email" in text_content
        assert "This is test content" in text_content
        assert "Listings Count: 5" in text_content
        assert "Source: TestSource" in text_content
        assert "2023-12-01 10:30:00" in text_content
    
    def test_build_default_html(self):
        """Test building default HTML content."""
        config = {
            "smtp_server": "smtp.gmail.com",
            "username": "test@example.com",
            "password": "password123",
            "sender_email": "test@example.com",
            "recipients": ["recipient@example.com"]
        }
        
        notifier = EmailNotifier(config)
        
        message = NotificationMessage(
            type=NotificationType.NEW_LISTINGS,
            title="HTML Test",
            content="HTML content",
            priority=NotificationPriority.HIGH,
            created_at=datetime(2023, 12, 1, 10, 30, 0),
            id="test-message-123"
        )
        
        html_content = notifier._build_default_html(message)
        
        assert "<!DOCTYPE html>" in html_content
        assert "HTML Test" in html_content
        assert "HTML content" in html_content
        assert "2023-12-01 at 10:30:00" in html_content
        assert "test-message-123" in html_content
        assert 'class="header high"' in html_content  # HIGH priority styling
    
    def test_format_datetime_filter(self):
        """Test datetime formatting filter."""
        config = {"smtp_server": "smtp.gmail.com"}
        notifier = EmailNotifier(config)
        
        test_datetime = datetime(2023, 12, 1, 10, 30, 45)
        formatted = notifier._format_datetime(test_datetime)
        
        assert formatted == "2023-12-01 10:30:45"
    
    def test_format_price_filter(self):
        """Test price formatting filter."""
        config = {"smtp_server": "smtp.gmail.com"}
        notifier = EmailNotifier(config)
        
        # Test with price containing euro symbol
        formatted1 = notifier._format_price("€1,200")
        assert formatted1 == "€1,200"
        
        # Test with plain number
        formatted2 = notifier._format_price("1200")
        assert formatted2 == "€1200"
    
    def test_is_valid_email(self):
        """Test email validation."""
        config = {"smtp_server": "smtp.gmail.com"}
        notifier = EmailNotifier(config)
        
        # Valid emails
        assert notifier._is_valid_email("test@example.com") is True
        assert notifier._is_valid_email("user.name@domain.co.uk") is True
        assert notifier._is_valid_email("test+tag@example.com") is True
        
        # Invalid emails
        assert notifier._is_valid_email("invalid-email") is False
        assert notifier._is_valid_email("@example.com") is False
        assert notifier._is_valid_email("test@") is False
        assert notifier._is_valid_email("test@.com") is False
    
    @pytest.mark.asyncio
    async def test_send_listings_legacy(self):
        """Test legacy send_listings method."""
        config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "test@example.com",
            "password": "password123",
            "sender_email": "test@example.com",
            "recipients": ["recipient@example.com"],
            "use_tls": True,
            "enabled": True
        }
        
        notifier = EmailNotifier(config)
        
        # Mock SMTP
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_smtp = MagicMock()
            mock_smtp_class.return_value.__enter__.return_value = mock_smtp
            
            listings = [
                {"title": "Test Apartment", "price": "€1,000"},
                {"title": "Another Apartment", "price": "€1,200"}
            ]
            
            result = await notifier.send_listings(listings)
            
            assert result.status == NotificationStatus.DELIVERED
            assert result.channel == notifier.get_channel_type()
    
    def test_test_connection_success(self):
        """Test connection testing with success."""
        config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "test@example.com",
            "password": "password123",
            "use_tls": True
        }
        
        notifier = EmailNotifier(config)
        
        # Mock successful connection
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_smtp = MagicMock()
            mock_smtp_class.return_value.__enter__.return_value = mock_smtp
            
            success = notifier.test_connection()
            
            assert success is True
            mock_smtp.starttls.assert_called_once()
            mock_smtp.login.assert_called_once_with("test@example.com", "password123")
    
    def test_test_connection_failure(self):
        """Test connection testing with failure."""
        config = {
            "smtp_server": "smtp.gmail.com",
            "smtp_port": 587,
            "username": "test@example.com",
            "password": "wrong_password",
            "use_tls": True
        }
        
        notifier = EmailNotifier(config)
        
        # Mock connection failure
        with patch('smtplib.SMTP') as mock_smtp_class:
            mock_smtp = MagicMock()
            mock_smtp.login.side_effect = Exception("Connection failed")
            mock_smtp_class.return_value.__enter__.return_value = mock_smtp
            
            success = notifier.test_connection()
            
            assert success is False


@pytest.mark.asyncio
async def test_email_integration():
    """Integration test for Email notifier."""
    config = {
        "smtp_server": "smtp.example.com",
        "smtp_port": 587,
        "username": "test@example.com",
        "password": "test_password",
        "sender_email": "test@example.com",
        "recipients": ["recipient@example.com"],
        "enabled": False  # Disable to avoid actual sending
    }
    
    notifier = EmailNotifier(config)
    
    message = NotificationMessage(
        type=NotificationType.NEW_LISTINGS,
        title="Integration Test",
        content="Testing email notifier integration"
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