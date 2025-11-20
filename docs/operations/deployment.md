# Production Deployment Guide

## Overview
This guide covers deploying MAFA to production environments, including infrastructure requirements, deployment strategies, security considerations, and ongoing maintenance procedures.

---

**Last Updated:** November 19, 2025  
**Version:** 1.0.0  
**Maintainer:** MAFA Operations Team  
**Estimated Reading Time:** 20-30 minutes

---

## Deployment Architecture

### Production Architecture Overview
```
                    ┌─────────────────┐
                    │    Load Balancer │
                    │    (Nginx/ALB)   │
                    └─────────┬───────┘
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
    ┌───────▼──────┐  ┌───────▼──────┐  ┌──────▼──────┐
    │  Web Server  │  │ Web Server   │  │ Web Server  │
    │   (Nginx)    │  │   (Nginx)    │  │   (Nginx)   │
    └──────┬───────┘  └──────┬───────┘  └─────┬──────┘
           │                 │                 │
           └─────────────────┼─────────────────┘
                             │
            ┌────────────────┼─────────────────┐
            │                │                 │
    ┌───────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
    │   API Server │  │  API Server │  │  API Server │
    │    (MAFA)    │  │    (MAFA)   │  │   (MAFA)    │
    └──────┬───────┘  └──────┬───────┘  └─────┬──────┘
           │                 │                 │
           └─────────────────┼─────────────────┘
                             │
            ┌────────────────┼─────────────────┐
            │                │                 │
    ┌───────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
    │   Database   │  │    Redis    │  │ File Storage│
    │ (PostgreSQL) │  │   Cache     │  │   (S3/CDN)  │
    └──────────────┘  └─────────────┘  └─────────────┘
```

### Infrastructure Requirements

#### Minimum Production Requirements
```
Web Tier:
- CPU: 2 cores per server
- RAM: 4GB per server
- Storage: 50GB SSD
- Network: 1Gbps

Application Tier:
- CPU: 4 cores per server
- RAM: 8GB per server
- Storage: 100GB SSD
- Network: 1Gbps

Database Tier:
- CPU: 4 cores
- RAM: 16GB
- Storage: 500GB SSD
- Network: 1Gbps

Cache Tier:
- CPU: 2 cores
- RAM: 4GB
- Storage: 50GB SSD

Total Infrastructure:
- Servers: 4-6 (depending on load)
- Estimated Cost: $500-1000/month
```

#### Recommended Production Requirements
```
Web Tier (Redundant):
- CPU: 4 cores per server
- RAM: 8GB per server
- Storage: 100GB SSD
- Network: 10Gbps
- Load Balancer: HA setup

Application Tier (Auto-scaling):
- CPU: 8 cores per server
- RAM: 16GB per server
- Storage: 200GB SSD
- Network: 10Gbps
- Auto-scaling: 2-10 instances

Database Tier (High Availability):
- CPU: 8 cores
- RAM: 32GB
- Storage: 1TB NVMe SSD
- Network: 10Gbps
- Replication: Master-Slave setup

Cache Tier (Clustered):
- CPU: 4 cores per node
- RAM: 8GB per node
- Storage: 100GB SSD
- Network: 10Gbps
- Cluster: 3-node setup

Total Infrastructure:
- Servers: 8-12 (depending on load)
- Estimated Cost: $1500-3000/month
```

---

## Deployment Strategies

### 1. Docker-Based Deployment

#### Production Docker Compose
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  # Load Balancer
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
      - ./logs/nginx:/var/log/nginx
    depends_on:
      - web1
      - web2
    restart: unless-stopped
    networks:
      - frontend

  # Web Servers
  web1:
    build: .
    environment:
      - ENV=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    volumes:
      - ./config/production.json:/app/config.json
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - database
      - redis
    restart: unless-stopped
    networks:
      - frontend
      - backend

  web2:
    build: .
    environment:
      - ENV=production
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
    volumes:
      - ./config/production.json:/app/config.json
      - ./data:/app/data
      - ./logs:/app/logs
    depends_on:
      - database
      - redis
    restart: unless-stopped
    networks:
      - frontend
      - backend

  # Database
  database:
    image: postgres:14-alpine
    environment:
      - POSTGRES_DB=${POSTGRES_DB}
      - POSTGRES_USER=${POSTGRES_USER}
      - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    ports:
      - "5432:5432"
    restart: unless-stopped
    networks:
      - backend

  # Redis Cache
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    restart: unless-stopped
    networks:
      - backend

  # Monitoring
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/etc/prometheus/console_libraries'
      - '--web.console.templates=/etc/prometheus/consoles'
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  prometheus_data:

networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
```

#### Production Nginx Configuration
```nginx
# nginx/nginx.conf
upstream mafa_backend {
    least_conn;
    server web1:8000 max_fails=3 fail_timeout=30s;
    server web2:8000 max_fails=3 fail_timeout=30s;
    keepalive 32;
}

server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;

    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=5r/s;

    # API routes
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        
        proxy_pass http://mafa_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }

    # WebSocket routes
    location /ws {
        proxy_pass http://mafa_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files
    location /static/ {
        alias /var/www/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Frontend application
    location / {
        root /var/www/html;
        try_files $uri $uri/ /index.html;
        
        # Security for frontend
        location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Health check
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

### 2. Kubernetes Deployment

#### Production K8s Manifests
```yaml
# k8s/namespace.yaml
apiVersion: v1
kind: Namespace
metadata:
  name: mafa-production

---
# k8s/configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: mafa-config
  namespace: mafa-production
data:
  ENV: "production"
  LOG_LEVEL: "INFO"
  DATABASE_URL: "postgresql://user:pass@postgres-service/mafa"
  REDIS_URL: "redis://redis-service:6379"

---
# k8s/secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: mafa-secrets
  namespace: mafa-production
type: Opaque
data:
  SECRET_KEY: <base64-encoded-secret>
  DATABASE_PASSWORD: <base64-encoded-db-password>
  REDIS_PASSWORD: <base64-encoded-redis-password>

---
# k8s/postgres-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: postgres
  namespace: mafa-production
spec:
  replicas: 1
  selector:
    matchLabels:
      app: postgres
  template:
    metadata:
      labels:
        app: postgres
    spec:
      containers:
      - name: postgres
        image: postgres:14-alpine
        env:
        - name: POSTGRES_DB
          value: mafa
        - name: POSTGRES_USER
          value: mafa
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mafa-secrets
              key: DATABASE_PASSWORD
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: postgres-storage
          mountPath: /var/lib/postgresql/data
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
      volumes:
      - name: postgres-storage
        persistentVolumeClaim:
          claimName: postgres-pvc

---
# k8s/postgres-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: postgres-service
  namespace: mafa-production
spec:
  selector:
    app: postgres
  ports:
  - protocol: TCP
    port: 5432
    targetPort: 5432

---
# k8s/redis-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: mafa-production
spec:
  replicas: 1
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        command: ["redis-server", "--requirepass", "$(REDIS_PASSWORD)"]
        env:
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: mafa-secrets
              key: REDIS_PASSWORD
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"

---
# k8s/redis-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: mafa-production
spec:
  selector:
    app: redis
  ports:
  - protocol: TCP
    port: 6379
    targetPort: 6379

---
# k8s/mafa-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mafa
  namespace: mafa-production
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mafa
  template:
    metadata:
      labels:
        app: mafa
    spec:
      containers:
      - name: mafa
        image: mafa:latest
        envFrom:
        - configMapRef:
            name: mafa-config
        - secretRef:
            name: mafa-secrets
        ports:
        - containerPort: 8000
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
        resources:
          requests:
            memory: "2Gi"
            cpu: "1000m"
          limits:
            memory: "4Gi"
            cpu: "2000m"
        volumeMounts:
        - name: config-volume
          mountPath: /app/config
        - name: data-volume
          mountPath: /app/data
      volumes:
      - name: config-volume
        configMap:
          name: mafa-config
      - name: data-volume
        persistentVolumeClaim:
          claimName: mafa-data-pvc

---
# k8s/mafa-service.yaml
apiVersion: v1
kind: Service
metadata:
  name: mafa-service
  namespace: mafa-production
spec:
  selector:
    app: mafa
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: ClusterIP

---
# k8s/ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: mafa-ingress
  namespace: mafa-production
  annotations:
    nginx.ingress.kubernetes.io/rewrite-target: /
    nginx.ingress.kubernetes.io/ssl-redirect: "true"
    nginx.ingress.kubernetes.io/force-ssl-redirect: "true"
spec:
  tls:
  - hosts:
    - your-domain.com
    secretName: mafa-tls-secret
  rules:
  - host: your-domain.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: mafa-service
            port:
              number: 80
```

### 3. Cloud Provider Deployments

#### AWS Deployment with ECS
```json
{
  "family": "mafa-task",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "2048",
  "memory": "4096",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/mafaTaskRole",
  "containerDefinitions": [
    {
      "name": "mafa",
      "image": "your-account.dkr.ecr.region.amazonaws.com/mafa:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "ENV",
          "value": "production"
        },
        {
          "name": "DATABASE_URL",
          "value": "postgresql://user:pass@rds-endpoint:5432/mafa"
        }
      ],
      "secrets": [
        {
          "name": "SECRET_KEY",
          "valueFrom": "arn:aws:ssm:region:account:parameter/mafa/secret-key"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/mafa",
          "awslogs-region": "region",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### Google Cloud Run Deployment
```yaml
# cloudbuild.yaml
steps:
  # Build container image
  - name: 'gcr.io/cloud-builders/docker'
    args: ['build', '-t', 'gcr.io/$PROJECT_ID/mafa:$BUILD_ID', '.']
  
  # Push container image to Container Registry
  - name: 'gcr.io/cloud-builders/docker'
    args: ['push', 'gcr.io/$PROJECT_ID/mafa:$BUILD_ID']
  
  # Deploy container image to Cloud Run
  - name: 'gcr.io/cloud-builders/gcloud'
    args:
    - 'run'
    - 'deploy'
    - 'mafa'
    - '--image'
    - 'gcr.io/$PROJECT_ID/mafa:$BUILD_ID'
    - '--region'
    - 'europe-west1'
    - '--platform'
    - 'managed'
    - '--allow-unauthenticated'
    - '--set-env-vars'
    - 'ENV=production,DATABASE_URL=${_DATABASE_URL}'
    - '--set-secrets'
    - 'SECRET_KEY=mafa-secret:latest'
    
substitutions:
  _DATABASE_URL: "postgresql://user:pass@cloud-sql-ip:5432/mafa"
```

---

## Environment Configuration

### Production Environment Variables
```bash
# .env.production
# Core Application
ENV=production
DEBUG=false
SECRET_KEY=your-super-secret-key-here

# Database
DATABASE_URL=postgresql://mafa_user:password@db-host:5432/mafa
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30

# Redis
REDIS_URL=redis://:password@redis-host:6379
REDIS_PASSWORD=your-redis-password

# Security
JWT_SECRET_KEY=your-jwt-secret
CORS_ORIGINS=https://yourdomain.com
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com

# Email
SMTP_HOST=smtp.yourprovider.com
SMTP_PORT=587
SMTP_USER=noreply@yourdomain.com
SMTP_PASSWORD=your-smtp-password

# Telegram
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# Discord
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/...

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json
LOG_FILE=/var/log/mafa/app.log

# Monitoring
SENTRY_DSN=https://your-sentry-dsn
NEW_RELIC_LICENSE_KEY=your-newrelic-key

# Rate Limiting
RATE_LIMIT_PER_MINUTE=60
RATE_LIMIT_PER_HOUR=1000

# File Storage
UPLOAD_PATH=/app/uploads
MAX_FILE_SIZE=10485760

# Background Tasks
CELERY_BROKER_URL=redis://redis-host:6379/1
CELERY_RESULT_BACKEND=redis://redis-host:6379/2

# HTTPS/SSL
SSL_CERT_PATH=/etc/ssl/certs/domain.crt
SSL_KEY_PATH=/etc/ssl/private/domain.key

# Backup
BACKUP_SCHEDULE=0 2 * * *
BACKUP_RETENTION_DAYS=30
```

### Configuration Validation
```python
# scripts/validate_production_config.py
import os
import sys
from typing import List

def validate_config() -> List[str]:
    """Validate production configuration."""
    errors = []
    
    # Required environment variables
    required_vars = [
        'SECRET_KEY',
        'DATABASE_URL',
        'REDIS_URL',
        'JWT_SECRET_KEY'
    ]
    
    for var in required_vars:
        if not os.getenv(var):
            errors.append(f"Missing required environment variable: {var}")
    
    # Validate secret key strength
    secret_key = os.getenv('SECRET_KEY', '')
    if len(secret_key) < 32:
        errors.append("SECRET_KEY must be at least 32 characters")
    
    # Validate database URL
    db_url = os.getenv('DATABASE_URL', '')
    if not db_url.startswith('postgresql://'):
        errors.append("DATABASE_URL must use PostgreSQL in production")
    
    # Validate Redis URL
    redis_url = os.getenv('REDIS_URL', '')
    if not redis_url.startswith('redis://'):
        errors.append("REDIS_URL must use Redis")
    
    # Validate CORS origins
    cors_origins = os.getenv('CORS_ORIGINS', '')
    if not cors_origins:
        errors.append("CORS_ORIGINS must be set for production")
    
    # Validate SSL settings
    if os.getenv('ENV') == 'production':
        if not os.path.exists('/etc/ssl/certs/domain.crt'):
            errors.append("SSL certificate not found")
        if not os.path.exists('/etc/ssl/private/domain.key'):
            errors.append("SSL private key not found")
    
    return errors

if __name__ == "__main__":
    errors = validate_config()
    if errors:
        print("Configuration validation failed:")
        for error in errors:
            print(f"  - {error}")
        sys.exit(1)
    else:
        print("Configuration validation passed")
        sys.exit(0)
```

---

## Deployment Process

### Automated Deployment Script
```bash
#!/bin/bash
# scripts/deploy-production.sh

set -e

echo "Starting production deployment..."

# Configuration
DOCKER_IMAGE="mafa:production"
BACKUP_NAME="mafa-backup-$(date +%Y%m%d-%H%M%S)"
ROLLBACK_VERSION=""

# Validate configuration
echo "Validating configuration..."
python scripts/validate_production_config.py

# Create backup
echo "Creating backup: $BACKUP_NAME"
pg_dump $DATABASE_URL > "backups/$BACKUP_NAME.sql"
tar -czf "backups/$BACKUP_NAME.tar.gz" -C backups "$BACKUP_NAME.sql"

# Pull latest image
echo "Pulling latest Docker image..."
docker pull $DOCKER_IMAGE

# Deploy with zero downtime
echo "Deploying new version..."
docker-compose -f docker-compose.prod.yml up -d --no-deps mafa

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 30

# Run health checks
echo "Running health checks..."
./scripts/health-check.sh

# Update database schema if needed
echo "Checking database migrations..."
docker-compose -f docker-compose.prod.yml exec mafa python -c "
from mafa.db.migrations import run_pending_migrations
run_pending_migrations()
"

# Clear caches
echo "Clearing caches..."
docker-compose -f docker-compose.prod.yml exec redis redis-cli FLUSHALL

# Update load balancer
echo "Updating load balancer configuration..."
./scripts/update-load-balancer.sh

# Final health check
echo "Final health check..."
if ./scripts/health-check.sh; then
    echo "Deployment successful!"
    
    # Cleanup old images
    docker image prune -f
    
    # Log successful deployment
    echo "$(date): Deployment successful" >> /var/log/mafa/deployments.log
else
    echo "Health check failed! Rolling back..."
    
    # Rollback to previous version
    if [ -n "$ROLLBACK_VERSION" ]; then
        docker tag $ROLLBACK_VERSION $DOCKER_IMAGE
        docker-compose -f docker-compose.prod.yml up -d --no-deps mafa
        echo "$(date): Rolled back to $ROLLBACK_VERSION" >> /var/log/mafa/deployments.log
    fi
    
    exit 1
fi

echo "Production deployment completed successfully!"
```

### Health Check Script
```bash
#!/bin/bash
# scripts/health-check.sh

# Check API health
echo "Checking API health..."
if ! curl -f -s http://localhost:8000/health > /dev/null; then
    echo "API health check failed"
    exit 1
fi

# Check database connection
echo "Checking database connection..."
if ! curl -f -s http://localhost:8000/api/system/health | grep -q "database.*connected"; then
    echo "Database connection check failed"
    exit 1
fi

# Check Redis connection
echo "Checking Redis connection..."
if ! curl -f -s http://localhost:8000/api/system/health | grep -q "redis.*connected"; then
    echo "Redis connection check failed"
    exit 1
fi

# Check response time
echo "Checking response time..."
response_time=$(curl -o /dev/null -s -w "%{time_total}" http://localhost:8000/health)
if (( $(echo "$response_time > 2.0" | bc -l) )); then
    echo "Response time too slow: ${response_time}s"
    exit 1
fi

# Check error rate
echo "Checking error rate..."
error_count=$(curl -s http://localhost:8000/metrics | grep "http_requests_total{status=~"5.." }" | awk '{print $2}')
if [ "$error_count" -gt 10 ]; then
    echo "High error rate detected: $error_count errors"
    exit 1
fi

echo "All health checks passed"
exit 0
```

---

## Security Configuration

### SSL/TLS Configuration
```bash
# scripts/setup-ssl.sh
#!/bin/bash

DOMAIN=$1
EMAIL=$2

if [ -z "$DOMAIN" ] || [ -z "$EMAIL" ]; then
    echo "Usage: $0 <domain> <email>"
    exit 1
fi

# Install Certbot
sudo apt update
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d $DOMAIN -d www.$DOMAIN \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    --redirect

# Setup auto-renewal
sudo crontab -l | { cat; echo "0 12 * * * /usr/bin/certbot renew --quiet"; } | sudo crontab -

echo "SSL certificate setup complete for $DOMAIN"
```

### Firewall Configuration
```bash
# scripts/setup-firewall.sh
#!/bin/bash

# Ubuntu/Debian UFW configuration
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (adjust port as needed)
sudo ufw allow 22/tcp

# Allow HTTP and HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Allow internal database access (only from application servers)
sudo ufw allow from 10.0.0.0/8 to any port 5432

# Allow Redis access (only from application servers)
sudo ufw allow from 10.0.0.0/8 to any port 6379

# Enable firewall
sudo ufw --force enable

echo "Firewall configured successfully"
```

### Security Headers
```nginx
# nginx/security-headers.conf
# Security headers
add_header X-Frame-Options "DENY" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Referrer-Policy "strict-origin-when-cross-origin" always;
add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:;" always;

# Remove server tokens
server_tokens off;

# Hide Nginx version
more_clear_headers Server;
```

---

## Monitoring and Logging

### Prometheus Configuration
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'mafa'
    static_configs:
      - targets: ['web1:8000', 'web2:8000']
    metrics_path: /metrics
    scrape_interval: 30s

  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx:9113']

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### Grafana Dashboard Configuration
```json
{
  "dashboard": {
    "id": null,
    "title": "MAFA Production Dashboard",
    "tags": ["mafa", "production"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "API Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_request_duration_seconds_sum[5m]) / rate(http_request_duration_seconds_count[5m])",
            "legendFormat": "Average Response Time"
          }
        ]
      },
      {
        "id": 2,
        "title": "Error Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m]) / rate(http_requests_total[5m])",
            "legendFormat": "5xx Error Rate"
          }
        ]
      },
      {
        "id": 3,
        "title": "Database Connections",
        "type": "graph",
        "targets": [
          {
            "expr": "pg_stat_database_numbackends",
            "legendFormat": "Active Connections"
          }
        ]
      },
      {
        "id": 4,
        "title": "Redis Memory Usage",
        "type": "graph",
        "targets": [
          {
            "expr": "redis_memory_used_bytes",
            "legendFormat": "Memory Used"
          }
        ]
      }
    ]
  }
}
```

### Centralized Logging
```yaml
# logging/fluentd.conf
<source>
  @type tail
  path /var/log/mafa/*.log
  pos_file /var/log/fluentd-mafa.log.pos
  tag mafa.*
  format json
</source>

<source>
  @type tail
  path /var/log/nginx/access.log
  pos_file /var/log/fluentd-nginx-access.log.pos
  tag nginx.access
  format /^(?<remote_addr>[\d\.]+) - (?<user>.*?) \[(?<time>.*?)\] "(?<method>\S+) (?<path>\S+) (?<protocol>\S+)" (?<status>\d+) (?<size>\d+) "(?<referrer>[^"]*)" "(?<agent>[^"]*)"/
</source>

<match mafa.**>
  @type elasticsearch
  host elasticsearch
  port 9200
  index_name mafa-logs
  type_name _doc
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

## Backup and Recovery

### Database Backup Script
```bash
#!/bin/bash
# scripts/backup-database.sh

BACKUP_DIR="/var/backups/mafa"
DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_NAME="mafa-db-$DATE.sql"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create database backup
pg_dump $DATABASE_URL > "$BACKUP_DIR/$BACKUP_NAME"

# Compress backup
gzip "$BACKUP_DIR/$BACKUP_NAME"

# Upload to S3 (optional)
if [ "$UPLOAD_TO_S3" = "true" ]; then
    aws s3 cp "$BACKUP_DIR/$BACKUP_NAME.gz" "s3://$S3_BUCKET/database/"
fi

# Cleanup old backups (keep 30 days)
find $BACKUP_DIR -name "mafa-db-*.gz" -mtime +30 -delete

# Log backup
echo "$(date): Database backup completed: $BACKUP_NAME.gz" >> /var/log/mafa/backups.log
```

### Application Backup Script
```bash
#!/bin/bash
# scripts/backup-app.sh

BACKUP_DIR="/var/backups/mafa"
DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_NAME="mafa-app-$DATE.tar.gz"

# Create application backup
tar -czf "$BACKUP_DIR/$BACKUP_NAME" \
    -C /opt/mafa \
    config/ \
    data/ \
    --exclude='logs/*' \
    --exclude='*.log'

# Upload to S3 (optional)
if [ "$UPLOAD_TO_S3" = "true" ]; then
    aws s3 cp "$BACKUP_DIR/$BACKUP_NAME" "s3://$S3_BUCKET/application/"
fi

# Cleanup old backups (keep 7 days)
find $BACKUP_DIR -name "mafa-app-*.tar.gz" -mtime +7 -delete

echo "$(date): Application backup completed: $BACKUP_NAME" >> /var/log/mafa/backups.log
```

### Recovery Procedures
```bash
#!/bin/bash
# scripts/restore-from-backup.sh

BACKUP_FILE=$1
TARGET_ENV=$2

if [ -z "$BACKUP_FILE" ] || [ -z "$TARGET_ENV" ]; then
    echo "Usage: $0 <backup-file> <target-environment>"
    echo "Example: $0 /var/backups/mafa/mafa-db-20251119-143000.sql.gz production"
    exit 1
fi

echo "Starting recovery process..."
echo "Backup file: $BACKUP_FILE"
echo "Target environment: $TARGET_ENV"

# Confirm recovery
read -p "Are you sure you want to restore from this backup? (yes/no): " confirm
if [ "$confirm" != "yes" ]; then
    echo "Recovery cancelled"
    exit 1
fi

# Stop application
echo "Stopping application services..."
docker-compose -f docker-compose.prod.yml stop mafa

# Restore database
if [[ $BACKUP_FILE == *.gz ]]; then
    gunzip -c $BACKUP_FILE | psql $DATABASE_URL
else
    psql $DATABASE_URL < $BACKUP_FILE
fi

# Restore application files
if [[ $BACKUP_FILE == *.tar.gz ]]; then
    tar -xzf $BACKUP_FILE -C /opt/mafa
fi

# Restart application
echo "Starting application services..."
docker-compose -f docker-compose.prod.yml start mafa

# Run health checks
sleep 30
if ./scripts/health-check.sh; then
    echo "Recovery completed successfully!"
    echo "$(date): Recovery from $BACKUP_FILE completed" >> /var/log/mafa/recovery.log
else
    echo "Recovery completed but health checks failed!"
    exit 1
fi
```

---

## Performance Optimization

### Database Optimization
```sql
-- Database optimization settings
-- postgresql.conf

# Memory settings
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB

# Checkpoint settings
wal_buffers = 16MB
checkpoint_completion_target = 0.9

# Query planner
random_page_cost = 1.1
effective_io_concurrency = 200

# Connection settings
max_connections = 100
```

### Application Optimization
```python
# Production settings optimization
class ProductionSettings:
    # Database optimization
    DATABASE_POOL_SIZE = 20
    DATABASE_MAX_OVERFLOW = 30
    DATABASE_POOL_TIMEOUT = 30
    DATABASE_POOL_RECYCLE = 3600
    
    # Redis optimization
    REDIS_SOCKET_TIMEOUT = 5
    REDIS_SOCKET_CONNECT_TIMEOUT = 5
    REDIS_RETRY_ON_TIMEOUT = True
    REDIS_HEALTH_CHECK_INTERVAL = 30
    
    # API optimization
    API_TIMEOUT = 30
    API_MAX_RETRIES = 3
    API_BACKOFF_FACTOR = 1
    
    # Caching
    CACHE_DEFAULT_TIMEOUT = 300
    CACHE_KEY_PREFIX = "mafa:"
    
    # Background tasks
    CELERY_BROKER_POOL_LIMIT = 10
    CELERY_RESULT_EXPIRES = 3600
```

### Nginx Optimization
```nginx
# nginx/optimized.conf
# Worker processes
worker_processes auto;
worker_rlimit_nofile 65535;

# Connection settings
events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

http {
    # Basic settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    keepalive_requests 1000;
    types_hash_max_size 2048;
    
    # Buffer settings
    client_body_buffer_size 128k;
    client_max_body_size 10m;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 4k;
    output_buffers 1 32k;
    postpone_output 1460;
    
    # Timeout settings
    client_body_timeout 12;
    client_header_timeout 12;
    send_timeout 10;
    
    # Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_comp_level 6;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Caching
    proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=mafa_cache:10m max_size=1g inactive=60m;
    
    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=static:10m rate=100r/s;
}
```

---

## Scaling Strategies

### Horizontal Scaling
```yaml
# docker-compose.scale.yml
version: '3.8'

services:
  mafa:
    scale: 5
    deploy:
      replicas: 5
    resources:
      limits:
        cpus: '2.0'
        memory: 4G
      reservations:
        cpus: '1.0'
        memory: 2G

  nginx:
    scale: 2
    deploy:
      replicas: 2
```

### Auto-scaling Configuration
```yaml
# kubernetes/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: mafa-hpa
  namespace: mafa-production
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: mafa
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
      - type: Pods
        value: 2
        periodSeconds: 60
```

---

## Maintenance Procedures

### Regular Maintenance Tasks
```bash
#!/bin/bash
# scripts/maintenance.sh

echo "Starting MAFA maintenance tasks..."

# Update system packages
echo "Updating system packages..."
sudo apt update && sudo apt upgrade -y

# Update Python dependencies
echo "Updating Python dependencies..."
source venv/bin/activate
pip list --outdated
pip install --upgrade pip
pip install -r requirements.txt

# Clean up old logs
echo "Cleaning up old logs..."
find /var/log/mafa -name "*.log" -mtime +30 -delete

# Clean up Docker resources
echo "Cleaning up Docker resources..."
docker system prune -f
docker volume prune -f

# Database maintenance
echo "Running database maintenance..."
psql $DATABASE_URL -c "VACUUM ANALYZE;"

# Redis maintenance
echo "Running Redis maintenance..."
redis-cli FLUSHDB
redis-cli BGREWRITEAOF

# Security updates
echo "Checking for security updates..."
sudo unattended-upgrade -d

echo "Maintenance tasks completed"
```

### Zero-Downtime Updates
```bash
#!/bin/bash
# scripts/rolling-update.sh

NEW_VERSION=$1

if [ -z "$NEW_VERSION" ]; then
    echo "Usage: $0 <new-version>"
    exit 1
fi

echo "Starting rolling update to version $NEW_VERSION"

# Update load balancer to drain connections
curl -X POST http://load-balancer/config \
    -d '{"drain_mode": true}'

# Update one instance at a time
for instance in web1 web2 web3; do
    echo "Updating $instance..."
    
    # Pull new image
    docker pull mafa:$NEW_VERSION
    
    # Update container
    docker-compose -f docker-compose.prod.yml up -d --no-deps $instance
    
    # Wait for health check
    sleep 30
    if ! curl -f -s http://$instance:8000/health > /dev/null; then
        echo "Health check failed for $instance"
        exit 1
    fi
    
    # Resume traffic to this instance
    curl -X POST http://load-balancer/config \
        -d "{\"resume_instance\": \"$instance\"}"
done

# Resume all traffic
curl -X POST http://load-balancer/config \
    -d '{"drain_mode": false}'

echo "Rolling update completed successfully"
```

---

## Troubleshooting Production Issues

### Common Issues and Solutions

#### High Memory Usage
```bash
# Check memory usage
docker stats

# Analyze memory usage
docker exec mafa-container python -c "
import psutil
import gc

print('Memory usage:')
print(f'  Total: {psutil.virtual_memory().total / 1024**3:.1f} GB')
print(f'  Available: {psutil.virtual_memory().available / 1024**3:.1f} GB')
print(f'  Used: {psutil.virtual_memory().used / 1024**3:.1f} GB')
print(f'  Percentage: {psutil.virtual_memory().percent}%')

print('\nTop processes by memory:')
for proc in psutil.process_iter(['pid', 'name', 'memory_percent']):
    try:
        print(f'  {proc.info[\"pid\"]}: {proc.info[\"name\"]} - {proc.info[\"memory_percent\"]:.1f}%')
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        pass
"

# Clear Python garbage collection
docker exec mafa-container python -c "
import gc
gc.collect()
print('Garbage collection completed')
"
```

#### Database Connection Issues
```bash
# Check database connections
psql $DATABASE_URL -c "
SELECT count(*) as total_connections,
       count(*) FILTER (WHERE state = 'active') as active_connections,
       count(*) FILTER (WHERE state = 'idle') as idle_connections
FROM pg_stat_activity;
"

# Check database performance
psql $DATABASE_URL -c "
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements
ORDER BY total_time DESC
LIMIT 10;
"

# Kill long-running queries
psql $DATABASE_URL -c "
SELECT pg_terminate_backend(pid)
FROM pg_stat_activity
WHERE state = 'active' AND now() - query_start > interval '5 minutes';
"
```

#### Redis Issues
```bash
# Check Redis info
redis-cli info memory
redis-cli info stats
redis-cli info clients

# Check memory usage
redis-cli info memory | grep used_memory_human

# Check slow queries
redis-cli slowlog get 10

# Clear Redis cache if needed
redis-cli FLUSHALL

# Restart Redis if hung
docker-compose restart redis
```

---

## Related Documentation

- [Development Setup](../developer-guide/development-setup.md) - Development environment
- [Monitoring Guide](monitoring.md) - System monitoring and alerting
- [Backup and Restore](backup-restore.md) - Data backup procedures
- [Security Guide](security.md) - Security best practices
- [Configuration Reference](../getting-started/configuration.md) - Configuration options

---

**Deployment Support**: For production deployment issues, consult our [Deployment FAQ](https://github.com/your-org/mafa/wiki/Deployment-FAQ) or contact the operations team.