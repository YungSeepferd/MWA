"""Comprehensive tests for MWA Core Scheduler."""

import pytest
import tempfile
import json
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from mwa_core.scheduler import (
    PersistentScheduler, 
    JobManager, 
    JobDefinitions,
    ScrapingJob,
    ContactDiscoveryJob,
    SchedulerConfig,
    JobConfig
)
from mwa_core.scheduler.job_definitions import JobStatus, JobResult, JobPriority
from mwa_core.config import Settings


class TestSchedulerConfig:
    """Test scheduler configuration."""
    
    def test_default_config(self):
        """Test default scheduler configuration."""
        config = SchedulerConfig()
        assert config.enabled is True
        assert config.timezone == "Europe/Berlin"
        assert config.default_max_retries == 3
        assert config.thread_pool_size == 10
    
    def test_job_config_validation(self):
        """Test job configuration validation."""
        # Valid interval job
        job_config = JobConfig(
            id="test_job",
            name="Test Job",
            function="test:function",
            trigger="interval",
            interval_minutes=30
        )
        assert job_config.trigger == "interval"
        assert job_config.interval_minutes == 30
        
        # Valid cron job
        job_config = JobConfig(
            id="test_cron",
            name="Test Cron",
            function="test:function",
            trigger="cron",
            cron_expression="0 9 * * *"
        )
        assert job_config.trigger == "cron"
        assert job_config.cron_expression == "0 9 * * *"
    
    def test_invalid_job_config(self):
        """Test invalid job configuration raises errors."""
        # Interval without interval params
        with pytest.raises(ValueError):
            JobConfig(
                id="invalid_interval",
                name="Invalid Interval",
                function="test:function",
                trigger="interval"
            )
        
        # Cron without cron params
        with pytest.raises(ValueError):
            JobConfig(
                id="invalid_cron",
                name="Invalid Cron",
                function="test:function",
                trigger="cron"
            )


class TestJobDefinitions:
    """Test job definitions and factory."""
    
    def test_scraping_job_creation(self):
        """Test scraping job creation."""
        job = JobDefinitions.create_job(
            job_type="scraping",
            job_id="test_scraping",
            provider="immoscout"
        )
        assert isinstance(job, ScrapingJob)
        assert job.job_id == "test_scraping"
        assert job.provider == "immoscout"
    
    def test_contact_discovery_job_creation(self):
        """Test contact discovery job creation."""
        job = JobDefinitions.create_job(
            job_type="contact_discovery",
            job_id="test_discovery"
        )
        assert isinstance(job, ContactDiscoveryJob)
        assert job.job_id == "test_discovery"
    
    def test_unknown_job_type(self):
        """Test unknown job type raises error."""
        with pytest.raises(ValueError):
            JobDefinitions.create_job(
                job_type="unknown",
                job_id="test_unknown"
            )
    
    def test_default_jobs(self):
        """Test default job configurations."""
        default_jobs = JobDefinitions.get_default_jobs()
        assert len(default_jobs) > 0
        
        # Check for expected job types
        job_ids = [job['id'] for job in default_jobs]
        assert 'immoscout_scraping' in job_ids
        assert 'wg_gesucht_scraping' in job_ids
        assert 'contact_discovery' in job_ids
        assert 'daily_cleanup' in job_ids


class TestJobExecution:
    """Test job execution and results."""
    
    def test_job_result_creation(self):
        """Test job result creation."""
        started_at = datetime.utcnow()
        result = JobResult(
            job_id="test_job",
            status=JobStatus.COMPLETED,
            started_at=started_at,
            execution_time_seconds=10.5
        )
        assert result.job_id == "test_job"
        assert result.status == JobStatus.COMPLETED
        assert result.started_at == started_at
        assert result.execution_time_seconds == 10.5
    
    def test_job_result_with_error(self):
        """Test job result with error."""
        started_at = datetime.utcnow()
        error = Exception("Test error")
        result = JobResult(
            job_id="test_job",
            status=JobStatus.FAILED,
            started_at=started_at,
            error=error
        )
        assert result.status == JobStatus.FAILED
        assert result.error == error


