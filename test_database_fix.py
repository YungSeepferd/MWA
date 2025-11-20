#!/usr/bin/env python3
"""
Test script to verify the ScrapingRun model fix for created_at field.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from mwa_core.storage.manager import EnhancedStorageManager
from mwa_core.storage.models import ScrapingRun, JobStatus
from datetime import datetime

def test_scrapingrun_model():
    """Test that ScrapingRun model has the created_at field."""
    print("Testing ScrapingRun model schema...")
    
    # Create a test database using the EnhancedStorageManager directly
    storage_manager = EnhancedStorageManager(":memory:")
    
    try:
        # Create a test scraping run
        with storage_manager.get_session() as session:
            # Create a new ScrapingRun instance
            scraping_run = ScrapingRun(
                provider="immoscout",
                status=JobStatus.COMPLETED,
                started_at=datetime.now(),
                created_at=datetime.now(),  # This should now work
                listings_found=10,
                listings_processed=10
            )
            
            session.add(scraping_run)
            session.commit()
            
            # Verify the created_at field exists and works
            retrieved_run = session.query(ScrapingRun).first()
            print(f"✓ ScrapingRun created successfully")
            print(f"  - ID: {retrieved_run.id}")
            print(f"  - Provider: {retrieved_run.provider}")
            print(f"  - Started At: {retrieved_run.started_at}")
            print(f"  - Created At: {retrieved_run.created_at}")
            print(f"  - Status: {retrieved_run.status.value}")
            
            # Test the to_dict method
            run_dict = retrieved_run.to_dict()
            print(f"✓ to_dict() method works correctly")
            print(f"  - created_at in dict: {run_dict.get('created_at')}")
            
            # Test querying by created_at (as used in the API)
            runs_by_created_at = session.query(ScrapingRun).order_by(
                ScrapingRun.created_at.desc()
            ).all()
            print(f"✓ Query by created_at works: {len(runs_by_created_at)} runs found")
            
            return True
            
    except Exception as e:
        print(f"✗ Error testing ScrapingRun model: {e}")
        return False

def test_api_compatibility():
    """Test that the API queries work with the new schema."""
    print("\nTesting API compatibility...")
    
    storage_manager = EnhancedStorageManager(":memory:")
    
    try:
        with storage_manager.get_session() as session:
            # Create some test data
            for i in range(3):
                scraping_run = ScrapingRun(
                    provider=f"test_provider_{i}",
                    status=JobStatus.COMPLETED,
                    started_at=datetime.now(),
                    created_at=datetime.now(),
                    listings_found=i * 5,
                    listings_processed=i * 5
                )
                session.add(scraping_run)
            session.commit()
            
            # Test the exact queries used in the API
            # Query 1: Order by created_at.desc()
            last_run = session.query(ScrapingRun).order_by(
                ScrapingRun.created_at.desc()
            ).first()
            print(f"✓ API Query 1 (order_by created_at.desc()): OK")
            
            # Query 2: Filter by created_at >= date
            today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            today_runs = session.query(ScrapingRun).filter(
                ScrapingRun.created_at >= today_start
            ).all()
            print(f"✓ API Query 2 (filter created_at >= date): {len(today_runs)} runs found")
            
            # Query 3: Limit with created_at ordering
            recent_runs = session.query(ScrapingRun).order_by(
                ScrapingRun.created_at.desc()
            ).limit(10).all()
            print(f"✓ API Query 3 (limit with created_at ordering): {len(recent_runs)} runs found")
            
            # Query 4: Pagination with created_at ordering
            paginated_runs = session.query(ScrapingRun).order_by(
                ScrapingRun.created_at.desc()
            ).offset(0).limit(50).all()
            print(f"✓ API Query 4 (pagination with created_at): {len(paginated_runs)} runs found")
            
            return True
            
    except Exception as e:
        print(f"✗ Error testing API compatibility: {e}")
        return False

if __name__ == "__main__":
    print("=== Testing ScrapingRun Database Schema Fix ===\n")
    
    # Test the model itself
    model_test = test_scrapingrun_model()
    
    # Test API compatibility
    api_test = test_api_compatibility()
    
    print("\n=== Test Results ===")
    if model_test and api_test:
        print("✓ All tests passed! Database schema fix is working correctly.")
        print("✓ The ScrapingRun model now has the required 'created_at' field.")
        print("✓ API queries using 'created_at' will now work properly.")
    else:
        print("✗ Some tests failed. Please check the database schema.")
    
    print("\n=== Next Steps ===")
    print("1. Run the database migration to apply the schema changes to your production database")
    print("2. Restart the API server to pick up the changes")
    print("3. Test the scraper endpoints to verify they work correctly")