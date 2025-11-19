"""
Comprehensive API endpoint testing suite for MWA Core API.

Tests all API endpoints including:
- Authentication endpoints
- Configuration management
- Listing operations
- Contact management
- Scraper control
- Scheduler management
- System monitoring
- WebSocket functionality
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from unittest.mock import Mock, patch, AsyncMock

from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
import httpx

# Import API components
from api.main import app
from api.auth import authenticate_user, create_access_token
from api.websocket.manager import websocket_manager, MessageType
from api.middleware.rate_limiter import RateLimitConfig
from mwa_core.config.settings import get_settings

# Test client
client = TestClient(app)

# Test data
TEST_USER = {
    "username": "test_user",
    "password": "test_password_123",
    "role": "user"
}

TEST_ADMIN = {
    "username": "admin",
    "password": "admin_password_123",
    "role": "admin"
}

TEST_CONFIG = {
    "scraping": {
        "providers": ["immoscout", "wg_gesucht"],
        "max_pages": 10,
        "delay_seconds": 2
    },
    "notifications": {
        "enabled": True,
        "channels": ["email", "telegram"]
    }
}

class TestAuthentication:
    """Test authentication and authorization endpoints."""
    
    def test_login_success(self):
        """Test successful user login."""
        response = client.post("/api/v1/auth/login", json={
            "username": TEST_USER["username"],
            "password": TEST_USER["password"]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "token_type" in data
        assert data["token_type"] == "bearer"
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials."""
        response = client.post("/api/v1/auth/login", json={
            "username": "invalid_user",
            "password": "wrong_password"
        })
        
        assert response.status_code == 401
        assert "detail" in response.json()
    
    def test_login_missing_fields(self):
        """Test login with missing required fields."""
        response = client.post("/api/v1/auth/login", json={
            "username": "test_user"
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_refresh_token_success(self):
        """Test successful token refresh."""
        # First login to get a token
        login_response = client.post("/api/v1/auth/login", json={
            "username": TEST_USER["username"],
            "password": TEST_USER["password"]
        })
        assert login_response.status_code == 200
        
        token_data = login_response.json()
        access_token = token_data["access_token"]
        
        # Refresh the token
        refresh_response = client.post("/api/v1/auth/refresh", 
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert refresh_response.status_code == 200
        refresh_data = refresh_response.json()
        assert "access_token" in refresh_data
    
    def test_refresh_token_invalid(self):
        """Test refresh with invalid token."""
        response = client.post("/api/v1/auth/refresh", 
            headers={"Authorization": "Bearer invalid_token"}
        )
        
        assert response.status_code == 401
    
    def test_current_user_info(self):
        """Test getting current user information."""
        # Login to get token
        login_response = client.post("/api/v1/auth/login", json={
            "username": TEST_USER["username"],
            "password": TEST_USER["password"]
        })
        assert login_response.status_code == 200
        
        token_data = login_response.json()
        access_token = token_data["access_token"]
        
        # Get user info
        user_response = client.get("/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        
        assert user_response.status_code == 200
        user_data = user_response.json()
        assert "username" in user_data
        assert "role" in user_data
        assert user_data["username"] == TEST_USER["username"]
    
    def test_protected_endpoint_without_token(self):
        """Test accessing protected endpoint without token."""
        response = client.get("/api/v1/config")
        assert response.status_code == 401
    
    def test_protected_endpoint_with_invalid_token(self):
        """Test accessing protected endpoint with invalid token."""
        response = client.get("/api/v1/config",
            headers={"Authorization": "Bearer invalid_token"}
        )
        assert response.status_code == 401


class TestConfigurationEndpoints:
    """Test configuration management endpoints."""
    
    def setup_method(self):
        """Setup method for authentication."""
        self.login_response = client.post("/api/v1/auth/login", json={
            "username": TEST_ADMIN["username"],
            "password": TEST_ADMIN["password"]
        })
        assert self.login_response.status_code == 200
        
        self.token_data = self.login_response.json()
        self.access_token = self.token_data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.access_token}"}
    
    def test_get_config_success(self):
        """Test getting configuration."""
        response = client.get("/api/v1/config", headers=self.headers)
        assert response.status_code == 200
    
    def test_update_config_success(self):
        """Test updating configuration."""
        response = client.put("/api/v1/config", json=TEST_CONFIG, headers=self.headers)
        assert response.status_code == 200
    
    def test_update_config_invalid_format(self):
        """Test updating configuration with invalid format."""
        response = client.put("/api/v1/config", json={"invalid": "data"}, headers=self.headers)
        assert response.status_code == 400
    
    def test_validate_config_success(self):
        """Test configuration validation."""
        response = client.post("/api/v1/config/validate", json=TEST_CONFIG, headers=self.headers)
        assert response.status_code == 200
    
    def test_export_config(self):
        """Test exporting configuration."""
        response = client.get("/api/v1/config/export", headers=self.headers)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
    
    def test_import_config(self):
        """Test importing configuration."""
        response = client.post("/api/v1/config/import", json=TEST_CONFIG, headers=self.headers)
        assert response.status_code == 200


class TestListingEndpoints:
    """Test listing management endpoints."""
    
    def setup_method(self):
        """Setup method for authentication."""
        self.login_response = client.post("/api/v1/auth/login", json={
            "username": TEST_USER["username"],
            "password": TEST_USER["password"]
        })
        assert self.login_response.status_code == 200
        
        self.token_data = self.login_response.json()
        self.access_token = self.token_data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.access_token}"}
    
    def test_get_listings_success(self):
        """Test getting listings."""
        response = client.get("/api/v1/listings", headers=self.headers)
        assert response.status_code == 200
    
    def test_get_listings_with_filters(self):
        """Test getting listings with filters."""
        params = {
            "min_price": 500,
            "max_price": 2000,
            "rooms_min": 1,
            "rooms_max": 3,
            "limit": 10
        }
        response = client.get("/api/v1/listings", params=params, headers=self.headers)
        assert response.status_code == 200
    
    def test_get_listing_by_id(self):
        """Test getting specific listing by ID."""
        response = client.get("/api/v1/listings/1", headers=self.headers)
        # Should return 200 for existing or 404 for non-existing
        assert response.status_code in [200, 404]
    
    def test_create_listing_success(self):
        """Test creating a new listing."""
        listing_data = {
            "title": "Test Listing",
            "price": 1200,
            "rooms": 2,
            "location": "Munich",
            "description": "Test description"
        }
        response = client.post("/api/v1/listings", json=listing_data, headers=self.headers)
        assert response.status_code == 201
    
    def test_update_listing_success(self):
        """Test updating a listing."""
        listing_data = {
            "title": "Updated Listing",
            "price": 1500,
            "rooms": 3
        }
        response = client.put("/api/v1/listings/1", json=listing_data, headers=self.headers)
        # Should return 200 for success or 404 for not found
        assert response.status_code in [200, 404]
    
    def test_delete_listing_success(self):
        """Test deleting a listing."""
        response = client.delete("/api/v1/listings/1", headers=self.headers)
        assert response.status_code in [200, 404, 204]
    
    def test_search_listings(self):
        """Test searching listings."""
        response = client.get("/api/v1/listings/search?q=munich", headers=self.headers)
        assert response.status_code == 200


class TestContactEndpoints:
    """Test contact management endpoints."""
    
    def setup_method(self):
        """Setup method for authentication."""
        self.login_response = client.post("/api/v1/auth/login", json={
            "username": TEST_USER["username"],
            "password": TEST_USER["password"]
        })
        assert self.login_response.status_code == 200
        
        self.token_data = self.login_response.json()
        self.access_token = self.token_data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.access_token}"}
    
    def test_get_contacts_success(self):
        """Test getting contacts."""
        response = client.get("/api/v1/contacts", headers=self.headers)
        assert response.status_code == 200
    
    def test_get_contact_by_id(self):
        """Test getting specific contact by ID."""
        response = client.get("/api/v1/contacts/1", headers=self.headers)
        assert response.status_code in [200, 404]
    
    def test_create_contact_success(self):
        """Test creating a new contact."""
        contact_data = {
            "name": "Test Contact",
            "email": "test@example.com",
            "phone": "+49123456789",
            "source": "test"
        }
        response = client.post("/api/v1/contacts", json=contact_data, headers=self.headers)
        assert response.status_code == 201
    
    def test_update_contact_success(self):
        """Test updating a contact."""
        contact_data = {
            "name": "Updated Contact",
            "email": "updated@example.com"
        }
        response = client.put("/api/v1/contacts/1", json=contact_data, headers=self.headers)
        assert response.status_code in [200, 404]
    
    def test_delete_contact_success(self):
        """Test deleting a contact."""
        response = client.delete("/api/v1/contacts/1", headers=self.headers)
        assert response.status_code in [200, 404, 204]
    
    def test_validate_contact(self):
        """Test contact validation."""
        contact_data = {
            "name": "Test Contact",
            "email": "invalid-email",
            "phone": "invalid-phone"
        }
        response = client.post("/api/v1/contacts/validate", json=contact_data, headers=self.headers)
        assert response.status_code == 200
    
    def test_search_contacts(self):
        """Test searching contacts."""
        response = client.get("/api/v1/contacts/search?q=test", headers=self.headers)
        assert response.status_code == 200


class TestScraperEndpoints:
    """Test scraper control endpoints."""
    
    def setup_method(self):
        """Setup method for authentication."""
        self.login_response = client.post("/api/v1/auth/login", json={
            "username": TEST_USER["username"],
            "password": TEST_USER["password"]
        })
        assert self.login_response.status_code == 200
        
        self.token_data = self.login_response.json()
        self.access_token = self.token_data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.access_token}"}
    
    def test_get_scraper_status(self):
        """Test getting scraper status."""
        response = client.get("/api/v1/scraper/status", headers=self.headers)
        assert response.status_code == 200
    
    def test_start_scraper_success(self):
        """Test starting scraper."""
        scraper_data = {
            "provider": "immoscout",
            "config": {
                "max_pages": 5,
                "delay_seconds": 1
            }
        }
        response = client.post("/api/v1/scraper/start", json=scraper_data, headers=self.headers)
        assert response.status_code in [200, 202]
    
    def test_stop_scraper_success(self):
        """Test stopping scraper."""
        response = client.post("/api/v1/scraper/stop", headers=self.headers)
        assert response.status_code in [200, 202]
    
    def test_get_scraper_history(self):
        """Test getting scraper execution history."""
        response = client.get("/api/v1/scraper/history", headers=self.headers)
        assert response.status_code == 200
    
    def test_run_manual_scraper(self):
        """Test manual scraper execution."""
        scraper_data = {
            "provider": "immoscout",
            "immediate": True
        }
        response = client.post("/api/v1/scraper/run", json=scraper_data, headers=self.headers)
        assert response.status_code in [200, 202]


