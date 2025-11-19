#!/usr/bin/env python3
"""
Week 1 Production Deployment Setup for MAFA Contact Discovery.

This script configures contact discovery settings, sets up monitoring,
and prepares the system for production deployment.
"""

import sys
import shutil
from pathlib import Path
from datetime import datetime
import json
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from mafa.config.settings import Settings
from mafa.contacts.storage import ContactStorage
from mafa.monitoring import get_health_checker, get_metrics_collector
from mafa.db.manager import ListingRepository


def setup_contact_discovery_config():
    """Set up contact discovery configuration for production."""
    logger.info("Setting up contact discovery configuration...")
    
    config_path = Path("config.json")
    example_path = Path("config.example.json")
    
    if not config_path.exists():
        if example_path.exists():
            logger.info("Creating config.json from example...")
            shutil.copy(example_path, config_path)
        else:
            logger.error("config.example.json not found!")
            return False
    
    try:
        # Load current config
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Add contact discovery section if not present
        if 'contact_discovery' not in config:
            config['contact_discovery'] = {
                "enabled": True,
                "confidence_threshold": "medium",
                "validation_enabled": True,
                "rate_limit_seconds": 1.0,
                "max_crawl_depth": 2,
                "blocked_domains": ["example.com", "test.com"],
                "preferred_contact_methods": ["email", "phone", "form"]
            }
            logger.info("Added contact discovery configuration")
        
        # Add storage section if not present
        if 'storage' not in config:
            config['storage'] = {
                "contact_retention_days": 90,
                "auto_cleanup_enabled": True,
                "backup_enabled": True
            }
            logger.info("Added storage configuration")
        
        # Save updated config
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info("Contact discovery configuration updated successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update configuration: {e}")
        return False


def setup_contact_database():
    """Set up contact database with proper permissions."""
    logger.info("Setting up contact database...")
    
    try:
        # Create data directory if it doesn't exist
        data_dir = Path("data")
        data_dir.mkdir(exist_ok=True)
        
        # Initialize contact storage (this creates the database)
        contact_storage = ContactStorage(data_dir / "contacts.db")
        
        # Test database connectivity
        stats = contact_storage.get_contact_statistics()
        logger.info(f"Contact database initialized successfully")
        logger.info(f"Current contact statistics: {stats}")
        
        # Set proper file permissions (Unix-like systems)
        try:
            import os
            os.chmod(data_dir / "contacts.db", 0o644)  # Readable by owner and group
            logger.info("Database permissions set")
        except Exception:
            logger.warning("Could not set database permissions (may be Windows)")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to set up contact database: {e}")
        return False


def setup_monitoring():
    """Set up monitoring for contact discovery failures."""
    logger.info("Setting up contact discovery monitoring...")
    
    try:
        # Initialize health checker
        health_checker = get_health_checker()
        
        # Get initial health status
        health_status = health_checker.get_health_status()
        
        logger.info(f"System health status: {health_status.status}")
        
        # Check contact discovery specifically
        contact_healthy, contact_msg = health_checker.check_contact_discovery_health()
        logger.info(f"Contact discovery health: {contact_healthy} - {contact_msg}")
        
        # Set up metrics collector
        metrics_collector = get_metrics_collector()
        
        logger.info("Monitoring setup completed")
        return True
        
    except Exception as e:
        logger.error(f"Failed to set up monitoring: {e}")
        return False


