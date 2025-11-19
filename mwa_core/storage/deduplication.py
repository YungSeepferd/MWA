"""
Advanced deduplication logic for MWA Core storage system.

Provides SHA-256 hash-based duplicate prevention, fuzzy matching for similar listings,
and configurable deduplication rules with performance optimization.
"""

from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from difflib import SequenceMatcher

from sqlalchemy import and_, or_, func
from sqlalchemy.orm import Session

from .models import Listing, Contact, DeduplicationStatus, ListingStatus
from .operations import CRUDOperations

logger = logging.getLogger(__name__)


class DeduplicationEngine:
    """Advanced deduplication engine with multiple strategies."""
    
    def __init__(self, crud_operations: CRUDOperations):
        """
        Initialize deduplication engine.
        
        Args:
            crud_operations: CRUDOperations instance
        """
        self.crud = crud_operations
        
        # Configuration for deduplication rules
        self.config = {
            "exact_match_threshold": 0.95,
            "fuzzy_match_threshold": 0.85,
            "price_variance_threshold": 0.1,  # 10% price difference allowed
            "size_variance_threshold": 0.15,  # 15% size difference allowed
            "title_similarity_threshold": 0.8,
            "address_similarity_threshold": 0.7,
            "max_duplicate_age_days": 365,  # Don't consider very old listings
            "enable_fuzzy_matching": True,
            "enable_price_normalization": True,
            "enable_address_normalization": True,
        }
    
    def check_duplicate(self, listing_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if a listing is a duplicate using multiple strategies.
        
        Args:
            listing_data: Listing data to check
            
        Returns:
            Dictionary with duplicate information
        """
        result = {
            "is_duplicate": False,
            "duplicate_strategy": None,
            "duplicate_of_id": None,
            "confidence": 0.0,
            "reason": None,
            "similar_listings": []
        }
        
        try:
            # Strategy 1: Exact hash match
            exact_match = self._check_exact_hash_match(listing_data)
            if exact_match["is_duplicate"]:
                return exact_match
            
            # Strategy 2: Provider + External ID match
            provider_match = self._check_provider_external_id_match(listing_data)
            if provider_match["is_duplicate"]:
                return provider_match
            
            # Strategy 3: URL match
            url_match = self._check_url_match(listing_data)
            if url_match["is_duplicate"]:
                return url_match
            
            # Strategy 4: Fuzzy matching (if enabled)
            if self.config["enable_fuzzy_matching"]:
                fuzzy_match = self._check_fuzzy_match(listing_data)
                if fuzzy_match["is_duplicate"]:
                    return fuzzy_match
            
            # Strategy 5: Content-based similarity
            content_match = self._check_content_similarity(listing_data)
            if content_match["is_duplicate"]:
                return content_match
            
            return result
            
        except Exception as e:
            logger.error(f"Error in duplicate check: {e}")
            return result
    
    def _check_exact_hash_match(self, listing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for exact hash signature match."""
        try:
            # Generate hash signature for the new listing
            hash_signature = self._generate_hash_signature(listing_data)
            
            with self.crud.get_session() as session:
                # Look for existing listing with same hash
                existing = session.query(Listing).filter_by(
                    hash_signature=hash_signature,
                    status=ListingStatus.ACTIVE
                ).first()
                
                if existing:
                    return {
                        "is_duplicate": True,
                        "duplicate_strategy": "exact_hash",
                        "duplicate_of_id": existing.id,
                        "confidence": 1.0,
                        "reason": f"Exact hash match with listing {existing.id}",
                        "similar_listings": [existing.to_dict()]
                    }
            
            return {"is_duplicate": False}
            
        except Exception as e:
            logger.error(f"Error in exact hash check: {e}")
            return {"is_duplicate": False}
    
    def _check_provider_external_id_match(self, listing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for provider + external ID match."""
        try:
            provider = listing_data.get("provider")
            external_id = listing_data.get("external_id")
            
            if not provider or not external_id:
                return {"is_duplicate": False}
            
            with self.crud.get_session() as session:
                existing = session.query(Listing).filter_by(
                    provider=provider,
                    external_id=external_id,
                    status=ListingStatus.ACTIVE
                ).first()
                
                if existing:
                    return {
                        "is_duplicate": True,
                        "duplicate_strategy": "provider_external_id",
                        "duplicate_of_id": existing.id,
                        "confidence": 0.95,
                        "reason": f"Provider+External ID match with listing {existing.id}",
                        "similar_listings": [existing.to_dict()]
                    }
            
            return {"is_duplicate": False}
            
        except Exception as e:
            logger.error(f"Error in provider/external ID check: {e}")
            return {"is_duplicate": False}
    
    def _check_url_match(self, listing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for exact URL match."""
        try:
            url = listing_data.get("url")
            if not url:
                return {"is_duplicate": False}
            
            with self.crud.get_session() as session:
                existing = session.query(Listing).filter_by(
                    url=url,
                    status=ListingStatus.ACTIVE
                ).first()
                
                if existing:
                    return {
                        "is_duplicate": True,
                        "duplicate_strategy": "url_match",
                        "duplicate_of_id": existing.id,
                        "confidence": 0.95,
                        "reason": f"URL match with listing {existing.id}",
                        "similar_listings": [existing.to_dict()]
                    }
            
            return {"is_duplicate": False}
            
        except Exception as e:
            logger.error(f"Error in URL check: {e}")
            return {"is_duplicate": False}
    
    def _check_fuzzy_match(self, listing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for fuzzy matches using various criteria."""
        try:
            similar_listings = self._find_similar_listings(listing_data)
            
            if not similar_listings:
                return {"is_duplicate": False}
            
            # Calculate similarity scores
            best_match = None
            best_score = 0.0
            
            for similar_listing in similar_listings:
                similarity_score = self._calculate_similarity_score(
                    listing_data, similar_listing
                )
                
                if similarity_score > best_score:
                    best_score = similarity_score
                    best_match = similar_listing
            
            # Check if best match exceeds threshold
            if best_match and best_score >= self.config["fuzzy_match_threshold"]:
                return {
                    "is_duplicate": True,
                    "duplicate_strategy": "fuzzy_match",
                    "duplicate_of_id": best_match["id"],
                    "confidence": best_score,
                    "reason": f"Fuzzy match with {best_score:.2f} similarity score",
                    "similar_listings": similar_listings
                }
            
            return {
                "is_duplicate": False,
                "similar_listings": similar_listings
            }
            
        except Exception as e:
            logger.error(f"Error in fuzzy match check: {e}")
            return {"is_duplicate": False}
    
    def _check_content_similarity(self, listing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check for content-based similarity."""
        try:
            # Normalize and compare key fields
            normalized_new = self._normalize_listing_data(listing_data)
            
            with self.crud.get_session() as session:
                # Get recent listings for comparison
                recent_listings = session.query(Listing).filter(
                    Listing.status == ListingStatus.ACTIVE,
                    Listing.scraped_at >= datetime.utcnow() - timedelta(days=30)
                ).limit(100).all()
                
                best_match = None
                best_score = 0.0
                
                for existing_listing in recent_listings:
                    normalized_existing = self._normalize_listing_data(existing_listing.to_dict())
                    
                    similarity_score = self._calculate_content_similarity(
                        normalized_new, normalized_existing
                    )
                    
                    if similarity_score > best_score:
                        best_score = similarity_score
                        best_match = existing_listing
                
                if best_match and best_score >= self.config["exact_match_threshold"]:
                    return {
                        "is_duplicate": True,
                        "duplicate_strategy": "content_similarity",
                        "duplicate_of_id": best_match.id,
                        "confidence": best_score,
                        "reason": f"Content similarity with {best_score:.2f} score",
                        "similar_listings": [best_match.to_dict()]
                    }
            
            return {"is_duplicate": False}
            
        except Exception as e:
            logger.error(f"Error in content similarity check: {e}")
            return {"is_duplicate": False}
    
    def _find_similar_listings(self, listing_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find potentially similar listings based on key criteria."""
        try:
            with self.crud.get_session() as session:
                query = session.query(Listing).filter(
                    Listing.status == ListingStatus.ACTIVE,
                    Listing.scraped_at >= datetime.utcnow() - timedelta(days=self.config["max_duplicate_age_days"])
                )
                
                # Filter by provider if available
                if listing_data.get("provider"):
                    query = query.filter(Listing.provider == listing_data["provider"])
                
                # Filter by price range if available
                if listing_data.get("price") and self.config["enable_price_normalization"]:
                    price_range = self._get_price_range(listing_data["price"])
                    if price_range:
                        query = query.filter(
                            Listing.price >= price_range[0],
                            Listing.price <= price_range[1]
                        )
                
                # Filter by size range if available
                if listing_data.get("size"):
                    size_range = self._get_size_range(listing_data["size"])
                    if size_range:
                        query = query.filter(
                            Listing.size >= size_range[0],
                            Listing.size <= size_range[1]
                        )
                
                # Get candidates for similarity comparison
                candidates = query.limit(50).all()
                
                similar_listings = []
                for candidate in candidates:
                    # Quick similarity check
                    if self._is_potentially_similar(listing_data, candidate.to_dict()):
                        similar_listings.append(candidate.to_dict())
                
                return similar_listings
                
        except Exception as e:
            logger.error(f"Error finding similar listings: {e}")
            return []
    
    def _calculate_similarity_score(self, listing1: Dict[str, Any], 
                                  listing2: Dict[str, Any]) -> float:
        """Calculate similarity score between two listings."""
        try:
            scores = []
            
            # Title similarity
            if listing1.get("title") and listing2.get("title"):
                title_score = SequenceMatcher(
                    None, 
                    self._normalize_text(listing1["title"]),
                    self._normalize_text(listing2["title"])
                ).ratio()
                scores.append(title_score * 0.3)  # Weight: 30%
            
            # Price similarity
            if listing1.get("price") and listing2.get("price"):
                price_score = self._calculate_price_similarity(
                    listing1["price"], listing2["price"]
                )
                scores.append(price_score * 0.25)  # Weight: 25%
            
            # Size similarity
            if listing1.get("size") and listing2.get("size"):
                size_score = self._calculate_size_similarity(
                    listing1["size"], listing2["size"]
                )
                scores.append(size_score * 0.2)  # Weight: 20%
            
            # Address similarity
            if listing1.get("address") and listing2.get("address"):
                address_score = SequenceMatcher(
                    None,
                    self._normalize_address(listing1["address"]),
                    self._normalize_address(listing2["address"])
                ).ratio()
                scores.append(address_score * 0.15)  # Weight: 15%
            
            # Rooms similarity
            if listing1.get("rooms") and listing2.get("rooms"):
                rooms_score = 1.0 if listing1["rooms"] == listing2["rooms"] else 0.0
                scores.append(rooms_score * 0.1)  # Weight: 10%
            
            return sum(scores) if scores else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating similarity score: {e}")
            return 0.0
    
    def _calculate_price_similarity(self, price1: str, price2: str) -> float:
        """Calculate similarity between two price strings."""
        try:
            # Extract numeric values
            num1 = self._extract_numeric_price(price1)
            num2 = self._extract_numeric_price(price2)
            
            if num1 is None or num2 is None:
                return 0.0
            
            # Calculate relative difference
            if num1 == num2:
                return 1.0
            
            max_price = max(num1, num2)
            min_price = min(num1, num2)
            difference = (max_price - min_price) / max_price
            
            # Return similarity score (inverse of difference)
            return max(0.0, 1.0 - difference / self.config["price_variance_threshold"])
            
        except Exception as e:
            logger.error(f"Error calculating price similarity: {e}")
            return 0.0
    
    def _calculate_size_similarity(self, size1: str, size2: str) -> float:
        """Calculate similarity between two size strings."""
        try:
            # Extract numeric values
            num1 = self._extract_numeric_size(size1)
            num2 = self._extract_numeric_size(size2)
            
            if num1 is None or num2 is None:
                return 0.0
            
            # Calculate relative difference
            if num1 == num2:
                return 1.0
            
            max_size = max(num1, num2)
            min_size = min(num1, num2)
            difference = (max_size - min_size) / max_size
            
            # Return similarity score (inverse of difference)
            return max(0.0, 1.0 - difference / self.config["size_variance_threshold"])
            
        except Exception as e:
            logger.error(f"Error calculating size similarity: {e}")
            return 0.0
    
    def _generate_hash_signature(self, listing_data: Dict[str, Any]) -> str:
        """Generate SHA-256 hash signature for a listing."""
        try:
            # Create normalized string for hashing
            hash_components = [
                listing_data.get("provider", ""),
                listing_data.get("external_id", ""),
                self._normalize_text(listing_data.get("title", "")),
                self._normalize_price(listing_data.get("price", "")),
                self._normalize_size(listing_data.get("size", "")),
                self._normalize_text(listing_data.get("rooms", "")),
                self._normalize_address(listing_data.get("address", ""))
            ]
            
            hash_string = "|".join(hash_components)
            return hashlib.sha256(hash_string.encode('utf-8')).hexdigest()
            
        except Exception as e:
            logger.error(f"Error generating hash signature: {e}")
            return ""
    
    def _normalize_listing_data(self, listing_data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize listing data for comparison."""
        return {
            "title": self._normalize_text(listing_data.get("title", "")),
            "price": self._normalize_price(listing_data.get("price", "")),
            "size": self._normalize_size(listing_data.get("size", "")),
            "rooms": self._normalize_text(listing_data.get("rooms", "")),
            "address": self._normalize_address(listing_data.get("address", "")),
            "description": self._normalize_text(listing_data.get("description", "")),
        }
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for comparison."""
        if not text:
            return ""
        
        # Convert to lowercase
        text = text.lower()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove special characters but keep spaces
        text = re.sub(r'[^\w\s]', '', text)
        
        return text
    
    def _normalize_price(self, price: str) -> str:
        """Normalize price string."""
        if not price:
            return ""
        
        # Extract numeric value and currency
        numbers = re.findall(r'[\d,]+', price)
        if numbers:
            # Remove commas and take first number
            normalized = numbers[0].replace(',', '')
            return normalized
        
        return price.lower().strip()
    
    def _normalize_size(self, size: str) -> str:
        """Normalize size string."""
        if not size:
            return ""
        
        # Extract numeric value
        numbers = re.findall(r'[\d.]+', size)
        if numbers:
            return numbers[0]
        
        return size.lower().strip()
    
    def _normalize_address(self, address: str) -> str:
        """Normalize address for comparison."""
        if not address:
            return ""
        
        # Convert to lowercase
        address = address.lower()
        
        # Remove common words that don't affect similarity
        common_words = ['straße', 'strasse', 'str', 'platz', 'pl', 'weg']
        for word in common_words:
            address = address.replace(word, '')
        
        # Remove extra whitespace
        address = re.sub(r'\s+', ' ', address).strip()
        
        return address
    
    def _extract_numeric_price(self, price: str) -> Optional[float]:
        """Extract numeric value from price string."""
        try:
            # Find all numbers in the string
            numbers = re.findall(r'[\d,]+', price)
            if numbers:
                # Take the first number and remove commas
                return float(numbers[0].replace(',', ''))
            return None
        except (ValueError, TypeError):
            return None
    
    def _extract_numeric_size(self, size: str) -> Optional[float]:
        """Extract numeric value from size string."""
        try:
            # Find all decimal numbers
            numbers = re.findall(r'[\d.]+', size)
            if numbers:
                return float(numbers[0])
            return None
        except (ValueError, TypeError):
            return None
    
    def _get_price_range(self, price: str) -> Optional[Tuple[str, str]]:
        """Get price range for filtering."""
        try:
            numeric_price = self._extract_numeric_price(price)
            if numeric_price is None:
                return None
            
            # Allow 10% variance
            variance = numeric_price * self.config["price_variance_threshold"]
            min_price = numeric_price - variance
            max_price = numeric_price + variance
            
            return (str(int(min_price)), str(int(max_price)))
        except Exception:
            return None
    
    def _get_size_range(self, size: str) -> Optional[Tuple[str, str]]:
        """Get size range for filtering."""
        try:
            numeric_size = self._extract_numeric_size(size)
            if numeric_size is None:
                return None
            
            # Allow 15% variance
            variance = numeric_size * self.config["size_variance_threshold"]
            min_size = numeric_size - variance
            max_size = numeric_size + variance
            
            return (str(min_size), str(max_size))
        except Exception:
            return None
    
    def _is_potentially_similar(self, listing1: Dict[str, Any], 
                               listing2: Dict[str, Any]) -> bool:
        """Quick check if two listings might be similar."""
        try:
            # Check title similarity (quick check)
            if (listing1.get("title") and listing2.get("title") and
                len(listing1["title"]) > 10 and len(listing2["title"]) > 10):
                title_ratio = SequenceMatcher(
                    None,
                    listing1["title"][:50],  # Compare first 50 chars
                    listing2["title"][:50]
                ).ratio()
                if title_ratio < 0.5:  # Titles are very different
                    return False
            
            # Check price similarity (if both have prices)
            if (listing1.get("price") and listing2.get("price") and
                self.config["enable_price_normalization"]):
                price_similarity = self._calculate_price_similarity(
                    listing1["price"], listing2["price"]
                )
                if price_similarity < 0.5:  # Prices are very different
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error in potential similarity check: {e}")
            return True  # Default to checking further
    
    def _calculate_content_similarity(self, normalized1: Dict[str, Any], 
                                    normalized2: Dict[str, Any]) -> float:
        """Calculate content-based similarity score."""
        try:
            scores = []
            
            # Compare each field
            for field in ["title", "price", "size", "rooms", "address"]:
                val1 = normalized1.get(field, "")
                val2 = normalized2.get(field, "")
                
                if val1 and val2:
                    if field in ["price", "size"]:
                        # Exact match for numeric fields
                        score = 1.0 if val1 == val2 else 0.0
                    else:
                        # Text similarity
                        score = SequenceMatcher(None, val1, val2).ratio()
                    
                    # Weight the scores
                    weights = {"title": 0.3, "price": 0.25, "size": 0.2, "rooms": 0.15, "address": 0.1}
                    scores.append(score * weights.get(field, 0.1))
            
            return sum(scores) if scores else 0.0
            
        except Exception as e:
            logger.error(f"Error calculating content similarity: {e}")
            return 0.0
    
    def mark_as_duplicate(self, duplicate_id: int, original_id: int, 
                         confidence: float, strategy: str) -> bool:
        """
        Mark a listing as a duplicate of another.
        
        Args:
            duplicate_id: ID of the duplicate listing
            original_id: ID of the original listing
            confidence: Confidence score
            strategy: Deduplication strategy used
            
        Returns:
            True if successful
        """
        try:
            with self.crud.get_session() as session:
                duplicate = session.query(Listing).filter_by(id=duplicate_id).first()
                original = session.query(Listing).filter_by(id=original_id).first()
                
                if not duplicate or not original:
                    logger.warning(f"Listings not found: {duplicate_id}, {original_id}")
                    return False
                
                # Update duplicate status
                duplicate.deduplication_status = DeduplicationStatus.DUPLICATE
                duplicate.duplicate_of_id = original_id
                duplicate.updated_at = datetime.utcnow()
                
                # Increment view count of original
                original.view_count += 1
                original.last_seen_at = datetime.utcnow()
                
                logger.info(f"Marked listing {duplicate_id} as duplicate of {original_id} "
                           f"(confidence: {confidence:.2f}, strategy: {strategy})")
                return True
                
        except Exception as e:
            logger.error(f"Error marking duplicate: {e}")
            return False
    
    def merge_duplicate_listings(self, source_id: int, target_id: int) -> bool:
        """
        Merge data from duplicate listing into original.
        
        Args:
            source_id: ID of the duplicate listing (source)
            target_id: ID of the original listing (target)
            
        Returns:
            True if successful
        """
        try:
            with self.crud.get_session() as session:
                source = session.query(Listing).filter_by(id=source_id).first()
                target = session.query(Listing).filter_by(id=target_id).first()
                
                if not source or not target:
                    logger.warning(f"Listings not found: {source_id}, {target_id}")
                    return False
                
                # Merge contacts
                for contact in source.contact_entries:
                    contact.listing_id = target_id
                
                # Merge images (if source has more images)
                source_images = source.get_images()
                target_images = target.get_images()
                
                if len(source_images) > len(target_images):
                    target.set_images(source_images)
                
                # Merge contacts info
                source_contacts = source.get_contacts()
                target_contacts = target.get_contacts()
                
                # Combine unique contacts
                combined_contacts = target_contacts.copy()
                for contact in source_contacts:
                    if contact not in combined_contacts:
                        combined_contacts.append(contact)
                
                target.set_contacts(combined_contacts)
                
                # Update metadata
                target.view_count += source.view_count
                target.last_seen_at = max(target.last_seen_at, source.last_seen_at)
                
                # Mark source as merged
                source.deduplication_status = DeduplicationStatus.MERGED
                source.status = ListingStatus.INACTIVE
                
                logger.info(f"Merged listing {source_id} into {target_id}")
                return True
                
        except Exception as e:
            logger.error(f"Error merging listings: {e}")
            return False
    
    def get_duplicate_statistics(self) -> Dict[str, Any]:
        """Get deduplication statistics."""
        try:
            with self.crud.get_session() as session:
                stats = {}
                
                # Count by deduplication status
                status_counts = session.query(
                    Listing.deduplication_status, func.count(Listing.id)
                ).group_by(Listing.deduplication_status).all()
                
                stats["by_deduplication_status"] = {
                    status.value if status else "unknown": count 
                    for status, count in status_counts
                }
                
                # Count duplicates by provider
                duplicate_stats = session.query(
                    Listing.provider, func.count(Listing.id)
                ).filter(
                    Listing.deduplication_status == DeduplicationStatus.DUPLICATE
                ).group_by(Listing.provider).all()
                
                stats["duplicates_by_provider"] = dict(duplicate_stats)
                
                # Total duplicates
                total_duplicates = session.query(Listing).filter(
                    Listing.deduplication_status == DeduplicationStatus.DUPLICATE
                ).count()
                
                stats["total_duplicates"] = total_duplicates
                
                # Duplicate detection rate
                total_listings = session.query(Listing).count()
                stats["duplicate_rate"] = (
                    total_duplicates / total_listings if total_listings > 0 else 0.0
                )
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting duplicate statistics: {e}")
            return {}
    
    def cleanup_duplicates(self, merge_data: bool = True) -> Dict[str, int]:
        """
        Clean up duplicate listings.
        
        Args:
            merge_data: Whether to merge data from duplicates
            
        Returns:
            Dictionary with cleanup counts
        """
        try:
            with self.crud.get_session() as session:
                cleanup_counts = {
                    "merged": 0,
                    "deleted": 0,
                    "errors": 0
                }
                
                # Get all duplicate listings
                duplicates = session.query(Listing).filter(
                    Listing.deduplication_status == DeduplicationStatus.DUPLICATE
                ).all()
                
                for duplicate in duplicates:
                    try:
                        if merge_data and duplicate.duplicate_of_id:
                            # Merge data into original
                            success = self.merge_duplicate_listings(
                                duplicate.id, duplicate.duplicate_of_id
                            )
                            if success:
                                cleanup_counts["merged"] += 1
                            else:
                                cleanup_counts["errors"] += 1
                        else:
                            # Just delete the duplicate
                            session.delete(duplicate)
                            cleanup_counts["deleted"] += 1
                            
                    except Exception as e:
                        logger.error(f"Error cleaning up duplicate {duplicate.id}: {e}")
                        cleanup_counts["errors"] += 1
                
                logger.info(f"Duplicate cleanup completed: {cleanup_counts}")
                return cleanup_counts
                
        except Exception as e:
            logger.error(f"Error in duplicate cleanup: {e}")
            return {"errors": 1}