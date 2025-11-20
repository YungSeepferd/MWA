# Troubleshooting Guide

## Overview
This comprehensive troubleshooting guide helps you identify and resolve common issues with MAFA. Whether you're experiencing problems with installation, searching, notifications, or dashboard functionality, this guide provides step-by-step solutions.

---

**Last Updated:** November 19, 2025  
**Version:** 1.0.0  
**Maintainer:** MAFA Support Team  
**Estimated Reading Time:** 15-20 minutes

---

## Quick Diagnostics

### System Health Check
Start with these basic checks to identify the issue scope:

#### 1. API Health Check
```bash
# Test API endpoint
curl http://localhost:8000/health

# Expected response:
{
  "status": "healthy",
  "timestamp": "2025-11-19T21:00:00Z",
  "version": "1.0.0",
  "services": {
    "database": "connected",
    "redis": "connected",
    "scrapers": "ready"
  }
}
```

#### 2. Dashboard Accessibility
```bash
# Test dashboard
curl -I http://localhost:8080

# Should return 200 OK status
HTTP/1.1 200 OK
```

#### 3. Database Connection Test
```bash
# Test database directly
python -c "
from mafa.db.manager import DatabaseManager
db = DatabaseManager()
result = db.test_connection()
print('Database:', 'OK' if result else 'FAILED')
"
```

---

## Installation Issues

### Docker Installation Problems

#### Container Won't Start
**Symptoms**: `docker-compose up` fails or containers exit immediately

**Diagnosis Steps**:
```bash
# Check container logs
docker-compose logs mafa

# Check container status
docker-compose ps

# Check system resources
docker system df
df -h
```

**Common Solutions**:

1. **Port Conflicts**
   ```bash
   # Check what's using ports 8000 and 8080
   lsof -i :8000
   lsof -i :8080
   
   # Stop conflicting services or change ports in docker-compose.yml
   # Edit docker-compose.yml:
   ports:
     - "8001:8000"  # Change host port
     - "8081:80"    # Change host port
   ```

2. **Permission Issues**
   ```bash
   # Fix file permissions
   sudo chown -R $USER:$USER .
   chmod -R 755 .
   
   # Ensure Docker can access the directory
   ls -la data/
   ```

3. **Resource Constraints**
   ```bash
   # Check available resources
   free -h
   docker system info | grep Memory
   
   # Increase Docker memory allocation
   # Docker Desktop: Settings > Resources > Memory
   # Linux: Edit /etc/docker/daemon.json
   ```

4. **Disk Space Issues**
   ```bash
   # Clean up Docker
   docker system prune -a
   
   # Clean up logs
   rm -rf logs/*
   ```

#### Database Connection Failed
**Symptoms**: Container starts but API returns database errors

**Solutions**:
```bash
# Reset database volume
docker-compose down -v
docker-compose up -d

# Check database file permissions
docker-compose exec mafa ls -la /app/data/

# Recreate database
docker-compose exec mafa python -c "
from mafa.db.manager import init_db
init_db()
"
```

### Source Installation Issues

#### Python Dependency Problems
**Symptoms**: Import errors or missing module errors

**Diagnosis**:
```bash
# Check Python version
python3 --version

# Check virtual environment
source venv/bin/activate
which python
pip list

# Check for specific missing modules
python -c "import fastapi; print('FastAPI OK')"
```

**Solutions**:
```bash
# Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt
```

#### Chrome/Selenium Issues
**Symptoms**: Scraper fails with browser-related errors

**Diagnosis**:
```bash
# Check Chrome installation
google-chrome --version

# Check ChromeDriver
which chromedriver
chromedriver --version

# Test Selenium manually
python -c "
from selenium import webdriver
driver = webdriver.Chrome()
driver.get('https://www.google.com')
print('Selenium OK')
driver.quit()
"
```

**Solutions**:
```bash
# Option 1: Install Chrome and ChromeDriver
# Ubuntu/Debian
sudo apt update
sudo apt install chromium-browser chromium-chromedriver

# macOS
brew install chromium
brew install --cask google-chrome

# Option 2: Use webdriver-manager
pip install webdriver-manager
python -c "
from webdriver_manager.chrome import ChromeDriverManager
from selenium import webdriver
driver = webdriver.Chrome(ChromeDriverManager().install())
print('ChromeDriver installed successfully')
driver.quit()
"
```

