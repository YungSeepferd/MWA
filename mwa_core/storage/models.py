"""
Enhanced data models for MWA Core storage system.

Provides SQLAlchemy ORM models for listings, contacts, scraping jobs, and other entities
with proper relationships, constraints, and indexing.
"""

from __future__ import annotations

import enum
import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional, Any

from sqlalchemy import (
    Column, Integer, String, Text, DateTime, Boolean, Float, 
    ForeignKey, UniqueConstraint, Index, Enum as SQLEnum,
    create_engine, event
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker, Session
from sqlalchemy.sql import func

Base = declarative_base()


class ListingStatus(enum.Enum):
    """Enumeration for listing statuses."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    EXPIRED = "expired"
    RENTED = "rented"
    DELETED = "deleted"


class ContactType(enum.Enum):
    """Enumeration for contact types."""
    EMAIL = "email"
    PHONE = "phone"
    FORM = "form"
    WEBSITE = "website"


class ContactStatus(enum.Enum):
    """Enumeration for contact validation status."""
    UNVALIDATED = "unvalidated"
    VALID = "valid"
    INVALID = "invalid"
    SUSPICIOUS = "suspicious"


class JobStatus(enum.Enum):
    """Enumeration for scraping job statuses."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DeduplicationStatus(enum.Enum):
    """Enumeration for deduplication status."""
    ORIGINAL = "original"
    DUPLICATE = "duplicate"
    MERGED = "merged"


class Listing(Base):
    """SQLAlchemy model for apartment listings."""
    
    __tablename__ = "listings"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String(50), nullable=False, index=True)
    external_id = Column(String(100), nullable=True)
    title = Column(String(500), nullable=False)
    url = Column(String(1000), nullable=False, unique=True, index=True)
    price = Column(String(50), nullable=True)
    size = Column(String(50), nullable=True)
    rooms = Column(String(20), nullable=True)
    address = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    images = Column(Text, nullable=True)  # JSON array
    contacts = Column(Text, nullable=True)  # JSON array
    scraped_at = Column(DateTime, nullable=False, default=func.now(), index=True)
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    status = Column(SQLEnum(ListingStatus), nullable=False, default=ListingStatus.ACTIVE, index=True)
    raw_data = Column(Text, nullable=True)  # JSON for provider-specific data
    
    # Enhanced fields for PR C
    hash_signature = Column(String(64), nullable=True, unique=True, index=True)  # SHA-256 hash
    deduplication_status = Column(SQLEnum(DeduplicationStatus), nullable=False, 
                                  default=DeduplicationStatus.ORIGINAL, index=True)
    duplicate_of_id = Column(Integer, ForeignKey("listings.id"), nullable=True)
    first_seen_at = Column(DateTime, nullable=False, default=func.now())
    last_seen_at = Column(DateTime, nullable=False, default=func.now())
    view_count = Column(Integer, nullable=False, default=1)
    
    # Relationships
    duplicate_listings = relationship("Listing", remote_side=[id])
    contact_entries = relationship("Contact", back_populates="listing", cascade="all, delete-orphan")
    scraping_runs = relationship("ScrapingRun", secondary="listing_scraping_runs", 
                                back_populates="listings")
    
    __table_args__ = (
        UniqueConstraint("provider", "external_id", name="uq_provider_external_id"),
        Index("idx_listings_provider_status", "provider", "status"),
        Index("idx_listings_scraped_at_desc", "scraped_at", postgresql_using="btree", 
              postgresql_ops={"scraped_at": "DESC"}),
        Index("idx_listings_hash_signature", "hash_signature"),
    )
    
    def __repr__(self) -> str:
        return f"<Listing(id={self.id}, title='{self.title}', provider='{self.provider}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "provider": self.provider,
            "external_id": self.external_id,
            "title": self.title,
            "url": self.url,
            "price": self.price,
            "size": self.size,
            "rooms": self.rooms,
            "address": self.address,
            "description": self.description,
            "images": self.get_images(),
            "contacts": self.get_contacts(),
            "scraped_at": self.scraped_at.isoformat() if self.scraped_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "status": self.status.value if self.status else None,
            "raw_data": self.get_raw_data(),
            "hash_signature": self.hash_signature,
            "deduplication_status": self.deduplication_status.value if self.deduplication_status else None,
            "duplicate_of_id": self.duplicate_of_id,
            "first_seen_at": self.first_seen_at.isoformat() if self.first_seen_at else None,
            "last_seen_at": self.last_seen_at.isoformat() if self.last_seen_at else None,
            "view_count": self.view_count,
        }
    
    def get_images(self) -> List[str]:
        """Get images as list."""
        if not self.images:
            return []
        try:
            return json.loads(self.images)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_images(self, images: List[str]) -> None:
        """Set images from list."""
        self.images = json.dumps(images) if images else None
    
    def get_contacts(self) -> List[Dict[str, Any]]:
        """Get contacts as list."""
        if not self.contacts:
            return []
        try:
            return json.loads(self.contacts)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_contacts(self, contacts: List[Dict[str, Any]]) -> None:
        """Set contacts from list."""
        self.contacts = json.dumps(contacts) if contacts else None
    
    def get_raw_data(self) -> Dict[str, Any]:
        """Get raw data as dict."""
        if not self.raw_data:
            return {}
        try:
            return json.loads(self.raw_data)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_raw_data(self, raw_data: Dict[str, Any]) -> None:
        """Set raw data from dict."""
        self.raw_data = json.dumps(raw_data) if raw_data else None
    
    def generate_hash_signature(self) -> str:
        """Generate SHA-256 hash signature for deduplication."""
        # Create a normalized string for hashing
        hash_string = f"{self.provider}|{self.external_id or ''}|{self.title}|{self.price or ''}|{self.size or ''}|{self.rooms or ''}|{self.address or ''}"
        return hashlib.sha256(hash_string.encode('utf-8')).hexdigest()
    
    def update_hash_signature(self) -> None:
        """Update the hash signature."""
        self.hash_signature = self.generate_hash_signature()


