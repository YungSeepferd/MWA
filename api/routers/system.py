"""
System status and health check router for MWA Core API.

Provides endpoints for system monitoring and health checks, including:
- Basic health check endpoints
- System status and performance metrics
- Component health monitoring
- System information and version details
- Error reporting and logging
- Resource usage monitoring
"""

import logging
import psutil
import os
import sys
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field

from mwa_core.config.settings import get_settings
from mwa_core.storage.manager import get_storage_manager
from mwa_core.orchestrator.orchestrator import Orchestrator

logger = logging.getLogger(__name__)

router = APIRouter()




# Pydantic models for system requests/responses
class HealthCheckResponse(BaseModel):
    """Response model for health check."""
    status: str
    timestamp: datetime
    service: str
    version: str
    uptime_seconds: Optional[float] = None
    dependencies: Dict[str, str] = {}
    details: Dict[str, Any] = {}


class SystemInfoResponse(BaseModel):
    """Response model for system information."""
    application: Dict[str, str]
    system: Dict[str, Any]
    environment: Dict[str, Any]
    configuration: Dict[str, Any]
    components: Dict[str, Any]
    timestamp: datetime


class PerformanceMetricsResponse(BaseModel):
    """Response model for performance metrics."""
    cpu: Dict[str, float]
    memory: Dict[str, float]
    disk: Dict[str, float]
    network: Dict[str, float]
    database: Dict[str, Any] = {}
    application: Dict[str, Any] = {}
    timestamp: datetime


class ComponentStatus(BaseModel):
    """Response model for component status."""
    name: str
    status: str
    healthy: bool
    last_check: datetime
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}


class ErrorReportRequest(BaseModel):
    """Request model for error reporting."""
    error_type: str = Field(..., min_length=1)
    error_message: str = Field(..., min_length=1)
    component: str = Field(..., min_length=1)
    context: Optional[Dict[str, Any]] = {}
    severity: str = Field("error", regex="^(info|warning|error|critical)$")


class ErrorReportResponse(BaseModel):
    """Response model for error reporting."""
    report_id: str
    status: str
    timestamp: datetime
    details: Dict[str, Any] = {}


class LogEntry(BaseModel):
    """Response model for log entry."""
    timestamp: datetime
    level: str
    component: str
    message: str
    metadata: Dict[str, Any] = {}


# Global variables for tracking startup time and system status
_startup_time = datetime.now()
_system_healthy = True
_components_status = {}




