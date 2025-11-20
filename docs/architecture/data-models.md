# Data Models Documentation

## Overview
This document describes the MAFA data models, their relationships, business logic, and validation rules. It provides a comprehensive understanding of how data flows through the system and how entities interact with each other.

---

**Last Updated:** November 19, 2025  
**Version:** 1.0.0  
**Maintainer:** MAFA Data Architecture Team  
**Estimated Reading Time:** 30-35 minutes

---

## Entity Relationship Model

### Core Entity Relationships
```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│    Users    │────▶│   Contacts  │◀────│  Listings   │
│             │     │             │     │             │
│ - Profile   │     │ - Encrypted │     │ - Provider  │
│ - Settings  │     │   Data      │     │ - Details   │
│ - Consent   │     │ - Validation│     │ - Location  │
└─────────────┘     └─────────────┘     └─────────────┘
       │                   │                   │
       │                   │                   │
       ▼                   ▼                   ▼
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│Search       │     │Discovery    │     │Notification │
│Criteria     │────▶│Jobs         │────▶│Channels     │
│             │     │             │     │             │
│ - Location  │     │ - Extraction│     │ - Delivery  │
│ - Filters   │     │ - Validation│     │ - Status    │
│ - Schedule  │     │ - Results   │     │ - Preferences│
└─────────────┘     └─────────────┘     └─────────────┘
```

### Entity Dependency Graph
```
Users (Root)
├── Contacts (1:N)
│   └── Contact Discovery Results (1:N)
├── Search Criteria (1:N)
│   └── Contact Discovery Jobs (1:N)
├── Notifications (1:N)
└── Notification Channels (1:N)

Listings (Independent)
└── Contact Discovery Results (N:1)

System (Global)
├── System Configuration
├── Audit Logs
└── API Rate Limits
```

---

## Core Data Models

### User Model
```python
# mafa/models/user.py
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
from pydantic import BaseModel, EmailStr, Field, validator
import uuid

class UserRole(str, Enum):
    """User roles in the system."""
    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"
    GUEST = "guest"

class UserStatus(str, Enum):
    """User account status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING_VERIFICATION = "pending_verification"

class UserPreferences(BaseModel):
    """User application preferences."""
    language: str = Field(default="de", description="Preferred language code")
    timezone: str = Field(default="Europe/Berlin", description="User timezone")
    currency: str = Field(default="EUR", description="Preferred currency")
    date_format: str = Field(default="DD.MM.YYYY", description="Date display format")
    notifications: Dict[str, bool] = Field(
        default_factory=lambda: {
            "email": True,
            "push": True,
            "sms": False,
            "discord": False,
            "telegram": False
        },
        description="Notification channel preferences"
    )
    privacy: Dict[str, bool] = Field(
        default_factory=lambda: {
            "share_analytics": False,
            "allow_data_export": True,
            "allow_contact_sharing": False
        },
        description="Privacy preferences"
    )
    search_defaults: Dict[str, Any] = Field(
        default_factory=dict,
        description="Default search parameters"
    )

class UserConsent(BaseModel):
    """User consent tracking for GDPR compliance."""
    gdpr_consent: bool = Field(description="General GDPR consent")
    gdpr_consent_date: Optional[datetime] = Field(description="Consent timestamp")
    data_processing_consent: bool = Field(description="Data processing consent")
    marketing_consent: bool = Field(description="Marketing communication consent")
    analytics_consent: bool = Field(description="Analytics tracking consent")
    
    @validator('gdpr_consent_date')
    def validate_consent_date(cls, v, values):
        if values.get('gdpr_consent') and not v:
            raise ValueError('Consent date required when consent is given')
        return v

class User(BaseModel):
    """User entity model."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    email: EmailStr = Field(description="User email address")
    password_hash: str = Field(description="Hashed password")
    first_name: str = Field(min_length=1, max_length=100, description="First name")
    last_name: str = Field(min_length=1, max_length=100, description="Last name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    date_of_birth: Optional[datetime] = Field(None, description="Date of birth")
    gender: Optional[str] = Field(None, description="Gender")
    nationality: Optional[str] = Field(None, max_length=100, description="Nationality")
    
    # Account status and verification
    status: UserStatus = Field(default=UserStatus.PENDING_VERIFICATION)
    role: UserRole = Field(default=UserRole.USER)
    is_active: bool = Field(default=True)
    is_verified: bool = Field(default=False)
    email_verification_token: Optional[str] = Field(None, description="Email verification token")
    password_reset_token: Optional[str] = Field(None, description="Password reset token")
    password_reset_expires: Optional[datetime] = Field(None, description="Password reset expiry")
    
    # Preferences and settings
    preferences: UserPreferences = Field(default_factory=UserPreferences)
    consent: UserConsent = Field(default_factory=UserConsent)
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")
    deleted_at: Optional[datetime] = Field(None, description="Soft deletion timestamp")
    
    # Security and audit
    login_attempts: int = Field(default=0, description="Failed login attempts")
    locked_until: Optional[datetime] = Field(None, description="Account lock expiry")
    two_factor_enabled: bool = Field(default=False, description="2FA status")
    two_factor_secret: Optional[str] = Field(None, description="2FA secret key")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            uuid.UUID: lambda v: str(v)
        }
    
    @property
    def full_name(self) -> str:
        """Get full name."""
        return f"{self.first_name} {self.last_name}"
    
    @property
    def is_account_locked(self) -> bool:
        """Check if account is locked."""
        return self.locked_until and datetime.utcnow() < self.locked_until
    
    def can_login(self) -> bool:
        """Check if user can attempt login."""
        return (self.is_active and 
                not self.is_account_locked and 
                self.status == UserStatus.ACTIVE)
    
    def increment_login_attempts(self) -> None:
        """Increment failed login attempts."""
        self.login_attempts += 1
        # Lock account after 5 failed attempts for 30 minutes
        if self.login_attempts >= 5:
            self.locked_until = datetime.utcnow() + timedelta(minutes=30)
    
    def reset_login_attempts(self) -> None:
        """Reset login attempts on successful login."""
        self.login_attempts = 0
        self.locked_until = None
        self.last_login = datetime.utcnow()

# User validation schemas
class UserCreate(BaseModel):
    """Schema for user creation."""
    email: EmailStr
    password: str = Field(min_length=8, description="Strong password required")
    first_name: str = Field(min_length=1, max_length=100)
    last_name: str = Field(min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    
    @validator('password')
    def validate_password(cls, v):
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        return v

class UserUpdate(BaseModel):
    """Schema for user updates."""
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    preferences: Optional[UserPreferences] = None
    consent: Optional[UserConsent] = None
```

