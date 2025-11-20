# Database Schema Documentation

## Overview
This document provides a comprehensive overview of the MAFA database schema, including table structures, relationships, indexes, and constraints. The database is built on PostgreSQL and uses UUIDs for primary keys.

---

**Last Updated:** November 19, 2025  
**Version:** 1.0.0  
**Maintainer:** MAFA Database Team  
**Estimated Reading Time:** 25-30 minutes

---

## Database Architecture

### Core Database Structure
```
┌─────────────────────────────────────────────────────────────┐
│                      PostgreSQL Database                    │
│                          (mwa_core)                        │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
┌───────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
│   Core       │  │  Contact    │  │  Search     │
│   Entities   │  │  Data       │  │  Criteria    │
│ (users, etc)│  │             │  │             │
└──────┬───────┘  └──────┬──────┘  └──────┬──────┘
       │                 │                 │
       └─────────────────┼─────────────────┘
                         │
        ┌────────────────┼─────────────────┐
        │                │                 │
┌───────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
│   Listing    │  │ Notification │  │    Audit    │
│   Data       │  │  History     │  │   & Logs    │
└──────────────┘  └─────────────┘  └─────────────┘
```

### Database Configuration
```sql
-- Database creation and basic configuration
CREATE DATABASE mwa_core
    WITH 
    OWNER = mwa_core_user
    ENCODING = 'UTF8'
    LC_COLLATE = 'en_US.UTF-8'
    LC_CTYPE = 'en_US.UTF-8'
    TEMPLATE = template0;

-- Extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- Role creation
CREATE ROLE mwa_core_user WITH
    LOGIN
    PASSWORD 'secure_password'
    NOSUPERUSER
    NOCREATEDB
    NOCREATEROLE
    NOINHERIT;

GRANT ALL PRIVILEGES ON DATABASE mwa_core TO mwa_core_user;
```

---

## Core Tables

### Users Table
```sql
-- users: User authentication and profile information
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    phone VARCHAR(20),
    date_of_birth DATE,
    gender VARCHAR(10),
    nationality VARCHAR(100),
    preferred_language VARCHAR(10) DEFAULT 'de',
    timezone VARCHAR(50) DEFAULT 'Europe/Berlin',
    
    -- Account status
    is_active BOOLEAN DEFAULT true,
    is_verified BOOLEAN DEFAULT false,
    email_verification_token VARCHAR(255),
    password_reset_token VARCHAR(255),
    password_reset_expires TIMESTAMP,
    
    -- Timestamps
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE,
    deleted_at TIMESTAMP WITH TIME ZONE,
    
    -- Preferences
    preferences JSONB DEFAULT '{}',
    
    -- GDPR compliance
    gdpr_consent_given BOOLEAN DEFAULT false,
    gdpr_consent_date TIMESTAMP WITH TIME ZONE,
    data_processing_consent BOOLEAN DEFAULT false,
    marketing_consent BOOLEAN DEFAULT false,
    analytics_consent BOOLEAN DEFAULT false
);

-- Indexes for users
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_is_active ON users(is_active);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_deleted_at ON users(deleted_at);
CREATE INDEX idx_users_preferences ON users USING GIN(preferences);

-- Triggers for updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_users_updated_at 
    BEFORE UPDATE ON users 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Contacts Table
```sql
-- contacts: Extracted contact information from listings
CREATE TABLE contacts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    
    -- Contact identification
    name VARCHAR(255) NOT NULL,
    name_variations TEXT[], -- Alternative spellings/names
    
    -- Encrypted contact information
    phone_encrypted BYTEA,
    email_encrypted BYTEA,
    address_encrypted BYTEA,
    website_encrypted BYTEA,
    
    -- Contact metadata
    contact_type VARCHAR(50) NOT NULL, -- 'landlord', 'agent', 'owner', 'contact_person'
    source_provider VARCHAR(50) NOT NULL, -- 'immoscout', 'wg_gesucht', 'manual'
    confidence_score DECIMAL(3,2) DEFAULT 0.0, -- 0.00 to 1.00
    
    -- Contact validation
    is_verified BOOLEAN DEFAULT false,
    verification_method VARCHAR(50), -- 'manual', 'automated', 'cross_reference'
    verification_date TIMESTAMP WITH TIME ZONE,
    verification_notes TEXT,
    
    -- Contact quality metrics
    quality_score DECIMAL(3,2) DEFAULT 0.0, -- Derived quality score
    last_contacted TIMESTAMP WITH TIME ZONE,
    contact_frequency VARCHAR(20), -- 'never', 'rare', 'regular', 'frequent'
    
    -- Tags and categorization
    tags TEXT[],
    category VARCHAR(100), -- 'premium', 'standard', 'unverified'
    notes TEXT,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    is_blacklisted BOOLEAN DEFAULT false,
    blacklisted_reason TEXT,
    
    -- Audit information
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id),
    
    -- Extraction metadata
    extraction_method VARCHAR(50), -- 'ocr', 'pdf', 'manual', 'api'
    extraction_confidence DECIMAL(3,2),
    source_listing_id UUID, -- Reference to original listing
    extraction_date TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for contacts