#### Database Initialization Errors
**Symptoms**: Database creation fails or permission errors

**Solutions**:
```bash
# Create directories with proper permissions
mkdir -p data logs config
chmod 755 data logs config

# Initialize database
python -c "
from mafa.db.manager import init_db
init_db()
print('Database initialized')
"

# Check database file
ls -la data/
file data/mafa.db
```

---

## Search and Scraping Issues

### No Search Results

#### Symptoms and Diagnosis
```bash
# Check search status
curl http://localhost:8000/api/scraper/status

# Check recent logs
tail -f logs/mafa.log | grep -i search

# Test manual search
curl -X POST http://localhost:8000/api/scraper/test
```

**Common Causes and Solutions**:

1. **No Search Criteria Configured**
   ```bash
   # Check configuration
   curl http://localhost:8000/api/config/
   
   # Add minimal search criteria
   curl -X PUT http://localhost:8000/api/config/ \
     -H "Content-Type: application/json" \
     -d '{
       "search_criteria": {
         "price_range": {"maximum": 2000},
         "room_requirements": {"minimum_rooms": 1}
       }
     }'
   ```

2. **Search Providers Disabled**
   ```bash
   # Check provider status
   curl http://localhost:8000/api/scraper/providers
   
   # Enable providers
   curl -X PUT http://localhost:8000/api/scraper/config \
     -H "Content-Type: application/json" \
     -d '{
       "providers": {
         "immoscout": {"enabled": true},
         "wg_gesucht": {"enabled": true}
       }
     }'
   ```

3. **Rate Limiting Issues**
   ```bash
   # Check rate limit status
   curl http://localhost:8000/api/scraper/statistics
   
   # Increase delays if needed
   # Edit config.json:
   "scraper_config": {
     "providers": {
       "immoscout": {
         "search_delay_seconds": 5,  # Increase from 2
         "rate_limit_per_hour": 50   # Decrease from 100
       }
     }
   }
   ```

4. **Network/Firewall Issues**
   ```bash
   # Test connectivity to apartment sites
   curl -I https://www.immoscout24.de
   curl -I https://www.wg-gesucht.de
   
   # Check proxy settings
   echo $HTTP_PROXY
   echo $HTTPS_PROXY
   ```

### Search Takes Too Long

#### Performance Optimization
```bash
# Check search duration
tail -f logs/mafa.log | grep "duration"

# Monitor system resources
top -p $(pgrep -f mafa)
```

**Solutions**:
1. **Reduce Search Scope**
   ```json
   {
     "scraper_config": {
       "providers": {
         "immoscout": {
           "max_results_per_search": 25
         }
       },
       "schedule": {
         "max_concurrent_searches": 1
       }
     }
   }
   ```

2. **Increase Timeouts**
   ```json
   {
     "scraper_config": {
       "request_settings": {
         "timeout_seconds": 60
       },
       "browser_settings": {
         "page_load_timeout": 45
       }
     }
   }
   ```

3. **Optimize Search Criteria**
   - Narrow price range
   - Limit number of districts
   - Reduce maximum results per search

### Duplicate Listings

#### Diagnosis
```bash
# Check for duplicates in database
python -c "
from mafa.db.manager import DatabaseManager
db = DatabaseManager()
duplicates = db.find_duplicates()
print(f'Found {len(duplicates)} potential duplicates')
for dup in duplicates[:5]:
    print(f'  - {dup}')
"

# Check deduplication logs
grep -i duplicate logs/mafa.log
```

**Solutions**:
1. **Enable Deduplication**
   ```json
   {
     "scraper_config": {
       "output_filters": {
         "exclude_duplicates": true
       }
     }
   }
   ```

2. **Clean Existing Duplicates**
   ```bash
   # Run deduplication process
   python -c "
   from mafa.db.manager import DatabaseManager
   db = DatabaseManager()
   db.clean_duplicates()
   print('Duplicates cleaned')
   "
   ```

---

## Contact Discovery Issues

### Low Contact Discovery Rate

