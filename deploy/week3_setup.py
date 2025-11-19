#!/usr/bin/env python3
"""
Week 3 Production Deployment Setup for MAFA PDF Support.

This script sets up PDF parsing support for extracting contact information from PDF documents.
"""

import sys
import subprocess
import logging
from pathlib import Path
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mafa.config.settings import Settings
from mafa.contacts.pdf_extractor import PDFExtractor


def install_pdf_dependencies():
    """Install required Python packages for PDF processing."""
    logger.info("Installing Python dependencies for PDF processing...")
    
    dependencies = [
        'PyMuPDF',
        'pdfplumber',
        'pillow'  # For image extraction from PDFs
    ]
    
    try:
        for dependency in dependencies:
            logger.info(f"Installing {dependency}...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', dependency], 
                         check=True, capture_output=True)
        
        logger.info("PDF dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        return False


def test_pdf_extraction():
    """Test PDF extraction with a sample document."""
    logger.info("Testing PDF extraction...")
    
    try:
        # Create a simple test PDF
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import inch
        
        # Create test PDF
        test_pdf_path = Path("test_contacts.pdf")
        c = canvas.Canvas(str(test_pdf_path), pagesize=letter)
        page_width, page_height = letter
        
        # Add title
        c.setFont("Helvetica-Bold", 16)
        c.drawString(1 * inch, page_height - 1 * inch, "Contact Information")
        
        # Add contact details
        c.setFont("Helvetica", 12)
        c.drawString(1 * inch, page_height - 1.5 * inch, "Email: info@muenchen-wohnungen.de")
        c.drawString(1 * inch, page_height - 1.8 * inch, "Phone: +49 89 12345678")
        c.drawString(1 * inch, page_height - 2.1 * inch, "Website: https://muenchen-wohnungen.de/contact")
        
        # Add a table
        c.setFont("Helvetica-Bold", 12)
        c.drawString(1 * inch, page_height - 2.8 * inch, "Contact Details:")
        
        c.setFont("Helvetica", 10)
        c.drawString(1 * inch, page_height - 3.2 * inch, "Method")
        c.drawString(3 * inch, page_height - 3.2 * inch, "Value")
        c.drawString(5 * inch, page_height - 3.2 * inch, "Notes")
        
        # Draw table lines
        c.line(1 * inch, page_height - 3.3 * inch, 6.5 * inch, page_height - 3.3 * inch)
        c.line(1 * inch, page_height - 3.6 * inch, 6.5 * inch, page_height - 3.6 * inch)
        
        # Add table data
        c.drawString(1 * inch, page_height - 3.5 * inch, "Email")
        c.drawString(3 * inch, page_height - 3.5 * inch, "bewerbung@wohnung.de")
        c.drawString(5 * inch, page_height - 3.5 * inch, "Applications")
        
        # Add metadata
        c.setTitle("Contact Information")
        c.setAuthor("MAFA Test")
        c.setSubject("Contact details for apartment listings")
        
        c.save()
        
        # Load example config for Settings
        config_path = Path("config.example.json")
        if config_path.exists():
            import json
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            config = Settings(**config_data)
        else:
            # Create minimal config
            config = Settings(personal_profile={}, search_criteria={}, notification={})
        
        # Test PDF extraction
        extractor = PDFExtractor(
            config=config,
            max_file_size_mb=10,
            extract_tables=True,
            extract_metadata=True,
            confidence_threshold=0.6
        )
        
        contacts = extractor.extract_contacts(test_pdf_path)
        
        # Clean up
        test_pdf_path.unlink()
        
        if contacts:
            logger.info(f"PDF test successful! Found {len(contacts)} contacts:")
            for contact in contacts:
                logger.info(f"  - {contact.contact.method}: {contact.contact.value} "
                          f"(confidence: {contact.contact.confidence.name})")
            return True
        else:
            logger.warning("PDF test completed but no contacts found")
            return True
            
    except Exception as e:
        logger.error(f"PDF test failed: {e}")
        return False


def create_pdf_test_examples():
    """Create example PDFs for testing PDF extraction."""
    logger.info("Creating PDF test examples...")
    
    try:
        from reportlab.lib.pagesizes import letter, A4
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import inch
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
        from reportlab.lib import colors
        
        examples_dir = Path("examples/pdf")
        examples_dir.mkdir(parents=True, exist_ok=True)
        
        # Example 1: Simple contact PDF
        pdf1_path = examples_dir / "simple_contacts.pdf"
        c1 = canvas.Canvas(str(pdf1_path), pagesize=letter)
        width, height = letter
        
        c1.setFont("Helvetica-Bold", 16)
        c1.drawString(1 * inch, height - 1 * inch, "Kontaktinformationen")
        
        c1.setFont("Helvetica", 12)
        c1.drawString(1 * inch, height - 1.5 * inch, "Für Anfragen:")
        c1.drawString(1 * inch, height - 1.8 * inch, "E-Mail: info@wohnen-in-muenchen.de")
        c1.drawString(1 * inch, height - 2.1 * inch, "Telefon: 089 / 12 34 56 78")
        c1.drawString(1 * inch, height - 2.4 * inch, "Fax: 089 / 12 34 56 79")
        
        c1.save()
        
        # Example 2: PDF with table
        pdf2_path = examples_dir / "table_contacts.pdf"
        doc2 = SimpleDocTemplate(str(pdf2_path), pagesize=letter)
        story2 = []
        
        styles = getSampleStyleSheet()
        
        # Title
        title = Paragraph("Kontaktdaten", styles['Title'])
        story2.append(title)
        story2.append(Spacer(1, 12))
        
        # Table data
        data = [
            ['Kontaktart', 'Wert', 'Bemerkung'],
            ['E-Mail', 'bewerbung@wohnung-muenchen.de', 'Bewerbungen'],
            ['Telefon', '+49 89 87654321', 'Mo-Fr 9-17 Uhr'],
            ['Website', 'https://wohnung-muenchen.de/kontakt', 'Kontaktformular'],
            ['E-Mail (Vertretung)', 'vertretung@wohnung-muenchen.de', 'Notfälle']
        ]
        
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story2.append(table)
        doc2.build(story2)
        
        # Example 3: PDF with metadata
        pdf3_path = examples_dir / "metadata_contacts.pdf"
        c3 = canvas.Canvas(str(pdf3_path), pagesize=A4)
        
        # Set metadata
        c3.setTitle("Wohnungsangebot mit Kontakt")
        c3.setAuthor("München Immobilien GmbH")
        c3.setSubject("Kontaktinformationen für Wohnungsanfragen")
        c3.setCreator("MAFA Contact Discovery System")
        
        # Add content
        c3.setFont("Helvetica-Bold", 14)
        c3.drawString(50, 750, "Schöne 3-Zimmer-Wohnung in München")
        
        c3.setFont("Helvetica", 11)
        c3.drawString(50, 700, "Kontakt für Besichtigungen:")
        c3.drawString(50, 680, "Herr Müller - müller@immobilien-muenchen.de")
        c3.drawString(50, 660, "Tel: 089-12345678 (Zentrale)")
        c3.drawString(50, 640, "Mobil: 0176-12345678")
        
        c3.save()
        
        logger.info(f"Created {len(list(examples_dir.glob('*.pdf')))} PDF test examples in {examples_dir}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create PDF examples: {e}")
        return False


def create_pdf_integration_example():
    """Create example script for PDF integration."""
    logger.info("Creating PDF integration example...")
    
    example_content = '''#!/usr/bin/env python3
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
    logger.info("\\nExample 2: Extracting from multiple PDFs")
    
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
    logger.info("\\nExample 3: Integration with contact discovery")
    
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
'''
    
    try:
        example_path = Path("examples/pdf_integration.py")
        example_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(example_path, 'w') as f:
            f.write(example_content)
        
        # Make executable
        example_path.chmod(0o755)
        
        logger.info(f"Created PDF integration example: {example_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create PDF integration example: {e}")
        return False


def update_configuration():
    """Update configuration with PDF settings."""
    logger.info("Updating configuration with PDF settings...")
    
    try:
        config_path = Path("config.json")
        
        if not config_path.exists():
            logger.error("config.json not found!")
            return False
        
        # Load current config
        import json
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Add PDF section
        config['pdf'] = {
            "enabled": True,
            "max_file_size_mb": 10,
            "extract_tables": True,
            "extract_metadata": True,
            "confidence_threshold": 0.7,
            "ocr_fallback": True,
            "supported_formats": ["pdf"]
        }
        
        # Save updated config
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info("Configuration updated with PDF settings")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update configuration: {e}")
        return False


def main():
    """Main deployment setup function."""
    logger.info("Starting Week 3 PDF Setup")
    logger.info("=" * 60)
    
    success_count = 0
    total_steps = 5
    
    # Step 1: Install PDF dependencies
    if install_pdf_dependencies():
        success_count += 1
        logger.info("✅ PDF dependencies installed")
    else:
        logger.error("❌ PDF dependencies installation failed")
    
    # Step 2: Test PDF extraction
    if test_pdf_extraction():
        success_count += 1
        logger.info("✅ PDF extraction test completed")
    else:
        logger.error("❌ PDF extraction test failed")
    
    # Step 3: Create test examples
    if create_pdf_test_examples():
        success_count += 1
        logger.info("✅ PDF test examples created")
    else:
        logger.error("❌ PDF test examples creation failed")
    
    # Step 4: Create integration example
    if create_pdf_integration_example():
        success_count += 1
        logger.info("✅ PDF integration example created")
    else:
        logger.error("❌ PDF integration example creation failed")
    
    # Step 5: Update configuration
    if update_configuration():
        success_count += 1
        logger.info("✅ Configuration updated")
    else:
        logger.error("❌ Configuration update failed")
    
    # Summary
    logger.info("=" * 60)
    logger.info("PDF SETUP SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Completed: {success_count}/{total_steps} steps")
    
    if success_count == total_steps:
        logger.info("🎉 Week 3 PDF setup completed successfully!")
        logger.info("Next steps:")
        logger.info("1. Test PDF functionality with: python examples/pdf_integration.py")
        logger.info("2. Add PDF support to your contact discovery workflow")
        logger.info("3. Monitor PDF processing performance and accuracy")
        logger.info("4. Test with real PDF attachments from apartment listings")
        return True
    else:
        logger.warning(f"⚠️  {total_steps - success_count} steps failed. Please review the errors above.")
        return False


if __name__ == "__main__":
    # Create log file
    log_file = f"week3_setup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    
    logger.info(f"Setup log will be saved to: {log_file}")
    
    success = main()
    sys.exit(0 if success else 1)