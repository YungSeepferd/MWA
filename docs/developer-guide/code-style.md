# Code Style Guide

## Overview
This document defines the coding standards and style guidelines for the MAFA project. Following these guidelines ensures consistent, readable, and maintainable code across all contributors.

---

**Last Updated:** November 19, 2025  
**Version:** 1.0.0  
**Maintainer:** MAFA Development Team  
**Estimated Reading Time:** 15-20 minutes

---

## General Principles

### Code Quality Goals
- **Readability**: Code should be self-documenting and easy to understand
- **Consistency**: Uniform style across the entire codebase
- **Maintainability**: Code should be easy to modify and extend
- **Reliability**: Code should be robust and handle edge cases
- **Performance**: Consider efficiency without sacrificing readability

### Core Guidelines
- **Explicit is better than implicit**
- **Simple is better than complex**
- **Complex is better than complicated**
- **Flat is better than nested**
- **Sparse is better than dense**

---

## Python Code Standards

### PEP 8 Compliance
MAFA follows Python PEP 8 style guidelines with the following exceptions:

#### Line Length
```python
# Maximum line length: 88 characters (Black default)
long_variable_name = some_function_call(
    parameter_one, parameter_two, parameter_three,
    parameter_four, parameter_five, parameter_six
)
```

#### Import Organization
```python
# Standard library imports
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

# Third-party imports
import requests
import pandas as pd
from fastapi import FastAPI, HTTPException

# Local imports
from mafa.config import settings
from mafa.db.models import Contact
from .exceptions import MAFAException
```

#### String Quotes
```python
# Use double quotes for strings
name = "Max Mustermann"
message = "Welcome to MAFA"

# Use single quotes for characters
letter = 'a'

# Use triple quotes for docstrings and multi-line strings
docstring = """
This is a multi-line string
that describes something important.
"""
```

### Type Annotations

#### Required Type Hints
```python
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass

def process_contacts(
    contacts: List[Dict[str, Any]], 
    settings: Optional[Dict[str, str]] = None
) -> List[Contact]:
    """Process contact data from apartment listings.
    
    Args:
        contacts: List of raw contact dictionaries
        settings: Optional processing settings
        
    Returns:
        List of processed Contact objects
        
    Raises:
        ValueError: If contacts parameter is invalid
    """
    if not contacts:
        raise ValueError("Contacts list cannot be empty")
    
    processed_contacts = []
    for contact_data in contacts:
        try:
            contact = Contact.from_dict(contact_data)
            processed_contacts.append(contact)
        except Exception as e:
            logger.warning(f"Failed to process contact: {e}")
    
    return processed_contacts
```

#### Generic Type Usage
```python
# Good
from typing import Generic, TypeVar

T = TypeVar('T')

class BaseService(Generic[T]):
    def __init__(self, repository: T) -> None:
        self.repository = repository
    
    def get_all(self) -> List[T]:
        return self.repository.find_all()

# Bad - too generic
def process_data(data):
    return [item for item in data if item]
```

### Code Structure

#### Class Organization
```python
from dataclasses import dataclass
from typing import Optional
import logging

logger = logging.getLogger(__name__)


@dataclass
class ContactInfo:
    """Contact information extracted from listings."""
    email: str
    phone: Optional[str] = None
    confidence: float = 0.0
    
    def is_valid(self) -> bool:
        """Check if contact information is valid."""
        return bool(self.email) and self.confidence >= 0.5


class ContactExtractor:
    """Extracts contact information from apartment listings."""
    
    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.logger = logging.getLogger(__name__)
        self._email_patterns = self._compile_email_patterns()
    
    def extract_contacts(self, text: str) -> List[ContactInfo]:
        """Extract contact information from text.
        
        Args:
            text: Raw listing text to analyze
            
        Returns:
            List of ContactInfo objects found in text
        """
        contacts = []
        
        # Extract emails
        for email in self._extract_emails(text):
            contacts.append(ContactInfo(email=email))
        
        # Extract phone numbers
        for phone in self._extract_phones(text):
            contacts.append(ContactInfo(email="", phone=phone))
        
        return contacts
    
    def _extract_emails(self, text: str) -> List[str]:
        """Extract email addresses from text."""
        import re
        pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        return re.findall(pattern, text)
    
    def _compile_email_patterns(self) -> List[str]:
        """Compile email extraction patterns."""
        return [
            r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}',
            # Add more patterns as needed
        ]
```

