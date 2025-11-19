"""
Enhanced contact discovery module for MWA Core.

Provides comprehensive contact information extraction from web pages,
including email addresses, phone numbers, contact forms, social media profiles,
and other contact pathways with advanced confidence scoring and validation.
"""

from .discovery import ContactDiscoveryEngine
from .extractors import (
    EmailExtractor,
    PhoneExtractor,
    FormExtractor,
    SocialMediaExtractor,
    OCRContactExtractor,
    PDFContactExtractor
)
from .crawler import ContactCrawler
from .scoring import ContactScoringEngine
from .validators import ContactValidator
from .integration import ContactDiscoveryIntegration
from .models import (
    Contact,
    ContactMethod,
    ContactForm,
    SocialMediaProfile,
    DiscoveryContext,
    ConfidenceLevel,
    ContactStatus
)

__all__ = [
    "ContactDiscoveryEngine",
    "EmailExtractor",
    "PhoneExtractor",
    "FormExtractor",
    "SocialMediaExtractor",
    "OCRContactExtractor",
    "PDFContactExtractor",
    "ContactCrawler",
    "ContactScoringEngine",
    "ContactValidator",
    "ContactDiscoveryIntegration",
    "Contact",
    "ContactMethod",
    "ContactForm",
    "SocialMediaProfile",
    "DiscoveryContext",
    "ConfidenceLevel",
    "ContactStatus"
]