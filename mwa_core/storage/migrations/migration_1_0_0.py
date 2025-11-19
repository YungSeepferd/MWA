"""
Migration from legacy schema to version 1.0.0.

This migration creates the enhanced database schema with all new tables and relationships.
"""

from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import text

logger = logging.getLogger(__name__)


def upgrade(session) -> None:
    """
    Apply migration to version 1.0.0.
    
    Args:
        session: Database session
    """
    try:
        logger.info("Applying migration to version 1.0.0")
        
        # Create enhanced listings table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider VARCHAR(50) NOT NULL,
                external_id VARCHAR(100),
                title VARCHAR(500) NOT NULL,
                url VARCHAR(1000) NOT NULL UNIQUE,
                price VARCHAR(50),
                size VARCHAR(50),
                rooms VARCHAR(20),
                address VARCHAR(500),
                description TEXT,
                images TEXT,
                contacts TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT 'active',
                raw_data TEXT,
                hash_signature VARCHAR(64) UNIQUE,
                deduplication_status VARCHAR(20) DEFAULT 'original',
                duplicate_of_id INTEGER,
                first_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                view_count INTEGER DEFAULT 1,
                FOREIGN KEY (duplicate_of_id) REFERENCES listings(id)
            )
        """))
        
        # Create enhanced contacts table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                listing_id INTEGER NOT NULL,
                type VARCHAR(20) NOT NULL,
                value VARCHAR(500) NOT NULL,
                confidence DECIMAL(3,2),
                source VARCHAR(50),
                status VARCHAR(20) DEFAULT 'unvalidated',
                validated_at TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                hash_signature VARCHAR(64),
                validation_metadata TEXT,
                usage_count INTEGER DEFAULT 0,
                last_used_at TIMESTAMP,
                FOREIGN KEY (listing_id) REFERENCES listings(id) ON DELETE CASCADE,
                UNIQUE(listing_id, type, value)
            )
        """))
        
        # Create scraping_runs table (replaces scraping_jobs)
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS scraping_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider VARCHAR(50) NOT NULL,
                status VARCHAR(20) NOT NULL DEFAULT 'pending',
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                listings_found INTEGER DEFAULT 0,
                listings_processed INTEGER DEFAULT 0,
                errors TEXT,
                performance_metrics TEXT,
                configuration_snapshot TEXT,
                trigger_type VARCHAR(50),
                triggered_by VARCHAR(100),
                duration_seconds DECIMAL(10,2),
                memory_usage_mb DECIMAL(10,2),
                cpu_usage_percent DECIMAL(5,2),
                network_requests INTEGER DEFAULT 0,
                data_size_mb DECIMAL(10,2)
            )
        """))
        
        # Create association table for listings and scraping runs
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS listing_scraping_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                listing_id INTEGER NOT NULL,
                scraping_run_id INTEGER NOT NULL,
                discovered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (listing_id) REFERENCES listings(id) ON DELETE CASCADE,
                FOREIGN KEY (scraping_run_id) REFERENCES scraping_runs(id) ON DELETE CASCADE,
                UNIQUE(listing_id, scraping_run_id)
            )
        """))
        
        # Create contact_validations table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS contact_validations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER NOT NULL,
                validation_method VARCHAR(50) NOT NULL,
                validation_result VARCHAR(20) NOT NULL,
                confidence_score DECIMAL(3,2),
                validation_metadata TEXT,
                validated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                validator_version VARCHAR(20),
                FOREIGN KEY (contact_id) REFERENCES contacts(id) ON DELETE CASCADE
            )
        """))
        
        # Create job_store table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS job_store (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id VARCHAR(100) NOT NULL UNIQUE,
                job_name VARCHAR(200) NOT NULL,
                job_type VARCHAR(50) NOT NULL,
                job_data TEXT NOT NULL,
                schedule_expression VARCHAR(100),
                next_run_time TIMESTAMP,
                last_run_time TIMESTAMP,
                run_count INTEGER DEFAULT 0,
                success_count INTEGER DEFAULT 0,
                failure_count INTEGER DEFAULT 0,
                enabled BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create enhanced configuration table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS configuration (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                key VARCHAR(100) NOT NULL UNIQUE,
                value TEXT NOT NULL,
                description VARCHAR(500),
                data_type VARCHAR(20) DEFAULT 'string',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_by VARCHAR(100)
            )
        """))
        
        # Create backup_metadata table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS backup_metadata (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                backup_type VARCHAR(50) NOT NULL,
                backup_path VARCHAR(1000) NOT NULL,
                backup_size_mb DECIMAL(10,2),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                status VARCHAR(20) DEFAULT 'running',
                checksum VARCHAR(64),
                metadata_info TEXT,
                created_by VARCHAR(100)
            )
        """))
        
        # Create schema_migrations table
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(20) PRIMARY KEY,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create indexes for performance
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_listings_provider ON listings(provider)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_listings_status ON listings(status)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_listings_scraped_at ON listings(scraped_at)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_listings_hash_signature ON listings(hash_signature)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_listings_provider_status ON listings(provider, status)"))
        
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_contacts_listing_id ON contacts(listing_id)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_contacts_type ON contacts(type)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_contacts_status ON contacts(status)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_contacts_listing_type ON contacts(listing_id, type)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_contacts_created_at ON contacts(created_at)"))
        
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_scraping_runs_provider ON scraping_runs(provider)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_scraping_runs_status ON scraping_runs(status)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_scraping_runs_started_at ON scraping_runs(started_at)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_scraping_runs_provider_status ON scraping_runs(provider, status)"))
        
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_listing_scraping_runs_listing ON listing_scraping_runs(listing_id)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_listing_scraping_runs_scraping_run ON listing_scraping_runs(scraping_run_id)"))
        
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_contact_validations_contact ON contact_validations(contact_id)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_contact_validations_validated_at ON contact_validations(validated_at)"))
        
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_job_store_next_run_time ON job_store(next_run_time)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_job_store_job_type_enabled ON job_store(job_type, enabled)"))
        
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_configuration_key ON configuration(key)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_backup_metadata_created_at ON backup_metadata(created_at)"))
        
        # Migrate data from old tables if they exist
        _migrate_legacy_data(session)
        
        # Record migration
        session.execute(
            text(f"INSERT INTO schema_migrations (version, applied_at) VALUES ('1.0.0', :applied_at)"),
            {"applied_at": datetime.utcnow()}
        )
        
        logger.info("Successfully applied migration to version 1.0.0")
        
    except Exception as e:
        logger.error(f"Error applying migration to version 1.0.0: {e}")
        raise


def downgrade(session) -> None:
    """
    Rollback migration from version 1.0.0.
    
    Args:
        session: Database session
    """
    try:
        logger.info("Rolling back migration from version 1.0.0")
        
        # Drop tables in reverse order (respect foreign key constraints)
        tables_to_drop = [
            "backup_metadata",
            "schema_migrations",
            "configuration",
            "job_store",
            "contact_validations",
            "listing_scraping_runs",
            "scraping_runs",
            "contacts",
            "listings"
        ]
        
        for table in tables_to_drop:
            session.execute(text(f"DROP TABLE IF EXISTS {table}"))
        
        # Recreate original tables (simplified version for rollback)
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider VARCHAR(50) NOT NULL,
                external_id VARCHAR(100),
                title TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                price TEXT,
                size TEXT,
                rooms TEXT,
                address TEXT,
                description TEXT,
                images TEXT,
                contacts TEXT,
                scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(20) DEFAULT 'active',
                raw_data TEXT,
                UNIQUE(provider, external_id)
            )
        """))
        
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                listing_id INTEGER,
                type VARCHAR(20) NOT NULL,
                value TEXT NOT NULL,
                confidence DECIMAL(3,2),
                source VARCHAR(50),
                validated BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (listing_id) REFERENCES listings(id),
                UNIQUE(listing_id, type, value)
            )
        """))
        
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS scraping_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                provider VARCHAR(50) NOT NULL,
                status VARCHAR(20) NOT NULL,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP,
                listings_found INTEGER DEFAULT 0,
                errors TEXT,
                performance_metrics TEXT
            )
        """))
        
        session.execute(text("""
            CREATE TABLE IF NOT EXISTS configuration (
                key VARCHAR(100) PRIMARY KEY,
                value TEXT NOT NULL,
                description TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))
        
        # Create basic indexes
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_listings_provider ON listings(provider)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_listings_status ON listings(status)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_listings_scraped_at ON listings(scraped_at)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_contacts_listing_id ON contacts(listing_id)"))
        session.execute(text("CREATE INDEX IF NOT EXISTS idx_contacts_type ON contacts(type)"))
        
        logger.info("Successfully rolled back migration from version 1.0.0")
        
    except Exception as e:
        logger.error(f"Error rolling back migration from version 1.0.0: {e}")
        raise


def _migrate_legacy_data(session, self=None) -> None:
    """
    Migrate data from legacy tables to new schema.
    
    Args:
        session: Database session
    """
    try:
        # Check if legacy tables exist
        result = session.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='scraping_jobs'"
        ).fetchone()
        
        if result:
            logger.info("Migrating data from legacy tables")
            
            # Migrate listings data
            legacy_listings = session.execute(
                "SELECT * FROM listings WHERE 1=1"
            ).fetchall()
            
            for listing in legacy_listings:
                # Update with new fields (if needed)
                session.execute(
                    """
                    UPDATE listings 
                    SET hash_signature = ?, deduplication_status = ?, first_seen_at = ?, 
                        last_seen_at = ?, view_count = ?
                    WHERE id = ?
                    """,
                    (
                        "",  # Will be generated by model
                        "original",
                        listing.scraped_at,
                        listing.scraped_at,
                        1,
                        listing.id
                    )
                )
            
            # Migrate contacts data
            legacy_contacts = session.execute(
                "SELECT * FROM contacts WHERE 1=1"
            ).fetchall()
            
            for contact in legacy_contacts:
                # Update with new fields
                session.execute(
                    """
                    UPDATE contacts 
                    SET status = ?, hash_signature = ?, validation_metadata = ?, 
                        usage_count = ?, last_used_at = ?
                    WHERE id = ?
                    """,
                    (
                        "valid" if contact.validated else "unvalidated",
                        "",  # Will be generated by model
                        None,
                        0,
                        None,
                        contact.id
                    )
                )
            
            # Migrate scraping_jobs to scraping_runs
            legacy_jobs = session.execute(
                "SELECT * FROM scraping_jobs WHERE 1=1"
            ).fetchall()
            
            for job in legacy_jobs:
                session.execute(
                    """
                    INSERT INTO scraping_runs (
                        provider, status, started_at, completed_at, listings_found,
                        errors, performance_metrics, trigger_type, triggered_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        job.provider,
                        job.status,
                        job.started_at,
                        job.completed_at,
                        job.listings_found,
                        job.errors,
                        job.performance_metrics,
                        "manual",  # Default trigger type
                        "legacy_migration"
                    )
                )
            
            logger.info("Legacy data migration completed")
            
    except Exception as e:
        logger.error(f"Error migrating legacy data: {e}")
        # Don't fail the migration if legacy data migration fails
        pass