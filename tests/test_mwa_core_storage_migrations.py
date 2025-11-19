"""
Comprehensive tests for MWA Core storage migration system.

Tests schema migrations, version management, and data migration from legacy systems.
"""

import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from mwa_core.storage import (
    EnhancedStorageManager, MigrationManager, Migration,
    DatabaseSchema, create_schema, get_default_database_url
)


class TestMigrationManager:
    """Test cases for MigrationManager."""
    
    def test_initialization(self):
        """Test migration manager initialization."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name, auto_migrate=False)
            migration_manager = storage.migrations
            
            assert migration_manager is not None
            assert migration_manager.schema is not None
            assert migration_manager.migrations_dir.exists()
            
            Path(f.name).unlink()
    
    def test_get_current_version(self):
        """Test getting current database version."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name, auto_migrate=False)
            migration_manager = storage.migrations
            
            # Initially should return default version
            current_version = migration_manager.get_current_version()
            assert current_version == "0.0.0"  # Default for new database
            
            Path(f.name).unlink()
    
    def test_get_available_migrations(self):
        """Test getting available migrations."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name, auto_migrate=False)
            migration_manager = storage.migrations
            
            available_migrations = migration_manager.get_available_migrations()
            assert isinstance(available_migrations, list)
            # Should find at least the 1.0.0 migration
            assert len(available_migrations) >= 1
            
            Path(f.name).unlink()
    
    def test_version_comparison(self):
        """Test version comparison logic."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name, auto_migrate=False)
            migration_manager = storage.migrations
            
            # Test version comparisons
            assert migration_manager._version_compare("1.0.0", "1.0.0") == 0
            assert migration_manager._version_compare("1.0.0", "2.0.0") == -1
            assert migration_manager._version_compare("2.0.0", "1.0.0") == 1
            assert migration_manager._version_compare("1.0.0", "1.1.0") == -1
            assert migration_manager._version_compare("1.1.0", "1.0.0") == 1
            
            Path(f.name).unlink()
    
    def test_create_migrations_table(self):
        """Test creating migrations tracking table."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name, auto_migrate=False)
            migration_manager = storage.migrations
            
            # Create migrations table
            success = migration_manager.create_migrations_table()
            assert success is True
            
            # Verify table exists
            db_info = storage.get_database_info()
            assert "schema_migrations" in db_info["tables"]
            
            Path(f.name).unlink()
    
    def test_migrate_to_version(self):
        """Test migrating to specific version."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name, auto_migrate=False)
            migration_manager = storage.migrations
            
            # Create migrations table first
            migration_manager.create_migrations_table()
            
            # Migrate to version 1.0.0
            success = migration_manager.migrate_to_version("1.0.0")
            assert success is True
            
            # Verify migration was applied
            current_version = migration_manager.get_current_version()
            assert current_version == "1.0.0"
            
            Path(f.name).unlink()
    
    def test_initialize_database(self):
        """Test database initialization with latest schema."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name, auto_migrate=False)
            migration_manager = storage.migrations
            
            # Initialize database
            success = migration_manager.initialize_database()
            assert success is True
            
            # Verify database is at latest version
            current_version = migration_manager.get_current_version()
            available_migrations = migration_manager.get_available_migrations()
            latest_version = available_migrations[-1] if available_migrations else "0.0.0"
            
            assert current_version == latest_version
            
            Path(f.name).unlink()


class TestMigrationBase:
    """Test cases for Migration base class."""
    
    def test_migration_interface(self):
        """Test that Migration base class defines required interface."""
        
        class TestMigration(Migration):
            def upgrade(self, session):
                pass
            
            def downgrade(self, session):
                pass
        
        migration = TestMigration()
        assert hasattr(migration, 'upgrade')
        assert hasattr(migration, 'downgrade')
    
    def test_migration_not_implemented(self):
        """Test that base Migration class raises NotImplementedError."""
        migration = Migration()
        
        with pytest.raises(NotImplementedError):
            migration.upgrade(None)
        
        with pytest.raises(NotImplementedError):
            migration.downgrade(None)


class TestSchemaMigration:
    """Test cases for schema migration functionality."""
    
    def test_migration_1_0_0_upgrade(self):
        """Test upgrading to version 1.0.0."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name, auto_migrate=False)
            
            # Apply migration manually
            from mwa_core.storage.migrations.migration_1_0_0 import upgrade
            
            with storage.schema.get_session() as session:
                upgrade(session)
            
            # Verify new tables were created
            db_info = storage.get_database_info()
            expected_tables = [
                "listings", "contacts", "scraping_runs", "listing_scraping_runs",
                "contact_validations", "job_store", "configuration", "backup_metadata",
                "schema_migrations"
            ]
            
            for table in expected_tables:
                assert table in db_info["tables"]
            
            Path(f.name).unlink()
    
    def test_migration_1_0_0_downgrade(self):
        """Test downgrading from version 1.0.0."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name, auto_migrate=False)
            
            # First upgrade
            from mwa_core.storage.migrations.migration_1_0_0 import upgrade
            with storage.schema.get_session() as session:
                upgrade(session)
            
            # Then downgrade
            from mwa_core.storage.migrations.migration_1_0_0 import downgrade
            with storage.schema.get_session() as session:
                downgrade(session)
            
            # Verify rollback (should have basic tables)
            db_info = storage.get_database_info()
            basic_tables = ["listings", "contacts", "scraping_jobs", "configuration"]
            
            for table in basic_tables:
                assert table in db_info["tables"]
            
            Path(f.name).unlink()
    
    def test_legacy_data_migration(self):
        """Test migration of data from legacy schema."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            # Create legacy storage first
            from mwa_core.storage.manager import StorageManager as LegacyStorageManager
            
            legacy_storage = LegacyStorageManager(f.name)
            
            # Add legacy data
            legacy_listing = {
                "provider": "immoscout",
                "external_id": "legacy_123",
                "title": "Legacy Listing",
                "url": "https://example.com/legacy",
                "price": "1000 €",
                "size": "80 m²",
                "rooms": "3.5",
                "address": "Legacy Street 1",
                "description": "Legacy apartment",
                "images": ["legacy1.jpg"],
                "contacts": [{"type": "email", "value": "legacy@example.com"}],
                "raw_data": {"legacy": "data"}
            }
            
            legacy_storage.add_listing(legacy_listing)
            
            # Add contact
            legacy_listing_retrieved = legacy_storage.get_listing_by_url("https://example.com/legacy")
            legacy_storage.add_contact(legacy_listing_retrieved["id"], {
                "type": "phone",
                "value": "+49 123 456789"
            })
            
            # Create new storage and migrate
            new_storage = EnhancedStorageManager(f.name, auto_migrate=False)
            migration = SchemaMigration(new_storage.schema)
            
            # Migrate from legacy
            success = migration.migrate_from_legacy_schema(legacy_storage)
            assert success is True
            
            # Verify migrated data
            migrated_listing = new_storage.get_listing_by_url("https://example.com/legacy")
            assert migrated_listing is not None
            assert migrated_listing["title"] == "Legacy Listing"
            assert migrated_listing["hash_signature"] is not None
            assert migrated_listing["deduplication_status"] == DeduplicationStatus.ORIGINAL.value
            
            # Verify contacts were migrated
            migrated_contacts = new_storage.get_contacts(listing_id=migrated_listing["id"])
            assert len(migrated_contacts) >= 1
            
            Path(f.name).unlink()


