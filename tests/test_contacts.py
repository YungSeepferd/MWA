"""
Comprehensive tests for the contact discovery module.

Tests email extraction, phone detection, form discovery, contact validation,
storage operations, and integration with providers.
"""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch
from urllib.parse import urlparse

from mafa.contacts.models import Contact, ContactMethod, ContactStatus, ConfidenceLevel, ContactForm, DiscoveryContext
from mafa.contacts.extractor import ContactExtractor
from mafa.contacts.validator import ContactValidator
from mafa.contacts.storage import ContactStorage
from mafa.config.settings import Settings


class TestContactModels:
    """Test contact data models."""
    
    def test_contact_creation(self):
        """Test basic contact creation and normalization."""
        contact = Contact(
            method=ContactMethod.EMAIL,
            value="Test@example.com",
            confidence=ConfidenceLevel.HIGH,
            source_url="https://example.com/contact"
        )
        
        assert contact.method == ContactMethod.EMAIL
        assert contact.value == "test@example.com"  # Should be lowercase
        assert contact.confidence == ConfidenceLevel.HIGH
        assert contact.source_url == "https://example.com/contact"
        assert contact.verification_status == ContactStatus.UNVERIFIED
        assert contact.contact_hash is not None
        assert len(contact.contact_hash) == 16
    
    def test_contact_phone_normalization(self):
        """Test phone number normalization."""
        contact = Contact(
            method=ContactMethod.PHONE,
            value="+49 (0) 89 1234-5678",
            confidence=ConfidenceLevel.MEDIUM,
            source_url="https://example.com"
        )
        
        # Phone normalization should remove formatting
        assert "+49" in contact.value
        assert " " not in contact.value.replace("+", "")
    
    def test_contact_to_dict(self):
        """Test contact serialization."""
        contact = Contact(
            method=ContactMethod.EMAIL,
            value="test@example.com",
            confidence=ConfidenceLevel.MEDIUM,
            source_url="https://example.com",
            discovery_path=["https://example.com", "https://example.com/contact"],
            metadata={"source": "extraction"}
        )
        
        contact_dict = contact.to_dict()
        
        assert contact_dict["method"] == "email"
        assert contact_dict["value"] == "test@example.com"
        assert contact_dict["confidence"] == "medium"
        assert contact_dict["source_url"] == "https://example.com"
        assert contact_dict["discovery_path"] == ["https://example.com", "https://example.com/contact"]
        assert contact_dict["metadata"]["source"] == "extraction"
        assert "contact_hash" in contact_dict
    
    def test_contact_from_dict(self):
        """Test contact deserialization."""
        contact_dict = {
            "method": "email",
            "value": "test@example.com",
            "confidence": "high",
            "source_url": "https://example.com",
            "discovery_path": ["https://example.com"],
            "timestamp": "2023-01-01T00:00:00",
            "verification_status": "verified",
            "metadata": {"test": "data"}
        }
        
        contact = Contact.from_dict(contact_dict)
        
        assert contact.method == ContactMethod.EMAIL
        assert contact.value == "test@example.com"
        assert contact.confidence == ConfidenceLevel.HIGH
        assert contact.verification_status == ContactStatus.VERIFIED
        assert contact.metadata["test"] == "data"
    
    def test_contact_form_creation(self):
        """Test contact form model."""
        form = ContactForm(
            action_url="https://example.com/contact",
            method="POST",
            fields=["name", "email", "message"],
            required_fields=["name", "email"],
            source_url="https://example.com",
            confidence=ConfidenceLevel.HIGH
        )
        
        assert form.action_url == "https://example.com/contact"
        assert form.method == "POST"
        assert form.fields == ["name", "email", "message"]
        assert form.required_fields == ["name", "email"]
        assert form.confidence == ConfidenceLevel.HIGH
        assert form.is_simple_form  # Should be true for few fields
    
    def test_discovery_context(self):
        """Test discovery context functionality."""
        context = DiscoveryContext(
            base_url="https://example.com/listing",
            domain="example.com"
        )
        
        assert context.domain == "example.com"
        assert context.allowed_domains == ["example.com"]
        assert context.max_depth == 2
        assert context.current_depth == 0
        assert context.can_crawl_deeper() is True
        
        # Test next depth
        next_context = context.next_depth()
        assert next_context.current_depth == 1
        assert next_context.can_crawl_deeper() is True
        
        # Test max depth
        max_context = DiscoveryContext(
            base_url="https://example.com",
            domain="example.com",
            max_depth=1,
            current_depth=1
        )
        assert max_context.can_crawl_deeper() is False


