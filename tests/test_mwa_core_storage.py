"""
Tests for MWA Core storage module.
"""

import json
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from mwa_core.storage import StorageManager, get_storage_manager, reset_storage_manager
from mwa_core.config import Settings


class TestStorageManager:
    """Test cases for StorageManager class."""
    
    def test_initialization(self):
        """Test storage manager initialization."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = StorageManager(f.name)
            
            assert storage.database_path == f.name
            assert Path(f.name).exists()
            
            Path(f.name).unlink()
    
    def test_database_schema_creation(self):
        """Test that database schema is created correctly."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = StorageManager(f.name)
            
            # Test that tables exist by running a simple query
            with storage.get_connection() as conn:
                # Check listings table
                result = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='listings'"
                ).fetchone()
                assert result is not None
                
                # Check contacts table
                result = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='contacts'"
                ).fetchone()
                assert result is not None
                
                # Check scraping_jobs table
                result = conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name='scraping_jobs'"
                ).fetchone()
                assert result is not None
            
            Path(f.name).unlink()
    
    def test_add_listing(self):
        """Test adding a new listing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = StorageManager(f.name)
            
            listing_data = {
                "provider": "immoscout",
                "external_id": "test_123",
                "title": "Test Apartment",
                "url": "https://example.com/test",
                "price": "1000 €",
                "size": "80 m²",
                "rooms": "3.5",
                "address": "Test Street 1, Munich",
                "description": "Nice apartment for testing",
                "images": ["image1.jpg", "image2.jpg"],
                "contacts": [{"type": "email", "value": "test@example.com"}],
                "raw_data": {"test": "data"}
            }
            
            # Add new listing
            result = storage.add_listing(listing_data)
            assert result is True
            
            # Verify listing was added
            retrieved = storage.get_listing_by_url("https://example.com/test")
            assert retrieved is not None
            assert retrieved["title"] == "Test Apartment"
            assert retrieved["provider"] == "immoscout"
            assert retrieved["price"] == "1000 €"
            
            Path(f.name).unlink()
    
    def test_add_duplicate_listing(self):
        """Test adding a duplicate listing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = StorageManager(f.name)
            
            listing_data = {
                "provider": "immoscout",
                "title": "Test Apartment",
                "url": "https://example.com/test",
                "price": "1000 €"
            }
            
            # Add first listing
            result1 = storage.add_listing(listing_data)
            assert result1 is True
            
            # Try to add duplicate
            result2 = storage.add_listing(listing_data)
            assert result2 is False
            
            Path(f.name).unlink()
    
    def test_get_listings_with_filtering(self):
        """Test getting listings with various filters."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = StorageManager(f.name)
            
            # Add test listings
            listings = [
                {
                    "provider": "immoscout",
                    "title": "Immo Listing 1",
                    "url": "https://immo1.com",
                    "price": "1000 €"
                },
                {
                    "provider": "immoscout",
                    "title": "Immo Listing 2",
                    "url": "https://immo2.com",
                    "price": "1200 €"
                },
                {
                    "provider": "wg_gesucht",
                    "title": "WG Listing 1",
                    "url": "https://wg1.com",
                    "price": "800 €"
                }
            ]
            
            for listing in listings:
                storage.add_listing(listing)
            
            # Test get all listings
            all_listings = storage.get_listings(limit=10)
            assert len(all_listings) == 3
            
            # Test filter by provider
            immo_listings = storage.get_listings(provider="immoscout")
            assert len(immo_listings) == 2
            assert all(l["provider"] == "immoscout" for l in immo_listings)
            
            # Test pagination
            page1 = storage.get_listings(limit=2, offset=0)
            page2 = storage.get_listings(limit=2, offset=2)
            assert len(page1) == 2
            assert len(page2) == 1
            
            Path(f.name).unlink()
    
    def test_update_listing_status(self):
        """Test updating listing status."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = StorageManager(f.name)
            
            listing_data = {
                "provider": "immoscout",
                "title": "Test Apartment",
                "url": "https://example.com/test",
                "price": "1000 €"
            }
            
            storage.add_listing(listing_data)
            
            # Update status
            result = storage.update_listing_status("https://example.com/test", "inactive")
            assert result is True
            
            # Verify status was updated
            updated = storage.get_listing_by_url("https://example.com/test")
            assert updated["status"] == "inactive"
            
            Path(f.name).unlink()
    
    def test_add_contact(self):
        """Test adding contacts to listings."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = StorageManager(f.name)
            
            # Add listing first
            listing_data = {
                "provider": "immoscout",
                "title": "Test Apartment",
                "url": "https://example.com/test",
                "price": "1000 €"
            }
            storage.add_listing(listing_data)
            
            # Get listing ID
            listing = storage.get_listing_by_url("https://example.com/test")
            listing_id = listing["id"]
            
            # Add contact
            contact_data = {
                "type": "email",
                "value": "contact@example.com",
                "confidence": 0.9,
                "source": "scraping",
                "validated": True
            }
            
            result = storage.add_contact(listing_id, contact_data)
            assert result is True
            
            # Verify contact was added
            contacts = storage.get_contacts(listing_id=listing_id)
            assert len(contacts) == 1
            assert contacts[0]["type"] == "email"
            assert contacts[0]["value"] == "contact@example.com"
            
            Path(f.name).unlink()
    
    def test_get_contacts_with_filtering(self):
        """Test getting contacts with various filters."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = StorageManager(f.name)
            
            # Add listing and contacts
            listing_data = {
                "provider": "immoscout",
                "title": "Test Apartment",
                "url": "https://example.com/test",
                "price": "1000 €"
            }
            storage.add_listing(listing_data)
            
            listing = storage.get_listing_by_url("https://example.com/test")
            listing_id = listing["id"]
            
            contacts = [
                {"type": "email", "value": "email1@example.com"},
                {"type": "email", "value": "email2@example.com"},
                {"type": "phone", "value": "+49 123 456789"}
            ]
            
            for contact in contacts:
                storage.add_contact(listing_id, contact)
            
            # Test get all contacts
            all_contacts = storage.get_contacts()
            assert len(all_contacts) == 3
            
            # Test filter by listing ID
            listing_contacts = storage.get_contacts(listing_id=listing_id)
            assert len(listing_contacts) == 3
            
            # Test filter by type
            email_contacts = storage.get_contacts(contact_type="email")
            assert len(email_contacts) == 2
            assert all(c["type"] == "email" for c in email_contacts)
            
            Path(f.name).unlink()
    
    def test_scraping_job_management(self):
        """Test scraping job creation and updates."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = StorageManager(f.name)
            
            # Create job
            job_id = storage.create_scraping_job("immoscout")
            assert job_id > 0
            
            # Update job
            result = storage.update_scraping_job(
                job_id=job_id,
                status="completed",
                listings_found=5,
                errors=["error1", "error2"],
                performance_metrics={"duration": 30.5, "requests": 10}
            )
            assert result is True
            
            # Verify job was updated
            stats = storage.get_statistics()
            recent_jobs = stats["recent_jobs"]
            assert len(recent_jobs) > 0
            assert recent_jobs[0]["status"] == "completed"
            assert recent_jobs[0]["listings_found"] == 5
            
            Path(f.name).unlink()
    
    def test_cleanup_old_data(self):
        """Test cleaning up old data."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = StorageManager(f.name)
            
            # Add old data (this would normally be done with old timestamps)
            # For testing, we'll just verify the method exists and runs
            result = storage.cleanup_old_data(days_to_keep=30)
            assert isinstance(result, int)
            
            Path(f.name).unlink()
    
    def test_get_statistics(self):
        """Test getting database statistics."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = StorageManager(f.name)
            
            # Add test data
            listings = [
                {
                    "provider": "immoscout",
                    "title": "Immo Listing",
                    "url": "https://immo.com",
                    "price": "1000 €"
                },
                {
                    "provider": "wg_gesucht",
                    "title": "WG Listing",
                    "url": "https://wg.com",
                    "price": "800 €"
                }
            ]
            
            for listing in listings:
                storage.add_listing(listing)
            
            # Add contacts
            listing = storage.get_listing_by_url("https://immo.com")
            storage.add_contact(listing["id"], {"type": "email", "value": "test@example.com"})
            
            # Get statistics
            stats = storage.get_statistics()
            
            assert stats["total_listings"] == 2
            assert "immoscout" in stats["listings_by_provider"]
            assert "wg_gesucht" in stats["listings_by_provider"]
            assert stats["total_contacts"] == 1
            assert "email" in stats["contacts_by_type"]
            
            Path(f.name).unlink()
    
    def test_json_field_handling(self):
        """Test proper handling of JSON fields."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = StorageManager(f.name)
            
            listing_data = {
                "provider": "immoscout",
                "title": "Test Apartment",
                "url": "https://example.com/test",
                "price": "1000 €",
                "images": ["image1.jpg", "image2.jpg"],
                "contacts": [{"type": "email", "value": "test@example.com"}],
                "raw_data": {"test": "data", "nested": {"key": "value"}}
            }
            
            storage.add_listing(listing_data)
            
            # Verify JSON fields are properly parsed
            retrieved = storage.get_listing_by_url("https://example.com/test")
            assert isinstance(retrieved["images"], list)
            assert len(retrieved["images"]) == 2
            assert isinstance(retrieved["contacts"], list)
            assert len(retrieved["contacts"]) == 1
            assert isinstance(retrieved["raw_data"], dict)
            assert retrieved["raw_data"]["test"] == "data"
            
            Path(f.name).unlink()


