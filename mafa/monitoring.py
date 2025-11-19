"""
Monitoring and health check infrastructure for MAFA.

Provides system health monitoring, performance metrics, and alerting
capabilities for production deployment.
"""

import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import sqlite3
import json
import os
from loguru import logger


@dataclass
class SystemMetrics:
    """System performance metrics."""
    timestamp: str
    cpu_percent: float
    memory_percent: float
    disk_usage_percent: float
    active_threads: int
    uptime_seconds: float


@dataclass
class ContactDiscoveryMetrics:
    """Contact discovery-specific metrics."""
    timestamp: str
    total_extractions: int
    successful_extractions: int
    failed_extractions: int
    contacts_found: int
    emails_found: int
    phones_found: int
    forms_found: int
    high_confidence_contacts: int
    validation_failures: int
    extraction_duration: float
    average_extraction_duration: float


@dataclass
class ApplicationMetrics:
    """Application-specific metrics."""
    timestamp: str
    total_scrapes: int
    successful_scrapes: int
    failed_scrapes: int
    listings_found: int
    new_listings: int
    database_size_mb: float
    last_scrape_duration: float
    average_scrape_duration: float
    contact_discovery: ContactDiscoveryMetrics = None


@dataclass
class HealthStatus:
    """Overall health status of the application."""
    status: str  # "healthy", "degraded", "unhealthy"
    timestamp: str
    checks: Dict[str, bool]
    issues: List[str]
    warnings: List[str]