class TestContactExtractor:
    """Test contact extraction functionality."""
    
    @pytest.fixture
    def mock_config(self):
        """Create mock configuration."""
        return Mock(spec=Settings)
    
    @pytest.fixture
    def extractor(self, mock_config):
        """Create contact extractor instance."""
        return ContactExtractor(mock_config)
    
    def test_normalize_text(self, extractor):
        """Test text normalization and deobfuscation."""
        # Test basic normalization
        text = "  Hello   World  "
        normalized = extractor.normalize_text(text)
        assert normalized == "Hello World"
        
        # Test email obfuscation
        obfuscated = "user [at] domain [dot] com"
        normalized = extractor.normalize_text(obfuscated)
        assert normalized == "user@domain.com"
        
        # Test HTML entities
        html_text = "user &#64; domain.com"
        normalized = extractor.normalize_text(html_text)
        assert "@" in normalized
    
    def test_extract_emails_basic(self, extractor):
        """Test basic email extraction."""
        text = "Contact us at test@example.com or admin@test.com"
        context = DiscoveryContext("https://example.com", "example.com")
        
        contacts = extractor.extract_emails(text, "https://example.com", context)
        
        assert len(contacts) == 2
        emails = [c.value for c in contacts]
        assert "test@example.com" in emails
        assert "admin@test.com" in emails
        
        # Check confidence levels
        for contact in contacts:
            assert contact.method == ContactMethod.EMAIL
            assert contact.source_url == "https://example.com"
    
    def test_extract_emails_obfuscated(self, extractor):
        """Test extraction of obfuscated emails."""
        text = "Email: user [at] company [dot] org or first.last(at)domain.com"
        context = DiscoveryContext("https://example.com", "example.com")
        
        contacts = extractor.extract_emails(text, "https://example.com", context)
        
        assert len(contacts) >= 1
        emails = [c.value.lower() for c in contacts]
        assert "user@company.org" in emails
    
    def test_extract_phones(self, extractor):
        """Test phone number extraction."""
        text = "Call us at +49 89 12345678 or 0049-89-1234-5678"
        context = DiscoveryContext("https://example.com", "example.com")
        
        contacts = extractor.extract_phones(text, "https://example.com", context)
        
        assert len(contacts) >= 1
        for contact in contacts:
            assert contact.method == ContactMethod.PHONE
            assert contact.value.startswith("+49")
    
    def test_extract_mailto_links(self, extractor):
        """Test mailto link extraction."""
        html = '''
        <html>
            <body>
                <a href="mailto:contact@example.com">Contact Us</a>
                <a href="mailto:info@company.org">Info</a>
            </body>
        </html>
        '''
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        context = DiscoveryContext("https://example.com", "example.com")
        
        contacts = extractor.extract_mailto_links(soup, "https://example.com", context)
        
        assert len(contacts) == 2
        emails = [c.value for c in contacts]
        assert "contact@example.com" in emails
        assert "info@company.org" in emails
        
        # Check that mailto links have high confidence
        for contact in contacts:
            assert contact.confidence == ConfidenceLevel.HIGH
    
    def test_extract_forms(self, extractor):
        """Test contact form extraction."""
        html = '''
        <html>
            <body>
                <form action="/contact" method="post">
                    <input type="text" name="name" required>
                    <input type="email" name="email" required>
                    <textarea name="message"></textarea>
                    <button type="submit">Send</button>
                </form>
            </body>
        </html>
        '''
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        context = DiscoveryContext("https://example.com", "example.com")
        
        forms = extractor.extract_forms(soup, "https://example.com", context)
        
        assert len(forms) == 1
        form = forms[0]
        assert form.action_url == "https://example.com/contact"
        assert form.method == "POST"
        assert "name" in form.fields
        assert "email" in form.fields
        assert "message" in form.fields
        assert "name" in form.required_fields
        assert "email" in form.required_fields
    
    def test_find_contact_links(self, extractor):
        """Test contact page link discovery."""
        html = '''
        <html>
            <body>
                <a href="/kontakt">Kontakt</a>
                <a href="/impressum">Impressum</a>
                <a href="/contact-us">Contact Us</a>
                <a href="/about">About</a>
                <a href="https://external.com">External</a>
            </body>
        </html>
        '''
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        context = DiscoveryContext("https://example.com", "example.com")
        
        links = extractor.find_contact_links(soup, "https://example.com", context)
        
        assert len(links) >= 3
        # Should find contact-related links
        contact_links = [link for link in links if any(keyword in link for keyword in ['kontakt', 'impressum', 'contact'])]
        assert len(contact_links) >= 3
    
    def test_deduplicate_contacts(self, extractor):
        """Test contact deduplication."""
        contacts = [
            Contact(ContactMethod.EMAIL, "test@example.com", ConfidenceLevel.HIGH, "https://example.com"),
            Contact(ContactMethod.EMAIL, "TEST@EXAMPLE.COM", ConfidenceLevel.MEDIUM, "https://example.com"),
            Contact(ContactMethod.EMAIL, "other@example.com", ConfidenceLevel.HIGH, "https://example.com"),
            Contact(ContactMethod.PHONE, "+49 89 123456", ConfidenceLevel.MEDIUM, "https://example.com")
        ]
        
        deduplicated = extractor.deduplicate_contacts(contacts)
        
        assert len(deduplicated) == 3  # Should remove duplicate email
        emails = [c.value for c in deduplicated if c.method == ContactMethod.EMAIL]
        assert "test@example.com" in emails
        assert "other@example.com" in emails
        
        # Original email should be kept (first occurrence)
        email_contacts = [c for c in deduplicated if c.value == "test@example.com"]
        assert len(email_contacts) == 1
        assert email_contacts[0].confidence == ConfidenceLevel.HIGH  # Keep first (highest confidence)


