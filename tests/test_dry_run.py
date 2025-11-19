"""
Tests for dry-run functionality in the MAFA orchestrator.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from mafa.orchestrator import run
from mafa.config.settings import Settings
from mafa.db.manager import ListingRepository
from mafa.notifier.discord import DiscordNotifier


class TestDryRunFunctionality:
    """Test suite for dry-run mode functionality."""

    @pytest.fixture
    def temp_config(self):
        """Create a temporary configuration file for testing."""
        config_data = {
            "personal_profile": {
                "my_full_name": "Test User",
                "my_profession": "Software Engineer",
                "my_employer": "Test Corp",
                "net_household_income_monthly": 4500,
                "total_occupants": 2,
                "intro_paragraph": "Test user for dry-run testing"
            },
            "search_criteria": {
                "max_price": 1500,
                "min_rooms": 2,
                "zip_codes": ["80331", "80333"]
            },
            "notification": {
                "provider": "discord",
                "discord_webhook_url": "https://discord.com/api/webhooks/test"
            },
            "scrapers": ["immoscout"]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(config_data, f, indent=2)
            temp_path = Path(f.name)
        
        yield temp_path
        
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

    @pytest.fixture
    def mock_listings(self):
        """Mock listing data for testing."""
        return [
            {
                "title": "Test Apartment in Munich 80331",
                "price": "1.200 €",
                "source": "TestProvider",
                "timestamp": "2024-01-01T12:00:00"
            },
            {
                "title": "Another Apartment in Munich 80333",
                "price": "1.400 €",
                "source": "TestProvider",
                "timestamp": "2024-01-01T12:30:00"
            }
        ]

    @patch('mafa.orchestrator.build_providers')
    @patch('mafa.orchestrator.get_metrics_collector')
    @patch('mafa.orchestrator.get_health_checker')
    @patch('mafa.orchestrator.Settings.load')
    def test_dry_run_mode_skips_database_persistence(
        self, mock_settings_load, mock_health_checker, mock_metrics_collector, 
        mock_build_providers, temp_config, mock_listings
    ):
        """Test that dry-run mode skips database persistence."""
        # Setup mocks
        mock_settings = Mock()
        mock_settings.scrapers = ["immoscout"]
        mock_settings.search_criteria = Mock()
        mock_settings.search_criteria.max_price = 1500
        mock_settings.search_criteria.zip_codes = ["80331", "80333"]
        mock_settings_load.return_value = mock_settings
        
        mock_health_status = Mock()
        mock_health_status.status = "healthy"
        mock_health_status.issues = []
        mock_health_checker.return_value.get_health_status.return_value = mock_health_status
        
        mock_metrics = Mock()
        mock_metrics_collector.return_value = mock_metrics
        
        mock_provider = Mock()
        mock_provider.scrape.return_value = mock_listings
        mock_provider.__class__.__name__ = "TestProvider"
        mock_build_providers.return_value = [mock_provider]
        
        # Test dry-run mode
        with patch('mafa.orchestrator.ListingRepository') as mock_repo_class:
            run(config_path=temp_config, dry_run=True)
            
            # Verify that ListingRepository was not instantiated in dry-run mode
            mock_repo_class.assert_not_called()

    @patch('mafa.orchestrator.build_providers')
    @patch('mafa.orchestrator.get_metrics_collector')
    @patch('mafa.orchestrator.get_health_checker')
    @patch('mafa.orchestrator.Settings.load')
    def test_normal_mode_includes_database_persistence(
        self, mock_settings_load, mock_health_checker, mock_metrics_collector, 
        mock_build_providers, temp_config, mock_listings
    ):
        """Test that normal mode includes database persistence."""
        # Setup mocks
        mock_settings = Mock()
        mock_settings.scrapers = ["immoscout"]
        mock_settings.search_criteria = Mock()
        mock_settings.search_criteria.max_price = 1500
        mock_settings.search_criteria.zip_codes = ["80331", "80333"]
        mock_settings_load.return_value = mock_settings
        
        mock_health_status = Mock()
        mock_health_status.status = "healthy"
        mock_health_status.issues = []
        mock_health_checker.return_value.get_health_status.return_value = mock_health_status
        
        mock_metrics = Mock()
        mock_metrics_collector.return_value = mock_metrics
        
        mock_provider = Mock()
        mock_provider.scrape.return_value = mock_listings
        mock_provider.__class__.__name__ = "TestProvider"
        mock_build_providers.return_value = [mock_provider]
        
        # Test normal mode
        with patch('mafa.orchestrator.ListingRepository') as mock_repo_class:
            mock_repo = Mock()
            mock_repo.bulk_add.return_value = 2
            mock_repo_class.return_value = mock_repo
            
            run(config_path=temp_config, dry_run=False)
            
            # Verify that ListingRepository was instantiated in normal mode
            mock_repo_class.assert_called_once()
            mock_repo.bulk_add.assert_called_once()

    @patch('mafa.orchestrator.build_providers')
    @patch('mafa.orchestrator.get_metrics_collector')
    @patch('mafa.orchestrator.get_health_checker')
    @patch('mafa.orchestrator.Settings.load')
    def test_dry_run_mode_skips_notifier_initialization(
        self, mock_settings_load, mock_health_checker, mock_metrics_collector, 
        mock_build_providers, temp_config, mock_listings
    ):
        """Test that dry-run mode skips notifier initialization."""
        # Setup mocks
        mock_settings = Mock()
        mock_settings.scrapers = ["immoscout"]
        mock_settings.search_criteria = Mock()
        mock_settings.search_criteria.max_price = 1500
        mock_settings.search_criteria.zip_codes = ["80331", "80333"]
        mock_settings_load.return_value = mock_settings
        
        mock_health_status = Mock()
        mock_health_status.status = "healthy"
        mock_health_status.issues = []
        mock_health_checker.return_value.get_health_status.return_value = mock_health_status
        
        mock_metrics = Mock()
        mock_metrics_collector.return_value = mock_metrics
        
        mock_provider = Mock()
        mock_provider.scrape.return_value = mock_listings
        mock_provider.__class__.__name__ = "TestProvider"
        mock_build_providers.return_value = [mock_provider]
        
        # Test dry-run mode
        with patch('mafa.orchestrator.DiscordNotifier') as mock_discord:
            run(config_path=temp_config, dry_run=True)
            
            # Verify that DiscordNotifier was not instantiated in dry-run mode
            mock_discord.assert_not_called()

    @patch('mafa.orchestrator.build_providers')
    @patch('mafa.orchestrator.get_metrics_collector')
    @patch('mafa.orchestrator.get_health_checker')
    @patch('mafa.orchestrator.Settings.load')
    def test_dry_run_mode_generates_csv_report(
        self, mock_settings_load, mock_health_checker, mock_metrics_collector, 
        mock_build_providers, temp_config, mock_listings
    ):
        """Test that dry-run mode still generates CSV reports."""
        # Setup mocks
        mock_settings = Mock()
        mock_settings.scrapers = ["immoscout"]
        mock_settings.search_criteria = Mock()
        mock_settings.search_criteria.max_price = 1500
        mock_settings.search_criteria.zip_codes = ["80331", "80333"]
        mock_settings_load.return_value = mock_settings
        
        mock_health_status = Mock()
        mock_health_status.status = "healthy"
        mock_health_status.issues = []
        mock_health_checker.return_value.get_health_status.return_value = mock_health_status
        
        mock_metrics = Mock()
        mock_metrics_collector.return_value = mock_metrics
        
        mock_provider = Mock()
        mock_provider.scrape.return_value = mock_listings
        mock_provider.__class__.__name__ = "TestProvider"
        mock_build_providers.return_value = [mock_provider]
        
        # Test dry-run mode
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / "data"
            data_dir.mkdir()
            
            with patch('mafa.orchestrator.Path') as mock_path:
                mock_path.return_value.resolve.return_value.parents[3] = temp_dir
                
                run(config_path=temp_config, dry_run=True)
                
                # Verify that CSV report was generated
                csv_files = list(data_dir.glob("report_*_dryrun.csv"))
                assert len(csv_files) == 1, "CSV report should be generated in dry-run mode"
                
                # Verify CSV content
                csv_file = csv_files[0]
                with open(csv_file, 'r') as f:
                    content = f.read()
                    assert "Test Apartment in Munich 80331" in content
                    assert "Another Apartment in Munich 80333" in content

    @patch('mafa.orchestrator.build_providers')
    @patch('mafa.orchestrator.get_metrics_collector')
    @patch('mafa.orchestrator.get_health_checker')
    @patch('mafa.orchestrator.Settings.load')
    def test_dry_run_mode_logs_appropriately(
        self, mock_settings_load, mock_health_checker, mock_metrics_collector, 
        mock_build_providers, temp_config, mock_listings
    ):
        """Test that dry-run mode logs appropriate messages."""
        # Setup mocks
        mock_settings = Mock()
        mock_settings.scrapers = ["immoscout"]
        mock_settings.search_criteria = Mock()
        mock_settings.search_criteria.max_price = 1500
        mock_settings.search_criteria.zip_codes = ["80331", "80333"]
        mock_settings_load.return_value = mock_settings
        
        mock_health_status = Mock()
        mock_health_status.status = "healthy"
        mock_health_status.issues = []
        mock_health_checker.return_value.get_health_status.return_value = mock_health_status
        
        mock_metrics = Mock()
        mock_metrics_collector.return_value = mock_metrics
        
        mock_provider = Mock()
        mock_provider.scrape.return_value = mock_listings
        mock_provider.__class__.__name__ = "TestProvider"
        mock_build_providers.return_value = [mock_provider]
        
        # Test dry-run mode logging
        with patch('mafa.orchestrator.logger') as mock_logger:
            run(config_path=temp_config, dry_run=True)
            
            # Verify dry-run specific log messages
            mock_logger.info.assert_any_call("DRY-RUN MODE: No database persistence, no notifications will be performed")
            mock_logger.info.assert_any_call("DRY-RUN: Skipping database initialization")
            mock_logger.info.assert_any_call("DRY-RUN: Skipping notifier initialization")

    @patch('mafa.orchestrator.build_providers')
    @patch('mafa.orchestrator.get_metrics_collector')
    @patch('mafa.orchestrator.get_health_checker')
    @patch('mafa.orchestrator.Settings.load')
    def test_dry_run_mode_with_no_listings(
        self, mock_settings_load, mock_health_checker, mock_metrics_collector, 
        mock_build_providers, temp_config
    ):
        """Test dry-run mode behavior when no listings are found."""
        # Setup mocks
        mock_settings = Mock()
        mock_settings.scrapers = ["immoscout"]
        mock_settings.search_criteria = Mock()
        mock_settings.search_criteria.max_price = 1500
        mock_settings.search_criteria.zip_codes = ["80331", "80333"]
        mock_settings_load.return_value = mock_settings
        
        mock_health_status = Mock()
        mock_health_status.status = "healthy"
        mock_health_status.issues = []
        mock_health_checker.return_value.get_health_status.return_value = mock_health_status
        
        mock_metrics = Mock()
        mock_metrics_collector.return_value = mock_metrics
        
        mock_provider = Mock()
        mock_provider.scrape.return_value = []  # No listings
        mock_provider.__class__.__name__ = "TestProvider"
        mock_build_providers.return_value = [mock_provider]
        
        # Test dry-run mode with no listings
        with patch('mafa.orchestrator.logger') as mock_logger:
            run(config_path=temp_config, dry_run=True)
            
            # Verify appropriate logging
            mock_logger.info.assert_any_call("No listings found from any provider")

    def test_dry_run_parameter_default(self):
        """Test that dry_run parameter defaults to False."""
        # This test verifies the function signature
        import inspect
        sig = inspect.signature(run)
        dry_run_param = sig.parameters['dry_run']
        assert dry_run_param.default is False, "dry_run should default to False"