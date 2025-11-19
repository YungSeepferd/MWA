"""
Enhanced contact extractors for MWA Core.

Provides specialized extractors for different types of contact information:
- Email extraction with advanced obfuscation handling
- Phone number extraction for German and international formats
- Contact form detection and analysis
- Social media profile discovery
- OCR-based extraction from images
- PDF-based extraction from documents
"""

import re
import html
import logging
from typing import List, Dict, Optional, Tuple, Set, Any, Union
from pathlib import Path
from urllib.parse import urljoin, urlparse
import asyncio
from dataclasses import asdict

from bs4 import BeautifulSoup
import httpx
from PIL import Image
import fitz  # PyMuPDF

from .models import (
    Contact, ContactMethod, ContactForm, SocialMediaProfile, 
    ConfidenceLevel, DiscoveryContext, SocialMediaPlatform
)
from ..config.settings import Settings

logger = logging.getLogger(__name__)


class BaseExtractor:
    """Base class for all contact extractors."""
    
    def __init__(self, config: Settings):
        self.config = config
        self.session = httpx.AsyncClient(timeout=30.0)
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.session.aclose()
    
    def normalize_text(self, text: str) -> str:
        """
        Normalize text by removing obfuscations and cleaning up content.
        
        Args:
            text: Raw text to normalize
            
        Returns:
            Normalized text with common obfuscations resolved
        """
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Replace common email obfuscations
        text = re.sub(r'\s*\[at\]\s*', '@', text, flags=re.IGNORECASE)
        text = re.sub(r'\s*\(at\)\s*', '@', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+at\s+', '@', text, flags=re.IGNORECASE)
        text = re.sub(r'\s*\[dot\]\s*', '.', text, flags=re.IGNORECASE)
        text = re.sub(r'\s*\(dot\)\s*', '.', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+dot\s+', '.', text, flags=re.IGNORECASE)
        
        # Handle Unicode obfuscations
        text = re.sub(r'&#64;', '@', text)  # @ in HTML entities
        text = re.sub(r'&#46;', '.', text)  # . in HTML entities
        
        # Remove HTML entities
        text = html.unescape(text)
        
        # Remove common tracking/analytics markers
        text = re.sub(r'\b(noreply|no-reply|no_reply|donotreply)\b', '', text, flags=re.IGNORECASE)
        
        return text.strip()


class EmailExtractor(BaseExtractor):
    """
    Advanced email extraction with comprehensive obfuscation handling.
    
    Supports multiple email formats and obfuscation techniques:
    - Standard email patterns
    - HTML entity obfuscation
    - JavaScript obfuscation
    - Image-based email extraction
    - Unicode obfuscation
    """
    
    # Enhanced email patterns for different obfuscation techniques
    EMAIL_PATTERNS = {
        'standard': r'\b([a-zA-Z0-9][a-zA-Z0-9._%+-]*)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b',
        'obfuscated_text': [
            r'\b([a-zA-Z0-9][a-zA-Z0-9._%+-]*)\s*\[at\]\s*([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b',
            r'\b([a-zA-Z0-9][a-zA-Z0-9._%+-]*)\s*\(at\)\s*([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b',
            r'\b([a-zA-Z0-9][a-zA-Z0-9._%+-]*)\s+at\s+([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b',
            r'\b([a-zA-Z0-9][a-zA-Z0-9._%+-]*)\s*\[dot\]\s*([a-zA-Z0-9.-]+)\b',
            r'\b([a-zA-Z0-9][a-zA-Z0-9._%+-]*)\s*\(dot\)\s*([a-zA-Z0-9.-]+)\b',
        ],
        'unicode': [
            r'\b([a-zA-Z0-9][a-zA-Z0-9._%+-]*)\s*&#64;\s*([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b',  # @ as HTML entity
            r'\b([a-zA-Z0-9][a-zA-Z0-9._%+-]*)\s*&#46;\s*([a-zA-Z0-9.-]+)\b',  # . as HTML entity
        ],
        'javascript': r'document\.write\([\'"]([^\'"]+)[\'"]\)',  # Basic JS obfuscation
    }
    
    # Common German email domains for better context
    GERMAN_DOMAINS = {
        'gmx.de', 'gmx.net', 'web.de', 't-online.de', 'freenet.de',
        'yahoo.de', 'hotmail.de', 'outlook.de', 'live.de',
        'gmail.com', 'googlemail.com'
    }
    
    # Business-related domains
    BUSINESS_DOMAINS = {
        'immobilien', 'verwaltung', 'makler', 'realtor', 'estate',
        'property', 'management', 'agency', 'broker'
    }
    
    def extract_emails(self, text: str, source_url: str, context: DiscoveryContext) -> List[Contact]:
        """
        Extract email addresses from text with advanced obfuscation handling.
        
        Args:
            text: Text to analyze
            source_url: URL where text was found
            context: Discovery context
            
        Returns:
            List of Contact objects for found emails
        """
        contacts = []
        normalized_text = self.normalize_text(text)
        
        # Extract standard emails
        standard_emails = self._extract_standard_emails(normalized_text, source_url, context)
        contacts.extend(standard_emails)
        
        # Extract obfuscated emails
        obfuscated_emails = self._extract_obfuscated_emails(normalized_text, source_url, context)
        contacts.extend(obfuscated_emails)
        
        # Extract from mailto links
        if 'mailto:' in text.lower():
            mailto_emails = self._extract_mailto_emails(text, source_url, context)
            contacts.extend(mailto_emails)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_contacts = []
        for contact in contacts:
            key = (contact.method, contact.value.lower())
            if key not in seen:
                seen.add(key)
                unique_contacts.append(contact)
        
        return unique_contacts
    
    def _extract_standard_emails(self, text: str, source_url: str, context: DiscoveryContext) -> List[Contact]:
        """Extract standard format emails."""
        contacts = []
        pattern = self.EMAIL_PATTERNS['standard']
        
        for match in re.finditer(pattern, text, re.IGNORECASE):
            try:
                email = match.group()
                
                # Skip obviously invalid emails
                if not self._is_valid_email(email):
                    continue
                
                # Determine confidence based on context
                confidence = self._determine_email_confidence(email, source_url, context)
                
                contact = Contact(
                    method=ContactMethod.EMAIL,
                    value=email,
                    confidence=confidence,
                    source_url=source_url,
                    discovery_path=context.discovery_path.copy(),
                    metadata={
                        "extraction_pattern": "standard",
                        "domain": email.split('@')[1] if '@' in email else '',
                        "is_german_domain": email.split('@')[1] in self.GERMAN_DOMAINS if '@' in email else False
                    }
                )
                
                contacts.append(contact)
                
            except Exception as e:
                logger.debug(f"Error processing standard email match: {e}")
                continue
        
        return contacts
    
    def _extract_obfuscated_emails(self, text: str, source_url: str, context: DiscoveryContext) -> List[Contact]:
        """Extract obfuscated emails with various techniques."""
        contacts = []
        
        # Text-based obfuscations
        for pattern in self.EMAIL_PATTERNS['obfuscated_text']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                try:
                    # Reconstruct email from obfuscated parts
                    if len(match.groups()) == 2:
                        user, domain = match.groups()
                        email = f"{user}@{domain}"
                    else:
                        email = match.group()
                    
                    # Clean up email
                    email = re.sub(r'[.,;:!?]+$', '', email)
                    email = email.strip()
                    
                    if not self._is_valid_email(email):
                        continue
                    
                    confidence = ConfidenceLevel.MEDIUM  # Obfuscated emails get medium confidence
                    
                    contact = Contact(
                        method=ContactMethod.EMAIL,
                        value=email,
                        confidence=confidence,
                        source_url=source_url,
                        discovery_path=context.discovery_path.copy(),
                        metadata={
                            "extraction_pattern": "obfuscated_text",
                            "obfuscation_type": "text_replacement",
                            "original_text": match.group()
                        }
                    )
                    
                    contacts.append(contact)
                    
                except Exception as e:
                    continue
        
        return contacts
    
    def _extract_mailto_emails(self, text: str, source_url: str, context: DiscoveryContext) -> List[Contact]:
        """Extract emails from mailto links."""
        contacts = []
        
        # Simple mailto extraction
        mailto_pattern = r'mailto:([^\s?&"<>]+)'
        matches = re.finditer(mailto_pattern, text, re.IGNORECASE)
        
        for match in matches:
            try:
                email = match.group(1)
                
                # Clean up email (remove parameters)
                if '?' in email:
                    email = email.split('?')[0]
                
                if not self._is_valid_email(email):
                    continue
                
                contact = Contact(
                    method=ContactMethod.MAILTO,
                    value=email,
                    confidence=ConfidenceLevel.HIGH,  # Mailto links are high confidence
                    source_url=source_url,
                    discovery_path=context.discovery_path.copy(),
                    metadata={
                        "extraction_pattern": "mailto_link",
                        "source_type": "html_attribute"
                    }
                )
                
                contacts.append(contact)
                
            except Exception as e:
                continue
        
        return contacts
    
    def _is_valid_email(self, email: str) -> bool:
        """Enhanced email validation."""
        if not email or '@' not in email:
            return False
        
        # Basic format check
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False
        
        # Skip obviously invalid domains
        invalid_domains = ['example.com', 'test.com', 'localhost', 'domain.com', 'email.com']
        domain = email.split('@')[1].lower()
        if domain in invalid_domains:
            return False
        
        # Check for excessive length
        if len(email) > 254 or len(email.split('@')[0]) > 64:
            return False
        
        return True
    
    def _determine_email_confidence(self, email: str, source_url: str, context: DiscoveryContext) -> ConfidenceLevel:
        """Determine confidence level for email extraction."""
        # Mailto links are high confidence
        if 'mailto' in source_url.lower():
            return ConfidenceLevel.HIGH
        
        # Email in specific contact contexts
        contact_keywords = ['contact', 'kontakt', 'impressum', 'about', 'uber', 'team']
        if any(keyword in source_url.lower() for keyword in contact_keywords):
            return ConfidenceLevel.HIGH
        
        # German domain emails in German context
        domain = email.split('@')[1] if '@' in email else ''
        if domain in self.GERMAN_DOMAINS and context.cultural_context == 'german':
            return ConfidenceLevel.HIGH
        
        # Business-related domains
        if any(business in domain for business in self.BUSINESS_DOMAINS):
            return ConfidenceLevel.HIGH
        
        # Standard text extraction
        return ConfidenceLevel.MEDIUM


class PhoneExtractor(BaseExtractor):
    """
    Advanced phone number extraction for German and international formats.
    
    Supports multiple phone number formats and validation techniques:
    - German national formats
    - International formats
    - Mobile number formats
    - Landline formats
    - Area code validation
    """
    
    # Enhanced phone patterns for different formats
    PHONE_PATTERNS = {
        'german_national': [
            r'(\+49\s?0?\s?[1-9]\d{1,4}\s?\d{3,}\s?\d{3,})',  # +49 format
            r'(0049\s?0?\s?[1-9]\d{1,4}\s?\d{3,}\s?\d{3,})',   # 0049 format
            r'(0\s?[1-9]\d{1,4}\s?\d{3,}\s?\d{3,})',            # National format
        ],
        'german_mobile': [
            r'(\+49\s?0?\s?1[5-7]\d{1,3}\s?\d{3,}\s?\d{3,})',   # German mobile
            r'(0\s?1[5-7]\d{1,3}\s?\d{3,}\s?\d{3,})',            # National mobile
        ],
        'munich_local': [
            r'(\(089\)\s?\d{3,}\s?\d{3,})',                      # (089) format
            r'(089\s?\d{3,}\s?\d{3,})',                           # 089 format
            r'(\+49\s?89\s?\d{3,}\s?\d{3,})',                    # +49 89 format
        ],
        'international': [
            r'(\+\d{1,3}\s?\d{2,}\s?\d{3,}\s?\d{3,})',           # International
            r'(00\d{1,3}\s?\d{2,}\s?\d{3,}\s?\d{3,})',           # International 00
        ],
        'generic': [
            r'\b(\d{4,}\s?\d{3,}\s?\d{3,})\b',                   # Generic long numbers
        ]
    }
    
    # German area codes for validation
    GERMAN_AREA_CODES = {
        '089', '030', '040', '069', '0711', '0211', '0221', '0231', '0241',
        '0251', '0261', '0271', '0281', '0291', '031', '033', '034', '035',
        '036', '037', '038', '039', '041', '042', '043', '044', '045', '046',
        '047', '048', '049', '051', '052', '053', '054', '055', '056', '057',
        '058', '059', '060', '061', '062', '063', '064', '065', '066', '067',
        '068', '069', '070', '071', '072', '073', '074', '075', '076', '077',
        '078', '079', '080', '081', '082', '083', '084', '085', '086', '087',
        '088', '089', '090', '091', '092', '093', '094', '095', '096', '097',
        '098', '099'
    }
    
    def extract_phones(self, text: str, source_url: str, context: DiscoveryContext) -> List[Contact]:
        """
        Extract phone numbers from text with German and international format support.
        
        Args:
            text: Text to analyze
            source_url: URL where text was found
            context: Discovery context
            
        Returns:
            List of Contact objects for found phone numbers
        """
        contacts = []
        
        # Extract German national numbers
        german_numbers = self._extract_german_phones(text, source_url, context)
        contacts.extend(german_numbers)
        
        # Extract Munich local numbers
        munich_numbers = self._extract_munich_phones(text, source_url, context)
        contacts.extend(munich_numbers)
        
        # Extract international numbers
        international_numbers = self._extract_international_phones(text, source_url, context)
        contacts.extend(international_numbers)
        
        # Extract mobile numbers
        mobile_numbers = self._extract_mobile_phones(text, source_url, context)
        contacts.extend(mobile_numbers)
        
        # Remove duplicates
        seen = set()
        unique_contacts = []
        for contact in contacts:
            key = (contact.method, contact.value)
            if key not in seen:
                seen.add(key)
                unique_contacts.append(contact)
        
        return unique_contacts
    
    def _extract_german_phones(self, text: str, source_url: str, context: DiscoveryContext) -> List[Contact]:
        """Extract German national format phone numbers."""
        contacts = []
        
        for pattern in self.PHONE_PATTERNS['german_national']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                try:
                    phone = match.group().strip()
                    
                    # Clean up phone number
                    phone = re.sub(r'[^\d+]', '', phone)
                    
                    # Validate German phone format
                    if not self._is_valid_german_phone(phone):
                        continue
                    
                    confidence = self._determine_phone_confidence(phone, source_url, context, 'german')
                    
                    contact = Contact(
                        method=ContactMethod.PHONE,
                        value=phone,
                        confidence=confidence,
                        source_url=source_url,
                        discovery_path=context.discovery_path.copy(),
                        metadata={
                            "extraction_pattern": "german_national",
                            "format": "national",
                            "area_code": self._extract_area_code(phone)
                        }
                    )
                    
                    contacts.append(contact)
                    
                except Exception as e:
                    continue
        
        return contacts
    
    def _extract_munich_phones(self, text: str, source_url: str, context: DiscoveryContext) -> List[Contact]:
        """Extract Munich-specific phone numbers."""
        contacts = []
        
        for pattern in self.PHONE_PATTERNS['munich_local']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                try:
                    phone = match.group().strip()
                    phone = re.sub(r'[^\d+]', '', phone)
                    
                    if not phone.startswith('089') or len(phone) < 10:
                        continue
                    
                    contact = Contact(
                        method=ContactMethod.PHONE,
                        value=phone,
                        confidence=ConfidenceLevel.HIGH,  # Munich numbers are high confidence
                        source_url=source_url,
                        discovery_path=context.discovery_path.copy(),
                        metadata={
                            "extraction_pattern": "munich_local",
                            "format": "local",
                            "area_code": "089",
                            "is_munich": True
                        }
                    )
                    
                    contacts.append(contact)
                    
                except Exception as e:
                    continue
        
        return contacts
    
    def _extract_international_phones(self, text: str, source_url: str, context: DiscoveryContext) -> List[Contact]:
        """Extract international format phone numbers."""
        contacts = []
        
        for pattern in self.PHONE_PATTERNS['international']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                try:
                    phone = match.group().strip()
                    phone = re.sub(r'[^\d+]', '', phone)
                    
                    if not self._is_valid_international_phone(phone):
                        continue
                    
                    confidence = self._determine_phone_confidence(phone, source_url, context, 'international')
                    
                    contact = Contact(
                        method=ContactMethod.PHONE,
                        value=phone,
                        confidence=confidence,
                        source_url=source_url,
                        discovery_path=context.discovery_path.copy(),
                        metadata={
                            "extraction_pattern": "international",
                            "format": "international",
                            "country_code": self._extract_country_code(phone)
                        }
                    )
                    
                    contacts.append(contact)
                    
                except Exception as e:
                    continue
        
        return contacts
    
    def _extract_mobile_phones(self, text: str, source_url: str, context: DiscoveryContext) -> List[Contact]:
        """Extract mobile phone numbers."""
        contacts = []
        
        for pattern in self.PHONE_PATTERNS['german_mobile']:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                try:
                    phone = match.group().strip()
                    phone = re.sub(r'[^\d+]', '', phone)
                    
                    # German mobile numbers start with 15, 16, or 17
                    if not (phone.startswith('+4915') or phone.startswith('+4916') or phone.startswith('+4917') or
                            phone.startswith('015') or phone.startswith('016') or phone.startswith('017')):
                        continue
                    
                    contact = Contact(
                        method=ContactMethod.PHONE,
                        value=phone,
                        confidence=ConfidenceLevel.HIGH,  # Mobile numbers are high confidence
                        source_url=source_url,
                        discovery_path=context.discovery_path.copy(),
                        metadata={
                            "extraction_pattern": "german_mobile",
                            "format": "mobile",
                            "is_mobile": True
                        }
                    )
                    
                    contacts.append(contact)
                    
                except Exception as e:
                    continue
        
        return contacts
    
    def _is_valid_german_phone(self, phone: str) -> bool:
        """Validate German phone number format."""
        if len(phone) < 10 or len(phone) > 15:
            return False
        
        # Check for valid German area codes
        if phone.startswith('0'):
            area_code = phone[1:4] if len(phone) > 4 else phone[1:]
            if area_code not in self.GERMAN_AREA_CODES:
                return False
        
        return True
    
    def _is_valid_international_phone(self, phone: str) -> bool:
        """Validate international phone number format."""
        if len(phone) < 8 or len(phone) > 16:
            return False
        
        # Must start with + or 00
        if not (phone.startswith('+') or phone.startswith('00')):
            return False
        
        return True
    
    def _extract_area_code(self, phone: str) -> Optional[str]:
        """Extract area code from German phone number."""
        if phone.startswith('+49'):
            # International format
            match = re.match(r'\+49\s?0?(\d{2,4})', phone)
            return match.group(1) if match else None
        elif phone.startswith('0'):
            # National format
            match = re.match(r'0(\d{2,4})', phone)
            return match.group(1) if match else None
        return None
    
    def _extract_country_code(self, phone: str) -> Optional[str]:
        """Extract country code from international phone number."""
        if phone.startswith('+'):
            match = re.match(r'\+(\d{1,3})', phone)
            return match.group(1) if match else None
        elif phone.startswith('00'):
            match = re.match(r'00(\d{1,3})', phone)
            return match.group(1) if match else None
        return None
    
    def _determine_phone_confidence(self, phone: str, source_url: str, context: DiscoveryContext, phone_type: str) -> ConfidenceLevel:
        """Determine confidence level for phone extraction."""
        # Munich numbers are high confidence
        if '089' in phone:
            return ConfidenceLevel.HIGH
        
        # German mobile numbers are high confidence
        if phone_type == 'mobile':
            return ConfidenceLevel.HIGH
        
        # Phone numbers in contact contexts
        contact_keywords = ['contact', 'kontakt', 'impressum', 'about', 'telefon', 'phone']
        if any(keyword in source_url.lower() for keyword in contact_keywords):
            return ConfidenceLevel.HIGH
        
        # German context with German numbers
        if context.cultural_context == 'german' and phone_type == 'german':
            return ConfidenceLevel.HIGH
        
        return ConfidenceLevel.MEDIUM


class FormExtractor(BaseExtractor):
    """
    Advanced contact form detection and analysis.
    
    Provides comprehensive form analysis including:
    - Form field detection
    - Required field analysis
    - CSRF token detection
    - Form complexity scoring
    - User-friendliness assessment
    """
    
    # Keywords that indicate contact forms
    CONTACT_FORM_KEYWORDS = {
        'contact', 'kontakt', 'message', 'nachricht', 'feedback', 'anfrage',
        'inquiry', 'support', 'help', 'assistance', 'question', 'frage'
    }
    
    # Field names that indicate contact forms
    CONTACT_FIELD_INDICATORS = {
        'name', 'email', 'message', 'subject', 'phone', 'telefon',
        'nachricht', 'betreff', 'anfrage', 'comment', 'text'
    }
    
    # Required field indicators
    REQUIRED_INDICATORS = {
        'required', 'aria-required', 'mandatory', 'pflicht', '*required'
    }
    
    def extract_forms(self, soup: BeautifulSoup, source_url: str, context: DiscoveryContext) -> List[ContactForm]:
        """
        Extract and analyze contact forms from HTML.
        
        Args:
            soup: BeautifulSoup object of the page
            source_url: URL of the page
            context: Discovery context
            
        Returns:
            List of ContactForm objects
        """
        forms = []
        
        # Find all forms
        form_elements = soup.find_all('form')
        
        for form in form_elements:
            try:
                form_obj = self._analyze_form(form, source_url, context)
                if form_obj:
                    forms.append(form_obj)
                    
            except Exception as e:
                logger.debug(f"Error analyzing form: {e}")
                continue
        
        return forms
    
    def _analyze_form(self, form, source_url: str, context: DiscoveryContext) -> Optional[ContactForm]:
        """Analyze a single form for contact characteristics."""
        try:
            # Extract basic form attributes
            action_url = form.get('action', '').strip()
            method = form.get('method', 'POST').upper()
            
            # Resolve relative URLs
            if action_url and not action_url.startswith(('http://', 'https://')):
                action_url = urljoin(source_url, action_url)
            elif not action_url:
                # Use current page as action if no action specified
                action_url = source_url
            
            # Extract form fields
            fields = []
            required_fields = []
            
            # Find all input elements
            inputs = form.find_all(['input', 'textarea', 'select'])
            
            for input_elem in inputs:
                field_name = input_elem.get('name')
                if not field_name:
                    continue
                
                fields.append(field_name)
                
                # Check if field is required
                if self._is_required_field(input_elem):
                    required_fields.append(field_name)
            
            # Extract CSRF token if present
            csrf_token = self._extract_csrf_token(form)
            
            # Determine if this is a contact form
            if not self._is_contact_form(form, fields):
                return None
            
            # Calculate complexity and user-friendliness scores
            complexity_score = self._calculate_complexity_score(fields, required_fields)
            user_friendly_score = self._calculate_user_friendly_score(form, fields)
            
            # Determine confidence
            confidence = self._determine_form_confidence(form, fields, source_url)
            
            form_obj = ContactForm(
                action_url=action_url,
                method=method,
                fields=fields,
                required_fields=required_fields,
                csrf_token=csrf_token,
                source_url=source_url,
                confidence=confidence,
                complexity_score=complexity_score,
                user_friendly_score=user_friendly_score,
                metadata={
                    "form_id": form.get('id'),
                    "form_class": form.get('class'),
                    "total_fields": len(fields),
                    "required_fields_count": len(required_fields)
                }
            )
            
            return form_obj
            
        except Exception as e:
            logger.debug(f"Form analysis failed: {e}")
            return None
    
    def _is_required_field(self, input_elem) -> bool:
        """Check if an input field is required."""
        # Check standard required attribute
        if input_elem.get('required') is not None:
            return True
        
        # Check ARIA required
        if input_elem.get('aria-required') == 'true':
            return True
        
        # Check for asterisk in labels
        labels = input_elem.find_parent('form').find_all('label')
        for label in labels:
            if 'for' in label.attrs and label['for'] == input_elem.get('id', ''):
                if '*' in label.get_text():
                    return True
        
        # Check field name against common required fields
        field_name = input_elem.get('name', '').lower()
        if field_name in ['name', 'email', 'message', 'subject']:
            return True
        
        return False
    
    def _extract_csrf_token(self, form) -> Optional[str]:
        """Extract CSRF token from form."""
        # Look for common CSRF token field names
        csrf_patterns = [
            r'csrf', r'token', r'_token', r'authenticity_token',
            r'__RequestVerificationToken', r'csrf_token'
        ]
        
        inputs = form.find_all('input', {'type': 'hidden'})
        
        for input_elem in inputs:
            name = input_elem.get('name', '').lower()
            for pattern in csrf_patterns:
                if re.search(pattern, name):
                    return input_elem.get('value')
        
        return None
    
    def _is_contact_form(self, form, fields: List[str]) -> bool:
        """Determine if a form is likely a contact form."""
        # Check form text for contact keywords
        form_text = form.get_text(strip=True).lower()
        if any(keyword in form_text for keyword in self.CONTACT_FORM_KEYWORDS):
            return True
        
        # Check field names for contact indicators
        field_names = [field.lower() for field in fields]
        contact_fields = sum(1 for field in field_names if field in self.CONTACT_FIELD_INDICATORS)
        
        if contact_fields >= 2:  # At least 2 contact-related fields
            return True
        
        # Check for email and message fields (strong indicator)
        has_email = any('email' in field for field in field_names)
        has_message = any(msg in field for field in field_names for msg in ['message', 'nachricht', 'text'])
        
        if has_email and has_message:
            return True
        
        return False
    
    def _calculate_complexity_score(self, fields: List[str], required_fields: List[str]) -> float:
        """Calculate form complexity score (0-1)."""
        if not fields:
            return 0.0
        
        # Base complexity from number of fields
        field_complexity = min(len(fields) / 10, 1.0)  # Normalize to 10 fields max
        
        # Required field complexity
        required_ratio = len(required_fields) / len(fields) if fields else 0
        required_complexity = required_ratio
        
        # Field type complexity
        complex_fields = ['file', 'date', 'datetime', 'select', 'radio', 'checkbox']
        complex_count = sum(1 for field in fields if any(cf in field.lower() for cf in complex_fields))
        type_complexity = min(complex_count / 3, 1.0)
        
        # Combine scores
        return (field_complexity + required_complexity + type_complexity) / 3
    
    def _calculate_user_friendly_score(self, form, fields: List[str]) -> float:
        """Calculate user-friendliness score (0-1)."""
        score = 0.5  # Base score
        
        # Check for labels
        labels = form.find_all('label')
        if labels:
            score += 0.2
        
        # Check for placeholder text
        inputs_with_placeholder = form.find_all(attrs={'placeholder': True})
        if inputs_with_placeholder:
            score += 0.1
        
        # Check for fieldsets/organization
        fieldsets = form.find_all('fieldset')
        if fieldsets:
            score += 0.1
        
        # Check for help text
        help_texts = form.find_all(class_=re.compile(r'help|hint|info'))
        if help_texts:
            score += 0.1
        
        return min(score, 1.0)
    
    def _determine_form_confidence(self, form, fields: List[str], source_url: str) -> ConfidenceLevel:
        """Determine confidence level for form extraction."""
        # Forms on contact pages are high confidence
        contact_keywords = ['contact', 'kontakt', 'impressum']
        if any(keyword in source_url.lower() for keyword in contact_keywords):
            return ConfidenceLevel.HIGH
        
        # Forms with email and message fields are high confidence
        field_names = [field.lower() for field in fields]
        has_email = any('email' in field for field in field_names)
        has_message = any(msg in field for field in field_names for msg in ['message', 'nachricht'])
        
        if has_email and has_message:
            return ConfidenceLevel.HIGH
        
        # Forms with multiple contact indicators are medium confidence
        contact_indicators = sum(1 for field in field_names if field in self.CONTACT_FIELD_INDICATORS)
        if contact_indicators >= 3:
            return ConfidenceLevel.MEDIUM
        
        return ConfidenceLevel.LOW


class SocialMediaExtractor(BaseExtractor):
    """
    Social media profile discovery and extraction.
    
    Supports major social media platforms:
    - Facebook
    - Instagram
    - Twitter
    - LinkedIn
    - WhatsApp
    - Telegram
    - XING (German professional network)
    """
    
    # Platform-specific patterns
    PLATFORM_PATTERNS = {
        SocialMediaPlatform.FACEBOOK: [
            r'facebook\.com/([a-zA-Z0-9._-]+)',
            r'fb\.com/([a-zA-Z0-9._-]+)',
            r'facebook\.com/pages/([a-zA-Z0-9._-]+)',
        ],
        SocialMediaPlatform.INSTAGRAM: [
            r'instagram\.com/([a-zA-Z0-9._-]+)',
            r'instagr\.am/([a-zA-Z0-9._-]+)',
        ],
        SocialMediaPlatform.TWITTER: [
            r'twitter\.com/([a-zA-Z0-9._-]+)',
            r'x\.com/([a-zA-Z0-9._-]+)',
        ],
        SocialMediaPlatform.LINKEDIN: [
            r'linkedin\.com/in/([a-zA-Z0-9._-]+)',
            r'linkedin\.com/company/([a-zA-Z0-9._-]+)',
        ],
        SocialMediaPlatform.WHATSAPP: [
            r'whatsapp\.com/([a-zA-Z0-9._-]+)',
            r'wa\.me/([a-zA-Z0-9._-]+)',
            r'api\.whatsapp\.com/send\?phone=([0-9+]+)',
        ],
        SocialMediaPlatform.TELEGRAM: [
            r't\.me/([a-zA-Z0-9._-]+)',
            r'telegram\.me/([a-zA-Z0-9._-]+)',
        ],
        SocialMediaPlatform.XING: [
            r'xing\.com/profile/([a-zA-Z0-9._-]+)',
            r'xing\.com/companies/([a-zA-Z0-9._-]+)',
        ],
    }
    
    # Business-related keywords for profile filtering
    BUSINESS_KEYWORDS = {
        'immobilien', 'verwaltung', 'makler', 'realtor', 'estate',
        'property', 'management', 'agency', 'broker', 'realty'
    }
    
    def extract_social_media(self, text: str, source_url: str, context: DiscoveryContext) -> List[SocialMediaProfile]:
        """
        Extract social media profiles from text.
        
        Args:
            text: Text to analyze
            source_url: URL where text was found
            context: Discovery context
            
        Returns:
            List of SocialMediaProfile objects
        """
        profiles = []
        
        for platform, patterns in self.PLATFORM_PATTERNS.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                
                for match in matches:
                    try:
                        username = match.group(1)
                        
                        # Construct full profile URL
                        profile_url = self._construct_profile_url(platform, username)
                        
                        # Extract display name if available
                        display_name = self._extract_display_name(text, match)
                        
                        # Determine confidence
                        confidence = self._determine_social_confidence(platform, username, source_url)
                        
                        profile = SocialMediaProfile(
                            platform=platform,
                            username=username,
                            profile_url=profile_url,
                            display_name=display_name,
                            source_url=source_url,
                            confidence=confidence,
                            metadata={
                                "extraction_pattern": pattern,
                                "is_business_related": self._is_business_profile(username, display_name)
                            }
                        )
                        
                        profiles.append(profile)
                        
                    except Exception as e:
                        continue
        
        # Remove duplicates
        seen = set()
        unique_profiles = []
        for profile in profiles:
            key = (profile.platform, profile.username)
            if key not in seen:
                seen.add(key)
                unique_profiles.append(profile)
        
        return unique_profiles
    
    def _construct_profile_url(self, platform: SocialMediaPlatform, username: str) -> str:
        """Construct full profile URL from platform and username."""
        base_urls = {
            SocialMediaPlatform.FACEBOOK: f"https://facebook.com/{username}",
            SocialMediaPlatform.INSTAGRAM: f"https://instagram.com/{username}",
            SocialMediaPlatform.TWITTER: f"https://twitter.com/{username}",
            SocialMediaPlatform.LINKEDIN: f"https://linkedin.com/in/{username}",
            SocialMediaPlatform.WHATSAPP: f"https://wa.me/{username}",
            SocialMediaPlatform.TELEGRAM: f"https://t.me/{username}",
            SocialMediaPlatform.XING: f"https://xing.com/profile/{username}",
        }
        
        return base_urls.get(platform, f"https://{platform.value}.com/{username}")
    
    def _extract_display_name(self, text: str, match) -> Optional[str]:
        """Extract display name from surrounding text."""
        try:
            # Get text around the match
            start = max(0, match.start() - 100)
            end = min(len(text), match.end() + 100)
            context_text = text[start:end]
            
            # Look for name patterns
            name_pattern = r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)'
            name_matches = re.findall(name_pattern, context_text)
            
            if name_matches:
                return name_matches[0]
            
        except Exception:
            pass
        
        return None
    
    def _determine_social_confidence(self, platform: SocialMediaPlatform, username: str, source_url: str) -> ConfidenceLevel:
        """Determine confidence level for social media profile."""
        # Business-related platforms are high confidence
        if platform in [SocialMediaPlatform.LINKEDIN, SocialMediaPlatform.XING]:
            return ConfidenceLevel.HIGH
        
        # Social media in contact contexts
        contact_keywords = ['contact', 'kontakt', 'impressum', 'about', 'social']
        if any(keyword in source_url.lower() for keyword in contact_keywords):
            return ConfidenceLevel.HIGH
        
        # Business-related usernames
        if any(keyword in username.lower() for keyword in self.BUSINESS_KEYWORDS):
            return ConfidenceLevel.HIGH
        
        return ConfidenceLevel.MEDIUM
    
    def _is_business_profile(self, username: str, display_name: Optional[str]) -> bool:
        """Check if profile appears to be business-related."""
        text_to_check = f"{username} {display_name or ''}".lower()
        return any(keyword in text_to_check for keyword in self.BUSINESS_KEYWORDS)


class OCRContactExtractor(BaseExtractor):
    """
    OCR-based contact extraction from images.
    
    Uses Tesseract OCR to extract contact information from:
    - Business cards
    - Contact banners
    - Screenshots with contact info
    - Scanned documents
    """
    
    def __init__(self, config: Settings, languages: Optional[List[str]] = None):
        super().__init__(config)
        self.languages = languages or ['deu', 'eng']
        
        # Try to import pytesseract
        try:
            import pytesseract
            self.pytesseract = pytesseract
        except ImportError:
            logger.warning("pytesseract not installed. OCR extraction will be disabled.")
            self.pytesseract = None
    
    def can_process(self, source: Union[str, Path, bytes]) -> bool:
        """Check if the source can be processed by OCR."""
        if not self.pytesseract:
            return False
        
        if isinstance(source, str):
            if source.startswith(('http://', 'https://')):
                parsed = urlparse(source)
                ext = Path(parsed.path).suffix.lower()
                return ext in ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff']
            else:
                path = Path(source)
                return path.exists() and path.suffix.lower() in ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff']
        elif isinstance(source, (Path, bytes)):
            return True
        
        return False
    
    async def extract_from_image(self, image_source: Union[str, Path, bytes], source_url: str, context: DiscoveryContext) -> List[Contact]:
        """
        Extract contacts from image using OCR.
        
        Args:
            image_source: Image URL, file path, or image data
            source_url: URL where image was found
            context: Discovery context
            
        Returns:
            List of Contact objects
        """
        if not self.pytesseract:
            return []
        
        try:
            # Load and preprocess image
            image = self._load_image(image_source)
            if not image:
                return []
            
            # Enhance image for better OCR
            enhanced_image = self._enhance_image(image)
            
            # Extract text using OCR
            ocr_text = self._extract_text(enhanced_image)
            if not ocr_text:
                return []
            
            logger.debug(f"OCR extracted text: {ocr_text[:200]}...")
            
            # Extract contacts from OCR text
            contacts = []
            
            # Use email extractor on OCR text
            email_extractor = EmailExtractor(self.config)
            emails = email_extractor.extract_emails(ocr_text, source_url, context)
            contacts.extend(emails)
            
            # Use phone extractor on OCR text
            phone_extractor = PhoneExtractor(self.config)
            phones = phone_extractor.extract_phones(ocr_text, source_url, context)
            contacts.extend(phones)
            
            # Mark contacts as OCR-extracted
            for contact in contacts:
                contact.extraction_method = "ocr"
                contact.metadata["ocr_extracted"] = True
            
            logger.info(f"OCR extraction found {len(contacts)} contacts")
            return contacts
            
        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return []
    
    def _load_image(self, source: Union[str, Path, bytes]) -> Optional[Image.Image]:
        """Load image from various sources."""
        try:
            if isinstance(source, str) and source.startswith(('http://', 'https://')):
                # Download image from URL
                response = httpx.get(source, timeout=10)
                response.raise_for_status()
                return Image.open(BytesIO(response.content))
            elif isinstance(source, (str, Path)):
                return Image.open(source)
            elif isinstance(source, bytes):
                from io import BytesIO
                return Image.open(BytesIO(source))
            else:
                return None
        except Exception as e:
            logger.error(f"Failed to load image: {e}")
            return None
    
    def _enhance_image(self, image: Image.Image) -> Image.Image:
        """Enhance image for better OCR results."""
        try:
            # Convert to RGB if necessary
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Enhance contrast
            from PIL import ImageEnhance
            enhancer = ImageEnhance.Contrast(image)
            image = enhancer.enhance(1.5)
            
            # Resize if too small
            width, height = image.size
            if width < 800 or height < 600:
                image = image.resize((width * 2, height * 2), Image.Resampling.LANCZOS)
            
            return image
            
        except Exception as e:
            logger.warning(f"Image enhancement failed: {e}")
            return image
    
    def _extract_text(self, image: Image.Image) -> str:
        """Extract text from image using OCR."""
        try:
            config = f'-l {"+".join(self.languages)} --psm 3'
            text = self.pytesseract.image_to_string(image, config=config)
            return text.strip()
        except Exception as e:
            logger.error(f"OCR text extraction failed: {e}")
            return ""


class PDFContactExtractor(BaseExtractor):
    """
    PDF-based contact extraction from documents.
    
    Extracts contact information from PDF files including:
    - Text content
    - Table data
    - Metadata
    - OCR for scanned documents
    """
    
    def __init__(self, config: Settings, max_file_size_mb: int = 10):
        super().__init__(config)
        self.max_file_size_mb = max_file_size_mb
    
    def can_process(self, source: Union[str, Path, bytes]) -> bool:
        """Check if the source can be processed as PDF."""
        if isinstance(source, str):
            if source.startswith(('http://', 'https://')):
                parsed = urlparse(source)
                return Path(parsed.path).suffix.lower() == '.pdf'
            else:
                path = Path(source)
                return path.exists() and path.suffix.lower() == '.pdf'
        elif isinstance(source, Path):
            return source.suffix.lower() == '.pdf'
        elif isinstance(source, bytes):
            return source.startswith(b'%PDF')
        
        return False
    
    async def extract_from_pdf(self, pdf_source: Union[str, Path, bytes], source_url: str, context: DiscoveryContext) -> List[Contact]:
        """
        Extract contacts from PDF document.
        
        Args:
            pdf_source: PDF URL, file path, or PDF data
            source_url: URL where PDF was found
            context: Discovery context
            
        Returns:
            List of Contact objects
        """
        try:
            # Load PDF document
            pdf_document = self._load_pdf(pdf_source)
            if not pdf_document:
                return []
            
            contacts = []
            
            # Extract text from PDF
            pdf_text = self._extract_text(pdf_document)
            if pdf_text:
                # Use email extractor on PDF text
                email_extractor = EmailExtractor(self.config)
                emails = email_extractor.extract_emails(pdf_text, source_url, context)
                contacts.extend(emails)
                
                # Use phone extractor on PDF text
                phone_extractor = PhoneExtractor(self.config)
                phones = phone_extractor.extract_phones(pdf_text, source_url, context)
                contacts.extend(phones)
            
            # Extract from PDF metadata
            metadata_contacts = self._extract_from_metadata(pdf_document, source_url, context)
            contacts.extend(metadata_contacts)
            
            # Mark contacts as PDF-extracted
            for contact in contacts:
                contact.extraction_method = "pdf"
                contact.metadata["pdf_extracted"] = True
            
            logger.info(f"PDF extraction found {len(contacts)} contacts")
            return contacts
            
        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            return []
    
    def _load_pdf(self, source: Union[str, Path, bytes]) -> Optional[fitz.Document]:
        """Load PDF from various sources."""
        try:
            if isinstance(source, str) and source.startswith(('http://', 'https://')):
                # Download PDF from URL
                response = httpx.get(source, timeout=30)
                response.raise_for_status()
                
                # Save to temporary file
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                    tmp_file.write(response.content)
                    tmp_path = tmp_file.name
                
                # Load from temporary file
                pdf_document = fitz.open(tmp_path)
                
                # Clean up temp file
                Path(tmp_path).unlink()
                
                return pdf_document
            elif isinstance(source, (str, Path)):
                return fitz.open(str(source))
            elif isinstance(source, bytes):
                # Save to temporary file
                import tempfile
                with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                    tmp_file.write(source)
                    tmp_path = tmp_file.name
                
                # Load from temporary file
                pdf_document = fitz.open(tmp_path)
                
                # Clean up temp file
                Path(tmp_path).unlink()
                
                return pdf_document
            else:
                return None
        except Exception as e:
            logger.error(f"Failed to load PDF: {e}")
            return None
    
    def _extract_text(self, pdf_document: fitz.Document) -> str:
        """Extract text from PDF document."""
        try:
            text_parts = []
            
            for page_num in range(len(pdf_document)):
                page = pdf_document[page_num]
                page_text = page.get_text()
                
                if page_text.strip():
                    text_parts.append(page_text)
            
            return '\n'.join(text_parts)
        except Exception as e:
            logger.error(f"PDF text extraction failed: {e}")
            return ""
    
    def _extract_from_metadata(self, pdf_document: fitz.Document, source_url: str, context: DiscoveryContext) -> List[Contact]:
        """Extract contacts from PDF metadata."""
        contacts = []
        
        try:
            metadata = pdf_document.metadata
            
            if metadata:
                # Check author field
                if metadata.get('author'):
                    author_text = metadata['author']
                    
                    email_extractor = EmailExtractor(self.config)
                    emails = email_extractor.extract_emails(author_text, source_url, context)
                    contacts.extend(emails)
                    
                    phone_extractor = PhoneExtractor(self.config)
                    phones = phone_extractor.extract_phones(author_text, source_url, context)
                    contacts.extend(phones)
                
                # Check creator field
                if metadata.get('creator'):
                    creator_text = metadata['creator']
                    
                    email_extractor = EmailExtractor(self.config)
                    emails = email_extractor.extract_emails(creator_text, source_url, context)
                    contacts.extend(emails)
                    
                    phone_extractor = PhoneExtractor(self.config)
                    phones = phone_extractor.extract_phones(creator_text, source_url, context)
                    contacts.extend(phones)
        
        except Exception as e:
            logger.warning(f"PDF metadata extraction failed: {e}")
        
        return contacts