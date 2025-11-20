#!/usr/bin/env python3
"""
MAFA Launcher - Simple web-based launcher for the Munich Apartment Finder Assistant.

This launcher provides a user-friendly web interface to:
- Check system status (Poetry, config, API)
- Start the application in different modes (dev, prod, dry-run)
- Configure settings
- Monitor logs
- Redirect to the dashboard
"""

import os
import sys
import json
import subprocess
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional

from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from mafa.config.settings import get_settings


class MafaLauncher:
    """MAFA Application Launcher with web interface."""
    
    def __init__(self):
        self.app = Flask(__name__)
        CORS(self.app)
        self.app.config['SECRET_KEY'] = 'mafa-launcher-secret-key'
        
        # Application state
        self.process = None
        self.is_running = False
        self.logs = []
        self.config = {
            'mode': 'dev',
            'config_path': 'config.json',
            'discord_webhook': '',
            'host': '0.0.0.0',
            'port': 8000
        }
        
        # Setup routes
        self.setup_routes()
        
    def setup_routes(self):
        """Setup Flask routes for the launcher."""
        
        @self.app.route('/')
        def index():
            """Serve the launcher HTML interface."""
            html_file = Path(__file__).parent / 'launcher.html'
            if html_file.exists():
                return html_file.read_text()
            else:
                return self.generate_default_html()
        
        @self.app.route('/api/launcher/status')
        def status():
            """Check system status."""
            return jsonify(self.check_status())
        
        @self.app.route('/api/launcher/start', methods=['POST'])
        def start():
            """Start the MAFA application."""
            data = request.get_json() or {}
            return jsonify(self.start_application(data))
        
        @self.app.route('/api/launcher/stop', methods=['POST'])
        def stop():
            """Stop the MAFA application."""
            return jsonify(self.stop_application())
        
        @self.app.route('/api/launcher/logs')
        def logs():
            """Get application logs."""
            return jsonify({'logs': self.logs})
        
        @self.app.route('/api/launcher/config', methods=['GET', 'POST'])
        def config():
            """Get or update launcher configuration."""
            if request.method == 'POST':
                data = request.get_json() or {}
                self.config.update(data)
                return jsonify({'success': True, 'config': self.config})
            return jsonify({'config': self.config})
    
    def check_status(self) -> Dict[str, Any]:
        """Check system status."""
        status = {
            'poetry_ready': self.check_poetry(),
            'config_ready': self.check_config(),
            'api_running': self.is_running,
            'launcher_running': True
        }
        return status
    
    def check_poetry(self) -> bool:
        """Check if Poetry is installed and environment is ready."""
        try:
            result = subprocess.run(
                ['poetry', '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def check_config(self) -> bool:
        """Check if configuration file exists."""
        config_path = Path(self.config['config_path'])
        return config_path.exists()
    
    def start_application(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Start the MAFA application."""
        if self.is_running:
            return {'success': False, 'error': 'Application is already running'}
        
        try:
            # Update configuration
            self.config.update(config)
            
            # Validate configuration
            if not self.check_poetry():
                return {'success': False, 'error': 'Poetry is not installed or not in PATH'}
            
            if not self.check_config():
                return {'success': False, 'error': f'Config file not found: {self.config["config_path"]}'}
            
            # Start application based on mode
            mode = self.config['mode']
            self.log(f'Starting application in {mode} mode...')
            
            if mode == 'dev':
                self.start_dev_server()
            elif mode == 'prod':
                self.start_prod_server()
            elif mode == 'dryrun':
                self.start_dryrun()
            else:
                return {'success': False, 'error': f'Unknown mode: {mode}'}
            
            self.is_running = True
            return {'success': True, 'message': f'Application started in {mode} mode'}
            
        except Exception as e:
            self.log(f'Error starting application: {str(e)}', 'error')
            return {'success': False, 'error': str(e)}
    
    def start_dev_server(self):
        """Start development server with hot-reload."""
        self.log('Starting development server with hot-reload...')
        
        cmd = [
            'poetry', 'run', 'uvicorn',
            'api.main:app',
            '--host', self.config['host'],
            '--port', str(self.config['port']),
            '--reload',
            '--log-level', 'info'
        ]
        
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        # Start log monitoring threads
        threading.Thread(target=self.monitor_stdout, daemon=True).start()
        threading.Thread(target=self.monitor_stderr, daemon=True).start()
        
        self.log(f'Development server started on {self.config["host"]}:{self.config["port"]}')
    
    def start_prod_server(self):
        """Start production server."""
        self.log('Starting production server...')
        
        cmd = [
            'poetry', 'run', 'uvicorn',
            'api.main:app',
            '--host', self.config['host'],
            '--port', str(self.config['port']),
            '--workers', '4',
            '--log-level', 'warning'
        ]
        
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        threading.Thread(target=self.monitor_stdout, daemon=True).start()
        threading.Thread(target=self.monitor_stderr, daemon=True).start()
        
        self.log(f'Production server started on {self.config["host"]}:{self.config["port"]}')
    
    def start_dryrun(self):
        """Start application in dry-run mode."""
        self.log('Starting application in dry-run mode...')
        
        cmd = [
            'poetry', 'run', 'python', 'run.py',
            '--dry-run'
        ]
        
        if self.config['config_path'] != 'config.json':
            cmd.extend(['--config', self.config['config_path']])
        
        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        
        threading.Thread(target=self.monitor_stdout, daemon=True).start()
        threading.Thread(target=self.monitor_stderr, daemon=True).start()
        
        self.log('Dry-run mode started')
    
    def stop_application(self) -> Dict[str, Any]:
        """Stop the running application."""
        if not self.is_running or not self.process:
            return {'success': False, 'error': 'Application is not running'}
        
        try:
            self.log('Stopping application...')
            self.process.terminate()
            
            # Wait for graceful shutdown
            try:
                self.process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.log('Force killing process...', 'warning')
                self.process.kill()
                self.process.wait()
            
            self.is_running = False
            self.process = None
            self.log('Application stopped successfully')
            
            return {'success': True, 'message': 'Application stopped'}
            
        except Exception as e:
            self.log(f'Error stopping application: {str(e)}', 'error')
            return {'success': False, 'error': str(e)}
    
    def monitor_stdout(self):
        """Monitor stdout from the application process."""
        if not self.process or not self.process.stdout:
            return
        
        for line in iter(self.process.stdout.readline, ''):
            if line.strip():
                self.log(line.strip(), 'info')
    
    def monitor_stderr(self):
        """Monitor stderr from the application process."""
        if not self.process or not self.process.stderr:
            return
        
        for line in iter(self.process.stderr.readline, ''):
            if line.strip():
                self.log(line.strip(), 'warning')
    
    def log(self, message: str, level: str = 'info'):
        """Add log entry."""
        timestamp = time.strftime('%H:%M:%S')
        self.logs.append({
            'timestamp': timestamp,
            'message': message,
            'level': level
        })
        
        # Keep only last 100 logs
        if len(self.logs) > 100:
            self.logs = self.logs[-100:]
        
        print(f'[{timestamp}] {level.upper()}: {message}')
    
    def generate_default_html(self) -> str:
        """Generate default HTML if launcher.html is not found."""
        return '''
<!DOCTYPE html>
<html>
<head>
    <title>MAFA Launcher</title>
    <style>
        body { font-family: Arial, sans-serif; text-align: center; padding: 50px; }
        .error { color: red; }
    </style>
</head>
<body>
    <h1>MAFA Launcher</h1>
    <p class="error">Error: launcher.html not found!</p>
    <p>Please ensure launcher.html is in the same directory as launcher.py</p>
</body>
</html>
        '''
    
    def run(self, host: str = '127.0.0.1', port: int = 8080):
        """Run the launcher server."""
        print(f'''
🚀 MAFA Launcher Starting...
═══════════════════════════════════════

📊 Launcher UI: http://{host}:{port}
🎯 Dashboard: http://localhost:8000 (after starting)
📚 API Docs: http://localhost:8000/docs (after starting)

🔧 Features:
   • System status monitoring
   • Multiple launch modes (dev/prod/dry-run)
   • Real-time log viewing
   • Configuration management
   • Automatic dashboard redirection

📋 Next Steps:
   1. Open http://{host}:{port} in your browser
   2. Check system status
   3. Configure settings
   4. Click "Start Application"
   5. Get redirected to dashboard automatically!

        ''')
        
        self.app.run(host=host, port=port, debug=False)


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='MAFA Launcher')
    parser.add_argument('--host', default='127.0.0.1', help='Launcher host (default: 127.0.0.1)')
    parser.add_argument('--port', type=int, default=8080, help='Launcher port (default: 8080)')
    parser.add_argument('--config', default='config.json', help='Config file path (default: config.json)')
    
    args = parser.parse_args()
    
    # Create launcher instance
    launcher = MafaLauncher()
    launcher.config['config_path'] = args.config
    
    # Run the launcher
    try:
        launcher.run(host=args.host, port=args.port)
    except KeyboardInterrupt:
        print('\n\n👋 Launcher stopped by user')
        if launcher.is_running:
            print('Stopping application...')
            launcher.stop_application()
    except Exception as e:
        print(f'\n\n❌ Launcher error: {e}')
        sys.exit(1)


if __name__ == '__main__':
    main()