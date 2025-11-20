"""
Enhanced storage manager for MWA Core.

Provides comprehensive data persistence capabilities with SQLAlchemy ORM,
advanced deduplication, migration support, and backup functionality.
"""

from __future__ import annotations

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

from .models import (
    Listing, Contact, ScrapingRun, ListingStatus, ContactType, ContactStatus, 
    JobStatus, DeduplicationStatus
)
from .schema import DatabaseSchema, get_default_database_url, SchemaMigration
from .operations import CRUDOperations
from .deduplication import DeduplicationEngine
from .backup import BackupManager
from .relationships import RelationshipManager
from .migrations import MigrationManager

logger = logging.getLogger(__name__)


class EnhancedStorageManager:
    """
    Enhanced storage manager for MWA Core with comprehensive features.
    
    Provides:
    - SQLAlchemy ORM with proper relationships
    - Advanced CRUD operations
    - Deduplication with SHA-256 and fuzzy matching
    - Migration system
    - Backup and restore
    - Data integrity management
    """
    
    def __init__(self, database_path: Optional[str] = None, auto_migrate: bool = True):
        """
        Initialize the enhanced storage manager.
        
        Args:
            database_path: Path to SQLite database file. If None, uses config setting.
            auto_migrate: Whether to automatically run migrations on startup.
        """
        self.database_url = get_default_database_url()
        if database_path:
            # Override with custom path
            self.database_url = f"sqlite:///{Path(database_path).resolve()}"
        
        # Initialize schema
        self.schema = DatabaseSchema(self.database_url)
        
        # Initialize components
        self.crud = CRUDOperations(self.schema)
        self.deduplication = DeduplicationEngine(self.crud)
        self.backup = BackupManager(self.schema)
        self.relationships = RelationshipManager(self.schema)
        self.migrations = MigrationManager(self.schema)
        
        # Ensure database is set up
        self._initialize_database(auto_migrate)
    
    def _initialize_database(self, auto_migrate: bool) -> None:
        """Initialize database with schema and migrations."""
        try:
            # Create all tables
            self.schema.create_all_tables()
            
            # Run migrations if enabled
            if auto_migrate:
                self.migrations.initialize_database()
            
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    # Legacy compatibility methods
    def add_listing(self, listing_data: Dict[str, Any]) -> bool:
        """
        Add a new listing (legacy compatibility).
        
        Args:
            listing_data: Dictionary containing listing information
            
        Returns:
            True if listing was added, False if it already exists or is duplicate
        """
        try:
            # Check for duplicates first
            duplicate_check = self.deduplication.check_duplicate(listing_data)
            if duplicate_check["is_duplicate"]:
                logger.info(f"Listing rejected as duplicate: {duplicate_check['reason']}")
                
                # Mark as duplicate if we have the original ID
                if duplicate_check["duplicate_of_id"]:
                    self.deduplication.mark_as_duplicate(
                        duplicate_check.get("new_listing_id", 0),
                        duplicate_check["duplicate_of_id"],
                        duplicate_check["confidence"],
                        duplicate_check["duplicate_strategy"]
                    )
                return False
            
            # Create listing using CRUD operations
            listing = self.crud.create_listing(listing_data)
            if listing:
                # Store the ID for duplicate marking if needed
                if duplicate_check["is_duplicate"] and duplicate_check["duplicate_of_id"]:
                    self.deduplication.mark_as_duplicate(
                        listing.id,
                        duplicate_check["duplicate_of_id"],
                        duplicate_check["confidence"],
                        duplicate_check["duplicate_strategy"]
                    )
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error adding listing: {e}")
            return False
    
    def get_listing_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get a listing by its URL (legacy compatibility).
        
        Args:
            url: Listing URL
            
        Returns:
            Listing data dictionary or None if not found
        """
        try:
            return self.crud.get_listing_by_url(url)
        except Exception as e:
            logger.error(f"Error getting listing by URL {url}: {e}")
            return None
    
    def get_listings(self, limit: int = 100, offset: int = 0,
                    provider: Optional[str] = None,
                    status: str = "active") -> List[Dict[str, Any]]:
        """
        Get listings with optional filtering (legacy compatibility).
        
        Args:
            limit: Maximum number of listings to return
            offset: Number of listings to skip
            provider: Filter by provider name
            status: Filter by status
            
        Returns:
            List of listing dictionaries
        """
        try:
            # Convert status string to enum
            status_enum = ListingStatus(status) if status else None
            
            return self.crud.get_listings(
                limit=limit,
                offset=offset,
                provider=provider,
                status=status_enum
            )
            
        except Exception as e:
            logger.error(f"Error getting listings: {e}")
            return []
    
    def update_listing_status(self, url: str, status: str) -> bool:
        """
        Update the status of a listing (legacy compatibility).
        
        Args:
            url: Listing URL
            status: New status
            
        Returns:
            True if updated successfully
        """
        try:
            # Get listing by URL first
            listing = self.crud.get_listing_by_url(url)
            if not listing:
                return False
            
            # Convert status string to enum
            status_enum = ListingStatus(status)
            
            return self.crud.update_listing(listing.id, {"status": status_enum})
            
        except Exception as e:
            logger.error(f"Error updating listing status: {e}")
            return False
    
    def add_contact(self, listing_id: int, contact_data: Dict[str, Any]) -> bool:
        """
        Add a contact to a listing (legacy compatibility).
        
        Args:
            listing_id: ID of the listing
            contact_data: Contact information
            
        Returns:
            True if contact was added
        """
        try:
            contact = self.crud.create_contact(listing_id, contact_data)
            return contact is not None
        except Exception as e:
            logger.error(f"Error adding contact: {e}")
            return False
    
    def get_contacts(self, listing_id: Optional[int] = None,
                    contact_type: Optional[str] = None,
                    limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get contacts with optional filtering (legacy compatibility).
        
        Args:
            listing_id: Filter by listing ID
            contact_type: Filter by contact type
            limit: Maximum number of contacts to return (optional)
            
        Returns:
            List of contact dictionaries
        """
        try:
            # Convert contact type string to enum
            contact_type_enum = ContactType(contact_type) if contact_type else None
            
            contacts = self.crud.get_contacts(
                listing_id=listing_id,
                contact_type=contact_type_enum,
                limit=limit
            )
            
            return [contact.to_dict() for contact in contacts]
            
        except Exception as e:
            logger.error(f"Error getting contacts: {e}")
            return []
    
    def create_scraping_job(self, provider: str) -> int:
        """
        Create a new scraping job record (legacy compatibility).
        
        Args:
            provider: Provider name
            
        Returns:
            Job ID
        """
        try:
            scraping_run = self.crud.create_scraping_run(provider, "manual", "legacy")
            return scraping_run.id if scraping_run else 0
        except Exception as e:
            logger.error(f"Error creating scraping job: {e}")
            return 0
    
    def update_scraping_job(self, job_id: int, status: str, 
                           listings_found: int = 0, errors: Optional[List[str]] = None,
                           performance_metrics: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update scraping job status and results (legacy compatibility).
        
        Args:
            job_id: Job ID
            status: New status
            listings_found: Number of listings found
            errors: List of error messages
            performance_metrics: Performance metrics
            
        Returns:
            True if updated successfully
        """
        try:
            # Convert status string to enum
            status_enum = JobStatus(status)
            
            update_data = {
                "status": status_enum,
                "listings_found": listings_found,
                "errors": json.dumps(errors or []),
                "performance_metrics": json.dumps(performance_metrics or {})
            }
            
            return self.crud.update_scraping_run(job_id, update_data)
            
        except Exception as e:
            logger.error(f"Error updating scraping job: {e}")
            return False
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> int:
        """
        Clean up old data based on retention policy (legacy compatibility).
        
        Args:
            days_to_keep: Number of days to keep data
            
        Returns:
            Number of records deleted
        """
        try:
            cleanup_counts = self.crud.cleanup_old_data(days_to_keep)
            return sum(cleanup_counts.values())
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return 0
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get database statistics (legacy compatibility).
        
        Returns:
            Dictionary with statistics
        """
        try:
            return self.crud.get_statistics()
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    # Enhanced methods for new functionality
    def check_duplicate(self, listing_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if a listing is a duplicate using advanced deduplication.
        
        Args:
            listing_data: Listing data to check
            
        Returns:
            Dictionary with duplicate information
        """
        return self.deduplication.check_duplicate(listing_data)
    
    def get_duplicate_statistics(self) -> Dict[str, Any]:
        """
        Get deduplication statistics.
        
        Returns:
            Dictionary with duplicate statistics
        """
        return self.deduplication.get_duplicate_statistics()
    
    def cleanup_duplicates(self, merge_data: bool = True) -> Dict[str, int]:
        """
        Clean up duplicate listings.
        
        Args:
            merge_data: Whether to merge data from duplicates
            
        Returns:
            Dictionary with cleanup counts
        """
        return self.deduplication.cleanup_duplicates(merge_data)
    
    def create_backup(self, backup_type: str = "full", 
                     backup_name: Optional[str] = None) -> Optional[str]:
        """
        Create a database backup.
        
        Args:
            backup_type: Type of backup ('full', 'schema', 'incremental')
            backup_name: Optional backup name
            
        Returns:
            Path to backup file or None if failed
        """
        try:
            if backup_type == "full":
                return self.backup.create_full_backup(backup_name)
            elif backup_type == "schema":
                return self.backup.create_schema_backup(backup_name)
            elif backup_type == "incremental":
                # Need to get last backup date for incremental
                last_backup = self.get_latest_backup()
                if last_backup:
                    last_date = datetime.fromisoformat(last_backup["created_at"])
                    return self.backup.create_incremental_backup(last_date, backup_name)
                else:
                    logger.warning("No previous backup found for incremental backup")
                    return None
            else:
                logger.error(f"Unsupported backup type: {backup_type}")
                return None
                
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return None
    
    def restore_backup(self, backup_path: str, verify_checksum: bool = True) -> bool:
        """
        Restore database from backup.
        
        Args:
            backup_path: Path to backup file
            verify_checksum: Whether to verify checksum before restore
            
        Returns:
            True if restore successful
        """
        return self.backup.restore_backup(backup_path, verify_checksum)
    
    def get_latest_backup(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the latest backup.
        
        Returns:
            Dictionary with backup information or None
        """
        try:
            with self.schema.get_session() as session:
                from .models import BackupMetadata
                
                latest_backup = session.query(BackupMetadata).filter_by(
                    status="completed"
                ).order_by(BackupMetadata.created_at.desc()).first()
                
                return latest_backup.to_dict() if latest_backup else None
                
        except Exception as e:
            logger.error(f"Error getting latest backup: {e}")
            return None
    
    def verify_data_integrity(self) -> Dict[str, Any]:
        """
        Verify data integrity and consistency.
        
        Returns:
            Dictionary with integrity check results
        """
        return self.backup.verify_data_integrity()
    
    def get_listing_with_relationships(self, listing_id: int) -> Optional[Dict[str, Any]]:
        """
        Get listing with all related data.
        
        Args:
            listing_id: Listing ID
            
        Returns:
            Dictionary with listing and all related data
        """
        return self.relationships.get_listing_with_relationships(listing_id)
    
    def get_data_integrity_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive data integrity report.
        
        Returns:
            Dictionary with integrity report
        """
        return self.relationships.get_data_integrity_report()
    
    def cleanup_orphaned_data(self) -> Dict[str, int]:
        """
        Clean up orphaned data.
        
        Returns:
            Dictionary with cleanup counts
        """
        return self.relationships.cleanup_orphaned_data()
    
    def export_data(self, format_type: str = "json", 
                   filters: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Export data in various formats.
        
        Args:
            format_type: Export format ('json', 'csv', 'xml')
            filters: Optional filters for data export
            
        Returns:
            Path to exported file or None if failed
        """
        return self.backup.export_data(format_type, filters)
    
    def import_data(self, import_path: str, format_type: str = "json") -> bool:
        """
        Import data from various formats.
        
        Args:
            import_path: Path to import file
            format_type: Import format
            
        Returns:
            True if import successful
        """
        return self.backup.import_data(import_path, format_type)
    
    def migrate_from_legacy(self, legacy_manager) -> bool:
        """
        Migrate data from legacy storage manager.
        
        Args:
            legacy_manager: Legacy StorageManager instance
            
        Returns:
            True if migration successful
        """
        try:
            migration = SchemaMigration(self.schema)
            
            # Create backup before migration
            backup_path = migration.create_migration_backup()
            if backup_path:
                logger.info(f"Created pre-migration backup: {backup_path}")
            
            # Perform migration
            return migration.migrate_from_legacy_schema(legacy_manager)
            
        except Exception as e:
            logger.error(f"Error migrating from legacy storage: {e}")
            return False
    
    def get_database_info(self) -> Dict[str, Any]:
        """
        Get comprehensive database information.
        
        Returns:
            Dictionary with database information
        """
        return self.schema.get_database_info()
    
    def validate_schema(self) -> Dict[str, Any]:
        """
        Validate the current database schema.
        
        Returns:
            Dictionary with validation results
        """
        return self.schema.validate_schema()
    
    def get_session(self):
        """
        Get a database session for custom operations.
        
        Returns:
            SQLAlchemy session
        """
        return self.schema.get_session()


# Global storage manager instance with enhanced features
_storage_manager = None


def get_storage_manager() -> EnhancedStorageManager:
    """Get or create the global enhanced storage manager instance."""
    global _storage_manager
    if _storage_manager is None:
        _storage_manager = EnhancedStorageManager()
    return _storage_manager


def reset_storage_manager() -> None:
    """Reset the global storage manager instance."""
    global _storage_manager
    _storage_manager = None


# Legacy compatibility - create alias for backward compatibility
StorageManager = EnhancedStorageManager