#### Diagnosis and Optimization
```bash
# Check contact discovery statistics
curl http://localhost:8000/api/analytics/contact-discovery

# Check extraction logs
grep -i "contact.*found" logs/mafa.log
grep -i "extraction.*failed" logs/mafa.log
```

**Optimization Strategies**:

1. **Adjust Confidence Thresholds**
   ```json
   {
     "contact_discovery": {
       "extraction_methods": {
         "email_patterns": {
           "confidence_threshold": 0.5  // Lower from 0.7
         },
         "phone_patterns": {
           "validate_format": false      // Disable strict validation
         }
       },
       "scoring_settings": {
         "minimum_confidence_for_notification": 0.5
       }
     }
   }
   ```

2. **Enable OCR Extraction**
   ```json
   {
     "contact_discovery": {
       "extraction_methods": {
         "ocr_extraction": {
           "enabled": true,
           "confidence_threshold": 0.4   // Lower for OCR
         }
       }
     }
   }
   ```

3. **Expand Email Patterns**
   ```json
   {
     "contact_discovery": {
       "extraction_methods": {
         "email_patterns": {
           "pattern_types": [
             "standard",
             "obfuscated",
             "base64",
             "javascript",
             "unicode",
             "rot13"
           ]
         }
       }
     }
   }
   ```

### Invalid Email Addresses

#### Email Validation Issues
```bash
# Check validation logs
grep -i "email.*invalid" logs/mafa.log
grep -i "validation.*failed" logs/mafa.log
```

**Solutions**:
1. **Disable Strict Validation**
   ```json
   {
     "contact_discovery": {
       "validation_settings": {
         "email_validation": {
           "enabled": false
         }
       }
     }
   }
   ```

2. **Relax Email Requirements**
   ```json
   {
     "contact_discovery": {
       "validation_settings": {
         "email_validation": {
           "check_smtp": false,
           "require_domain": []  // Allow any domain
         }
       }
     }
   }
   ```

3. **Manual Email Testing**
   ```bash
   # Test email format validation
   python -c "
   import re
   email = 'test@example.com'
   pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
   print('Valid:', bool(re.match(pattern, email)))
   "
   ```

### Phone Number Extraction Issues

#### German Phone Number Handling
```bash
# Check phone extraction logs
grep -i "phone.*found" logs/mafa.log
grep -i "phone.*invalid" logs/mafa.log
```

**Solutions**:
1. **Enable International Formats**
   ```json
   {
     "contact_discovery": {
       "extraction_methods": {
         "phone_patterns": {
           "country_code": "+49",
           "validate_format": false,
           "extract_mobile_preferred": true
         }
       }
     }
   }
   ```

2. **Custom Phone Patterns**
   Add support for various German phone formats:
   - `089 123456` (Munich landline)
   - `+49 89 123456` (International format)
   - `0171 1234567` (Mobile number)
   - `0800 123456` (Toll-free)

---

## Notification Issues

### Email Notifications Not Working

#### Diagnosis
```bash
# Test email configuration
curl -X POST http://localhost:8000/api/config/test-notifications \
  -H "Content-Type: application/json" \
  -d '{"channel": "email", "test_message": "Test email"}'

# Check email logs
grep -i "email" logs/mafa.log
grep -i "smtp" logs/mafa.log
```

**Common Solutions**:

1. **SMTP Configuration**
   ```json
   {
     "notification_settings": {
       "email": {
         "smtp_server": "smtp.gmail.com",
         "smtp_port": 587,
         "use_tls": true,
         "sender_email": "your-app@gmail.com",
         "sender_password": "your-app-password"
       }
     }
   }
   ```

2. **Gmail App Password**
   - Enable 2-factor authentication on Gmail
   - Generate app-specific password
   - Use app password instead of regular password

3. **Firewall/Network Issues**
   ```bash
   # Test SMTP connectivity
   telnet smtp.gmail.com 587
   openssl s_client -connect smtp.gmail.com:587
   
   # Check firewall settings
   sudo ufw status
   sudo iptables -L
   ```

4. **Email in Spam Folder**
   - Check spam/junk folders
   - Add sender to safe senders list
   - Use professional email address

### Discord Notifications Failing

