"""
System status and health check Pydantic schemas for MWA Core API.

Provides request/response models for system monitoring, health checks,
performance metrics, error reporting, and logging.
"""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from enum import Enum
import platform

from pydantic import BaseModel, Field, validator
from .common import (
    PaginationParams, SortParams, DateRange, SearchParams, 
    PaginatedResponse, SuccessResponse, ErrorResponse
)


# Health Check Models
class HealthCheckResponse(BaseModel):
    """Response model for health check."""
    status: str = Field(..., pattern="^(healthy|degraded|unhealthy)$", description="Overall health status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Check timestamp")
    service: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    uptime_seconds: Optional[float] = Field(None, description="System uptime in seconds")
    dependencies: Dict[str, str] = Field(default_factory=dict, description="Dependency health status")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional health details")
    
    class Config:
        schema_extra = {
            "example": {
                "status": "healthy",
                "timestamp": "2025-11-19T11:25:18Z",
                "service": "MWA Core API",
                "version": "1.0.0",
                "uptime_seconds": 86400.5,
                "dependencies": {
                    "database": "healthy",
                    "storage": "healthy",
                    "scraper": "healthy"
                },
                "details": {
                    "memory_usage": "65%",
                    "cpu_usage": "25%",
                    "active_connections": 15
                }
            }
        }


class ComponentHealth(BaseModel):
    """Health status of a system component."""
    name: str = Field(..., description="Component name")
    status: str = Field(..., pattern="^(healthy|degraded|unhealthy)$", description="Component status")
    healthy: bool = Field(..., description="Whether component is healthy")
    last_check: datetime = Field(default_factory=datetime.now, description="Last check timestamp")
    response_time_ms: Optional[float] = Field(None, description="Response time in milliseconds")
    error_message: Optional[str] = Field(None, description="Error message if unhealthy")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional component data")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "database",
                "status": "healthy",
                "healthy": True,
                "last_check": "2025-11-19T11:25:18Z",
                "response_time_ms": 45.2,
                "error_message": None,
                "metadata": {
                    "connection_pool_size": 20,
                    "active_connections": 5,
                    "database_size_mb": 1250.5
                }
            }
        }


# System Information Models
class SystemInfoResponse(BaseModel):
    """Response model for system information."""
    application: Dict[str, str] = Field(..., description="Application information")
    system: Dict[str, Any] = Field(..., description="System information")
    environment: Dict[str, Any] = Field(..., description="Environment information")
    configuration: Dict[str, Any] = Field(..., description="Configuration summary")
    components: Dict[str, Any] = Field(..., description="Component information")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "application": {
                    "name": "MWA Core API",
                    "version": "1.0.0",
                    "description": "Munich Apartment Finder Assistant Core API",
                    "startup_time": "2025-11-19T10:00:00Z",
                    "uptime_seconds": 5118.5
                },
                "system": {
                    "platform": "darwin",
                    "python_version": "3.11.0",
                    "cpu_count": 8,
                    "memory_total": 17179869184,
                    "disk_total": 1000000000000,
                    "boot_time": "2025-11-19T06:30:00Z"
                },
                "environment": {
                    "config_path": "/path/to/config.json",
                    "data_directory": "/data/",
                    "log_level": "INFO",
                    "timezone": "Europe/Berlin"
                },
                "configuration": {
                    "scraper_enabled": ["immoscout", "wg_gesucht"],
                    "scheduler_enabled": True,
                    "contact_discovery": True,
                    "storage_path": "/data/mwa_core.db"
                },
                "components": {
                    "settings": {"status": "loaded", "healthy": True},
                    "storage": {"status": "connected", "healthy": True}
                },
                "timestamp": "2025-11-19T11:25:18Z"
            }
        }


