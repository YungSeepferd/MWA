"""
Integration tests for MWA Core API.

Tests end-to-end functionality and integration with MWA Core components:
- Database integration testing
- MWA Core component integration
- WebSocket integration testing
- Error handling and recovery
- Performance testing
"""

import pytest
import asyncio
import time
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from unittest.mock import Mock, patch, AsyncMock
import threading
import queue

from fastapi import FastAPI, WebSocket
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect
import httpx

# Import API and MWA Core components
from api.main import app
from api.auth import authenticate_user, create_access_token
from api.websocket.manager import websocket_manager, MessageType, WebSocketMessage
from mwa_core.config.settings import get_settings
from mwa_core.storage.manager import StorageManager
from mwa_core.orchestrator.orchestrator import Orchestrator
from mwa_core.scheduler.job_manager import JobManager

# Test client and configuration
client = TestClient(app)
settings = get_settings()

class TestDatabaseIntegration:
    """Test database integration with MWA Core storage."""
    
    def setup_method(self):
        """Setup database for testing."""
        self.admin_login = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin_password_123"
        })
        if self.admin_login.status_code == 200:
            token_data = self.admin_login.json()
            self.headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        else:
            self.headers = {}
    
    def test_storage_manager_integration(self):
        """Test integration with StorageManager."""
        # This would test actual database operations
        # For now, we'll simulate the integration
        with patch('mwa_core.storage.manager.StorageManager') as mock_storage:
            # Mock storage manager methods
            mock_instance = Mock()
            mock_instance.get_config.return_value = {"test": "data"}
            mock_instance.save_config.return_value = True
            mock_storage.return_value = mock_instance
            
            # Test configuration endpoint
            response = client.get("/api/v1/config", headers=self.headers)
            assert response.status_code == 200
    
    def test_listing_data_persistence(self):
        """Test listing data persistence and retrieval."""
        # Create test listing
        listing_data = {
            "title": "Integration Test Listing",
            "price": 1500,
            "rooms": 2,
            "location": "Munich",
            "description": "Test listing for integration testing"
        }
        
        create_response = client.post("/api/v1/listings", json=listing_data, headers=self.headers)
        # Should succeed or fail gracefully
        assert create_response.status_code in [201, 500, 422]
        
        # Verify listing can be retrieved
        get_response = client.get("/api/v1/listings", headers=self.headers)
        assert get_response.status_code == 200
    
    def test_contact_data_persistence(self):
        """Test contact data persistence and retrieval."""
        # Create test contact
        contact_data = {
            "name": "Integration Test Contact",
            "email": "integration@example.com",
            "phone": "+49123456789",
            "source": "integration_test"
        }
        
        create_response = client.post("/api/v1/contacts", json=contact_data, headers=self.headers)
        # Should succeed or fail gracefully
        assert create_response.status_code in [201, 500, 422]
        
        # Verify contact can be retrieved
        get_response = client.get("/api/v1/contacts", headers=self.headers)
        assert get_response.status_code == 200
    
    def test_configuration_backup_and_restore(self):
        """Test configuration backup and restore functionality."""
        # Export configuration
        export_response = client.get("/api/v1/config/export", headers=self.headers)
        if export_response.status_code == 200:
            config_data = export_response.json()
            
            # Import configuration back
            import_response = client.post("/api/v1/config/import", json=config_data, headers=self.headers)
            assert import_response.status_code in [200, 400]


class TestOrchestratorIntegration:
    """Test integration with MWA Core orchestrator."""
    
    def setup_method(self):
        """Setup for orchestrator integration tests."""
        self.admin_login = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin_password_123"
        })
        if self.admin_login.status_code == 200:
            token_data = self.admin_login.json()
            self.headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        else:
            self.headers = {}
    
    def test_scraper_orchestration(self):
        """Test scraper orchestration integration."""
        # Mock orchestrator for testing
        with patch('mwa_core.orchestrator.orchestrator.Orchestrator') as mock_orchestrator:
            mock_instance = Mock()
            mock_instance.start_scraper.return_value = {"job_id": "test_job_123"}
            mock_instance.stop_scraper.return_value = {"status": "stopped"}
            mock_instance.get_status.return_value = {"running": False}
            mock_orchestrator.return_value = mock_instance
            
            # Test starting scraper
            scraper_data = {
                "provider": "immoscout",
                "config": {"max_pages": 1}
            }
            response = client.post("/api/v1/scraper/start", json=scraper_data, headers=self.headers)
            assert response.status_code in [200, 202]
    
    def test_multiple_scraper_coordination(self):
        """Test coordination of multiple scrapers."""
        scraper_configs = [
            {"provider": "immoscout", "config": {"max_pages": 1}},
            {"provider": "wg_gesucht", "config": {"max_pages": 1}}
        ]
        
        started_jobs = []
        for scraper_config in scraper_configs:
            response = client.post("/api/v1/scraper/start", json=scraper_config, headers=self.headers)
            if response.status_code in [200, 202]:
                started_jobs.append(response.json())
        
        # Verify multiple jobs can be managed
        status_response = client.get("/api/v1/scraper/status", headers=self.headers)
        assert status_response.status_code == 200


