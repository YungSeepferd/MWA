"""
Scraper management Pydantic schemas for MWA Core API.

Provides request/response models for scraper operations including
status monitoring, configuration, manual runs, and performance metrics.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from enum import Enum

from pydantic import BaseModel, Field, validator, root_validator
from .common import (
    PaginationParams, SortParams, DateRange, SearchParams, 
    PaginatedResponse, ExportRequest, SuccessResponse,
    StatisticsResponse, JobStatus
)


# Scraper Status Models
class ScraperStatusResponse(BaseModel):
    """Response model for scraper status."""
    scraper_engine: Dict[str, Any] = Field(..., description="Scraper engine status")
    orchestrator: Dict[str, Any] = Field(..., description="Orchestrator status")
    storage: Dict[str, Any] = Field(..., description="Storage system status")
    last_run: Optional[Dict[str, Any]] = Field(None, description="Last scraping run information")
    active_jobs: List[Dict[str, Any]] = Field(default_factory=list, description="Active scraping jobs")
    total_runs_today: int = Field(..., description="Total runs today")
    total_listings_today: int = Field(..., description="Total listings found today")
    scraper_health: str = Field(..., description="Overall scraper health status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Status check timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "scraper_engine": {
                    "initialized": True,
                    "providers_loaded": 2,
                    "contact_discovery_enabled": True,
                    "active_sessions": 1
                },
                "orchestrator": {
                    "initialized": True,
                    "notification_manager_enabled": True,
                    "running": False
                },
                "storage": {
                    "connected": True,
                    "total_listings": 1250,
                    "total_contacts": 2100
                },
                "last_run": {
                    "id": 456,
                    "provider": "immoscout",
                    "status": "completed",
                    "started_at": "2025-11-19T10:00:00Z",
                    "completed_at": "2025-11-19T10:15:30Z",
                    "listings_found": 25
                },
                "active_jobs": [],
                "total_runs_today": 3,
                "total_listings_today": 75,
                "scraper_health": "healthy",
                "timestamp": "2025-11-19T11:22:26Z"
            }
        }


# Scraper Run Models
class ScraperRunRequest(BaseModel):
    """Request model for starting a scraper run."""
    providers: List[str] = Field(..., min_items=1, description="List of providers to scrape")
    config_overrides: Optional[Dict[str, Any]] = Field(None, description="Configuration overrides")
    notify_on_completion: bool = Field(True, description="Send notifications on completion")
    job_id: Optional[str] = Field(None, description="Optional job ID for tracking")
    priority: str = Field("normal", regex="^(low|normal|high|urgent)$", description="Run priority")
    
    @validator('providers')
    def validate_providers(cls, v):
        valid_providers = ['immoscout', 'wg_gesucht']
        for provider in v:
            if provider not in valid_providers:
                raise ValueError(f'Invalid provider: {provider}. Must be one of: {valid_providers}')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "providers": ["immoscout", "wg_gesucht"],
                "config_overrides": {
                    "request_delay_seconds": 3.0,
                    "timeout_seconds": 45
                },
                "notify_on_completion": True,
                "job_id": "manual_run_001",
                "priority": "high"
            }
        }


class ScraperRunResponse(BaseModel):
    """Response model for scraper run results."""
    run_id: str = Field(..., description="Unique run identifier")
    status: JobStatus = Field(..., description="Run status")
    started_at: datetime = Field(..., description="Run start time")
    completed_at: Optional[datetime] = Field(None, description="Run completion time")
    providers: List[str] = Field(..., description="Providers scraped")
    config_used: Dict[str, Any] = Field(default_factory=dict, description="Configuration used")
    results: Dict[str, Any] = Field(default_factory=dict, description="Scraping results")
    error_details: Optional[List[str]] = Field(None, description="Error details")
    duration_seconds: Optional[float] = Field(None, description="Run duration in seconds")
    performance_metrics: Optional[Dict[str, Any]] = Field(None, description="Performance metrics")
    
    class Config:
        schema_extra = {
            "example": {
                "run_id": "run_20251119_112226",
                "status": "completed",
                "started_at": "2025-11-19T11:22:26Z",
                "completed_at": "2025-11-19T11:25:45Z",
                "providers": ["immoscout", "wg_gesucht"],
                "config_used": {
                    "request_delay_seconds": 2.0,
                    "timeout_seconds": 30
                },
                "results": {
                    "listings_found": 45,
                    "new_listings": 38,
                    "providers": {
                        "immoscout": {
                            "listings": 25,
                            "new": 20,
                            "errors": []
                        },
                        "wg_gesucht": {
                            "listings": 20,
                            "new": 18,
                            "errors": []
                        }
                    }
                },
                "duration_seconds": 199.5,
                "performance_metrics": {
                    "memory_peak_mb": 128.5,
                    "average_response_time": 1.8,
                    "error_rate": 0.02
                }
            }
        }


class ScrapingRunHistory(BaseModel):
    """Historical scraping run information."""
    id: int = Field(..., description="Run ID")
    provider: str = Field(..., description="Scraping provider")
    status: JobStatus = Field(..., description="Run status")
    started_at: datetime = Field(..., description="Start time")
    completed_at: Optional[datetime] = Field(None, description="Completion time")
    listings_found: int = Field(..., description="Number of listings found")
    listings_processed: int = Field(..., description="Number of listings processed")
    duration_seconds: Optional[float] = Field(None, description="Duration in seconds")
    error_count: int = Field(..., description="Number of errors")
    trigger_type: Optional[str] = Field(None, description="What triggered this run")
    
    class Config:
        schema_extra = {
            "example": {
                "id": 456,
                "provider": "immoscout",
                "status": "completed",
                "started_at": "2025-11-19T10:00:00Z",
                "completed_at": "2025-11-19T10:15:30Z",
                "listings_found": 25,
                "listings_processed": 25,
                "duration_seconds": 930.5,
                "error_count": 0,
                "trigger_type": "scheduled"
            }
        }


# Scraper Statistics Models
class ScraperStatisticsResponse(BaseModel):
    """Response model for scraper statistics."""
    total_runs: int = Field(..., description="Total number of runs")
    successful_runs: int = Field(..., description="Number of successful runs")
    failed_runs: int = Field(..., description="Number of failed runs")
    total_listings_scraped: int = Field(..., description="Total listings scraped")
    total_new_listings: int = Field(..., description="Total new listings found")
    run_frequency: Dict[str, Any] = Field(default_factory=dict, description="Run frequency statistics")
    average_runtime: Optional[float] = Field(None, description="Average runtime in seconds")
    success_rate: float = Field(..., description="Success rate percentage")
    top_providers: List[Dict[str, Any]] = Field(default_factory=list, description="Top performing providers")
    recent_activity: List[Dict[str, Any]] = Field(default_factory=list, description="Recent activity")
    timestamp: datetime = Field(default_factory=datetime.now, description="Statistics timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "total_runs": 150,
                "successful_runs": 142,
                "failed_runs": 8,
                "total_listings_scraped": 3750,
                "total_new_listings": 2890,
                "run_frequency": {
                    "runs_per_day": 5.2,
                    "total_days_active": 28,
                    "average_interval_hours": 4.6
                },
                "average_runtime": 245.3,
                "success_rate": 94.7,
                "top_providers": [
                    {
                        "provider": "immoscout",
                        "run_count": 75,
                        "success_rate": 96.0,
                        "total_listings": 2100,
                        "average_runtime": 180.5
                    },
                    {
                        "provider": "wg_gesucht",
                        "run_count": 75,
                        "success_rate": 93.3,
                        "total_listings": 1650,
                        "average_runtime": 310.1
                    }
                ],
                "recent_activity": [
                    {
                        "id": 456,
                        "provider": "immoscout",
                        "status": "completed",
                        "started_at": "2025-11-19T10:00:00Z",
                        "listings_found": 25
                    }
                ],
                "timestamp": "2025-11-19T11:22:26Z"
            }
        }


class ProviderStatistics(BaseModel):
    """Statistics for a specific scraper provider."""
    name: str = Field(..., description="Provider name")
    enabled: bool = Field(..., description="Whether provider is enabled")
    description: str = Field(..., description="Provider description")
    last_run: Optional[datetime] = Field(None, description="Last run time")
    run_count: int = Field(..., description="Total number of runs")
    success_rate: float = Field(..., description="Success rate percentage")
    average_runtime: Optional[float] = Field(None, description="Average runtime in seconds")
    total_listings: int = Field(..., description="Total listings scraped")
    error_rate: float = Field(..., description="Error rate percentage")
    last_error: Optional[str] = Field(None, description="Last error message")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "immoscout",
                "enabled": True,
                "description": "ImmoScout24.de apartment listings",
                "last_run": "2025-11-19T10:00:00Z",
                "run_count": 75,
                "success_rate": 96.0,
                "average_runtime": 180.5,
                "total_listings": 2100,
                "error_rate": 2.1,
                "last_error": None
            }
        }


# Scraper Configuration Models
class ScraperConfigRequest(BaseModel):
    """Request model for updating scraper configuration."""
    providers: Optional[List[str]] = Field(None, description="Enabled providers")
    request_delay_seconds: Optional[float] = Field(None, ge=0.1, le=60.0, description="Delay between requests")
    timeout_seconds: Optional[int] = Field(None, ge=5, le=300, description="Request timeout")
    user_agent: Optional[str] = Field(None, max_length=500, description="User agent string")
    max_retries: Optional[int] = Field(None, ge=0, le=10, description="Maximum retry attempts")
    contact_discovery_enabled: Optional[bool] = Field(None, description="Enable contact discovery")
    contact_discovery_timeout: Optional[int] = Field(None, ge=10, le=120, description="Contact discovery timeout")
    rate_limiting: Optional[Dict[str, Any]] = Field(None, description="Rate limiting configuration")
    proxy_settings: Optional[Dict[str, Any]] = Field(None, description="Proxy configuration")
    
    @validator('providers')
    def validate_providers(cls, v):
        if v:
            valid_providers = ['immoscout', 'wg_gesucht']
            for provider in v:
                if provider not in valid_providers:
                    raise ValueError(f'Invalid provider: {provider}. Must be one of: {valid_providers}')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "providers": ["immoscout", "wg_gesucht"],
                "request_delay_seconds": 2.0,
                "timeout_seconds": 30,
                "user_agent": "MWA-Bot/1.0 (+https://example.com/bot)",
                "max_retries": 3,
                "contact_discovery_enabled": True,
                "contact_discovery_timeout": 60,
                "rate_limiting": {
                    "requests_per_minute": 30,
                    "burst_limit": 5
                },
                "proxy_settings": {
                    "enabled": False,
                    "host": "proxy.example.com",
                    "port": 8080
                }
            }
        }


class ScraperConfigResponse(BaseModel):
    """Response model for scraper configuration."""
    current_config: Dict[str, Any] = Field(..., description="Current configuration")
    updated_fields: List[str] = Field(default_factory=list, description="Fields that were updated")
    validation_warnings: List[str] = Field(default_factory=list, description="Configuration warnings")
    timestamp: datetime = Field(default_factory=datetime.now, description="Update timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "current_config": {
                    "providers": ["immoscout", "wg_gesucht"],
                    "request_delay_seconds": 2.0,
                    "timeout_seconds": 30
                },
                "updated_fields": ["request_delay_seconds", "timeout_seconds"],
                "validation_warnings": [
                    "Consider increasing request delay for better rate limiting"
                ],
                "timestamp": "2025-11-19T11:22:26Z"
            }
        }


# Scraper Test Models
class ScraperTestRequest(BaseModel):
    """Request model for testing scraper configuration."""
    providers: List[str] = Field(..., min_items=1, description="Providers to test")
    config_test: Optional[Dict[str, Any]] = Field(None, description="Test configuration")
    test_type: str = Field("connectivity", regex="^(connectivity|full|dry_run)$", description="Type of test")
    max_pages: Optional[int] = Field(None, ge=1, le=100, description="Maximum pages to test")
    
    class Config:
        schema_extra = {
            "example": {
                "providers": ["immoscout"],
                "config_test": {
                    "request_delay_seconds": 5.0
                },
                "test_type": "connectivity",
                "max_pages": 3
            }
        }


class ScraperTestResult(BaseModel):
    """Result of scraper configuration test."""
    test_id: str = Field(..., description="Unique test identifier")
    providers_tested: List[str] = Field(..., description="Providers tested")
    configuration_valid: bool = Field(..., description="Whether configuration is valid")
    connectivity_tests: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Connectivity test results")
    simulation_results: Dict[str, Any] = Field(default_factory=dict, description="Simulation results")
    recommendations: List[str] = Field(default_factory=list, description="Configuration recommendations")
    test_duration_seconds: float = Field(..., description="Test duration in seconds")
    timestamp: datetime = Field(default_factory=datetime.now, description="Test timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "test_id": "test_20251119_112226",
                "providers_tested": ["immoscout"],
                "configuration_valid": True,
                "connectivity_tests": {
                    "immoscout": {
                        "connection_successful": True,
                        "response_time_ms": 450,
                        "status_code": 200,
                        "server_reachable": True
                    }
                },
                "simulation_results": {
                    "listings_found": 15,
                    "avg_response_time": 2.1,
                    "errors_encountered": 0,
                    "estimated_runtime": 180.0
                },
                "recommendations": [
                    "Configuration looks good",
                    "Consider reducing request delay for better performance"
                ],
                "test_duration_seconds": 45.2,
                "timestamp": "2025-11-19T11:22:26Z"
            }
        }


# Scraper Performance Models
class PerformanceMetrics(BaseModel):
    """Performance metrics for scraper operations."""
    memory_usage_mb: float = Field(..., description="Memory usage in MB")
    cpu_usage_percent: float = Field(..., description="CPU usage percentage")
    network_requests: int = Field(..., description="Number of network requests")
    average_response_time: float = Field(..., description="Average response time in seconds")
    error_rate: float = Field(..., description="Error rate percentage")
    throughput_listings_per_minute: Optional[float] = Field(None, description="Listings processed per minute")
    
    class Config:
        schema_extra = {
            "example": {
                "memory_usage_mb": 128.5,
                "cpu_usage_percent": 35.2,
                "network_requests": 150,
                "average_response_time": 1.8,
                "error_rate": 2.1,
                "throughput_listings_per_minute": 12.5
            }
        }


class ScraperHealthCheck(BaseModel):
    """Health check results for scraper components."""
    component: str = Field(..., description="Component name")
    status: str = Field(..., regex="^(healthy|degraded|unhealthy)$", description="Health status")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    error_message: Optional[str] = Field(None, description="Error message if any")
    last_check: datetime = Field(..., description="Last check timestamp")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional health information")
    
    class Config:
        schema_extra = {
            "example": {
                "component": "immoscout_provider",
                "status": "healthy",
                "response_time_ms": 245.5,
                "error_message": None,
                "last_check": "2025-11-19T11:22:26Z",
                "metadata": {
                    "last_successful_run": "2025-11-19T10:00:00Z",
                    "consecutive_failures": 0
                }
            }
        }


# Scraper Job Management
class ScraperJobRequest(BaseModel):
    """Request model for creating scraper jobs."""
    job_name: str = Field(..., min_length=1, max_length=200, description="Job name")
    providers: List[str] = Field(..., min_items=1, description="Providers to scrape")
    schedule_expression: Optional[str] = Field(None, description="Cron-style schedule expression")
    enabled: bool = Field(True, description="Whether job is enabled")
    job_config: Dict[str, Any] = Field(default_factory=dict, description="Job-specific configuration")
    notification_settings: Optional[Dict[str, Any]] = Field(None, description="Notification settings")
    
    class Config:
        schema_extra = {
            "example": {
                "job_name": "Daily ImmoScout Scrape",
                "providers": ["immoscout"],
                "schedule_expression": "0 9 * * *",
                "enabled": True,
                "job_config": {
                    "max_pages": 20,
                    "delay_range": [1.0, 3.0]
                },
                "notification_settings": {
                    "on_success": True,
                    "on_failure": True,
                    "recipients": ["admin@example.com"]
                }
            }
        }


class ScraperJobResponse(BaseModel):
    """Response model for scraper job information."""
    job_id: str = Field(..., description="Unique job identifier")
    job_name: str = Field(..., description="Job name")
    status: str = Field(..., description="Job status")
    next_run: Optional[datetime] = Field(None, description="Next scheduled run")
    last_run: Optional[datetime] = Field(None, description="Last run time")
    run_count: int = Field(..., description="Number of runs")
    success_count: int = Field(..., description="Number of successful runs")
    failure_count: int = Field(..., description="Number of failed runs")
    job_config: Dict[str, Any] = Field(default_factory=dict, description="Job configuration")
    created_at: datetime = Field(default_factory=datetime.now, description="Job creation time")
    
    class Config:
        schema_extra = {
            "example": {
                "job_id": "job_daily_immoscout",
                "job_name": "Daily ImmoScout Scrape",
                "status": "active",
                "next_run": "2025-11-20T09:00:00Z",
                "last_run": "2025-11-19T09:00:00Z",
                "run_count": 28,
                "success_count": 26,
                "failure_count": 2,
                "job_config": {
                    "providers": ["immoscout"],
                    "max_pages": 20
                },
                "created_at": "2025-10-20T10:00:00Z"
            }
        }


# Scraper Resource Management
class ResourceUsage(BaseModel):
    """Resource usage information."""
    cpu_percent: float = Field(..., description="CPU usage percentage")
    memory_mb: float = Field(..., description="Memory usage in MB")
    disk_io_mb: float = Field(..., description="Disk I/O in MB")
    network_io_mb: float = Field(..., description="Network I/O in MB")
    active_connections: int = Field(..., description="Active network connections")
    
    class Config:
        schema_extra = {
            "example": {
                "cpu_percent": 35.2,
                "memory_mb": 128.5,
                "disk_io_mb": 45.3,
                "network_io_mb": 12.7,
                "active_connections": 5
            }
        }


class RateLimitStatus(BaseModel):
    """Rate limiting status information."""
    provider: str = Field(..., description="Provider name")
    requests_per_minute: int = Field(..., description="Rate limit per minute")
    current_rate: float = Field(..., description="Current request rate")
    remaining_requests: int = Field(..., description="Remaining requests this minute")
    reset_time: datetime = Field(..., description="Rate limit reset time")
    
    class Config:
        schema_extra = {
            "example": {
                "provider": "immoscout",
                "requests_per_minute": 30,
                "current_rate": 15.5,
                "remaining_requests": 14,
                "reset_time": "2025-11-19T11:23:00Z"
            }
        }


# Scraper Error Handling
class ScraperError(BaseModel):
    """Scraper error information."""
    error_id: str = Field(..., description="Unique error identifier")
    provider: str = Field(..., description="Provider where error occurred")
    error_type: str = Field(..., description="Error type")
    error_message: str = Field(..., description="Error message")
    context: Dict[str, Any] = Field(default_factory=dict, description="Error context")
    severity: str = Field(..., regex="^(low|medium|high|critical)$", description="Error severity")
    occurred_at: datetime = Field(..., description="When error occurred")
    resolved: bool = Field(False, description="Whether error has been resolved")
    
    class Config:
        schema_extra = {
            "example": {
                "error_id": "err_20251119_112226_001",
                "provider": "immoscout",
                "error_type": "TimeoutError",
                "error_message": "Request timed out after 30 seconds",
                "context": {
                    "url": "https://immoscout24.de/...",
                    "attempt_number": 2,
                    "retry_delay": 5.0
                },
                "severity": "medium",
                "occurred_at": "2025-11-19T11:22:26Z",
                "resolved": False
            }
        }


class ErrorSummary(BaseModel):
    """Summary of scraper errors."""
    total_errors: int = Field(..., description="Total number of errors")
    errors_by_type: Dict[str, int] = Field(default_factory=dict, description="Errors by type")
    errors_by_provider: Dict[str, int] = Field(default_factory=dict, description="Errors by provider")
    recent_errors: List[ScraperError] = Field(default_factory=list, description="Recent errors")
    error_rate: float = Field(..., description="Error rate percentage")
    timestamp: datetime = Field(default_factory=datetime.now, description="Summary timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "total_errors": 25,
                "errors_by_type": {
                    "TimeoutError": 15,
                    "ConnectionError": 8,
                    "HTTPError": 2
                },
                "errors_by_provider": {
                    "immoscout": 18,
                    "wg_gesucht": 7
                },
                "recent_errors": [],
                "error_rate": 2.1,
                "timestamp": "2025-11-19T11:22:26Z"
            }
        }