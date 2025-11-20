"""
Comprehensive tests for MWA Core contact discovery system.

Tests all components of the enhanced contact discovery pipeline:
- Contact extraction and validation
- Web crawling and link following
- Confidence scoring and deduplication
- Storage integration
- Performance and reliability
"""

import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
from urllib.parse import urlparse

from mwa_core.contact.models import (
    Contact, ContactForm, SocialMediaProfile, DiscoveryContext,
    ConfidenceLevel, ContactStatus, ContactMethod, SocialMediaPlatform
)
from mwa_core.contact.discovery import ContactDiscoveryEngine, DiscoveryStats
from mwa_core.contact.extractors import (
    EmailExtractor, PhoneExtractor, FormExtractor, SocialMediaExtractor
)
from mwa_core.contact.scoring import ContactScoringEngine
from mwa_core.contact.validators import ContactValidator, ValidationResult
from mwa_core.contact.integration import ContactDiscoveryIntegration
from mwa_core.config.settings import Settings


def _is_domain_in_allowed_domains(domain: str, allowed_domains: list) -> bool:
    """Check if domain is in allowed domains list."""
    return any(d == domain for d in allowed_domains)


def _is_xing_url(url: str) -> bool:
    """Check if URL is a valid XING URL."""
    try:
        parsed = urlparse(url)
        return parsed.hostname in ['xing.com', 'www.xing.com']
    except Exception:
        return False


class TestContactModels:
    """Test contact data models."""
    
    def test_contact_creation(self):
        """Test basic contact creation."""
        contact = Contact(
            method=ContactMethod.EMAIL,
            value="test@example.com",
            confidence=ConfidenceLevel.HIGH,
            source_url="https://example.com"
        )
        
        assert contact.method == ContactMethod.EMAIL
        assert contact.value == "test@example.com"
        assert contact.confidence == ConfidenceLevel.HIGH
        assert contact.is_high_confidence
        assert not contact.is_verified
        assert contact.domain == "example.com"
    
    def test_contact_normalization(self):
        """Test contact value normalization."""
        # Email normalization
        email_contact = Contact(
            method=ContactMethod.EMAIL,
            value="  TEST@EXAMPLE.COM  ",
            confidence=ConfidenceLevel.HIGH,
            source_url="https://example.com"
        )
        assert email_contact.value == "test@example.com"
        
        # Phone normalization
        phone_contact = Contact(
            method=ContactMethod.PHONE,
            value="+49 (0) 89 123 456 789",
            confidence=ConfidenceLevel.HIGH,
            source_url="https://example.com"
        )
        assert phone_contact.value == "+49089123456789"
    
    def test_contact_serialization(self):
        """Test contact serialization and deserialization."""
        contact = Contact(
            method=ContactMethod.EMAIL,
            value="test@example.com",
            confidence=ConfidenceLevel.HIGH,
            source_url="https://example.com",
            metadata={"test": "data"}
        )
        
        # Test to_dict
        contact_dict = contact.to_dict()
        assert contact_dict['method'] == 'email'
        assert contact_dict['value'] == 'test@example.com'
        assert contact_dict['confidence'] == 'high'
        assert contact_dict['metadata']['test'] == 'data'
        
        # Test from_dict
        restored_contact = Contact.from_dict(contact_dict)
        assert restored_contact.method == ContactMethod.EMAIL
        assert restored_contact.value == "test@example.com"
        assert restored_contact.confidence == ConfidenceLevel.HIGH
    
    def test_contact_form_creation(self):
        """Test contact form creation."""
        form = ContactForm(
            action_url="https://example.com/contact",
            method="POST",
            fields=["name", "email", "message"],
            required_fields=["name", "email"],
            source_url="https://example.com"
        )
        
        assert form.action_url == "https://example.com/contact"
        assert form.method == "POST"
        assert len(form.fields) == 3
        assert form.has_email_field
        assert form.has_message_field
        assert form.is_simple_form
    
    def test_social_media_profile_creation(self):
        """Test social media profile creation."""
        profile = SocialMediaProfile(
            platform=SocialMediaPlatform.LINKEDIN,
            username="testuser",
            profile_url="https://linkedin.com/in/testuser",
            display_name="Test User",
            source_url="https://example.com"
        )
        
        assert profile.platform == SocialMediaPlatform.LINKEDIN
        assert profile.username == "testuser"
        assert profile.is_business_profile is False
    
    def test_discovery_context_creation(self):
        """Test discovery context creation."""
        context = DiscoveryContext(
            base_url="https://example.com",
            domain="example.com",
            max_depth=3,
            current_depth=1
        )
        
        assert context.base_url == "https://example.com"
        assert context.domain == "example.com"
        assert context.max_depth == 3
        assert context.current_depth == 1
        assert context.can_crawl_deeper
        assert self._is_domain_in_allowed_domains("example.com", context.allowed_domains)


