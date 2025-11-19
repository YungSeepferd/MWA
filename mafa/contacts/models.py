"""
Data models for contact discovery.

Defines contact information structures and enums for the contact discovery system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, List, Dict, Any
from pathlib import Path
import hashlib


class ContactMethod(Enum):
    """Types of contact methods that can be discovered."""
    EMAIL = "email"
    PHONE = "phone"
    FORM = "form"
    PAGE = "page"
    MAILTO = "mailto"


class ConfidenceLevel(Enum):
    """Confidence levels for contact discovery methods."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ContactStatus(Enum):
    """Status of contact verification."""
    UNVERIFIED = "unverified"
    VERIFIED = "verified"
    INVALID = "invalid"
    FLAGGED = "flagged"


@dataclass
class Contact:
    """
    Represents a discovered contact method.
    
    Attributes:
        method: Type of contact method (email, phone, form, etc.)
        value: The actual contact information (email address, phone number, URL, etc.)
        confidence: Confidence level of the discovery
        source_url: URL where the contact was found
        discovery_path: Sequence of URLs followed to reach this contact
        timestamp: When this contact was discovered
        verification_status: Current verification status
        metadata: Additional context about the discovery
    """
    method: ContactMethod
    value: str
    confidence: ConfidenceLevel
    source_url: str
    discovery_path: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.now)
    verification_status: ContactStatus = ContactStatus.UNVERIFIED
    metadata: Dict[str, Any] = field(default_factory=dict)
    
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
    
    @property
    def is_verified(self) -> bool:
        """Check if contact is verified."""
        return self.verification_status == ContactStatus.VERIFIED
    
    @property
    def is_high_confidence(self) -> bool:
        """Check if contact has high confidence level."""
        return self.confidence == ConfidenceLevel.HIGH
    
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
            metadata=data.get("metadata", {})
        )


@dataclass
class ContactForm:
    """
    Represents a contact form found on a webpage.
    
    Attributes:
        action_url: The form's action URL
        method: HTTP method (GET/POST)
        fields: List of form field names
        required_fields: List of required field names
        csrf_token: CSRF protection token if present
        source_url: URL where the form was found
        confidence: Confidence that this is a usable contact form
    """
    action_url: str
    method: str = "POST"
    fields: List[str] = field(default_factory=list)
    required_fields: List[str] = field(default_factory=list)
    csrf_token: Optional[str] = None
    source_url: str = ""
    confidence: ConfidenceLevel = ConfidenceLevel.MEDIUM
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Normalize form data after initialization."""
        self.method = self.method.upper()
        if self.method not in ["GET", "POST"]:
            self.method = "POST"  # Default fallback
    
    @property
    def is_simple_form(self) -> bool:
        """Check if this is a simple contact form (few fields)."""
        return len(self.fields) <= 5 and len(self.required_fields) <= 3
    
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
                **self.metadata
            }
        )


@dataclass
class DiscoveryContext:
    """
    Context information for contact discovery operations.
    
    Attributes:
        base_url: The original URL being analyzed
        domain: Domain of the base URL
        allowed_domains: List of domains we're allowed to crawl
        max_depth: Maximum crawling depth
        current_depth: Current crawling depth
        respect_robots: Whether to respect robots.txt
        timeout: Request timeout in seconds
    """
    base_url: str
    domain: str
    allowed_domains: List[str] = field(default_factory=list)
    max_depth: int = 2
    current_depth: int = 0
    respect_robots: bool = True
    timeout: int = 30
    
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
            timeout=self.timeout
        )