CREATE INDEX idx_contacts_user_id ON contacts(user_id);
CREATE INDEX idx_contacts_name ON contacts USING GIN(to_tsvector('german', name));
CREATE INDEX idx_contacts_source_provider ON contacts(source_provider);
CREATE INDEX idx_contacts_contact_type ON contacts(contact_type);
CREATE INDEX idx_contacts_confidence_score ON contacts(confidence_score);
CREATE INDEX idx_contacts_quality_score ON contacts(quality_score);
CREATE INDEX idx_contacts_is_active ON contacts(is_active);
CREATE INDEX idx_contacts_tags ON contacts USING GIN(tags);
CREATE INDEX idx_contacts_created_at ON contacts(created_at);
CREATE INDEX idx_contacts_extraction_method ON contacts(extraction_method);
CREATE INDEX idx_contacts_source_listing_id ON contacts(source_listing_id);

CREATE TRIGGER update_contacts_updated_at 
    BEFORE UPDATE ON contacts 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Listings Table
```sql
-- listings: Real estate listings from various providers
CREATE TABLE listings (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Provider information
    provider VARCHAR(50) NOT NULL, -- 'immoscout', 'wg_gesucht'
    provider_listing_id VARCHAR(255) NOT NULL,
    provider_url TEXT,
    provider_created_at TIMESTAMP WITH TIME ZONE,
    provider_updated_at TIMESTAMP WITH TIME ZONE,
    
    -- Property details
    title VARCHAR(500) NOT NULL,
    description TEXT,
    property_type VARCHAR(100), -- 'apartment', 'house', 'room', 'studio'
    furnishing_level VARCHAR(50), -- 'furnished', 'partially_furnished', 'unfurnished'
    
    -- Location
    street VARCHAR(255),
    house_number VARCHAR(20),
    postal_code VARCHAR(10),
    city VARCHAR(100) NOT NULL,
    district VARCHAR(100),
    latitude DECIMAL(10,8),
    longitude DECIMAL(11,8),
    
    -- Financial information
    rent_netto DECIMAL(10,2),
    rent_brutto DECIMAL(10,2),
    additional_costs DECIMAL(10,2),
    deposit DECIMAL(10,2),
    currency VARCHAR(3) DEFAULT 'EUR',
    
    -- Property specifications
    rooms DECIMAL(3,1),
    bedroom_count INTEGER,
    bathroom_count INTEGER,
    living_area DECIMAL(8,2), -- square meters
    total_area DECIMAL(8,2), -- square meters
    floor VARCHAR(50),
    total_floors INTEGER,
    year_built INTEGER,
    condition VARCHAR(50), -- 'new', 'renovated', 'good', 'needs_renovation'
    
    -- Availability
    available_from DATE,
    available_until DATE,
    lease_duration_min INTEGER, -- months
    lease_duration_max INTEGER, -- months
    
    -- Media and content
    images TEXT[], -- URLs to images
    virtual_tour_url TEXT,
    floor_plan_url TEXT,
    
    -- Contact information (denormalized for quick access)
    contact_name VARCHAR(255),
    contact_phone_encrypted BYTEA,
    contact_email_encrypted BYTEA,
    
    -- Processing status
    is_processed BOOLEAN DEFAULT false,
    processing_errors TEXT[],
    last_processed_at TIMESTAMP WITH TIME ZONE,
    
    -- Quality and scoring
    listing_quality_score DECIMAL(3,2) DEFAULT 0.0,
    relevance_score DECIMAL(3,2) DEFAULT 0.0,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    is_archived BOOLEAN DEFAULT false,
    is_favorite BOOLEAN DEFAULT false,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    first_seen_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    UNIQUE(provider, provider_listing_id)
);

-- Indexes for listings
CREATE INDEX idx_listings_provider ON listings(provider);
CREATE INDEX idx_listings_provider_listing_id ON listings(provider_listing_id);
CREATE INDEX idx_listings_city ON listings(city);
CREATE INDEX idx_listings_property_type ON listings(property_type);
CREATE INDEX idx_listings_rent_netto ON listings(rent_netto);
CREATE INDEX idx_listings_rooms ON listings(rooms);
CREATE INDEX idx_listings_available_from ON listings(available_from);
CREATE INDEX idx_listings_is_active ON listings(is_active);
CREATE INDEX idx_listings_is_processed ON listings(is_processed);
CREATE INDEX idx_listings_listing_quality_score ON listings(listing_quality_score);
CREATE INDEX idx_listings_relevance_score ON listings(relevance_score);
CREATE INDEX idx_listings_created_at ON listings(created_at);
CREATE INDEX idx_listings_last_seen_at ON listings(last_seen_at);
CREATE INDEX idx_listings_location ON listings USING GIST(
    ll_to_earth(latitude, longitude)
);

-- Full-text search indexes
CREATE INDEX idx_listings_title_search ON listings USING GIN(to_tsvector('german', title));
CREATE INDEX idx_listings_description_search ON listings USING GIN(to_tsvector('german', description));

CREATE TRIGGER update_listings_updated_at 
    BEFORE UPDATE ON listings 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

---

## Search and Discovery Tables

### Search Criteria Table
```sql
-- search_criteria: User-defined search parameters
CREATE TABLE search_criteria (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    
    -- Location criteria
    preferred_cities TEXT[] NOT NULL, -- Array of preferred cities
    preferred_districts TEXT[], -- Array of preferred districts
    excluded_cities TEXT[], -- Cities to avoid
    excluded_districts TEXT[], -- Districts to avoid
    max_distance_km INTEGER DEFAULT 50, -- Maximum distance from preferred locations
    
    -- Property criteria
    property_types TEXT[] DEFAULT ARRAY['apartment', 'house'], -- Allowed property types
    min_rooms DECIMAL(3,1),
    max_rooms DECIMAL(3,1),
    min_area DECIMAL(8,2),
    max_area DECIMAL(8,2),
    min_floor INTEGER,
    max_floor INTEGER,
    
    -- Financial criteria
    min_rent_netto DECIMAL(10,2),
    max_rent_netto DECIMAL(10,2),
    max_additional_costs DECIMAL(10,2),
    max_deposit DECIMAL(10,2),
    
    -- Availability criteria
    available_from DATE,
    available_until DATE,
    min_lease_duration INTEGER, -- months
    max_lease_duration INTEGER, -- months
    
    -- Quality criteria
    min_quality_score DECIMAL(3,2) DEFAULT 0.5,
    require_verified_contact BOOLEAN DEFAULT false,
    
    -- Timing criteria
    search_frequency VARCHAR(20) DEFAULT 'daily', -- 'hourly', 'daily', 'weekly'
    last_run_at TIMESTAMP WITH TIME ZONE,
    next_run_at TIMESTAMP WITH TIME ZONE,
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    auto_apply BOOLEAN DEFAULT false, -- Automatically apply to new matches
    
    -- Metadata
    tags TEXT[],
    notes TEXT,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id),
    updated_by UUID REFERENCES users(id)
);