class MetricsCollector:
    """Collects and stores system and application metrics."""
    
    def __init__(self, data_dir: Path):
        self.data_dir = data_dir
        self.metrics_file = data_dir / "metrics.json"
        self.data_dir.mkdir(exist_ok=True)
        
        # In-memory storage for recent metrics
        self.recent_metrics: List[Dict] = []
        self.max_metrics_history = 1000
        
        # Application counters
        self.scrapes_total = 0
        self.scrapes_success = 0
        self.scrapes_failed = 0
        self.total_listings = 0
        self.new_listings = 0
        self.scrape_durations: List[float] = []
        
        # Contact discovery counters
        self.contact_extractions_total = 0
        self.contact_extractions_success = 0
        self.contact_extractions_failed = 0
        self.contacts_found_total = 0
        self.emails_found = 0
        self.phones_found = 0
        self.forms_found = 0
        self.high_confidence_contacts = 0
        self.validation_failures = 0
        self.extraction_durations: List[float] = []
        
        # Start background monitoring if in production
        self._start_background_monitoring()
    
    def _start_background_monitoring(self):
        """Start background thread for system monitoring."""
        def monitor_loop():
            while True:
                try:
                    # Collect system metrics every 60 seconds
                    metrics = self._collect_system_metrics()
                    self._store_metrics(metrics)
                    time.sleep(60)
                except Exception as e:
                    logger.error(f"Error in background monitoring: {e}")
                    time.sleep(60)
        
        # Only start background monitoring if not in test mode
        if not os.environ.get('MAFA_TEST_MODE'):
            monitor_thread = threading.Thread(target=monitor_loop, daemon=True)
            monitor_thread.start()
    
    def _collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics."""
        return SystemMetrics(
            timestamp=datetime.now().isoformat(),
            cpu_percent=psutil.cpu_percent(interval=1),
            memory_percent=psutil.virtual_memory().percent,
            disk_usage_percent=psutil.disk_usage('/').percent,
            active_threads=threading.active_count(),
            uptime_seconds=time.time() - psutil.boot_time()
        )
    
    def _collect_contact_discovery_metrics(self) -> ContactDiscoveryMetrics:
        """Collect current contact discovery metrics."""
        # Calculate average extraction duration
        avg_extraction_duration = 0.0
        if self.extraction_durations:
            avg_extraction_duration = sum(self.extraction_durations) / len(self.extraction_durations)
        
        # Get last extraction duration
        last_extraction_duration = 0.0
        if self.extraction_durations:
            last_extraction_duration = self.extraction_durations[-1]
        
        return ContactDiscoveryMetrics(
            timestamp=datetime.now().isoformat(),
            total_extractions=self.contact_extractions_total,
            successful_extractions=self.contact_extractions_success,
            failed_extractions=self.contact_extractions_failed,
            contacts_found=self.contacts_found_total,
            emails_found=self.emails_found,
            phones_found=self.phones_found,
            forms_found=self.forms_found,
            high_confidence_contacts=self.high_confidence_contacts,
            validation_failures=self.validation_failures,
            extraction_duration=last_extraction_duration,
            average_extraction_duration=avg_extraction_duration
        )

    def _collect_application_metrics(self) -> ApplicationMetrics:
        """Collect current application metrics."""
        # Get database size
        db_path = self.data_dir / "listings.db"
        db_size_mb = 0.0
        if db_path.exists():
            db_size_mb = db_path.stat().st_size / (1024 * 1024)
        
        # Calculate average scrape duration
        avg_duration = 0.0
        if self.scrape_durations:
            avg_duration = sum(self.scrape_durations) / len(self.scrape_durations)
        
        # Get last scrape duration
        last_duration = 0.0
        if self.scrape_durations:
            last_duration = self.scrape_durations[-1]
        
        # Collect contact discovery metrics
        contact_metrics = self._collect_contact_discovery_metrics()
        
        return ApplicationMetrics(
            timestamp=datetime.now().isoformat(),
            total_scrapes=self.scrapes_total,
            successful_scrapes=self.scrapes_success,
            failed_scrapes=self.scrapes_failed,
            listings_found=self.total_listings,
            new_listings=self.new_listings,
            database_size_mb=db_size_mb,
            last_scrape_duration=last_duration,
            average_scrape_duration=avg_duration,
            contact_discovery=contact_metrics
        )
    
    def _store_metrics(self, metrics: SystemMetrics):
        """Store metrics to file and in-memory buffer."""
        metrics_dict = asdict(metrics)
        
        # Add to in-memory buffer
        self.recent_metrics.append(metrics_dict)
        
        # Limit buffer size
        if len(self.recent_metrics) > self.max_metrics_history:
            self.recent_metrics = self.recent_metrics[-self.max_metrics_history:]
        
        # Append to file
        try:
            existing_data = []
            if self.metrics_file.exists():
                with open(self.metrics_file, 'r') as f:
                    existing_data = json.load(f)
            
            existing_data.append(metrics_dict)
            
            # Keep only last 10000 entries in file
            if len(existing_data) > 10000:
                existing_data = existing_data[-10000:]
            
            with open(self.metrics_file, 'w') as f:
                json.dump(existing_data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Failed to store metrics: {e}")
    
    def record_contact_extraction(self, duration: float, success: bool, contacts_found: int = 0,
                                emails: int = 0, phones: int = 0, forms: int = 0,
                                high_confidence: int = 0, validation_failures: int = 0):
        """Record a contact extraction attempt."""
        self.contact_extractions_total += 1
        self.extraction_durations.append(duration)
        
        if success:
            self.contact_extractions_success += 1
        else:
            self.contact_extractions_failed += 1
        
        self.contacts_found_total += contacts_found
        self.emails_found += emails
        self.phones_found += phones
        self.forms_found += forms
        self.high_confidence_contacts += high_confidence
        self.validation_failures += validation_failures
        
        # Keep only last 100 durations for average calculation
        if len(self.extraction_durations) > 100:
            self.extraction_durations = self.extraction_durations[-100:]
        
        # Log warning if high failure rate
        if self.contact_extractions_total > 10:
            failure_rate = self.contact_extractions_failed / self.contact_extractions_total
            if failure_rate > 0.3:  # 30% failure rate
                logger.warning(f"High contact extraction failure rate: {failure_rate:.1%}")
        
        # Store application metrics immediately
        app_metrics = self._collect_application_metrics()
        self._store_metrics(app_metrics)

    def record_scrape_attempt(self, duration: float, success: bool, listings_found: int = 0, new_listings: int = 0):
        """Record a scrape attempt."""
        self.scrapes_total += 1
        self.scrape_durations.append(duration)
        
        if success:
            self.scrapes_success += 1
        else:
            self.scrapes_failed += 1
        
        self.total_listings += listings_found
        self.new_listings += new_listings
        
        # Keep only last 100 durations for average calculation
        if len(self.scrape_durations) > 100:
            self.scrape_durations = self.scrape_durations[-100:]
        
        # Store application metrics immediately
        app_metrics = self._collect_application_metrics()
        self._store_metrics(app_metrics)
    
    def get_recent_metrics(self, hours: int = 1) -> List[SystemMetrics]:
        """Get metrics from the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        recent = []
        for metrics_dict in self.recent_metrics:
            try:
                metrics_time = datetime.fromisoformat(metrics_dict['timestamp'])
                if metrics_time > cutoff_time:
                    recent.append(metrics_dict)
            except Exception:
                continue
        
        return recent
    
    def get_application_summary(self) -> ApplicationMetrics:
        """Get current application metrics summary."""
        return self._collect_application_metrics()


