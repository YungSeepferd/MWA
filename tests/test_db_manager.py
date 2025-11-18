"""Unit tests for database manager."""

import tempfile
from pathlib import Path
from mafa.db.manager import ListingRepository


def test_listing_repository():
    """Test basic CRUD operations on the listing repository."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        db_path = Path(tmp_dir) / "test.db"
        repo = ListingRepository(db_path=db_path)
        
        # Test empty repository
        listing = {
            "title": "Test Apartment",
            "price": "1200 €",
            "source": "Test",
            "timestamp": "2023-01-01T00:00:00"
        }
        
        # Test adding a listing
        assert repo.add_listing(listing) is True
        assert repo.listing_exists(listing) is True
        
        # Test duplicate detection
        assert repo.add_listing(listing) is False
        
        # Test bulk add
        listing2 = {
            "title": "Another Apartment",
            "price": "1500 €",
            "source": "Test",
            "timestamp": "2023-01-01T00:00:00"
        }
        listing3 = {
            "title": "Duplicate Apartment",
            "price": "1200 €",
            "source": "Test",
            "timestamp": "2023-01-01T00:00:00"
        }
        
        new_count = repo.bulk_add([listing2, listing3, listing])  # listing is duplicate
        assert new_count == 1  # Only listing2 should be added
        assert repo.listing_exists(listing2) is True
        assert repo.listing_exists(listing3) is False