class ApplicationInfo(BaseModel):
    """Application information details."""
    name: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")
    description: Optional[str] = Field(None, description="Application description")
    build_info: Dict[str, str] = Field(default_factory=dict, description="Build information")
    environment: str = Field(..., description="Environment name")
    startup_time: datetime = Field(..., description="Application startup time")
    
    class Config:
        schema_extra = {
            "example": {
                "name": "MWA Core API",
                "version": "1.0.0",
                "description": "Munich Apartment Finder Assistant Core API",
                "build_info": {
                    "build_date": "2025-11-19",
                    "git_commit": "abc123def",
                    "build_number": "42"
                },
                "environment": "production",
                "startup_time": "2025-11-19T10:00:00Z"
            }
        }


class SystemSpecs(BaseModel):
    """System specification information."""
    platform: str = Field(..., description="Operating system platform")
    architecture: str = Field(..., description="System architecture")
    python_version: str = Field(..., description="Python version")
    cpu_count: int = Field(..., description="Number of CPU cores")
    memory_total: int = Field(..., description="Total memory in bytes")
    disk_total: int = Field(..., description="Total disk space in bytes")
    boot_time: datetime = Field(..., description="System boot time")
    hostname: str = Field(..., description="System hostname")
    
    class Config:
        schema_extra = {
            "example": {
                "platform": "darwin",
                "architecture": "x86_64",
                "python_version": "3.11.0",
                "cpu_count": 8,
                "memory_total": 17179869184,
                "disk_total": 1000000000000,
                "boot_time": "2025-11-19T06:30:00Z",
                "hostname": "mwa-server-01"
            }
        }


# Performance Metrics Models
class PerformanceMetricsResponse(BaseModel):
    """Response model for performance metrics."""
    cpu: Dict[str, float] = Field(..., description="CPU metrics")
    memory: Dict[str, float] = Field(..., description="Memory metrics")
    disk: Dict[str, float] = Field(..., description="Disk metrics")
    network: Dict[str, float] = Field(..., description="Network metrics")
    database: Dict[str, Any] = Field(default_factory=dict, description="Database metrics")
    application: Dict[str, Any] = Field(default_factory=dict, description="Application metrics")
    timestamp: datetime = Field(default_factory=datetime.now, description="Metrics timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "cpu": {
                    "usage_percent": 25.5,
                    "count": 8,
                    "load_average": 1.2
                },
                "memory": {
                    "total": 17179869184,
                    "available": 8584934592,
                    "percent": 50.0,
                    "used": 8584934592
                },
                "disk": {
                    "total": 1000000000000,
                    "used": 500000000000,
                    "free": 500000000000,
                    "percent": 50.0
                },
                "network": {
                    "bytes_sent": 1048576,
                    "bytes_recv": 2097152,
                    "packets_sent": 1000,
                    "packets_recv": 2000
                },
                "database": {
                    "total_listings": 1250,
                    "total_contacts": 2100,
                    "status": "connected"
                },
                "application": {
                    "uptime_seconds": 5118.5,
                    "active_requests": 15,
                    "requests_per_minute": 45.0
                },
                "timestamp": "2025-11-19T11:25:18Z"
            }
        }


class CPUMetrics(BaseModel):
    """CPU performance metrics."""
    usage_percent: float = Field(..., description="CPU usage percentage")
    count: int = Field(..., description="Number of CPU cores")
    load_average: Optional[float] = Field(None, description="1-minute load average")
    load_average_5min: Optional[float] = Field(None, description="5-minute load average")
    load_average_15min: Optional[float] = Field(None, description="15-minute load average")
    frequency_mhz: Optional[float] = Field(None, description="CPU frequency in MHz")
    
    class Config:
        schema_extra = {
            "example": {
                "usage_percent": 25.5,
                "count": 8,
                "load_average": 1.2,
                "load_average_5min": 1.5,
                "load_average_15min": 1.8,
                "frequency_mhz": 2400.0
            }
        }


