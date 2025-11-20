#!/usr/bin/env python3
"""
Property Management Company Analysis for MWA-MüncheWohnungsAssistent

This script analyzes the database and contact data to identify and extract
property management companies ("Hausverwaltungen") from the MWA database.

Key analysis features:
- Examines database structure and existing data
- Identifies property management patterns in contact information
- Filters business contacts vs individual contacts
- Analyzes German property management company terminology
- Provides confidence scoring for property management identification
- Exports comprehensive results

Author: MWA Core Analysis System
Date: 2025-11-20
"""

import sqlite3
import json
import re
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Set, Tuple
from dataclasses import dataclass
from collections import defaultdict, Counter


@dataclass
class PropertyManagementContact:
    """Represents a potential property management company contact."""
    id: Optional[int]
    listing_id: Optional[int]
    type: str
    value: str
    confidence: float
    source: str
    status: str
    company_name: Optional[str] = None
    business_email: bool = False
    professional_phone: bool = False
    multiple_listings: bool = False
    german_business_terms: bool = False
    verification_count: int = 0
    created_at: Optional[str] = None
    
    def __post_init__(self):
        """Calculate confidence score based on various indicators."""
        score = 0.0
        
        # Base confidence from original confidence score
        if self.confidence:
            score += self.confidence * 0.3
        
        # German business terms in value/name
        german_terms = [
            'hausverwaltung', 'hausverwaltungen', 'immobilienverwaltung', 
            'weg-verwaltung', 'property management', 'verwaltung', 'gmbh',
            'ag', 'kgaa', 'ug', 'limited', 'company', 'unternehmen',
            'immobilien', 'property', 'real estate', 'immobilienmakler'
        ]
        
        value_lower = self.value.lower()
        if any(term in value_lower for term in german_terms):
            score += 0.4
            self.german_business_terms = True
        
        # Business email patterns
        if self.type == 'email':
            business_patterns = [
                r'@.*\.(de|com|org|net|info|business)',
                r'.*\.(de|com|org|net|info|business)',
                r'.*info.*@',
                r'.*office.*@',
                r'.*service.*@',
                r'.*kontakt.*@',
                r'.*admin.*@'
            ]
            
            if any(re.match(pattern, value_lower) for pattern in business_patterns):
                score += 0.3
                self.business_email = True
            elif '@' in self.value and not any(personal in value_lower for personal in ['@web.de', '@gmx.de', '@yahoo', '@hotmail', '@aol']):
                score += 0.2
        
        # Professional phone number patterns
        elif self.type == 'phone':
            # German business phone patterns
            phone_clean = re.sub(r'[^\d+]', '', self.value)
            if len(phone_clean) >= 10 and not phone_clean.startswith('01'):
                score += 0.2
                self.professional_phone = True
        
        # Multiple listings association
        if self.multiple_listings:
            score += 0.3
        
        # Verification count bonus
        if self.verification_count > 1:
            score += 0.1 * min(self.verification_count, 3)
        
        # Cap at 1.0
        self.confidence = min(score, 1.0)


