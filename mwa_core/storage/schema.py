"""
Database schema definitions and utilities for MWA Core storage system.

Provides schema creation, validation, and migration utilities.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

from sqlalchemy import create_engine, event, inspect
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker, Session

from .models import Base, Listing, Contact, ScrapingRun, ListingScrapingRun
from .models import ContactValidation, JobStore, Configuration, BackupMetadata

logger = logging.getLogger(__name__)


class DatabaseSchema:
    """Manages database schema creation and validation."""
    
    def __init__(self, database_url: str):
        """
        Initialize the database schema manager.
        
        Args:
            database_url: Database connection URL
        """
        self.database_url = database_url
        self.engine = create_engine(
            database_url,
            echo=False,  # Set to True for SQL debugging
            pool_pre_ping=True,  # Verify connections before use
            pool_recycle=3600,  # Recycle connections after 1 hour
        )
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)
        
        # Enable foreign key constraints for SQLite
        if database_url.startswith("sqlite"):
            self._enable_sqlite_foreign_keys()
    
    def _enable_sqlite_foreign_keys(self) -> None:
        """Enable foreign key constraints for SQLite databases."""
        @event.listens_for(Engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            if self.database_url.startswith("sqlite"):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA foreign_keys=ON")
                cursor.close()
    
    def create_all_tables(self) -> None:
        """Create all database tables."""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("All database tables created successfully")
        except SQLAlchemyError as e:
            logger.error(f"Error creating database tables: {e}")
            raise
    
    def drop_all_tables(self) -> None:
        """Drop all database tables (use with caution)."""
        try:
            Base.metadata.drop_all(bind=self.engine)
            logger.warning("All database tables dropped")
        except SQLAlchemyError as e:
            logger.error(f"Error dropping database tables: {e}")
            raise
    
    def validate_schema(self) -> Dict[str, Any]:
        """
        Validate the current database schema.
        
        Returns:
            Dictionary with validation results
        """
        try:
            inspector = inspect(self.engine)
            validation_results = {
                "valid": True,
                "missing_tables": [],
                "missing_columns": {},
                "missing_indexes": {},
                "errors": []
            }
            
            # Check for required tables
            required_tables = [
                "listings", "contacts", "scraping_runs", "listing_scraping_runs",
                "contact_validations", "job_store", "configuration", "backup_metadata"
            ]
            
            existing_tables = inspector.get_table_names()
            
            for table_name in required_tables:
                if table_name not in existing_tables:
                    validation_results["missing_tables"].append(table_name)
                    validation_results["valid"] = False
                else:
                    # Check for required columns in each table
                    table_columns = [col["name"] for col in inspector.get_columns(table_name)]
                    expected_columns = self._get_expected_columns(table_name)
                    
                    missing_cols = [col for col in expected_columns if col not in table_columns]
                    if missing_cols:
                        validation_results["missing_columns"][table_name] = missing_cols
                        validation_results["valid"] = False
                    
                    # Check for expected indexes
                    table_indexes = [idx["name"] for idx in inspector.get_indexes(table_name)]
                    expected_indexes = self._get_expected_indexes(table_name)
                    
                    missing_indexes = [idx for idx in expected_indexes if idx not in table_indexes]
                    if missing_indexes:
                        validation_results["missing_indexes"][table_name] = missing_indexes
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Schema validation error: {e}")
            return {
                "valid": False,
                "errors": [str(e)]
            }
    
    def _get_expected_columns(self, table_name: str) -> List[str]:
        """Get expected columns for a given table."""
        expected_columns = {
            "listings": [
                "id", "provider", "external_id", "title", "url", "price", "size", 
                "rooms", "address", "description", "images", "contacts", "scraped_at", 
                "updated_at", "status", "raw_data", "hash_signature", "deduplication_status", 
                "duplicate_of_id", "first_seen_at", "last_seen_at", "view_count"
            ],
            "contacts": [
                "id", "listing_id", "type", "value", "confidence", "source", "status", 
                "validated_at", "created_at", "updated_at", "hash_signature", 
                "validation_metadata", "usage_count", "last_used_at"
            ],
            "scraping_runs": [
                "id", "provider", "status", "started_at", "completed_at", "listings_found", 
                "listings_processed", "errors", "performance_metrics", "configuration_snapshot", 
                "trigger_type", "triggered_by", "duration_seconds", "memory_usage_mb", 
                "cpu_usage_percent", "network_requests", "data_size_mb"
            ],
            "listing_scraping_runs": [
                "id", "listing_id", "scraping_run_id", "discovered_at"
            ],
            "contact_validations": [
                "id", "contact_id", "validation_method", "validation_result", 
                "confidence_score", "validation_metadata", "validated_at", "validator_version"
            ],
            "job_store": [
                "id", "job_id", "job_name", "job_type", "job_data", "schedule_expression", 
                "next_run_time", "last_run_time", "run_count", "success_count", 
                "failure_count", "enabled", "created_at", "updated_at"
            ],
            "configuration": [
                "id", "key", "value", "description", "data_type", "updated_at", "updated_by"
            ],
            "backup_metadata": [
                "id", "backup_type", "backup_path", "backup_size_mb", "created_at", 
                "completed_at", "status", "checksum", "metadata_info", "created_by"
            ]
        }
        return expected_columns.get(table_name, [])
    
    def _get_expected_indexes(self, table_name: str) -> List[str]:
        """Get expected indexes for a given table."""
        expected_indexes = {
            "listings": [
                "idx_listings_provider", "idx_listings_status", "idx_listings_scraped_at",
                "idx_listings_provider_status", "idx_listings_hash_signature"
            ],
            "contacts": [
                "idx_contacts_listing_id", "idx_contacts_type", "idx_contacts_status",
                "idx_contacts_listing_type", "idx_contacts_created_at"
            ],
            "scraping_runs": [
                "idx_scraping_runs_provider", "idx_scraping_runs_status", 
                "idx_scraping_runs_started_at", "idx_scraping_runs_provider_status"
            ]
        }
        return expected_indexes.get(table_name, [])
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get database information.
        
        Returns:
            Dictionary with database information
        """
        try:
            inspector = inspect(self.engine)
            
            info = {
                "database_url": self.database_url,
                "tables": {},
                "total_tables": len(inspector.get_table_names()),
                "engine_name": self.engine.name,
            }
            
            for table_name in inspector.get_table_names():
                columns = inspector.get_columns(table_name)
                indexes = inspector.get_indexes(table_name)
                
                info["tables"][table_name] = {
                    "columns": len(columns),
                    "indexes": len(indexes),
                    "column_names": [col["name"] for col in columns],
                    "index_names": [idx["name"] for idx in indexes],
                }
            
            return info
            
        except Exception as e:
            logger.error(f"Error getting database info: {e}")
            return {"error": str(e)}
    
    def get_session(self) -> Session:
        """Get a database session."""
        return self.SessionLocal()


