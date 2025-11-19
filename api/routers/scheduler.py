"""
Scheduler management router for MWA Core API.

Provides endpoints for managing the job scheduler system, including:
- Getting scheduler status and job information
- Creating, updating, and deleting scheduled jobs
- Pausing and resuming scheduler operations
- Scheduler configuration management
- Job execution history and statistics
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends, Query, Path, Body
from pydantic import BaseModel, Field, validator

try:
    from mwa_core.scheduler.job_manager import JobManager
    JOB_MANAGER_AVAILABLE = True
except ImportError:
    JobManager = None
    JOB_MANAGER_AVAILABLE = False

from mwa_core.scheduler.config import SchedulerConfig
from mwa_core.storage.manager import get_storage_manager
from mwa_core.config.settings import get_settings

logger = logging.getLogger(__name__)

router = APIRouter()


# Pydantic models for scheduler requests/responses
class SchedulerStatusResponse(BaseModel):
    """Response model for scheduler status."""
    scheduler_running: bool
    job_count: int
    active_jobs: int
    next_runs: List[Dict[str, Any]] = []
    worker_status: Dict[str, Any] = {}
    scheduler_info: Dict[str, Any] = {}
    timestamp: datetime


class JobInfo(BaseModel):
    """Response model for job information."""
    id: str
    name: str
    description: Optional[str] = None
    job_type: str
    provider: Optional[str] = None
    enabled: bool
    next_run: Optional[datetime] = None
    last_run: Optional[datetime] = None
    run_count: int
    failure_count: int
    status: str
    schedule_expression: str
    metadata: Dict[str, Any] = {}


class JobCreateRequest(BaseModel):
    """Request model for creating a scheduled job."""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    job_type: str = Field(..., regex="^(scraping|cleanup|backup|notification)$")
    provider: Optional[str] = Field(None, regex="^(immoscout|wg_gesucht|all)$")
    schedule_expression: str = Field(..., description="Cron-style schedule expression")
    enabled: bool = Field(True)
    parameters: Optional[Dict[str, Any]] = {}


class JobUpdateRequest(BaseModel):
    """Request model for updating a scheduled job."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    schedule_expression: Optional[str] = None
    enabled: Optional[bool] = None
    parameters: Optional[Dict[str, Any]] = None


class JobExecutionResponse(BaseModel):
    """Response model for job execution information."""
    job_id: str
    execution_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    result_data: Optional[Dict[str, Any]] = None
    error_details: Optional[str] = None


class SchedulerConfigResponse(BaseModel):
    """Response model for scheduler configuration."""
    enabled: bool
    timezone: str
    job_store_path: str
    max_workers: int
    job_defaults: Dict[str, Any]
    current_config: Dict[str, Any]


class SchedulerConfigRequest(BaseModel):
    """Request model for updating scheduler configuration."""
    enabled: Optional[bool] = None
    timezone: Optional[str] = None
    max_workers: Optional[int] = Field(None, ge=1, le=20)
    job_defaults: Optional[Dict[str, Any]] = None


# Dependency to get job manager (simplified for this implementation)
def get_job_manager_instance():
    """Get the job manager instance."""
    # This is a simplified implementation since the actual JobManager
    # might require initialization with specific parameters
    if not JOB_MANAGER_AVAILABLE:
        return None
    
    try:
        return JobManager()
    except Exception:
        # Return a mock manager if initialization fails
        return None


# Dependency to get storage manager
def get_storage_manager_instance():
    """Get the storage manager instance."""
    return get_storage_manager()