class PropertyManagementAnalyzer:
    """Main analyzer for property management company extraction."""
    
    def __init__(self, db_paths: List[str] = None):
        """Initialize analyzer with database paths."""
        self.db_paths = db_paths or [
            'data/mwa_core.db',
            'data/contacts.db'
        ]
        self.property_management_contacts: List[PropertyManagementContact] = []
        self.analysis_results = {}
        
        # German property management patterns
        self.business_indicators = {
            'german_terms': [
                'hausverwaltung', 'hausverwaltungen', 'immobilienverwaltung',
                'weg-verwaltung', 'verwaltung', 'immobilien', 'property management',
                'gmbh', 'ag', 'kgaa', 'ug', 'limited', 'unternehmen'
            ],
            'business_email_domains': [
                'business', 'company', 'enterprise', 'office', 'service',
                'management', 'immobilien', 'property', 'realestate'
            ],
            'professional_phone_patterns': [
                r'^\+49[\d\s\-\.]+',  # German country code
                r'^0[\d\s\-\.]{8,}',   # German numbers starting with 0
                r'^[\d\s\-\.]{10,}$'   # At least 10 digits
            ]
        }
    
    def analyze_databases(self) -> Dict[str, Any]:
        """Analyze all database files for property management companies."""
        print("🔍 Starting Property Management Company Analysis...")
        print(f"📊 Analyzing databases: {', '.join(self.db_paths)}")
        
        results = {
            'analysis_timestamp': datetime.now().isoformat(),
            'databases_analyzed': len(self.db_paths),
            'total_contacts_found': 0,
            'potential_property_managers': [],
            'business_contact_statistics': {},
            'german_property_management_companies': [],
            'high_confidence_matches': [],
            'confidence_distribution': {},
            'source_analysis': {},
            'recommendations': []
        }
        
        # Analyze each database
        for db_path in self.db_paths:
            if not Path(db_path).exists():
                print(f"⚠️  Database not found: {db_path}")
                continue
            
            print(f"📁 Analyzing database: {db_path}")
            db_results = self._analyze_single_database(db_path)
            results['total_contacts_found'] += db_results['contacts_count']
            results['potential_property_managers'].extend(db_results['property_managers'])
            
            # Merge results
            for key in ['business_contact_statistics', 'source_analysis']:
                if key in db_results:
                    if key not in results:
                        results[key] = {}
                    results[key].update(db_results[key])
        
        # Post-process results
        self._post_process_results(results)
        
        self.analysis_results = results
        return results
    
    def _analyze_single_database(self, db_path: str) -> Dict[str, Any]:
        """Analyze a single database file."""
        results = {
            'database_path': db_path,
            'contacts_count': 0,
            'property_managers': [],
            'business_contact_statistics': {},
            'source_analysis': {},
            'schema_analysis': {}
        }
        
        try:
            with sqlite3.connect(db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get table schema
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                results['schema_analysis']['tables'] = tables
                
                print(f"📋 Found tables: {', '.join(tables)}")
                
                # Analyze contacts table if it exists
                if 'contacts' in tables:
                    results.update(self._analyze_contacts_table(cursor))
                elif 'listings' in tables:
                    results.update(self._analyze_listings_table(cursor))
                
        except sqlite3.Error as e:
            print(f"❌ Database error for {db_path}: {e}")
            results['error'] = str(e)
        
        return results
    
    def _analyze_contacts_table(self, cursor) -> Dict[str, Any]:
        """Analyze the contacts table for property management companies."""
        results = {
            'contacts_count': 0,
            'property_managers': [],
            'business_contact_statistics': {},
            'source_analysis': {}
        }
        
        try:
            # Get all contacts
            cursor.execute("""
                SELECT id, listing_id, type, value, confidence, validated, created_at
                FROM contacts
                ORDER BY confidence DESC
            """)
            
            contacts = cursor.fetchall()
            results['contacts_count'] = len(contacts)
            
            print(f"📧 Found {len(contacts)} contacts")
            
            # Group contacts by value to find duplicates
            contact_groups = defaultdict(list)
            for contact in contacts:
                contact_dict = dict(contact)
                contact_groups[contact_dict['value']].append(contact_dict)
            
            # Analyze each unique contact
            for contact_value, contact_instances in contact_groups.items():
                pm_contact = self._analyze_contact_value(contact_value, contact_instances)
                if pm_contact and pm_contact.confidence >= 0.3:  # Minimum threshold
                    results['property_managers'].append(pm_contact)
            
            # Convert contacts to dictionaries for statistics
            contacts_dict = [dict(contact) for contact in contacts]
            
            # Calculate statistics
            results['business_contact_statistics'] = self._calculate_contact_statistics(contacts_dict)
            results['source_analysis'] = self._analyze_contact_sources(contacts_dict)
            
        except sqlite3.Error as e:
            print(f"❌ Error analyzing contacts table: {e}")
            results['error'] = str(e)
        
        return results
    
    def _analyze_listings_table(self, cursor) -> Dict[str, Any]:
        """Analyze listings table to extract contact information."""
        results = {
            'listings_count': 0,
            'property_managers': [],
            'contacts_from_listings': []
        }
        
        try:
            # Get listings with potential contact info
            cursor.execute("""
                SELECT id, title, description, contacts, provider, url, address
                FROM listings 
                ORDER BY id DESC
            """)
            
            listings = cursor.fetchall()
            results['listings_count'] = len(listings)
            
            print(f"🏠 Found {len(listings)} listings")
            
            # Extract contacts from listing data
            for listing in listings:
                listing_dict = dict(listing)
                contacts = self._extract_contacts_from_listing(listing_dict)
                results['contacts_from_listings'].extend(contacts)
                
                # Analyze for property management patterns
                pm_contacts = self._analyze_listing_for_property_management(listing_dict)
                results['property_managers'].extend(pm_contacts)
            
        except sqlite3.Error as e:
            print(f"❌ Error analyzing listings table: {e}")
            results['error'] = str(e)
        
        return results
    
    def _analyze_contact_value(self, contact_value: str, instances: List[Dict]) -> Optional[PropertyManagementContact]:
        """Analyze a contact value for property management indicators."""
        if not contact_value:
            return None
        
        # Use first instance for basic info
        instance = instances[0]
        
        # Create property management contact
        pm_contact = PropertyManagementContact(
            id=instance.get('id'),
            listing_id=instance.get('listing_id'),
            type=instance.get('type', '').lower(),
            value=contact_value,
            confidence=instance.get('confidence', 0.0),
            source=instance.get('source', ''),
            status=instance.get('status', ''),
            verification_count=len(instances),
            created_at=instance.get('created_at')
        )
        
        # Check if associated with multiple listings
        listing_ids = set(i.get('listing_id') for i in instances if i.get('listing_id'))
        pm_contact.multiple_listings = len(listing_ids) > 1
        
        # Analyze for company name patterns
        pm_contact.company_name = self._extract_company_name(contact_value, pm_contact.type)
        
        return pm_contact if pm_contact.confidence >= 0.2 else None
    
    def _extract_company_name(self, contact_value: str, contact_type: str) -> Optional[str]:
        """Extract potential company name from contact value."""
        if contact_type == 'email':
            # Extract domain as potential company name
            if '@' in contact_value:
                domain = contact_value.split('@')[1].lower()
                if domain.endswith('.de'):
                    company = domain[:-3]
                elif '.' in domain:
                    company = domain.split('.')[0]
                else:
                    company = domain
                
                # Clean up common patterns
                company = re.sub(r'[^a-zA-Zäöüß\s]', '', company)
                return company.title() if company and len(company) > 2 else None
        
        elif contact_type in ['phone', 'form']:
            # For phone numbers, try to find company name in the value
            # This might be in format "CompanyName - Phone" or similar
            if ' - ' in contact_value or ' | ' in contact_value:
                parts = re.split(r' - | \| ', contact_value)
                if len(parts) > 1:
                    potential_name = parts[0].strip()
                    if len(potential_name) > 2 and potential_name.isalpha():
                        return potential_name
        
        return None
    
    def _extract_contacts_from_listing(self, listing: Dict) -> List[Dict]:
        """Extract contact information from listing data."""
        contacts = []
        
        # Check contacts field (JSON)
        if listing.get('contacts'):
            try:
                if isinstance(listing['contacts'], str):
                    contacts_data = json.loads(listing['contacts'])
                else:
                    contacts_data = listing['contacts']
                
                if isinstance(contacts_data, list):
                    for contact in contacts_data:
                        contact['listing_id'] = listing['id']
                        contact['source'] = 'listing_extraction'
                        contacts.append(contact)
            except (json.JSONDecodeError, TypeError):
                pass
        
        # Check description for contact patterns
        description = listing.get('description', '') or ''
        title = listing.get('title', '') or ''
        combined_text = f"{title} {description}"
        
        # Extract email addresses
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', combined_text)
        for email in emails:
            contacts.append({
                'type': 'email',
                'value': email,
                'listing_id': listing['id'],
                'source': 'text_extraction',
                'confidence': 0.6
            })
        
        # Extract phone numbers
        phones = re.findall(r'\+?49[\d\s\-\.]{8,}', combined_text)
        for phone in phones:
            contacts.append({
                'type': 'phone',
                'value': phone,
                'listing_id': listing['id'],
                'source': 'text_extraction',
                'confidence': 0.5
            })
        
        return contacts
    
    def _analyze_listing_for_property_management(self, listing: Dict) -> List[PropertyManagementContact]:
        """Analyze a listing for property management company indicators."""
        pm_contacts = []
        
        # Check for property management indicators in title and description
        title = listing.get('title', '').lower()
        description = listing.get('description', '').lower()
        combined_text = f"{title} {description}"
        
        # Look for German property management terms
        if any(term in combined_text for term in self.business_indicators['german_terms']):
            # Extract contacts from this listing
            contacts = self._extract_contacts_from_listing(listing)
            
            for contact in contacts:
                pm_contact = PropertyManagementContact(
                    id=None,
                    listing_id=listing['id'],
                    type=contact.get('type', ''),
                    value=contact.get('value', ''),
                    confidence=contact.get('confidence', 0.0) + 0.3,  # Bonus for property management context
                    source=contact.get('source', 'listing_analysis'),
                    status='extracted'
                )
                
                if pm_contact.confidence >= 0.4:
                    pm_contacts.append(pm_contact)
        
        return pm_contacts
    
    def _calculate_contact_statistics(self, contacts: List) -> Dict[str, Any]:
        """Calculate contact statistics."""
        if not contacts:
            return {}
        
        stats = {
            'total_contacts': len(contacts),
            'by_type': Counter(c.get('type', 'unknown') for c in contacts),
            'confidence_ranges': {
                'high_0.8_1.0': len([c for c in contacts if c.get('confidence', 0) >= 0.8]),
                'medium_0.5_0.8': len([c for c in contacts if 0.5 <= c.get('confidence', 0) < 0.8]),
                'low_0.0_0.5': len([c for c in contacts if c.get('confidence', 0) < 0.5])
            },
            'unique_values': len(set(c.get('value') for c in contacts)),
            'validation_status': Counter(c.get('validated', False) for c in contacts)
        }
        
        return stats
    
    def _analyze_contact_sources(self, contacts: List) -> Dict[str, Any]:
        """Analyze contact validation status for patterns."""
        validation_analysis = {}
        
        for contact in contacts:
            validation = 'validated' if contact.get('validated', False) else 'unvalidated'
            if validation not in validation_analysis:
                validation_analysis[validation] = {
                    'count': 0,
                    'avg_confidence': 0.0,
                    'types': Counter()
                }
            
            validation_analysis[validation]['count'] += 1
            validation_analysis[validation]['avg_confidence'] += contact.get('confidence', 0)
            validation_analysis[validation]['types'][contact.get('type', 'unknown')] += 1
        
        # Calculate average confidence
        for validation_data in validation_analysis.values():
            if validation_data['count'] > 0:
                validation_data['avg_confidence'] /= validation_data['count']
        
        return validation_analysis
    
    def _post_process_results(self, results: Dict[str, Any]) -> None:
        """Post-process analysis results."""
        property_managers = results['potential_property_managers']
        
        # Sort by confidence
        property_managers.sort(key=lambda x: x.confidence, reverse=True)
        
        # Filter high confidence matches
        results['high_confidence_matches'] = [
            pm for pm in property_managers if pm.confidence >= 0.7
        ]
        
        # Filter German property management companies
        results['german_property_management_companies'] = [
            pm for pm in property_managers if pm.german_business_terms
        ]
        
        # Calculate confidence distribution
        confidence_ranges = {
            'very_high_0.9_1.0': len([pm for pm in property_managers if pm.confidence >= 0.9]),
            'high_0.7_0.9': len([pm for pm in property_managers if 0.7 <= pm.confidence < 0.9]),
            'medium_0.5_0.7': len([pm for pm in property_managers if 0.5 <= pm.confidence < 0.7]),
            'low_0.3_0.5': len([pm for pm in property_managers if 0.3 <= pm.confidence < 0.5])
        }
        results['confidence_distribution'] = confidence_ranges
        
        # Generate recommendations
        results['recommendations'] = self._generate_recommendations(results)
    
    def _generate_recommendations(self, results: Dict[str, Any]) -> List[str]:
        """Generate analysis recommendations."""
        recommendations = []
        
        if len(results['high_confidence_matches']) > 0:
            recommendations.append(
                f"Found {len(results['high_confidence_matches'])} high-confidence property management contacts"
            )
        
        if len(results['german_property_management_companies']) > 0:
            recommendations.append(
                f"Identified {len(results['german_property_management_companies'])} German property management companies"
            )
        
        if results['total_contacts_found'] > 1000:
            recommendations.append(
                "Large dataset detected - consider implementing batch processing for efficiency"
            )
        
        avg_confidence = sum(pm.confidence for pm in results['potential_property_managers']) / max(len(results['potential_property_managers']), 1)
        if avg_confidence < 0.5:
            recommendations.append(
                "Low average confidence scores - consider refining property management detection patterns"
            )
        
        return recommendations
    
    def export_results(self, output_file: str = None) -> str:
        """Export analysis results to JSON file."""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"property_management_analysis_{timestamp}.json"
        
        # Convert PropertyManagementContact objects to dictionaries
        export_data = {
            'analysis_summary': {
                'total_contacts_analyzed': self.analysis_results.get('total_contacts_found', 0),
                'potential_property_managers_found': len(self.analysis_results.get('potential_property_managers', [])),
                'high_confidence_matches': len(self.analysis_results.get('high_confidence_matches', [])),
                'german_property_management_companies': len(self.analysis_results.get('german_property_management_companies', [])),
                'analysis_timestamp': self.analysis_results.get('analysis_timestamp'),
                'confidence_distribution': self.analysis_results.get('confidence_distribution', {})
            },
            'high_confidence_property_managers': [
                {
                    'id': pm.id,
                    'type': pm.type,
                    'value': pm.value,
                    'confidence': pm.confidence,
                    'source': pm.source,
                    'company_name': pm.company_name,
                    'business_email': pm.business_email,
                    'professional_phone': pm.professional_phone,
                    'multiple_listings': pm.multiple_listings,
                    'german_business_terms': pm.german_business_terms,
                    'verification_count': pm.verification_count
                }
                for pm in self.analysis_results.get('high_confidence_matches', [])
            ],
            'german_property_management_companies': [
                {
                    'id': pm.id,
                    'type': pm.type,
                    'value': pm.value,
                    'confidence': pm.confidence,
                    'company_name': pm.company_name,
                    'business_email': pm.business_email,
                    'professional_phone': pm.professional_phone
                }
                for pm in self.analysis_results.get('german_property_management_companies', [])
            ],
            'detailed_analysis': {
                'business_contact_statistics': self.analysis_results.get('business_contact_statistics', {}),
                'source_analysis': self.analysis_results.get('source_analysis', {}),
                'recommendations': self.analysis_results.get('recommendations', [])
            },
            'methodology': {
                'confidence_scoring': "Multi-factor scoring based on business indicators",
                'german_terms_matched': self.business_indicators['german_terms'],
                'business_email_patterns': self.business_indicators['business_email_domains'],
                'minimum_confidence_threshold': 0.3,
                'high_confidence_threshold': 0.7
            }
        }
        
        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return output_file
    
    def print_summary(self) -> None:
        """Print analysis summary to console."""
        if not self.analysis_results:
            print("❌ No analysis results available")
            return
        
        results = self.analysis_results
        
        print("\n" + "="*60)
        print("🏢 PROPERTY MANAGEMENT COMPANY ANALYSIS SUMMARY")
        print("="*60)
        
        print(f"📊 Total Contacts Analyzed: {results.get('total_contacts_found', 0)}")
        print(f"🏢 Potential Property Managers: {len(results.get('potential_property_managers', []))}")
        print(f"⭐ High Confidence Matches: {len(results.get('high_confidence_matches', []))}")
        print(f"🇩🇪 German Property Management Companies: {len(results.get('german_property_management_companies', []))}")
        
        # Confidence distribution
        conf_dist = results.get('confidence_distribution', {})
        if conf_dist:
            print("\n📈 Confidence Score Distribution:")
            for range_name, count in conf_dist.items():
                print(f"   {range_name}: {count}")
        
        # Top sources
        validation_analysis = results.get('source_analysis', {})
        if validation_analysis:
            print("\n📡 Contact Validation Analysis:")
            for validation, data in sorted(validation_analysis.items(), key=lambda x: x[1]['count'], reverse=True)[:5]:
                print(f"   {validation}: {data['count']} contacts (avg confidence: {data['avg_confidence']:.2f})")
        
        # Recommendations
        recommendations = results.get('recommendations', [])
        if recommendations:
            print("\n💡 Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. {rec}")
        
        print("\n" + "="*60)


def main():
    """Main analysis function."""
    print("🚀 Starting MWA Property Management Company Analysis")
    print("=" * 60)
    
    # Initialize analyzer
    analyzer = PropertyManagementAnalyzer()
    
    # Run analysis
    try:
        results = analyzer.analyze_databases()
        
        # Print summary
        analyzer.print_summary()
        
        # Export results
        output_file = analyzer.export_results()
        print(f"\n💾 Results exported to: {output_file}")
        
        print("\n✅ Analysis completed successfully!")
        
    except Exception as e:
        print(f"❌ Analysis failed: {e}")
        raise


if __name__ == "__main__":
    main()