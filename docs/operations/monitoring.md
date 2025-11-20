# System Monitoring Guide

## Overview
This guide covers monitoring, alerting, and observability for MAFA production systems. It includes metrics collection, log management, performance monitoring, and incident response procedures.

---

**Last Updated:** November 19, 2025  
**Version:** 1.0.0  
**Maintainer:** MAFA Operations Team  
**Estimated Reading Time:** 20-25 minutes

---

## Monitoring Architecture

### Monitoring Stack Overview
```
┌─────────────────────────────────────────────────────────────┐
│                     Monitoring Dashboard                    │
│                     (Grafana/Prometheus)                   │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
┌───────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
│   Metrics    │  │    Logs     │  │   Alerts    │
│ (Prometheus) │  │(ELK/Fluentd)│  │ (AlertManager)│
└──────┬───────┘  └──────┬──────┘  └──────┬──────┘
       │                 │                 │
       └─────────────────┼─────────────────┘
                         │
        ┌────────────────┼─────────────────┐
        │                │                 │
┌───────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
│   MAFA API   │  │  Database   │  │  Infrastructure│
│   Server     │  │  Server     │  │  (VM/Container)│
└──────────────┘  └─────────────┘  └─────────────┘
```

### Key Monitoring Components
- **Metrics Collection**: Prometheus for time-series data
- **Visualization**: Grafana dashboards for real-time monitoring
- **Log Aggregation**: ELK Stack (Elasticsearch, Logstash, Kibana)
- **Alerting**: Prometheus AlertManager with multiple notification channels
- **APM**: Application Performance Monitoring for deep insights
- **Infrastructure**: System-level monitoring (CPU, memory, disk, network)

---

## Metrics Collection

### Application Metrics

#### Core Business Metrics
```python
# mafa/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, generate_latest
import time
import logging

# Business metrics
contacts_discovered = Counter(
    'mafa_contacts_discovered_total',
    'Total contacts discovered',
    ['source', 'confidence_level']
)

searches_completed = Counter(
    'mafa_searches_completed_total',
    'Total searches completed',
    ['provider', 'status']
)

listings_processed = Counter(
    'mafa_listings_processed_total',
    'Total listings processed',
    ['provider']
)

# Performance metrics
search_duration = Histogram(
    'mafa_search_duration_seconds',
    'Time spent searching',
    ['provider']
)

contact_extraction_duration = Histogram(
    'mafa_contact_extraction_duration_seconds',
    'Time spent extracting contacts'
)

# System metrics
active_connections = Gauge(
    'mafa_active_connections',
    'Number of active connections'
)

database_connections = Gauge(
    'mafa_database_connections',
    'Number of database connections'
)

# Custom metrics for apartment search
contacts_quality_score = Histogram(
    'mafa_contacts_quality_score',
    'Quality score distribution of discovered contacts',
    buckets=[0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
)

search_coverage_percentage = Gauge(
    'mafa_search_coverage_percentage',
    'Percentage of relevant listings found'
)
```

#### Scraping Performance Metrics
```python
# mafa/scrapers/metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Scraper-specific metrics
scrapes_attempted = Counter(
    'mafa_scrapes_attempted_total',
    'Total scraping attempts',
    ['provider', 'status']  # status: success, failure, timeout
)

scrapes_duration = Histogram(
    'mafa_scrapes_duration_seconds',
    'Time spent on each scrape',
    ['provider']
)

rate_limit_hits = Counter(
    'mafa_rate_limit_hits_total',
    'Number of rate limit violations',
    ['provider']
)

listings_found_per_scrape = Histogram(
    'mafa_listings_found_per_scrape',
    'Number of listings found per scrape',
    ['provider']
)

scraper_health_status = Gauge(
    'mafa_scraper_health_status',
    'Health status of scrapers',
    ['provider']  # 1 = healthy, 0 = unhealthy
)
```

### Infrastructure Metrics