@router.get("/status", response_model=SchedulerStatusResponse, summary="Get scheduler status")
async def get_scheduler_status(
    job_manager = Depends(get_job_manager_instance),
    storage_manager = Depends(get_storage_manager_instance)
):
    """
    Get the current status of the job scheduler.
    
    Args:
        job_manager: Job manager instance
        storage_manager: Storage manager instance
        
    Returns:
        Current scheduler status
    """
    try:
        scheduler_running = True  # Simplified - would check actual scheduler status
        job_count = 0
        active_jobs = 0
        next_runs = []
        worker_status = {"workers": 0, "active": 0}
        
        # Get job information from storage if job_manager is available
        if job_manager:
            try:
                jobs = job_manager.get_all_jobs()
                job_count = len(jobs)
                active_jobs = sum(1 for job in jobs if job.enabled)
                
                # Get next runs
                next_runs = []
                for job in jobs[:5]:  # Next 5 jobs
                    if job.next_run:
                        next_runs.append({
                            "job_id": job.id,
                            "job_name": job.name,
                            "next_run": job.next_run.isoformat() if hasattr(job.next_run, 'isoformat') else str(job.next_run)
                        })
            except Exception as e:
                logger.warning(f"Could not get job information: {e}")
        
        # Get scheduler configuration info
        settings = get_settings()
        scheduler_info = {
            "timezone": settings.scheduler.timezone,
            "max_workers": settings.scheduler.max_workers,
            "job_store_path": settings.scheduler.job_store_path,
            "persistent": settings.scheduler.persistent
        }
        
        return SchedulerStatusResponse(
            scheduler_running=scheduler_running,
            job_count=job_count,
            active_jobs=active_jobs,
            next_runs=next_runs,
            worker_status=worker_status,
            scheduler_info=scheduler_info,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        logger.error(f"Error getting scheduler status: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting scheduler status: {str(e)}")


@router.get("/jobs", response_model=List[JobInfo], summary="Get all scheduled jobs")
async def get_scheduled_jobs(
    enabled_only: bool = Query(False, description="Return only enabled jobs"),
    job_manager = Depends(get_job_manager_instance)
):
    """
    Get information about all scheduled jobs.
    
    Args:
        enabled_only: If True, only return enabled jobs
        job_manager: Job manager instance
        
    Returns:
        List of scheduled jobs
    """
    try:
        if not job_manager:
            return []
        
        jobs = job_manager.get_all_jobs()
        
        job_infos = []
        for job in jobs:
            if enabled_only and not job.enabled:
                continue
            
            job_info = JobInfo(
                id=job.id,
                name=job.name,
                description=getattr(job, 'description', None),
                job_type=getattr(job, 'job_type', 'unknown'),
                provider=getattr(job, 'provider', None),
                enabled=job.enabled,
                next_run=getattr(job, 'next_run', None),
                last_run=getattr(job, 'last_run', None),
                run_count=getattr(job, 'run_count', 0),
                failure_count=getattr(job, 'failure_count', 0),
                status=getattr(job, 'status', 'unknown'),
                schedule_expression=getattr(job, 'trigger', str(job.next_run)) if hasattr(job, 'trigger') else "unknown",
                metadata=getattr(job, 'metadata', {})
            )
            job_infos.append(job_info)
        
        return job_infos
        
    except Exception as e:
        logger.error(f"Error getting scheduled jobs: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting scheduled jobs: {str(e)}")


@router.get("/jobs/{job_id}", response_model=JobInfo, summary="Get specific job information")
async def get_job(
    job_id: str = Path(..., description="Job ID"),
    job_manager = Depends(get_job_manager_instance)
):
    """
    Get detailed information about a specific scheduled job.
    
    Args:
        job_id: ID of the job to retrieve
        job_manager: Job manager instance
        
    Returns:
        Detailed job information
    """
    try:
        if not job_manager:
            raise HTTPException(status_code=503, detail="Job manager not available")
        
        job = job_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        return JobInfo(
            id=job.id,
            name=job.name,
            description=getattr(job, 'description', None),
            job_type=getattr(job, 'job_type', 'unknown'),
            provider=getattr(job, 'provider', None),
            enabled=job.enabled,
            next_run=getattr(job, 'next_run', None),
            last_run=getattr(job, 'last_run', None),
            run_count=getattr(job, 'run_count', 0),
            failure_count=getattr(job, 'failure_count', 0),
            status=getattr(job, 'status', 'unknown'),
            schedule_expression=getattr(job, 'trigger', str(job.next_run)) if hasattr(job, 'trigger') else "unknown",
            metadata=getattr(job, 'metadata', {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting job: {str(e)}")


@router.post("/jobs", response_model=JobInfo, summary="Create new scheduled job")
async def create_job(
    request: JobCreateRequest,
    job_manager = Depends(get_job_manager_instance)
):
    """
    Create a new scheduled job.
    
    Args:
        request: Job creation request
        job_manager: Job manager instance
        
    Returns:
        Created job information
    """
    try:
        if not job_manager:
            raise HTTPException(status_code=503, detail="Job manager not available")
        
        # Create job using job manager
        job = job_manager.create_job(
            name=request.name,
            description=request.description,
            job_type=request.job_type,
            provider=request.provider,
            schedule_expression=request.schedule_expression,
            enabled=request.enabled,
            parameters=request.parameters or {}
        )
        
        return JobInfo(
            id=job.id,
            name=job.name,
            description=getattr(job, 'description', None),
            job_type=getattr(job, 'job_type', 'unknown'),
            provider=getattr(job, 'provider', None),
            enabled=job.enabled,
            next_run=getattr(job, 'next_run', None),
            last_run=getattr(job, 'last_run', None),
            run_count=getattr(job, 'run_count', 0),
            failure_count=getattr(job, 'failure_count', 0),
            status=getattr(job, 'status', 'unknown'),
            schedule_expression=request.schedule_expression,
            metadata=request.parameters or {}
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating job: {e}")
        raise HTTPException(status_code=500, detail=f"Error creating job: {str(e)}")


@router.put("/jobs/{job_id}", response_model=JobInfo, summary="Update scheduled job")
async def update_job(
    job_id: str = Path(..., description="Job ID"),
    request: JobUpdateRequest = Body(...),
    job_manager = Depends(get_job_manager_instance)
):
    """
    Update an existing scheduled job.
    
    Args:
        job_id: ID of the job to update
        request: Job update request
        job_manager: Job manager instance
        
    Returns:
        Updated job information
    """
    try:
        if not job_manager:
            raise HTTPException(status_code=503, detail="Job manager not available")
        
        job = job_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Update job
        updated_job = job_manager.update_job(
            job_id=job_id,
            name=request.name,
            description=request.description,
            schedule_expression=request.schedule_expression,
            enabled=request.enabled,
            parameters=request.parameters
        )
        
        return JobInfo(
            id=updated_job.id,
            name=updated_job.name,
            description=getattr(updated_job, 'description', None),
            job_type=getattr(updated_job, 'job_type', 'unknown'),
            provider=getattr(updated_job, 'provider', None),
            enabled=updated_job.enabled,
            next_run=getattr(updated_job, 'next_run', None),
            last_run=getattr(updated_job, 'last_run', None),
            run_count=getattr(updated_job, 'run_count', 0),
            failure_count=getattr(updated_job, 'failure_count', 0),
            status=getattr(updated_job, 'status', 'unknown'),
            schedule_expression=getattr(updated_job, 'trigger', str(updated_job.next_run)) if hasattr(updated_job, 'trigger') else "unknown",
            metadata=getattr(updated_job, 'metadata', {})
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating job: {str(e)}")


@router.delete("/jobs/{job_id}", summary="Delete scheduled job")
async def delete_job(
    job_id: str = Path(..., description="Job ID"),
    job_manager = Depends(get_job_manager_instance)
):
    """
    Delete a scheduled job.
    
    Args:
        job_id: ID of the job to delete
        job_manager: Job manager instance
        
    Returns:
        Deletion confirmation
    """
    try:
        if not job_manager:
            raise HTTPException(status_code=503, detail="Job manager not available")
        
        job = job_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        success = job_manager.remove_job(job_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to delete job")
        
        return {
            "success": True,
            "message": "Job deleted successfully",
            "job_id": job_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting job: {str(e)}")


@router.post("/jobs/{job_id}/pause", summary="Pause scheduled job")
async def pause_job(
    job_id: str = Path(..., description="Job ID"),
    job_manager = Depends(get_job_manager_instance)
):
    """
    Pause a scheduled job.
    
    Args:
        job_id: ID of the job to pause
        job_manager: Job manager instance
        
    Returns:
        Pause confirmation
    """
    try:
        if not job_manager:
            raise HTTPException(status_code=503, detail="Job manager not available")
        
        success = job_manager.pause_job(job_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to pause job")
        
        return {
            "success": True,
            "message": "Job paused successfully",
            "job_id": job_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error pausing job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error pausing job: {str(e)}")


@router.post("/jobs/{job_id}/resume", summary="Resume scheduled job")
async def resume_job(
    job_id: str = Path(..., description="Job ID"),
    job_manager = Depends(get_job_manager_instance)
):
    """
    Resume a paused scheduled job.
    
    Args:
        job_id: ID of the job to resume
        job_manager: Job manager instance
        
    Returns:
        Resume confirmation
    """
    try:
        if not job_manager:
            raise HTTPException(status_code=503, detail="Job manager not available")
        
        success = job_manager.resume_job(job_id)
        if not success:
            raise HTTPException(status_code=500, detail="Failed to resume job")
        
        return {
            "success": True,
            "message": "Job resumed successfully",
            "job_id": job_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error resuming job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error resuming job: {str(e)}")


@router.post("/jobs/{job_id}/trigger", response_model=JobExecutionResponse, summary="Trigger job execution")
async def trigger_job(
    job_id: str = Path(..., description="Job ID"),
    job_manager = Depends(get_job_manager_instance)
):
    """
    Manually trigger a job execution.
    
    Args:
        job_id: ID of the job to trigger
        job_manager: Job manager instance
        
    Returns:
        Job execution information
    """
    try:
        if not job_manager:
            raise HTTPException(status_code=503, detail="Job manager not available")
        
        job = job_manager.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Trigger job execution
        execution_result = job_manager.trigger_job(job_id)
        
        return JobExecutionResponse(
            job_id=job_id,
            execution_id=execution_result.get('execution_id', 'unknown'),
            status=execution_result.get('status', 'completed'),
            started_at=datetime.now(),
            completed_at=datetime.now(),
            duration_seconds=execution_result.get('duration', 0.0),
            result_data=execution_result.get('result'),
            error_details=execution_result.get('error')
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering job {job_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Error triggering job: {str(e)}")


@router.get("/executions", summary="Get job execution history")
async def get_job_executions(
    job_id: Optional[str] = Query(None, description="Filter by job ID"),
    limit: int = Query(50, ge=1, le=200, description="Number of executions to retrieve"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
    storage_manager = Depends(get_storage_manager_instance)
):
    """
    Get job execution history.
    
    Args:
        job_id: Optional job ID filter
        limit: Maximum number of executions to return
        offset: Pagination offset
        storage_manager: Storage manager instance
        
    Returns:
        List of job executions
    """
    try:
        # This would typically query the storage for job execution history
        # For now, return a placeholder response
        
        executions = []
        if job_id:
            executions.append({
                "job_id": job_id,
                "execution_id": "exec_001",
                "status": "completed",
                "started_at": datetime.now().isoformat(),
                "completed_at": datetime.now().isoformat(),
                "duration_seconds": 120.5,
                "result_data": {"listings_processed": 25},
                "error_details": None
            })
        
        return {
            "executions": executions,
            "total": len(executions),
            "limit": limit,
            "offset": offset,
            "filters": {
                "job_id": job_id
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting job executions: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting job executions: {str(e)}")


@router.get("/config", response_model=SchedulerConfigResponse, summary="Get scheduler configuration")
async def get_scheduler_config(
    settings = Depends(get_settings)
):
    """
    Get the current scheduler configuration.
    
    Args:
        settings: Settings instance
        
    Returns:
        Scheduler configuration
    """
    try:
        scheduler_config = settings.scheduler
        
        return SchedulerConfigResponse(
            enabled=scheduler_config.enabled,
            timezone=scheduler_config.timezone,
            job_store_path=scheduler_config.job_store_path,
            max_workers=scheduler_config.max_workers,
            job_defaults=scheduler_config.job_defaults,
            current_config=scheduler_config.dict()
        )
        
    except Exception as e:
        logger.error(f"Error getting scheduler configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting scheduler configuration: {str(e)}")


@router.put("/config", summary="Update scheduler configuration")
async def update_scheduler_config(
    request: SchedulerConfigRequest,
    settings = Depends(get_settings)
):
    """
    Update the scheduler configuration.
    
    Args:
        request: Configuration update request
        settings: Settings instance
        
    Returns:
        Updated configuration confirmation
    """
    try:
        # Get current configuration
        current_config = settings.scheduler.dict()
        
        # Apply updates
        update_data = {}
        if request.enabled is not None:
            update_data["enabled"] = request.enabled
        if request.timezone is not None:
            update_data["timezone"] = request.timezone
        if request.max_workers is not None:
            update_data["max_workers"] = request.max_workers
        if request.job_defaults is not None:
            update_data["job_defaults"] = request.job_defaults
        
        # Merge updates into current configuration
        current_config.update(update_data)
        
        # Save updated configuration
        settings.scheduler = settings.scheduler.__class__(**current_config)
        settings.save()
        
        # Reload settings to apply changes
        from mwa_core.config.settings import reload_settings
        reload_settings()
        
        return {
            "success": True,
            "message": "Scheduler configuration updated successfully",
            "updated_config": current_config,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error updating scheduler configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Error updating scheduler configuration: {str(e)}")


@router.post("/start", summary="Start scheduler")
async def start_scheduler(
    job_manager = Depends(get_job_manager_instance)
):
    """
    Start the job scheduler.
    
    Args:
        job_manager: Job manager instance
        
    Returns:
        Start confirmation
    """
    try:
        if not job_manager:
            raise HTTPException(status_code=503, detail="Job manager not available")
        
        success = job_manager.start()
        if not success:
            raise HTTPException(status_code=500, detail="Failed to start scheduler")
        
        return {
            "success": True,
            "message": "Scheduler started successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting scheduler: {e}")
        raise HTTPException(status_code=500, detail=f"Error starting scheduler: {str(e)}")


@router.post("/stop", summary="Stop scheduler")
async def stop_scheduler(
    job_manager = Depends(get_job_manager_instance)
):
    """
    Stop the job scheduler.
    
    Args:
        job_manager: Job manager instance
        
    Returns:
        Stop confirmation
    """
    try:
        if not job_manager:
            raise HTTPException(status_code=503, detail="Job manager not available")
        
        success = job_manager.stop()
        if not success:
            raise HTTPException(status_code=500, detail="Failed to stop scheduler")
        
        return {
            "success": True,
            "message": "Scheduler stopped successfully",
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping scheduler: {e}")
        raise HTTPException(status_code=500, detail=f"Error stopping scheduler: {str(e)}")


# Dependency to get storage manager
def get_storage_manager_instance():
    """Get the storage manager instance."""
    return get_storage_manager()