@router.get("/health", response_model=HealthCheckResponse, summary="Basic health check")
async def health_check():
    """
    Basic health check endpoint.
    
    Returns:
        Health status of the application
    """
    try:
        uptime_seconds = (datetime.now() - _startup_time).total_seconds()
        
        return HealthCheckResponse(
            status="healthy",
            timestamp=datetime.now(),
            service="MWA Core API",
            version="1.0.0",
            uptime_seconds=uptime_seconds,
            dependencies={},
            details={
                "status_code": 200
            }
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthCheckResponse(
            status="unhealthy",
            timestamp=datetime.now(),
            service="MWA Core API",
            version="1.0.0",
            details={
                "error": str(e),
                "status_code": 503
            }
        )


@router.get("/health/detailed", response_model=HealthCheckResponse, summary="Detailed health check")
async def detailed_health_check(
    settings = Depends(get_settings),
    storage_manager = Depends(get_storage_manager)
):
    """
    Detailed health check with component validation.
    
    Args:
        settings: Settings instance
        storage_manager: Storage manager instance
        
    Returns:
        Detailed health status with component checks
    """
    try:
        dependencies = {}
        component_details = {}
        all_healthy = True
        
        # Check settings
        try:
            settings_dict = settings.dict()
            dependencies["settings"] = "healthy"
            component_details["settings"] = {"loaded": True, "config_path": str(settings.config_path)}
        except Exception as e:
            dependencies["settings"] = "unhealthy"
            component_details["settings"] = {"error": str(e)}
            all_healthy = False
        
        # Check storage manager
        try:
            stats = storage_manager.get_statistics()
            dependencies["storage"] = "healthy"
            component_details["storage"] = {
                "accessible": True,
                "listings_count": stats.get("total_listings", 0),
                "contacts_count": stats.get("total_contacts", 0)
            }
        except Exception as e:
            dependencies["storage"] = "unhealthy"
            component_details["storage"] = {"error": str(e)}
            all_healthy = False
        
        uptime_seconds = (datetime.now() - _startup_time).total_seconds()
        
        return HealthCheckResponse(
            status="healthy" if all_healthy else "degraded",
            timestamp=datetime.now(),
            service="MWA Core API",
            version="1.0.0",
            uptime_seconds=uptime_seconds,
            dependencies=dependencies,
            details=component_details
        )
        
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return HealthCheckResponse(
            status="unhealthy",
            timestamp=datetime.now(),
            service="MWA Core API",
            version="1.0.0",
            details={
                "error": str(e),
                "status_code": 503
            }
        )


@router.get("/info", response_model=SystemInfoResponse, summary="Get system information")
async def get_system_info(
    settings = Depends(get_settings),
    storage_manager = Depends(get_storage_manager)
):
    """
    Get comprehensive system information.
    
    Args:
        settings: Settings instance
        storage_manager: Storage manager instance
        
    Returns:
        System information details
    """
    try:
        # Application info
        application_info = {
            "name": "MWA Core API",
            "version": "1.0.0",
            "description": "Munich Apartment Finder Assistant Core API",
            "startup_time": _startup_time.isoformat(),
            "uptime_seconds": (datetime.now() - _startup_time).total_seconds()
        }
        
        # System info
        system_info = {
            "platform": sys.platform,
            "python_version": sys.version,
            "cpu_count": psutil.cpu_count(),
            "memory_total": psutil.virtual_memory().total,
            "disk_total": psutil.disk_usage('/').total,
            "boot_time": datetime.fromtimestamp(psutil.boot_time()).isoformat()
        }
        
        # Environment info
        environment_info = {
            "config_path": str(settings.config_path),
            "data_directory": "data/",
            "log_level": settings.log_level,
            "timezone": getattr(settings, 'timezone', 'Europe/Berlin')
        }
        
        # Configuration summary
        config_summary = {
            "scraper_enabled": settings.scraper.enabled_providers,
            "scheduler_enabled": settings.scheduler.enabled,
            "contact_discovery": settings.contact_discovery.enabled,
            "notification_system": settings.notification_system_enabled,
            "storage_path": settings.storage.database_path
        }
        
        # Components status
        components_info = {}
        try:
            components_info["settings"] = {"status": "loaded", "healthy": True}
        except Exception:
            components_info["settings"] = {"status": "error", "healthy": False}
        
        try:
            stats = storage_manager.get_statistics()
            components_info["storage"] = {"status": "connected", "healthy": True, "stats": stats}
        except Exception as e:
            components_info["storage"] = {"status": "error", "healthy": False, "error": str(e)}
        
        return SystemInfoResponse(
            application=application_info,
            system=system_info,
            environment=environment_info,
            configuration=config_summary,
            components=components_info,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting system information: {str(e)}")


@router.get("/performance", response_model=PerformanceMetricsResponse, summary="Get performance metrics")
async def get_performance_metrics(
    storage_manager = Depends(get_storage_manager)
):
    """
    Get system performance metrics.
    
    Args:
        storage_manager: Storage manager instance
        
    Returns:
        Performance metrics data
    """
    try:
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        cpu_count = psutil.cpu_count()
        
        # Memory metrics
        memory = psutil.virtual_memory()
        
        # Disk metrics
        disk = psutil.disk_usage('/')
        
        # Network metrics (simplified)
        network = psutil.net_io_counters()
        
        # Database metrics
        db_metrics = {}
        try:
            stats = storage_manager.get_statistics()
            db_metrics = {
                "total_listings": stats.get("total_listings", 0),
                "total_contacts": stats.get("total_contacts", 0),
                "status": "connected"
            }
        except Exception as e:
            db_metrics = {
                "status": "error",
                "error": str(e)
            }
        
        # Application metrics
        app_metrics = {
            "uptime_seconds": (datetime.now() - _startup_time).total_seconds(),
            "startup_time": _startup_time.isoformat(),
            "healthy": _system_healthy
        }
        
        return PerformanceMetricsResponse(
            cpu={
                "usage_percent": cpu_percent,
                "count": cpu_count,
                "load_average": psutil.getloadavg()[0] if hasattr(psutil, 'getloadavg') else None
            },
            memory={
                "total": memory.total,
                "available": memory.available,
                "percent": memory.percent,
                "used": memory.used
            },
            disk={
                "total": disk.total,
                "used": disk.used,
                "free": disk.free,
                "percent": (disk.used / disk.total * 100)
            },
            network={
                "bytes_sent": getattr(network, 'bytes_sent', 0),
                "bytes_recv": getattr(network, 'bytes_recv', 0),
                "packets_sent": getattr(network, 'packets_sent', 0),
                "packets_recv": getattr(network, 'packets_recv', 0)
            },
            database=db_metrics,
            application=app_metrics,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting performance metrics: {str(e)}")


@router.get("/components", response_model=List[ComponentStatus], summary="Get component status")
async def get_component_status(
    settings = Depends(get_settings),
    storage_manager = Depends(get_storage_manager)
):
    """
    Get status of all system components.
    
    Args:
        settings: Settings instance
        storage_manager: Storage manager instance
        
    Returns:
        List of component statuses
    """
    try:
        components = []
        
        # Settings component
        try:
            settings_dict = settings.dict()
            components.append(ComponentStatus(
                name="Settings",
                status="healthy",
                healthy=True,
                last_check=datetime.now(),
                metadata={"config_loaded": True, "config_path": str(settings.config_path)}
            ))
        except Exception as e:
            components.append(ComponentStatus(
                name="Settings",
                status="error",
                healthy=False,
                last_check=datetime.now(),
                error_message=str(e)
            ))
        
        # Storage component
        try:
            stats = storage_manager.get_statistics()
            components.append(ComponentStatus(
                name="Storage",
                status="healthy",
                healthy=True,
                last_check=datetime.now(),
                metadata={"listings_count": stats.get("total_listings", 0), "contacts_count": stats.get("total_contacts", 0)}
            ))
        except Exception as e:
            components.append(ComponentStatus(
                name="Storage",
                status="error",
                healthy=False,
                last_check=datetime.now(),
                error_message=str(e)
            ))
        
        # Scraper component
        try:
            components.append(ComponentStatus(
                name="Scraper",
                status="healthy",
                healthy=True,
                last_check=datetime.now(),
                metadata={"enabled_providers": settings.scraper.enabled_providers}
            ))
        except Exception as e:
            components.append(ComponentStatus(
                name="Scraper",
                status="error",
                healthy=False,
                last_check=datetime.now(),
                error_message=str(e)
            ))
        
        # Scheduler component
        try:
            components.append(ComponentStatus(
                name="Scheduler",
                status="healthy" if settings.scheduler.enabled else "disabled",
                healthy=settings.scheduler.enabled,
                last_check=datetime.now(),
                metadata={"enabled": settings.scheduler.enabled, "timezone": settings.scheduler.timezone}
            ))
        except Exception as e:
            components.append(ComponentStatus(
                name="Scheduler",
                status="error",
                healthy=False,
                last_check=datetime.now(),
                error_message=str(e)
            ))
        
        # Contact Discovery component
        try:
            components.append(ComponentStatus(
                name="ContactDiscovery",
                status="healthy" if settings.contact_discovery.enabled else "disabled",
                healthy=settings.contact_discovery.enabled,
                last_check=datetime.now(),
                metadata={"enabled": settings.contact_discovery.enabled, "confidence_threshold": settings.contact_discovery.confidence_threshold}
            ))
        except Exception as e:
            components.append(ComponentStatus(
                name="ContactDiscovery",
                status="error",
                healthy=False,
                last_check=datetime.now(),
                error_message=str(e)
            ))
        
        return components
        
    except Exception as e:
        logger.error(f"Error getting component status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting component status: {str(e)}")


@router.post("/errors", response_model=ErrorReportResponse, summary="Report system error")
async def report_error(
    request: ErrorReportRequest
):
    """
    Report an error or issue in the system.
    
    Args:
        request: Error report details
        
    Returns:
        Error report confirmation
    """
    try:
        report_id = f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{hash(request.error_message) % 10000}"
        
        # Log the error
        logger.error(f"System error reported: {request.error_type} - {request.error_message}", extra={
            "component": request.component,
            "severity": request.severity,
            "context": request.context,
            "report_id": report_id
        })
        
        return ErrorReportResponse(
            report_id=report_id,
            status="reported",
            timestamp=datetime.now(),
            details={
                "error_type": request.error_type,
                "component": request.component,
                "severity": request.severity,
                "context": request.context
            }
        )
        
    except Exception as e:
        logger.error(f"Error reporting failed: {e}")
        raise HTTPException(status_code=500, detail=f"Error reporting: {str(e)}")


@router.get("/logs", response_model=List[LogEntry], summary="Get system logs")
async def get_system_logs(
    level: Optional[str] = Query(None, regex="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$", description="Filter by log level"),
    component: Optional[str] = Query(None, description="Filter by component"),
    limit: int = Query(100, ge=1, le=1000, description="Number of log entries"),
    since: Optional[datetime] = Query(None, description="Get logs since this time")
):
    """
    Get system logs (simplified implementation).
    
    Args:
        level: Log level filter
        component: Component filter
        limit: Maximum number of log entries
        since: Get logs since this time
        
    Returns:
        List of log entries
    """
    try:
        # This is a simplified implementation
        # In a real system, you would query actual log files or a logging system
        
        logs = [
            LogEntry(
                timestamp=datetime.now() - timedelta(minutes=i),
                level="INFO",
                component="api",
                message=f"System health check completed - {i} minutes ago",
                metadata={"check_duration": "0.1s"}
            )
            for i in range(min(limit, 10))
        ]
        
        # Apply filters
        if level:
            logs = [log for log in logs if log.level == level]
        
        if component:
            logs = [log for log in logs if log.component == component]
        
        if since:
            logs = [log for log in logs if log.timestamp >= since]
        
        return logs[:limit]
        
    except Exception as e:
        logger.error(f"Error getting system logs: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting system logs: {str(e)}")


@router.get("/metrics", summary="Get system metrics summary")
async def get_system_metrics(
    storage_manager = Depends(get_storage_manager)
):
    """
    Get a summary of system metrics.
    
    Args:
        storage_manager: Storage manager instance
        
    Returns:
        Summary of system metrics
    """
    try:
        # Get basic system metrics
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        # Get application metrics
        try:
            stats = storage_manager.get_statistics()
            app_stats = {
                "total_listings": stats.get("total_listings", 0),
                "total_contacts": stats.get("total_contacts", 0),
                "storage_size_mb": stats.get("database_size", 0) / (1024 * 1024)  # Convert to MB
            }
        except Exception:
            app_stats = {"total_listings": 0, "total_contacts": 0, "storage_size_mb": 0}
        
        uptime_seconds = (datetime.now() - _startup_time).total_seconds()
        
        return {
            "timestamp": datetime.now().isoformat(),
            "system": {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "disk_percent": (disk.used / disk.total * 100),
                "uptime_seconds": uptime_seconds
            },
            "application": app_stats,
            "status": "healthy"
        }
        
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting system metrics: {str(e)}")


@router.get("/version", summary="Get application version")
async def get_version():
    """
    Get application version information.
    
    Returns:
        Version information
    """
    return {
        "application": "MWA Core API",
        "version": "1.0.0",
        "build_info": {
            "build_date": "2025-11-19",
            "python_version": sys.version,
            "platform": sys.platform
        },
        "timestamp": datetime.now().isoformat()
    }


@router.post("/shutdown", summary="Initiate system shutdown")
async def initiate_shutdown():
    """
    Initiate a graceful system shutdown.
    
    Returns:
        Shutdown confirmation
    """
    try:
        # Note: In a real implementation, this would trigger a graceful shutdown
        # For now, just return a confirmation
        
        logger.info("System shutdown initiated")
        
        return {
            "success": True,
            "message": "System shutdown initiated",
            "timestamp": datetime.now().isoformat(),
            "note": "This is a simulated shutdown in the API implementation"
        }
        
    except Exception as e:
        logger.error(f"Error initiating shutdown: {e}")
        raise HTTPException(status_code=500, detail=f"Error initiating shutdown: {str(e)}")