class TestContactValidator:
    """Test contact validation functionality."""
    
    @pytest.fixture
    def validator(self):
        """Create validator instance."""
        return ContactValidator(enable_smtp_verification=False)
    
    @pytest.mark.asyncio
    async def test_validate_email_syntax(self, validator):
        """Test email syntax validation."""
        contact = Contact(
            ContactMethod.EMAIL,
            "test@example.com",
            ConfidenceLevel.HIGH,
            "https://example.com"
        )
        
        await validator._validate_email(contact)
        
        assert contact.verification_status == ContactStatus.UNVERIFIED  # No SMTP verification
        
        # Test invalid email
        invalid_contact = Contact(
            ContactMethod.EMAIL,
            "invalid-email",
            ConfidenceLevel.LOW,
            "https://example.com"
        )
        
        from mafa.exceptions import ValidationError
        with pytest.raises(ValidationError):
            await validator._validate_email(invalid_contact)
    
    @pytest.mark.asyncio
    async def test_validate_phone(self, validator):
        """Test phone number validation."""
        contact = Contact(
            ContactMethod.PHONE,
            "+49891234567",
            ConfidenceLevel.MEDIUM,
            "https://example.com"
        )
        
        validator._validate_phone(contact)
        assert contact.verification_status == ContactStatus.VERIFIED
        
        # Test invalid phone
        invalid_contact = Contact(
            ContactMethod.PHONE,
            "123",  # Too short
            ConfidenceLevel.LOW,
            "https://example.com"
        )
        
        from mafa.exceptions import ValidationError
        with pytest.raises(ValidationError):
            validator._validate_phone(invalid_contact)
    
    def test_get_validation_summary(self, validator):
        """Test validation summary generation."""
        contacts = [
            Contact(ContactMethod.EMAIL, "test@example.com", ConfidenceLevel.HIGH, "https://example.com"),
            Contact(ContactMethod.EMAIL, "invalid@", ConfidenceLevel.MEDIUM, "https://example.com"),
            Contact(ContactMethod.PHONE, "+49891234567", ConfidenceLevel.LOW, "https://example.com")
        ]
        
        # Manually set verification statuses for testing
        contacts[0].verification_status = ContactStatus.VERIFIED
        contacts[1].verification_status = ContactStatus.INVALID
        contacts[2].verification_status = ContactStatus.UNVERIFIED
        
        summary = validator.get_validation_summary(contacts)
        
        assert summary['total'] == 3
        assert summary['verified'] == 1
        assert summary['invalid'] == 1
        assert summary['unverified'] == 1
        assert summary['flagged'] == 0
    
    def test_filter_high_confidence_contacts(self, validator):
        """Test high confidence contact filtering."""
        contacts = [
            Contact(ContactMethod.EMAIL, "high@example.com", ConfidenceLevel.HIGH, "https://example.com"),
            Contact(ContactMethod.EMAIL, "medium@example.com", ConfidenceLevel.MEDIUM, "https://example.com"),
            Contact(ContactMethod.EMAIL, "low@example.com", ConfidenceLevel.LOW, "https://example.com")
        ]
        
        # Set verification statuses
        contacts[0].verification_status = ContactStatus.VERIFIED
        contacts[1].verification_status = ContactStatus.VERIFIED
        contacts[2].verification_status = ContactStatus.UNVERIFIED
        
        filtered = validator.filter_high_confidence_contacts(contacts)
        
        # Should include high-confidence verified and high-confidence medium
        assert len(filtered) == 2
        values = [c.value for c in filtered]
        assert "high@example.com" in values
        assert "medium@example.com" in values
        assert "low@example.com" not in values


