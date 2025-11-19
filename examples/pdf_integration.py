#!/usr/bin/env python3
"""
PDF Integration Example for MAFA Contact Discovery.

This example demonstrates how to use the PDF extractor to extract
contact information from PDF documents.
"""

import asyncio
import logging
from pathlib import Path

from mafa.contacts.pdf_extractor import PDFExtractor
from mafa.contacts.integration import ContactDiscoveryIntegration

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def main():
    """Main example function."""
    
    # Load example config for Settings
    import json
    from pathlib import Path
    
    config_path = Path("config.example.json")
    if config_path.exists():
        with open(config_path, 'r') as f:
            config_data = json.load(f)
        config = Settings(**config_data)
    else:
        # Create minimal config
        config = Settings(personal_profile={}, search_criteria={}, notification={})
    
    # Initialize PDF extractor
    pdf_extractor = PDFExtractor(
        config=config,
        max_file_size_mb=10,
        extract_tables=True,
        extract_metadata=True,
        confidence_threshold=0.6,
        ocr_fallback=True
    )
    
    # Example 1: Extract from single PDF
    logger.info("Example 1: Extracting from single PDF")
    
    pdf_path = Path("examples/pdf/simple_contacts.pdf")
    if pdf_path.exists():
        contacts = pdf_extractor.extract_contacts(pdf_path)
        
        logger.info(f"Found {len(contacts)} contacts:")
        for contact in contacts:
            logger.info(f"  - {contact.contact.method}: {contact.contact.value} "
                       f"(confidence: {contact.contact.confidence.name})")
    else:
        logger.warning(f"Test PDF not found: {pdf_path}")
    
    # Example 2: Extract from multiple PDFs
    logger.info("\nExample 2: Extracting from multiple PDFs")
    
    examples_dir = Path("examples/pdf")
    if examples_dir.exists():
        pdf_files = list(examples_dir.glob("*.pdf"))
        
        for pdf_file in pdf_files:
            logger.info(f"Processing {pdf_file.name}...")
            contacts = pdf_extractor.extract_contacts(pdf_file)
            
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
    
    # Add PDF extractor to the integration
    integration.add_extractor(pdf_extractor)
    
    # Simulate processing a listing with PDF attachments
    listing_data = {
        "id": "test_listing_456",
        "url": "https://example.com/listing/456",
        "title": "Test Listing with PDF",
        "pdf_urls": [
            "https://example.com/downloads/brochure.pdf",
            "https://example.com/downloads/application_form.pdf"
        ]
    }
    
    # Process listing with PDF support
    contacts = await integration.process_listing(listing_data)
    
    logger.info(f"Total contacts found: {len(contacts)}")
    for contact in contacts:
        logger.info(f"  - {contact.contact.method}: {contact.contact.value} "
                   f"(source: {contact.source})")


if __name__ == "__main__":
    asyncio.run(main())
