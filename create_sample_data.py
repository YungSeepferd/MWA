#!/usr/bin/env python3
"""
Create sample data for MWA Property Management Analysis

This script creates realistic sample data including property management companies
to demonstrate the property management analysis capabilities.
"""

import sqlite3
import json
from datetime import datetime, timedelta
from pathlib import Path


def create_sample_listings_and_contacts():
    """Create sample listings and contacts with property management companies."""
    
    # Sample property management companies and their contacts
    property_managers = [
        {
            'company_name': 'Münchner Hausverwaltung Schmidt GmbH',
            'email': 'info@schmidt-hausverwaltung.de',
            'phone': '+49 89 12345678',
            'website': 'www.schmidt-hausverwaltung.de',
            'listings': 3
        },
        {
            'company_name': 'Immobilienverwaltung Bayern AG',
            'email': 'kontakt@immobilienverwaltung-bayern.de',
            'phone': '+49 89 98765432',
            'website': 'www.immobilienverwaltung-bayern.de',
            'listings': 2
        },
        {
            'company_name': 'WEG-Verwaltung München',
            'email': 'service@weg-verwaltung-muenchen.de',
            'phone': '+49 89 55566677',
            'website': 'www.weg-verwaltung-muenchen.de',
            'listings': 1
        },
        {
            'company_name': 'Property Management Munich Ltd.',
            'email': 'office@property-management-munich.com',
            'phone': '+49 89 11122233',
            'website': 'www.property-management-munich.com',
            'listings': 2
        },
        {
            'company_name': 'Alpen Immobilien Verwaltung',
            'email': 'verwaltung@alpen-immobilien.de',
            'phone': '+49 89 44455566',
            'website': 'www.alpen-immobilien.de',
            'listings': 1
        }
    ]
    
    # Sample individual landlords (for comparison)
    individual_landlords = [
        {
            'name': 'Max Mustermann',
            'email': 'max.mustermann@gmail.com',
            'phone': '+49 172 1234567',
            'listings': 1
        },
        {
            'name': 'Erika Musterfrau',
            'email': 'erika.musterfrau@web.de',
            'phone': '+49 176 9876543',
            'listings': 1
        }
    ]
    
    # Create sample listings
    listings = []
    contact_id = 1
    
    # Property management company listings
    for pm in property_managers:
        for i in range(pm['listings']):
            listing_id = len(listings) + 1
            
            listing = {
                'id': listing_id,
                'title': f'Schöne 3-Zimmer-Wohnung in München - {pm["company_name"]}',
                'url': f'https://www.immoscout.de/expose/{listing_id}',
                'price': f'{1200 + i * 100}€',
                'size': f'{70 + i * 10}m²',
                'rooms': '3',
                'address': f'Musterstraße {10 + i}, 80331 München',
                'description': f'Helle und moderne Wohnung im Herzen von München. '
                             f'Verwaltet durch {pm["company_name"]}. '
                             f'Kontakt: {pm["email"]} oder {pm["phone"]}. '
                             f'Besuchen Sie uns unter {pm["website"]}.',
                'provider': 'immoscout',
                'status': 'active',
                'scraped_at': datetime.now().isoformat(),
                'created_at': datetime.now().isoformat()
            }
            listings.append(listing)
    
    # Individual landlord listings
    for landlord in individual_landlords:
        listing_id = len(listings) + 1
        
        listing = {
            'id': listing_id,
            'title': f'Gemütliche 2-Zimmer-Wohnung - Privat',
            'url': f'https://www.immoscout.de/expose/{listing_id}',
            'price': '950€',
            'size': '60m²',
            'rooms': '2',
            'address': f'Beispielstraße {5}, 80333 München',
            'description': f'Nette Wohnung direkt vermietet durch {landlord["name"]}. '
                         f'Kontakt: {landlord["email"]} oder {landlord["phone"]}.',
            'provider': 'immoscout',
            'status': 'active',
            'scraped_at': datetime.now().isoformat(),
            'created_at': datetime.now().isoformat()
        }
        listings.append(listing)
    
    # Create contacts
    contacts = []
    
    # Property management company contacts
    for pm in property_managers:
        for i in range(pm['listings']):
            listing_id = i + 1  # Corresponding listing ID
            
            # Email contact
            contacts.append({
                'id': contact_id,
                'listing_id': listing_id,
                'type': 'email',
                'value': pm['email'],
                'confidence': 0.95,
                'validated': True,
                'created_at': datetime.now().isoformat()
            })
            contact_id += 1
            
            # Phone contact
            contacts.append({
                'id': contact_id,
                'listing_id': listing_id,
                'type': 'phone',
                'value': pm['phone'],
                'confidence': 0.90,
                'validated': True,
                'created_at': datetime.now().isoformat()
            })
            contact_id += 1
    
    # Individual landlord contacts
    for i, landlord in enumerate(individual_landlords):
        listing_id = len(property_managers) + i + 1
        
        # Email contact
        contacts.append({
            'id': contact_id,
            'listing_id': listing_id,
            'type': 'email',
            'value': landlord['email'],
            'confidence': 0.85,
            'source': 'listing_extraction',
            'validated': True,
            'created_at': datetime.now().isoformat()
        })
        contact_id += 1
        
        # Phone contact
        contacts.append({
            'id': contact_id,
            'listing_id': listing_id,
            'type': 'phone',
            'value': landlord['phone'],
            'confidence': 0.80,
            'source': 'listing_extraction',
            'validated': True,
            'created_at': datetime.now().isoformat()
        })
        contact_id += 1
    
    return listings, contacts


def insert_sample_data():
    """Insert sample data into the database."""
    
    db_path = 'data/mwa_core.db'
    
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        return False
    
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            
            # Insert sample listings
            listings, contacts = create_sample_listings_and_contacts()
            
            print(f"📝 Inserting {len(listings)} sample listings...")
            for listing in listings:
                cursor.execute("""
                    INSERT INTO listings (title, url, price, size, rooms, address,
                                      description, provider, status, scraped_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    listing['title'], listing['url'], listing['price'], listing['size'],
                    listing['rooms'], listing['address'], listing['description'],
                    listing['provider'], listing['status'], listing['scraped_at']
                ))
            
            # Get the listing IDs that were inserted
            cursor.execute("SELECT id FROM listings ORDER BY id DESC LIMIT ?", (len(listings),))
            inserted_listing_ids = [row[0] for row in cursor.fetchall()]
            
            print(f"📧 Inserting {len(contacts)} sample contacts...")
            for i, contact in enumerate(contacts):
                # Map the listing_id to the actual inserted ID
                actual_listing_id = inserted_listing_ids[contact['listing_id'] - 1]
                
                cursor.execute("""
                    INSERT INTO contacts (listing_id, type, value, confidence, validated, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    actual_listing_id, contact['type'], contact['value'],
                    contact['confidence'], contact['validated'], contact['created_at']
                ))
            
            conn.commit()
            print(f"✅ Successfully inserted {len(listings)} listings and {len(contacts)} contacts")
            return True
            
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}")
        return False


def main():
    """Main function to create sample data."""
    print("🚀 Creating Sample Data for Property Management Analysis")
    print("=" * 60)
    
    success = insert_sample_data()
    
    if success:
        print("\n✅ Sample data created successfully!")
        print("📊 You can now run the property management analysis:")
        print("   python property_management_analysis.py")
    else:
        print("\n❌ Failed to create sample data")


if __name__ == "__main__":
    main()