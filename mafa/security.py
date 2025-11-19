"""
Security utilities for MAFA application.

Provides input validation, sanitization, and security checks to prevent
common vulnerabilities in web scraping and configuration handling.
"""

import re
import hashlib
import html
from typing import List, Dict, Any, Optional
from pathlib import Path
from urllib.parse import urlparse
import bleach


class SecurityValidator:
    """Centralized security validation for MAFA."""
    
    # Dangerous patterns that should be filtered
    DANGEROUS_PATTERNS = [
        r'<script[^>]*>.*?</script>',  # Script tags
        r'javascript:',  # JavaScript protocol
        r'on\w+\s*=',   # Event handlers like onclick=
        r'vbscript:',   # VBScript protocol
        r'data:text/html',  # Data URL with HTML
        r'<iframe[^>]*>.*?</iframe>',  # Iframe tags
        r'eval\s*\(',   # Eval function calls
    ]
    
    # Allowed HTML tags for rich text content
    ALLOWED_TAGS = ['b', 'i', 'em', 'strong', 'u', 'p', 'br']
    
    # Maximum lengths for various fields
    MAX_TITLE_LENGTH = 200
    MAX_PRICE_LENGTH = 50
    MAX_SOURCE_LENGTH = 100
    MAX_INTRO_LENGTH = 1000
    
    @classmethod
    def sanitize_text(cls, text: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize text input by removing dangerous patterns and HTML.
        
        Args:
            text: Input text to sanitize
            max_length: Maximum allowed length
            
        Returns:
            Sanitized text string
        """
        if not isinstance(text, str):
            return ""
        
        # Remove null bytes and control characters
        text = ''.join(char for char in text if ord(char) >= 32 or char in ['\n', '\r', '\t'])
        
        # Remove dangerous patterns
        for pattern in cls.DANGEROUS_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.DOTALL)
        
        # Escape HTML entities
        text = html.escape(text)
        
        # Truncate if necessary
        if max_length and len(text) > max_length:
            text = text[:max_length].strip()
        
        return text.strip()
    
    @classmethod
    def sanitize_listing(cls, listing: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize a complete listing dictionary.
        
        Args:
            listing: Raw listing dictionary
            
        Returns:
            Sanitized listing dictionary
        """
        if not isinstance(listing, dict):
            return {}
        
        sanitized = {}
        
        # Sanitize standard fields
        for field in ['title', 'price', 'source', 'timestamp']:
            if field in listing:
                if field == 'title':
                    sanitized[field] = cls.sanitize_text(listing[field], cls.MAX_TITLE_LENGTH)
                elif field == 'price':
                    sanitized[field] = cls.sanitize_text(listing[field], cls.MAX_PRICE_LENGTH)
                elif field == 'source':
                    sanitized[field] = cls.sanitize_text(listing[field], cls.MAX_SOURCE_LENGTH)
                else:
                    sanitized[field] = str(listing[field])
        
        return sanitized
    
    @classmethod
    def validate_url(cls, url: str) -> bool:
        """
        Validate that a URL is safe and properly formatted.
        
        Args:
            url: URL string to validate
            
        Returns:
            True if URL is safe, False otherwise
        """
        try:
            parsed = urlparse(url)
            
            # Check scheme
            if parsed.scheme not in ['http', 'https']:
                return False
            
            # Check for dangerous patterns in URL
            url_lower = url.lower()
            dangerous_patterns = [
                'javascript:', 'vbscript:', 'data:', 'file:', 'ftp:'
            ]
            
            for pattern in dangerous_patterns:
                if pattern in url_lower:
                    return False
            
            # Check for valid domain
            if not parsed.netloc or '.' not in parsed.netloc:
                return False
            
            return True
            
        except Exception:
            return False
    
    @classmethod
    def validate_file_path(cls, file_path: Path, base_dir: Optional[Path] = None) -> bool:
        """
        Validate that a file path is safe and within allowed directories.
        
        Args:
            file_path: Path to validate
            base_dir: Base directory that file must be within (optional)
            
        Returns:
            True if path is safe, False otherwise
        """
        try:
            # Resolve to absolute path to prevent directory traversal
            resolved_path = file_path.resolve()
            
            # Check if path escapes the base directory
            if base_dir:
                base_resolved = base_dir.resolve()
                try:
                    resolved_path.relative_to(base_resolved)
                except ValueError:
                    return False
            
            # Check for dangerous path components
            dangerous_components = ['..', '~', '$', '%', '&']
            for component in dangerous_components:
                if component in str(resolved_path):
                    return False
            
            return True
            
        except Exception:
            return False
    
    @classmethod
    def validate_config_data(cls, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sanitize configuration data to prevent injection attacks.
        
        Args:
            config_data: Raw configuration dictionary
            
        Returns:
            Sanitized configuration dictionary
        """
        if not isinstance(config_data, dict):
            return {}
        
        sanitized = {}
        
        # Sanitize personal profile
        if 'personal_profile' in config_data:
            profile = config_data['personal_profile']
            if isinstance(profile, dict):
                sanitized['personal_profile'] = {}
                
                # Sanitize text fields
                text_fields = ['my_full_name', 'my_profession', 'my_employer', 'intro_paragraph']
                for field in text_fields:
                    if field in profile:
                        max_len = cls.MAX_INTRO_LENGTH if field == 'intro_paragraph' else 100
                        sanitized['personal_profile'][field] = cls.sanitize_text(
                            str(profile[field]), max_len
                        )
                
                # Validate numeric fields
                numeric_fields = ['net_household_income_monthly', 'total_occupants']
                for field in numeric_fields:
                    if field in profile:
                        try:
                            value = int(profile[field])
                            if value > 0:  # Basic validation
                                sanitized['personal_profile'][field] = value
                            else:
                                sanitized['personal_profile'][field] = 1
                        except (ValueError, TypeError):
                            sanitized['personal_profile'][field] = 1
        
        # Sanitize search criteria
        if 'search_criteria' in config_data:
            criteria = config_data['search_criteria']
            if isinstance(criteria, dict):
                sanitized['search_criteria'] = {}
                
                # Validate numeric fields
                if 'max_price' in criteria:
                    try:
                        sanitized['search_criteria']['max_price'] = max(1, int(criteria['max_price']))
                    except (ValueError, TypeError):
                        sanitized['search_criteria']['max_price'] = 2000
                
                if 'min_rooms' in criteria:
                    try:
                        sanitized['search_criteria']['min_rooms'] = max(1, int(criteria['min_rooms']))
                    except (ValueError, TypeError):
                        sanitized['search_criteria']['min_rooms'] = 1
                
                # Sanitize zip codes
                if 'zip_codes' in criteria and isinstance(criteria['zip_codes'], list):
                    sanitized['search_criteria']['zip_codes'] = []
                    for zip_code in criteria['zip_codes'][:50]:  # Limit to 50 zip codes
                        if isinstance(zip_code, str) and re.match(r'^\d{5}$', zip_code.strip()):
                            sanitized['search_criteria']['zip_codes'].append(zip_code.strip())
        
        # Sanitize notification settings
        if 'notification' in config_data:
            notification = config_data['notification']
            if isinstance(notification, dict):
                sanitized['notification'] = {}
                
                # Validate provider
                if 'provider' in notification:
                    provider = notification['provider'].lower()
                    if provider in ['discord', 'telegram']:
                        sanitized['notification']['provider'] = provider
                
                # Sanitize Discord webhook URL
                if 'discord_webhook_url' in notification:
                    webhook_url = notification['discord_webhook_url']
                    if cls.validate_url(webhook_url) and 'discord.com' in webhook_url:
                        sanitized['notification']['discord_webhook_url'] = webhook_url
                
                # Sanitize Telegram settings
                if 'telegram_bot_token' in notification:
                    token = notification['telegram_bot_token']
                    # Basic token format validation
                    if re.match(r'^\d+:[A-Za-z0-9_-]{35}$', token):
                        sanitized['notification']['telegram_bot_token'] = token
                
                if 'telegram_chat_id' in notification:
                    chat_id = str(notification['telegram_chat_id'])
                    # Basic chat ID validation (numbers with optional leading -)
                    if re.match(r'^-?\d+$', chat_id):
                        sanitized['notification']['telegram_chat_id'] = chat_id
        
        return sanitized
    
    @classmethod
    def generate_secure_hash(cls, data: str) -> str:
        """
        Generate a secure hash for data deduplication.
        
        Args:
            data: String data to hash
            
        Returns:
            SHA-256 hex digest
        """
        return hashlib.sha256(data.encode('utf-8')).hexdigest()
    
    @classmethod
    def check_input_size(cls, data: Any, max_size: int = 1024 * 1024) -> bool:
        """
        Check if input data size is within acceptable limits.
        
        Args:
            data: Input data to check
            max_size: Maximum size in bytes (default 1MB)
            
        Returns:
            True if size is acceptable, False otherwise
        """
        if isinstance(data, str):
            size = len(data.encode('utf-8'))
        elif isinstance(data, dict):
            import json
            size = len(json.dumps(data).encode('utf-8'))
        else:
            size = len(str(data).encode('utf-8'))
        
        return size <= max_size


def sanitize_user_input(text: str) -> str:
    """
    Convenience function for sanitizing user input.
    
    Args:
        text: Input text to sanitize
        
    Returns:
        Sanitized text
    """
    return SecurityValidator.sanitize_text(text)


def validate_scraping_target(url: str) -> bool:
    """
    Validate that a URL is safe for scraping.
    
    Args:
        url: URL to validate
        
    Returns:
        True if safe for scraping, False otherwise
    """
    return SecurityValidator.validate_url(url)