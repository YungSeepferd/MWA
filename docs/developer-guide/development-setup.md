# Development Setup Guide

## Overview
This guide covers setting up a complete development environment for MAFA, including all necessary tools, dependencies, and workflows for effective development, testing, and contribution.

---

**Last Updated:** November 19, 2025  
**Version:** 1.0.0  
**Maintainer:** MAFA Development Team  
**Estimated Reading Time:** 20-30 minutes

---

## Prerequisites

### System Requirements
- **Operating System**: Linux, macOS, or Windows 10+
- **RAM**: Minimum 8GB, Recommended 16GB+
- **Storage**: 10GB free space for development environment
- **Network**: Stable internet connection for dependency installation

### Required Software

#### Core Development Tools
```bash
# Git (version control)
git --version  # Should be 2.25+

# Python (backend development)
python3 --version  # Should be 3.8+

# Node.js (frontend development)
node --version  # Should be 16+
npm --version   # Should be 8+

# Docker (containerization)
docker --version   # Should be 20.10+
docker-compose --version  # Should be 2.0+
```

#### Optional but Recommended
```bash
# Redis (caching and session storage)
redis-server --version

# PostgreSQL (production database)
psql --version

# Visual Studio Code (recommended IDE)
code --version
```

### Platform-Specific Installation

#### Ubuntu/Debian
```bash
# Update package index
sudo apt update

# Install system dependencies
sudo apt install -y \
    git \
    python3 \
    python3-pip \
    python3-venv \
    python3-dev \
    build-essential \
    libssl-dev \
    libffi-dev \
    libpq-dev \
    nodejs \
    npm \
    redis-server \
    postgresql-client

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Log out and back in for group changes to take effect
```

#### macOS
```bash
# Install Homebrew (if not already installed)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install \
    git \
    python@3.8 \
    node \
    redis \
    postgresql

# Install Docker Desktop
brew install --cask docker

# Install additional tools
brew install \
    tree \
    jq \
    httpie
```

#### Windows
```powershell
# Install Chocolatey (if not already installed)
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://chocolatey.org/install.ps1'))

# Install dependencies
choco install -y \
    git \
    python3 \
    nodejs \
    redis \
    docker-desktop

# Install VS Code
choco install -y visualstudiocode
```

---

## Environment Setup

### 1. Clone Repository
```bash
# Clone the repository
git clone https://github.com/your-org/mafa.git
cd mafa

# Verify clone
git status
git remote -v
```

### 2. Python Environment Setup

#### Create Virtual Environment
```bash
# Create project-specific virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate

# Verify activation
which python
python --version
```

#### Install Dependencies
```bash
# Upgrade pip
pip install --upgrade pip

# Install production dependencies
pip install -r requirements.txt

# Install development dependencies
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install

# Verify installation
pip list
```

### 3. Node.js Environment Setup

```bash
# Navigate to frontend directory
cd dashboard

# Install dependencies
npm install

# Install global dependencies for development
npm install -g \
    eslint \
    prettier \
    webpack-dev-server

# Build frontend for development
npm run build:dev

# Return to project root
cd ..
```

### 4. Database Setup

#### SQLite (Default Development)
```bash
# Create data directory
mkdir -p data

# Initialize database
python -c "
from mafa.db.manager import init_db
init_db()
print('Database initialized')
"

# Verify database creation
ls -la data/
file data/mafa.db
```

#### PostgreSQL (Advanced Development)
```bash
# Start PostgreSQL service
# Ubuntu/Debian:
sudo systemctl start postgresql
sudo systemctl enable postgresql

# macOS:
brew services start postgresql

# Create development database
sudo -u postgres createdb mafa_dev
sudo -u postgres createuser mafa_dev_user -P

# Set environment variable
echo "export DATABASE_URL='postgresql://mafa_dev_user:password@localhost/mafa_dev'" >> ~/.bashrc
source ~/.bashrc

# Test connection
python -c "
from sqlalchemy import create_engine
engine = create_engine('postgresql://mafa_dev_user:password@localhost/mafa_dev')
engine.connect()
print('PostgreSQL connection successful')
"
```

### 5. Redis Setup