class TestJobManager:
    """Test job manager functionality."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            yield f.name
        Path(f.name).unlink(missing_ok=True)
    
    @pytest.fixture
    def job_manager(self, temp_db):
        """Create job manager with temporary database."""
        config = SchedulerConfig(
            persistence={
                'enabled': True,
                'database_url': f'sqlite:///{temp_db}'
            },
            thread_pool_size=2
        )
        manager = JobManager(config)
        yield manager
        manager.stop(wait=False)
    
    def test_job_manager_initialization(self, job_manager):
        """Test job manager initialization."""
        assert job_manager.config is not None
        assert job_manager.scheduler is not None
        assert job_manager.resource_manager is not None
        assert job_manager.retry_manager is not None
    
    def test_add_remove_job(self, job_manager):
        """Test adding and removing jobs."""
        job = ScrapingJob(job_id="test_scraping", provider="immoscout")
        trigger_config = JobConfig(
            id="test_scraping",
            name="Test Scraping",
            function="test:function",
            trigger="interval",
            interval_minutes=60
        )
        
        # Add job
        assert job_manager.add_job(job, trigger_config) is True
        assert job_manager.get_job("test_scraping") == job
        
        # List jobs
        jobs = job_manager.list_jobs()
        assert len(jobs) == 1
        assert jobs[0]['id'] == "test_scraping"
        
        # Remove job
        assert job_manager.remove_job("test_scraping") is True
        assert job_manager.get_job("test_scraping") is None
    
    def test_job_stats(self, job_manager):
        """Test job statistics tracking."""
        job_id = "test_stats"
        job_manager.job_stats[job_id] = JobExecutionStats()
        
        # Record some executions
        result1 = JobResult(
            job_id=job_id,
            status=JobStatus.COMPLETED,
            started_at=datetime.utcnow(),
            execution_time_seconds=5.0
        )
        result2 = JobResult(
            job_id=job_id,
            status=JobStatus.FAILED,
            started_at=datetime.utcnow(),
            execution_time_seconds=3.0
        )
        
        stats = job_manager.job_stats[job_id]
        stats.record_execution(result1)
        stats.record_execution(result2)
        
        assert stats.total_executions == 2
        assert stats.successful_executions == 1
        assert stats.failed_executions == 1
        assert stats.failure_rate == 0.5
        assert stats.average_execution_time == 4.0
    
    def test_resource_manager(self, job_manager):
        """Test resource manager functionality."""
        resource_manager = job_manager.resource_manager
        
        # Check resources (should pass in test environment)
        result = resource_manager.check_resources()
        assert isinstance(result, bool)
        
        # Get resource usage
        usage = resource_manager.get_resource_usage()
        assert isinstance(usage, dict)
        assert 'cpu_percent' in usage
        assert 'memory_used_mb' in usage
    
    def test_retry_manager(self, job_manager):
        """Test retry manager functionality."""
        retry_manager = job_manager.retry_manager
        
        job_id = "test_retry"
        
        # Should retry initially
        assert retry_manager.should_retry(job_id) is True
        
        # Record retries
        retry_manager.record_retry(job_id)
        assert retry_manager.get_retry_delay(job_id) == 60  # base delay
        
        retry_manager.record_retry(job_id)
        assert retry_manager.get_retry_delay(job_id) == 120  # doubled delay
        
        # Reset retries
        retry_manager.reset_retries(job_id)
        assert retry_manager.get_retry_delay(job_id) == 60  # back to base
    
    def test_system_status(self, job_manager):
        """Test system status reporting."""
        status = job_manager.get_system_status()
        
        assert 'scheduler_running' in status
        assert 'total_jobs' in status
        assert 'resource_usage' in status
        assert 'job_stats' in status


class TestPersistentScheduler:
    """Test persistent scheduler functionality."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            yield f.name
        Path(f.name).unlink(missing_ok=True)
    
    @pytest.fixture
    def scheduler(self, temp_db):
        """Create scheduler with temporary database."""
        config = SchedulerConfig(
            persistence={
                'enabled': True,
                'database_url': f'sqlite:///{temp_db}'
            },
            enabled=True
        )
        scheduler = PersistentScheduler(config)
        yield scheduler
        scheduler.stop(wait=False)
    
    def test_scheduler_initialization(self, scheduler):
        """Test scheduler initialization."""
        assert scheduler.config is not None
        assert scheduler.job_manager is not None
        assert scheduler.config.enabled is True
    
    def test_scheduler_start_stop(self, scheduler):
        """Test scheduler start and stop."""
        # Start scheduler
        scheduler.start()
        assert scheduler.job_manager.scheduler.running is True
        
        # Stop scheduler
        scheduler.stop(wait=False)
        assert scheduler.job_manager.scheduler.running is False
    
    def test_add_custom_job(self, scheduler):
        """Test adding custom job to scheduler."""
        job = ScrapingJob(job_id="custom_test", provider="immoscout")
        trigger_config = {
            'id': 'custom_test',
            'name': 'Custom Test',
            'function': 'test:function',
            'trigger': 'interval',
            'interval_minutes': 30
        }
        
        result = scheduler.add_job(job, trigger_config)
        assert result is True
        
        jobs = scheduler.list_jobs()
        assert len(jobs) == 1
        assert jobs[0]['id'] == 'custom_test'
    
    def test_job_backup_restore(self, scheduler):
        """Test job backup and restore functionality."""
        # Add some jobs first
        job1 = ScrapingJob(job_id="backup_test1", provider="immoscout")
        job2 = ContactDiscoveryJob(job_id="backup_test2")
        
        scheduler.add_job(job1, {
            'id': 'backup_test1',
            'name': 'Backup Test 1',
            'function': 'test:function1',
            'trigger': 'interval',
            'interval_minutes': 60
        })
        
        scheduler.add_job(job2, {
            'id': 'backup_test2',
            'name': 'Backup Test 2',
            'function': 'test:function2',
            'trigger': 'interval',
            'interval_hours': 6
        })
        
        # Backup jobs
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            backup_path = f.name
        
        try:
            backup_file = scheduler.backup_jobs(backup_path)
            assert Path(backup_file).exists()
            
            # Verify backup content
            with open(backup_file, 'r') as f:
                backup_data = json.load(f)
            assert 'jobs' in backup_data
            assert len(backup_data['jobs']) >= 2
            
            # Remove jobs
            scheduler.remove_job('backup_test1')
            scheduler.remove_job('backup_test2')
            
            # Restore jobs
            result = scheduler.restore_jobs(backup_file)
            assert result is True
            
            # Verify jobs were restored
            jobs = scheduler.list_jobs()
            job_ids = [job['id'] for job in jobs]
            assert 'backup_test1' in job_ids
            assert 'backup_test2' in job_ids
            
        finally:
            Path(backup_path).unlink(missing_ok=True)
    
    def test_get_job_stats(self, scheduler):
        """Test getting job statistics."""
        # Add a job
        job = ScrapingJob(job_id="stats_test", provider="immoscout")
        scheduler.add_job(job, {
            'id': 'stats_test',
            'name': 'Stats Test',
            'function': 'test:function',
            'trigger': 'interval',
            'interval_minutes': 60
        })
        
        # Get stats (should be empty initially)
        stats = scheduler.get_job_stats('stats_test')
        assert stats is not None
        assert stats['total_executions'] == 0
        assert stats['successful_executions'] == 0
        assert stats['failed_executions'] == 0
    
    def test_system_status(self, scheduler):
        """Test getting system status."""
        status = scheduler.get_system_status()
        
        assert 'scheduler_running' in status
        assert 'total_jobs' in status
        assert 'resource_usage' in status
        assert 'job_stats' in status