class Contact(Base):
    """SQLAlchemy model for contacts with market intelligence capabilities."""
    
    __tablename__ = "contacts"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False, index=True)
    type = Column(SQLEnum(ContactType), nullable=False, index=True)
    value = Column(String(500), nullable=False)
    confidence = Column(Float, nullable=True)
    source = Column(String(50), nullable=True)
    status = Column(SQLEnum(ContactStatus), nullable=False,
                   default=ContactStatus.UNVALIDATED, index=True)
    validated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    # Enhanced fields for PR C
    hash_signature = Column(String(64), nullable=True, index=True)
    validation_metadata = Column(Text, nullable=True)  # JSON for validation details
    usage_count = Column(Integer, nullable=False, default=0)
    last_used_at = Column(DateTime, nullable=True)
    
    # Market Intelligence Fields
    position = Column(String(100), nullable=True)
    company_name = Column(String(200), nullable=True)
    agency_type = Column(String(50), nullable=True, index=True)
    market_areas = Column(Text, nullable=True)  # JSON array of market areas
    outreach_history = Column(Text, nullable=True)  # JSON array of outreach history
    preferred_contact_method = Column(String(20), nullable=True)
    last_contacted = Column(DateTime, nullable=True, index=True)
    confidence_score = Column(Float, nullable=True, default=0.0, index=True)
    quality_score = Column(Float, nullable=True, default=0.0, index=True)
    is_active = Column(Boolean, nullable=False, default=True, index=True)
    is_blacklisted = Column(Boolean, nullable=False, default=False, index=True)
    blacklist_reason = Column(Text, nullable=True)
    scraped_from_url = Column(String(1000), nullable=True)
    source_provider = Column(String(50), nullable=True, index=True)
    extraction_method = Column(String(50), nullable=True)
    extraction_confidence = Column(Float, nullable=True)
    lead_source = Column(String(50), nullable=True, index=True)
    tags = Column(Text, nullable=True)  # JSON array of tags
    notes = Column(Text, nullable=True)
    
    # Relationships
    listing = relationship("Listing", back_populates="contact_entries")
    validation_history = relationship("ContactValidation", back_populates="contact",
                                    cascade="all, delete-orphan")
    
    __table_args__ = (
        UniqueConstraint("listing_id", "type", "value", name="uq_listing_contact"),
        Index("idx_contacts_listing_type", "listing_id", "type"),
        Index("idx_contacts_status", "status"),
        Index("idx_contacts_created_at", "created_at"),
    )
    
    def __repr__(self) -> str:
        return f"<Contact(id={self.id}, type='{self.type.value}', value='{self.value}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "listing_id": self.listing_id,
            "type": self.type.value if self.type else None,
            "value": self.value,
            "confidence": self.confidence,
            "source": self.source,
            "status": self.status.value if self.status else None,
            "validated_at": self.validated_at.isoformat() if self.validated_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "hash_signature": self.hash_signature,
            "validation_metadata": self.get_validation_metadata(),
            "usage_count": self.usage_count,
            "last_used_at": self.last_used_at.isoformat() if self.last_used_at else None,
            # Market Intelligence Fields
            "position": self.position,
            "company_name": self.company_name,
            "agency_type": self.agency_type,
            "market_areas": self.get_market_areas(),
            "outreach_history": self.get_outreach_history(),
            "preferred_contact_method": self.preferred_contact_method,
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
            "lead_source": self.lead_source,
            "tags": self.get_tags(),
            "notes": self.notes,
        }
    
    def get_validation_metadata(self) -> Dict[str, Any]:
        """Get validation metadata as dict."""
        if not self.validation_metadata:
            return {}
        try:
            return json.loads(self.validation_metadata)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_validation_metadata(self, metadata: Dict[str, Any]) -> None:
        """Set validation metadata from dict."""
        self.validation_metadata = json.dumps(metadata) if metadata else None

    def get_market_areas(self) -> List[str]:
        """Get market areas as list."""
        if not self.market_areas:
            return []
        try:
            return json.loads(self.market_areas)
        except (json.JSONDecodeError, TypeError):
            return []

    def set_market_areas(self, market_areas: List[str]) -> None:
        """Set market areas from list."""
        self.market_areas = json.dumps(market_areas) if market_areas else None

    def get_outreach_history(self) -> List[Dict[str, Any]]:
        """Get outreach history as list."""
        if not self.outreach_history:
            return []
        try:
            return json.loads(self.outreach_history)
        except (json.JSONDecodeError, TypeError):
            return []

    def set_outreach_history(self, outreach_history: List[Dict[str, Any]]) -> None:
        """Set outreach history from list."""
        self.outreach_history = json.dumps(outreach_history) if outreach_history else None

    def get_tags(self) -> List[str]:
        """Get tags as list."""
        if not self.tags:
            return []
        try:
            return json.loads(self.tags)
        except (json.JSONDecodeError, TypeError):
            return []

    def set_tags(self, tags: List[str]) -> None:
        """Set tags from list."""
        self.tags = json.dumps(tags) if tags else None

    def generate_hash_signature(self) -> str:
        """Generate SHA-256 hash signature."""
        hash_string = f"{self.listing_id}|{self.type.value}|{self.value}"
        return hashlib.sha256(hash_string.encode('utf-8')).hexdigest()

    def update_hash_signature(self) -> None:
        """Update the hash signature."""
        self.hash_signature = self.generate_hash_signature()