class TestEmailExtractor:
    """Test email extraction functionality."""
    
    @pytest.fixture
    def settings(self):
        """Create test settings."""
        return Settings()
    
    @pytest.fixture
    async def extractor(self, settings):
        """Create email extractor."""
        extractor = EmailExtractor(settings)
        async with extractor:
            yield extractor
    
    def test_email_pattern_matching(self, extractor):
        """Test email pattern matching."""
        test_text = """
        Contact us at info@example.com or support@test.org
        You can also reach john.doe@company.co.uk
        """
        
        contacts = extractor.extract_emails(test_text, "https://test.com", Mock())
        
        assert len(contacts) == 3
        assert any(c.value == "info@example.com" for c in contacts)
        assert any(c.value == "support@test.org" for c in contacts)
        assert any(c.value == "john.doe@company.co.uk" for c in contacts)
    
    def test_obfuscated_email_extraction(self, extractor):
        """Test extraction of obfuscated emails."""
        test_text = """
        Contact: info [at] example [dot] com
        Email: support(at)test(dot)org
        Reach us: john dot doe at company dot com
        """
        
        contacts = extractor.extract_emails(test_text, "https://test.com", Mock())
        
        assert len(contacts) >= 2  # Should find at least 2 obfuscated emails
        # Check that obfuscated emails are found with medium confidence
        obfuscated_contacts = [c for c in contacts if c.metadata.get('extraction_pattern') == 'obfuscated_text']
        assert len(obfuscated_contacts) > 0
    
    def test_mailto_link_extraction(self, extractor):
        """Test mailto link extraction."""
        test_text = """
        <a href="mailto:info@example.com">Contact Us</a>
        <a href="mailto:support@test.org?subject=Help">Support</a>
        """
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(test_text, 'html.parser')
        context = Mock()
        context.discovery_path = []
        
        contacts = extractor.extract_mailto_links(soup, "https://test.com", context)
        
        assert len(contacts) == 2
        assert any(c.value == "info@example.com" for c in contacts)
        assert any(c.value == "support@test.org" for c in contacts)
        # Mailto links should have high confidence
        assert all(c.confidence == ConfidenceLevel.HIGH for c in contacts)
    
    def test_email_validation(self, extractor):
        """Test email validation."""
        # Valid emails
        valid_emails = [
            "test@example.com",
            "john.doe@company.co.uk",
            "info+tag@example.org"
        ]
        
        for email in valid_emails:
            assert extractor._is_valid_email(email)
        
        # Invalid emails
        invalid_emails = [
            "invalid-email",
            "test@",
            "@example.com",
            "test@example",
            "test..double@example.com"
        ]
        
        for email in invalid_emails:
            assert not extractor._is_valid_email(email)
    
    def test_german_domain_scoring(self, extractor):
        """Test German domain scoring."""
        test_emails = [
            "test@gmx.de",
            "info@web.de",
            "support@t-online.de"
        ]
        
        for email in test_emails:
            confidence = extractor._determine_email_confidence(email, "https://test.com", Mock(cultural_context="german"))
            assert confidence == ConfidenceLevel.HIGH


class TestPhoneExtractor:
    """Test phone number extraction functionality."""
    
    @pytest.fixture
    def settings(self):
        """Create test settings."""
        return Settings()
    
    @pytest.fixture
    async def extractor(self, settings):
        """Create phone extractor."""
        extractor = PhoneExtractor(settings)
        async with extractor:
            yield extractor
    
    def test_german_phone_extraction(self, extractor):
        """Test German phone number extraction."""
        test_text = """
        Call us at +49 89 12345678
        Local: 089 123 456 789
        National: 030 12345678
        International: 0049 89 12345678
        """
        
        contacts = extractor.extract_phones(test_text, "https://test.com", Mock())
        
        assert len(contacts) >= 3
        # Check Munich numbers have high confidence
        munich_contacts = [c for c in contacts if '089' in c.value]
        assert len(munich_contacts) > 0
        assert all(c.confidence == ConfidenceLevel.HIGH for c in munich_contacts)
    
    def test_mobile_phone_extraction(self, extractor):
        """Test mobile phone extraction."""
        test_text = """
        Mobile: +49 151 12345678
        Cell: 0176 123 456 789
        Phone: +49 160 98765432
        """
        
        contacts = extractor.extract_phones(test_text, "https://test.com", Mock())
        
        mobile_contacts = [c for c in contacts if c.metadata.get('is_mobile')]
        assert len(mobile_contacts) > 0
        assert all(c.confidence == ConfidenceLevel.HIGH for c in mobile_contacts)
    
    def test_international_phone_extraction(self, extractor):
        """Test international phone extraction."""
        test_text = """
        International: +1 555 123 4567
        Europe: +44 20 1234 5678
        Asia: +81 3 1234 5678
        """
        
        contacts = extractor.extract_phones(test_text, "https://test.com", Mock())
        
        international_contacts = [c for c in contacts if c.value.startswith('+')]
        assert len(international_contacts) >= 2
    
    def test_phone_validation(self, extractor):
        """Test phone number validation."""
        # Valid German phones
        valid_phones = [
            "+49 89 12345678",
            "089 123 456 789",
            "030 12345678",
            "+49 151 12345678"
        ]
        
        for phone in valid_phones:
            assert extractor._is_valid_german_phone(extractor.normalize_text(phone))
        
        # Invalid phones
        invalid_phones = [
            "123",  # Too short
            "+49 1234567890123456",  # Too long
            "999 12345678"  # Invalid area code
        ]
        
        for phone in invalid_phones:
            assert not extractor._is_valid_german_phone(extractor.normalize_text(phone))