#### System-Level Monitoring
```python
# scripts/system_metrics.py
import psutil
import time
from prometheus_client import start_http_server, Gauge

# CPU metrics
cpu_usage = Gauge('system_cpu_usage_percent', 'CPU usage percentage')
cpu_temperature = Gauge('system_cpu_temperature_celsius', 'CPU temperature in Celsius')

# Memory metrics
memory_usage = Gauge('system_memory_usage_percent', 'Memory usage percentage')
swap_usage = Gauge('system_swap_usage_percent', 'Swap usage percentage')

# Disk metrics
disk_usage = Gauge('system_disk_usage_percent', 'Disk usage percentage', ['mount_point'])
disk_io_read = Gauge('system_disk_io_read_bytes_total', 'Total bytes read from disk')
disk_io_write = Gauge('system_disk_io_write_bytes_total', 'Total bytes written to disk')

# Network metrics
network_bytes_sent = Gauge('system_network_bytes_sent_total', 'Total bytes sent')
network_bytes_recv = Gauge('system_network_bytes_recv_total', 'Total bytes received')
network_errors = Gauge('system_network_errors_total', 'Total network errors')

# Container metrics
container_cpu_usage = Gauge('container_cpu_usage_percent', 'Container CPU usage', ['container_name'])
container_memory_usage = Gauge('container_memory_usage_percent', 'Container memory usage', ['container_name'])

def collect_system_metrics():
    """Collect system-level metrics."""
    # CPU
    cpu_usage.set(psutil.cpu_percent())
    cpu_temp = psutil.sensors_temperatures()
    if cpu_temp:
        temp = cpu_temp.get('coretemp', [{}])[0].get('current', 0)
        cpu_temperature.set(temp)
    
    # Memory
    memory = psutil.virtual_memory()
    memory_usage.set(memory.percent)
    swap = psutil.swap_memory()
    swap_usage.set(swap.percent)
    
    # Disk
    for partition in psutil.disk_partitions():
        try:
            usage = psutil.disk_usage(partition.mountpoint)
            disk_usage.labels(mount_point=partition.mountpoint).set(
                (usage.used / usage.total) * 100
            )
        except PermissionError:
            continue
    
    # Disk I/O
    disk_io = psutil.disk_io_counters()
    if disk_io:
        disk_io_read.set(disk_io.read_bytes)
        disk_io_write.set(disk_io.write_bytes)
    
    # Network
    network_io = psutil.net_io_counters()
    if network_io:
        network_bytes_sent.set(network_io.bytes_sent)
        network_bytes_recv.set(network_io.bytes_recv)

if __name__ == "__main__":
    # Start Prometheus metrics server
    start_http_server(8001)
    
    # Collect metrics every 15 seconds
    while True:
        collect_system_metrics()
        time.sleep(15)
```

### Database Monitoring

#### PostgreSQL Metrics
```sql
-- Database monitoring queries

-- Active connections
SELECT count(*) as active_connections FROM pg_stat_activity WHERE state = 'active';

-- Slow queries
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements
WHERE mean_time > 1000  -- Queries taking more than 1 second
ORDER BY total_time DESC
LIMIT 10;

-- Table sizes
SELECT schemaname, tablename, 
       pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;

-- Index usage
SELECT schemaname, tablename, indexname, idx_scan, idx_tup_read, idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;

-- Database size over time
SELECT date_trunc('hour', query_start) as hour,
       sum(calls) as total_queries,
       sum(total_time) as total_time_ms
FROM pg_stat_statements
GROUP BY hour
ORDER BY hour DESC;
```

#### Database Monitoring Script
```bash
#!/bin/bash
# scripts/db_monitoring.sh

DATABASE_URL=$1
METRICS_FILE="/var/lib/prometheus/node-exporter/textfile_collector/db_metrics.prom"

# Function to write Prometheus metrics
write_metric() {
    local name=$1
    local value=$2
    local labels=$3
    echo "${name}${labels} ${value}" >> $METRICS_FILE
}

# Clear previous metrics
> $METRICS_FILE

# Connection metrics
active_connections=$(psql $DATABASE_URL -t -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';")
write_metric "mafa_db_active_connections" "$active_connections" ""

idle_connections=$(psql $DATABASE_URL -t -c "SELECT count(*) FROM pg_stat_activity WHERE state = 'idle';")
write_metric "mafa_db_idle_connections" "$idle_connections" ""

# Database size
db_size=$(psql $DATABASE_URL -t -c "SELECT pg_database_size(current_database());")
write_metric "mafa_db_size_bytes" "$db_size" ""

# Table statistics
psql $DATABASE_URL -c "
SELECT schemaname, tablename,
       n_tup_ins as inserts,
       n_tup_upd as updates,
       n_tup_del as deletes,
       n_live_tup as live_tuples,
       n_dead_tup as dead_tuples
FROM pg_stat_user_tables 
WHERE schemaname = 'public';" | while read schema table inserts updates deletes live dead; do
    write_metric "mafa_db_table_inserts" "$inserts" "table=\"$table\""
    write_metric "mafa_db_table_updates" "$updates" "table=\"$table\""
    write_metric "mafa_db_table_deletes" "$deletes" "table=\"$table\""
    write_metric "mafa_db_table_live_tuples" "$live" "table=\"$table\""
    write_metric "mafa_db_table_dead_tuples" "$dead" "table=\"$table\""
done
```

---

## Grafana Dashboards