### Contact Model
```python
# mafa/models/contact.py
from datetime import datetime
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid

class ContactType(str, Enum):
    """Types of contacts."""
    LANDLORD = "landlord"
    AGENT = "agent"
    OWNER = "owner"
    PROPERTY_MANAGER = "property_manager"
    CONTACT_PERSON = "contact_person"
    OTHER = "other"

class ContactSource(str, Enum):
    """Sources of contact information."""
    IMMOSCOUT = "immoscout"
    WG_GESUCHT = "wg_gesucht"
    MANUAL = "manual"
    OCR = "ocr"
    PDF = "pdf"
    API = "api"

class ValidationStatus(str, Enum):
    """Contact validation status."""
    PENDING = "pending"
    VALID = "valid"
    INVALID = "invalid"
    UNCERTAIN = "uncertain"
    VERIFIED = "verified"

class ContactQuality(BaseModel):
    """Contact quality metrics."""
    confidence_score: float = Field(ge=0.0, le=1.0, description="Extraction confidence")
    completeness_score: float = Field(ge=0.0, le=1.0, description="Data completeness")
    accuracy_score: float = Field(ge=0.0, le=1.0, description="Data accuracy")
    relevance_score: float = Field(ge=0.0, le=1.0, description="Relevance to user")
    
    @property
    def overall_quality(self) -> float:
        """Calculate overall quality score."""
        return (self.confidence_score * 0.3 + 
                self.completeness_score * 0.3 + 
                self.accuracy_score * 0.2 + 
                self.relevance_score * 0.2)

class ContactData(BaseModel):
    """Encrypted contact information."""
    name: str = Field(description="Contact name")
    phone: Optional[str] = Field(None, description="Phone number (encrypted)")
    email: Optional[str] = Field(None, description="Email address (encrypted)")
    address: Optional[str] = Field(None, description="Address (encrypted)")
    website: Optional[str] = Field(None, description="Website URL")
    company: Optional[str] = Field(None, description="Company name")
    position: Optional[str] = Field(None, description="Job position")
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not re.match(r'^(\+49|0)[1-9][0-9]{1,14}$', v):
            raise ValueError('Invalid German phone number format')
        return v
    
    @validator('email')
    def validate_email(cls, v):
        if v and not re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', v):
            raise ValueError('Invalid email format')
        return v

class Contact(BaseModel):
    """Contact entity model."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID = Field(description="Owning user ID")
    
    # Basic contact information
    name: str = Field(max_length=255, description="Contact name")
    name_variations: List[str] = Field(default_factory=list, description="Alternative names")
    contact_type: ContactType = Field(description="Type of contact")
    source: ContactSource = Field(description="Source of contact information")
    
    # Encrypted contact data
    phone_encrypted: Optional[bytes] = Field(None, description="Encrypted phone")
    email_encrypted: Optional[bytes] = Field(None, description="Encrypted email")
    address_encrypted: Optional[bytes] = Field(None, description="Encrypted address")
    website_encrypted: Optional[bytes] = Field(None, description="Encrypted website")
    
    # Validation and quality
    validation_status: ValidationStatus = Field(default=ValidationStatus.PENDING)
    validation_method: Optional[str] = Field(None, description="Validation method used")
    validation_date: Optional[datetime] = Field(None, description="Validation timestamp")
    validation_notes: Optional[str] = Field(None, description="Validation notes")
    
    # Quality metrics
    quality_metrics: ContactQuality = Field(default_factory=ContactQuality)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    
    # Contact management
    last_contacted: Optional[datetime] = Field(None, description="Last contact date")
    contact_frequency: str = Field(default="never", description="Contact frequency")
    tags: List[str] = Field(default_factory=list, description="Contact tags")
    category: str = Field(default="standard", description="Contact category")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    # Status and flags
    is_active: bool = Field(default=True, description="Contact active status")
    is_verified: bool = Field(default=False, description="Verification status")
    is_blacklisted: bool = Field(default=False, description="Blacklist status")
    blacklisted_reason: Optional[str] = Field(None, description="Blacklist reason")
    
    # Extraction metadata
    extraction_method: str = Field(description="Extraction method used")
    extraction_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    source_listing_id: Optional[uuid.UUID] = Field(None, description="Source listing ID")
    extraction_date: datetime = Field(default_factory=datetime.utcnow)
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[uuid.UUID] = Field(None, description="Creator user ID")
    updated_by: Optional[uuid.UUID] = Field(None, description="Last updater user ID")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            uuid.UUID: lambda v: str(v)
        }
    
    @property
    def display_name(self) -> str:
        """Get display name for contact."""
        return self.name
    
    @property
    def is_high_quality(self) -> bool:
        """Check if contact meets high quality threshold."""
        return self.quality_score >= 0.8
    
    @property
    def needs_validation(self) -> bool:
        """Check if contact needs validation."""
        return (self.validation_status == ValidationStatus.PENDING or
                self.validation_status == ValidationStatus.UNCERTAIN)
    
    def update_quality_score(self) -> None:
        """Update quality score based on metrics."""
        self.quality_score = self.quality_metrics.overall_quality
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the contact."""
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the contact."""
        if tag in self.tags:
            self.tags.remove(tag)
    
    def blacklist(self, reason: str) -> None:
        """Blacklist the contact."""
        self.is_blacklisted = True
        self.blacklisted_reason = reason
    
    def unblacklist(self) -> None:
        """Remove contact from blacklist."""
        self.is_blacklisted = False
        self.blacklisted_reason = None

# Contact schemas
class ContactCreate(BaseModel):
    """Schema for creating contacts."""
    name: str = Field(min_length=1, max_length=255)
    contact_type: ContactType
    source: ContactSource
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None)
    address: Optional[str] = Field(None)
    website: Optional[str] = Field(None)
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = Field(None)
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not re.match(r'^(\+49|0)[1-9][0-9]{1,14}$', v):
            raise ValueError('Invalid German phone number format')
        return v

class ContactUpdate(BaseModel):
    """Schema for updating contacts."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    contact_type: Optional[ContactType] = None
    phone: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None)
    address: Optional[str] = Field(None)
    website: Optional[str] = Field(None)
    tags: Optional[List[str]] = None
    notes: Optional[str] = Field(None)
    is_active: Optional[bool] = None
    is_blacklisted: Optional[bool] = None
    blacklisted_reason: Optional[str] = Field(None)

class ContactValidation(BaseModel):
    """Schema for contact validation."""
    validation_status: ValidationStatus
    validation_method: str = Field(description="Method used for validation")
    validation_notes: Optional[str] = Field(None, description="Validation notes")
    confidence_adjustment: float = Field(default=0.0, ge=-0.5, le=0.5)
```

