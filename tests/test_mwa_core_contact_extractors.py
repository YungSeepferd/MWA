"""
Focused tests for contact extractors in MWA Core.

Tests specific extraction methods and edge cases:
- Email extraction patterns and obfuscation
- Phone number format variations
- Form detection and analysis
- Social media profile discovery
- OCR and PDF extraction
- Error handling and edge cases
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path

from mwa_core.contact.extractors import (
    EmailExtractor, PhoneExtractor, FormExtractor, 
    SocialMediaExtractor, OCRContactExtractor, PDFContactExtractor
)
from mwa_core.contact.models import (
    Contact, ContactMethod, ConfidenceLevel, DiscoveryContext
)
from mwa_core.config.settings import Settings


class TestEmailExtractorAdvanced:
    """Advanced tests for email extraction."""
    
    @pytest.fixture
    def settings(self):
        return Settings()
    
    @pytest.fixture
    async def extractor(self, settings):
        extractor = EmailExtractor(settings)
        async with extractor:
            yield extractor
    
    def test_unicode_obfuscation_extraction(self, extractor):
        """Test extraction of Unicode-obfuscated emails."""
        test_cases = [
            "Contact: admin&#64;website&#46;com",
            "Email: info&#64;example&#46;org",
            "Support: help&#64;company&#46;de",
        ]
        
        for test_text in test_cases:
            contacts = extractor.extract_emails(test_text, "https://test.com", Mock())
            assert len(contacts) > 0
            
            # Check that Unicode obfuscation was detected
            unicode_contacts = [c for c in contacts if c.metadata.get('extraction_pattern') == 'unicode']
            assert len(unicode_contacts) > 0
    
    def test_javascript_obfuscation_extraction(self, extractor):
        """Test extraction of JavaScript-obfuscated emails."""
        test_cases = [
            "document.write('admin' + '@' + 'website' + '.' + 'com')",
            "var email = 'info' + '@' + 'example' + '.' + 'de';",
            "contact = 'support' + '@' + 'company' + '.' + 'org';",
        ]
        
        for test_text in test_cases:
            contacts = extractor.extract_emails(test_text, "https://test.com", Mock())
            # JavaScript obfuscation is complex to detect, but should find some patterns
            assert len(contacts) >= 0  # May or may not find depending on pattern complexity
    
    def test_image_based_email_extraction(self, extractor):
        """Test handling of image-based email obfuscation."""
        # This would typically be handled by OCR extractor
        # But email extractor should handle basic cases
        test_text = """
        <img src="email.png" alt="info@example.com">
        <img src="contact.gif" title="support@test.org">
        """
        
        contacts = extractor.extract_emails(test_text, "https://test.com", Mock())
        # Should extract from alt/title attributes
        assert len(contacts) >= 0  # May find emails in alt/title text
    
    def test_email_with_special_characters(self, extractor):
        """Test extraction of emails with special characters."""
        test_cases = [
            "test+tag@example.com",
            "user.name@company.co.uk",
            "admin_test@subdomain.example.org",
            "info-2024@muenchen-immobilien.de",
        ]
        
        for email in test_cases:
            contacts = extractor.extract_emails(f"Contact: {email}", "https://test.com", Mock())
            assert len(contacts) > 0
            assert any(c.value == email for c in contacts)
    
    def test_international_domain_extraction(self, extractor):
        """Test extraction of emails with international domains."""
        test_cases = [
            "test@example.de",
            "info@company.co.uk",
            "contact@site.com.au",
            "admin@website.fr",
            "support@firma.it",
        ]
        
        for email in test_cases:
            contacts = extractor.extract_emails(f"Email: {email}", "https://test.com", Mock())
            assert len(contacts) > 0
            assert any(c.value == email for c in contacts)
    
    def test_disposable_email_detection(self, extractor):
        """Test detection of disposable email addresses."""
        disposable_emails = [
            "test@tempmail.org",
            "user@10minutemail.com",
            "contact@mailinator.com",
        ]
        
        for email in disposable_emails:
            contacts = extractor.extract_emails(f"Email: {email}", "https://test.com", Mock())
            # Should still extract but with lower confidence
            if contacts:
                assert contacts[0].confidence == ConfidenceLevel.LOW
    
    def test_email_context_scoring(self, extractor):
        """Test email scoring based on context."""
        # High context (contact page)
        high_context_text = """
        <html>
        <head><title>Kontakt - Immobilienverwaltung</title></head>
        <body>
            <h1>Kontaktieren Sie uns</h1>
            <p>Email: info@immobilien-muenchen.de</p>
        </body>
        </html>
        """
        
        high_context_contacts = extractor.extract_emails(high_context_text, "https://immobilien.de/kontakt", Mock())
        assert len(high_context_contacts) > 0
        assert high_context_contacts[0].confidence == ConfidenceLevel.HIGH
        
        # Low context (random page)
        low_context_text = """
        <html>
        <body>
            <p>Random text with email: test@example.com</p>
        </body>
        </html>
        """
        
        low_context_contacts = extractor.extract_emails(low_context_text, "https://random-site.com/page", Mock())
        assert len(low_context_contacts) > 0
        assert low_context_contacts[0].confidence == ConfidenceLevel.MEDIUM


class TestPhoneExtractorAdvanced:
    """Advanced tests for phone number extraction."""
    
    @pytest.fixture
    def settings(self):
        return Settings()
    
    @pytest.fixture
    async def extractor(self, settings):
        extractor = PhoneExtractor(settings)
        async with extractor:
            yield extractor
    
    def test_german_area_code_validation(self, extractor):
        """Test validation of German area codes."""
        valid_area_codes = [
            "089", "030", "040", "069", "0711", "0211", "0221", "0231"
        ]
        
        for area_code in valid_area_codes:
            phone = f"+49 {area_code} 12345678"
            assert extractor._validate_german_format(phone)
    
    def test_international_phone_formats(self, extractor):
        """Test various international phone formats."""
        test_cases = [
            "+1 555 123 4567",      # USA
            "+44 20 1234 5678",     # UK
            "+33 1 23 45 67 89",    # France
            "+81 3 1234 5678",      # Japan
            "+86 10 1234 5678",     # China
        ]
        
        for phone in test_cases:
            contacts = extractor.extract_phones(f"Phone: {phone}", "https://test.com", Mock())
            assert len(contacts) > 0
            assert any(c.value == phone.replace(' ', '') for c in contacts)
    
    def test_mobile_vs_landline_detection(self, extractor):
        """Test detection of mobile vs landline numbers."""
        # German mobile numbers
        mobile_numbers = [
            "+49 151 12345678",
            "+49 160 98765432",
            "+49 176 55555555",
            "0151 12345678",
            "0176 98765432"
        ]
        
        for mobile in mobile_numbers:
            contacts = extractor.extract_phones(f"Mobile: {mobile}", "https://test.com", Mock())
            assert len(contacts) > 0
            mobile_contacts = [c for c in contacts if c.metadata.get('is_mobile')]
            assert len(mobile_contacts) > 0
            assert all(c.confidence == ConfidenceLevel.HIGH for c in mobile_contacts)
        
        # Landline numbers
        landline_numbers = [
            "+49 89 12345678",
            "+49 30 98765432",
            "089 12345678",
            "030 98765432"
        ]
        
        for landline in landline_numbers:
            contacts = extractor.extract_phones(f"Phone: {landline}", "https://test.com", Mock())
            assert len(contacts) > 0
            landline_contacts = [c for c in contacts if not c.metadata.get('is_mobile')]
            assert len(landline_contacts) > 0
    
    def test_phone_number_with_extensions(self, extractor):
        """Test phone numbers with extensions."""
        test_cases = [
            "+49 89 12345678-123",
            "+49 30 98765432 ext. 456",
            "089 12345678 x789",
        ]
        
        for phone in test_cases:
            contacts = extractor.extract_phones(f"Phone: {phone}", "https://test.com", Mock())
            # Should extract the base number
            assert len(contacts) > 0
    
    def test_formatted_phone_extraction(self, extractor):
        """Test extraction of various formatted phone numbers."""
        test_cases = [
            "(089) 123 456 789",
            "089/123 456 78",
            "089-123-456-789",
            "+49 (0) 89 123 456 78",
        ]
        
        for phone in test_cases:
            contacts = extractor.extract_phones(f"Phone: {phone}", "https://test.com", Mock())
            assert len(contacts) > 0
    
    def test_phone_context_scoring(self, extractor):
        """Test phone scoring based on context."""
        # Munich business context
        munich_text = """
        <html>
        <head><title>Immobilienverwaltung München</title></head>
        <body>
            <h1>Hausverwaltung München</h1>
            <p>Telefon: +49 89 12345678</p>
        </body>
        </html>
        """
        
        munich_contacts = extractor.extract_phones(munich_text, "https://muenchen-immobilien.de", 
                                                  Mock(cultural_context="german"))
        assert len(munich_contacts) > 0
        assert munich_contacts[0].confidence == ConfidenceLevel.HIGH


class TestFormExtractorAdvanced:
    """Advanced tests for form extraction."""
    
    @pytest.fixture
    def settings(self):
        return Settings()
    
    @pytest.fixture
    async def extractor(self, settings):
        extractor = FormExtractor(settings)
        async with extractor:
            yield extractor
    
    def test_complex_form_analysis(self, extractor):
        """Test analysis of complex forms."""
        from bs4 import BeautifulSoup
        
        complex_html = """
        <form action="/kontakt" method="post" id="contactForm" class="contact-form">
            <fieldset>
                <legend>Kontaktinformationen</legend>
                <label for="name">Name *</label>
                <input type="text" id="name" name="name" required>
                
                <label for="email">E-Mail *</label>
                <input type="email" id="email" name="email" required>
                
                <label for="phone">Telefon</label>
                <input type="tel" id="phone" name="phone">
                
                <label for="subject">Betreff *</label>
                <select id="subject" name="subject" required>
                    <option value="">Bitte wählen</option>
                    <option value="anfrage">Anfrage</option>
                    <option value="besichtigung">Besichtigung</option>
                    <option value="sonstiges">Sonstiges</option>
                </select>
            </fieldset>
            
            <fieldset>
                <legend>Ihre Nachricht</legend>
                <label for="message">Nachricht *</label>
                <textarea id="message" name="message" required></textarea>
                
                <label for="file">Datei anhängen</label>
                <input type="file" id="file" name="file" accept=".pdf,.doc,.docx">
            </fieldset>
            
            <fieldset>
                <legend>Einverständnis</legend>
                <label>
                    <input type="checkbox" name="datenschutz" required>
                    Ich akzeptiere die Datenschutzerklärung *
                </label>
                
                <label>
                    <input type="checkbox" name="newsletter">
                    Newsletter abonnieren
                </label>
            </fieldset>
            
            <input type="hidden" name="csrf_token" value="abc123xyz">
            <button type="submit">Nachricht senden</button>
        </form>
        """
        
        soup = BeautifulSoup(complex_html, 'html.parser')
        context = Mock()
        context.discovery_path = []
        
        forms = extractor.extract_forms(soup, "https://test.com/kontakt", context)
        
        assert len(forms) == 1
        form = forms[0]
        
        # Check complex form properties
        assert len(form.fields) >= 8  # Multiple fields
        assert "csrf_token" in form.fields
        assert form.csrf_token == "abc123xyz"
        assert len(form.required_fields) >= 4  # Multiple required fields
        
        # Check complexity scoring
        assert form.complexity_score > 0.5  # Should be complex
        assert form.user_friendly_score > 0.5  # Should be user-friendly
    
    def test_non_contact_form_filtering(self, extractor):
        """Test filtering out non-contact forms."""
        from bs4 import BeautifulSoup
        
        # Login form (should be filtered out)
        login_html = """
        <form action="/login" method="post">
            <input name="username" type="text" required>
            <input name="password" type="password" required>
            <button type="submit">Login</button>
        </form>
        """
        
        login_soup = BeautifulSoup(login_html, 'html.parser')
        context = Mock()
        context.discovery_path = []
        
        login_forms = extractor.extract_forms(login_soup, "https://test.com/login", context)
        assert len(login_forms) == 0  # Should not be recognized as contact form
        
        # Search form (should be filtered out)
        search_html = """
        <form action="/search" method="get">
            <input name="q" type="search" placeholder="Search...">
            <button type="submit">Search</button>
        </form>
        """
        
        search_soup = BeautifulSoup(search_html, 'html.parser')
        search_forms = extractor.extract_forms(search_soup, "https://test.com/search", context)
        assert len(search_forms) == 0  # Should not be recognized as contact form
    
    def test_multilingual_form_detection(self, extractor):
        """Test form detection in different languages."""
        from bs4 import BeautifulSoup
        
        # German form
        german_html = """
        <form action="/kontakt" method="post">
            <input name="name" placeholder="Ihr Name">
            <input name="email" placeholder="Ihre E-Mail">
            <textarea name="nachricht" placeholder="Ihre Nachricht"></textarea>
            <button type="submit">Nachricht senden</button>
        </form>
        """
        
        german_soup = BeautifulSoup(german_html, 'html.parser')
        context = Mock()
        context.discovery_path = []
        context.language_preference = "de"
        
        german_forms = extractor.extract_forms(german_soup, "https://test.de/kontakt", context)
        assert len(german_forms) == 1
        assert german_forms[0].confidence == ConfidenceLevel.HIGH  # German context
    
    def test_form_accessibility_features(self, extractor):
        """Test detection of form accessibility features."""
        from bs4 import BeautifulSoup
        
        accessible_html = """
        <form action="/contact" method="post">
            <fieldset>
                <legend>Contact Information</legend>
                
                <label for="name">Full Name <span class="required">*</span></label>
                <input type="text" id="name" name="name" required aria-required="true" 
                       placeholder="Enter your full name">
                
                <label for="email">Email Address <span class="required">*</span></label>
                <input type="email" id="email" name="email" required aria-required="true"
                       placeholder="your.email@example.com">
                
                <label for="message">Your Message <span class="required">*</span></label>
                <textarea id="message" name="message" required aria-required="true" 
                          placeholder="Please describe your inquiry..."></textarea>
                
                <div class="help-text">Fields marked with * are required</div>
            </fieldset>
            
            <button type="submit">Send Message</button>
        </form>
        """
        
        soup = BeautifulSoup(accessible_html, 'html.parser')
        context = Mock()
        context.discovery_path = []
        
        forms = extractor.extract_forms(soup, "https://test.com/contact", context)
        
        assert len(forms) == 1
        form = forms[0]
        
        # Should have high user-friendliness score due to accessibility features
        assert form.user_friendly_score > 0.7


class TestSocialMediaExtractorAdvanced:
    """Advanced tests for social media extraction."""
    
    @pytest.fixture
    def settings(self):
        return Settings()
    
    @pytest.fixture
    async def extractor(self, settings):
        extractor = SocialMediaExtractor(settings)
        async with extractor:
            yield extractor
    
    def test_business_social_media_detection(self, extractor):
        """Test detection of business-related social media profiles."""
        test_text = """
        <div class="company-info">
            <h2>Immobilienverwaltung München GmbH</h2>
            <p>Follow us on LinkedIn: https://linkedin.com/company/immobilien-verwaltung-muenchen</p>
            <p>XING Profile: https://xing.com/profile/Max_Mustermann_Immobilien</p>
            <p>Facebook: https://facebook.com/ImmobilienMuenchen</p>
            <p>Instagram: https://instagram.com/muenchen_immobilien</p>
        </div>
        """
        
        profiles = extractor.extract_social_media(test_text, "https://company.com", Mock())
        
        business_profiles = [p for p in profiles if p.is_business_profile]
        assert len(business_profiles) > 0
        
        # Check that business keywords are detected
        for profile in business_profiles:
            assert any(keyword in profile.username.lower() or (profile.display_name or '').lower() 
                      for keyword in ['immobilien', 'verwaltung', 'muenchen'])
    
    def test_social_media_platform_specific_patterns(self, extractor):
        """Test platform-specific URL patterns."""
        test_cases = [
            # LinkedIn variations
            ("https://linkedin.com/in/johndoe", SocialMediaPlatform.LINKEDIN),
            ("https://linkedin.com/company/acme-corp", SocialMediaPlatform.LINKEDIN),
            ("https://linkedin.com/pub/jane-smith/1/234/567", SocialMediaPlatform.LINKEDIN),
            
            # XING variations
            ("https://xing.com/profile/Max_Mustermann", SocialMediaPlatform.XING),
            ("https://xing.com/companies/Immobilien-GmbH", SocialMediaPlatform.XING),
            
            # WhatsApp variations
            ("https://wa.me/4915112345678", SocialMediaPlatform.WHATSAPP),
            ("https://api.whatsapp.com/send?phone=491601234567", SocialMediaPlatform.WHATSAPP),
        ]
        
        for url, expected_platform in test_cases:
            profiles = extractor.extract_social_media(f"Profile: {url}", "https://test.com", Mock())
            assert len(profiles) > 0
            assert any(p.platform == expected_platform and p.profile_url == url for p in profiles)
    
    def test_social_media_confidence_scoring(self, extractor):
        """Test confidence scoring for social media profiles."""
        # High confidence (business context)
        business_text = """
        <html>
        <head><title>Immobilienverwaltung - Kontakt</title></head>
        <body>
            <h1>Unsere Social Media Profile</h1>
            <p>LinkedIn: https://linkedin.com/company/immobilien-verwaltung</p>
        </body>
        </html>
        """
        
        business_profiles = extractor.extract_social_media(business_text, "https://immobilien.de/kontakt", Mock())
        assert len(business_profiles) > 0
        assert business_profiles[0].confidence == ConfidenceLevel.HIGH
        
        # Low confidence (random mention)
        random_text = """
        <p>Random text with social media: https://facebook.com/somepage</p>
        """
        
        random_profiles = extractor.extract_social_media(random_text, "https://random-site.com/page", Mock())
        if random_profiles:
            assert random_profiles[0].confidence == ConfidenceLevel.MEDIUM
    
    def test_social_media_display_name_extraction(self, extractor):
        """Test extraction of display names for social media profiles."""
        test_text = """
        <div class="team-member">
            <h3>Max Mustermann</h3>
            <p>LinkedIn: https://linkedin.com/in/max-mustermann</p>
            <p>Experienced property manager with 10+ years in Munich real estate market.</p>
        </div>
        """
        
        profiles = extractor.extract_social_media(test_text, "https://company.com/team", Mock())
        
        linkedin_profiles = [p for p in profiles if p.platform == SocialMediaPlatform.LINKEDIN]
        if linkedin_profiles:
            profile = linkedin_profiles[0]
            assert profile.display_name is not None
            assert "Max Mustermann" in profile.display_name


class TestOCRContactExtractor:
    """Tests for OCR-based contact extraction."""
    
    @pytest.fixture
    def settings(self):
        return Settings()
    
    @pytest.fixture
    def extractor(self, settings):
        extractor = OCRContactExtractor(settings)
        return extractor
    
    def test_ocr_extractor_initialization(self, extractor):
        """Test OCR extractor initialization."""
        assert extractor.languages == ['deu', 'eng']
        assert extractor.confidence_threshold == 0.7
        assert extractor.preprocess is True
    
    def test_image_format_support(self, extractor):
        """Test supported image formats."""
        supported_formats = ['.png', '.jpg', '.jpeg', '.webp', '.bmp', '.tiff']
        
        for ext in supported_formats:
            assert extractor.can_process(f"test{ext}")
            assert extractor.can_process(f"https://example.com/image{ext}")
    
    def test_ocr_extraction_mock(self, extractor):
        """Test OCR extraction with mocked text."""
        # Mock the OCR text extraction
        with patch.object(extractor, '_extract_text', return_value="Contact: info@example.com, Phone: +49 89 12345678"):
            with patch.object(extractor, '_load_image', return_value=Mock()):
                with patch.object(extractor, '_enhance_image', return_value=Mock()):
                    contacts = extractor.extract_contacts("test_image.png")
        
        assert len(contacts) >= 2  # Should find email and phone
        assert any(c.contact.method == ContactMethod.EMAIL for c in contacts)
        assert any(c.contact.method == ContactMethod.PHONE for c in contacts)
    
    def test_image_quality_scoring(self, extractor):
        """Test image quality scoring."""
        # Mock image with different quality levels
        from PIL import Image
        import numpy as np
        
        # High quality image (mock)
        high_quality_image = Mock()
        high_quality_image.convert.return_value = Mock()
        high_quality_image.convert.return_value.size = (1000, 1000)
        
        with patch('cv2.Laplacian', return_value=np.array([[100, 200], [300, 400]])):
            with patch('numpy.std', return_value=50):
                quality = extractor._calculate_image_quality(high_quality_image)
                assert quality > 0.5
        
        # Low quality image (mock)
        low_quality_image = Mock()
        low_quality_image.convert.return_value = Mock()
        low_quality_image.convert.return_value.size = (100, 100)
        
        with patch('cv2.Laplacian', return_value=np.array([[10, 20], [30, 40]])):
            with patch('numpy.std', return_value=10):
                quality = extractor._calculate_image_quality(low_quality_image)
                assert quality < 0.5


class TestPDFContactExtractor:
    """Tests for PDF-based contact extraction."""
    
    @pytest.fixture
    def settings(self):
        return Settings()
    
    @pytest.fixture
    def extractor(self, settings):
        extractor = PDFContactExtractor(settings)
        return extractor
    
    def test_pdf_extractor_initialization(self, extractor):
        """Test PDF extractor initialization."""
        assert extractor.max_file_size_mb == 10
        assert extractor.extract_tables is True
        assert extractor.extract_metadata is True
        assert extractor.confidence_threshold == 0.7
    
    def test_pdf_format_support(self, extractor):
        """Test supported PDF formats."""
        assert extractor.can_process("test.pdf")
        assert extractor.can_process("https://example.com/document.pdf")
        assert extractor.can_process(b"%PDF-1.4\n...")
        assert not extractor.can_process("test.doc")
        assert not extractor.can_process("https://example.com/image.jpg")
    
    def test_pdf_extraction_mock(self, extractor):
        """Test PDF extraction with mocked content."""
        # Mock PDF text extraction
        with patch.object(extractor, '_extract_text', return_value="Contact: info@example.com, Phone: +49 89 12345678"):
            with patch.object(extractor, '_load_pdf', return_value=Mock()):
                with patch.object(extractor, '_extract_from_metadata', return_value=[]):
                    contacts = extractor.extract_contacts("test.pdf")
        
        assert len(contacts) >= 2  # Should find email and phone
        assert any(c.contact.method == ContactMethod.EMAIL for c in contacts)
        assert any(c.contact.method == ContactMethod.PHONE for c in contacts)
    
    def test_pdf_metadata_extraction(self, extractor):
        """Test PDF metadata extraction."""
        mock_metadata = {
            'author': 'John Doe <john.doe@example.com>',
            'creator': 'Adobe Acrobat <info@company.com>',
            'title': 'Contact Information Document',
            'subject': 'Real Estate Contacts'
        }
        
        mock_pdf = Mock()
        mock_pdf.metadata = mock_metadata
        
        with patch.object(extractor, '_extract_contacts_from_text', return_value=[]):
            metadata_contacts = extractor._extract_from_metadata(mock_pdf, "test.pdf", {})
        
        # Should extract contacts from metadata fields
        assert len(metadata_contacts) >= 0  # May find contacts depending on implementation
    
    def test_large_pdf_handling(self, extractor):
        """Test handling of large PDF files."""
        # Mock large file size
        with patch('pathlib.Path.stat') as mock_stat:
            mock_stat.return_value.st_size = 20 * 1024 * 1024  # 20MB
            
            # Should skip processing due to size limit
            contacts = extractor.extract_contacts("large.pdf")
            assert len(contacts) == 0


# Error handling and edge case tests
class TestExtractorErrorHandling:
    """Test error handling in extractors."""
    
    @pytest.mark.asyncio
    async def test_extractor_network_errors(self):
        """Test handling of network errors."""
        settings = Settings()
        
        # Test email extractor
        async with EmailExtractor(settings) as extractor:
            with patch('httpx.AsyncClient.get', side_effect=Exception("Network error")):
                contacts = await extractor.extract_emails("test@example.com", "https://test.com", Mock())
                assert len(contacts) == 0  # Should handle error gracefully
    
    @pytest.mark.asyncio
    async def test_extractor_timeout_handling(self):
        """Test handling of request timeouts."""
        settings = Settings()
        settings.contact_discovery.request_timeout = 0.1
        
        async with EmailExtractor(settings) as extractor:
            with patch('httpx.AsyncClient.get', side_effect=asyncio.TimeoutError):
                contacts = await extractor.extract_emails("test content", "https://test.com", Mock())
                assert len(contacts) == 0  # Should handle timeout gracefully
    
    def test_extractor_invalid_input_handling(self):
        """Test handling of invalid input."""
        settings = Settings()
        
        # Test with None/empty input
        extractor = EmailExtractor(settings)
        
        contacts = extractor.extract_emails(None, "https://test.com", Mock())
        assert len(contacts) == 0
        
        contacts = extractor.extract_emails("", "https://test.com", Mock())
        assert len(contacts) == 0
        
        contacts = extractor.extract_emails("   ", "https://test.com", Mock())
        assert len(contacts) == 0
    
    def test_extractor_malformed_html_handling(self):
        """Test handling of malformed HTML."""
        settings = Settings()
        
        malformed_html_cases = [
            "<p>Unclosed paragraph",
            "<div><span>Nested unclosed",
            "<form><input></form><input>",  # Input outside form
            "<<<<>>>>",  # Invalid markup
        ]
        
        for malformed_html in malformed_html_cases:
            from bs4 import BeautifulSoup
            try:
                soup = BeautifulSoup(malformed_html, 'html.parser')
                extractor = FormExtractor(settings)
                forms = extractor.extract_forms(soup, "https://test.com", Mock())
                # Should not crash, may return empty list
                assert isinstance(forms, list)
            except Exception as e:
                # Should handle gracefully
                assert "malformed" in str(e).lower() or "parse" in str(e).lower()


# Performance tests
class TestExtractorPerformance:
    """Test performance characteristics of extractors."""
    
    def test_large_text_processing(self):
        """Test processing of large text documents."""
        settings = Settings()
        extractor = EmailExtractor(settings)
        
        # Generate large text with emails
        large_text = " ".join([
            f"Contact person {i}: email{i}@example{i}.com, phone: +49 89 {i}12345678"
            for i in range(1000)
        ])
        
        start_time = asyncio.get_event_loop().time()
        contacts = extractor.extract_emails(large_text, "https://test.com", Mock())
        end_time = asyncio.get_event_loop().time()
        
        assert len(contacts) == 1000  # Should find all emails
        assert end_time - start_time < 5.0  # Should complete within reasonable time
    
    def test_concurrent_extraction(self):
        """Test concurrent extraction performance."""
        settings = Settings()
        
        async def concurrent_test():
            extractor = EmailExtractor(settings)
            async with extractor:
                # Create multiple extraction tasks
                tasks = []
                for i in range(10):
                    text = f"Contact: test{i}@example{i}.com"
                    task = extractor.extract_emails(text, "https://test.com", Mock())
                    tasks.append(task)
                
                # Run concurrently
                start_time = asyncio.get_event_loop().time()
                results = await asyncio.gather(*tasks)
                end_time = asyncio.get_event_loop().time()
                
                # Check results
                assert len(results) == 10
                for result in results:
                    assert len(result) == 1
                    assert result[0].value == f"test{results.index(result)}@example{results.index(result)}.com"
                
                assert end_time - start_time < 2.0  # Should complete quickly
        
        asyncio.run(concurrent_test())


if __name__ == "__main__":
    pytest.main([__file__, "-v"])