class MemoryMetrics(BaseModel):
    """Memory performance metrics."""
    total: int = Field(..., description="Total memory in bytes")
    available: int = Field(..., description="Available memory in bytes")
    used: int = Field(..., description="Used memory in bytes")
    percent: float = Field(..., description="Memory usage percentage")
    cached: Optional[int] = Field(None, description="Cached memory in bytes")
    shared: Optional[int] = Field(None, description="Shared memory in bytes")
    
    class Config:
        schema_extra = {
            "example": {
                "total": 17179869184,
                "available": 8584934592,
                "used": 8584934592,
                "percent": 50.0,
                "cached": 2147483648,
                "shared": 1073741824
            }
        }


class DiskMetrics(BaseModel):
    """Disk performance metrics."""
    total: int = Field(..., description="Total disk space in bytes")
    used: int = Field(..., description="Used disk space in bytes")
    free: int = Field(..., description="Free disk space in bytes")
    percent: float = Field(..., description="Disk usage percentage")
    read_bytes_per_sec: Optional[int] = Field(None, description="Read throughput")
    write_bytes_per_sec: Optional[int] = Field(None, description="Write throughput")
    
    class Config:
        schema_extra = {
            "example": {
                "total": 1000000000000,
                "used": 500000000000,
                "free": 500000000000,
                "percent": 50.0,
                "read_bytes_per_sec": 104857600,
                "write_bytes_per_sec": 52428800
            }
        }


class NetworkMetrics(BaseModel):
    """Network performance metrics."""
    bytes_sent: int = Field(..., description="Bytes sent")
    bytes_recv: int = Field(..., description="Bytes received")
    packets_sent: int = Field(..., description="Packets sent")
    packets_recv: int = Field(..., description="Packets received")
    errors_in: Optional[int] = Field(None, description="Input errors")
    errors_out: Optional[int] = Field(None, description="Output errors")
    
    class Config:
        schema_extra = {
            "example": {
                "bytes_sent": 1048576,
                "bytes_recv": 2097152,
                "packets_sent": 1000,
                "packets_recv": 2000,
                "errors_in": 0,
                "errors_out": 0
            }
        }


# Error Reporting Models
class ErrorReportRequest(BaseModel):
    """Request model for error reporting."""
    error_type: str = Field(..., min_length=1, description="Type of error")
    error_message: str = Field(..., min_length=1, description="Error message")
    component: str = Field(..., min_length=1, description="Component where error occurred")
    context: Optional[Dict[str, Any]] = Field(None, description="Error context")
    severity: str = Field("error", pattern="^(info|warning|error|critical)$", description="Error severity")
    stack_trace: Optional[str] = Field(None, description="Stack trace if available")
    user_agent: Optional[str] = Field(None, description="User agent string")
    
    class Config:
        schema_extra = {
            "example": {
                "error_type": "DatabaseConnectionError",
                "error_message": "Failed to connect to database",
                "component": "storage",
                "context": {
                    "database_url": "sqlite:///./data/mwa_core.db",
                    "connection_attempts": 3
                },
                "severity": "error",
                "stack_trace": "Traceback (most recent call last)...",
                "user_agent": "MWA-Bot/1.0"
            }
        }


class ErrorReportResponse(BaseModel):
    """Response model for error reporting."""
    report_id: str = Field(..., description="Unique error report ID")
    status: str = Field(..., description="Report status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Report timestamp")
    details: Dict[str, Any] = Field(default_factory=dict, description="Additional report details")
    
    class Config:
        schema_extra = {
            "example": {
                "report_id": "err_20251119_112518_001",
                "status": "reported",
                "timestamp": "2025-11-19T11:25:18Z",
                "details": {
                    "error_type": "DatabaseConnectionError",
                    "component": "storage",
                    "severity": "error",
                    "processed": True
                }
            }
        }