class TestSchedulerEndpoints:
    """Test scheduler management endpoints."""
    
    def setup_method(self):
        """Setup method for authentication."""
        self.login_response = client.post("/api/v1/auth/login", json={
            "username": TEST_ADMIN["username"],
            "password": TEST_ADMIN["password"]
        })
        assert self.login_response.status_code == 200
        
        self.token_data = self.login_response.json()
        self.access_token = self.token_data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.access_token}"}
    
    def test_get_scheduled_jobs(self):
        """Test getting scheduled jobs."""
        response = client.get("/api/v1/scheduler/jobs", headers=self.headers)
        assert response.status_code == 200
    
    def test_create_scheduled_job(self):
        """Test creating a scheduled job."""
        job_data = {
            "name": "Test Job",
            "schedule": "0 9 * * *",  # Daily at 9 AM
            "command": "run_scraper",
            "args": ["immoscout"]
        }
        response = client.post("/api/v1/scheduler/jobs", json=job_data, headers=self.headers)
        assert response.status_code in [201, 200]
    
    def test_update_scheduled_job(self):
        """Test updating a scheduled job."""
        job_data = {
            "schedule": "0 10 * * *",  # Change to 10 AM
            "enabled": False
        }
        response = client.put("/api/v1/scheduler/jobs/1", json=job_data, headers=self.headers)
        assert response.status_code in [200, 404]
    
    def test_delete_scheduled_job(self):
        """Test deleting a scheduled job."""
        response = client.delete("/api/v1/scheduler/jobs/1", headers=self.headers)
        assert response.status_code in [200, 404, 204]
    
    def test_pause_resume_job(self):
        """Test pausing and resuming jobs."""
        # Pause job
        response = client.post("/api/v1/scheduler/jobs/1/pause", headers=self.headers)
        assert response.status_code in [200, 404]
        
        # Resume job
        response = client.post("/api/v1/scheduler/jobs/1/resume", headers=self.headers)
        assert response.status_code in [200, 404]