class TestFormExtractor:
    """Test contact form extraction functionality."""
    
    @pytest.fixture
    def settings(self):
        """Create test settings."""
        return Settings()
    
    @pytest.fixture
    async def extractor(self, settings):
        """Create form extractor."""
        extractor = FormExtractor(settings)
        async with extractor:
            yield extractor
    
    def test_contact_form_detection(self, extractor):
        """Test contact form detection."""
        from bs4 import BeautifulSoup
        
        html = """
        <form action="/contact" method="post">
            <input type="text" name="name" required>
            <input type="email" name="email" required>
            <textarea name="message" required></textarea>
            <button type="submit">Send Message</button>
        </form>
        """
        
        soup = BeautifulSoup(html, 'html.parser')
        context = Mock()
        context.discovery_path = []
        
        forms = extractor.extract_forms(soup, "https://test.com/contact", context)
        
        assert len(forms) == 1
        form = forms[0]
        assert form.action_url == "https://test.com/contact"
        assert form.method == "POST"
        assert "name" in form.fields
        assert "email" in form.fields
        assert "message" in form.fields
        assert form.has_email_field
        assert form.has_message_field
        assert form.is_simple_form
    
    def test_form_complexity_scoring(self, extractor):
        """Test form complexity scoring."""
        from bs4 import BeautifulSoup
        
        # Simple form
        simple_html = """
        <form>
            <input name="name">
            <input name="email">
            <textarea name="message"></textarea>
        </form>
        """
        
        simple_soup = BeautifulSoup(simple_html, 'html.parser')
        simple_form = simple_soup.find('form')
        
        complexity = extractor._calculate_complexity_score(["name", "email", "message"], ["name", "email"])
        assert complexity < 0.5  # Should be low complexity
        
        # Complex form
        complex_html = """
        <form>
            <input name="name" type="text">
            <input name="email" type="email">
            <input name="phone" type="tel">
            <select name="subject">
                <option>General</option>
                <option>Support</option>
            </select>
            <input name="file" type="file">
            <input name="date" type="date">
            <textarea name="message"></textarea>
            <input name="newsletter" type="checkbox">
        </form>
        """
        
        complex_soup = BeautifulSoup(complex_html, 'html.parser')
        complex_form = complex_soup.find('form')
        
        fields = ["name", "email", "phone", "subject", "file", "date", "message", "newsletter"]
        required = ["name", "email", "phone", "subject", "message"]
        
        complexity = extractor._calculate_complexity_score(fields, required)
        assert complexity > 0.5  # Should be high complexity


class TestSocialMediaExtractor:
    """Test social media profile extraction functionality."""
    
    @pytest.fixture
    def settings(self):
        """Create test settings."""
        return Settings()
    
    @pytest.fixture
    async def extractor(self, settings):
        """Create social media extractor."""
        extractor = SocialMediaExtractor(settings)
        async with extractor:
            yield extractor
    
    def test_social_media_extraction(self, extractor):
        """Test social media profile extraction."""
        test_text = """
        Follow us on Facebook: https://facebook.com/companypage
        Connect on LinkedIn: https://linkedin.com/in/johndoe
        Instagram: https://instagram.com/company
        Twitter: https://twitter.com/companyhandle
        WhatsApp: https://wa.me/4915112345678
        """
        
        profiles = extractor.extract_social_media(test_text, "https://test.com", Mock())
        
        assert len(profiles) >= 4
        platforms = [p.platform for p in profiles]
        assert SocialMediaPlatform.FACEBOOK in platforms
        assert SocialMediaPlatform.LINKEDIN in platforms
        assert SocialMediaPlatform.INSTAGRAM in platforms
        assert SocialMediaPlatform.TWITTER in platforms
    
    def test_business_profile_detection(self, extractor):
        """Test business profile detection."""
        test_text = """
        Real estate company: https://linkedin.com/company/immobilien-gmbh
        Property management: https://xing.com/profile/makler-verwaltung
        Personal profile: https://facebook.com/john.doe
        """
        
        profiles = extractor.extract_social_media(test_text, "https://test.com", Mock())
        
        business_profiles = [p for p in profiles if p.is_business_profile]
        assert len(business_profiles) > 0
        
        # Check that business-related profiles are detected
        for profile in business_profiles:
            assert any(keyword in (profile.display_name or '').lower() or profile.username.lower() 
                      for keyword in ['immobilien', 'verwaltung', 'makler'])


