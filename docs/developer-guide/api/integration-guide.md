# MAFA Backend-to-Frontend Integration Guide

## Overview

This document provides comprehensive guidance for the backend-to-frontend integration of the MAFA (Munich Apartment Finder Assistant) application, ensuring seamless communication between the user-friendly interface and the existing backend API system.

## Architecture Overview

### Backend Architecture
- **Framework**: FastAPI with modular router structure
- **Authentication**: JWT-based with role permissions
- **Real-time**: WebSocket connections for live updates
- **Database**: SQLite with SQLAlchemy ORM
- **Background Tasks**: APScheduler for job management

### Frontend Architecture
- **Framework**: Bootstrap 5 with vanilla JavaScript
- **Components**: Modular JavaScript components for different features
- **Real-time**: WebSocket client for live updates
- **UI/UX**: Responsive design with mobile-first approach

### Communication Flow
```
Frontend (JavaScript) ↔ HTTP API ↔ Backend (FastAPI) ↔ Database
                     ↕ WebSocket ↕
               Real-time Updates
```

## API Endpoints Integration

### 1. Configuration Management (`/api/v1/config/`)

#### Endpoints
- `GET /api/v1/config/` - Get current configuration
- `PUT /api/v1/config/` - Update configuration
- `POST /api/v1/config/validate` - Validate configuration
- `POST /api/v1/config/export` - Export configuration
- `POST /api/v1/config/import` - Import configuration

#### Integration Example
```javascript
// Frontend JavaScript
async function updateConfig(configData) {
    try {
        const response = await fetch('/api/v1/config/', {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(configData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Configuration update failed');
        }
        
        return await response.json();
    } catch (error) {
        console.error('Configuration update error:', error);
        throw error;
    }
}
```

#### Validation Levels
- **Basic**: Required fields validation
- **Standard**: Business rules validation
- **Strict**: Security and performance validation

### 2. Search Management (`/api/v1/scraper/`)

#### Endpoints
- `GET /api/v1/scraper/configurations` - List search configurations
- `POST /api/v1/scraper/configurations` - Create search configuration
- `PUT /api/v1/scraper/configurations/{id}` - Update configuration
- `DELETE /api/v1/scraper/configurations/{id}` - Delete configuration
- `POST /api/v1/scraper/preview` - Preview search results
- `POST /api/v1/scraper/start` - Start scraping job
- `GET /api/v1/scraper/statistics` - Get scraping statistics

#### Integration Example
```javascript
// Search configuration creation
async function createSearchConfig(searchData) {
    try {
        const response = await fetch('/api/v1/scraper/configurations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(searchData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Search configuration creation failed');
        }
        
        return await response.json();
    } catch (error) {
        console.error('Search configuration error:', error);
        throw error;
    }
}
```

### 3. Contact Management (`/api/v1/contacts/`)

#### Endpoints
- `GET /api/v1/contacts/` - List contacts with pagination
- `GET /api/v1/contacts/{id}` - Get contact details
- `PUT /api/v1/contacts/{id}` - Update contact
- `DELETE /api/v1/contacts/{id}` - Delete contact
- `POST /api/v1/contacts/bulk` - Bulk operations
- `POST /api/v1/contacts/export` - Export contacts

#### Integration Example
```javascript
// Contact bulk operations
async function bulkUpdateContacts(contactIds, updates) {
    try {
        const response = await fetch('/api/v1/contacts/bulk', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                contact_ids: contactIds,
                updates: updates
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Bulk update failed');
        }
        
        return await response.json();
    } catch (error) {
        console.error('Bulk update error:', error);
        throw error;
    }
}
```

### 4. Analytics (`/api/v1/analytics/`)

#### Endpoints
- `GET /api/v1/analytics/dashboard` - Dashboard statistics
- `GET /api/v1/analytics/contact-discovery` - Contact discovery metrics
- `GET /api/v1/analytics/search-performance` - Search performance data
- `GET /api/v1/analytics/export` - Export analytics data

#### Integration Example
```javascript
// Analytics data retrieval
async function getDashboardStats() {
    try {
        const response = await fetch('/api/v1/analytics/dashboard', {
            method: 'GET',
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        
        if (!response.ok) {
            throw new Error('Failed to fetch dashboard statistics');
        }
        
        return await response.json();
    } catch (error) {
        console.error('Analytics error:', error);
        throw error;
    }
}
```

## WebSocket Integration

