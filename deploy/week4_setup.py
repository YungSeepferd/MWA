#!/usr/bin/env python3
"""
Week 4 Production Deployment Setup for MAFA JavaScript Rendering & Dashboard.

This script sets up JavaScript rendering for SPA sites and deploys the contact review dashboard.
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
from mafa.crawler.js_renderer import JSRenderer


def install_playwright_dependencies():
    """Install Playwright and browser dependencies."""
    logger.info("Installing Playwright dependencies...")
    
    try:
        # Install playwright
        logger.info("Installing playwright package...")
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'playwright'], 
                     check=True, capture_output=True)
        
        # Install browser binaries
        logger.info("Installing browser binaries...")
        subprocess.run([sys.executable, '-m', 'playwright', 'install', 'chromium'], 
                     check=True, capture_output=True)
        
        logger.info("Playwright dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install Playwright dependencies: {e}")
        return False


def install_dashboard_dependencies():
    """Install dependencies for the contact review dashboard."""
    logger.info("Installing dashboard dependencies...")
    
    dependencies = [
        'fastapi',
        'uvicorn',
        'jinja2',
        'python-multipart'  # For file uploads
    ]
    
    try:
        for dependency in dependencies:
            logger.info(f"Installing {dependency}...")
            subprocess.run([sys.executable, '-m', 'pip', 'install', dependency], 
                         check=True, capture_output=True)
        
        logger.info("Dashboard dependencies installed successfully")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install dashboard dependencies: {e}")
        return False


def test_javascript_rendering():
    """Test JavaScript rendering with a sample page."""
    logger.info("Testing JavaScript rendering...")
    
    try:
        import asyncio
        
        async def test_render():
            # Initialize renderer
            renderer = JSRenderer(
                timeout_seconds=30,
                wait_for_load=True,
                headless=True,
                confidence_threshold=0.6
            )
            
            # Test with a simple HTML page
            test_html = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Test Contact Page</title>
            </head>
            <body>
                <h1>Contact Information</h1>
                <p>Email: <span id="email">test@example.com</span></p>
                <p>Phone: <span id="phone">+49 89 12345678</span></p>
                <form action="/contact" method="post">
                    <input type="email" name="email" placeholder="Your email">
                    <input type="tel" name="phone" placeholder="Your phone">
                    <textarea name="message" placeholder="Your message"></textarea>
                    <button type="submit">Send</button>
                </form>
                <script>
                    // Simulate dynamic content loading
                    setTimeout(function() {
                        document.getElementById('email').textContent = 'dynamic@example.com';
                        document.getElementById('phone').textContent = '+49 89 87654321';
                    }, 1000);
                </script>
            </body>
            </html>
            """
            
            # Save test HTML
            test_path = Path("test_render.html")
            test_path.write_text(test_html)
            
            # Test rendering
            contacts = await renderer.extract_contacts(f"file://{test_path.absolute()}")
            
            # Clean up
            test_path.unlink()
            await renderer.close()
            
            return contacts
        
        # Run async test
        contacts = asyncio.run(test_render())
        
        if contacts:
            logger.info(f"JavaScript rendering test successful! Found {len(contacts)} contacts:")
            for contact in contacts:
                logger.info(f"  - {contact.contact.method}: {contact.contact.value} "
                          f"(confidence: {contact.contact.confidence.name})")
            return True
        else:
            logger.warning("JavaScript rendering test completed but no contacts found")
            return True
            
    except Exception as e:
        logger.error(f"JavaScript rendering test failed: {e}")
        return False


def create_dashboard_static_files():
    """Create additional static files for the dashboard."""
    logger.info("Creating dashboard static files...")
    
    try:
        # Create static directories
        static_dirs = [
            "dashboard/static/images",
            "dashboard/static/fonts"
        ]
        
        for dir_path in static_dirs:
            Path(dir_path).mkdir(parents=True, exist_ok=True)
        
        # Create favicon
        favicon_content = '''data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIzMiIgaGVpZ2h0PSIzMiIgdmlld0JveD0iMCAwIDMyIDMyIj4KICA8cmVjdCB3aWR0aD0iMzIiIGhlaWdodD0iMzIiIGZpbGw9IiMwMDdiZmYiIHJ4PSI0Ii8+CiAgPHN2ZyB4PSI4IiB5PSI4IiB3aWR0aD0iMTYiIGhlaWdodD0iMTYiIHZpZXdCb3g9IjAgMCAyNCAyNCIgZmlsbD0id2hpdGUiPgogICAgPHBhdGggZD0iTTEyIDJDNi40OCAyIDIgNi40OCAyIDEyczQuNDggMTAgMTAgMTAgMTAtNC40OCAxMC0xMFMxNy41MiAyIDEyIDJ6bTAgMThjLTQuNDEgMC04LTMuNTktOC04czMuNTktOCA4LTggOCAzLjU5IDggOC0zLjU5IDgtOCA4em0tMi0xM2gydjZoLTJ2LTZ6bTAgOGgydjJoLTJ2LTJ6Ii8+CiAgPC9zdmc+Cjwvc3ZnPgo='''
        
        # Save favicon
        import base64
        favicon_data = base64.b64decode(favicon_content.split(',')[1])
        Path("dashboard/static/images/favicon.ico").write_bytes(favicon_data)
        
        logger.info("Dashboard static files created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create dashboard static files: {e}")
        return False