class TestContactScoringEngine:
    """Test contact scoring functionality."""
    
    @pytest.fixture
    def scoring_engine(self):
        """Create scoring engine."""
        return ContactScoringEngine()
    
    def test_basic_contact_scoring(self, scoring_engine):
        """Test basic contact scoring."""
        contact = Contact(
            method=ContactMethod.EMAIL,
            value="info@immobilien-gmbh.de",
            confidence=ConfidenceLevel.MEDIUM,
            source_url="https://immobilien-gmbh.de/contact",
            cultural_context="german"
        )
        
        score = scoring_engine.score_contact(contact)
        
        assert 0.0 <= score <= 1.0
        assert score > 0.5  # Should have good score due to German domain and context
    
    def test_email_scoring_factors(self, scoring_engine):
        """Test email-specific scoring factors."""
        # High-quality email
        good_email = Contact(
            method=ContactMethod.EMAIL,
            value="info@immobilien-gmbh.de",
            confidence=ConfidenceLevel.HIGH,
            source_url="https://immobilien-gmbh.de/kontakt",
            extraction_method="mailto_link"
        )
        
        good_score = scoring_engine.score_contact(good_email)
        
        # Low-quality email
        bad_email = Contact(
            method=ContactMethod.EMAIL,
            value="test@example.com",
            confidence=ConfidenceLevel.LOW,
            source_url="https://random-site.com",
            extraction_method="standard_pattern"
        )
        
        bad_score = scoring_engine.score_contact(bad_email)
        
        assert good_score > bad_score
    
    def test_phone_scoring_factors(self, scoring_engine):
        """Test phone-specific scoring factors."""
        # Munich number (high value)
        munich_phone = Contact(
            method=ContactMethod.PHONE,
            value="+49 89 12345678",
            confidence=ConfidenceLevel.HIGH,
            source_url="https://muenchen-immobilien.de",
            cultural_context="german"
        )
        
        munich_score = scoring_engine.score_contact(munich_phone)
        
        # Generic number
        generic_phone = Contact(
            method=ContactMethod.PHONE,
            value="+1 555 1234567",
            confidence=ConfidenceLevel.MEDIUM,
            source_url="https://random-site.com"
        )
        
        generic_score = scoring_engine.score_contact(generic_phone)
        
        assert munich_score > generic_score
    
    def test_batch_scoring(self, scoring_engine):
        """Test batch scoring functionality."""
        contacts = [
            Contact(method=ContactMethod.EMAIL, value=f"test{i}@example.com", 
                   confidence=ConfidenceLevel.MEDIUM, source_url="https://test.com")
            for i in range(5)
        ]
        
        results = scoring_engine.score_batch(contacts)
        
        assert len(results) == 5
        for contact, score in results:
            assert 0.0 <= score <= 1.0
            assert contact in contacts
    
    def test_scoring_explanation(self, scoring_engine):
        """Test scoring explanation generation."""
        contact = Contact(
            method=ContactMethod.EMAIL,
            value="info@immobilien-gmbh.de",
            confidence=ConfidenceLevel.HIGH,
            source_url="https://immobilien-gmbh.de/kontakt"
        )
        
        explanation = scoring_engine.get_scoring_explanation(contact)
        
        assert 'final_score' in explanation
        assert 'confidence_level' in explanation
        assert 'factors' in explanation
        assert 'recommendations' in explanation
        
        # Check that all factors are present
        factors = explanation['factors']
        expected_factors = ['format_validity', 'domain_reputation', 'contextual_relevance', 
                          'extraction_method', 'cultural_fit', 'verification_status', 'historical_performance']
        for factor in expected_factors:
            assert factor in factors


class TestContactValidator:
    """Test contact validation functionality."""
    
    @pytest.fixture
    def validator(self):
        """Create contact validator."""
        return ContactValidator(enable_dns_verification=False)  # Disable DNS for testing
    
    @pytest.mark.asyncio
    async def test_email_validation_basic(self, validator):
        """Test basic email validation."""
        contact = Contact(
            method=ContactMethod.EMAIL,
            value="test@example.com",
            confidence=ConfidenceLevel.MEDIUM,
            source_url="https://test.com"
        )
        
        result = await validator.validate_contact(contact, "basic")
        
        assert result.is_valid
        assert result.validation_method == "syntax"
        assert result.confidence_score > 0.5
    
    @pytest.mark.asyncio
    async def test_email_validation_invalid(self, validator):
        """Test invalid email validation."""
        contact = Contact(
            method=ContactMethod.EMAIL,
            value="invalid-email",
            confidence=ConfidenceLevel.MEDIUM,
            source_url="https://test.com"
        )
        
        result = await validator.validate_contact(contact, "basic")
        
        assert not result.is_valid
        assert len(result.errors) > 0
        assert result.confidence_score < 0.5
    
    @pytest.mark.asyncio
    async def test_phone_validation(self, validator):
        """Test phone number validation."""
        contact = Contact(
            method=ContactMethod.PHONE,
            value="+49 89 12345678",
            confidence=ConfidenceLevel.HIGH,
            source_url="https://test.com"
        )
        
        result = await validator.validate_contact(contact, "standard")
        
        assert result.is_valid
        assert result.validation_method == "format"
        assert result.confidence_score > 0.7
    
    @pytest.mark.asyncio
    async def test_batch_validation(self, validator):
        """Test batch validation."""
        contacts = [
            Contact(method=ContactMethod.EMAIL, value="test1@example.com", 
                   confidence=ConfidenceLevel.MEDIUM, source_url="https://test.com"),
            Contact(method=ContactMethod.EMAIL, value="test2@example.com", 
                   confidence=ConfidenceLevel.MEDIUM, source_url="https://test.com"),
            Contact(method=ContactMethod.EMAIL, value="invalid-email", 
                   confidence=ConfidenceLevel.MEDIUM, source_url="https://test.com")
        ]
        
        results = await validator.validate_contacts_batch(contacts, "basic")
        
        assert len(results) == 3
        assert results[0].is_valid
        assert results[1].is_valid
        assert not results[2].is_valid
    
    def test_validation_summary(self, validator):
        """Test validation summary generation."""
        results = [
            ValidationResult(Mock(), True, "syntax", 0.9),
            ValidationResult(Mock(), True, "dns", 0.8),
            ValidationResult(Mock(), False, "syntax", 0.2, errors=["Invalid format"])
        ]
        
        summary = validator.get_validation_summary(results)
        
        assert summary['total'] == 3
        assert summary['valid'] == 2
        assert summary['invalid'] == 1
        assert summary['valid_percentage'] == 66.67
        assert summary['average_confidence'] > 0.6