-- Indexes for search_criteria
CREATE INDEX idx_search_criteria_user_id ON search_criteria(user_id);
CREATE INDEX idx_search_criteria_is_active ON search_criteria(is_active);
CREATE INDEX idx_search_criteria_next_run_at ON search_criteria(next_run_at);
CREATE INDEX idx_search_criteria_created_at ON search_criteria(created_at);
CREATE INDEX idx_search_criteria_tags ON search_criteria USING GIN(tags);

CREATE TRIGGER update_search_criteria_updated_at 
    BEFORE UPDATE ON search_criteria 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Contact Discovery Jobs Table
```sql
-- contact_discovery_jobs: Tracking contact extraction jobs
CREATE TABLE contact_discovery_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    search_criteria_id UUID REFERENCES search_criteria(id) ON DELETE CASCADE,
    
    -- Job identification
    job_type VARCHAR(50) NOT NULL, -- 'listing_scrape', 'contact_extraction', 'validation'
    status VARCHAR(20) NOT NULL DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed', 'cancelled'
    
    -- Job parameters
    parameters JSONB NOT NULL DEFAULT '{}',
    provider_config JSONB,
    
    -- Results
    listings_processed INTEGER DEFAULT 0,
    contacts_extracted INTEGER DEFAULT 0,
    contacts_validated INTEGER DEFAULT 0,
    errors_count INTEGER DEFAULT 0,
    
    -- Timing
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    estimated_duration INTERVAL,
    actual_duration INTERVAL,
    
    -- Progress tracking
    progress_percentage INTEGER DEFAULT 0,
    current_stage VARCHAR(100),
    
    -- Error handling
    error_messages TEXT[],
    retry_count INTEGER DEFAULT 0,
    max_retries INTEGER DEFAULT 3,
    
    -- Output
    result_data JSONB,
    output_files TEXT[], -- Paths to generated files
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    created_by UUID REFERENCES users(id)
);

-- Indexes for contact_discovery_jobs
CREATE INDEX idx_contact_discovery_jobs_user_id ON contact_discovery_jobs(user_id);
CREATE INDEX idx_contact_discovery_jobs_search_criteria_id ON contact_discovery_jobs(search_criteria_id);
CREATE INDEX idx_contact_discovery_jobs_status ON contact_discovery_jobs(status);
CREATE INDEX idx_contact_discovery_jobs_job_type ON contact_discovery_jobs(job_type);
CREATE INDEX idx_contact_discovery_jobs_started_at ON contact_discovery_jobs(started_at);
CREATE INDEX idx_contact_discovery_jobs_created_at ON contact_discovery_jobs(created_at);
```

