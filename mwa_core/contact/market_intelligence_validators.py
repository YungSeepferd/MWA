"""
Enhanced validation rules for Market Intelligence Contacts.

Provides specialized validation for market intelligence fields including
agency types, market areas, outreach history, and business intelligence data.
"""

import re
from typing import Dict, List, Optional, Any
from datetime import datetime

from .market_intelligence import (
    MarketIntelligenceContact, AgencyType, ContactMethod, LeadSource, OutreachHistoryEntry
)


class MarketIntelligenceValidator:
    """
    Validator for market intelligence contact fields with enhanced business logic.
    
    Provides validation for:
    - Agency type and business information
    - Market area classification
    - Outreach history integrity
    - Contact preference validation
    - Quality scoring validation
    """
    
    # Valid market area patterns for German real estate market
    GERMAN_MARKET_AREA_PATTERNS = [
        r'^[A-Za-zäöüß\s\-]+$',  # German city/district names
        r'^[A-Za-zäöüß\s\-]+\s+\([A-Za-zäöüß\s\-]+\)$',  # District (City) format
        r'^[A-Za-zäöüß\s\-]+\s+-\s+[A-Za-zäöüß\s\-]+$',  # City - District format
    ]
    
    # Valid position titles in real estate industry
    VALID_POSITIONS = [
        'property manager', 'property management', 'real estate agent',
        'landlord', 'owner', 'administrator', 'coordinator', 'director',
        'manager', 'assistant', 'specialist', 'consultant', 'broker'
    ]
    
    def validate_agency_type(self, agency_type: Optional[AgencyType]) -> List[str]:
        """Validate agency type selection."""
        errors = []
        
        if agency_type and not isinstance(agency_type, AgencyType):
            errors.append("Invalid agency type format")
        
        return errors
    
    def validate_position(self, position: Optional[str]) -> List[str]:
        """Validate position title."""
        errors = []
        
        if position:
            if len(position) > 100:
                errors.append("Position title too long (max 100 characters)")
            
            # Check for suspicious patterns
            suspicious_patterns = ['test', 'example', 'fake', 'dummy']
            if any(pattern in position.lower() for pattern in suspicious_patterns):
                errors.append("Position title contains suspicious patterns")
            
            # Validate against known position titles
            position_lower = position.lower()
            if not any(valid_position in position_lower for valid_position in self.VALID_POSITIONS):
                errors.append("Position title may not be relevant to real estate industry")
        
        return errors
    
    def validate_company_name(self, company_name: Optional[str]) -> List[str]:
        """Validate company name."""
        errors = []
        
        if company_name:
            if len(company_name) > 200:
                errors.append("Company name too long (max 200 characters)")
            
            # Check for suspicious patterns
            suspicious_patterns = ['test', 'example', 'fake', 'dummy']
            if any(pattern in company_name.lower() for pattern in suspicious_patterns):
                errors.append("Company name contains suspicious patterns")
            
            # Validate company name format
            if not re.match(r'^[A-Za-z0-9äöüß\s\-\&\.\,\(\)]+$', company_name):
                errors.append("Company name contains invalid characters")
        
        return errors
    
    def validate_market_areas(self, market_areas: List[str]) -> List[str]:
        """Validate market areas list."""
        errors = []
        
        if market_areas:
            if len(market_areas) > 50:
                errors.append("Too many market areas (max 50)")
            
            for area in market_areas:
                if len(area) > 100:
                    errors.append(f"Market area '{area}' too long (max 100 characters)")
                
                # Validate format against German market patterns
                valid_format = False
                for pattern in self.GERMAN_MARKET_AREA_PATTERNS:
                    if re.match(pattern, area):
                        valid_format = True
                        break
                
                if not valid_format:
                    errors.append(f"Market area '{area}' has invalid format")
        
        return errors
    
    def validate_outreach_history(self, outreach_history: List[OutreachHistoryEntry]) -> List[str]:
        """Validate outreach history entries."""
        errors = []
        
        if outreach_history:
            if len(outreach_history) > 1000:
                errors.append("Too many outreach history entries (max 1000)")
            
            for i, entry in enumerate(outreach_history):
                # Validate timestamp
                if entry.timestamp > datetime.now():
                    errors.append(f"Outreach entry {i} has future timestamp")
                
                # Validate method
                if not isinstance(entry.method, ContactMethod):
                    errors.append(f"Outreach entry {i} has invalid contact method")
                
                # Validate status
                valid_statuses = ['sent', 'delivered', 'opened', 'responded', 'failed']
                if entry.status not in valid_statuses:
                    errors.append(f"Outreach entry {i} has invalid status")
        
        return errors
    
    def validate_preferred_contact_method(self, method: Optional[ContactMethod]) -> List[str]:
        """Validate preferred contact method."""
        errors = []
        
        if method and not isinstance(method, ContactMethod):
            errors.append("Invalid preferred contact method")
        
        return errors
    
    def validate_confidence_score(self, score: float) -> List[str]:
        """Validate confidence score."""
        errors = []
        
        if score < 0.0 or score > 1.0:
            errors.append("Confidence score must be between 0.0 and 1.0")
        
        return errors
    
    def validate_quality_score(self, score: float) -> List[str]:
        """Validate quality score."""
        errors = []
        
        if score < 0.0 or score > 1.0:
            errors.append("Quality score must be between 0.0 and 1.0")
        
        return errors
    
    def validate_tags(self, tags: List[str]) -> List[str]:
        """Validate tags list."""
        errors = []
        
        if tags:
            if len(tags) > 100:
                errors.append("Too many tags (max 100)")
            
            for tag in tags:
                if len(tag) > 50:
                    errors.append(f"Tag '{tag}' too long (max 50 characters)")
                
                # Validate tag format
                if not re.match(r'^[A-Za-z0-9\-\_\s]+$', tag):
                    errors.append(f"Tag '{tag}' contains invalid characters")
        
        return errors
    
    def validate_notes(self, notes: Optional[str]) -> List[str]:
        """Validate notes field."""
        errors = []
        
        if notes and len(notes) > 1000:
            errors.append("Notes too long (max 1000 characters)")
        
        return errors
    
    def validate_contact(self, contact: MarketIntelligenceContact) -> Dict[str, Any]:
        """
        Comprehensive validation of a market intelligence contact.
        
        Args:
            contact: Market intelligence contact to validate
            
        Returns:
            Dictionary with validation results
        """
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'field_validations': {}
        }
        
        # Validate individual fields
        field_validations = {
            'agency_type': self.validate_agency_type(contact.agency_type),
            'position': self.validate_position(contact.position),
            'company_name': self.validate_company_name(contact.company_name),
            'market_areas': self.validate_market_areas(contact.market_areas),
            'outreach_history': self.validate_outreach_history(contact.outreach_history),
            'preferred_contact_method': self.validate_preferred_contact_method(contact.preferred_contact_method),
            'confidence_score': self.validate_confidence_score(contact.confidence_score),
            'quality_score': self.validate_quality_score(contact.quality_score),
            'tags': self.validate_tags(contact.tags),
            'notes': self.validate_notes(contact.notes),
        }
        
        # Collect errors and warnings
        for field_name, field_errors in field_validations.items():
            validation_results['field_validations'][field_name] = {
                'errors': field_errors,
                'warnings': []  # Could add warnings here in future
            }
            
            if field_errors:
                validation_results['errors'].extend([
                    f"{field_name}: {error}" for error in field_errors
                ])
        
        # Business logic validations
        business_errors = self._validate_business_logic(contact)
        validation_results['errors'].extend(business_errors)
        
        # Determine overall validity
        validation_results['is_valid'] = len(validation_results['errors']) == 0
        
        return validation_results
    
    def _validate_business_logic(self, contact: MarketIntelligenceContact) -> List[str]:
        """Validate business logic rules."""
        errors = []
        
        # Rule: If blacklisted, must have reason
        if contact.is_blacklisted and not contact.blacklist_reason:
            errors.append("Blacklisted contacts must have a blacklist reason")
        
        # Rule: If company name provided, should have position
        if contact.company_name and not contact.position:
            errors.append("Contacts with company name should have position specified")
        
        # Rule: Confidence score should be consistent with base confidence
        if contact.confidence and contact.confidence_score:
            base_confidence_map = {
                'high': 0.8,
                'medium': 0.6,
                'low': 0.4,
                'uncertain': 0.2
            }
            
            expected_min = base_confidence_map.get(contact.confidence.value, 0.0)
            if contact.confidence_score < expected_min:
                errors.append(f"Confidence score {contact.confidence_score} is lower than expected for {contact.confidence.value} confidence level")
        
        # Rule: Quality score should be reasonable given data completeness
        if contact.quality_score > 0.8:
            # High quality contacts should have complete information
            required_fields = ['position', 'company_name', 'agency_type', 'market_areas']
            missing_fields = [field for field in required_fields if not getattr(contact, field)]
            
            if missing_fields:
                errors.append(f"High quality score requires complete information. Missing: {', '.join(missing_fields)}")
        
        return errors
    
    def get_validation_recommendations(self, contact: MarketIntelligenceContact) -> List[str]:
        """Get recommendations for improving contact quality."""
        recommendations = []
        
        # Data completeness recommendations
        if not contact.position:
            recommendations.append("Add position title for better categorization")
        
        if not contact.company_name:
            recommendations.append("Add company name for business context")
        
        if not contact.agency_type:
            recommendations.append("Specify agency type for market analysis")
        
        if not contact.market_areas:
            recommendations.append("Add market areas for geographic targeting")
        
        if not contact.tags:
            recommendations.append("Add tags for better organization and filtering")
        
        # Quality improvement recommendations
        if contact.quality_score < 0.6:
            recommendations.append("Consider adding more detailed information to improve quality score")
        
        if contact.confidence_score < 0.7:
            recommendations.append("Verify contact information to improve confidence score")
        
        # Engagement recommendations
        if not contact.outreach_history:
            recommendations.append("Start outreach to build engagement history")
        elif len(contact.get_recent_outreach(30)) == 0:
            recommendations.append("Consider recent outreach to maintain engagement")
        
        return recommendations


# Convenience function for quick validation
def validate_market_intelligence_contact(contact: MarketIntelligenceContact) -> Dict[str, Any]:
    """Quick function to validate a market intelligence contact."""
    validator = MarketIntelligenceValidator()
    return validator.validate_contact(contact)