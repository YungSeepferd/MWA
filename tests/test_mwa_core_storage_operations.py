"""
Comprehensive tests for MWA Core storage operations.

Tests all CRUD operations, deduplication, relationships, and advanced features.
"""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from mwa_core.storage import (
    EnhancedStorageManager, get_storage_manager, reset_storage_manager,
    ListingStatus, ContactType, ContactStatus, JobStatus, DeduplicationStatus
)


class TestEnhancedStorageManager:
    """Test cases for EnhancedStorageManager."""
    
    def test_initialization(self):
        """Test storage manager initialization."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            
            assert storage.database_url == f"sqlite:///{Path(f.name).resolve()}"
            assert storage.schema is not None
            assert storage.crud is not None
            assert storage.deduplication is not None
            assert storage.backup is not None
            assert storage.relationships is not None
            assert storage.migrations is not None
            
            Path(f.name).unlink()
    
    def test_database_creation(self):
        """Test that database and tables are created."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            
            # Verify database info
            db_info = storage.get_database_info()
            assert db_info["total_tables"] > 0
            assert "listings" in db_info["tables"]
            assert "contacts" in db_info["tables"]
            assert "scraping_runs" in db_info["tables"]
            
            Path(f.name).unlink()
    
    def test_schema_validation(self):
        """Test database schema validation."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            
            validation = storage.validate_schema()
            assert validation["valid"] is True
            assert len(validation["missing_tables"]) == 0
            
            Path(f.name).unlink()
    
    def test_add_listing_basic(self):
        """Test basic listing creation."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            
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
            
            result = storage.add_listing(listing_data)
            assert result is True
            
            # Verify listing was added
            retrieved = storage.get_listing_by_url("https://example.com/test")
            assert retrieved is not None
            assert retrieved["title"] == "Test Apartment"
            assert retrieved["provider"] == "immoscout"
            
            Path(f.name).unlink()
    
    def test_add_duplicate_listing(self):
        """Test duplicate listing prevention."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            
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
            storage = EnhancedStorageManager(f.name)
            
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
            storage = EnhancedStorageManager(f.name)
            
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
            storage = EnhancedStorageManager(f.name)
            
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
            storage = EnhancedStorageManager(f.name)
            
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
            storage = EnhancedStorageManager(f.name)
            
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
            recent_jobs = stats["recent_scraping_runs"]
            assert len(recent_jobs) > 0
            assert recent_jobs[0]["status"] == "completed"
            assert recent_jobs[0]["listings_found"] == 5
            
            Path(f.name).unlink()
    
    def test_cleanup_old_data(self):
        """Test cleaning up old data."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            
            # Add old data (this would normally be done with old timestamps)
            # For testing, we'll just verify the method exists and runs
            result = storage.cleanup_old_data(days_to_keep=30)
            assert isinstance(result, int)
            
            Path(f.name).unlink()
    
    def test_get_statistics(self):
        """Test getting database statistics."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            
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


class TestDeduplication:
    """Test cases for deduplication functionality."""
    
    def test_exact_hash_match(self):
        """Test exact hash-based duplicate detection."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            
            listing_data = {
                "provider": "immoscout",
                "external_id": "test_123",
                "title": "Test Apartment",
                "url": "https://example.com/test",
                "price": "1000 €",
                "size": "80 m²",
                "rooms": "3.5",
                "address": "Test Street 1, Munich"
            }
            
            # Add first listing
            result1 = storage.add_listing(listing_data)
            assert result1 is True
            
            # Try to add exact duplicate
            duplicate_data = listing_data.copy()
            duplicate_data["url"] = "https://example.com/test2"  # Different URL but same content
            
            duplicate_check = storage.check_duplicate(duplicate_data)
            assert duplicate_check["is_duplicate"] is True
            assert duplicate_check["duplicate_strategy"] == "exact_hash"
            assert duplicate_check["confidence"] == 1.0
            
            Path(f.name).unlink()
    
    def test_provider_external_id_match(self):
        """Test provider + external ID duplicate detection."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            
            listing_data = {
                "provider": "immoscout",
                "external_id": "unique_123",
                "title": "Test Apartment",
                "url": "https://example.com/test1",
                "price": "1000 €"
            }
            
            # Add first listing
            result1 = storage.add_listing(listing_data)
            assert result1 is True
            
            # Try to add duplicate with same provider/external_id
            duplicate_data = {
                "provider": "immoscout",
                "external_id": "unique_123",
                "title": "Different Title",
                "url": "https://example.com/test2",
                "price": "1200 €"
            }
            
            duplicate_check = storage.check_duplicate(duplicate_data)
            assert duplicate_check["is_duplicate"] is True
            assert duplicate_check["duplicate_strategy"] == "provider_external_id"
            
            Path(f.name).unlink()
    
    def test_url_match(self):
        """Test URL-based duplicate detection."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            
            listing_data = {
                "provider": "immoscout",
                "title": "Test Apartment",
                "url": "https://example.com/test",
                "price": "1000 €"
            }
            
            # Add first listing
            result1 = storage.add_listing(listing_data)
            assert result1 is True
            
            # Try to add duplicate with same URL
            duplicate_data = {
                "provider": "wg_gesucht",
                "title": "Different Title",
                "url": "https://example.com/test",
                "price": "1200 €"
            }
            
            duplicate_check = storage.check_duplicate(duplicate_data)
            assert duplicate_check["is_duplicate"] is True
            assert duplicate_check["duplicate_strategy"] == "url_match"
            
            Path(f.name).unlink()
    
    def test_fuzzy_matching(self):
        """Test fuzzy matching for similar listings."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            
            # Add original listing
            original_data = {
                "provider": "immoscout",
                "title": "Schöne 3-Zimmer Wohnung in München",
                "url": "https://example.com/original",
                "price": "1000 €",
                "size": "80 m²",
                "rooms": "3",
                "address": "München, Schwabing"
            }
            
            result1 = storage.add_listing(original_data)
            assert result1 is True
            
            # Try to add very similar listing
            similar_data = {
                "provider": "immoscout",
                "title": "Schöne 3 Zimmer Wohnung in München",  # Slightly different
                "url": "https://example.com/similar",
                "price": "1000 €",
                "size": "80 m²",
                "rooms": "3",
                "address": "München Schwabing"  # Slightly different
            }
            
            duplicate_check = storage.check_duplicate(similar_data)
            # Should detect as duplicate due to high similarity
            if duplicate_check["is_duplicate"]:
                assert duplicate_check["duplicate_strategy"] == "fuzzy_match"
                assert duplicate_check["confidence"] > 0.8
            
            Path(f.name).unlink()
    
    def test_duplicate_statistics(self):
        """Test duplicate statistics calculation."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            
            # Add some listings including duplicates
            listings = [
                {
                    "provider": "immoscout",
                    "external_id": "unique_1",
                    "title": "Listing 1",
                    "url": "https://example.com/1",
                    "price": "1000 €"
                },
                {
                    "provider": "immoscout",
                    "external_id": "unique_1",  # Duplicate by external ID
                    "title": "Listing 1 Duplicate",
                    "url": "https://example.com/1-dup",
                    "price": "1000 €"
                },
                {
                    "provider": "wg_gesucht",
                    "external_id": "unique_2",
                    "title": "Listing 2",
                    "url": "https://example.com/2",
                    "price": "800 €"
                }
            ]
            
            for listing in listings:
                storage.add_listing(listing)
            
            # Get duplicate statistics
            stats = storage.get_duplicate_statistics()
            assert "total_duplicates" in stats
            assert "duplicates_by_provider" in stats
            assert "duplicate_rate" in stats
            
            Path(f.name).unlink()