### Listing Model
```python
# mafa/models/listing.py
from datetime import datetime, date
from typing import Optional, List, Dict, Any, Union
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid

class PropertyType(str, Enum):
    """Types of properties."""
    APARTMENT = "apartment"
    HOUSE = "house"
    ROOM = "room"
    STUDIO = "studio"
    LOFT = "loft"
    PENTHOUSE = "penthouse"
    OTHER = "other"

class FurnishingLevel(str, Enum):
    """Furnishing levels."""
    FURNISHED = "furnished"
    PARTIALLY_FURNISHED = "partially_furnished"
    UNFURNISHED = "unfurnished"
    MOVE_IN_READY = "move_in_ready"

class PropertyCondition(str, Enum):
    """Property conditions."""
    NEW = "new"
    RENOVATED = "renovated"
    GOOD = "good"
    NEEDS_RENOVATION = "needs_renovation"
    OLD = "old"

class ListingStatus(str, Enum):
    """Listing status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    RENTED = "rented"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"

class Location(BaseModel):
    """Property location data."""
    street: Optional[str] = Field(None, description="Street address")
    house_number: Optional[str] = Field(None, description="House number")
    postal_code: Optional[str] = Field(None, description="Postal code")
    city: str = Field(description="City")
    district: Optional[str] = Field(None, description="District/Neighborhood")
    latitude: Optional[float] = Field(None, ge=-90, le=90, description="Latitude")
    longitude: Optional[float] = Field(None, ge=-180, le=180, description="Longitude")
    
    @property
    def full_address(self) -> str:
        """Get full address string."""
        parts = []
        if self.street:
            parts.append(self.street)
        if self.house_number:
            parts.append(str(self.house_number))
        if self.postal_code:
            parts.append(self.postal_code)
        if self.city:
            parts.append(self.city)
        return " ".join(parts)
    
    @property
    def coordinates(self) -> Optional[tuple]:
        """Get coordinates as tuple."""
        if self.latitude and self.longitude:
            return (self.latitude, self.longitude)
        return None

class FinancialDetails(BaseModel):
    """Financial information for property."""
    rent_netto: Optional[float] = Field(None, ge=0, description="Net rent")
    rent_brutto: Optional[float] = Field(None, ge=0, description="Gross rent")
    additional_costs: Optional[float] = Field(None, ge=0, description="Additional costs")
    deposit: Optional[float] = Field(None, ge=0, description="Security deposit")
    currency: str = Field(default="EUR", description="Currency")
    
    @validator('additional_costs')
    def validate_additional_costs(cls, v, values):
        if v and v < 0:
            raise ValueError('Additional costs cannot be negative')
        return v
    
    @property
    def total_monthly_cost(self) -> Optional[float]:
        """Calculate total monthly cost."""
        if self.rent_brutto and self.additional_costs:
            return self.rent_brutto + self.additional_costs
        return self.rent_brutto

class PropertySpecs(BaseModel):
    """Property specifications."""
    rooms: Optional[float] = Field(None, gt=0, description="Number of rooms")
    bedroom_count: Optional[int] = Field(None, ge=0, description="Bedroom count")
    bathroom_count: Optional[int] = Field(None, ge=0, description="Bathroom count")
    living_area: Optional[float] = Field(None, gt=0, description="Living area in m²")
    total_area: Optional[float] = Field(None, gt=0, description="Total area in m²")
    floor: Optional[str] = Field(None, description="Floor number/name")
    total_floors: Optional[int] = Field(None, ge=0, description="Total floors in building")
    year_built: Optional[int] = Field(None, ge=1800, le=datetime.now().year, description="Year built")
    has_balcony: bool = Field(default=False, description="Balcony available")
    has_terrace: bool = Field(default=False, description="Terrace available")
    has_garden: bool = Field(default=False, description="Garden available")
    has_parking: bool = Field(default=False, description="Parking available")

class Availability(BaseModel):
    """Property availability information."""
    available_from: Optional[date] = Field(None, description="Available from date")
    available_until: Optional[date] = Field(None, description="Available until date")
    lease_duration_min: Optional[int] = Field(None, ge=1, description="Minimum lease duration in months")
    lease_duration_max: Optional[int] = Field(None, ge=1, description="Maximum lease duration in months")
    
    @validator('lease_duration_max')
    def validate_lease_duration(cls, v, values):
        if v and 'lease_duration_min' in values and values['lease_duration_min']:
            if v < values['lease_duration_min']:
                raise ValueError('Maximum lease duration cannot be less than minimum')
        return v
    
    @property
    def is_available_now(self) -> bool:
        """Check if property is available now."""
        if not self.available_from:
            return True
        return date.today() >= self.available_from
    
    @property
    def availability_period(self) -> Optional[str]:
        """Get availability period description."""
        if not self.available_from:
            return "Immediately available"
        
        if self.available_until:
            return f"{self.available_from} to {self.available_until}"
        return f"Available from {self.available_from}"

class MediaContent(BaseModel):
    """Media content associated with listing."""
    images: List[str] = Field(default_factory=list, description="Image URLs")
    virtual_tour_url: Optional[str] = Field(None, description="Virtual tour URL")
    floor_plan_url: Optional[str] = Field(None, description="Floor plan URL")
    video_urls: List[str] = Field(default_factory=list, description="Video URLs")
    
    @validator('images')
    def validate_images(cls, v):
        for url in v:
            if not url.startswith(('http://', 'https://')):
                raise ValueError('All image URLs must be valid HTTP/HTTPS URLs')
        return v
    
    @validator('virtual_tour_url', 'floor_plan_url')
    def validate_urls(cls, v):
        if v and not v.startswith(('http://', 'https://')):
            raise ValueError('URLs must be valid HTTP/HTTPS URLs')
        return v

class ListingQuality(BaseModel):
    """Listing quality metrics."""
    data_completeness: float = Field(default=0.0, ge=0.0, le=1.0)
    information_accuracy: float = Field(default=0.0, ge=0.0, le=1.0)
    media_quality: float = Field(default=0.0, ge=0.0, le=1.0)
    description_quality: float = Field(default=0.0, ge=0.0, le=1.0)
    
    @property
    def overall_score(self) -> float:
        """Calculate overall quality score."""
        return (self.data_completeness * 0.3 + 
                self.information_accuracy * 0.3 + 
                self.media_quality * 0.2 + 
                self.description_quality * 0.2)

class Listing(BaseModel):
    """Real estate listing entity model."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    
    # Provider information
    provider: str = Field(description="Data provider")
    provider_listing_id: str = Field(description="Provider's listing ID")
    provider_url: Optional[str] = Field(None, description="Provider listing URL")
    provider_created_at: Optional[datetime] = Field(None, description="Provider creation time")
    provider_updated_at: Optional[datetime] = Field(None, description="Provider update time")
    
    # Property details
    title: str = Field(max_length=500, description="Listing title")
    description: Optional[str] = Field(None, description="Property description")
    property_type: PropertyType = Field(description="Type of property")
    furnishing_level: Optional[FurnishingLevel] = Field(None, description="Furnishing level")
    condition: Optional[PropertyCondition] = Field(None, description="Property condition")
    
    # Location and address
    location: Location = Field(description="Property location")
    
    # Financial information
    financial: FinancialDetails = Field(default_factory=FinancialDetails)
    
    # Property specifications
    specs: PropertySpecs = Field(default_factory=PropertySpecs)
    
    # Availability
    availability: Availability = Field(default_factory=Availability)
    
    # Media content
    media: MediaContent = Field(default_factory=MediaContent)
    
    # Contact information (denormalized for quick access)
    contact_name: Optional[str] = Field(None, description="Contact person name")
    contact_phone_encrypted: Optional[bytes] = Field(None, description="Encrypted contact phone")
    contact_email_encrypted: Optional[bytes] = Field(None, description="Encrypted contact email")
    
    # Processing status
    is_processed: bool = Field(default=False, description="Processing status")
    processing_errors: List[str] = Field(default_factory=list, description="Processing errors")
    last_processed_at: Optional[datetime] = Field(None, description="Last processing time")
    
    # Quality metrics
    quality_metrics: ListingQuality = Field(default_factory=ListingQuality)
    listing_quality_score: float = Field(default=0.0, ge=0.0, le=1.0)
    relevance_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Relevance to user searches")
    
    # Status flags
    status: ListingStatus = Field(default=ListingStatus.ACTIVE)
    is_active: bool = Field(default=True, description="Active status")
    is_archived: bool = Field(default=False, description="Archived status")
    is_favorite: bool = Field(default=False, description="User favorite status")
    
    # Audit timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    first_seen_at: datetime = Field(default_factory=datetime.utcnow)
    last_seen_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            uuid.UUID: lambda v: str(v)
        }
    
    @property
    def full_address(self) -> str:
        """Get full address."""
        return self.location.full_address
    
    @property
    def coordinates(self) -> Optional[tuple]:
        """Get coordinates."""
        return self.location.coordinates
    
    @property
    def monthly_cost(self) -> Optional[float]:
        """Get total monthly cost."""
        return self.financial.total_monthly_cost
    
    @property
    def is_available(self) -> bool:
        """Check if property is currently available."""
        return (self.status == ListingStatus.ACTIVE and 
                self.is_active and 
                self.availability.is_available_now)
    
    @property
    def has_contact_info(self) -> bool:
        """Check if contact information is available."""
        return any([self.contact_name, self.contact_phone_encrypted, self.contact_email_encrypted])
    
    def update_quality_score(self) -> None:
        """Update quality score based on metrics."""
        self.listing_quality_score = self.quality_metrics.overall_score
    
    def mark_as_processed(self, success: bool = True, errors: List[str] = None) -> None:
        """Mark listing as processed."""
        self.is_processed = success
        self.last_processed_at = datetime.utcnow()
        if errors:
            self.processing_errors = errors
    
    def archive(self) -> None:
        """Archive the listing."""
        self.is_archived = True
        self.status = ListingStatus.WITHDRAWN
    
    def unarchive(self) -> None:
        """Unarchive the listing."""
        self.is_archived = False
        if self.is_active:
            self.status = ListingStatus.ACTIVE

# Listing schemas
class ListingCreate(BaseModel):
    """Schema for creating listings."""
    provider: str
    provider_listing_id: str
    title: str
    description: Optional[str] = None
    property_type: PropertyType
    location: Location
    financial: FinancialDetails
    specs: PropertySpecs
    availability: Availability
    media: Optional[MediaContent] = None
    contact_name: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "provider": "immoscout",
                "provider_listing_id": "12345",
                "title": "Beautiful 3-room apartment in Munich",
                "description": "Spacious apartment with balcony...",
                "property_type": "apartment",
                "location": {
                    "street": "Musterstraße",
                    "house_number": "123",
                    "postal_code": "80331",
                    "city": "München",
                    "district": "Altstadt"
                },
                "financial": {
                    "rent_netto": 1200.00,
                    "additional_costs": 200.00,
                    "deposit": 2400.00
                },
                "specs": {
                    "rooms": 3.0,
                    "living_area": 75.5,
                    "floor": "2",
                    "has_balcony": True
                },
                "availability": {
                    "available_from": "2025-01-01",
                    "lease_duration_min": 12
                }
            }
        }

class ListingUpdate(BaseModel):
    """Schema for updating listings."""
    title: Optional[str] = None
    description: Optional[str] = None
    property_type: Optional[PropertyType] = None
    location: Optional[Location] = None
    financial: Optional[FinancialDetails] = None
    specs: Optional[PropertySpecs] = None
    availability: Optional[Availability] = None
    media: Optional[MediaContent] = None
    is_active: Optional[bool] = None
    is_favorite: Optional[bool] = None

class ListingSearch(BaseModel):
    """Schema for searching listings."""
    # Location filters
    cities: List[str] = Field(default_factory=list, description="Preferred cities")
    districts: List[str] = Field(default_factory=list, description="Preferred districts")
    max_distance: Optional[int] = Field(None, description="Max distance from city center")
    
    # Property filters
    property_types: List[PropertyType] = Field(default_factory=list, description="Property types")
    min_rooms: Optional[float] = Field(None, gt=0, description="Minimum rooms")
    max_rooms: Optional[float] = Field(None, gt=0, description="Maximum rooms")
    min_area: Optional[float] = Field(None, gt=0, description="Minimum area")
    max_area: Optional[float] = Field(None, gt=0, description="Maximum area")
    
    # Financial filters
    min_rent_netto: Optional[float] = Field(None, ge=0, description="Minimum rent")
    max_rent_netto: Optional[float] = Field(None, ge=0, description="Maximum rent")
    max_additional_costs: Optional[float] = Field(None, ge=0, description="Max additional costs")
    max_deposit: Optional[float] = Field(None, ge=0, description="Maximum deposit")
    
    # Availability filters
    available_from: Optional[date] = Field(None, description="Available from date")
    min_lease_duration: Optional[int] = Field(None, ge=1, description="Min lease duration")
    
    # Quality filters
    min_quality_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Min quality score")
    require_contact_info: bool = Field(default=False, description="Must have contact info")
    
    # Pagination and sorting
    page: int = Field(default=1, ge=1, description="Page number")
    limit: int = Field(default=20, ge=1, le=100, description="Items per page")
    sort_by: str = Field(default="created_at", description="Sort field")
    sort_order: str = Field(default="desc", description="Sort order")
    
    @validator('max_rooms')
    def validate_rooms(cls, v, values):
        if v and 'min_rooms' in values and values['min_rooms'] and v < values['min_rooms']:
            raise ValueError('Maximum rooms cannot be less than minimum rooms')
        return v
    
    @validator('max_area')
    def validate_area(cls, v, values):
        if v and 'min_area' in values and values['min_area'] and v < values['min_area']:
            raise ValueError('Maximum area cannot be less than minimum area')
        return v
```

---

## Search and Discovery Models

