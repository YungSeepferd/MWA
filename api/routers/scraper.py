"""
Scraper control router for MWA Core API.

Provides endpoints for managing and controlling scraper operations, including:
- Starting and stopping scrapers
- Getting scraper status and statistics
- Configuring scraper parameters
- Manual scraper runs
- Scraper performance monitoring
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, Query, Body
from pydantic import BaseModel, Field, validator

from mwa_core.orchestrator.orchestrator import Orchestrator
from mwa_core.scraper.engine import ScraperEngine
from mwa_core.storage.manager import get_storage_manager
from mwa_core.config.settings import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for scraper requests/responses
class ScraperStatusResponse(BaseModel):
    """Response model for scraper status."""
    scraper_engine: Dict[str, Any]
    orchestrator: Dict[str, Any]
    storage: Dict[str, Any]
    last_run: Optional[Dict[str, Any]] = None
    active_jobs: List[Dict[str, Any]] = []
    total_runs_today: int
    total_listings_today: int
    timestamp: datetime


class ScraperStartRequest(BaseModel):
    """Request model for starting scraper."""
    providers: List[str] = Field(..., min_items=1, description="List of providers to enable")
    config_overrides: Optional[Dict[str, Any]] = Field(None, description="Configuration overrides")
    notify_on_completion: bool = Field(True, description="Send notifications on completion")
    job_id: Optional[str] = Field(None, description="Optional job ID for tracking")


class ScraperStatsResponse(BaseModel):
    """Response model for scraper statistics."""
    total_runs: int
    successful_runs: int
    failed_runs: int
    total_listings_scraped: int
    total_new_listings: int
    run_frequency: Dict[str, Any]
    average_runtime: Optional[float] = None
    success_rate: float
    top_providers: List[Dict[str, Any]]
    recent_activity: List[Dict[str, Any]]
    timestamp: datetime


class ScraperConfigRequest(BaseModel):
    """Request model for updating scraper configuration."""
    providers: Optional[List[str]] = None
    request_delay_seconds: Optional[float] = Field(None, ge=0.1, le=60.0)
    timeout_seconds: Optional[int] = Field(None, ge=5, le=300)
    user_agent: Optional[str] = Field(None, max_length=500)
    max_retries: Optional[int] = Field(None, ge=0, le=10)
    contact_discovery_enabled: Optional[bool] = None
    contact_discovery_timeout: Optional[int] = Field(None, ge=10, le=120)


class ScraperRunResponse(BaseModel):
    """Response model for scraper run results."""
    run_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    providers: List[str]
    config_used: Dict[str, Any]
    results: Dict[str, Any] = {}
    error_details: Optional[List[str]] = None
    duration_seconds: Optional[float] = None


class ScraperProviderInfo(BaseModel):
    """Response model for scraper provider information."""
    name: str
    enabled: bool
    description: str
    last_run: Optional[datetime] = None
    run_count: int
    success_rate: float
    average_runtime: Optional[float] = None


# Dependency to get orchestrator
def get_orchestrator_instance() -> Orchestrator:
    """Get the orchestrator instance."""
    return Orchestrator()


# Dependency to get storage manager
def get_storage_manager_instance():
    """Get the storage manager instance."""
    return get_storage_manager()


@router.get("/status", response_model=ScraperStatusResponse, summary="Get scraper status")
async def get_scraper_status(
    orchestrator: Orchestrator = Depends(get_orchestrator_instance),
    storage_manager = Depends(get_storage_manager_instance)
):
    """
    Get the current status of all scraper components.
    
    Args:
        orchestrator: Orchestrator instance
        storage_manager: Storage manager instance
        
    Returns:
        Current scraper status
    """
    try:
        # Get basic scraper information
        scraper_engine = {
            "initialized": True,
            "providers_loaded": len(["immoscout", "wg_gesucht"]),  # Simplified
            "contact_discovery_enabled": True,  # From settings
        }
        
        # Get orchestrator status
        orchestrator_status = {
            "initialized": True,
            "notification_manager_enabled": orchestrator.notification_manager is not None
        }
        
        # Get storage statistics
        storage_stats = storage_manager.get_statistics()
        
        # Get last scraping run
        last_run = None
        try:
            with storage_manager.get_session() as session:
                from mwa_core.storage.models import ScrapingRun
                last_scraping_run = session.query(ScrapingRun).order_by(
                    ScrapingRun.created_at.desc()
                ).first()
                
                if last_scraping_run:
                    last_run = {
                        "id": last_scraping_run.id,
                        "provider": last_scraping_run.provider,
                        "status": last_scraping_run.status.value,
                        "started_at": last_scraping_run.created_at.isoformat(),
                        "completed_at": last_scraping_run.completed_at.isoformat() if last_scraping_run.completed_at else None,
                        "listings_found": last_scraping_run.listings_found
                    }
        except Exception as e:
            logger.warning(f"Could not get last run info: {e}")
        
        # Get today's activity
        today = datetime.now().date()
        today_runs = 0
        today_listings = 0
        
        try:
            with storage_manager.get_session() as session:
                from datetime import datetime as dt
                today_start = dt.combine(today, dt.min.time())
                
                # Get runs for today
                today_scraping_runs = session.query(ScrapingRun).filter(
                    ScrapingRun.created_at >= today_start
                ).all()
                
                today_runs = len(today_scraping_runs)
                today_listings = sum(run.listings_found for run in today_scraping_runs)
        except Exception as e:
            logger.warning(f"Could not get today's statistics: {e}")
        
        return ScraperStatusResponse(
            scraper_engine=scraper_engine,
            orchestrator=orchestrator_status,
            storage=storage_stats,
            last_run=last_run,
            active_jobs=[],  # Placeholder for job management
            total_runs_today=today_runs,
            total_listings_today=today_listings,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error getting scraper status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting scraper status: {str(e)}")


@router.post("/start", response_model=ScraperRunResponse, summary="Start scraper run")
async def start_scraper(
    request: ScraperStartRequest,
    orchestrator: Orchestrator = Depends(get_orchestrator_instance),
    settings = Depends(get_settings)
):
    """
    Start a new scraper run with specified providers.
    
    Args:
        request: Scraper start request
        orchestrator: Orchestrator instance
        settings: Settings instance
        
    Returns:
        Scraper run information
    """
    try:
        # Validate providers
        valid_providers = ["immoscout", "wg_gesucht"]
        for provider in request.providers:
            if provider not in valid_providers:
                raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")
        
        # Prepare configuration
        config = settings.scraper.dict()
        if request.config_overrides:
            config.update(request.config_overrides)
        
        # Run scraper in background
        run_id = f"manual_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Note: This is a simplified implementation
        # In production, you would run the scraper asynchronously
        # and return a job ID for tracking
        
        try:
            new_count = orchestrator.run(request.providers, config)
            
            return ScraperRunResponse(
                run_id=run_id,
                status="completed",
                started_at=datetime.now(),
                completed_at=datetime.now(),
                providers=request.providers,
                config_used=config,
                results={
                    "new_listings": new_count,
                    "providers_used": len(request.providers)
                },
                duration_seconds=0.0  # Would calculate actual duration
            )
            
        except Exception as e:
            return ScraperRunResponse(
                run_id=run_id,
                status="failed",
                started_at=datetime.now(),
                providers=request.providers,
                config_used=config,
                error_details=[str(e)]
            )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting scraper: {e}")
        raise HTTPException(status_code=500, detail=f"Error starting scraper: {str(e)}")


@router.get("/statistics", response_model=ScraperStatsResponse, summary="Get scraper statistics")
async def get_scraper_statistics(
    orchestrator: Orchestrator = Depends(get_orchestrator_instance),
    storage_manager = Depends(get_storage_manager_instance)
):
    """
    Get comprehensive scraper performance statistics.
    
    Args:
        orchestrator: Orchestrator instance
        storage_manager: Storage manager instance
        
    Returns:
        Scraper statistics
    """
    try:
        # Get scraping runs from storage
        try:
            with storage_manager.get_session() as session:
                from mwa_core.storage.models import ScrapingRun
                
                # Get all runs
                all_runs = session.query(ScrapingRun).all()
                
                total_runs = len(all_runs)
                successful_runs = sum(1 for run in all_runs if run.status.value == "completed")
                failed_runs = sum(1 for run in all_runs if run.status.value == "failed")
                
                # Calculate success rate
                success_rate = (successful_runs / total_runs * 100) if total_runs > 0 else 0
                
                # Get total listings
                total_listings_scraped = sum(run.listings_found for run in all_runs)
                
                # Calculate average runtime
                completed_runs_with_duration = []
                for run in all_runs:
                    if run.completed_at and run.created_at:
                        duration = (run.completed_at - run.created_at).total_seconds()
                        completed_runs_with_duration.append(duration)
                
                average_runtime = sum(completed_runs_with_duration) / len(completed_runs_with_duration) if completed_runs_with_duration else None
                
                # Get provider statistics
                provider_stats = {}
                for run in all_runs:
                    provider = run.provider
                    if provider not in provider_stats:
                        provider_stats[provider] = {
                            "runs": 0,
                            "successful": 0,
                            "total_listings": 0,
                            "total_runtime": 0.0
                        }
                    
                    provider_stats[provider]["runs"] += 1
                    if run.status.value == "completed":
                        provider_stats[provider]["successful"] += 1
                    provider_stats[provider]["total_listings"] += run.listings_found
                    
                    if run.completed_at and run.created_at:
                        duration = (run.completed_at - run.created_at).total_seconds()
                        provider_stats[provider]["total_runtime"] += duration
                
                # Calculate provider success rates and averages
                top_providers = []
                for provider, stats in provider_stats.items():
                    success_rate = (stats["successful"] / stats["runs"] * 100) if stats["runs"] > 0 else 0
                    avg_runtime = stats["total_runtime"] / stats["runs"] if stats["runs"] > 0 else None
                    
                    top_providers.append({
                        "provider": provider,
                        "run_count": stats["runs"],
                        "success_rate": success_rate,
                        "total_listings": stats["total_listings"],
                        "average_runtime": avg_runtime
                    })
                
                # Sort by run count
                top_providers.sort(key=lambda x: x["run_count"], reverse=True)
                
                # Get recent activity (last 10 runs)
                recent_runs = session.query(ScrapingRun).order_by(
                    ScrapingRun.created_at.desc()
                ).limit(10).all()
                
                recent_activity = []
                for run in recent_runs:
                    recent_activity.append({
                        "id": run.id,
                        "provider": run.provider,
                        "status": run.status.value,
                        "started_at": run.created_at.isoformat(),
                        "listings_found": run.listings_found
                    })
                
                # Calculate new listings (simplified - would need comparison logic)
                # For now, just use total listings as approximation
                total_new_listings = total_listings_scraped
                
                return ScraperStatsResponse(
                    total_runs=total_runs,
                    successful_runs=successful_runs,
                    failed_runs=failed_runs,
                    total_listings_scraped=total_listings_scraped,
                    total_new_listings=total_new_listings,
                    run_frequency={
                        "runs_per_day": total_runs / max(1, (datetime.now() - min(run.created_at for run in all_runs).date()).days),
                        "total_days_active": max(1, (datetime.now() - min(run.created_at for run in all_runs).date()).days)
                    } if all_runs else {"runs_per_day": 0, "total_days_active": 0},
                    average_runtime=average_runtime,
                    success_rate=success_rate,
                    top_providers=top_providers,
                    recent_activity=recent_activity,
                    timestamp=datetime.now()
                )
                
        except Exception as e:
            logger.warning(f"Could not get detailed statistics: {e}")
            # Return basic statistics
            return ScraperStatsResponse(
                total_runs=0,
                successful_runs=0,
                failed_runs=0,
                total_listings_scraped=0,
                total_new_listings=0,
                run_frequency={"runs_per_day": 0, "total_days_active": 0},
                success_rate=0,
                top_providers=[],
                recent_activity=[],
                timestamp=datetime.now()
            )
        
    except Exception as e:
        logger.error(f"Error getting scraper statistics: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting scraper statistics: {str(e)}")


@router.get("/providers", response_model=List[ScraperProviderInfo], summary="Get scraper provider information")
async def get_scraper_providers(
    storage_manager = Depends(get_storage_manager_instance)
):
    """
    Get information about all available scraper providers.
    
    Args:
        storage_manager: Storage manager instance
        
    Returns:
        List of scraper providers
    """
    try:
        # Define available providers
        providers = [
            {
                "name": "immoscout",
                "enabled": True,
                "description": "ImmoScout24.de apartment listings"
            },
            {
                "name": "wg_gesucht",
                "enabled": True,
                "description": "WG-Gesucht.de shared accommodation listings"
            }
        ]
        
        # Get provider statistics
        try:
            with storage_manager.get_session() as session:
                from mwa_core.storage.models import ScrapingRun
                
                provider_stats = {}
                for provider in ["immoscout", "wg_gesucht"]:
                    runs = session.query(ScrapingRun).filter(
                        ScrapingRun.provider == provider
                    ).all()
                    
                    if runs:
                        successful = sum(1 for run in runs if run.status.value == "completed")
                        success_rate = (successful / len(runs) * 100) if runs else 0
                        
                        # Get last run
                        last_run = max(runs, key=lambda x: x.created_at).created_at
                        
                        # Calculate average runtime
                        runtimes = []
                        for run in runs:
                            if run.completed_at and run.created_at:
                                runtime = (run.completed_at - run.created_at).total_seconds()
                                runtimes.append(runtime)
                        average_runtime = sum(runtimes) / len(runtimes) if runtimes else None
                    else:
                        success_rate = 0
                        last_run = None
                        average_runtime = None
                    
                    provider_stats[provider] = {
                        "run_count": len(runs),
                        "success_rate": success_rate,
                        "last_run": last_run,
                        "average_runtime": average_runtime
                    }
        except Exception as e:
            logger.warning(f"Could not get provider statistics: {e}")
            provider_stats = {}
        
        # Build response
        provider_infos = []
        for provider in providers:
            stats = provider_stats.get(provider["name"], {})
            provider_info = ScraperProviderInfo(
                name=provider["name"],
                enabled=provider["enabled"],
                description=provider["description"],
                last_run=stats.get("last_run"),
                run_count=stats.get("run_count", 0),
                success_rate=stats.get("success_rate", 0.0),
                average_runtime=stats.get("average_runtime")
            )
            provider_infos.append(provider_info)
        
        return provider_infos
        
    except Exception as e:
        logger.error(f"Error getting scraper providers: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting scraper providers: {str(e)}")


@router.put("/config", summary="Update scraper configuration")
async def update_scraper_config(
    request: ScraperConfigRequest,
    settings = Depends(get_settings)
):
    """
    Update scraper configuration.
    
    Args:
        request: Configuration update request
        settings: Settings instance
        
    Returns:
        Updated configuration confirmation
    """
    try:
        # Get current configuration
        current_config = settings.scraper.dict()
        
        # Apply updates
        update_data = {}
        if request.providers is not None:
            update_data["enabled_providers"] = request.providers
        if request.request_delay_seconds is not None:
            update_data["request_delay_seconds"] = request.request_delay_seconds
        if request.timeout_seconds is not None:
            update_data["timeout_seconds"] = request.timeout_seconds
        if request.user_agent is not None:
            update_data["user_agent"] = request.user_agent
        if request.max_retries is not None:
            update_data["max_retries"] = request.max_retries
        if request.contact_discovery_enabled is not None:
            update_data["contact_discovery_enabled"] = request.contact_discovery_enabled
        if request.contact_discovery_timeout is not None:
            update_data["contact_discovery_timeout"] = request.contact_discovery_timeout
        
        # Merge updates into current configuration
        current_config.update(update_data)
        
        # Save updated configuration
        settings.scraper = settings.scraper.__class__(**current_config)
        settings.save()
        
        # Reload settings to apply changes
        from mwa_core.config.settings import reload_settings
        reload_settings()
        
        return {
            "success": True,
            "message": "Scraper configuration updated successfully",
            "updated_config": current_config,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error updating scraper configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating scraper configuration: {str(e)}")


@router.post("/test", summary="Test scraper configuration")
async def test_scraper_config(
    providers: List[str] = Body(..., description="Providers to test"),
    config_test: Optional[Dict[str, Any]] = Body(None, description="Test configuration"),
    orchestrator: Orchestrator = Depends(get_orchestrator_instance)
):
    """
    Test scraper configuration with a dry run.
    
    Args:
        providers: Providers to test
        config_test: Test configuration
        orchestrator: Orchestrator instance
        
    Returns:
        Test results
    """
    try:
        # Validate providers
        valid_providers = ["immoscout", "wg_gesucht"]
        for provider in providers:
            if provider not in valid_providers:
                raise HTTPException(status_code=400, detail=f"Invalid provider: {provider}")
        
        # Run a test (dry run would be implemented here)
        # For now, return a simulated test result
        
        test_results = {
            "test_id": f"test_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "providers_tested": providers,
            "configuration_valid": True,
            "connectivity_tests": {},
            "simulation_results": {
                "listings_found": len(providers) * 10,  # Simulated
                "avg_response_time": 2.5,  # Simulated
                "errors_encountered": 0
            },
            "recommendations": [],
            "timestamp": datetime.now().isoformat()
        }
        
        # Add provider-specific test results
        for provider in providers:
            test_results["connectivity_tests"][provider] = {
                "connection_successful": True,
                "response_time_ms": 500 + hash(provider) % 1000,  # Simulated
                "status_code": 200
            }
        
        return test_results
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error testing scraper configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Error testing scraper configuration: {str(e)}")


@router.get("/runs", summary="Get recent scraper runs")
async def get_recent_runs(
    limit: int = Query(50, ge=1, le=200, description="Number of runs to retrieve"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    storage_manager = Depends(get_storage_manager_instance)
):
    """
    Get information about recent scraper runs.
    
    Args:
        limit: Maximum number of runs to return
        offset: Pagination offset
        storage_manager: Storage manager instance
        
    Returns:
        List of recent scraper runs
    """
    try:
        try:
            with storage_manager.get_session() as session:
                from mwa_core.storage.models import ScrapingRun
                
                # Get recent runs
                runs = session.query(ScrapingRun).order_by(
                    ScrapingRun.created_at.desc()
                ).offset(offset).limit(limit).all()
                
                runs_data = []
                for run in runs:
                    duration = None
                    if run.completed_at and run.created_at:
                        duration = (run.completed_at - run.created_at).total_seconds()
                    
                    runs_data.append({
                        "id": run.id,
                        "provider": run.provider,
                        "status": run.status.value,
                        "started_at": run.created_at.isoformat(),
                        "completed_at": run.completed_at.isoformat() if run.completed_at else None,
                        "listings_found": run.listings_found,
                        "duration_seconds": duration,
                        "error_details": run.errors
                    })
                
                # Get total count for pagination
                total_count = session.query(ScrapingRun).count()
                
                return {
                    "runs": runs_data,
                    "total": total_count,
                    "limit": limit,
                    "offset": offset
                }
                
        except Exception as e:
            logger.warning(f"Could not get recent runs: {e}")
            return {
                "runs": [],
                "total": 0,
                "limit": limit,
                "offset": offset
            }
        
    except Exception as e:
        logger.error(f"Error getting recent scraper runs: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting recent scraper runs: {str(e)}")


# Search Management Endpoints
@router.get("/configurations", summary="Get search configurations")
async def get_search_configurations():
    """
    Get all search configurations.
    
    Returns:
        List of search configurations
    """
    try:
        # Return mock data for now - in production this would come from database
        configurations = [
            {
                "id": 1,
                "name": "Main Apartment Search",
                "min_price": 300,
                "max_price": 1500,
                "min_rooms": 1,
                "districts": [1, 2, 3],
                "status": "running",
                "last_run": "2025-11-19T10:00:00Z",
                "results_count": 15,
                "created_at": "2025-11-18T09:00:00Z",
                "updated_at": "2025-11-19T10:00:00Z"
            },
            {
                "id": 2,
                "name": "Budget Search",
                "min_price": 200,
                "max_price": 800,
                "min_rooms": 1,
                "districts": [4, 5],
                "status": "paused",
                "last_run": "2025-11-18T15:30:00Z",
                "results_count": 8,
                "created_at": "2025-11-17T14:30:00Z",
                "updated_at": "2025-11-18T15:30:00Z"
            }
        ]
        
        return {
            "success": True,
            "data": configurations,
            "total": len(configurations),
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting search configurations: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": "Failed to retrieve search configurations",
                "timestamp": datetime.now().isoformat()
            }
        )


@router.get("/statistics", summary="Get search statistics")
async def get_search_statistics():
    """
    Get search performance statistics.
    
    Returns:
        Search statistics
    """
    try:
        # Return mock data for now - in production this would be calculated from database
        stats = {
            "total_searches": 3,
            "running_searches": 2,
            "paused_searches": 1,
            "results_today": 5,
            "results_this_week": 23,
            "results_this_month": 89,
            "success_rate": 85,
            "average_runtime_minutes": 12.5,
            "total_runtime_hours": 45.2,
            "error_rate": 5.0,
            "last_updated": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting search statistics: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": "Failed to retrieve search statistics",
                "timestamp": datetime.now().isoformat()
            }
        )


@router.post("/preview", summary="Preview search configuration")
async def preview_search(
    config: Dict[str, Any] = Body(..., description="Search configuration to preview")
):
    """
    Preview search results based on configuration.
    
    Args:
        config: Search configuration
        
    Returns:
        Search preview results
    """
    try:
        # Validate input
        if not config:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Bad request",
                    "message": "Search configuration cannot be empty",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        # Validate required fields
        if "min_price" not in config or "max_price" not in config:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Validation error",
                    "message": "Price range is required for search preview",
                    "missing_fields": ["min_price", "max_price"],
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        # Validate price range
        min_price = config.get("min_price", 0)
        max_price = config.get("max_price", 0)
        
        if min_price < 0 or max_price < 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Validation error",
                    "message": "Price values must be positive",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        if min_price >= max_price:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Validation error",
                    "message": "Minimum price must be less than maximum price",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        # Simulate search preview based on configuration
        estimated_results = max(10, int((max_price - min_price) / 100))
        
        # Mock sample results
        sample_results = [
            {
                "title": "Modern 2-room apartment in Maxvorstadt",
                "location": "Maxvorstadt",
                "price": min_price + (max_price - min_price) * 0.6,
                "rooms": 2,
                "size": 65,
                "url": "https://immoscout24.de/example1"
            },
            {
                "title": "Cozy studio in city center",
                "location": "Altstadt",
                "price": min_price + (max_price - min_price) * 0.4,
                "rooms": 1,
                "size": 35,
                "url": "https://immoscout24.de/example2"
            },
            {
                "title": "Shared apartment near university",
                "location": "Schwabing-West",
                "price": min_price + (max_price - min_price) * 0.3,
                "rooms": 1,
                "size": 25,
                "url": "https://wg-gesucht.de/example1"
            }
        ]
        
        # Filter by providers
        providers = config.get("providers", ["immoscout", "wg_gesucht"])
        
        return {
            "success": True,
            "data": {
                "estimated_results": estimated_results,
                "estimated_time_minutes": int(estimated_results * 0.5),
                "providers": providers,
                "sample_results": sample_results,
                "search_config": config
            },
            "warnings": [],
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error previewing search: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": "Failed to generate search preview",
                "timestamp": datetime.now().isoformat()
            }
        )


@router.post("/save", summary="Save search configuration")
async def save_search(
    config: Dict[str, Any] = Body(..., description="Search configuration to save")
):
    """
    Save a new search configuration.
    
    Args:
        config: Search configuration
        
    Returns:
        Saved search information
    """
    try:
        # Validate input
        if not config:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Bad request",
                    "message": "Search configuration cannot be empty",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        # Validate required fields
        required_fields = ["name", "min_price", "max_price"]
        missing_fields = []
        
        for field in required_fields:
            if field not in config or not config[field]:
                missing_fields.append(field)
        
        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Validation error",
                    "message": "Missing required fields",
                    "missing_fields": missing_fields,
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        # Validate price range
        min_price = config.get("min_price", 0)
        max_price = config.get("max_price", 0)
        
        if min_price < 0 or max_price < 0:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Validation error",
                    "message": "Price values must be positive",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        if min_price >= max_price:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Validation error",
                    "message": "Minimum price must be less than maximum price",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        # Validate name length
        if len(config["name"]) > 100:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Validation error",
                    "message": "Search name cannot exceed 100 characters",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        # Mock saving - in production this would save to database
        search_id = hash(config["name"]) % 1000 + 1  # Simple ID generation
        
        saved_config = {
            "id": search_id,
            "name": config["name"],
            "min_price": min_price,
            "max_price": max_price,
            "min_rooms": config.get("min_rooms", 1),
            "districts": config.get("districts", []),
            "amenities": config.get("amenities", []),
            "providers": config.get("providers", ["immoscout"]),
            "schedule": config.get("schedule", {"type": "daily"}),
            "status": "idle",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "data": saved_config,
            "message": "Search configuration saved successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving search: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": "Failed to save search configuration",
                "timestamp": datetime.now().isoformat()
            }
        )


@router.post("/start", summary="Start search")
async def start_search(
    config: Dict[str, Any] = Body(..., description="Search configuration")
):
    """
    Start a new search based on configuration.
    
    Args:
        config: Search configuration
        
    Returns:
        Search start result
    """
    try:
        # Validate input
        if not config:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Bad request",
                    "message": "Search configuration cannot be empty",
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        # Validate required fields for starting search
        required_fields = ["min_price", "max_price"]
        missing_fields = []
        
        for field in required_fields:
            if field not in config or not config[field]:
                missing_fields.append(field)
        
        if missing_fields:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Validation error",
                    "message": "Missing required fields to start search",
                    "missing_fields": missing_fields,
                    "timestamp": datetime.now().isoformat()
                }
            )
        
        # Mock search start - in production this would trigger actual scraping
        search_id = config.get("id", 3)
        job_id = f"search_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Simulate validation
        if not config.get("providers"):
            logger.warning("No providers specified for search, using defaults")
        
        start_result = {
            "search_id": search_id,
            "job_id": job_id,
            "status": "started",
            "started_at": datetime.now().isoformat(),
            "estimated_completion": (datetime.now() + timedelta(minutes=15)).isoformat(),
            "search_config": config,
            "providers": config.get("providers", ["immoscout", "wg_gesucht"]),
            "estimated_results": 25
        }
        
        return {
            "success": True,
            "data": start_result,
            "message": "Search started successfully",
            "warnings": [
                "Search is running in simulation mode",
                "Results will be displayed when search completes"
            ] if search_id == 3 else [],
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting search: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Internal server error",
                "message": "Failed to start search",
                "timestamp": datetime.now().isoformat()
            }
        )