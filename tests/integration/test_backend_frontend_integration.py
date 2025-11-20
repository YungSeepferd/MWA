"""
Comprehensive backend-to-frontend integration tests for MAFA application.
Tests all API endpoints, WebSocket connections, and data flow integration.
"""

import pytest
import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from api.main import app
from api.ws.manager import WebSocketManager
from api.routers.config import router as config_router
from api.routers.scraper import router as scraper_router
from api.routers.contacts import router as contacts_router
from api.routers.system import router as system_router
from mwa_core.storage.models import Base
from mwa_core.storage.manager import DatabaseManager

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test_integration.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Test client
client = TestClient(app)

# Test data
TEST_CONFIG = {
    "search_preferences": {
        "min_price": 500,
        "max_price": 1500,
        "min_rooms": 1,
        "max_rooms": 3,
        "min_square_meters": 20,
        "max_square_meters": 100,
        "locations": ["Munich", "Freimann", "Schwabing"]
    },
    "notification_settings": {
        "email_enabled": True,
        "telegram_enabled": False,
        "discord_enabled": True,
        "email_address": "test@example.com",
        "discord_webhook": "https://discord.com/api/webhooks/test"
    },
    "scraper_settings": {
        "immoscout_enabled": True,
        "wg_gesucht_enabled": True,
        "search_interval_minutes": 30,
        "max_results_per_search": 50
    }
}

TEST_SEARCH_CONFIG = {
    "name": "Test Search Configuration",
    "provider": "immoscout",
    "criteria": {
        "min_price": 600,
        "max_price": 1200,
        "rooms": 2,
        "locations": ["Munich"],
        "property_types": ["apartment", "flat"]
    },
    "is_active": True,
    "schedule": {
        "interval_minutes": 30,
        "enabled": True
    }
}

TEST_CONTACT = {
    "name": "Test Contact",
    "email": "test.contact@example.com",
    "phone": "+49 123 456789",
    "source": "immoscout",
    "property_details": {
        "title": "Test Apartment",
        "price": 800,
        "rooms": 2,
        "square_meters": 60,
        "location": "Munich"
    },
    "status": "new",
    "priority": "medium"
}