class TestIntegration:
    """Integration tests for scheduler with other components."""
    
    @pytest.fixture
    def temp_db(self):
        """Create temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            yield f.name
        Path(f.name).unlink(missing_ok=True)
    
    @patch('mwa_core.scheduler.job_definitions.get_settings')
    @patch('mwa_core.scheduler.job_definitions.Orchestrator')
    def test_scraping_job_execution(self, mock_orchestrator, mock_get_settings, temp_db):
        """Test scraping job execution with mocked orchestrator."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.get_provider_config.return_value = {
            'headless': True,
            'timeout': 30,
            'max_retries': 3
        }
        mock_get_settings.return_value = mock_settings
        
        # Mock orchestrator
        mock_orch_instance = Mock()
        mock_orch_instance.run.return_value = 5  # 5 new listings
        mock_orchestrator.return_value = mock_orch_instance
        
        # Create scraping job
        job = ScrapingJob(job_id="integration_test", provider="immoscout")
        
        # Execute job
        result = job.execute()
        
        # Verify results
        assert result.status == JobStatus.COMPLETED
        assert result.result_data['new_listings_count'] == 5
        assert result.result_data['provider'] == 'immoscout'
        assert result.execution_time_seconds > 0
        
        # Verify orchestrator was called
        mock_orch_instance.run.assert_called_once_with(
            ['immoscout'],
            mock_settings.get_provider_config.return_value
        )
    
    @patch('mwa_core.scheduler.job_definitions.get_settings')
    @patch('mwa_core.scheduler.job_definitions.discover_contacts_for_listing')
    def test_contact_discovery_job_execution(self, mock_discover_contacts, mock_get_settings, temp_db):
        """Test contact discovery job execution."""
        # Mock settings
        mock_settings = Mock()
        mock_settings.contact_discovery.confidence_threshold = "medium"
        mock_get_settings.return_value = mock_settings
        
        # Mock contact discovery
        mock_discover_contacts.return_value = [
            {'type': 'email', 'value': 'test@example.com', 'confidence': 0.9}
        ]
        
        # Mock storage
        mock_storage = Mock()
        mock_storage.get_listings_without_contacts.return_value = [
            {'id': 1, 'url': 'http://example.com', 'description': 'Test listing'}
        ]
        mock_storage.add_contact.return_value = True
        
        # Create contact discovery job
        job = ContactDiscoveryJob(job_id="discovery_test")
        
        # Execute job with mocked storage
        result = job.execute(storage_manager=mock_storage)
        
        # Verify results
        assert result.status == JobStatus.COMPLETED
        assert result.result_data['discovered_contacts'] == 1
        assert result.result_data['processed_listings'] == 1
        
        # Verify storage methods were called
        mock_storage.get_listings_without_contacts.assert_called_once()
        mock_storage.add_contact.assert_called_once()


def test_cli_integration():
    """Test CLI integration with scheduler."""
    # This would test the CLI commands, but we'll keep it simple for now
    # In a real test, we'd use subprocess or click.testing
    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])