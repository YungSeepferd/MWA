"""Job manager for MWA Core Scheduler with failure handling and retries."""

from __future__ import annotations

import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from concurrent.futures import ThreadPoolExecutor, as_completed
import psutil

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.pool import ThreadPoolExecutor as APThreadPoolExecutor
from apscheduler.events import (
    EVENT_JOB_EXECUTED, EVENT_JOB_ERROR, EVENT_JOB_MISSED,
    EVENT_JOB_SUBMITTED, EVENT_JOB_REMOVED
)

from .config import SchedulerConfig, JobConfig
from .job_definitions import BaseJob, JobResult, JobStatus, JobDefinitions
from mwa_core.config import get_settings

logger = logging.getLogger(__name__)


class JobExecutionStats:
    """Statistics for job execution."""
    
    def __init__(self):
        self.total_executions = 0
        self.successful_executions = 0
        self.failed_executions = 0
        self.total_execution_time = 0.0
        self.average_execution_time = 0.0
        self.last_execution_time = None
        self.last_success_time = None
        self.last_failure_time = None
        self.failure_rate = 0.0
    
    def record_execution(self, result: JobResult):
        """Record job execution result."""
        self.total_executions += 1
        self.last_execution_time = result.completed_at or datetime.utcnow()
        self.total_execution_time += result.execution_time_seconds or 0.0
        
        if result.status == JobStatus.COMPLETED:
            self.successful_executions += 1
            self.last_success_time = self.last_execution_time
        else:
            self.failed_executions += 1
            self.last_failure_time = self.last_execution_time
        
        # Calculate average execution time
        if self.total_executions > 0:
            self.average_execution_time = self.total_execution_time / self.total_executions
        
        # Calculate failure rate
        if self.total_executions > 0:
            self.failure_rate = self.failed_executions / self.total_executions


