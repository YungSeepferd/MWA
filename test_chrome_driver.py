#!/usr/bin/env python3
"""
Test script to verify Chrome driver and provider functionality.

This script tests the enhanced Selenium driver and provider implementations
to ensure they can successfully scrape real data from ImmoScout24 and WG-Gesucht.
"""

import logging
import sys
import json
from datetime import datetime
from typing import Dict, Any

# Configure logging to see what's happening
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'chrome_driver_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

logger = logging.getLogger(__name__)

def test_basic_driver():
    """Test basic Chrome driver functionality."""
    logger.info("=" * 50)
    logger.info("Testing basic Chrome driver...")
    
    try:
        from mafa.driver import SeleniumDriver
        
        with SeleniumDriver(headless=True, timeout=10) as driver:
            logger.info("✅ Chrome driver initialized successfully")
            
            # Test navigation to a simple page
            driver.get("https://httpbin.org/get")
            title = driver.title
            logger.info(f"✅ Successfully navigated to test page: {title}")
            
            # Test page source
            if driver.page_source:
                logger.info("✅ Page source retrieved successfully")
            else:
                logger.warning("⚠️  Page source is empty")
            
            return True
            
    except Exception as e:
        logger.error(f"❌ Basic driver test failed: {e}")
        return False

def test_immoscout_provider():
    """Test ImmoScout24 provider with real website."""
    logger.info("=" * 50)
    logger.info("Testing ImmoScout24 provider...")
    
    try:
        from mwa_core.providers.immoscout import ImmoScoutProvider
        
        # Use a simpler test URL first
        config = {
            "headless": True,
            "timeout": 30,
            "max_retries": 2
        }
        
        provider = ImmoScoutProvider()
        logger.info(f"Provider initialized with URL: {provider.base_url}")
        
        listings = provider.fetch_listings(config)
        
        logger.info(f"✅ ImmoScout scraping completed: {len(listings)} listings found")
        
        for i, listing in enumerate(listings[:3], 1):  # Show first 3 listings
            logger.info(f"  Listing {i}: {listing.title[:60]}...")
            logger.info(f"    Price: {listing.price}")
            logger.info(f"    URL: {listing.url[:80]}...")
        
        if len(listings) > 3:
            logger.info(f"  ... and {len(listings) - 3} more listings")
        
        return len(listings) > 0
        
    except Exception as e:
        logger.error(f"❌ ImmoScout provider test failed: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False

def test_wg_gesucht_provider():
    """Test WG-Gesucht provider with real website."""
    logger.info("=" * 50)
    logger.info("Testing WG-Gesucht provider...")
    
    try:
        from mwa_core.providers.wg_gesucht import WGGesuchtProvider
        
        config = {
            "headless": True,
            "timeout": 30,
            "max_retries": 2
        }
        
        provider = WGGesuchtProvider()
        logger.info(f"Provider initialized with URL: {provider.base_url}")
        
        listings = provider.fetch_listings(config)
        
        logger.info(f"✅ WG-Gesucht scraping completed: {len(listings)} listings found")
        
        for i, listing in enumerate(listings[:3], 1):  # Show first 3 listings
            logger.info(f"  Listing {i}: {listing.title[:60]}...")
            logger.info(f"    Price: {listing.price}")
            logger.info(f"    URL: {listing.url[:80]}...")
        
        if len(listings) > 3:
            logger.info(f"  ... and {len(listings) - 3} more listings")
        
        return len(listings) > 0
        
    except Exception as e:
        logger.error(f"❌ WG-Gesucht provider test failed: {e}")
        import traceback
        logger.error(f"Full traceback: {traceback.format_exc()}")
        return False

def test_config_loading():
    """Test configuration file loading."""
    logger.info("=" * 50)
    logger.info("Testing configuration loading...")
    
    try:
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        logger.info("✅ Configuration loaded successfully")
        logger.info(f"  Scrapers: {config.get('scrapers', [])}")
        logger.info(f"  Contact discovery enabled: {config.get('contact_discovery', {}).get('enabled', False)}")
        
        return True
        
    except FileNotFoundError:
        logger.warning("⚠️  config.json not found")
        return False
    except Exception as e:
        logger.error(f"❌ Configuration loading failed: {e}")
        return False

def main():
    """Run all tests and report results."""
    logger.info("🚀 Starting Chrome Driver and Provider Tests")
    logger.info(f"Test started at: {datetime.now()}")
    
    tests = [
        ("Configuration Loading", test_config_loading),
        ("Basic Chrome Driver", test_basic_driver),
        ("ImmoScout24 Provider", test_immoscout_provider),
        ("WG-Gesucht Provider", test_wg_gesucht_provider),
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results[test_name] = result
        except Exception as e:
            logger.error(f"❌ {test_name} failed with exception: {e}")
            results[test_name] = False
    
    # Summary
    logger.info("=" * 50)
    logger.info("TEST SUMMARY")
    logger.info("=" * 50)
    
    passed = 0
    failed = 0
    
    for test_name, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        logger.info(f"{test_name}: {status}")
        if result:
            passed += 1
        else:
            failed += 1
    
    logger.info("=" * 50)
    logger.info(f"Total: {len(results)} tests | Passed: {passed} | Failed: {failed}")
    
    if failed == 0:
        logger.info("🎉 All tests passed! Chrome driver is working correctly.")
        return 0
    else:
        logger.error(f"⚠️  {failed} test(s) failed. Check the logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())