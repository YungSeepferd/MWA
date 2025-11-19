"""
CRUD operations for MWA Core storage system.

Provides comprehensive Create, Read, Update, Delete operations for all entities
with transaction management, bulk operations, and query optimization.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta
import json
from typing import Dict, List, Optional, Any, Union, Tuple
from contextlib import contextmanager

from sqlalchemy import and_, or_, func, text
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy.sql import expression

from .models import (
    Listing, Contact, ScrapingRun, ListingScrapingRun, ContactValidation,
    JobStore, Configuration, BackupMetadata, ListingStatus, ContactType,
    ContactStatus, JobStatus, DeduplicationStatus
)
from .schema import DatabaseSchema

logger = logging.getLogger(__name__)


class CRUDOperations:
    """Comprehensive CRUD operations for all entities."""
    
    def __init__(self, database_schema: DatabaseSchema):
        """
        Initialize CRUD operations.
        
        Args:
            database_schema: DatabaseSchema instance
        """
        self.schema = database_schema
    
    @contextmanager
    def get_session(self) -> Session:
        """
        Get a database session with proper error handling.
        
        Yields:
            SQLAlchemy session
        """
        session = self.schema.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Session error: {e}")
            raise
        finally:
            session.close()
    
    # Listing Operations
    def create_listing(self, listing_data: Dict[str, Any]) -> Optional[Listing]:
        """
        Create a new listing.
        
        Args:
            listing_data: Dictionary with listing data
            
        Returns:
            Created Listing object or None if failed
        """
        try:
            with self.get_session() as session:
                # Check for existing listing by URL
                existing = session.query(Listing).filter_by(
                    url=listing_data["url"]
                ).first()
                
                if existing:
                    logger.debug(f"Listing already exists: {listing_data['url']}")
                    return None
                
                # Create new listing
                listing = Listing(
                    provider=listing_data["provider"],
                    external_id=listing_data.get("external_id"),
                    title=listing_data["title"],
                    url=listing_data["url"],
                    price=listing_data.get("price"),
                    size=listing_data.get("size"),
                    rooms=listing_data.get("rooms"),
                    address=listing_data.get("address"),
                    description=listing_data.get("description"),
                    images=json.dumps(listing_data.get("images", [])),
                    contacts=json.dumps(listing_data.get("contacts", [])),
                    raw_data=json.dumps(listing_data.get("raw_data", {})),
                )
                
                # Generate hash signature for deduplication
                listing.update_hash_signature()
                
                session.add(listing)
                session.flush()  # Get the ID
                
                logger.info(f"Created listing: {listing.title} (ID: {listing.id})")
                return listing
                
        except IntegrityError as e:
            logger.warning(f"Listing creation failed (integrity error): {e}")
            return None
        except Exception as e:
            logger.error(f"Error creating listing: {e}")
            return None
    
    def get_listing(self, listing_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a listing by ID.
        
        Args:
            listing_id: Listing ID
            
        Returns:
            Listing dictionary or None
        """
        try:
            with self.get_session() as session:
                listing = session.query(Listing).filter_by(id=listing_id).first()
                return listing.to_dict() if listing else None
        except Exception as e:
            logger.error(f"Error getting listing {listing_id}: {e}")
            return None
    
    def get_listing_by_url(self, url: str) -> Optional[Dict[str, Any]]:
        """
        Get a listing by URL.
        
        Args:
            url: Listing URL
            
        Returns:
            Listing dictionary or None
        """
        try:
            with self.get_session() as session:
                listing = session.query(Listing).filter_by(url=url).first()
                return listing.to_dict() if listing else None
        except Exception as e:
            logger.error(f"Error getting listing by URL {url}: {e}")
            return None
    
    def get_listings(
        self,
        limit: int = 100,
        offset: int = 0,
        provider: Optional[str] = None,
        status: Optional[ListingStatus] = None,
        search_query: Optional[str] = None,
        min_price: Optional[str] = None,
        max_price: Optional[str] = None,
        order_by: str = "scraped_at",
        order_desc: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Get listings with various filters and options.
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            provider: Filter by provider
            status: Filter by status
            search_query: Search in title and description
            min_price: Minimum price filter
            max_price: Maximum price filter
            order_by: Field to order by
            order_desc: Order descending
            
        Returns:
            List of Listing objects
        """
        try:
            with self.get_session() as session:
                query = session.query(Listing)
                
                # Apply filters
                if provider:
                    query = query.filter(Listing.provider == provider)
                
                if status:
                    query = query.filter(Listing.status == status)
                
                if search_query:
                    search_filter = or_(
                        Listing.title.ilike(f"%{search_query}%"),
                        Listing.description.ilike(f"%{search_query}%")
                    )
                    query = query.filter(search_filter)
                
                if min_price:
                    query = query.filter(Listing.price >= min_price)
                
                if max_price:
                    query = query.filter(Listing.price <= max_price)
                
                # Apply ordering
                order_field = getattr(Listing, order_by, Listing.scraped_at)
                if order_desc:
                    order_field = order_field.desc()
                
                query = query.order_by(order_field)
                
                # Apply pagination
                query = query.limit(limit).offset(offset)
                
                listings = query.all()
                return [listing.to_dict() for listing in listings]
                
        except Exception as e:
            logger.error(f"Error getting listings: {e}")
            return []
    
    def update_listing(self, listing_id: int, update_data: Dict[str, Any]) -> bool:
        """
        Update a listing.
        
        Args:
            listing_id: Listing ID
            update_data: Dictionary with fields to update
            
        Returns:
            True if updated successfully
        """
        try:
            with self.get_session() as session:
                listing = session.query(Listing).filter_by(id=listing_id).first()
                
                if not listing:
                    logger.warning(f"Listing not found: {listing_id}")
                    return False
                
                # Update fields
                for key, value in update_data.items():
                    if hasattr(listing, key) and key != "id":
                        setattr(listing, key, value)
                
                # Update hash signature if relevant fields changed
                if any(key in update_data for key in ["title", "price", "size", "rooms", "address"]):
                    listing.update_hash_signature()
                
                listing.updated_at = datetime.utcnow()
                
                logger.info(f"Updated listing: {listing_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating listing {listing_id}: {e}")
            return False
    
    def delete_listing(self, listing_id: int) -> bool:
        """
        Delete a listing and its related data.
        
        Args:
            listing_id: Listing ID
            
        Returns:
            True if deleted successfully
        """
        try:
            with self.get_session() as session:
                listing = session.query(Listing).filter_by(id=listing_id).first()
                
                if not listing:
                    logger.warning(f"Listing not found: {listing_id}")
                    return False
                
                session.delete(listing)
                
                logger.info(f"Deleted listing: {listing_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error deleting listing {listing_id}: {e}")
            return False
    
    def bulk_create_listings(self, listings_data: List[Dict[str, Any]]) -> int:
        """
        Bulk create multiple listings.
        
        Args:
            listings_data: List of listing data dictionaries
            
        Returns:
            Number of listings created
        """
        try:
            with self.get_session() as session:
                created_count = 0
                
                for listing_data in listings_data:
                    # Check for existing listing by URL
                    existing = session.query(Listing).filter_by(
                        url=listing_data["url"]
                    ).first()
                    
                    if existing:
                        continue
                    
                    # Create new listing
                    listing = Listing(
                        provider=listing_data["provider"],
                        external_id=listing_data.get("external_id"),
                        title=listing_data["title"],
                        url=listing_data["url"],
                        price=listing_data.get("price"),
                        size=listing_data.get("size"),
                        rooms=listing_data.get("rooms"),
                        address=listing_data.get("address"),
                        description=listing_data.get("description"),
                        images=json.dumps(listing_data.get("images", [])),
                        contacts=json.dumps(listing_data.get("contacts", [])),
                        raw_data=json.dumps(listing_data.get("raw_data", {})),
                    )
                    
                    # Generate hash signature
                    listing.update_hash_signature()
                    
                    session.add(listing)
                    created_count += 1
                
                logger.info(f"Bulk created {created_count} listings")
                return created_count
                
        except Exception as e:
            logger.error(f"Error bulk creating listings: {e}")
            return 0
    
    # Contact Operations
    def create_contact(self, listing_id: int, contact_data: Dict[str, Any]) -> Optional[Contact]:
        """
        Create a new contact for a listing.
        
        Args:
            listing_id: Listing ID
            contact_data: Contact data dictionary
            
        Returns:
            Created Contact object or None
        """
        try:
            with self.get_session() as session:
                # Check if listing exists
                listing = session.query(Listing).filter_by(id=listing_id).first()
                if not listing:
                    logger.warning(f"Listing not found: {listing_id}")
                    return None
                
                # Check for existing contact
                existing = session.query(Contact).filter_by(
                    listing_id=listing_id,
                    type=ContactType(contact_data["type"]),
                    value=contact_data["value"]
                ).first()
                
                if existing:
                    logger.debug(f"Contact already exists for listing {listing_id}")
                    return None
                
                # Create new contact
                contact = Contact(
                    listing_id=listing_id,
                    type=ContactType(contact_data["type"]),
                    value=contact_data["value"],
                    confidence=contact_data.get("confidence"),
                    source=contact_data.get("source"),
                    status=ContactStatus(contact_data.get("status", "unvalidated")),
                )
                
                # Generate hash signature
                contact.update_hash_signature()
                
                session.add(contact)
                session.flush()
                
                logger.info(f"Created contact for listing {listing_id}: {contact.value}")
                return contact
                
        except IntegrityError as e:
            logger.warning(f"Contact creation failed (integrity error): {e}")
            return None
        except Exception as e:
            logger.error(f"Error creating contact: {e}")
            return None
    
    def get_contacts(
        self,
        listing_id: Optional[int] = None,
        contact_type: Optional[ContactType] = None,
        status: Optional[ContactStatus] = None,
        validated_only: bool = False,
        limit: int = 1000
    ) -> List[Contact]:
        """
        Get contacts with various filters.
        
        Args:
            listing_id: Filter by listing ID
            contact_type: Filter by contact type
            status: Filter by status
            validated_only: Only validated contacts
            limit: Maximum results
            
        Returns:
            List of Contact objects
        """
        try:
            with self.get_session() as session:
                query = session.query(Contact)
                
                if listing_id:
                    query = query.filter(Contact.listing_id == listing_id)
                
                if contact_type:
                    query = query.filter(Contact.type == contact_type)
                
                if status:
                    query = query.filter(Contact.status == status)
                
                if validated_only:
                    query = query.filter(Contact.status == ContactStatus.VALID)
                
                query = query.order_by(Contact.created_at.desc())
                query = query.limit(limit)
                
                return query.all()
                
        except Exception as e:
            logger.error(f"Error getting contacts: {e}")
            return []
    
    def update_contact_status(self, contact_id: int, status: ContactStatus, 
                            validation_metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update contact status and validation metadata.
        
        Args:
            contact_id: Contact ID
            status: New status
            validation_metadata: Optional validation metadata
            
        Returns:
            True if updated successfully
        """
        try:
            with self.get_session() as session:
                contact = session.query(Contact).filter_by(id=contact_id).first()
                
                if not contact:
                    logger.warning(f"Contact not found: {contact_id}")
                    return False
                
                contact.status = status
                contact.validated_at = datetime.utcnow()
                
                if validation_metadata:
                    contact.set_validation_metadata(validation_metadata)
                
                # Create validation history entry
                validation = ContactValidation(
                    contact_id=contact_id,
                    validation_method="manual",  # Could be extended
                    validation_result=status,
                    confidence_score=contact.confidence,
                )
                session.add(validation)
                
                logger.info(f"Updated contact {contact_id} status to {status.value}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating contact status: {e}")
            return False
    
    # Scraping Run Operations
    def create_scraping_run(self, provider: str, trigger_type: str = "manual", 
                          triggered_by: str = "system") -> Optional[ScrapingRun]:
        """
        Create a new scraping run.
        
        Args:
            provider: Provider name
            trigger_type: Trigger type (manual, scheduled, api)
            triggered_by: Who triggered it
            
        Returns:
            Created ScrapingRun object
        """
        try:
            with self.get_session() as session:
                scraping_run = ScrapingRun(
                    provider=provider,
                    status=JobStatus.PENDING,
                    trigger_type=trigger_type,
                    triggered_by=triggered_by,
                )
                
                session.add(scraping_run)
                session.flush()
                
                logger.info(f"Created scraping run for {provider}: {scraping_run.id}")
                return scraping_run
                
        except Exception as e:
            logger.error(f"Error creating scraping run: {e}")
            return None
    
    def update_scraping_run(self, run_id: int, update_data: Dict[str, Any]) -> bool:
        """
        Update scraping run status and results.
        
        Args:
            run_id: Scraping run ID
            update_data: Data to update
            
        Returns:
            True if updated successfully
        """
        try:
            with self.get_session() as session:
                scraping_run = session.query(ScrapingRun).filter_by(id=run_id).first()
                
                if not scraping_run:
                    logger.warning(f"Scraping run not found: {run_id}")
                    return False
                
                # Update fields
                for key, value in update_data.items():
                    if hasattr(scraping_run, key) and key != "id":
                        setattr(scraping_run, key, value)
                
                # Set completion time if status is completed or failed
                if ("status" in update_data and 
                    update_data["status"] in [JobStatus.COMPLETED, JobStatus.FAILED]):
                    scraping_run.completed_at = datetime.utcnow()
                
                logger.info(f"Updated scraping run {run_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error updating scraping run {run_id}: {e}")
            return False
    
    def get_scraping_runs(
        self,
        provider: Optional[str] = None,
        status: Optional[JobStatus] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ScrapingRun]:
        """
        Get scraping runs with filters.
        
        Args:
            provider: Filter by provider
            status: Filter by status
            limit: Maximum results
            offset: Results to skip
            
        Returns:
            List of ScrapingRun objects
        """
        try:
            with self.get_session() as session:
                query = session.query(ScrapingRun)
                
                if provider:
                    query = query.filter(ScrapingRun.provider == provider)
                
                if status:
                    query = query.filter(ScrapingRun.status == status)
                
                query = query.order_by(ScrapingRun.started_at.desc())
                query = query.limit(limit).offset(offset)
                
                return query.all()
                
        except Exception as e:
            logger.error(f"Error getting scraping runs: {e}")
            return []
    
    # Statistics and Analytics
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive database statistics.
        
        Returns:
            Dictionary with statistics
        """
        try:
            with self.get_session() as session:
                stats = {}
                
                # Count listings
                stats["total_listings"] = session.query(Listing).count()
                
                # Count by provider
                provider_counts = session.query(
                    Listing.provider, func.count(Listing.id)
                ).group_by(Listing.provider).all()
                stats["listings_by_provider"] = dict(provider_counts)
                
                # Count by status
                status_counts = session.query(
                    Listing.status, func.count(Listing.id)
                ).group_by(Listing.status).all()
                stats["listings_by_status"] = {
                    status.value if status else "unknown": count 
                    for status, count in status_counts
                }
                
                # Count contacts
                stats["total_contacts"] = session.query(Contact).count()
                
                # Count by type
                type_counts = session.query(
                    Contact.type, func.count(Contact.id)
                ).group_by(Contact.type).all()
                stats["contacts_by_type"] = {
                    contact_type.value if contact_type else "unknown": count 
                    for contact_type, count in type_counts
                }
                
                # Recent scraping runs
                recent_runs = session.query(ScrapingRun).order_by(
                    ScrapingRun.started_at.desc()
                ).limit(10).all()
                stats["recent_scraping_runs"] = [run.to_dict() for run in recent_runs]
                
                # Database size (approximate for SQLite)
                if self.schema.engine.name == "sqlite":
                    result = session.execute(text("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")).first()
                    stats["database_size_bytes"] = result[0] if result else 0
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting statistics: {e}")
            return {}
    
    def cleanup_old_data(self, days_to_keep: int = 90) -> Dict[str, int]:
        """
        Clean up old data based on retention policy.
        
        Args:
            days_to_keep: Number of days to keep data
            
        Returns:
            Dictionary with cleanup counts
        """
        try:
            with self.get_session() as session:
                cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)
                
                cleanup_counts = {}
                
                # Delete old contacts
                contacts_deleted = session.query(Contact).filter(
                    Contact.created_at < cutoff_date
                ).delete()
                cleanup_counts["contacts_deleted"] = contacts_deleted
                
                # Delete old scraping runs
                runs_deleted = session.query(ScrapingRun).filter(
                    ScrapingRun.started_at < cutoff_date
                ).delete()
                cleanup_counts["scraping_runs_deleted"] = runs_deleted
                
                # Delete old backup metadata
                backups_deleted = session.query(BackupMetadata).filter(
                    BackupMetadata.created_at < cutoff_date
                ).delete()
                cleanup_counts["backup_metadata_deleted"] = backups_deleted
                
                logger.info(f"Cleaned up old data: {cleanup_counts}")
                return cleanup_counts
                
        except Exception as e:
            logger.error(f"Error cleaning up old data: {e}")
            return {}