class HealthChecker:
    """Performs health checks on various system components."""
    
    def __init__(self, data_dir: Path, config_path: Optional[Path] = None):
        self.data_dir = data_dir
        self.config_path = config_path
        self.data_dir.mkdir(exist_ok=True)
    
    def check_database_health(self) -> tuple[bool, str]:
        """Check database connectivity and integrity."""
        try:
            db_path = self.data_dir / "listings.db"
            if not db_path.exists():
                return True, "Database file doesn't exist yet (will be created on first use)"
            
            with sqlite3.connect(db_path) as conn:
                # Test basic query
                cursor = conn.execute("SELECT COUNT(*) FROM listings LIMIT 1")
                cursor.fetchone()
                
                # Check if we can write
                conn.execute("BEGIN")
                conn.execute("ROLLBACK")
                
            return True, f"Database accessible ({db_path.stat().st_size / 1024:.1f} KB)"
            
        except Exception as e:
            return False, f"Database error: {str(e)}"
    
    def check_configuration_health(self) -> tuple[bool, str]:
        """Check configuration file validity."""
        try:
            if not self.config_path:
                return True, "No custom config path specified"
            
            if not self.config_path.exists():
                return False, f"Configuration file not found: {self.config_path}"
            
            # Basic validation
            with open(self.config_path, 'r') as f:
                config_data = json.load(f)
            
            required_sections = ['personal_profile', 'search_criteria', 'notification']
            for section in required_sections:
                if section not in config_data:
                    return False, f"Missing required config section: {section}"
            
            return True, f"Configuration file valid ({len(json.dumps(config_data))} bytes)"
            
        except json.JSONDecodeError as e:
            return False, f"Invalid JSON in configuration: {str(e)}"
        except Exception as e:
            return False, f"Configuration error: {str(e)}"
    
    def check_disk_space(self) -> tuple[bool, str]:
        """Check available disk space."""
        try:
            disk_usage = psutil.disk_usage('/')
            free_gb = disk_usage.free / (1024**3)
            total_gb = disk_usage.total / (1024**3)
            usage_percent = (disk_usage.used / disk_usage.total) * 100
            
            if usage_percent > 90:
                return False, f"Disk space critical: {usage_percent:.1f}% used, {free_gb:.1f}GB free"
            elif usage_percent > 80:
                return True, f"Disk space warning: {usage_percent:.1f}% used, {free_gb:.1f}GB free"
            else:
                return True, f"Disk space healthy: {usage_percent:.1f}% used, {free_gb:.1f}GB free"
                
        except Exception as e:
            return False, f"Disk space check failed: {str(e)}"
    
    def check_memory_usage(self) -> tuple[bool, str]:
        """Check system memory usage."""
        try:
            memory = psutil.virtual_memory()
            usage_percent = memory.percent
            available_gb = memory.available / (1024**3)
            
            if usage_percent > 90:
                return False, f"Memory usage critical: {usage_percent:.1f}% used, {available_gb:.1f}GB available"
            elif usage_percent > 80:
                return True, f"Memory usage warning: {usage_percent:.1f}% used, {available_gb:.1f}GB available"
            else:
                return True, f"Memory usage healthy: {usage_percent:.1f}% used, {available_gb:.1f}GB available"
                
        except Exception as e:
            return False, f"Memory check failed: {str(e)}"
    
    def check_contact_discovery_health(self) -> tuple[bool, str]:
        """Check contact discovery system health."""
        try:
            from mafa.monitoring import get_metrics_collector
            metrics_collector = get_metrics_collector(self.data_dir)
            
            # Check if contact discovery is being used
            if metrics_collector.contact_extractions_total == 0:
                return True, "No contact extractions performed yet (normal for new deployment)"
            
            # Check failure rate
            if metrics_collector.contact_extractions_total > 10:
                failure_rate = metrics_collector.contact_extractions_failed / metrics_collector.contact_extractions_total
                if failure_rate > 0.5:  # 50% failure rate
                    return False, f"Critical: High contact extraction failure rate: {failure_rate:.1%}"
                elif failure_rate > 0.3:  # 30% failure rate
                    return True, f"Warning: Elevated contact extraction failure rate: {failure_rate:.1%}"
            
            # Check contact discovery performance
            if metrics_collector.extraction_durations:
                avg_duration = sum(metrics_collector.extraction_durations) / len(metrics_collector.extraction_durations)
                if avg_duration > 60:  # 60 seconds average
                    return True, f"Warning: Slow contact extraction (avg: {avg_duration:.1f}s)"
            
            # Check validation failure rate
            if metrics_collector.contacts_found_total > 0:
                validation_failure_rate = metrics_collector.validation_failures / metrics_collector.contacts_found_total
                if validation_failure_rate > 0.7:  # 70% validation failure rate
                    return False, f"Critical: High contact validation failure rate: {validation_failure_rate:.1%}"
            
            return True, f"Contact discovery healthy ({metrics_collector.contacts_found_total} contacts found, {metrics_collector.high_confidence_contacts} high confidence)"
            
        except Exception as e:
            return False, f"Contact discovery health check failed: {str(e)}"
    
    def get_health_status(self) -> HealthStatus:
        """Perform comprehensive health check."""
        checks = {}
        issues = []
        warnings = []
        
        # Database health
        db_healthy, db_msg = self.check_database_health()
        checks['database'] = db_healthy
        if not db_healthy:
            issues.append(db_msg)
        
        # Configuration health
        config_healthy, config_msg = self.check_configuration_health()
        checks['configuration'] = config_healthy
        if not config_healthy:
            issues.append(config_msg)
        
        # Contact discovery health
        contact_healthy, contact_msg = self.check_contact_discovery_health()
        checks['contact_discovery'] = contact_healthy
        if not contact_healthy:
            if "Critical" in contact_msg:
                issues.append(contact_msg)
            else:
                warnings.append(contact_msg)
        
        # Disk space
        disk_healthy, disk_msg = self.check_disk_space()
        checks['disk_space'] = disk_healthy
        if not disk_healthy:
            if "critical" in disk_msg.lower():
                issues.append(disk_msg)
            else:
                warnings.append(disk_msg)
        
        # Memory usage
        memory_healthy, memory_msg = self.check_memory_usage()
        checks['memory'] = memory_healthy
        if not memory_healthy:
            if "critical" in memory_msg.lower():
                issues.append(memory_msg)
            else:
                warnings.append(memory_msg)
        
        # Determine overall status
        if issues:
            status = "unhealthy"
        elif warnings:
            status = "degraded"
        else:
            status = "healthy"
        
        return HealthStatus(
            status=status,
            timestamp=datetime.now().isoformat(),
            checks=checks,
            issues=issues,
            warnings=warnings
        )


