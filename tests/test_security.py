"""
Security validation tests for MAFA application.

Tests input sanitization, validation, and security features.
"""

import pytest
import tempfile
from pathlib import Path

from mafa.security import SecurityValidator, sanitize_user_input, validate_scraping_target
from mafa.exceptions import MAFAError


class TestSecurityValidator:
    """Test SecurityValidator functionality."""
    
    def test_sanitize_text_basic(self):
        """Test basic text sanitization."""
        # Test normal text
        clean_text = SecurityValidator.sanitize_text("Hello World")
        assert clean_text == "Hello World"
        
        # Test text with dangerous patterns
        dangerous_text = "<script>alert('xss')</script>Hello World"
        sanitized = SecurityValidator.sanitize_text(dangerous_text)
        assert "<script>" not in sanitized
        assert "Hello World" in sanitized
        
        # Test HTML escaping
        html_text = "<div>Test & \"quoted\"</div>"
        sanitized = SecurityValidator.sanitize_text(html_text)
        assert "<div>" in sanitized  # HTML should be escaped
        assert "&" in sanitized  # Ampersand should be escaped
        assert '"' in sanitized  # Quotes should be escaped
    
    def test_sanitize_text_with_max_length(self):
        """Test text sanitization with length limits."""
        long_text = "a" * 500
        sanitized = SecurityValidator.sanitize_text(long_text, max_length=100)
        assert len(sanitized) <= 100
        
        # Should truncate clean text
        clean_text = "Clean text" * 50
        sanitized = SecurityValidator.sanitize_text(clean_text, max_length=100)
        assert len(sanitized) <= 100
        assert "Clean text" in sanitized
    
    def test_sanitize_listing(self):
        """Test listing sanitization."""
        malicious_listing = {
            "title": "<script>alert('title')</script>Clean Title",
            "price": "<img src=x onerror=alert('price')>€1000",
            "source": "javascript:alert('source')",
            "timestamp": "2023-01-01T00:00:00"
        }
        
        sanitized = SecurityValidator.sanitize_listing(malicious_listing)
        
        # Dangerous patterns should be removed
        assert "<script>" not in sanitized["title"]
        assert "<img" not in sanitized["price"]
        assert "javascript:" not in sanitized["source"]
        
        # Clean content should be preserved
        assert "Clean Title" in sanitized["title"]
        assert "€1000" in sanitized["price"]
        assert sanitized["timestamp"] == "2023-01-01T00:00:00"
    
    def test_validate_url_safe(self):
        """Test URL validation for safe URLs."""
        safe_urls = [
            "https://www.example.com",
            "https://sub.domain.com/path?query=value"
        ]
        
        for url in safe_urls:
            assert SecurityValidator.validate_url(url) is True
            
        # localhost should be rejected (no domain)
        assert SecurityValidator.validate_url("http://localhost:8080") is False
    
    def test_validate_url_dangerous(self):
        """Test URL validation rejects dangerous URLs."""
        dangerous_urls = [
            "javascript:alert('xss')",
            "data:text/html,<script>alert('xss')</script>",
            "vbscript:msgbox('xss')",
            "file:///etc/passwd",
            "ftp://malicious.com",
            "not-a-url"
        ]
        
        for url in dangerous_urls:
            assert SecurityValidator.validate_url(url) is False
    
    def test_validate_file_path_safe(self):
        """Test file path validation for safe paths."""
        # Test safe paths within base_dir
        safe_paths = [
            Path("/home/user/data/listings.db"),
            Path("./data/output.json")
        ]
        
        base_dir = Path("/home/user")
        for path in safe_paths:
            assert SecurityValidator.validate_file_path(path, base_dir) is True
            
        # Path outside base_dir should be rejected
        assert SecurityValidator.validate_file_path(Path("/var/log/mafa.log"), base_dir) is False
    
    def test_validate_file_path_dangerous(self):
        """Test file path validation rejects dangerous paths."""
        dangerous_paths = [
            Path("../../../etc/passwd"),
            Path("/home/user/../etc/passwd"),
            Path("/tmp/~/malicious"),
            Path("/home/user/$DATA")
        ]
        
        base_dir = Path("/home/user")
        for path in dangerous_paths:
            assert SecurityValidator.validate_file_path(path, base_dir) is False
    
    def test_validate_config_data(self):
        """Test configuration data sanitization."""
        malicious_config = {
            "personal_profile": {
                "my_full_name": "<script>alert('name')</script>Max",
                "my_profession": "Engineer<script>alert('prof')</script>",
                "my_employer": "Company & <script>alert('employer')</script>",
                "net_household_income_monthly": -500,  # Invalid negative
                "total_occupants": 0,  # Invalid zero
                "intro_paragraph": "<div>Valid paragraph</div>" + "x" * 2000  # Long content
            },
            "search_criteria": {
                "max_price": -100,  # Invalid
                "min_rooms": "invalid",  # Invalid type
                "zip_codes": ["<script>alert('zip')</script>12345", "80799", "80803"]
            },
            "notification": {
                "provider": "discord",
                "discord_webhook_url": "javascript:alert('webhook')",  # Invalid URL
                "telegram_bot_token": "invalid_token_format",
                "telegram_chat_id": "not_a_number"
            }
        }
        
        sanitized = SecurityValidator.validate_config_data(malicious_config)
        
        # Check that dangerous content is removed
        assert "<script>" not in str(sanitized)
        
        # Check that valid content is preserved
        assert "Max" in sanitized["personal_profile"]["my_full_name"]
        assert "Engineer" in sanitized["personal_profile"]["my_profession"]
        
        # Check that invalid values are corrected
        assert sanitized["personal_profile"]["net_household_income_monthly"] > 0
        assert sanitized["personal_profile"]["total_occupants"] > 0
        
        # Check that zip codes are validated
        valid_zips = sanitized["search_criteria"]["zip_codes"]
        assert "80799" in valid_zips
        assert "80803" in valid_zips
        # Malicious zip should be removed
        malicious_zips = [z for z in valid_zips if "<script>" in z]
        assert len(malicious_zips) == 0
        
        # Check notification validation - invalid URL should be rejected
        assert "discord_webhook_url" not in sanitized["notification"]  # Invalid URL should be removed
    
    def test_generate_secure_hash(self):
        """Test secure hash generation."""
        hash1 = SecurityValidator.generate_secure_hash("test data")
        hash2 = SecurityValidator.generate_secure_hash("test data")
        hash3 = SecurityValidator.generate_secure_hash("different data")
        
        # Same input should produce same hash
        assert hash1 == hash2
        
        # Different input should produce different hash
        assert hash1 != hash3
        
        # Hash should be 64 characters (SHA-256 hex)
        assert len(hash1) == 64
        assert all(c in "0123456789abcdef" for c in hash1)
    
    def test_check_input_size(self):
        """Test input size validation."""
        # Small input should pass
        small_data = "short text"
        assert SecurityValidator.check_input_size(small_data) is True
        
        # Large text should fail
        large_text = "x" * (2 * 1024 * 1024)  # 2MB
        assert SecurityValidator.check_input_size(large_text) is False
        
        # Large dict should fail
        large_dict = {"data": "x" * (2 * 1024 * 1024)}
        assert SecurityValidator.check_input_size(large_dict) is False
        
        # Config-sized dict should pass
        config_dict = {
            "personal_profile": {"name": "Test", "profession": "Engineer"},
            "search_criteria": {"max_price": 2000, "zip_codes": ["12345"]},
            "notification": {"provider": "discord"}
        }
        assert SecurityValidator.check_input_size(config_dict) is True


