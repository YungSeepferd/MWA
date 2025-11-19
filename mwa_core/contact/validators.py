"""
Advanced contact validation and verification system.

Provides comprehensive validation for different contact types:
- Email validation with DNS/MX verification
- Phone number validation with format checking
- Form validation with accessibility testing
- Social media profile validation
- Bulk validation with rate limiting
- Verification result tracking
"""

import re
import asyncio
import logging
import dns.resolver
import smtplib
import socket
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime, timedelta
from urllib.parse import urlparse
import httpx

from .models import Contact, ContactMethod, ContactStatus, ConfidenceLevel
from .scoring import ContactScoringEngine

logger = logging.getLogger(__name__)


class ValidationResult:
    """Result of contact validation."""
    
    def __init__(self, contact: Contact, is_valid: bool, validation_method: str,
                 confidence_score: float, errors: List[str] = None,
                 warnings: List[str] = None, metadata: Dict[str, Any] = None):
        self.contact = contact
        self.is_valid = is_valid
        self.validation_method = validation_method
        self.confidence_score = confidence_score
        self.errors = errors or []
        self.warnings = warnings or []
        self.metadata = metadata or {}
        self.validated_at = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary."""
        return {
            'contact': self.contact.to_dict(),
            'is_valid': self.is_valid,
            'validation_method': self.validation_method,
            'confidence_score': self.confidence_score,
            'errors': self.errors,
            'warnings': self.warnings,
            'metadata': self.metadata,
            'validated_at': self.validated_at.isoformat()
        }


class ContactValidator:
    """
    Advanced contact validation system with multiple validation methods.
    
    Features:
    - Multi-level email validation (syntax, DNS, SMTP)
    - Phone number format validation with international support
    - Form accessibility validation
    - Social media profile verification
    - Rate limiting for external validations
    - Bulk validation with progress tracking
    - Validation result persistence
    """
    
    # Email validation patterns
    EMAIL_PATTERNS = {
        'strict': r'^[a-zA-Z0-9]([a-zA-Z0-9._%+-]*[a-zA-Z0-9])?@[a-zA-Z0-9]([a-zA-Z0-9.-]*[a-zA-Z0-9])?\.[a-zA-Z]{2,}$',
        'standard': r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$',
        'lenient': r'^[^@]+@[^@]+\.[^@]+$'
    }
    
    # Phone validation patterns by region
    PHONE_PATTERNS = {
        'german': r'^(\+49|0049|0)[1-9][0-9]{1,14}$',
        'international': r'^\+[1-9]\d{1,14}$',
        'generic': r'^\+?\d{7,15}$'
    }
    
    # Domains that commonly reject verification attempts
    BLOCKED_VERIFICATION_DOMAINS = {
        'gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com',
        'web.de', 'gmx.de', 't-online.de', 'freenet.de'
    }
    
    # Disposable email domains
    DISPOSABLE_DOMAINS = {
        'tempmail.org', '10minutemail.com', 'mailinator.com',
        'guerrillamail.com', 'throwaway.email', 'temp-mail.org'
    }
    
    def __init__(self, enable_smtp_verification: bool = False, 
                 enable_dns_verification: bool = True,
                 rate_limit_seconds: float = 1.0,
                 max_validation_attempts: int = 3):
        """
        Initialize contact validator.
        
        Args:
            enable_smtp_verification: Whether to perform SMTP verification
            enable_dns_verification: Whether to perform DNS verification
            rate_limit_seconds: Minimum seconds between validation attempts
            max_validation_attempts: Maximum attempts for failed validations
        """
        self.enable_smtp_verification = enable_smtp_verification
        self.enable_dns_verification = enable_dns_verification
        self.rate_limit_seconds = rate_limit_seconds
        self.max_validation_attempts = max_validation_attempts
        
        # Rate limiting state
        self.last_validation_time = 0
        self.validation_counts = {}
        
        # Scoring engine for confidence calculation
        self.scoring_engine = ContactScoringEngine()
        
        logger.info(f"Contact validator initialized (SMTP: {enable_smtp_verification}, DNS: {enable_dns_verification})")
    
    async def validate_contact(self, contact: Contact, validation_level: str = "standard") -> ValidationResult:
        """
        Validate a single contact with specified validation level.
        
        Args:
            contact: Contact to validate
            validation_level: Validation level ("basic", "standard", "comprehensive")
            
        Returns:
            ValidationResult with validation details
        """
        try:
            # Rate limiting
            await self._enforce_rate_limit()
            
            # Validate based on contact method
            if contact.method == ContactMethod.EMAIL:
                return await self._validate_email(contact, validation_level)
            elif contact.method == ContactMethod.PHONE:
                return await self._validate_phone(contact, validation_level)
            elif contact.method == ContactMethod.FORM:
                return await self._validate_form(contact, validation_level)
            elif contact.method == ContactMethod.WEBSITE:
                return await self._validate_website(contact, validation_level)
            elif contact.method == ContactMethod.SOCIAL_MEDIA:
                return await self._validate_social_media(contact, validation_level)
            else:
                # Generic validation for other methods
                return ValidationResult(
                    contact=contact,
                    is_valid=True,
                    validation_method="generic",
                    confidence_score=0.5,
                    warnings=["No specific validation for this contact method"]
                )
        
        except Exception as e:
            logger.error(f"Validation failed for {contact.value}: {e}")
            return ValidationResult(
                contact=contact,
                is_valid=False,
                validation_method="error",
                confidence_score=0.1,
                errors=[f"Validation error: {str(e)}"]
            )
    
    async def validate_contacts_batch(self, contacts: List[Contact], 
                                    validation_level: str = "standard",
                                    progress_callback: Optional[callable] = None) -> List[ValidationResult]:
        """
        Validate multiple contacts with progress tracking.
        
        Args:
            contacts: List of contacts to validate
            validation_level: Validation level
            progress_callback: Optional callback for progress updates
            
        Returns:
            List of ValidationResult objects
        """
        results = []
        total = len(contacts)
        
        for i, contact in enumerate(contacts):
            result = await self.validate_contact(contact, validation_level)
            results.append(result)
            
            # Progress callback
            if progress_callback:
                progress = (i + 1) / total * 100
                progress_callback(progress, i + 1, total)
        
        return results
    
    async def _validate_email(self, contact: Contact, validation_level: str) -> ValidationResult:
        """
        Validate email address with multiple levels of checks.
        
        Args:
            contact: Email contact to validate
            validation_level: Validation level
            
        Returns:
            ValidationResult
        """
        email = contact.value.lower().strip()
        errors = []
        warnings = []
        metadata = {}
        
        # Level 1: Basic syntax validation
        syntax_valid = self._validate_email_syntax(email)
        if not syntax_valid:
            errors.append("Invalid email syntax")
            return ValidationResult(
                contact=contact,
                is_valid=False,
                validation_method="syntax",
                confidence_score=0.1,
                errors=errors
            )
        
        # Extract domain
        try:
            local_part, domain = email.rsplit('@', 1)
            metadata['domain'] = domain
            metadata['local_part'] = local_part
        except ValueError:
            errors.append("Invalid email format")
            return ValidationResult(
                contact=contact,
                is_valid=False,
                validation_method="format",
                confidence_score=0.1,
                errors=errors
            )
        
        # Check for disposable email domains
        if domain in self.DISPOSABLE_DOMAINS:
            warnings.append("Email uses disposable domain")
            metadata['disposable_domain'] = True
        
        # Check for obviously invalid domains
        if self._is_invalid_domain(domain):
            errors.append("Invalid or suspicious domain")
            return ValidationResult(
                contact=contact,
                is_valid=False,
                validation_method="domain",
                confidence_score=0.2,
                errors=errors,
                warnings=warnings,
                metadata=metadata
            )
        
        # Level 2: DNS/MX record verification (if enabled)
        if self.enable_dns_verification and validation_level in ["standard", "comprehensive"]:
            dns_valid = await self._verify_domain_mx_records(domain)
            if not dns_valid:
                errors.append("No valid MX records found for domain")
                return ValidationResult(
                    contact=contact,
                    is_valid=False,
                    validation_method="dns",
                    confidence_score=0.3,
                    errors=errors,
                    warnings=warnings,
                    metadata=metadata
                )
            metadata['mx_records_found'] = True
        
        # Level 3: SMTP verification (if enabled and appropriate)
        if (self.enable_smtp_verification and 
            validation_level == "comprehensive" and
            domain.lower() not in self.BLOCKED_VERIFICATION_DOMAINS):
            
            smtp_valid = await self._verify_email_smtp(email, domain)
            if smtp_valid:
                metadata['smtp_verified'] = True
                confidence = 0.95
                validation_method = "smtp"
            else:
                warnings.append("SMTP verification inconclusive")
                confidence = 0.7
                validation_method = "dns+smtp"
        else:
            confidence = 0.8
            validation_method = "dns" if self.enable_dns_verification else "syntax"
        
        return ValidationResult(
            contact=contact,
            is_valid=True,
            validation_method=validation_method,
            confidence_score=confidence,
            warnings=warnings,
            metadata=metadata
        )
    
    def _validate_email_syntax(self, email: str) -> bool:
        """Validate email syntax using multiple pattern levels."""
        # Check length limits
        if len(email) > 254 or len(email.split('@')[0]) > 64:
            return False
        
        # Try strict pattern first
        if re.match(self.EMAIL_PATTERNS['strict'], email):
            return True
        
        # Fall back to standard pattern
        if re.match(self.EMAIL_PATTERNS['standard'], email):
            return True
        
        # Last resort: lenient pattern
        return bool(re.match(self.EMAIL_PATTERNS['lenient'], email))
    
    def _is_invalid_domain(self, domain: str) -> bool:
        """Check for invalid or suspicious domains."""
        domain = domain.lower()
        
        # Check for obviously invalid patterns
        invalid_patterns = [
            r'^localhost$',
            r'^127\.',
            r'^0\.0\.0\.0$',
            r'^(example|test|sample)\.(com|org|net)$',
            r'^.*\.\..*$',  # Double dots
            r'^.*[_-]{2,}.*$',  # Multiple consecutive hyphens/underscores
            r'^\d+\.\d+\.\d+\.\d+$',  # IP addresses
        ]
        
        for pattern in invalid_patterns:
            if re.match(pattern, domain):
                return True
        
        # Check for excessive subdomain depth
        if domain.count('.') > 4:
            return True
        
        # Check for suspicious TLDs
        suspicious_tlds = ['.tk', '.ml', '.ga', '.cf']
        if any(domain.endswith(tld) for tld in suspicious_tlds):
            return True
        
        return False
    
    async def _verify_domain_mx_records(self, domain: str) -> bool:
        """Verify domain has valid MX records."""
        try:
            # Check MX records
            mx_records = dns.resolver.resolve(domain, 'MX')
            return len(mx_records) > 0
        except dns.resolver.NXDOMAIN:
            return False
        except dns.resolver.NoAnswer:
            # No MX records, check A records as fallback
            try:
                dns.resolver.resolve(domain, 'A')
                return True
            except:
                return False
        except Exception as e:
            logger.debug(f"DNS verification failed for {domain}: {e}")
            return False
    
    async def _verify_email_smtp(self, email: str, domain: str) -> bool:
        """Verify email address using SMTP (with extreme caution)."""
        try:
            # Get MX records
            mx_records = dns.resolver.resolve(domain, 'MX')
            if not mx_records:
                return False
            
            # Use the highest priority MX server
            mx_host = str(sorted(mx_records, key=lambda x: x.preference)[0].exchange)
            
            # Connect to SMTP server
            server = smtplib.SMTP(timeout=10)
            server.set_debuglevel(0)
            
            try:
                server.connect(mx_host)
                server.helo('mwa-contact-validator.local')
                server.mail('validation@mwacontact.local')
                
                # Try to verify the email (without actually sending)
                code, message = server.rcpt(email)
                
                # Acceptable response codes
                return code in [250, 251]
                
            finally:
                server.quit()
                
        except Exception as e:
            logger.debug(f"SMTP verification failed for {email}: {e}")
            return False
    
    async def _validate_phone(self, contact: Contact, validation_level: str) -> ValidationResult:
        """
        Validate phone number format.
        
        Args:
            contact: Phone contact to validate
            validation_level: Validation level
            
        Returns:
            ValidationResult
        """
        phone = contact.value
        errors = []
        warnings = []
        metadata = {}
        
        # Remove formatting characters for validation
        clean_phone = re.sub(r'[^\d+]', '', phone)
        metadata['cleaned_number'] = clean_phone
        
        # Basic length validation
        if len(clean_phone) < 6 or len(clean_phone) > 16:
            errors.append("Phone number length outside valid range")
            return ValidationResult(
                contact=contact,
                is_valid=False,
                validation_method="format",
                confidence_score=0.2,
                errors=errors,
                metadata=metadata
            )
        
        # Format-specific validation
        if phone.startswith('+'):
            # International format validation
            if not self._validate_international_format(phone):
                errors.append("Invalid international phone format")
                return ValidationResult(
                    contact=contact,
                    is_valid=False,
                    validation_method="format",
                    confidence_score=0.3,
                    errors=errors,
                    metadata=metadata
                )
            metadata['format'] = 'international'
            
        elif phone.startswith('0'):
            # National format validation (German)
            if not self._validate_german_format(phone):
                errors.append("Invalid German phone format")
                return ValidationResult(
                    contact=contact,
                    is_valid=False,
                    validation_method="format",
                    confidence_score=0.3,
                    errors=errors,
                    metadata=metadata
                )
            metadata['format'] = 'german_national'
            
        else:
            warnings.append("Phone number format unclear")
            metadata['format'] = 'unknown'
        
        # Advanced validation for comprehensive level
        if validation_level == "comprehensive":
            # Area code validation for German numbers
            if metadata['format'] == 'german_national':
                area_code_valid = self._validate_german_area_code(clean_phone)
                if not area_code_valid:
                    warnings.append("German area code validation inconclusive")
                metadata['area_code_validated'] = area_code_valid
            
            # Mobile number detection
            is_mobile = self._is_mobile_number(clean_phone)
            metadata['is_mobile'] = is_mobile
        
        # Determine confidence score
        if errors:
            confidence = 0.2
        elif warnings:
            confidence = 0.7
        else:
            confidence = 0.9
        
        validation_method = "format"
        if validation_level == "comprehensive" and 'area_code_validated' in metadata:
            validation_method = "comprehensive"
        
        return ValidationResult(
            contact=contact,
            is_valid=len(errors) == 0,
            validation_method=validation_method,
            confidence_score=confidence,
            errors=errors,
            warnings=warnings,
            metadata=metadata
        )
    
    def _validate_international_format(self, phone: str) -> bool:
        """Validate international phone format."""
        # Must start with + and country code
        if not phone.startswith('+'):
            return False
        
        # Extract country code
        country_code_match = re.match(r'^\+(\d{1,3})', phone)
        if not country_code_match:
            return False
        
        country_code = int(country_code_match.group(1))
        
        # Valid country code ranges
        if country_code < 1 or country_code > 999:
            return False
        
        # Pattern matching
        return bool(re.match(self.PHONE_PATTERNS['international'], phone))
    
    def _validate_german_format(self, phone: str) -> bool:
        """Validate German phone format."""
        # Pattern matching
        if not re.match(self.PHONE_PATTERNS['german'], phone):
            return False
        
        # Area code validation
        clean_phone = re.sub(r'[^\d+]', '', phone)
        if clean_phone.startswith('49'):
            # Remove country code for area code check
            national_part = clean_phone[2:]
        else:
            national_part = clean_phone[1:]  # Remove leading 0
        
        # Basic area code check (must start with valid digit)
        if national_part and national_part[0] not in '123456789':
            return False
        
        return True
    
    def _validate_german_area_code(self, phone: str) -> bool:
        """Validate German area code."""
        # Extract area code
        if phone.startswith('49'):
            phone = phone[2:]  # Remove country code
        elif phone.startswith('0'):
            phone = phone[1:]  # Remove national prefix
        
        # Get first 2-4 digits as area code
        area_code = phone[:4]
        
        # Common German area codes (simplified list)
        valid_area_codes = {
            '30', '40', '69', '89', '711', '211', '221', '231', '241',
            '251', '261', '271', '281', '291', '30', '31', '32', '33',
            '34', '35', '36', '37', '38', '39', '40', '41', '42', '43',
            '44', '45', '46', '47', '48', '49', '50', '51', '52', '53',
            '54', '55', '56', '57', '58', '59', '60', '61', '62', '63',
            '64', '65', '66', '67', '68', '69', '70', '71', '72', '73',
            '74', '75', '76', '77', '78', '79', '80', '81', '82', '83',
            '84', '85', '86', '87', '88', '89', '90', '91', '92', '93',
            '94', '95', '96', '97', '98', '99'
        }
        
        # Check progressively shorter area codes
        for length in range(4, 1, -1):
            if phone[:length] in valid_area_codes:
                return True
        
        return False
    
    def _is_mobile_number(self, phone: str) -> bool:
        """Check if phone number is mobile."""
        clean_phone = re.sub(r'[^\d+]', '', phone)
        
        # German mobile numbers start with 15, 16, or 17
        if (clean_phone.startswith('4915') or clean_phone.startswith('4916') or 
            clean_phone.startswith('4917') or clean_phone.startswith('015') or 
            clean_phone.startswith('016') or clean_phone.startswith('017')):
            return True
        
        return False
    
    async def _validate_form(self, contact: Contact, validation_level: str) -> ValidationResult:
        """
        Validate contact form accessibility.
        
        Args:
            contact: Form contact to validate
            validation_level: Validation level
            
        Returns:
            ValidationResult
        """
        form_url = contact.value
        errors = []
        warnings = []
        metadata = {}
        
        # Basic URL validation
        try:
            parsed = urlparse(form_url)
            if parsed.scheme not in ['http', 'https']:
                errors.append(f"Invalid form URL scheme: {parsed.scheme}")
                return ValidationResult(
                    contact=contact,
                    is_valid=False,
                    validation_method="url",
                    confidence_score=0.2,
                    errors=errors,
                    metadata=metadata
                )
        except Exception as e:
            errors.append(f"Invalid form URL: {str(e)}")
            return ValidationResult(
                contact=contact,
                is_valid=False,
                validation_method="url",
                confidence_score=0.1,
                errors=errors,
                metadata=metadata
            )
        
        # Form accessibility check (if enabled)
        if validation_level in ["standard", "comprehensive"]:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.head(form_url)
                    
                    if response.status_code >= 400:
                        errors.append(f"Form URL returned status {response.status_code}")
                        return ValidationResult(
                            contact=contact,
                            is_valid=False,
                            validation_method="accessibility",
                            confidence_score=0.3,
                            errors=errors,
                            metadata=metadata
                        )
                    
                    metadata['accessibility_check'] = True
                    metadata['response_status'] = response.status_code
                    
                    # For comprehensive validation, check actual form content
                    if validation_level == "comprehensive":
                        form_analysis = await self._analyze_form_content(form_url)
                        metadata.update(form_analysis)
                        
            except Exception as e:
                warnings.append(f"Form accessibility check failed: {str(e)}")
                metadata['accessibility_error'] = str(e)
        
        # Determine confidence score
        if errors:
            confidence = 0.2
        elif warnings:
            confidence = 0.6
        else:
            confidence = 0.8
        
        validation_method = "accessibility" if validation_level != "basic" else "url"
        
        return ValidationResult(
            contact=contact,
            is_valid=len(errors) == 0,
            validation_method=validation_method,
            confidence_score=confidence,
            errors=errors,
            warnings=warnings,
            metadata=metadata
        )
    
    async def _analyze_form_content(self, form_url: str) -> Dict[str, Any]:
        """Analyze actual form content for validation."""
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(form_url)
                response.raise_for_status()
                
                # Basic form analysis would go here
                # This is a placeholder for more sophisticated form analysis
                return {
                    'form_found': True,
                    'content_length': len(response.text),
                    'has_forms': 'form' in response.text.lower(),
                    'has_input_fields': 'input' in response.text.lower()
                }
                
        except Exception as e:
            return {
                'form_analysis_error': str(e),
                'form_found': False
            }
    
    async def _validate_website(self, contact: Contact, validation_level: str) -> ValidationResult:
        """
        Validate website accessibility.
        
        Args:
            contact: Website contact to validate
            validation_level: Validation level
            
        Returns:
            ValidationResult
        """
        website_url = contact.value
        errors = []
        warnings = []
        metadata = {}
        
        try:
            parsed = urlparse(website_url)
            if parsed.scheme not in ['http', 'https']:
                errors.append(f"Invalid website URL scheme: {parsed.scheme}")
                return ValidationResult(
                    contact=contact,
                    is_valid=False,
                    validation_method="url",
                    confidence_score=0.2,
                    errors=errors,
                    metadata=metadata
                )
        except Exception as e:
            errors.append(f"Invalid website URL: {str(e)}")
            return ValidationResult(
                contact=contact,
                is_valid=False,
                validation_method="url",
                confidence_score=0.1,
                errors=errors,
                metadata=metadata
            )
        
        # Website accessibility check
        if validation_level in ["standard", "comprehensive"]:
            try:
                async with httpx.AsyncClient(timeout=15.0) as client:
                    response = await client.get(website_url, follow_redirects=True)
                    
                    if response.status_code >= 400:
                        errors.append(f"Website returned status {response.status_code}")
                        return ValidationResult(
                            contact=contact,
                            is_valid=False,
                            validation_method="accessibility",
                            confidence_score=0.3,
                            errors=errors,
                            metadata=metadata
                        )
                    
                    metadata['accessibility_check'] = True
                    metadata['response_status'] = response.status_code
                    metadata['final_url'] = str(response.url)
                    metadata['content_type'] = response.headers.get('content-type', 'unknown')
                    
            except Exception as e:
                warnings.append(f"Website accessibility check failed: {str(e)}")
                metadata['accessibility_error'] = str(e)
        
        # Determine confidence score
        if errors:
            confidence = 0.2
        elif warnings:
            confidence = 0.7
        else:
            confidence = 0.9
        
        validation_method = "accessibility" if validation_level != "basic" else "url"
        
        return ValidationResult(
            contact=contact,
            is_valid=len(errors) == 0,
            validation_method=validation_method,
            confidence_score=confidence,
            errors=errors,
            warnings=warnings,
            metadata=metadata
        )
    
    async def _validate_social_media(self, contact: Contact, validation_level: str) -> ValidationResult:
        """
        Validate social media profile accessibility.
        
        Args:
            contact: Social media contact to validate
            validation_level: Validation level
            
        Returns:
            ValidationResult
        """
        profile_url = contact.value
        errors = []
        warnings = []
        metadata = {}
        
        try:
            parsed = urlparse(profile_url)
            if not parsed.scheme or not parsed.netloc:
                errors.append("Invalid social media URL format")
                return ValidationResult(
                    contact=contact,
                    is_valid=False,
                    validation_method="url",
                    confidence_score=0.2,
                    errors=errors,
                    metadata=metadata
                )
        except Exception as e:
            errors.append(f"Invalid social media URL: {str(e)}")
            return ValidationResult(
                contact=contact,
                is_valid=False,
                validation_method="url",
                confidence_score=0.1,
                errors=errors,
                metadata=metadata
            )
        
        # Social media accessibility check
        if validation_level in ["standard", "comprehensive"]:
            try:
                async with httpx.AsyncClient(timeout=10.0) as client:
                    response = await client.head(profile_url)
                    
                    if response.status_code == 404:
                        errors.append("Social media profile not found (404)")
                        return ValidationResult(
                            contact=contact,
                            is_valid=False,
                            validation_method="accessibility",
                            confidence_score=0.2,
                            errors=errors,
                            metadata=metadata
                        )
                    elif response.status_code >= 400:
                        warnings.append(f"Social media profile returned status {response.status_code}")
                    
                    metadata['accessibility_check'] = True
                    metadata['response_status'] = response.status_code
                    
            except Exception as e:
                warnings.append(f"Social media accessibility check failed: {str(e)}")
                metadata['accessibility_error'] = str(e)
        
        # Determine confidence score
        if errors:
            confidence = 0.2
        elif warnings:
            confidence = 0.6
        else:
            confidence = 0.8
        
        validation_method = "accessibility" if validation_level != "basic" else "url"
        
        return ValidationResult(
            contact=contact,
            is_valid=len(errors) == 0,
            validation_method=validation_method,
            confidence_score=confidence,
            errors=errors,
            warnings=warnings,
            metadata=metadata
        )
    
    async def _enforce_rate_limit(self) -> None:
        """Enforce rate limiting for validation attempts."""
        current_time = time.time()
        time_since_last = current_time - self.last_validation_time
        
        if time_since_last < self.rate_limit_seconds:
            sleep_time = self.rate_limit_seconds - time_since_last
            await asyncio.sleep(sleep_time)
        
        self.last_validation_time = time.time()
    
    def get_validation_summary(self, results: List[ValidationResult]) -> Dict[str, Any]:
        """
        Get summary of validation results.
        
        Args:
            results: List of validation results
            
        Returns:
            Summary statistics
        """
        total = len(results)
        if total == 0:
            return {'total': 0}
        
        valid_count = sum(1 for r in results if r.is_valid)
        invalid_count = total - valid_count
        
        # Group by validation method
        methods = {}
        for result in results:
            method = result.validation_method
            if method not in methods:
                methods[method] = {'valid': 0, 'invalid': 0}
            
            if result.is_valid:
                methods[method]['valid'] += 1
            else:
                methods[method]['invalid'] += 1
        
        # Calculate average confidence
        avg_confidence = sum(r.confidence_score for r in results) / total
        
        return {
            'total': total,
            'valid': valid_count,
            'invalid': invalid_count,
            'valid_percentage': (valid_count / total) * 100,
            'average_confidence': avg_confidence,
            'methods': methods,
            'validation_timestamp': datetime.now().isoformat()
        }
    
    def filter_high_confidence_contacts(self, results: List[ValidationResult], 
                                      min_confidence: float = 0.7) -> List[ValidationResult]:
        """
        Filter validation results to only include high-confidence contacts.
        
        Args:
            results: List of validation results
            min_confidence: Minimum confidence threshold
            
        Returns:
            Filtered list of high-confidence results
        """
        return [r for r in results if r.is_valid and r.confidence_score >= min_confidence]
    
    def get_recommendations(self, results: List[ValidationResult]) -> Dict[str, List[str]]:
        """
        Get recommendations for improving contact quality based on validation results.
        
        Args:
            results: List of validation results
            
        Returns:
            Dictionary with recommendations
        """
        recommendations = {
            'high_priority': [],
            'medium_priority': [],
            'low_priority': [],
            'validation_issues': []
        }
        
        summary = self.get_validation_summary(results)
        
        # High priority recommendations
        if summary['valid_percentage'] < 50:
            recommendations['high_priority'].append(
                f"Low validation success rate ({summary['valid_percentage']:.1f}%) - review extraction methods"
            )
        
        # Method-specific recommendations
        if 'dns' in summary['methods'] and summary['methods']['dns']['invalid'] > 0:
            recommendations['high_priority'].append(
                "DNS validation failures detected - check domain quality"
            )
        
        if 'smtp' in summary['methods'] and summary['methods']['smtp']['invalid'] > 0:
            recommendations['high_priority'].append(
                "SMTP validation failures detected - consider disabling for high-volume validation"
            )
        
        # Medium priority recommendations
        if summary['average_confidence'] < 0.7:
            recommendations['medium_priority'].append(
                f"Low average confidence ({summary['average_confidence']:.2f}) - consider additional verification"
            )
        
        # Validation issues
        for result in results:
            if not result.is_valid and result.errors:
                for error in result.errors:
                    if "syntax" in error.lower():
                        recommendations['validation_issues'].append("Syntax validation issues detected")
                    elif "domain" in error.lower():
                        recommendations['validation_issues'].append("Domain validation issues detected")
                    elif "format" in error.lower():
                        recommendations['validation_issues'].append("Format validation issues detected")
        
        # Remove duplicates and limit recommendations
        for key in recommendations:
            recommendations[key] = list(set(recommendations[key]))[:5]
        
        return recommendations


# Convenience functions for quick validation
async def validate_contact(contact: Contact, validation_level: str = "standard") -> ValidationResult:
    """Quick function to validate a single contact."""
    validator = ContactValidator()
    return await validator.validate_contact(contact, validation_level)


async def validate_contacts_batch(contacts: List[Contact], validation_level: str = "standard") -> List[ValidationResult]:
    """Quick function to validate multiple contacts."""
    validator = ContactValidator()
    return await validator.validate_contacts_batch(contacts, validation_level)


def is_contact_valid(contact: Contact, validation_level: str = "basic") -> bool:
    """Quick check if a contact is valid (synchronous wrapper)."""
    import asyncio
    result = asyncio.run(validate_contact(contact, validation_level))
    return result.is_valid