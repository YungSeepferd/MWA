"""
Enhanced data models for contact discovery in MWA Core.

Provides comprehensive data structures for contacts, forms, social media profiles,
and discovery context with advanced metadata and confidence scoring.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Optional, Any, Set
from pathlib import Path
import hashlib
import json


class ContactMethod(Enum):
    """Types of contact methods that can be discovered."""
    EMAIL = "email"
    PHONE = "phone"
    FORM = "form"
    WEBSITE = "website"
    MAILTO = "mailto"
    SOCIAL_MEDIA = "social_media"
    ADDRESS = "address"


class ConfidenceLevel(Enum):
    """Confidence levels for contact discovery methods."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNCERTAIN = "uncertain"


class ContactStatus(Enum):
    """Status of contact verification."""
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    INVALID = "invalid"
    SUSPICIOUS = "suspicious"
    FLAGGED = "flagged"


class SocialMediaPlatform(Enum):
    """Supported social media platforms."""
    FACEBOOK = "facebook"
    INSTAGRAM = "instagram"
    TWITTER = "twitter"
    LINKEDIN = "linkedin"
    WHATSAPP = "whatsapp"
    TELEGRAM = "telegram"
    XING = "xing"


@dataclass
class Contact:
    """
    Represents a discovered contact method with enhanced metadata.
    
    Attributes:
        method: Type of contact method (email, phone, form, etc.)
        value: The actual contact information (email address, phone number, URL, etc.)
        confidence: Confidence level of the discovery
        source_url: URL where the contact was found
        discovery_path: Sequence of URLs followed to reach this contact
        timestamp: When this contact was discovered
        verification_status: Current verification status
        metadata: Additional context about the discovery
        extraction_method: How this contact was extracted
        language: Language of the source content
        cultural_context: Cultural/geographic context for better validation
    """
    method: ContactMethod
    value: str
    confidence: ConfidenceLevel
    source_url: str
    discovery_path: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    verification_status: ContactStatus = ContactStatus.UNVERIFIED
    metadata: Dict[str, Any] = field(default_factory=dict)
    extraction_method: str = "pattern_matching"
    language: str = "unknown"
    cultural_context: str = "general"
    
    def __post_init__(self):
        """Validate and normalize contact data after initialization."""
        # Generate a unique hash for deduplication
        hash_input = f"{self.method.value}:{self.value}:{self.source_url}"
        self.contact_hash = hashlib.sha256(hash_input.encode()).hexdigest()[:16]
        
        # Normalize value based on method
        if self.method == ContactMethod.EMAIL:
            self.value = self.value.lower().strip()
        elif self.method == ContactMethod.PHONE:
            # Remove common phone formatting characters
            import re
            self.value = re.sub(r'[^\d+]', '', self.value)
        elif self.method == ContactMethod.WEBSITE:
            # Normalize URLs
            if not self.value.startswith(('http://', 'https://')):
                self.value = f"https://{self.value}"
    
    @property
    def is_verified(self) -> bool:
        """Check if contact is verified."""
        return self.verification_status == ContactStatus.VERIFIED
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if contact has high confidence level."""
        return self.confidence == ConfidenceLevel.HIGH
    
    @property
    def domain(self) -> Optional[str]:
        """Extract domain from contact value if applicable."""
        if self.method in [ContactMethod.EMAIL, ContactMethod.WEBSITE]:
            if '@' in self.value:
                return self.value.split('@')[1]
            elif self.value.startswith(('http://', 'https://')):
                from urllib.parse import urlparse
                return urlparse(self.value).netloc
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert contact to dictionary for serialization."""
        return {
            "method": self.method.value,
            "value": self.value,
            "confidence": self.confidence.value,
            "source_url": self.source_url,
            "discovery_path": self.discovery_path,
            "timestamp": self.timestamp.isoformat(),
            "verification_status": self.verification_status.value,
            "metadata": self.metadata,
            "extraction_method": self.extraction_method,
            "language": self.language,
            "cultural_context": self.cultural_context,
            "contact_hash": self.contact_hash
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Contact":
        """Create contact from dictionary."""
        # Convert timestamp string back to datetime
        if isinstance(data.get("timestamp"), str):
            data["timestamp"] = datetime.fromisoformat(data["timestamp"])
        
        return cls(
            method=ContactMethod(data["method"]),
            value=data["value"],
            confidence=ConfidenceLevel(data["confidence"]),
            source_url=data["source_url"],
            discovery_path=data.get("discovery_path", []),
            timestamp=data.get("timestamp", datetime.now()),
            verification_status=ContactStatus(data.get("verification_status", "unverified")),
            metadata=data.get("metadata", {}),
            extraction_method=data.get("extraction_method", "pattern_matching"),
            language=data.get("language", "unknown"),
            cultural_context=data.get("cultural_context", "general")
        )


@dataclass
class ContactForm:
    """
    Represents a contact form found on a webpage with enhanced analysis.
    
    Attributes:
        action_url: The form's action URL
        method: HTTP method (GET/POST)
        fields: List of form field names
        required_fields: List of required field names
        csrf_token: CSRF protection token if present
        source_url: URL where the form was found
        confidence: Confidence that this is a usable contact form
        metadata: Additional context about the form
        complexity_score: Complexity rating (0-1)
        user_friendly_score: User-friendliness rating (0-1)
    """
    action_url: str
    method: str = "POST"
    fields: List[str] = field(default_factory=list)
    required_fields: List[str] = field(default_factory=list)
    csrf_token: Optional[str] = None
    source_url: str = ""
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    metadata: Dict[str, Any] = field(default_factory=dict)
    complexity_score: float = 0.5
    user_friendly_score: float = 0.5
    
    def __post_init__(self):
        """Normalize form data after initialization."""
        self.method = self.method.upper()
        if self.method not in ["GET", "POST"]:
            self.method = "POST"  # Default fallback
    
    @property
    def is_simple_form(self) -> bool:
        """Check if this is a simple contact form (few fields)."""
        return len(self.fields) <= 5 and len(self.required_fields) <= 3
    
    @property
    def has_email_field(self) -> bool:
        """Check if form has an email field."""
        email_fields = ['email', 'e-mail', 'mail', 'e_mail', 'email_address']
        return any(field.lower() in email_fields for field in self.fields)
    
    @property
    def has_message_field(self) -> bool:
        """Check if form has a message field."""
        message_fields = ['message', 'nachricht', 'comment', 'text', 'body']
        return any(field.lower() in message_fields for field in self.fields)
    
    def to_contact(self) -> Contact:
        """Convert form to a Contact object."""
        return Contact(
            method=ContactMethod.FORM,
            value=self.action_url,
            confidence=self.confidence,
            source_url=self.source_url,
            metadata={
                "method": self.method,
                "fields": self.fields,
                "required_fields": self.required_fields,
                "csrf_token": self.csrf_token,
                "complexity_score": self.complexity_score,
                "user_friendly_score": self.user_friendly_score,
                **self.metadata
            }
        )


@dataclass
class SocialMediaProfile:
    """
    Represents a social media profile discovered during contact extraction.
    
    Attributes:
        platform: Social media platform
        username: Username or handle
        profile_url: Full profile URL
        display_name: Display name if available
        source_url: URL where the profile was found
        confidence: Confidence level of the discovery
        metadata: Additional context about the profile
    """
    platform: SocialMediaPlatform
    username: str
    profile_url: str
    display_name: Optional[str] = None
    source_url: str = ""
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_business_profile(self) -> bool:
        """Check if this appears to be a business profile."""
        business_indicators = ['business', 'company', 'firm', 'immobilien', 'verwaltung']
        return any(indicator in (self.display_name or '').lower() for indicator in business_indicators)
    
    def to_contact(self) -> Contact:
        """Convert social media profile to a Contact object."""
        return Contact(
            method=ContactMethod.SOCIAL_MEDIA,
            value=self.profile_url,
            confidence=self.confidence,
            source_url=self.source_url,
            metadata={
                "platform": self.platform.value,
                "username": self.username,
                "display_name": self.display_name,
                "is_business_profile": self.is_business_profile,
                **self.metadata
            }
        )


@dataclass
class DiscoveryContext:
    """
    Enhanced context information for contact discovery operations.
    
    Attributes:
        base_url: The original URL being analyzed
        domain: Domain of the base URL
        allowed_domains: List of domains we're allowed to crawl
        max_depth: Maximum crawling depth
        current_depth: Current crawling depth
        respect_robots: Whether to respect robots.txt
        timeout: Request timeout in seconds
        user_agent: User agent string for requests
        language_preference: Preferred language for content
        cultural_context: Cultural/geographic context for better extraction
        extraction_methods: Enabled extraction methods
        confidence_threshold: Minimum confidence threshold
    """
    base_url: str
    domain: str
    allowed_domains: List[str] = field(default_factory=list)
    max_depth: int = 2
    current_depth: int = 0
    respect_robots: bool = True
    timeout: int = 30
    user_agent: str = "MWA-ContactDiscovery/1.0"
    language_preference: str = "de"
    cultural_context: str = "german"
    extraction_methods: List[str] = field(default_factory=lambda: ["email", "phone", "form", "social_media"])
    confidence_threshold: ConfidenceLevel = ConfidenceLevel.LOW
    
    def __post_init__(self):
        """Initialize allowed domains if not provided."""
        if not self.allowed_domains:
            self.allowed_domains = [self.domain]
    
    @property
    def can_crawl_deeper(self) -> bool:
        """Check if we can crawl to a deeper level."""
        return self.current_depth < self.max_depth
    
    def next_depth(self) -> "DiscoveryContext":
        """Create a new context for the next crawling depth."""
        return DiscoveryContext(
            base_url=self.base_url,
            domain=self.domain,
            allowed_domains=self.allowed_domains,
            max_depth=self.max_depth,
            current_depth=self.current_depth + 1,
            respect_robots=self.respect_robots,
            timeout=self.timeout,
            user_agent=self.user_agent,
            language_preference=self.language_preference,
            cultural_context=self.cultural_context,
            extraction_methods=self.extraction_methods,
            confidence_threshold=self.confidence_threshold
        )
    
    def with_language(self, language: str) -> "DiscoveryContext":
        """Create a new context with different language preference."""
        return DiscoveryContext(
            base_url=self.base_url,
            domain=self.domain,
            allowed_domains=self.allowed_domains,
            max_depth=self.max_depth,
            current_depth=self.current_depth,
            respect_robots=self.respect_robots,
            timeout=self.timeout,
            user_agent=self.user_agent,
            language_preference=language,
            cultural_context=self.cultural_context,
            extraction_methods=self.extraction_methods,
            confidence_threshold=self.confidence_threshold
        )


@dataclass
class ExtractionResult:
    """
    Represents the result of a contact extraction operation.
    
    Attributes:
        contacts: List of discovered contacts
        forms: List of discovered contact forms
        social_media_profiles: List of discovered social media profiles
        source_url: URL that was processed
        extraction_time: Time taken for extraction
        confidence_scores: Confidence scores for each extraction method
        metadata: Additional metadata about the extraction
    """
    contacts: List[Contact] = field(default_factory=list)
    forms: List[ContactForm] = field(default_factory=list)
    social_media_profiles: List[SocialMediaProfile] = field(default_factory=list)
    source_url: str = ""
    extraction_time: float = 0.0
    confidence_scores: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def total_contacts(self) -> int:
        """Get total number of contacts found."""
        return len(self.contacts) + len(self.forms) + len(self.social_media_profiles)
    
    @property
    def high_confidence_contacts(self) -> List[Contact]:
        """Get only high confidence contacts."""
        return [c for c in self.contacts if c.confidence == ConfidenceLevel.HIGH]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            "contacts": [c.to_dict() for c in self.contacts],
            "forms": [f.to_contact().to_dict() for f in self.forms],
            "social_media_profiles": [s.to_contact().to_dict() for s in self.social_media_profiles],
            "source_url": self.source_url,
            "extraction_time": self.extraction_time,
            "confidence_scores": self.confidence_scores,
            "metadata": self.metadata,
            "total_contacts": self.total_contacts
        }


@dataclass
class ValidationResult:
    """
    Represents the result of contact validation.
    
    Attributes:
        contact: The contact that was validated
        is_valid: Whether the contact is valid
        validation_method: Method used for validation
        confidence_score: Confidence score of the validation
        validation_metadata: Additional validation metadata
        errors: Any errors encountered during validation
        warnings: Any warnings generated during validation
    """
    contact: Contact
    is_valid: bool
    validation_method: str
    confidence_score: float
    validation_metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert validation result to dictionary."""
        return {
            "contact": self.contact.to_dict(),
            "is_valid": self.is_valid,
            "validation_method": self.validation_method,
            "confidence_score": self.confidence_score,
            "validation_metadata": self.validation_metadata,
            "errors": self.errors,
            "warnings": self.warnings
        }