### Contact Discovery Results Table
```sql
-- contact_discovery_results: Results from contact extraction processes
CREATE TABLE contact_discovery_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID NOT NULL REFERENCES contact_discovery_jobs(id) ON DELETE CASCADE,
    listing_id UUID REFERENCES listings(id) ON DELETE CASCADE,
    contact_id UUID REFERENCES contacts(id) ON DELETE CASCADE,
    
    -- Extraction details
    extraction_method VARCHAR(50) NOT NULL, -- 'ocr', 'pdf', 'api', 'web_scraping'
    confidence_score DECIMAL(3,2) NOT NULL,
    
    -- Raw extracted data
    raw_data JSONB NOT NULL,
    extracted_fields JSONB NOT NULL,
    
    -- Processing results
    validation_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'valid', 'invalid', 'uncertain'
    validation_errors TEXT[],
    
    -- Quality metrics
    data_completeness DECIMAL(3,2), -- Percentage of required fields populated
    extraction_accuracy DECIMAL(3,2), -- Estimated accuracy of extraction
    duplicate_probability DECIMAL(3,2), -- Likelihood this is a duplicate
    
    -- Processing metadata
    processing_time_ms INTEGER,
    processing_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    -- Status
    is_final BOOLEAN DEFAULT false,
    is_accepted BOOLEAN DEFAULT false,
    rejection_reason TEXT,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for contact_discovery_results
CREATE INDEX idx_contact_discovery_results_job_id ON contact_discovery_results(job_id);
CREATE INDEX idx_contact_discovery_results_listing_id ON contact_discovery_results(listing_id);
CREATE INDEX idx_contact_discovery_results_contact_id ON contact_discovery_results(contact_id);
CREATE INDEX idx_contact_discovery_results_extraction_method ON contact_discovery_results(extraction_method);
CREATE INDEX idx_contact_discovery_results_confidence_score ON contact_discovery_results(confidence_score);
CREATE INDEX idx_contact_discovery_results_validation_status ON contact_discovery_results(validation_status);
CREATE INDEX idx_contact_discovery_results_processing_timestamp ON contact_discovery_results(processing_timestamp);
```

---

## Notification and Communication Tables

### Notifications Table
```sql
-- notifications: User notifications and alerts
CREATE TABLE notifications (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Notification content
    type VARCHAR(50) NOT NULL, -- 'new_listing', 'contact_found', 'system_alert', 'reminder'
    title VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    
    -- Notification data
    data JSONB DEFAULT '{}', -- Additional notification-specific data
    action_url TEXT, -- URL for notification action
    
    -- Delivery preferences
    delivery_method VARCHAR(20) DEFAULT 'app', -- 'app', 'email', 'sms', 'push'
    delivery_status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'sent', 'delivered', 'failed'
    delivery_attempts INTEGER DEFAULT 0,
    max_delivery_attempts INTEGER DEFAULT 3,
    
    -- Priority and urgency
    priority VARCHAR(10) DEFAULT 'normal', -- 'low', 'normal', 'high', 'urgent'
    is_urgent BOOLEAN DEFAULT false,
    
    -- Status
    is_read BOOLEAN DEFAULT false,
    read_at TIMESTAMP WITH TIME ZONE,
    is_archived BOOLEAN DEFAULT false,
    
    -- Scheduling
    scheduled_for TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Metadata
    category VARCHAR(50), -- 'search_results', 'system', 'billing', 'account'
    tags TEXT[],
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for notifications
CREATE INDEX idx_notifications_user_id ON notifications(user_id);
CREATE INDEX idx_notifications_type ON notifications(type);
CREATE INDEX idx_notifications_delivery_status ON notifications(delivery_status);
CREATE INDEX idx_notifications_is_read ON notifications(is_read);
CREATE INDEX idx_notifications_priority ON notifications(priority);
CREATE INDEX idx_notifications_created_at ON notifications(created_at);
CREATE INDEX idx_notifications_category ON notifications(category);
CREATE INDEX idx_notifications_tags ON notifications USING GIN(tags);

CREATE TRIGGER update_notifications_updated_at 
    BEFORE UPDATE ON notifications 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Notification Channels Table
```sql
-- notification_channels: User notification channel preferences
CREATE TABLE notification_channels (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- Channel configuration
    channel_type VARCHAR(20) NOT NULL, -- 'email', 'sms', 'push', 'discord', 'telegram'
    channel_name VARCHAR(50) NOT NULL, -- User-defined name for the channel
    destination VARCHAR(255) NOT NULL, -- Email, phone, device token, etc.
    
    -- Verification
    is_verified BOOLEAN DEFAULT false,
    verification_code VARCHAR(10),
    verification_expires TIMESTAMP WITH TIME ZONE,
    verified_at TIMESTAMP WITH TIME ZONE,
    
    -- Preferences
    is_active BOOLEAN DEFAULT true,
    is_primary BOOLEAN DEFAULT false,
    
    -- Notification types enabled for this channel
    enabled_notification_types TEXT[] DEFAULT ARRAY['new_listing', 'contact_found'],
    
    -- Rate limiting
    rate_limit_per_hour INTEGER DEFAULT 10,
    rate_limit_per_day INTEGER DEFAULT 100,
    
    -- Metadata
    metadata JSONB DEFAULT '{}', -- Channel-specific settings
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(user_id, channel_type, destination)
);

-- Indexes for notification_channels
CREATE INDEX idx_notification_channels_user_id ON notification_channels(user_id);
CREATE INDEX idx_notification_channels_channel_type ON notification_channels(channel_type);
CREATE INDEX idx_notification_channels_is_active ON notification_channels(is_active);
CREATE INDEX idx_notification_channels_is_primary ON notification_channels(is_primary);
```

---

## System and Audit Tables

### System Configuration Table
```sql
-- system_configuration: Global system settings
CREATE TABLE system_configuration (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    key VARCHAR(255) UNIQUE NOT NULL,
    value JSONB NOT NULL,
    data_type VARCHAR(20) NOT NULL, -- 'string', 'number', 'boolean', 'object', 'array'
    description TEXT,
    
    -- Metadata
    category VARCHAR(100), -- 'api', 'scraper', 'notification', 'security'
    is_sensitive BOOLEAN DEFAULT false,
    is_public BOOLEAN DEFAULT false,
    
    -- Validation
    validation_rules JSONB, -- JSON schema or validation rules
    
    -- Status
    is_active BOOLEAN DEFAULT true,
    requires_restart BOOLEAN DEFAULT false,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_by UUID REFERENCES users(id),
    
    -- Constraints
    CHECK (data_type IN ('string', 'number', 'boolean', 'object', 'array'))
);