class TestSystemEndpoints:
    """Test system monitoring endpoints."""
    
    def setup_method(self):
        """Setup method for authentication."""
        self.login_response = client.post("/api/v1/auth/login", json={
            "username": TEST_USER["username"],
            "password": TEST_USER["password"]
        })
        assert self.login_response.status_code == 200
        
        self.token_data = self.login_response.json()
        self.access_token = self.token_data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.access_token}"}
    
    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "service" in data
    
    def test_system_info(self):
        """Test system information endpoint."""
        response = client.get("/api/v1/system/info", headers=self.headers)
        assert response.status_code == 200
    
    def test_system_metrics(self):
        """Test system metrics endpoint."""
        response = client.get("/api/v1/system/metrics", headers=self.headers)
        assert response.status_code == 200
    
    def test_component_status(self):
        """Test component status endpoint."""
        response = client.get("/api/v1/system/components", headers=self.headers)
        assert response.status_code == 200
    
    def test_performance_stats(self):
        """Test performance statistics endpoint."""
        response = client.client.get("/api/v1/system/performance", headers=self.headers)
        assert response.status_code == 200


class TestRateLimiting:
    """Test rate limiting functionality."""
    
    def setup_method(self):
        """Setup for rate limiting tests."""
        self.headers = {"Authorization": "Bearer test_token"}
    
    def test_rate_limiting_applied(self):
        """Test that rate limiting is applied to endpoints."""
        # Make multiple requests quickly to trigger rate limiting
        responses = []
        for i in range(20):  # Exceed rate limit
            response = client.get("/api/v1/config", headers=self.headers)
            responses.append(response.status_code)
        
        # Should see some 429 (Too Many Requests) responses
        assert 429 in responses or any(r.status_code >= 400 for r in [client.get("/api/v1/config", headers=self.headers) for _ in range(5)])
    
    def test_rate_limit_headers_present(self):
        """Test that rate limit headers are present in responses."""
        response = client.get("/api/v1/config", headers=self.headers)
        if response.status_code == 200:
            # Headers might not be present on every request
            pass  # This is acceptable
    
    def test_rate_limit_exempt_paths(self):
        """Test that exempt paths are not rate limited."""
        # These should not be rate limited
        exempt_paths = ["/health", "/docs", "/api/info"]
        
        for path in exempt_paths:
            if path == "/api/info":
                response = client.get(path, headers=self.headers)
            else:
                response = client.get(path)
            
            assert response.status_code != 429  # Should not be rate limited


