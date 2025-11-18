"""
Configuration module for MAFA.

Provides a ``Settings`` class that loads ``config.json`` (or ``config.example.json`` as a fallback)
and validates the required fields using **pydantic**. Environment variables can override any
setting when a ``.env`` file is present (loaded automatically via ``python-dotenv``).
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import List, Literal, Optional

from pydantic import BaseModel, BaseSettings, Field, validator
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


class SearchCriteria(BaseModel):
    max_price: int = Field(..., gt=0, description="Maximum monthly rent in €")
    min_rooms: int = Field(..., gt=0, description="Minimum number of rooms")
    zip_codes: List[str] = Field(..., min_items=1, description="Desired Munich ZIP codes")


class Notification(BaseModel):
    provider: Literal["telegram"] = Field(
        "telegram", description="Notification provider – currently only telegram is supported"
    )
    telegram_bot_token: Optional[str] = Field(
        None, description="Telegram Bot token (required when provider == 'telegram')"
    )
    telegram_chat_id: Optional[str] = Field(
        None, description="Telegram chat ID to send alerts to"
    )

    @validator("telegram_bot_token", "telegram_chat_id", always=True)
    def require_telegram_fields(cls, v, values, field):
        if values.get("provider") == "telegram":
            if not v:
                raise ValueError(f"{field.name} is required for telegram notifications")
        return v


class Settings(BaseSettings):
    """
    Top‑level settings object. It reads ``config.json`` (or ``config.example.json``) and
    validates the structure. All fields are exposed as attributes for easy import.
    """

    personal_profile: PersonalProfile
    search_criteria: SearchCriteria
    notification: Notification

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
settings = Settings.load()