### Connection Management
```javascript
// WebSocket connection setup
class WebSocketManager {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
        this.reconnectDelay = 1000;
    }
    
    connect() {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        const wsUrl = `${protocol}//${window.location.host}/ws`;
        
        this.ws = new WebSocket(wsUrl);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
        };
        
        this.ws.onmessage = (event) => {
            const message = JSON.parse(event.data);
            this.handleMessage(message);
        };
        
        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.attemptReconnect();
        };
        
        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }
    
    handleMessage(message) {
        switch (message.type) {
            case 'DASHBOARD_UPDATE':
                this.updateDashboard(message.data);
                break;
            case 'CONTACT_UPDATE':
                this.updateContacts(message.data);
                break;
            case 'SEARCH_STATUS':
                this.updateSearchStatus(message.data);
                break;
            case 'PROGRESS_UPDATE':
                this.updateProgress(message.data);
                break;
            // Handle other message types
        }
    }
    
    attemptReconnect() {
        if (this.reconnectAttempts < this.maxReconnectAttempts) {
            setTimeout(() => {
                this.reconnectAttempts++;
                this.connect();
            }, this.reconnectDelay * Math.pow(2, this.reconnectAttempts));
        }
    }
}
```

### Message Types
- **DASHBOARD_UPDATE**: Dashboard statistics updates
- **CONTACT_UPDATE**: New/updated contacts
- **SEARCH_STATUS**: Search job status changes
- **PROGRESS_UPDATE**: Background job progress
- **ANALYTICS_UPDATE**: Analytics data updates
- **SETUP_WIZARD_UPDATE**: Setup wizard progress
- **CONFIGURATION_UPDATE**: Configuration changes
- **SYSTEM_HEALTH**: System health status

## Frontend Components Integration

### 1. Setup Wizard Component

#### Features
- 4-step wizard flow
- Real-time validation
- Auto-save functionality
- WebSocket integration
- Progress indicators

#### Integration Points
```javascript
// Setup wizard initialization
class SetupWizard {
    constructor() {
        this.currentStep = 1;
        this.totalSteps = 4;
        this.formData = {};
        this.wsManager = new WebSocketManager();
    }
    
    async saveStep(stepData) {
        try {
            const response = await fetch('/api/v1/config/', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(stepData)
            });
            
            if (!response.ok) {
                throw new Error('Failed to save step data');
            }
            
            // Broadcast update via WebSocket
            this.wsManager.broadcast({
                type: 'SETUP_WIZARD_UPDATE',
                data: {
                    step: this.currentStep,
                    status: 'completed',
                    timestamp: new Date().toISOString()
                }
            });
            
            return await response.json();
        } catch (error) {
            console.error('Setup wizard save error:', error);
            throw error;
        }
    }
}
```

### 2. Search Management Component

#### Features
- Search configuration CRUD
- Real-time preview
- Job status monitoring
- Performance analytics

#### Integration Points
```javascript
// Search management implementation
class SearchManager {
    constructor() {
        this.searchConfigs = [];
        this.activeJobs = new Map();
        this.wsManager = new WebSocketManager();
    }
    
    async createSearchConfig(configData) {
        try {
            // Validate configuration
            const validationResponse = await fetch('/api/v1/scraper/preview', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(configData)
            });
            
            if (!validationResponse.ok) {
                const error = await validationResponse.json();
                throw new Error(error.detail || 'Search validation failed');
            }
            
            // Create configuration
            const createResponse = await fetch('/api/v1/scraper/configurations', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify(configData)
            });
            
            return await createResponse.json();
        } catch (error) {
            console.error('Search config creation error:', error);
            throw error;
        }
    }
    
    async startSearchJob(configId) {
        try {
            const response = await fetch('/api/v1/scraper/start', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({ config_id: configId })
            });
            
            if (!response.ok) {
                throw new Error('Failed to start search job');
            }
            
            const job = await response.json();
            this.activeJobs.set(configId, job);
            
            // Start monitoring via WebSocket
            this.wsManager.broadcast({
                type: 'SEARCH_STATUS',
                data: {
                    config_id: configId,
                    job_id: job.id,
                    status: 'running',
                    timestamp: new Date().toISOString()
                }
            });
            
            return job;
        } catch (error) {
            console.error('Search job start error:', error);
            throw error;
        }
    }
}
```

### 3. Contact Review Component

#### Features
- Contact CRUD operations
- Bulk operations
- Filtering and pagination
- Real-time updates
- Export functionality

#### Integration Points
```javascript
// Contact review implementation
class ContactReview {
    constructor() {
        this.contacts = [];
        this.selectedContacts = new Set();
        this.wsManager = new WebSocketManager();
    }
    