-- Indexes for system_configuration
CREATE INDEX idx_system_configuration_key ON system_configuration(key);
CREATE INDEX idx_system_configuration_category ON system_configuration(category);
CREATE INDEX idx_system_configuration_is_active ON system_configuration(is_active);
CREATE INDEX idx_system_configuration_is_sensitive ON system_configuration(is_sensitive);

CREATE TRIGGER update_system_configuration_updated_at 
    BEFORE UPDATE ON system_configuration 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

### Audit Logs Table
```sql
-- audit_logs: Comprehensive audit trail
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- User context
    user_id UUID REFERENCES users(id),
    session_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    
    -- Action details
    action VARCHAR(100) NOT NULL, -- 'create', 'update', 'delete', 'login', 'logout'
    entity_type VARCHAR(100) NOT NULL, -- 'user', 'contact', 'listing', 'search_criteria'
    entity_id UUID,
    
    -- Change details
    old_values JSONB,
    new_values JSONB,
    changed_fields TEXT[],
    
    -- Request context
    request_id VARCHAR(255),
    request_method VARCHAR(10),
    request_path TEXT,
    request_ip INET,
    request_user_agent TEXT,
    
    -- System context
    service_name VARCHAR(100), -- 'api', 'scraper', 'dashboard'
    service_version VARCHAR(50),
    server_name VARCHAR(255),
    
    -- Result
    success BOOLEAN NOT NULL DEFAULT true,
    error_message TEXT,
    error_code VARCHAR(50),
    
    -- Risk assessment
    risk_level VARCHAR(10) DEFAULT 'low', -- 'low', 'medium', 'high', 'critical'
    
    -- Metadata
    metadata JSONB DEFAULT '{}',
    
    -- Timestamp
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for audit_logs
CREATE INDEX idx_audit_logs_user_id ON audit_logs(user_id);
CREATE INDEX idx_audit_logs_action ON audit_logs(action);
CREATE INDEX idx_audit_logs_entity_type ON audit_logs(entity_type);
CREATE INDEX idx_audit_logs_entity_id ON audit_logs(entity_id);
CREATE INDEX idx_audit_logs_success ON audit_logs(success);
CREATE INDEX idx_audit_logs_risk_level ON audit_logs(risk_level);
CREATE INDEX idx_audit_logs_created_at ON audit_logs(created_at);
CREATE INDEX idx_audit_logs_request_id ON audit_logs(request_id);

-- Partitioning for audit_logs (by month for better performance)
CREATE TABLE audit_logs_2025_11 PARTITION OF audit_logs
FOR VALUES FROM ('2025-11-01') TO ('2025-12-01');
```

### API Rate Limiting Table
```sql
-- api_rate_limits: Rate limiting tracking
CREATE TABLE api_rate_limits (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Identification
    identifier VARCHAR(255) NOT NULL, -- IP address, user ID, or API key
    identifier_type VARCHAR(20) NOT NULL, -- 'ip', 'user', 'api_key'
    
    -- Rate limiting
    endpoint VARCHAR(255) NOT NULL,
    limit_per_window INTEGER NOT NULL,
    window_seconds INTEGER NOT NULL,
    
    -- Tracking
    request_count INTEGER DEFAULT 0,
    window_start TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    window_end TIMESTAMP WITH TIME ZONE,
    
    -- Status
    is_blocked BOOLEAN DEFAULT false,
    block_expires_at TIMESTAMP WITH TIME ZONE,
    
    -- Audit
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(identifier, identifier_type, endpoint)
);

-- Indexes for api_rate_limits
CREATE INDEX idx_api_rate_limits_identifier ON api_rate_limits(identifier);
CREATE INDEX idx_api_rate_limits_endpoint ON api_rate_limits(endpoint);
CREATE INDEX idx_api_rate_limits_is_blocked ON api_rate_limits(is_blocked);
CREATE INDEX idx_api_rate_limits_window_start ON api_rate_limits(window_start);

CREATE TRIGGER update_api_rate_limits_updated_at 
    BEFORE UPDATE ON api_rate_limits 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
```

---

## Indexes and Performance Optimization

### Composite Indexes
```sql
-- Composite indexes for common query patterns
CREATE INDEX idx_contacts_user_active ON contacts(user_id, is_active) WHERE is_active = true;
CREATE INDEX idx_listings_city_type_active ON listings(city, property_type) WHERE is_active = true;
CREATE INDEX idx_listings_rent_rooms ON listings(rent_netto, rooms) WHERE is_active = true;
CREATE INDEX idx_notifications_user_unread ON notifications(user_id, is_read) WHERE is_read = false;

-- Partial indexes for performance
CREATE INDEX idx_listings_processed ON listings(id) WHERE is_processed = false;
CREATE INDEX idx_users_active ON users(id) WHERE is_active = true AND deleted_at IS NULL;
CREATE INDEX idx_contacts_high_quality ON contacts(id) WHERE quality_score >= 0.8;
```

