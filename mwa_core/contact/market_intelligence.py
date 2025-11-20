"""
Enhanced Market Intelligence Contact Model.

Provides advanced contact management capabilities with market intelligence features
for the Market Intelligence dashboard.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from enum import Enum
import json

from .models import Contact, ContactMethod, ConfidenceLevel, ContactStatus


class AgencyType(Enum):
    """Enumeration for agency types in market intelligence."""
    PROPERTY_MANAGER = "property_manager"
    LANDLORD = "landlord"
    REAL_ESTATE_AGENT = "real_estate_agent"
    OTHER = "other"


class ContactMethod(Enum):
    """Enumeration for preferred contact methods."""
    EMAIL = "email"
    PHONE = "phone"
    SMS = "sms"
    WHATSAPP = "whatsapp"


class LeadSource(Enum):
    """Enumeration for lead sources."""
    WEB_SCRAPING = "web_scraping"
    REFERRAL = "referral"
    PARTNER = "partner"
    MANUAL = "manual"


@dataclass
class OutreachHistoryEntry:
    """Represents an outreach attempt in the contact's history."""
    
    outreach_id: str
    method: ContactMethod
    timestamp: datetime
    status: str  # sent, delivered, opened, responded, etc.
    response: Optional[str] = None
    notes: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "outreach_id": self.outreach_id,
            "method": self.method.value,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status,
            "response": self.response,
            "notes": self.notes
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> OutreachHistoryEntry:
        """Create from dictionary."""
        return cls(
            outreach_id=data["outreach_id"],
            method=ContactMethod(data["method"]),
            timestamp=datetime.fromisoformat(data["timestamp"]),
            status=data["status"],
            response=data.get("response"),
            notes=data.get("notes")
        )


