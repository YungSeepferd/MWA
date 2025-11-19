"""Configuration for MWA Core Scheduler."""

from __future__ import annotations

from typing import List, Literal, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class JobConfig(BaseModel):
    """Configuration for individual scheduled jobs."""
    
    id: str = Field(..., description="Unique job identifier")
    name: str = Field(..., description="Human-readable job name")
    function: str = Field(..., description="Python function path (module:function)")
    trigger: Literal["interval", "cron", "date"] = Field(..., description="Job trigger type")
    
    # Interval trigger parameters
    interval_seconds: Optional[int] = Field(None, ge=1, description="Interval in seconds")
    interval_minutes: Optional[int] = Field(None, ge=1, description="Interval in minutes") 
    interval_hours: Optional[int] = Field(None, ge=1, description="Interval in hours")
    interval_days: Optional[int] = Field(None, ge=1, description="Interval in days")
    
    # Cron trigger parameters
    cron_expression: Optional[str] = Field(None, description="Cron expression (e.g., '0 9 * * *')")
    cron_year: Optional[str] = Field(None, description="Cron year field")
    cron_month: Optional[str] = Field(None, description="Cron month field")
    cron_day: Optional[str] = Field(None, description="Cron day field")
    cron_week: Optional[str] = Field(None, description="Cron week field")
    cron_day_of_week: Optional[str] = Field(None, description="Cron day of week field")
    cron_hour: Optional[str] = Field(None, description="Cron hour field")
    cron_minute: Optional[str] = Field(None, description="Cron minute field")
    cron_second: Optional[str] = Field(None, description="Cron second field")
    
    # Date trigger parameters
    run_date: Optional[datetime] = Field(None, description="Specific date/time to run")
    
    # Job behavior parameters
    max_instances: int = Field(1, ge=1, description="Maximum concurrent instances")
    coalesce: bool = Field(True, description="Coalesce missed executions")
    misfire_grace_time: Optional[int] = Field(None, ge=1, description="Seconds to wait before considering job misfired")
    
    # Retry configuration
    max_retries: int = Field(3, ge=0, description="Maximum retry attempts")
    retry_delay_seconds: int = Field(60, ge=1, description="Delay between retries")
    retry_backoff_multiplier: float = Field(2.0, ge=1.0, description="Backoff multiplier for retries")
    
    # Job-specific parameters
    args: List[Any] = Field(default_factory=list, description="Positional arguments for job function")
    kwargs: Dict[str, Any] = Field(default_factory=dict, description="Keyword arguments for job function")
    
    @validator("trigger")
    def validate_trigger_params(cls, v, values):
        """Validate that required parameters are provided for each trigger type."""
        if v == "interval":
            has_interval = any([
                values.get("interval_seconds"),
                values.get("interval_minutes"), 
                values.get("interval_hours"),
                values.get("interval_days")
            ])
            if not has_interval:
                raise ValueError("Interval trigger requires at least one interval parameter")
        elif v == "cron":
            has_cron = any([
                values.get("cron_expression"),
                any(values.get(f"cron_{field}") for field in ["year", "month", "day", "week", "day_of_week", "hour", "minute", "second"])
            ])
            if not has_cron:
                raise ValueError("Cron trigger requires cron expression or individual cron fields")
        elif v == "date":
            if not values.get("run_date"):
                raise ValueError("Date trigger requires run_date parameter")
        return v


class PersistenceConfig(BaseModel):
    """Configuration for job persistence."""
    
    enabled: bool = Field(True, description="Enable job persistence")
    database_url: str = Field("sqlite:///data/scheduler.db", description="Database URL for job store")
    table_prefix: str = Field("apscheduler_", description="Table prefix for scheduler tables")
    pickle_protocol: int = Field(2, description="Pickle protocol version")


class ResourceConfig(BaseModel):
    """Configuration for resource management."""
    
    max_concurrent_jobs: int = Field(10, ge=1, description="Maximum concurrent jobs")
    max_cpu_percent: float = Field(80.0, ge=1.0, le=100.0, description="Maximum CPU usage percentage")
    max_memory_mb: int = Field(1024, ge=128, description="Maximum memory usage in MB")
    job_timeout_seconds: int = Field(3600, ge=60, description="Maximum job execution time")
    resource_check_interval_seconds: int = Field(30, ge=5, description="Interval for resource checks")


class MonitoringConfig(BaseModel):
    """Configuration for scheduler monitoring."""
    
    enabled: bool = Field(True, description="Enable monitoring")
    metrics_retention_days: int = Field(30, ge=1, description="Days to retain metrics")
    health_check_interval_seconds: int = Field(60, ge=10, description="Health check interval")
    alert_on_job_failure: bool = Field(True, description="Send alerts on job failures")
    alert_on_resource_limit: bool = Field(True, description="Send alerts on resource limit exceeded")


class SchedulerConfig(BaseModel):
    """Main scheduler configuration."""
    
    enabled: bool = Field(True, description="Enable scheduler")
    timezone: str = Field("Europe/Berlin", description="Scheduler timezone")
    
    # Job configurations
    jobs: List[JobConfig] = Field(default_factory=list, description="Scheduled jobs")
    
    # Sub-configurations
    persistence: PersistenceConfig = Field(default_factory=PersistenceConfig)
    resources: ResourceConfig = Field(default_factory=ResourceConfig)
    monitoring: MonitoringConfig = Field(default_factory=MonitoringConfig)
    
    # Threading configuration
    thread_pool_size: int = Field(10, ge=1, description="Thread pool size")
    process_pool_size: int = Field(4, ge=1, description="Process pool size")
    
    # Logging configuration
    log_level: str = Field("INFO", description="Scheduler log level")
    log_job_execution: bool = Field(True, description="Log job execution details")
    log_job_failures: bool = Field(True, description="Log job failures with full details")
    
    # Default job configurations
    default_max_retries: int = Field(3, ge=0, description="Default maximum retries")
    default_retry_delay: int = Field(60, ge=1, description="Default retry delay in seconds")
    default_job_timeout: int = Field(3600, ge=60, description="Default job timeout in seconds")