### Main MAFA Dashboard
```json
{
  "dashboard": {
    "id": null,
    "title": "MAFA Production Dashboard",
    "tags": ["mafa", "production", "apartment-search"],
    "timezone": "UTC",
    "refresh": "30s",
    "time": {
      "from": "now-1h",
      "to": "now"
    },
    "panels": [
      {
        "id": 1,
        "title": "System Overview",
        "type": "stat",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0},
        "targets": [
          {
            "expr": "up{job=\"mafa\"}",
            "legendFormat": "API Server Status"
          },
          {
            "expr": "mafa_active_connections",
            "legendFormat": "Active Connections"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {"mode": "thresholds"},
            "thresholds": {
              "steps": [
                {"color": "red", "value": null},
                {"color": "green", "value": 1}
              ]
            }
          }
        }
      },
      {
        "id": 2,
        "title": "Contacts Discovery Rate",
        "type": "graph",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0},
        "targets": [
          {
            "expr": "rate(mafa_contacts_discovered_total[5m])",
            "legendFormat": "{{source}} - {{confidence_level}}"
          }
        ]
      },
      {
        "id": 3,
        "title": "Search Performance",
        "type": "graph",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8},
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(mafa_search_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          },
          {
            "expr": "histogram_quantile(0.50, rate(mafa_search_duration_seconds_bucket[5m]))",
            "legendFormat": "50th percentile"
          }
        ]
      },
      {
        "id": 4,
        "title": "Contact Quality Distribution",
        "type": "graph",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8},
        "targets": [
          {
            "expr": "rate(mafa_contacts_quality_score_bucket[5m])",
            "legendFormat": "{{le}}"
          }
        ]
      },
      {
        "id": 5,
        "title": "Database Connections",
        "type": "graph",
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 16},
        "targets": [
          {
            "expr": "mafa_db_active_connections",
            "legendFormat": "Active"
          },
          {
            "expr": "mafa_db_idle_connections",
            "legendFormat": "Idle"
          }
        ]
      },
      {
        "id": 6,
        "title": "Scraper Health",
        "type": "stat",
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 16},
        "targets": [
          {
            "expr": "mafa_scraper_health_status",
            "legendFormat": "{{provider}}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "color": {"mode": "thresholds"},
            "thresholds": {
              "steps": [
                {"color": "red", "value": null},
                {"color": "red", "value": 0},
                {"color": "green", "value": 1}
              ]
            }
          }
        }
      }
    ]
  }
}
```

### Infrastructure Dashboard
```json
{
  "dashboard": {
    "title": "MAFA Infrastructure Dashboard",
    "panels": [
      {
        "title": "CPU Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "system_cpu_usage_percent",
            "legendFormat": "CPU Usage"
          }
        ]
      },
      {
        "title": "Memory Usage",
        "type": "graph", 
        "targets": [
          {
            "expr": "system_memory_usage_percent",
            "legendFormat": "Memory Usage"
          }
        ]
      },
      {
        "title": "Disk Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "system_disk_usage_percent",
            "legendFormat": "{{mount_point}}"
          }
        ]
      },
      {
        "title": "Network I/O",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(system_network_bytes_sent_total[5m])",
            "legendFormat": "Bytes Sent"
          },
          {
            "expr": "rate(system_network_bytes_recv_total[5m])",
            "legendFormat": "Bytes Received"
          }
        ]
      }
    ]
  }
}
```

---

## Log Management

### Log Configuration
```python
# mafa/logging_config.py
import logging
import logging.config
import json
from pythonjsonlogger import jsonlogger

LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(name)s %(levelname)s %(message)s %(filename)s %(lineno)d'
        },
        'detailed': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'json',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'DEBUG',
            'formatter': 'detailed',
            'filename': '/var/log/mafa/app.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        },
        'error_file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'ERROR',
            'formatter': 'json',
            'filename': '/var/log/mafa/error.log',
            'maxBytes': 10485760,
            'backupCount': 10
        }
    },
    'loggers': {
        '': {  # root logger
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False
        },
        'mafa': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'mafa.scrapers': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'mafa.contacts': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False
        }
    }
}
```

### Structured Logging Examples
```python
# mafa/services/search_service.py
import structlog

logger = structlog.get_logger(__name__)

class SearchService:
    def __init__(self):
        self.logger = logger.bind(service="search")
    
    async def execute_search(self, provider: str, criteria: dict) -> dict:
        """Execute apartment search with structured logging."""
        # Log search start
        self.logger.info(
            "search_started",
            provider=provider,
            criteria=criteria,
            search_id=uuid.uuid4().hex[:8]
        )
        
        try:
            # Perform search
            start_time = time.time()
            results = await self._perform_search(provider, criteria)
            duration = time.time() - start_time
            
            # Log successful search
            self.logger.info(
                "search_completed",
                provider=provider,
                listings_found=len(results),
                duration_seconds=duration,
                search_id=self.search_id
            )
            
            # Log contact extraction
            contacts_extracted = await self._extract_contacts(results)
            self.logger.info(
                "contacts_extracted",
                provider=provider,
                contacts_count=len(contacts_extracted),
                extraction_duration=time.time() - start_time
            )
            
            return results
            
        except Exception as e:
            # Log error with context
            self.logger.error(
                "search_failed",
                provider=provider,
                error=str(e),
                error_type=type(e).__name__,
                duration_seconds=time.time() - start_time,
                exc_info=True
            )
            raise
```

