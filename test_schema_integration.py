#!/usr/bin/env python3
"""
Test script to verify schema integration with routers.

This script tests:
1. Schema imports work correctly
2. Models are valid Pydantic models
3. Integration with existing router patterns
4. Basic validation works
"""

import sys
import os
import traceback
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any

# Add the project root to Python path
sys.path.insert(0, '/Users/dinz/Coding Projects/MWA-MüncheWohnungsAssistent')

def test_schema_imports():
    """Test that all schema modules can be imported successfully."""
    print("🔍 Testing schema imports...")
    
    try:
        # Test individual module imports
        from api.schemas.common import (
            ContactType, ContactStatus, ListingStatus, JobStatus,
            PaginationParams, EmailField, PhoneField, UrlField,
            ErrorResponse, SuccessResponse, ComponentHealth
        )
        print("✅ Common schemas imported successfully")
        
        from api.schemas.config import (
            ConfigResponse, ConfigUpdateRequest, ProviderConfig,
            ConfigValidationResponse
        )
        print("✅ Config schemas imported successfully")
        
        from api.schemas.contacts import (
            ContactResponse, ContactSearchRequest, ContactCreateRequest,
            ContactValidationRequest, ContactStatisticsResponse
        )
        print("✅ Contact schemas imported successfully")
        
        from api.schemas.listings import (
            ListingResponse, ListingSearchRequest, ListingCreateRequest,
            ListingStatisticsResponse, PriceStatistics
        )
        print("✅ Listing schemas imported successfully")
        
        from api.schemas.scraper import (
            ScraperStatusResponse, ScraperRunRequest, ScraperStatisticsResponse,
            PerformanceMetrics
        )
        print("✅ Scraper schemas imported successfully")
        
        from api.schemas.scheduler import (
            SchedulerStatusResponse, JobInfo, JobCreateRequest,
            JobExecutionResponse, JobStatistics
        )
        print("✅ Scheduler schemas imported successfully")
        
        from api.schemas.system import (
            SystemInfoResponse, PerformanceMetricsResponse,
            HealthCheckResponse, ErrorReportRequest
        )
        print("✅ System schemas imported successfully")
        
        # Test package-level import
        import api.schemas
        print("✅ Package-level import successful")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"❌ Unexpected error during imports: {e}")
        traceback.print_exc()
        return False

def test_model_validation():
    """Test that models can be instantiated and validated correctly."""
    print("\n🔍 Testing model validation...")
    
    try:
        from api.schemas.contacts import ContactResponse, ContactSearchRequest
        from api.schemas.common import PaginationParams, ErrorResponse, EmailField
        
        # Test ContactResponse
        contact_data = {
            "id": 1,
            "listing_id": 123,
            "type": "email",
            "value": "test@example.com",
            "confidence": 0.95,
            "source": "ocr_extraction",
            "status": "valid",
            "validated_at": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "validation_metadata": {"method": "regex", "verified": True}
        }
        
        contact_response = ContactResponse(**contact_data)
        assert contact_response.id == 1
        assert contact_response.value == "test@example.com"
        print("✅ ContactResponse validation passed")
        
        # Test ContactSearchRequest
        search_request = ContactSearchRequest(
            query="test",
            contact_type="email",
            limit=50,
            offset=0
        )
        assert search_request.limit == 50
        assert search_request.contact_type == "email"
        print("✅ ContactSearchRequest validation passed")
        
        # Test PaginationParams
        pagination = PaginationParams(limit=20, offset=10)
        assert pagination.limit == 20
        print("✅ PaginationParams validation passed")
        
        # Test ErrorResponse
        error = ErrorResponse(
            error="ValidationError",
            message="Invalid data provided",
            details={"field": "email", "value": "invalid"}
        )
        assert error.error == "ValidationError"
        print("✅ ErrorResponse validation passed")
        
        # Test custom field types
        email_field = EmailField("test@example.com")
        assert str(email_field) == "test@example.com"
        print("✅ EmailField validation passed")
        
        return True
        
    except Exception as e:
        print(f"❌ Validation error: {e}")
        traceback.print_exc()
        return False

def test_schema_consistency():
    """Test consistency between different schema modules."""
    print("\n🔍 Testing schema consistency...")
    
    try:
        from api.schemas.contacts import ContactResponse
        from api.schemas.listings import ListingResponse
        from api.schemas.common import ComponentHealth, HealthCheckResponse
        
        # Test that response models have consistent datetime handling
        now = datetime.now()
        
        # ContactResponse should handle datetime fields
        contact_data = {
            "id": 1,
            "listing_id": 123,
            "type": "email",
            "value": "test@example.com",
            "confidence": 0.95,
            "source": "test",
            "status": "valid",
            "validated_at": now,
            "created_at": now,
            "updated_at": now
        }
        contact = ContactResponse(**contact_data)
        
        # ListingResponse should have similar structure
        listing_data = {
            "id": 456,
            "title": "Test Listing",
            "price": 1000,
            "location": "Munich",
            "url": "https://example.com/listing/456",
            "provider": "immoscout",
            "created_at": now,
            "updated_at": now
        }
        listing = ListingResponse(**listing_data)
        
        print("✅ Schema consistency test passed")
        return True
        
    except Exception as e:
        print(f"❌ Consistency error: {e}")
        traceback.print_exc()
        return False

