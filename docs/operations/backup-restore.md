# Backup and Restore Guide

## Overview
This guide covers comprehensive backup and restore procedures for MAFA, including database backups, configuration files, application data, and disaster recovery protocols for production environments.

---

**Last Updated:** November 19, 2025  
**Version:** 1.0.0  
**Maintainer:** MAFA Operations Team  
**Estimated Reading Time:** 25-30 minutes

---

## Backup Strategy Overview

### Backup Architecture
```
┌─────────────────────────────────────────────────────────────┐
│                      MAFA Production                        │
│                       Environment                          │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
┌───────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
│   Primary    │  │  Database   │  │ Application │
│  Database    │  │   Server    │  │   Files     │
└──────┬───────┘  └──────┬──────┘  └──────┬──────┘
       │                 │                 │
       └─────────────────┼─────────────────┘
                         │
        ┌────────────────┼─────────────────┐
        │                │                 │
┌───────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
│    Local     │  │    Cloud    │  │   Archive   │
│   Backup     │  │  Backup     │  │   Storage   │
│  Storage     │  │  Storage    │  │             │
└──────────────┘  └─────────────┘  └─────────────┘
```

### Backup Components
1. **Database Backups**: PostgreSQL full and incremental backups
2. **Configuration Files**: Environment configs, API keys, service configs
3. **Application Data**: User data, logs, temporary files
4. **Container Images**: Docker images and dependencies
5. **SSL Certificates**: TLS certificates and private keys
6. **Documentation**: System documentation and procedures

### Backup Schedule
- **Continuous**: Database WAL archival (real-time)
- **Hourly**: Incremental database backups
- **Daily**: Full database backups + application data
- **Weekly**: Complete system backups
- **Monthly**: Archive retention and cleanup

---

## Database Backup Procedures

### PostgreSQL Backup Configuration
```bash
#!/bin/bash
# scripts/db_backup_config.sh

# Install required packages
sudo apt-get install postgresql-client awscli

# Create backup user
sudo -u postgres psql -c "
CREATE USER backup_user WITH PASSWORD 'secure_backup_password';
GRANT CONNECT ON DATABASE mwa_core TO backup_user;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO backup_user;
GRANT USAGE ON SCHEMA public TO backup_user;
GRANT SELECT ON ALL SEQUENCES IN SCHEMA public TO backup_user;
"

# Configure WAL archiving
sudo -u postgres psql -c "
ALTER SYSTEM SET wal_level = replica;
ALTER SYSTEM SET archive_mode = on;
ALTER SYSTEM SET archive_command = 'aws s3 cp %p s3://mafa-backups/wal/%f';
ALTER SYSTEM SET max_wal_senders = 3;
ALTER SYSTEM SET checkpoint_segments = 16;
"

sudo systemctl restart postgresql
```

### Automated Database Backup Script
```bash
#!/bin/bash
# scripts/backup_database.sh

set -euo pipefail

# Configuration
DB_NAME="mwa_core"
DB_USER="backup_user"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
BACKUP_DIR="${BACKUP_DIR:-/var/backups/mafa}"
S3_BUCKET="${S3_BUCKET:-mafa-backups}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"
DATE=$(date +%Y%m%d_%H%M%S)

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Logging
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$BACKUP_DIR/backup.log"
}

error_exit() {
    log "ERROR: $1"
    exit 1
}

# Cleanup old backups
cleanup_old_backups() {
    log "Cleaning up backups older than $RETENTION_DAYS days"
    find "$BACKUP_DIR" -name "*.sql*" -type f -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -name "*.dump*" -type f -mtime +$RETENTION_DAYS -delete
}

# Full database backup
create_full_backup() {
    local backup_file="$BACKUP_DIR/mafa_full_backup_$DATE.sql"
    log "Creating full database backup: $backup_file"
    
    PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --verbose \
        --no-owner \
        --no-privileges \
        --format=custom \
        --file="$backup_file" \
        || error_exit "Full backup failed"
    
    # Compress backup
    gzip "$backup_file" || error_exit "Compression failed"
    
    # Upload to S3
    local s3_key="backups/database/full/mafa_full_backup_$DATE.sql.gz"
    log "Uploading to S3: s3://$S3_BUCKET/$s3_key"
    aws s3 cp "${backup_file}.gz" "s3://$S3_BUCKET/$s3_key" || error_exit "S3 upload failed"
    
    # Verify upload
    aws s3 ls "s3://$S3_BUCKET/$s3_key" || error_exit "S3 verification failed"
    
    log "Full backup completed successfully"
}

# Schema-only backup
create_schema_backup() {
    local backup_file="$BACKUP_DIR/mafa_schema_$DATE.sql"
    log "Creating schema backup: $backup_file"
    
    PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --schema-only \
        --no-owner \
        --no-privileges \
        > "$backup_file" \
        || error_exit "Schema backup failed"
    
    # Compress and upload
    gzip "$backup_file"
    local s3_key="backups/database/schema/mafa_schema_$DATE.sql.gz"
    aws s3 cp "${backup_file}.gz" "s3://$S3_BUCKET/$s3_key"
    
    log "Schema backup completed successfully"
}

# Data-only backup
create_data_backup() {
    local backup_file="$BACKUP_DIR/mafa_data_$DATE.sql"
    log "Creating data backup: $backup_file"
    
    PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --data-only \
        --no-owner \
        --no-privileges \
        > "$backup_file" \
        || error_exit "Data backup failed"
    
    # Compress and upload
    gzip "$backup_file"
    local s3_key="backups/database/data/mafa_data_$DATE.sql.gz"
    aws s3 cp "${backup_file}.gz" "s3://$S3_BUCKET/$s3_key"
    
    log "Data backup completed successfully"
}

# Table-specific backup
backup_specific_tables() {
    local tables="$1"
    local backup_file="$BACKUP_DIR/mafa_tables_$DATE.sql"
    
    log "Creating backup for tables: $tables"
    
    PGPASSWORD="$DB_PASSWORD" pg_dump \
        -h "$DB_HOST" \
        -p "$DB_PORT" \
        -U "$DB_USER" \
        -d "$DB_NAME" \
        --table="$tables" \
        --data-only \
        --no-owner \
        --no-privileges \
        > "$backup_file" \
        || error_exit "Table backup failed"
    
    # Compress and upload
    gzip "$backup_file"
    local s3_key="backups/database/tables/mafa_tables_$DATE.sql.gz"
    aws s3 cp "${backup_file}.gz" "s3://$S3_BUCKET/$s3_key"
    
    log "Table backup completed successfully"
}

# Check database integrity
verify_backup_integrity() {
    local backup_file="$1"
    
    log "Verifying backup integrity: $backup_file"
    
    # Test SQL syntax
    if [[ $backup_file == *.gz ]]; then
        gunzip -t "$backup_file" || error_exit "Backup file is corrupted (compression)"
        zcat "$backup_file" | head -50 | grep -q "^--" || error_exit "Backup file appears corrupted (SQL syntax)"
    else
        head -50 "$backup_file" | grep -q "^--" || error_exit "Backup file appears corrupted (SQL syntax)"
    fi
    
    log "Backup integrity verified successfully"
}

# Main execution
main() {
    log "Starting database backup process"
    
    # Load configuration
    if [[ -f "/etc/mafa/backup.conf" ]]; then
        source /etc/mafa/backup.conf
    fi
    
    # Check required environment variables
    [[ -n "${DB_PASSWORD:-}" ]] || error_exit "DB_PASSWORD not set"
    
    # Create backups
    case "${BACKUP_TYPE:-full}" in
        "full")
            create_full_backup
            create_schema_backup
            ;;
        "schema")
            create_schema_backup
            ;;
        "data")
            create_data_backup
            ;;
        "tables")
            backup_specific_tables "${TABLES:-contacts,listings}"
            ;;
        *)
            error_exit "Invalid backup type: $BACKUP_TYPE"
            ;;
    esac
    
    # Cleanup old backups
    cleanup_old_backups
    
    # Send notification
    log "Database backup process completed successfully"
    
    # Optional: Send notification
    if command -v mail >/dev/null 2>&1; then
        echo "Database backup completed successfully at $(date)" | mail -s "MAFA Database Backup Success" ops@mafa.app
    fi
}

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

### Continuous WAL Archiving
```bash
#!/bin/bash
# scripts/wal_archiving.sh