class TestConfigurationIntegration:
    """Test configuration management integration"""
    
    def setup_method(self):
        """Setup test environment"""
        Base.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()
        
    def teardown_method(self):
        """Cleanup test environment"""
        self.db.close()
        Base.metadata.drop_all(bind=engine)
    
    def test_get_configuration(self):
        """Test retrieving current configuration"""
        response = client.get("/api/v1/config/")
        assert response.status_code == 200
        
        data = response.json()
        assert "search_preferences" in data
        assert "notification_settings" in data
        assert "scraper_settings" in data
    
    def test_update_configuration(self):
        """Test updating configuration"""
        response = client.put(
            "/api/v1/config/",
            json=TEST_CONFIG,
            headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["search_preferences"]["min_price"] == 500
        assert data["notification_settings"]["email_enabled"] is True
    
    def test_validate_configuration_basic(self):
        """Test basic configuration validation"""
        response = client.post(
            "/api/v1/config/validate",
            json={"validation_level": "basic", "config": TEST_CONFIG},
            headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["valid"] is True
        assert "errors" in data
        assert "warnings" in data
    
    def test_validate_configuration_with_errors(self):
        """Test configuration validation with errors"""
        invalid_config = TEST_CONFIG.copy()
        invalid_config["search_preferences"]["min_price"] = -100
        invalid_config["search_preferences"]["max_price"] = -50
        
        response = client.post(
            "/api/v1/config/validate",
            json={"validation_level": "standard", "config": invalid_config},
            headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["valid"] is False
        assert len(data["errors"]) > 0
    
    def test_export_configuration(self):
        """Test configuration export"""
        response = client.post(
            "/api/v1/config/export",
            json={"format": "json"},
            headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "export_data" in data
        assert "export_timestamp" in data
        assert "version" in data
    
    def test_import_configuration(self):
        """Test configuration import"""
        response = client.post(
            "/api/v1/config/import",
            json={"config_data": TEST_CONFIG},
            headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["imported"] is True
        assert "imported_fields" in data


class TestSearchManagementIntegration:
    """Test search management integration"""
    
    def setup_method(self):
        """Setup test environment"""
        Base.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()
    
    def teardown_method(self):
        """Cleanup test environment"""
        self.db.close()
        Base.metadata.drop_all(bind=engine)
    
    def test_create_search_configuration(self):
        """Test creating search configuration"""
        response = client.post(
            "/api/v1/scraper/configurations",
            json=TEST_SEARCH_CONFIG,
            headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == TEST_SEARCH_CONFIG["name"]
        assert data["provider"] == TEST_SEARCH_CONFIG["provider"]
        assert "id" in data
    
    def test_get_search_configurations(self):
        """Test retrieving search configurations"""
        # First create a configuration
        client.post(
            "/api/v1/scraper/configurations",
            json=TEST_SEARCH_CONFIG,
            headers={"Authorization": "Bearer test_token"}
        )
        
        response = client.get("/api/v1/scraper/configurations")
        assert response.status_code == 200
        
        data = response.json()
        assert "configurations" in data
        assert len(data["configurations"]) > 0
    
    def test_update_search_configuration(self):
        """Test updating search configuration"""
        # Create configuration first
        create_response = client.post(
            "/api/v1/scraper/configurations",
            json=TEST_SEARCH_CONFIG,
            headers={"Authorization": "Bearer test_token"}
        )
        config_id = create_response.json()["id"]
        
        # Update configuration
        updated_config = TEST_SEARCH_CONFIG.copy()
        updated_config["name"] = "Updated Search Configuration"
        
        response = client.put(
            f"/api/v1/scraper/configurations/{config_id}",
            json=updated_config,
            headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Updated Search Configuration"
    
    def test_delete_search_configuration(self):
        """Test deleting search configuration"""
        # Create configuration first
        create_response = client.post(
            "/api/v1/scraper/configurations",
            json=TEST_SEARCH_CONFIG,
            headers={"Authorization": "Bearer test_token"}
        )
        config_id = create_response.json()["id"]
        
        # Delete configuration
        response = client.delete(
            f"/api/v1/scraper/configurations/{config_id}",
            headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == 200
        
        # Verify deletion
        get_response = client.get("/api/v1/scraper/configurations")
        configs = get_response.json()["configurations"]
        assert not any(c["id"] == config_id for c in configs)
    
    def test_preview_search_results(self):
        """Test search preview functionality"""
        response = client.post(
            "/api/v1/scraper/preview",
            json=TEST_SEARCH_CONFIG,
            headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "preview_results" in data
        assert "estimated_count" in data
        assert "validation_status" in data
    
    def test_start_search_job(self):
        """Test starting search job"""
        # Create configuration first
        create_response = client.post(
            "/api/v1/scraper/configurations",
            json=TEST_SEARCH_CONFIG,
            headers={"Authorization": "Bearer test_token"}
        )
        config_id = create_response.json()["id"]
        
        # Start search job
        response = client.post(
            "/api/v1/scraper/start",
            json={"config_id": config_id},
            headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "job_id" in data
        assert "status" in data
        assert data["status"] == "started"
    
    def test_get_search_statistics(self):
        """Test retrieving search statistics"""
        response = client.get("/api/v1/scraper/statistics")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_configurations" in data
        assert "active_jobs" in data
        assert "total_results" in data
        assert "success_rate" in data


class TestContactManagementIntegration:
    """Test contact management integration"""
    
    def setup_method(self):
        """Setup test environment"""
        Base.metadata.create_all(bind=engine)
        self.db = TestingSessionLocal()
    
    def teardown_method(self):
        """Cleanup test environment"""
        self.db.close()
        Base.metadata.drop_all(bind=engine)
    
    def test_create_contact(self):
        """Test creating contact"""
        response = client.post(
            "/api/v1/contacts/",
            json=TEST_CONTACT,
            headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == 201
        
        data = response.json()
        assert data["name"] == TEST_CONTACT["name"]
        assert data["email"] == TEST_CONTACT["email"]
        assert "id" in data
    
    def test_get_contacts(self):
        """Test retrieving contacts with pagination"""
        # Create test contacts
        for i in range(5):
            contact = TEST_CONTACT.copy()
            contact["name"] = f"Test Contact {i}"
            contact["email"] = f"test{i}@example.com"
            client.post(
                "/api/v1/contacts/",
                json=contact,
                headers={"Authorization": "Bearer test_token"}
            )
        
        response = client.get("/api/v1/contacts/")
        assert response.status_code == 200
        
        data = response.json()
        assert "contacts" in data
        assert "pagination" in data
        assert len(data["contacts"]) > 0
    
    def test_get_contact_details(self):
        """Test retrieving contact details"""
        # Create contact first
        create_response = client.post(
            "/api/v1/contacts/",
            json=TEST_CONTACT,
            headers={"Authorization": "Bearer test_token"}
        )
        contact_id = create_response.json()["id"]
        
        # Get contact details
        response = client.get(f"/api/v1/contacts/{contact_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == contact_id
        assert data["name"] == TEST_CONTACT["name"]
    
    def test_update_contact(self):
        """Test updating contact"""
        # Create contact first
        create_response = client.post(
            "/api/v1/contacts/",
            json=TEST_CONTACT,
            headers={"Authorization": "Bearer test_token"}
        )
        contact_id = create_response.json()["id"]
        
        # Update contact
        updated_contact = TEST_CONTACT.copy()
        updated_contact["status"] = "contacted"
        updated_contact["priority"] = "high"
        
        response = client.put(
            f"/api/v1/contacts/{contact_id}",
            json=updated_contact,
            headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "contacted"
        assert data["priority"] == "high"
    
    def test_delete_contact(self):
        """Test deleting contact"""
        # Create contact first
        create_response = client.post(
            "/api/v1/contacts/",
            json=TEST_CONTACT,
            headers={"Authorization": "Bearer test_token"}
        )
        contact_id = create_response.json()["id"]
        
        # Delete contact
        response = client.delete(
            f"/api/v1/contacts/{contact_id}",
            headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == 200
        
        # Verify deletion
        get_response = client.get(f"/api/v1/contacts/{contact_id}")
        assert get_response.status_code == 404
    
    def test_bulk_contact_operations(self):
        """Test bulk contact operations"""
        # Create test contacts
        contact_ids = []
        for i in range(3):
            contact = TEST_CONTACT.copy()
            contact["name"] = f"Bulk Test Contact {i}"
            contact["email"] = f"bulk{i}@example.com"
            create_response = client.post(
                "/api/v1/contacts/",
                json=contact,
                headers={"Authorization": "Bearer test_token"}
            )
            contact_ids.append(create_response.json()["id"])
        
        # Bulk update
        response = client.post(
            "/api/v1/contacts/bulk",
            json={
                "contact_ids": contact_ids,
                "updates": {"status": "reviewed", "priority": "low"}
            },
            headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["updated_count"] == 3
        assert "updated_contacts" in data
    
    def test_export_contacts(self):
        """Test contact export functionality"""
        # Create test contacts
        for i in range(3):
            contact = TEST_CONTACT.copy()
            contact["name"] = f"Export Test Contact {i}"
            contact["email"] = f"export{i}@example.com"
            client.post(
                "/api/v1/contacts/",
                json=contact,
                headers={"Authorization": "Bearer test_token"}
            )
        
        response = client.post(
            "/api/v1/contacts/export",
            json={"format": "json", "filters": {}},
            headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "export_data" in data
        assert "export_timestamp" in data
        assert "total_contacts" in data


class TestSystemIntegration:
    """Test system endpoints integration"""
    
    def test_system_health(self):
        """Test system health endpoint"""
        response = client.get("/api/v1/system/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "services" in data
    
    def test_system_info(self):
        """Test system information endpoint"""
        response = client.get("/api/v1/system/info")
        assert response.status_code == 200
        
        data = response.json()
        assert "version" in data
        assert "environment" in data
        assert "uptime" in data
    
    def test_system_metrics(self):
        """Test system metrics endpoint"""
        response = client.get("/api/v1/system/metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert "cpu_usage" in data
        assert "memory_usage" in data
        assert "disk_usage" in data
    
    def test_system_logs(self):
        """Test system logs endpoint"""
        response = client.get("/api/v1/system/logs")
        assert response.status_code == 200
        
        data = response.json()
        assert "logs" in data
        assert "pagination" in data


class TestWebSocketIntegration:
    """Test WebSocket integration"""
    
    def setup_method(self):
        """Setup test environment"""
        self.ws_manager = WebSocketManager()
    
    def test_websocket_connection(self):
        """Test WebSocket connection establishment"""
        with client.websocket_connect("/ws") as websocket:
            # Test connection
            data = websocket.receive_json()
            assert data["type"] == "connection_established"
    
    def test_dashboard_update_broadcast(self):
        """Test dashboard update broadcasting"""
        with client.websocket_connect("/ws") as websocket:
            # Send dashboard update
            test_data = {
                "total_contacts": 100,
                "active_searches": 5,
                "new_contacts_today": 10
            }
            
            self.ws_manager.broadcast_dashboard_update(test_data)
            
            # Receive broadcast
            data = websocket.receive_json()
            assert data["type"] == "DASHBOARD_UPDATE"
            assert data["data"]["total_contacts"] == 100
    
    def test_contact_update_broadcast(self):
        """Test contact update broadcasting"""
        with client.websocket_connect("/ws") as websocket:
            # Send contact update
            test_contact = {
                "id": "test_contact_1",
                "name": "Test Contact",
                "status": "new",
                "action": "created"
            }
            
            self.ws_manager.broadcast_contact_update(test_contact)
            
            # Receive broadcast
            data = websocket.receive_json()
            assert data["type"] == "CONTACT_UPDATE"
            assert data["data"]["id"] == "test_contact_1"
    
    def test_search_status_broadcast(self):
        """Test search status broadcasting"""
        with client.websocket_connect("/ws") as websocket:
            # Send search status update
            test_status = {
                "config_id": "test_config_1",
                "job_id": "test_job_1",
                "status": "running",
                "progress": 45
            }
            
            self.ws_manager.broadcast_search_status(test_status)
            
            # Receive broadcast
            data = websocket.receive_json()
            assert data["type"] == "SEARCH_STATUS"
            assert data["data"]["status"] == "running"
    
    def test_progress_update_broadcast(self):
        """Test progress update broadcasting"""
        with client.websocket_connect("/ws") as websocket:
            # Send progress update
            test_progress = {
                "job_id": "test_job_1",
                "job_type": "scraping",
                "progress": 75,
                "message": "Processing results..."
            }
            
            self.ws_manager.broadcast_progress_update(test_progress)
            
            # Receive broadcast
            data = websocket.receive_json()
            assert data["type"] == "PROGRESS_UPDATE"
            assert data["data"]["progress"] == 75


class TestErrorHandlingIntegration:
    """Test error handling integration"""
    
    def test_authentication_error(self):
        """Test authentication error handling"""
        response = client.get("/api/v1/config/")
        assert response.status_code == 401
        
        data = response.json()
        assert "detail" in data
        assert "error_type" in data
        assert data["error_type"] == "authentication_error"
    
    def test_validation_error(self):
        """Test validation error handling"""
        invalid_config = {
            "search_preferences": {
                "min_price": "invalid",  # Should be number
                "max_price": -100  # Invalid value
            }
        }
        
        response = client.put(
            "/api/v1/config/",
            json=invalid_config,
            headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == 422
        
        data = response.json()
        assert "detail" in data
        assert "error_type" in data
        assert data["error_type"] == "validation_error"
    
    def test_not_found_error(self):
        """Test not found error handling"""
        response = client.get(
            "/api/v1/contacts/nonexistent_id",
            headers={"Authorization": "Bearer test_token"}
        )
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
        assert "error_type" in data
        assert data["error_type"] == "not_found_error"
    
    def test_server_error_handling(self):
        """Test server error handling"""
        # This would typically test a scenario that causes a server error
        # For now, we'll test the error response format
        response = client.post(
            "/api/v1/scraper/start",
            json={"config_id": "nonexistent_id"},
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Should handle gracefully even if config doesn't exist
        assert response.status_code in [404, 500]
        
        data = response.json()
        assert "detail" in data
        assert "error_type" in data


class TestPerformanceIntegration:
    """Test performance integration"""
    
    def test_api_response_times(self):
        """Test API response times"""
        endpoints = [
            "/api/v1/config/",
            "/api/v1/scraper/configurations",
            "/api/v1/contacts/",
            "/api/v1/system/health"
        ]
        
        for endpoint in endpoints:
            start_time = time.time()
            response = client.get(endpoint)
            end_time = time.time()
            
            response_time = end_time - start_time
            
            # API should respond within 1 second
            assert response_time < 1.0, f"Endpoint {endpoint} took too long: {response_time}s"
    
    def test_pagination_performance(self):
        """Test pagination performance with large datasets"""
        # Create many contacts
        for i in range(100):
            contact = TEST_CONTACT.copy()
            contact["name"] = f"Performance Test Contact {i}"
            contact["email"] = f"perf{i}@example.com"
            client.post(
                "/api/v1/contacts/",
                json=contact,
                headers={"Authorization": "Bearer test_token"}
            )
        
        # Test pagination
        start_time = time.time()
        response = client.get("/api/v1/contacts/?page=1&limit=20")
        end_time = time.time()
        
        response_time = end_time - start_time
        
        # Pagination should be fast even with many records
        assert response_time < 0.5, f"Pagniation took too long: {response_time}s"
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["contacts"]) == 20
        assert data["pagination"]["total"] >= 100
    
    def test_concurrent_requests(self):
        """Test handling concurrent requests"""
        import threading
        import queue
        
        results = queue.Queue()
        
        def make_request():
            try:
                response = client.get("/api/v1/system/health")
                results.put(response.status_code)
            except Exception as e:
                results.put(str(e))
        
        # Make 10 concurrent requests
        threads = []
        for _ in range(10):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        success_count = 0
        while not results.empty():
            result = results.get()
            if result == 200:
                success_count += 1
        
        # Most requests should succeed
        assert success_count >= 8, f"Only {success_count}/10 requests succeeded"


class TestSecurityIntegration:
    """Test security integration"""
    
    def test_csrf_protection(self):
        """Test CSRF protection"""
        # This test would verify CSRF token handling
        # For now, we'll test that the endpoint exists
        response = client.get("/api/v1/auth/csrf-token")
        assert response.status_code in [200, 401]  # May require auth
    
    def test_rate_limiting(self):
        """Test rate limiting"""
        # Make multiple rapid requests
        responses = []
        for _ in range(20):
            response = client.get("/api/v1/system/health")
            responses.append(response.status_code)
        
        # Should allow reasonable number of requests
        success_count = sum(1 for status in responses if status == 200)
        assert success_count >= 10, f"Rate limiting too strict: {success_count}/20 succeeded"
    
    def test_input_sanitization(self):
        """Test input sanitization"""
        # Test with potentially malicious input
        malicious_config = TEST_CONFIG.copy()
        malicious_config["search_preferences"]["locations"] = [
            "Munich<script>alert('xss')</script>",
            "'; DROP TABLE contacts; --"
        ]
        
        response = client.post(
            "/api/v1/config/validate",
            json={"validation_level": "basic", "config": malicious_config},
            headers={"Authorization": "Bearer test_token"}
        )
        
        # Should handle malicious input gracefully
        assert response.status_code in [200, 422]
        
        if response.status_code == 200:
            data = response.json()
            # Should either be valid with sanitized input or invalid due to detection
            assert "valid" in data


# Integration test runner
class IntegrationTestRunner:
    """Run all integration tests"""
    
    @staticmethod
    def run_all_tests():
        """Run all integration test suites"""
        test_suites = [
            TestConfigurationIntegration,
            TestSearchManagementIntegration,
            TestContactManagementIntegration,
            TestSystemIntegration,
            TestWebSocketIntegration,
            TestErrorHandlingIntegration,
            TestPerformanceIntegration,
            TestSecurityIntegration
        ]
        
        results = {}
        
        for test_suite in test_suites:
            suite_name = test_suite.__name__
            print(f"Running {suite_name}...")
            
            try:
                # Create test instance
                test_instance = test_suite()
                
                # Get all test methods
                test_methods = [method for method in dir(test_instance) 
                              if method.startswith('test_')]
                
                suite_results = []
                for test_method in test_methods:
                    try:
                        # Setup if available
                        if hasattr(test_instance, 'setup_method'):
                            test_instance.setup_method()
                        
                        # Run test
                        getattr(test_instance, test_method)()
                        suite_results.append((test_method, "PASSED"))
                        
                        # Teardown if available
                        if hasattr(test_instance, 'teardown_method'):
                            test_instance.teardown_method()
                            
                    except Exception as e:
                        suite_results.append((test_method, f"FAILED: {str(e)}"))
                
                results[suite_name] = suite_results
                
            except Exception as e:
                results[suite_name] = [("SUITE_SETUP", f"FAILED: {str(e)}")]
        
        return results
    
    @staticmethod
    def generate_report(results: Dict[str, List[tuple]]) -> str:
        """Generate test report"""
        report = ["# Integration Test Report\n"]
        report.append(f"Generated: {datetime.now().isoformat()}\n")
        
        total_tests = 0
        passed_tests = 0
        
        for suite_name, test_results in results.items():
            report.append(f"## {suite_name}\n")
            
            for test_name, status in test_results:
                total_tests += 1
                if status == "PASSED":
                    passed_tests += 1
                    report.append(f"✅ {test_name}")
                else:
                    report.append(f"❌ {test_name}: {status}")
            
            report.append("")
        
        # Summary
        report.append("## Summary")
        report.append(f"Total Tests: {total_tests}")
        report.append(f"Passed: {passed_tests}")
        report.append(f"Failed: {total_tests - passed_tests}")
        report.append(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        return "\n".join(report)


if __name__ == "__main__":
    # Run all integration tests
    runner = IntegrationTestRunner()
    results = runner.run_all_tests()
    
    # Generate and print report
    report = runner.generate_report(results)
    print(report)
    
    # Save report to file
    with open("integration_test_report.md", "w") as f:
        f.write(report)
    
    print("\nIntegration test report saved to integration_test_report.md")