### Log Aggregation Setup

#### Fluentd Configuration
```xml
# logging/fluentd.conf
<source>
  @type tail
  path /var/log/mafa/app.log
  pos_file /var/log/fluentd-mafa-app.log.pos
  tag mafa.app
  format json
</source>

<source>
  @type tail
  path /var/log/mafa/error.log
  pos_file /var/log/fluentd-mafa-error.log.pos
  tag mafa.error
  format json
</source>

<source>
  @type tail
  path /var/log/nginx/access.log
  pos_file /var/log/fluentd-nginx-access.log.pos
  tag nginx.access
  format /^(?<remote_addr>[\d\.]+) - (?<user>.*?) \[(?<time>.*?)\] "(?<method>\S+) (?<path>\S+) (?<protocol>\S+)" (?<status>\d+) (?<size>\d+) "(?<referrer>[^"]*)" "(?<agent>[^"]*)"/
</source>

<filter mafa.**>
  @type record_transformer
  <record>
    hostname "#{Socket.gethostname}"
    environment production
    service_name mafa
  </record>
</filter>

<match mafa.**>
  @type elasticsearch
  host elasticsearch
  port 9200
  index_name mafa-logs
  type_name _doc
  include_tag_key true
  tag_key @log_name
</match>

<match nginx.access>
  @type elasticsearch
  host elasticsearch
  port 9200
  index_name nginx-logs
  type_name _doc
</match>
```

---

## Alerting Configuration

### Prometheus Alert Rules
```yaml
# monitoring/alert_rules.yml
groups:
  - name: mafa.rules
    rules:
      # High-level application alerts
      - alert: MAFAAPIDown
        expr: up{job="mafa"} == 0
        for: 1m
        labels:
          severity: critical
          service: mafa
        annotations:
          summary: "MAFA API is down"
          description: "MAFA API has been down for more than 1 minute"

      - alert: HighErrorRate
        expr: rate(mafa_http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
          service: mafa
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value }} errors per second"

      - alert: HighResponseTime
        expr: histogram_quantile(0.95, rate(mafa_http_request_duration_seconds_bucket[5m])) > 2
        for: 10m
        labels:
          severity: warning
          service: mafa
        annotations:
          summary: "High response time"
          description: "95th percentile response time is {{ $value }} seconds"

      # Contact discovery alerts
      - alert: LowContactDiscovery
        expr: rate(mafa_contacts_discovered_total[1h]) < 1
        for: 30m
        labels:
          severity: warning
          service: mafa
        annotations:
          summary: "Low contact discovery rate"
          description: "Contact discovery rate is {{ $value }} contacts per hour"

      - alert: NoContactsDiscovered
        expr: rate(mafa_contacts_discovered_total[2h]) == 0
        for: 15m
        labels:
          severity: critical
          service: mafa
        annotations:
          summary: "No contacts discovered"
          description: "No contacts have been discovered in the last 2 hours"

      # Scraper-specific alerts
      - alert: ScraperUnhealthy
        expr: mafa_scraper_health_status == 0
        for: 5m
        labels:
          severity: warning
          service: mafa
        annotations:
          summary: "Scraper {{ $labels.provider }} is unhealthy"
          description: "Scraper {{ $labels.provider }} has been unhealthy for 5 minutes"

      - alert: HighScrapingFailureRate
        expr: rate(mafa_scrapes_attempted_total{status="failure"}[10m]) > 0.5
        for: 10m
        labels:
          severity: warning
          service: mafa
        annotations:
          summary: "High scraping failure rate"
          description: "Scraper {{ $labels.provider }} has {{ $value }} failures per second"

      # Database alerts
      - alert: DatabaseConnectionsHigh
        expr: mafa_db_active_connections > 80
        for: 5m
        labels:
          severity: warning
          service: database
        annotations:
          summary: "High database connections"
          description: "Database has {{ $value }} active connections"

      - alert: DatabaseDown
        expr: up{job="postgres"} == 0
        for: 1m
        labels:
          severity: critical
          service: database
        annotations:
          summary: "Database is down"
          description: "PostgreSQL database has been down for 1 minute"

      # Infrastructure alerts
      - alert: HighCPUUsage
        expr: system_cpu_usage_percent > 80
        for: 10m
        labels:
          severity: warning
          service: infrastructure
        annotations:
          summary: "High CPU usage"
          description: "CPU usage is {{ $value }}% on {{ $labels.instance }}"

      - alert: HighMemoryUsage
        expr: system_memory_usage_percent > 85
        for: 5m
        labels:
          severity: warning
          service: infrastructure
        annotations:
          summary: "High memory usage"
          description: "Memory usage is {{ $value }}% on {{ $labels.instance }}"

      - alert: DiskSpaceLow
        expr: system_disk_usage_percent > 85
        for: 5m
        labels:
          severity: warning
          service: infrastructure
        annotations:
          summary: "Low disk space"
          description: "Disk usage is {{ $value }}% on {{ $labels.instance }}"
```