#### Function Organization
```python
# Good - clear, focused functions
def validate_email(email: str) -> bool:
    """Validate email format."""
    import re
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_contact_data(data: Dict[str, Any]) -> bool:
    """Validate contact data structure."""
    required_fields = ['email', 'source']
    return all(field in data for field in required_fields)


def process_contact_data(data: Dict[str, Any]) -> ContactInfo:
    """Process and validate contact data."""
    if not validate_contact_data(data):
        raise ValueError("Invalid contact data structure")
    
    email = data['email']
    if not validate_email(email):
        raise ValueError(f"Invalid email format: {email}")
    
    return ContactInfo(
        email=email,
        phone=data.get('phone'),
        confidence=data.get('confidence', 0.0)
    )


# Bad - overly complex function
def process_contact_data(data: Dict[str, Any]) -> ContactInfo:
    """Single function doing too many things."""
    # Email validation
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if 'email' not in data or not re.match(email_pattern, data['email']):
        # Phone validation
        phone_pattern = r'^\+?[1-9]\d{1,14}$'
        if 'phone' in data and not re.match(phone_pattern, data['phone']):
            # Database lookup
            existing = db.find_contact(data['email'])
            if existing:
                # Contact merging logic
                merged = merge_contacts(existing, data)
                return merged
            # New contact creation
            return ContactInfo(
                email=data['email'],
                phone=data.get('phone'),
                confidence=data.get('confidence', 0.0)
            )
        raise ValueError("Invalid contact data")
```

### Error Handling

#### Exception Usage
```python
# Good - specific exceptions
class ContactExtractionError(Exception):
    """Raised when contact extraction fails."""


class ValidationError(Exception):
    """Raised when data validation fails."""


def extract_contact_info(text: str) -> ContactInfo:
    """Extract contact information with proper error handling."""
    if not text.strip():
        raise ValidationError("Empty text provided")
    
    try:
        email = _extract_email(text)
        phone = _extract_phone(text)
        return ContactInfo(email=email, phone=phone)
    except Exception as e:
        raise ContactExtractionError(f"Failed to extract contacts: {e}") from e


# Bad - generic exceptions
def extract_contact_info(text: str) -> ContactInfo:
    """Bad error handling."""
    if not text.strip():
        raise Exception("Empty text")  # Too generic
    
    try:
        # Complex extraction logic
        return result
    except Exception as e:  # Catching everything
        raise Exception(f"Error: {e}")  # Lost original exception
```

#### Logging Best Practices
```python
import logging
from functools import wraps

logger = logging.getLogger(__name__)


def setup_logging():
    """Configure application logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler('mafa.log')
        ]
    )


def log_operation(func):
    """Decorator to log function calls."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        logger.info(f"Calling {func.__name__} with args={args}, kwargs={kwargs}")
        try:
            result = func(*args, **kwargs)
            logger.info(f"{func.__name__} completed successfully")
            return result
        except Exception as e:
            logger.error(f"{func.__name__} failed: {e}", exc_info=True)
            raise
    return wrapper


@log_operation
def process_listings(listings: List[Dict]) -> List[Contact]:
    """Process apartment listings to extract contacts."""
    contacts = []
    for i, listing in enumerate(listings):
        logger.debug(f"Processing listing {i+1}/{len(listings)}")
        try:
            contact = extract_contact_info(listing['text'])
            contacts.append(contact)
        except ValidationError as e:
            logger.warning(f"Skipping invalid listing: {e}")
            continue
    return contacts
```

### Data Classes and Dataclasses