#### Discord Webhook Issues
```bash
# Test Discord webhook
curl -X POST https://discord.com/api/webhooks/YOUR_WEBHOOK \
  -H "Content-Type: application/json" \
  -d '{"content": "Test message from MAFA"}'
```

**Solutions**:
1. **Verify Webhook URL**
   ```
   Discord Server Settings > Integrations > Webhooks
   Copy webhook URL
   ```

2. **Test Webhook Permissions**
   - Ensure webhook has permission to send messages
   - Check channel permissions
   - Verify webhook is not expired

3. **Content Formatting**
   ```json
   {
     "notification_settings": {
       "discord": {
         "webhook_url": "https://discord.com/api/webhooks/YOUR_WEBHOOK",
         "embed_style": "simple"
       }
     }
   }
   ```

### Telegram Bot Not Responding

#### Bot Configuration
```bash
# Test bot token
curl https://api.telegram.org/botYOUR_BOT_TOKEN/getMe

# Test sending message
curl -X POST "https://api.telegram.org/botYOUR_BOT_TOKEN/sendMessage" \
  -H "Content-Type: application/json" \
  -d '{"chat_id": "YOUR_CHAT_ID", "text": "Test message"}'
```

**Solutions**:
1. **Create Bot Properly**
   - Message @BotFather on Telegram
   - Use `/newbot` command
   - Get bot token and chat ID

2. **Get Chat ID**
   ```
   1. Start conversation with your bot
   2. Visit: https://api.telegram.org/bot<TOKEN>/getUpdates
   3. Find your chat_id in the response
   ```

3. **Bot Permissions**
   - Ensure bot can send messages
   - Check bot is not blocked
   - Verify chat_id is correct

---

## Dashboard Issues

### Dashboard Not Loading

#### Browser and Network Issues
```bash
# Check dashboard endpoint
curl -I http://localhost:8080

# Check API endpoint
curl -I http://localhost:8000
```

**Solutions**:

1. **Clear Browser Cache**
   ```
   Chrome: Ctrl+Shift+Delete
   Firefox: Ctrl+Shift+Delete
   Safari: Cmd+Option+E
   ```

2. **Disable Browser Extensions**
   - Ad blockers may interfere
   - Privacy extensions may block requests
   - Try incognito/private mode

3. **Check Network/Firewall**
   ```bash
   # Test local connectivity
   ping localhost
   telnet localhost 8080
   
   # Check firewall rules
   sudo ufw status
   netstat -tlnp | grep :8080
   ```

4. **Browser Compatibility**
   - Use modern browser (Chrome 80+, Firefox 75+, Safari 13+)
   - Enable JavaScript
   - Enable cookies

### Real-time Updates Not Working

#### WebSocket Connection Issues
```bash
# Test WebSocket endpoint
wscat -c ws://localhost:8000/ws

# Check WebSocket logs
grep -i websocket logs/mafa.log
```

**Solutions**:
1. **Browser WebSocket Support**
   - Most modern browsers support WebSocket
   - Check browser console for errors
   - Try different browser

2. **Network Issues**
   ```bash
   # Test WebSocket connection
   curl -i -N -H "Connection: Upgrade" \
     -H "Upgrade: websocket" \
     -H "Sec-WebSocket-Version: 13" \
     -H "Sec-WebSocket-Key: SGVsbG8sIHdvcmxkIQ==" \
     http://localhost:8000/ws
   ```

3. **Proxy/Firewall**
   - Some proxies block WebSocket connections
   - Check corporate firewall settings
   - Configure WebSocket proxying if needed

### Dashboard Performance Issues

#### Performance Optimization
```bash
# Check system resources
top -p $(pgrep -f mafa)
free -h
df -h
```

**Solutions**:
1. **Reduce Data Display**
   - Use pagination instead of loading all data
   - Apply filters to reduce results
   - Clear browser cache regularly

2. **Browser Performance**
   - Disable browser animations
   - Close unnecessary tabs
   - Update browser to latest version

3. **System Resources**
   - Increase available RAM
   - Close other applications
   - Use SSD storage for better performance

---

## Database Issues

### Database Corruption

#### Symptoms and Recovery
```bash
# Check database integrity
sqlite3 data/mafa.db "PRAGMA integrity_check;"

# Check database file size
ls -lah data/mafa.db
```