class ResourceManager:
    """Manages system resources for job execution."""
    
    def __init__(self, config: ResourceConfig):
        self.config = config
        self.logger = logging.getLogger(f"{__name__}.ResourceManager")
    
    def check_resources(self) -> bool:
        """Check if system has sufficient resources for job execution."""
        try:
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > self.config.max_cpu_percent:
                self.logger.warning(f"CPU usage too high: {cpu_percent}% > {self.config.max_cpu_percent}%")
                return False
            
            # Check memory usage
            memory = psutil.virtual_memory()
            memory_used_mb = memory.used / (1024 * 1024)
            if memory_used_mb > self.config.max_memory_mb:
                self.logger.warning(f"Memory usage too high: {memory_used_mb:.1f}MB > {self.config.max_memory_mb}MB")
                return False
            
            # Check if we're at max concurrent jobs
            # This will be managed by the scheduler's max_instances, but we can add additional logic here
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error checking system resources: {e}")
            return False  # Fail safe
    
    def get_resource_usage(self) -> Dict[str, Any]:
        """Get current resource usage statistics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                "cpu_percent": cpu_percent,
                "memory_used_mb": memory.used / (1024 * 1024),
                "memory_total_mb": memory.total / (1024 * 1024),
                "memory_percent": memory.percent,
                "disk_used_gb": disk.used / (1024 * 1024 * 1024),
                "disk_total_gb": disk.total / (1024 * 1024 * 1024),
                "disk_percent": disk.percent,
            }
        except Exception as e:
            self.logger.error(f"Error getting resource usage: {e}")
            return {}


class RetryManager:
    """Manages job retry logic with exponential backoff."""
    
    def __init__(self, max_retries: int = 3, base_delay: int = 60, backoff_multiplier: float = 2.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.backoff_multiplier = backoff_multiplier
        self.retry_counts: Dict[str, int] = {}
        self.logger = logging.getLogger(f"{__name__}.RetryManager")
    
    def should_retry(self, job_id: str) -> bool:
        """Determine if a job should be retried."""
        retry_count = self.retry_counts.get(job_id, 0)
        return retry_count < self.max_retries
    
    def get_retry_delay(self, job_id: str) -> int:
        """Get delay before next retry with exponential backoff."""
        retry_count = self.retry_counts.get(job_id, 0)
        delay = self.base_delay * (self.backoff_multiplier ** retry_count)
        return int(delay)
    
    def record_retry(self, job_id: str):
        """Record a retry attempt."""
        self.retry_counts[job_id] = self.retry_counts.get(job_id, 0) + 1
        self.logger.info(f"Job {job_id} retry count: {self.retry_counts[job_id]}")
    
    def reset_retries(self, job_id: str):
        """Reset retry count for a job."""
        if job_id in self.retry_counts:
            del self.retry_counts[job_id]
            self.logger.info(f"Reset retry count for job {job_id}")


class JobManager:
    """Manages job execution with failure handling and retries."""
    
    def __init__(self, config: SchedulerConfig):
        self.config = config
        self.scheduler = None
        self.job_stats: Dict[str, JobExecutionStats] = {}
        self.resource_manager = ResourceManager(config.resources)
        self.retry_manager = RetryManager(
            max_retries=config.default_max_retries,
            base_delay=config.default_retry_delay,
            backoff_multiplier=2.0
        )
        self.job_definitions: Dict[str, BaseJob] = {}
        self.executor = ThreadPoolExecutor(max_workers=config.thread_pool_size)
        self.logger = logging.getLogger(__name__)
        self._shutdown = False
        self._lock = threading.Lock()
        
        # Initialize scheduler
        self._initialize_scheduler()
    
    def _initialize_scheduler(self):
        """Initialize APScheduler with configuration."""
        # Configure job stores
        jobstores = {}
        if self.config.persistence.enabled:
            jobstores['default'] = SQLAlchemyJobStore(
                url=self.config.persistence.database_url,
                tablename=f"{self.config.persistence.table_prefix}jobs"
            )
        else:
            from apscheduler.jobstores.memory import MemoryJobStore
            jobstores['default'] = MemoryJobStore()
        
        # Configure executors
        executors = {
            'default': APThreadPoolExecutor(
                max_workers=self.config.thread_pool_size,
                pool_kwargs={'thread_name_prefix': 'APScheduler'}
            )
        }
        
        # Configure job defaults
        job_defaults = {
            'coalesce': True,
            'max_instances': 1,
            'misfire_grace_time': 300  # 5 minutes
        }
        
        # Create scheduler
        self.scheduler = BackgroundScheduler(
            jobstores=jobstores,
            executors=executors,
            job_defaults=job_defaults,
            timezone=self.config.timezone
        )
        
        # Add event listeners
        self.scheduler.add_listener(
            self._job_executed_listener,
            EVENT_JOB_EXECUTED | EVENT_JOB_ERROR
        )
        self.scheduler.add_listener(
            self._job_submitted_listener,
            EVENT_JOB_SUBMITTED
        )
        
        self.logger.info("Scheduler initialized successfully")
    
    def start(self):
        """Start the scheduler."""
        if not self.config.enabled:
            self.logger.warning("Scheduler is disabled in configuration")
            return
        
        with self._lock:
            if self.scheduler and not self.scheduler.running:
                self.scheduler.start()
                self.logger.info("Scheduler started")
    
    def stop(self, wait: bool = True):
        """Stop the scheduler."""
        with self._lock:
            self._shutdown = True
            if self.scheduler and self.scheduler.running:
                self.scheduler.shutdown(wait=wait)
                self.logger.info("Scheduler stopped")
            
            # Shutdown executor
            self.executor.shutdown(wait=wait)
    
    def add_job(self, job: BaseJob, trigger_config: JobConfig) -> bool:
        """Add a job to the scheduler."""
        try:
            # Store job definition
            self.job_definitions[job.job_id] = job
            
            # Initialize stats
            self.job_stats[job.job_id] = JobExecutionStats()
            
            # Create APScheduler job
            self.scheduler.add_job(
                func=self._execute_job_wrapper,
                trigger=self._create_trigger(trigger_config),
                id=job.job_id,
                name=job.name,
                args=[job.job_id],
                max_instances=trigger_config.max_instances,
                coalesce=trigger_config.coalesce,
                misfire_grace_time=trigger_config.misfire_grace_time,
                replace_existing=True
            )
            
            self.logger.info(f"Job {job.job_id} added to scheduler")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to add job {job.job_id}: {e}", exc_info=True)
            return False
    
    def remove_job(self, job_id: str) -> bool:
        """Remove a job from the scheduler."""
        try:
            self.scheduler.remove_job(job_id)
            # Clean up stats and definitions
            self.job_stats.pop(job_id, None)
            self.job_definitions.pop(job_id, None)
            self.retry_manager.reset_retries(job_id)
            
            self.logger.info(f"Job {job_id} removed from scheduler")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to remove job {job_id}: {e}")
            return False
    
    def get_job(self, job_id: str) -> Optional[BaseJob]:
        """Get job definition by ID."""
        return self.job_definitions.get(job_id)
    
    def list_jobs(self) -> List[Dict[str, Any]]:
        """List all scheduled jobs."""
        jobs = []
        for job in self.scheduler.get_jobs():
            job_info = {
                'id': job.id,
                'name': job.name,
                'next_run_time': job.next_run_time,
                'trigger': str(job.trigger),
                'max_instances': job.max_instances,
                'coalesce': job.coalesce,
            }
            
            # Add stats if available
            if job.id in self.job_stats:
                stats = self.job_stats[job.id]
                job_info['stats'] = {
                    'total_executions': stats.total_executions,
                    'successful_executions': stats.successful_executions,
                    'failed_executions': stats.failed_executions,
                    'failure_rate': stats.failure_rate,
                    'average_execution_time': stats.average_execution_time,
                    'last_execution_time': stats.last_execution_time,
                }
            
            jobs.append(job_info)
        
        return jobs
    
    def get_job_stats(self, job_id: str) -> Optional[JobExecutionStats]:
        """Get execution statistics for a job."""
        return self.job_stats.get(job_id)
    
    def execute_job_now(self, job_id: str) -> bool:
        """Execute a job immediately."""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                job.modify(next_run_time=datetime.utcnow())
                self.logger.info(f"Job {job_id} scheduled for immediate execution")
                return True
            else:
                self.logger.warning(f"Job {job_id} not found")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to execute job {job_id} immediately: {e}")
            return False
    
    def _execute_job_wrapper(self, job_id: str):
        """Wrapper for job execution with error handling and retries."""
        if self._shutdown:
            self.logger.warning(f"Skipping job {job_id} - scheduler is shutting down")
            return
        
        # Check resources
        if not self.resource_manager.check_resources():
            self.logger.warning(f"Insufficient resources to execute job {job_id}")
            # Reschedule for later
            self._reschedule_job(job_id, delay=300)  # 5 minutes
            return
        
        job = self.job_definitions.get(job_id)
        if not job:
            self.logger.error(f"Job definition not found for {job_id}")
            return
        
        try:
            self.logger.info(f"Executing job {job_id}")
            
            # Execute the job
            result = job.execute()
            
            # Record stats
            if job_id in self.job_stats:
                self.job_stats[job_id].record_execution(result)
            
            # Handle result
            if result.status == JobStatus.COMPLETED:
                self.logger.info(f"Job {job_id} completed successfully")
                self.retry_manager.reset_retries(job_id)
                
                # Log detailed results if configured
                if self.config.log_job_execution and result.result_data:
                    self.logger.info(f"Job {job_id} result: {result.result_data}")
                    
            else:
                self.logger.error(f"Job {job_id} failed: {result.error}")
                self._handle_job_failure(job_id, result)
                
        except Exception as e:
            self.logger.error(f"Unexpected error executing job {job_id}: {e}", exc_info=True)
            
            # Create a failed result
            result = JobResult(
                job_id=job_id,
                status=JobStatus.FAILED,
                started_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
                error=e
            )
            
            self._handle_job_failure(job_id, result)
    
    def _handle_job_failure(self, job_id: str, result: JobResult):
        """Handle job failure with retry logic."""
        if self.retry_manager.should_retry(job_id):
            retry_delay = self.retry_manager.get_retry_delay(job_id)
            self.retry_manager.record_retry(job_id)
            
            self.logger.info(f"Retrying job {job_id} in {retry_delay} seconds")
            self._reschedule_job(job_id, delay=retry_delay)
        else:
            self.logger.error(f"Job {job_id} failed after maximum retries")
            # Could send alert notification here
    
    def _reschedule_job(self, job_id: str, delay: int):
        """Reschedule a job for later execution."""
        try:
            job = self.scheduler.get_job(job_id)
            if job:
                new_time = datetime.utcnow() + timedelta(seconds=delay)
                job.modify(next_run_time=new_time)
                self.logger.info(f"Job {job_id} rescheduled for {new_time}")
        except Exception as e:
            self.logger.error(f"Failed to reschedule job {job_id}: {e}")
    
    def _create_trigger(self, config: JobConfig):
        """Create APScheduler trigger from configuration."""
        from apscheduler.triggers.interval import IntervalTrigger
        from apscheduler.triggers.cron import CronTrigger
        from apscheduler.triggers.date import DateTrigger
        
        if config.trigger == "interval":
            return IntervalTrigger(
                seconds=config.interval_seconds or 0,
                minutes=config.interval_minutes or 0,
                hours=config.interval_hours or 0,
                days=config.interval_days or 0,
                timezone=self.config.timezone
            )
        
        elif config.trigger == "cron":
            if config.cron_expression:
                return CronTrigger.from_crontab(
                    config.cron_expression,
                    timezone=self.config.timezone
                )
            else:
                return CronTrigger(
                    year=config.cron_year,
                    month=config.cron_month,
                    day=config.cron_day,
                    week=config.cron_week,
                    day_of_week=config.cron_day_of_week,
                    hour=config.cron_hour,
                    minute=config.cron_minute,
                    second=config.cron_second,
                    timezone=self.config.timezone
                )
        
        elif config.trigger == "date":
            return DateTrigger(
                run_date=config.run_date,
                timezone=self.config.timezone
            )
        
        else:
            raise ValueError(f"Unsupported trigger type: {config.trigger}")
    
    def _job_executed_listener(self, event):
        """Listener for job execution events."""
        job_id = event.job_id
        if event.exception:
            self.logger.error(f"Job {job_id} failed with exception: {event.exception}")
        else:
            self.logger.info(f"Job {job_id} executed successfully")
    
    def _job_submitted_listener(self, event):
        """Listener for job submission events."""
        job_id = event.job_id
        self.logger.debug(f"Job {job_id} submitted for execution")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get overall system status."""
        return {
            "scheduler_running": self.scheduler.running if self.scheduler else False,
            "total_jobs": len(self.job_definitions),
            "resource_usage": self.resource_manager.get_resource_usage(),
            "job_stats": {
                job_id: {
                    "total_executions": stats.total_executions,
                    "successful_executions": stats.successful_executions,
                    "failed_executions": stats.failed_executions,
                    "failure_rate": stats.failure_rate,
                    "average_execution_time": stats.average_execution_time,
                    "last_execution_time": stats.last_execution_time.isoformat() if stats.last_execution_time else None,
                }
                for job_id, stats in self.job_stats.items()
            }
        }