#### Use dataclasses for Simple Data Containers
```python
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime

@dataclass
class SearchResult:
    """Represents a search result from apartment websites."""
    title: str
    price: int
    rooms: int
    url: str
    source: str
    discovered_at: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_within_budget(self, max_price: int) -> bool:
        """Check if result is within budget."""
        return self.price <= max_price
    
    def __post_init__(self):
        """Validate data after initialization."""
        if self.price <= 0:
            raise ValueError("Price must be positive")
        if self.rooms <= 0:
            raise ValueError("Rooms must be positive")
```

---

## JavaScript/TypeScript Standards

### ES6+ Features

#### Modern JavaScript Patterns
```javascript
// Good - Modern ES6+ features
const ContactCard = ({ contact, onApprove }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  
  const handleApprove = useCallback(async () => {
    setIsLoading(true);
    try {
      await onApprove(contact.id);
      setIsExpanded(false);
    } catch (error) {
      console.error('Failed to approve contact:', error);
    } finally {
      setIsLoading(false);
    }
  }, [contact.id, onApprove]);
  
  const contactMethods = useMemo(() => {
    const methods = [];
    if (contact.email) methods.push(contact.email);
    if (contact.phone) methods.push(contact.phone);
    return methods;
  }, [contact]);
  
  return (
    <div className="contact-card">
      <h3>{contact.name}</h3>
      <ul>
        {contactMethods.map(method => (
          <li key={method}>{method}</li>
        ))}
      </ul>
      <button 
        onClick={handleApprove}
        disabled={isLoading}
      >
        {isLoading ? 'Approving...' : 'Approve'}
      </button>
    </div>
  );
};

// Bad - Old JavaScript patterns
const ContactCard = function(contact, onApprove) {
  const [isExpanded, setIsExpanded] = React.useState(false);
  const [isLoading, setIsLoading] = React.useState(false);
  
  function handleApprove() {
    setIsLoading(true);
    onApprove(contact.id);
    setIsLoading(false);
  }
  
  return React.createElement('div', { className: 'contact-card' },
    React.createElement('h3', null, contact.name),
    React.createElement('button', { 
      onClick: handleApprove,
      disabled: isLoading
    }, isLoading ? 'Approving...' : 'Approve')
  );
};
```

#### Async/Await Patterns
```javascript
// Good - Async/await with proper error handling
class ContactService {
  async fetchContacts(filters = {}) {
    try {
      const response = await fetch('/api/contacts', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(filters),
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      return data.contacts;
    } catch (error) {
      console.error('Failed to fetch contacts:', error);
      throw new NetworkError('Failed to fetch contacts', error);
    }
  }
  
  async approveContact(contactId) {
    const response = await fetch(`/api/contacts/${contactId}/approve`, {
      method: 'POST',
    });
    
    if (!response.ok) {
      throw new Error(`Approval failed: ${response.status}`);
    }
    
    return await response.json();
  }
}

// Custom error classes
class NetworkError extends Error {
  constructor(message, originalError) {
    super(message);
    this.name = 'NetworkError';
    this.originalError = originalError;
  }
}
```

### React Component Guidelines

#### Functional Components with Hooks
```javascript
// Good - Clean functional component
import React, { useState, useEffect, useCallback } from 'react';
import { ContactCard } from './ContactCard';
import { LoadingSpinner } from './LoadingSpinner';

export const ContactList = ({ filter, onContactSelect }) => {
  const [contacts, setContacts] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const loadContacts = useCallback(async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/contacts?filter=${filter}`);
      if (!response.ok) throw new Error('Failed to load contacts');
      
      const data = await response.json();
      setContacts(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  }, [filter]);
  
  useEffect(() => {
    loadContacts();
  }, [loadContacts]);
  
  if (isLoading) {
    return <LoadingSpinner />;
  }
  
  if (error) {
    return (
      <div className="error-message">
        Error: {error}
        <button onClick={loadContacts}>Retry</button>
      </div>
    );
  }
  
  return (
    <div className="contact-list">
      {contacts.map(contact => (
        <ContactCard
          key={contact.id}
          contact={contact}
          onSelect={onContactSelect}
        />
      ))}
    </div>
  );
};
```

#### PropTypes and TypeScript
```javascript
// With PropTypes
import PropTypes from 'prop-types';

