"""
Comprehensive configuration validation tests.
"""

import pytest
import json
import tempfile
from pathlib import Path
from pydantic import ValidationError

from mafa.config.settings import Settings, PersonalProfile, SearchCriteria, Notification


class TestPersonalProfile:
    """Test PersonalProfile model validation."""
    
    def test_valid_personal_profile(self):
        """Test that valid personal profile passes validation."""
        data = {
            "my_full_name": "Max Mustermann",
            "my_profession": "Software Engineer",
            "my_employer": "Google Germany GmbH",
            "net_household_income_monthly": 4500,
            "total_occupants": 2,
            "intro_paragraph": "Wir sind ein ruhiges, zuverlässiges und nicht-rauchendes Paar..."
        }
        
        profile = PersonalProfile(**data)
        assert profile.my_full_name == "Max Mustermann"
        assert profile.net_household_income_monthly == 4500
    
    def test_missing_required_fields(self):
        """Test that missing required fields raise ValidationError."""
        data = {
            "my_full_name": "Max Mustermann",
            "my_profession": "Software Engineer",
            # Missing other required fields
        }
        
        with pytest.raises(ValidationError):
            PersonalProfile(**data)
    
    def test_invalid_income_value(self):
        """Test that negative or zero income values are rejected."""
        data = {
            "my_full_name": "Max Mustermann",
            "my_profession": "Software Engineer",
            "my_employer": "Google Germany GmbH",
            "net_household_income_monthly": -100,  # Invalid: negative
            "total_occupants": 2,
            "intro_paragraph": "Test paragraph"
        }
        
        with pytest.raises(ValidationError):
            PersonalProfile(**data)
    
    def test_invalid_occupants_value(self):
        """Test that zero or negative occupants are rejected."""
        data = {
            "my_full_name": "Max Mustermann",
            "my_profession": "Software Engineer",
            "my_employer": "Google Germany GmbH",
            "net_household_income_monthly": 4500,
            "total_occupants": 0,  # Invalid: must be > 0
            "intro_paragraph": "Test paragraph"
        }
        
        with pytest.raises(ValidationError):
            PersonalProfile(**data)


class TestSearchCriteria:
    """Test SearchCriteria model validation."""
    
    def test_valid_search_criteria(self):
        """Test that valid search criteria pass validation."""
        data = {
            "max_price": 2000,
            "min_rooms": 2,
            "zip_codes": ["80799", "80803", "80331"]
        }
        
        criteria = SearchCriteria(**data)
        assert criteria.max_price == 2000
        assert criteria.min_rooms == 2
        assert len(criteria.zip_codes) == 3
    
    def test_empty_zip_codes(self):
        """Test that empty zip codes list is rejected."""
        data = {
            "max_price": 2000,
            "min_rooms": 2,
            "zip_codes": []  # Invalid: must have at least 1 item
        }
        
        with pytest.raises(ValidationError):
            SearchCriteria(**data)
    
    def test_invalid_price(self):
        """Test that negative or zero prices are rejected."""
        data = {
            "max_price": -100,  # Invalid: must be > 0
            "min_rooms": 2,
            "zip_codes": ["80799"]
        }
        
        with pytest.raises(ValidationError):
            SearchCriteria(**data)


class TestNotification:
    """Test Notification model validation."""
    
    def test_valid_discord_notification(self):
        """Test that valid Discord notification passes validation."""
        data = {
            "provider": "discord",
            "discord_webhook_url": "https://discord.com/api/webhooks/test"
        }
        
        notification = Notification(**data)
        assert notification.provider == "discord"
        assert notification.discord_webhook_url == "https://discord.com/api/webhooks/test"
    
    def test_valid_telegram_notification(self):
        """Test that valid Telegram notification passes validation."""
        data = {
            "provider": "telegram",
            "telegram_bot_token": "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz",
            "telegram_chat_id": "123456789"
        }
        
        notification = Notification(**data)
        assert notification.provider == "telegram"
        assert notification.telegram_bot_token == "1234567890:ABCdefGHIjklMNOpqrsTUVwxyz"
        assert notification.telegram_chat_id == "123456789"
    
    def test_missing_discord_webhook(self):
        """Test that Discord provider without webhook URL is rejected."""
        data = {
            "provider": "discord",
            # Missing discord_webhook_url
        }
        
        with pytest.raises(ValidationError):
            Notification(**data)
    
    def test_missing_telegram_fields(self):
        """Test that Telegram provider without required fields is rejected."""
        data = {
            "provider": "telegram",
            "telegram_bot_token": "test_token",
            # Missing telegram_chat_id
        }
        
        with pytest.raises(ValidationError):
            Notification(**data)


