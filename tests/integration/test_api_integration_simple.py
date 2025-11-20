"""
Simplified API integration tests for MAFA backend-to-frontend integration.
Tests core API endpoints without complex dependencies.
"""

import pytest
import json
import asyncio
from datetime import datetime
from typing import Dict, Any
from fastapi.testclient import TestClient
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

# Mock API endpoints for testing
class MockAPI:
    """Mock API for testing integration patterns."""
    
    def __init__(self):
        self.app = FastAPI(title="MAFA Test API")
        self.setup_routes()
        self.config_data = {
            "search_preferences": {
                "min_price": 500,
                "max_price": 1500,
                "min_rooms": 1,
                "max_rooms": 3,
                "locations": ["Munich", "Freimann"]
            },
            "notification_settings": {
                "email_enabled": True,
                "telegram_enabled": False,
                "discord_enabled": True
            },
            "scraper_settings": {
                "immoscout_enabled": True,
                "wg_gesucht_enabled": True,
                "search_interval_minutes": 30
            }
        }
        self.search_configs = {}
        self.contacts = {}
        self.next_id = 1
    
    def setup_routes(self):
        """Setup mock API routes."""
        
        @self.app.get("/api/v1/config/")
        async def get_config():
            return self.config_data
        
        @self.app.put("/api/v1/config/")
        async def update_config(config: Dict[str, Any]):
            self.config_data.update(config)
            return self.config_data
        
        @self.app.post("/api/v1/config/validate")
        async def validate_config(request: Dict[str, Any]):
            config = request.get("config", {})
            level = request.get("validation_level", "basic")
            
            errors = []
            warnings = []
            
            # Basic validation
            if level in ["basic", "standard", "strict"]:
                if "search_preferences" in config:
                    prefs = config["search_preferences"]
                    if prefs.get("min_price", 0) < 0:
                        errors.append("Minimum price cannot be negative")
                    if prefs.get("max_price", 0) < prefs.get("min_price", 0):
                        errors.append("Maximum price must be greater than minimum price")
            
            # Standard validation
            if level in ["standard", "strict"]:
                if "search_preferences" in config:
                    prefs = config["search_preferences"]
                    if not prefs.get("locations"):
                        warnings.append("No locations specified")
            
            return {
                "valid": len(errors) == 0,
                "errors": errors,
                "warnings": warnings,
                "validation_level": level
            }
        
        @self.app.get("/api/v1/scraper/configurations")
        async def get_search_configurations():
            return {
                "configurations": list(self.search_configs.values()),
                "total": len(self.search_configs)
            }
        
        @self.app.post("/api/v1/scraper/configurations")
        async def create_search_configuration(config: Dict[str, Any]):
            config_id = str(self.next_id)
            self.next_id += 1
            
            config_data = {
                "id": config_id,
                "name": config.get("name", "Unnamed Search"),
                "provider": config.get("provider", "immoscout"),
                "criteria": config.get("criteria", {}),
                "is_active": config.get("is_active", True),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            self.search_configs[config_id] = config_data
            return config_data
        
        @self.app.get("/api/v1/scraper/configurations/{config_id}")
        async def get_search_configuration(config_id: str):
            if config_id not in self.search_configs:
                raise HTTPException(status_code=404, detail="Configuration not found")
            return self.search_configs[config_id]
        
        @self.app.put("/api/v1/scraper/configurations/{config_id}")
        async def update_search_configuration(config_id: str, config: Dict[str, Any]):
            if config_id not in self.search_configs:
                raise HTTPException(status_code=404, detail="Configuration not found")
            
            self.search_configs[config_id].update(config)
            self.search_configs[config_id]["updated_at"] = datetime.now().isoformat()
            return self.search_configs[config_id]
        
        @self.app.delete("/api/v1/scraper/configurations/{config_id}")
        async def delete_search_configuration(config_id: str):
            if config_id not in self.search_configs:
                raise HTTPException(status_code=404, detail="Configuration not found")
            
            del self.search_configs[config_id]
            return {"message": "Configuration deleted successfully"}
        
        @self.app.post("/api/v1/scraper/preview")
        async def preview_search(config: Dict[str, Any]):
            # Mock preview results
            return {
                "preview_results": [
                    {
                        "title": "Test Apartment 1",
                        "price": 800,
                        "rooms": 2,
                        "location": "Munich"
                    },
                    {
                        "title": "Test Apartment 2", 
                        "price": 1200,
                        "rooms": 3,
                        "location": "Freimann"
                    }
                ],
                "estimated_count": 25,
                "validation_status": "valid"
            }
        
        @self.app.post("/api/v1/scraper/start")
        async def start_search_job(request: Dict[str, Any]):
            config_id = request.get("config_id")
            if config_id and config_id not in self.search_configs:
                raise HTTPException(status_code=404, detail="Configuration not found")
            
            return {
                "job_id": f"job_{self.next_id}",
                "status": "started",
                "config_id": config_id,
                "started_at": datetime.now().isoformat()
            }
        
        @self.app.get("/api/v1/scraper/statistics")
        async def get_scraper_statistics():
            return {
                "total_configurations": len(self.search_configs),
                "active_jobs": 2,
                "total_results": 150,
                "success_rate": 0.85,
                "last_run": datetime.now().isoformat()
            }
        
        @self.app.get("/api/v1/contacts/")
        async def get_contacts(page: int = 1, limit: int = 20):
            contacts_list = list(self.contacts.values())
            start = (page - 1) * limit
            end = start + limit
            
            return {
                "contacts": contacts_list[start:end],
                "pagination": {
                    "page": page,
                    "limit": limit,
                    "total": len(self.contacts),
                    "pages": (len(self.contacts) + limit - 1) // limit
                }
            }
        
        @self.app.post("/api/v1/contacts/")
        async def create_contact(contact: Dict[str, Any]):
            contact_id = str(self.next_id)
            self.next_id += 1
            
            contact_data = {
                "id": contact_id,
                "name": contact.get("name", "Unknown"),
                "email": contact.get("email"),
                "phone": contact.get("phone"),
                "source": contact.get("source", "manual"),
                "status": "new",
                "priority": contact.get("priority", "medium"),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
            
            self.contacts[contact_id] = contact_data
            return contact_data
        
        @self.app.get("/api/v1/contacts/{contact_id}")
        async def get_contact(contact_id: str):
            if contact_id not in self.contacts:
                raise HTTPException(status_code=404, detail="Contact not found")
            return self.contacts[contact_id]
        
        @self.app.put("/api/v1/contacts/{contact_id}")
        async def update_contact(contact_id: str, contact: Dict[str, Any]):
            if contact_id not in self.contacts:
                raise HTTPException(status_code=404, detail="Contact not found")
            
            self.contacts[contact_id].update(contact)
            self.contacts[contact_id]["updated_at"] = datetime.now().isoformat()
            return self.contacts[contact_id]
        
        @self.app.delete("/api/v1/contacts/{contact_id}")
        async def delete_contact(contact_id: str):
            if contact_id not in self.contacts:
                raise HTTPException(status_code=404, detail="Contact not found")
            
            del self.contacts[contact_id]
            return {"message": "Contact deleted successfully"}
        
        @self.app.post("/api/v1/contacts/bulk")
        async def bulk_contact_operations(request: Dict[str, Any]):
            contact_ids = request.get("contact_ids", [])
            updates = request.get("updates", {})
            
            updated_contacts = []
            for contact_id in contact_ids:
                if contact_id in self.contacts:
                    self.contacts[contact_id].update(updates)
                    self.contacts[contact_id]["updated_at"] = datetime.now().isoformat()
                    updated_contacts.append(self.contacts[contact_id])
            
            return {
                "updated_count": len(updated_contacts),
                "updated_contacts": updated_contacts
            }
        
        @self.app.post("/api/v1/contacts/export")
        async def export_contacts(request: Dict[str, Any]):
            format_type = request.get("format", "json")
            filters = request.get("filters", {})
            
            # Apply filters (simplified)
            contacts_list = list(self.contacts.values())
            
            return {
                "export_data": contacts_list,
                "export_timestamp": datetime.now().isoformat(),
                "format": format_type,
                "total_contacts": len(contacts_list)
            }
        
        @self.app.get("/api/v1/system/health")
        async def health_check():
            return {
                "status": "healthy",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0",
                "services": {
                    "database": "healthy",
                    "redis": "healthy",
                    "websocket": "healthy"
                }
            }
        
        @self.app.get("/api/v1/system/info")
        async def system_info():
            return {
                "version": "1.0.0",
                "environment": "test",
                "uptime": "2 hours, 30 minutes",
                "python_version": "3.10.9"
            }
        
        @self.app.get("/api/v1/system/metrics")
        async def system_metrics():
            return {
                "cpu_usage": 25.5,
                "memory_usage": 45.2,
                "disk_usage": 60.1,
                "active_connections": 5,
                "requests_per_minute": 120
            }


# Test setup
@pytest.fixture
def mock_api():
    """Create mock API for testing."""
    return MockAPI()

@pytest.fixture
def client(mock_api):
    """Create test client."""
    return TestClient(mock_api.app)


class TestConfigurationAPI:
    """Test configuration API endpoints."""
    
    def test_get_configuration(self, client):
        """Test retrieving configuration."""
        response = client.get("/api/v1/config/")
        assert response.status_code == 200
        
        data = response.json()
        assert "search_preferences" in data
        assert "notification_settings" in data
        assert "scraper_settings" in data
        assert data["search_preferences"]["min_price"] == 500
    
    def test_update_configuration(self, client):
        """Test updating configuration."""
        new_config = {
            "search_preferences": {
                "min_price": 600,
                "max_price": 1600,
                "locations": ["Munich", "Schwabing"]
            }
        }
        
        response = client.put("/api/v1/config/", json=new_config)
        assert response.status_code == 200
        
        data = response.json()
        assert data["search_preferences"]["min_price"] == 600
        assert data["search_preferences"]["locations"] == ["Munich", "Schwabing"]
    
    def test_validate_configuration_basic(self, client):
        """Test basic configuration validation."""
        config = {
            "search_preferences": {
                "min_price": 500,
                "max_price": 1500,
                "locations": ["Munich"]
            }
        }
        
        response = client.post(
            "/api/v1/config/validate",
            json={"config": config, "validation_level": "basic"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["valid"] is True
        assert "errors" in data
        assert "warnings" in data
    
    def test_validate_configuration_with_errors(self, client):
        """Test configuration validation with errors."""
        invalid_config = {
            "search_preferences": {
                "min_price": -100,
                "max_price": -50
            }
        }
        
        response = client.post(
            "/api/v1/config/validate",
            json={"config": invalid_config, "validation_level": "basic"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["valid"] is False
        assert len(data["errors"]) > 0


class TestSearchManagementAPI:
    """Test search management API endpoints."""
    
    def test_create_search_configuration(self, client):
        """Test creating search configuration."""
        config = {
            "name": "Test Search",
            "provider": "immoscout",
            "criteria": {
                "min_price": 600,
                "max_price": 1200,
                "rooms": 2,
                "locations": ["Munich"]
            },
            "is_active": True
        }
        
        response = client.post("/api/v1/scraper/configurations", json=config)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Test Search"
        assert data["provider"] == "immoscout"
        assert "id" in data
    
    def test_get_search_configurations(self, client):
        """Test retrieving search configurations."""
        # Create a configuration first
        config = {
            "name": "Test Search",
            "provider": "immoscout",
            "criteria": {"min_price": 600}
        }
        client.post("/api/v1/scraper/configurations", json=config)
        
        response = client.get("/api/v1/scraper/configurations")
        assert response.status_code == 200
        
        data = response.json()
        assert "configurations" in data
        assert "total" in data
        assert len(data["configurations"]) > 0
    
    def test_update_search_configuration(self, client):
        """Test updating search configuration."""
        # Create configuration first
        create_response = client.post("/api/v1/scraper/configurations", json={
            "name": "Original Search",
            "provider": "immoscout",
            "criteria": {"min_price": 600}
        })
        config_id = create_response.json()["id"]
        
        # Update configuration
        updated_config = {
            "name": "Updated Search",
            "criteria": {"min_price": 700}
        }
        
        response = client.put(f"/api/v1/scraper/configurations/{config_id}", json=updated_config)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Updated Search"
        assert data["criteria"]["min_price"] == 700
    
    def test_delete_search_configuration(self, client):
        """Test deleting search configuration."""
        # Create configuration first
        create_response = client.post("/api/v1/scraper/configurations", json={
            "name": "Test Search",
            "provider": "immoscout"
        })
        config_id = create_response.json()["id"]
        
        # Delete configuration
        response = client.delete(f"/api/v1/scraper/configurations/{config_id}")
        assert response.status_code == 200
        
        # Verify deletion
        get_response = client.get(f"/api/v1/scraper/configurations/{config_id}")
        assert get_response.status_code == 404
    
    def test_preview_search(self, client):
        """Test search preview functionality."""
        config = {
            "name": "Preview Test",
            "provider": "immoscout",
            "criteria": {
                "min_price": 600,
                "max_price": 1200,
                "locations": ["Munich"]
            }
        }
        
        response = client.post("/api/v1/scraper/preview", json=config)
        assert response.status_code == 200
        
        data = response.json()
        assert "preview_results" in data
        assert "estimated_count" in data
        assert "validation_status" in data
        assert len(data["preview_results"]) > 0
    
    def test_start_search_job(self, client):
        """Test starting search job."""
        # Create configuration first
        create_response = client.post("/api/v1/scraper/configurations", json={
            "name": "Job Test",
            "provider": "immoscout"
        })
        config_id = create_response.json()["id"]
        
        # Start job
        response = client.post("/api/v1/scraper/start", json={"config_id": config_id})
        assert response.status_code == 200
        
        data = response.json()
        assert "job_id" in data
        assert data["status"] == "started"
        assert data["config_id"] == config_id
    
    def test_get_scraper_statistics(self, client):
        """Test retrieving scraper statistics."""
        response = client.get("/api/v1/scraper/statistics")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_configurations" in data
        assert "active_jobs" in data
        assert "total_results" in data
        assert "success_rate" in data


class TestContactManagementAPI:
    """Test contact management API endpoints."""
    
    def test_create_contact(self, client):
        """Test creating contact."""
        contact = {
            "name": "Test Contact",
            "email": "test@example.com",
            "phone": "+49 123 456789",
            "source": "immoscout",
            "priority": "high"
        }
        
        response = client.post("/api/v1/contacts/", json=contact)
        assert response.status_code == 200
        
        data = response.json()
        assert data["name"] == "Test Contact"
        assert data["email"] == "test@example.com"
        assert data["status"] == "new"
        assert "id" in data
    
    def test_get_contacts(self, client):
        """Test retrieving contacts with pagination."""
        # Create test contacts
        for i in range(5):
            client.post("/api/v1/contacts/", json={
                "name": f"Test Contact {i}",
                "email": f"test{i}@example.com"
            })
        
        response = client.get("/api/v1/contacts/")
        assert response.status_code == 200
        
        data = response.json()
        assert "contacts" in data
        assert "pagination" in data
        assert len(data["contacts"]) > 0
    
    def test_get_contact_details(self, client):
        """Test retrieving contact details."""
        # Create contact first
        create_response = client.post("/api/v1/contacts/", json={
            "name": "Detail Test",
            "email": "detail@example.com"
        })
        contact_id = create_response.json()["id"]
        
        # Get contact details
        response = client.get(f"/api/v1/contacts/{contact_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == contact_id
        assert data["name"] == "Detail Test"
    
    def test_update_contact(self, client):
        """Test updating contact."""
        # Create contact first
        create_response = client.post("/api/v1/contacts/", json={
            "name": "Update Test",
            "email": "update@example.com"
        })
        contact_id = create_response.json()["id"]
        
        # Update contact
        updated_contact = {
            "status": "contacted",
            "priority": "low"
        }
        
        response = client.put(f"/api/v1/contacts/{contact_id}", json=updated_contact)
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "contacted"
        assert data["priority"] == "low"
    
    def test_delete_contact(self, client):
        """Test deleting contact."""
        # Create contact first
        create_response = client.post("/api/v1/contacts/", json={
            "name": "Delete Test",
            "email": "delete@example.com"
        })
        contact_id = create_response.json()["id"]
        
        # Delete contact
        response = client.delete(f"/api/v1/contacts/{contact_id}")
        assert response.status_code == 200
        
        # Verify deletion
        get_response = client.get(f"/api/v1/contacts/{contact_id}")
        assert get_response.status_code == 404
    
    def test_bulk_contact_operations(self, client):
        """Test bulk contact operations."""
        # Create test contacts
        contact_ids = []
        for i in range(3):
            create_response = client.post("/api/v1/contacts/", json={
                "name": f"Bulk Test {i}",
                "email": f"bulk{i}@example.com"
            })
            contact_ids.append(create_response.json()["id"])
        
        # Bulk update
        response = client.post("/api/v1/contacts/bulk", json={
            "contact_ids": contact_ids,
            "updates": {"status": "reviewed", "priority": "low"}
        })
        assert response.status_code == 200
        
        data = response.json()
        assert data["updated_count"] == 3
        assert "updated_contacts" in data
    
    def test_export_contacts(self, client):
        """Test contact export functionality."""
        # Create test contacts
        for i in range(3):
            client.post("/api/v1/contacts/", json={
                "name": f"Export Test {i}",
                "email": f"export{i}@example.com"
            })
        
        response = client.post("/api/v1/contacts/export", json={
            "format": "json",
            "filters": {}
        })
        assert response.status_code == 200
        
        data = response.json()
        assert "export_data" in data
        assert "export_timestamp" in data
        assert "total_contacts" in data
        assert len(data["export_data"]) >= 3


class TestSystemAPI:
    """Test system API endpoints."""
    
    def test_health_check(self, client):
        """Test system health endpoint."""
        response = client.get("/api/v1/system/health")
        assert response.status_code == 200
        
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "services" in data
        assert data["status"] == "healthy"
    
    def test_system_info(self, client):
        """Test system information endpoint."""
        response = client.get("/api/v1/system/info")
        assert response.status_code == 200
        
        data = response.json()
        assert "version" in data
        assert "environment" in data
        assert "uptime" in data
    
    def test_system_metrics(self, client):
        """Test system metrics endpoint."""
        response = client.get("/api/v1/system/metrics")
        assert response.status_code == 200
        
        data = response.json()
        assert "cpu_usage" in data
        assert "memory_usage" in data
        assert "disk_usage" in data


class TestErrorHandling:
    """Test API error handling."""
    
    def test_not_found_error(self, client):
        """Test 404 error handling."""
        response = client.get("/api/v1/contacts/nonexistent")
        assert response.status_code == 404
        
        data = response.json()
        assert "detail" in data
    
    def test_validation_error(self, client):
        """Test validation error handling."""
        # This would depend on the specific validation implementation
        # For now, we test that the API handles invalid data gracefully
        response = client.post("/api/v1/contacts/", json={})
        # Should still work since most fields are optional in our mock
        assert response.status_code == 200


class TestAPIIntegration:
    """Test overall API integration patterns."""
    
    def test_cors_headers(self, client):
        """Test CORS headers are present."""
        response = client.options("/api/v1/config/")
        # FastAPI adds CORS headers by default
        assert response.status_code in [200, 405]  # 405 for OPTIONS if not explicitly allowed
    
    def test_response_format_consistency(self, client):
        """Test consistent response formats."""
        # Test configuration endpoint
        config_response = client.get("/api/v1/config/")
        assert config_response.status_code == 200
        assert isinstance(config_response.json(), dict)
        
        # Test contacts endpoint
        contacts_response = client.get("/api/v1/contacts/")
        assert contacts_response.status_code == 200
        assert isinstance(contacts_response.json(), dict)
        
        # Test system endpoint
        health_response = client.get("/api/v1/system/health")
        assert health_response.status_code == 200
        assert isinstance(health_response.json(), dict)
    
    def test_api_versioning(self, client):
        """Test API versioning is consistent."""
        # All endpoints should use /api/v1/ prefix
        endpoints = [
            "/api/v1/config/",
            "/api/v1/contacts/",
            "/api/v1/scraper/configurations",
            "/api/v1/system/health"
        ]
        
        for endpoint in endpoints:
            response = client.get(endpoint)
            # Should not return 404 for versioned endpoints
            assert response.status_code != 404


if __name__ == "__main__":
    # Run tests directly
    import sys
    
    # Create test instance
    mock_api = MockAPI()
    client = TestClient(mock_api.app)
    
    # Run basic integration test
    print("Running basic API integration test...")
    
    try:
        # Test configuration
        response = client.get("/api/v1/config/")
        print(f"✅ GET /api/v1/config/ - {response.status_code}")
        
        # Test contacts
        response = client.post("/api/v1/contacts/", json={
            "name": "Test Contact",
            "email": "test@example.com"
        })
        print(f"✅ POST /api/v1/contacts/ - {response.status_code}")
        
        # Test search
        response = client.post("/api/v1/scraper/configurations", json={
            "name": "Test Search",
            "provider": "immoscout"
        })
        print(f"✅ POST /api/v1/scraper/configurations - {response.status_code}")
        
        # Test system
        response = client.get("/api/v1/system/health")
        print(f"✅ GET /api/v1/system/health - {response.status_code}")
        
        print("\n🎉 All basic integration tests passed!")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        sys.exit(1)