class TestStorageManagerFunctions:
    """Test cases for storage manager utility functions."""
    
    def test_get_storage_manager_singleton(self):
        """Test that get_storage_manager returns a singleton."""
        with patch('mwa_core.storage.manager.StorageManager') as mock_manager:
            mock_instance = MagicMock()
            mock_manager.return_value = mock_instance
            
            manager1 = get_storage_manager()
            manager2 = get_storage_manager()
            
            assert manager1 is manager2
            mock_manager.assert_called_once()
    
    def test_reset_storage_manager(self):
        """Test resetting the storage manager singleton."""
        with patch('mwa_core.storage.manager.StorageManager') as mock_manager:
            mock_instance = MagicMock()
            mock_manager.return_value = mock_instance
            
            # Get manager
            manager1 = get_storage_manager()
            
            # Reset
            reset_storage_manager()
            
            # Get new manager
            manager2 = get_storage_manager()
            
            assert manager1 is not manager2
            assert mock_manager.call_count == 2


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_database_connection_error(self):
        """Test handling of database connection errors."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = StorageManager(f.name)
            
            # Simulate database error by corrupting the file
            Path(f.name).write_text("corrupted data")
            
            with pytest.raises(Exception):
                with storage.get_connection() as conn:
                    conn.execute("SELECT * FROM listings")
            
            Path(f.name).unlink()
    
    def test_invalid_json_data(self):
        """Test handling of invalid JSON data."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = StorageManager(f.name)
            
            # Add listing with invalid JSON data (this should be handled gracefully)
            listing_data = {
                "provider": "immoscout",
                "title": "Test Apartment",
                "url": "https://example.com/test",
                "price": "1000 €",
                "images": None,  # This might cause issues
                "contacts": "invalid",  # This is not a list
                "raw_data": "also invalid"  # This is not a dict
            }
            
            # This should not crash
            result = storage.add_listing(listing_data)
            assert result is True
            
            Path(f.name).unlink()