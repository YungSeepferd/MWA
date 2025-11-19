"""
Tests for MWA Core configuration module.
"""

import json
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from mwa_core.config import Settings, get_settings, reload_settings


class TestSettings:
    """Test cases for Settings class."""
    
    def test_load_valid_config(self):
        """Test loading a valid configuration file."""
        config_data = {
            "personal_profile": {
                "my_full_name": "Test User",
                "my_profession": "Software Engineer",
                "my_employer": "Test Corp",
                "net_household_income_monthly": 5000,
                "total_occupants": 2,
                "intro_paragraph": "Test introduction"
            },
            "search_criteria": {
                "max_price": 1500,
                "min_rooms": 2,
                "zip_codes": ["80331", "80333"]
            },
            "notification": {
                "provider": "discord",
                "discord_webhook_url": "https://discord.com/api/webhooks/test"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            f.flush()
            
            settings = Settings.load(Path(f.name))
            
            assert settings.personal_profile.my_full_name == "Test User"
            assert settings.search_criteria.max_price == 1500
            assert settings.notification.provider == "discord"
            
            Path(f.name).unlink()
    
    def test_load_invalid_config(self):
        """Test loading an invalid configuration file."""
        config_data = {
            "personal_profile": {
                "my_full_name": "Test User",
                # Missing required fields
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            f.flush()
            
            with pytest.raises(ValueError):
                Settings.load(Path(f.name))
            
            Path(f.name).unlink()
    
    def test_load_nonexistent_config(self):
        """Test loading a non-existent configuration file."""
        with pytest.raises(FileNotFoundError):
            Settings.load(Path("/nonexistent/config.json"))
    
    def test_fallback_to_example_config(self):
        """Test fallback to example configuration."""
        # Create a temporary example config
        example_data = {
            "personal_profile": {
                "my_full_name": "Example User",
                "my_profession": "Example Profession",
                "my_employer": "Example Employer",
                "net_household_income_monthly": 4000,
                "total_occupants": 1,
                "intro_paragraph": "Example introduction"
            },
            "search_criteria": {
                "max_price": 1200,
                "min_rooms": 1,
                "zip_codes": ["80331"]
            },
            "notification": {
                "provider": "discord",
                "discord_webhook_url": "https://discord.com/api/webhooks/example"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(example_data, f)
            f.flush()
            
            # Mock the example path
            with patch('mwa_core.config.settings.Path') as mock_path:
                mock_example = MagicMock()
                mock_example.exists.return_value = True
                mock_example.__truediv__.return_value = Path(f.name)
                
                mock_config = MagicMock()
                mock_config.exists.return_value = False
                mock_config.__truediv__.return_value = Path("/nonexistent/config.json")
                
                mock_path.return_value = mock_config
                mock_path.return_value.parents = [None, None, MagicMock()]
                mock_path.return_value.parents[2].__truediv__.return_value = mock_example
                
                settings = Settings.load()
                assert settings.personal_profile.my_full_name == "Example User"
            
            Path(f.name).unlink()
    
    def test_save_config(self):
        """Test saving configuration to file."""
        config_data = {
            "personal_profile": {
                "my_full_name": "Save Test User",
                "my_profession": "Test Profession",
                "my_employer": "Test Employer",
                "net_household_income_monthly": 4500,
                "total_occupants": 1,
                "intro_paragraph": "Test intro"
            },
            "search_criteria": {
                "max_price": 1300,
                "min_rooms": 2,
                "zip_codes": ["80335"]
            },
            "notification": {
                "provider": "discord",
                "discord_webhook_url": "https://discord.com/api/webhooks/save_test"
            }
        }
        
        settings = Settings.parse_obj(config_data)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            settings.save(Path(f.name))
            
            # Verify file was created and contains correct data
            assert Path(f.name).exists()
            
            with open(f.name, 'r') as read_f:
                saved_data = json.load(read_f)
                assert saved_data["personal_profile"]["my_full_name"] == "Save Test User"
            
            Path(f.name).unlink()
    
    def test_get_provider_config(self):
        """Test getting provider-specific configuration."""
        config_data = {
            "personal_profile": {
                "my_full_name": "Test User",
                "my_profession": "Engineer",
                "my_employer": "Test Corp",
                "net_household_income_monthly": 5000,
                "total_occupants": 1,
                "intro_paragraph": "Test"
            },
            "search_criteria": {
                "max_price": 1500,
                "min_rooms": 2,
                "zip_codes": ["80331"]
            },
            "notification": {
                "provider": "discord",
                "discord_webhook_url": "https://discord.com/api/webhooks/test"
            },
            "scraper": {
                "timeout_seconds": 45,
                "user_agent": "Test User Agent",
                "request_delay_seconds": 2.0,
                "max_retries": 5
            }
        }
        
        settings = Settings.parse_obj(config_data)
        provider_config = settings.get_provider_config("immoscout")
        
        assert provider_config["timeout"] == 45
        assert provider_config["user_agent"] == "Test User Agent"
        assert provider_config["request_delay"] == 2.0
        assert provider_config["max_retries"] == 5
    
    def test_notification_validation(self):
        """Test notification configuration validation."""
        # Test valid Discord config
        valid_discord = {
            "provider": "discord",
            "discord_webhook_url": "https://discord.com/api/webhooks/test"
        }
        notification = NotificationConfig.parse_obj(valid_discord)
        assert notification.provider == "discord"
        
        # Test invalid Discord config (missing webhook URL)
        invalid_discord = {
            "provider": "discord"
        }
        with pytest.raises(ValueError):
            NotificationConfig.parse_obj(invalid_discord)
        
        # Test valid Telegram config
        valid_telegram = {
            "provider": "telegram",
            "telegram_bot_token": "test_token",
            "telegram_chat_id": "test_chat"
        }
        notification = NotificationConfig.parse_obj(valid_telegram)
        assert notification.provider == "telegram"
        
        # Test invalid Telegram config (missing token)
        invalid_telegram = {
            "provider": "telegram",
            "telegram_chat_id": "test_chat"
        }
        with pytest.raises(ValueError):
            NotificationConfig.parse_obj(invalid_telegram)
    
    def test_default_values(self):
        """Test default configuration values."""
        minimal_config = {
            "personal_profile": {
                "my_full_name": "Test User",
                "my_profession": "Engineer",
                "my_employer": "Test Corp",
                "net_household_income_monthly": 5000,
                "total_occupants": 1,
                "intro_paragraph": "Test"
            },
            "search_criteria": {
                "max_price": 1500,
                "min_rooms": 2,
                "zip_codes": ["80331"]
            },
            "notification": {
                "provider": "discord",
                "discord_webhook_url": "https://discord.com/api/webhooks/test"
            }
        }
        
        settings = Settings.parse_obj(minimal_config)
        
        # Check default values
        assert settings.contact_discovery.enabled is True
        assert settings.contact_discovery.confidence_threshold == "medium"
        assert settings.storage.contact_retention_days == 90
        assert settings.scraper.enabled_providers == ["immoscout", "wg_gesucht"]
        assert settings.log_level == "INFO"


class TestSettingsFunctions:
    """Test cases for settings utility functions."""
    
    def test_get_settings_singleton(self):
        """Test that get_settings returns a singleton."""
        with patch('mwa_core.config.settings.Settings.load') as mock_load:
            mock_settings = MagicMock()
            mock_load.return_value = mock_settings
            
            settings1 = get_settings()
            settings2 = get_settings()
            
            assert settings1 is settings2
            mock_load.assert_called_once()
    
    def test_reload_settings(self):
        """Test reloading settings."""
        with patch('mwa_core.config.settings.Settings.load') as mock_load:
            mock_settings = MagicMock()
            mock_load.return_value = mock_settings
            
            # First load
            settings1 = get_settings()
            
            # Reload
            settings2 = reload_settings()
            
            assert settings1 is not settings2
            assert mock_load.call_count == 2


class TestEnvironmentVariables:
    """Test environment variable overrides."""
    
    @patch.dict('os.environ', {'MWA_LOG_LEVEL': 'DEBUG', 'MWA_SCRAPER_TIMEOUT_SECONDS': '60'})
    def test_environment_variable_override(self):
        """Test that environment variables override config file values."""
        config_data = {
            "personal_profile": {
                "my_full_name": "Test User",
                "my_profession": "Engineer",
                "my_employer": "Test Corp",
                "net_household_income_monthly": 5000,
                "total_occupants": 1,
                "intro_paragraph": "Test"
            },
            "search_criteria": {
                "max_price": 1500,
                "min_rooms": 2,
                "zip_codes": ["80331"]
            },
            "notification": {
                "provider": "discord",
                "discord_webhook_url": "https://discord.com/api/webhooks/test"
            },
            "scraper": {
                "timeout_seconds": 30  # This should be overridden by env var
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f)
            f.flush()
            
            settings = Settings.load(Path(f.name))
            
            # Environment variable should override config file
            assert settings.log_level == "DEBUG"
            assert settings.scraper.timeout_seconds == 60
            
            Path(f.name).unlink()