### Alert Manager Configuration
```yaml
# monitoring/alertmanager.yml
global:
  smtp_smarthost: 'smtp.gmail.com:587'
  smtp_from: 'alerts@mafa.app'
  smtp_auth_username: 'alerts@mafa.app'
  smtp_auth_password: 'your-smtp-password'

route:
  group_by: ['alertname', 'service']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'
    - match:
        service: mafa
      receiver: 'mafa-team'
    - match:
        service: infrastructure
      receiver: 'infrastructure-team'

receivers:
  - name: 'default'
    email_configs:
      - to: 'ops@mafa.app'
        subject: '[MAFA] {{ .GroupLabels.alertname }}'

  - name: 'critical-alerts'
    email_configs:
      - to: 'oncall@mafa.app'
        subject: '[CRITICAL] {{ .GroupLabels.alertname }}'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
        channel: '#critical-alerts'
        text: 'Critical alert: {{ .GroupLabels.alertname }}'

  - name: 'mafa-team'
    email_configs:
      - to: 'mafa-team@mafa.app'
        subject: '[MAFA] {{ .GroupLabels.alertname }}'
    slack_configs:
      - api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'
        channel: '#mafa-dev'
        text: 'MAFA alert: {{ .GroupLabels.alertname }}'

  - name: 'infrastructure-team'
    email_configs:
      - to: 'infrastructure@mafa.app'
        subject: '[INFRA] {{ .GroupLabels.alertname }}'

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'instance']
```

---

## Application Performance Monitoring (APM)

### OpenTelemetry Configuration
```python
# mafa/apm/config.py
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.sqlalchemy import SqlalchemyInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

def setup_apm():
    """Setup OpenTelemetry APM."""
    # Create tracer provider
    trace.set_tracer_provider(TracerProvider())
    tracer = trace.get_tracer(__name__)
    
    # Configure Jaeger exporter
    jaeger_exporter = JaegerExporter(
        agent_host_name="jaeger",
        agent_port=6831,
    )
    
    # Add span processor
    span_processor = BatchSpanProcessor(jaeger_exporter)
    trace.get_tracer_provider().add_span_processor(span_processor)
    
    # Auto-instrument FastAPI
    FastAPIInstrumentor.instrument_app(app)
    
    # Instrument database
    SqlalchemyInstrumentor().instrument()
    
    # Instrument HTTP requests
    RequestsInstrumentor().instrument()
    
    return tracer

# Usage in FastAPI app
from fastapi import FastAPI
from mafa.apm.config import setup_apm

app = FastAPI()
tracer = setup_apm()

@app.get("/api/contacts/")
async def get_contacts():
    with tracer.start_as_current_span("get_contacts") as span:
        span.set_attribute("http.method", "GET")
        span.set_attribute("http.route", "/api/contacts/")
        
        # Your business logic here
        contacts = await contact_service.get_contacts()
        
        span.set_attribute("contacts.count", len(contacts))
        return contacts
```

### Custom Metrics with APM
```python
# mafa/services/monitoring_service.py
import time
from opentelemetry import metrics
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import ConsoleMetricExporter

class MonitoringService:
    def __init__(self):
        # Setup metrics
        metrics.set_meter_provider(MeterProvider())
        self.meter = metrics.get_meter(__name__)
        
        # Create custom metrics
        self.search_counter = self.meter.create_counter(
            "mafa_searches_total",
            description="Total number of searches performed"
        )
        
        self.contact_counter = self.meter.create_counter(
            "mafa_contacts_found_total", 
            description="Total number of contacts found"
        )
        
        self.search_duration = self.meter.create_histogram(
            "mafa_search_duration_ms",
            description="Time spent on searches in milliseconds"
        )
        
        self.active_searches = self.meter.create_up_down_counter(
            "mafa_active_searches",
            description="Number of currently active searches"
        )
    
    def record_search_start(self, provider: str):
        """Record search start."""
        self.active_searches.add(1, {"provider": provider})
        return time.time()
    
    def record_search_end(self, start_time: float, provider: str, status: str, contacts_found: int = 0):
        """Record search completion."""
        duration_ms = (time.time() - start_time) * 1000
        
        self.search_counter.add(1, {"provider": provider, "status": status})
        self.search_duration.record(duration_ms, {"provider": provider})
        self.active_searches.add(-1, {"provider": provider})
        
        if status == "success" and contacts_found > 0:
            self.contact_counter.add(contacts_found, {"provider": provider})
```