@dataclass
class MarketIntelligenceContact(Contact):
    """
    Enhanced contact model with market intelligence capabilities.
    
    Extends the base Contact model with additional fields for market analysis,
    outreach tracking, and business intelligence.
    """
    
    # Market Intelligence Fields
    position: Optional[str] = None
    company_name: Optional[str] = None
    agency_type: Optional[AgencyType] = None
    market_areas: List[str] = field(default_factory=list)
    outreach_history: List[OutreachHistoryEntry] = field(default_factory=list)
    preferred_contact_method: Optional[ContactMethod] = None
    last_contacted: Optional[datetime] = None
    
    # Enhanced scoring
    confidence_score: float = 0.0
    quality_score: float = 0.0
    
    # Market intelligence flags
    is_active: bool = True
    is_blacklisted: bool = False
    blacklist_reason: Optional[str] = None
    
    # Source and extraction information
    scraped_from_url: Optional[str] = None
    source_provider: Optional[str] = None
    extraction_method: Optional[str] = None
    extraction_confidence: Optional[float] = None
    lead_source: Optional[LeadSource] = None
    
    # Management fields
    tags: List[str] = field(default_factory=list)
    notes: Optional[str] = None
    
    def __post_init__(self):
        """Validate and normalize market intelligence data after initialization."""
        super().__post_init__()
        
        # Validate confidence and quality scores
        if self.confidence_score < 0.0 or self.confidence_score > 1.0:
            raise ValueError("confidence_score must be between 0.0 and 1.0")
        if self.quality_score < 0.0 or self.quality_score > 1.0:
            raise ValueError("quality_score must be between 0.0 and 1.0")
        
        # Normalize market areas
        self.market_areas = [area.strip() for area in self.market_areas if area.strip()]
        
        # Normalize tags
        self.tags = [tag.strip() for tag in self.tags if tag.strip()]
    
    def add_outreach_entry(self, entry: OutreachHistoryEntry) -> None:
        """Add an outreach entry to the history."""
        self.outreach_history.append(entry)
        self.last_contacted = entry.timestamp
    
    def get_recent_outreach(self, days: int = 30) -> List[OutreachHistoryEntry]:
        """Get outreach entries from the last N days."""
        cutoff_date = datetime.now() - timedelta(days=days)
        return [entry for entry in self.outreach_history if entry.timestamp >= cutoff_date]
    
    def calculate_engagement_score(self) -> float:
        """Calculate engagement score based on outreach history."""
        if not self.outreach_history:
            return 0.0
        
        recent_outreach = self.get_recent_outreach(90)  # Last 90 days
        if not recent_outreach:
            return 0.0
        
        # Calculate score based on response rate and frequency
        total_attempts = len(recent_outreach)
        responded_attempts = len([entry for entry in recent_outreach if entry.response])
        
        response_rate = responded_attempts / total_attempts if total_attempts > 0 else 0.0
        frequency_score = min(total_attempts / 10.0, 1.0)  # Cap at 1.0 for 10+ attempts
        
        return (response_rate * 0.7) + (frequency_score * 0.3)
    
    def update_quality_score(self) -> None:
        """Update the quality score based on current data."""
        factors = []
        
        # Data completeness factor
        completeness_score = 0.0
        if self.position and self.company_name:
            completeness_score += 0.3
        if self.agency_type:
            completeness_score += 0.2
        if self.market_areas:
            completeness_score += 0.2
        if self.scraped_from_url:
            completeness_score += 0.1
        if self.tags:
            completeness_score += 0.1
        if self.notes:
            completeness_score += 0.1
        factors.append(completeness_score)
        
        # Engagement factor
        engagement_score = self.calculate_engagement_score()
        factors.append(engagement_score)
        
        # Confidence factor
        factors.append(self.confidence_score)
        
        # Calculate weighted average
        weights = [0.4, 0.3, 0.3]  # Completeness, engagement, confidence
        self.quality_score = sum(f * w for f, w in zip(factors, weights))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert contact to dictionary for serialization."""
        base_dict = super().to_dict()
        
        # Add market intelligence fields
        market_intel_dict = {
            "position": self.position,
            "company_name": self.company_name,
            "agency_type": self.agency_type.value if self.agency_type else None,
            "market_areas": self.market_areas,
            "outreach_history": [entry.to_dict() for entry in self.outreach_history],
            "preferred_contact_method": self.preferred_contact_method.value if self.preferred_contact_method else None,
            "last_contacted": self.last_contacted.isoformat() if self.last_contacted else None,
            "confidence_score": self.confidence_score,
            "quality_score": self.quality_score,
            "is_active": self.is_active,
            "is_blacklisted": self.is_blacklisted,
            "blacklist_reason": self.blacklist_reason,
            "scraped_from_url": self.scraped_from_url,
            "source_provider": self.source_provider,
            "extraction_method": self.extraction_method,
            "extraction_confidence": self.extraction_confidence,
            "lead_source": self.lead_source.value if self.lead_source else None,
            "tags": self.tags,
            "notes": self.notes,
            "engagement_score": self.calculate_engagement_score()
        }
        
        return {**base_dict, **market_intel_dict}
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> MarketIntelligenceContact:
        """Create contact from dictionary."""
        # Extract base contact data
        base_contact = Contact.from_dict(data)
        
        # Extract market intelligence data
        outreach_history = [
            OutreachHistoryEntry.from_dict(entry) 
            for entry in data.get("outreach_history", [])
        ]
        
        return cls(
            # Base contact fields
            method=base_contact.method,
            value=base_contact.value,
            confidence=base_contact.confidence,
            source_url=base_contact.source_url,
            discovery_path=base_contact.discovery_path,
            timestamp=base_contact.timestamp,
            verification_status=base_contact.verification_status,
            metadata=base_contact.metadata,
            extraction_method=base_contact.extraction_method,
            language=base_contact.language,
            cultural_context=base_contact.cultural_context,
            
            # Market intelligence fields
            position=data.get("position"),
            company_name=data.get("company_name"),
            agency_type=AgencyType(data["agency_type"]) if data.get("agency_type") else None,
            market_areas=data.get("market_areas", []),
            outreach_history=outreach_history,
            preferred_contact_method=ContactMethod(data["preferred_contact_method"]) if data.get("preferred_contact_method") else None,
            last_contacted=datetime.fromisoformat(data["last_contacted"]) if data.get("last_contacted") else None,
            confidence_score=data.get("confidence_score", 0.0),
            quality_score=data.get("quality_score", 0.0),
            is_active=data.get("is_active", True),
            is_blacklisted=data.get("is_blacklisted", False),
            blacklist_reason=data.get("blacklist_reason"),
            scraped_from_url=data.get("scraped_from_url"),
            source_provider=data.get("source_provider"),
            extraction_confidence=data.get("extraction_confidence"),
            lead_source=LeadSource(data["lead_source"]) if data.get("lead_source") else None,
            tags=data.get("tags", []),
            notes=data.get("notes")
        )


# Convenience functions for market intelligence operations
def create_market_intelligence_contact(
    contact: Contact,
    position: Optional[str] = None,
    company_name: Optional[str] = None,
    agency_type: Optional[AgencyType] = None,
    market_areas: Optional[List[str]] = None
) -> MarketIntelligenceContact:
    """Create a market intelligence contact from a base contact."""
    return MarketIntelligenceContact(
        method=contact.method,
        value=contact.value,
        confidence=contact.confidence,
        source_url=contact.source_url,
        discovery_path=contact.discovery_path,
        timestamp=contact.timestamp,
        verification_status=contact.verification_status,
        metadata=contact.metadata,
        extraction_method=contact.extraction_method,
        language=contact.language,
        cultural_context=contact.cultural_context,
        position=position,
        company_name=company_name,
        agency_type=agency_type,
        market_areas=market_areas or []
    )