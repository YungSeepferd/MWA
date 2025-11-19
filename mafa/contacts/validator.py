"""
Contact validation and verification utilities.

Provides email and phone number validation, syntax checking,
and optional verification methods (with careful rate limiting).
"""

import re
import dns.resolver
import smtplib
import asyncio
from typing import List, Optional, Tuple, Dict
from urllib.parse import urlparse
import httpx
import logging

from .models import Contact, ContactMethod, ContactStatus, ConfidenceLevel
from ..exceptions import ValidationError


logger = logging.getLogger(__name__)


class ContactValidator:
    """
    Validates and verifies contact information.
    
    Provides multiple levels of validation:
    1. Syntax validation (basic format checks)
    2. Domain verification (DNS/MX record checks)
    3. Optional SMTP verification (with rate limiting)
    4. Phone number format validation
    """
    
    # Email syntax patterns
    EMAIL_SYNTAX_PATTERNS = {
        'strict': r'^[a-zA-Z0-9]([a-zA-Z0-9._%+-]*[a-zA-Z0-9])?@[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}$',
        'standard': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'lenient': r'^[^@]+@[^@]+\.[^@]+$'
    }
    
    # Phone number patterns by country
    PHONE_PATTERNS = {
        'german': r'^(\+49|0049|0)[1-9][0-9]{1,14}$',
        'international': r'^\+[1-9]\d{1,14}$',
        'generic': r'^\+?\d{7,15}$'
    }
    
    # Domains that commonly reject verification attempts
    BLOCKED_VERIFICATION_DOMAINS = [
        'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
        'web.de', 'gmx.de', 't-online.de', 'freenet.de'
    ]
    
    def __init__(self, enable_smtp_verification: bool = False, rate_limit: float = 1.0):
        """
        Initialize contact validator.
        
        Args:
            enable_smtp_verification: Whether to perform SMTP verification (can be intrusive)
            rate_limit: Minimum seconds between verification attempts
        """
        self.enable_smtp_verification = enable_smtp_verification
        self.rate_limit = rate_limit
        self.last_verification_time = 0
        
    async def validate_contact(self, contact: Contact) -> Contact:
        """
        Validate a single contact and update its verification status.
        
        Args:
            contact: Contact to validate
            
        Returns:
            Updated contact with verification status
        """
        try:
            if contact.method == ContactMethod.EMAIL:
                await self._validate_email(contact)
            elif contact.method == ContactMethod.PHONE:
                self._validate_phone(contact)
            elif contact.method == ContactMethod.FORM:
                await self._validate_form(contact)
            else:
                # For other methods, mark as unverified
                contact.verification_status = ContactStatus.UNVERIFIED
            
            return contact
            
        except ValidationError as e:
            contact.verification_status = ContactStatus.INVALID
            contact.metadata['validation_error'] = str(e)
            return contact
        except Exception as e:
            contact.verification_status = ContactStatus.FLAGGED
            contact.metadata['validation_error'] = f"Unexpected error: {str(e)}"
            return contact
    
    async def validate_contacts(self, contacts: List[Contact]) -> List[Contact]:
        """
        Validate a list of contacts with rate limiting.
        
        Args:
            contacts: List of contacts to validate
            
        Returns:
            List of validated contacts
        """
        validated_contacts = []
        
        for contact in contacts:
            # Rate limiting
            await self._rate_limit()
            
            # Validate contact
            validated_contact = await self.validate_contact(contact)
            validated_contacts.append(validated_contact)
        
        return validated_contacts
    
    async def _validate_email(self, contact: Contact) -> None:
        """
        Validate email address with multiple levels of checks.
        
        Args:
            contact: Email contact to validate
        """
        email = contact.value.lower().strip()
        
        # Syntax validation
        if not self._validate_email_syntax(email):
            raise ValidationError(f"Invalid email syntax: {email}")
        
        # Extract domain
        try:
            local, domain = email.rsplit('@', 1)
        except ValueError:
            raise ValidationError(f"Invalid email format: {email}")
        
        # Check for obviously invalid domains
        if self._is_invalid_domain(domain):
            raise ValidationError(f"Invalid or blocked domain: {domain}")
        
        # DNS/MX record verification
        if not await self._verify_domain_mx_records(domain):
            raise ValidationError(f"No MX records found for domain: {domain}")
        
        # Optional SMTP verification (if enabled and domain not blocked)
        if (self.enable_smtp_verification and 
            domain.lower() not in self.BLOCKED_VERIFICATION_DOMAINS):
            try:
                smtp_valid = await self._verify_email_smtp(email, domain)
                if smtp_valid:
                    contact.verification_status = ContactStatus.VERIFIED
                else:
                    contact.verification_status = ContactStatus.INVALID
            except Exception as e:
                logger.warning(f"SMTP verification failed for {email}: {str(e)}")
                contact.verification_status = ContactStatus.UNVERIFIED
        else:
            contact.verification_status = ContactStatus.UNVERIFIED
    
    def _validate_email_syntax(self, email: str) -> bool:
        """
        Validate email syntax using multiple pattern levels.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if syntax is valid
        """
        # Check length limits
        if len(email) > 254 or len(email.split('@')[0]) > 64:
            return False
        
        # Try strict pattern first
        if re.match(self.EMAIL_SYNTAX_PATTERNS['strict'], email):
            return True
        
        # Fall back to standard pattern
        if re.match(self.EMAIL_SYNTAX_PATTERNS['standard'], email):
            return True
        
        # Last resort: lenient pattern
        return bool(re.match(self.EMAIL_SYNTAX_PATTERNS['lenient'], email))
    
    def _is_invalid_domain(self, domain: str) -> bool:
        """
        Check for invalid or suspicious domains.
        
        Args:
            domain: Domain to check
            
        Returns:
            True if domain is invalid
        """
        domain = domain.lower()
        
        # Check for obviously invalid domains
        invalid_patterns = [
            r'^localhost$',
            r'^127\.',
            r'^0\.0\.0\.0$',
            r'^(example|test|sample)\.(com|org|net)$',
            r'^.*\.\..*$',  # Double dots
            r'^.*[_-]{2,}.*$'  # Multiple consecutive hyphens/underscores
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, domain):
                return True
        
        # Check for excessive subdomain depth
        if domain.count('.') > 4:
            return True
        
        return False
    
    async def _verify_domain_mx_records(self, domain: str) -> bool:
        """
        Verify domain has valid MX records.
        
        Args:
            domain: Domain to check
            
        Returns:
            True if MX records exist
        """
        try:
            # Check MX records
            mx_records = dns.resolver.resolve(domain, 'MX')
            return len(mx_records) > 0
        except dns.resolver.NXDOMAIN:
            return False
        except dns.resolver.NoAnswer:
            # No MX records, but check A records as fallback
            try:
                dns.resolver.resolve(domain, 'A')
                return True
            except:
                return False
        except Exception:
            return False
    
    async def _verify_email_smtp(self, email: str, domain: str) -> bool:
        """
        Verify email address using SMTP (optional, with rate limiting).
        
        Args:
            email: Email address to verify
            domain: Domain of the email
            
        Returns:
            True if email appears to exist
        """
        try:
            # Get MX records
            mx_records = dns.resolver.resolve(domain, 'MX')
            mx_host = str(mx_records[0].exchange)
            
            # Connect to SMTP server
            server = smtplib.SMTP(timeout=10)
            server.set_debuglevel(0)
            
            try:
                server.connect(mx_host)
                server.helo('mafa.example.com')  # Use proper hostname in production
                server.mail('test@mafa.example.com')
                
                # Try to verify the email
                code, message = server.rcpt(email)
                
                # 250/251 = accepted, 450/451 = temporary failure
                return code in [250, 251]
                
            finally:
                server.quit()
                
        except Exception as e:
            logger.debug(f"SMTP verification failed for {email}: {str(e)}")
            return False
    
    def _validate_phone(self, contact: Contact) -> None:
        """
        Validate phone number format.
        
        Args:
            contact: Phone contact to validate
        """
        phone = contact.value
        
        # Remove all non-digit characters for validation
        digits_only = re.sub(r'[^\d+]', '', phone)
        
        # Check for valid phone patterns
        valid_patterns = [
            self.PHONE_PATTERNS['german'],
            self.PHONE_PATTERNS['international'],
            self.PHONE_PATTERNS['generic']
        ]
        
        is_valid = any(re.match(pattern, digits_only) for pattern in valid_patterns)
        
        if not is_valid:
            raise ValidationError(f"Invalid phone number format: {phone}")
        
        contact.verification_status = ContactStatus.VERIFIED
    
    async def _validate_form(self, contact: Contact) -> None:
        """
        Validate contact form accessibility.
        
        Args:
            contact: Form contact to validate
        """
        form_url = contact.value
        
        # Basic URL validation
        try:
            parsed = urlparse(form_url)
            if parsed.scheme not in ['http', 'https']:
                raise ValidationError(f"Invalid form URL scheme: {parsed.scheme}")
            
            # Try to fetch the form page (without submitting)
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.head(form_url)
                
                if response.status_code >= 400:
                    raise ValidationError(f"Form URL returned status {response.status_code}")
                
                contact.verification_status = ContactStatus.UNVERIFIED
                
        except Exception as e:
            raise ValidationError(f"Form validation failed: {str(e)}")
    
    async def _rate_limit(self) -> None:
        """Implement rate limiting for verification attempts."""
        import time
        current_time = time.time()
        time_since_last = current_time - self.last_verification_time
        
        if time_since_last < self.rate_limit:
            sleep_time = self.rate_limit - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.last_verification_time = time.time()
    
    def get_validation_summary(self, contacts: List[Contact]) -> Dict[str, int]:
        """
        Get a summary of validation results.
        
        Args:
            contacts: List of contacts to summarize
            
        Returns:
            Dictionary with validation status counts
        """
        summary = {
            'total': len(contacts),
            'verified': 0,
            'unverified': 0,
            'invalid': 0,
            'flagged': 0
        }
        
        for contact in contacts:
            status = contact.verification_status
            if status == ContactStatus.VERIFIED:
                summary['verified'] += 1
            elif status == ContactStatus.UNVERIFIED:
                summary['unverified'] += 1
            elif status == ContactStatus.INVALID:
                summary['invalid'] += 1
            elif status == ContactStatus.FLAGGED:
                summary['flagged'] += 1
        
        return summary
    
    def filter_high_confidence_contacts(self, contacts: List[Contact]) -> List[Contact]:
        """
        Filter contacts to only include high-confidence, verified ones.
        
        Args:
            contacts: List of contacts to filter
            
        Returns:
            Filtered list of high-confidence contacts
        """
        high_confidence = []
        
        for contact in contacts:
            # Include if high confidence and verified or high confidence with medium confidence
            if (contact.is_high_confidence and 
                (contact.is_verified or contact.confidence == ConfidenceLevel.MEDIUM)):
                high_confidence.append(contact)
        
        return high_confidence
    
    def get_recommendations(self, contacts: List[Contact]) -> Dict[str, List[str]]:
        """
        Get recommendations for improving contact discovery and validation.
        
        Args:
            contacts: List of contacts to analyze
            
        Returns:
            Dictionary with recommendations
        """
        recommendations = {
            'high_priority': [],
            'medium_priority': [],
            'low_priority': [],
            'data_quality': []
        }
        
        # Analyze validation results
        summary = self.get_validation_summary(contacts)
        
        # High priority recommendations
        if summary['invalid'] > summary['verified']:
            recommendations['high_priority'].append(
                "High number of invalid contacts detected. Review extraction patterns."
            )
        
        if summary['flagged'] > 0:
            recommendations['high_priority'].append(
                f"{summary['flagged']} contacts flagged for review due to validation errors."
            )
        
        # Medium priority recommendations
        if summary['unverified'] > summary['verified'] * 2:
            recommendations['medium_priority'].append(
                "Consider enabling SMTP verification for better accuracy."
            )
        
        if len(contacts) < 3:
            recommendations['medium_priority'].append(
                "Low number of contacts found. Consider increasing crawl depth or adding more sources."
            )
        
        # Low priority recommendations
        email_contacts = [c for c in contacts if c.method == ContactMethod.EMAIL]
        if email_contacts:
            domains = set(c.value.split('@')[1] for c in email_contacts)
            if len(domains) == 1:
                recommendations['low_priority'].append(
                    "All emails from same domain. Consider finding diverse contact sources."
                )
        
        # Data quality recommendations
        if summary['verified'] > 0:
            verification_rate = summary['verified'] / summary['total']
            if verification_rate > 0.8:
                recommendations['data_quality'].append(
                    f"High verification rate ({verification_rate:.1%}). Extraction quality is good."
                )
            elif verification_rate < 0.3:
                recommendations['data_quality'].append(
                    f"Low verification rate ({verification_rate:.1%}). Review extraction patterns."
                )
        
        return recommendations


class ValidationError(Exception):
    """Raised when contact validation fails."""
    pass