const ContactCard = ({ contact, onApprove, onReject }) => {
  // Component implementation
};

ContactCard.propTypes = {
  contact: PropTypes.shape({
    id: PropTypes.string.isRequired,
    email: PropTypes.string.isRequired,
    phone: PropTypes.string,
    confidence: PropTypes.number.isRequired,
  }).isRequired,
  onApprove: PropTypes.func.isRequired,
  onReject: PropTypes.func.isRequired,
};

// With TypeScript
interface Contact {
  id: string;
  email: string;
  phone?: string;
  confidence: number;
}

interface ContactCardProps {
  contact: Contact;
  onApprove: (id: string) => Promise<void>;
  onReject: (id: string) => void;
}

const ContactCard: React.FC<ContactCardProps> = ({ contact, onApprove, onReject }) => {
  // Component implementation
};
```

---

## CSS/Styling Standards

### CSS Architecture

#### BEM Methodology
```css
/* Block */
.contact-card {
  display: flex;
  flex-direction: column;
  padding: 1rem;
  border: 1px solid #e1e5e9;
  border-radius: 8px;
  background-color: #ffffff;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

/* Element */
.contact-card__header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.contact-card__title {
  font-size: 1.25rem;
  font-weight: 600;
  color: #2d3748;
  margin: 0;
}

.contact-card__confidence {
  display: inline-block;
  padding: 0.25rem 0.5rem;
  font-size: 0.875rem;
  font-weight: 500;
  color: #ffffff;
  background-color: #48bb78;
  border-radius: 4px;
}

/* Modifier */
.contact-card--high-quality {
  border-color: #48bb78;
}

.contact-card--high-quality .contact-card__confidence {
  background-color: #38a169;
}

.contact-card--loading {
  opacity: 0.6;
  pointer-events: none;
}
```

#### CSS Custom Properties
```css
:root {
  /* Colors */
  --color-primary: #3182ce;
  --color-primary-dark: #2c5aa0;
  --color-success: #38a169;
  --color-warning: #d69e2e;
  --color-error: #e53e3e;
  
  /* Spacing */
  --spacing-xs: 0.25rem;
  --spacing-sm: 0.5rem;
  --spacing-md: 1rem;
  --spacing-lg: 1.5rem;
  --spacing-xl: 2rem;
  
  /* Typography */
  --font-size-sm: 0.875rem;
  --font-size-base: 1rem;
  --font-size-lg: 1.125rem;
  --font-size-xl: 1.25rem;
  
  /* Shadows */
  --shadow-sm: 0 1px 3px rgba(0, 0, 0, 0.12);
  --shadow-md: 0 4px 6px rgba(0, 0, 0, 0.1);
  --shadow-lg: 0 10px 15px rgba(0, 0, 0, 0.1);
  
  /* Transitions */
  --transition-fast: 150ms ease-in-out;
  --transition-normal: 300ms ease-in-out;
}

.contact-card {
  background-color: var(--color-white);
  box-shadow: var(--shadow-md);
  transition: box-shadow var(--transition-fast);
}

.contact-card:hover {
  box-shadow: var(--shadow-lg);
}
```

### Responsive Design
```css
/* Mobile-first approach */
.contact-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: var(--spacing-md);
  padding: var(--spacing-md);
}

/* Tablet */
@media (min-width: 768px) {
  .contact-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: var(--spacing-lg);
    padding: var(--spacing-lg);
  }
}

/* Desktop */
@media (min-width: 1024px) {
  .contact-grid {
    grid-template-columns: repeat(3, 1fr);
    gap: var(--spacing-xl);
    padding: var(--spacing-xl);
  }
}

/* Large desktop */
@media (min-width: 1440px) {
  .contact-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}
```

---

## File Organization

### Python Project Structure
```
mafa/
├── __init__.py
├── config/
│   ├── __init__.py
│   ├── settings.py
│   └── validators.py
├── contacts/
│   ├── __init__.py
│   ├── extractors.py
│   ├── validators.py
│   └── models.py
├── scrapers/
│   ├── __init__.py
│   ├── base.py
│   ├── immoscout.py
│   └── wg_gesucht.py
├── db/
│   ├── __init__.py
│   ├── models.py
│   └── migrations/
└── utils/
    ├── __init__.py
    ├── helpers.py
    └── validators.py