def test_enum_usage():
    """Test that enums work correctly across modules."""
    print("\n🔍 Testing enum usage...")
    
    try:
        from api.schemas.common import ContactType, ContactStatus, ListingStatus, JobStatus
        from api.schemas.contacts import ContactCreateRequest
        
        # Test enum values
        assert ContactType.EMAIL.value == "email"
        assert ContactStatus.VALID.value == "valid"
        assert ListingStatus.ACTIVE.value == "active"
        assert JobStatus.PENDING.value == "pending"
        print("✅ Enum values are correct")
        
        # Test that models accept enum values
        contact_request = ContactCreateRequest(
            type=ContactType.EMAIL,
            value="test@example.com",
            confidence=0.9,
            source="test"
        )
        assert contact_request.type == "email"
        print("✅ Models accept enum values correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Enum error: {e}")
        traceback.print_exc()
        return False

def test_router_compatibility():
    """Test compatibility with existing router patterns."""
    print("\n🔍 Testing router compatibility...")
    
    try:
        from api.schemas.contacts import ContactResponse, ContactSearchRequest
        
        # Test that our schemas can replace existing router models
        # This simulates how the router would use our new schemas
        
        # Test response model structure
        response_data = {
            "id": 1,
            "listing_id": 123,
            "type": "email",
            "value": "test@example.com",
            "confidence": 0.95,
            "source": "ocr_extraction",
            "status": "valid",
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        contact_response = ContactResponse(**response_data)
        
        # Test search request structure
        search_request = ContactSearchRequest(
            query="test query",
            contact_type="email",
            limit=50,
            offset=0,
            sort_by="confidence",
            sort_order="desc"
        )
        
        print("✅ Router compatibility test passed")
        return True
        
    except Exception as e:
        print(f"❌ Router compatibility error: {e}")
        traceback.print_exc()
        return False

def test_fastapi_integration():
    """Test FastAPI integration capabilities."""
    print("\n🔍 Testing FastAPI integration...")
    
    try:
        from fastapi import FastAPI
        from pydantic import BaseModel
        
        # Create a minimal FastAPI app to test our schemas
        app = FastAPI()
        
        # Test that our schemas work as FastAPI models
        from api.schemas.contacts import ContactResponse, ContactSearchRequest
        from api.schemas.common import ErrorResponse
        
        @app.get("/test-contact", response_model=ContactResponse)
        async def test_contact():
            return ContactResponse(
                id=1,
                listing_id=123,
                type="email",
                value="test@example.com",
                confidence=0.95,
                source="test",
                status="valid",
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
        
        @app.post("/test-search", response_model=Dict[str, Any])
        async def test_search(request: ContactSearchRequest):
            return {"message": "Search request received", "query": request.query}
        
        @app.get("/test-error", responses={400: {"model": ErrorResponse}})
        async def test_error():
            raise HTTPException(status_code=400, detail=ErrorResponse(
                error="BadRequest",
                message="Invalid request",
                details={"field": "test"}
            ))
        
        print("✅ FastAPI integration test passed")
        return True
        
    except Exception as e:
        print(f"❌ FastAPI integration error: {e}")
        traceback.print_exc()
        return False

def test_mwa_core_integration():
    """Test integration with mwa_core models."""
    print("\n🔍 Testing mwa_core integration...")
    
    try:
        # Test that our schemas align with mwa_core patterns
        from mwa_core.storage.models import Contact, ContactType, ContactStatus
        
        # Our schemas should be compatible with mwa_core patterns
        from api.schemas.contacts import ContactResponse
        
        # Test data structure compatibility
        mwa_contact_data = {
            "id": 1,
            "listing_id": 123,
            "type": ContactType.EMAIL,
            "value": "test@example.com",
            "confidence": 0.95,
            "source": "test",
            "status": ContactStatus.VALID,
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }
        
        # Our response model should handle this data
        contact_response = ContactResponse(**mwa_contact_data)
        
        print("✅ mwa_core integration test passed")
        return True
        
    except Exception as e:
        print(f"❌ mwa_core integration error: {e}")
        traceback.print_exc()
        return False

def main():
    """Run all integration tests."""
    print("🚀 Starting MWA Schema Integration Tests")
    print("=" * 50)
    
    tests = [
        ("Schema Imports", test_schema_imports),
        ("Model Validation", test_model_validation),
        ("Schema Consistency", test_schema_consistency),
        ("Enum Usage", test_enum_usage),
        ("Router Compatibility", test_router_compatibility),
        ("FastAPI Integration", test_fastapi_integration),
        ("mwa_core Integration", test_mwa_core_integration),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nTotal: {passed + failed} tests")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    
    if failed == 0:
        print("\n🎉 All tests passed! Schema integration is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {failed} tests failed. Please review the issues above.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)