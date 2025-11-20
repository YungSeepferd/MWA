"""
Integration module for contact discovery with MWA Core storage system.

Provides seamless integration between contact discovery and the enhanced storage system:
- Contact storage and retrieval
- Relationship management with listings
- Deduplication and merging
- Validation result persistence
- Performance metrics integration
- Batch operations and optimization
"""

import asyncio
import logging
from typing import List, Dict, Optional, Tuple, Any
from pathlib import Path
from datetime import datetime
import json

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from .models import Contact, ContactForm, ContactMethod, ContactStatus, ConfidenceLevel
from .discovery import ContactDiscoveryEngine
from .scoring import ContactScoringEngine
from .validators import ContactValidator, ValidationResult
from ..storage.models import Contact as StorageContact, ContactValidation as StorageValidation, Listing
from ..storage.operations import CRUDOperations as StorageOperations
from ..storage.deduplication import DeduplicationEngine
from ..config.settings import Settings

logger = logging.getLogger(__name__)


class ContactDiscoveryIntegration:
    """
    Integration layer between contact discovery and MWA Core storage system.
    
    Features:
    - Seamless storage integration with enhanced models
    - Intelligent deduplication and merging
    - Validation result persistence
    - Performance metrics tracking
    - Batch operations for efficiency
    - Relationship management with listings
    """
    
    def __init__(self, config: Settings, storage_operations: Optional[StorageOperations] = None):
        """
        Initialize contact discovery integration.
        
        Args:
            config: Application configuration
            storage_operations: Storage operations instance (optional)
        """
        self.config = config
        self.settings = config.contact_discovery
        self.storage_ops = storage_operations or StorageOperations(config.storage.database_schema)
        
        # Initialize discovery engine
        self.discovery_engine = ContactDiscoveryEngine(config)
        
        # Initialize scoring and validation
        self.scoring_engine = ContactScoringEngine(config)
        self.validator = ContactValidator(
            enable_smtp_verification=self.settings.smtp_verification,
            enable_dns_verification=self.settings.dns_verification,
            rate_limit_seconds=self.settings.rate_limit_seconds
        )
        
        # Initialize deduplication
        self.deduplication_engine = DeduplicationEngine(config)
        
        logger.info(f"Contact discovery integration initialized")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.discovery_engine.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.discovery_engine.__aexit__(exc_type, exc_val, exc_tb)
    
    async def process_listing(self, listing: Dict, listing_id: Optional[int] = None) -> Tuple[List[Contact], List[ContactForm]]:
        """
        Process a single listing for contact discovery and store results.
        
        Args:
            listing: Listing data dictionary
            listing_id: Associated listing ID from storage (optional)
            
        Returns:
            Tuple of (contacts, forms) discovered and stored
        """
        if not self.settings.enabled:
            logger.debug("Contact discovery disabled, skipping extraction")
            return [], []
        
        start_time = datetime.now()
        
        try:
            # Extract URL from listing
            url = self._extract_listing_url(listing)
            if not url:
                logger.warning(f"No URL found in listing: {listing.get('title', 'Unknown')}")
                return [], []
            
            # Perform contact discovery
            logger.info(f"Starting contact discovery for listing: {url}")
            result = await self.discovery_engine.discover_contacts(url)
            
            # Store results with listing association
            stored_contacts = await self._store_contacts(result.contacts, listing_id)
            stored_forms = await self._store_forms(result.forms, listing_id)
            
            # Update listing with contact information
            if listing_id:
                await self._update_listing_contacts(listing_id, stored_contacts, stored_forms)
            
            # Log results
            duration = (datetime.now() - start_time).total_seconds()
            logger.info(f"Listing contact discovery completed: {len(stored_contacts)} contacts, "
                       f"{len(stored_forms)} forms, duration: {duration:.1f}s")
            
            return stored_contacts, stored_forms
            
        except Exception as e:
            logger.error(f"Contact discovery failed for listing: {e}")
            return [], []
    
    async def process_listings_batch(self, listings: List[Dict], listing_ids: Optional[List[int]] = None) -> Dict[str, int]:
        """
        Process multiple listings for contact discovery in batch.
        
        Args:
            listings: List of listing data dictionaries
            listing_ids: Associated listing IDs (optional)
            
        Returns:
            Dictionary with summary statistics
        """
        if not self.settings.enabled:
            logger.debug("Contact discovery disabled, skipping batch processing")
            return {"processed": 0, "contacts_found": 0, "forms_found": 0}
        
        summary = {
            "processed": 0,
            "contacts_found": 0,
            "forms_found": 0,
            "errors": 0
        }
        
        # Process listings concurrently with rate limiting
        semaphore = asyncio.Semaphore(3)  # Limit concurrent processing
        
        async def process_single_listing(listing: Dict, listing_id: Optional[int]) -> Tuple[int, int]:
            async with semaphore:
                contacts, forms = await self.process_listing(listing, listing_id)
                return len(contacts), len(forms)
        
        # Create tasks
        tasks = []
        for i, listing in enumerate(listings):
            listing_id = listing_ids[i] if listing_ids and i < len(listing_ids) else None
            task = asyncio.create_task(process_single_listing(listing, listing_id))
            tasks.append(task)
        
        # Execute tasks and collect results
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to process listing {i}: {result}")
                    summary["errors"] += 1
                else:
                    contacts_count, forms_count = result
                    summary["processed"] += 1
                    summary["contacts_found"] += contacts_count
                    summary["forms_found"] += forms_count
            
        except Exception as e:
            logger.error(f"Batch processing failed: {e}")
            summary["errors"] += len(listings)
        
        logger.info(f"Batch contact discovery completed: {summary}")
        return summary
    
    async def _store_contacts(self, contacts: List[Contact], listing_id: Optional[int] = None) -> List[Contact]:
        """
        Store contacts in the enhanced storage system.
        
        Args:
            contacts: List of contacts to store
            listing_id: Associated listing ID (optional)
            
        Returns:
            List of successfully stored contacts
        """
        if not contacts:
            return []
        
        stored_contacts = []
        
        with self.storage_ops.get_session() as session:
            for contact in contacts:
                try:
                    # Check for existing contact
                    existing = self._find_existing_contact(session, contact, listing_id)
                    
                    if existing:
                        # Update existing contact
                        updated_contact = self._update_existing_contact(session, existing, contact)
                        stored_contacts.append(updated_contact)
                    else:
                        # Create new contact
                        new_contact = self._create_storage_contact(session, contact, listing_id)
                        stored_contacts.append(contact)
                    
                except Exception as e:
                    logger.error(f"Failed to store contact {contact.value}: {e}")
                    continue
        
        logger.debug(f"Stored {len(stored_contacts)} contacts")
        return stored_contacts
    
    async def _store_forms(self, forms: List[ContactForm], listing_id: Optional[int] = None) -> List[ContactForm]:
        """
        Store contact forms in the enhanced storage system.
        
        Args:
            forms: List of contact forms to store
            listing_id: Associated listing ID (optional)
            
        Returns:
            List of successfully stored forms
        """
        if not forms:
            return []
        
        stored_forms = []
        
        with self.storage_ops.get_session() as session:
            for form in forms:
                try:
                    # Convert form to contact for storage
                    form_contact = form.to_contact()
                    
                    # Check for existing form
                    existing = self._find_existing_contact(session, form_contact, listing_id)
                    
                    if existing:
                        # Update existing form
                        updated_form = self._update_existing_contact(session, existing, form_contact)
                        stored_forms.append(form)
                    else:
                        # Create new form
                        new_form = self._create_storage_contact(session, form_contact, listing_id)
                        stored_forms.append(form)
                    
                except Exception as e:
                    logger.error(f"Failed to store form {form.action_url}: {e}")
                    continue
        
        logger.debug(f"Stored {len(stored_forms)} forms")
        return stored_forms
    
    def _find_existing_contact(self, session: Session, contact: Contact, listing_id: Optional[int] = None) -> Optional[StorageContact]:
        """Find existing contact in storage."""
        query = session.query(StorageContact).filter(
            and_(
                StorageContact.type == contact.method.value,
                StorageContact.value == contact.value
            )
        )
        
        if listing_id:
            query = query.filter(StorageContact.listing_id == listing_id)
        
        return query.first()
    
    def _create_storage_contact(self, session: Session, contact: Contact, listing_id: Optional[int] = None) -> StorageContact:
        """Create new storage contact from discovery contact."""
        storage_contact = StorageContact(
            listing_id=listing_id,
            type=contact.method.value,
            value=contact.value,
            confidence=self._get_confidence_score(contact),
            source=contact.extraction_method,
            status=self._get_storage_status(contact.verification_status),
            validation_metadata=json.dumps(contact.metadata) if contact.metadata else None
        )
        
        # Generate hash signature for deduplication
        storage_contact.update_hash_signature()
        
        session.add(storage_contact)
        session.commit()
        
        return storage_contact
    
    def _update_existing_contact(self, session: Session, existing: StorageContact, contact: Contact) -> StorageContact:
        """Update existing storage contact with new information."""
        # Update confidence if higher
        new_confidence = self._get_confidence_score(contact)
        if new_confidence > (existing.confidence or 0):
            existing.confidence = new_confidence
        
        # Update source if more reliable
        if contact.extraction_method in ['mailto_link', 'standard_pattern']:
            existing.source = contact.extraction_method
        
        # Update status if verified
        if contact.verification_status == ContactStatus.VERIFIED:
            existing.status = self._get_storage_status(contact.verification_status)
            existing.validated_at = datetime.now()
        
        # Update validation metadata
        if contact.metadata:
            existing.validation_metadata = json.dumps(contact.metadata)
        
        existing.updated_at = datetime.now()
        session.commit()
        
        return existing
    
    def _get_confidence_score(self, contact: Contact) -> float:
        """Convert confidence level to numeric score."""
        confidence_map = {
            ConfidenceLevel.HIGH: 0.9,
            ConfidenceLevel.MEDIUM: 0.6,
            ConfidenceLevel.LOW: 0.3,
            ConfidenceLevel.UNCERTAIN: 0.1
        }
        return confidence_map.get(contact.confidence, 0.5)
    
    def _get_storage_status(self, status: ContactStatus) -> str:
        """Convert contact status to storage status."""
        status_map = {
            ContactStatus.VERIFIED: "valid",
            ContactStatus.INVALID: "invalid",
            ContactStatus.SUSPICIOUS: "suspicious",
            ContactStatus.FLAGGED: "suspicious",
            ContactStatus.UNVERIFIED: "unvalidated"
        }
        return status_map.get(status, "unvalidated")
    
    async def _update_listing_contacts(self, listing_id: int, contacts: List[Contact], forms: List[ContactForm]) -> None:
        """Update listing with contact information."""
        try:
            with self.storage_ops.get_session() as session:
                listing = session.query(Listing).filter(Listing.id == listing_id).first()
                if not listing:
                    logger.warning(f"Listing {listing_id} not found for contact update")
                    return
                
                # Update contacts field with discovered contacts
                contact_data = []
                for contact in contacts:
                    contact_data.append({
                        'method': contact.method.value,
                        'value': contact.value,
                        'confidence': contact.confidence.value,
                        'verified': contact.verification_status == ContactStatus.VERIFIED
                    })
                
                listing.contacts = json.dumps(contact_data)
                listing.updated_at = datetime.now()
                session.commit()
                
                logger.debug(f"Updated listing {listing_id} with {len(contacts)} contacts")
                
        except Exception as e:
            logger.error(f"Failed to update listing {listing_id} contacts: {e}")
    
    async def validate_stored_contacts(self, listing_id: Optional[int] = None,
                                     validation_level: str = "standard") -> List[ValidationResult]:
        """
        Validate contacts stored in the database.
        
        Args:
            listing_id: Specific listing ID to validate (optional)
            validation_level: Validation level ("basic", "standard", "comprehensive")
            
        Returns:
            List of validation results
        """
        with self.storage_ops.get_session() as session:
            # Query contacts to validate
            query = session.query(StorageContact).filter(StorageContact.status != "invalid")
            
            if listing_id:
                query = query.filter(StorageContact.listing_id == listing_id)
            
            storage_contacts = query.all()
            
            if not storage_contacts:
                return []
            
            # Convert to discovery contacts
            contacts_to_validate = []
            for storage_contact in storage_contacts:
                contact = Contact(
                    method=ContactMethod(storage_contact.type),
                    value=storage_contact.value,
                    confidence=ConfidenceLevel.HIGH if storage_contact.confidence > 0.8 else ConfidenceLevel.MEDIUM,
                    source_url="stored_contact",
                    verification_status=ContactStatus.UNVERIFIED
                )
                contacts_to_validate.append(contact)
            
            # Validate contacts
            validation_results = await self.validator.validate_contacts_batch(
                contacts_to_validate, validation_level
            )
            
            # Update storage with validation results
            for storage_contact, result in zip(storage_contacts, validation_results):
                if result.is_valid:
                    storage_contact.status = "valid"
                    storage_contact.validated_at = datetime.now()
                else:
                    storage_contact.status = "invalid"
                
                # Store validation metadata
                validation_metadata = StorageValidation(
                    contact_id=storage_contact.id,
                    validation_method=result.validation_method,
                    validation_result=result.is_valid,
                    confidence_score=result.confidence_score,
                    validation_metadata=json.dumps(result.metadata)
                )
                session.add(validation_metadata)
            
            session.commit()
            
            logger.info(f"Validated {len(validation_results)} stored contacts")
            return validation_results
    
    def get_contacts_for_listing(self, listing_id: int, 
                               contact_type: Optional[str] = None,
                               min_confidence: Optional[float] = None) -> List[Dict[str, Any]]:
        """
        Retrieve contacts for a specific listing.
        
        Args:
            listing_id: Listing ID
            contact_type: Filter by contact type (optional)
            min_confidence: Minimum confidence threshold (optional)
            
        Returns:
            List of contact dictionaries
        """
        with self.storage_ops.get_session() as session:
            query = session.query(StorageContact).filter(StorageContact.listing_id == listing_id)
            
            if contact_type:
                query = query.filter(StorageContact.type == contact_type)
            
            if min_confidence is not None:
                query = query.filter(StorageContact.confidence >= min_confidence)
            
            storage_contacts = query.all()
            
            contacts = []
            for storage_contact in storage_contacts:
                contact_data = {
                    'id': storage_contact.id,
                    'type': storage_contact.type,
                    'value': storage_contact.value,
                    'confidence': storage_contact.confidence,
                    'source': storage_contact.source,
                    'status': storage_contact.status,
                    'validated_at': storage_contact.validated_at.isoformat() if storage_contact.validated_at else None,
                    'created_at': storage_contact.created_at.isoformat(),
                    'updated_at': storage_contact.updated_at.isoformat()
                }
                contacts.append(contact_data)
            
            return contacts
    
    def search_contacts(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Search contacts by value or metadata.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of matching contact dictionaries
        """
        with self.storage_ops.get_session() as session:
            # Search in value and validation metadata
            storage_contacts = session.query(StorageContact).filter(
                or_(
                    StorageContact.value.contains(query),
                    StorageContact.validation_metadata.contains(query)
                )
            ).limit(limit).all()
            
            contacts = []
            for storage_contact in storage_contacts:
                contact_data = {
                    'id': storage_contact.id,
                    'listing_id': storage_contact.listing_id,
                    'type': storage_contact.type,
                    'value': storage_contact.value,
                    'confidence': storage_contact.confidence,
                    'source': storage_contact.source,
                    'status': storage_contact.status
                }
                contacts.append(contact_data)
            
            return contacts
    
    def get_contact_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive contact discovery statistics.
        
        Returns:
            Dictionary with contact statistics
        """
        with self.storage_ops.get_session() as session:
            # Total contacts
            total_contacts = session.query(StorageContact).count()
            
            # Contacts by type
            type_stats = {}
            for contact_type in ['email', 'phone', 'form', 'website', 'social_media']:
                count = session.query(StorageContact).filter(StorageContact.type == contact_type).count()
                if count > 0:
                    type_stats[contact_type] = count
            
            # Contacts by status
            status_stats = {}
            for status in ['valid', 'invalid', 'suspicious', 'unvalidated']:
                count = session.query(StorageContact).filter(StorageContact.status == status).count()
                if count > 0:
                    status_stats[status] = count
            
            # Recent activity (last 30 days)
            from datetime import datetime, timedelta
            recent_date = datetime.now() - timedelta(days=30)
            recent_contacts = session.query(StorageContact).filter(
                StorageContact.created_at >= recent_date
            ).count()
            
            # High confidence contacts
            high_confidence = session.query(StorageContact).filter(StorageContact.confidence >= 0.8).count()
            
            return {
                'total_contacts': total_contacts,
                'contacts_by_type': type_stats,
                'contacts_by_status': status_stats,
                'recent_contacts_30_days': recent_contacts,
                'high_confidence_contacts': high_confidence,
                'statistics_timestamp': datetime.now().isoformat()
            }
    
    def cleanup_old_contacts(self, days_old: int = 90) -> int:
        """
        Remove old contacts and their validation history.
        
        Args:
            days_old: Number of days after which contacts should be deleted
            
        Returns:
            Number of contacts deleted
        """
        try:
            with self.storage_ops.get_session() as session:
                cutoff_date = datetime.now() - timedelta(days=days_old)
                
                # Delete validation history first (foreign key constraint)
                deleted_validations = session.query(StorageValidation).join(StorageContact).filter(
                    StorageContact.created_at < cutoff_date
                ).delete(synchronize_session=False)
                
                # Delete old contacts
                deleted_contacts = session.query(StorageContact).filter(
                    StorageContact.created_at < cutoff_date
                ).delete(synchronize_session=False)
                
                session.commit()
                
                logger.info(f"Cleaned up {deleted_contacts} old contacts and {deleted_validations} validation records")
                return deleted_contacts
                
        except Exception as e:
            logger.error(f"Contact cleanup failed: {e}")
            return 0
    
    def _extract_listing_url(self, listing: Dict) -> Optional[str]:
        """Extract URL from listing data."""
        url_fields = ['url', 'link', 'source_url', 'details_url', 'website']
        for field in url_fields:
            if field in listing and listing[field]:
                return listing[field]
        return None


# Convenience functions for integration
async def process_listing_contacts(listing: Dict, config: Settings, listing_id: Optional[int] = None) -> Tuple[List[Contact], List[ContactForm]]:
    """Quick function to process contacts for a single listing."""
    async with ContactDiscoveryIntegration(config) as integration:
        return await integration.process_listing(listing, listing_id)


async def validate_listing_contacts(listing_id: int, config: Settings, validation_level: str = "standard") -> List[ValidationResult]:
    """Quick function to validate contacts for a listing."""
    async with ContactDiscoveryIntegration(config) as integration:
        return await integration.validate_stored_contacts(listing_id, validation_level)


def get_listing_contacts(listing_id: int, config: Settings, contact_type: Optional[str] = None, min_confidence: Optional[float] = None) -> List[Dict[str, Any]]:
    """Quick function to get contacts for a listing."""
    integration = ContactDiscoveryIntegration(config)
    return integration.get_contacts_for_listing(listing_id, contact_type, min_confidence)