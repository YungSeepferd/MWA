#!/usr/bin/env python3
"""
OCR Integration Example for MAFA Contact Discovery.

This example demonstrates how to use the OCR extractor to extract
contact information from images.
"""

import asyncio
import logging
from pathlib import Path

from mafa.contacts.ocr_extractor import OCRExtractor
from mafa.contacts.integration import ContactDiscoveryIntegration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Main example function."""
    
    # Load example config for Settings
    import json
    config_path = Path("config.example.json")
    if config_path.exists():
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        config = Settings(**config_data)
    else:
        # Create minimal config
        config = Settings(personal_profile={}, search_criteria={}, notification={})
    
    # Initialize OCR extractor
    ocr_extractor = OCRExtractor(
        config=config,
        languages=['deu', 'eng'],
        confidence_threshold=0.6,
        preprocess=True,
        enhance_contrast=True,
        denoise=True
    )
    
    # Example 1: Extract from single image
    logger.info("Example 1: Extracting from single image")
    
    image_path = Path("examples/ocr/business_card.png")
    if image_path.exists():
        contacts = ocr_extractor.extract_contacts(image_path)
        
        logger.info(f"Found {len(contacts)} contacts:")
        for contact in contacts:
            logger.info(f"  - {contact.contact.method}: {contact.contact.value} "
                       f"(confidence: {contact.contact.confidence.name})")
    else:
        logger.warning(f"Test image not found: {image_path}")
    
    # Example 2: Extract from multiple images
    logger.info("\nExample 2: Extracting from multiple images")
    
    examples_dir = Path("examples/ocr")
    if examples_dir.exists():
        image_files = list(examples_dir.glob("*.png"))
        
        for image_file in image_files:
            logger.info(f"Processing {image_file.name}...")
            contacts = ocr_extractor.extract_contacts(image_file)
            
            if contacts:
                logger.info(f"  Found {len(contacts)} contacts")
                for contact in contacts:
                    logger.info(f"    - {contact.contact.method}: {contact.contact.value}")
            else:
                logger.info("  No contacts found")
    
    # Example 3: Integration with contact discovery
    logger.info("\nExample 3: Integration with contact discovery")
    
    # Initialize contact discovery integration
    integration = ContactDiscoveryIntegration()
    
    # Add OCR extractor to the integration
    integration.add_extractor(ocr_extractor)
    
    # Simulate processing a listing with image URLs
    listing_data = {
        "id": "test_listing_123",
        "url": "https://example.com/listing/123",
        "title": "Test Listing",
        "image_urls": [
            "https://example.com/images/contact_card.png",
            "https://example.com/images/business_info.png"
        ]
    }
    
    # Process listing with OCR support
    contacts = await integration.process_listing(listing_data)
    
    logger.info(f"Total contacts found: {len(contacts)}")
    for contact in contacts:
        logger.info(f"  - {contact.contact.method}: {contact.contact.value} "
                   f"(source: {contact.source})")


if __name__ == "__main__":
    asyncio.run(main())