---

## Log Analysis and Visualization

### Kibana Dashboard Configuration
```json
{
  "version": "7.10.0",
  "objects": [
    {
      "attributes": {
        "title": "MAFA Logs Dashboard",
        "type": "dashboard",
        "panelsJSON": "[{\"gridData\":{\"x\":0,\"y\":0,\"w\":48,\"h\":15,\"i\":\"1\"},\"panelIndex\":\"1\",\"embeddableConfig\":{\"vis\":{\"legendOpen\":false},\"mapCenter\":{\"lat\":0,\"lon\":0}},\"panelRefName\":\"panel_1\",\"version\":\"7.10.0\"}]"
      },
      "references": []
    },
    {
      "attributes": {
        "title": "MAFA Errors",
        "type": "visualization",
        "visState": {
          "type": "histogram",
          "params": {
            "grid": {"categoryLines": false, "style": {"color": "#eee"}},
            "categoryAxes": [
              {
                "id": "CategoryAxis-1",
                "type": "category",
                "position": "bottom",
                "show": true,
                "style": {},
                "scale": {"type": "linear"},
                "labels": {"show": true, "truncate": 100},
                "title": {}
              }
            ],
            "valueAxes": [
              {
                "id": "ValueAxis-1",
                "name": "LeftAxis-1",
                "type": "value",
                "position": "left",
                "show": true,
                "style": {},
                "scale": {"type": "linear", "mode": "normal"},
                "labels": {"show": true, "rotate": 0, "filter": false, "truncate": 100},
                "title": {"text": "Count"}
              }
            ]
          }
        },
        "aggs": [
          {"id": "1", "enabled": true, "type": "count", "schema": "metric", "params": {}},
          {
            "id": "2",
            "enabled": true,
            "type": "date_histogram",
            "schema": "segment",
            "params": {
              "field": "@timestamp",
              "interval": "auto",
              "min_doc_count": 1
            }
          },
          {
            "id": "3",
            "enabled": true,
            "type": "filters",
            "schema": "split",
            "params": {
              "filters": [
                {"input": {"query": "level:error", "label": "Errors"}},
                {"input": {"query": "level:warning", "label": "Warnings"}}
              ]
            }
          }
        ]
      }
    }
  ]
}
```

### Log Queries for Analysis
```python
# scripts/log_analysis.py
#!/usr/bin/env python3
"""
Log analysis scripts for MAFA production monitoring.
"""

import requests
import json
from datetime import datetime, timedelta

class ElasticsearchAnalyzer:
    def __init__(self, es_host="elasticsearch", port=9200):
        self.base_url = f"http://{es_host}:{port}"
        self.headers = {"Content-Type": "application/json"}
    
    def search_logs(self, index="mafa-logs", query=None, size=1000):
        """Search logs in Elasticsearch."""
        if query is None:
            query = {"match_all": {}}
        
        search_url = f"{self.base_url}/{index}/_search"
        payload = {
            "query": query,
            "size": size,
            "sort": [{"@timestamp": {"order": "desc"}}]
        }
        
        response = requests.post(search_url, json=payload, headers=self.headers)
        return response.json()
    
    def get_error_summary(self, hours=24):
        """Get error summary for the last N hours."""
        now = datetime.now()
        start_time = now - timedelta(hours=hours)
        
        query = {
            "bool": {
                "must": [
                    {"range": {"@timestamp": {"gte": start_time.isoformat()}}},
                    {"term": {"level": "error"}}
                ]
            }
        }
        
        results = self.search_logs(query=query)
        
        # Analyze errors by service and error type
        error_summary = {}
        for hit in results["hits"]["hits"]:
            source = hit["_source"]
            service = source.get("service", "unknown")
            error_type = source.get("error_type", "unknown")
            
            key = f"{service}:{error_type}"
            if key not in error_summary:
                error_summary[key] = {
                    "count": 0,
                    "examples": []
                }
            
            error_summary[key]["count"] += 1
            if len(error_summary[key]["examples"]) < 3:
                error_summary[key]["examples"].append({
                    "timestamp": source.get("@timestamp"),
                    "message": source.get("message", "")[:200]
                })
        
        return error_summary
    
    def get_performance_logs(self, provider=None, hours=1):
        """Get performance-related logs."""
        now = datetime.now()
        start_time = now - timedelta(hours=hours)
        
        query = {
            "bool": {
                "must": [
                    {"range": {"@timestamp": {"gte": start_time.isoformat()}}},
                    {"bool": {"should": [
                        {"term": {"event": "search_completed"}},
                        {"term": {"event": "search_failed"}},
                        {"range": {"duration_seconds": {"gte": 5}}}
                    ]}}
                ]
            }
        }
        
        if provider:
            query["bool"]["must"].append({"term": {"provider": provider}})
        
        return self.search_logs(query=query)
    
    def get_scraper_health_summary(self, hours=24):
        """Get scraper health summary."""
        now = datetime.now()
        start_time = now - timedelta(hours=hours)
        
        query = {
            "bool": {
                "must": [
                    {"range": {"@timestamp": {"gte": start_time.isoformat()}}},
                    {"term": {"service": "mafa.scrapers"}}
                ]
            }
        }
        
        results = self.search_logs(query=query)
        
        # Analyze scraper performance
        scraper_stats = {}
        for hit in results["hits"]["hits"]:
            source = hit["_source"]
            provider = source.get("provider", "unknown")
            event = source.get("event", "unknown")
            
            if provider not in scraper_stats:
                scraper_stats[provider] = {
                    "total_searches": 0,
                    "successful_searches": 0,
                    "failed_searches": 0,
                    "total_listings": 0,
                    "total_contacts": 0,
                    "average_duration": 0,
                    "durations": []
                }
            
            stats = scraper_stats[provider]
            stats["total_searches"] += 1
            
            if event == "search_completed":
                stats["successful_searches"] += 1
                stats["total_listings"] += source.get("listings_found", 0)
                stats["total_contacts"] += source.get("contacts_found", 0)
                
                duration = source.get("duration_seconds", 0)
                stats["durations"].append(duration)
            elif event == "search_failed":
                stats["failed_searches"] += 1
        
        # Calculate averages
        for provider, stats in scraper_stats.items():
            if stats["durations"]:
                stats["average_duration"] = sum(stats["durations"]) / len(stats["durations"])
        
        return scraper_stats

def main():
    analyzer = ElasticsearchAnalyzer()
    
    print("=== Error Summary (Last 24 Hours) ===")
    error_summary = analyzer.get_error_summary()
    for key, data in error_summary.items():
        print(f"{key}: {data['count']} errors")
        for example in data["examples"]:
            print(f"  - {example['timestamp']}: {example['message']}")
    
    print("\n=== Scraper Health (Last 24 Hours) ===")
    scraper_stats = analyzer.get_scraper_health_summary()
    for provider, stats in scraper_stats.items():
        success_rate = (stats["successful_searches"] / stats["total_searches"] * 100) if stats["total_searches"] > 0 else 0
        print(f"{provider}:")
        print(f"  Success rate: {success_rate:.1f}%")
        print(f"  Average duration: {stats['average_duration']:.2f}s")
        print(f"  Total contacts found: {stats['total_contacts']}")

if __name__ == "__main__":
    main()
```