class TestMigrationErrorHandling:
    """Test error handling in migration system."""
    
    def test_migration_with_invalid_version(self):
        """Test migration with invalid version string."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name, auto_migrate=False)
            migration_manager = storage.migrations
            
            # Create migrations table first
            migration_manager.create_migrations_table()
            
            # Try to migrate to invalid version
            success = migration_manager.migrate_to_version("invalid.version")
            assert success is False
            
            Path(f.name).unlink()
    
    def test_migration_with_missing_file(self):
        """Test migration with missing migration file."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name, auto_migrate=False)
            migration_manager = storage.migrations
            
            # Create migrations table first
            migration_manager.create_migrations_table()
            
            # Try to load non-existent migration
            migration_module = migration_manager._load_migration("9.9.9")
            assert migration_module is None
            
            Path(f.name).unlink()
    
    def test_migration_rollback_on_error(self):
        """Test that migrations rollback on error."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name, auto_migrate=False)
            
            # Create a broken migration
            class BrokenMigration(Migration):
                def upgrade(self, session):
                    raise Exception("Migration failed")
                
                def downgrade(self, session):
                    pass
            
            # Try to apply broken migration
            with patch.object(storage.migrations, '_load_migration') as mock_load:
                mock_load.return_value = BrokenMigration()
                
                success = storage.migrations.migrate_to_version("broken.1.0")
                assert success is False
            
            Path(f.name).unlink()


class TestDatabaseSchema:
    """Test cases for DatabaseSchema functionality."""
    
    def test_schema_creation(self):
        """Test database schema creation."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            database_url = f"sqlite:///{Path(f.name).resolve()}"
            schema = create_schema(database_url)
            
            # Create all tables
            schema.create_all_tables()
            
            # Verify schema validation
            validation = schema.validate_schema()
            assert validation["valid"] is True
            
            Path(f.name).unlink()
    
    def test_schema_validation_with_missing_tables(self):
        """Test schema validation when tables are missing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            database_url = f"sqlite:///{Path(f.name).resolve()}"
            schema = create_schema(database_url)
            
            # Create only some tables
            from mwa_core.storage.models import Base, Listing
            Base.metadata.create_all(bind=schema.engine, tables=[Listing.__table__])
            
            # Validate schema
            validation = schema.validate_schema()
            assert validation["valid"] is False
            assert len(validation["missing_tables"]) > 0
            
            Path(f.name).unlink()
    
    def test_database_info(self):
        """Test getting database information."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            database_url = f"sqlite:///{Path(f.name).resolve()}"
            schema = create_schema(database_url)
            
            # Create some tables
            schema.create_all_tables()
            
            # Get database info
            db_info = schema.get_database_info()
            assert "database_url" in db_info
            assert "tables" in db_info
            assert "total_tables" in db_info
            assert db_info["total_tables"] > 0
            
            Path(f.name).unlink()
    
    def test_get_default_database_url(self):
        """Test getting default database URL from configuration."""
        url = get_default_database_url()
        assert url.startswith("sqlite:///")
        assert "mwa_core.db" in url


