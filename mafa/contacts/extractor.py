"""
Contact extraction engine for MAFA.

Provides comprehensive contact information extraction from web pages,
including email addresses, phone numbers, contact forms, and other contact pathways.
"""

import re
import html
import httpx
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from typing import List, Dict, Set, Optional, Tuple
from pathlib import Path
import asyncio
from dataclasses import asdict

from .models import Contact, ContactMethod, ConfidenceLevel, DiscoveryContext, ContactForm
from ..exceptions import ScrapingError
from ..security import SecurityValidator
from ..config.settings import Settings


class ContactExtractor:
    """
    Main contact extraction engine.
    
    Handles multiple extraction strategies:
    - Direct email/phone extraction from HTML
    - Mailto link extraction
    - Contact form detection
    - Link following to contact pages
    - PDF and image parsing (planned)
    """
    
    # Email extraction patterns
    EMAIL_PATTERNS = [
        # Standard email pattern with obfuscation handling
        r'\b([a-zA-Z0-9][a-zA-Z0-9._%+-]*)@([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b',
        # Obfuscated email patterns
        r'\b([a-zA-Z0-9][a-zA-Z0-9._%+-]*)\s*\[at\]\s*([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b',
        r'\b([a-zA-Z0-9][a-zA-Z0-9._%+-]*)\s*\(at\)\s*([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b',
        r'\b([a-zA-Z0-9][a-zA-Z0-9._%+-]*)\s+at\s+([a-zA-Z0-9.-]+\.[a-zA-Z]{2,})\b',
        r'\b([a-zA-Z0-9][a-zA-Z0-9._%+-]*)\s*\[dot\]\s*([a-zA-Z0-9.-]+)\b',
        r'\b([a-zA-Z0-9][a-zA-Z0-9._%+-]*)\s*\(dot\)\s*([a-zA-Z0-9.-]+)\b',
    ]
    
    # Phone number patterns (German focus)
    PHONE_PATTERNS = [
        r'\b(\+49\s?0?\s?\d{2,4}\s?\d{3,}\s?\d{3,})\b',  # German formats
        r'\b(0\d{2,4}\s?\d{3,}\s?\d{3,})\b',  # German local formats
        r'\b(\d{4}\s?\d{3,}\s?\d{3,})\b',  # Generic formats
        r'\b(\+\d{1,3}\s?\d{2,}\s?\d{3,}\s?\d{3,})\b',  # International
    ]
    
    # Contact keywords for page identification
    CONTACT_KEYWORDS = [
        'kontakt', 'contact', 'impressum', 'about', 'über', 'contactus',
        'vermieter', 'hausverwaltung', 'landlord', 'owner', 'agenzia',
        'kontaktformular', 'kontaktseite', 'kontaktseite', 'contactform'
    ]
    
    # Contact page URL patterns
    CONTACT_URL_PATTERNS = [
        r'/kontakt',
        r'/contact',
        r'/impressum',
        r'/about',
        r'/uber',
        r'/contact-us',
        r'/contactus',
        r'/kontaktformular',
        r'/contact-form',
        r'/vermieter',
        r'/landlord',
        r'/owner'
    ]
    
    def __init__(self, config: Settings):
        """Initialize the contact extractor."""
        self.config = config
        self.session = httpx.AsyncClient(timeout=30.0)
        self.visited_urls: Set[str] = set()
        
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
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text.strip())
        
        # Replace common email obfuscations
        text = re.sub(r'\s*\[at\]\s*', '@', text, flags=re.IGNORECASE)
        text = re.sub(r'\s*\(at\)\s*', '@', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+at\s+', '@', text, flags=re.IGNORECASE)
        text = re.sub(r'\s*\[dot\]\s*', '.', text, flags=re.IGNORECASE)
        text = re.sub(r'\s*\(dot\)\s*', '.', text, flags=re.IGNORECASE)
        text = re.sub(r'\s+dot\s+', '.', text, flags=re.IGNORECASE)
        
        # Remove HTML entities
        text = html.unescape(text)
        
        # Remove common tracking/analytics markers
        text = re.sub(r'\b(noreply|no-reply|no_reply|donotreply)\b', '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def extract_emails(self, text: str, source_url: str, context: DiscoveryContext) -> List[Contact]:
        """
        Extract email addresses from text.
        
        Args:
            text: Text to analyze
            source_url: URL where text was found
            context: Discovery context
            
        Returns:
            List of Contact objects for found emails
        """
        contacts = []
        normalized_text = self.normalize_text(text)
        
        for pattern in self.EMAIL_PATTERNS:
            matches = re.finditer(pattern, normalized_text, re.IGNORECASE)
            
            for match in matches:
                try:
                    # Extract email parts
                    if len(match.groups()) == 2:
                        user, domain = match.groups()
                        email = f"{user}@{domain}"
                    else:
                        email = match.group()
                    
                    # Clean up email
                    email = re.sub(r'[.,;:!?]+$', '', email)  # Remove trailing punctuation
                    email = email.strip()
                    
                    # Skip obviously invalid emails
                    if not self._is_valid_email(email):
                        continue
                    
                    # Determine confidence based on extraction method
                    confidence = self._determine_email_confidence(match, source_url)
                    
                    contact = Contact(
                        method=ContactMethod.EMAIL,
                        value=email,
                        confidence=confidence,
                        source_url=source_url,
                        discovery_path=context.discovery_path.copy(),
                        metadata={
                            "extraction_pattern": pattern,
                            "normalized": normalized_text != text
                        }
                    )
                    
                    contacts.append(contact)
                    
                except Exception as e:
                    # Continue processing other matches
                    continue
        
        return contacts
    
    def extract_phones(self, text: str, source_url: str, context: DiscoveryContext) -> List[Contact]:
        """
        Extract phone numbers from text.
        
        Args:
            text: Text to analyze
            source_url: URL where text was found
            context: Discovery context
            
        Returns:
            List of Contact objects for found phone numbers
        """
        contacts = []
        
        for pattern in self.PHONE_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            
            for match in matches:
                try:
                    phone = match.group().strip()
                    
                    # Clean up phone number
                    phone = re.sub(r'[^\d+]', '', phone)
                    
                    # Skip very short numbers
                    if len(phone) < 7:
                        continue
                    
                    confidence = self._determine_phone_confidence(match, source_url)
                    
                    contact = Contact(
                        method=ContactMethod.PHONE,
                        value=phone,
                        confidence=confidence,
                        source_url=source_url,
                        discovery_path=context.discovery_path.copy(),
                        metadata={
                            "extraction_pattern": pattern,
                            "original": match.group()
                        }
                    )
                    
                    contacts.append(contact)
                    
                except Exception as e:
                    continue
        
        return contacts
    
    def extract_mailto_links(self, soup: BeautifulSoup, source_url: str, context: DiscoveryContext) -> List[Contact]:
        """
        Extract mailto links from HTML.
        
        Args:
            soup: BeautifulSoup object of the page
            source_url: URL of the page
            context: Discovery context
            
        Returns:
            List of Contact objects for found mailto links
        """
        contacts = []
        
        # Find all mailto links
        mailto_links = soup.find_all('a', href=re.compile(r'^mailto:', re.IGNORECASE))
        
        for link in mailto_links:
            try:
                email = link.get('href', '').replace('mailto:', '', 1).strip()
                
                if not email or not self._is_valid_email(email):
                    continue
                
                # Use link text as additional context if available
                link_text = link.get_text(strip=True)
                
                confidence = ConfidenceLevel.HIGH  # Mailto links are high confidence
                
                contact = Contact(
                    method=ContactMethod.MAILTO,
                    value=email,
                    confidence=confidence,
                    source_url=source_url,
                    discovery_path=context.discovery_path.copy(),
                    metadata={
                        "link_text": link_text,
                        "link_attrs": dict(link.attrs)
                    }
                )
                
                contacts.append(contact)
                
            except Exception as e:
                continue
        
        return contacts
    
    def extract_forms(self, soup: BeautifulSoup, source_url: str, context: DiscoveryContext) -> List[ContactForm]:
        """
        Extract contact forms from HTML.
        
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
                action_url = form.get('action', '').strip()
                method = form.get('method', 'POST').upper()
                
                if not action_url:
                    # Try to find submit button or other indicators this is a contact form
                    if not self._is_contact_form(form):
                        continue
                    action_url = source_url
                else:
                    # Resolve relative URLs
                    action_url = urljoin(source_url, action_url)
                
                # Extract form fields
                fields = []
                required_fields = []
                
                inputs = form.find_all(['input', 'textarea', 'select'])
                for input_elem in inputs:
                    field_name = input_elem.get('name')
                    if field_name:
                        fields.append(field_name)
                        
                        # Check if required
                        if (input_elem.get('required') or 
                            input_elem.get('aria-required') == 'true' or
                            field_name.lower() in ['name', 'email', 'message']):
                            required_fields.append(field_name)
                
                # Check if this looks like a contact form
                if not self._is_contact_form(form) and len(required_fields) < 2:
                    continue
                
                # Extract CSRF token if present
                csrf_token = None
                csrf_input = form.find('input', {'name': re.compile(r'csrf|token', re.I)})
                if csrf_input:
                    csrf_token = csrf_input.get('value')
                
                confidence = self._determine_form_confidence(form, source_url)
                
                form_obj = ContactForm(
                    action_url=action_url,
                    method=method,
                    fields=fields,
                    required_fields=required_fields,
                    csrf_token=csrf_token,
                    source_url=source_url,
                    confidence=confidence
                )
                
                forms.append(form_obj)
                
            except Exception as e:
                continue
        
        return forms
    
    def find_contact_links(self, soup: BeautifulSoup, base_url: str, context: DiscoveryContext) -> List[str]:
        """
        Find links that might lead to contact information.
        
        Args:
            soup: BeautifulSoup object of the page
            base_url: Base URL for resolving relative links
            context: Discovery context
            
        Returns:
            List of candidate contact page URLs
        """
        candidate_urls = []
        
        # Find all links
        links = soup.find_all('a', href=True)
        
        for link in links:
            try:
                href = link.get('href', '').strip()
                link_text = link.get_text(strip=True).lower()
                
                # Skip external links or non-HTTP links
                if not href.startswith(('http://', 'https://')):
                    href = urljoin(base_url, href)
                
                if not href.startswith(('http://', 'https://')):
                    continue
                
                # Check if URL is within allowed domains
                parsed_href = urlparse(href)
                if parsed_href.netloc not in context.allowed_domains:
                    continue
                
                # Check for contact keywords in link text or href
                is_contact_link = (
                    any(keyword in link_text for keyword in self.CONTACT_KEYWORDS) or
                    any(re.search(pattern, href, re.IGNORECASE) for pattern in self.CONTACT_URL_PATTERNS)
                )
                
                if is_contact_link:
                    candidate_urls.append(href)
                
            except Exception as e:
                continue
        
        # Remove duplicates while preserving order
        seen = set()
        unique_urls = []
        for url in candidate_urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        
        return unique_urls[:10]  # Limit to top 10 candidates
    
    async def discover_contacts(self, url: str, context: Optional[DiscoveryContext] = None) -> Tuple[List[Contact], List[ContactForm]]:
        """
        Main contact discovery method.
        
        Args:
            url: URL to analyze for contact information
            context: Discovery context (optional)
            
        Returns:
            Tuple of (contacts, forms) discovered from the URL
        """
        if context is None:
            parsed_url = urlparse(url)
            context = DiscoveryContext(
                base_url=url,
                domain=parsed_url.netloc,
                allowed_domains=[parsed_url.netloc]
            )
        
        # Check if we've already visited this URL
        if url in self.visited_urls:
            return [], []
        
        self.visited_urls.add(url)
        
        try:
            # Fetch the page
            response = await self.session.get(url)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract contacts from current page
            contacts = []
            forms = []
            
            # Extract mailto links (high confidence)
            contacts.extend(self.extract_mailto_links(soup, url, context))
            
            # Extract from page text
            text_content = soup.get_text()
            contacts.extend(self.extract_emails(text_content, url, context))
            contacts.extend(self.extract_phones(text_content, url, context))
            
            # Extract forms
            forms.extend(self.extract_forms(soup, url, context))
            
            # If no contacts found and we can crawl deeper, try contact pages
            if not contacts and context.can_crawl_deeper():
                contact_links = self.find_contact_links(soup, url, context)
                
                for contact_url in contact_links[:3]:  # Limit to top 3 contact pages
                    try:
                        sub_contacts, sub_forms = await self.discover_contacts(
                            contact_url, context.next_depth()
                        )
                        contacts.extend(sub_contacts)
                        forms.extend(sub_forms)
                    except Exception as e:
                        # Continue with other contact pages if one fails
                        continue
            
            return contacts, forms
            
        except httpx.RequestError as e:
            raise ScrapingError(f"Failed to fetch {url}: {str(e)}")
        except httpx.HTTPStatusError as e:
            raise ScrapingError(f"HTTP error for {url}: {str(e)}")
        except Exception as e:
            raise ScrapingError(f"Unexpected error processing {url}: {str(e)}")
    
    def _is_valid_email(self, email: str) -> bool:
        """Basic email validation."""
        if not email or '@' not in email:
            return False
        
        # Basic format check
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False
        
        # Skip obvious invalid domains
        invalid_domains = ['example.com', 'test.com', 'localhost', 'domain.com']
        domain = email.split('@')[1].lower()
        if domain in invalid_domains:
            return False
        
        return True
    
    def _is_contact_form(self, form) -> bool:
        """Check if a form looks like a contact form."""
        form_text = form.get_text(strip=True).lower()
        
        # Keywords that suggest this is a contact form
        contact_keywords = [
            'message', 'nachricht', 'betreff', 'subject', 'kontakt',
            'ihre nachricht', 'ihre e-mail', 'ihre nachricht', 'schreiben sie uns'
        ]
        
        # Check form text for contact keywords
        if any(keyword in form_text for keyword in contact_keywords):
            return True
        
        # Check for common contact form field names
        field_names = [field.get('name', '').lower() for field in form.find_all(['input', 'textarea'])]
        contact_field_names = ['name', 'email', 'message', 'subject', 'nachricht', 'betreff']
        
        if any(field in contact_field_names for field in field_names):
            return True
        
        return False
    
    def _determine_email_confidence(self, match, source_url: str) -> ConfidenceLevel:
        """Determine confidence level for email extraction."""
        # Mailto links are high confidence
        if hasattr(match, 'group') and 'mailto' in source_url.lower():
            return ConfidenceLevel.HIGH
        
        # Email in specific contact contexts
        if any(keyword in source_url.lower() for keyword in ['contact', 'kontakt', 'impressum']):
            return ConfidenceLevel.HIGH
        
        # Standard text extraction
        return ConfidenceLevel.MEDIUM
    
    def _determine_phone_confidence(self, match, source_url: str) -> ConfidenceLevel:
        """Determine confidence level for phone extraction."""
        # Phone numbers in contact contexts
        if any(keyword in source_url.lower() for keyword in ['contact', 'kontakt', 'impressum']):
            return ConfidenceLevel.HIGH
        
        # German phone format (with +49)
        if '+49' in match.group():
            return ConfidenceLevel.HIGH
        
        return ConfidenceLevel.MEDIUM
    
    def _determine_form_confidence(self, form, source_url: str) -> ConfidenceLevel:
        """Determine confidence level for form extraction."""
        # Forms on contact pages
        if any(keyword in source_url.lower() for keyword in ['contact', 'kontakt']):
            return ConfidenceLevel.HIGH
        
        # Check for contact-related form fields
        form_text = form.get_text(strip=True).lower()
        if any(keyword in form_text for keyword in ['message', 'nachricht', 'kontakt']):
            return ConfidenceLevel.HIGH
        
        return ConfidenceLevel.MEDIUM
    
    def deduplicate_contacts(self, contacts: List[Contact]) -> List[Contact]:
        """
        Remove duplicate contacts based on method and value.
        
        Args:
            contacts: List of contacts to deduplicate
            
        Returns:
            Deduplicated list of contacts
        """
        seen = set()
        unique_contacts = []
        
        for contact in contacts:
            key = (contact.method, contact.value.lower())
            if key not in seen:
                seen.add(key)
                unique_contacts.append(contact)
        
        return unique_contacts