---

## Performance Monitoring

### Response Time Monitoring
```python
# mafa/middleware/performance.py
import time
import asyncio
from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import Histogram, Counter

# Performance metrics
request_duration = Histogram(
    'mafa_http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'status_code']
)

requests_total = Counter(
    'mafa_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code']
)

class PerformanceMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Process request
        response = await call_next(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Extract labels
        method = request.method
        endpoint = request.url.path
        status_code = str(response.status_code)
        
        # Record metrics
        request_duration.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code
        ).observe(duration)
        
        requests_total.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code
        ).inc()
        
        return response

app = FastAPI()
app.add_middleware(PerformanceMiddleware)
```

### Database Performance Monitoring
```python
# mafa/db/performance.py
import time
import logging
from sqlalchemy import event
from sqlalchemy.engine import Engine
from prometheus_client import Counter, Histogram

# Database metrics
db_query_duration = Histogram(
    'mafa_db_query_duration_seconds',
    'Database query duration',
    ['operation', 'table']
)

db_query_errors = Counter(
    'mafa_db_query_errors_total',
    'Total database query errors',
    ['operation', 'table']
)

@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()

@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    duration = time.time() - context._query_start_time
    
    # Extract table name from statement
    table = "unknown"
    if "FROM" in statement.upper():
        table = statement.split("FROM")[1].split(" ")[1].strip().lower()
    elif "UPDATE" in statement.upper():
        table = statement.split("UPDATE")[1].split(" ")[1].strip().lower()
    elif "INSERT INTO" in statement.upper():
        table = statement.split("INSERT INTO")[1].split(" ")[1].strip().lower()
    elif "DELETE FROM" in statement.upper():
        table = statement.split("DELETE FROM")[1].split(" ")[1].strip().lower()
    
    # Determine operation type
    operation = statement.split(" ")[0].upper()
    
    db_query_duration.labels(operation=operation, table=table).observe(duration)

@event.listens_for(Engine, "handle_error")
def receive_handle_error(exception, connection, cursor, statement, parameters, context):
    duration = time.time() - context._query_start_time
    
    # Extract table name
    table = "unknown"
    if statement:
        if "FROM" in statement.upper():
            table = statement.split("FROM")[1].split(" ")[1].strip().lower()
        elif "UPDATE" in statement.upper():
            table = statement.split("UPDATE")[1].split(" ")[1].strip().lower()
    
    operation = statement.split(" ")[0].upper() if statement else "UNKNOWN"
    db_query_errors.labels(operation=operation, table=table).inc()
```

