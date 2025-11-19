"""
Scheduler management Pydantic schemas for MWA Core API.

Provides request/response models for job scheduler operations including
job management, execution history, and configuration.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field, validator
from .common import (
    PaginationParams, SortParams, DateRange, SearchParams, 
    PaginatedResponse, SuccessResponse, JobStatus
)


# Scheduler Status Models
class SchedulerStatusResponse(BaseModel):
    """Response model for scheduler status."""
    scheduler_running: bool = Field(..., description="Whether scheduler is running")
    job_count: int = Field(..., description="Total number of jobs")
    active_jobs: int = Field(..., description="Number of active jobs")
    next_runs: List[Dict[str, Any]] = Field(default_factory=list, description="Next scheduled runs")
    worker_status: Dict[str, Any] = Field(default_factory=dict, description="Worker status information")
    scheduler_info: Dict[str, Any] = Field(default_factory=dict, description="Scheduler information")
    last_check: datetime = Field(default_factory=datetime.now, description="Status check time")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "scheduler_running": True,
                "job_count": 8,
                "active_jobs": 6,
                "next_runs": [
                    {
                        "job_id": "daily_scrape",
                        "job_name": "Daily Scrape Job",
                        "next_run": "2025-11-20T09:00:00Z"
                    }
                ],
                "worker_status": {
                    "workers": 4,
                    "active": 2,
                    "idle": 2
                },
                "scheduler_info": {
                    "timezone": "Europe/Berlin",
                    "job_store_path": "/data/scheduler/jobs.db",
                    "max_workers": 4
                },
                "last_check": "2025-11-19T11:23:51Z",
                "timestamp": "2025-11-19T11:23:51Z"
            }
        }


# Job Models
class JobInfo(BaseModel):
    """Response model for job information."""
    id: str = Field(..., description="Unique job identifier")
    name: str = Field(..., description="Job name")
    description: Optional[str] = Field(None, description="Job description")
    job_type: str = Field(..., description="Type of job")
    provider: Optional[str] = Field(None, description="Associated provider")
    enabled: bool = Field(..., description="Whether job is enabled")
    next_run: Optional[datetime] = Field(None, description="Next scheduled run")
    last_run: Optional[datetime] = Field(None, description="Last run time")
    run_count: int = Field(..., description="Number of executions")
    failure_count: int = Field(..., description="Number of failures")
    success_count: int = Field(..., description="Number of successful runs")
    status: str = Field(..., description="Current job status")
    schedule_expression: str = Field(..., description="Schedule expression")
    last_status: Optional[str] = Field(None, description="Last execution status")
    average_runtime: Optional[float] = Field(None, description="Average runtime in seconds")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Job metadata")
    created_at: datetime = Field(..., description="Job creation time")
    updated_at: datetime = Field(..., description="Last update time")
    
    class Config:
        schema_extra = {
            "example": {
                "id": "daily_scrape",
                "name": "Daily ImmoScout Scrape",
                "description": "Scrapes ImmoScout24 daily at 9 AM",
                "job_type": "scraping",
                "provider": "immoscout",
                "enabled": True,
                "next_run": "2025-11-20T09:00:00Z",
                "last_run": "2025-11-19T09:00:00Z",
                "run_count": 30,
                "failure_count": 2,
                "success_count": 28,
                "status": "active",
                "schedule_expression": "0 9 * * *",
                "last_status": "completed",
                "average_runtime": 450.5,
                "metadata": {
                    "max_pages": 50,
                    "timeout": 1800
                },
                "created_at": "2025-10-01T10:00:00Z",
                "updated_at": "2025-11-19T09:15:00Z"
            }
        }


class JobCreateRequest(BaseModel):
    """Request model for creating a scheduled job."""
    name: str = Field(..., min_length=1, max_length=200, description="Job name")
    description: Optional[str] = Field(None, max_length=500, description="Job description")
    job_type: str = Field(..., regex="^(scraping|cleanup|backup|notification|maintenance)$", description="Job type")
    provider: Optional[str] = Field(None, regex="^(immoscout|wg_gesucht|all)$", description="Associated provider")
    schedule_expression: str = Field(..., description="Cron-style schedule expression")
    enabled: bool = Field(True, description="Whether job is enabled")
    parameters: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Job parameters")
    timeout_seconds: Optional[int] = Field(None, ge=60, le=3600, description="Job timeout")
    retry_attempts: Optional[int] = Field(3, ge=0, le=10, description="Number of retry attempts")
    retry_delay_seconds: Optional[int] = Field(300, ge=60, le=3600, description="Delay between retries")
    notification_config: Optional[Dict[str, Any]] = Field(None, description="Notification configuration")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Daily ImmoScout Scrape",
                "description": "Scrapes ImmoScout24 daily at 9 AM",
                "job_type": "scraping",
                "provider": "immoscout",
                "schedule_expression": "0 9 * * *",
                "enabled": True,
                "parameters": {
                    "max_pages": 50,
                    "delay_range": [2.0, 5.0]
                },
                "timeout_seconds": 1800,
                "retry_attempts": 3,
                "retry_delay_seconds": 300,
                "notification_config": {
                    "on_success": True,
                    "on_failure": True,
                    "recipients": ["admin@example.com"]
                }
            }
        }


class JobUpdateRequest(BaseModel):
    """Request model for updating a scheduled job."""
    name: Optional[str] = Field(None, min_length=1, max_length=200, description="Job name")
    description: Optional[str] = Field(None, max_length=500, description="Job description")
    schedule_expression: Optional[str] = Field(None, description="Schedule expression")
    enabled: Optional[bool] = Field(None, description="Whether job is enabled")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Job parameters")
    timeout_seconds: Optional[int] = Field(None, ge=60, le=3600, description="Job timeout")
    retry_attempts: Optional[int] = Field(None, ge=0, le=10, description="Number of retry attempts")
    retry_delay_seconds: Optional[int] = Field(None, ge=60, le=3600, description="Delay between retries")
    notification_config: Optional[Dict[str, Any]] = Field(None, description="Notification configuration")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "Updated Daily Scrape",
                "description": "Updated description",
                "schedule_expression": "0 8 * * *",
                "enabled": True,
                "parameters": {
                    "max_pages": 75,
                    "timeout": 2400
                },
                "timeout_seconds": 2400
            }
        }


# Job Execution Models
class JobExecutionResponse(BaseModel):
    """Response model for job execution information."""
    execution_id: str = Field(..., description="Unique execution identifier")
    job_id: str = Field(..., description="Associated job ID")
    job_name: str = Field(..., description="Job name")
    status: JobStatus = Field(..., description="Execution status")
    started_at: datetime = Field(..., description="Execution start time")
    completed_at: Optional[datetime] = Field(None, description="Execution completion time")
    duration_seconds: Optional[float] = Field(None, description="Execution duration")
    result_data: Optional[Dict[str, Any]] = Field(None, description="Execution result data")
    error_details: Optional[str] = Field(None, description="Error details if failed")
    logs: Optional[List[str]] = Field(None, description="Execution logs")
    trigger_type: Optional[str] = Field(None, description="What triggered the execution")
    worker_id: Optional[str] = Field(None, description="Worker that executed the job")
    
    class Config:
        schema_extra = {
            "example": {
                "execution_id": "exec_20251119_112351_001",
                "job_id": "daily_scrape",
                "job_name": "Daily ImmoScout Scrape",
                "status": "completed",
                "started_at": "2025-11-19T09:00:00Z",
                "completed_at": "2025-11-19T09:15:30Z",
                "duration_seconds": 930.5,
                "result_data": {
                    "listings_found": 45,
                    "new_listings": 38,
                    "errors": 0
                },
                "error_details": None,
                "logs": [
                    "Starting daily scrape job",
                    "Provider: immoscout",
                    "Found 45 listings",
                    "Job completed successfully"
                ],
                "trigger_type": "scheduled",
                "worker_id": "worker_2"
            }
        }


class JobExecutionHistory(BaseModel):
    """Historical job execution information."""
    executions: List[JobExecutionResponse] = Field(..., description="List of executions")
    total: int = Field(..., description="Total number of executions")
    limit: int = Field(..., description="Requested limit")
    offset: int = Field(..., description="Requested offset")
    job_id: Optional[str] = Field(None, description="Job ID filter")
    status_filter: Optional[JobStatus] = Field(None, description="Status filter")
    
    class Config:
        schema_extra = {
            "example": {
                "executions": [],
                "total": 30,
                "limit": 20,
                "offset": 0,
                "job_id": "daily_scrape",
                "status_filter": "completed"
            }
        }


# Scheduler Configuration Models
class SchedulerConfigResponse(BaseModel):
    """Response model for scheduler configuration."""
    enabled: bool = Field(..., description="Whether scheduler is enabled")
    timezone: str = Field(..., description="Scheduler timezone")
    job_store_path: str = Field(..., description="Job store file path")
    max_workers: int = Field(..., description="Maximum number of workers")
    job_defaults: Dict[str, Any] = Field(default_factory=dict, description="Default job settings")
    current_config: Dict[str, Any] = Field(..., description="Current configuration")
    job_store_size_mb: Optional[float] = Field(None, description="Job store size in MB")
    database_url: Optional[str] = Field(None, description="Database connection URL")
    
    class Config:
        schema_extra = {
            "example": {
                "enabled": True,
                "timezone": "Europe/Berlin",
                "job_store_path": "/data/scheduler/jobs.db",
                "max_workers": 4,
                "job_defaults": {
                    "max_retries": 3,
                    "retry_delay": 300,
                    "timeout": 1800
                },
                "current_config": {
                    "enabled": True,
                    "timezone": "Europe/Berlin",
                    "max_workers": 4
                },
                "job_store_size_mb": 15.2,
                "database_url": "sqlite:///./data/scheduler.db"
            }
        }


class SchedulerConfigRequest(BaseModel):
    """Request model for updating scheduler configuration."""
    enabled: Optional[bool] = Field(None, description="Whether scheduler is enabled")
    timezone: Optional[str] = Field(None, description="Scheduler timezone")
    max_workers: Optional[int] = Field(None, ge=1, le=20, description="Maximum number of workers")
    job_defaults: Optional[Dict[str, Any]] = Field(None, description="Default job settings")
    
    class Config:
        schema_extra = {
            "example": {
                "enabled": True,
                "timezone": "Europe/Berlin",
                "max_workers": 6,
                "job_defaults": {
                    "max_retries": 5,
                    "retry_delay": 600,
                    "timeout": 3600
                }
            }
        }


# Job Management Models
class JobControlRequest(BaseModel):
    """Request model for job control operations."""
    job_id: str = Field(..., description="Job identifier")
    action: str = Field(..., regex="^(pause|resume|trigger|cancel)$", description="Control action")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Action parameters")
    
    class Config:
        schema_extra = {
            "example": {
                "job_id": "daily_scrape",
                "action": "trigger",
                "parameters": {
                    "force_run": True,
                    "override_schedule": True
                }
            }
        }


class JobControlResponse(BaseModel):
    """Response model for job control operations."""
    success: bool = Field(..., description="Operation success status")
    job_id: str = Field(..., description="Job ID")
    action: str = Field(..., description="Performed action")
    message: str = Field(..., description="Operation message")
    execution_id: Optional[str] = Field(None, description="Created execution ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="Operation timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "job_id": "daily_scrape",
                "action": "trigger",
                "message": "Job triggered successfully",
                "execution_id": "exec_20251119_112351_002",
                "timestamp": "2025-11-19T11:23:51Z"
            }
        }


# Job Templates and Predefined Jobs
class JobTemplate(BaseModel):
    """Predefined job template."""
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    job_type: str = Field(..., description="Job type")
    schedule_expression: str = Field(..., description="Default schedule")
    default_parameters: Dict[str, Any] = Field(default_factory=dict, description="Default parameters")
    template_config: Dict[str, Any] = Field(default_factory=dict, description="Template configuration")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "daily_scraper",
                "description": "Daily scraper job template",
                "job_type": "scraping",
                "schedule_expression": "0 9 * * *",
                "default_parameters": {
                    "timeout": 1800,
                    "max_retries": 3
                },
                "template_config": {
                    "notification_on_success": True,
                    "notification_on_failure": True
                }
            }
        }


class JobStatistics(BaseModel):
    """Job execution statistics."""
    total_jobs: int = Field(..., description="Total number of jobs")
    active_jobs: int = Field(..., description="Number of active jobs")
    paused_jobs: int = Field(..., description="Number of paused jobs")
    total_executions: int = Field(..., description="Total executions")
    successful_executions: int = Field(..., description="Number of successful executions")
    failed_executions: int = Field(..., description="Number of failed executions")
    average_runtime: Optional[float] = Field(None, description="Average runtime in seconds")
    success_rate: float = Field(..., description="Success rate percentage")
    most_active_job: Optional[str] = Field(None, description="Most active job name")
    next_scheduled_runs: List[Dict[str, Any]] = Field(default_factory=list, description="Next scheduled runs")
    recent_failures: List[Dict[str, Any]] = Field(default_factory=list, description="Recent failures")
    timestamp: datetime = Field(default_factory=datetime.now, description="Statistics timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "total_jobs": 8,
                "active_jobs": 6,
                "paused_jobs": 2,
                "total_executions": 450,
                "successful_executions": 425,
                "failed_executions": 25,
                "average_runtime": 380.5,
                "success_rate": 94.4,
                "most_active_job": "daily_scrape",
                "next_scheduled_runs": [
                    {
                        "job_id": "daily_scrape",
                        "next_run": "2025-11-20T09:00:00Z"
                    }
                ],
                "recent_failures": [],
                "timestamp": "2025-11-19T11:23:51Z"
            }
        }


# Job Dependencies and Workflows
class JobDependency(BaseModel):
    """Job dependency definition."""
    dependent_job: str = Field(..., description="Job that depends on another")
    prerequisite_job: str = Field(..., description="Job that must complete first")
    dependency_type: str = Field("completion", regex="^(completion|success|failure)$", description="Dependency type")
    timeout_seconds: Optional[int] = Field(None, description="Dependency timeout")
    
    class Config:
        schema_extra = {
            "example": {
                "dependent_job": "backup_job",
                "prerequisite_job": "daily_scrape",
                "dependency_type": "success",
                "timeout_seconds": 3600
            }
        }


class JobWorkflow(BaseModel):
    """Job workflow definition."""
    workflow_id: str = Field(..., description="Workflow identifier")
    name: str = Field(..., description="Workflow name")
    description: Optional[str] = Field(None, description="Workflow description")
    jobs: List[str] = Field(..., description="List of job IDs in workflow")
    dependencies: List[JobDependency] = Field(default_factory=list, description="Job dependencies")
    enabled: bool = Field(True, description="Whether workflow is enabled")
    
    class Config:
        schema_extra = {
            "example": {
                "workflow_id": "daily_maintenance",
                "name": "Daily Maintenance Workflow",
                "description": "Daily scraping and maintenance workflow",
                "jobs": ["daily_scrape", "cleanup_job", "backup_job"],
                "dependencies": [
                    {
                        "dependent_job": "backup_job",
                        "prerequisite_job": "daily_scrape",
                        "dependency_type": "success"
                    }
                ],
                "enabled": True
            }
        }


# Worker Management
class WorkerInfo(BaseModel):
    """Scheduler worker information."""
    worker_id: str = Field(..., description="Worker identifier")
    status: str = Field(..., regex="^(idle|busy|offline|error)$", description="Worker status")
    current_job: Optional[str] = Field(None, description="Current job being executed")
    jobs_completed: int = Field(..., description="Number of jobs completed")
    jobs_failed: int = Field(..., description="Number of jobs failed")
    last_activity: datetime = Field(..., description="Last activity time")
    worker_config: Dict[str, Any] = Field(default_factory=dict, description="Worker configuration")
    
    class Config:
        schema_extra = {
            "example": {
                "worker_id": "worker_1",
                "status": "idle",
                "current_job": None,
                "jobs_completed": 125,
                "jobs_failed": 3,
                "last_activity": "2025-11-19T11:20:00Z",
                "worker_config": {
                    "max_concurrent_jobs": 1,
                    "timeout": 3600
                }
            }
        }


class WorkerStatistics(BaseModel):
    """Worker performance statistics."""
    total_workers: int = Field(..., description="Total number of workers")
    active_workers: int = Field(..., description="Number of active workers")
    idle_workers: int = Field(..., description="Number of idle workers")
    workers: List[WorkerInfo] = Field(default_factory=list, description="Worker information")
    average_job_duration: float = Field(..., description="Average job duration")
    worker_utilization: Dict[str, float] = Field(default_factory=dict, description="Worker utilization rates")
    timestamp: datetime = Field(default_factory=datetime.now, description="Statistics timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "total_workers": 4,
                "active_workers": 2,
                "idle_workers": 2,
                "workers": [],
                "average_job_duration": 380.5,
                "worker_utilization": {
                    "worker_1": 85.2,
                    "worker_2": 78.9,
                    "worker_3": 0.0,
                    "worker_4": 0.0
                },
                "timestamp": "2025-11-19T11:23:51Z"
            }
        }


# Schedule Management
class SchedulePattern(BaseModel):
    """Predefined schedule patterns."""
    name: str = Field(..., description="Pattern name")
    description: str = Field(..., description="Pattern description")
    cron_expression: str = Field(..., description="Cron expression")
    timezone: str = Field(..., description="Timezone")
    example_next_runs: List[datetime] = Field(..., description="Example next runs")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "daily_9am",
                "description": "Run daily at 9:00 AM",
                "cron_expression": "0 9 * * *",
                "timezone": "Europe/Berlin",
                "example_next_runs": [
                    "2025-11-20T09:00:00Z",
                    "2025-11-21T09:00:00Z",
                    "2025-11-22T09:00:00Z"
                ]
            }
        }


class ScheduleConflict(BaseModel):
    """Schedule conflict information."""
    job_id: str = Field(..., description="Conflicting job ID")
    conflicting_job_id: str = Field(..., description="Job causing conflict")
    conflict_type: str = Field(..., description="Type of conflict")
    severity: str = Field(..., regex="^(low|medium|high)$", description="Conflict severity")
    description: str = Field(..., description="Conflict description")
    suggested_resolution: Optional[str] = Field(None, description="Suggested resolution")
    
    class Config:
        schema_extra = {
            "example": {
                "job_id": "daily_scrape",
                "conflicting_job_id": "backup_job",
                "conflict_type": "resource_contention",
                "severity": "medium",
                "description": "Both jobs scheduled at same time",
                "suggested_resolution": "Stagger scheduling by 30 minutes"
            }
        }


# Job Recovery and Resilience
class JobRecoveryRequest(BaseModel):
    """Request model for job recovery operations."""
    job_id: str = Field(..., description="Job to recover")
    action: str = Field(..., regex="^(retry|skip|reschedule|cancel)$", description="Recovery action")
    execution_id: Optional[str] = Field(None, description="Failed execution ID")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Recovery parameters")
    
    class Config:
        schema_extra = {
            "example": {
                "job_id": "daily_scrape",
                "action": "retry",
                "execution_id": "exec_20251119_112351_003",
                "parameters": {
                    "delay_minutes": 30,
                    "override_timeout": True
                }
            }
        }


class JobRecoveryResponse(BaseModel):
    """Response model for job recovery operations."""
    success: bool = Field(..., description="Recovery success status")
    job_id: str = Field(..., description="Job ID")
    action: str = Field(..., description="Recovery action performed")
    new_execution_id: Optional[str] = Field(None, description="New execution ID")
    message: str = Field(..., description="Recovery message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Recovery timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "job_id": "daily_scrape",
                "action": "retry",
                "new_execution_id": "exec_20251119_112351_004",
                "message": "Job scheduled for retry in 30 minutes",
                "timestamp": "2025-11-19T11:23:51Z"
            }
        }