```bash
# Start Redis server
# Ubuntu/Debian:
sudo systemctl start redis-server
sudo systemctl enable redis-server

# macOS:
brew services start redis

# Windows (if installed as service):
Start-Service Redis

# Test Redis connection
redis-cli ping
# Should return: PONG

# Set Redis URL in environment
echo "export REDIS_URL='redis://localhost:6379'" >> ~/.bashrc
source ~/.bashrc
```

---

## Development Configuration

### Environment Configuration
```bash
# Create environment file
cp .env.example .env

# Configure environment variables
cat > .env << EOF
# Development Environment
MAFA_ENV=development
DEBUG=true

# Database
DATABASE_URL=sqlite:///data/mafa_dev.db

# Redis
REDIS_URL=redis://localhost:6379

# API Configuration
API_HOST=127.0.0.1
API_PORT=8000
API_RELOAD=true

# Security (development only)
SECRET_KEY=dev-secret-key-not-for-production
JWT_SECRET_KEY=dev-jwt-secret-key

# Logging
LOG_LEVEL=DEBUG
LOG_FORMAT=detailed

# Frontend
VITE_API_URL=http://127.0.0.1:8000
VITE_WS_URL=ws://127.0.0.1:8000

# Development Tools
ENABLE_PROFILING=true
ENABLE_DEBUG_TOOLBAR=true
EOF

# Source environment variables
source .env
```

### IDE Configuration

#### Visual Studio Code Setup
```bash
# Install recommended extensions
code --install-extension ms-python.python
code --install-extension ms-vscode.vscode-json
code --install-extension bradlc.vscode-tailwindcss
code --install-extension esbenp.prettier-vscode
code --install-extension ms-python.flake8
```

#### VS Code Workspace Settings
Create `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.formatting.provider": "black",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.pylintEnabled": false,
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests/"],
  "editor.formatOnSave": true,
  "editor.codeActionsOnSave": {
    "source.organizeImports": true
  },
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true,
    "**/node_modules": true,
    "**/dist": true,
    "**/.pytest_cache": true
  }
}
```

#### VS Code Debug Configuration
Create `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "MAFA API",
      "type": "python",
      "request": "launch",
      "program": "${workspaceFolder}/api/main.py",
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    },
    {
      "name": "MAFA Tests",
      "type": "python",
      "request": "launch",
      "module": "pytest",
      "args": ["tests/"],
      "console": "integratedTerminal",
      "cwd": "${workspaceFolder}"
    }
  ]
}
```

---

## Development Workflow

### 1. Starting Development Servers

#### Backend Development Server
```bash
# Activate virtual environment
source venv/bin/activate

# Start development server with auto-reload
python run.py --dev

# Or start with custom configuration
python run.py --config config/development.json --reload

# Or use uvicorn directly
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

#### Frontend Development Server
```bash
# Navigate to dashboard directory
cd dashboard

# Start development server
npm run dev

# Server will be available at http://localhost:8080
# API proxy to http://127.0.0.1:8000
```

#### Using Docker for Development
```bash
# Start development environment with Docker
docker-compose -f docker-compose.dev.yml up -d

# View logs
docker-compose -f docker-compose.dev.yml logs -f mafa

# Access development environment
# API: http://localhost:8000
# Dashboard: http://localhost:8080
```

### 2. Development Commands

#### Code Quality
```bash
# Run linting
flake8 mafa/ tests/
black mafa/ tests/
isort mafa/ tests/

# Type checking
mypy mafa/

# Security analysis
bandit -r mafa/

# Format code
black mafa/ tests/
isort mafa/ tests/
prettier --write dashboard/static/**/*.{js,css}
```

#### Testing
```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=mafa --cov-report=html

# Run specific test file
pytest tests/test_contacts.py

# Run tests with markers
pytest -m "not slow"

# Run integration tests
pytest tests/integration/

# Run performance tests
pytest tests/performance/
```

#### Database Operations
```bash
# Initialize database
python -c "from mafa.db.manager import init_db; init_db()"

# Reset database
rm data/mafa_dev.db
python -c "from mafa.db.manager import init_db; init_db()"

# Create database migration
alembic revision --autogenerate -m "Description"

# Run migrations
alembic upgrade head