### Search Criteria Model
```python
# mafa/models/search_criteria.py
from datetime import datetime, date
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field
import uuid

class SearchFrequency(str, Enum):
    """Search execution frequency."""
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MANUAL = "manual"

class LocationCriteria(BaseModel):
    """Location-based search criteria."""
    preferred_cities: List[str] = Field(default_factory=list, description="Preferred cities")
    preferred_districts: List[str] = Field(default_factory=list, description="Preferred districts")
    excluded_cities: List[str] = Field(default_factory=list, description="Cities to avoid")
    excluded_districts: List[str] = Field(default_factory=list, description="Districts to avoid")
    max_distance_km: int = Field(default=50, description="Max distance from preferred locations")
    
    @property
    def has_location_preferences(self) -> bool:
        """Check if location preferences are defined."""
        return bool(self.preferred_cities or self.preferred_districts)

class PropertyCriteria(BaseModel):
    """Property-based search criteria."""
    property_types: List[PropertyType] = Field(
        default_factory=lambda: [PropertyType.APARTMENT],
        description="Allowed property types"
    )
    min_rooms: Optional[float] = Field(None, gt=0, description="Minimum rooms")
    max_rooms: Optional[float] = Field(None, gt=0, description="Maximum rooms")
    min_area: Optional[float] = Field(None, gt=0, description="Minimum area")
    max_area: Optional[float] = Field(None, gt=0, description="Maximum area")
    min_floor: Optional[int] = Field(None, ge=0, description="Minimum floor")
    max_floor: Optional[int] = Field(None, ge=0, description="Maximum floor")
    required_features: List[str] = Field(
        default_factory=list,
        description="Required features (balcony, parking, etc.)"
    )

class FinancialCriteria(BaseModel):
    """Financial search criteria."""
    min_rent_netto: Optional[float] = Field(None, ge=0, description="Minimum rent")
    max_rent_netto: Optional[float] = Field(None, ge=0, description="Maximum rent")
    max_additional_costs: Optional[float] = Field(None, ge=0, description="Max additional costs")
    max_deposit: Optional[float] = Field(None, ge=0, description="Maximum deposit")
    max_total_monthly_cost: Optional[float] = Field(None, ge=0, description="Max total monthly cost")

class AvailabilityCriteria(BaseModel):
    """Availability-based search criteria."""
    available_from: Optional[date] = Field(None, description="Available from date")
    available_until: Optional[date] = Field(None, description="Available until date")
    min_lease_duration: Optional[int] = Field(None, ge=1, description="Min lease duration")
    max_lease_duration: Optional[int] = Field(None, ge=1, description="Max lease duration")

class QualityCriteria(BaseModel):
    """Quality-based search criteria."""
    min_quality_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Min quality score")
    require_verified_contact: bool = Field(default=False, description="Must have verified contact")
    require_complete_info: bool = Field(default=False, description="Must have complete information")
    min_data_completeness: float = Field(default=0.0, ge=0.0, le=1.0, description="Min data completeness")

class SearchCriteria(BaseModel):
    """Search criteria entity model."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID = Field(description="Owning user ID")
    name: str = Field(max_length=255, description="Search criteria name")
    description: Optional[str] = Field(None, description="Search description")
    
    # Search parameters
    location: LocationCriteria = Field(default_factory=LocationCriteria)
    property: PropertyCriteria = Field(default_factory=PropertyCriteria)
    financial: FinancialCriteria = Field(default_factory=FinancialCriteria)
    availability: AvailabilityCriteria = Field(default_factory=AvailabilityCriteria)
    quality: QualityCriteria = Field(default_factory=QualityCriteria)
    
    # Search execution
    search_frequency: SearchFrequency = Field(default=SearchFrequency.DAILY)
    last_run_at: Optional[datetime] = Field(None, description="Last execution time")
    next_run_at: Optional[datetime] = Field(None, description="Next execution time")
    
    # Status and automation
    is_active: bool = Field(default=True, description="Active status")
    auto_apply: bool = Field(default=False, description="Auto-apply to new matches")
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Search tags")
    notes: Optional[str] = Field(None, description="Additional notes")
    
    # Results tracking
    total_runs: int = Field(default=0, description="Total execution count")
    total_matches: int = Field(default=0, description="Total matches found")
    last_match_count: int = Field(default=0, description="Last run match count")
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[uuid.UUID] = Field(None, description="Creator user ID")
    updated_by: Optional[uuid.UUID] = Field(None, description="Last updater user ID")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            uuid.UUID: lambda v: str(v)
        }
    
    @property
    def is_due_for_execution(self) -> bool:
        """Check if search is due for execution."""
        if not self.is_active or self.search_frequency == SearchFrequency.MANUAL:
            return False
        
        if not self.next_run_at:
            return True
        
        return datetime.utcnow() >= self.next_run_at
    
    @property
    def execution_summary(self) -> Dict[str, Any]:
        """Get execution summary."""
        return {
            "total_runs": self.total_runs,
            "total_matches": self.total_matches,
            "last_run": self.last_run_at,
            "last_match_count": self.last_match_count,
            "is_due": self.is_due_for_execution,
            "next_run": self.next_run_at
        }
    
    def calculate_next_run(self) -> None:
        """Calculate next execution time based on frequency."""
        if self.search_frequency == SearchFrequency.MANUAL:
            self.next_run_at = None
        elif self.search_frequency == SearchFrequency.HOURLY:
            self.next_run_at = datetime.utcnow() + timedelta(hours=1)
        elif self.search_frequency == SearchFrequency.DAILY:
            self.next_run_at = datetime.utcnow() + timedelta(days=1)
        elif self.search_frequency == SearchFrequency.WEEKLY:
            self.next_run_at = datetime.utcnow() + timedelta(weeks=1)
    
    def update_execution_stats(self, match_count: int) -> None:
        """Update execution statistics."""
        self.total_runs += 1
        self.total_matches += match_count
        self.last_match_count = match_count
        self.last_run_at = datetime.utcnow()
        self.calculate_next_run()
    
    def add_tag(self, tag: str) -> None:
        """Add a tag to the search criteria."""
        if tag not in self.tags:
            self.tags.append(tag)
    
    def remove_tag(self, tag: str) -> None:
        """Remove a tag from the search criteria."""
        if tag in self.tags:
            self.tags.remove(tag)

# Search criteria schemas
class SearchCriteriaCreate(BaseModel):
    """Schema for creating search criteria."""
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(None)
    location: LocationCriteria
    property: PropertyCriteria
    financial: FinancialCriteria
    availability: AvailabilityCriteria
    quality: QualityCriteria
    search_frequency: SearchFrequency = SearchFrequency.DAILY
    auto_apply: bool = False
    tags: List[str] = Field(default_factory=list)
    notes: Optional[str] = Field(None)

class SearchCriteriaUpdate(BaseModel):
    """Schema for updating search criteria."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None)
    location: Optional[LocationCriteria] = None
    property: Optional[PropertyCriteria] = None
    financial: Optional[FinancialCriteria] = None
    availability: Optional[AvailabilityCriteria] = None
    quality: Optional[QualityCriteria] = None
    search_frequency: Optional[SearchFrequency] = None
    auto_apply: Optional[bool] = None
    is_active: Optional[bool] = None
    tags: Optional[List[str]] = None
    notes: Optional[str] = Field(None)
```