# PostgreSQL WAL archival script
# Called automatically by PostgreSQL when WAL files are ready for archival

WAL_FILE=$1
WAL_PATH=$2

# S3 bucket for WAL files
WAL_S3_BUCKET="mafa-backups/wal"

# Log archiving
echo "[$(date)] Archiving WAL file: $WAL_FILE" >> /var/log/postgresql/wal_archival.log

# Archive to S3
aws s3 cp "$WAL_PATH" "s3://$WAL_S3_BUCKET/$WAL_FILE" || exit 1

# Verify archival
aws s3 ls "s3://$WAL_S3_BUCKET/$WAL_FILE" >/dev/null || exit 1

# Clean up local WAL files older than 7 days
find /var/lib/postgresql/*/main/pg_wal -name "*.wal" -type f -mtime +7 -delete

echo "[$(date)] Successfully archived: $WAL_FILE" >> /var/log/postgresql/wal_archival.log

exit 0
```

---

## Application Data Backup

### Configuration Backup Script
```bash
#!/bin/bash
# scripts/backup_configs.sh

set -euo pipefail

# Configuration
S3_BUCKET="${S3_BUCKET:-mafa-backups}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/tmp/config_backup_$DATE"
CONFIG_DIR="${CONFIG_DIR:-/etc/mafa}"

# Create backup directory
mkdir -p "$BACKUP_DIR"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

error_exit() {
    log "ERROR: $1"
    exit 1
}

# Backup MAFA configuration files
backup_mafa_configs() {
    log "Backing up MAFA configuration files"
    
    # Main config directory
    if [[ -d "$CONFIG_DIR" ]]; then
        cp -r "$CONFIG_DIR" "$BACKUP_DIR/mafa_configs" || error_exit "Failed to copy MAFA configs"
    fi
    
    # Environment files
    find / -name "*.env*" -type f 2>/dev/null | while read env_file; do
        if [[ "$env_file" =~ \.(mafa|app) ]]; then
            mkdir -p "$BACKUP_DIR/environment_files"
            cp "$env_file" "$BACKUP_DIR/environment_files/"
        fi
    done
    
    # Docker configurations
    if [[ -f "docker-compose.yml" ]]; then
        mkdir -p "$BACKUP_DIR/docker"
        cp docker-compose.yml "$BACKUP_DIR/docker/"
    fi
    
    for dockerfile in Dockerfile*; do
        if [[ -f "$dockerfile" ]]; then
            mkdir -p "$BACKUP_DIR/docker"
            cp "$dockerfile" "$BACKUP_DIR/docker/"
        fi
    done
    
    # Nginx configuration
    if [[ -d "/etc/nginx" ]]; then
        cp -r /etc/nginx "$BACKUP_DIR/nginx" || true
    fi
    
    # Systemd service files
    cp /etc/systemd/system/mafa* "$BACKUP_DIR/systemd/" 2>/dev/null || true
    
    log "MAFA configuration backup completed"
}

# Backup SSL certificates
backup_ssl_certificates() {
    log "Backing up SSL certificates"
    
    mkdir -p "$BACKUP_DIR/ssl"
    
    # Let's Encrypt certificates
    if [[ -d "/etc/letsencrypt" ]]; then
        cp -r /etc/letsencrypt "$BACKUP_DIR/ssl/letsencrypt"
    fi
    
    # Custom SSL certificates
    find /etc/ssl /etc/pki -name "*.pem" -o -name "*.crt" -o -name "*.key" 2>/dev/null | while read cert_file; do
        mkdir -p "$BACKUP_DIR/ssl/custom"
        cp "$cert_file" "$BACKUP_DIR/ssl/custom/"
    done
    
    log "SSL certificates backup completed"
}

# Backup application logs
backup_application_logs() {
    log "Backing up application logs"
    
    mkdir -p "$BACKUP_DIR/logs"
    
    # Application logs
    if [[ -d "/var/log/mafa" ]]; then
        cp -r /var/log/mafa "$BACKUP_DIR/logs/mafa"
    fi
    
    # System logs (last 7 days)
    if [[ -d "/var/log" ]]; then
        find /var/log -name "*.log" -type f -mtime -7 | while read log_file; do
            mkdir -p "$BACKUP_DIR/logs/system/$(dirname "$log_file" | sed 's|/var/log/||')"
            cp "$log_file" "$BACKUP_DIR/logs/system/$(dirname "$log_file" | sed 's|/var/log/||')/"
        done
    fi
    
    log "Application logs backup completed"
}

# Backup user data and uploads
backup_user_data() {
    log "Backing up user data and uploads"
    
    mkdir -p "$BACKUP_DIR/user_data"
    
    # Dashboard uploads
    if [[ -d "/var/www/mafa/uploads" ]]; then
        cp -r /var/www/mafa/uploads "$BACKUP_DIR/user_data/dashboard_uploads"
    fi
    
    # Temporary files
    if [[ -d "/tmp/mafa" ]]; then
        cp -r /tmp/mafa "$BACKUP_DIR/user_data/temp_files"
    fi
    
    # Cron job files
    if [[ -d "/etc/cron.d" ]]; then
        cp /etc/cron.d/mafa* "$BACKUP_DIR/user_data/cron_jobs" 2>/dev/null || true
    fi
    
    log "User data backup completed"
}

# Backup monitoring configurations
backup_monitoring_configs() {
    log "Backing up monitoring configurations"
    
    mkdir -p "$BACKUP_DIR/monitoring"
    
    # Grafana configurations
    if [[ -d "/etc/grafana" ]]; then
        cp -r /etc/grafana "$BACKUP_DIR/monitoring/grafana"
    fi
    
    # Prometheus configurations
    if [[ -d "/etc/prometheus" ]]; then
        cp -r /etc/prometheus "$BACKUP_DIR/monitoring/prometheus"
    fi
    
    # AlertManager configurations
    if [[ -d "/etc/alertmanager" ]]; then
        cp -r /etc/alertmanager "$BACKUP_DIR/monitoring/alertmanager"
    fi
    
    log "Monitoring configurations backup completed"
}

# Upload to S3
upload_to_s3() {
    local s3_prefix="backups/configs/$DATE"
    
    log "Uploading configuration backup to S3"
    
    # Create archive
    cd "$BACKUP_DIR"
    tar -czf "../mafa_configs_$DATE.tar.gz" . || error_exit "Failed to create archive"
    cd ..
    
    # Upload to S3
    aws s3 cp "mafa_configs_$DATE.tar.gz" "s3://$S3_BUCKET/$s3_prefix/" || error_exit "S3 upload failed"
    
    # Cleanup local backup
    rm -rf "$BACKUP_DIR" "mafa_configs_$DATE.tar.gz"
    
    log "Configuration backup uploaded successfully to s3://$S3_BUCKET/$s3_prefix/"
}

# Main execution
main() {
    log "Starting configuration backup process"
    
    # Check AWS CLI
    command -v aws >/dev/null 2>&1 || error_exit "AWS CLI not installed"
    
    # Run backup procedures
    backup_mafa_configs
    backup_ssl_certificates
    backup_application_logs
    backup_user_data
    backup_monitoring_configs
    
    # Upload to S3
    upload_to_s3
    
    log "Configuration backup process completed successfully"
    
    # Cleanup S3 backups older than 30 days
    find . -name "mafa_configs_*.tar.gz" -mtime +30 -delete 2>/dev/null || true
}

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

### Complete System Backup Script
```bash
#!/bin/bash
# scripts/backup_complete_system.sh

set -euo pipefail

# Configuration
S3_BUCKET="${S3_BUCKET:-mafa-backups}"
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/tmp/system_backup_$DATE"
EXCLUDE_PATHS=(
    "/proc"
    "/sys"
    "/dev"
    "/run"
    "/tmp"
    "/var/cache"
    "/var/lib/docker"
    "/var/lib/lxcfs"
    "/snap"
)

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

error_exit() {
    log "ERROR: $1"
    exit 1
}

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Generate exclude list for rsync
generate_exclude_list() {
    cat > "$BACKUP_DIR/exclude_list.txt" << EOF
/proc/*
/sys/*
/dev/*
/run/*
/tmp/*
/var/cache/*
/var/lib/docker/*
/var/lib/lxcfs/*
/snap/*
EOF
    
    # Add custom exclusions
    echo "/var/log/journal/*" >> "$BACKUP_DIR/exclude_list.txt"
    echo "*.tmp" >> "$BACKUP_DIR/exclude_list.txt"
    echo "*.log.*" >> "$BACKUP_DIR/exclude_list.txt"
}

# Create system information snapshot
create_system_snapshot() {
    log "Creating system information snapshot"
    
    mkdir -p "$BACKUP_DIR/system_info"
    
    # System information
    uname -a > "$BACKUP_DIR/system_info/kernel_info.txt"
    cat /etc/os-release > "$BACKUP_DIR/system_info/os_info.txt"
    free -h > "$BACKUP_DIR/system_info/memory_info.txt"
    df -h > "$BACKUP_DIR/system_info/disk_info.txt"
    lscpu > "$BACKUP_DIR/system_info/cpu_info.txt"
    
    # Package list
    if command -v dpkg >/dev/null 2>&1; then
        dpkg -l > "$BACKUP_DIR/system_info/packages_debian.txt"
    fi
    
    if command -v rpm >/dev/null 2>&1; then
        rpm -qa > "$BACKUP_DIR/system_info/packages_rpm.txt"
    fi
    
    # Running services
    systemctl list-units --type=service --state=running > "$BACKUP_DIR/system_info/running_services.txt"
    
    # Network interfaces
    ip addr show > "$BACKUP_DIR/system_info/network_interfaces.txt"
    ip route show > "$BACKUP_DIR/system_info/routing_table.txt"
    
    log "System information snapshot completed"
}

# Create file system backup
create_filesystem_backup() {
    log "Creating filesystem backup"
    
    generate_exclude_list
    
    # Create root filesystem backup
    mkdir -p "$BACKUP_DIR/rootfs"
    
    rsync -aAXv \
        --exclude-from="$BACKUP_DIR/exclude_list.txt" \
        --progress \
        / "$BACKUP_DIR/rootfs/" \
        || error_exit "Filesystem backup failed"
    
    log "Filesystem backup completed"
}

# Create Docker images backup
backup_docker_images() {
    log "Backing up Docker images"
    
    if ! command -v docker >/dev/null 2>&1; then
        log "Docker not found, skipping image backup"
        return 0
    fi
    
    mkdir -p "$BACKUP_DIR/docker_images"
    
    # Save all Docker images
    docker images --format "{{.Repository}}:{{.Tag}}" | while read image; do
        log "Saving Docker image: $image"
        docker save "$image" | gzip > "$BACKUP_DIR/docker_images/$(echo "$image" | sed 's|[/:]|_|g').tar.gz"
    done
    
    log "Docker images backup completed"
}

# Create backup script and metadata
create_backup_metadata() {
    log "Creating backup metadata"
    
    # Backup script
    cp "$0" "$BACKUP_DIR/backup_script.sh"
    chmod +x "$BACKUP_DIR/backup_script.sh"
    
    # Backup manifest
    cat > "$BACKUP_DIR/BACKUP_MANIFEST.txt" << EOF
MAFA Complete System Backup
============================
Backup Date: $(date)
Hostname: $(hostname)
OS: $(cat /etc/os-release | grep PRETTY_NAME | cut -d'"' -f2)
Kernel: $(uname -r)
Architecture: $(uname -m)

Backup Contents:
- Root filesystem backup (excludes: /proc, /sys, /dev, /run, /tmp, etc.)
- Docker images
- System information snapshot
- Backup scripts and documentation

Restore Instructions:
1. Download and extract backup archive
2. Run the backup_script.sh with restore flag
3. Follow on-screen instructions for restoration

Backup Size: $(du -sh "$BACKUP_DIR" | cut -f1)
Backup Location: $BACKUP_DIR
EOF
    
    log "Backup metadata created"
}

# Upload to S3
upload_backup_to_s3() {
    local s3_prefix="backups/complete/$DATE"
    
    log "Uploading complete system backup to S3"
    
    # Create archive
    cd "$(dirname "$BACKUP_DIR")"
    tar -czf "mafa_system_backup_$DATE.tar.gz" "$(basename "$BACKUP_DIR")" || error_exit "Failed to create archive"
    cd - >/dev/null
    
    # Upload to S3
    aws s3 cp "mafa_system_backup_$DATE.tar.gz" "s3://$S3_BUCKET/$s3_prefix/" || error_exit "S3 upload failed"
    
    # Store backup info
    cat > "/tmp/backup_info_$DATE.json" << EOF
{
    "backup_date": "$DATE",
    "hostname": "$(hostname)",
    "s3_path": "s3://$S3_BUCKET/$s3_prefix/",
    "backup_size": "$(du -sh "mafa_system_backup_$DATE.tar.gz" | cut -f1)",
    "backup_type": "complete_system"
}
EOF
    
    aws s3 cp "/tmp/backup_info_$DATE.json" "s3://$S3_BUCKET/$s3_prefix/backup_info.json"
    
    # Cleanup
    rm -rf "$BACKUP_DIR" "mafa_system_backup_$DATE.tar.gz"
    rm "/tmp/backup_info_$DATE.json"
    
    log "Complete system backup uploaded to s3://$S3_BUCKET/$s3_prefix/"
}

# Main execution
main() {
    log "Starting complete system backup process"
    
    # Check prerequisites
    command -v aws >/dev/null 2>&1 || error_exit "AWS CLI not installed"
    command -v rsync >/dev/null 2>&1 || error_exit "rsync not installed"
    
    # Check disk space
    AVAILABLE_SPACE=$(df "$(dirname "$BACKUP_DIR")" | tail -1 | awk '{print $4}')
    if [[ $AVAILABLE_SPACE -lt 10485760 ]]; then  # Less than 10GB
        error_exit "Insufficient disk space for backup (need at least 10GB)"
    fi
    
    # Run backup procedures
    create_system_snapshot
    create_filesystem_backup
    backup_docker_images
    create_backup_metadata
    upload_backup_to_s3
    
    log "Complete system backup process finished successfully"
}

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

---

## Restore Procedures

### Database Restore Script
```bash
#!/bin/bash
# scripts/restore_database.sh

set -euo pipefail

# Configuration
DB_NAME="${DB_NAME:-mwa_core}"
DB_USER="${DB_USER:-mwa_core_user}"
DB_HOST="${DB_HOST:-localhost}"
DB_PORT="${DB_PORT:-5432}"
BACKUP_SOURCE="${BACKUP_SOURCE:-}"  # S3 path or local file
RESTORE_MODE="${RESTORE_MODE:-full}"  # full, schema, data, tables

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

error_exit() {
    log "ERROR: $1"
    exit 1
}

# Download backup from S3
download_backup() {
    local backup_file="$1"
    local local_file="${backup_file##*/}"  # Extract filename
    
    log "Downloading backup: $backup_file"
    
    if [[ "$backup_file" == s3://* ]]; then
        aws s3 cp "$backup_file" "/tmp/$local_file" || error_exit "Failed to download backup"
    elif [[ "$backup_file" == http://* ]] || [[ "$backup_file" == https://* ]]; then
        curl -o "/tmp/$local_file" "$backup_file" || error_exit "Failed to download backup"
    else
        # Local file
        cp "$backup_file" "/tmp/$local_file" || error_exit "Failed to copy local backup"
    fi
    
    echo "/tmp/$local_file"
}

# Verify backup integrity
verify_backup() {
    local backup_file="$1"
    
    log "Verifying backup integrity: $backup_file"
    
    if [[ "$backup_file" == *.gz ]]; then
        gunzip -t "$backup_file" || error_exit "Backup file is corrupted (compression)"
    fi
    
    # Check file size
    local file_size=$(stat -f%z "$backup_file" 2>/dev/null || stat -c%s "$backup_file")
    if [[ $file_size -lt 1024 ]]; then
        error_exit "Backup file is too small, possible corruption"
    fi
    
    log "Backup integrity verified"
}

# Restore full database
restore_full_database() {
    local backup_file="$1"
    
    log "Starting full database restore"
    
    # Stop MAFA services
    log "Stopping MAFA services"
    systemctl stop mafa-api || true
    systemctl stop mafa-scheduler || true
    
    # Drop and recreate database
    log "Recreating database"
    sudo -u postgres psql -c "DROP DATABASE IF EXISTS $DB_NAME;" || error_exit "Failed to drop database"
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" || error_exit "Failed to create database"
    
    # Restore from backup
    log "Restoring database from backup"
    if [[ "$backup_file" == *.gz ]]; then
        gunzip -c "$backup_file" | PGPASSWORD="$DB_PASSWORD" pg_restore \
            -h "$DB_HOST" \
            -p "$DB_PORT" \
            -U "$DB_USER" \
            -d "$DB_NAME" \
            --verbose \
            --no-owner \
            --no-privileges \
            || error_exit "Database restore failed"
    else
        PGPASSWORD="$DB_PASSWORD" pg_restore \
            -h "$DB_HOST" \
            -p "$DB_PORT" \
            -U "$DB_USER" \
            -d "$DB_NAME" \
            --verbose \
            --no-owner \
            --no-privileges \
            "$backup_file" \
            || error_exit "Database restore failed"
    fi
    
    # Update database permissions
    log "Updating database permissions"
    sudo -u postgres psql -d "$DB_NAME" -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"
    sudo -u postgres psql -d "$DB_NAME" -c "GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $DB_USER;"
    sudo -u postgres psql -d "$DB_NAME" -c "GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $DB_USER;"
    
    # Start MAFA services
    log "Starting MAFA services"
    systemctl start mafa-api
    systemctl start mafa-scheduler
    
    log "Full database restore completed successfully"
}

# Restore schema only
restore_schema() {
    local backup_file="$1"
    
    log "Starting schema restore"
    
    # Drop existing tables
    sudo -u postgres psql -d "$DB_NAME" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" || error_exit "Failed to reset schema"
    
    # Restore schema
    if [[ "$backup_file" == *.gz ]]; then
        gunzip -c "$backup_file" | PGPASSWORD="$DB_PASSWORD" psql \
            -h "$DB_HOST" \
            -p "$DB_PORT" \
            -U "$DB_USER" \
            -d "$DB_NAME" \
            || error_exit "Schema restore failed"
    else
        PGPASSWORD="$DB_PASSWORD" psql \
            -h "$DB_HOST" \
            -p "$DB_PORT" \
            -U "$DB_USER" \
            -d "$DB_NAME" \
            < "$backup_file" \
            || error_exit "Schema restore failed"
    fi
    
    log "Schema restore completed successfully"
}

# Restore data only
restore_data() {
    local backup_file="$1"
    
    log "Starting data restore"
    
    # Clear existing data
    sudo -u postgres psql -d "$DB_NAME" -c "
        TRUNCATE TABLE contacts CASCADE;
        TRUNCATE TABLE listings CASCADE;
        TRUNCATE TABLE search_criteria CASCADE;
        TRUNCATE TABLE notifications CASCADE;
    " || log "Warning: Some tables may not exist"
    
    # Restore data
    if [[ "$backup_file" == *.gz ]]; then
        gunzip -c "$backup_file" | PGPASSWORD="$DB_PASSWORD" psql \
            -h "$DB_HOST" \
            -p "$DB_PORT" \
            -U "$DB_USER" \
            -d "$DB_NAME" \
            || error_exit "Data restore failed"
    else
        PGPASSWORD="$DB_PASSWORD" psql \
            -h "$DB_HOST" \
            -p "$DB_PORT" \
            -U "$DB_USER" \
            -d "$DB_NAME" \
            < "$backup_file" \
            || error_exit "Data restore failed"
    fi
    
    log "Data restore completed successfully"
}

# Point-in-time recovery
point_in_time_recovery() {
    local target_time="$1"
    
    log "Starting point-in-time recovery to: $target_time"
    
    # Stop PostgreSQL
    systemctl stop postgresql
    
    # Restore base backup
    # This would require the base backup and WAL files
    
    # Configure recovery
    cat > /var/lib/postgresql/*/main/recovery.conf << EOF
restore_command = 'aws s3 cp s3://mafa-backups/wal/%f %p'
recovery_target_time = '$target_time'
recovery_target_action = 'promote'
EOF
    
    # Start PostgreSQL
    systemctl start postgresql
    
    log "Point-in-time recovery initiated"
}

# Main execution
main() {
    log "Starting database restore process"
    
    # Check required environment variables
    [[ -n "${DB_PASSWORD:-}" ]] || error_exit "DB_PASSWORD not set"
    [[ -n "$BACKUP_SOURCE" ]] || error_exit "BACKUP_SOURCE not specified"
    
    # Download backup
    local backup_file=$(download_backup "$BACKUP_SOURCE")
    
    # Verify backup
    verify_backup "$backup_file"
    
    # Execute restore based on mode
    case "$RESTORE_MODE" in
        "full")
            restore_full_database "$backup_file"
            ;;
        "schema")
            restore_schema "$backup_file"
            ;;
        "data")
            restore_data "$backup_file"
            ;;
        "pitr")
            point_in_time_recovery "${TARGET_TIME:-}"
            ;;
        *)
            error_exit "Invalid restore mode: $RESTORE_MODE"
            ;;
    esac
    
    # Cleanup
    rm -f "$backup_file"
    
    log "Database restore process completed successfully"
}

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

### Configuration Restore Script
```bash
#!/bin/bash
# scripts/restore_configs.sh

set -euo pipefail

# Configuration
S3_BUCKET="${S3_BUCKET:-mafa-backups}"
BACKUP_FILE="${BACKUP_FILE:-}"  # S3 path to config backup
RESTORE_PATH="${RESTORE_PATH:-/tmp/restore_configs}"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

error_exit() {
    log "ERROR: $1"
    exit 1
}

# Download configuration backup
download_config_backup() {
    log "Downloading configuration backup: $BACKUP_FILE"
    
    mkdir -p "$RESTORE_PATH"
    
    if [[ "$BACKUP_FILE" == s3://* ]]; then
        aws s3 cp "$BACKUP_FILE" "$RESTORE_PATH/" || error_exit "Failed to download config backup"
    elif [[ "$BACKUP_FILE" == http://* ]] || [[ "$BACKUP_FILE" == https://* ]]; then
        curl -o "$RESTORE_PATH/config_backup.tar.gz" "$BACKUP_FILE" || error_exit "Failed to download config backup"
    else
        # Local file
        cp "$BACKUP_FILE" "$RESTORE_PATH/config_backup.tar.gz" || error_exit "Failed to copy local config backup"
    fi
    
    log "Configuration backup downloaded successfully"
}

# Extract configuration backup
extract_config_backup() {
    log "Extracting configuration backup"
    
    cd "$RESTORE_PATH"
    tar -xzf config_backup.tar.gz || error_exit "Failed to extract config backup"
    cd - >/dev/null
    
    log "Configuration backup extracted"
}

# Restore MAFA configuration files
restore_mafa_configs() {
    log "Restoring MAFA configuration files"
    
    local backup_configs="$RESTORE_PATH/mafa_configs"
    
    if [[ -d "$backup_configs" ]]; then
        # Stop MAFA services
        log "Stopping MAFA services"
        systemctl stop mafa-api || true
        systemctl stop mafa-scheduler || true
        
        # Backup current configs
        if [[ -d "/etc/mafa" ]]; then
            cp -r /etc/mafa "/etc/mafa.backup.$(date +%Y%m%d_%H%M%S)"
        fi
        
        # Restore configs
        cp -r "$backup_configs" /etc/mafa
        
        # Set permissions
        chown -R root:root /etc/mafa
        chmod 600 /etc/mafa/*.json
        chmod 644 /etc/mafa/*.yaml
        
        log "MAFA configuration files restored"
    else
        log "Warning: MAFA config directory not found in backup"
    fi
}

# Restore environment files
restore_environment_files() {
    log "Restoring environment files"
    
    local env_backup="$RESTORE_PATH/environment_files"
    
    if [[ -d "$env_backup" ]]; then
        find "$env_backup" -name "*.env*" -type f | while read env_file; do
            filename=$(basename "$env_file")
            log "Restoring environment file: $filename"
            
            # Backup existing file
            if [[ -f "/etc/mafa/$filename" ]]; then
                cp "/etc/mafa/$filename" "/etc/mafa/$filename.backup.$(date +%Y%m%d_%H%M%S)"
            fi
            
            cp "$env_file" "/etc/mafa/$filename"
            chmod 600 "/etc/mafa/$filename"
        done
        
        log "Environment files restored"
    fi
}

# Restore Docker configurations
restore_docker_configs() {
    log "Restoring Docker configurations"
    
    local docker_backup="$RESTORE_PATH/docker"
    
    if [[ -d "$docker_backup" ]]; then
        for config_file in "$docker_backup"/*; do
            filename=$(basename "$config_file")
            log "Restoring Docker config: $filename"
            
            if [[ -f "$config_file" ]]; then
                cp "$config_file" "./$filename"
            fi
        done
        
        log "Docker configurations restored"
    fi
}

# Restore SSL certificates
restore_ssl_certificates() {
    log "Restoring SSL certificates"
    
    local ssl_backup="$RESTORE_PATH/ssl"
    
    if [[ -d "$ssl_backup" ]]; then
        # Backup current certificates
        if [[ -d "/etc/letsencrypt" ]]; then
            cp -r /etc/letsencrypt "/etc/letsencrypt.backup.$(date +%Y%m%d_%H%M%S)"
        fi
        
        # Restore Let's Encrypt certificates
        if [[ -d "$ssl_backup/letsencrypt" ]]; then
            cp -r "$ssl_backup/letsencrypt" /etc/
            chmod -R 600 /etc/letsencrypt/live/*/privkey.pem
            chmod 644 /etc/letsencrypt/live/*/*.pem
        fi
        
        # Restore custom certificates
        if [[ -d "$ssl_backup/custom" ]]; then
            cp -r "$ssl_backup/custom"/* /etc/ssl/ 2>/dev/null || true
        fi
        
        log "SSL certificates restored"
    fi
}

# Restore systemd service files
restore_systemd_services() {
    log "Restoring systemd service files"
    
    local systemd_backup="$RESTORE_PATH/systemd"
    
    if [[ -d "$systemd_backup" ]]; then
        cp "$systemd_backup"/* /etc/systemd/system/
        systemctl daemon-reload
        log "Systemd service files restored"
    fi
}

# Restore monitoring configurations
restore_monitoring_configs() {
    log "Restoring monitoring configurations"
    
    local monitoring_backup="$RESTORE_PATH/monitoring"
    
    if [[ -d "$monitoring_backup" ]]; then
        # Backup current configs
        if [[ -d "/etc/grafana" ]]; then
            cp -r /etc/grafana "/etc/grafana.backup.$(date +%Y%m%d_%H%M%S)"
        fi
        
        # Restore Grafana configs
        if [[ -d "$monitoring_backup/grafana" ]]; then
            cp -r "$monitoring_backup/grafana" /etc/
            systemctl restart grafana-server
        fi
        
        log "Monitoring configurations restored"
    fi
}

# Validate restored configurations
validate_configs() {
    log "Validating restored configurations"
    
    # Check MAFA config syntax
    if [[ -f "/etc/mafa/config.json" ]]; then
        python3 -c "import json; json.load(open('/etc/mafa/config.json'))" || {
            log "ERROR: Invalid MAFA config.json syntax"
            return 1
        }
    fi
    
    # Check docker-compose syntax
    if [[ -f "docker-compose.yml" ]]; then
        docker-compose config >/dev/null || {
            log "ERROR: Invalid docker-compose.yml syntax"
            return 1
        }
    fi
    
    # Test service configuration
    if command -v systemctl >/dev/null 2>&1; then
        systemctl status mafa-api >/dev/null 2>&1 || {
            log "WARNING: MAFA API service configuration may have issues"
        }
    fi
    
    log "Configuration validation completed"
}

# Main execution
main() {
    log "Starting configuration restore process"
    
    # Check prerequisites
    command -v aws >/dev/null 2>&1 || error_exit "AWS CLI not installed"
    
    # Check required parameters
    [[ -n "$BACKUP_FILE" ]] || error_exit "BACKUP_FILE not specified"
    
    # Load environment variables if file exists
    if [[ -f ".env" ]]; then
        source .env
    fi
    
    # Download and extract backup
    download_config_backup
    extract_config_backup
    
    # Restore configurations
    restore_mafa_configs
    restore_environment_files
    restore_docker_configs
    restore_ssl_certificates
    restore_systemd_services
    restore_monitoring_configs
    
    # Validate restored configurations
    validate_configs
    
    # Cleanup
    rm -rf "$RESTORE_PATH"
    
    log "Configuration restore process completed successfully"
    log "Please restart MAFA services to apply the restored configurations"
}

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

---

## Disaster Recovery Procedures

### Disaster Recovery Plan
```markdown
# MAFA Disaster Recovery Plan

## Emergency Contacts
- **On-Call Engineer**: +49-XXX-XXXXXXX
- **Database Administrator**: dba@mafa.app
- **System Administrator**: admin@mafa.app
- **Management**: mgmt@mafa.app

## Recovery Time Objectives (RTO)
- **Critical System**: 2 hours
- **Full System**: 4 hours
- **Data Recovery**: 6 hours

## Recovery Point Objectives (RPO)
- **Database**: 15 minutes (WAL archiving)
- **Configuration**: 24 hours
- **Application Data**: 24 hours

## Disaster Scenarios

### Scenario 1: Complete System Failure
**Symptoms**: No services responding, system won't boot, hardware failure

**Recovery Steps**:
1. Assess damage and notify stakeholders
2. Provision new infrastructure
3. Restore complete system backup
4. Restore latest database backup
5. Validate system functionality
6. Update DNS if IP address changed

### Scenario 2: Database Corruption
**Symptoms**: Database won't start, data corruption errors, inconsistent data

**Recovery Steps**:
1. Stop application services
2. Assess corruption extent
3. Restore from latest clean backup
4. Apply WAL files for point-in-time recovery
5. Validate data integrity
6. Restart services

### Scenario 3: Configuration Corruption
**Symptoms**: Services won't start, configuration errors, missing files

**Recovery Steps**:
1. Stop affected services
2. Identify corrupted configuration files
3. Restore configuration from backup
4. Validate configuration syntax
5. Restart services

### Scenario 4: Security Breach
**Symptoms**: Unauthorized access, data breach, compromised credentials

**Recovery Steps**:
1. Isolate affected systems immediately
2. Change all credentials and API keys
3. Restore from clean backup (before breach)
4. Apply security patches
5. Implement additional monitoring
6. Conduct security audit

## Recovery Testing Schedule
- **Monthly**: Database restore testing
- **Quarterly**: Configuration restore testing
- **Semi-Annually**: Complete system recovery testing
- **Annually**: Full disaster recovery simulation

## Backup Verification
- **Daily**: Automated backup integrity checks
- **Weekly**: Manual backup restoration testing
- **Monthly**: Cross-region backup verification
```

### Emergency Recovery Script
```bash
#!/bin/bash
# scripts/emergency_recovery.sh

set -euo pipefail

# Emergency recovery configuration
EMERGENCY_CONTACT="oncall@mafa.app"
RECOVERY_LOG="/var/log/mafa/emergency_recovery.log"
BACKUP_TIMESTAMP="${BACKUP_TIMESTAMP:-}"  # Format: 20251119_210000

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$RECOVERY_LOG"
}

error_exit() {
    log "ERROR: $1"
    send_emergency_notification "RECOVERY FAILED: $1"
    exit 1
}

# Send emergency notification
send_emergency_notification() {
    local message="$1"
    log "Sending emergency notification: $message"
    
    # Send email
    if command -v mail >/dev/null 2>&1; then
        echo "$message" | mail -s "MAFA Emergency Recovery" "$EMERGENCY_CONTACT"
    fi
    
    # Send Slack notification (if webhook configured)
    if [[ -n "${SLACK_WEBHOOK_URL:-}" ]]; then
        curl -X POST -H 'Content-type: application/json' \
            --data "{\"text\":\"🚨 MAFA Emergency: $message\"}" \
            "$SLACK_WEBHOOK_URL" || true
    fi
}

# Assess system status
assess_system_status() {
    log "Assessing current system status"
    
    # Check database connectivity
    if command -v psql >/dev/null 2>&1; then
        if psql -c "SELECT 1;" >/dev/null 2>&1; then
            log "Database: HEALTHY"
            return 0
        else
            log "Database: FAILED"
            return 1
        fi
    else
        log "Database: NOT ACCESSIBLE"
        return 1
    fi
}

# Emergency database recovery
emergency_db_recovery() {
    log "Starting emergency database recovery"
    
    # Stop all services
    log "Stopping all MAFA services"
    systemctl stop mafa-api || true
    systemctl stop mafa-scheduler || true
    systemctl stop postgresql || true
    
    # Find latest clean backup
    local backup_prefix="backups/database/full/mafa_full_backup"
    if [[ -n "$BACKUP_TIMESTAMP" ]]; then
        backup_prefix="${backup_prefix}_${BACKUP_TIMESTAMP}"
    else
        backup_prefix=$(aws s3 ls "s3://${S3_BUCKET:-mafa-backups}/${backup_prefix}" | sort | tail -1 | awk '{print $4}')
    fi
    
    if [[ -z "$backup_prefix" ]]; then
        error_exit "No database backup found"
    fi
    
    local s3_backup="s3://${S3_BUCKET:-mafa-backups}/backups/database/full/${backup_prefix}"
    log "Using backup: $s3_backup"
    
    # Restore database
    DB_PASSWORD="$DB_PASSWORD" ./scripts/restore_database.sh \
        BACKUP_SOURCE="$s3_backup" \
        RESTORE_MODE="full" \
        || error_exit "Database restore failed"
    
    log "Emergency database recovery completed"
}

# Emergency configuration recovery
emergency_config_recovery() {
    log "Starting emergency configuration recovery"
    
    # Find latest config backup
    local config_prefix="backups/configs/"
    local latest_config=$(aws s3 ls "s3://${S3_BUCKET:-mafa-backups}/${config_prefix}" | sort | tail -1 | awk '{print $4}')
    
    if [[ -z "$latest_config" ]]; then
        error_exit "No configuration backup found"
    fi
    
    local s3_config="s3://${S3_BUCKET:-mafa-backups}/${config_prefix}${latest_config}"
    log "Using config backup: $s3_config"
    
    # Restore configurations
    ./scripts/restore_configs.sh \
        BACKUP_FILE="$s3_config" \
        || error_exit "Configuration restore failed"
    
    log "Emergency configuration recovery completed"
}

# Restart services
restart_services() {
    log "Restarting MAFA services"
    
    # Start database
    systemctl start postgresql
    sleep 10
    
    # Start MAFA services
    systemctl start mafa-api || error_exit "Failed to start MAFA API"
    systemctl start mafa-scheduler || error_exit "Failed to start MAFA scheduler"
    
    # Verify services are running
    sleep 30
    
    if systemctl is-active --quiet mafa-api && systemctl is-active --quiet mafa-scheduler; then
        log "All services restarted successfully"
    else
        error_exit "Some services failed to start"
    fi
}

# Health check
perform_health_check() {
    log "Performing post-recovery health check"
    
    # Check API health
    if curl -f -s http://localhost:8000/health >/dev/null; then
        log "API health check: PASSED"
    else
        log "API health check: FAILED"
        return 1
    fi
    
    # Check database connectivity
    if psql -c "SELECT COUNT(*) FROM contacts;" >/dev/null 2>&1; then
        log "Database connectivity: PASSED"
    else
        log "Database connectivity: FAILED"
        return 1
    fi
    
    # Check log files for errors
    if tail -n 100 /var/log/mafa/app.log | grep -i error >/dev/null; then
        log "Application logs: WARNINGS FOUND"
    else
        log "Application logs: CLEAN"
    fi
    
    log "Health check completed"
}

# Main execution
main() {
    log "Starting MAFA emergency recovery process"
    send_emergency_notification "MAFA Emergency Recovery Initiated"
    
    # Check if recovery is really needed
    if assess_system_status; then
        log "System appears to be healthy. Aborting emergency recovery."
        exit 0
    fi
    
    # Perform recovery procedures
    emergency_db_recovery
    emergency_config_recovery
    restart_services
    
    # Verify recovery success
    if perform_health_check; then
        log "Emergency recovery completed successfully"
        send_emergency_notification "MAFA Emergency Recovery COMPLETED SUCCESSFULLY"
    else
        error_exit "Emergency recovery failed health check"
    fi
}

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

---

## Backup Monitoring and Validation

### Backup Monitoring Script
```bash
#!/bin/bash
# scripts/monitor_backups.sh

set -euo pipefail

# Configuration
S3_BUCKET="${S3_BUCKET:-mafa-backups}"
MONITOR_LOG="/var/log/mafa/backup_monitor.log"
ALERT_THRESHOLD_HOURS=25  # Alert if backup is older than 25 hours

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$MONITOR_LOG"
}

# Check backup freshness
check_backup_freshness() {
    local backup_type="$1"
    local s3_prefix="backups/$backup_type/"
    
    log "Checking freshness of $backup_type backups"
    
    # Get latest backup timestamp
    local latest_backup=$(aws s3 ls "s3://$S3_BUCKET/$s3_prefix" --recursive | sort | tail -1)
    
    if [[ -z "$latest_backup" ]]; then
        log "ALERT: No $backup_type backups found"
        return 1
    fi
    
    # Extract timestamp
    local backup_time=$(echo "$latest_backup" | awk '{print $1 " " $2}' | cut -d'.' -f1)
    local backup_epoch=$(date -d "$backup_time" +%s 2>/dev/null || date -j -f "%Y-%m-%d %H:%M:%S" "$backup_time" +%s)
    local current_epoch=$(date +%s)
    local age_hours=$(( (current_epoch - backup_epoch) / 3600 ))
    
    log "Latest $backup_type backup: $backup_time (${age_hours}h old)"
    
    # Check freshness
    if [[ $age_hours -gt $ALERT_THRESHOLD_HOURS ]]; then
        log "ALERT: $backup_type backup is ${age_hours}h old (threshold: ${ALERT_THRESHOLD_HOURS}h)"
        return 1
    fi
    
    return 0
}

# Test backup integrity
test_backup_integrity() {
    local backup_type="$1"
    local backup_file="$2"
    
    log "Testing integrity of $backup_type backup: $backup_file"
    
    # Download backup to temporary location
    local temp_file="/tmp/backup_test_$(date +%s).gz"
    aws s3 cp "$backup_file" "$temp_file" >/dev/null 2>&1 || {
        log "ALERT: Failed to download backup for integrity test"
        rm -f "$temp_file"
        return 1
    }
    
    # Test compression integrity
    gunzip -t "$temp_file" >/dev/null 2>&1 || {
        log "ALERT: Backup file is corrupted (compression test failed)"
        rm -f "$temp_file"
        return 1
    }
    
    # Test SQL syntax (for database backups)
    if [[ "$backup_type" == "database" ]]; then
        zcat "$temp_file" | head -50 | grep -q "^--" || {
            log "ALERT: Backup file appears corrupted (SQL syntax test failed)"
            rm -f "$temp_file"
            return 1
        }
    fi
    
    # Cleanup
    rm -f "$temp_file"
    
    log "Backup integrity test passed for $backup_type"
    return 0
}

# Check backup sizes
check_backup_sizes() {
    local backup_type="$1"
    local s3_prefix="backups/$backup_type/"
    
    log "Checking backup sizes for $backup_type"
    
    # Get backup sizes
    local backup_sizes=$(aws s3 ls "s3://$S3_BUCKET/$s3_prefix" --recursive --summarize | grep "Total Size" | awk '{print $3}')
    
    if [[ -n "$backup_sizes" ]]; then
        local avg_size=$(echo "$backup_sizes" | awk '{sum+=$1; count++} END {print sum/count}')
        local min_size=$(echo "$backup_sizes" | sort -n | head -1)
        local max_size=$(echo "$backup_sizes" | sort -nr | head -1)
        
        log "$backup_type backup sizes - Min: $min_size bytes, Max: $max_size bytes, Avg: $avg_size bytes"
        
        # Alert if average size is suspiciously small
        if [[ $(echo "$avg_size < 1024" | bc -l) -eq 1 ]]; then
            log "ALERT: $backup_type backups are unusually small"
            return 1
        fi
    fi
    
    return 0
}

# Generate backup report
generate_backup_report() {
    local report_file="/tmp/backup_report_$(date +%Y%m%d_%H%M%S).txt"
    
    log "Generating backup report: $report_file"
    
    cat > "$report_file" << EOF
MAFA Backup Report
==================
Generated: $(date)

Backup Status Summary:
EOF
    
    # Check each backup type
    for backup_type in database configs complete; do
        log "Checking $backup_type backup status"
        
        if check_backup_freshness "$backup_type"; then
            echo "✓ $backup_type: Fresh" >> "$report_file"
        else
            echo "✗ $backup_type: Stale or missing" >> "$report_file"
        fi
    done
    
    echo "" >> "$report_file"
    echo "Last 10 Backups:" >> "$report_file"
    aws s3 ls "s3://$S3_BUCKET/backups/" --recursive | tail -10 >> "$report_file"
    
    # Send report
    if command -v mail >/dev/null 2>&1; then
        mail -s "MAFA Backup Report - $(date +%Y-%m-%d)" ops@mafa.app < "$report_file"
    fi
    
    # Upload to S3
    aws s3 cp "$report_file" "s3://$S3_BUCKET/reports/backup_report_$(date +%Y%m%d).txt"
    
    # Cleanup
    rm -f "$report_file"
    
    log "Backup report generated and distributed"
}

# Main execution
main() {
    log "Starting backup monitoring check"
    
    # Check AWS CLI
    command -v aws >/dev/null 2>&1 || { log "ERROR: AWS CLI not installed"; exit 1; }
    
    # Check each backup type
    local issues_found=0
    
    for backup_type in database configs complete; do
        if ! check_backup_freshness "$backup_type"; then
            issues_found=1
        fi
        
        # Test integrity of latest backup
        local latest_backup=$(aws s3 ls "s3://$S3_BUCKET/backups/$backup_type/" | sort | tail -1 | awk '{print $4}')
        if [[ -n "$latest_backup" ]]; then
            if ! test_backup_integrity "$backup_type" "s3://$S3_BUCKET/backups/$backup_type/$latest_backup"; then
                issues_found=1
            fi
        fi
        
        if ! check_backup_sizes "$backup_type"; then
            issues_found=1
        fi
    done
    
    # Generate daily report
    if [[ $(date +%H) == "06" ]]; then  # 6 AM daily report
        generate_backup_report
    fi
    
    # Alert if issues found
    if [[ $issues_found -eq 1 ]]; then
        log "ALERT: Backup monitoring found issues - check $MONITOR_LOG"
        # Send alert (implement based on your alerting system)
        echo "Backup monitoring issues detected" | mail -s "MAFA Backup Alert" ops@mafa.app
    fi
    
    log "Backup monitoring check completed"
}

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
```

### Cron Jobs for Automated Backup
```bash
#!/bin/bash
# Add these lines to crontab (crontab -e)

# Database backups - every 6 hours
0 */6 * * * /scripts/backup_database.sh >> /var/log/mafa/backup_cron.log 2>&1

# Configuration backups - daily at 2 AM
0 2 * * * /scripts/backup_configs.sh >> /var/log/mafa/backup_cron.log 2>&1

# Complete system backup - weekly on Sunday at 3 AM
0 3 * * 0 /scripts/backup_complete_system.sh >> /var/log/mafa/backup_cron.log 2>&1

# Backup monitoring - every 4 hours
0 */4 * * * /scripts/monitor_backups.sh >> /var/log/mafa/backup_monitor.log 2>&1

# Clean old backups - daily at 4 AM
0 4 * * * find /var/backups/mafa -name "*.sql*" -type f -mtime +30 -delete 2>/dev/null

# Sync backups to offsite storage - daily at 5 AM
0 5 * * * aws s3 sync /var/backups/mafa/ s3://mafa-backups-local/ --delete >> /var/log/mafa/backup_sync.log 2>&1
```

---

## Backup Retention and Cleanup

### Retention Policy
```bash
# retention_policy.sh
# Backup retention policy implementation

RETENTION_POLICY=(
    # Format: type:frequency:retention_days
    "database:hourly:7"
    "database:daily:30"
    "database:weekly:90"
    "configs:daily:30"
    "configs:weekly:180"
    "complete:monthly:365"
)

apply_retention_policy() {
    local backup_type="$1"
    local frequency="$2"
    local retention_days="$3"
    
    log "Applying retention policy for $backup_type ($frequency): $retention_days days"
    
    # S3 path for this backup type
    local s3_prefix="s3://${S3_BUCKET}/backups/${backup_type}/${frequency}/"
    
    # List and delete old backups
    aws s3 ls "$s3_prefix" | while read -r line; do
        local backup_date=$(echo "$line" | awk '{print $1}')
        local backup_time=$(echo "$line" | awk '{print $2}')
        local backup_datetime="${backup_date}T${backup_time}"
        local backup_epoch=$(date -d "$backup_datetime" +%s 2>/dev/null || echo "0")
        local current_epoch=$(date +%s)
        local age_days=$(( (current_epoch - backup_epoch) / 86400 ))
        
        if [[ $age_days -gt $retention_days ]]; then
            local backup_file=$(echo "$line" | awk '{print $4}')
            log "Deleting old backup: $backup_file (age: ${age_days} days)"
            aws s3 rm "$s3_prefix$backup_file"
        fi
    done
}

# Main retention application
main() {
    log "Starting backup retention policy application"
    
    for policy in "${RETENTION_POLICY[@]}"; do
        IFS=':' read -r backup_type frequency retention_days <<< "$policy"
        apply_retention_policy "$backup_type" "$frequency" "$retention_days"
    done
    
    log "Backup retention policy application completed"
}
```

---

## Related Documentation

- [Deployment Guide](deployment.md) - Production deployment procedures
- [System Monitoring](monitoring.md) - Monitoring and alerting setup
- [Security Guide](security.md) - Security best practices
- [Configuration Reference](../getting-started/configuration.md) - Configuration options

---

**Backup Support**: For backup-related issues or questions, contact the operations team or create an issue with the `backup` label.