```

### JavaScript Project Structure
```
dashboard/
├── src/
│   ├── components/
│   │   ├── common/
│   │   │   ├── Button.jsx
│   │   │   ├── Input.jsx
│   │   │   └── Modal.jsx
│   │   ├── contact/
│   │   │   ├── ContactCard.jsx
│   │   │   └── ContactList.jsx
│   │   └── layout/
│   │       ├── Header.jsx
│   │       └── Sidebar.jsx
│   ├── hooks/
│   │   ├── useContacts.js
│   │   ├── useApi.js
│   │   └── useLocalStorage.js
│   ├── utils/
│   │   ├── api.js
│   │   ├── formatters.js
│   │   └── validators.js
│   ├── styles/
│   │   ├── globals.css
│   │   ├── components.css
│   │   └── utilities.css
│   └── App.jsx
└── public/
    ├── index.html
    └── favicon.ico
```

---

## Code Review Checklist

### Python Code Review
- [ ] Code follows PEP 8 style guidelines
- [ ] Type hints are used consistently
- [ ] Functions and classes have proper docstrings
- [ ] Error handling is appropriate and specific
- [ ] Logging is used for important operations
- [ ] No hardcoded values (use constants/configuration)
- [ ] Code is tested with adequate test coverage
- [ ] Imports are organized and sorted
- [ ] No unused imports or variables
- [ ] Complex logic is well-commented

### JavaScript Code Review
- [ ] Modern ES6+ features are used appropriately
- [ ] React components follow functional patterns
- [ ] PropTypes or TypeScript types are defined
- [ ] Error handling is implemented properly
- [ ] No console.log statements in production code
- [ ] Code is responsive and mobile-friendly
- [ ] CSS follows BEM methodology
- [ ] No inline styles (use CSS classes)
- [ ] Accessibility considerations are implemented
- [ ] Performance optimizations are considered

### General Code Review
- [ ] Code is readable and self-documenting
- [ ] No code duplication
- [ ] Appropriate use of abstractions
- [ ] Security considerations addressed
- [ ] Performance impact evaluated
- [ ] Documentation is updated if needed
- [ ] Backward compatibility maintained
- [ ] Migration plan provided if needed

---

## Tools and Configuration

### Python Tools Configuration

#### pyproject.toml
```toml
[build-system]
requires = ["setuptools>=45", "wheel", "setuptools_scm[toml]>=6.2"]
build-backend = "setuptools.build_meta"

[project]
name = "mafa"
version = "1.0.0"
description = "Munich Apartment Finder Assistant"
authors = [
    {name = "MAFA Team", email = "team@mafa.app"}
]
license = {text = "MIT"}
readme = "README.md"
requires-python = ">=3.8"
classifiers = [
    "Development Status :: 4 - Beta",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
]

[project.optional-dependencies]
dev = [
    "pytest>=6.0",
    "pytest-cov>=2.0",
    "black>=21.0",
    "isort>=5.0",
    "flake8>=3.8",
    "mypy>=0.800",
    "pre-commit>=2.0",
]

