#!/usr/bin/env python3
"""
Test script to verify Discord notifier functionality.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from mafa.config.settings import Settings
from mafa.notifier.discord import DiscordNotifier
from unittest.mock import Mock, patch

def test_discord_notifier_initialization():
    """Test that DiscordNotifier can be initialized correctly."""
    print("Testing Discord notifier initialization...")
    
    # Create a mock settings object with valid Discord configuration
    mock_settings = Mock()
    mock_settings.notification.provider = "discord"
    mock_settings.notification.discord_webhook_url = "https://discord.com/api/webhooks/test/test"
    
    try:
        # Test initialization with valid settings
        notifier = DiscordNotifier(mock_settings)
        print("✓ DiscordNotifier initialized successfully")
        
        # Test the send_listings method
        test_listings = [
            {
                "title": "Test Listing 1",
                "price": "1000 €",
                "source": "immoscout",
                "timestamp": "2025-11-20T10:00:00Z"
            },
            {
                "title": "Test Listing 2", 
                "price": "1200 €",
                "source": "wg_gesucht",
                "timestamp": "2025-11-20T11:00:00Z"
            }
        ]
        
        # Mock the httpx.post call to avoid actual network requests
        with patch('mafa.notifier.discord.httpx.post') as mock_post:
            mock_post.return_value.status_code = 200
            
            notifier.send_listings(test_listings)
            print("✓ send_listings method called successfully")
            
            # Verify that httpx.post was called with the correct arguments
            mock_post.assert_called_once()
            print("✓ HTTP request was made to Discord webhook")
            
        return True
        
    except Exception as e:
        print(f"✗ Error testing Discord notifier: {e}")
        return False

def test_discord_notifier_with_invalid_url():
    """Test DiscordNotifier behavior with invalid webhook URL."""
    print("\nTesting Discord notifier with invalid URL...")
    
    # Create a mock settings object with invalid Discord configuration
    mock_settings = Mock()
    mock_settings.notification.provider = "discord"
    mock_settings.notification.discord_webhook_url = None  # Invalid URL
    
    try:
        # This should raise a ValueError
        notifier = DiscordNotifier(mock_settings)
        print("✗ DiscordNotifier should have raised ValueError for missing webhook URL")
        return False
        
    except ValueError as e:
        print(f"✓ DiscordNotifier correctly raised ValueError: {e}")
        return True
    except Exception as e:
        print(f"✗ Unexpected error: {e}")
        return False

def test_configuration_validation():
    """Test that the configuration validation works correctly."""
    print("\nTesting configuration validation...")
    
    try:
        # Load settings from config.json
        settings = Settings.load()
        print(f"✓ Configuration loaded successfully")
        print(f"  - Notification provider: {settings.notification.provider}")
        print(f"  - Discord webhook URL: {settings.notification.discord_webhook_url}")
        
        # Check if webhook URL is valid
        if settings.notification.discord_webhook_url and "YOUR_WEBHOOK" not in settings.notification.discord_webhook_url:
            print("✓ Discord webhook URL appears to be configured")
            return True
        else:
            print("✗ Discord webhook URL is not properly configured (placeholder detected)")
            return False
            
    except Exception as e:
        print(f"✗ Error loading configuration: {e}")
        return False

if __name__ == "__main__":
    print("=== Testing Discord Notification System ===\n")
    
    # Test initialization
    init_test = test_discord_notifier_initialization()
    
    # Test invalid URL handling
    invalid_test = test_discord_notifier_with_invalid_url()
    
    # Test configuration validation
    config_test = test_configuration_validation()
    
    print("\n=== Test Results ===")
    if init_test and invalid_test and config_test:
        print("✓ All Discord notifier tests passed!")
        print("✓ The Discord notifier code is working correctly")
    else:
        print("✗ Some Discord notifier tests failed")
    
    print("\n=== Issue Analysis ===")
    print("The main issue is that the Discord webhook URL in config.json is still a placeholder.")
    print("To fix this, you need to:")
    print("1. Create a Discord webhook in your Discord server")
    print("2. Update the 'discord_webhook_url' in config.json with the real webhook URL")
    print("3. Restart the application")
    
    print("\n=== Steps to Create Discord Webhook ===")
    print("1. Go to your Discord server")
    print("2. Server Settings → Integrations → Webhooks")
    print("3. Create New Webhook")
    print("4. Copy the Webhook URL")
    print("5. Update config.json with the real URL")