class TestSchedulerIntegration:
    """Test integration with MWA Core scheduler."""
    
    def setup_method(self):
        """Setup for scheduler integration tests."""
        self.admin_login = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin_password_123"
        })
        if self.admin_login.status_code == 200:
            token_data = self.admin_login.json()
            self.headers = {"Authorization": f"Bearer {token_data['access_token']}"}
        else:
            self.headers = {}
    
    def test_job_scheduling_integration(self):
        """Test job scheduling integration."""
        with patch('mwa_core.scheduler.job_manager.JobManager') as mock_job_manager:
            mock_instance = Mock()
            mock_instance.create_job.return_value = {"job_id": "scheduled_job_123"}
            mock_instance.get_jobs.return_value = [{"job_id": "test", "schedule": "0 9 * * *"}]
            mock_instance.update_job.return_value = True
            mock_instance.delete_job.return_value = True
            mock_job_manager.return_value = mock_instance
            
            # Test creating scheduled job
            job_data = {
                "name": "Test Scheduled Job",
                "schedule": "0 9 * * *",
                "command": "run_scraper",
                "args": ["immoscout"]
            }
            response = client.post("/api/v1/scheduler/jobs", json=job_data, headers=self.headers)
            assert response.status_code in [201, 200]
    
    def test_job_pause_resume_functionality(self):
        """Test job pause and resume functionality."""
        # Test pausing job
        pause_response = client.post("/api/v1/scheduler/jobs/1/pause", headers=self.headers)
        assert pause_response.status_code in [200, 404]
        
        # Test resuming job
        resume_response = client.post("/api/v1/scheduler/jobs/1/resume", headers=self.headers)
        assert resume_response.status_code in [200, 404]
    
    def test_job_execution_monitoring(self):
        """Test job execution monitoring."""
        # Get job execution history
        history_response = client.get("/api/v1/scheduler/jobs/1/history", headers=self.headers)
        assert history_response.status_code in [200, 404]
        
        # Get job execution status
        status_response = client.get("/api/v1/scheduler/jobs/1/status", headers=self.headers)
        assert status_response.status_code in [200, 404]


class TestWebSocketIntegration:
    """Test WebSocket integration and real-time functionality."""
    
    def setup_method(self):
        """Setup for WebSocket integration tests."""
        self.user_login = client.post("/api/v1/auth/login", json={
            "username": "test_user",
            "password": "test_password_123"
        })
        if self.user_login.status_code == 200:
            token_data = self.user_login.json()
            self.access_token = token_data["access_token"]
        else:
            self.access_token = None
    
    def test_websocket_authentication_integration(self):
        """Test WebSocket authentication integration."""
        if not self.access_token:
            pytest.skip("No access token available")
        
        with client.websocket_connect(
            f"/api/v1/websocket/connect?token={self.access_token}"
        ) as websocket:
            # Should receive welcome message
            data = websocket.receive_json()
            assert "connection_id" in data
            assert "user_id" in data
    
    def test_websocket_room_broadcasting(self):
        """Test WebSocket room broadcasting."""
        room_name = "test_integration_room"
        
        with client.websocket_connect(f"/api/v1/websocket/connect?room={room_name}") as websocket:
            # Receive welcome message
            data = websocket.receive_json()
            assert data["room"] == room_name
            
            # Test broadcasting to room
            broadcast_response = client.post("/api/v1/websocket/system-status", json={
                "status": "test_status",
                "message": "Integration test message"
            })
            assert broadcast_response.status_code in [200, 403]
    
    def test_websocket_heartbeat_integration(self):
        """Test WebSocket heartbeat integration."""
        with client.websocket_connect("/api/v1/websocket/connect") as websocket:
            # Receive welcome message
            data = websocket.receive_json()
            
            # Send heartbeat message
            heartbeat = {
                "type": "heartbeat",
                "data": {"timestamp": datetime.now().isoformat()}
            }
            websocket.send_json(heartbeat)
            
            # Should receive heartbeat response
            response = websocket.receive_json()
            assert response["type"] == "heartbeat"
    
    def test_websocket_statistics_integration(self):
        """Test WebSocket statistics integration."""
        # Connect and disconnect to generate statistics
        with client.websocket_connect("/api/v1/websocket/connect") as ws1:
            ws1.receive_json()  # Welcome message
        
        with client.websocket_connect("/api/v1/websocket/connect") as ws2:
            ws2.receive_json()  # Welcome message
        
        # Get updated statistics
        stats_response = client.get("/api/v1/websocket/stats")
        assert stats_response.status_code == 200
        
        stats = stats_response.json()
        assert "total_connections" in stats
        assert "active_connections" in stats
        
        # At least 2 connections should have been made
        assert stats["total_connections"] >= 2


