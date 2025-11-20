# Configuration Reference

## Overview
Comprehensive guide to configuring MAFA for optimal apartment search performance. This reference covers all configuration options, from basic settings to advanced customization.

---

**Last Updated:** November 19, 2025  
**Version:** 1.0.0  
**Maintainer:** MAFA Development Team  
**Estimated Reading Time:** 15-20 minutes

---

## Configuration File Structure

MAFA uses JSON configuration files with the following structure:

```json
{
  "personal_profile": { ... },
  "search_criteria": { ... },
  "notification_settings": { ... },
  "scraper_config": { ... },
  "contact_discovery": { ... },
  "storage_config": { ... },
  "security_settings": { ... }
}
```

---

## Personal Profile Configuration

### Required Settings
Configure your personal information for apartment applications:

```json
{
  "personal_profile": {
    "full_name": "Your Full Name",
    "email_address": "your.email@example.com",
    "phone_number": "+49 123 456789",
    "occupation": "Software Developer",
    "employer": "Tech Company GmbH",
    "monthly_income": 3500,
    "number_of_occupants": 1,
    "application_introduction": "I am a reliable tenant looking for a modern apartment in Munich...",
    "preferred_contact_method": "email"
  }
}
```

### Field Descriptions
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `full_name` | string | ✅ | Legal name as it appears on applications |
| `email_address` | string | ✅ | Primary email for notifications |
| `phone_number` | string | ❌ | International format (e.g., +49 123 456789) |
| `occupation` | string | ✅ | Current profession |
| `employer` | string | ❌ | Current employer name |
| `monthly_income` | integer | ✅ | Gross monthly income in EUR |
| `number_of_occupants` | integer | ✅ | Total people who will live in apartment |
| `application_introduction` | string | ❌ | Personal introduction paragraph |
| `preferred_contact_method` | string | ✅ | "email", "phone", or "contact_form" |

---

## Search Criteria Configuration

### Basic Search Settings
```json
{
  "search_criteria": {
    "price_range": {
      "minimum": 800,
      "maximum": 1500
    },
    "room_requirements": {
      "minimum_rooms": 2,
      "maximum_rooms": 3,
      "prefer_open_plan": false
    },
    "location_preferences": {
      "target_districts": [
        "Schwabing",
        "Maxvorstadt",
        "Bogenhausen",
        "Glockenbachviertel"
      ],
      "avoid_districts": [
        "Moosach",
        "Neuperlach"
      ],
      "minimum_public_transport_rating": 3,
      "preferred_street_types": ["quiet", "tree_lined"],
      "avoid_busy_streets": true
    },
    "apartment_requirements": {
      "minimum_size_sqm": 45,
      "furnished_preference": "unfurnished",
      "balcony_required": true,
      "pet_friendly": true,
      "parking_required": false,
      "elevator_required": false,
      "floor_preference": "any"
    },
    "move_in_timeline": {
      "earliest_date": "2025-02-01",
      "latest_date": "2025-04-30",
      "flexibility_weeks": 2
    }
  }
}
```

### Advanced Search Options
```json
{
  "search_criteria": {
    "filters": {
      "property_types": ["apartment", "loft"],
      "building_age": {
        "minimum_year": 1950,
        "maximum_year": 2025
      },
      "energy_efficiency": {
        "minimum_rating": "C",
        "avoid_poor_ratings": true
      },
      "neighborhood_features": {
        "supermarket_distance_max": 500,
        "restaurant_density_min": 3,
        "park_nearby": true,
        "nightlife_access": "moderate"
      }
    },
    "exclusions": {
      "exclude_listings_with": [
        "smoking_allowed",
        "partying_allowed",
        "short_term_rental"
      ],
      "exclude_property_types": ["shared_room", "hostel"],
      "minimum_listing_age_days": 0
    }
  }
}
```

---

## Notification Settings

### Email Notifications
```json
{
  "notification_settings": {
    "email": {
      "enabled": true,
      "smtp_server": "smtp.gmail.com",
      "smtp_port": 587,
      "sender_email": "notifications@mafa.app",
      "sender_password": "your-app-password",
      "use_tls": true,
      "digest_frequency": "immediate",
      "quiet_hours": {
        "enabled": true,
        "start_time": "22:00",
        "end_time": "08:00",
        "timezone": "Europe/Berlin"
      }
    }
  }
}
```

### Discord Integration
```json
{
  "notification_settings": {
    "discord": {
      "enabled": true,
      "webhook_url": "https://discord.com/api/webhooks/YOUR_WEBHOOK",
      "channel_mentions": false,
      "include_listing_images": true,
      "embed_style": "detailed"
    }
  }
}
```

### Telegram Integration
```json
{
  "notification_settings": {
    "telegram": {
      "enabled": true,
      "bot_token": "123456789:ABCdefGHIjklMNOpqrsTUVwxyz",
      "chat_id": "123456789",
      "send_photos": true,
      "parse_mode": "HTML"
    }
  }
}
```

