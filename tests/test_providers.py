"""Unit tests for provider scrapers."""

from unittest.mock import Mock, patch

from mafa.providers.immoscout import ImmoScoutProvider
from mafa.providers.wg_gesucht import WGGesuchtProvider


def test_immoscout_provider_scrape():
    """Test ImmoScoutProvider scraping with mocked Selenium driver."""
    provider = ImmoScoutProvider()
    
    # Mock the Selenium driver and its methods
    with patch('mafa.providers.immoscout.SeleniumDriver') as mock_driver:
        mock_instance = Mock()
        mock_driver.return_value.__enter__.return_value = mock_instance
        mock_instance.get.return_value = None
        
        # Mock finding elements
        mock_item = Mock()
        mock_item.find_element.return_value.text = "Test Listing"
        mock_item.find_element.side_effect = [
            Mock(text="Test Listing"),  # h5 element for title
            Mock(text="1000 €")        # price element
        ]
        mock_instance.find_elements.return_value = [mock_item]
        
        # Test scraping
        results = provider.scrape()
        
        assert len(results) == 1
        assert results[0]["title"] == "Test Listing"
        assert results[0]["price"] == "1000 €"
        assert results[0]["source"] == "ImmobilienScout24"


def test_wg_gesucht_provider_scrape():
    """Test WGGesuchtProvider scraping with mocked Selenium driver."""
    provider = WGGesuchtProvider()
    
    # Mock the Selenium driver and its methods
    with patch('mafa.providers.wg_gesucht.SeleniumDriver') as mock_driver:
        mock_instance = Mock()
        mock_driver.return_value.__enter__.return_value = mock_instance
        mock_instance.get.return_value = None
        
        # Mock finding elements
        mock_item = Mock()
        mock_item.find_element.return_value.text = "WG Zimmer"
        mock_item.find_element.side_effect = [
            Mock(text="WG Zimmer"),    # h2 element for title
            Mock(text="500 €")         # price element
        ]
        mock_instance.find_elements.return_value = [mock_item]
        
        # Test scraping
        results = provider.scrape()
        
        assert len(results) == 1
        assert results[0]["title"] == "WG Zimmer"
        assert results[0]["price"] == "500 €"
        assert results[0]["source"] == "WG Gesucht"