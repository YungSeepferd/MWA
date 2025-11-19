"""
JavaScript rendering for dynamic websites.

This module provides functionality to render JavaScript-heavy websites
using Playwright to extract contact information from dynamic content.
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Union, Tuple
from urllib.parse import urlparse

from playwright.async_api import async_playwright, Browser, BrowserContext, Page

from ..contacts.extractor import ContactExtractor
from ..contacts.models import Contact, ContactMethod, ConfidenceLevel

logger = logging.getLogger(__name__)

@dataclass
class ExtractedContact:
    """Contact extraction result wrapper."""
    source: str
    contact: Contact
    context: Dict
    raw_data: Dict
    confidence: ConfidenceLevel

logger = logging.getLogger(__name__)

class JSRenderer:
    """
    Renders JavaScript-heavy websites using Playwright to extract contact information.
    
    Supports dynamic content loading, SPA frameworks (React, Vue, Angular),
    and automated form discovery.
    """
    
    def __init__(
        self,
        timeout_seconds: int = 30,
        wait_for_load: bool = True,
        block_resources: Optional[List[str]] = None,
        user_agent: Optional[str] = None,
        viewport: Optional[Dict] = None,
        headless: bool = True,
        confidence_threshold: float = 0.7
    ):
        """
        Initialize JavaScript renderer.
        
        Args:
            timeout_seconds: Maximum time to wait for page load
            wait_for_load: Whether to wait for page load event
            block_resources: List of resource types to block (e.g., ['image', 'stylesheet'])
            user_agent: Custom user agent string
            viewport: Viewport configuration (width, height)
            headless: Whether to run browser in headless mode
            confidence_threshold: Minimum confidence score for extracted contacts
        """
        self.timeout_seconds = timeout_seconds
        self.wait_for_load = wait_for_load
        self.block_resources = block_resources or ['image', 'stylesheet', 'font', 'media']
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        self.viewport = viewport or {"width": 1920, "height": 1080}
        self.headless = headless
        self.confidence_threshold = confidence_threshold
        
        # Browser instance (initialized on first use)
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._init_browser()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def _init_browser(self):
        """Initialize browser instance."""
        if self.browser:
            return
        
        try:
            playwright = await async_playwright().start()
            self.browser = await playwright.chromium.launch(
                headless=self.headless,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]
            )
            
            # Create context with custom settings
            self.context = await self.browser.new_context(
                user_agent=self.user_agent,
                viewport=self.viewport,
                java_script_enabled=True,
                ignore_https_errors=True
            )
            
            # Block unnecessary resources
            if self.block_resources:
                await self.context.route("**/*", self._block_resources)
            
            logger.info("Browser initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {e}")
            raise
    
    async def _block_resources(self, route):
        """Block unnecessary resources to improve performance."""
        resource_type = route.request.resource_type
        
        if resource_type in self.block_resources:
            await route.abort()
        else:
            await route.continue_()
    
    async def close(self):
        """Close browser instance."""
        if self.context:
            await self.context.close()
            self.context = None
        
        if self.browser:
            await self.browser.close()
            self.browser = None
        
        logger.info("Browser closed")
    
    def can_process(self, source: Union[str, Path]) -> bool:
        """
        Check if the source can be processed by this renderer.
        
        Args:
            source: Website URL
            
        Returns:
            True if the source is a URL that can be processed
        """
        if isinstance(source, str):
            return source.startswith(('http://', 'https://'))
        return False
    
    async def extract_contacts(
        self,
        source: Union[str, Path],
        context: Optional[Dict] = None
    ) -> List[Contact]:
        """
        Extract contacts from a JavaScript-heavy website.
        
        Args:
            source: Website URL
            context: Additional context for extraction
            
        Returns:
            List of extracted contacts with confidence scores
        """
        if not self.can_process(source):
            logger.warning(f"Cannot process source: {source}")
            return []
        
        try:
            # Initialize browser if not already done
            if not self.browser:
                await self._init_browser()
            
            # Create new page
            page = await self.context.new_page()
            
            # Navigate to URL
            logger.info(f"Navigating to {source}")
            await page.goto(
                source,
                wait_until='networkidle' if self.wait_for_load else 'domcontentloaded',
                timeout=self.timeout_seconds * 1000
            )
            
            # Wait for dynamic content to load
            if self.wait_for_load:
                await page.wait_for_timeout(2000)  # Additional wait for dynamic content
            
            # Extract page content
            content = await page.content()
            
            # Extract text from page
            text = await page.evaluate('() => document.body.innerText')
            
            # Extract contacts from text
            contacts = self._extract_contacts_from_text(text, source, context)
            
            # Extract forms from page
            forms = await self._extract_forms_from_page(page, source, context)
            contacts.extend(forms)
            
            # Extract contact information from structured data
            structured_contacts = await self._extract_structured_data(page, source, context)
            contacts.extend(structured_contacts)
            
            # Score contacts based on extraction quality
            scored_contacts = self._score_contacts(contacts, page, text)
            
            # Filter by confidence threshold - convert confidence enum to numeric value
            def confidence_to_numeric(confidence: ConfidenceLevel) -> float:
                if confidence == ConfidenceLevel.HIGH:
                    return 1.0
                elif confidence == ConfidenceLevel.MEDIUM:
                    return 0.7
                else:
                    return 0.4
            
            filtered_contacts = [
                contact for contact in scored_contacts
                if confidence_to_numeric(contact.confidence) >= self.confidence_threshold
            ]
            
            # Convert ExtractedContact wrappers to Contact objects
            final_contacts = [extracted.contact for extracted in filtered_contacts]
            
            logger.info(f"Extracted {len(final_contacts)} contacts from {source}")
            
            # Close page
            await page.close()
            
            return final_contacts
            
        except Exception as e:
            logger.error(f"JavaScript rendering failed for {source}: {e}")
            return []
    
    def _extract_contacts_from_text(
        self,
        text: str,
        source: Union[str, Path],
        context: Optional[Dict]
    ) -> List[ExtractedContact]:
        """Extract contacts from rendered page text."""
        contacts = []
        
        # Extract emails
        emails = self._extract_emails(text)
        for email, confidence in emails:
            contact = Contact(
                method=ContactMethod.EMAIL,
                value=email,
                confidence=confidence,
                source_url=str(source)
            )
            extracted = ExtractedContact(
                source=str(source),
                contact=contact,
                context=context or {},
                raw_data={"text_snippet": self._get_text_snippet(text, email)},
                confidence=confidence
            )
            contacts.append(extracted)
        
        # Extract phone numbers
        phones = self._extract_phones(text)
        for phone, confidence in phones:
            contact = Contact(
                method=ContactMethod.PHONE,
                value=phone,
                confidence=confidence,
                source_url=str(source)
            )
            extracted = ExtractedContact(
                source=str(source),
                contact=contact,
                context=context or {},
                raw_data={"text_snippet": self._get_text_snippet(text, phone)},
                confidence=confidence
            )
            contacts.append(extracted)
        
        # Extract forms
        forms = self._extract_forms(text)
        for form_url, confidence in forms:
            contact = Contact(
                method=ContactMethod.FORM,
                value=form_url,
                confidence=confidence,
                source_url=str(source)
            )
            extracted = ExtractedContact(
                source=str(source),
                contact=contact,
                context=context or {},
                raw_data={"text_snippet": self._get_text_snippet(text, form_url)},
                confidence=confidence
            )
            contacts.append(extracted)
        
        return contacts
    
    async def _extract_forms_from_page(
        self,
        page: Page,
        source: Union[str, Path],
        context: Optional[Dict]
    ) -> List[ExtractedContact]:
        """Extract contact forms from page."""
        forms = []
        
        try:
            # Find all forms on the page
            form_elements = await page.query_selector_all('form')
            
            for i, form_element in enumerate(form_elements):
                # Check if form is a contact form
                form_html = await form_element.evaluate('(form) => form.outerHTML')
                
                if self._is_contact_form(form_html):
                    # Get form action URL
                    action_url = await form_element.get_attribute('action')
                    
                    # If no action, use current page URL
                    if not action_url:
                        action_url = str(source)
                    
                    # Validate URL
                    if self._validate_url(action_url):
                        # Check for contact-related fields
                        has_contact_fields = await self._has_contact_fields(form_element)
                        
                        if has_contact_fields:
                            confidence = ConfidenceLevel.HIGH
                        else:
                            confidence = ConfidenceLevel.MEDIUM
                        
                        contact = Contact(
                            method=ContactMethod.FORM,
                            value=action_url,
                            confidence=confidence,
                            source_url=str(source)
                        )
                        extracted = ExtractedContact(
                            source=str(source),
                            contact=contact,
                            context={**context, "form_index": i} if context else {"form_index": i},
                            raw_data={"form_html": form_html},
                            confidence=confidence
                        )
                        forms.append(extracted)
            
            # Also look for contact links
            contact_links = await page.query_selector_all('a[href*="contact"], a[href*="kontakt"], a[href*="anfrage"]')
            
            for link in contact_links:
                href = await link.get_attribute('href')
                
                if href and self._validate_url(href):
                    # Resolve relative URLs
                    if not href.startswith(('http://', 'https://')):
                        href = f"{source.rstrip('/')}/{href.lstrip('/')}"
                    
                    contact = Contact(
                        method=ContactMethod.FORM,
                        value=href,
                        confidence=ConfidenceLevel.HIGH,
                        source_url=str(source)
                    )
                    extracted = ExtractedContact(
                        source=str(source),
                        contact=contact,
                        context=context or {},
                        raw_data={"link_text": await link.inner_text()},
                        confidence=ConfidenceLevel.HIGH
                    )
                    forms.append(extracted)
        
        except Exception as e:
            logger.warning(f"Form extraction failed: {e}")
        
        return forms
    
    def _is_contact_form(self, form_html: str) -> bool:
        """Check if form is likely a contact form."""
        form_html_lower = form_html.lower()
        
        # Check for contact-related keywords
        contact_keywords = [
            'contact', 'kontakt', 'anfrage', 'nachricht', 'message',
            'name', 'email', 'telefon', 'phone', 'betreff', 'subject'
        ]
        
        return any(keyword in form_html_lower for keyword in contact_keywords)
    
    async def _has_contact_fields(self, form_element) -> bool:
        """Check if form has contact-related fields."""
        try:
            # Look for common contact form fields
            name_fields = await form_element.query_selector_all('input[name*="name"], input[name*="Name"]')
            email_fields = await form_element.query_selector_all('input[type="email"], input[name*="email"], input[name*="Email"]')
            phone_fields = await form_element.query_selector_all('input[name*="phone"], input[name*="Phone"], input[name*="telefon"], input[name*="Telefon"]')
            message_fields = await form_element.query_selector_all('textarea[name*="message"], textarea[name*="Message"], textarea[name*="nachricht"], textarea[name*="Nachricht"]')
            
            # Form is likely a contact form if it has name + (email or phone) + message
            has_name = len(name_fields) > 0
            has_contact = len(email_fields) > 0 or len(phone_fields) > 0
            has_message = len(message_fields) > 0
            
            return has_name and has_contact and has_message
        
        except Exception:
            return False
    
    async def _extract_structured_data(
        self,
        page: Page,
        source: Union[str, Path],
        context: Optional[Dict]
    ) -> List[ExtractedContact]:
        """Extract contact information from structured data (JSON-LD, microdata)."""
        contacts = []
        
        try:
            # Extract JSON-LD data
            json_ld_scripts = await page.query_selector_all('script[type="application/ld+json"]')
            
            for script in json_ld_scripts:
                json_content = await script.inner_text()
                
                if json_content:
                    import json
                    try:
                        data = json.loads(json_content)
                        
                        # Extract contact information from structured data
                        structured_contacts = self._extract_from_json_ld(data, source, context)
                        contacts.extend(structured_contacts)
                    
                    except json.JSONDecodeError:
                        logger.debug("Invalid JSON-LD data")
        
        except Exception as e:
            logger.warning(f"Structured data extraction failed: {e}")
        
        return contacts
    
    def _extract_from_json_ld(
        self,
        data: Union[Dict, List],
        source: Union[str, Path],
        context: Optional[Dict]
    ) -> List[ExtractedContact]:
        """Extract contacts from JSON-LD structured data."""
        contacts = []
        
        if isinstance(data, list):
            for item in data:
                contacts.extend(self._extract_from_json_ld(item, source, context))
        elif isinstance(data, dict):
            # Check for contact information in various schema types
            schema_type = data.get('@type', '').lower()
            
            if 'contact' in schema_type or 'organization' in schema_type or 'person' in schema_type:
                # Extract email
                email = data.get('email')
                if email and self._validate_email(email):
                    contact = Contact(
                        method=ContactMethod.EMAIL,
                        value=email,
                        confidence=ConfidenceLevel.HIGH,
                        source_url=str(source)
                    )
                    extracted = ExtractedContact(
                        source=str(source),
                        contact=contact,
                        context={**context, "schema_type": schema_type} if context else {"schema_type": schema_type},
                        raw_data={"json_ld": data},
                        confidence=ConfidenceLevel.HIGH
                    )
                    contacts.append(extracted)
                
                # Extract telephone
                telephone = data.get('telephone')
                if telephone and self._validate_phone(telephone):
                    contact = Contact(
                        method=ContactMethod.PHONE,
                        value=telephone,
                        confidence=ConfidenceLevel.HIGH,
                        source_url=str(source)
                    )
                    extracted = ExtractedContact(
                        source=str(source),
                        contact=contact,
                        context={**context, "schema_type": schema_type} if context else {"schema_type": schema_type},
                        raw_data={"json_ld": data},
                        confidence=ConfidenceLevel.HIGH
                    )
                    contacts.append(extracted)
                
                # Extract contact point
                contact_point = data.get('contactPoint')
                if contact_point:
                    if isinstance(contact_point, list):
                        for cp in contact_point:
                            contacts.extend(self._extract_from_json_ld(cp, source, context))
                    elif isinstance(contact_point, dict):
                        contacts.extend(self._extract_from_json_ld(contact_point, source, context))
            
            # Recursively check other fields
            for key, value in data.items():
                if isinstance(value, (dict, list)):
                    contacts.extend(self._extract_from_json_ld(value, source, context))
        
        return contacts
    
    def _extract_emails(self, text: str) -> List[Tuple[str, ConfidenceLevel]]:
        """Extract email addresses from text."""
        emails = []
        
        # Pattern for email addresses
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        
        # Also handle obfuscated emails
        obfuscated_patterns = [
            (r'\b[A-Za-z0-9._%+-]+\s*\[\s*at\s*\]\s*[A-Za-z0-9.-]+\s*\[\s*dot\s*\]\s*[A-Z|a-z]{2,}\b', self._deobfuscate_email),
            (r'\b[A-Za-z0-9._%+-]+\s*\(\s*at\s*\)\s*[A-Za-z0-9.-]+\s*\(\s*dot\s*\)\s*[A-Z|a-z]{2,}\b', self._deobfuscate_email),
        ]
        
        # Extract normal emails
        for match in re.finditer(email_pattern, text):
            email = match.group()
            if self._validate_email(email):
                emails.append((email, ConfidenceLevel.HIGH))
        
        # Extract obfuscated emails
        for pattern, deobfuscator in obfuscated_patterns:
            for match in re.finditer(pattern, text):
                obfuscated = match.group()
                email = deobfuscator(obfuscated)
                if self._validate_email(email):
                    emails.append((email, ConfidenceLevel.MEDIUM))
        
        return emails
    
    def _extract_phones(self, text: str) -> List[Tuple[str, ConfidenceLevel]]:
        """Extract phone numbers from text."""
        phones = []
        
        # Patterns for German and international phone numbers
        patterns = [
            # German format
            r'\b(?:\+49|0049|0)\s*[1-9]\d{1,4}\s*\d{1,14}(?:\s*\d{1,14})?\b',
            # International format
            r'\b(?:\+|00)\d{1,4}\s*\d{1,14}(?:\s*\d{1,14})?\b',
            # Local format (Munich)
            r'\b089\s*\d{1,14}(?:\s*\d{1,14})?\b',
        ]
        
        for pattern in patterns:
            for match in re.finditer(pattern, text):
                phone = match.group()
                if self._validate_phone(phone):
                    # Score based on format completeness
                    if phone.startswith('+') or phone.startswith('00'):
                        confidence = ConfidenceLevel.HIGH
                    elif '089' in phone:  # Munich area code
                        confidence = ConfidenceLevel.HIGH
                    else:
                        confidence = ConfidenceLevel.MEDIUM
                    
                    phones.append((phone, confidence))
        
        return phones
    
    def _extract_forms(self, text: str) -> List[Tuple[str, ConfidenceLevel]]:
        """Extract form URLs from text."""
        forms = []
        
        # Look for form-related keywords and URLs
        form_keywords = ['formular', 'anfrage', 'kontakt', 'bewerbung', 'anmeldung']
        url_pattern = r'https?://[^\s<>"]+|www\.[^\s<>"]+'
        
        # Find URLs near form keywords
        lines = text.split('\n')
        for i, line in enumerate(lines):
            line_lower = line.lower()
            
            # Check if line contains form keywords
            if any(keyword in line_lower for keyword in form_keywords):
                # Look for URLs in this line or nearby lines
                search_window = lines[max(0, i-1):min(len(lines), i+2)]
                search_text = ' '.join(search_window)
                
                for match in re.finditer(url_pattern, search_text):
                    url = match.group()
                    # Validate URL
                    if self._validate_url(url):
                        # Score based on proximity to form keywords
                        if any(keyword in line_lower for keyword in form_keywords):
                            confidence = ConfidenceLevel.HIGH
                        else:
                            confidence = ConfidenceLevel.MEDIUM
                        
                        forms.append((url, confidence))
        
        return forms
    
    def _deobfuscate_email(self, obfuscated: str) -> str:
        """Convert obfuscated email to normal format."""
        # Replace [at] or (at) with @
        email = re.sub(r'\s*\[\s*at\s*\]\s*|\s*\(\s*at\s*\)\s*', '@', obfuscated, flags=re.IGNORECASE)
        # Replace [dot] or (dot) with .
        email = re.sub(r'\s*\[\s*dot\s*\]\s*|\s*\(\s*dot\s*\)\s*', '.', email, flags=re.IGNORECASE)
        # Remove any remaining spaces
        email = email.replace(' ', '')
        return email
    
    def _get_text_snippet(self, text: str, keyword: str, window: int = 50) -> str:
        """Get text snippet around a keyword."""
        try:
            index = text.index(keyword)
            start = max(0, index - window)
            end = min(len(text), index + len(keyword) + window)
            return text[start:end]
        except ValueError:
            return ""
    
    def _score_contacts(
        self,
        contacts: List[ExtractedContact],
        page: Page,
        text: str
    ) -> List[ExtractedContact]:
        """Score contacts based on extraction quality."""
        # Calculate text quality
        text_quality = self._calculate_text_quality(text)
        
        # Adjust contact scores based on quality metrics
        scored_contacts = []
        for contact in contacts:
            # Convert confidence enum to numeric value for calculation
            if contact.confidence == ConfidenceLevel.HIGH:
                base_confidence = 1.0
            elif contact.confidence == ConfidenceLevel.MEDIUM:
                base_confidence = 0.7
            else:
                base_confidence = 0.4
            
            # Adjust based on text quality
            final_confidence = min(1.0, base_confidence * text_quality)
            
            # Update contact confidence and wrapper confidence
            if final_confidence >= 0.8:
                contact.confidence = ConfidenceLevel.HIGH
                contact.contact.confidence = ConfidenceLevel.HIGH
            elif final_confidence >= 0.5:
                contact.confidence = ConfidenceLevel.MEDIUM
                contact.contact.confidence = ConfidenceLevel.MEDIUM
            else:
                contact.confidence = ConfidenceLevel.LOW
                contact.contact.confidence = ConfidenceLevel.LOW
            
            scored_contacts.append(contact)
        
        return scored_contacts
    
    def _calculate_text_quality(self, text: str) -> float:
        """Calculate text quality score (0-1)."""
        if not text:
            return 0.0
        
        # Calculate character diversity (avoid repetitive garbage)
        unique_chars = len(set(text))
        total_chars = len(text)
        
        if total_chars == 0:
            return 0.0
        
        char_diversity = unique_chars / total_chars
        
        # Check for common OCR errors
        ocr_errors = len(re.findall(r'[^\w\s@+.\-(),:/]', text)) / total_chars
        
        # Calculate word coherence (ratio of words to total tokens)
        words = len(re.findall(r'\b\w+\b', text))
        quality_score = (char_diversity + (1 - ocr_errors) + min(1.0, words / 10)) / 3
        
        return max(0.1, min(1.0, quality_score))
    
    def _validate_email(self, email: str) -> bool:
        """Validate email format."""
        pattern = r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _validate_phone(self, phone: str) -> bool:
        """Validate phone number format."""
        # Remove common separators
        clean_phone = re.sub(r'[\s\-\(\)]', '', phone)
        # Check if it has enough digits
        digits = len(re.findall(r'\d', clean_phone))
        return digits >= 6  # Minimum 6 digits for a valid phone number
    
    def _validate_url(self, url: str) -> bool:
        """Validate URL format."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False


# Example usage
if __name__ == "__main__":
    import asyncio
    
    async def main():
        # Initialize JavaScript renderer
        renderer = JSRenderer(
            timeout_seconds=30,
            wait_for_load=True,
            headless=True,
            confidence_threshold=0.6
        )
        
        # Test with a sample URL
        test_url = "https://example.com/contact"
        
        if renderer.can_process(test_url):
            contacts = await renderer.extract_contacts(test_url)
            
            for contact in contacts:
                print(f"Found {contact.contact.method}: {contact.contact.value} "
                      f"(confidence: {contact.contact.confidence.name})")
        else:
            print("Cannot process the provided URL")
        
        await renderer.close()
    
    # Run async main
    asyncio.run(main())