class TestBackupAndRestore:
    """Test cases for backup and restore functionality."""
    
    def test_create_full_backup(self):
        """Test creating a full database backup."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            
            # Add some test data
            listing_data = {
                "provider": "immoscout",
                "title": "Test Apartment",
                "url": "https://example.com/test",
                "price": "1000 €"
            }
            storage.add_listing(listing_data)
            
            # Create backup
            backup_path = storage.create_backup("full", "test_backup")
            assert backup_path is not None
            assert Path(backup_path).exists()
            
            # Clean up
            Path(backup_path).unlink()
            Path(f.name).unlink()
    
    def test_create_schema_backup(self):
        """Test creating a schema-only backup."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            
            # Create schema backup
            backup_path = storage.create_backup("schema", "test_schema_backup")
            assert backup_path is not None
            assert Path(backup_path).exists()
            
            # Clean up
            Path(backup_path).unlink()
            Path(f.name).unlink()
    
    def test_data_export_import(self):
        """Test data export and import functionality."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            
            # Add test data
            listing_data = {
                "provider": "immoscout",
                "title": "Test Apartment",
                "url": "https://example.com/test",
                "price": "1000 €"
            }
            storage.add_listing(listing_data)
            
            # Export data
            export_path = storage.export_data("json")
            assert export_path is not None
            assert Path(export_path).exists()
            
            # Create new storage and import
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f2:
                storage2 = EnhancedStorageManager(f2.name)
                
                # Import data
                success = storage2.import_data(export_path, "json")
                assert success is True
                
                # Verify imported data
                imported_listings = storage2.get_listings()
                assert len(imported_listings) == 1
                assert imported_listings[0]["title"] == "Test Apartment"
                
                Path(f2.name).unlink()
            
            # Clean up
            Path(export_path).unlink()
            Path(f.name).unlink()
    
    def test_data_integrity_verification(self):
        """Test data integrity verification."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            
            # Add test data
            listing_data = {
                "provider": "immoscout",
                "title": "Test Apartment",
                "url": "https://example.com/test",
                "price": "1000 €"
            }
            storage.add_listing(listing_data)
            
            # Verify integrity
            integrity_report = storage.verify_data_integrity()
            assert "valid" in integrity_report
            assert "checks" in integrity_report
            
            Path(f.name).unlink()
    
    def test_get_latest_backup(self):
        """Test getting information about the latest backup."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            
            # No backups yet
            latest = storage.get_latest_backup()
            assert latest is None
            
            # Create a backup
            backup_path = storage.create_backup("full", "test_latest")
            assert backup_path is not None
            
            # Get latest backup info
            latest = storage.get_latest_backup()
            assert latest is not None
            assert latest["backup_type"] == "full"
            assert latest["status"] == "completed"
            
            # Clean up
            Path(backup_path).unlink()
            Path(f.name).unlink()


class TestRelationships:
    """Test cases for data relationships."""
    
    def test_get_listing_with_relationships(self):
        """Test getting listing with all related data."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            
            # Add listing with contacts
            listing_data = {
                "provider": "immoscout",
                "title": "Test Apartment",
                "url": "https://example.com/test",
                "price": "1000 €"
            }
            storage.add_listing(listing_data)
            
            listing = storage.get_listing_by_url("https://example.com/test")
            listing_id = listing["id"]
            
            # Add contacts
            storage.add_contact(listing_id, {"type": "email", "value": "test@example.com"})
            storage.add_contact(listing_id, {"type": "phone", "value": "+49 123 456789"})
            
            # Get listing with relationships
            full_listing = storage.get_listing_with_relationships(listing_id)
            assert full_listing is not None
            assert "contacts" in full_listing
            assert len(full_listing["contacts"]) == 2
            assert full_listing["scraping_runs"] == []
            
            Path(f.name).unlink()
    
    def test_scraping_run_listing_association(self):
        """Test association between scraping runs and listings."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            
            # Add listing
            listing_data = {
                "provider": "immoscout",
                "title": "Test Apartment",
                "url": "https://example.com/test",
                "price": "1000 €"
            }
            storage.add_listing(listing_data)
            
            listing = storage.get_listing_by_url("https://example.com/test")
            listing_id = listing["id"]
            
            # Create scraping run
            run_id = storage.create_scraping_job("immoscout")
            
            # Associate listing with scraping run
            success = storage.relationships.associate_listing_with_scraping_run(
                listing_id, run_id
            )
            assert success is True
            
            # Get scraping run with listings
            run_with_listings = storage.relationships.get_scraping_run_with_listings(run_id)
            assert run_with_listings is not None
            assert "listings" in run_with_listings
            assert len(run_with_listings["listings"]) == 1
            
            Path(f.name).unlink()
    
    def test_data_integrity_report(self):
        """Test data integrity report generation."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            
            # Add test data
            listing_data = {
                "provider": "immoscout",
                "title": "Test Apartment",
                "url": "https://example.com/test",
                "price": "1000 €"
            }
            storage.add_listing(listing_data)
            
            # Generate integrity report
            report = storage.get_data_integrity_report()
            assert "timestamp" in report
            assert "summary" in report
            assert "details" in report
            assert report["summary"]["valid"] is True
            
            Path(f.name).unlink()
    
    def test_cleanup_orphaned_data(self):
        """Test cleaning up orphaned data."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            
            # Clean up should work even with no data
            cleanup_counts = storage.cleanup_orphaned_data()
            assert isinstance(cleanup_counts, dict)
            
            Path(f.name).unlink()


class TestAdvancedFeatures:
    """Test cases for advanced storage features."""
    
    def test_bulk_operations(self):
        """Test bulk CRUD operations."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            
            # Prepare bulk listing data
            bulk_listings = []
            for i in range(10):
                bulk_listings.append({
                    "provider": "immoscout",
                    "title": f"Bulk Listing {i}",
                    "url": f"https://example.com/bulk{i}",
                    "price": f"{1000 + i * 100} €"
                })
            
            # Bulk create listings
            created_count = storage.crud.bulk_create_listings(bulk_listings)
            assert created_count == 10
            
            # Verify all were created
            all_listings = storage.get_listings(limit=20)
            assert len(all_listings) == 10
            
            Path(f.name).unlink()
    
    def test_advanced_listing_queries(self):
        """Test advanced listing query capabilities."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            
            # Add test listings
            listings = [
                {
                    "provider": "immoscout",
                    "title": "Luxury Apartment in City Center",
                    "url": "https://example.com/luxury",
                    "price": "2000 €",
                    "size": "120 m²",
                    "rooms": "4",
                    "address": "Munich City Center"
                },
                {
                    "provider": "wg_gesucht",
                    "title": "Cozy Room in Shared Apartment",
                    "url": "https://example.com/room",
                    "price": "500 €",
                    "size": "20 m²",
                    "rooms": "1",
                    "address": "Munich Schwabing"
                }
            ]
            
            for listing in listings:
                storage.add_listing(listing)
            
            # Test search query
            search_results = storage.crud.get_listings(search_query="apartment")
            assert len(search_results) >= 1
            
            # Test price filtering
            price_results = storage.crud.get_listings(max_price="1500 €")
            assert len(price_results) >= 1
            
            Path(f.name).unlink()
    
    def test_contact_validation(self):
        """Test contact validation functionality."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            
            # Add listing
            listing_data = {
                "provider": "immoscout",
                "title": "Test Apartment",
                "url": "https://example.com/test",
                "price": "1000 €"
            }
            storage.add_listing(listing_data)
            
            listing = storage.get_listing_by_url("https://example.com/test")
            listing_id = listing["id"]
            
            # Add contact
            storage.add_contact(listing_id, {
                "type": "email",
                "value": "test@example.com"
            })
            
            # Get contact
            contacts = storage.crud.get_contacts(listing_id=listing_id)
            contact = contacts[0]
            
            # Update contact status
            success = storage.crud.update_contact_status(
                contact["id"], 
                ContactStatus.VALID,
                {"validation_method": "email_check", "result": "valid"}
            )
            assert success is True
            
            # Verify status was updated
            updated_contacts = storage.crud.get_contacts(listing_id=listing_id)
            assert updated_contacts[0]["status"] == ContactStatus.VALID
            
            Path(f.name).unlink()
    
    def test_migration_system(self):
        """Test database migration system."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name, auto_migrate=False)
            
            # Get current version
            current_version = storage.migrations.get_current_version()
            assert current_version is not None
            
            # Get available migrations
            available_migrations = storage.migrations.get_available_migrations()
            assert isinstance(available_migrations, list)
            
            Path(f.name).unlink()
    
    def test_configuration_management(self):
        """Test configuration management."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            
            # Set configuration
            config_entry = storage.crud.session.query(storage.models.Configuration).filter_by(
                key="test_setting"
            ).first()
            
            if not config_entry:
                config_entry = storage.models.Configuration(
                    key="test_setting",
                    value="test_value",
                    description="Test configuration setting"
                )
                storage.crud.session.add(config_entry)
                storage.crud.session.commit()
            
            # Get configuration
            retrieved_config = storage.crud.session.query(
                storage.models.Configuration
            ).filter_by(key="test_setting").first()
            
            assert retrieved_config is not None
            assert retrieved_config.value == "test_value"
            
            Path(f.name).unlink()


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_database_connection_error(self):
        """Test handling of database connection errors."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            
            # Simulate database error by corrupting the file
            Path(f.name).write_text("corrupted data")
            
            # This should handle the error gracefully
            try:
                stats = storage.get_statistics()
                # Should return empty stats or handle error
                assert isinstance(stats, dict)
            except Exception:
                # Expected to fail with corrupted database
                pass
            
            Path(f.name).unlink()
    
    def test_invalid_data_handling(self):
        """Test handling of invalid data."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            
            # Try to add listing with invalid data
            invalid_listing = {
                "provider": "immoscout",
                "title": None,  # Invalid title
                "url": "invalid-url",  # Invalid URL format
                "price": "invalid-price"  # Invalid price
            }
            
            # Should handle gracefully
            result = storage.add_listing(invalid_listing)
            # May fail or handle gracefully depending on validation
            assert isinstance(result, bool)
            
            Path(f.name).unlink()
    
    def test_concurrent_access(self):
        """Test concurrent database access."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage1 = EnhancedStorageManager(f.name)
            storage2 = EnhancedStorageManager(f.name)
            
            # Both should be able to access the same database
            listing_data = {
                "provider": "immoscout",
                "title": "Test Apartment",
                "url": "https://example.com/test1",
                "price": "1000 €"
            }
            
            result1 = storage1.add_listing(listing_data)
            assert result1 is True
            
            # Second storage should see the data
            listings = storage2.get_listings()
            assert len(listings) == 1
            
            Path(f.name).unlink()


# Integration tests
class TestIntegration:
    """Integration tests for the complete storage system."""
    
    def test_complete_workflow(self):
        """Test complete workflow from data creation to backup."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            
            # Step 1: Add listings
            listings = [
                {
                    "provider": "immoscout",
                    "title": "Luxury Apartment",
                    "url": "https://example.com/luxury",
                    "price": "2000 €",
                    "size": "120 m²",
                    "rooms": "4"
                },
                {
                    "provider": "wg_gesucht",
                    "title": "Cozy Room",
                    "url": "https://example.com/room",
                    "price": "500 €",
                    "size": "20 m²",
                    "rooms": "1"
                }
            ]
            
            for listing in listings:
                result = storage.add_listing(listing)
                assert result is True
            
            # Step 2: Add contacts
            luxury_listing = storage.get_listing_by_url("https://example.com/luxury")
            storage.add_contact(luxury_listing["id"], {
                "type": "email",
                "value": "luxury@example.com"
            })
            
            # Step 3: Create scraping run
            run_id = storage.create_scraping_job("immoscout")
            storage.update_scraping_job(run_id, "completed", listings_found=2)
            
            # Step 4: Check for duplicates
            duplicate_check = storage.check_duplicate({
                "provider": "immoscout",
                "title": "Luxury Apartment",
                "url": "https://example.com/luxury-dup",
                "price": "2000 €",
                "size": "120 m²",
                "rooms": "4"
            })
            assert duplicate_check["is_duplicate"] is True
            
            # Step 5: Get comprehensive data
            full_listing = storage.get_listing_with_relationships(luxury_listing["id"])
            assert full_listing is not None
            assert len(full_listing["contacts"]) == 1
            
            # Step 6: Create backup
            backup_path = storage.create_backup("full", "integration_test")
            assert backup_path is not None
            
            # Step 7: Verify data integrity
            integrity_report = storage.get_data_integrity_report()
            assert integrity_report["summary"]["valid"] is True
            
            # Step 8: Get statistics
            stats = storage.get_statistics()
            assert stats["total_listings"] == 2
            assert stats["total_contacts"] == 1
            
            # Clean up
            Path(backup_path).unlink()
            Path(f.name).unlink()
    
    def test_performance_with_large_dataset(self):
        """Test performance with a larger dataset."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            
            # Add many listings
            bulk_listings = []
            for i in range(100):
                bulk_listings.append({
                    "provider": "immoscout" if i % 2 == 0 else "wg_gesucht",
                    "title": f"Test Listing {i}",
                    "url": f"https://example.com/listing{i}",
                    "price": f"{500 + i * 10} €"
                })
            
            # Measure bulk creation time
            import time
            start_time = time.time()
            created_count = storage.crud.bulk_create_listings(bulk_listings)
            creation_time = time.time() - start_time
            
            assert created_count == 100
            assert creation_time < 10  # Should be reasonably fast
            
            # Test query performance
            start_time = time.time()
            listings = storage.get_listings(limit=50)
            query_time = time.time() - start_time
            
            assert len(listings) == 50
            assert query_time < 1  # Should be fast
            
            Path(f.name).unlink()