**Recovery Steps**:
1. **Backup Current Database**
   ```bash
   cp data/mafa.db data/mafa.db.backup
   ```

2. **Attempt Repair**
   ```bash
   sqlite3 data/mafa.db "REINDEX;"
   sqlite3 data/mafa.db "VACUUM;"
   ```

3. **Restore from Backup**
   ```bash
   # If repair fails, restore from backup
   cp data/mafa.db.backup data/mafa.db
   
   # Or restore from auto-backup
   ls backups/
   cp backups/latest/mafa.db data/
   ```

### Database Lock Issues

#### Concurrent Access Problems
```bash
# Check for database locks
lsof data/mafa.db

# Check for stuck processes
ps aux | grep mafa
```

**Solutions**:
1. **Close All Connections**
   ```bash
   # Restart MAFA services
   docker-compose restart mafa
   
   # Or kill stuck processes
   pkill -f mafa
   ```

2. **Increase Connection Limits**
   ```json
   {
     "storage_config": {
       "database": {
         "pool_size": 20,
         "max_overflow": 30
       }
     }
   }
   ```

### Large Database Performance

#### Optimization Strategies
```bash
# Check database size and record counts
sqlite3 data/mafa.db "SELECT COUNT(*) FROM contacts;"
sqlite3 data/mafa.db "SELECT COUNT(*) FROM listings;"
```

**Solutions**:
1. **Database Cleanup**
   ```bash
   # Remove old data
   python -c "
   from mafa.db.manager import DatabaseManager
   db = DatabaseManager()
   db.cleanup_old_data(days=30)
   "
   ```

2. **Add Database Indexes**
   ```bash
   # Add performance indexes
   sqlite3 data/mafa.db "
   CREATE INDEX IF NOT EXISTS idx_contacts_created ON contacts(created_at);
   CREATE INDEX IF NOT EXISTS idx_contacts_source ON contacts(source);
   CREATE INDEX IF NOT EXISTS idx_listings_price ON listings(price);
   "
   ```

3. **Database Migration**
   ```bash
   # Migrate to PostgreSQL for better performance
   # Update DATABASE_URL in configuration
   DATABASE_URL="postgresql://user:pass@localhost/mafa"
   ```

---

## Performance Issues

### System Running Slowly

#### Resource Monitoring
```bash
# Monitor system resources
top -p $(pgrep -f mafa)

# Check disk usage
df -h
du -sh data/ logs/

# Check memory usage
free -h
```

**Solutions**:
1. **Increase System Resources**
   - Add more RAM (minimum 4GB recommended)
   - Use SSD storage
   - Ensure adequate CPU cores

2. **Optimize MAFA Settings**
   ```json
   {
     "scraper_config": {
       "schedule": {
         "max_concurrent_searches": 1,  // Reduce from 2+
         "interval_minutes": 240         // Increase frequency
       }
     }
   }
   ```

3. **Background Cleanup**
   ```bash
   # Schedule regular cleanup
   # Add to crontab:
   0 2 * * * /path/to/mafa/scripts/cleanup.sh
   ```

### High CPU Usage

#### Search Optimization
```bash
# Check which processes consume CPU
top -p $(pgrep -f mafa)

# Monitor search processes
ps aux | grep search
```

**Solutions**:
1. **Reduce Search Frequency**
   ```json
   {
     "scraper_config": {
       "schedule": {
         "interval_minutes": 480  // Every 8 hours
       }
     }
   }
   ```

2. **Limit Search Scope**
   - Narrow price ranges
   - Reduce number of districts
   - Limit maximum results

3. **Enable Rate Limiting**
   ```json
   {
     "scraper_config": {
       "providers": {
         "immoscout": {
           "rate_limit_per_hour": 20
         }
       }
     }
   }
   ```

### High Memory Usage

#### Memory Optimization
```bash
# Monitor memory usage
ps aux | grep mafa
cat /proc/meminfo
```

**Solutions**:
1. **Limit Data Retention**
   ```json
   {
     "storage_config": {
       "cleanup": {
         "old_listings_retention_days": 7,  // Reduce from 30
         "failed_contact_attempts_retention_days": 1
       }
     }
   }
   ```

