"""
Migration to version 2.1.0 - ScrapingRun Schema Enhancement.

This migration adds the missing 'created_at' column to the scraping_runs table
to fix database schema issues and ensure compatibility with the API.
"""

from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import text

logger = logging.getLogger(__name__)


def upgrade(session) -> None:
    """
    Apply migration to version 2.1.0.
    
    Args:
        session: Database session
    """
    try:
        logger.info("Applying migration to version 2.1.0 - ScrapingRun Schema Enhancement")
        
        # Add created_at column to scraping_runs table
        session.execute(text("""
            ALTER TABLE scraping_runs ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        """))
        
        # Create index for created_at column
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_scraping_runs_created_at ON scraping_runs(created_at)
        """))
        
        # Update existing records to set created_at = started_at
        session.execute(text("""
            UPDATE scraping_runs SET created_at = started_at WHERE created_at IS NULL
        """))
        
        # Record migration
        session.execute(
            text("INSERT INTO schema_migrations (version, applied_at) VALUES ('2.1.0', :applied_at)"),
            {"applied_at": datetime.utcnow()}
        )
        
        logger.info("Successfully applied migration to version 2.1.0")
        
    except Exception as e:
        logger.error(f"Error applying migration to version 2.1.0: {e}")
        raise


def downgrade(session) -> None:
    """
    Rollback migration from version 2.1.0.
    
    Args:
        session: Database session
    """
    try:
        logger.info("Rolling back migration from version 2.1.0")
        
        # Drop created_at column from scraping_runs table
        try:
            session.execute(text("ALTER TABLE scraping_runs DROP COLUMN created_at"))
        except Exception as e:
            logger.warning(f"Could not drop column created_at: {e}")
        
        # Drop created_at index
        try:
            session.execute(text("DROP INDEX IF EXISTS idx_scraping_runs_created_at"))
        except Exception as e:
            logger.warning(f"Could not drop index idx_scraping_runs_created_at: {e}")
        
        # Remove migration record
        session.execute(text("DELETE FROM schema_migrations WHERE version = '2.1.0'"))
        
        logger.info("Successfully rolled back migration from version 2.1.0")
        
    except Exception as e:
        logger.error(f"Error rolling back migration from version 2.1.0: {e}")
        raise