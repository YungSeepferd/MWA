"""
Notifier factory for creating notifier instances based on configuration.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Type

from .base import BaseNotifier, NotificationChannel
from .discord import DiscordNotifier
from .email import EmailNotifier
from .slack import SlackNotifier
from .webhook import WebhookNotifier

logger = logging.getLogger(__name__)


class NotifierFactory:
    """Factory class for creating notifier instances."""
    
    # Registry of available notifiers
    _notifiers: Dict[NotificationChannel, Type[BaseNotifier]] = {
        NotificationChannel.DISCORD: DiscordNotifier,
        NotificationChannel.EMAIL: EmailNotifier,
        NotificationChannel.SLACK: SlackNotifier,
        NotificationChannel.WEBHOOK: WebhookNotifier,
    }
    
    @classmethod
    def register_notifier(cls, channel: NotificationChannel, notifier_class: Type[BaseNotifier]):
        """
        Register a new notifier type.
        
        Args:
            channel: The notification channel this notifier handles
            notifier_class: The notifier class to register
        """
        cls._notifiers[channel] = notifier_class
        logger.info(f"Registered notifier {notifier_class.__name__} for channel {channel.value}")
    
    @classmethod
    def create_notifier(cls, channel: NotificationChannel, config: Dict[str, Any], name: str = None) -> BaseNotifier:
        """
        Create a notifier instance for the specified channel.
        
        Args:
            channel: The notification channel
            config: Configuration dictionary for the notifier
            name: Optional name for the notifier instance
            
        Returns:
            Configured notifier instance
            
        Raises:
            ValueError: If the channel is not supported
            ConfigurationError: If the configuration is invalid
        """
        if channel not in cls._notifiers:
            raise ValueError(f"Unsupported notification channel: {channel.value}")
        
        notifier_class = cls._notifiers[channel]
        
        try:
            notifier = notifier_class(config, name)
            
            # Validate configuration
            if not notifier.validate_config():
                raise ConfigurationError(f"Invalid configuration for {channel.value} notifier")
            
            logger.info(f"Created {notifier_class.__name__} instance named '{name or notifier.name}'")
            return notifier
            
        except Exception as e:
            logger.error(f"Failed to create {channel.value} notifier: {e}")
            raise ConfigurationError(f"Failed to create {channel.value} notifier: {e}")
    
    @classmethod
    def create_notifiers_from_config(cls, config: Dict[str, Any]) -> List[BaseNotifier]:
        """
        Create multiple notifiers from a configuration dictionary.
        
        Args:
            config: Configuration dictionary containing notifier settings
            
        Returns:
            List of configured notifier instances
        """
        notifiers = []
        
        # Check for legacy configuration format
        if "notification" in config:
            legacy_notifiers = cls._create_legacy_notifiers(config["notification"])
            notifiers.extend(legacy_notifiers)
        
        # Check for new notifier configuration format
        if "notifiers" in config:
            new_notifiers = cls._create_new_notifiers(config["notifiers"])
            notifiers.extend(new_notifiers)
        
        # Check for individual channel configurations
        for channel in NotificationChannel:
            channel_config = config.get(f"{channel.value}_notifier")
            if channel_config:
                try:
                    notifier = cls.create_notifier(channel, channel_config)
                    notifiers.append(notifier)
                except Exception as e:
                    logger.warning(f"Failed to create {channel.value} notifier: {e}")
        
        if not notifiers:
            logger.warning("No notifiers configured")
        
        return notifiers
    
    @classmethod
    def _create_legacy_notifiers(cls, notification_config: Dict[str, Any]) -> List[BaseNotifier]:
        """Create notifiers from legacy configuration format."""
        notifiers = []
        
        provider = notification_config.get("provider")
        if not provider:
            return notifiers
        
        # Map legacy provider names to channels
        channel_map = {
            "discord": NotificationChannel.DISCORD,
            "telegram": NotificationChannel.TELEGRAM,
            "email": NotificationChannel.EMAIL,
        }
        
        channel = channel_map.get(provider)
        if channel and channel in cls._notifiers:
            try:
                # Convert legacy config to new format
                config = cls._convert_legacy_config(notification_config, provider)
                notifier = cls.create_notifier(channel, config)
                notifiers.append(notifier)
            except Exception as e:
                logger.warning(f"Failed to create legacy {provider} notifier: {e}")
        
        return notifiers
    
    @classmethod
    def _create_new_notifiers(cls, notifiers_config: Dict[str, Any]) -> List[BaseNotifier]:
        """Create notifiers from new configuration format."""
        notifiers = []
        
        for notifier_name, notifier_config in notifiers_config.items():
            if not isinstance(notifier_config, dict):
                logger.warning(f"Invalid notifier configuration for {notifier_name}")
                continue
            
            channel_name = notifier_config.get("channel")
            if not channel_name:
                logger.warning(f"No channel specified for notifier {notifier_name}")
                continue
            
            try:
                channel = NotificationChannel(channel_name)
                notifier = cls.create_notifier(channel, notifier_config, notifier_name)
                notifiers.append(notifier)
            except ValueError:
                logger.warning(f"Unknown notification channel: {channel_name}")
            except Exception as e:
                logger.warning(f"Failed to create notifier {notifier_name}: {e}")
        
        return notifiers
    
    @classmethod
    def _convert_legacy_config(cls, legacy_config: Dict[str, Any], provider: str) -> Dict[str, Any]:
        """Convert legacy configuration to new format."""
        config = {
            "enabled": True,
            "max_retries": 3,
            "retry_delay": 1.0,
            "timeout": 30,
            "rate_limit_delay": 0,
        }
        
        if provider == "discord":
            config["webhook_url"] = legacy_config.get("discord_webhook_url")
        elif provider == "telegram":
            config["bot_token"] = legacy_config.get("telegram_bot_token")
            config["chat_id"] = legacy_config.get("telegram_chat_id")
        elif provider == "email":
            config["smtp_server"] = legacy_config.get("email_smtp_server")
            config["smtp_port"] = legacy_config.get("email_smtp_port")
            config["username"] = legacy_config.get("email_username")
            config["password"] = legacy_config.get("email_password")
            config["recipients"] = legacy_config.get("email_recipients", [])
        
        return config
    
    @classmethod
    def get_available_channels(cls) -> List[NotificationChannel]:
        """
        Get list of available notification channels.
        
        Returns:
            List of supported NotificationChannel values
        """
        return list(cls._notifiers.keys())
    
    @classmethod
    def get_channel_notifiers(cls) -> Dict[NotificationChannel, Type[BaseNotifier]]:
        """
        Get mapping of channels to their notifier classes.
        
        Returns:
            Dictionary mapping NotificationChannel to notifier class
        """
        return cls._notifiers.copy()


class ConfigurationError(Exception):
    """Raised when notifier configuration is invalid."""
    pass


# Convenience functions
def create_discord_notifier(webhook_url: str, **kwargs) -> DiscordNotifier:
    """Create a Discord notifier with the given webhook URL."""
    config = {
        "webhook_url": webhook_url,
        "enabled": kwargs.get("enabled", True),
        "max_retries": kwargs.get("max_retries", 3),
        "retry_delay": kwargs.get("retry_delay", 1.0),
        "timeout": kwargs.get("timeout", 30),
        "rate_limit_delay": kwargs.get("rate_limit_delay", 0),
    }
    return NotifierFactory.create_notifier(NotificationChannel.DISCORD, config)


def create_email_notifier(smtp_server: str, username: str, password: str, 
                         recipients: List[str], **kwargs) -> EmailNotifier:
    """Create an email notifier with the given SMTP settings."""
    config = {
        "smtp_server": smtp_server,
        "smtp_port": kwargs.get("smtp_port", 587),
        "username": username,
        "password": password,
        "recipients": recipients,
        "enabled": kwargs.get("enabled", True),
        "max_retries": kwargs.get("max_retries", 3),
        "retry_delay": kwargs.get("retry_delay", 1.0),
        "timeout": kwargs.get("timeout", 30),
        "rate_limit_delay": kwargs.get("rate_limit_delay", 1.0),
    }
    return NotifierFactory.create_notifier(NotificationChannel.EMAIL, config)


def create_slack_notifier(webhook_url: str, **kwargs) -> SlackNotifier:
    """Create a Slack notifier with the given webhook URL."""
    config = {
        "webhook_url": webhook_url,
        "enabled": kwargs.get("enabled", True),
        "max_retries": kwargs.get("max_retries", 3),
        "retry_delay": kwargs.get("retry_delay", 1.0),
        "timeout": kwargs.get("timeout", 30),
        "rate_limit_delay": kwargs.get("rate_limit_delay", 0),
    }
    return NotifierFactory.create_notifier(NotificationChannel.SLACK, config)


def create_webhook_notifier(url: str, **kwargs) -> WebhookNotifier:
    """Create a generic webhook notifier with the given URL."""
    config = {
        "url": url,
        "method": kwargs.get("method", "POST"),
        "headers": kwargs.get("headers", {}),
        "enabled": kwargs.get("enabled", True),
        "max_retries": kwargs.get("max_retries", 3),
        "retry_delay": kwargs.get("retry_delay", 1.0),
        "timeout": kwargs.get("timeout", 30),
        "rate_limit_delay": kwargs.get("rate_limit_delay", 0),
    }
    return NotifierFactory.create_notifier(NotificationChannel.WEBHOOK, config)