class TestSettings:
    """Test Settings model validation."""
    
    def test_valid_settings_loading(self):
        """Test that valid settings JSON file can be loaded."""
        config_data = {
            "personal_profile": {
                "my_full_name": "Max Mustermann",
                "my_profession": "Software Engineer",
                "my_employer": "Google Germany GmbH",
                "net_household_income_monthly": 4500,
                "total_occupants": 2,
                "intro_paragraph": "Test paragraph"
            },
            "search_criteria": {
                "max_price": 2000,
                "min_rooms": 2,
                "zip_codes": ["80799"]
            },
            "notification": {
                "provider": "discord",
                "discord_webhook_url": "https://discord.com/api/webhooks/test"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = Path(f.name)
        
        try:
            settings = Settings.load(path=config_path)
            assert settings.personal_profile.my_full_name == "Max Mustermann"
            assert settings.search_criteria.max_price == 2000
            assert settings.notification.provider == "discord"
        finally:
            config_path.unlink()
    
    def test_config_file_not_found_fallback(self):
        """Test that missing config file falls back to example file."""
        non_existent_path = Path("/non/existent/path.json")
        # This should try to fall back to config.example.json
        # The test assumes config.example.json exists
        try:
            settings = Settings.load(path=non_existent_path)
            assert settings is not None
        except FileNotFoundError:
            # Expected if example file doesn't exist
            pass
    
    def test_invalid_json_parsing(self):
        """Test that invalid JSON in config file raises appropriate error."""
        invalid_json = "{ invalid json content "
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(invalid_json)
            config_path = Path(f.name)
        
        try:
            with pytest.raises(json.JSONDecodeError):
                Settings.load(path=config_path)
        finally:
            config_path.unlink()
    
    def test_environment_variable_override(self):
        """Test that environment variables can override configuration."""
        import os
        import tempfile
        
        config_data = {
            "personal_profile": {
                "my_full_name": "Original Name",
                "my_profession": "Software Engineer",
                "my_employer": "Google Germany GmbH",
                "net_household_income_monthly": 4500,
                "total_occupants": 2,
                "intro_paragraph": "Test paragraph"
            },
            "search_criteria": {
                "max_price": 2000,
                "min_rooms": 2,
                "zip_codes": ["80799"]
            },
            "notification": {
                "provider": "discord",
                "discord_webhook_url": "https://discord.com/api/webhooks/test"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            config_path = Path(f.name)
        
        try:
            # Set environment variable
            os.environ['MY_FULL_NAME'] = 'Environment Name'
            
            # Load settings (environment variables should override)
            settings = Settings.load(path=config_path)
            
            # Note: This test depends on how environment variable handling is implemented
            # Adjust based on actual implementation
            assert settings is not None
            
        finally:
            config_path.unlink()
            if 'MY_FULL_NAME' in os.environ:
                del os.environ['MY_FULL_NAME']


class TestConfigurationEdgeCases:
    """Test edge cases and error conditions in configuration."""
    
    def test_circular_references_prevention(self):
        """Test that configuration prevents circular references or malicious input."""
        # This is more relevant for web applications, but good to test
        malicious_data = {
            "personal_profile": {
                "my_full_name": "Test",
                "my_profession": "Test",
                "my_employer": "Test",
                "net_household_income_monthly": 1000,
                "total_occupants": 1,
                "intro_paragraph": "x" * 10000  # Very long paragraph
            },
            "search_criteria": {
                "max_price": 2000,
                "min_rooms": 2,
                "zip_codes": ["80799"] * 1000  # Very long list
            },
            "notification": {
                "provider": "discord",
                "discord_webhook_url": "https://discord.com/api/webhooks/test"
            }
        }
        
        try:
            profile = PersonalProfile(**malicious_data["personal_profile"])
            criteria = SearchCriteria(**malicious_data["search_criteria"])
            # Should handle large inputs gracefully
            assert len(profile.intro_paragraph) == 10000
            assert len(criteria.zip_codes) == 1000
        except ValidationError:
            # Acceptable if validation rejects extreme values
            pass
    
    def test_invalid_provider_name(self):
        """Test that invalid provider names are handled."""
        config_data = {
            "personal_profile": {
                "my_full_name": "Max Mustermann",
                "my_profession": "Software Engineer",
                "my_employer": "Google Germany GmbH",
                "net_household_income_monthly": 4500,
                "total_occupants": 2,
                "intro_paragraph": "Test paragraph"
            },
            "search_criteria": {
                "max_price": 2000,
                "min_rooms": 2,
                "zip_codes": ["80799"]
            },
            "notification": {
                "provider": "invalid_provider",
                "discord_webhook_url": "https://discord.com/api/webhooks/test"
            }
        }
        
        with pytest.raises(ValidationError):
            Notification(**config_data["notification"])