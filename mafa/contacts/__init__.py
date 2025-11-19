"""
Contact discovery module for MAFA.

Provides comprehensive contact information extraction from web pages,
including email addresses, phone numbers, contact forms, and other contact pathways.
"""

from .models import Contact, ContactMethod, ContactForm, DiscoveryContext
from .extractor import ContactExtractor
from .storage import ContactStorage
from .validator import ContactValidator
from .integration import ContactDiscoveryIntegration, process_listing_contacts

__all__ = [
    "ContactExtractor",
    "Contact",
    "ContactMethod",
    "ContactForm",
    "DiscoveryContext",
    "ContactStorage",
    "ContactValidator",
    "ContactDiscoveryIntegration",
    "process_listing_contacts"
]