### Notification Rules
```json
{
  "notification_settings": {
    "rules": {
      "new_listing": {
        "minimum_confidence": 0.7,
        "immediate_notification": true,
        "channels": ["email", "discord"]
      },
      "contact_update": {
        "minimum_confidence": 0.5,
        "immediate_notification": false,
        "channels": ["email"]
      },
      "search_status": {
        "enabled": true,
        "channels": ["email"]
      },
      "daily_digest": {
        "enabled": true,
        "time": "09:00",
        "include_statistics": true,
        "channels": ["email"]
      }
    }
  }
}
```

---

## Scraper Configuration

### Provider Settings
```json
{
  "scraper_config": {
    "providers": {
      "immoscout": {
        "enabled": true,
        "priority": 1,
        "max_results_per_search": 50,
        "search_delay_seconds": 2,
        "rate_limit_per_hour": 100
      },
      "wg_gesucht": {
        "enabled": true,
        "priority": 2,
        "max_results_per_search": 30,
        "search_delay_seconds": 3,
        "rate_limit_per_hour": 80
      }
    },
    "schedule": {
      "enabled": true,
      "interval_minutes": 120,
      "cron_expression": "*/120 * * * *",
      "max_concurrent_searches": 2,
      "retry_attempts": 3,
      "retry_delay_seconds": 30
    },
    "request_settings": {
      "user_agent": "Mozilla/5.0 (compatible; MAFA/1.0)",
      "timeout_seconds": 30,
      "max_redirects": 5,
      "enable_cookies": true,
      "proxy_settings": {
        "enabled": false,
        "proxy_url": null,
        "username": null,
        "password": null
      }
    }
  }
}
```

### Advanced Scraper Options
```json
{
  "scraper_config": {
    "browser_settings": {
      "headless_mode": true,
      "window_size": "1920x1080",
      "disable_images": false,
      "disable_javascript": false,
      "disable_css": false,
      "page_load_timeout": 30,
      "implicit_wait": 10
    },
    "anti_detection": {
      "randomize_user_agent": true,
      "randomize_delays": true,
      "use_session_rotation": true,
      "simulate_human_behavior": true
    },
    "output_filters": {
      "exclude_duplicates": true,
      "minimum_contact_confidence": 0.5,
      "maximum_age_days": 7,
      "require_phone_or_email": true
    }
  }
}
```

---

## Contact Discovery Configuration

### Extraction Settings
```json
{
  "contact_discovery": {
    "extraction_methods": {
      "email_patterns": {
        "enabled": true,
        "pattern_types": ["standard", "obfuscated", "base64", "javascript"],
        "confidence_threshold": 0.7
      },
      "phone_patterns": {
        "enabled": true,
        "country_code": "+49",
        "validate_format": true,
        "extract_mobile_preferred": true
      },
      "contact_forms": {
        "enabled": true,
        "form_detection_threshold": 0.8,
        "extract_field_labels": true,
        "prefer_contact_methods": ["email", "phone"]
      },
      "ocr_extraction": {
        "enabled": true,
        "confidence_threshold": 0.6,
        "languages": ["de", "en"],
        "image_preprocessing": true
      }
    },
    "validation_settings": {
      "email_validation": {
        "enabled": true,
        "check_smtp": false,
        "require_domain": ["gmail.com", "web.de", "gmx.net"]
      },
      "phone_validation": {
        "enabled": true,
        "check_format": true,
        "german_format_required": true
      }
    },
    "scoring_settings": {
      "confidence_calculation": {
        "source_reliability": 0.3,
        "extraction_confidence": 0.4,
        "validation_score": 0.3
      },
      "minimum_confidence_for_notification": 0.7,
      "auto_approve_threshold": 0.9
    }
  }
}
```

---

## Storage Configuration

### Database Settings
```json
{
  "storage_config": {
    "database": {
      "url": "sqlite:///data/mafa.db",
      "pool_size": 10,
      "max_overflow": 20,
      "echo": false,
      "pool_pre_ping": true
    },
    "backup": {
      "enabled": true,
      "interval_hours": 24,
      "backup_directory": "backups/",
      "max_backup_files": 30,
      "compress_backups": true,
      "backup_retention_days": 90
    },
    "cleanup": {
      "enabled": true,
      "old_listings_retention_days": 30,
      "failed_contact_attempts_retention_days": 7,
      "log_retention_days": 30
    },
    "indexing": {
      "enable_full_text_search": true,
      "contact_search_index": true,
      "listing_search_index": true,
      "automatic_optimization": true
    }
  }
}
```

---

## Security Settings

### Authentication & Authorization
```json
{
  "security_settings": {
    "authentication": {
      "enabled": true,
      "method": "jwt",
      "secret_key": "your-secret-key-here",
      "algorithm": "HS256",
      "access_token_expire_minutes": 30,
      "refresh_token_expire_days": 7
    },
    "rate_limiting": {
      "enabled": true,
      "requests_per_minute": 60,
      "burst_limit": 10,
      "ip_whitelist": [],
      "api_key_required": false
    },
    "data_protection": {
      "encrypt_sensitive_data": true,
      "hash_passwords": true,
      "secure_cookies": true,
      "https_only": false,
      "cors_origins": ["http://localhost:3000"],
      "allowed_hosts": ["localhost", "127.0.0.1"]
    }
  }
}
```