class ErrorSummary(BaseModel):
    """Summary of system errors."""
    total_errors: int = Field(..., description="Total number of errors")
    errors_by_type: Dict[str, int] = Field(default_factory=dict, description="Errors by type")
    errors_by_component: Dict[str, int] = Field(default_factory=dict, description="Errors by component")
    errors_by_severity: Dict[str, int] = Field(default_factory=dict, description="Errors by severity")
    recent_errors: List[Dict[str, Any]] = Field(default_factory=list, description="Recent errors")
    error_rate_per_hour: float = Field(..., description="Error rate per hour")
    timestamp: datetime = Field(default_factory=datetime.now, description="Summary timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "total_errors": 25,
                "errors_by_type": {
                    "DatabaseConnectionError": 10,
                    "TimeoutError": 8,
                    "ValidationError": 7
                },
                "errors_by_component": {
                    "storage": 15,
                    "scraper": 7,
                    "api": 3
                },
                "errors_by_severity": {
                    "critical": 2,
                    "error": 15,
                    "warning": 8
                },
                "recent_errors": [],
                "error_rate_per_hour": 1.2,
                "timestamp": "2025-11-19T11:25:18Z"
            }
        }


# Log Entry Models
class LogEntry(BaseModel):
    """System log entry."""
    timestamp: datetime = Field(..., description="Log entry timestamp")
    level: str = Field(..., pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$", description="Log level")
    component: str = Field(..., description="Logging component")
    message: str = Field(..., description="Log message")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional log metadata")
    source_file: Optional[str] = Field(None, description="Source file")
    source_line: Optional[int] = Field(None, description="Source line number")
    
    class Config:
        schema_extra = {
            "example": {
                "timestamp": "2025-11-19T11:25:18Z",
                "level": "INFO",
                "component": "api",
                "message": "Health check completed successfully",
                "metadata": {
                    "endpoint": "/health",
                    "response_time_ms": 45.2,
                    "status_code": 200
                },
                "source_file": "api/routers/system.py",
                "source_line": 150
            }
        }


class LogSearchRequest(BaseModel):
    """Request model for log searching."""
    query: Optional[str] = Field(None, description="Search query")
    levels: Optional[List[str]] = Field(None, description="Log levels to include")
    components: Optional[List[str]] = Field(None, description="Components to include")
    date_range: Optional[DateRange] = Field(None, description="Date range filter")
    pagination: PaginationParams = Field(default_factory=PaginationParams, description="Pagination parameters")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "health check",
                "levels": ["INFO", "WARNING", "ERROR"],
                "components": ["api", "storage"],
                "date_range": {
                    "date_from": "2025-11-19T11:00:00Z",
                    "date_to": "2025-11-19T11:30:00Z"
                },
                "pagination": {
                    "limit": 50,
                    "offset": 0
                }
            }
        }


class LogSearchResponse(BaseModel):
    """Response model for log search results."""
    logs: List[LogEntry] = Field(..., description="Found log entries")
    total: int = Field(..., description="Total number of matching logs")
    limit: int = Field(..., description="Requested limit")
    offset: int = Field(..., description="Requested offset")
    search_params: Dict[str, Any] = Field(default_factory=dict, description="Search parameters used")
    
    class Config:
        schema_extra = {
            "example": {
                "logs": [],
                "total": 150,
                "limit": 50,
                "offset": 0,
                "search_params": {
                    "query": "health check",
                    "levels": ["INFO", "WARNING", "ERROR"]
                }
            }
        }


# System Metrics Models
class SystemMetricsResponse(BaseModel):
    """Response model for system metrics summary."""
    timestamp: datetime = Field(default_factory=datetime.now, description="Metrics timestamp")
    system: Dict[str, Any] = Field(..., description="System metrics")
    application: Dict[str, Any] = Field(..., description="Application metrics")
    status: str = Field(..., description="Overall system status")
    
    class Config:
        schema_extra = {
            "example": {
                "timestamp": "2025-11-19T11:25:18Z",
                "system": {
                    "cpu_percent": 25.5,
                    "memory_percent": 50.0,
                    "disk_percent": 45.2,
                    "uptime_seconds": 5118.5
                },
                "application": {
                    "total_listings": 1250,
                    "total_contacts": 2100,
                    "storage_size_mb": 1250.5,
                    "active_jobs": 3
                },
                "status": "healthy"
            }
        }


