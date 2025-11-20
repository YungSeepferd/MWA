"""
Enhanced configuration settings for MWA Core with comprehensive notification support.

Provides a Settings class that loads configuration from JSON files with
environment variable overrides and validation using pydantic.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import List, Literal, Optional, Dict, Any

from pydantic import BaseModel, Field, validator
try:
    from pydantic_settings import BaseSettings
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings
from dotenv import load_dotenv

# Load a .env file if it exists in the project root
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")

logger = logging.getLogger(__name__)


class PersonalProfile(BaseModel):
    """Personal profile configuration for apartment applications."""
    my_full_name: str = Field(..., description="Full name for the email")
    my_profession: str = Field(..., description="Occupation")
    my_employer: str = Field(..., description="Employer for income proof")
    net_household_income_monthly: int = Field(..., gt=0, description="Monthly net household income")
    total_occupants: int = Field(..., gt=0, description="Number of people moving in")
    intro_paragraph: str = Field(..., description="Personal pitch in German")


class ContactDiscoveryConfig(BaseModel):
    """Enhanced configuration for contact discovery features."""
    enabled: bool = Field(True, description="Enable contact discovery feature")
    confidence_threshold: Literal["low", "medium", "high", "uncertain"] = Field("medium", description="Minimum confidence threshold for contacts")
    validation_enabled: bool = Field(True, description="Enable contact validation")
    validation_level: Literal["basic", "standard", "comprehensive"] = Field("standard", description="Validation level for contacts")
    rate_limit_seconds: float = Field(1.0, ge=0.1, description="Minimum seconds between contact discovery attempts")
    max_crawl_depth: int = Field(2, ge=1, le=5, description="Maximum depth for contact page crawling")
    blocked_domains: List[str] = Field(default_factory=list, description="Domains to exclude from contact discovery")
    preferred_contact_methods: List[Literal["email", "phone", "form", "social_media"]] = Field(
        default_factory=lambda: ["email", "phone", "form", "social_media"],
        description="Preferred contact methods in order of priority"
    )
    
    # Advanced features
    smart_crawling: bool = Field(True, description="Enable smart crawling with ML-based link prioritization")
    smtp_verification: bool = Field(False, description="Enable SMTP verification (use with caution)")
    dns_verification: bool = Field(True, description="Enable DNS/MX record verification")
    ocr_extraction: bool = Field(True, description="Enable OCR extraction from images")
    pdf_extraction: bool = Field(True, description="Enable PDF extraction from documents")
    social_media_detection: bool = Field(True, description="Enable social media profile detection")
    respect_robots_txt: bool = Field(True, description="Respect robots.txt files during crawling")
    user_agent: str = Field(
        "MWA-ContactDiscovery/1.0 (Compatible; Real Estate Contact Discovery)",
        description="User agent string for contact discovery requests"
    )
    
    # Performance settings
    max_concurrent_requests: int = Field(5, ge=1, le=20, description="Maximum concurrent requests")
    request_timeout: int = Field(30, ge=5, le=120, description="Request timeout in seconds")
    retry_attempts: int = Field(3, ge=0, le=10, description="Number of retry attempts for failed requests")
    
    # Cultural and language settings
    cultural_context: str = Field("german", description="Cultural context for better contact extraction")
    language_preference: str = Field("de", description="Preferred language for content analysis")
    
    @validator("rate_limit_seconds")
    def validate_rate_limit(cls, v):
        """Ensure rate limit is reasonable."""
        if v < 0.1:
            raise ValueError("Rate limit must be at least 0.1 seconds")
        if v > 60:
            raise ValueError("Rate limit should not exceed 60 seconds")
        return v


class StorageConfig(BaseModel):
    """Enhanced configuration for data storage and retention."""
    contact_retention_days: int = Field(90, ge=7, description="Number of days to retain contact data")
    auto_cleanup_enabled: bool = Field(True, description="Enable automatic cleanup of old contacts")
    backup_enabled: bool = Field(True, description="Enable contact database backup")
    backup_interval_days: int = Field(7, ge=1, description="Backup interval in days")
    database_path: str = Field("data/mwa_core.db", description="Path to SQLite database file")
    deduplication_enabled: bool = Field(True, description="Enable contact deduplication")
    validation_history_retention_days: int = Field(365, ge=30, description="Days to retain validation history")
    database_schema: str = Field("mwa_core", description="Database schema name")


class SearchCriteria(BaseModel):
    """Search criteria for apartment listings."""
    max_price: int = Field(..., gt=0, description="Maximum monthly rent in €")
    min_rooms: int = Field(..., gt=0, description="Minimum number of rooms")
    zip_codes: List[str] = Field(..., min_length=1, description="Desired Munich ZIP codes")


class DiscordNotifierConfig(BaseModel):
    """Discord notifier configuration."""
    enabled: bool = Field(True, description="Enable Discord notifications")
    webhook_url: str = Field(..., description="Discord webhook URL")
    username: str = Field("MWA Bot", description="Bot username for Discord")
    avatar_url: Optional[str] = Field(None, description="Bot avatar URL")
    use_embeds: bool = Field(True, description="Use rich embeds for Discord messages")
    max_retries: int = Field(3, ge=0, le=10, description="Maximum retry attempts")
    retry_delay: float = Field(1.0, ge=0.1, description="Delay between retries in seconds")
    rate_limit_delay: float = Field(0, ge=0, description="Rate limiting delay in seconds")


class EmailNotifierConfig(BaseModel):
    """Email notifier configuration."""
    enabled: bool = Field(True, description="Enable email notifications")
    smtp_server: str = Field(..., description="SMTP server hostname")
    smtp_port: int = Field(587, ge=1, le=65535, description="SMTP server port")
    username: str = Field(..., description="SMTP username")
    password: str = Field(..., description="SMTP password")
    sender_email: str = Field(..., description="Sender email address")
    sender_name: str = Field("MWA Notifications", description="Sender display name")
    recipients: List[str] = Field(..., min_length=1, description="Email recipients")
    cc_recipients: List[str] = Field(default_factory=list, description="CC recipients")
    bcc_recipients: List[str] = Field(default_factory=list, description="BCC recipients")
    use_tls: bool = Field(True, description="Use TLS encryption")
    use_ssl: bool = Field(False, description="Use SSL encryption")
    template_dir: str = Field("mwa_core/notifier/templates", description="Template directory")
    default_template: str = Field("email_default.html", description="Default email template")
    use_html: bool = Field(True, description="Send HTML emails")
    max_retries: int = Field(3, ge=0, le=10, description="Maximum retry attempts")
    retry_delay: float = Field(1.0, ge=0.1, description="Delay between retries in seconds")
    rate_limit_delay: float = Field(1.0, ge=0, description="Rate limiting delay in seconds")


class SlackNotifierConfig(BaseModel):
    """Slack notifier configuration."""
    enabled: bool = Field(True, description="Enable Slack notifications")
    webhook_url: str = Field(..., description="Slack webhook URL")
    channel: Optional[str] = Field(None, description="Slack channel override")
    username: str = Field("MWA Bot", description="Bot username for Slack")
    icon_emoji: str = Field(":robot_face:", description="Bot icon emoji")
    icon_url: Optional[str] = Field(None, description="Bot icon URL")
    use_blocks: bool = Field(True, description="Use Slack blocks for rich formatting")
    max_retries: int = Field(3, ge=0, le=10, description="Maximum retry attempts")
    retry_delay: float = Field(1.0, ge=0.1, description="Delay between retries in seconds")
    rate_limit_delay: float = Field(0, ge=0, description="Rate limiting delay in seconds")


class WebhookNotifierConfig(BaseModel):
    """Generic webhook notifier configuration."""
    enabled: bool = Field(True, description="Enable webhook notifications")
    url: str = Field(..., description="Webhook URL")
    method: str = Field("POST", description="HTTP method")
    headers: Dict[str, str] = Field(default_factory=dict, description="Custom headers")
    auth: Optional[Dict[str, Any]] = Field(None, description="Authentication configuration")
    query_params: Dict[str, str] = Field(default_factory=dict, description="Query parameters")
    content_type: str = Field("application/json", description="Content type")
    timeout: int = Field(30, ge=5, le=300, description="Request timeout")
    follow_redirects: bool = Field(True, description="Follow redirects")
    verify_ssl: bool = Field(True, description="Verify SSL certificates")
    payload_template: Optional[Dict[str, Any]] = Field(None, description="Custom payload template")
    use_raw_content: bool = Field(False, description="Send raw content instead of JSON")
    custom_payload_keys: Dict[str, Any] = Field(default_factory=dict, description="Custom payload keys")
    success_status_codes: List[int] = Field(default_factory=lambda: [200, 201, 202, 204], description="Success status codes")
    response_key_path: Optional[str] = Field(None, description="Response validation key path")
    max_retries: int = Field(3, ge=0, le=10, description="Maximum retry attempts")
    retry_delay: float = Field(1.0, ge=0.1, description="Delay between retries in seconds")
    rate_limit_delay: float = Field(0, ge=0, description="Rate limiting delay in seconds")


class NotificationConfig(BaseModel):
    """Enhanced notification configuration with legacy support."""
    # Legacy configuration (backward compatibility)
    provider: Literal["discord", "telegram", "email"] = Field(
        "discord",
        description="Notification provider – discord (webhook) is preferred",
    )
    discord_webhook_url: Optional[str] = Field(
        None,
        description="Discord webhook URL (required when provider == 'discord')",
    )
    telegram_bot_token: Optional[str] = Field(
        None, description="Telegram Bot token (required when provider == 'telegram')"
    )
    telegram_chat_id: Optional[str] = Field(
        None, description="Telegram chat ID to send alerts to"
    )
    email_smtp_server: Optional[str] = Field(
        None, description="SMTP server for email notifications"
    )
    email_smtp_port: Optional[int] = Field(
        None, description="SMTP port for email notifications"
    )
    email_username: Optional[str] = Field(
        None, description="Email username for authentication"
    )
    email_password: Optional[str] = Field(
        None, description="Email password for authentication"
    )
    email_recipients: List[str] = Field(
        default_factory=list, description="Email recipients for notifications"
    )
    contact_discovery_alerts: bool = Field(
        True, description="Enable alerts for new high-confidence contacts"
    )
    validation_failure_alerts: bool = Field(
        True, description="Enable alerts for contact validation failures"
    )
    
    # New notifier configurations
    discord: Optional[DiscordNotifierConfig] = Field(None, description="Discord notifier configuration")
    email: Optional[EmailNotifierConfig] = Field(None, description="Email notifier configuration")
    slack: Optional[SlackNotifierConfig] = Field(None, description="Slack notifier configuration")
    webhook: Optional[WebhookNotifierConfig] = Field(None, description="Generic webhook notifier configuration")
    
    # Global notification settings
    rate_limiting_enabled: bool = Field(True, description="Enable rate limiting")
    max_notifications_per_minute: int = Field(10, ge=1, le=100, description="Maximum notifications per minute")
    deduplication_enabled: bool = Field(True, description="Enable notification deduplication")
    deduplication_window_seconds: int = Field(300, ge=60, le=3600, description="Deduplication time window")
    retry_failed_notifications: bool = Field(True, description="Automatically retry failed notifications")
    max_retry_age_hours: int = Field(24, ge=1, le=168, description="Maximum age of failed notifications to retry")
    
    @validator("discord_webhook_url")
    def require_discord_url(cls, v, values):
        if values and values.get("provider") == "discord" and not v:
            raise ValueError("discord_webhook_url is required when provider == 'discord'")
        return v
    
    @validator("telegram_bot_token", "telegram_chat_id")
    def require_telegram_fields(cls, v, values):
        if values and values.get("provider") == "telegram":
            if not v:
                raise ValueError(f"Field is required for telegram notifications")
        return v


class ScraperConfig(BaseModel):
    """Enhanced scraper configuration."""
    enabled_providers: List[Literal["immoscout", "wg_gesucht"]] = Field(
        default_factory=lambda: ["immoscout", "wg_gesucht"],
        description="Ordered list of scraper providers to execute",
    )
    request_delay_seconds: float = Field(1.0, ge=0.1, description="Delay between requests")
    max_retries: int = Field(3, ge=0, description="Maximum number of retries for failed requests")
    timeout_seconds: int = Field(30, ge=5, description="Request timeout in seconds")
    user_agent: str = Field(
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        description="User agent string for requests"
    )
    contact_discovery_enabled: bool = Field(
        True, description="Enable contact discovery during scraping"
    )
    contact_discovery_timeout: int = Field(
        30, ge=10, le=120, description="Timeout for contact discovery operations"
    )


class SchedulerConfig(BaseModel):
    """Configuration for the job scheduler."""
    enabled: bool = Field(True, description="Enable job scheduling")
    timezone: str = Field("Europe/Berlin", description="Scheduler timezone")
    persistent: bool = Field(True, description="Enable persistent job storage")
    job_store_path: str = Field("data/scheduler.db", description="Path to job store database")
    max_workers: int = Field(5, ge=1, le=20, description="Maximum number of worker threads")
    job_defaults: Dict[str, Any] = Field(
        default_factory=lambda: {
            'coalesce': True,
            'max_instances': 1,
            'misfire_grace_time': 300
        },
        description="Default job configuration"
    )


class NotifiersConfig(BaseModel):
    """Configuration for multiple notifiers."""
    discord: Optional[DiscordNotifierConfig] = Field(None, description="Discord notifier")
    email: Optional[EmailNotifierConfig] = Field(None, description="Email notifier")
    slack: Optional[SlackNotifierConfig] = Field(None, description="Slack notifier")
    webhook: Optional[WebhookNotifierConfig] = Field(None, description="Generic webhook notifier")
    
    def get_enabled_notifiers(self) -> Dict[str, Dict[str, Any]]:
        """Get all enabled notifiers as a dictionary."""
        notifiers = {}
        
        if self.discord and self.discord.enabled:
            notifiers["discord"] = self.discord.dict()
        
        if self.email and self.email.enabled:
            notifiers["email"] = self.email.dict()
        
        if self.slack and self.slack.enabled:
            notifiers["slack"] = self.slack.dict()
        
        if self.webhook and self.webhook.enabled:
            notifiers["webhook"] = self.webhook.dict()
        
        return notifiers


class SecurityConfig(BaseModel):
    """Security configuration for authentication and authorization."""
    secret_key: Optional[str] = Field(None, description="JWT secret key")
    access_token_expire_minutes: int = Field(30, ge=1, le=1440, description="Access token expiration in minutes")
    refresh_token_expire_days: int = Field(7, ge=1, le=30, description="Refresh token expiration in days")
    password_min_length: int = Field(8, ge=4, le=128, description="Minimum password length")
    max_login_attempts: int = Field(5, ge=1, le=20, description="Maximum login attempts before lockout")
    lockout_duration_minutes: int = Field(15, ge=1, le=1440, description="Account lockout duration in minutes")
    enable_csrf_protection: bool = Field(True, description="Enable CSRF protection")
    session_timeout_minutes: int = Field(60, ge=5, le=1440, description="Session timeout in minutes")


class Settings(BaseSettings):
    """
    Enhanced top-level settings object for MWA Core with comprehensive notification support.
    
    Reads configuration from JSON files and validates the structure.
    Environment variables can override any setting.
    """
    
    personal_profile: PersonalProfile | None = Field(
        default=None,
        description="Personal profile configuration"
    )
    search_criteria: SearchCriteria | None = Field(
        default=None,
        description="Search criteria configuration"
    )
    notification: NotificationConfig | None = Field(
        default=None,
        description="Notification configuration (legacy)"
    )
    notifiers: NotifiersConfig | None = Field(
        default=None,
        description="Multiple notifier configurations"
    )
    contact_discovery: ContactDiscoveryConfig = Field(
        default_factory=ContactDiscoveryConfig,
        description="Contact discovery configuration"
    )
    storage: StorageConfig = Field(
        default_factory=StorageConfig,
        description="Storage and retention configuration"
    )
    scraper: ScraperConfig = Field(
        default_factory=ScraperConfig,
        description="Scraper configuration"
    )
    scheduler: SchedulerConfig = Field(
        default_factory=SchedulerConfig,
        description="Scheduler configuration"
    )
    security: SecurityConfig = Field(
        default_factory=SecurityConfig,
        description="Security configuration"
    )
    
    # Path to the JSON configuration file
    config_path: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[2] / "config.json",
        description="Path to the user configuration file",
    )
    
    # Logging configuration
    log_level: str = Field("INFO", description="Logging level")
    log_format: str = Field(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        description="Log format string"
    )
    
    # Performance monitoring
    performance_tracking: bool = Field(True, description="Enable performance tracking")
    metrics_retention_days: int = Field(30, ge=7, description="Days to retain performance metrics")
    
    # Notification system settings
    notification_system_enabled: bool = Field(True, description="Enable the notification system")
    notification_history_retention_days: int = Field(30, ge=7, description="Days to retain notification history")
    max_notification_queue_size: int = Field(1000, ge=100, description="Maximum notification queue size")

    class Config:
        env_prefix = "MWA_"  # Environment variables prefixed with MWA_
        case_sensitive = False
        extra = "allow"  # Allow extra fields for backward compatibility

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "Settings":
        """
        Load settings from a JSON file.
        
        If path is None, the default config_path attribute is used.
        config.example.json is used as a fallback when the target file does not exist.
        """
        if path is None:
            path = cls().config_path

        if not path.exists():
            # Fallback to the example file shipped with the repository
            example_path = Path(__file__).resolve().parents[2] / "config.example.json"
            if not example_path.exists():
                raise FileNotFoundError(
                    f"Neither {path} nor {example_path} could be found."
                )
            logger.warning(f"Config file {path} not found, using example config {example_path}")
            path = example_path

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file {path}: {e}")
            raise ValueError(f"Invalid JSON in config file {path}: {e}")
        except Exception as e:
            logger.error(f"Error reading config file {path}: {e}")
            raise

        # Parse and validate the configuration
        try:
            settings = cls.parse_obj(data)
            # Update the config_path to the actual path used
            settings.config_path = path
            return settings
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            raise ValueError(f"Configuration validation failed: {e}")

    def save(self, path: Optional[Path] = None) -> None:
        """
        Save current settings to a JSON file.
        
        Args:
            path: Path to save the configuration. If None, uses the current config_path.
        """
        if path is None:
            path = self.config_path
            
        # Convert to dict and remove internal fields
        data = self.dict(exclude={"config_path"})
        
        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            logger.info(f"Configuration saved to {path}")
        except Exception as e:
            logger.error(f"Error saving config file {path}: {e}")
            raise

    def get_provider_config(self, provider_name: str) -> Dict[str, Any]:
        """
        Get provider-specific configuration.
        
        Args:
            provider_name: Name of the provider (e.g., 'immoscout', 'wg_gesucht')
            
        Returns:
            Dictionary with provider-specific configuration
        """
        # This method can be extended to support provider-specific configs
        return {
            "headless": True,
            "timeout": self.scraper.timeout_seconds,
            "user_agent": self.scraper.user_agent,
            "request_delay": self.scraper.request_delay_seconds,
            "max_retries": self.scraper.max_retries,
            "contact_discovery_enabled": self.scraper.contact_discovery_enabled,
            "contact_discovery_timeout": self.scraper.contact_discovery_timeout,
        }

    def get_contact_discovery_config(self) -> Dict[str, Any]:
        """
        Get contact discovery configuration.
        
        Returns:
            Dictionary with contact discovery configuration
        """
        return {
            "enabled": self.contact_discovery.enabled,
            "confidence_threshold": self.contact_discovery.confidence_threshold,
            "validation_enabled": self.contact_discovery.validation_enabled,
            "validation_level": self.contact_discovery.validation_level,
            "rate_limit_seconds": self.contact_discovery.rate_limit_seconds,
            "max_crawl_depth": self.contact_discovery.max_crawl_depth,
            "blocked_domains": self.contact_discovery.blocked_domains,
            "preferred_contact_methods": self.contact_discovery.preferred_contact_methods,
            "smart_crawling": self.contact_discovery.smart_crawling,
            "smtp_verification": self.contact_discovery.smtp_verification,
            "dns_verification": self.contact_discovery.dns_verification,
            "ocr_extraction": self.contact_discovery.ocr_extraction,
            "pdf_extraction": self.contact_discovery.pdf_extraction,
            "social_media_detection": self.contact_discovery.social_media_detection,
            "respect_robots_txt": self.contact_discovery.respect_robots_txt,
            "user_agent": self.contact_discovery.user_agent,
            "max_concurrent_requests": self.contact_discovery.max_concurrent_requests,
            "request_timeout": self.contact_discovery.request_timeout,
            "retry_attempts": self.contact_discovery.retry_attempts,
            "cultural_context": self.contact_discovery.cultural_context,
            "language_preference": self.contact_discovery.language_preference,
        }

    def get_notification_config(self) -> Dict[str, Any]:
        """
        Get notification system configuration.
        
        Returns:
            Dictionary with notification configuration
        """
        config = {
            "notification_system_enabled": self.notification_system_enabled,
            "notification_history_retention_days": self.notification_history_retention_days,
            "max_notification_queue_size": self.max_notification_queue_size,
        }
        
        # Add legacy notification config if available
        if self.notification:
            config["notification"] = self.notification.dict()
        
        # Add new notifier configurations if available
        if self.notifiers:
            config["notifiers"] = self.notifiers.get_enabled_notifiers()
        
        return config

    def get_notifier_config(self, notifier_type: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration for a specific notifier type.
        
        Args:
            notifier_type: Type of notifier ('discord', 'email', 'slack', 'webhook')
            
        Returns:
            Notifier configuration or None if not configured
        """
        if not self.notifiers:
            return None
        
        notifier_map = {
            'discord': self.notifiers.discord,
            'email': self.notifiers.email,
            'slack': self.notifiers.slack,
            'webhook': self.notifiers.webhook,
        }
        
        notifier_config = notifier_map.get(notifier_type)
        if notifier_config and notifier_config.enabled:
            return notifier_config.dict()
        
        return None

    def validate_configuration(self) -> List[str]:
        """
        Validate configuration settings and return list of issues.
        
        Returns:
            List of validation issues (empty if valid)
        """
        issues = []
        
        # Validate contact discovery settings
        if self.contact_discovery.enabled:
            if self.contact_discovery.smtp_verification and not self.contact_discovery.dns_verification:
                issues.append("SMTP verification enabled without DNS verification - this may cause issues")
            
            if self.contact_discovery.max_crawl_depth > 3 and not self.contact_discovery.smart_crawling:
                issues.append("High crawl depth without smart crawling may be inefficient")
            
            if self.contact_discovery.rate_limit_seconds < 0.5:
                issues.append("Very low rate limit may cause issues with target websites")
        
        # Validate storage settings
        if self.storage.contact_retention_days < 30:
            issues.append("Short contact retention period may lose valuable data")
        
        # Validate notification settings
        if self.notification and self.notification.contact_discovery_alerts:
            if self.notification.provider == "discord" and not self.notification.discord_webhook_url:
                issues.append("Contact discovery alerts enabled but Discord webhook not configured")
        
        # Validate new notifier configurations
        if self.notifiers:
            if self.notifiers.discord and self.notifiers.discord.enabled:
                if not self.notifiers.discord.webhook_url:
                    issues.append("Discord notifier enabled but webhook URL not configured")
            
            if self.notifiers.email and self.notifiers.email.enabled:
                email_config = self.notifiers.email
                if not email_config.smtp_server or not email_config.username or not email_config.password:
                    issues.append("Email notifier enabled but SMTP credentials not configured")
                if not email_config.recipients:
                    issues.append("Email notifier enabled but no recipients configured")
            
            if self.notifiers.slack and self.notifiers.slack.enabled:
                if not self.notifiers.slack.webhook_url:
                    issues.append("Slack notifier enabled but webhook URL not configured")
            
            if self.notifiers.webhook and self.notifiers.webhook.enabled:
                if not self.notifiers.webhook.url:
                    issues.append("Webhook notifier enabled but URL not configured")
        
        return issues

    def generate_example_config(self) -> Dict[str, Any]:
        """Generate example configuration with all new features."""
        return {
            "personal_profile": {
                "my_full_name": "Max Mustermann",
                "my_profession": "Software Engineer",
                "my_employer": "Tech Company GmbH",
                "net_household_income_monthly": 5000,
                "total_occupants": 2,
                "intro_paragraph": "Ich bin ein verantwortungsvoller Mieter mit stabilem Einkommen..."
            },
            "search_criteria": {
                "max_price": 1500,
                "min_rooms": 2,
                "zip_codes": ["80331", "80333", "80335", "80336", "80337", "80469", "80538", "80539", "80636", "80637", "80638", "80639", "80796", "80797", "80798", "80799", "80801", "80802", "80803", "80804", "80805", "80807", "80809", "80933", "80935", "80937", "80939", "80992", "80993", "80995", "80997", "80999"]
            },
            "notification": {
                "provider": "discord",
                "discord_webhook_url": "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL",
                "contact_discovery_alerts": True,
                "validation_failure_alerts": True
            },
            "notifiers": {
                "discord": {
                    "enabled": True,
                    "webhook_url": "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL",
                    "username": "MWA Bot",
                    "use_embeds": True,
                    "max_retries": 3,
                    "retry_delay": 1.0
                },
                "email": {
                    "enabled": True,
                    "smtp_server": "smtp.gmail.com",
                    "smtp_port": 587,
                    "username": "your-email@gmail.com",
                    "password": "your-app-password",
                    "sender_email": "your-email@gmail.com",
                    "sender_name": "MWA Notifications",
                    "recipients": ["recipient1@example.com", "recipient2@example.com"],
                    "use_tls": True,
                    "use_html": True,
                    "max_retries": 3,
                    "retry_delay": 1.0
                },
                "slack": {
                    "enabled": False,
                    "webhook_url": "https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK",
                    "username": "MWA Bot",
                    "use_blocks": True,
                    "max_retries": 3,
                    "retry_delay": 1.0
                },
                "webhook": {
                    "enabled": False,
                    "url": "https://your-webhook-endpoint.com/notify",
                    "method": "POST",
                    "headers": {"Authorization": "Bearer YOUR_TOKEN"},
                    "max_retries": 3,
                    "retry_delay": 1.0
                }
            },
            "contact_discovery": {
                "enabled": True,
                "confidence_threshold": "medium",
                "validation_enabled": True,
                "validation_level": "standard",
                "rate_limit_seconds": 1.0,
                "max_crawl_depth": 2,
                "blocked_domains": ["spam.com", "test.com"],
                "preferred_contact_methods": ["email", "phone", "form", "social_media"],
                "smart_crawling": True,
                "smtp_verification": False,
                "dns_verification": True,
                "ocr_extraction": True,
                "pdf_extraction": True,
                "social_media_detection": True,
                "respect_robots_txt": True,
                "user_agent": "MWA-ContactDiscovery/1.0 (Compatible; Real Estate Contact Discovery)",
                "max_concurrent_requests": 5,
                "request_timeout": 30,
                "retry_attempts": 3,
                "cultural_context": "german",
                "language_preference": "de"
            },
            "storage": {
                "contact_retention_days": 90,
                "auto_cleanup_enabled": True,
                "backup_enabled": True,
                "backup_interval_days": 7,
                "database_path": "data/mwa_core.db",
                "deduplication_enabled": True,
                "validation_history_retention_days": 365
            },
            "scraper": {
                "enabled_providers": ["immoscout", "wg_gesucht"],
                "request_delay_seconds": 1.0,
                "max_retries": 3,
                "timeout_seconds": 30,
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "contact_discovery_enabled": True,
                "contact_discovery_timeout": 30
            },
            "scheduler": {
                "enabled": True,
                "timezone": "Europe/Berlin",
                "persistent": True,
                "job_store_path": "data/scheduler.db",
                "max_workers": 5,
                "job_defaults": {
                    "coalesce": True,
                    "max_instances": 1,
                    "misfire_grace_time": 300
                }
            },
            "notification_system_enabled": True,
            "notification_history_retention_days": 30,
            "max_notification_queue_size": 1000,
            "log_level": "INFO",
            "performance_tracking": True,
            "metrics_retention_days": 30
        }


