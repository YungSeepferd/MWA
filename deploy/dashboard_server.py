#!/usr/bin/env python3
"""
Dashboard deployment script for MAFA Contact Review System.

This script starts the contact review dashboard server.
"""

import argparse
import logging
from pathlib import Path

from api.contact_review import ContactReviewDashboard
from mafa.contacts.storage import ContactStorage

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Start MAFA Contact Review Dashboard')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to')
    parser.add_argument('--port', type=int, default=8080, help='Port to bind to')
    parser.add_argument('--debug', action='store_true', help='Enable debug mode')
    parser.add_argument('--database', default='data/contacts.db', help='Database file path')
    
    args = parser.parse_args()
    
    logger.info("Starting MAFA Contact Review Dashboard...")
    logger.info(f"Host: {args.host}")
    logger.info(f"Port: {args.port}")
    logger.info(f"Database: {args.database}")
    logger.info(f"Debug: {args.debug}")
    
    try:
        # Initialize contact storage
        contact_storage = ContactStorage(args.database)
        
        # Initialize dashboard
        dashboard = ContactReviewDashboard(contact_storage)
        
        logger.info("Dashboard initialized successfully")
        logger.info(f"Access the dashboard at: http://{args.host}:{args.port}")
        
        # Run dashboard
        dashboard.run(host=args.host, port=args.port, debug=args.debug)
        
    except Exception as e:
        logger.error(f"Failed to start dashboard: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
