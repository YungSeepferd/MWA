"""
System monitoring and health check router for MWA Core API.

Provides endpoints for:
- System health checks
- Performance metrics
- Dashboard statistics
- Analytics data for charts
- System status monitoring
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from statistics import mean

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for system requests/responses
class SystemMetricsResponse(BaseModel):
    """Response model for system metrics."""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    active_connections: int
    uptime_seconds: float
    timestamp: datetime
    health_status: str


class PerformanceMetricsResponse(BaseModel):
    """Response model for performance metrics."""
    cpu_usage: float
    memory_usage: float
    disk_usage: float
    request_rate: float
    active_connections: int
    response_time_ms: float
    timestamp: datetime


class DashboardStatsResponse(BaseModel):
    """Response model for dashboard statistics."""
    total_contacts: int
    contacts_by_status: Dict[str, int]
    contacts_by_type: Dict[str, int]
    contacts_by_confidence: Dict[str, int]
    recent_contacts_7_days: int
    recent_contacts_30_days: int
    high_confidence_contacts: int
    validated_contacts: int
    validation_rate: float
    average_confidence: float
    top_sources: List[Dict[str, Any]]
    active_searches: int
    new_contacts_today: int
    success_rate: float
    timestamp: datetime


class AnalyticsDataResponse(BaseModel):
    """Response model for analytics data."""
    timeframe: str
    contact_discovery_trend: List[Dict[str, Any]]
    provider_performance: List[Dict[str, Any]]
    confidence_distribution: List[Dict[str, Any]]
    contact_methods: List[Dict[str, Any]]
    search_performance: List[Dict[str, Any]]
    timestamp: datetime


class SystemStatusResponse(BaseModel):
    """Response model for system status."""
    healthy: bool
    components: Dict[str, Dict[str, Any]]
    metrics: Dict[str, float]
    timestamp: datetime


class ChartDataPoint(BaseModel):
    """Data point for chart responses."""
    label: str
    value: float
    date: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """Response model for health checks."""
    status: str
    timestamp: datetime
    uptime_seconds: float
    version: str
    components: Dict[str, str]


# Mock data generators for demonstration
def generate_mock_metrics() -> Dict[str, Any]:
    """Generate mock system metrics."""
    import random
    import time
    
    return {
        "cpu_usage": round(random.uniform(10, 80), 1),
        "memory_usage": round(random.uniform(30, 70), 1),
        "disk_usage": round(random.uniform(20, 60), 1),
        "active_connections": random.randint(5, 25),
        "uptime_seconds": int(time.time()) % 86400,  # Mock uptime
        "timestamp": datetime.now()
    }


def generate_mock_dashboard_stats() -> Dict[str, Any]:
    """Generate mock dashboard statistics."""
    import random
    
    total_contacts = random.randint(150, 500)
    approved = random.randint(80, total_contacts - 20)
    pending = random.randint(10, 50)
    rejected = total_contacts - approved - pending
    
    return {
        "total_contacts": total_contacts,
        "contacts_by_status": {
            "approved": approved,
            "pending": pending,
            "rejected": rejected
        },
        "contacts_by_type": {
            "email": random.randint(80, 200),
            "phone": random.randint(40, 100),
            "form": random.randint(20, 60),
            "other": random.randint(10, 30)
        },
        "contacts_by_confidence": {
            "high_0.8_1.0": random.randint(60, 150),
            "medium_0.5_0.8": random.randint(40, 100),
            "low_0.0_0.5": random.randint(20, 80)
        },
        "recent_contacts_7_days": random.randint(20, 80),
        "recent_contacts_30_days": random.randint(80, 200),
        "high_confidence_contacts": random.randint(60, 150),
        "validated_contacts": random.randint(100, 300),
        "validation_rate": round(random.uniform(70, 95), 1),
        "average_confidence": round(random.uniform(0.6, 0.9), 2),
        "top_sources": [
            {"source": "ImmoScout24", "count": random.randint(50, 150)},
            {"source": "WG-Gesucht", "count": random.randint(30, 100)},
            {"source": "Immowelt", "count": random.randint(20, 80)},
            {"source": "eBay Kleinanzeigen", "count": random.randint(15, 60)},
            {"source": "Local Newspapers", "count": random.randint(10, 40)}
        ],
        "active_searches": random.randint(3, 8),
        "new_contacts_today": random.randint(5, 25),
        "success_rate": round(random.uniform(75, 95), 1),
        "timestamp": datetime.now()
    }


def generate_mock_analytics_data(timeframe: str = "30") -> Dict[str, Any]:
    """Generate mock analytics data for charts."""
    import random
    from datetime import timedelta
    
    days = int(timeframe)
    end_date = datetime.now()
    start_date = end_date - timedelta(days=days)
    
    # Generate trend data
    contact_discovery_trend = []
    current_date = start_date
    while current_date <= end_date:
        contact_discovery_trend.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "count": random.randint(2, 20),
            "quality": round(random.uniform(0.6, 0.95), 2),
            "response_rate": round(random.uniform(0.1, 0.4), 2)
        })
        current_date += timedelta(days=1)
    
    # Provider performance
    provider_performance = [
        {"provider": "ImmoScout24", "success_rate": 92, "avg_response_time": 2.1, "listings_found": 156},
        {"provider": "WG-Gesucht", "success_rate": 88, "avg_response_time": 1.8, "listings_found": 89},
        {"provider": "Immowelt", "success_rate": 85, "avg_response_time": 2.5, "listings_found": 67},
        {"provider": "eBay Kleinanzeigen", "success_rate": 78, "avg_response_time": 3.2, "listings_found": 34}
    ]
    
    # Confidence distribution
    confidence_distribution = [
        {"range": "90-100%", "count": 45, "percentage": 15},
        {"range": "80-89%", "count": 78, "percentage": 26},
        {"range": "70-79%", "count": 67, "percentage": 22},
        {"range": "60-69%", "count": 56, "percentage": 19},
        {"range": "Below 60%", "count": 54, "percentage": 18}
    ]
    
    # Contact methods
    contact_methods = [
        {"method": "Email", "count": 180, "percentage": 60},
        {"method": "Phone", "count": 75, "percentage": 25},
        {"method": "Contact Form", "count": 30, "percentage": 10},
        {"method": "Other", "count": 15, "percentage": 5}
    ]
    
    # Search performance (simplified)
    search_performance = []
    for i in range(days):
        date = start_date + timedelta(days=i)
        search_performance.append({
            "date": date.strftime("%Y-%m-%d"),
            "searches_run": random.randint(2, 8),
            "new_listings": random.randint(5, 25),
            "contacts_found": random.randint(2, 15)
        })
    
    return {
        "timeframe": timeframe,
        "contact_discovery_trend": contact_discovery_trend,
        "provider_performance": provider_performance,
        "confidence_distribution": confidence_distribution,
        "contact_methods": contact_methods,
        "search_performance": search_performance,
        "timestamp": datetime.now()
    }


@router.get("/health", response_model=HealthCheckResponse, summary="System health check")
async def health_check():
    """
    Basic health check endpoint.
    
    Returns:
        Health check status
    """
    return HealthCheckResponse(
        status="healthy",
        timestamp=datetime.now(),
        uptime_seconds=86400,  # Mock uptime
        version="2.0.0",
        components={
            "database": "healthy",
            "scraper": "healthy",
            "scheduler": "healthy",
            "notifications": "healthy"
        }
    )


@router.get("/metrics", response_model=SystemMetricsResponse, summary="Get system metrics")
async def get_system_metrics():
    """
    Get current system metrics.
    
    Returns:
        System performance metrics
    """
    try:
        metrics = generate_mock_metrics()
        return SystemMetricsResponse(**metrics)
    except Exception as e:
        logger.error(f"Error getting system metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system metrics")


@router.get("/performance", response_model=PerformanceMetricsResponse, summary="Get performance metrics")
async def get_performance_metrics():
    """
    Get performance metrics for monitoring.
    
    Returns:
        Performance metrics
    """
    try:
        metrics = generate_mock_metrics()
        metrics["request_rate"] = round(metrics["cpu_usage"] * 0.1, 2)  # Mock request rate
        metrics["response_time_ms"] = round(metrics["cpu_usage"] * 2.5, 1)  # Mock response time
        
        return PerformanceMetricsResponse(**metrics)
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance metrics")


@router.get("/dashboard/stats", response_model=DashboardStatsResponse, summary="Get dashboard statistics")
async def get_dashboard_stats():
    """
    Get statistics for the dashboard.
    
    Returns:
        Dashboard statistics
    """
    try:
        stats = generate_mock_dashboard_stats()
        return DashboardStatsResponse(**stats)
    except Exception as e:
        logger.error(f"Error getting dashboard stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get dashboard statistics")


@router.get("/analytics/data", response_model=AnalyticsDataResponse, summary="Get analytics data")
async def get_analytics_data(
    timeframe: str = Query("30", description="Timeframe in days (7, 30, 90, 365)"),
    metric: str = Query("contacts", description="Primary metric for analysis")
):
    """
    Get analytics data for charts and reporting.
    
    Args:
        timeframe: Analysis timeframe in days
        metric: Primary metric to analyze
        
    Returns:
        Analytics data
    """
    try:
        if timeframe not in ["7", "30", "90", "365"]:
            raise HTTPException(status_code=400, detail="Invalid timeframe. Use: 7, 30, 90, or 365")
        
        data = generate_mock_analytics_data(timeframe)
        return AnalyticsDataResponse(**data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting analytics data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics data")


@router.get("/analytics/trend", response_model=List[ChartDataPoint], summary="Get trend data")
async def get_trend_data(
    metric: str = Query("contacts", description="Metric to get trend for"),
    timeframe: str = Query("30", description="Timeframe in days")
):
    """
    Get trend data for specific metrics.
    
    Args:
        metric: Metric to analyze
        timeframe: Timeframe in days
        
    Returns:
        Trend data points
    """
    try:
        if timeframe not in ["7", "30", "90", "365"]:
            raise HTTPException(status_code=400, detail="Invalid timeframe")
        
        data = generate_mock_analytics_data(timeframe)
        trend_key = f"{metric}_trend" if f"{metric}_trend" in data else "contact_discovery_trend"
        
        trend_data = data.get(trend_key, [])
        return [
            ChartDataPoint(
                label=point.get("date", ""),
                value=point.get("count", point.get(metric, 0)),
                date=point.get("date")
            )
            for point in trend_data
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting trend data: {e}")
        raise HTTPException(status_code=500, detail="Failed to get trend data")


@router.get("/analytics/insights", summary="Get AI-generated insights")
async def get_analytics_insights(timeframe: str = Query("30", description="Timeframe in days")):
    """
    Get AI-generated insights and recommendations.
    
    Args:
        timeframe: Analysis timeframe
        
    Returns:
        AI-generated insights
    """
    try:
        insights = [
            {
                "type": "recommendation",
                "title": "Peak Search Hours",
                "description": "Your searches are most successful between 9-11 AM and 6-8 PM. Consider scheduling more searches during these hours.",
                "confidence": 0.85,
                "action": "Adjust search schedule"
            },
            {
                "type": "trend",
                "title": "Contact Quality Improvement",
                "description": "Your contact extraction accuracy has improved by 12% over the last week.",
                "confidence": 0.92,
                "action": "Continue current approach"
            },
            {
                "type": "alert",
                "title": "High Competition Area",
                "description": "Munich Central (Maxvorstadt) shows high listing competition. Consider expanding to adjacent districts.",
                "confidence": 0.78,
                "action": "Expand search area"
            },
            {
                "type": "opportunity",
                "title": "Weekend Listings",
                "description": "17% more new listings appear on weekends. Weekend searches yield higher contact rates.",
                "confidence": 0.73,
                "action": "Add weekend searches"
            }
        ]
        
        return {
            "timeframe": timeframe,
            "insights": insights,
            "generated_at": datetime.now().isoformat(),
            "version": "2.0.0"
        }
    except Exception as e:
        logger.error(f"Error getting analytics insights: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics insights")


@router.get("/status", response_model=SystemStatusResponse, summary="Get system status")
async def get_system_status():
    """
    Get overall system status and component health.
    
    Returns:
        System status
    """
    try:
        metrics = generate_mock_metrics()
        
        components = {
            "database": {
                "status": "healthy",
                "response_time_ms": 45,
                "last_check": datetime.now().isoformat()
            },
            "scraper": {
                "status": "healthy", 
                "active_jobs": 3,
                "last_run": datetime.now().isoformat(),
                "success_rate": 94.2
            },
            "scheduler": {
                "status": "healthy",
                "active_jobs": 5,
                "next_run": (datetime.now() + timedelta(hours=1)).isoformat()
            },
            "notifications": {
                "status": "healthy",
                "queue_size": 12,
                "delivery_rate": 98.5
            }
        }
        # Convert metrics to only include float values for the response
        metrics_float = {
            "cpu_usage": float(metrics["cpu_usage"]),
            "memory_usage": float(metrics["memory_usage"]),
            "disk_usage": float(metrics["disk_usage"]),
            "active_connections": float(metrics["active_connections"]),
            "uptime_seconds": float(metrics["uptime_seconds"])
        }
        # Convert metrics to ensure all values are floats for the response
        metrics_dict = {
            "cpu_usage": float(metrics["cpu_usage"]),
            "memory_usage": float(metrics["memory_usage"]),
            "disk_usage": float(metrics["disk_usage"]),
            "active_connections": float(metrics["active_connections"]),
            "uptime_seconds": float(metrics["uptime_seconds"])
        }
        
        return SystemStatusResponse(
            healthy=True,
            components=components,
            metrics=metrics_dict,
            timestamp=datetime.now()
        )
    except Exception as e:
        logger.error(f"Error getting system status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system status")


@router.post("/export/analytics", summary="Export analytics data")
async def export_analytics(
    timeframe: str = Body("30", description="Timeframe in days"),
    format: str = Body("json", description="Export format (json, csv, xlsx)")
):
    """
    Export analytics data in various formats.
    
    Args:
        timeframe: Data timeframe
        format: Export format
        
    Returns:
        Exported data
    """
    try:
        data = generate_mock_analytics_data(timeframe)
        
        return {
            "exported_at": datetime.now().isoformat(),
            "timeframe": timeframe,
            "format": format,
            "data": data,
            "summary": {
                "total_contacts": sum(point.get("count", 0) for point in data["contact_discovery_trend"]),
                "average_daily": round(sum(point.get("count", 0) for point in data["contact_discovery_trend"]) / len(data["contact_discovery_trend"]), 1),
                "peak_day": max(data["contact_discovery_trend"], key=lambda x: x.get("count", 0))["date"]
            }
        }
    except Exception as e:
        logger.error(f"Error exporting analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to export analytics data")


@router.get("/info", summary="Get system information")
async def get_system_info():
    """
    Get general system information.
    
    Returns:
        System information
    """
    return {
        "name": "MAFA - Munich Apartment Finder Assistant",
        "version": "2.0.0",
        "description": "Real-time apartment search and contact discovery system",
        "features": [
            "Multi-provider scraping",
            "AI-powered contact extraction", 
            "Real-time notifications",
            "Advanced analytics",
            "WebSocket real-time updates"
        ],
        "endpoints": {
            "dashboard": "/api/v1/system/dashboard/stats",
            "analytics": "/api/v1/system/analytics/data",
            "metrics": "/api/v1/system/metrics",
            "status": "/api/v1/system/status"
        },
        "timestamp": datetime.now().isoformat()
    }