# Global settings instance with lazy loading
_settings_instance = None

def get_settings() -> Settings:
    """Get or create the global settings instance."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings.load()
    return _settings_instance


def reload_settings() -> Settings:
    """Reload settings from the configuration file."""
    global _settings_instance
    _settings_instance = Settings.load()
    return _settings_instance


# Configuration validation and migration functions
def validate_configuration(settings: Settings) -> List[str]:
    """
    Validate configuration settings and return list of issues.
    
    Args:
        settings: Settings object to validate
        
    Returns:
        List of validation issues (empty if valid)
    """
    return settings.validate_configuration()


def migrate_configuration(old_config: Dict[str, Any]) -> Settings:
    """
    Migrate old configuration format to new format.
    
    Args:
        old_config: Old configuration dictionary
        
    Returns:
        Migrated Settings object
    """
    # This is a placeholder for configuration migration logic
    # In a real implementation, this would handle version-to-version migrations
    
    logger.info("Migrating configuration to latest format")
    
    # Create new settings from old config
    try:
        settings = Settings.parse_obj(old_config)
        logger.info("Configuration migration completed successfully")
        return settings
    except Exception as e:
        logger.error(f"Configuration migration failed: {e}")
        # Return default settings if migration fails
        return Settings()


# Example configuration generation
def generate_example_config() -> Dict[str, Any]:
    """Generate example configuration with all new features."""
    return Settings.generate_example_config()