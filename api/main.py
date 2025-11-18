"""FastAPI dashboard for MAFA."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Dict

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from mafa.config.settings import Settings
from mafa.db.manager import ListingRepository
from mafa.orchestrator import run as orchestrator_run
from mafa.providers import build_providers, PROVIDER_REGISTRY
from mafa.scheduler import SchedulerService


app = FastAPI(title="MAFA Dashboard", description="Munich Apartment Finder Assistant Dashboard")
settings = Settings.load()


class RunRequest(BaseModel):
    """Request body for manual run endpoint."""
    config_path: Optional[Path] = None
    job_id: Optional[str] = None
    run_at: Optional[str] = None  # ISO timestamp


class ProviderInfo(BaseModel):
    name: str
    class_name: str
    description: Optional[str] = None


class ListingInfo(BaseModel):
    id: int
    title: str
    price: str
    source: str
    timestamp: str
    url: Optional[str] = None


@app.get("/", response_class=HTMLResponse)
def dashboard():
    """Simple HTML dashboard."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>MAFA Dashboard</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; }
            .card { border: 1px solid #ccc; padding: 20px; margin: 10px 0; border-radius: 5px; }
            .btn { background: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 3px; }
        </style>
    </head>
    <body>
        <h1>MAFA Dashboard</h1>
        <div class="card">
            <h2>Providers</h2>
            <p>Configured scrapers: {providers}</p>
            <a href="/providers" class="btn">View Providers</a>
        </div>
        <div class="card">
            <h2>Run Scraper</h2>
            <form action="/run" method="post">
                <input type="submit" value="Run Now" class="btn">
            </form>
        </div>
        <div class="card">
            <h2>Latest Listings</h2>
            <a href="/listings" class="btn">View Listings</a>
        </div>
    </body>
    </html>
    """.format(providers=", ".join(settings.scrapers))
    return HTMLResponse(content=html)


@app.get("/providers")
def list_providers() -> List[ProviderInfo]:
    """List available providers and their current configuration."""
    providers = []
    for name, cls in PROVIDER_REGISTRY.items():
        providers.append(ProviderInfo(name=name, class_name=cls.__name__))
    return providers


@app.post("/run")
def run_scraper(request: RunRequest):
    """Trigger a manual scraper run."""
    try:
        orchestrator_run(config_path=request.config_path)
        return {"status": "success", "message": "Scraper run initiated"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/listings")
def list_listings(limit: int = 50) -> List[ListingInfo]:
    """Retrieve recent listings from the database."""
    repo = ListingRepository()
    # Simple implementation: fetch raw listings and map to model
    # For a real application, add proper pagination.
    listings = []
    # NOTE: The ListingRepository currently doesn't expose a list method.
    # This is a simplified placeholder implementation.
    # In production you would add a `list_recent` method to the repository.
    return listings


# Dependency to get the scheduler instance
def get_scheduler() -> SchedulerService:
    """Provide a SchedulerService instance."""
    return SchedulerService(settings)


@app.get("/scheduler/status")
def scheduler_status(scheduler: SchedulerService = Depends(get_scheduler)):
    """Get scheduler status and job list."""
    jobs = []
    for job in scheduler.scheduler.get_jobs():
        jobs.append({"id": job.id, "next_run": job.next_run_time})
    return {"running": scheduler.scheduler.running, "jobs": jobs}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)