class MetricPoint(BaseModel):
    """Single metric data point."""
    timestamp: datetime = Field(..., description="Measurement timestamp")
    value: float = Field(..., description="Metric value")
    tags: Optional[Dict[str, str]] = Field(None, description="Metric tags")
    
    class Config:
        schema_extra = {
            "example": {
                "timestamp": "2025-11-19T11:25:00Z",
                "value": 25.5,
                "tags": {
                    "component": "cpu",
                    "host": "server-01"
                }
            }
        }


class MetricSeries(BaseModel):
    """Series of metric data points."""
    metric_name: str = Field(..., description="Metric name")
    unit: Optional[str] = Field(None, description="Metric unit")
    points: List[MetricPoint] = Field(..., description="Metric data points")
    aggregation: Optional[str] = Field(None, description="Data aggregation type")
    
    class Config:
        schema_extra = {
            "example": {
                "metric_name": "cpu_usage_percent",
                "unit": "percent",
                "points": [
                    {
                        "timestamp": "2025-11-19T11:20:00Z",
                        "value": 23.5
                    },
                    {
                        "timestamp": "2025-11-19T11:25:00Z",
                        "value": 25.5
                    }
                ],
                "aggregation": "average"
            }
        }


# System Control Models
class SystemShutdownRequest(BaseModel):
    """Request model for system shutdown."""
    mode: str = Field("graceful", pattern="^(graceful|force)$", description="Shutdown mode")
    delay_seconds: int = Field(30, ge=0, le=300, description="Shutdown delay in seconds")
    reason: Optional[str] = Field(None, description="Shutdown reason")
    notify_users: bool = Field(True, description="Whether to notify users")
    
    class Config:
        schema_extra = {
            "example": {
                "mode": "graceful",
                "delay_seconds": 60,
                "reason": "Scheduled maintenance",
                "notify_users": True
            }
        }


class SystemShutdownResponse(BaseModel):
    """Response model for system shutdown."""
    success: bool = Field(..., description="Shutdown initiation success")
    message: str = Field(..., description="Shutdown message")
    shutdown_time: datetime = Field(..., description="Scheduled shutdown time")
    mode: str = Field(..., description="Shutdown mode used")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "success": True,
                "message": "System shutdown initiated",
                "shutdown_time": "2025-11-19T11:26:18Z",
                "mode": "graceful",
                "timestamp": "2025-11-19T11:25:18Z"
            }
        }


# Resource Monitoring Models
class ResourceUsage(BaseModel):
    """Resource usage information."""
    cpu_percent: float = Field(..., description="CPU usage percentage")
    memory_percent: float = Field(..., description="Memory usage percentage")
    disk_percent: float = Field(..., description="Disk usage percentage")
    network_io_mb_per_sec: Optional[float] = Field(None, description="Network I/O rate")
    active_connections: int = Field(..., description="Active network connections")
    
    class Config:
        schema_extra = {
            "example": {
                "cpu_percent": 25.5,
                "memory_percent": 50.0,
                "disk_percent": 45.2,
                "network_io_mb_per_sec": 12.5,
                "active_connections": 15
            }
        }


class ResourceAlert(BaseModel):
    """Resource usage alert."""
    alert_id: str = Field(..., description="Alert identifier")
    metric: str = Field(..., description="Metric that triggered alert")
    threshold: float = Field(..., description="Alert threshold")
    current_value: float = Field(..., description="Current metric value")
    severity: str = Field(..., pattern="^(low|medium|high|critical)$", description="Alert severity")
    message: str = Field(..., description="Alert message")
    timestamp: datetime = Field(default_factory=datetime.now, description="Alert timestamp")
    
    class Config:
        schema_extra = {
            "example": {
                "alert_id": "alert_cpu_001",
                "metric": "cpu_usage_percent",
                "threshold": 80.0,
                "current_value": 85.2,
                "severity": "high",
                "message": "CPU usage above 80% threshold",
                "timestamp": "2025-11-19T11:25:18Z"
            }
        }