class ScrapingRun(Base):
    """SQLAlchemy model for scraping runs (history)."""
    
    __tablename__ = "scraping_runs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    provider = Column(String(50), nullable=False, index=True)
    status = Column(SQLEnum(JobStatus), nullable=False, default=JobStatus.PENDING, index=True)
    started_at = Column(DateTime, nullable=False, default=func.now(), index=True)
    created_at = Column(DateTime, nullable=False, default=func.now(), index=True)
    completed_at = Column(DateTime, nullable=True)
    listings_found = Column(Integer, nullable=False, default=0)
    listings_processed = Column(Integer, nullable=False, default=0)
    errors = Column(Text, nullable=True)  # JSON array
    performance_metrics = Column(Text, nullable=True)  # JSON object
    configuration_snapshot = Column(Text, nullable=True)  # JSON object
    trigger_type = Column(String(50), nullable=True)  # manual, scheduled, api
    triggered_by = Column(String(100), nullable=True)  # user, system, etc.
    
    # Enhanced fields for PR C
    duration_seconds = Column(Float, nullable=True)
    memory_usage_mb = Column(Float, nullable=True)
    cpu_usage_percent = Column(Float, nullable=True)
    network_requests = Column(Integer, nullable=False, default=0)
    data_size_mb = Column(Float, nullable=True)
    
    # Relationships
    listings = relationship("Listing", secondary="listing_scraping_runs", 
                           back_populates="scraping_runs")
    
    __table_args__ = (
        Index("idx_scraping_runs_provider_status", "provider", "status"),
        Index("idx_scraping_runs_started_at_desc", "started_at", postgresql_using="btree", 
              postgresql_ops={"started_at": "DESC"}),
    )
    
    def __repr__(self) -> str:
        return f"<ScrapingRun(id={self.id}, provider='{self.provider}', status='{self.status.value}')>"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "provider": self.provider,
            "status": self.status.value if self.status else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "listings_found": self.listings_found,
            "listings_processed": self.listings_processed,
            "errors": self.get_errors(),
            "performance_metrics": self.get_performance_metrics(),
            "configuration_snapshot": self.get_configuration_snapshot(),
            "trigger_type": self.trigger_type,
            "triggered_by": self.triggered_by,
            "duration_seconds": self.duration_seconds,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent,
            "network_requests": self.network_requests,
            "data_size_mb": self.data_size_mb,
        }
    
    def get_errors(self) -> List[str]:
        """Get errors as list."""
        if not self.errors:
            return []
        try:
            return json.loads(self.errors)
        except (json.JSONDecodeError, TypeError):
            return []
    
    def set_errors(self, errors: List[str]) -> None:
        """Set errors from list."""
        self.errors = json.dumps(errors) if errors else None
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics as dict."""
        if not self.performance_metrics:
            return {}
        try:
            return json.loads(self.performance_metrics)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_performance_metrics(self, metrics: Dict[str, Any]) -> None:
        """Set performance metrics from dict."""
        self.performance_metrics = json.dumps(metrics) if metrics else None
    
    def get_configuration_snapshot(self) -> Dict[str, Any]:
        """Get configuration snapshot as dict."""
        if not self.configuration_snapshot:
            return {}
        try:
            return json.loads(self.configuration_snapshot)
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_configuration_snapshot(self, config: Dict[str, Any]) -> None:
        """Set configuration snapshot from dict."""
        self.configuration_snapshot = json.dumps(config) if config else None


class ListingScrapingRun(Base):
    """Association table for many-to-many relationship between listings and scraping runs."""
    
    __tablename__ = "listing_scraping_runs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    listing_id = Column(Integer, ForeignKey("listings.id"), nullable=False, index=True)
    scraping_run_id = Column(Integer, ForeignKey("scraping_runs.id"), nullable=False, index=True)
    discovered_at = Column(DateTime, nullable=False, default=func.now())
    
    __table_args__ = (
        UniqueConstraint("listing_id", "scraping_run_id", name="uq_listing_scraping_run"),
        Index("idx_listing_scraping_runs_listing", "listing_id"),
        Index("idx_listing_scraping_runs_scraping_run", "scraping_run_id"),
    )


class ContactValidation(Base):
    """Model for contact validation history."""
    
    __tablename__ = "contact_validations"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    contact_id = Column(Integer, ForeignKey("contacts.id"), nullable=False, index=True)
    validation_method = Column(String(50), nullable=False)  # email, phone, etc.
    validation_result = Column(SQLEnum(ContactStatus), nullable=False)
    confidence_score = Column(Float, nullable=True)
    validation_metadata = Column(Text, nullable=True)  # JSON
    validated_at = Column(DateTime, nullable=False, default=func.now())
    validator_version = Column(String(20), nullable=True)
    
    # Relationships
    contact = relationship("Contact", back_populates="validation_history")
    
    __table_args__ = (
        Index("idx_contact_validations_contact", "contact_id"),
        Index("idx_contact_validations_validated_at", "validated_at"),
    )


class JobStore(Base):
    """Model for job store (scheduler jobs)."""
    
    __tablename__ = "job_store"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    job_id = Column(String(100), nullable=False, unique=True, index=True)
    job_name = Column(String(200), nullable=False)
    job_type = Column(String(50), nullable=False, index=True)  # scraping, cleanup, etc.
    job_data = Column(Text, nullable=False)  # JSON
    schedule_expression = Column(String(100), nullable=True)  # cron expression
    next_run_time = Column(DateTime, nullable=True, index=True)
    last_run_time = Column(DateTime, nullable=True)
    run_count = Column(Integer, nullable=False, default=0)
    success_count = Column(Integer, nullable=False, default=0)
    failure_count = Column(Integer, nullable=False, default=0)
    enabled = Column(Boolean, nullable=False, default=True, index=True)
    created_at = Column(DateTime, nullable=False, default=func.now())
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    
    __table_args__ = (
        Index("idx_job_store_next_run_time", "next_run_time"),
        Index("idx_job_store_job_type_enabled", "job_type", "enabled"),
    )


class Configuration(Base):
    """Model for runtime configuration settings."""
    
    __tablename__ = "configuration"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    key = Column(String(100), nullable=False, unique=True, index=True)
    value = Column(Text, nullable=False)
    description = Column(String(500), nullable=True)
    data_type = Column(String(20), nullable=False, default="string")  # string, int, float, bool, json
    updated_at = Column(DateTime, nullable=False, default=func.now(), onupdate=func.now())
    updated_by = Column(String(100), nullable=True)
    
    __table_args__ = (
        Index("idx_configuration_key", "key"),
    )
    
    def get_value(self) -> Any:
        """Get value with proper type conversion."""
        if self.data_type == "int":
            return int(self.value)
        elif self.data_type == "float":
            return float(self.value)
        elif self.data_type == "bool":
            return self.value.lower() in ("true", "1", "yes", "on")
        elif self.data_type == "json":
            try:
                return json.loads(self.value)
            except (json.JSONDecodeError, TypeError):
                return {}
        else:
            return self.value
    
    def set_value(self, value: Any) -> None:
        """Set value with proper type conversion."""
        if isinstance(value, bool):
            self.value = str(value).lower()
            self.data_type = "bool"
        elif isinstance(value, int):
            self.value = str(value)
            self.data_type = "int"
        elif isinstance(value, float):
            self.value = str(value)
            self.data_type = "float"
        elif isinstance(value, (dict, list)):
            self.value = json.dumps(value)
            self.data_type = "json"
        else:
            self.value = str(value)
            self.data_type = "string"


class BackupMetadata(Base):
    """Model for backup metadata."""
    
    __tablename__ = "backup_metadata"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    backup_type = Column(String(50), nullable=False, index=True)  # full, incremental, schema
    backup_path = Column(String(1000), nullable=False)
    backup_size_mb = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, default=func.now(), index=True)
    completed_at = Column(DateTime, nullable=True)
    status = Column(String(20), nullable=False, default="running")  # running, completed, failed
    checksum = Column(String(64), nullable=True)  # SHA-256 checksum
    metadata_info = Column(Text, nullable=True)  # JSON with additional metadata
    created_by = Column(String(100), nullable=True)
    
    __table_args__ = (
        Index("idx_backup_metadata_created_at", "created_at"),
    )