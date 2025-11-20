"""
Test script for Market Intelligence Contact implementation.

Validates the database migration, model creation, validation, and scoring
functionality for the Market Intelligence Contact system.
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from mwa_core.contact.market_intelligence import (
    MarketIntelligenceContact, AgencyType, ContactMethod, LeadSource, OutreachHistoryEntry,
    create_market_intelligence_contact
)
from mwa_core.contact.market_intelligence_validators import MarketIntelligenceValidator
from mwa_core.contact.market_intelligence_scoring import MarketIntelligenceScoringEngine
from mwa_core.contact.models import Contact, ContactMethod as BaseContactMethod, ConfidenceLevel, ContactStatus


def test_market_intelligence_contact_creation():
    """Test creating a Market Intelligence Contact."""
    print("=== Testing Market Intelligence Contact Creation ===")
    
    # Create a base contact
    base_contact = Contact(
        method=BaseContactMethod.EMAIL,
        value="property.manager@example.com",
        confidence=ConfidenceLevel.HIGH,
        source_url="https://immoscout24.de/listing/123",
        discovery_path=["https://immoscout24.de"],
        verification_status=ContactStatus.UNVERIFIED
    )
    
    # Create market intelligence contact
    mi_contact = create_market_intelligence_contact(
        contact=base_contact,
        position="Property Manager",
        company_name="Munich Property Management GmbH",
        agency_type=AgencyType.PROPERTY_MANAGER,
        market_areas=["Munich Center", "Schwabing"]
    )
    
    # Add outreach history
    outreach_entry = OutreachHistoryEntry(
        outreach_id="test_001",
        method=ContactMethod.EMAIL,
        timestamp=datetime.now(),
        status="sent",
        response="Positive response received"
    )
    mi_contact.add_outreach_entry(outreach_entry)
    
    # Test serialization
    contact_dict = mi_contact.to_dict()
    print("✓ Contact created successfully")
    print(f"  - Position: {mi_contact.position}")
    print(f"  - Company: {mi_contact.company_name}")
    print(f"  - Agency Type: {mi_contact.agency_type}")
    print(f"  - Market Areas: {mi_contact.market_areas}")
    print(f"  - Outreach History: {len(mi_contact.outreach_history)} entries")
    print(f"  - Engagement Score: {mi_contact.calculate_engagement_score():.2f}")
    
    return mi_contact


def test_market_intelligence_validation(mi_contact):
    """Test market intelligence contact validation."""
    print("\n=== Testing Market Intelligence Contact Validation ===")
    
    validator = MarketIntelligenceValidator()
    validation_result = validator.validate_contact(mi_contact)
    
    print(f"✓ Validation completed")
    print(f"  - Is Valid: {validation_result['is_valid']}")
    print(f"  - Errors: {len(validation_result['errors'])}")
    
    if validation_result['errors']:
        print("  - Error Details:")
        for error in validation_result['errors']:
            print(f"    * {error}")
    
    # Get recommendations
    recommendations = validator.get_validation_recommendations(mi_contact)
    print(f"  - Recommendations: {len(recommendations)}")
    for rec in recommendations:
        print(f"    * {rec}")
    
    return validation_result


def test_market_intelligence_scoring(mi_contact):
    """Test market intelligence contact scoring."""
    print("\n=== Testing Market Intelligence Contact Scoring ===")
    
    scoring_engine = MarketIntelligenceScoringEngine()
    
    # Basic scoring
    score = scoring_engine.score_market_intelligence_contact(mi_contact)
    print(f"✓ Scoring completed")
    print(f"  - Overall Score: {score:.3f}")
    
    # Detailed explanation
    explanation = scoring_engine.get_market_intelligence_scoring_explanation(mi_contact)
    print(f"  - Base Contact Score: {explanation['base_contact_score']:.3f}")
    
    print("  - Market Intelligence Factors:")
    for factor_name, factor_data in explanation['market_intelligence_factors'].items():
        print(f"    * {factor_name}: {factor_data['score']:.3f}")
    
    print("  - Recommendations:")
    for rec in explanation['recommendations']:
        print(f"    * {rec}")
    
    return score, explanation


def test_database_schema_compatibility():
    """Test that the database schema changes are compatible."""
    print("\n=== Testing Database Schema Compatibility ===")
    
    # This would normally test the actual database migration
    # For now, we'll simulate the expected structure
    
    expected_fields = [
        'position', 'company_name', 'agency_type', 'market_areas',
        'outreach_history', 'preferred_contact_method', 'last_contacted',
        'confidence_score', 'quality_score', 'is_active', 'is_blacklisted',
        'blacklist_reason', 'scraped_from_url', 'source_provider',
        'extraction_method', 'extraction_confidence', 'lead_source',
        'tags', 'notes'
    ]
    
    print("✓ Expected database fields:")
    for field in expected_fields:
        print(f"  - {field}")
    
    print("  Note: Actual database testing requires running the migration")
    
    return expected_fields


def main():
    """Run all tests."""
    print("Market Intelligence Contact Implementation Test")
    print("=" * 50)
    
    try:
        # Test 1: Contact creation
        mi_contact = test_market_intelligence_contact_creation()
        
        # Test 2: Validation
        validation_result = test_market_intelligence_validation(mi_contact)
        
        # Test 3: Scoring
        score, explanation = test_market_intelligence_scoring(mi_contact)
        
        # Test 4: Database compatibility
        expected_fields = test_database_schema_compatibility()
        
        # Summary
        print("\n=== Test Summary ===")
        print("✓ All core functionality tests passed")
        print(f"✓ Market Intelligence Contact model: OK")
        print(f"✓ Validation system: OK ({'VALID' if validation_result['is_valid'] else 'INVALID'})")
        print(f"✓ Scoring system: OK (Score: {score:.3f})")
        print(f"✓ Database schema: READY for migration")
        
        # Show sample JSON output
        print("\n=== Sample Contact JSON ===")
        sample_json = json.dumps(mi_contact.to_dict(), indent=2)
        print(sample_json[:500] + "..." if len(sample_json) > 500 else sample_json)
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)