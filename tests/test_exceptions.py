"""
Tests for custom exception classes.
"""

import pytest

from mafa.exceptions import (
    MAFAError,
    ConfigurationError,
    ScrapingError,
    DatabaseError,
    NotificationError,
    ProviderError,
    SchedulerError,
    TemplateError
)


class TestMAFAExceptions:
    """Test custom exception hierarchy."""
    
    def test_mafa_error_base_class(self):
        """Test base MAFAError class functionality."""
        error = MAFAError("Test error message")
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.details == {}
    
    def test_mafa_error_with_details(self):
        """Test MAFAError with additional details."""
        details = {"key": "value", "status_code": 500}
        error = MAFAError("Test error", details=details)
        assert error.details == details
        assert error.details["key"] == "value"
        assert error.details["status_code"] == 500
    
    def test_specialized_exceptions(self):
        """Test that all specialized exceptions inherit from MAFAError."""
        exceptions = [
            ConfigurationError("Config error"),
            ScrapingError("Scraping error"),
            DatabaseError("Database error"),
            NotificationError("Notification error"),
            SchedulerError("Scheduler error"),
            TemplateError("Template error"),
        ]
        
        for exc in exceptions:
            assert isinstance(exc, MAFAError)
            assert isinstance(exc, Exception)
    
    def test_provider_error_with_details(self):
        """Test ProviderError includes provider name in message."""
        provider_error = ProviderError(
            provider_name="ImmoScout",
            message="Failed to scrape",
            details={"retry_count": 3}
        )
        
        assert provider_error.provider_name == "ImmoScout"
        assert "[ImmoScout]" in str(provider_error)
        assert "Failed to scrape" in str(provider_error)
        assert provider_error.details["provider_name"] == "ImmoScout"
        assert provider_error.details["retry_count"] == 3
    
    def test_exception_inheritance_chain(self):
        """Test that all exceptions form proper inheritance hierarchy."""
        # All specialized exceptions should be instances of MAFAError
        assert isinstance(ConfigurationError("test"), MAFAError)
        assert isinstance(ScrapingError("test"), MAFAError)
        assert isinstance(DatabaseError("test"), MAFAError)
        assert isinstance(NotificationError("test"), MAFAError)
        assert isinstance(ProviderError("test", "msg"), MAFAError)
        assert isinstance(SchedulerError("test"), MAFAError)
        assert isinstance(TemplateError("test"), MAFAError)
        
        # All should also be instances of Exception
        assert isinstance(ConfigurationError("test"), Exception)
        assert isinstance(ScrapingError("test"), Exception)
        assert isinstance(DatabaseError("test"), Exception)
        assert isinstance(NotificationError("test"), Exception)
        assert isinstance(ProviderError("test", "msg"), Exception)
        assert isinstance(SchedulerError("test"), Exception)
        assert isinstance(TemplateError("test"), Exception)
    
    def test_exception_pickling(self):
        """Test that exceptions can be pickled for multiprocessing."""
        import pickle
        
        # Test basic exception pickling
        error = MAFAError("Test error", details={"key": "value"})
        pickled = pickle.dumps(error)
        unpickled = pickle.loads(pickled)
        
        assert str(unpickled) == str(error)
        assert unpickled.message == error.message
        assert unpickled.details == error.details
        
        # Test ProviderError pickling
        provider_error = ProviderError(
            provider_name="TestProvider",
            message="Test provider error",
            details={"retry_count": 2}
        )
        pickled_provider = pickle.dumps(provider_error)
        unpickled_provider = pickle.loads(pickled_provider)
        
        assert unpickled_provider.provider_name == "TestProvider"
        assert str(unpickled_provider) == str(provider_error)


class TestExceptionUsage:
    """Test how exceptions are used in practice."""
    
    def test_exception_chaining(self):
        """Test exception chaining with cause preservation."""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise ConfigurationError("Configuration failed", details={"cause": str(e)}) from e
        except ConfigurationError as wrapped:
            assert "Configuration failed" in str(wrapped)
            assert isinstance(wrapped.__cause__, ValueError)
            assert str(wrapped.__cause__) == "Original error"
    
    def test_exception_as_dict_key(self):
        """Test that exceptions can be used as dictionary keys (for error tracking)."""
        error_types = {
            ConfigurationError("config"): "config_issues",
            ScrapingError("scraping"): "scraping_issues",
            DatabaseError("database"): "db_issues"
        }
        
        assert len(error_types) == 3
        assert error_types[ConfigurationError("config")] == "config_issues"
    
    def test_exception_equality(self):
        """Test exception equality for error deduplication."""
        error1 = MAFAError("Same message")
        error2 = MAFAError("Same message")
        error3 = MAFAError("Different message")
        
        # Exceptions with same message and details should be considered equal
        assert error1.message == error2.message
        assert error1.details == error2.details
        
        # But exception instances themselves aren't equal
        assert error1 != error2
        assert error1 != error3