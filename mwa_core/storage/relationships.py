"""
Data relationships and associations for MWA Core storage system.

Defines relationships between different entities and provides utilities for
managing complex data associations.
"""

from __future__ import annotations

import logging
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timedelta

from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session, joinedload, selectinload

from .models import (
    Listing, Contact, ScrapingRun, ListingScrapingRun, ContactValidation,
    JobStore, Configuration, BackupMetadata, ListingStatus, ContactType,
    ContactStatus, JobStatus, DeduplicationStatus
)

logger = logging.getLogger(__name__)


class RelationshipManager:
    """Manages complex data relationships and associations."""
    
    def __init__(self, database_schema):
        """
        Initialize relationship manager.
        
        Args:
            database_schema: DatabaseSchema instance
        """
        self.schema = database_schema
    
    def get_listing_with_relationships(self, listing_id: int) -> Optional[Dict[str, Any]]:
        """
        Get listing with all related data.
        
        Args:
            listing_id: Listing ID
            
        Returns:
            Dictionary with listing and all related data
        """
        try:
            with self.schema.get_session() as session:
                listing = session.query(Listing).options(
                    selectinload(Listing.contact_entries),
                    selectinload(Listing.scraping_runs),
                    selectinload(Listing.duplicate_listings)
                ).filter_by(id=listing_id).first()
                
                if not listing:
                    return None
                
                # Build comprehensive listing data
                listing_data = listing.to_dict()
                
                # Add contacts with validation history
                listing_data["contacts"] = []
                for contact in listing.contact_entries:
                    contact_data = contact.to_dict()
                    contact_data["validation_history"] = [
                        validation.to_dict() 
                        for validation in contact.validation_history
                    ]
                    listing_data["contacts"].append(contact_data)
                
                # Add scraping runs
                listing_data["scraping_runs"] = [
                    run.to_dict() for run in listing.scraping_runs
                ]
                
                # Add duplicate listings
                listing_data["duplicate_listings"] = [
                    dup.to_dict() for dup in listing.duplicate_listings
                    if dup.id != listing_id
                ]
                
                return listing_data
                
        except Exception as e:
            logger.error(f"Error getting listing with relationships {listing_id}: {e}")
            return None
    
    def get_scraping_run_with_listings(self, run_id: int) -> Optional[Dict[str, Any]]:
        """
        Get scraping run with all associated listings.
        
        Args:
            run_id: Scraping run ID
            
        Returns:
            Dictionary with scraping run and associated listings
        """
        try:
            with self.schema.get_session() as session:
                scraping_run = session.query(ScrapingRun).options(
                    selectinload(ScrapingRun.listings)
                ).filter_by(id=run_id).first()
                
                if not scraping_run:
                    return None
                
                run_data = scraping_run.to_dict()
                run_data["listings"] = [
                    listing.to_dict() for listing in scraping_run.listings
                ]
                
                return run_data
                
        except Exception as e:
            logger.error(f"Error getting scraping run with listings {run_id}: {e}")
            return None
    
    def associate_listing_with_scraping_run(self, listing_id: int, run_id: int) -> bool:
        """
        Associate a listing with a scraping run.
        
        Args:
            listing_id: Listing ID
            run_id: Scraping run ID
            
        Returns:
            True if association successful
        """
        try:
            with self.schema.get_session() as session:
                # Check if association already exists
                existing = session.query(ListingScrapingRun).filter_by(
                    listing_id=listing_id,
                    scraping_run_id=run_id
                ).first()
                
                if existing:
                    logger.debug(f"Association already exists: listing {listing_id}, run {run_id}")
                    return True
                
                # Create new association
                association = ListingScrapingRun(
                    listing_id=listing_id,
                    scraping_run_id=run_id
                )
                
                session.add(association)
                
                logger.info(f"Associated listing {listing_id} with scraping run {run_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error associating listing {listing_id} with run {run_id}: {e}")
            return False
    
    def get_listings_by_scraping_run(self, run_id: int, 
                                   limit: int = 1000) -> List[Dict[str, Any]]:
        """
        Get all listings discovered in a scraping run.
        
        Args:
            run_id: Scraping run ID
            limit: Maximum number of listings
            
        Returns:
            List of listing dictionaries
        """
        try:
            with self.schema.get_session() as session:
                # Get listings through association table
                listings = session.query(Listing).join(
                    ListingScrapingRun
                ).filter(
                    ListingScrapingRun.scraping_run_id == run_id
                ).order_by(
                    ListingScrapingRun.discovered_at.desc()
                ).limit(limit).all()
                
                return [listing.to_dict() for listing in listings]
                
        except Exception as e:
            logger.error(f"Error getting listings for scraping run {run_id}: {e}")
            return []
    
    def get_scraping_runs_by_listing(self, listing_id: int) -> List[Dict[str, Any]]:
        """
        Get all scraping runs that discovered a listing.
        
        Args:
            listing_id: Listing ID
            
        Returns:
            List of scraping run dictionaries
        """
        try:
            with self.schema.get_session() as session:
                # Get scraping runs through association table
                scraping_runs = session.query(ScrapingRun).join(
                    ListingScrapingRun
                ).filter(
                    ListingScrapingRun.listing_id == listing_id
                ).order_by(
                    ListingScrapingRun.discovered_at.desc()
                ).all()
                
                return [run.to_dict() for run in scraping_runs]
                
        except Exception as e:
            logger.error(f"Error getting scraping runs for listing {listing_id}: {e}")
            return []
    
    def get_contact_validation_history(self, contact_id: int) -> List[Dict[str, Any]]:
        """
        Get complete validation history for a contact.
        
        Args:
            contact_id: Contact ID
            
        Returns:
            List of validation history entries
        """
        try:
            with self.schema.get_session() as session:
                validations = session.query(ContactValidation).filter_by(
                    contact_id=contact_id
                ).order_by(ContactValidation.validated_at.desc()).all()
                
                return [validation.to_dict() for validation in validations]
                
        except Exception as e:
            logger.error(f"Error getting validation history for contact {contact_id}: {e}")
            return []
    
    def add_contact_validation(self, contact_id: int, validation_data: Dict[str, Any]) -> bool:
        """
        Add a validation entry for a contact.
        
        Args:
            contact_id: Contact ID
            validation_data: Validation data
            
        Returns:
            True if validation added successfully
        """
        try:
            with self.schema.get_session() as session:
                # Check if contact exists
                contact = session.query(Contact).filter_by(id=contact_id).first()
                if not contact:
                    logger.warning(f"Contact not found: {contact_id}")
                    return False
                
                # Create validation entry
                validation = ContactValidation(
                    contact_id=contact_id,
                    validation_method=validation_data["validation_method"],
                    validation_result=validation_data["validation_result"],
                    confidence_score=validation_data.get("confidence_score"),
                    validator_version=validation_data.get("validator_version", "1.0.0")
                )
                
                # Set validation metadata if provided
                if "validation_metadata" in validation_data:
                    validation.validation_metadata = json.dumps(
                        validation_data["validation_metadata"]
                    )
                
                session.add(validation)
                
                # Update contact status
                contact.status = validation_data["validation_result"]
                contact.validated_at = datetime.utcnow()
                
                logger.info(f"Added validation for contact {contact_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error adding validation for contact {contact_id}: {e}")
            return False
    
    def get_duplicate_listings(self, original_id: int) -> List[Dict[str, Any]]:
        """
        Get all duplicate listings of an original listing.
        
        Args:
            original_id: Original listing ID
            
        Returns:
            List of duplicate listing dictionaries
        """
        try:
            with self.schema.get_session() as session:
                duplicates = session.query(Listing).filter_by(
                    duplicate_of_id=original_id,
                    deduplication_status=DeduplicationStatus.DUPLICATE
                ).all()
                
                return [dup.to_dict() for dup in duplicates]
                
        except Exception as e:
            logger.error(f"Error getting duplicate listings for {original_id}: {e}")
            return []
    
    def get_listing_duplicates_chain(self, listing_id: int) -> List[Dict[str, Any]]:
        """
        Get the complete chain of duplicates for a listing.
        
        Args:
            listing_id: Starting listing ID
            
        Returns:
            List of all related listings in the duplicate chain
        """
        try:
            with self.schema.get_session() as session:
                # Get the original listing (follow duplicate_of_id chain)
                current_listing = session.query(Listing).filter_by(id=listing_id).first()
                if not current_listing:
                    return []
                
                # Find the original listing
                original_id = listing_id
                while current_listing.duplicate_of_id:
                    original_id = current_listing.duplicate_of_id
                    current_listing = session.query(Listing).filter_by(id=original_id).first()
                    if not current_listing:
                        break
                
                # Get all duplicates of the original
                all_duplicates = session.query(Listing).filter(
                    or_(
                        Listing.id == original_id,
                        Listing.duplicate_of_id == original_id
                    )
                ).all()
                
                return [listing.to_dict() for listing in all_duplicates]
                
        except Exception as e:
            logger.error(f"Error getting duplicate chain for {listing_id}: {e}")
            return []
    
    def get_job_execution_history(self, job_id: str) -> List[Dict[str, Any]]:
        """
        Get execution history for a scheduled job.
        
        Args:
            job_id: Job ID
            
        Returns:
            List of job execution entries
        """
        try:
            with self.schema.get_session() as session:
                job = session.query(JobStore).filter_by(job_id=job_id).first()
                if not job:
                    return []
                
                return job.to_dict()
                
        except Exception as e:
            logger.error(f"Error getting job execution history for {job_id}: {e}")
            return []
    
    def update_job_statistics(self, job_id: str, success: bool, 
                            execution_time: Optional[float] = None) -> bool:
        """
        Update job execution statistics.
        
        Args:
            job_id: Job ID
            success: Whether execution was successful
            execution_time: Optional execution time in seconds
            
        Returns:
            True if update successful
        """
        try:
            with self.schema.get_session() as session:
                job = session.query(JobStore).filter_by(job_id=job_id).first()
                if not job:
                    logger.warning(f"Job not found: {job_id}")
                    return False
                
                # Update statistics
                job.run_count += 1
                job.last_run_time = datetime.utcnow()
                
                if success:
                    job.success_count += 1
                else:
                    job.failure_count += 1
                
                # Update next run time if schedule is set
                if job.schedule_expression:
                    # This would require a cron parser to calculate next run time
                    # For now, just update the last run time
                    pass
                
                logger.info(f"Updated statistics for job {job_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating job statistics for {job_id}: {e}")
            return False
    
    def get_configuration_with_history(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration value with update history.
        
        Args:
            key: Configuration key
            
        Returns:
            Dictionary with configuration and history
        """
        try:
            with self.schema.get_session() as session:
                config = session.query(Configuration).filter_by(key=key).first()
                if not config:
                    return None
                
                config_data = config.to_dict()
                
                # Add update history (simplified - would need separate history table for full history)
                config_data["last_updated"] = config.updated_at.isoformat() if config.updated_at else None
                config_data["updated_by"] = config.updated_by
                
                return config_data
                
        except Exception as e:
            logger.error(f"Error getting configuration with history for {key}: {e}")
            return None
    
    def get_related_listings(self, listing_id: int, 
                           relationship_type: str = "similar") -> List[Dict[str, Any]]:
        """
        Get related listings based on various criteria.
        
        Args:
            listing_id: Source listing ID
            relationship_type: Type of relationship ('similar', 'same_provider', 'same_area')
            
        Returns:
            List of related listing dictionaries
        """
        try:
            with self.schema.get_session() as session:
                source_listing = session.query(Listing).filter_by(id=listing_id).first()
                if not source_listing:
                    return []
                
                related_listings = []
                
                if relationship_type == "same_provider":
                    # Get listings from same provider
                    related_listings = session.query(Listing).filter(
                        and_(
                            Listing.provider == source_listing.provider,
                            Listing.id != listing_id,
                            Listing.status == ListingStatus.ACTIVE
                        )
                    ).limit(20).all()
                
                elif relationship_type == "same_area":
                    # Get listings from same area (simplified - based on address similarity)
                    if source_listing.address:
                        related_listings = session.query(Listing).filter(
                            and_(
                                Listing.address.ilike(f"%{source_listing.address[:20]}%"),
                                Listing.id != listing_id,
                                Listing.status == ListingStatus.ACTIVE
                            )
                        ).limit(20).all()
                
                elif relationship_type == "similar":
                    # Get similar listings (simplified - based on price and size range)
                    if source_listing.price and source_listing.size:
                        related_listings = session.query(Listing).filter(
                            and_(
                                Listing.price == source_listing.price,
                                Listing.size == source_listing.size,
                                Listing.id != listing_id,
                                Listing.status == ListingStatus.ACTIVE
                            )
                        ).limit(20).all()
                
                return [listing.to_dict() for listing in related_listings]
                
        except Exception as e:
            logger.error(f"Error getting related listings for {listing_id}: {e}")
            return []
    
    def cleanup_orphaned_data(self) -> Dict[str, int]:
        """
        Clean up orphaned data (contacts without listings, etc.).
        
        Returns:
            Dictionary with cleanup counts
        """
        try:
            cleanup_counts = {
                "orphaned_contacts": 0,
                "orphaned_validations": 0,
                "orphaned_associations": 0
            }
            
            with self.schema.get_session() as session:
                # Clean up orphaned contacts
                orphaned_contacts = session.execute("""
                    DELETE FROM contacts 
                    WHERE listing_id NOT IN (SELECT id FROM listings)
                """)
                cleanup_counts["orphaned_contacts"] = orphaned_contacts.rowcount
                
                # Clean up orphaned contact validations
                orphaned_validations = session.execute("""
                    DELETE FROM contact_validations 
                    WHERE contact_id NOT IN (SELECT id FROM contacts)
                """)
                cleanup_counts["orphaned_validations"] = orphaned_validations.rowcount
                
                # Clean up orphaned listing-scraping run associations
                orphaned_associations = session.execute("""
                    DELETE FROM listing_scraping_runs 
                    WHERE listing_id NOT IN (SELECT id FROM listings)
                       OR scraping_run_id NOT IN (SELECT id FROM scraping_runs)
                """)
                cleanup_counts["orphaned_associations"] = orphaned_associations.rowcount
            
            logger.info(f"Cleaned up orphaned data: {cleanup_counts}")
            return cleanup_counts
            
        except Exception as e:
            logger.error(f"Error cleaning up orphaned data: {e}")
            return cleanup_counts
    
    def get_data_integrity_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive data integrity report.
        
        Returns:
            Dictionary with integrity report
        """
        try:
            report = {
                "timestamp": datetime.utcnow().isoformat(),
                "summary": {"valid": True, "issues": 0, "warnings": 0},
                "details": {}
            }
            
            with self.schema.get_session() as session:
                # Check for orphaned records
                orphaned_contacts = session.execute("""
                    SELECT COUNT(*) 
                    FROM contacts c 
                    LEFT JOIN listings l ON c.listing_id = l.id 
                    WHERE l.id IS NULL
                """).scalar()
                
                orphaned_validations = session.execute("""
                    SELECT COUNT(*) 
                    FROM contact_validations cv 
                    LEFT JOIN contacts c ON cv.contact_id = c.id 
                    WHERE c.id IS NULL
                """).scalar()
                
                orphaned_associations = session.execute("""
                    SELECT COUNT(*) 
                    FROM listing_scraping_runs lsr 
                    LEFT JOIN listings l ON lsr.listing_id = l.id 
                    LEFT JOIN scraping_runs sr ON lsr.scraping_run_id = sr.id 
                    WHERE l.id IS NULL OR sr.id IS NULL
                """).scalar()
                
                report["details"]["orphaned_records"] = {
                    "orphaned_contacts": orphaned_contacts,
                    "orphaned_validations": orphaned_validations,
                    "orphaned_associations": orphaned_associations
                }
                
                # Check for inconsistent duplicate relationships
                invalid_duplicates = session.execute("""
                    SELECT COUNT(*) 
                    FROM listings l1 
                    LEFT JOIN listings l2 ON l1.duplicate_of_id = l2.id 
                    WHERE l1.deduplication_status = 'duplicate' AND l2.id IS NULL
                """).scalar()
                
                report["details"]["invalid_duplicates"] = invalid_duplicates
                
                # Check for circular duplicate references
                circular_refs = session.execute("""
                    WITH RECURSIVE duplicate_chain AS (
                        SELECT id, duplicate_of_id, 1 as depth, CAST(id AS TEXT) as path
                        FROM listings 
                        WHERE duplicate_of_id IS NOT NULL
                        UNION ALL
                        SELECT l.id, l.duplicate_of_id, dc.depth + 1, dc.path || '->' || CAST(l.id AS TEXT)
                        FROM listings l
                        JOIN duplicate_chain dc ON l.id = dc.duplicate_of_id
                        WHERE dc.depth < 10
                    )
                    SELECT COUNT(*) 
                    FROM duplicate_chain 
                    WHERE path LIKE '%' || CAST(id AS TEXT) || '%' 
                    AND depth > 1
                """).scalar()
                
                report["details"]["circular_references"] = circular_refs
                
                # Update summary
                total_issues = (orphaned_contacts + orphaned_validations + 
                              orphaned_associations + invalid_duplicates + circular_refs)
                
                report["summary"]["issues"] = total_issues
                report["summary"]["valid"] = total_issues == 0
                
                if total_issues > 0:
                    report["summary"]["warnings"] = total_issues
                
            return report
            
        except Exception as e:
            logger.error(f"Error generating data integrity report: {e}")
            return {"error": str(e), "valid": False}