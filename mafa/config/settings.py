"""
Configuration module for MAFA.

Provides a ``Settings`` class that loads ``config.json`` (or ``config.example.json`` as a fallback)
and validates the required fields using **pydantic**. Environment variables can override any
setting when a ``.env`` file is present (loaded automatically via ``python-dotenv``).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, validator
try:
    from pydantic_settings import BaseSettings
except ImportError:
    # Fallback for older pydantic versions
    from pydantic import BaseSettings
from dotenv import load_dotenv

# Load a .env file if it exists in the project root
load_dotenv(dotenv_path=Path(__file__).resolve().parents[2] / ".env")


class PersonalProfile(BaseModel):
    my_full_name: str = Field(..., description="Full name for the email")
    my_profession: str = Field(..., description="Occupation")
    my_employer: str = Field(..., description="Employer for income proof")
    net_household_income_monthly: int = Field(..., gt=0, description="Monthly net household income")
    total_occupants: int = Field(..., gt=0, description="Number of people moving in")
    intro_paragraph: str = Field(..., description="Personal pitch in German")


class ContactDiscoveryConfig(BaseModel):
    enabled: bool = Field(True, description="Enable contact discovery feature")
    confidence_threshold: Literal["low", "medium", "high"] = Field("medium", description="Minimum confidence threshold for contacts")
    validation_enabled: bool = Field(True, description="Enable contact validation")
    rate_limit_seconds: float = Field(1.0, ge=0.1, description="Minimum seconds between contact discovery attempts")
    max_crawl_depth: int = Field(2, ge=1, le=5, description="Maximum depth for contact page crawling")
    blocked_domains: List[str] = Field(default_factory=list, description="Domains to exclude from contact discovery")
    preferred_contact_methods: List[Literal["email", "phone", "form"]] = Field(
        default_factory=lambda: ["email", "phone", "form"],
        description="Preferred contact methods in order of priority"
    )


class StorageConfig(BaseModel):
    contact_retention_days: int = Field(90, ge=7, description="Number of days to retain contact data")
    auto_cleanup_enabled: bool = Field(True, description="Enable automatic cleanup of old contacts")
    backup_enabled: bool = Field(True, description="Enable contact database backup")


class SearchCriteria(BaseModel):
    max_price: int = Field(..., gt=0, description="Maximum monthly rent in €")
    min_rooms: int = Field(..., gt=0, description="Minimum number of rooms")
    zip_codes: List[str] = Field(..., min_items=1, description="Desired Munich ZIP codes")


class Notification(BaseModel):
    provider: Literal["discord", "telegram"] = Field(
        "discord",
        description="Notification provider – discord (webhook) is preferred; telegram is deprecated",
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

    @validator("discord_webhook_url")
    def require_discord_url(cls, v, values):
        if values and values.get("provider") == "discord" and not v:
            raise ValueError("discord_webhook_url is required when provider == 'discord'")
        return v

    @validator("telegram_bot_token")
    def require_telegram_token(cls, v, values):
        if values and values.get("provider") == "telegram" and not v:
            raise ValueError("telegram_bot_token is required for telegram notifications")
        return v

    @validator("telegram_chat_id")
    def require_telegram_chat_id(cls, v, values):
        if values and values.get("provider") == "telegram" and not v:
            raise ValueError("telegram_chat_id is required for telegram notifications")
        return v


class Settings(BaseSettings):
    """
    Top‑level settings object. It reads ``config.json`` (or ``config.example.json``) and
    validates the structure. All fields are exposed as attributes for easy import.
    """

    personal_profile: PersonalProfile
    search_criteria: SearchCriteria
    notification: Notification
    contact_discovery: ContactDiscoveryConfig = Field(
        default_factory=ContactDiscoveryConfig,
        description="Contact discovery configuration"
    )
    storage: StorageConfig = Field(
        default_factory=StorageConfig,
        description="Storage and retention configuration"
    )

    # Ordered list of scraper providers to execute.
    scrapers: List[Literal["immoscout", "wg_gesucht"]] = Field(
        default_factory=lambda: ["immoscout", "wg_gesucht"],
        description="Ordered list of scraper providers to execute",
    )

    # Path to the JSON configuration file – can be overridden via env var CONFIG_PATH
    config_path: Path = Field(
        default_factory=lambda: Path(__file__).resolve().parents[2] / "config.json",
        description="Path to the user configuration file",
    )

    class Config:
        env_prefix = ""  # No prefix – plain environment variable names are used
        case_sensitive = False

    @classmethod
    def load(cls, path: Optional[Path] = None) -> "Settings":
        """
        Load settings from a JSON file. If ``path`` is ``None`` the default
        ``config_path`` attribute is used. ``config.example.json`` is used as a fallback
        when the target file does not exist.
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
            path = example_path

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        # ``parse_obj`` validates the dict against the pydantic model hierarchy
        return cls.parse_obj(data)


# Export a singleton that can be imported throughout the codebase
# Use lazy loading to avoid validation errors at import time
_settings_instance = None

def get_settings() -> Settings:
    """Get or create the global settings instance."""
    global _settings_instance
    if _settings_instance is None:
        _settings_instance = Settings.load()
    return _settings_instance

# For backward compatibility, but lazy loading (avoid immediate validation)
# Use get_settings() function instead of direct import