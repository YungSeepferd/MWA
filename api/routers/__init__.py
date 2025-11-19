"""
FastAPI routers package for MWA Core API.

This package contains modular routers for different aspects of the MWA system:
- config: Configuration management endpoints
- listings: Listing management endpoints  
- contacts: Contact management endpoints
- scraper: Scraper control endpoints
- scheduler: Scheduler management endpoints
- system: System status and health check endpoints
"""

from fastapi import APIRouter

# Import all routers
from .config import router as config_router
from .listings import router as listings_router
from .contacts import router as contacts_router
from .scraper import router as scraper_router
from .scheduler import router as scheduler_router
from .system import router as system_router


def create_api_router() -> APIRouter:
    """
    Create and configure the main API router with all sub-routers.
    
    Returns:
        Configured APIRouter instance with all endpoints
    """
    api_router = APIRouter()
    
    # Include all sub-routers with appropriate prefixes
    api_router.include_router(
        config_router, 
        prefix="/config", 
        tags=["Configuration"]
    )
    
    api_router.include_router(
        listings_router, 
        prefix="/listings", 
        tags=["Listings"]
    )
    
    api_router.include_router(
        contacts_router, 
        prefix="/contacts", 
        tags=["Contacts"]
    )
    
    api_router.include_router(
        scraper_router, 
        prefix="/scraper", 
        tags=["Scraper"]
    )
    
    api_router.include_router(
        scheduler_router, 
        prefix="/scheduler", 
        tags=["Scheduler"]
    )
    
    api_router.include_router(
        system_router, 
        prefix="/system", 
        tags=["System"]
    )
    
    return api_router


# Export the main router factory function
__all__ = ["create_api_router"]