### Contact Discovery Models
```python
# mafa/models/contact_discovery.py
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from enum import Enum
from pydantic import BaseModel, Field, validator
import uuid

class JobType(str, Enum):
    """Types of contact discovery jobs."""
    LISTING_SCRAPE = "listing_scrape"
    CONTACT_EXTRACTION = "contact_extraction"
    VALIDATION = "validation"
    BATCH_PROCESS = "batch_process"
    REAL_TIME = "real_time"

class JobStatus(str, Enum):
    """Job execution status."""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

class ExtractionMethod(str, Enum):
    """Contact extraction methods."""
    OCR = "ocr"
    PDF = "pdf"
    API = "api"
    WEB_SCRAPING = "web_scraping"
    MANUAL = "manual"

class JobConfiguration(BaseModel):
    """Configuration for discovery jobs."""
    # Provider settings
    providers: List[str] = Field(default_factory=list, description="Enabled providers")
    rate_limit: int = Field(default=60, description="Requests per minute")
    timeout_seconds: int = Field(default=30, description="Request timeout")
    max_retries: int = Field(default=3, description="Max retry attempts")
    
    # Extraction settings
    extraction_methods: List[ExtractionMethod] = Field(
        default_factory=lambda: [ExtractionMethod.OCR, ExtractionMethod.PDF],
        description="Enabled extraction methods"
    )
    confidence_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Min confidence")
    validation_required: bool = Field(default=True, description="Validation required")
    
    # Quality settings
    min_quality_score: float = Field(default=0.5, ge=0.0, le=1.0, description="Min quality score")
    deduplication_enabled: bool = Field(default=True, description="Enable deduplication")
    blacklist_enabled: bool = Field(default=True, description="Enable blacklist filtering")
    
    # Output settings
    output_format: str = Field(default="json", description="Output format")
    save_raw_data: bool = Field(default=True, description="Save raw extracted data")
    generate_report: bool = Field(default=True, description="Generate processing report")

class JobProgress(BaseModel):
    """Job progress tracking."""
    current_stage: str = Field(description="Current processing stage")
    progress_percentage: float = Field(default=0.0, ge=0.0, le=100.0, description="Progress percentage")
    items_processed: int = Field(default=0, description="Items processed")
    items_total: int = Field(default=0, description="Total items")
    estimated_time_remaining: Optional[int] = Field(None, description="Estimated seconds remaining")
    
    @property
    def is_complete(self) -> bool:
        """Check if job is complete."""
        return self.progress_percentage >= 100.0
    
    @property
    def processing_rate(self) -> Optional[float]:
        """Get processing rate (items per second)."""
        if self.items_processed > 0:
            return self.items_processed / max(1, (datetime.utcnow() - self.start_time).total_seconds())
        return None

class JobResults(BaseModel):
    """Job execution results."""
    listings_processed: int = Field(default=0, description="Listings processed")
    contacts_extracted: int = Field(default=0, description="Contacts extracted")
    contacts_validated: int = Field(default=0, description="Contacts validated")
    contacts_duplicated: int = Field(default=0, description="Duplicates found")
    contacts_blacklisted: int = Field(default=0, description="Blacklisted contacts")
    
    # Quality metrics
    extraction_accuracy: float = Field(default=0.0, ge=0.0, le=1.0, description="Extraction accuracy")
    validation_success_rate: float = Field(default=0.0, ge=0.0, le=1.0, description="Validation success rate")
    
    # Error statistics
    errors_count: int = Field(default=0, description="Total errors")
    error_types: Dict[str, int] = Field(default_factory=dict, description="Errors by type")
    warnings_count: int = Field(default=0, description="Total warnings")
    
    # Output files
    output_files: List[str] = Field(default_factory=list, description="Generated output files")
    report_url: Optional[str] = Field(None, description="Processing report URL")
    
    @property
    def success_rate(self) -> float:
        """Calculate overall success rate."""
        total_operations = self.listings_processed + self.contacts_extracted
        if total_operations == 0:
            return 0.0
        successful_operations = total_operations - self.errors_count
        return successful_operations / total_operations

class ContactDiscoveryJob(BaseModel):
    """Contact discovery job entity model."""
    id: uuid.UUID = Field(default_factory=uuid.uuid4)
    user_id: uuid.UUID = Field(description="Owning user ID")
    search_criteria_id: Optional[uuid.UUID] = Field(None, description="Associated search criteria")
    
    # Job identification
    job_type: JobType = Field(description="Type of job")
    status: JobStatus = Field(default=JobStatus.PENDING, description="Job status")
    name: str = Field(description="Job name")
    description: Optional[str] = Field(None, description="Job description")
    
    # Configuration
    configuration: JobConfiguration = Field(default_factory=JobConfiguration)
    provider_config: Dict[str, Any] = Field(default_factory=dict, description="Provider-specific config")
    
    # Progress tracking
    progress: JobProgress = Field(default_factory=JobProgress)
    started_at: Optional[datetime] = Field(None, description="Start time")
    completed_at: Optional[datetime] = Field(None, description="Completion time")
    estimated_duration: Optional[int] = Field(None, description="Estimated duration in seconds")
    actual_duration: Optional[int] = Field(None, description="Actual duration in seconds")
    
    # Results
    results: JobResults = Field(default_factory=JobResults)
    result_data: Optional[Dict[str, Any]] = Field(None, description="Structured result data")
    
    # Error handling
    error_messages: List[str] = Field(default_factory=list, description="Error messages")
    warnings: List[str] = Field(default_factory=list, description="Warning messages")
    retry_count: int = Field(default=0, description="Retry attempts")
    max_retries: int = Field(default=3, description="Max retry attempts")
    
    # Status flags
    is_cancelled: bool = Field(default=False, description="Cancellation status")
    can_retry: bool = Field(default=True, description="Retry allowed")
    requires_attention: bool = Field(default=False, description="Manual attention required")
    
    # Audit
    created_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[uuid.UUID] = Field(None, description="Creator user ID")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat(),
            uuid.UUID: lambda v: str(v)
        }
    
    @property
    def is_running(self) -> bool:
        """Check if job is currently running."""
        return self.status == JobStatus.RUNNING
    
    @property
    def is_finished(self) -> bool:
        """Check if job has finished (success or failure)."""
        return self.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED, JobStatus.TIMEOUT]
    
    @property
    def is_successful(self) -> bool:
        """Check if job completed successfully."""
        return self.status == JobStatus.COMPLETED
    
    @property
    def execution_time(self) -> Optional[int]:
        """Get actual execution time in seconds."""
        if self.started_at and self.completed_at:
            return int((self.completed_at - self.started_at).total_seconds())
        return None
    
    def start(self) -> None:
        """Start job execution."""
        if self.status != JobStatus.PENDING:
            raise ValueError("Job cannot be started from current status")
        
        self.status = JobStatus.RUNNING
        self.started_at = datetime.utcnow()
        self.progress.current_stage = "initializing"
    
    def complete(self, results: JobResults) -> None:
        """Mark job as completed."""
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.results = results
        self.progress.progress_percentage = 100.0
        self.progress.current_stage = "completed"
        self.actual_duration = self.execution_time
    
    def fail(self, error_message: str) -> None:
        """Mark job as failed."""
        self.status = JobStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_messages.append(error_message)
        self.progress.current_stage = "failed"
        self.actual_duration = self.execution_time
    
    def cancel(self) -> None:
        """Cancel job execution."""
        if self.status == JobStatus.RUNNING:
            self.status = JobStatus.CANCELLED
            self.is_cancelled = True
            self.completed_at = datetime.utcnow()
            self.progress.current_stage = "cancelled"
        else:
            raise ValueError("Only running jobs can be cancelled")
    
    def add_warning(self, warning: str) -> None:
        """Add a warning message."""
        self.warnings.append(warning)
        self.results.warnings_count += 1
    
    def add_error(self, error: str) -> None:
        """Add an error message."""
        self.error_messages.append(error)
        self.results.errors_count += 1
    
    def update_progress(self, stage: str, percentage: float, items_processed: int = None) -> None:
        """Update job progress."""
        self.progress.current_stage = stage
        self.progress.progress_percentage = min(100.0, max(0.0, percentage))
        if items_processed is not None:
            self.progress.items_processed = items_processed

# Discovery job schemas
class ContactDiscoveryJobCreate(BaseModel):
    """Schema for creating discovery jobs."""
    job_type: JobType
    name: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(None)
    search_criteria_id: Optional[uuid.UUID] = Field(None)
    configuration: Optional[JobConfiguration] = None
    provider_config: Optional[Dict[str, Any]] = None

class ContactDiscoveryJobUpdate(BaseModel):
    """Schema for updating discovery jobs."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None)
    configuration: Optional[JobConfiguration] = None
    max_retries: Optional[int] = Field(None, ge=0)
    can_retry: Optional[bool] = None

class ExtractionResult(BaseModel):
    """Schema for extraction results."""
    listing_id: Optional[uuid.UUID] = Field(None, description="Source listing ID")
    contact_id: Optional[uuid.UUID] = Field(None, description="Existing or new contact ID")
    extraction_method: ExtractionMethod = Field(description="Method used")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Extraction confidence")
    
    # Raw extracted data
    raw_data: Dict[str, Any] = Field(description="Raw extracted data")
    extracted_fields: Dict[str, Any] = Field(description="Processed fields")
    
    # Processing results
    validation_status: ValidationStatus = Field(description="Validation status")
    validation_errors: List[str] = Field(default_factory=list, description="Validation errors")
    
    # Quality metrics
    data_completeness: float = Field(ge=0.0, le=1.0, description="Data completeness")
    extraction_accuracy: float = Field(ge=0.0, le=1.0, description="Extraction accuracy")
    duplicate_probability: float = Field(ge=0.0, le=1.0, description="Duplicate probability")
    
    # Processing metadata
    processing_time_ms: int = Field(description="Processing time in milliseconds")
    processing_timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # Status
    is_final: bool = Field(default=False, description="Final result")
    is_accepted: bool = Field(default=False, description="User accepted")
    rejection_reason: Optional[str] = Field(None, description="Rejection reason")
```

---

## Data Validation and Business Rules

