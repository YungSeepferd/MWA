import pytest
from mwa_core.scraper import ProviderRegistry, Listing
from mwa_core.providers import ImmoScoutProvider, WGGesuchtProvider


def test_registry_singleton():
    r1 = ProviderRegistry()
    r2 = ProviderRegistry()
    assert r1 is r2


def test_registry_lists_providers():
    registry = ProviderRegistry()
    names = registry.list()
    assert "immoscout" in names
    assert "wg_gesucht" in names


def test_registry_instantiate():
    registry = ProviderRegistry()
    provider = registry.instantiate("immoscout")
    assert isinstance(provider, ImmoScoutProvider)


def test_immoscout_provider_returns_listings():
    provider = ImmoScoutProvider()
    listings = provider.fetch_listings({"headless": True})
    assert isinstance(listings, list)
    for listing in listings:
        assert isinstance(listing, Listing)
        assert listing.source == "ImmobilienScout24"


def test_wg_gesucht_provider_returns_listings():
    provider = WGGesuchtProvider()
    listings = provider.fetch_listings({"headless": True})
    assert isinstance(listings, list)
    for listing in listings:
        assert isinstance(listing, Listing)
        assert listing.source == "WG Gesucht"