def create_production_config():
    """Create production-specific configuration file."""
    logger.info("Creating production configuration...")
    
    try:
        # Create production config directory
        prod_config_dir = Path("config/production")
        prod_config_dir.mkdir(parents=True, exist_ok=True)
        
        # Create production config template
        prod_config = {
            "contact_discovery": {
                "enabled": True,
                "confidence_threshold": "high",  # Stricter for production
                "validation_enabled": True,
                "rate_limit_seconds": 2.0,  # Slower for production
                "max_crawl_depth": 2,
                "blocked_domains": [
                    "example.com", "test.com", "localhost", "127.0.0.1"
                ],
                "preferred_contact_methods": ["email", "phone", "form"]
            },
            "storage": {
                "contact_retention_days": 180,  # Longer retention for production
                "auto_cleanup_enabled": True,
                "backup_enabled": True
            },
            "monitoring": {
                "alert_thresholds": {
                    "extraction_failure_rate": 0.3,  # 30% failure rate
                    "validation_failure_rate": 0.5,  # 50% validation failure
                    "slow_extraction_seconds": 60   # 60 seconds
                }
            }
        }
        
        # Save production config
        prod_config_path = prod_config_dir / "contact_discovery.json"
        with open(prod_config_path, 'w') as f:
            json.dump(prod_config, f, indent=2)
        
        logger.info(f"Production configuration created at: {prod_config_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create production config: {e}")
        return False


def run_health_checks():
    """Run comprehensive health checks."""
    logger.info("Running health checks...")
    
    try:
        health_checker = get_health_checker()
        health_status = health_checker.get_health_status()
        
        logger.info("=" * 50)
        logger.info("HEALTH CHECK RESULTS")
        logger.info("=" * 50)
        logger.info(f"Overall Status: {health_status.status}")
        logger.info(f"Timestamp: {health_status.timestamp}")
        
        for check_name, check_result in health_status.checks.items():
            status_icon = "✅" if check_result else "❌"
            logger.info(f"{status_icon} {check_name}: {check_result}")
        
        if health_status.issues:
            logger.error("CRITICAL ISSUES:")
            for issue in health_status.issues:
                logger.error(f"  - {issue}")
        
        if health_status.warnings:
            logger.warning("WARNINGS:")
            for warning in health_status.warnings:
                logger.warning(f"  - {warning}")
        
        logger.info("=" * 50)
        
        return health_status.status in ["healthy", "degraded"]
        
    except Exception as e:
        logger.error(f"Health checks failed: {e}")
        return False


def main():
    """Main deployment setup function."""
    logger.info("Starting Week 1 Production Deployment Setup")
    logger.info("=" * 60)
    
    success_count = 0
    total_steps = 5
    
    # Step 1: Configure contact discovery
    if setup_contact_discovery_config():
        success_count += 1
        logger.info("✅ Contact discovery configuration completed")
    else:
        logger.error("❌ Contact discovery configuration failed")
    
    # Step 2: Set up contact database
    if setup_contact_database():
        success_count += 1
        logger.info("✅ Contact database setup completed")
    else:
        logger.error("❌ Contact database setup failed")
    
    # Step 3: Set up monitoring
    if setup_monitoring():
        success_count += 1
        logger.info("✅ Monitoring setup completed")
    else:
        logger.error("❌ Monitoring setup failed")
    
    # Step 4: Create production config
    if create_production_config():
        success_count += 1
        logger.info("✅ Production configuration created")
    else:
        logger.error("❌ Production configuration creation failed")
    
    # Step 5: Run health checks
    if run_health_checks():
        success_count += 1
        logger.info("✅ Health checks passed")
    else:
        logger.error("❌ Health checks failed")
    
    # Summary
    logger.info("=" * 60)
    logger.info("DEPLOYMENT SETUP SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Completed: {success_count}/{total_steps} steps")
    
    if success_count == total_steps:
        logger.info("🎉 All Week 1 setup steps completed successfully!")
        logger.info("Next steps:")
        logger.info("1. Review the production configuration in config/production/")
        logger.info("2. Test contact discovery with the example script: examples/contact_discovery_integration.py")
        logger.info("3. Integrate contact discovery into your scraping workflow")
        logger.info("4. Monitor the system health and contact discovery metrics")
        return True
    else:
        logger.warning(f"⚠️  {total_steps - success_count} steps failed. Please review the errors above.")
        return False


if __name__ == "__main__":
    # Create log file
    log_file = f"week1_setup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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