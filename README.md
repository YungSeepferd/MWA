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

## 🤝 Contributing

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

---

**Note**: This project is designed for educational purposes and personal use. Please respect the terms of service of the real estate websites you scrape and use rate limiting appropriately.