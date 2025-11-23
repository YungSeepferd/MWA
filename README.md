# Munich Apartment Finder Assistant (MAFA)

![CI](https://github.com/your-org/mafa/workflows/CI/badge.svg)

MAFA is a Python-based real estate scraping and notification system designed for the Munich rental market. It aggregates listings from multiple portals, stores them in a SQLite database, and sends templated application messages via Discord webhooks.

## ✨ Features

- **Advanced Contact Discovery** - Automated extraction of email addresses, phone numbers, and contact forms from property listings
- **Modular Provider Architecture** - Extensible scrapers for ImmoScout24, WG-Gesucht, and other real estate portals
- **Discord Notifications** - Send personalized application messages via Discord webhooks
- **SQLite Database** - Persistent storage with deduplication and contact management
- **Scheduled Runs** - APScheduler integration for periodic scraping and contact discovery
- **FastAPI Dashboard** - Web interface for manual runs, listing management, and contact review
- **Jinja2 Templates** - Customizable application message templates
- **Docker Support** - Complete containerization with Docker Compose
- **Comprehensive Testing** - 60%+ test coverage with detailed test suites
- **Security & Monitoring** - Input validation, health checks, and performance metrics

## 🚀 Quick Start

### Prerequisites

- Python 3.10+ 
- Docker (optional, for containerized deployment)
- Discord webhook URL (for notifications)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd mafa-munchewohnungsassistent
   ```

2. **Install Poetry dependencies**
   ```bash
   poetry install
   ```

3. **Configure the application**
   ```bash
   cp config.example.json config.json
   # Edit config.json with your settings
   ```

4. **Run the application**
   ```bash
   # Manual run
   poetry run python run.py

   # Start the dashboard
   poetry run uvicorn api.main:app --reload
   ```

### Docker Deployment

1. **Build and start services**
   ```bash
   docker-compose up -d
   ```

2. **Access the dashboard**
   - Open http://localhost:8000 in your browser

## 🔍 Contact Discovery

MAFA now includes advanced contact discovery capabilities that automatically extract contact information from property listings:

### Contact Extraction Features
- **Email Detection**: Pattern-based extraction with obfuscation handling (e.g., "user [at] domain [dot] com")
- **Phone Number Recognition**: German and international phone format support
- **Contact Form Discovery**: Automated detection of contact forms with field analysis
- **Confidence Scoring**: Multi-level confidence assessment (High/Medium/Low)
- **Contact Validation**: DNS/MX verification, syntax checking, and optional SMTP verification
- **Deduplication**: Hash-based contact deduplication across sources

### Contact Discovery Usage
```python
from mafa.contacts.extractor import ContactExtractor
from mafa.contacts.validator import ContactValidator
from mafa.contacts.storage import ContactStorage

# Extract contacts from a listing
extractor = ContactExtractor(config)
contacts, forms = await extractor.discover_contacts("https://example-listing.com")

# Validate contacts
validator = ContactValidator()
validated_contacts = await validator.validate_contacts(contacts)

# Store contacts
storage = ContactStorage(Path("data/contacts.db"))
storage.store_contacts(validated_contacts)
```

## ⚙️ Configuration

### config.json Structure

```json
{
  "personal_profile": {
    "my_full_name": "Max Mustermann",
    "my_profession": "Software Engineer",
    "my_employer": "Tech Corp",
    "net_household_income_monthly": 4500,
    "total_occupants": 2,
    "intro_paragraph": "I am a reliable tenant..."
  },
  "search_criteria": {
    "max_price": 1500,
    "min_rooms": 2,
    "zip_codes": ["80331", "80333", "80335"]
  },
  "notification": {
    "provider": "discord",
    "discord_webhook_url": "https://discord.com/api/webhooks/..."
  },
  "scrapers": ["immoscout", "wg_gesucht"],
  "contact_discovery": {
    "enabled": true,
    "confidence_threshold": "medium",
    "validation_enabled": true,
    "rate_limit_seconds": 1.0
  }
}
```

### Environment Variables

- `CONFIG_PATH` - Path to configuration file (default: config.json)
- `PYTHONPATH` - Python path for imports
- `DISCORD_WEBHOOK_URL` - Discord webhook URL (overrides config)

## 📁 Project Structure

```
mafa/
├── config/
│   ├── settings.py          # Pydantic settings model
│   └── __init__.py
├── contacts/                # Contact discovery system
│   ├── extractor.py         # Contact extraction engine
│   ├── models.py            # Contact data models
│   ├── storage.py           # SQLite contact storage
│   ├── validator.py         # Contact validation utilities
│   └── __init__.py
├── crawler/                 # Legacy crawler modules (deprecated)
├── db/
│   ├── manager.py           # SQLite repository
│   └── __init__.py
├── notifier/
│   ├── discord.py           # Discord webhook notifier
│   └── telegram.py          # Legacy Telegram notifier
├── orchestrator/
│   ├── __init__.py          # Main orchestration logic
├── providers/
│   ├── base.py              # Provider protocol
│   ├── immoscout.py         # ImmoScout24 provider
│   ├── wg_gesucht.py        # WG-Gesucht provider
│   └── __init__.py          # Provider registry
├── scheduler/
│   ├── scheduler.py         # APScheduler integration
│   └── __init__.py
├── templates/
│   ├── apply_short.jinja2   # Short application template
│   ├── apply_detailed.jinja2 # Detailed application template
│   └── __init__.py          # Jinja2 environment
├── dashboard/               # Legacy dashboard (deprecated)
├── security.py              # Security validation utilities
├── exceptions.py            # Custom exception hierarchy
├── monitoring.py            # Health checks and metrics
└── driver.py                # Selenium driver wrapper

api/
└── main.py                  # FastAPI dashboard

tests/
├── test_contacts.py         # Contact discovery tests (706 lines)
├── test_configuration.py    # Configuration validation tests
├── test_db_manager.py       # Database tests
├── test_exceptions.py       # Exception handling tests
├── test_providers.py        # Provider tests
└── test_security.py         # Security validation tests

Dockerfile                   # Container definition
docker-compose.yml           # Service orchestration
.github/workflows/ci.yml     # GitHub Actions CI
ROADMAP.md                   # Production deployment roadmap
```

## 🛠️ Development

### Running Tests

```bash
poetry run pytest tests/ -v
```

### Code Quality

```bash
poetry run black .
poetry run isort .
poetry run flake8 .
```

### Adding New Providers

1. **Create provider class**
   ```python
   from mafa.providers.base import BaseProvider
   
   class MyProvider(BaseProvider):
       def scrape(self) -> List[Dict]:
           # Implementation here
           pass
   ```

2. **Register provider**
   ```python
   # In mafa/providers/__init__.py
   PROVIDER_REGISTRY["my_provider"] = MyProvider
   ```

3. **Add to config**
   ```json
   {
     "scrapers": ["immoscout", "my_provider"]
   }
   ```

## 📊 Scheduler

The scheduler uses APScheduler to run scraper jobs:

- **Periodic Jobs** - Runs every 30 minutes by default
- **Manual Jobs** - Triggered via FastAPI dashboard
- **Configuration** - Modify `mafa/scheduler/scheduler.py` for custom schedules

## 📧 Templates

Customize application messages using Jinja2 templates:

- **Variables Available**: `listing`, `settings.personal_profile.*`
- **Default Templates**: 
  - `apply_short.jinja2` - Concise application
  - `apply_detailed.jinja2` - Detailed application

## 🐳 Docker Services

### mafa-app
- FastAPI dashboard on port 8000
- Interactive web interface

### mafa-scheduler
- Background scheduler service
- Periodic scraping runs

## 📚 Documentation & Quality Assurance

### Comprehensive Documentation Suite
MAFA includes a complete documentation system with automated validation and quality assurance tools.

#### 🚀 Getting Started
- **[Installation Guide](docs/getting-started/installation.md)** - Step-by-step installation instructions
- **[Quick Start Guide](docs/getting-started/quick-start.md)** - 5-minute setup to get started
- **[Configuration Reference](docs/getting-started/configuration.md)** - Complete configuration options

#### 👥 User Guide
- **[System Overview](docs/user-guide/overview.md)** - Complete overview of MAFA capabilities
- **[Setup Wizard Guide](docs/user-guide/setup-wizard.md)** - Guided setup process
- **[Dashboard Manual](docs/user-guide/dashboard.md)** - Using the web dashboard effectively
- **[User Workflows](docs/user-guide/workflows/)** - Detailed user interaction patterns
- **[Troubleshooting Guide](docs/user-guide/troubleshooting.md)** - Common issues and solutions

#### 🛠️ Developer Guide
- **[Development Setup](docs/developer-guide/development-setup.md)** - Setting up development environment
- **[Contributing Guidelines](docs/developer-guide/contributing.md)** - How to contribute to the project
- **[Code Style Guide](docs/developer-guide/code-style.md)** - Coding standards and best practices
- **[API Integration Guide](docs/developer-guide/api/integration-guide.md)** - MAFA API usage and integration
- **[Testing Guidelines](docs/developer-guide/testing/)** - Comprehensive testing strategies and scenarios
- **[Documentation Standards](docs/developer-guide/documentation-guidelines.md)** - Documentation guidelines and best practices

#### 🏗️ Architecture Documentation
- **[System Overview](docs/architecture/system-overview.md)** - High-level system architecture
- **[Repository Structure](docs/architecture/repository-structure.md)** - Detailed codebase organization
- **[Database Schema](docs/architecture/database-schema.md)** - Database design and relationships
- **[Data Models](docs/architecture/data-models.md)** - Entity relationships and validation
- **[Contact Discovery System](docs/architecture/contact-discovery.md)** - Technical implementation details

#### ⚙️ Operations Manual
- **[Deployment Guide](docs/operations/deployment.md)** - Production deployment procedures
- **[Monitoring & Observability](docs/operations/monitoring.md)** - System monitoring and alerting
- **[Backup & Restore](docs/operations/backup-restore.md)** - Data backup and recovery procedures
- **[Security Best Practices](docs/operations/security.md)** - Security configuration and monitoring

#### 📋 Project Management
- **[Development Plan](docs/project/development-plan.md)** - Current development roadmap and planning
- **[Roadmap](docs/project/roadmap.md)** - Long-term project vision and milestones
- **[Changelog](docs/project/changelog.md)** - Version history and changes
- **[Release Notes](docs/project/release-notes.md)** - Detailed release information
- **[Governance](docs/project/governance.md)** - Project management and decision-making
- **[Implementation Details](docs/project/implementation/)** - Sprint planning and execution details
- **[Quality Assurance Reports](docs/project/qa-reports/)** - Comprehensive testing results and analysis

### 📖 Documentation Templates & Examples
- **[Guide Template](docs/templates/guide-template.md)** - Standard template for documentation guides
- **[API Reference Template](docs/templates/api-reference-template.md)** - Template for API documentation
- **[Release Notes Template](docs/templates/release-notes-template.md)** - Template for release documentation
- **[Markdown Formatting Examples](docs/examples/markdown-examples.md)** - Comprehensive formatting reference

### 🔧 Documentation Quality Assurance Tools

#### Validation Scripts
Run comprehensive documentation quality checks:

```bash
# Comprehensive documentation validation
./scripts/validate-docs.sh

# Check for broken links
./scripts/check-links.sh

# Validate documentation structure
./scripts/validate-structure.sh

# Lint markdown files
./scripts/lint-docs.sh

# Validate document metadata
./scripts/validate-metadata.sh
```

#### Maintenance Tools
- **Update Documentation Indexes**: `./scripts/update-docs-index.sh`
- **Generate Documentation Statistics**: `./scripts/docs-stats.sh`
- **Metadata Validation**: `./scripts/validate-metadata.sh`

#### GitHub Actions Workflow
- **Automated Documentation Testing**: Triggers on documentation changes
- **Link Validation**: Checks internal and external links
- **Structure Validation**: Ensures documentation organization
- **Quality Reports**: Generates comprehensive documentation reports
- **PR Comments**: Automatic feedback on documentation changes

#### Pre-commit Hooks
Documentation quality checks run automatically on commits:

```bash
# Install pre-commit hooks
pre-commit install

# Run documentation checks manually
pre-commit run docs-structure-check
pre-commit run docs-links-check
pre-commit run docs-lint
```

### 📊 Documentation Coverage Analysis
Monitor documentation completeness and quality:

```bash
# Generate documentation statistics
./scripts/docs-stats.sh --detailed

# Check documentation coverage
./scripts/validate-structure.sh --tolerance strict

# Update all documentation indexes
./scripts/update-docs-index.sh
```

### 🔄 CI/CD Integration
Documentation validation is integrated into the development workflow:

- **Pull Request Validation**: Automatic documentation checks on PRs
- **Schedule Maintenance**: Weekly documentation quality reports
- **Branch Protection**: Documentation standards enforced via GitHub Actions
- **Artifact Generation**: Documentation reports available as workflow artifacts

### 📝 Documentation Standards
All documentation follows strict quality standards:

- **Metadata Requirements**: Consistent frontmatter across all documents
- **Link Validation**: All internal links verified automatically
- **Structure Compliance**: Documentation organization follows established patterns
- **Markdown Quality**: Consistent formatting and style guidelines
- **Cross-references**: Proper internal linking and navigation

### 🎯 Quick Documentation Access

#### For New Users
1. **[Quick Start Guide](docs/getting-started/quick-start.md)** - Get started in 5 minutes
2. **[User Overview](docs/user-guide/overview.md)** - Understand what MAFA does
3. **[Configuration Guide](docs/getting-started/configuration.md)** - Set up your instance

#### For Developers
1. **[Development Setup](docs/developer-guide/development-setup.md)** - Set up development environment
2. **[Contributing Guidelines](docs/developer-guide/contributing.md)** - How to contribute effectively
3. **[API Integration](docs/developer-guide/api/integration-guide.md)** - Use MAFA APIs programmatically

#### For Operators
1. **[Deployment Guide](docs/operations/deployment.md)** - Production deployment
2. **[Monitoring Guide](docs/operations/monitoring.md)** - System observability
3. **[Security Guidelines](docs/operations/security.md)** - Security best practices

#### For Project Managers
1. **[Development Plan](docs/project/development-plan.md)** - Current sprint details
2. **[Roadmap](docs/project/roadmap.md)** - Long-term vision
3. **[QA Reports](docs/project/qa-reports/)** - Quality assurance metrics

### 📞 Documentation Support
- **Documentation Issues**: [Report documentation problems](https://github.com/your-org/mafa-docs/issues)
- **Template Requests**: Request new documentation templates
- **Style Guide Questions**: Refer to [Documentation Guidelines](docs/developer-guide/documentation-guidelines.md)
- **Quality Feedback**: Use automated validation tools for immediate feedback

### Legacy Documentation (Deprecated)
The following sections have been moved to dedicated documentation files:
- Configuration (see [Configuration Reference](docs/getting-started/configuration.md))
- Contact Discovery (see [Contact Discovery System](docs/architecture/contact-discovery.md))
- Development guidelines (see [Developer Guide](docs/developer-guide/))

## 🤝 Contributing

1. **Read the Documentation**: Review our [Contributing Guidelines](docs/developer-guide/contributing.md)
2. Fork the repository
3. Create a feature branch (`git checkout -b feature/amazing-feature`)
4. Make changes and add tests
5. Ensure CI passes (`poetry run pytest`)
6. Update documentation as needed
7. Commit changes (`git commit -m 'Add amazing feature'`)
8. Push to branch (`git push origin feature/amazing-feature`)
9. Open a Pull Request

For detailed contribution guidance, see our [Developer Guide](docs/developer-guide/contributing.md).

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make changes and add tests
4. Ensure CI passes (`poetry run pytest`)
5. Commit changes (`git commit -m 'Add amazing feature'`)
6. Push to branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔧 Troubleshooting

### Common Issues

**Selenium WebDriver Issues**
- Ensure Chrome is installed in Docker image
- Check webdriver-manager configuration

**Database Lock Errors**
- Run only one instance of the application
- Check for proper connection handling

**Discord Webhook Failures**
- Verify webhook URL is correct
- Check Discord server permissions

## 📞 Support

For support and questions:
- Open an issue on GitHub
- Check existing issues for solutions
- Review the documentation in this README

## 🤖 Roo Developer Quickstart

This section provides comprehensive guidance for developers using Roo (AI coding assistants) to work with the MAFA project.

### Roo Mode Configuration

MAFA includes a specialized **MAFA QA Tester & Roadmap Planner** mode for Roo that provides:

- **Systematic Repository Analysis** - Automatic mapping of project structure and dependencies
- **Comprehensive QA Guidance** - Test case generation, edge condition identification, security analysis
- **Architectural Consistency Checks** - Pattern validation, dependency flow analysis, design pattern assessment
- **Structured Roadmap Planning** - Prioritized development phases with risk assessment and rollback plans

### Enabling Roo Mode

1. **Copy the Roo configuration**:
   ```bash
   cp mcp.example.json mcp.json
   ```

2. **Configure your Roo client** to use the MAFA mode:
   - Mode file: `.roo/modes/mafa-qa-tester-roadmap-planner.json`
   - System prompt: `.roo/system-prompt-mafa-qa-tester.md`

3. **Available Roo Commands**:
   ```bash
   /run-dev              # Start development environment
   /run-tests            # Run comprehensive test suite
   /run-scraper          # Test scraper in dry-run mode
   /analyze-code         # Perform code analysis
   /generate-roadmap    # Create development roadmap
   /health-check         # Run system health checks
   ```

### Roo Development Workflow

#### 1. Initial Repository Analysis
When starting work, Roo will automatically:
- Map the current repository structure
- Identify dependencies and configuration
- Analyze code quality and security
- Generate a comprehensive repo map

#### 2. Quality Assurance Process
Roo provides systematic QA guidance:
- **Test Case Generation**: Creates tests that would break if bugs exist
- **Edge Condition Analysis**: Identifies failure modes and boundary conditions
- **Security Assessment**: Reviews input validation and potential vulnerabilities
- **Performance Analysis**: Identifies bottlenecks and optimization opportunities

#### 3. Architectural Guidance
Roo ensures architectural consistency:
- **Pattern Validation**: Checks adherence to established design patterns
- **Dependency Analysis**: Identifies circular dependencies and coupling issues
- **Modularity Review**: Assesses separation of concerns and module boundaries
- **Interface Consistency**: Validates protocol implementations and API contracts

#### 4. Roadmap Planning
Roo generates structured development roadmaps:
- **Critical Fixes**: Immediate issues affecting system stability
- **Stability Improvements**: Reliability and maintainability enhancements
- **Architectural Upgrades**: Strategic improvements for scalability
- **Feature Extensions**: New capabilities and integrations

### Development Environment Setup

#### Quick Start with Docker
```bash
# Start development environment
./scripts/docker-dev.sh start

# Access services
# FastAPI Dashboard: http://localhost:8000
# Streamlit Dashboard: http://localhost:3001
# MCP Shim: http://localhost:3000
```

#### Local Development
```bash
# Install dependencies
poetry install

# Run tests
./scripts/run-tests.sh

# Test scraper in dry-run
./scripts/run-scraper-dryrun.sh

# Analyze code quality
./scripts/analyze-code.sh

# Generate roadmap
./scripts/generate-roadmap.sh
```

### Roo-Specific Features

#### Dry-Run Mode
MAFA includes comprehensive dry-run functionality:
```bash
# Test without database persistence or notifications
poetry run python run.py --dry-run

# Roo can validate dry-run behavior
/analyze-code --scope=dry-run
```

#### MCP Integration
MAFA provides Model Context Protocol (MCP) servers for enhanced AI interaction:
- **Health Monitor**: System health checks and diagnostics
- **Code Analyzer**: Static analysis and improvement suggestions
- **Documentation Server**: Context-aware documentation retrieval

#### Automated Quality Gates
Pre-commit hooks ensure code quality:
```bash
# Install pre-commit hooks
pre-commit install

# Run all quality checks
pre-commit run --all-files
```

### Roo Development Best Practices

#### 1. Systematic Approach
- Always start with repository analysis
- Use Roo's structured QA guidance
- Follow the recommended development phases
- Validate changes with comprehensive testing

#### 2. Risk Management
- Every proposal includes risk assessment
- Rollback plans are required for significant changes
- Testing strategies are specified upfront
- Security implications are considered

#### 3. Documentation Standards
- All changes include documentation updates
- API documentation is kept current
- Architecture decisions are recorded
- Troubleshooting guides are maintained

#### 4. Code Quality
- Follow established coding patterns
- Maintain test coverage above 70%
- Address all security warnings
- Optimize for performance and maintainability

### Roo Command Examples

#### Repository Analysis
```bash
# Full repository analysis
/analyze-code --scope=full

# Security-focused analysis
/analyze-code --scope=security

# Performance analysis
/analyze-code --scope=performance
```

#### Testing and Validation
```bash
# Run all tests
/run-tests

# Run specific test patterns
/run-tests test_provider

# Skip linting for quick checks
/run-tests --fast
```

#### Development Planning
```bash
# Generate current phase roadmap
/generate-roadmap current

# Plan next development phase
/generate-roadmap next

# Long-term strategic planning
/generate-roadmap future
```

#### System Health
```bash
# Comprehensive health check
/health-check

# Basic health check only
/health-check basic

# Security-focused health check
/health-check security
```

### Integration with Development Tools

#### IDE Integration
- **VS Code**: Use Roo extension with MAFA mode
- **PyCharm**: Configure Roo as external tool
- **Vim/Neovim**: Use Roo CLI integration

#### CI/CD Integration
- **GitHub Actions**: Automated testing and quality checks
- **Docker**: Containerized development environment
- **MCP**: Enhanced AI-assisted development

#### Monitoring and Logging
- **Structured Logging**: Loguru-based logging with JSON output
- **Health Checks**: Comprehensive system diagnostics
- **Performance Metrics**: Resource usage and response time tracking

### Troubleshooting Roo Integration

#### Common Issues
1. **Mode Not Found**: Ensure `.roo/` directory is properly configured
2. **MCP Connection**: Check MCP server configuration and network access
3. **Permission Errors**: Verify file permissions in `.roo/modes/`
4. **Command Not Found**: Ensure scripts are executable (`chmod +x scripts/*.sh`)

#### Debug Mode
```bash
# Enable debug logging
export MAFA_LOG_LEVEL=DEBUG

# Run with verbose output
/run-dev --verbose

# Check system health
/health-check --detailed
```

### Contributing with Roo

When contributing to MAFA using Roo:

1. **Start Analysis**: Let Roo analyze the current state
2. **Plan Changes**: Use Roo's roadmap planning for structured approach
3. **Implement**: Follow Roo's QA guidance for implementation
4. **Test**: Use Roo's test generation for comprehensive coverage
5. **Document**: Update documentation as guided by Roo
6. **Validate**: Run health checks and quality gates

### Advanced Roo Features

#### Custom Prompts
Create custom prompts for specific tasks:
```bash
# Create custom analysis prompt
echo "Focus on contact discovery pipeline" > .roo/custom-prompt.txt
```

#### Integration Scripts
Automate common Roo workflows:
```bash
# Full development cycle
./scripts/roo-dev-cycle.sh analyze implement test validate
```

#### Performance Optimization
Roo can help optimize performance:
```bash
# Analyze performance bottlenecks
/analyze-code --scope=performance

# Generate optimization roadmap
/generate-roadmap --focus=performance
```

## 🚀 Selenium Scraping Primer

MAFA uses Selenium with Chrome for web scraping real estate listings. Here's a quick primer on the scraping architecture:

### SeleniumDriver Class
The [`mafa/driver.py`](mafa/driver.py) provides a robust Selenium wrapper with:

```python
from mafa.driver import SeleniumDriver

# Basic usage
with SeleniumDriver(headless=True, timeout=30) as driver:
    driver.get("https://example.com")
    
    # Use WebDriverWait helper methods
    element = driver.wait_for_element(By.CSS_SELECTOR, ".listing", timeout=10)
    elements = driver.wait_for_elements(By.CLASS_NAME, "result-item", timeout=5)
    clickable_element = driver.wait_for_element_clickable(By.ID, "submit-btn", timeout=3)
```

### WebDriverWait Helper Methods
- **`wait_for_element()`** - Wait for single element with timeout
- **`wait_for_elements()`** - Wait for multiple elements (returns empty list on timeout)
- **`wait_for_element_clickable()`** - Wait for element to be clickable

### Provider Architecture
Providers inherit from `BaseProvider` protocol and implement the `scrape()` method:

```python
from mafa.providers.base import BaseProvider

class MyProvider(BaseProvider):
    def scrape(self) -> List[Dict]:
        # Implementation using SeleniumDriver
        pass
```

### Best Practices
1. **Use WebDriverWait** instead of direct `find_elements()` calls
2. **Implement retry logic** with exponential backoff
3. **Use proper logging** instead of print statements
4. **Handle timeouts gracefully** with appropriate error messages
5. **Validate extracted data** before returning listings

### Error Handling
- `SeleniumDriverError` for driver-related issues
- `TimeoutException` for element wait timeouts
- `ProviderError` for provider-specific failures

---

**Note**: This project is designed for educational purposes and personal use. Please respect the terms of service of the real estate websites you scrape and use rate limiting appropriately.

**Roo Integration**: The MAFA project is optimized for AI-assisted development with comprehensive Roo mode support, enabling systematic, high-quality code development and maintenance.