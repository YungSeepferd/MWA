# Installation Guide

## Overview
This guide covers all methods to install and set up MAFA (MüncheWohnungsAssistent) on your system. Choose the method that best fits your needs and technical expertise.

---

**Last Updated:** November 19, 2025  
**Version:** 1.0.0  
**Maintainer:** MAFA Development Team  
**Estimated Reading Time:** 10-15 minutes

---

## Quick Installation Summary

| Method | Difficulty | Time | Best For |
|--------|------------|------|----------|
| **Docker** | ⭐ Easy | 5 minutes | Most users, production |
| **Source** | ⭐⭐ Medium | 15-30 minutes | Developers, customization |
| **Requirements** | ⭐⭐⭐ Advanced | 20-45 minutes | Custom environments |

---

## Method 1: Docker Installation (Recommended)

### Prerequisites
- Docker Engine 20.10+ installed
- Docker Compose V2+
- 2GB available disk space
- Ports 8000 and 8080 available

### Installation Steps

#### 1. Clone the Repository
```bash
git clone https://github.com/your-org/mafa.git
cd mafa
```

#### 2. Configure Environment
```bash
# Copy example configuration
cp .env.example .env
cp config.example.json config.json

# Edit configuration (optional - defaults work for most cases)
nano .env
```

#### 3. Launch with Docker Compose
```bash
# Production deployment
docker-compose up -d

# Development deployment
docker-compose -f docker-compose.dev.yml up -d
```

#### 4. Verify Installation
```bash
# Check container status
docker-compose ps

# Check logs
docker-compose logs -f mafa

# Test API endpoint
curl http://localhost:8000/health
### Docker Configuration Options

#### Environment Variables (.env)
```bash
# Core Configuration
MAFA_ENV=production
DEBUG=false
SECRET_KEY=your-secret-key-here

# Database
DATABASE_URL=sqlite:///data/mafa.db
REDIS_URL=redis://redis:6379

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
API_WORKERS=4

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/mafa.log

# Security
CORS_ORIGINS=["http://localhost:3000"]
ALLOWED_HOSTS=["localhost", "127.0.0.1"]

# Scraper Settings
MAX_CONCURRENT_SCRAPERS=2
REQUEST_TIMEOUT=30
RETRY_ATTEMPTS=3

# Contact Discovery
CONTACT_CONFIDENCE_THRESHOLD=0.7
MAX_CONTACTS_PER_LISTING=5
```

#### Docker Compose Services
```yaml
services:
  mafa:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - ./data:/app/data
      - ./logs:/app/logs
      - ./config:/app/config
    environment:
      - DATABASE_URL=sqlite:///data/mafa.db
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    restart: unless-stopped

  dashboard:
    build:
      context: ./dashboard
      dockerfile: Dockerfile
    ports:
      - "8080:80"
    depends_on:
      - mafa
    restart: unless-stopped
```

### Docker Management Commands

#### Start/Stop Services
```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# Restart specific service
docker-compose restart mafa

# View logs
docker-compose logs -f mafa
```

#### Update Installation
```bash
# Pull latest changes
git pull origin main

# Rebuild containers
docker-compose build --no-cache
docker-compose up -d
```

---

## Method 2: Source Installation

### Prerequisites
- Python 3.8+ installed
- Node.js 16+ (for dashboard)
- Git
- Chrome/Chromium browser (for Selenium)
- 4GB available disk space

#### Python Dependencies
```bash
# Install system dependencies (Ubuntu/Debian)
sudo apt update
sudo apt install python3 python3-pip python3-venv
sudo apt install nodejs npm
sudo apt install chromium-browser chromium-chromedriver

# Install system dependencies (macOS)
brew install python@3.8 node chromium
brew install --cask google-chrome

# Install system dependencies (Fedora/CentOS)
sudo dnf install python3 python3-pip nodejs npm
sudo dnf install chromium google-chrome-stable
```

### Installation Steps

#### 1. Clone and Setup Python Environment
```bash
git clone https://github.com/your-org/mafa.git
cd mafa

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate  # Windows

# Install Python dependencies
pip install -r requirements.txt

# Install development dependencies (optional)
pip install -r requirements-dev.txt
```

#### 2. Install Chrome and ChromeDriver
```bash
# Option 1: Using webdriver-manager (automatic)
pip install webdriver-manager

# Option 2: Manual installation
# Download ChromeDriver matching your Chrome version
# Extract to /usr/local/bin/ (Linux/macOS) or C:\Windows\System32\ (Windows)
```

#### 3. Setup Database and Configuration
```bash
# Create data directory
mkdir -p data logs config

# Copy and edit configuration
cp config.example.json config.json
cp .env.example .env

# Initialize database
python -c "from mafa.db.manager import init_db; init_db()"

# Setup dashboard (if using frontend)
cd dashboard
npm install
npm run build
cd ..
```

#### 4. Launch Application
```bash
# Start API server
python -m api.main

# Or start with development mode
python run.py

