"""
End-to-end integration tests for MAFA.
Tests the complete workflow from scraping to notification.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from mafa.orchestrator import run
from mafa.config.settings import Settings
from mafa.db.manager import ListingRepository
from mafa.notifier.discord import DiscordNotifier


class TestEndToEndWorkflow:
    """Test suite for end-to-end MAFA workflow."""

    @pytest.fixture
    def temp_config(self):
        """Create a temporary configuration for testing."""
        config_data = {
            "personal_profile": {
                "my_full_name": "Test User",
                "my_profession": "Software Engineer",
                "my_employer": "Test Corp",
                "net_household_income_monthly": 4500,
                "total_occupants": 2,
                "intro_paragraph": "Test user for integration testing"
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
            "scrapers": ["immoscout"],
            "contact_discovery": {
                "enabled": True,
                "confidence_threshold": "medium",
                "validation_enabled": True,
                "rate_limit_seconds": 1.0
            }
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
                "source": "ImmoScout24",
                "timestamp": datetime.now().isoformat(),
                "url": "https://www.immobilienscout24.de/expose/123456",
                "description": "Beautiful apartment in Munich city center",
                "size": "60 sqm",
                "rooms": 2
            },
            {
                "title": "Another Apartment in Munich 80333",
                "price": "1.400 €",
                "source": "ImmoScout24",
                "timestamp": datetime.now().isoformat(),
                "url": "https://www.immobilienscout24.de/expose/789012",
                "description": "Spacious apartment with balcony",
                "size": "75 sqm",
                "rooms": 3
            }
        ]

    @patch('mafa.orchestrator.build_providers')
    @patch('mafa.orchestrator.get_metrics_collector')
    @patch('mafa.orchestrator.get_health_checker')
    @patch('mafa.orchestrator.Settings.load')
    def test_complete_workflow_normal_mode(
        self, mock_settings_load, mock_health_checker, mock_metrics_collector, 
        mock_build_providers, temp_config, mock_listings
    ):
        """Test complete workflow in normal mode."""
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
        
        # Mock provider
        mock_provider = Mock()
        mock_provider.scrape.return_value = mock_listings
        mock_provider.__class__.__name__ = "ImmoScoutProvider"
        mock_build_providers.return_value = [mock_provider]
        
        # Mock database and notifier
        with patch('mafa.orchestrator.ListingRepository') as mock_repo_class, \
             patch('mafa.orchestrator.DiscordNotifier') as mock_discord_class:
            
            mock_repo = Mock()
            mock_repo.bulk_add.return_value = 2
            mock_repo_class.return_value = mock_repo
            
            mock_notifier = Mock()
            mock_discord_class.return_value = mock_notifier
            
            # Run the workflow
            with tempfile.TemporaryDirectory() as temp_dir:
                data_dir = Path(temp_dir) / "data"
                data_dir.mkdir()
                
                with patch('mafa.orchestrator.Path') as mock_path:
                    mock_path.return_value.resolve.return_value.parents[3] = temp_dir
                    
                    run(config_path=temp_config, dry_run=False)
            
            # Verify workflow steps
            mock_provider.scrape.assert_called_once()
            mock_repo.bulk_add.assert_called_once_with(mock_listings)
            mock_notifier.send_listings.assert_called_once()
            
            # Verify metrics collection
            assert mock_metrics.record_scrape_attempt.call_count >= 1

    @patch('mafa.orchestrator.build_providers')
    @patch('mafa.orchestrator.get_metrics_collector')
    @patch('mafa.orchestrator.get_health_checker')
    @patch('mafa.orchestrator.Settings.load')
    def test_complete_workflow_dry_run_mode(
        self, mock_settings_load, mock_health_checker, mock_metrics_collector, 
        mock_build_providers, temp_config, mock_listings
    ):
        """Test complete workflow in dry-run mode."""
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
        
        # Mock provider
        mock_provider = Mock()
        mock_provider.scrape.return_value = mock_listings
        mock_provider.__class__.__name__ = "ImmoScoutProvider"
        mock_build_providers.return_value = [mock_provider]
        
        # Run the workflow in dry-run mode
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / "data"
            data_dir.mkdir()
            
            with patch('mafa.orchestrator.Path') as mock_path, \
                 patch('mafa.orchestrator.ListingRepository') as mock_repo_class, \
                 patch('mafa.orchestrator.DiscordNotifier') as mock_discord_class:
                
                mock_path.return_value.resolve.return_value.parents[3] = temp_dir
                
                run(config_path=temp_config, dry_run=True)
            
            # Verify dry-run behavior
            mock_provider.scrape.assert_called_once()
            mock_repo_class.assert_not_called()  # Database not initialized
            mock_discord_class.assert_not_called()  # Notifier not initialized

    @patch('mafa.orchestrator.build_providers')
    @patch('mafa.orchestrator.get_metrics_collector')
    @patch('mafa.orchestrator.get_health_checker')
    @patch('mafa.orchestrator.Settings.load')
    def test_workflow_with_provider_failure(
        self, mock_settings_load, mock_health_checker, mock_metrics_collector, 
        mock_build_providers, temp_config
    ):
        """Test workflow behavior when provider fails."""
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
        
        # Mock provider that fails
        mock_provider = Mock()
        mock_provider.scrape.side_effect = Exception("Scraping failed")
        mock_provider.__class__.__name__ = "ImmoScoutProvider"
        mock_build_providers.return_value = [mock_provider]
        
        # Run the workflow
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / "data"
            data_dir.mkdir()
            
            with patch('mafa.orchestrator.Path') as mock_path:
                mock_path.return_value.resolve.return_value.parents[3] = temp_dir
                
                # Should not raise exception despite provider failure
                run(config_path=temp_config, dry_run=True)
        
        # Verify error handling
        mock_provider.scrape.assert_called_once()
        assert mock_metrics.record_scrape_attempt.call_count >= 1

    @patch('mafa.orchestrator.build_providers')
    @patch('mafa.orchestrator.get_metrics_collector')
    @patch('mafa.orchestrator.get_health_checker')
    @patch('mafa.orchestrator.Settings.load')
    def test_workflow_with_no_listings(
        self, mock_settings_load, mock_health_checker, mock_metrics_collector, 
        mock_build_providers, temp_config
    ):
        """Test workflow when no listings are found."""
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
        
        # Mock provider with no listings
        mock_provider = Mock()
        mock_provider.scrape.return_value = []
        mock_provider.__class__.__name__ = "ImmoScoutProvider"
        mock_build_providers.return_value = [mock_provider]
        
        # Run the workflow
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / "data"
            data_dir.mkdir()
            
            with patch('mafa.orchestrator.Path') as mock_path:
                mock_path.return_value.resolve.return_value.parents[3] = temp_dir
                
                run(config_path=temp_config, dry_run=True)
        
        # Verify behavior with no listings
        mock_provider.scrape.assert_called_once()
        assert mock_metrics.record_scrape_attempt.call_count >= 1

    @patch('mafa.orchestrator.build_providers')
    @patch('mafa.orchestrator.get_metrics_collector')
    @patch('mafa.orchestrator.get_health_checker')
    @patch('mafa.orchestrator.Settings.load')
    def test_workflow_with_multiple_providers(
        self, mock_settings_load, mock_health_checker, mock_metrics_collector, 
        mock_build_providers, temp_config, mock_listings
    ):
        """Test workflow with multiple providers."""
        # Setup mocks
        mock_settings = Mock()
        mock_settings.scrapers = ["immoscout", "wg_gesucht"]
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
        
        # Mock multiple providers
        mock_provider1 = Mock()
        mock_provider1.scrape.return_value = mock_listings[:1]
        mock_provider1.__class__.__name__ = "ImmoScoutProvider"
        
        mock_provider2 = Mock()
        mock_provider2.scrape.return_value = mock_listings[1:]
        mock_provider2.__class__.__name__ = "WGGesuchtProvider"
        
        mock_build_providers.return_value = [mock_provider1, mock_provider2]
        
        # Run the workflow
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / "data"
            data_dir.mkdir()
            
            with patch('mafa.orchestrator.Path') as mock_path:
                mock_path.return_value.resolve.return_value.parents[3] = temp_dir
                
                run(config_path=temp_config, dry_run=True)
        
        # Verify both providers were called
        mock_provider1.scrape.assert_called_once()
        mock_provider2.scrape.assert_called_once()
        assert mock_metrics.record_scrape_attempt.call_count >= 2

    @patch('mafa.orchestrator.build_providers')
    @patch('mafa.orchestrator.get_metrics_collector')
    @patch('mafa.orchestrator.get_health_checker')
    @patch('mafa.orchestrator.Settings.load')
    def test_workflow_csv_report_generation(
        self, mock_settings_load, mock_health_checker, mock_metrics_collector, 
        mock_build_providers, temp_config, mock_listings
    ):
        """Test CSV report generation in workflow."""
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
        
        # Mock provider
        mock_provider = Mock()
        mock_provider.scrape.return_value = mock_listings
        mock_provider.__class__.__name__ = "ImmoScoutProvider"
        mock_build_providers.return_value = [mock_provider]
        
        # Run the workflow and check CSV generation
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / "data"
            data_dir.mkdir()
            
            with patch('mafa.orchestrator.Path') as mock_path:
                mock_path.return_value.resolve.return_value.parents[3] = temp_dir
                
                run(config_path=temp_config, dry_run=True)
            
            # Verify CSV report was generated
            csv_files = list(data_dir.glob("report_*_dryrun.csv"))
            assert len(csv_files) == 1, "CSV report should be generated"
            
            # Verify CSV content
            csv_file = csv_files[0]
            with open(csv_file, 'r') as f:
                content = f.read()
                assert "Test Apartment in Munich 80331" in content
                assert "Another Apartment in Munich 80333" in content
                assert "title,price,source,timestamp" in content

    @patch('mafa.orchestrator.build_providers')
    @patch('mafa.orchestrator.get_metrics_collector')
    @patch('mafa.orchestrator.get_health_checker')
    @patch('mafa.orchestrator.Settings.load')
    def test_workflow_health_check_integration(
        self, mock_settings_load, mock_health_checker, mock_metrics_collector, 
        mock_build_providers, temp_config, mock_listings
    ):
        """Test health check integration in workflow."""
        # Setup mocks
        mock_settings = Mock()
        mock_settings.scrapers = ["immoscout"]
        mock_settings.search_criteria = Mock()
        mock_settings.search_criteria.max_price = 1500
        mock_settings.search_criteria.zip_codes = ["80331", "80333"]
        mock_settings_load.return_value = mock_settings
        
        # Mock unhealthy system
        mock_health_status = Mock()
        mock_health_status.status = "unhealthy"
        mock_health_status.issues = ["Database connection failed", "Memory usage high"]
        mock_health_checker.return_value.get_health_status.return_value = mock_health_status
        
        mock_metrics = Mock()
        mock_metrics_collector.return_value = mock_metrics
        
        # Mock provider
        mock_provider = Mock()
        mock_provider.scrape.return_value = mock_listings
        mock_provider.__class__.__name__ = "ImmoScoutProvider"
        mock_build_providers.return_value = [mock_provider]
        
        # Run the workflow - should continue despite unhealthy status
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / "data"
            data_dir.mkdir()
            
            with patch('mafa.orchestrator.Path') as mock_path:
                mock_path.return_value.resolve.return_value.parents[3] = temp_dir
                
                # Should not raise exception despite unhealthy status
                run(config_path=temp_config, dry_run=True)
        
        # Verify health check was called
        mock_health_checker.return_value.get_health_status.assert_called_once()
        mock_provider.scrape.assert_called_once()