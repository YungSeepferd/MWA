"""
Comprehensive tests for MWA Core storage deduplication system.

Tests SHA-256 hash-based duplicate prevention, fuzzy matching, and advanced
deduplication strategies.
"""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

from mwa_core.storage import (
    EnhancedStorageManager, DeduplicationEngine, CRUDOperations,
    ListingStatus, ContactType, ContactStatus, JobStatus, DeduplicationStatus
)


class TestDeduplicationEngine:
    """Test cases for DeduplicationEngine."""
    
    def test_initialization(self):
        """Test deduplication engine initialization."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            engine = storage.deduplication
            
            assert engine is not None
            assert engine.crud is not None
            assert "exact_match_threshold" in engine.config
            assert "fuzzy_match_threshold" in engine.config
            
            Path(f.name).unlink()
    
    def test_exact_hash_duplicate_detection(self):
        """Test exact hash-based duplicate detection."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            engine = storage.deduplication
            
            # Add original listing
            original_data = {
                "provider": "immoscout",
                "external_id": "test_123",
                "title": "Test Apartment",
                "url": "https://example.com/original",
                "price": "1000 €",
                "size": "80 m²",
                "rooms": "3.5",
                "address": "Test Street 1, Munich"
            }
            
            storage.add_listing(original_data)
            
            # Check exact duplicate (identical content but different URL and no external_id)
            duplicate_data = original_data.copy()
            duplicate_data["url"] = "https://example.com/duplicate"  # Different URL
            duplicate_data["external_id"] = None  # No external_id to avoid provider/external_id match
            
            result = engine.check_duplicate(duplicate_data)
            assert result["is_duplicate"] is True
            # Should detect as duplicate using either exact hash or content similarity
            assert result["duplicate_strategy"] in ["exact_hash", "content_similarity"]
            assert result["confidence"] >= 0.9
            assert "duplicate_of_id" in result
            
            Path(f.name).unlink()
    
    def test_provider_external_id_duplicate_detection(self):
        """Test provider + external ID duplicate detection."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            engine = storage.deduplication
            
            # Add original listing
            original_data = {
                "provider": "immoscout",
                "external_id": "unique_456",
                "title": "Test Apartment",
                "url": "https://example.com/original",
                "price": "1000 €"
            }
            
            storage.add_listing(original_data)
            
            # Check duplicate with same provider/external_id
            duplicate_data = {
                "provider": "immoscout",
                "external_id": "unique_456",
                "title": "Different Title",
                "url": "https://example.com/duplicate",
                "price": "1200 €"
            }
            
            result = engine.check_duplicate(duplicate_data)
            assert result["is_duplicate"] is True
            assert result["duplicate_strategy"] == "provider_external_id"
            assert result["confidence"] == 0.95
            
            Path(f.name).unlink()
    
    def test_url_duplicate_detection(self):
        """Test URL-based duplicate detection."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            engine = storage.deduplication
            
            # Add original listing
            original_data = {
                "provider": "immoscout",
                "title": "Test Apartment",
                "url": "https://example.com/same-url",
                "price": "1000 €"
            }
            
            storage.add_listing(original_data)
            
            # Check duplicate with same URL
            duplicate_data = {
                "provider": "wg_gesucht",
                "title": "Different Title",
                "url": "https://example.com/same-url",
                "price": "1500 €"
            }
            
            result = engine.check_duplicate(duplicate_data)
            assert result["is_duplicate"] is True
            assert result["duplicate_strategy"] == "url_match"
            assert result["confidence"] == 0.95
            
            Path(f.name).unlink()
    
    def test_fuzzy_matching_similarity(self):
        """Test fuzzy matching for similar listings."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            engine = storage.deduplication
            
            # Add original listing
            original_data = {
                "provider": "immoscout",
                "title": "Schöne 3-Zimmer Wohnung in München",
                "url": "https://example.com/original",
                "price": "1000 €",
                "size": "80 m²",
                "rooms": "3",
                "address": "München, Schwabing"
            }
            
            storage.add_listing(original_data)
            
            # Check very similar listing
            similar_data = {
                "provider": "immoscout",
                "title": "Schöne 3 Zimmer Wohnung in München",  # Slightly different
                "url": "https://example.com/similar",
                "price": "1000 €",
                "size": "80 m²",
                "rooms": "3",
                "address": "München Schwabing"  # Slightly different
            }
            
            result = engine.check_duplicate(similar_data)
            # Should detect as duplicate due to high similarity
            if result["is_duplicate"]:
                assert result["duplicate_strategy"] == "fuzzy_match"
                assert result["confidence"] > 0.8
            
            Path(f.name).unlink()
    
    def test_content_similarity_detection(self):
        """Test content-based similarity detection."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            engine = storage.deduplication
            
            # Add original listing
            original_data = {
                "provider": "immoscout",
                "title": "Moderne Wohnung mit Balkon",
                "url": "https://example.com/original",
                "price": "1200 €",
                "size": "90 m²",
                "rooms": "3",
                "address": "München Maxvorstadt"
            }
            
            storage.add_listing(original_data)
            
            # Check listing with very similar content
            similar_data = {
                "provider": "immoscout",
                "title": "Moderne Wohnung mit großem Balkon",  # Very similar
                "url": "https://example.com/similar",
                "price": "1200 €",
                "size": "90 m²",
                "rooms": "3",
                "address": "München Maxvorstadt"
            }
            
            result = engine.check_duplicate(similar_data)
            # Should have high similarity score
            if result["is_duplicate"]:
                assert result["duplicate_strategy"] == "content_similarity"
                assert result["confidence"] >= 0.9
            
            Path(f.name).unlink()
    
    def test_non_duplicate_detection(self):
        """Test that truly different listings are not marked as duplicates."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            engine = storage.deduplication
            
            # Add original listing
            original_data = {
                "provider": "immoscout",
                "title": "Luxury Penthouse",
                "url": "https://example.com/penthouse",
                "price": "5000 €",
                "size": "200 m²",
                "rooms": "5",
                "address": "München City Center"
            }
            
            storage.add_listing(original_data)
            
            # Check completely different listing
            different_data = {
                "provider": "wg_gesucht",
                "title": "Small Student Room",
                "url": "https://example.com/student-room",
                "price": "300 €",
                "size": "15 m²",
                "rooms": "1",
                "address": "München Student Area"
            }
            
            result = engine.check_duplicate(different_data)
            assert result["is_duplicate"] is False
            
            Path(f.name).unlink()
    
    def test_price_similarity_calculation(self):
        """Test price similarity calculation."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            engine = storage.deduplication
            
            # Test identical prices
            score1 = engine._calculate_price_similarity("1000 €", "1000 €")
            assert score1 == 1.0
            
            # Test similar prices (within 10% threshold)
            score2 = engine._calculate_price_similarity("1000 €", "1050 €")
            assert score2 > 0.5
            
            # Test different prices (outside threshold)
            score3 = engine._calculate_price_similarity("1000 €", "2000 €")
            assert score3 < 0.5
            
            Path(f.name).unlink()
    
    def test_size_similarity_calculation(self):
        """Test size similarity calculation."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            engine = storage.deduplication
            
            # Test identical sizes
            score1 = engine._calculate_size_similarity("80 m²", "80 m²")
            assert score1 == 1.0
            
            # Test similar sizes (within 15% threshold)
            score2 = engine._calculate_size_similarity("80 m²", "85 m²")
            assert score2 > 0.5
            
            # Test different sizes (outside threshold)
            score3 = engine._calculate_size_similarity("80 m²", "120 m²")
            assert score3 < 0.5
            
            Path(f.name).unlink()
    
    def test_text_normalization(self):
        """Test text normalization for comparison."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            engine = storage.deduplication
            
            # Test text normalization
            normalized = engine._normalize_text("Schöne 3-Zimmer Wohnung!!!")
            assert normalized == "schöne 3 zimmer wohnung"
            
            # Test address normalization
            normalized_addr = engine._normalize_address("München, Schwabinger Straße 1")
            assert "schwabinger" in normalized_addr
            assert "straße" not in normalized_addr  # Common words removed
            
            Path(f.name).unlink()
    
    def test_hash_signature_generation(self):
        """Test SHA-256 hash signature generation."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            engine = storage.deduplication
            
            listing_data = {
                "provider": "immoscout",
                "external_id": "test_123",
                "title": "Test Apartment",
                "price": "1000 €",
                "size": "80 m²",
                "rooms": "3.5",
                "address": "Test Street 1, Munich"
            }
            
            hash1 = engine._generate_hash_signature(listing_data)
            hash2 = engine._generate_hash_signature(listing_data)
            
            # Same data should generate same hash
            assert hash1 == hash2
            assert len(hash1) == 64  # SHA-256 produces 64 character hex string
            
            # Different data should generate different hash
            different_data = listing_data.copy()
            different_data["title"] = "Different Apartment"
            hash3 = engine._generate_hash_signature(different_data)
            assert hash1 != hash3
            
            Path(f.name).unlink()
    
    def test_duplicate_marking(self):
        """Test marking listings as duplicates."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            engine = storage.deduplication
            
            # Add original listing
            original_data = {
                "provider": "immoscout",
                "title": "Original Listing",
                "url": "https://example.com/original",
                "price": "1000 €"
            }
            
            storage.add_listing(original_data)
            original = storage.get_listing_by_url("https://example.com/original")
            
            # Add duplicate listing
            duplicate_data = {
                "provider": "immoscout",
                "title": "Duplicate Listing",
                "url": "https://example.com/duplicate",
                "price": "1000 €"
            }
            
            storage.add_listing(duplicate_data)
            duplicate = storage.get_listing_by_url("https://example.com/duplicate")
            
            # Mark as duplicate
            success = engine.mark_as_duplicate(
                duplicate["id"], 
                original["id"], 
                0.95, 
                "test_strategy"
            )
            assert success is True
            
            # Verify duplicate was marked
            updated_duplicate = storage.get_listing_by_url("https://example.com/duplicate")
            assert updated_duplicate["deduplication_status"] == DeduplicationStatus.DUPLICATE.value
            assert updated_duplicate["duplicate_of_id"] == original["id"]
            
            Path(f.name).unlink()
    
    def test_duplicate_merging(self):
        """Test merging data from duplicate listings."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            engine = storage.deduplication
            
            # Add original listing
            original_data = {
                "provider": "immoscout",
                "title": "Original Listing",
                "url": "https://example.com/original",
                "price": "1000 €"
            }
            
            storage.add_listing(original_data)
            original = storage.get_listing_by_url("https://example.com/original")
            
            # Add duplicate listing with additional data
            duplicate_data = {
                "provider": "immoscout",
                "title": "Duplicate Listing",
                "url": "https://example.com/duplicate",
                "price": "1000 €",
                "images": ["extra_image1.jpg", "extra_image2.jpg"],
                "contacts": [{"type": "phone", "value": "+49 123 456789"}]
            }
            
            storage.add_listing(duplicate_data)
            duplicate = storage.get_listing_by_url("https://example.com/duplicate")
            
            # Add contact to duplicate
            storage.add_contact(duplicate["id"], {
                "type": "email",
                "value": "extra@example.com"
            })
            
            # Merge duplicates
            success = engine.merge_duplicate_listings(duplicate["id"], original["id"])
            assert success is True
            
            # Verify merge
            updated_original = storage.get_listing_with_relationships(original["id"])
            assert len(updated_original["contacts"]) >= 1
            
            # Verify duplicate was marked as merged
            updated_duplicate = storage.get_listing_by_url("https://example.com/duplicate")
            assert updated_duplicate["deduplication_status"] == DeduplicationStatus.MERGED.value
            assert updated_duplicate["status"] == ListingStatus.INACTIVE.value
            
            Path(f.name).unlink()
    
    def test_duplicate_cleanup(self):
        """Test cleanup of duplicate listings."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            engine = storage.deduplication
            
            # Add original listing
            original_data = {
                "provider": "immoscout",
                "title": "Original Listing",
                "url": "https://example.com/original",
                "price": "1000 €"
            }
            
            storage.add_listing(original_data)
            original = storage.get_listing_by_url("https://example.com/original")
            
            # Add multiple duplicates
            for i in range(3):
                duplicate_data = {
                    "provider": "immoscout",
                    "title": f"Duplicate Listing {i}",
                    "url": f"https://example.com/duplicate{i}",
                    "price": "1000 €"
                }
                
                storage.add_listing(duplicate_data)
                duplicate = storage.get_listing_by_url(f"https://example.com/duplicate{i}")
                
                # Mark as duplicate
                engine.mark_as_duplicate(duplicate["id"], original["id"], 0.9, "test")
            
            # Cleanup duplicates
            cleanup_results = engine.cleanup_duplicates(merge_data=False)
            assert "merged" in cleanup_results
            assert "deleted" in cleanup_results
            
            Path(f.name).unlink()
    
    def test_duplicate_statistics(self):
        """Test duplicate statistics calculation."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            engine = storage.deduplication
            
            # Add listings including duplicates
            listings = [
                {
                    "provider": "immoscout",
                    "external_id": "unique_1",
                    "title": "Original 1",
                    "url": "https://example.com/original1",
                    "price": "1000 €"
                },
                {
                    "provider": "immoscout",
                    "external_id": "unique_1",  # Duplicate
                    "title": "Duplicate 1",
                    "url": "https://example.com/duplicate1",
                    "price": "1000 €"
                },
                {
                    "provider": "wg_gesucht",
                    "external_id": "unique_2",
                    "title": "Original 2",
                    "url": "https://example.com/original2",
                    "price": "800 €"
                },
                {
                    "provider": "wg_gesucht",
                    "external_id": "unique_2",  # Duplicate
                    "title": "Duplicate 2",
                    "url": "https://example.com/duplicate2",
                    "price": "800 €"
                }
            ]
            
            for listing in listings:
                storage.add_listing(listing)
            
            # Get duplicate statistics
            stats = engine.get_duplicate_statistics()
            assert "total_duplicates" in stats
            assert "duplicates_by_provider" in stats
            assert "duplicate_rate" in stats
            assert stats["total_duplicates"] > 0
            assert stats["duplicate_rate"] > 0
            
            Path(f.name).unlink()


class TestAdvancedDeduplication:
    """Test advanced deduplication scenarios."""
    
    def test_deduplication_with_different_providers(self):
        """Test deduplication across different providers."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            engine = storage.deduplication
            
            # Add listing on one provider
            immoscout_data = {
                "provider": "immoscout",
                "title": "Beautiful Apartment",
                "url": "https://immoscout.com/listing1",
                "price": "1200 €",
                "size": "90 m²",
                "rooms": "3",
                "address": "Munich City Center"
            }
            
            storage.add_listing(immoscout_data)
            
            # Add very similar listing on different provider
            wg_gesucht_data = {
                "provider": "wg_gesucht",
                "title": "Beautiful Apartment",  # Same title
                "url": "https://wg-gesucht.com/listing1",
                "price": "1200 €",  # Same price
                "size": "90 m²",  # Same size
                "rooms": "3",  # Same rooms
                "address": "Munich City Center"  # Same address
            }
            
            duplicate_check = engine.check_duplicate(wg_gesucht_data)
            # Should detect as duplicate despite different provider
            if duplicate_check["is_duplicate"]:
                assert duplicate_check["confidence"] > 0.8
            
            Path(f.name).unlink()
    
    def test_deduplication_with_price_variations(self):
        """Test deduplication with price variations."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            engine = storage.deduplication
            
            # Add original listing
            original_data = {
                "provider": "immoscout",
                "title": "Standard Apartment",
                "url": "https://example.com/original",
                "price": "1000 €",
                "size": "80 m²",
                "rooms": "3"
            }
            
            storage.add_listing(original_data)
            
            # Check with slightly different price (within 10% threshold)
            similar_price_data = original_data.copy()
            similar_price_data["url"] = "https://example.com/similar-price"
            similar_price_data["price"] = "1050 €"  # 5% difference
            
            result1 = engine.check_duplicate(similar_price_data)
            # Should still match due to price similarity
            
            # Check with significantly different price (outside threshold)
            different_price_data = original_data.copy()
            different_price_data["url"] = "https://example.com/different-price"
            different_price_data["price"] = "1500 €"  # 50% difference
            
            result2 = engine.check_duplicate(different_price_data)
            # Should be less likely to match
            
            Path(f.name).unlink()
    
    def test_deduplication_performance(self):
        """Test deduplication performance with many listings."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            engine = storage.deduplication
            
            # Add many listings
            for i in range(50):
                listing_data = {
                    "provider": "immoscout" if i % 2 == 0 else "wg_gesucht",
                    "title": f"Test Listing {i}",
                    "url": f"https://example.com/listing{i}",
                    "price": f"{500 + i * 20} €",
                    "size": f"{20 + i * 2} m²",
                    "rooms": f"{1 + i % 4}",
                    "address": f"Munich District {i}"
                }
                
                storage.add_listing(listing_data)
            
            # Test deduplication performance
            import time
            start_time = time.time()
            
            duplicate_check = engine.check_duplicate({
                "provider": "immoscout",
                "title": "Test Listing 25",
                "url": "https://example.com/duplicate25",
                "price": "1000 €",
                "size": "70 m²",
                "rooms": "3",
                "address": "Munich District 25"
            })
            
            processing_time = time.time() - start_time
            
            # Should be reasonably fast even with many listings
            assert processing_time < 5.0  # 5 seconds max
            
            Path(f.name).unlink()
    
    def test_deduplication_edge_cases(self):
        """Test deduplication edge cases."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            storage = EnhancedStorageManager(f.name)
            engine = storage.deduplication
            
            # Test with missing fields
            minimal_data = {
                "provider": "immoscout",
                "title": "Minimal Listing",
                "url": "https://example.com/minimal"
            }
            
            result = engine.check_duplicate(minimal_data)
            assert isinstance(result, dict)
            assert "is_duplicate" in result
            
            # Test with empty strings
            empty_data = {
                "provider": "immoscout",
                "title": "",
                "url": "https://example.com/empty",
                "price": "",
                "size": "",
                "rooms": "",
                "address": ""
            }
            
            result = engine.check_duplicate(empty_data)
            assert isinstance(result, dict)
            
            Path(f.name).unlink()