### Full-Text Search Indexes
```sql
-- German text search configuration
CREATE TEXT SEARCH CONFIGURATION german_custom (COPY = german);

-- Custom dictionaries for real estate terms
CREATE DICTIONARY realestate_synonyms (
    Template = synonym,
    Synonyms = realestate_synonyms
);

-- Text search indexes with custom configuration
CREATE INDEX idx_listings_search_german ON listings USING GIN(
    to_tsvector('german_custom', title || ' ' || COALESCE(description, ''))
);

CREATE INDEX idx_contacts_search_german ON contacts USING GIN(
    to_tsvector('german_custom', name)
);
```

---

## Database Functions and Triggers

### Data Quality Functions
```sql
-- Function to calculate contact quality score
CREATE OR REPLACE FUNCTION calculate_contact_quality_score(contact_data JSONB)
RETURNS DECIMAL(3,2) AS $$
DECLARE
    score DECIMAL(3,2) := 0.0;
    field_count INTEGER := 0;
    total_fields INTEGER := 5; -- name, phone, email, address, website
BEGIN
    -- Check presence of fields (weight: 0.1 each)
    IF contact_data ? 'name' THEN
        score := score + 0.1;
        field_count := field_count + 1;
    END IF;
    
    IF contact_data ? 'phone' THEN
        score := score + 0.1;
        field_count := field_count + 1;
    END IF;
    
    IF contact_data ? 'email' THEN
        score := score + 0.1;
        field_count := field_count + 1;
    END IF;
    
    IF contact_data ? 'address' THEN
        score := score + 0.1;
        field_count := field_count + 1;
    END IF;
    
    IF contact_data ? 'website' THEN
        score := score + 0.1;
        field_count := field_count + 1;
    END IF;
    
    -- Bonus for data completeness (up to 0.3)
    IF field_count > 0 THEN
        score := score + (field_count::DECIMAL / total_fields * 0.3);
    END IF;
    
    -- Cap at 1.0
    RETURN LEAST(score, 1.0);
END;
$$ LANGUAGE plpgsql;

-- Function to validate email format
CREATE OR REPLACE FUNCTION is_valid_email(email TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN email ~* '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$';
END;
$$ LANGUAGE plpgsql;

-- Function to validate phone number (German format)
CREATE OR REPLACE FUNCTION is_valid_german_phone(phone TEXT)
RETURNS BOOLEAN AS $$
BEGIN
    RETURN phone ~* '^(\+49|0)[1-9][0-9]{1,14}$';
END;
$$ LANGUAGE plpgsql;

-- Function to calculate listing relevance score
CREATE OR REPLACE FUNCTION calculate_listing_relevance(
    listing_data JSONB,
    criteria_data JSONB
)
RETURNS DECIMAL(3,2) AS $$
DECLARE
    score DECIMAL(3,2) := 0.0;
    max_score DECIMAL(3,2) := 1.0;
BEGIN
    -- Location match (40% weight)
    IF criteria_data ? 'preferred_cities' AND listing_data ? 'city' THEN
        IF listing_data->>'city' = ANY(ARRAY(SELECT jsonb_array_elements_text(criteria_data->'preferred_cities'))) THEN
            score := score + 0.4;
        END IF;
    END IF;
    
    -- Property type match (20% weight)
    IF criteria_data ? 'property_types' AND listing_data ? 'property_type' THEN
        IF listing_data->>'property_type' = ANY(ARRAY(SELECT jsonb_array_elements_text(criteria_data->'property_types'))) THEN
            score := score + 0.2;
        END IF;
    END IF;
    
    -- Price range match (25% weight)
    IF criteria_data ? 'min_rent_netto' AND criteria_data ? 'max_rent_netto' 
       AND listing_data ? 'rent_netto' THEN
        DECLARE
            min_rent DECIMAL := criteria_data->>'min_rent_netto'::DECIMAL;
            max_rent DECIMAL := criteria_data->>'max_rent_netto'::DECIMAL;
            listing_rent DECIMAL := listing_data->>'rent_netto'::DECIMAL;
        BEGIN
            IF listing_rent BETWEEN min_rent AND max_rent THEN
                score := score + 0.25;
            ELSIF listing_rent BETWEEN min_rent AND (max_rent * 1.1) THEN
                score := score + 0.15; -- Partial match
            END IF;
        END;
    END IF;
    
    -- Room count match (15% weight)
    IF criteria_data ? 'min_rooms' AND criteria_data ? 'max_rooms' 
       AND listing_data ? 'rooms' THEN
        DECLARE
            min_rooms DECIMAL := criteria_data->>'min_rooms'::DECIMAL;
            max_rooms DECIMAL := criteria_data->>'max_rooms'::DECIMAL;
            listing_rooms DECIMAL := listing_data->>'rooms'::DECIMAL;
        BEGIN
            IF listing_rooms BETWEEN min_rooms AND max_rooms THEN
                score := score + 0.15;
            END IF;
        END;
    END IF;
    
    RETURN LEAST(score, max_score);
END;
$$ LANGUAGE plpgsql;
```