### Validation Rules Engine
```python
# mafa/models/validation.py
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from datetime import datetime, date
import re
import phonenumbers
from phonenumbers import PhoneNumberType

class ValidationRuleType(str, Enum):
    """Types of validation rules."""
    REQUIRED = "required"
    FORMAT = "format"
    RANGE = "range"
    LENGTH = "length"
    CUSTOM = "custom"
    BUSINESS_LOGIC = "business_logic"

class ValidationSeverity(str, Enum):
    """Validation error severity."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"

class ValidationRule:
    """Validation rule definition."""
    def __init__(
        self,
        field_path: str,
        rule_type: ValidationRuleType,
        severity: ValidationSeverity,
        message: str,
        **kwargs
    ):
        self.field_path = field_path
        self.rule_type = rule_type
        self.severity = severity
        self.message = message
        self.parameters = kwargs
    
    def validate(self, value: Any, context: Dict[str, Any] = None) -> tuple[bool, Optional[str]]:
        """Validate a value against this rule."""
        context = context or {}
        
        try:
            if self.rule_type == ValidationRuleType.REQUIRED:
                return self._validate_required(value)
            elif self.rule_type == ValidationRuleType.FORMAT:
                return self._validate_format(value)
            elif self.rule_type == ValidationRuleType.RANGE:
                return self._validate_range(value)
            elif self.rule_type == ValidationRuleType.LENGTH:
                return self._validate_length(value)
            elif self.rule_type == ValidationRuleType.CUSTOM:
                return self._validate_custom(value, context)
            elif self.rule_type == ValidationRuleType.BUSINESS_LOGIC:
                return self._validate_business_logic(value, context)
            else:
                return True, None
        except Exception as e:
            return False, f"Validation error: {str(e)}"
    
    def _validate_required(self, value: Any) -> tuple[bool, Optional[str]]:
        """Validate required field."""
        if value is None or (isinstance(value, str) and not value.strip()):
            return False, self.message
        return True, None
    
    def _validate_format(self, value: Any) -> tuple[bool, Optional[str]]:
        """Validate format (regex, email, phone, etc.)."""
        if value is None:
            return True, None
        
        format_type = self.parameters.get('format')
        
        if format_type == 'email':
            if not re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', str(value)):
                return False, self.message
        elif format_type == 'phone':
            try:
                parsed = phonenumbers.parse(str(value), 'DE')
                if not phonenumbers.is_valid_number(parsed):
                    return False, self.message
            except:
                return False, self.message
        elif format_type == 'postal_code':
            if not re.match(r'^\d{5}$', str(value)):
                return False, self.message
        elif 'pattern' in self.parameters:
            if not re.match(self.parameters['pattern'], str(value)):
                return False, self.message
        
        return True, None
    
    def _validate_range(self, value: Any) -> tuple[bool, Optional[str]]:
        """Validate numeric range."""
        if value is None:
            return True, None
        
        try:
            num_value = float(value)
            min_value = self.parameters.get('min')
            max_value = self.parameters.get('max')
            
            if min_value is not None and num_value < min_value:
                return False, self.message
            if max_value is not None and num_value > max_value:
                return False, self.message
            
            return True, None
        except (ValueError, TypeError):
            return False, "Value must be numeric"
    
    def _validate_length(self, value: Any) -> tuple[bool, Optional[str]]:
        """Validate string length."""
        if value is None:
            return True, None
        
        str_value = str(value)
        min_length = self.parameters.get('min_length')
        max_length = self.parameters.get('max_length')
        
        if min_length is not None and len(str_value) < min_length:
            return False, self.message
        if max_length is not None and len(str_value) > max_length:
            return False, self.message
        
        return True, None
    
    def _validate_custom(self, value: Any, context: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate using custom function."""
        validator_func = self.parameters.get('validator_func')
        if validator_func and callable(validator_func):
            return validator_func(value, context)
        return True, None
    
    def _validate_business_logic(self, value: Any, context: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Validate business logic rules."""
        # Implement business logic validation
        field_name = self.field_path.split('.')[-1]
        
        # Example business rules
        if field_name == 'rent_netto' and context.get('rent_brutto'):
            if float(value or 0) > float(context['rent_brutto'] or 0):
                return False, "Net rent cannot exceed gross rent"
        
        if field_name == 'available_from' and context.get('available_until'):
            if value and context['available_until'] and date.fromisoformat(str(value)) > context['available_until']:
                return False, "Available from date cannot be after available until date"
        
        return True, None

class ValidationEngine:
    """Engine for running validation rules."""
    
    def __init__(self):
        self.rules: List[ValidationRule] = []
    
    def add_rule(self, rule: ValidationRule) -> None:
        """Add a validation rule."""
        self.rules.append(rule)
    
    def validate_entity(self, entity_data: Dict[str, Any], entity_type: str) -> Dict[str, List[str]]:
        """Validate an entity against all applicable rules."""
        errors = {}
        warnings = {}
        
        for rule in self.rules:
            # Extract value from entity data using field path
            value = self._get_nested_value(entity_data, rule.field_path)
            
            # Validate the value
            is_valid, error_message = rule.validate(value, entity_data)
            
            if not is_valid:
                field_name = rule.field_path.split('.')[-1]
                if rule.severity == ValidationSeverity.ERROR:
                    errors.setdefault(field_name, []).append(error_message)
                elif rule.severity == ValidationSeverity.WARNING:
                    warnings.setdefault(field_name, []).append(error_message)
        
        return {'errors': errors, 'warnings': warnings}
    
    def _get_nested_value(self, data: Dict[str, Any], field_path: str) -> Any:
        """Get value from nested dictionary using dot notation."""
        keys = field_path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value

# Define validation rules for each entity type
def get_user_validation_rules() -> List[ValidationRule]:
    """Get validation rules for User entity."""
    return [
        ValidationRule(
            'email', ValidationRuleType.REQUIRED, ValidationSeverity.ERROR,
            'Email address is required'
        ),
        ValidationRule(
            'email', ValidationRuleType.FORMAT, ValidationSeverity.ERROR,
            'Invalid email format', format='email'
        ),
        ValidationRule(
            'first_name', ValidationRuleType.REQUIRED, ValidationSeverity.ERROR,
            'First name is required'
        ),
        ValidationRule(
            'last_name', ValidationRuleType.REQUIRED, ValidationSeverity.ERROR,
            'Last name is required'
        ),
        ValidationRule(
            'password_hash', ValidationRuleType.REQUIRED, ValidationSeverity.ERROR,
            'Password hash is required'
        ),
        ValidationRule(
            'preferences.language', ValidationRuleType.FORMAT, ValidationSeverity.ERROR,
            'Invalid language code', format='pattern', pattern=r'^[a-z]{2}$'
        ),
        ValidationRule(
            'consent.gdpr_consent', ValidationRuleType.BUSINESS_LOGIC, ValidationSeverity.ERROR,
            'GDPR consent required for data processing'
        )
    ]

def get_contact_validation_rules() -> List[ValidationRule]:
    """Get validation rules for Contact entity."""
    return [
        ValidationRule(
            'name', ValidationRuleType.REQUIRED, ValidationSeverity.ERROR,
            'Contact name is required'
        ),
        ValidationRule(
            'name', ValidationRuleType.LENGTH, ValidationSeverity.ERROR,
            'Contact name must be between 1 and 255 characters',
            min_length=1, max_length=255
        ),
        ValidationRule(
            'phone', ValidationRuleType.FORMAT, ValidationSeverity.WARNING,
            'Invalid phone number format', format='phone'
        ),
        ValidationRule(
            'email', ValidationRuleType.FORMAT, ValidationSeverity.WARNING,
            'Invalid email format', format='email'
        ),
        ValidationRule(
            'confidence_score', ValidationRuleType.RANGE, ValidationSeverity.ERROR,
            'Confidence score must be between 0 and 1',
            min=0.0, max=1.0
        ),
        ValidationRule(
            'quality_score', ValidationRuleType.RANGE, ValidationSeverity.ERROR,
            'Quality score must be between 0 and 1',
            min=0.0, max=1.0
        )
    ]

def get_listing_validation_rules() -> List[ValidationRule]:
    """Get validation rules for Listing entity."""
    return [
        ValidationRule(
            'title', ValidationRuleType.REQUIRED, ValidationSeverity.ERROR,
            'Listing title is required'
        ),
        ValidationRule(
            'provider', ValidationRuleType.REQUIRED, ValidationSeverity.ERROR,
            'Provider is required'
        ),
        ValidationRule(
            'location.city', ValidationRuleType.REQUIRED, ValidationSeverity.ERROR,
            'City is required'
        ),
        ValidationRule(
            'financial.rent_netto', ValidationRuleType.RANGE, ValidationSeverity.ERROR,
            'Net rent must be positive',
            min=0.0
        ),
        ValidationRule(
            'specs.rooms', ValidationRuleType.RANGE, ValidationSeverity.WARNING,
            'Room count should be positive',
            min=0.0
        ),
        ValidationRule(
            'specs.living_area', ValidationRuleType.RANGE, ValidationSeverity.WARNING,
            'Living area should be positive',
            min=0.0
        )
    ]

# Validation service
class ValidationService:
    """Service for entity validation."""
    
    def __init__(self):
        self.engine = ValidationEngine()
        self._setup_default_rules()
    
    def _setup_default_rules(self) -> None:
        """Setup default validation rules."""
        # User rules
        for rule in get_user_validation_rules():
            self.engine.add_rule(rule)
        
        # Contact rules
        for rule in get_contact_validation_rules():
            self.engine.add_rule(rule)
        
        # Listing rules
        for rule in get_listing_validation_rules():
            self.engine.add_rule(rule)
    
    def validate_user(self, user_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate user data."""
        return self.engine.validate_entity(user_data, 'user')
    
    def validate_contact(self, contact_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate contact data."""
        return self.engine.validate_entity(contact_data, 'contact')
    
    def validate_listing(self, listing_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Validate listing data."""
        return self.engine.validate_entity(listing_data, 'listing')
    
    def is_valid(self, entity_data: Dict[str, Any], entity_type: str) -> bool:
        """Check if entity is valid."""
        validation_result = self.engine.validate_entity(entity_data, entity_type)
        return len(validation_result['errors']) == 0
```

---

## Data Relationship Constraints