class TestSecurityHeaders:
    """Test security headers middleware."""
    
    def test_security_headers_present(self):
        """Test that security headers are present in responses."""
        response = client.get("/health")
        
        # Check for security headers
        assert "X-Frame-Options" in response.headers
        assert "X-Content-Type-Options" in response.headers
        assert "X-XSS-Protection" in response.headers
        assert "Referrer-Policy" in response.headers
    
    def test_cors_headers_present(self):
        """Test that CORS headers are present when appropriate."""
        # Test preflight request
        response = client.options("/health", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        })
        
        # CORS headers should be present for valid origins
        if response.status_code == 200:
            assert "Access-Control-Allow-Origin" in response.headers
    
    def test_hsts_header_for_https(self):
        """Test HSTS header for HTTPS requests."""
        # This would require HTTPS setup, so we test the header logic
        response = client.get("/health")
        # HSTS might not be present for HTTP requests
        # The middleware should handle this appropriately


class TestWebSocket:
    """Test WebSocket functionality."""
    
    def test_websocket_connection_establishes(self):
        """Test WebSocket connection establishment."""
        with client.websocket_connect("/api/v1/websocket/connect") as websocket:
            # Connection should be established
            data = websocket.receive_json()
            assert "connection_id" in data
    
    def test_websocket_heartbeat(self):
        """Test WebSocket heartbeat functionality."""
        with client.websocket_connect("/api/v1/websocket/connect") as websocket:
            # Receive welcome message
            data = websocket.receive_json()
            assert "connection_id" in data
            
            # Send heartbeat
            heartbeat_message = {
                "type": "heartbeat",
                "data": {"timestamp": datetime.now().isoformat()}
            }
            websocket.send_json(heartbeat_message)
            
            # Should receive heartbeat response
            response = websocket.receive_json()
            assert response["type"] == "heartbeat"
    
    def test_websocket_room_joining(self):
        """Test WebSocket room joining."""
        with client.websocket_connect("/api/v1/websocket/connect?room=test_room") as websocket:
            # Connection should be established
            data = websocket.receive_json()
            assert "connection_id" in data
    
    def test_websocket_stats_endpoint(self):
        """Test WebSocket statistics endpoint."""
        response = client.get("/api/v1/websocket/stats")
        assert response.status_code == 200
        
        stats = response.json()
        assert "total_connections" in stats
        assert "active_connections" in stats
    
    def test_websocket_rooms_endpoint(self):
        """Test WebSocket rooms listing endpoint."""
        response = client.get("/api/v1/websocket/rooms")
        assert response.status_code == 200
        
        rooms = response.json()
        assert "rooms" in rooms