class TestMigrationIntegration:
    """Integration tests for migration system."""
    
    def test_complete_migration_workflow(self):
        """Test complete migration workflow."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            # Start with fresh database
            storage = EnhancedStorageManager(f.name, auto_migrate=False)
            
            # Initialize database (should apply all migrations)
            success = storage.migrations.initialize_database()
            assert success is True
            
            # Verify database is functional
            listing_data = {
                "provider": "immoscout",
                "title": "Test Listing",
                "url": "https://example.com/test",
                "price": "1000 €"
            }
            
            result = storage.add_listing(listing_data)
            assert result is True
            
            # Verify enhanced features work
            stats = storage.get_statistics()
            assert stats["total_listings"] == 1
            
            # Verify deduplication works
            duplicate_check = storage.check_duplicate(listing_data)
            assert duplicate_check["is_duplicate"] is True
            
            Path(f.name).unlink()
    
    def test_migration_with_existing_data(self):
        """Test migration when database already has data."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            # Create storage and add some data
            storage = EnhancedStorageManager(f.name, auto_migrate=True)
            
            # Add listings
            for i in range(5):
                listing_data = {
                    "provider": "immoscout",
                    "title": f"Test Listing {i}",
                    "url": f"https://example.com/test{i}",
                    "price": f"{1000 + i * 100} €"
                }
                storage.add_listing(listing_data)
            
            # Add contacts
            listing = storage.get_listing_by_url("https://example.com/test0")
            storage.add_contact(listing["id"], {
                "type": "email",
                "value": f"contact{i}@example.com"
            })
            
            # Force re-initialization (should handle existing data)
            success = storage.migrations.initialize_database()
            assert success is True
            
            # Verify data is still there
            stats = storage.get_statistics()
            assert stats["total_listings"] == 5
            assert stats["total_contacts"] >= 1
            
            Path(f.name).unlink()
    
    def test_migration_rollback_and_reapply(self):
        """Test rolling back and reapplying migrations."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name, auto_migrate=False)
            
            # Create migrations table
            storage.migrations.create_migrations_table()
            
            # Apply migration
            success1 = storage.migrations.migrate_to_version("1.0.0")
            assert success1 is True
            
            # Rollback migration
            success2 = storage.migrations.migrate_to_version("0.0.0")
            assert success2 is True
            
            # Reapply migration
            success3 = storage.migrations.migrate_to_version("1.0.0")
            assert success3 is True
            
            # Verify final state
            current_version = storage.migrations.get_current_version()
            assert current_version == "1.0.0"
            
            Path(f.name).unlink()


# Performance tests
class TestMigrationPerformance:
    """Performance tests for migration system."""
    
    def test_large_dataset_migration(self):
        """Test migration performance with large dataset."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            # Create storage with lots of data
            storage = EnhancedStorageManager(f.name, auto_migrate=False)
            
            # Add many listings
            bulk_listings = []
            for i in range(100):
                bulk_listings.append({
                    "provider": "immoscout" if i % 2 == 0 else "wg_gesucht",
                    "title": f"Test Listing {i}",
                    "url": f"https://example.com/test{i}",
                    "price": f"{500 + i * 10} €"
                })
            
            # Use CRUD to bulk create
            created_count = storage.crud.bulk_create_listings(bulk_listings)
            assert created_count == 100
            
            # Measure migration time
            import time
            start_time = time.time()
            
            success = storage.migrations.initialize_database()
            
            migration_time = time.time() - start_time
            
            assert success is True
            assert migration_time < 30  # Should complete within 30 seconds
            
            Path(f.name).unlink()