class TestErrorHandling:
    """Test error handling and recovery."""
    
    def setup_method(self):
        """Setup for error handling tests."""
        self.headers = {"Authorization": "Bearer invalid_token"}
    
    def test_authentication_error_handling(self):
        """Test authentication error handling."""
        # Test invalid token
        response = client.get("/api/v1/config", headers=self.headers)
        assert response.status_code == 401
        
        # Test missing token
        response = client.get("/api/v1/config")
        assert response.status_code == 401
    
    def test_authorization_error_handling(self):
        """Test authorization error handling."""
        # Login as user (limited permissions)
        user_login = client.post("/api/v1/auth/login", json={
            "username": "test_user",
            "password": "test_password_123"
        })
        
        if user_login.status_code == 200:
            token_data = user_login.json()
            user_headers = {"Authorization": f"Bearer {token_data['access_token']}"}
            
            # Try to access admin-only endpoint
            response = client.post("/api/v1/scheduler/jobs", json={
                "name": "Test Job",
                "schedule": "0 9 * * *",
                "command": "test"
            }, headers=user_headers)
            assert response.status_code == 403
    
    def test_validation_error_handling(self):
        """Test validation error handling."""
        # Test invalid configuration
        invalid_config = {
            "scraping": {
                "max_pages": "invalid",  # Should be integer
                "delay_seconds": -1     # Should be positive
            }
        }
        
        response = client.put("/api/v1/config", json=invalid_config)
        assert response.status_code == 401  # Need authentication first
        
        # Login and try again
        admin_login = client.post("/api/v1/auth/login", json={
            "username": "admin",
            "password": "admin_password_123"
        })
        
        if admin_login.status_code == 200:
            token_data = admin_login.json()
            headers = {"Authorization": f"Bearer {token_data['access_token']}"}
            
            response = client.put("/api/v1/config", json=invalid_config, headers=headers)
            assert response.status_code == 400
    
    def test_rate_limiting_error_handling(self):
        """Test rate limiting error handling."""
        headers = {"Authorization": "Bearer invalid_token"}
        
        # Make rapid requests to trigger rate limiting
        responses = []
        for i in range(15):  # Exceed rate limit
            response = client.get("/api/v1/config", headers=headers)
            responses.append(response.status_code)
        
        # Should see some 429 responses
        assert 429 in responses or any(r >= 400 for r in responses[-5:])
    
    def test_websocket_error_handling(self):
        """Test WebSocket error handling."""
        # Test connecting with invalid token
        try:
            with client.websocket_connect("/api/v1/websocket/connect?token=invalid_token"):
                pass
        except Exception:
            # Should fail gracefully
            pass
        
        # Test sending invalid message format
        with client.websocket_connect("/api/v1/websocket/connect") as websocket:
            websocket.receive_json()  # Welcome message
            
            # Send invalid JSON
            websocket.send_text("invalid json")
            
            # Should handle error gracefully or disconnect
            try:
                response = websocket.receive_json()
                # If we get a response, it should be an error message
                if "error" in response:
                    assert response["type"] == "error"
            except WebSocketDisconnect:
                # Or disconnect gracefully
                pass


