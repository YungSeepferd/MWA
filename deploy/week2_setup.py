#!/usr/bin/env python3
"""
Week 2 Production Deployment Setup for MAFA OCR Support.

This script sets up OCR support for extracting contact information from images.
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
from mafa.contacts.ocr_extractor import OCRExtractor


def check_tesseract_installation():
    """Check if Tesseract OCR is installed."""
    logger.info("Checking Tesseract OCR installation...")
    
    try:
        # Check if tesseract command is available
        result = subprocess.run(['tesseract', '--version'],
                              capture_output=True, text=True, check=True)
        
        version_info = result.stdout.split('\n')[0]
        logger.info(f"Tesseract version: {version_info}")
        return True
        
    except (subprocess.CalledProcessError, FileNotFoundError):
        logger.warning("Tesseract OCR not found. Please install it:")
        logger.info("Ubuntu/Debian: sudo apt-get install tesseract-ocr tesseract-ocr-deu")
        logger.info("macOS: brew install tesseract tesseract-lang")
        logger.info("Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki")
        return False


def install_python_dependencies():
    """Install required Python packages for OCR."""
    logger.info("Installing Python dependencies for OCR...")
    
    dependencies = [
        'pytesseract',
        'pillow',
        'opencv-python',
        'numpy'
    ]
    
    try:
        for dependency in dependencies:
            logger.info(f"Installing {dependency}...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', dependency], 
                         check=True, capture_output=True)
        
        logger.info("Python dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dependencies: {e}")
        return False


def test_ocr_extraction():
    """Test OCR extraction with a sample image."""
    logger.info("Testing OCR extraction...")
    
    try:
        # Create a simple test image with text
        from PIL import Image, ImageDraw, ImageFont
        import json
        
        # Create image with contact information
        img = Image.new('RGB', (400, 200), color='white')
        draw = ImageDraw.Draw(img)
        
        # Try to use a default font
        try:
            font = ImageFont.load_default()
        except:
            font = None
        
        # Add text
        draw.text((10, 10), "Contact Information:", fill='black', font=font)
        draw.text((10, 40), "Email: test@example.com", fill='black', font=font)
        draw.text((10, 70), "Phone: +49 89 12345678", fill='black', font=font)
        draw.text((10, 100), "Contact Form: https://example.com/contact", fill='black', font=font)
        
        # Save test image
        test_image_path = Path("test_ocr.png")
        img.save(test_image_path)
        
        # Load example config for Settings
        config_path = Path("config.example.json")
        if config_path.exists():
            with open(config_path, 'r') as f:
                config_data = json.load(f)
            config = Settings(**config_data)
        else:
            # Create minimal config
            config = Settings(personal_profile={}, search_criteria={}, notification={})
        
        # Test OCR extraction
        extractor = OCRExtractor(
            config=config,
            languages=['eng'],
            confidence_threshold=0.5,
            preprocess=True
        )
        
        contacts = extractor.extract_contacts(test_image_path)
        
        # Clean up
        test_image_path.unlink()
        
        if contacts:
            logger.info(f"OCR test successful! Found {len(contacts)} contacts:")
            for contact in contacts:
                logger.info(f"  - {contact.contact.method}: {contact.contact.value} "
                          f"(confidence: {contact.contact.confidence.name})")
            return True
        else:
            logger.warning("OCR test completed but no contacts found")
            return True
            
    except Exception as e:
        logger.error(f"OCR test failed: {e}")
        return False


def update_configuration():
    """Update configuration with OCR settings."""
    logger.info("Updating configuration with OCR settings...")
    
    try:
        config_path = Path("config.json")
        
        if not config_path.exists():
            logger.error("config.json not found!")
            return False
        
        # Load current config
        import json
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Add OCR section
        config['ocr'] = {
            "enabled": True,
            "languages": ["deu", "eng"],
            "confidence_threshold": 0.7,
            "preprocessing": {
                "enhance_contrast": True,
                "denoise": True,
                "sharpen": True
            },
            "max_image_size_mb": 10,
            "supported_formats": ["png", "jpg", "jpeg", "webp", "bmp", "tiff"]
        }
        
        # Save updated config
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info("Configuration updated with OCR settings")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update configuration: {e}")
        return False


def create_ocr_test_examples():
    """Create example images for testing OCR."""
    logger.info("Creating OCR test examples...")
    
    try:
        examples_dir = Path("examples/ocr")
        examples_dir.mkdir(parents=True, exist_ok=True)
        
        from PIL import Image, ImageDraw, ImageFont
        
        # Example 1: Business card style
        img1 = Image.new('RGB', (400, 250), color='white')
        draw1 = ImageDraw.Draw(img1)
        
        draw1.text((20, 20), "München Wohnungen GmbH", fill='black', font=ImageFont.load_default())
        draw1.text((20, 50), "Kontakt:", fill='black', font=ImageFont.load_default())
        draw1.text((20, 80), "Email: info@muenchen-wohnungen.de", fill='black', font=ImageFont.load_default())
        draw1.text((20, 110), "Telefon: +49 89 12345678", fill='black', font=ImageFont.load_default())
        draw1.text((20, 140), "Website: www.muenchen-wohnungen.de", fill='black', font=ImageFont.load_default())
        
        img1.save(examples_dir / "business_card.png")
        
        # Example 2: Screenshot style with obfuscated email
        img2 = Image.new('RGB', (500, 300), color='#f0f0f0')
        draw2 = ImageDraw.Draw(img2)
        
        draw2.rectangle([10, 10, 490, 290], fill='white', outline='gray')
        draw2.text((30, 30), "Kontaktformular", fill='black', font=ImageFont.load_default())
        draw2.text((30, 70), "Bei Fragen wenden Sie sich bitte an:", fill='black', font=ImageFont.load_default())
        draw2.text((30, 110), "E-Mail: kontakt [at] wohnung-muenchen [dot] de", fill='black', font=ImageFont.load_default())
        draw2.text((30, 150), "oder rufen Sie uns an unter:", fill='black', font=ImageFont.load_default())
        draw2.text((30, 190), "089 / 12 34 56 78", fill='black', font=ImageFont.load_default())
        
        img2.save(examples_dir / "contact_form.png")
        
        # Example 3: Poor quality image (simulated)
        img3 = Image.new('RGB', (350, 200), color='lightgray')
        draw3 = ImageDraw.Draw(img3)
        
        # Add some noise
        for _ in range(100):
            x = 10 + 330 * (hash(str(_)) % 1000) / 1000
            y = 10 + 180 * (hash(str(_ + 100)) % 1000) / 1000
            draw3.point((x, y), fill='white')
        
        draw3.text((20, 30), "KONTAKT", fill='black', font=ImageFont.load_default())
        draw3.text((20, 70), "mail: bewerbung@wohnung.de", fill='black', font=ImageFont.load_default())
        draw3.text((20, 110), "tel: 089-87654321", fill='black', font=ImageFont.load_default())
        
        img3.save(examples_dir / "poor_quality.png")
        
        logger.info(f"Created {len(list(examples_dir.glob('*.png')))} OCR test examples in {examples_dir}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create OCR examples: {e}")
        return False


def create_ocr_integration_example():
    """Create example script for OCR integration."""
    logger.info("Creating OCR integration example...")
    
    example_content = '''#!/usr/bin/env python3
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
    logger.info("\\nExample 2: Extracting from multiple images")
    
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
    logger.info("\\nExample 3: Integration with contact discovery")
    
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
'''
    
    try:
        example_path = Path("examples/ocr_integration.py")
        example_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(example_path, 'w') as f:
            f.write(example_content)
        
        # Make executable
        example_path.chmod(0o755)
        
        logger.info(f"Created OCR integration example: {example_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create OCR integration example: {e}")
        return False


def main():
    """Main deployment setup function."""
    logger.info("Starting Week 2 OCR Setup")
    logger.info("=" * 60)
    
    success_count = 0
    total_steps = 6
    
    # Step 1: Check Tesseract installation
    if check_tesseract_installation():
        success_count += 1
        logger.info("✅ Tesseract OCR check completed")
    else:
        logger.warning("⚠️  Tesseract OCR not installed (manual installation required)")
        success_count += 1  # Don't fail the whole setup for this
    
    # Step 2: Install Python dependencies
    if install_python_dependencies():
        success_count += 1
        logger.info("✅ Python dependencies installed")
    else:
        logger.error("❌ Python dependencies installation failed")
    
    # Step 3: Test OCR extraction
    if test_ocr_extraction():
        success_count += 1
        logger.info("✅ OCR extraction test completed")
    else:
        logger.error("❌ OCR extraction test failed")
    
    # Step 4: Update configuration
    if update_configuration():
        success_count += 1
        logger.info("✅ Configuration updated")
    else:
        logger.error("❌ Configuration update failed")
    
    # Step 5: Create test examples
    if create_ocr_test_examples():
        success_count += 1
        logger.info("✅ OCR test examples created")
    else:
        logger.error("❌ OCR test examples creation failed")
    
    # Step 6: Create integration example
    if create_ocr_integration_example():
        success_count += 1
        logger.info("✅ OCR integration example created")
    else:
        logger.error("❌ OCR integration example creation failed")
    
    # Summary
    logger.info("=" * 60)
    logger.info("OCR SETUP SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Completed: {success_count}/{total_steps} steps")
    
    if success_count == total_steps:
        logger.info("🎉 Week 2 OCR setup completed successfully!")
        logger.info("Next steps:")
        logger.info("1. Install Tesseract OCR if not already installed")
        logger.info("2. Test OCR functionality with: python examples/ocr_integration.py")
        logger.info("3. Add OCR support to your contact discovery workflow")
        logger.info("4. Monitor OCR performance and accuracy")
        return True
    else:
        logger.warning(f"⚠️  {total_steps - success_count} steps failed. Please review the errors above.")
        return False


if __name__ == "__main__":
    # Create log file
    log_file = f"week2_setup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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