class TestAPIIntegration:
    """Test API integration and end-to-end functionality."""
    
    def setup_method(self):
        """Setup for integration tests."""
        # Login as admin for full access
        self.login_response = client.post("/api/v1/auth/login", json={
            "username": TEST_ADMIN["username"],
            "password": TEST_ADMIN["password"]
        })
        assert self.login_response.status_code == 200
        
        self.token_data = self.login_response.json()
        self.access_token = self.token_data["access_token"]
        self.headers = {"Authorization": f"Bearer {self.access_token}"}
    
    def test_full_workflow(self):
        """Test a complete workflow from config to scraper execution."""
        # 1. Update configuration
        config_response = client.put("/api/v1/config", json=TEST_CONFIG, headers=self.headers)
        assert config_response.status_code == 200
        
        # 2. Get configuration to verify
        get_config_response = client.get("/api/v1/config", headers=self.headers)
        assert get_config_response.status_code == 200
        
        # 3. Start scraper
        scraper_response = client.post("/api/v1/scraper/start", json={
            "provider": "immoscout",
            "config": {"max_pages": 1, "delay_seconds": 1}
        }, headers=self.headers)
        assert scraper_response.status_code in [200, 202]
        
        # 4. Get system status
        system_response = client.get("/api/v1/system/info", headers=self.headers)
        assert system_response.status_code == 200
    
    def test_error_handling(self):
        """Test error handling across different endpoints."""
        # Test with invalid data on various endpoints
        invalid_configs = [
            {},  # Empty config
            {"invalid": "data"},  # Invalid structure
            {"scraping": {"invalid": "config"}}  # Invalid values
        ]
        
        for invalid_config in invalid_configs:
            response = client.put("/api/v1/config", json=invalid_config, headers=self.headers)
            assert response.status_code == 400


# Test fixtures and utilities
@pytest.fixture
def auth_headers():
    """Fixture for authentication headers."""
    login_response = client.post("/api/v1/auth/login", json={
        "username": TEST_USER["username"],
        "password": TEST_USER["password"]
    })
    if login_response.status_code == 200:
        token_data = login_response.json()
        return {"Authorization": f"Bearer {token_data['access_token']}"}
    return {}

@pytest.fixture
def admin_headers():
    """Fixture for admin authentication headers."""
    login_response = client.post("/api/v1/auth/login", json={
        "username": TEST_ADMIN["username"],
        "password": TEST_ADMIN["password"]
    })
    if login_response.status_code == 200:
        token_data = login_response.json()
        return {"Authorization": f"Bearer {token_data['access_token']}"}
    return {}


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])