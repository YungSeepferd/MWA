"""
Contact discovery integration for MAFA scraping workflow.

Provides seamless integration of contact discovery with existing scraping
operations, including automatic contact extraction from listings and
monitoring of discovery performance.
"""

import asyncio
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from urllib.parse import urlparse
import logging
from datetime import datetime

from .extractor import ContactExtractor
from .validator import ContactValidator
from .storage import ContactStorage
from .models import Contact, ContactForm, ContactMethod, ConfidenceLevel, ContactStatus
from ..config.settings import Settings
from ..monitoring import get_metrics_collector
from ..exceptions import ScrapingError

logger = logging.getLogger(__name__)


class ContactDiscoveryIntegration:
    """
    Integrates contact discovery with the existing MAFA scraping workflow.
    
    Provides automatic contact extraction from listings, validation, storage,
    and performance monitoring.
    """
    
    def __init__(self, config: Settings, storage_path: Optional[Path] = None):
        """
        Initialize contact discovery integration.
        
        Args:
            config: Application configuration
            storage_path: Path to contact storage database (optional)
        """
        self.config = config
        self.settings = config.contact_discovery
        self.storage_path = storage_path or Path("data/contacts.db")
        self.storage = ContactStorage(self.storage_path)
        self.extractor = ContactExtractor(config)
        self.validator = ContactValidator(
            enable_smtp_verification=False,  # Safe default for production
            rate_limit=self.settings.rate_limit_seconds
        )
        self.metrics_collector = get_metrics_collector(self.storage_path.parent)
        
        logger.info(f"Contact discovery integration initialized (enabled: {self.settings.enabled})")
    
    async def process_listing(self, listing: Dict, listing_id: Optional[int] = None) -> Tuple[List[Contact], List[ContactForm]]:
        """
        Process a single listing for contact discovery.
        
        Args:
            listing: Listing data dictionary
            listing_id: Associated listing ID from main database (optional)
            
        Returns:
            Tuple of (contacts, forms) discovered from the listing
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
                self._record_extraction_metrics(start_time, False, 0, 0, 0, 0, 0, 0)
                return [], []
            
            # Perform contact discovery
            logger.info(f"Starting contact discovery for: {url}")
            contacts, forms = await self.extractor.discover_contacts(url)
            
            # Validate contacts if enabled
            if self.settings.validation_enabled:
                contacts = await self.validator.validate_contacts(contacts)
            
            # Filter by confidence threshold
            contacts = self._filter_by_confidence(contacts)
            
            # Store contacts and forms
            stored_contacts = self._store_contacts(contacts, listing_id)
            stored_forms = self._store_forms(forms, listing_id)
            
            # Record metrics
            extraction_duration = (datetime.now() - start_time).total_seconds()
            self._record_extraction_metrics(
                start_time, True, len(stored_contacts), 
                sum(1 for c in stored_contacts if c.method == ContactMethod.EMAIL),
                sum(1 for c in stored_contacts if c.method == ContactMethod.PHONE),
                len(stored_forms),
                sum(1 for c in stored_contacts if c.confidence == ConfidenceLevel.HIGH),
                sum(1 for c in stored_contacts if c.verification_status == ContactStatus.INVALID)
            )
            
            logger.info(f"Contact discovery completed for {url}: {len(stored_contacts)} contacts, {len(stored_forms)} forms")
            return stored_contacts, stored_forms
            
        except Exception as e:
            logger.error(f"Contact discovery failed for listing: {str(e)}")
            extraction_duration = (datetime.now() - start_time).total_seconds()
            self._record_extraction_metrics(start_time, False, 0, 0, 0, 0, 0, 0)
            raise ScrapingError(f"Contact discovery failed: {str(e)}")
    
    async def process_listings_batch(self, listings: List[Dict], listing_ids: Optional[List[int]] = None) -> Dict[str, int]:
        """
        Process multiple listings for contact discovery.
        
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
        
        for i, listing in enumerate(listings):
            try:
                listing_id = listing_ids[i] if listing_ids and i < len(listing_ids) else None
                contacts, forms = await self.process_listing(listing, listing_id)
                
                summary["processed"] += 1
                summary["contacts_found"] += len(contacts)
                summary["forms_found"] += len(forms)
                
            except Exception as e:
                logger.error(f"Failed to process listing {i}: {str(e)}")
                summary["errors"] += 1
        
        logger.info(f"Batch contact discovery completed: {summary}")
        return summary
    
    def _extract_listing_url(self, listing: Dict) -> Optional[str]:
        """Extract URL from listing data."""
        # Try different possible URL fields
        url_fields = ['url', 'link', 'source_url', 'details_url']
        for field in url_fields:
            if field in listing and listing[field]:
                return listing[field]
        return None
    
    def _filter_by_confidence(self, contacts: List[Contact]) -> List[Contact]:
        """Filter contacts by confidence threshold."""
        if self.settings.confidence_threshold == "high":
            return [c for c in contacts if c.confidence == ConfidenceLevel.HIGH]
        elif self.settings.confidence_threshold == "medium":
            return [c for c in contacts if c.confidence in [ConfidenceLevel.HIGH, ConfidenceLevel.MEDIUM]]
        else:  # "low" or any other value
            return contacts
    
    def _store_contacts(self, contacts: List[Contact], listing_id: Optional[int]) -> List[Contact]:
        """Store contacts in database."""
        stored_contacts = []
        for contact in contacts:
            if self._should_store_contact(contact):
                if self.storage.store_contact(contact, listing_id):
                    stored_contacts.append(contact)
        return stored_contacts
    
    def _store_forms(self, forms: List[ContactForm], listing_id: Optional[int]) -> List[ContactForm]:
        """Store contact forms in database."""
        stored_forms = []
        for form in forms:
            if self.storage.store_contact_form(form, listing_id):
                stored_forms.append(form)
        return stored_forms
    
    def _should_store_contact(self, contact: Contact) -> bool:
        """Determine if a contact should be stored based on settings."""
        # Check blocked domains for email contacts
        if contact.method == ContactMethod.EMAIL:
            domain = contact.value.split('@')[1] if '@' in contact.value else ''
            if domain in self.settings.blocked_domains:
                logger.debug(f"Skipping contact from blocked domain: {domain}")
                return False
        
        return True
    
    def _record_extraction_metrics(self, start_time: datetime, success: bool, contacts_found: int,
                                 emails: int, phones: int, forms: int, high_confidence: int,
                                 validation_failures: int):
        """Record extraction performance metrics."""
        duration = (datetime.now() - start_time).total_seconds()
        
        self.metrics_collector.record_contact_extraction(
            duration=duration,
            success=success,
            contacts_found=contacts_found,
            emails=emails,
            phones=phones,
            forms=forms,
            high_confidence=high_confidence,
            validation_failures=validation_failures
        )
        
        # Log warnings for concerning metrics
        if contacts_found == 0 and success:
            logger.warning(f"No contacts found in extraction (duration: {duration:.1f}s)")
        
        if validation_failures > contacts_found * 0.5:  # >50% validation failure rate
            logger.warning(f"High validation failure rate: {validation_failures}/{contacts_found}")
    
    def get_contact_stats(self) -> Dict:
        """Get contact discovery statistics."""
        try:
            stats = self.storage.get_contact_statistics()
            return {
                "total_contacts": stats["total_contacts"],
                "contacts_by_method": stats["contacts_by_method"],
                "contacts_by_confidence": stats["contacts_by_confidence"],
                "recent_contacts_7_days": stats["recent_contacts_7_days"],
                "extraction_success_rate": (
                    self.metrics_collector.contact_extractions_success / self.metrics_collector.contact_extractions_total
                    if self.metrics_collector.contact_extractions_total > 0 else 0
                )
            }
        except Exception as e:
            logger.error(f"Failed to get contact stats: {str(e)}")
            return {}
    
    async def cleanup_old_contacts(self, days_old: int = None) -> int:
        """Clean up contacts older than specified days."""
        days = days_old or self.config.storage.contact_retention_days
        try:
            deleted_count = self.storage.cleanup_old_contacts(days)
            logger.info(f"Cleaned up {deleted_count} old contacts (older than {days} days)")
            return deleted_count
        except Exception as e:
            logger.error(f"Contact cleanup failed: {str(e)}")
            return 0


# Convenience function for quick integration
async def process_listing_contacts(listing: Dict, config: Settings, listing_id: Optional[int] = None) -> Tuple[List[Contact], List[ContactForm]]:
    """
    Convenience function to process contacts for a single listing.
    
    Args:
        listing: Listing data dictionary
        config: Application configuration
        listing_id: Associated listing ID (optional)
        
    Returns:
        Tuple of (contacts, forms) discovered from the listing
    """
    integration = ContactDiscoveryIntegration(config)
    return await integration.process_listing(listing, listing_id)