    async loadContacts(page = 1, filters = {}) {
        try {
            const params = new URLSearchParams({
                page: page.toString(),
                limit: '20',
                ...filters
            });
            
            const response = await fetch(`/api/v1/contacts/?${params}`, {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to load contacts');
            }
            
            const data = await response.json();
            this.contacts = data.contacts;
            return data;
        } catch (error) {
            console.error('Contact loading error:', error);
            throw error;
        }
    }
    
    async bulkUpdate(updates) {
        try {
            const contactIds = Array.from(this.selectedContacts);
            
            const response = await fetch('/api/v1/contacts/bulk', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${token}`
                },
                body: JSON.stringify({
                    contact_ids: contactIds,
                    updates: updates
                })
            });
            
            if (!response.ok) {
                throw new Error('Bulk update failed');
            }
            
            const result = await response.json();
            
            // Broadcast update via WebSocket
            this.wsManager.broadcast({
                type: 'CONTACT_UPDATE',
                data: {
                    updated_contacts: result.updated_contacts,
                    timestamp: new Date().toISOString()
                }
            });
            
            return result;
        } catch (error) {
            console.error('Bulk update error:', error);
            throw error;
        }
    }
}
```

### 4. Analytics Dashboard Component

#### Features
- Real-time statistics
- Interactive charts
- Data export
- Performance metrics

#### Integration Points
```javascript
// Analytics dashboard implementation
class AnalyticsDashboard {
    constructor() {
        this.charts = new Map();
        this.wsManager = new WebSocketManager();
    }
    
    async loadDashboardData() {
        try {
            const response = await fetch('/api/v1/analytics/dashboard', {
                method: 'GET',
                headers: {
                    'Authorization': `Bearer ${token}`
                }
            });
            
            if (!response.ok) {
                throw new Error('Failed to load dashboard data');
            }
            
            const data = await response.json();
            this.updateCharts(data);
            return data;
        } catch (error) {
            console.error('Dashboard data loading error:', error);
            throw error;
        }
    }
    
    updateCharts(data) {
        // Update contact discovery chart
        if (this.charts.has('contactDiscovery')) {
            const chart = this.charts.get('contactDiscovery');
            chart.data.labels = data.contact_discovery.labels;
            chart.data.datasets[0].data = data.contact_discovery.values;
            chart.update();
        }
        
        // Update search performance chart
        if (this.charts.has('searchPerformance')) {
            const chart = this.charts.get('searchPerformance');
            chart.data.labels = data.search_performance.labels;
            chart.data.datasets[0].data = data.search_performance.values;
            chart.update();
        }
    }
    
    initializeCharts() {
        // Chart.js initialization
        const contactCtx = document.getElementById('contactDiscoveryChart').getContext('2d');
        this.charts.set('contactDiscovery', new Chart(contactCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Contacts Discovered',
                    data: [],
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        }));
    }
}
```

## Error Handling Integration

### Frontend Error Handling
```javascript
// Global error handler
class ErrorHandler {
    static handle(error, context = '') {
        console.error(`Error in ${context}:`, error);
        
        // Show user-friendly error message
        const errorMessage = this.getErrorMessage(error);
        this.showUserMessage(errorMessage, 'error');
        
        // Log error for debugging
        this.logError(error, context);
    }
    
    static getErrorMessage(error) {
        if (error.response) {
            // API error
            const status = error.response.status;
            const data = error.response.data;
            
            switch (status) {
                case 400:
                    return data.detail || 'Invalid request data';
                case 401:
                    return 'Authentication required';
                case 403:
                    return 'Insufficient permissions';
                case 404:
                    return 'Resource not found';
                case 422:
                    return data.detail || 'Validation error';
                case 500:
                    return 'Server error occurred';
                default:
                    return data.detail || 'An error occurred';
            }
        } else if (error.message) {
            return error.message;
        } else {
            return 'An unexpected error occurred';
        }
    }
    
    static showUserMessage(message, type = 'info') {
        // Implementation depends on your UI framework
        const toast = document.createElement('div');
        toast.className = `toast toast-${type}`;
        toast.textContent = message;
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 5000);
    }
    
    static logError(error, context) {
        // Send error to logging service
        fetch('/api/v1/logs/error', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                error: error.message,
                stack: error.stack,
                context: context,
                timestamp: new Date().toISOString(),
                user_agent: navigator.userAgent
            })
        }).catch(console.error);
    }
}
```

### Backend Error Handling
```python
# API error response format
from fastapi import HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, Any

class ErrorResponse(BaseModel):
    detail: str
    error_type: str
    timestamp: str
    context: Optional[Dict[str, Any]] = None

# Custom exception handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            detail=exc.detail,
            error_type="http_error",
            timestamp=datetime.utcnow().isoformat(),
            context={"path": str(request.url)}
        ).dict()
    )

# Validation error handler
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            detail="Validation error",
            error_type="validation_error",
            timestamp=datetime.utcnow().isoformat(),
            context={"errors": exc.errors()}
        ).dict()
    )
```

## Security Integration

### Authentication Flow
```javascript
// Authentication management
class AuthManager {
    constructor() {
        this.token = localStorage.getItem('auth_token');
        this.refreshToken = localStorage.getItem('refresh_token');
    }
    
    async login(credentials) {
        try {
            const response = await fetch('/api/v1/auth/login', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(credentials)
            });
            
            if (!response.ok) {
                throw new Error('Login failed');
            }
            
            const data = await response.json();
            this.token = data.access_token;
            this.refreshToken = data.refresh_token;
            
            localStorage.setItem('auth_token', this.token);
            localStorage.setItem('refresh_token', this.refreshToken);
            
            return data;
        } catch (error) {
            console.error('Login error:', error);
            throw error;
        }
    }
    
    async refreshToken() {
        try {
            const response = await fetch('/api/v1/auth/refresh', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    refresh_token: this.refreshToken
                })
            });
            
            if (!response.ok) {
                throw new Error('Token refresh failed');
            }
            
            const data = await response.json();
            this.token = data.access_token;
            localStorage.setItem('auth_token', this.token);
            
            return data;
        } catch (error) {
            console.error('Token refresh error:', error);
            this.logout();
            throw error;
        }
    }
    
    logout() {
        this.token = null;
        this.refreshToken = null;
        localStorage.removeItem('auth_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
    }
}
```

### CSRF Protection
```javascript
// CSRF token management
class CSRFManager {
    static async getCSRFToken() {
        try {
            const response = await fetch('/api/v1/auth/csrf-token', {
                method: 'GET',
                credentials: 'include'
            });
            
            if (!response.ok) {
                throw new Error('Failed to get CSRF token');
            }
            
            const data = await response.json();
            return data.csrf_token;
        } catch (error) {
            console.error('CSRF token error:', error);
            throw error;
        }
    }
    
    static async makeSecureRequest(url, options = {}) {
        const csrfToken = await this.getCSRFToken();
        
        const secureOptions = {
            ...options,
            headers: {
                ...options.headers,
                'X-CSRF-Token': csrfToken
            },
            credentials: 'include'
        };
        
        return fetch(url, secureOptions);
    }
}
```

## Performance Optimization

### Frontend Optimization
```javascript
// Request caching and debouncing
class RequestCache {
    constructor() {
        this.cache = new Map();
        this.pendingRequests = new Map();
    }
    
    async getCachedData(key, fetchFunction, ttl = 300000) { // 5 minutes TTL
        // Check cache
        if (this.cache.has(key)) {
            const cached = this.cache.get(key);
            if (Date.now() - cached.timestamp < ttl) {
                return cached.data;
            }
        }
        
        // Check if request is pending
        if (this.pendingRequests.has(key)) {
            return this.pendingRequests.get(key);
        }
        
        // Make new request
        const promise = fetchFunction();
        this.pendingRequests.set(key, promise);
        
        try {
            const data = await promise;
            this.cache.set(key, {
                data: data,
                timestamp: Date.now()
            });
            return data;
        } finally {
            this.pendingRequests.delete(key);
        }
    }
}

// Debounced search
class DebouncedSearch {
    constructor() {
        this.timeoutId = null;
        this.delay = 300;
    }
    
    search(query, callback) {
        clearTimeout(this.timeoutId);
        this.timeoutId = setTimeout(() => {
            callback(query);
        }, this.delay);
    }
}
```

### Backend Optimization
```python
# Response caching
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend
from fastapi_cache.decorator import cache

@app.get("/api/v1/analytics/dashboard")
@cache(expire=60)  # Cache for 1 minute
async def get_dashboard_stats():
    # Implementation
    pass

# Database connection pooling
from sqlalchemy import create_engine
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True
)

# Async background tasks
from celery import Celery

celery_app = Celery("mafa")

@celery_app.task
async def process_search_results(results):
    # Process search results in background
    pass
```

## Testing Integration

### Frontend Testing
```javascript
// API integration tests
describe('API Integration', () => {
    test('should create search configuration', async () => {
        const configData = {
            name: 'Test Search',
            provider: 'immoscout',
            criteria: {
                min_price: 500,
                max_price: 1000,
                rooms: 2
            }
        };
        
        const response = await fetch('/api/v1/scraper/configurations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${testToken}`
            },
            body: JSON.stringify(configData)
        });
        
        expect(response.status).toBe(201);
        const data = await response.json();
        expect(data.name).toBe('Test Search');
    });
    
    test('should handle validation errors', async () => {
        const invalidData = {
            name: '',
            provider: 'invalid'
        };
        
        const response = await fetch('/api/v1/scraper/configurations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${testToken}`
            },
            body: JSON.stringify(invalidData)
        });
        
        expect(response.status).toBe(422);
        const data = await response.json();
        expect(data.error_type).toBe('validation_error');
    });
});
```

### Backend Testing
```python
# API endpoint tests
import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)

