"""
Migration to version 2.0.0 - Market Intelligence Contact Enhancement.

This migration adds market intelligence fields to the contacts table
for enhanced contact management and market analysis capabilities.
"""

from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy import text

logger = logging.getLogger(__name__)


def upgrade(session) -> None:
    """
    Apply migration to version 2.0.0.
    
    Args:
        session: Database session
    """
    try:
        logger.info("Applying migration to version 2.0.0 - Market Intelligence Enhancement")
        
        # Add market intelligence columns to contacts table
        session.execute(text("""
            ALTER TABLE contacts ADD COLUMN position VARCHAR(100)
        """))
        
        session.execute(text("""
            ALTER TABLE contacts ADD COLUMN company_name VARCHAR(200)
        """))
        
        session.execute(text("""
            ALTER TABLE contacts ADD COLUMN agency_type VARCHAR(50)
        """))
        
        session.execute(text("""
            ALTER TABLE contacts ADD COLUMN market_areas TEXT
        """))  # JSON array of market areas
        
        session.execute(text("""
            ALTER TABLE contacts ADD COLUMN outreach_history TEXT
        """))  # JSON array of outreach history entries
        
        session.execute(text("""
            ALTER TABLE contacts ADD COLUMN preferred_contact_method VARCHAR(20)
        """))
        
        session.execute(text("""
            ALTER TABLE contacts ADD COLUMN last_contacted TIMESTAMP
        """))
        
        session.execute(text("""
            ALTER TABLE contacts ADD COLUMN confidence_score DECIMAL(3,2) DEFAULT 0.0
        """))
        
        session.execute(text("""
            ALTER TABLE contacts ADD COLUMN quality_score DECIMAL(3,2) DEFAULT 0.0
        """))
        
        session.execute(text("""
            ALTER TABLE contacts ADD COLUMN is_active BOOLEAN DEFAULT TRUE
        """))
        
        session.execute(text("""
            ALTER TABLE contacts ADD COLUMN is_blacklisted BOOLEAN DEFAULT FALSE
        """))
        
        session.execute(text("""
            ALTER TABLE contacts ADD COLUMN blacklist_reason TEXT
        """))
        
        session.execute(text("""
            ALTER TABLE contacts ADD COLUMN scraped_from_url VARCHAR(1000)
        """))
        
        session.execute(text("""
            ALTER TABLE contacts ADD COLUMN source_provider VARCHAR(50)
        """))
        
        session.execute(text("""
            ALTER TABLE contacts ADD COLUMN extraction_method VARCHAR(50)
        """))
        
        session.execute(text("""
            ALTER TABLE contacts ADD COLUMN extraction_confidence DECIMAL(3,2)
        """))
        
        session.execute(text("""
            ALTER TABLE contacts ADD COLUMN lead_source VARCHAR(50)
        """))
        
        session.execute(text("""
            ALTER TABLE contacts ADD COLUMN tags TEXT
        """))  # JSON array of tags
        
        session.execute(text("""
            ALTER TABLE contacts ADD COLUMN notes TEXT
        """))
        
        # Create indexes for market intelligence queries
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_contacts_agency_type ON contacts(agency_type)
        """))
        
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_contacts_is_active ON contacts(is_active)
        """))
        
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_contacts_is_blacklisted ON contacts(is_blacklisted)
        """))
        
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_contacts_last_contacted ON contacts(last_contacted)
        """))
        
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_contacts_confidence_score ON contacts(confidence_score)
        """))
        
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_contacts_quality_score ON contacts(quality_score)
        """))
        
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_contacts_source_provider ON contacts(source_provider)
        """))
        
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_contacts_lead_source ON contacts(lead_source)
        """))
        
        # Create a GIN-like index for market_areas array field (using JSON functions)
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_contacts_market_areas 
            ON contacts(json_extract(market_areas, '$'))
        """))
        
        # Create a GIN-like index for tags array field
        session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_contacts_tags 
            ON contacts(json_extract(tags, '$'))
        """))
        
        # Record migration
        session.execute(
            text(f"INSERT INTO schema_migrations (version, applied_at) VALUES ('2.0.0', :applied_at)"),
            {"applied_at": datetime.utcnow()}
        )
        
        logger.info("Successfully applied migration to version 2.0.0")
        
    except Exception as e:
        logger.error(f"Error applying migration to version 2.0.0: {e}")
        raise


def downgrade(session) -> None:
    """
    Rollback migration from version 2.0.0.
    
    Args:
        session: Database session
    """
    try:
        logger.info("Rolling back migration from version 2.0.0")
        
        # Drop market intelligence columns
        columns_to_drop = [
            "position",
            "company_name",
            "agency_type",
            "market_areas",
            "outreach_history",
            "preferred_contact_method",
            "last_contacted",
            "confidence_score",
            "quality_score",
            "is_active",
            "is_blacklisted",
            "blacklist_reason",
            "scraped_from_url",
            "source_provider",
            "extraction_method",
            "extraction_confidence",
            "lead_source",
            "tags",
            "notes"
        ]
        
        for column in columns_to_drop:
            try:
                session.execute(text(f"ALTER TABLE contacts DROP COLUMN {column}"))
            except Exception as e:
                logger.warning(f"Could not drop column {column}: {e}")
        
        # Drop market intelligence indexes
        indexes_to_drop = [
            "idx_contacts_agency_type",
            "idx_contacts_is_active",
            "idx_contacts_is_blacklisted",
            "idx_contacts_last_contacted",
            "idx_contacts_confidence_score",
            "idx_contacts_quality_score",
            "idx_contacts_source_provider",
            "idx_contacts_lead_source",
            "idx_contacts_market_areas",
            "idx_contacts_tags"
        ]
        
        for index in indexes_to_drop:
            try:
                session.execute(text(f"DROP INDEX IF EXISTS {index}"))
            except Exception as e:
                logger.warning(f"Could not drop index {index}: {e}")
        
        # Remove migration record
        session.execute(text("DELETE FROM schema_migrations WHERE version = '2.0.0'"))
        
        logger.info("Successfully rolled back migration from version 2.0.0")
        
    except Exception as e:
        logger.error(f"Error rolling back migration from version 2.0.0: {e}")
        raise