2. **Database Connection Pooling**
   ```json
   {
     "storage_config": {
       "database": {
         "pool_size": 5,  // Reduce from 10
         "max_overflow": 10
       }
     }
   }
   ```

3. **Regular Restarts**
   ```bash
   # Schedule weekly restarts
   # Add to crontab:
   0 3 * * 0 docker-compose restart mafa
   ```

---

## Error Recovery Procedures

### Complete System Reset

When all else fails, perform a complete system reset:

```bash
# 1. Stop all services
docker-compose down

# 2. Remove all data (backup first!)
cp -r data data.backup
rm -rf data/* logs/*

# 3. Clean Docker
docker system prune -f

# 4. Recreate containers
docker-compose up -d

# 5. Reconfigure system
# Run setup wizard again
```

### Backup and Restore

#### Backup Procedure
```bash
# Create comprehensive backup
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups/backup_$DATE"

mkdir -p $BACKUP_DIR

# Backup database
cp data/mafa.db $BACKUP_DIR/

# Backup configuration
cp config.json $BACKUP_DIR/
cp .env $BACKUP_DIR/

# Backup logs (last 7 days)
find logs/ -name "*.log" -mtime -7 -exec cp {} $BACKUP_DIR/ \;

# Create archive
tar -czf "mafa_backup_$DATE.tar.gz" $BACKUP_DIR
rm -rf $BACKUP_DIR

echo "Backup created: mafa_backup_$DATE.tar.gz"
```

#### Restore Procedure
```bash
# Extract backup
tar -xzf mafa_backup_20251119_140000.tar.gz

# Stop services
docker-compose down

# Restore database
cp backup_20251119_140000/mafa.db data/

# Restore configuration
cp backup_20251119_140000/config.json config/
cp backup_20251119_140000/.env .

# Start services
docker-compose up -d

# Verify restoration
curl http://localhost:8000/health
```

---

## Getting Additional Help

### Log Analysis

#### Important Log Files
```bash
# Application logs
tail -f logs/mafa.log

# Error logs
tail -f logs/error.log

# Access logs
tail -f logs/access.log

# System logs (if using systemd)
journalctl -u mafa -f
```

#### Log Analysis Commands
```bash
# Search for errors
grep -i error logs/mafa.log | tail -20

# Search for specific issues
grep -i "database\|connection\|timeout" logs/mafa.log

# Check search-related logs
grep -i "search\|scraper" logs/mafa.log | tail -10

# Check notification logs
grep -i "notification\|email\|discord" logs/mafa.log
```

### System Information

#### Useful Diagnostic Commands
```bash
# System information
uname -a
cat /etc/os-release

# Docker information
docker --version
docker-compose --version
docker system info

# Python information
python3 --version
pip list | grep -E "(fastapi|selenium|sqlalchemy)"

# MAFA version
curl http://localhost:8000/api/system/info
```

### Creating Support Tickets

When creating a support request, include:

1. **System Information**
   - Operating system and version
   - MAFA version (`curl http://localhost:8000/api/system/version`)
   - Installation method (Docker/source)

2. **Problem Description**
   - What you were trying to do
   - What happened instead
   - When the issue started

3. **Error Messages**
   - Copy exact error messages
   - Include relevant log entries
   - Screenshot of any error dialogs

4. **Steps to Reproduce**
   - Step-by-step instructions
   - Configuration details
   - Recent changes made

### Community Resources

- **GitHub Issues**: [Create issue](https://github.com/your-org/mafa/issues)
- **Discussion Forum**: [Community discussions](https://github.com/your-org/mafa/discussions)
- **Wiki**: [Additional documentation](https://github.com/your-org/mafa/wiki)
- **Discord**: [Real-time support](https://discord.gg/mafa)

---

## Related Documentation

- [Installation Guide](../getting-started/installation.md) - Setup and installation
- [Quick Start Guide](../getting-started/quick-start.md) - Get started quickly
- [Configuration Reference](../getting-started/configuration.md) - Detailed settings
- [Dashboard Guide](dashboard.md) - Interface and features
- [User Guide Overview](overview.md) - Complete user guide

---

**Support**: For urgent issues, create an issue on GitHub with your system details and error messages. For community support, visit our [Discussions page](https://github.com/your-org/mafa/discussions).