def test_create_search_config():
    config_data = {
        "name": "Test Search",
        "provider": "immoscout",
        "criteria": {
            "min_price": 500,
            "max_price": 1000,
            "rooms": 2
        }
    }
    
    response = client.post(
        "/api/v1/scraper/configurations",
        json=config_data,
        headers={"Authorization": f"Bearer {test_token}"}
    )
    
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Test Search"

def test_config_validation():
    invalid_data = {
        "name": "",
        "provider": "invalid"
    }
    
    response = client.post(
        "/api/v1/scraper/configurations",
        json=invalid_data,
        headers={"Authorization": f"Bearer {test_token}"}
    )
    
    assert response.status_code == 422
    data = response.json()
    assert data["error_type"] == "validation_error"
```

## Deployment Considerations

### Environment Configuration
```python
# Production settings
class ProductionSettings:
    # Database
    DATABASE_URL = os.getenv("DATABASE_URL")
    
    # Redis for caching
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Security
    SECRET_KEY = os.getenv("SECRET_KEY")
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY")
    
    # CORS
    CORS_ORIGINS = [
        "https://dashboard.mafa.app",
        "https://api.mafa.app"
    ]
    
    # Rate limiting
    RATE_LIMIT_PER_MINUTE = 60
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL = 30
```

### Monitoring and Logging
```python
# Structured logging
import structlog