class TestContactDiscoveryEngine:
    """Test main contact discovery engine."""
    
    @pytest.fixture
    def settings(self):
        """Create test settings."""
        return Settings()
    
    @pytest.fixture
    async def discovery_engine(self, settings):
        """Create discovery engine."""
        engine = ContactDiscoveryEngine(settings)
        async with engine:
            yield engine
    
    @pytest.mark.asyncio
    async def test_basic_discovery(self, discovery_engine):
        """Test basic contact discovery."""
        # Mock HTML content
        html_content = """
        <html>
        <body>
            <p>Contact us at info@example.com or call +49 89 12345678</p>
            <form action="/contact" method="post">
                <input name="name" required>
                <input name="email" required>
                <textarea name="message" required></textarea>
            </form>
            <a href="https://facebook.com/company">Facebook</a>
        </body>
        </html>
        """
        
        # Mock HTTP response
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = html_content
            mock_get.return_value = mock_response
            
            result = await discovery_engine.discover_contacts(
                "https://test.com",
                enable_crawling=False,
                enable_validation=False
            )
        
        assert result.contacts
        assert len(result.contacts) >= 2  # Email and phone
        assert result.forms
        assert len(result.forms) == 1
        assert result.extraction_time > 0
    
    @pytest.mark.asyncio
    async def test_discovery_with_validation(self, discovery_engine):
        """Test discovery with validation enabled."""
        html_content = """
        <p>Valid email: test@example.com</p>
        <p>Invalid email: not-an-email</p>
        """
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = html_content
            mock_get.return_value = mock_response
            
            result = await discovery_engine.discover_contacts(
                "https://test.com",
                enable_crawling=False,
                enable_validation=True
            )
        
        # Should have both valid and invalid contacts
        valid_contacts = [c for c in result.contacts if c.verification_status == ContactStatus.VERIFIED]
        invalid_contacts = [c for c in result.contacts if c.verification_status == ContactStatus.INVALID]
        
        assert len(valid_contacts) > 0
        assert len(invalid_contacts) > 0
    
    @pytest.mark.asyncio
    async def test_discovery_with_crawling(self, discovery_engine):
        """Test discovery with crawling enabled."""
        main_html = """
        <html>
        <body>
            <p>Main contact: main@example.com</p>
            <a href="/contact">Contact Page</a>
            <a href="/about">About Page</a>
        </body>
        </html>
        """
        
        contact_html = """
        <html>
        <body>
            <p>Contact page: contact@example.com, +49 89 12345678</p>
            <form action="/submit" method="post">
                <input name="name">
                <input name="email">
            </form>
        </body>
        </html>
        """
        
        # Mock different responses for different URLs
        responses = {
            "https://test.com": main_html,
            "https://test.com/contact": contact_html,
            "https://test.com/about": "<p>About us</p>"
        }
        
        def mock_get(url, **kwargs):
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = responses.get(url, "<p>Not found</p>")
            return mock_response
        
        with patch('httpx.AsyncClient.get', side_effect=mock_get):
            result = await discovery_engine.discover_contacts(
                "https://test.com",
                enable_crawling=True,
                enable_validation=False
            )
        
        # Should find contacts from main page and crawled pages
        assert len(result.contacts) >= 3  # Main email, contact email, contact phone
        assert len(result.forms) >= 1  # Form from contact page
    
    @pytest.mark.asyncio
    async def test_batch_discovery(self, discovery_engine):
        """Test batch discovery functionality."""
        urls = [
            "https://test1.com",
            "https://test2.com",
            "https://test3.com"
        ]
        
        html_content = "<p>Contact: test@example.com</p>"
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = html_content
            mock_get.return_value = mock_response
            
            results = await discovery_engine.discover_contacts_batch(
                urls, enable_crawling=False, enable_validation=False
            )
        
        assert len(results) == 3
        for result in results:
            assert result.contacts
            assert any(c.value == "test@example.com" for c in result.contacts)
    
    def test_discovery_stats(self, discovery_engine):
        """Test discovery statistics."""
        stats = discovery_engine.get_discovery_stats()
        
        assert isinstance(stats, DiscoveryStats)
        assert stats.urls_processed >= 0
        assert stats.contacts_found >= 0
        assert stats.forms_found >= 0
    
    def test_cache_functionality(self, discovery_engine):
        """Test discovery cache functionality."""
        cache_info = discovery_engine.get_cache_info()
        
        assert 'cache_size' in cache_info
        assert 'cache_keys' in cache_info
        assert isinstance(cache_info['cache_size'], int)
        
        # Test cache clearing
        discovery_engine.clear_cache()
        cache_info = discovery_engine.get_cache_info()
        assert cache_info['cache_size'] == 0


