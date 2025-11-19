"""Persistent scheduler with APScheduler integration for MWA Core."""

from __future__ import annotations

import logging
import signal
import sys
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path

from .config import SchedulerConfig
from .job_manager import JobManager
from .job_definitions import JobDefinitions, BaseJob
from mwa_core.config import get_settings

logger = logging.getLogger(__name__)


class PersistentScheduler:
    """Persistent scheduler with APScheduler integration."""
    
    def __init__(self, config: Optional[SchedulerConfig] = None):
        self.config = config or self._load_config()
        self.job_manager = JobManager(self.config)
        self._setup_signal_handlers()
        self.logger = logging.getLogger(__name__)
        
        # Configure logging
        self._configure_logging()
    
    def _load_config(self) -> SchedulerConfig:
        """Load scheduler configuration from settings."""
        settings = get_settings()
        
        # Try to load scheduler config from settings, use defaults if not found
        scheduler_data = getattr(settings, 'scheduler', {})
        
        if isinstance(scheduler_data, dict) and scheduler_data:
            return SchedulerConfig(**scheduler_data)
        else:
            # Use default configuration
            return SchedulerConfig(
                jobs=[
                    JobConfig(**job_data) 
                    for job_data in JobDefinitions.get_default_jobs()
                ]
            )
    
    def _configure_logging(self):
        """Configure logging for the scheduler."""
        log_level = getattr(logging, self.config.log_level.upper(), logging.INFO)
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        
        # Set specific logger levels
        logging.getLogger('apscheduler').setLevel(log_level)
        logging.getLogger('sqlalchemy').setLevel(logging.WARNING)  # Reduce SQL noise
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            self.logger.info(f"Received signal {signum}, shutting down gracefully...")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def start(self):
        """Start the persistent scheduler."""
        if not self.config.enabled:
            self.logger.warning("Scheduler is disabled in configuration")
            return
        
        self.logger.info("Starting persistent scheduler...")
        
        try:
            # Start job manager
            self.job_manager.start()
            
            # Add default jobs if none are configured
            if not self.config.jobs:
                self._add_default_jobs()
            else:
                self._add_configured_jobs()
            
            self.logger.info("Persistent scheduler started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start scheduler: {e}", exc_info=True)
            raise
    
    def stop(self, wait: bool = True):
        """Stop the persistent scheduler."""
        self.logger.info("Stopping persistent scheduler...")
        
        try:
            self.job_manager.stop(wait=wait)
            self.logger.info("Persistent scheduler stopped successfully")
            
        except Exception as e:
            self.logger.error(f"Error stopping scheduler: {e}", exc_info=True)
    
    def _add_default_jobs(self):
        """Add default jobs to the scheduler."""
        self.logger.info("Adding default jobs...")
        
        default_jobs = JobDefinitions.get_default_jobs()
        
        for job_config in default_jobs:
            try:
                # Create job instance
                job_type = job_config.get('type', 'scraping')
                job_id = job_config['id']
                
                # Extract job-specific parameters
                job_kwargs = {}
                if job_type == 'scraping':
                    job_kwargs['provider'] = job_config.get('provider', 'immoscout')
                
                job = JobDefinitions.create_job(
                    job_type=job_type,
                    job_id=job_id,
                    **job_kwargs
                )
                
                # Create trigger configuration
                from .config import JobConfig
                trigger_config = JobConfig(**job_config)
                
                # Add job to manager
                if self.job_manager.add_job(job, trigger_config):
                    self.logger.info(f"Added default job: {job.name}")
                else:
                    self.logger.error(f"Failed to add default job: {job.name}")
                    
            except Exception as e:
                self.logger.error(f"Error adding default job {job_config.get('id', 'unknown')}: {e}")
    
    def _add_configured_jobs(self):
        """Add jobs from configuration."""
        self.logger.info(f"Adding {len(self.config.jobs)} configured jobs...")
        
        for job_config in self.config.jobs:
            try:
                # Determine job type and create instance
                job_type = self._determine_job_type(job_config)
                
                # Extract job-specific parameters
                job_kwargs = {}
                if job_type == 'scraping':
                    # Extract provider from function path or kwargs
                    if 'provider' in job_config.kwargs:
                        job_kwargs['provider'] = job_config.kwargs['provider']
                    elif 'immoscout' in job_config.function:
                        job_kwargs['provider'] = 'immoscout'
                    elif 'wg_gesucht' in job_config.function:
                        job_kwargs['provider'] = 'wg_gesucht'
                    else:
                        job_kwargs['provider'] = 'immoscout'  # Default
                
                job = JobDefinitions.create_job(
                    job_type=job_type,
                    job_id=job_config.id,
                    **job_kwargs
                )
                
                # Add job to manager
                if self.job_manager.add_job(job, job_config):
                    self.logger.info(f"Added configured job: {job.name}")
                else:
                    self.logger.error(f"Failed to add configured job: {job.name}")
                    
            except Exception as e:
                self.logger.error(f"Error adding configured job {job_config.id}: {e}")
    
    def _determine_job_type(self, job_config: JobConfig) -> str:
        """Determine job type from configuration."""
        # Check function path for job type hints
        if 'scrap' in job_config.function.lower():
            return 'scraping'
        elif 'contact' in job_config.function.lower() or 'discovery' in job_config.function.lower():
            return 'contact_discovery'
        elif 'cleanup' in job_config.function.lower():
            return 'cleanup'
        else:
            # Default to scraping
            return 'scraping'
    
    def add_job(self, job: BaseJob, trigger_config: Dict[str, Any]) -> bool:
        """Add a custom job to the scheduler."""
        try:
            from .config import JobConfig
            config = JobConfig(**trigger_config)
            return self.job_manager.add_job(job, config)
        except Exception as e:
            self.logger.error(f"Failed to add custom job: {e}")
            return False
    
    def remove_job(self, job_id: str) -> bool:
        """Remove a job from the scheduler."""
        return self.job_manager.remove_job(job_id)
    
    def execute_job_now(self, job_id: str) -> bool:
        """Execute a job immediately."""
        return self.job_manager.execute_job_now(job_id)
    
    def list_jobs(self) -> List[Dict[str, Any]]:
        """List all scheduled jobs."""
        return self.job_manager.list_jobs()
    
    def get_job_stats(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get execution statistics for a job."""
        stats = self.job_manager.get_job_stats(job_id)
        if stats:
            return {
                'total_executions': stats.total_executions,
                'successful_executions': stats.successful_executions,
                'failed_executions': stats.failed_executions,
                'failure_rate': stats.failure_rate,
                'average_execution_time': stats.average_execution_time,
                'last_execution_time': stats.last_execution_time.isoformat() if stats.last_execution_time else None,
                'last_success_time': stats.last_success_time.isoformat() if stats.last_success_time else None,
                'last_failure_time': stats.last_failure_time.isoformat() if stats.last_failure_time else None,
            }
        return None
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        return self.job_manager.get_system_status()
    
    def get_job_logs(self, job_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent logs for a job."""
        # This would typically query a log database or file
        # For now, return a placeholder
        return []
    
    def backup_jobs(self, backup_path: Optional[str] = None) -> str:
        """Backup job configurations to a file."""
        if backup_path is None:
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            backup_path = f"data/scheduler_backup_{timestamp}.json"
        
        try:
            backup_data = {
                'timestamp': datetime.utcnow().isoformat(),
                'jobs': [],
                'config': self.config.dict()
            }
            
            # Get job configurations
            for job_info in self.list_jobs():
                job_id = job_info['id']
                job_config = next((j for j in self.config.jobs if j.id == job_id), None)
                if job_config:
                    backup_data['jobs'].append(job_config.dict())
            
            # Write backup file
            Path(backup_path).parent.mkdir(parents=True, exist_ok=True)
            import json
            with open(backup_path, 'w', encoding='utf-8') as f:
                json.dump(backup_data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Jobs backed up to {backup_path}")
            return backup_path
            
        except Exception as e:
            self.logger.error(f"Failed to backup jobs: {e}")
            raise
    
    def restore_jobs(self, backup_path: str) -> bool:
        """Restore job configurations from a backup file."""
        try:
            import json
            with open(backup_path, 'r', encoding='utf-8') as f:
                backup_data = json.load(f)
            
            # Clear existing jobs
            for job in self.list_jobs():
                self.remove_job(job['id'])
            
            # Restore jobs
            restored_count = 0
            for job_config_data in backup_data.get('jobs', []):
                try:
                    from .config import JobConfig
                    job_config = JobConfig(**job_config_data)
                    
                    # Recreate job
                    job_type = self._determine_job_type(job_config)
                    job_kwargs = {}
                    
                    if job_type == 'scraping':
                        # Extract provider
                        if 'provider' in job_config.kwargs:
                            job_kwargs['provider'] = job_config.kwargs['provider']
                        elif 'immoscout' in job_config.function:
                            job_kwargs['provider'] = 'immoscout'
                        elif 'wg_gesucht' in job_config.function:
                            job_kwargs['provider'] = 'wg_gesucht'
                    
                    job = JobDefinitions.create_job(
                        job_type=job_type,
                        job_id=job_config.id,
                        **job_kwargs
                    )
                    
                    if self.job_manager.add_job(job, job_config):
                        restored_count += 1
                        
                except Exception as e:
                    self.logger.error(f"Failed to restore job {job_config_data.get('id', 'unknown')}: {e}")
                    continue
            
            self.logger.info(f"Restored {restored_count} jobs from backup")
            return restored_count > 0
            
        except Exception as e:
            self.logger.error(f"Failed to restore jobs from {backup_path}: {e}")
            return False


# Global scheduler instance
_scheduler_instance = None


def get_scheduler(config: Optional[SchedulerConfig] = None) -> PersistentScheduler:
    """Get or create the global scheduler instance."""
    global _scheduler_instance
    if _scheduler_instance is None:
        _scheduler_instance = PersistentScheduler(config)
    return _scheduler_instance


def start_scheduler(config: Optional[SchedulerConfig] = None) -> PersistentScheduler:
    """Start the global scheduler instance."""
    scheduler = get_scheduler(config)
    scheduler.start()
    return scheduler


def stop_scheduler(wait: bool = True):
    """Stop the global scheduler instance."""
    global _scheduler_instance
    if _scheduler_instance:
        _scheduler_instance.stop(wait=wait)
        _scheduler_instance = None