### Automatic Triggers
```sql
-- Trigger to automatically calculate contact quality score
CREATE OR REPLACE FUNCTION update_contact_quality_score()
RETURNS TRIGGER AS $$
BEGIN
    NEW.quality_score := calculate_contact_quality_score(
        jsonb_build_object(
            'name', NEW.name,
            'phone_encrypted', NEW.phone_encrypted,
            'email_encrypted', NEW.email_encrypted,
            'address_encrypted', NEW.address_encrypted,
            'website_encrypted', NEW.website_encrypted
        )
    );
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_contact_quality_score
    BEFORE INSERT OR UPDATE ON contacts
    FOR EACH ROW EXECUTE FUNCTION update_contact_quality_score();

-- Trigger to update listing search indices
CREATE OR REPLACE FUNCTION update_listing_search_indices()
RETURNS TRIGGER AS $$
BEGIN
    -- Update full-text search indices
    -- This could be implemented with external search engines like Elasticsearch
    
    -- Update location-based search indices
    -- Could implement with PostGIS for geo-spatial queries
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_listing_search_indices
    AFTER INSERT OR UPDATE ON listings
    FOR EACH ROW EXECUTE FUNCTION update_listing_search_indices();

-- Trigger to clean up expired rate limits
CREATE OR REPLACE FUNCTION cleanup_expired_rate_limits()
RETURNS VOID AS $$
BEGIN
    DELETE FROM api_rate_limits 
    WHERE window_end < CURRENT_TIMESTAMP - INTERVAL '1 day';
END;
$$ LANGUAGE plpgsql;
```

---

## Data Retention and Cleanup

### Automated Cleanup Procedures
```sql
-- Function to archive old data
CREATE OR REPLACE FUNCTION archive_old_data()
RETURNS VOID AS $$
DECLARE
    cutoff_date TIMESTAMP WITH TIME ZONE;
BEGIN
    -- Archive old audit logs (keep for 1 year)
    cutoff_date := CURRENT_TIMESTAMP - INTERVAL '1 year';
    
    -- Move old audit logs to archive table or external storage
    INSERT INTO audit_logs_archive 
    SELECT * FROM audit_logs 
    WHERE created_at < cutoff_date;
    
    DELETE FROM audit_logs WHERE created_at < cutoff_date;
    
    -- Clean up old notifications (keep for 6 months)
    cutoff_date := CURRENT_TIMESTAMP - INTERVAL '6 months';
    
    DELETE FROM notifications 
    WHERE created_at < cutoff_date 
    AND is_read = true;
    
    -- Clean up old rate limit records
    DELETE FROM api_rate_limits 
    WHERE window_end < CURRENT_TIMESTAMP - INTERVAL '1 day';
    
    -- Clean up old failed jobs
    DELETE FROM contact_discovery_jobs 
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '3 months' 
    AND status = 'failed';
    
    -- Update table statistics
    ANALYZE;
    
    RAISE NOTICE 'Data cleanup completed at %', CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- Schedule cleanup job (requires pg_cron extension)
-- SELECT cron.schedule('cleanup-old-data', '0 2 * * *', 'SELECT archive_old_data();');
```

---

## Security and Permissions

### Row Level Security (RLS) Policies
```sql
-- Enable RLS on user-specific tables
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE contacts ENABLE ROW LEVEL SECURITY;
ALTER TABLE search_criteria ENABLE ROW LEVEL SECURITY;
ALTER TABLE notifications ENABLE ROW LEVEL SECURITY;
ALTER TABLE notification_channels ENABLE ROW LEVEL SECURITY;

-- Users can only see their own data
CREATE POLICY users_own_data ON users
    FOR ALL TO mwa_core_user
    USING (id = current_setting('app.current_user_id', true)::UUID);

CREATE POLICY contacts_own_data ON contacts
    FOR ALL TO mwa_core_user
    USING (user_id = current_setting('app.current_user_id', true)::UUID);

CREATE POLICY search_criteria_own_data ON search_criteria
    FOR ALL TO mwa_core_user
    USING (user_id = current_setting('app.current_user_id', true)::UUID);

CREATE POLICY notifications_own_data ON notifications
    FOR ALL TO mwa_core_user
    USING (user_id = current_setting('app.current_user_id', true)::UUID);

CREATE POLICY notification_channels_own_data ON notification_channels
    FOR ALL TO mwa_core_user
    USING (user_id = current_setting('app.current_user_id', true)::UUID);

-- Admin users can see all data
CREATE POLICY admin_all_data ON users
    FOR ALL TO mwa_core_user
    USING (
        EXISTS (
            SELECT 1 FROM users 
            WHERE id = current_setting('app.current_user_id', true)::UUID 
            AND is_active = true
            AND 'admin' = ANY(roles)
        )
    );
```