class TestContactDiscoveryIntegration:
    """Test contact discovery integration with storage."""
    
    @pytest.fixture
    def settings(self):
        """Create test settings."""
        return Settings()
    
    @pytest.fixture
    async def integration(self, settings):
        """Create integration instance."""
        integration = ContactDiscoveryIntegration(settings)
        async with integration:
            yield integration
    
    @pytest.mark.asyncio
    async def test_listing_processing(self, integration):
        """Test processing of a single listing."""
        listing = {
            'title': 'Test Apartment',
            'url': 'https://test-listing.com',
            'description': 'Nice apartment in Munich',
            'price': '1500€',
            'address': 'Munich, Germany'
        }
        
        # Mock discovery result
        with patch.object(integration.discovery_engine, 'discover_contacts') as mock_discover:
            from mwa_core.contact.models import ExtractionResult
            mock_result = ExtractionResult(
                contacts=[
                    Contact(method=ContactMethod.EMAIL, value="test@example.com", 
                           confidence=ConfidenceLevel.HIGH, source_url="https://test-listing.com"),
                    Contact(method=ContactMethod.PHONE, value="+49 89 12345678", 
                           confidence=ConfidenceLevel.HIGH, source_url="https://test-listing.com")
                ],
                forms=[],
                source_url="https://test-listing.com",
                extraction_time=1.0
            )
            mock_discover.return_value = mock_result
            
            contacts, forms = await integration.process_listing(listing, listing_id=1)
        
        assert len(contacts) == 2
        assert len(forms) == 0
    
    @pytest.mark.asyncio
    async def test_batch_listing_processing(self, integration):
        """Test batch processing of listings."""
        listings = [
            {'title': 'Listing 1', 'url': 'https://test1.com'},
            {'title': 'Listing 2', 'url': 'https://test2.com'},
            {'title': 'Listing 3', 'url': 'https://test3.com'}
        ]
        
        listing_ids = [1, 2, 3]
        
        # Mock discovery results
        with patch.object(integration.discovery_engine, 'discover_contacts') as mock_discover:
            from mwa_core.contact.models import ExtractionResult
            mock_result = ExtractionResult(
                contacts=[
                    Contact(method=ContactMethod.EMAIL, value="test@example.com", 
                           confidence=ConfidenceLevel.HIGH, source_url="https://test.com")
                ],
                forms=[],
                source_url="https://test.com",
                extraction_time=1.0
            )
            mock_discover.return_value = mock_result
            
            summary = await integration.process_listings_batch(listings, listing_ids)
        
        assert summary['processed'] == 3
        assert summary['contacts_found'] == 3
        assert summary['forms_found'] == 0
        assert summary['errors'] == 0
    
    @pytest.mark.asyncio
    async def test_contact_validation_integration(self, integration):
        """Test contact validation through integration."""
        # This would require actual storage setup
        # For now, test the validation logic
        contacts = [
            Contact(method=ContactMethod.EMAIL, value="valid@example.com", 
                   confidence=ConfidenceLevel.HIGH, source_url="https://test.com"),
            Contact(method=ContactMethod.EMAIL, value="invalid-email", 
                   confidence=ConfidenceLevel.LOW, source_url="https://test.com")
        ]
        
        results = await integration.validator.validate_contacts_batch(contacts, "basic")
        
        assert len(results) == 2
        assert results[0].is_valid
        assert not results[1].is_valid
    
    def test_contact_statistics(self, integration):
        """Test contact statistics generation."""
        stats = integration.get_contact_statistics()
        
        assert 'total_contacts' in stats
        assert 'contacts_by_type' in stats
        assert 'contacts_by_status' in stats
        assert 'recent_contacts_30_days' in stats
        assert 'high_confidence_contacts' in stats
        assert 'statistics_timestamp' in stats


