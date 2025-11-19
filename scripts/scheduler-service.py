#!/usr/bin/env python3
"""
Scheduler service script for running the MWA Core scheduler as a system service.

This script provides a simple way to run the scheduler as a background service
with proper logging and signal handling.
"""

import argparse
import logging
import signal
import sys
import time
from pathlib import Path

from mwa_core.scheduler import start_scheduler, stop_scheduler
from mwa_core.config import get_settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/scheduler.log')
    ]
)
logger = logging.getLogger(__name__)


class SchedulerService:
    """Scheduler service with proper signal handling and logging."""
    
    def __init__(self, config_path=None):
        self.config_path = config_path
        self.running = False
        self.scheduler = None
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown."""
        def signal_handler(signum, frame):
            logger.info(f"Received signal {signum}, shutting down gracefully...")
            self.stop()
            sys.exit(0)
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
    
    def start(self):
        """Start the scheduler service."""
        logger.info("Starting MWA Core Scheduler Service...")
        
        try:
            # Load settings if config path provided
            if self.config_path:
                settings = get_settings()
                settings.config_path = Path(self.config_path)
                settings = settings.load()
                logger.info(f"Loaded configuration from {settings.config_path}")
            
            # Start scheduler
            self.scheduler = start_scheduler()
            self.running = True
            
            logger.info("Scheduler service started successfully")
            
            # Keep the service running
            while self.running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Scheduler service interrupted by user")
            self.stop()
        except Exception as e:
            logger.error(f"Scheduler service failed: {e}", exc_info=True)
            self.stop()
            sys.exit(1)
    
    def stop(self):
        """Stop the scheduler service."""
        if not self.running:
            return
        
        logger.info("Stopping scheduler service...")
        self.running = False
        
        try:
            stop_scheduler(wait=True)
            logger.info("Scheduler service stopped successfully")
        except Exception as e:
            logger.error(f"Error stopping scheduler service: {e}")


def main():
    """Main entry point for the scheduler service."""
    parser = argparse.ArgumentParser(
        description="MWA Core Scheduler Service",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Start scheduler with default configuration
    python scheduler-service.py start
    
    # Start scheduler with custom configuration
    python scheduler-service.py start --config /path/to/config.json
    
    # Run in foreground with verbose logging
    python scheduler-service.py start --verbose
    
    # Stop the service (if running as daemon)
    python scheduler-service.py stop
        """
    )
    
    parser.add_argument(
        'command',
        choices=['start', 'stop', 'status'],
        help='Command to execute'
    )
    
    parser.add_argument(
        '--config',
        type=str,
        help='Path to configuration file'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    parser.add_argument(
        '--daemon',
        action='store_true',
        help='Run as daemon (background process)'
    )
    
    parser.add_argument(
        '--pidfile',
        type=str,
        default='/tmp/mwa-scheduler.pid',
        help='PID file path (default: /tmp/mwa-scheduler.pid)'
    )
    
    parser.add_argument(
        '--logfile',
        type=str,
        default='logs/scheduler.log',
        help='Log file path (default: logs/scheduler.log)'
    )
    
    args = parser.parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Ensure log directory exists
    log_path = Path(args.logfile)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Add file handler if not already present
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(logging.DEBUG if args.verbose else logging.INFO)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    
    # Get root logger and add file handler
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    
    if args.command == 'start':
        if args.daemon:
            # Daemonize the process
            daemonize(args.pidfile)
        
        # Create and start service
        service = SchedulerService(args.config)
        service.start()
        
    elif args.command == 'stop':
        # Stop the daemon
        stop_daemon(args.pidfile)
        
    elif args.command == 'status':
        # Check status
        check_status(args.pidfile)


def daemonize(pidfile):
    """Daemonize the current process."""
    try:
        # Check if already running
        if Path(pidfile).exists():
            with open(pidfile, 'r') as f:
                old_pid = int(f.read().strip())
            try:
                # Check if process is still running
                import os
                os.kill(old_pid, 0)
                print(f"Scheduler is already running with PID {old_pid}")
                sys.exit(1)
            except ProcessLookupError:
                # Process is not running, remove stale PID file
                Path(pidfile).unlink()
        
        # Double fork to daemonize
        try:
            pid = os.fork()
            if pid > 0:
                # Parent process
                sys.exit(0)
        except OSError as e:
            print(f"Fork #1 failed: {e}")
            sys.exit(1)
        
        # Decouple from parent environment
        os.chdir('/')
        os.setsid()
        os.umask(0)
        
        # Second fork
        try:
            pid = os.fork()
            if pid > 0:
                # Parent process
                sys.exit(0)
        except OSError as e:
            print(f"Fork #2 failed: {e}")
            sys.exit(1)
        
        # Redirect standard file descriptors
        sys.stdout.flush()
        sys.stderr.flush()
        
        si = open('/dev/null', 'r')
        so = open('/dev/null', 'a+')
        se = open('/dev/null', 'a+')
        
        os.dup2(si.fileno(), sys.stdin.fileno())
        os.dup2(so.fileno(), sys.stdout.fileno())
        os.dup2(se.fileno(), sys.stderr.fileno())
        
        # Write PID file
        with open(pidfile, 'w') as f:
            f.write(str(os.getpid()))
        
        logger.info(f"Daemonized process with PID {os.getpid()}")
        
    except Exception as e:
        print(f"Failed to daemonize: {e}")
        sys.exit(1)


def stop_daemon(pidfile):
    """Stop the daemon process."""
    try:
        if not Path(pidfile).exists():
            print("Scheduler is not running (no PID file found)")
            return
        
        with open(pidfile, 'r') as f:
            pid = int(f.read().strip())
        
        import os
        os.kill(pid, signal.SIGTERM)
        
        # Wait for process to terminate
        for _ in range(10):  # Wait up to 10 seconds
            try:
                os.kill(pid, 0)
                time.sleep(1)
            except ProcessLookupError:
                break
        
        # Remove PID file
        Path(pidfile).unlink()
        print(f"Scheduler stopped (PID {pid})")
        
    except ProcessLookupError:
        print(f"Scheduler process not found (PID {pid})")
        Path(pidfile).unlink(missing_ok=True)
    except Exception as e:
        print(f"Failed to stop scheduler: {e}")


def check_status(pidfile):
    """Check if scheduler is running."""
    try:
        if not Path(pidfile).exists():
            print("Scheduler is not running")
            return
        
        with open(pidfile, 'r') as f:
            pid = int(f.read().strip())
        
        import os
        os.kill(pid, 0)
        print(f"Scheduler is running with PID {pid}")
        
    except ProcessLookupError:
        print("Scheduler is not running (stale PID file)")
        Path(pidfile).unlink(missing_ok=True)
    except Exception as e:
        print(f"Error checking status: {e}")


if __name__ == "__main__":
    main()