class PerformanceOptimizer:
    """Performance optimization utilities."""
    
    @staticmethod
    def optimize_database(db_path: Path):
        """Optimize SQLite database performance."""
        try:
            with sqlite3.connect(db_path) as conn:
                # Analyze database for query optimization
                conn.execute("ANALYZE")
                
                # Vacuum database to reclaim space
                conn.execute("VACUUM")
                
                # Set pragmas for better performance
                conn.execute("PRAGMA journal_mode = WAL")  # Write-Ahead Logging
                conn.execute("PRAGMA synchronous = NORMAL")  # Balanced safety/performance
                conn.execute("PRAGMA cache_size = 1000")  # Increase cache
                conn.execute("PRAGMA temp_store = memory")  # Store temp tables in memory
                
                conn.commit()
                logger.info("Database optimization completed")
                
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
    
    @staticmethod
    def create_database_indexes(db_path: Path):
        """Create database indexes for better query performance."""
        try:
            with sqlite3.connect(db_path) as conn:
                # Create indexes for common query patterns
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_listings_hash 
                    ON listings(hash)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_listings_source 
                    ON listings(source)
                """)
                
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_listings_timestamp 
                    ON listings(timestamp)
                """)
                
                conn.commit()
                logger.info("Database indexes created successfully")
                
        except Exception as e:
            logger.error(f"Database index creation failed: {e}")
    
    @staticmethod
    def get_performance_recommendations(metrics_collector: MetricsCollector) -> List[str]:
        """Get performance optimization recommendations based on metrics."""
        recommendations = []
        
        try:
            # Check recent metrics
            recent_metrics = metrics_collector.get_recent_metrics(hours=24)
            
            if not recent_metrics:
                recommendations.append("No recent metrics available - monitoring may not be working")
                return recommendations
            
            # Analyze CPU usage
            cpu_values = [m['cpu_percent'] for m in recent_metrics if 'cpu_percent' in m]
            if cpu_values:
                avg_cpu = sum(cpu_values) / len(cpu_values)
                if avg_cpu > 80:
                    recommendations.append("High CPU usage detected - consider optimizing scraping frequency")
            
            # Analyze memory usage
            memory_values = [m['memory_percent'] for m in recent_metrics if 'memory_percent' in m]
            if memory_values:
                avg_memory = sum(memory_values) / len(memory_values)
                if avg_memory > 85:
                    recommendations.append("High memory usage detected - consider increasing system memory")
            
            # Analyze scrape performance
            app_summary = metrics_collector.get_application_summary()
            if app_summary.average_scrape_duration > 60:
                recommendations.append("Slow scraping detected - consider optimizing provider selection")
            
            # Check failure rate
            if app_summary.total_scrapes > 0:
                failure_rate = app_summary.failed_scrapes / app_summary.total_scrapes
                if failure_rate > 0.1:
                    recommendations.append(f"High failure rate ({failure_rate:.1%}) - check provider configurations")
            
            if not recommendations:
                recommendations.append("Performance looks good - no specific optimizations needed")
                
        except Exception as e:
            recommendations.append(f"Could not analyze performance metrics: {str(e)}")
        
        return recommendations


# Global instances
_metrics_collector: Optional[MetricsCollector] = None
_health_checker: Optional[HealthChecker] = None


def get_metrics_collector(data_dir: Optional[Path] = None) -> MetricsCollector:
    """Get or create global metrics collector instance."""
    global _metrics_collector
    if _metrics_collector is None:
        if data_dir is None:
            data_dir = Path(__file__).resolve().parents[2] / "data"
        _metrics_collector = MetricsCollector(data_dir)
    return _metrics_collector


def get_health_checker(data_dir: Optional[Path] = None, config_path: Optional[Path] = None) -> HealthChecker:
    """Get or create global health checker instance."""
    global _health_checker
    if _health_checker is None:
        if data_dir is None:
            data_dir = Path(__file__).resolve().parents[2] / "data"
        _health_checker = HealthChecker(data_dir, config_path)
    return _health_checker