class TestConvenienceFunctions:
    """Test convenience functions for sanitization."""
    
    def test_sanitize_user_input(self):
        """Test convenience sanitize function."""
        dangerous_input = "<script>alert('xss')</script>Clean text"
        sanitized = sanitize_user_input(dangerous_input)
        
        assert "<script>" not in sanitized
        assert "Clean text" in sanitized
    
    def test_validate_scraping_target(self):
        """Test convenience URL validation function."""
        assert validate_scraping_target("https://example.com") is True
        assert validate_scraping_target("javascript:alert('xss')") is False


class TestSecurityEdgeCases:
    """Test edge cases and security boundary conditions."""
    
    def test_empty_input_handling(self):
        """Test handling of empty or None input."""
        assert SecurityValidator.sanitize_text("") == ""
        assert SecurityValidator.sanitize_text(None) == ""
        assert SecurityValidator.sanitize_listing({}) == {}
    
    def test_unicode_handling(self):
        """Test handling of Unicode and special characters."""
        unicode_text = "Hëllö Wörld 🌍 你好"
        sanitized = SecurityValidator.sanitize_text(unicode_text)
        assert sanitized == unicode_text  # Unicode should be preserved
        
        # Test with dangerous Unicode content
        dangerous_unicode = "Safe <script>alert('xss')</script> Hëllö"
        sanitized = SecurityValidator.sanitize_text(dangerous_unicode)
        assert "Hëllö" in sanitized
        assert "<script>" not in sanitized
    
    def test_null_byte_handling(self):
        """Test handling of null bytes and control characters."""
        dangerous_text = "Safe\x00text\x01with\x02control\x03chars"
        sanitized = SecurityValidator.sanitize_text(dangerous_text)
        
        # Null bytes and control characters should be removed
        assert "\x00" not in sanitized
        assert "\x01" not in sanitized
        assert "Safe" in sanitized
        assert "text" in sanitized
    
    def test_case_insensitive_pattern_matching(self):
        """Test that dangerous patterns are matched case-insensitively."""
        dangerous_variations = [
            "<SCRIPT>alert('xss')</SCRIPT>",
            "<Script>alert('xss')</Script>",
            "<ScRiPt>alert('xss')</ScRiPt>"
        ]
        
        for dangerous in dangerous_variations:
            sanitized = SecurityValidator.sanitize_text(dangerous)
            assert "<script>" not in sanitized.lower()
    
    def test_concatenated_attack_patterns(self):
        """Test handling of concatenated attack patterns."""
        complex_attack = (
            "<script>alert('1')</script>"
            "Normal text"
            "<img src=x onerror=alert('2')>"
            "More text"
            "javascript:alert('3')"
            "End text"
        )
        
        sanitized = SecurityValidator.sanitize_text(complex_attack)
        
        # All dangerous patterns should be removed
        assert "<script>" not in sanitized.lower()
        assert "<img" not in sanitized.lower()
        assert "javascript:" not in sanitized.lower()
        
        # Clean text should be preserved
        assert "Normal text" in sanitized
        assert "More text" in sanitized
        assert "End text" in sanitized
    
    def test_configuration_poisoning_prevention(self):
        """Test prevention of configuration poisoning attacks."""
        # Test nested malicious content
        malicious_nested = {
            "personal_profile": {
                "my_full_name": "Name",
                "intro_paragraph": {
                    "__class__": "<script>alert('pwned')</script>"
                }
            }
        }
        
        sanitized = SecurityValidator.validate_config_data(malicious_nested)
        
        # Should handle nested malicious content
        assert isinstance(sanitized["personal_profile"]["intro_paragraph"], str)
        assert "<script>" not in str(sanitized)
    
    def test_rate_limiting_awareness(self):
        """Test that validation functions are efficient for rate limiting."""
        import time
        
        # Test that sanitization is fast enough for rate limiting
        large_input = "x" * 10000
        
        start_time = time.time()
        for _ in range(100):
            SecurityValidator.sanitize_text(large_input)
        end_time = time.time()
        
        # Should process 100 sanitizations in reasonable time (< 1 second)
        assert (end_time - start_time) < 1.0