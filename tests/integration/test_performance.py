"""
Performance tests for MAFA.
Tests system performance under various conditions.
"""

import pytest
import time
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor
import psutil
import threading

from mafa.orchestrator import run
from mafa.providers.immoscout import ImmoScoutProvider
from mafa.db.manager import ListingRepository


class TestPerformance:
    """Test suite for MAFA performance characteristics."""

    @pytest.fixture
    def temp_config(self):
        """Create a temporary configuration for testing."""
        config_data = {
            "personal_profile": {
                "my_full_name": "Performance Test User",
                "my_profession": "Software Engineer",
                "my_employer": "Test Corp",
                "net_household_income_monthly": 4500,
                "total_occupants": 2,
                "intro_paragraph": "Performance testing user"
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
    def large_listing_dataset(self):
        """Generate a large dataset of listings for performance testing."""
        listings = []
        for i in range(1000):  # 1000 listings
            listings.append({
                "title": f"Test Apartment {i} in Munich 8033{i % 10}",
                "price": f"{1000 + (i % 500)} €",
                "source": "ImmoScout24",
                "timestamp": "2024-01-01T12:00:00",
                "url": f"https://www.immobilienscout24.de/expose/{i}",
                "description": f"Test apartment number {i}",
                "size": f"{50 + (i % 50)} sqm",
                "rooms": 1 + (i % 4)
            })
        return listings

    def test_orchestrator_performance_large_dataset(
        self, temp_config, large_listing_dataset
    ):
        """Test orchestrator performance with large dataset."""
        with patch('mafa.orchestrator.build_providers') as mock_build_providers, \
             patch('mafa.orchestrator.get_metrics_collector') as mock_metrics, \
             patch('mafa.orchestrator.get_health_checker') as mock_health, \
             patch('mafa.orchestrator.Settings.load') as mock_settings:
            
            # Setup mocks
            mock_settings_instance = Mock()
            mock_settings_instance.scrapers = ["immoscout"]
            mock_settings_instance.search_criteria = Mock()
            mock_settings_instance.search_criteria.max_price = 1500
            mock_settings_instance.search_criteria.zip_codes = ["80331", "80333"]
            mock_settings.return_value = mock_settings_instance
            
            mock_health_status = Mock()
            mock_health_status.status = "healthy"
            mock_health_status.issues = []
            mock_health.return_value.get_health_status.return_value = mock_health_status
            
            mock_metrics_instance = Mock()
            mock_metrics.return_value = mock_metrics_instance
            
            # Mock provider with large dataset
            mock_provider = Mock()
            mock_provider.scrape.return_value = large_listing_dataset
            mock_provider.__class__.__name__ = "ImmoScoutProvider"
            mock_build_providers.return_value = [mock_provider]
            
            # Measure performance
            start_time = time.time()
            start_memory = psutil.Process().memory_info().rss
            
            with tempfile.TemporaryDirectory() as temp_dir:
                data_dir = Path(temp_dir) / "data"
                data_dir.mkdir()
                
                with patch('mafa.orchestrator.Path') as mock_path:
                    mock_path.return_value.resolve.return_value.parents[3] = temp_dir
                    
                    run(config_path=temp_config, dry_run=True)
            
            end_time = time.time()
            end_memory = psutil.Process().memory_info().rss
            
            duration = end_time - start_time
            memory_used = end_memory - start_memory
            
            # Performance assertions
            assert duration < 30.0, f"Orchestrator took too long: {duration:.2f}s"
            assert memory_used < 100 * 1024 * 1024, f"Used too much memory: {memory_used / 1024 / 1024:.2f}MB"
            
            # Verify all listings were processed
            assert mock_provider.scrape.call_count == 1
            assert mock_metrics_instance.record_scrape_attempt.call_count >= 1

    def test_concurrent_orchestrator_runs(self, temp_config):
        """Test orchestrator performance with concurrent runs."""
        with patch('mafa.orchestrator.build_providers') as mock_build_providers, \
             patch('mafa.orchestrator.get_metrics_collector') as mock_metrics, \
             patch('mafa.orchestrator.get_health_checker') as mock_health, \
             patch('mafa.orchestrator.Settings.load') as mock_settings:
            
            # Setup mocks
            mock_settings_instance = Mock()
            mock_settings_instance.scrapers = ["immoscout"]
            mock_settings_instance.search_criteria = Mock()
            mock_settings_instance.search_criteria.max_price = 1500
            mock_settings_instance.search_criteria.zip_codes = ["80331", "80333"]
            mock_settings.return_value = mock_settings_instance
            
            mock_health_status = Mock()
            mock_health_status.status = "healthy"
            mock_health_status.issues = []
            mock_health.return_value.get_health_status.return_value = mock_health_status
            
            mock_metrics_instance = Mock()
            mock_metrics.return_value = mock_metrics_instance
            
            # Mock provider
            mock_provider = Mock()
            mock_provider.scrape.return_value = [
                {
                    "title": "Test Apartment",
                    "price": "1.200 €",
                    "source": "ImmoScout24",
                    "timestamp": "2024-01-01T12:00:00"
                }
            ]
            mock_provider.__class__.__name__ = "ImmoScoutProvider"
            mock_build_providers.return_value = [mock_provider]
            
            # Run concurrent orchestrator instances
            def run_orchestrator():
                with tempfile.TemporaryDirectory() as temp_dir:
                    data_dir = Path(temp_dir) / "data"
                    data_dir.mkdir()
                    
                    with patch('mafa.orchestrator.Path') as mock_path:
                        mock_path.return_value.resolve.return_value.parents[3] = temp_dir
                        
                        run(config_path=temp_config, dry_run=True)
            
            # Measure concurrent performance
            start_time = time.time()
            
            with ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(run_orchestrator) for _ in range(5)]
                for future in futures:
                    future.result()  # Wait for completion
            
            end_time = time.time()
            duration = end_time - start_time
            
            # Performance assertions
            assert duration < 60.0, f"Concurrent runs took too long: {duration:.2f}s"
            assert mock_provider.scrape.call_count == 5

    def test_database_performance_bulk_operations(self, large_listing_dataset):
        """Test database performance with bulk operations."""
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test.db"
            
            # Create repository
            repo = ListingRepository(db_path)
            
            # Measure bulk insert performance
            start_time = time.time()
            inserted_count = repo.bulk_add(large_listing_dataset)
            end_time = time.time()
            
            duration = end_time - start_time
            
            # Performance assertions
            assert duration < 10.0, f"Bulk insert took too long: {duration:.2f}s"
            assert inserted_count == len(large_listing_dataset)
            
            # Measure query performance
            start_time = time.time()
            all_listings = repo.get_all_listings()
            end_time = time.time()
            
            duration = end_time - start_time
            assert duration < 5.0, f"Query took too long: {duration:.2f}s"
            assert len(all_listings) == len(large_listing_dataset)

    def test_memory_usage_with_large_configurations(self):
        """Test memory usage with large configuration files."""
        # Create large configuration
        large_config = {
            "personal_profile": {
                "my_full_name": "Test User",
                "my_profession": "Software Engineer",
                "my_employer": "Test Corp",
                "net_household_income_monthly": 4500,
                "total_occupants": 2,
                "intro_paragraph": "Test user"
            },
            "search_criteria": {
                "max_price": 1500,
                "min_rooms": 2,
                "zip_codes": [f"80{str(i).zfill(3)}" for i in range(100)]  # 100 zip codes
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
                "rate_limit_seconds": 1.0,
                "blocked_domains": [f"example{i}.com" for i in range(1000)],  # 1000 blocked domains
                "preferred_contact_methods": ["email", "phone", "form"]
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(large_config, f, indent=2)
            temp_path = Path(f.name)
        
        try:
            # Measure memory usage during config loading
            start_memory = psutil.Process().memory_info().rss
            
            from mafa.config.settings import Settings
            settings = Settings.load(path=temp_path)
            
            end_memory = psutil.Process().memory_info().rss
            memory_used = end_memory - start_memory
            
            # Memory assertions
            assert memory_used < 50 * 1024 * 1024, f"Config loading used too much memory: {memory_used / 1024 / 1024:.2f}MB"
            assert len(settings.search_criteria.zip_codes) == 100
            
        finally:
            if temp_path.exists():
                temp_path.unlink()

    def test_provider_scraping_performance(self):
        """Test provider scraping performance."""
        provider = ImmoScoutProvider()
        
        # Mock the scraping to avoid actual network calls
        with patch.object(provider, '_scrape_listings') as mock_scrape:
            # Simulate scraping response time
            mock_scrape.return_value = [
                {
                    "title": "Test Apartment",
                    "price": "1.200 €",
                    "source": "ImmoScout24",
                    "timestamp": "2024-01-01T12:00:00"
                }
            ]
            
            # Measure scraping performance
            start_time = time.time()
            listings = provider.scrape()
            end_time = time.time()
            
            duration = end_time - start_time
            
            # Performance assertions
            assert duration < 5.0, f"Provider scraping took too long: {duration:.2f}s"
            assert len(listings) == 1

    def test_notification_performance(self, large_listing_dataset):
        """Test notification performance with large datasets."""
        from mafa.notifier.discord import DiscordNotifier
        
        # Create mock settings
        mock_settings = Mock()
        mock_settings.notification.provider = "discord"
        mock_settings.notification.discord_webhook_url = "https://discord.com/api/webhooks/test"
        
        with patch('httpx.post') as mock_post:
            mock_post.return_value = Mock(status_code=200)
            
            notifier = DiscordNotifier(mock_settings)
            
            # Measure notification performance
            start_time = time.time()
            notifier.send_listings(large_listing_dataset)
            end_time = time.time()
            
            duration = end_time - start_time
            
            # Performance assertions
            assert duration < 10.0, f"Notification sending took too long: {duration:.2f}s"
            assert mock_post.call_count == 1

    def test_filtering_performance(self, large_listing_dataset):
        """Test listing filtering performance."""
        from mafa.orchestrator import _filter_listings
        
        # Create mock criteria
        mock_criteria = Mock()
        mock_criteria.max_price = 1500
        mock_criteria.zip_codes = ["80331", "80333", "80335"]
        
        # Measure filtering performance
        start_time = time.time()
        filtered = _filter_listings(large_listing_dataset, mock_criteria)
        end_time = time.time()
        
        duration = end_time - start_time
        
        # Performance assertions
        assert duration < 5.0, f"Filtering took too long: {duration:.2f}s"
        assert len(filtered) > 0, "No listings passed filtering"

    def test_csv_generation_performance(self, large_listing_dataset):
        """Test CSV report generation performance."""
        import csv
        from datetime import datetime
        
        # Measure CSV generation performance
        start_time = time.time()
        
        with tempfile.TemporaryDirectory() as temp_dir:
            data_dir = Path(temp_dir) / "data"
            data_dir.mkdir()
            
            report_path = data_dir / f"report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
            
            with open(report_path, mode="w", newline="", encoding="utf-8") as csvfile:
                fieldnames = ["title", "price", "source", "timestamp"]
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                
                for listing in large_listing_dataset:
                    writer.writerow({
                        "title": listing.get("title", ""),
                        "price": listing.get("price", ""),
                        "source": listing.get("source", ""),
                        "timestamp": listing.get("timestamp", "")
                    })
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Performance assertions
        assert duration < 5.0, f"CSV generation took too long: {duration:.2f}s"
        
        # Verify file was created
        assert report_path.exists(), "CSV file was not created"

    def test_thread_safety(self, temp_config):
        """Test thread safety of orchestrator operations."""
        results = []
        errors = []
        
        def run_orchestrator_thread(thread_id):
            try:
                with patch('mafa.orchestrator.build_providers') as mock_build_providers, \
                     patch('mafa.orchestrator.get_metrics_collector') as mock_metrics, \
                     patch('mafa.orchestrator.get_health_checker') as mock_health, \
                     patch('mafa.orchestrator.Settings.load') as mock_settings:
                    
                    # Setup mocks
                    mock_settings_instance = Mock()
                    mock_settings_instance.scrapers = ["immoscout"]
                    mock_settings_instance.search_criteria = Mock()
                    mock_settings_instance.search_criteria.max_price = 1500
                    mock_settings_instance.search_criteria.zip_codes = ["80331", "80333"]
                    mock_settings.return_value = mock_settings_instance
                    
                    mock_health_status = Mock()
                    mock_health_status.status = "healthy"
                    mock_health_status.issues = []
                    mock_health.return_value.get_health_status.return_value = mock_health_status
                    
                    mock_metrics_instance = Mock()
                    mock_metrics.return_value = mock_metrics_instance
                    
                    # Mock provider
                    mock_provider = Mock()
                    mock_provider.scrape.return_value = [
                        {
                            "title": f"Test Apartment {thread_id}",
                            "price": "1.200 €",
                            "source": "ImmoScout24",
                            "timestamp": "2024-01-01T12:00:00"
                        }
                    ]
                    mock_provider.__class__.__name__ = "ImmoScoutProvider"
                    mock_build_providers.return_value = [mock_provider]
                    
                    with tempfile.TemporaryDirectory() as temp_dir:
                        data_dir = Path(temp_dir) / "data"
                        data_dir.mkdir()
                        
                        with patch('mafa.orchestrator.Path') as mock_path:
                            mock_path.return_value.resolve.return_value.parents[3] = temp_dir
                            
                            run(config_path=temp_config, dry_run=True)
                    
                    results.append(thread_id)
                    
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        # Run multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=run_orchestrator_thread, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Thread safety assertions
        assert len(errors) == 0, f"Thread safety errors: {errors}"
        assert len(results) == 10, f"Expected 10 successful runs, got {len(results)}"