### Database Roles and Permissions
```sql
-- Application role (for web application)
CREATE ROLE mwa_app_role;
GRANT CONNECT ON DATABASE mwa_core TO mwa_app_role;
GRANT USAGE ON SCHEMA public TO mwa_app_role;

-- Grant specific permissions
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO mwa_app_role;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO mwa_app_role;

-- Read-only role (for reporting and analytics)
CREATE ROLE mwa_readonly_role;
GRANT CONNECT ON DATABASE mwa_core TO mwa_readonly_role;
GRANT USAGE ON SCHEMA public TO mwa_readonly_role;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO mwa_readonly_role;

-- Admin role (for database administration)
CREATE ROLE mwa_admin_role;
GRANT ALL PRIVILEGES ON DATABASE mwa_core TO mwa_admin_role;
GRANT ALL PRIVILEGES ON SCHEMA public TO mwa_admin_role;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO mwa_admin_role;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO mwa_admin_role;
```

---

## Backup and Recovery

### Backup Strategy
```sql
-- Logical backup using pg_dump
-- Example: pg_dump -h localhost -U mwa_core_user -d mwa_core --schema-only > schema_backup.sql

-- Point-in-time recovery setup
-- Enable WAL archiving in postgresql.conf
wal_level = replica
archive_mode = on
archive_command = 'cp %p /var/lib/postgresql/archive/%f'
max_wal_senders = 3
checkpoint_segments = 16

-- Backup validation function
CREATE OR REPLACE FUNCTION validate_backup_integrity()
RETURNS TABLE (
    table_name TEXT,
    row_count BIGINT,
    last_modified TIMESTAMP WITH TIME ZONE,
    issues TEXT[]
) AS $$
DECLARE
    table_record RECORD;
    issue_list TEXT[];
BEGIN
    FOR table_record IN 
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_type = 'BASE TABLE'
        ORDER BY table_name
    LOOP
        BEGIN
            -- Check row counts for main tables
            EXECUTE format('SELECT COUNT(*) FROM %I', table_record.table_name) INTO row_count;
            
            -- Check for recent modifications
            EXECUTE format(
                'SELECT MAX(updated_at) FROM %I WHERE updated_at > NOW() - INTERVAL ''24 hours''',
                table_record.table_name
            ) INTO last_modified;
            
            issue_list := ARRAY[]::TEXT[];
            
            -- Add issues if any
            IF row_count = 0 AND table_record.table_name IN ('users', 'contacts') THEN
                issue_list := array_append(issue_list, 'Expected non-zero row count');
            END IF;
            
            RETURN QUERY SELECT 
                table_record.table_name,
                row_count,
                COALESCE(last_modified, '1970-01-01'::TIMESTAMP WITH TIME ZONE),
                issue_list;
                
        EXCEPTION WHEN OTHERS THEN
            RETURN QUERY SELECT 
                table_record.table_name,
                0::BIGINT,
                '1970-01-01'::TIMESTAMP WITH TIME ZONE,
                ARRAY['Error querying table: ' || SQLERRM];
        END;
    END LOOP;
END;
$$ LANGUAGE plpgsql;
```

---

## Performance Monitoring

### Database Performance Views
```sql
-- Create performance monitoring views
CREATE VIEW database_performance AS
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation,
    most_common_vals,
    most_common_freqs
FROM pg_stats
WHERE schemaname = 'public'
ORDER BY tablename, attname;

CREATE VIEW slow_queries AS
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    rows,
    100.0 * shared_blks_hit / nullif(shared_blks_hit + shared_blks_read, 0) AS hit_percent
FROM pg_stat_statements
WHERE mean_time > 100  -- Queries taking more than 100ms on average
ORDER BY mean_time DESC
LIMIT 20;

CREATE VIEW table_sizes AS
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size,
    pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

CREATE VIEW index_usage AS
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch,
    pg_size_pretty(pg_relation_size(indexrelname)) as index_size
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
```

---

## Migration Scripts

### Version Control for Schema Changes
```sql
-- Schema migration tracking table
CREATE TABLE schema_migrations (
    id SERIAL PRIMARY KEY,
    version VARCHAR(255) UNIQUE NOT NULL,
    description TEXT NOT NULL,
    applied_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    applied_by VARCHAR(255),
    checksum VARCHAR(64)
);

-- Example migration record
INSERT INTO schema_migrations (version, description, applied_by) 
VALUES ('001_initial_schema', 'Initial database schema creation', 'admin');

-- Function to check migration status
CREATE OR REPLACE FUNCTION get_migration_status()
RETURNS TABLE (
    version TEXT,
    description TEXT,
    applied_at TIMESTAMP WITH TIME ZONE,
    applied_by TEXT,
    applied BOOLEAN
) AS $$
BEGIN
    -- This would check against actual migration files
    -- For now, return current status
    RETURN QUERY
    SELECT 
        sm.version,
        sm.description,
        sm.applied_at,
        sm.applied_by,
        true as applied
    FROM schema_migrations sm
    ORDER BY sm.version;
END;
$$ LANGUAGE plpgsql;
```

---

## Related Documentation

- [Data Models](data-models.md) - Entity relationships and business logic
- [Contact Discovery System](contact-discovery.md) - Contact extraction and validation
- [System Overview](../architecture/system-overview.md) - Overall system architecture
- [Configuration Reference](../getting-started/configuration.md) - Database configuration
- [Security Guide](../operations/security.md) - Database security practices

---

**Database Support**: For database-related issues or questions, contact the database team or create an issue with the `database` label.