# Or start dashboard separately
cd dashboard
npm run dev
```

### Source Configuration Options

#### Development Configuration (config.json)
```json
{
  "environment": "development",
  "debug": true,
  "database": {
    "url": "sqlite:///data/mafa_dev.db",
    "echo": true
  },
  "redis": {
    "url": "redis://localhost:6379"
  },
  "api": {
    "host": "127.0.0.1",
    "port": 8000,
    "reload": true
  },
  "logging": {
    "level": "DEBUG",
    "format": "detailed"
  },
  "scrapers": {
    "max_concurrent": 1,
    "timeout": 60,
    "retry_attempts": 2
  }
}
```

#### Production Configuration (config.json)
```json
{
  "environment": "production",
  "debug": false,
  "database": {
    "url": "sqlite:///data/mafa.db"
  },
  "redis": {
    "url": "redis://localhost:6379"
  },
  "api": {
    "host": "0.0.0.0",
    "port": 8000,
    "workers": 4
  },
  "logging": {
    "level": "INFO",
    "format": "json",
    "file": "logs/mafa.log"
  },
  "security": {
    "secret_key": "${SECRET_KEY}",
    "cors_origins": ["https://yourdomain.com"]
  }
}
```

### Source Management Commands

#### Development Server
```bash
# Start development server with auto-reload
python run.py --dev

# Start with specific configuration
python run.py --config config/development.json

# Start with custom port
python run.py --port 8080

# Run tests
python -m pytest tests/

# Run linting
flake8 mafa/ tests/
black mafa/ tests/
```

#### Production Server
```bash
# Start production server
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Or using systemd service
sudo systemctl start mafa
sudo systemctl status mafa

# Check logs
tail -f logs/mafa.log
```

---

## Method 3: Requirements-Based Installation

### Prerequisites
- Python 3.8+ with pip
- System-specific dependencies:
  - **Ubuntu/Debian**: `build-essential libssl-dev libffi-dev python3-dev`
  - **macOS**: Xcode Command Line Tools
  - **Windows**: Visual Studio Build Tools

### Advanced Configuration

#### Custom Database Setup
```bash
# PostgreSQL
pip install psycopg2-binary
export DATABASE_URL="postgresql://user:password@localhost/mafa"

# MySQL
pip install mysqlclient
export DATABASE_URL="mysql://user:password@localhost/mafa"

# SQLite (default, no extra dependencies)
export DATABASE_URL="sqlite:///path/to/mafa.db"
```

#### Custom Redis Setup
```bash
# Install Redis
# Ubuntu/Debian
sudo apt install redis-server

# macOS
brew install redis

# Windows
# Download from https://redis.io/download

# Configure connection
export REDIS_URL="redis://localhost:6379"
```

#### Custom Chrome/Selenium Setup
```bash
# Option 1: Use system Chrome
export CHROME_PATH="/usr/bin/google-chrome"
export CHROMEDRIVER_PATH="/usr/local/bin/chromedriver"

# Option 2: Use Chrome in container
export USE_CHROME_CONTAINER=true

# Option 3: Disable Selenium (limited functionality)
export DISABLE_JAVASCRIPT=true
```

---

## Verification and Testing

### Health Check
```bash
# API health check
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

### Test Basic Functionality
```bash
# Test configuration endpoint
curl http://localhost:8000/api/config/

# Test contact endpoint
curl http://localhost:8000/api/contacts/

# Test listings endpoint
curl http://localhost:8000/api/listings/

# Test scraper status
curl http://localhost:8000/api/scraper/status
```

### Dashboard Access
```bash
# Open dashboard (default installation)
open http://localhost:8080

# Or direct API access
open http://localhost:8000/docs  # API documentation
```

---

## Troubleshooting Installation Issues

### Common Docker Issues

#### Container Won't Start
```bash
# Check logs
docker-compose logs mafa

# Common fixes
# 1. Port conflicts
docker-compose down
# Edit docker-compose.yml to change ports
docker-compose up -d

# 2. Permission issues
sudo chown -R $USER:$USER .
docker-compose up -d

# 3. Disk space
docker system prune -a
```

#### Database Connection Issues
```bash
# Reset database
docker-compose down -v
docker-compose up -d

# Check database file permissions
ls -la data/
chmod 644 data/*.db
```

### Common Source Installation Issues

#### Python Dependencies
```bash
# Virtual environment issues
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# System dependencies (Ubuntu)
sudo apt install python3-dev libpq-dev
pip install psycopg2-binary
```

#### Chrome/Selenium Issues
```bash
# ChromeDriver version mismatch
# Check Chrome version
google-chrome --version

# Download matching ChromeDriver
wget https://chromedriver.storage.googleapis.com/$(curl -s https://chromedriver.storage.googleapis.com/LATEST_RELEASE)/chromedriver_linux64.zip

# Or use webdriver-manager
pip install webdriver-manager
python -c "from webdriver_manager.chrome import ChromeDriverManager; ChromeDriverManager().install()"
```

#### Database Issues
```bash
# Reset database
rm data/mafa.db
python -c "from mafa.db.manager import init_db; init_db()"

# Check database permissions
ls -la data/
chmod 664 data/mafa.db
```

---

## Next Steps

After successful installation:

1. **Complete Setup**: Follow the [Quick Start Guide](./quick-start.md) for initial configuration
2. **Configure Settings**: Review [Configuration Reference](./configuration.md) for detailed options
3. **Explore Dashboard**: Access the web interface at `http://localhost:8080`
4. **Read Documentation**: Check the [User Guide](../user-guide/overview.md) for usage instructions

---

## Related Documentation

- [Quick Start Guide](./quick-start.md) - Get up and running in 5 minutes
- [Configuration Reference](./configuration.md) - Detailed configuration options
- [User Guide Overview](../user-guide/overview.md) - Complete user documentation
- [Architecture Overview](../architecture/system-overview.md) - Technical system details

---

**Support**: If you encounter issues, please check the [Troubleshooting Guide](../user-guide/troubleshooting.md) or create an issue in our [GitHub repository](https://github.com/your-org/mafa/issues).