class TestPerformanceAndReliability:
    """Test performance and reliability aspects."""
    
    @pytest.mark.asyncio
    async def test_rate_limiting(self):
        """Test rate limiting functionality."""
        from mwa_core.contact.validators import ContactValidator
        
        validator = ContactValidator(rate_limit_seconds=0.1)
        
        start_time = datetime.now()
        
        # Validate multiple contacts quickly
        contacts = [
            Contact(method=ContactMethod.EMAIL, value=f"test{i}@example.com", 
                   confidence=ConfidenceLevel.MEDIUM, source_url="https://test.com")
            for i in range(3)
        ]
        
        results = await validator.validate_contacts_batch(contacts, "basic")
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        # Should take at least 0.2 seconds due to rate limiting
        assert duration >= 0.2
        assert len(results) == 3
    
    @pytest.mark.asyncio
    async def test_error_handling(self):
        """Test error handling in discovery engine."""
        settings = Settings()
        engine = ContactDiscoveryEngine(settings)
        
        # Test with invalid URL
        result = await engine.discover_contacts(
            "invalid://url",
            enable_crawling=False,
            enable_validation=False
        )
        
        assert result.error is not None
        assert result.extraction_time > 0
    
    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test timeout handling."""
        settings = Settings()
        
        # Set very short timeout
        settings.contact_discovery.request_timeout = 0.1
        
        engine = ContactDiscoveryEngine(settings)
        
        with patch('httpx.AsyncClient.get') as mock_get:
            # Simulate timeout
            mock_get.side_effect = asyncio.TimeoutError("Request timed out")
            
            result = await engine.discover_contacts(
                "https://slow-site.com",
                enable_crawling=False,
                enable_validation=False
            )
        
        assert result.error is not None
        assert "timeout" in result.error.lower() or "timed out" in result.error.lower()
    
    def test_memory_efficiency(self):
        """Test memory efficiency with large datasets."""
        scoring_engine = ContactScoringEngine()
        
        # Create large batch of contacts
        contacts = [
            Contact(
                method=ContactMethod.EMAIL,
                value=f"test{i}@example.com",
                confidence=ConfidenceLevel.MEDIUM,
                source_url="https://test.com"
            )
            for i in range(1000)
        ]
        
        # Score all contacts
        results = scoring_engine.score_batch(contacts)
        
        assert len(results) == 1000
        assert all(0.0 <= score <= 1.0 for _, score in results)


class TestIntegrationScenarios:
    """Test real-world integration scenarios."""
    
    @pytest.mark.asyncio
    async def test_german_real_estate_scenario(self):
        """Test German real estate website scenario."""
        settings = Settings()
        settings.contact_discovery.cultural_context = "german"
        settings.contact_discovery.language_preference = "de"
        
        engine = ContactDiscoveryEngine(settings)
        
        # Mock German real estate page
        german_html = """
        <html lang="de">
        <head><title>Immobilien München - Wohnungen zur Miete</title></head>
        <body>
            <h1>Immobilienverwaltung München</h1>
            <p>Kontaktieren Sie uns:</p>
            <p>Email: info@muenchen-immobilien.de</p>
            <p>Telefon: +49 89 12345678</p>
            <p>Mobil: +49 151 98765432</p>
            
            <h2>Kontaktformular</h2>
            <form action="/kontakt" method="post">
                <input type="text" name="name" placeholder="Ihr Name" required>
                <input type="email" name="email" placeholder="Ihre E-Mail" required>
                <input type="tel" name="telefon" placeholder="Ihre Telefonnummer">
                <textarea name="nachricht" placeholder="Ihre Nachricht" required></textarea>
                <button type="submit">Nachricht senden</button>
            </form>
            
            <h3>Social Media</h3>
            <a href="https://xing.com/profile/immobilien-verwaltung">XING</a>
            <a href="https://linkedin.com/company/muenchen-immobilien">LinkedIn</a>
            
            <h3>Impressum</h3>
            <p>Email: verwaltung@example.com</p>
            <p>Telefon: 089 87654321</p>
        </body>
        </html>
        """
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = german_html
            mock_get.return_value = mock_response
            
            result = await engine.discover_contacts(
                "https://muenchen-immobilien.de",
                enable_crawling=False,
                enable_validation=False
            )
        
        # Should find multiple German-specific contacts
        assert len(result.contacts) >= 4  # Multiple emails and phones
        assert len(result.forms) >= 1
        
        # Check for German-specific patterns
        german_emails = [c for c in result.contacts if c.method == ContactMethod.EMAIL and '.de' in c.value]
        munich_phones = [c for c in result.contacts if c.method == ContactMethod.PHONE and '089' in c.value]
        german_social = [c for c in result.contacts if c.method == ContactMethod.SOCIAL_MEDIA and self._is_xing_url(c.value)]
        
        assert len(german_emails) > 0
        assert len(munich_phones) > 0
        assert len(german_social) > 0
    
    @pytest.mark.asyncio
    async def test_obfuscated_contact_extraction(self):
        """Test extraction of obfuscated contacts."""
        settings = Settings()
        engine = ContactDiscoveryEngine(settings)
        
        # HTML with obfuscated contacts
        obfuscated_html = """
        <html>
        <body>
            <p>Contact: info [at] example [dot] com</p>
            <p>Email: support (at) test (dot) org</p>
            <p>Phone: +49 89 123 456 789</p>
            <p>Mobile: 0151 987 654 321</p>
            <script>
                document.write('admin' + '@' + 'website' + '.' + 'com');
            </script>
        </body>
        </html>
        """
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = obfuscated_html
            mock_get.return_value = mock_response
            
            result = await engine.discover_contacts(
                "https://obfuscated-site.com",
                enable_crawling=False,
                enable_validation=False
            )
        
        # Should find both standard and obfuscated contacts
        all_contacts = result.contacts
        assert len(all_contacts) >= 2
        
        # Check for obfuscated email extraction
        obfuscated_contacts = [c for c in all_contacts if c.metadata.get('extraction_pattern') == 'obfuscated_text']
        assert len(obfuscated_contacts) > 0
    
    @pytest.mark.asyncio
    async def test_contact_deduplication(self):
        """Test contact deduplication functionality."""
        settings = Settings()
        engine = ContactDiscoveryEngine(settings)
        
        # HTML with duplicate contacts
        duplicate_html = """
        <html>
        <body>
            <header>Contact: info@example.com</header>
            <main>Email us at info@example.com for more info</main>
            <footer>Our email: info@example.com</footer>
            <p>Phone: +49 89 12345678 (repeated)</p>
            <p>Call us: +49 89 12345678</p>
        </body>
        </html>
        """
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = duplicate_html
            mock_get.return_value = mock_response
            
            result = await engine.discover_contacts(
                "https://duplicate-site.com",
                enable_crawling=False,
                enable_validation=False
            )
        
        # Should deduplicate contacts
        unique_emails = set(c.value for c in result.contacts if c.method == ContactMethod.EMAIL)
        unique_phones = set(c.value for c in result.contacts if c.method == ContactMethod.PHONE)
        
        assert len(unique_emails) == 1  # Only one unique email
        assert len(unique_phones) == 1  # Only one unique phone


# Integration test for the complete pipeline
@pytest.mark.asyncio
async def test_complete_contact_discovery_pipeline():
    """Test the complete contact discovery pipeline end-to-end."""
    settings = Settings()
    
    # Configure for comprehensive testing
    settings.contact_discovery.enabled = True
    settings.contact_discovery.validation_enabled = True
    settings.contact_discovery.smart_crawling = True
    settings.contact_discovery.ocr_extraction = True
    settings.contact_discovery.social_media_detection = True
    
    async with ContactDiscoveryEngine(settings) as engine:
        # Mock comprehensive website
        comprehensive_html = """
        <html lang="de">
        <head><title>Immobilienverwaltung München</title></head>
        <body>
            <!-- Direct contacts -->
            <p>Kontakt: info@immobilien-muenchen.de</p>
            <p>Telefon: +49 89 12345678</p>
            <p>Mobil: +49 151 98765432</p>
            
            <!-- Obfuscated contacts -->
            <p>Email: verwaltung [at] hausverwaltung [dot] de</p>
            
            <!-- Contact form -->
            <form action="/kontakt" method="post">
                <input name="name" required>
                <input name="email" required>
                <textarea name="nachricht" required></textarea>
                <button type="submit">Senden</button>
            </form>
            
            <!-- Social media -->
            <a href="https://xing.com/profile/immobilien-verwaltung">XING Profil</a>
            <a href="https://linkedin.com/company/muenchen-immobilien">LinkedIn</a>
            
            <!-- Links to other pages -->
            <a href="/kontakt">Kontaktseite</a>
            <a href="/impressum">Impressum</a>
        </body>
        </html>
        """
        
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.text = comprehensive_html
            mock_get.return_value = mock_response
            
            # Run complete discovery
            result = await engine.discover_contacts(
                "https://comprehensive-test.com",
                enable_crawling=True,
                enable_validation=True
            )
        
        # Verify comprehensive results
        assert len(result.contacts) >= 4  # Multiple emails, phones, social profiles
        assert len(result.forms) >= 1  # Contact form
        
        # Check for different contact types
        emails = [c for c in result.contacts if c.method == ContactMethod.EMAIL]
        phones = [c for c in result.contacts if c.method == ContactMethod.PHONE]
        social = [c for c in result.contacts if c.method == ContactMethod.SOCIAL_MEDIA]
        
        assert len(emails) >= 2  # Direct and obfuscated
        assert len(phones) >= 2  # Landline and mobile
        assert len(social) >= 1  # Social media profiles
        
        # Check confidence levels
        high_confidence = [c for c in result.contacts if c.confidence == ConfidenceLevel.HIGH]
        medium_confidence = [c for c in result.contacts if c.confidence == ConfidenceLevel.MEDIUM]
        
        assert len(high_confidence) > 0  # Should have some high-confidence contacts
        assert len(medium_confidence) > 0  # Should have some medium-confidence contacts
        
        # Check validation status
        verified_contacts = [c for c in result.contacts if c.verification_status == ContactStatus.VERIFIED]
        invalid_contacts = [c for c in result.contacts if c.verification_status == ContactStatus.INVALID]
        
        assert len(verified_contacts) > 0  # Should have some verified contacts
        # May have invalid contacts depending on validation results
        
        # Check metadata
        for contact in result.contacts:
            assert contact.metadata is not None
            assert 'extraction_method' in contact.metadata
            assert 'confidence_score' in contact.metadata
        
        click.echo(f"Complete pipeline test successful: {len(result.contacts)} contacts, {len(result.forms)} forms")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])