### Foreign Key Relationships
```python
# mafa/models/relationships.py
from sqlalchemy import Column, ForeignKey, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import uuid
from datetime import datetime

Base = declarative_base()

class UserRelationship(Base):
    """User relationship to other entities."""
    __tablename__ = "user_relationships"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    related_user_id = Column(String(36), ForeignKey("users.id"), nullable=True)
    related_contact_id = Column(String(36), ForeignKey("contacts.id"), nullable=True)
    related_listing_id = Column(String(36), ForeignKey("listings.id"), nullable=True)
    
    relationship_type = Column(String(50), nullable=False)  # 'owner', 'collaborator', 'viewer'
    permissions = Column(String(255))  # JSON string of permissions
    is_active = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", foreign_keys=[user_id], back_populates="relationships")
    related_user = relationship("User", foreign_keys=[related_user_id])
    contact = relationship("Contact", foreign_keys=[related_contact_id])
    listing = relationship("Listing", foreign_keys=[related_listing_id])

class ContactListingAssociation(Base):
    """Many-to-many association between contacts and listings."""
    __tablename__ = "contact_listing_associations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    contact_id = Column(String(36), ForeignKey("contacts.id"), nullable=False)
    listing_id = Column(String(36), ForeignKey("listings.id"), nullable=False)
    
    association_type = Column(String(50), nullable=False)  # 'extracted_from', 'contact_for', 'referenced_in'
    confidence_score = Column(String(10))  # DECIMAL as string
    is_verified = Column(Boolean, default=False)
    verification_date = Column(DateTime)
    notes = Column(String(500))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    contact = relationship("Contact", back_populates="listing_associations")
    listing = relationship("Listing", back_populates="contact_associations")

class SearchCriteriaListingAssociation(Base):
    """Many-to-many association between search criteria and listings."""
    __tablename__ = "search_criteria_listing_associations"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    search_criteria_id = Column(String(36), ForeignKey("search_criteria.id"), nullable=False)
    listing_id = Column(String(36), ForeignKey("listings.id"), nullable=False)
    
    relevance_score = Column(String(10))  # DECIMAL as string
    match_reasons = Column(String(500))  # JSON string
    is_manual_match = Column(Boolean, default=False)
    is_automated_match = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    search_criteria = relationship("SearchCriteria", back_populates="listing_matches")
    listing = relationship("Listing", back_populates="search_matches")

# Update base models to include relationships
class User(Base):
    """Updated User model with relationships."""
    __tablename__ = "users"
    
    # Existing fields...
    relationships = relationship("UserRelationship", foreign_keys="UserRelationship.user_id", 
                                back_populates="user", cascade="all, delete-orphan")

class Contact(Base):
    """Updated Contact model with relationships."""
    __tablename__ = "contacts"
    
    # Existing fields...
    listing_associations = relationship("ContactListingAssociation", 
                                       back_populates="contact", cascade="all, delete-orphan")

class Listing(Base):
    """Updated Listing model with relationships."""
    __tablename__ = "listings"
    
    # Existing fields...
    contact_associations = relationship("ContactListingAssociation", 
                                       back_populates="listing", cascade="all, delete-orphan")
    search_matches = relationship("SearchCriteriaListingAssociation", 
                                 back_populates="listing", cascade="all, delete-orphan")

class SearchCriteria(Base):
    """Updated SearchCriteria model with relationships."""
    __tablename__ = "search_criteria"
    
    # Existing fields...
    listing_matches = relationship("SearchCriteriaListingAssociation", 
                                  back_populates="search_criteria", cascade="all, delete-orphan")
```

---

## Data Lifecycle and State Management

### Entity State Management
```python
# mafa/models/state_management.py
from typing import Dict, Any, Optional
from enum import Enum
from datetime import datetime
import uuid

class EntityState(Enum):
    """Entity lifecycle states."""
    DRAFT = "draft"
    ACTIVE = "active"
    INACTIVE = "inactive"
    ARCHIVED = "archived"
    DELETED = "deleted"
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class StateTransition:
    """State transition definition."""
    def __init__(self, from_state: EntityState, to_state: EntityState, 
                 action: str, conditions: list = None, permissions: list = None):
        self.from_state = from_state
        self.to_state = to_state
        self.action = action
        self.conditions = conditions or []
        self.permissions = permissions or []

class StateMachine:
    """State machine for entity lifecycle management."""
    
    def __init__(self, entity_type: str):
        self.entity_type = entity_type
        self.transitions: Dict[tuple, StateTransition] = {}
        self._setup_transitions()
    
    def _setup_transitions(self) -> None:
        """Setup valid state transitions."""
        # User state transitions
        if self.entity_type == "user":
            self._add_transition(EntityState.PENDING, EntityState.ACTIVE, "verify_email")
            self._add_transition(EntityState.PENDING, EntityState.ACTIVE, "auto_verify")
            self._add_transition(EntityState.ACTIVE, EntityState.INACTIVE, "deactivate")
            self._add_transition(EntityState.INACTIVE, EntityState.ACTIVE, "reactivate")
            self._add_transition(EntityState.ACTIVE, EntityState.DELETED, "delete")
            self._add_transition(EntityState.INACTIVE, EntityState.DELETED, "delete")
            self._add_transition(EntityState.PENDING, EntityState.REJECTED, "reject")
        
        # Contact state transitions
        elif self.entity_type == "contact":
            self._add_transition(EntityState.PENDING, EntityState.ACTIVE, "create")
            self._add_transition(EntityState.PENDING, EntityState.ACTIVE, "validate")
            self._add_transition(EntityState.ACTIVE, EntityState.INACTIVE, "deactivate")
            self._add_transition(EntityState.INACTIVE, EntityState.ACTIVE, "reactivate")
            self._add_transition(EntityState.ACTIVE, EntityState.ARCHIVED, "archive")
            self._add_transition(EntityState.ARCHIVED, EntityState.ACTIVE, "unarchive")
            self._add_transition(EntityState.ACTIVE, EntityState.DELETED, "delete")
            self._add_transition(EntityState.INACTIVE, EntityState.DELETED, "delete")
        
        # Listing state transitions
        elif self.entity_type == "listing":
            self._add_transition(EntityState.PENDING, EntityState.ACTIVE, "activate")
            self._add_transition(EntityState.PENDING, EntityState.ACTIVE, "process")
            self._add_transition(EntityState.ACTIVE, EntityState.INACTIVE, "deactivate")
            self._add_transition(EntityState.INACTIVE, EntityState.ACTIVE, "reactivate")
            self._add_transition(EntityState.ACTIVE, EntityState.ARCHIVED, "archive")
            self._add_transition(EntityState.ARCHIVED, EntityState.ACTIVE, "unarchive")
            self._add_transition(EntityState.ACTIVE, EntityState.DELETED, "delete")
    
    def _add_transition(self, from_state: EntityState, to_state: EntityState, 
                       action: str, conditions: list = None, permissions: list = None) -> None:
        """Add a state transition."""
        transition = StateTransition(from_state, to_state, action, conditions, permissions)
        self.transitions[(from_state, action)] = transition
    
    def can_transition(self, current_state: EntityState, action: str, 
                      context: Dict[str, Any] = None) -> tuple[bool, Optional[str]]:
        """Check if transition is allowed."""
        context = context or {}
        transition_key = (current_state, action)
        
        if transition_key not in self.transitions:
            return False, f"Transition '{action}' not allowed from state '{current_state.value}'"
        
        transition = self.transitions[transition_key]
        
        # Check conditions
        for condition in transition.conditions:
            if not condition(context):
                return False, f"Condition not met for transition '{action}'"
        
        return True, None
    
    def transition(self, entity: Any, action: str, context: Dict[str, Any] = None) -> tuple[bool, str]:
        """Perform state transition."""
        context = context or {}
        current_state = EntityState(entity.status)
        
        can_transition, error_message = self.can_transition(current_state, action, context)
        if not can_transition:
            return False, error_message
        
        transition = self.transitions[(current_state, action)]
        
        # Perform the transition
        old_state = entity.status
        entity.status = transition.to_state.value
        entity.updated_at = datetime.utcnow()
        
        # Add state change to audit log
        if hasattr(entity, '_state_history'):
            entity._state_history.append({
                'from_state': old_state,
                'to_state': transition.to_state.value,
                'action': action,
                'timestamp': datetime.utcnow(),
                'context': context
            })
        
        return True, f"Successfully transitioned from '{old_state}' to '{transition.to_state.value}'"

# State management for entities
class StatefulEntity:
    """Mixin for entities that need state management."""
    
    def __init__(self):
        self._state_machine = StateMachine(self.__class__.__name__.lower())
        self._state_history = []
    
    def can_perform_action(self, action: str, context: Dict[str, Any] = None) -> bool:
        """Check if entity can perform an action."""
        current_state = EntityState(self.status)
        can_transition, _ = self._state_machine.can_transition(current_state, action, context)
        return can_transition
    
    def perform_action(self, action: str, context: Dict[str, Any] = None) -> tuple[bool, str]:
        """Perform an action on the entity."""
        return self._state_machine.transition(self, action, context)
    
    def get_state_history(self) -> list:
        """Get state transition history."""
        return self._state_history.copy()

class UserStateful(User, StatefulEntity):
    """User with state management."""
    
    def __init__(self, **kwargs):
        User.__init__(self, **kwargs)
        StatefulEntity.__init__(self)
        
        # Initialize state
        if not hasattr(self, 'status'):
            self.status = EntityState.PENDING.value

class ContactStateful(Contact, StatefulEntity):
    """Contact with state management."""
    
    def __init__(self, **kwargs):
        Contact.__init__(self, **kwargs)
        StatefulEntity.__init__(self)
        
        # Initialize state
        if not hasattr(self, 'status'):
            self.status = EntityState.PENDING.value

class ListingStateful(Listing, StatefulEntity):
    """Listing with state management."""
    
    def __init__(self, **kwargs):
        Listing.__init__(self, **kwargs)
        StatefulEntity.__init__(self)
        
        # Initialize state
        if not hasattr(self, 'status'):
            self.status = EntityState.PENDING.value
```

---