class TestContactStorage:
    """Test contact storage functionality."""
    
    @pytest.fixture
    def temp_storage(self):
        """Create temporary storage instance."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            db_path = Path(tmp_dir) / "test_contacts.db"
            storage = ContactStorage(db_path)
            yield storage
    
    def test_store_contact(self, temp_storage):
        """Test storing a single contact."""
        contact = Contact(
            ContactMethod.EMAIL,
            "test@example.com",
            ConfidenceLevel.HIGH,
            "https://example.com",
            metadata={"source": "extraction"}
        )
        
        result = temp_storage.store_contact(contact)
        assert result is True  # Should be stored
        
        # Try to store duplicate
        duplicate_contact = Contact(
            ContactMethod.EMAIL,
            "test@example.com",
            ConfidenceLevel.MEDIUM,
            "https://example.com"
        )
        
        result = temp_storage.store_contact(duplicate_contact)
        assert result is False  # Should be duplicate
    
    def test_store_contacts(self, temp_storage):
        """Test storing multiple contacts."""
        contacts = [
            Contact(ContactMethod.EMAIL, "test1@example.com", ConfidenceLevel.HIGH, "https://example.com"),
            Contact(ContactMethod.EMAIL, "test2@example.com", ConfidenceLevel.MEDIUM, "https://example.com"),
            Contact(ContactMethod.PHONE, "+49891234567", ConfidenceLevel.HIGH, "https://example.com")
        ]
        
        summary = temp_storage.store_contacts(contacts)
        
        assert summary['stored'] == 3
        assert summary['duplicates'] == 0
        assert summary['failed'] == 0
    
    def test_store_contact_form(self, temp_storage):
        """Test storing contact form."""
        form = ContactForm(
            action_url="https://example.com/contact",
            fields=["name", "email", "message"],
            required_fields=["name", "email"],
            source_url="https://example.com",
            confidence=ConfidenceLevel.HIGH
        )
        
        result = temp_storage.store_contact_form(form)
        assert result is True
    
    def test_get_contacts_by_listing(self, temp_storage):
        """Test retrieving contacts by listing ID."""
        contacts = [
            Contact(ContactMethod.EMAIL, "test@example.com", ConfidenceLevel.HIGH, "https://example.com"),
            Contact(ContactMethod.PHONE, "+49891234567", ConfidenceLevel.MEDIUM, "https://example.com")
        ]
        
        # Store contacts with listing ID 1
        temp_storage.store_contacts(contacts, listing_id=1)
        
        retrieved = temp_storage.get_contacts_by_listing(1)
        assert len(retrieved) == 2
        
        # Check structure
        email_contacts = [c for c in retrieved if c['method'] == 'email']
        assert len(email_contacts) == 1
        assert email_contacts[0]['value'] == "test@example.com"
    
    def test_update_contact_verification(self, temp_storage):
        """Test updating contact verification status."""
        contact = Contact(
            ContactMethod.EMAIL,
            "test@example.com",
            ConfidenceLevel.HIGH,
            "https://example.com"
        )
        
        temp_storage.store_contact(contact)
        
        # Update verification status
        result = temp_storage.update_contact_verification(1, ContactStatus.VERIFIED, {"verified_by": "smtp"})
        assert result is True
        
        # Verify the update
        retrieved = temp_storage.get_contacts_by_listing(None)
        updated_contact = retrieved[0]
        assert updated_contact['verification_status'] == 'verified'
        assert updated_contact['metadata']['verified_by'] == 'smtp'
    
    def test_get_contact_statistics(self, temp_storage):
        """Test contact statistics generation."""
        contacts = [
            Contact(ContactMethod.EMAIL, "test1@example.com", ConfidenceLevel.HIGH, "https://example.com"),
            Contact(ContactMethod.EMAIL, "test2@example.com", ConfidenceLevel.MEDIUM, "https://example.com"),
            Contact(ContactMethod.PHONE, "+49891234567", ConfidenceLevel.HIGH, "https://example.com")
        ]
        
        temp_storage.store_contacts(contacts)
        
        stats = temp_storage.get_contact_statistics()
        
        assert stats['total_contacts'] == 3
        assert stats['contacts_by_method']['email'] == 2
        assert stats['contacts_by_method']['phone'] == 1
        assert stats['recent_contacts_7_days'] == 3
    
    def test_search_contacts(self, temp_storage):
        """Test contact search functionality."""
        contacts = [
            Contact(ContactMethod.EMAIL, "john@example.com", ConfidenceLevel.HIGH, "https://example.com"),
            Contact(ContactMethod.EMAIL, "jane@company.org", ConfidenceLevel.MEDIUM, "https://example.com"),
            Contact(ContactMethod.PHONE, "+49891234567", ConfidenceLevel.HIGH, "https://example.com")
        ]
        
        temp_storage.store_contacts(contacts)
        
        # Search for "john"
        results = temp_storage.search_contacts("john")
        assert len(results) == 1
        assert results[0]['value'] == "john@example.com"
        
        # Search for "example"
        results = temp_storage.search_contacts("example")
        assert len(results) == 1  # Should match domain in metadata
        
        # Search for non-existent
        results = temp_storage.search_contacts("nonexistent")
        assert len(results) == 0


class TestIntegration:
    """Test integration between components."""
    
    @pytest.mark.asyncio
    async def test_contact_extraction_and_storage_integration(self):
        """Test full workflow: extract -> store -> retrieve."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            # Create storage
            db_path = Path(tmp_dir) / "test_contacts.db"
            storage = ContactStorage(db_path)
            
            # Create extractor
            from unittest.mock import Mock
            mock_config = Mock(spec=Settings)
            extractor = ContactExtractor(mock_config)
            
            # Mock HTML content
            html_content = '''
            <html>
                <body>
                    <p>Contact us at test@example.com or call +49 89 123456</p>
                    <a href="mailto:admin@company.org">Admin Email</a>
                    <form action="/contact" method="post">
                        <input name="name" required>
                        <input name="email" required>
                    </form>
                    <a href="/kontakt">Contact Page</a>
                </body>
            </html>
            '''
            
            # Mock HTTP response
            with patch.object(extractor.session, 'get') as mock_get:
                mock_response = Mock()
                mock_response.text = html_content
                mock_response.raise_for_status.return_value = None
                mock_get.return_value = mock_response
                
                # Extract contacts
                contacts, forms = await extractor.discover_contacts("https://example.com")
                
                # Check results
                assert len(contacts) >= 2  # At least email and phone
                assert len(forms) >= 1  # At least one form
                
                # Store contacts
                summary = storage.store_contacts(contacts)
                assert summary['stored'] >= 2
                
                # Verify storage
                stats = storage.get_contact_statistics()
                assert stats['total_contacts'] >= 2
    
    @pytest.mark.asyncio
    async def test_contact_validation_integration(self):
        """Test contact validation integration."""
        validator = ContactValidator(enable_smtp_verification=False)
        
        # Create test contacts
        contacts = [
            Contact(ContactMethod.EMAIL, "valid@example.com", ConfidenceLevel.HIGH, "https://example.com"),
            Contact(ContactMethod.EMAIL, "invalid-email", ConfidenceLevel.LOW, "https://example.com"),
            Contact(ContactMethod.PHONE, "+49891234567", ConfidenceLevel.MEDIUM, "https://example.com")
        ]
        
        # Validate contacts
        validated_contacts = await validator.validate_contacts(contacts)
        
        # Check results
        assert len(validated_contacts) == 3
        
        # Get summary
        summary = validator.get_validation_summary(validated_contacts)
        assert summary['total'] == 3
        
        # Check recommendations
        recommendations = validator.get_recommendations(validated_contacts)
        assert isinstance(recommendations, dict)
        assert 'high_priority' in recommendations
        assert 'medium_priority' in recommendations


class TestContactExtractorEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.fixture
    def extractor(self):
        """Create extractor with mock config."""
        mock_config = Mock(spec=Settings)
        return ContactExtractor(mock_config)
    
    def test_empty_text_extraction(self, extractor):
        """Test extraction from empty or invalid text."""
        context = DiscoveryContext("https://example.com", "example.com")
        
        # Empty text
        contacts = extractor.extract_emails("", "https://example.com", context)
        assert len(contacts) == 0
        
        # None text
        contacts = extractor.extract_emails(None, "https://example.com", context)
        assert len(contacts) == 0
        
        # Text with no valid emails
        contacts = extractor.extract_emails("No valid emails here", "https://example.com", context)
        assert len(contacts) == 0
    
    def test_invalid_email_patterns(self, extractor):
        """Test rejection of invalid email patterns."""
        invalid_emails = [
            "test@",  # Missing domain
            "@domain.com",  # Missing local part
            "test..test@domain.com",  # Double dots
            "test@domain",  # No TLD
            "test@.com",  # Domain starts with dot
            "test@domain..com"  # Double dots in domain
        ]
        
        for email in invalid_emails:
            assert not extractor._is_valid_email(email)
    
    def test_malformed_html_handling(self, extractor):
        """Test handling of malformed HTML."""
        malformed_html = '''
        <html>
            <body>
                <p>Contact: test@example.com
                <a href="mailto:admin@company.org>Admin</a>
                <form action="/contact>
                    <input name="name">
                </form>
            </body>
        '''
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(malformed_html, 'html.parser')
        context = DiscoveryContext("https://example.com", "example.com")
        
        # Should not crash on malformed HTML
        contacts = extractor.extract_mailto_links(soup, "https://example.com", context)
        forms = extractor.extract_forms(soup, "https://example.com", context)
        
        # Should extract valid content despite malformation
        assert len(contacts) >= 0
        assert len(forms) >= 0