---

## Incident Response

### Incident Response Playbook
```markdown
# MAFA Incident Response Playbook

## Severity Levels

### SEV-1 (Critical)
- Complete system outage
- Data loss or security breach
- Affects all users
- Response time: 15 minutes

### SEV-2 (High)
- Major functionality impaired
- Affects significant portion of users
- Response time: 1 hour

### SEV-3 (Medium)
- Minor functionality issues
- Affects small portion of users
- Response time: 4 hours

### SEV-4 (Low)
- Informational or cosmetic issues
- Response time: 1 business day

## Response Procedures

### Initial Response (0-15 minutes)
1. **Acknowledge Alert**
   - Confirm receipt of alert
   - Assign incident commander
   - Create incident channel (Slack/Teams)

2. **Assess Impact**
   - Determine severity level
   - Identify affected services
   - Estimate user impact

3. **Notify Stakeholders**
   - Update status page
   - Notify on-call engineer
   - Alert management if SEV-1/2

### Investigation (15-60 minutes)
1. **Gather Information**
   - Review monitoring dashboards
   - Check recent deployments
   - Examine log files

2. **Identify Root Cause**
   - Use structured troubleshooting
   - Test hypotheses systematically
   - Document findings

3. **Implement Temporary Fix**
   - Apply workaround if available
   - Restore service functionality
   - Monitor for stability

### Resolution (1-4 hours)
1. **Implement Permanent Fix**
   - Deploy corrected code/configuration
   - Test fix in staging environment
   - Deploy to production

2. **Verify Resolution**
   - Confirm all symptoms resolved
   - Monitor for regression
   - Update incident status

3. **Post-Incident Activities**
   - Document root cause
   - Create action items
   - Schedule post-mortem
   - Update runbooks

## Communication Templates

### Initial Alert
```
[MAFA] SEV-2 Incident: High API Response Times
Status: Investigating
Impact: Users experiencing slow API responses
Started: 2025-11-19 21:00 UTC
Incident Commander: @john.doe
Next Update: 21:15 UTC
```

### Resolution Update
```
[MAFA] SEV-2 Incident: High API Response Times - RESOLVED
Status: Resolved
Resolution: Database connection pool increased from 10 to 20
Impact Duration: 45 minutes
Incident Commander: @john.doe
Post-mortem: Scheduled for 2025-11-20 10:00 UTC
```

## Automated Response Scripts
```bash
#!/bin/bash
# scripts/incident_response.sh

SEVERITY=$1
INCIDENT_TYPE=$2

case $SEVERITY in
  "SEV-1"|"SEV-2")
    # Create incident channel
    /usr/local/bin/create-incident-channel.sh "$INCIDENT_TYPE"
    
    # Notify on-call
    /usr/local/bin/notify-oncall.sh "$SEVERITY" "$INCIDENT_TYPE"
    
    # Update status page
    /usr/local/bin/update-status-page.sh "investigating" "$INCIDENT_TYPE"
    
    # Start log collection
    /usr/local/bin/collect-logs.sh &
    
    # Enable debug logging
    /usr/local/bin/enable-debug-logging.sh
    ;;
    
  "SEV-3"|"SEV-4")
    # Log incident for tracking
    echo "$(date): $SEVERITY - $INCIDENT_TYPE" >> /var/log/incidents.log
    ;;
esac
```

---

## Monitoring Best Practices

### Metric Naming Conventions
- Use consistent prefixes: `mafa_` for MAFA-specific metrics
- Use clear, descriptive names: `mafa_contacts_discovered_total` not `contacts`
- Include units in names: `_duration_seconds`, `_bytes_total`
- Use appropriate metric types: Counter for totals, Gauge for current values

### Alert Design
- Make alerts actionable: "High error rate" is better than "Errors detected"
- Set appropriate thresholds based on historical data
- Include context in alert messages: service name, severity, recommended actions
- Test alert rules regularly to avoid alert fatigue

### Dashboard Design
- Start with business metrics, then technical details
- Use consistent color schemes and layouts
- Include relevant time ranges for each metric
- Add annotations for deployments and incidents

### Log Management
- Structure logs for easy parsing and searching
- Include correlation IDs for tracing requests
- Set appropriate log levels for different environments
- Regular log rotation and archival

---

## Related Documentation

- [Deployment Guide](deployment.md) - Production deployment procedures
- [Backup and Restore](backup-restore.md) - Data backup and recovery
- [Security Guide](security.md) - Security monitoring and compliance
- [Configuration Reference](../getting-started/configuration.md) - Configuration options

---

**Monitoring Support**: For monitoring-related issues or enhancements, contact the operations team or create an issue with the `monitoring` label.