[tool.black]
line-length = 88
target-version = ['py38', 'py39', 'py310']
include = '\.pyi?$'
exclude = '''
/(
    \.eggs
  | \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 88
include_trailing_comma = true
force_grid_wrap = 0
use_parentheses = true
ensure_newline_before_comments = true

[tool.flake8]
max-line-length = 88
extend-ignore = ["E203", "W503"]
exclude = [
    ".git",
    "__pycache__",
    "build",
    "dist",
    ".venv",
    ".eggs",
    "*.egg",
]

[tool.mypy]
python_version = "3.8"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
disallow_untyped_decorators = true
no_implicit_optional = true
warn_redundant_casts = true
warn_unused_ignores = true
warn_no_return = true
warn_unreachable = true
strict_equality = true

[tool.pytest.ini_options]
minversion = "6.0"
addopts = "-ra -q --strict-markers --strict-config"
testpaths = ["tests"]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
    "unit: marks tests as unit tests",
]
```

### JavaScript Tools Configuration

#### package.json
```json
{
  "name": "mafa-dashboard",
  "version": "1.0.0",
  "description": "MAFA Frontend Dashboard",
  "main": "src/index.js",
  "scripts": {
    "start": "react-scripts start",
    "build": "react-scripts build",
    "test": "react-scripts test",
    "eject": "react-scripts eject",
    "lint": "eslint src/",
    "lint:fix": "eslint src/ --fix",
    "format": "prettier --write src/",
    "type-check": "tsc --noEmit"
  },
  "dependencies": {
    "react": "^18.0.0",
    "react-dom": "^18.0.0",
    "react-router-dom": "^6.0.0",
    "axios": "^0.27.0"
  },
  "devDependencies": {
    "@types/react": "^18.0.0",
    "@types/react-dom": "^18.0.0",
    "@typescript-eslint/eslint-plugin": "^5.0.0",
    "@typescript-eslint/parser": "^5.0.0",
    "eslint": "^8.0.0",
    "eslint-config-prettier": "^8.0.0",
    "eslint-plugin-react": "^7.0.0",
    "eslint-plugin-react-hooks": "^4.0.0",
    "prettier": "^2.0.0",
    "typescript": "^4.0.0"
  }
}
```

#### .eslintrc.js
```javascript
module.exports = {
  env: {
    browser: true,
    es2021: true,
    node: true,
  },
  extends: [
    'eslint:recommended',
    '@typescript-eslint/recommended',
    'prettier',
    'plugin:react/recommended',
    'plugin:react-hooks/recommended',
  ],
  parser: '@typescript-eslint/parser',
  parserOptions: {
    ecmaFeatures: {
      jsx: true,
    },
    ecmaVersion: 12,
    sourceType: 'module',
  },
  plugins: [
    'react',
    'react-hooks',
    '@typescript-eslint',
  ],
  rules: {
    'react/react-in-jsx-scope': 'off',
    'react/prop-types': 'off',
    '@typescript-eslint/no-unused-vars': 'error',
    '@typescript-eslint/explicit-function-return-type': 'warn',
    'prefer-const': 'error',
    'no-var': 'error',
    'no-console': 'warn',
  },
  settings: {
    react: {
      version: 'detect',
    },
  },
};
```

#### prettier.config.js
```javascript
module.exports = {
  semi: true,
  trailingComma: 'es5',
  singleQuote: true,
  printWidth: 80,
  tabWidth: 2,
  useTabs: false,
  bracketSpacing: true,
  bracketSameLine: false,
  arrowParens: 'avoid',
  endOfLine: 'lf',
};
```

---

## Best Practices Summary

### Do's
- ✅ Write self-documenting code
- ✅ Use type annotations consistently
- ✅ Follow the principle of least surprise
- ✅ Handle errors gracefully
- ✅ Write comprehensive tests
- ✅ Document complex logic
- ✅ Use meaningful variable and function names
- ✅ Keep functions small and focused
- ✅ Write code that is easy to test
- ✅ Consider performance implications

### Don'ts
- ❌ Use magic numbers (use constants)
- ❌ Leave commented-out code
- ❌ Create overly complex functions
- ❌ Ignore linter warnings
- ❌ Use global variables excessively
- ❌ Skip error handling
- ❌ Write code without tests
- ❌ Use unclear variable names
- ❌ Hardcode configuration values
- ❌ Create deeply nested code

---

## Related Documentation

- [Development Setup](development-setup.md) - Development environment setup
- [Contributing Guidelines](contributing.md) - How to contribute to MAFA
- [Documentation Guidelines](documentation-guidelines.md) - Writing documentation
- [API Integration Guide](api/integration-guide.md) - Backend integration
- [Architecture Overview](../architecture/system-overview.md) - System design

---

**Code Style Support**: For questions about code style, refer to our [Style Guide FAQ](https://github.com/your-org/mafa/wiki/Style-Guide-FAQ) or ask in the developer Discord.