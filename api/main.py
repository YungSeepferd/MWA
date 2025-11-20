"""
Enhanced FastAPI dashboard for MWA Core with comprehensive router structure.

Provides a complete API server with modular routers for:
- Configuration management
- Listing operations
- Contact management
- Scraper control
- Scheduler management
- System monitoring
- Health checks
- Contact review (existing functionality)
"""

import logging
from datetime import datetime
from typing import Dict, Any
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware

from mwa_core.config.settings import get_settings
from api.routers import create_api_router
from api.contact_review import create_contact_review_api
from api.auth import router as auth_router
from api.middleware import (
    RateLimitMiddleware,
    create_rate_limiter,
    SecurityHeadersMiddleware,
    get_production_security_config
)
from api.ws import websocket_router


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Load settings
settings = get_settings()

# Create FastAPI application with authentication
app = FastAPI(
    title="MWA Core API",
    description="Munich Apartment Finder Assistant - Core API with authentication and comprehensive router structure",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add security middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000", "http://127.0.0.1:8000", "ws://localhost:3000", "ws://localhost:8000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Authorization", "Content-Type", "X-Requested-With", "Accept", "Origin", "User-Agent"],
    max_age=86400,
)

# Add trusted host middleware for security
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["localhost", "127.0.0.1", "*.localhost"]
)

# Add security headers middleware
security_config = get_production_security_config()
security_middleware = SecurityHeadersMiddleware(app, security_config)

# Add rate limiting middleware (temporarily disabled to fix the dict callable error)
# rate_limiter_config = create_rate_limiter(
#     requests_per_minute=100,  # Allow 100 requests per minute
#     requests_per_hour=1000,   # Allow 1000 requests per hour
#     requests_per_day=10000    # Allow 10000 requests per day
# )
# app.add_middleware(
#     RateLimitMiddleware,
#     config=rate_limiter_config,
#     exempt_paths={"/", "/health", "/docs", "/redoc", "/openapi.json", "/api/info", "/api/routers"}
# )

# Include authentication router
app.include_router(
    auth_router,
    prefix="/api/v1",
    tags=["Authentication"]
)

# Include the main API router
api_router = create_api_router()
app.include_router(
    api_router,
    prefix="/api/v1",
    tags=["MWA Core API"]
)

# Include WebSocket router
app.include_router(
    websocket_router,
    prefix="/api/v1",
    tags=["WebSocket"]
)

# Include the contact review router
contact_review_app = create_contact_review_api(settings)
app.mount("/api/v1/contacts", contact_review_app)