# Backup database
cp data/mafa_dev.db data/mafa_dev.backup.db
```

#### Frontend Commands
```bash
cd dashboard

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Run linting
npm run lint

# Run tests
npm test

# Type checking
npm run type-check
```

### 3. Git Workflow

#### Feature Development
```bash
# Create feature branch
git checkout -b feature/new-feature-name

# Make changes and commit
git add .
git commit -m "feat: add new feature description"

# Push branch
git push origin feature/new-feature-name

# Create pull request
# (Use GitHub UI or gh CLI)
```

#### Commit Message Convention
```
feat: add contact discovery optimization
fix: resolve database connection timeout
docs: update API documentation
style: format code with black
refactor: simplify contact scoring logic
test: add unit tests for contact extractor
chore: update dependencies
```

#### Branch Strategy
- `main`: Production-ready code
- `develop`: Integration branch for features
- `feature/*`: Individual feature development
- `hotfix/*`: Critical bug fixes
- `release/*`: Release preparation

---

## Testing Setup

### 1. Test Configuration

#### Create Test Configuration
```bash
# Copy test configuration
cp config.example.json config/test.json

# Create test environment file
cat > .env.test << EOF
MAFA_ENV=test
DEBUG=false
DATABASE_URL=sqlite:///data/test.db
REDIS_URL=redis://localhost:6379/1
LOG_LEVEL=WARNING
EOF
```

#### Test Database Setup
```bash
# Create test database
python -c "
from mafa.db.manager import DatabaseManager
from sqlalchemy import create_engine

# Create test database
engine = create_engine('sqlite:///data/test.db')
from mafa.db.models import Base
Base.metadata.create_all(engine)
print('Test database created')
"
```

### 2. Test Types

#### Unit Tests
```bash
# Run unit tests
pytest tests/unit/

# Run specific unit test
pytest tests/unit/test_contacts.py::test_contact_extraction

# Run with coverage
pytest tests/unit/ --cov=mafa --cov-report=term-missing
```

#### Integration Tests
```bash
# Run integration tests
pytest tests/integration/

# Run API integration tests
pytest tests/integration/test_api_integration.py

# Run database integration tests
pytest tests/integration/test_database.py
```

#### End-to-End Tests
```bash
# Run E2E tests (requires running servers)
pytest tests/e2e/

# Run with browser automation
pytest tests/e2e/ --browser=chrome
```

### 3. Test Data Management

#### Fixtures
```python
# tests/fixtures/test_data.py
import pytest
from tests.factories import ContactFactory, ListingFactory

@pytest.fixture
def sample_contacts():
    return ContactFactory.create_batch(10)

@pytest.fixture
def sample_listings():
    return ListingFactory.create_batch(5)
```

#### Factories
```python
# tests/factories.py
import factory
from mafa.models import Contact, Listing

class ContactFactory(factory.Factory):
    class Meta:
        model = Contact
    
    email = factory.Faker('email')
    phone = factory.Faker('phone_number')
    confidence = factory.Faker('random_int', min=50, max=100)
    source = 'test'

class ListingFactory(factory.Factory):
    class Meta:
        model = Listing
    
    title = factory.Faker('sentence')
    price = factory.Faker('random_int', min=500, max=2000)
    rooms = factory.Faker('random_int', min=1, max=5)
    source = 'test'
```

---

## Development Tools

### 1. API Development

#### Interactive API Documentation
```bash
# Start development server
python run.py --dev

# Access API documentation
open http://127.0.0.1:8000/docs

# Alternative documentation
open http://127.0.0.1:8000/redoc
```

#### API Testing
```bash
# Test API endpoints
curl -X GET http://127.0.0.1:8000/api/contacts/

# Test with authentication
curl -H "Authorization: Bearer <token>" \
     http://127.0.0.1:8000/api/contacts/

# Test using HTTPie (recommended)
http GET localhost:8000/api/contacts/
http POST localhost:8000/api/contacts/ \
    email="test@example.com" \
    confidence:=0.9
```

### 2. Database Development

#### Database GUI Tools
```bash
# Install database GUI tools
pip install sqlalchemy[postgresql]

# Use built-in development tools
python -c "
from mafa.db.manager import DatabaseManager
db = DatabaseManager()
db.open_sqlite_browser()  # Opens SQLite browser
"

# For PostgreSQL
psql postgresql://user:pass@localhost/mafa_dev
```

#### Database Migrations
```bash
# Create new migration
alembic revision --autogenerate -m "Add contact validation"

# Apply migrations
alembic upgrade head

# Rollback migration
alembic downgrade -1

# Check migration status
alembic current
alembic history
```

### 3. Frontend Development

#### Browser DevTools
```bash
# Start development server
cd dashboard && npm run dev

# Open browser to http://localhost:8080
# Use F12 to open developer tools
```

#### Frontend Debugging
```javascript
// Add debug logging in frontend code
const DEBUG = process.env.NODE_ENV === 'development';

function debugLog(message, data) {
  if (DEBUG) {
    console.log(`[MAFA-DEBUG] ${message}`, data);
  }
}

// Usage
debugLog('Contact loaded', contact);
```

### 4. Performance Development

#### Profiling
```python
# Enable profiling in development
import cProfile
import pstats

def profile_function(func):
    def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        result = func(*args, **kwargs)
        pr.disable()
        
        stats = pstats.Stats(pr)
        stats.sort_stats('cumulative')
        stats.print_stats(10)
        
        return result
    return wrapper

# Usage
@profile_function
def expensive_operation():
    # Your code here
    pass
```

#### Performance Monitoring
```bash
# Monitor system resources
htop
iotop

# Monitor database performance
python -c "
from mafa.db.manager import DatabaseManager
db = DatabaseManager()
stats = db.get_performance_stats()
print('Database stats:', stats)
"
```

---

## Troubleshooting Development Issues

### Common Problems

#### Virtual Environment Issues
```bash
# Recreate virtual environment
rm -rf venv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Check Python path
which python
python -c "import sys; print(sys.path)"
```

#### Database Connection Issues
```bash
# Check database file permissions
ls -la data/
chmod 664 data/mafa_dev.db

# Reset database
rm data/mafa_dev.db
python -c "from mafa.db.manager import init_db; init_db()"
```

#### Frontend Build Issues
```bash
# Clear node modules and rebuild
cd dashboard
rm -rf node_modules
rm -rf dist
npm install
npm run build:dev
```

#### Docker Development Issues
```bash
# Reset Docker development environment
docker-compose -f docker-compose.dev.yml down -v
docker system prune -f
docker-compose -f docker-compose.dev.yml up -d

# Check Docker logs
docker-compose -f docker-compose.dev.yml logs -f
```

### Debug Mode Configuration
```python
# Enable debug mode in development
# api/main.py
from mafa.config.settings import get_settings

settings = get_settings()
if settings.debug:
    import debugpy
    debugpy.listen(5678)
    print("Waiting for debugger attach...")
    debugpy.wait_for_client()
```

---

## Contribution Guidelines

### Code Style Standards
- **Python**: Follow PEP 8, use Black for formatting
- **JavaScript**: Follow Airbnb style guide, use Prettier
- **CSS**: Follow BEM methodology for naming
- **Documentation**: Use clear, concise language

### Pull Request Process
1. **Fork and Branch**: Create feature branch from `develop`
2. **Implement**: Write code following style guidelines
3. **Test**: Ensure all tests pass
4. **Document**: Update documentation if needed
5. **Submit**: Create pull request with clear description
6. **Review**: Address code review feedback
7. **Merge**: After approval, merge to `develop`

### Code Review Checklist
- [ ] Code follows style guidelines
- [ ] Tests are included and passing
- [ ] Documentation is updated
- [ ] No security vulnerabilities
- [ ] Performance considerations addressed
- [ ] Error handling implemented
- [ ] Logging is appropriate

---

## Related Documentation

- [Contributing Guidelines](contributing.md) - Detailed contribution process
- [Code Style Guide](code-style.md) - Development standards
- [Documentation Guidelines](documentation-guidelines.md) - Writing documentation
- [API Integration Guide](api/integration-guide.md) - Backend integration
- [Architecture Overview](../architecture/system-overview.md) - System design

---

**Development Support**: For development-related questions, join our [Developer Discord](https://discord.gg/mafa-dev) or create an issue with the `development` label.