---

## Environment-Specific Configurations

### Development Configuration
```json
{
  "environment": "development",
  "debug": true,
  "logging": {
    "level": "DEBUG",
    "format": "detailed",
    "file": "logs/mafa-dev.log"
  },
  "database": {
    "url": "sqlite:///data/mafa-dev.db",
    "echo": true
  },
  "scraper_config": {
    "browser_settings": {
      "headless_mode": false,
      "slow_mo": 500
    }
  }
}
```

### Production Configuration
```json
{
  "environment": "production",
  "debug": false,
  "logging": {
    "level": "INFO",
    "format": "json",
    "file": "logs/mafa.log",
    "max_size_mb": 100,
    "backup_count": 10
  },
  "database": {
    "url": "postgresql://user:pass@localhost/mafa",
    "pool_size": 20,
    "max_overflow": 30
  },
  "security_settings": {
    "https_only": true,
    "secure_cookies": true
  }
}
```

---

## Configuration Validation

### Schema Validation
Use the built-in validation to check your configuration:

```bash
# Validate current configuration
curl -X POST http://localhost:8000/api/config/validate \
  -H "Content-Type: application/json" \
  -d @config.json

# Expected response:
{
  "valid": true,
  "errors": [],
  "warnings": [
    "Consider setting a shorter backup interval for production"
  ]
}
```

### Configuration Sections Validation
| Section | Required Fields | Optional Fields |
|---------|----------------|-----------------|
| `personal_profile` | full_name, email_address, occupation, monthly_income, number_of_occupants | phone_number, employer, application_introduction |
| `search_criteria` | price_range.maximum, room_requirements.minimum_rooms, location_preferences.target_districts | All other fields |
| `notification_settings` | At least one enabled notification method | quiet_hours, rules |
| `scraper_config` | At least one enabled provider | schedule, browser_settings |
| `contact_discovery` | extraction_methods | validation_settings, scoring_settings |
| `storage_config` | database.url | backup, cleanup, indexing |
| `security_settings` | authentication.enabled | rate_limiting, data_protection |

---

## Configuration Best Practices

### Security
- ✅ Use environment variables for sensitive data
- ✅ Enable HTTPS in production
- ✅ Regularly rotate API keys and tokens
- ✅ Enable rate limiting
- ✅ Use strong secret keys

### Performance
- ✅ Set appropriate rate limits for scrapers
- ✅ Configure database connection pooling
- ✅ Enable database indexing
- ✅ Use appropriate cleanup schedules

### Reliability
- ✅ Enable backup functionality
- ✅ Set up monitoring and alerting
- ✅ Configure retry mechanisms
- ✅ Use quiet hours for notifications

### User Experience
- ✅ Start with conservative settings
- ✅ Gradually optimize based on results
- ✅ Test notification channels
- ✅ Monitor contact quality

---

## Environment Variables

MAFA supports environment variables for sensitive configuration:

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost/mafa

# Email
SMTP_PASSWORD=your-email-password
SENDER_EMAIL=noreply@mafa.app

# Telegram
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz

# Discord
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK

# Security
SECRET_KEY=your-super-secret-key
JWT_SECRET_KEY=your-jwt-secret

# Redis
REDIS_URL=redis://localhost:6379

# Proxy
HTTP_PROXY=http://proxy.company.com:8080
HTTPS_PROXY=https://proxy.company.com:8080
```

---

## Troubleshooting Configuration

### Common Configuration Issues

#### 1. Invalid JSON Format
```bash
# Validate JSON syntax
python -m json.tool config.json

# Or use online JSON validators
```

#### 2. Missing Required Fields
```bash
# Check validation results
curl -X POST http://localhost:8000/api/config/validate
```

#### 3. Invalid Email/Telegram Settings
```bash
# Test notification channels
curl -X POST http://localhost:8000/api/config/test-notifications
```

#### 4. Database Connection Issues
```bash
# Test database connection
curl -X GET http://localhost:8000/api/system/health
```

### Configuration Reset
If configuration becomes corrupted:

```bash
# Reset to defaults
cp config.example.json config.json

# Or use API reset
curl -X POST http://localhost:8000/api/config/reset
```

---

## Related Documentation

- [Installation Guide](./installation.md) - Setup and installation
- [Quick Start Guide](./quick-start.md) - Get started in 5 minutes
- [User Guide Overview](../user-guide/overview.md) - Complete user documentation
- [API Integration](../developer-guide/api/integration-guide.md) - Backend integration
- [Operations Guide](../operations/deployment.md) - Production deployment

---

**Configuration Support**: For help with configuration, see our [Configuration FAQ](https://github.com/your-org/mafa/wiki/Configuration-FAQ) or create an issue in the repository.