@app.get("/", response_class=HTMLResponse)
async def root():
    """Root endpoint with API information."""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>MWA Core API</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; margin: 40px; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 40px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
            h1 { color: #2c3e50; border-bottom: 3px solid #3498db; padding-bottom: 10px; }
            h2 { color: #34495e; margin-top: 30px; }
            .endpoint { background: #ecf0f1; padding: 15px; margin: 10px 0; border-radius: 5px; border-left: 4px solid #3498db; }
            .endpoint a { color: #2980b9; text-decoration: none; font-weight: bold; }
            .endpoint a:hover { text-decoration: underline; }
            .description { margin-top: 5px; color: #7f8c8d; }
            .badge { background: #3498db; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; }
            .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin: 20px 0; }
            .stat-card { background: #3498db; color: white; padding: 20px; border-radius: 8px; text-align: center; }
            .stat-number { font-size: 2em; font-weight: bold; }
            .footer { margin-top: 40px; padding-top: 20px; border-top: 1px solid #bdc3c7; color: #7f8c8d; text-align: center; }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🏠 MWA Core API</h1>
            <p><strong>Munich Apartment Finder Assistant</strong> - Core API with comprehensive router structure</p>
            
            <div class="stats">
                <div class="stat-card">
                    <div class="stat-number">7</div>
                    <div>Router Modules</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">50+</div>
                    <div>API Endpoints</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number">Real-time</div>
                    <div>WebSocket</div>
                </div>
            </div>
            
            <h2>🚀 Available Endpoints</h2>
            
            <div class="endpoint">
                <a href="/docs">API Documentation</a> <span class="badge">Swagger UI</span>
                <div class="description">Interactive API documentation with request/response examples</div>
            </div>
            
            <div class="endpoint">
                <a href="/redoc">ReDoc Documentation</a> <span class="badge">ReDoc</span>
                <div class="description">Alternative API documentation format</div>
            </div>
            
            <div class="endpoint">
                <a href="/api/v1/config">Configuration</a> <span class="badge">GET/POST/PUT</span>
                <div class="description">Manage application settings, validation, export/import</div>
            </div>
            
            <div class="endpoint">
                <a href="/api/v1/listings">Listings</a> <span class="badge">CRUD</span>
                <div class="description">Retrieve, create, update listings with filtering and search</div>
            </div>
            
            <div class="endpoint">
                <a href="/api/v1/contacts">Contacts</a> <span class="badge">CRUD</span>
                <div class="description">Manage discovered contacts, validation, search, and export</div>
            </div>
            
            <div class="endpoint">
                <a href="/api/v1/scraper">Scraper Control</a> <span class="badge">POST/GET</span>
                <div class="description">Start/stop scrapers, monitor performance, configure parameters</div>
            </div>
            
            <div class="endpoint">
                <a href="/api/v1/scheduler">Scheduler</a> <span class="badge">CRUD</span>
                <div class="description">Manage scheduled jobs, pause/resume operations</div>
            </div>
            
            <div class="endpoint">
                <a href="/api/v1/system">System Status</a> <span class="badge">GET/POST</span>
                <div class="description">Health checks, performance metrics, component monitoring</div>
            </div>
            
            <div class="endpoint">
                <a href="/api/v1/contacts/review">Contact Review</a> <span class="badge">Dashboard</span>
                <div class="description">Comprehensive contact review and management interface</div>
            </div>
            
            <div class="endpoint">
                <a href="/api/v1/websocket/test">WebSocket Test</a> <span class="badge">Real-time</span>
                <div class="description">WebSocket testing interface for real-time communication</div>
            </div>
            
            <div class="endpoint">
                <a href="/api/v1/websocket/stats">WebSocket Stats</a> <span class="badge">Monitoring</span>
                <div class="description">Real-time connection statistics and WebSocket monitoring</div>
            </div>
            
            
            <h2>🏗️ Architecture</h2>
            <p>The API is built with a modular router structure following FastAPI best practices:</p>
            <ul>
                <li><strong>Configuration Router</strong>: Settings management with validation and export/import</li>
                <li><strong>Listings Router</strong>: Complete CRUD operations with advanced filtering</li>
                <li><strong>Contacts Router</strong>: Contact management with validation and search</li>
                <li><strong>Scraper Router</strong>: Scraper orchestration and monitoring</li>
                <li><strong>Scheduler Router</strong>: Job scheduling and management</li>
                <li><strong>System Router</strong>: Health checks and system monitoring</li>
            </ul>
            
            <h2>🔧 Integration Points</h2>
            <p>The API integrates with MWA Core components:</p>
            <ul>
                <li><code>mwa_core.config.settings</code> - Configuration management</li>
                <li><code>mwa_core.storage.manager</code> - Data persistence</li>
                <li><code>mwa_core.orchestrator</code> - Scraping coordination</li>
                <li><code>mwa_core.scheduler</code> - Job scheduling</li>
                <li><code>mwa_core.contact</code> - Contact discovery and validation</li>
            </ul>
            
            <div class="footer">
                <p>MWA Core API v1.0.0 | Built with FastAPI & MWA Core Architecture</p>
                <p>Generated on """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S") + """</p>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/health")
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "MWA Core API",
        "version": "1.0.0",
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/info")
async def api_info():
    """Get API information and available endpoints."""
    return {
        "name": "MWA Core API",
        "version": "1.0.0",
        "description": "Munich Apartment Finder Assistant - Core API",
        "routers": {
            "config": "/api/v1/config - Configuration management",
            "listings": "/api/v1/listings - Listing management",
            "contacts": "/api/v1/contacts - Contact management", 
            "scraper": "/api/v1/scraper - Scraper control",
            "scheduler": "/api/v1/scheduler - Scheduler management",
            "system": "/api/v1/system - System monitoring",
            "contact_review": "/api/v1/contacts/review - Contact review dashboard"
        },
        "documentation": {
            "swagger_ui": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        },
        "timestamp": datetime.now().isoformat()
    }


@app.get("/api/routers")
async def list_routers():
    """List all available API routers and their endpoints."""
    return {
        "routers": [
            {
                "name": "Configuration",
                "prefix": "/api/v1/config",
                "tags": ["Configuration"],
                "description": "Configuration management endpoints"
            },
            {
                "name": "Listings", 
                "prefix": "/api/v1/listings",
                "tags": ["Listings"],
                "description": "Listing management endpoints"
            },
            {
                "name": "Contacts",
                "prefix": "/api/v1/contacts", 
                "tags": ["Contacts"],
                "description": "Contact management endpoints"
            },
            {
                "name": "Scraper",
                "prefix": "/api/v1/scraper",
                "tags": ["Scraper"],
                "description": "Scraper control endpoints"
            },
            {
                "name": "Scheduler",
                "prefix": "/api/v1/scheduler",
                "tags": ["Scheduler"], 
                "description": "Scheduler management endpoints"
            },
            {
                "name": "System",
                "prefix": "/api/v1/system",
                "tags": ["System"],
                "description": "System status and monitoring endpoints"
            },
            {
                "name": "Contact Review",
                "prefix": "/api/v1/contacts",
                "tags": ["Contact Review"],
                "description": "Contact review and management dashboard"
            }
        ],
        "timestamp": datetime.now().isoformat()
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global HTTP exception handler."""
    logger.warning(f"HTTP {exc.status_code} error: {exc.detail} - {request.url}")
    return {
        "error": {
            "status_code": exc.status_code,
            "detail": exc.detail,
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url.path)
        }
    }


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global exception handler for unhandled errors."""
    logger.error(f"Unhandled exception: {exc} - {request.url}", exc_info=True)
    return {
        "error": {
            "status_code": 500,
            "detail": "Internal server error",
            "timestamp": datetime.now().isoformat(),
            "path": str(request.url.path)
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    # Get configuration from settings
    host = "0.0.0.0"
    port = 8000
    
    # Add SSL configuration if needed
    ssl_keyfile = None
    ssl_certfile = None
    
    logger.info(f"Starting MWA Core API server on {host}:{port}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=False,  # Set to True for development
        ssl_keyfile=ssl_keyfile,
        ssl_certfile=ssl_certfile,
        log_level="info"
    )