def create_dashboard_deployment_script():
    """Create deployment script for the dashboard."""
    logger.info("Creating dashboard deployment script...")
    
    deployment_script = '''#!/usr/bin/env python3
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
'''
    
    try:
        script_path = Path("deploy/dashboard_server.py")
        script_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(script_path, 'w') as f:
            f.write(deployment_script)
        
        # Make executable
        script_path.chmod(0o755)
        
        logger.info(f"Created dashboard deployment script: {script_path}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to create dashboard deployment script: {e}")
        return False


def create_systemd_service():
    """Create systemd service file for the dashboard."""
    logger.info("Creating systemd service file...")
    
    service_content = '''[Unit]
Description=MAFA Contact Review Dashboard
After=network.target

[Service]
Type=simple
User=mafa
Group=mafa
WorkingDirectory=/opt/mafa
ExecStart=/usr/bin/python3 /opt/mafa/deploy/dashboard_server.py --host 0.0.0.0 --port 8080
Restart=always
RestartSec=10
Environment=PYTHONPATH=/opt/mafa

# Logging
StandardOutput=journal
StandardError=journal

# Security
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/mafa/data

[Install]
WantedBy=multi-user.target
'''
    
    try:
        service_path = Path("deploy/mafa-dashboard.service")
        service_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(service_path, 'w') as f:
            f.write(service_content)
        
        logger.info(f"Created systemd service file: {service_path}")
        logger.info("To install the service:")
        logger.info(f"  sudo cp {service_path} /etc/systemd/system/")
        logger.info("  sudo systemctl daemon-reload")
        logger.info("  sudo systemctl enable mafa-dashboard")
        logger.info("  sudo systemctl start mafa-dashboard")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to create systemd service file: {e}")
        return False


def update_configuration():
    """Update configuration with JavaScript rendering and dashboard settings."""
    logger.info("Updating configuration with JavaScript rendering and dashboard settings...")
    
    try:
        config_path = Path("config.json")
        
        if not config_path.exists():
            logger.error("config.json not found!")
            return False
        
        # Load current config
        import json
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        # Add JavaScript rendering section
        config['javascript_rendering'] = {
            "enabled": True,
            "timeout_seconds": 30,
            "wait_for_load": True,
            "block_resources": ["image", "stylesheet", "font", "media"],
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "viewport": {"width": 1920, "height": 1080},
            "headless": True,
            "confidence_threshold": 0.7
        }
        
        # Add dashboard section
        config['dashboard'] = {
            "enabled": True,
            "host": "0.0.0.0",
            "port": 8080,
            "require_auth": False,
            "auto_refresh_seconds": 30,
            "page_size": 50
        }
        
        # Save updated config
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        logger.info("Configuration updated with JavaScript rendering and dashboard settings")
        return True
        
    except Exception as e:
        logger.error(f"Failed to update configuration: {e}")
        return False


def main():
    """Main deployment setup function."""
    logger.info("Starting Week 4 JavaScript Rendering & Dashboard Setup")
    logger.info("=" * 60)
    
    success_count = 0
    total_steps = 7
    
    # Step 1: Install Playwright dependencies
    if install_playwright_dependencies():
        success_count += 1
        logger.info("✅ Playwright dependencies installed")
    else:
        logger.error("❌ Playwright dependencies installation failed")
    
    # Step 2: Install dashboard dependencies
    if install_dashboard_dependencies():
        success_count += 1
        logger.info("✅ Dashboard dependencies installed")
    else:
        logger.error("❌ Dashboard dependencies installation failed")
    
    # Step 3: Test JavaScript rendering
    if test_javascript_rendering():
        success_count += 1
        logger.info("✅ JavaScript rendering test completed")
    else:
        logger.error("❌ JavaScript rendering test failed")
    
    # Step 4: Create dashboard static files
    if create_dashboard_static_files():
        success_count += 1
        logger.info("✅ Dashboard static files created")
    else:
        logger.error("❌ Dashboard static files creation failed")
    
    # Step 5: Create deployment script
    if create_dashboard_deployment_script():
        success_count += 1
        logger.info("✅ Dashboard deployment script created")
    else:
        logger.error("❌ Dashboard deployment script creation failed")
    
    # Step 6: Create systemd service
    if create_systemd_service():
        success_count += 1
        logger.info("✅ Systemd service file created")
    else:
        logger.error("❌ Systemd service file creation failed")
    
    # Step 7: Update configuration
    if update_configuration():
        success_count += 1
        logger.info("✅ Configuration updated")
    else:
        logger.error("❌ Configuration update failed")
    
    # Summary
    logger.info("=" * 60)
    logger.info("JAVASCRIPT RENDERING & DASHBOARD SETUP SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Completed: {success_count}/{total_steps} steps")
    
    if success_count == total_steps:
        logger.info("🎉 Week 4 JavaScript rendering & dashboard setup completed successfully!")
        logger.info("Next steps:")
        logger.info("1. Start the dashboard: python deploy/dashboard_server.py")
        logger.info("2. Access the dashboard at: http://localhost:8080")
        logger.info("3. Test JavaScript rendering with SPA websites")
        logger.info("4. Monitor dashboard performance and user feedback")
        logger.info("5. Consider setting up authentication for production use")
        return True
    else:
        logger.warning(f"⚠️  {total_steps - success_count} steps failed. Please review the errors above.")
        return False


if __name__ == "__main__":
    # Create log file
    log_file = f"week4_setup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
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