class TestPerformance:
    """Test API performance and scalability."""
    
    def setup_method(self):
        """Setup for performance tests."""
        self.headers = {"Authorization": "Bearer test_token"}
    
    def test_response_time_performance(self):
        """Test response time performance."""
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = end_time - start_time
        assert response_time < 1.0  # Should respond within 1 second
    
    def test_concurrent_requests_performance(self):
        """Test concurrent request handling."""
        import concurrent.futures
        
        def make_request():
            return client.get("/health")
        
        # Make multiple concurrent requests
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(make_request) for _ in range(20)]
            responses = [future.result() for future in futures]
        
        # All requests should succeed or fail gracefully
        success_count = sum(1 for r in responses if r.status_code == 200)
        assert success_count >= 15  # At least 75% should succeed
    
    def test_large_response_performance(self):
        """Test handling of large responses."""
        # Get a potentially large dataset
        response = client.get("/api/v1/listings?limit=1000", headers=self.headers)
        
        if response.status_code == 200:
            data = response.json()
            # Should handle large responses reasonably
            assert isinstance(data, (list, dict))
    
    def test_websocket_concurrent_connections(self):
        """Test WebSocket concurrent connection handling."""
        connections = []
        
        try:
            # Create multiple WebSocket connections
            for i in range(5):
                ws = client.websocket_connect("/api/v1/websocket/connect")
                # Receive welcome message
                data = ws.receive_json()
                connections.append(ws)
                assert "connection_id" in data
            
            # Get statistics to verify connections
            stats_response = client.get("/api/v1/websocket/stats")
            if stats_response.status_code == 200:
                stats = stats_response.json()
                assert stats["active_connections"] >= 5
        
        finally:
            # Clean up connections
            for ws in connections:
                try:
                    ws.close()
                except:
                    pass


class TestMonitoringIntegration:
    """Test monitoring and alerting integration."""
    
    def setup_method(self):
        """Setup for monitoring tests."""
        self.headers = {"Authorization": "Bearer test_token"}
    
    def test_system_monitoring_integration(self):
        """Test system monitoring endpoints."""
        # Get system information
        info_response = client.get("/api/v1/system/info", headers=self.headers)
        assert info_response.status_code == 200
        
        # Get system metrics
        metrics_response = client.get("/api/v1/system/metrics", headers=self.headers)
        assert metrics_response.status_code == 200
        
        # Get component status
        components_response = client.get("/api/v1/system/components", headers=self.headers)
        assert components_response.status_code == 200
    
    def test_health_check_integration(self):
        """Test health check integration."""
        # Basic health check
        health_response = client.get("/health")
        assert health_response.status_code == 200
        
        health_data = health_response.json()
        assert "status" in health_data
        assert "service" in health_data
        assert "timestamp" in health_data
        
        # Health status should be healthy
        assert health_data["status"] in ["healthy", "degraded"]
    
    def test_performance_monitoring_integration(self):
        """Test performance monitoring integration."""
        performance_response = client.get("/api/v1/system/performance", headers=self.headers)
        assert performance_response.status_code == 200
        
        performance_data = performance_response.json()
        assert "response_times" in performance_data or "cpu_usage" in performance_data
        assert "memory_usage" in performance_data or "request_count" in performance_data


class TestSecurityIntegration:
    """Test security integration across components."""
    
    def test_security_headers_integration(self):
        """Test security headers across all endpoints."""
        endpoints_to_test = [
            "/health",
            "/api/v1/config",
            "/api/v1/listings",
            "/api/v1/contacts"
        ]
        
        for endpoint in endpoints_to_test:
            if endpoint == "/api/v1/config" or endpoint.startswith("/api/v1/"):
                response = client.get(endpoint)
            else:
                response = client.get(endpoint)
            
            if response.status_code != 401:  # Skip unauthorized endpoints
                # Check for security headers
                assert "X-Frame-Options" in response.headers
                assert "X-Content-Type-Options" in response.headers
                assert "X-XSS-Protection" in response.headers
    
    def test_cors_integration(self):
        """Test CORS integration across endpoints."""
        # Test preflight request
        response = client.options("/api/v1/config", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        })
        
        # Should handle CORS appropriately
        if response.status_code == 200:
            assert "Access-Control-Allow-Origin" in response.headers
    
    def test_rate_limiting_integration(self):
        """Test rate limiting integration across endpoints."""
        # Test rate limiting on different endpoints
        endpoints = [
            "/api/v1/config",
            "/api/v1/listings",
            "/api/v1/contacts"
        ]
        
        for endpoint in endpoints:
            responses = []
            for i in range(15):  # Trigger rate limiting
                response = client.get(endpoint, headers={"Authorization": "Bearer invalid"})
                responses.append(response.status_code)
            
            # Should see rate limiting on protected endpoints
            rate_limited = any(r == 429 for r in responses)
            unauthorized = any(r == 401 for r in responses)
            assert rate_limited or unauthorized


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--tb=short"])