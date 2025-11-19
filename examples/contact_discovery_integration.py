#!/usr/bin/env python3
"""
Example script demonstrating contact discovery integration with MAFA scraping.

This script shows how to integrate the new contact discovery features
with the existing scraping workflow for production deployment.
"""

import asyncio
import sys
from pathlib import Path
from typing import List, Dict

# Add the project root to Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mafa.config.settings import Settings
from mafa.contacts import ContactDiscoveryIntegration
from mafa.monitoring import get_health_checker
from mafa.db.manager import ListingRepository
from loguru import logger


async def main():
    """Main function demonstrating contact discovery integration."""
    
    logger.info("Starting MAFA Contact Discovery Integration Example")
    
    # Load configuration
    try:
        config = Settings.load()
        logger.info(f"Configuration loaded for user: {config.personal_profile.my_full_name}")
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        return
    
    # Check system health
    health_checker = get_health_checker()
    health_status = health_checker.get_health_status()
    
    logger.info(f"System health: {health_status.status}")
    if health_status.issues:
        logger.warning(f"Health issues: {health_status.issues}")
    if health_status.warnings:
        logger.warning(f"Health warnings: {health_status.warnings}")
    
    # Initialize contact discovery integration
    contact_integration = ContactDiscoveryIntegration(config)
    
    # Example: Process a single listing
    example_listing = {
        "title": "Schöne 2-Zimmer Wohnung in München",
        "price": "1200 €",
        "url": "https://example-immobilien.de/angebot/12345",
        "source": "Example Immobilien",
        "description": "Schöne Wohnung mit Balkon. Kontakt: info@example-immobilien.de oder Tel: 089 12345678",
        "timestamp": "2024-11-18T10:00:00"
    }
    
    logger.info("Processing example listing for contact discovery...")
    
    try:
        contacts, forms = await contact_integration.process_listing(example_listing, listing_id=1)
        
        logger.success(f"Contact discovery completed!")
        logger.info(f"Found {len(contacts)} contacts:")
        for contact in contacts:
            logger.info(f"  - {contact.method.value}: {contact.value} (confidence: {contact.confidence.value})")
        
        logger.info(f"Found {len(forms)} contact forms:")
        for form in forms:
            logger.info(f"  - Form at {form.action_url} (method: {form.method})")
        
    except Exception as e:
        logger.error(f"Contact discovery failed: {e}")
    
    # Get contact discovery statistics
    stats = contact_integration.get_contact_stats()
    if stats:
        logger.info("Contact Discovery Statistics:")
        logger.info(f"  Total contacts: {stats.get('total_contacts', 0)}")
        logger.info(f"  Contacts by method: {stats.get('contacts_by_method', {})}")
        logger.info(f"  Recent contacts (7 days): {stats.get('recent_contacts_7_days', 0)}")
        logger.info(f"  Extraction success rate: {stats.get('extraction_success_rate', 0):.1%}")
    
    # Demonstrate batch processing
    example_listings = [
        {
            "title": "Wohnung 1",
            "price": "1000 €",
            "url": "https://example1.de/angebot/1",
            "source": "Example1"
        },
        {
            "title": "Wohnung 2", 
            "price": "1500 €",
            "url": "https://example2.de/angebot/2",
            "source": "Example2"
        }
    ]
    
    logger.info("Processing batch of listings...")
    batch_results = await contact_integration.process_listings_batch(example_listings)
    logger.info(f"Batch processing results: {batch_results}")
    
    # Demonstrate health monitoring
    logger.info("Checking contact discovery health...")
    contact_health = health_checker.check_contact_discovery_health()
    logger.info(f"Contact discovery health: {contact_health[0]} - {contact_health[1]}")
    
    logger.success("Contact discovery integration example completed!")


if __name__ == "__main__":
    # Configure logging
    logger.add(
        "contact_discovery_example.log",
        rotation="10 MB",
        retention="10 days",
        level="INFO"
    )
    
    # Run the example
    asyncio.run(main())