logger = structlog.get_logger()

@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    
    logger.info(
        "request_processed",
        method=request.method,
        url=str(request.url),
        status_code=response.status_code,
        process_time=process_time
    )
    
    return response

# Health checks
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "services": {
            "database": await check_database_health(),
            "redis": await check_redis_health(),
            "websocket": check_websocket_health()
        }
    }
```

## Troubleshooting Guide

### Common Issues

#### 1. WebSocket Connection Failures
**Symptoms**: Real-time updates not working
**Causes**: Network issues, CORS misconfiguration
**Solutions**:
- Check WebSocket URL configuration
- Verify CORS settings
- Test network connectivity

#### 2. Authentication Errors
**Symptoms**: 401 Unauthorized responses
**Causes**: Expired tokens, incorrect credentials
**Solutions**:
- Implement token refresh logic
- Verify token storage
- Check authentication flow

#### 3. API Response Format Mismatches
**Symptoms**: Frontend parsing errors
**Causes**: Backend response format changes
**Solutions**:
- Verify API response schemas
- Update frontend parsing logic
- Add response validation

#### 4. Performance Issues
**Symptoms**: Slow page loads, timeouts
**Causes**: Large data transfers, inefficient queries
**Solutions**:
- Implement pagination
- Add response caching
- Optimize database queries

### Debugging Tools

#### Frontend Debugging
```javascript
// Debug logging
const DEBUG = process.env.NODE_ENV === 'development';

function debugLog(message, data) {
    if (DEBUG) {
        console.log(`[DEBUG] ${message}`, data);
    }
}

// Network request interceptor
if (DEBUG) {
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
        console.log('[FETCH]', args[0], args[1]);
        return originalFetch.apply(this, args).then(response => {
            console.log('[RESPONSE]', response.status, response.url);
            return response;
        });
    };
}
```

#### Backend Debugging
```python
# Request logging
import logging

logging.basicConfig(level=logging.DEBUG)

@app.middleware("http")
async def debug_requests(request: Request, call_next):
    if DEBUG:
        logger.debug(f"Request: {request.method} {request.url}")
        logger.debug(f"Headers: {dict(request.headers)}")
        
    response = await call_next(request)
    
    if DEBUG:
        logger.debug(f"Response: {response.status_code}")
    
    return response
```

## Maintenance and Updates

### Version Compatibility
- Maintain API versioning (`/api/v1/`, `/api/v2/`)
- Document breaking changes
- Provide migration guides

### Regular Maintenance Tasks
- Monitor API performance
- Update dependencies
- Review security patches
- Test integration points

### Backup and Recovery
- Regular database backups
- Configuration backups
- Disaster recovery procedures

This integration guide provides comprehensive documentation for maintaining and extending the MAFA backend-to-frontend integration. Regular updates and monitoring ensure continued smooth operation of the system.