def create_schema(database_url: str) -> DatabaseSchema:
    """
    Create a database schema manager.
    
    Args:
        database_url: Database connection URL
        
    Returns:
        DatabaseSchema instance
    """
    return DatabaseSchema(database_url)


def get_default_database_url(config_path: Optional[str] = None) -> str:
    """
    Get the default database URL from configuration.
    
    Args:
        config_path: Optional path to configuration file
        
    Returns:
        Database connection URL
    """
    from mwa_core.config import get_settings
    
    settings = get_settings()
    database_path = settings.storage.database_path
    
    # Ensure directory exists
    Path(database_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Convert to absolute path
    database_path = str(Path(database_path).resolve())
    
    # Create SQLite URL
    return f"sqlite:///{database_path}"


# Schema migration utilities
class SchemaMigration:
    """Handles database schema migrations."""
    
    def __init__(self, database_schema: DatabaseSchema):
        """
        Initialize schema migration manager.
        
        Args:
            database_schema: DatabaseSchema instance
        """
        self.schema = database_schema
    
    def migrate_from_legacy_schema(self, legacy_manager) -> bool:
        """
        Migrate data from legacy SQLite schema to new SQLAlchemy schema.
        
        Args:
            legacy_manager: Legacy StorageManager instance
            
        Returns:
            True if migration successful
        """
        try:
            logger.info("Starting schema migration from legacy to new format")
            
            # Get legacy data
            legacy_listings = legacy_manager.get_listings(limit=10000)
            legacy_contacts = legacy_manager.get_contacts()
            
            # Get database statistics
            legacy_stats = legacy_manager.get_statistics()
            
            with self.schema.get_session() as session:
                # Migrate listings
                for legacy_listing in legacy_listings:
                    # Check if listing already exists
                    existing = session.query(Listing).filter_by(
                        url=legacy_listing["url"]
                    ).first()
                    
                    if existing:
                        logger.debug(f"Listing already exists: {legacy_listing['url']}")
                        continue
                    
                    # Create new listing
                    listing = Listing(
                        provider=legacy_listing["provider"],
                        external_id=legacy_listing.get("external_id"),
                        title=legacy_listing["title"],
                        url=legacy_listing["url"],
                        price=legacy_listing.get("price"),
                        size=legacy_listing.get("size"),
                        rooms=legacy_listing.get("rooms"),
                        address=legacy_listing.get("address"),
                        description=legacy_listing.get("description"),
                        images=json.dumps(legacy_listing.get("images", [])),
                        contacts=json.dumps(legacy_listing.get("contacts", [])),
                        scraped_at=legacy_listing.get("scraped_at"),
                        updated_at=legacy_listing.get("updated_at"),
                        status=ListingStatus(legacy_listing.get("status", "active")),
                        raw_data=json.dumps(legacy_listing.get("raw_data", {})),
                    )
                    
                    # Generate hash signature
                    listing.update_hash_signature()
                    
                    session.add(listing)
                    session.flush()  # Get the ID
                    
                    # Migrate contacts for this listing
                    listing_contacts = [
                        c for c in legacy_contacts 
                        if c.get("listing_id") == legacy_listing.get("id")
                    ]
                    
                    for legacy_contact in listing_contacts:
                        contact = Contact(
                            listing_id=listing.id,
                            type=ContactType(legacy_contact["type"]),
                            value=legacy_contact["value"],
                            confidence=legacy_contact.get("confidence"),
                            source=legacy_contact.get("source"),
                            status=ContactStatus.VALID if legacy_contact.get("validated") else ContactStatus.UNVALIDATED,
                            validated_at=legacy_listing.get("updated_at") if legacy_contact.get("validated") else None,
                        )
                        
                        # Generate hash signature
                        contact.update_hash_signature()
                        
                        session.add(contact)
                
                session.commit()
                logger.info(f"Successfully migrated {len(legacy_listings)} listings and {len(legacy_contacts)} contacts")
                
                return True
                
        except Exception as e:
            logger.error(f"Schema migration failed: {e}")
            session.rollback()
            return False
    
    def create_migration_backup(self) -> Optional[str]:
        """
        Create a backup before migration.
        
        Returns:
            Path to backup file or None if failed
        """
        try:
            from .backup import BackupManager
            
            backup_manager = BackupManager(self.schema)
            backup_path = backup_manager.create_full_backup("pre_migration")
            
            logger.info(f"Migration backup created: {backup_path}")
            return backup_path
            
        except Exception as e:
            logger.error(f"Failed to create migration backup: {e}")
            return None