# System Maintenance Models
class MaintenanceWindow(BaseModel):
    """System maintenance window."""
    window_id: str = Field(..., description="Maintenance window identifier")
    name: str = Field(..., description="Maintenance window name")
    description: Optional[str] = Field(None, description="Maintenance description")
    start_time: datetime = Field(..., description="Maintenance start time")
    end_time: datetime = Field(..., description="Maintenance end time")
    affected_components: List[str] = Field(..., description="Components affected")
    status: str = Field(..., pattern="^(scheduled|in_progress|completed|cancelled)$", description="Window status")
    
    class Config:
        schema_extra = {
            "example": {
                "window_id": "maint_20251119_230000",
                "name": "Weekly Database Maintenance",
                "description": "Database optimization and backup",
                "start_time": "2025-11-19T23:00:00Z",
                "end_time": "2025-11-20T01:00:00Z",
                "affected_components": ["database", "api"],
                "status": "scheduled"
            }
        }


class SystemMaintenanceRequest(BaseModel):
    """Request model for system maintenance."""
    action: str = Field(..., pattern="^(start|end|schedule|cancel)$", description="Maintenance action")
    window_id: Optional[str] = Field(None, description="Maintenance window ID")
    name: Optional[str] = Field(None, description="Maintenance name")
    description: Optional[str] = Field(None, description="Maintenance description")
    start_time: Optional[datetime] = Field(None, description="Maintenance start time")
    duration_minutes: Optional[int] = Field(None, description="Maintenance duration")
    affected_components: Optional[List[str]] = Field(None, description="Affected components")
    
    class Config:
        schema_extra = {
            "example": {
                "action": "schedule",
                "name": "Database Optimization",
                "description": "Weekly database maintenance",
                "start_time": "2025-11-20T02:00:00Z",
                "duration_minutes": 120,
                "affected_components": ["database", "storage"]
            }
        }


# Version and Update Models
class VersionInfo(BaseModel):
    """Application version information."""
    application: str = Field(..., description="Application name")
    version: str = Field(..., description="Version string")
    build_info: Dict[str, str] = Field(default_factory=dict, description="Build information")
    update_available: bool = Field(False, description="Whether update is available")
    latest_version: Optional[str] = Field(None, description="Latest available version")
    
    class Config:
        schema_extra = {
            "example": {
                "application": "MWA Core API",
                "version": "1.0.0",
                "build_info": {
                    "build_date": "2025-11-19",
                    "git_commit": "abc123def",
                    "build_number": "42"
                },
                "update_available": False,
                "latest_version": None
            }
        }


class SystemStatusResponse(BaseModel):
    """Comprehensive system status response."""
    overall_status: str = Field(..., pattern="^(healthy|degraded|unhealthy)$", description="Overall system status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Status timestamp")
    uptime_seconds: float = Field(..., description="System uptime")
    components: List[ComponentHealth] = Field(..., description="Component statuses")
    metrics: Optional[PerformanceMetricsResponse] = Field(None, description="Current performance metrics")
    alerts: List[ResourceAlert] = Field(default_factory=list, description="Active alerts")
    maintenance_windows: List[MaintenanceWindow] = Field(default_factory=list, description="Scheduled maintenance")
    
    class Config:
        schema_extra = {
            "example": {
                "overall_status": "healthy",
                "timestamp": "2025-11-19T11:25:18Z",
                "uptime_seconds": 5118.5,
                "components": [],
                "metrics": {
                    "cpu": {"usage_percent": 25.5, "count": 8},
                    "memory": {"percent": 50.0, "total": 17179869184},
                    "disk": {"percent": 45.2, "total": 1000000000000}
                },
                "alerts": [],
                "maintenance_windows": []
            }
        }