## Data Quality and Consistency

### Data Quality Rules
```python
# mafa/models/data_quality.py
from typing import Dict, Any, List, Optional
from datetime import datetime, date
import re

class DataQualityRule:
    """Data quality validation rule."""
    
    def __init__(self, name: str, description: str, severity: str, 
                 rule_func: callable, entity_type: str):
        self.name = name
        self.description = description
        self.severity = severity  # 'critical', 'major', 'minor'
        self.rule_func = rule_func
        self.entity_type = entity_type
    
    def evaluate(self, entity_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """Evaluate the rule against entity data."""
        try:
            result = self.rule_func(entity_data)
            if isinstance(result, tuple):
                return result
            else:
                return result, None
        except Exception as e:
            return False, f"Rule evaluation error: {str(e)}"

class DataQualityChecker:
    """Data quality assessment for entities."""
    
    def __init__(self):
        self.rules: Dict[str, List[DataQualityRule]] = {}
        self._setup_rules()
    
    def _setup_rules(self) -> None:
        """Setup data quality rules."""
        
        # User data quality rules
        self.rules['user'] = [
            DataQualityRule(
                "email_uniqueness",
                "Email address must be unique",
                "critical",
                lambda data: self._check_email_uniqueness(data),
                "user"
            ),
            DataQualityRule(
                "name_completeness",
                "Both first and last name should be provided",
                "major",
                lambda data: (bool(data.get('first_name') and data.get('last_name')), 
                             "Both names required"),
                "user"
            ),
            DataQualityRule(
                "consent_completeness",
                "GDPR consent should be properly recorded",
                "critical",
                lambda data: self._check_gdpr_consent(data),
                "user"
            )
        ]
        
        # Contact data quality rules
        self.rules['contact'] = [
            DataQualityRule(
                "name_validity",
                "Contact name should be valid and meaningful",
                "major",
                lambda data: self._validate_contact_name(data),
                "contact"
            ),
            DataQualityRule(
                "contact_information_completeness",
                "At least one contact method should be available",
                "major",
                lambda data: self._check_contact_completeness(data),
                "contact"
            ),
            DataQualityRule(
                "quality_score_accuracy",
                "Quality score should accurately reflect data quality",
                "minor",
                lambda data: self._validate_quality_score(data),
                "contact"
            ),
            DataQualityRule(
                "duplicate_detection",
                "Contact should be checked for duplicates",
                "major",
                lambda data: self._check_duplicates(data),
                "contact"
            )
        ]
        
        # Listing data quality rules
        self.rules['listing'] = [
            DataQualityRule(
                "location_completeness",
                "Location information should be complete",
                "critical",
                lambda data: self._check_location_completeness(data),
                "listing"
            ),
            DataQualityRule(
                "price_consistency",
                "Price information should be consistent",
                "major",
                lambda data: self._check_price_consistency(data),
                "listing"
            ),
            DataQualityRule(
                "description_quality",
                "Listing should have meaningful description",
                "minor",
                lambda data: self._validate_description(data),
                "listing"
            ),
            DataQualityRule(
                "property_specs_validity",
                "Property specifications should be realistic",
                "major",
                lambda data: self._validate_property_specs(data),
                "listing"
            )
        ]
    
    def check_data_quality(self, entity_data: Dict[str, Any], entity_type: str) -> Dict[str, Any]:
        """Check data quality for an entity."""
        if entity_type not in self.rules:
            return {'quality_score': 1.0, 'issues': []}
        
        issues = []
        critical_issues = 0
        major_issues = 0
        minor_issues = 0
        
        for rule in self.rules[entity_type]:
            passed, message = rule.evaluate(entity_data)
            
            if not passed:
                issue = {
                    'rule': rule.name,
                    'severity': rule.severity,
                    'description': rule.description,
                    'message': message or 'Rule validation failed'
                }
                issues.append(issue)
                
                if rule.severity == 'critical':
                    critical_issues += 1
                elif rule.severity == 'major':
                    major_issues += 1
                else:
                    minor_issues += 1
        
        # Calculate overall quality score
        total_issues = len(issues)
        if total_issues == 0:
            quality_score = 1.0
        else:
            # Weighted scoring based on issue severity
            weighted_issues = (critical_issues * 3 + major_issues * 2 + minor_issues * 1)
            max_possible_score = len(self.rules[entity_type]) * 3  # Assume max weight of 3
            quality_score = max(0.0, 1.0 - (weighted_issues / max_possible_score))
        
        return {
            'quality_score': quality_score,
            'issues': issues,
            'issue_count': {
                'critical': critical_issues,
                'major': major_issues,
                'minor': minor_issues,
                'total': total_issues
            },
            'rule_count': len(self.rules[entity_type]),
            'passed_rules': len(self.rules[entity_type]) - total_issues
        }
    
    # Quality check helper methods
    def _check_email_uniqueness(self, data: Dict[str, Any]) -> tuple[bool, str]:
        """Check if email is unique (requires database check)."""
        # This would need to be implemented with actual database query
        # For now, return placeholder
        return True, None
    
    def _check_gdpr_consent(self, data: Dict[str, Any]) -> tuple[bool, str]:
        """Check GDPR consent completeness."""
        consent_data = data.get('consent', {})
        if not consent_data.get('gdpr_consent'):
            return False, "GDPR consent is required"
        return True, None
    
    def _validate_contact_name(self, data: Dict[str, Any]) -> tuple[bool, str]:
        """Validate contact name quality."""
        name = data.get('name', '').strip()
        if len(name) < 2:
            return False, "Contact name too short"
        if not re.match(r'^[a-zA-ZäöüßÄÖÜß\s\-\.\']+$', name):
            return False, "Contact name contains invalid characters"
        return True, None
    
    def _check_contact_completeness(self, data: Dict[str, Any]) -> tuple[bool, str]:
        """Check if contact has at least one contact method."""
        phone = data.get('phone_encrypted')
        email = data.get('email_encrypted')
        address = data.get('address_encrypted')
        
        if not any([phone, email, address]):
            return False, "At least one contact method required"
        return True, None
    
    def _validate_quality_score(self, data: Dict[str, Any]) -> tuple[bool, str]:
        """Validate quality score accuracy."""
        quality_score = data.get('quality_score', 0.0)
        quality_metrics = data.get('quality_metrics', {})
        
        # Check if quality score matches calculated score
        if quality_metrics:
            calculated_score = (
                quality_metrics.get('confidence_score', 0.0) * 0.3 +
                quality_metrics.get('completeness_score', 0.0) * 0.3 +
                quality_metrics.get('accuracy_score', 0.0) * 0.2 +
                quality_metrics.get('relevance_score', 0.0) * 0.2
            )
            
            if abs(quality_score - calculated_score) > 0.1:
                return False, "Quality score doesn't match calculated metrics"
        
        return True, None
    
    def _check_duplicates(self, data: Dict[str, Any]) -> tuple[bool, str]:
        """Check for potential duplicates (requires database check)."""
        # This would need to be implemented with actual database query
        # For now, return placeholder
        return True, None
    
    def _check_location_completeness(self, data: Dict[str, Any]) -> tuple[bool, str]:
        """Check location information completeness."""
        location = data.get('location', {})
        city = location.get('city')
        postal_code = location.get('postal_code')
        
        if not city:
            return False, "City is required"
        if postal_code and not re.match(r'^\d{5}$', postal_code):
            return False, "Invalid postal code format"
        return True, None
    
    def _check_price_consistency(self, data: Dict[str, Any]) -> tuple[bool, str]:
        """Check price information consistency."""
        financial = data.get('financial', {})
        rent_netto = financial.get('rent_netto')
        rent_brutto = financial.get('rent_brutto')
        additional_costs = financial.get('additional_costs')
        
        if rent_brutto and rent_netto and additional_costs:
            calculated_brutto = rent_netto + additional_costs
            if abs(rent_brutto - calculated_brutto) > 1.0:
                return False, "Gross rent doesn't match net rent plus additional costs"
        
        return True, None
    
    def _validate_description(self, data: Dict[str, Any]) -> tuple[bool, str]:
        """Validate listing description quality."""
        description = data.get('description', '').strip()
        if len(description) < 50:
            return False, "Description too short (minimum 50 characters)"
        return True, None
    
    def _validate_property_specs(self, data: Dict[str, Any]) -> tuple[bool, str]:
        """Validate property specifications."""
        specs = data.get('specs', {})
        rooms = specs.get('rooms')
        living_area = specs.get('living_area')
        
        if rooms and (rooms <= 0 or rooms > 20):
            return False, "Room count should be between 0 and 20"
        
        if living_area and (living_area <= 0 or living_area > 1000):
            return False, "Living area should be between 0 and 1000 square meters"
        
        return True, None

# Global data quality checker instance
data_quality_checker = DataQualityChecker()
```

---

## Related Documentation

- [Database Schema](database-schema.md) - Database table structures and relationships
- [Contact Discovery System](contact-discovery.md) - Contact extraction and discovery workflows
- [System Overview](../architecture/system-overview.md) - Overall system architecture
- [API Documentation](../developer-guide/api/integration-guide.md) - API endpoint documentation
- [Security Guide](../operations/security.md) - Data security and privacy practices

---

**Data Architecture Support**: For data modeling questions or issues, contact the data architecture team or create an issue with the `data-model` label.