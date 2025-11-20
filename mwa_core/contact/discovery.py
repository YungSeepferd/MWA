"""
Enhanced contact discovery engine for MWA Core.

Main orchestration engine that coordinates all contact discovery activities:
- Multi-method contact extraction
- Intelligent crawling and link following
- Advanced scoring and validation
- Result aggregation and deduplication
- Performance monitoring and optimization
"""

import asyncio
import logging
import time
from typing import List, Dict, Optional, Tuple, Any, Set
from pathlib import Path
from urllib.parse import urlparse
from dataclasses import dataclass, field
from datetime import datetime

from .models import Contact, ContactForm, SocialMediaProfile, DiscoveryContext, ExtractionResult, ConfidenceLevel
from .extractors import (
    EmailExtractor, PhoneExtractor, FormExtractor, 
    SocialMediaExtractor, OCRContactExtractor, PDFContactExtractor
)
from .crawler import ContactCrawler, SmartContactCrawler
from .scoring import ContactScoringEngine
from .validators import ContactValidator, ValidationResult
from ..config.settings import Settings

logger = logging.getLogger(__name__)


@dataclass
class DiscoveryStats:
    """Statistics for contact discovery operations."""
    urls_processed: int = 0
    contacts_found: int = 0
    forms_found: int = 0
    social_profiles_found: int = 0
    extraction_time: float = 0.0
    validation_time: float = 0.0
    total_time: float = 0.0
    success_rate: float = 0.0
    high_confidence_contacts: int = 0
    verified_contacts: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    
    @property
    def duration(self) -> float:
        """Get duration in seconds."""
        return (datetime.now() - self.start_time).total_seconds()


class ContactDiscoveryEngine:
    """
    Main contact discovery engine that orchestrates all extraction and validation activities.
    
    Features:
    - Multi-method contact extraction (email, phone, forms, social media)
    - Intelligent web crawling with depth control
    - Advanced scoring and confidence assessment
    - Comprehensive validation with multiple levels
    - Result deduplication and merging
    - Performance monitoring and optimization
    - Configurable extraction strategies
    """
    
    def __init__(self, config: Settings, storage_path: Optional[Path] = None):
        """
        Initialize the contact discovery engine.
        
        Args:
            config: Application configuration
            storage_path: Path for persistent storage (optional)
        """
        self.config = config
        self.settings = config.contact_discovery
        self.storage_path = storage_path or Path("data/contact_discovery")
        
        # Initialize extractors
        self.email_extractor = EmailExtractor(config)
        self.phone_extractor = PhoneExtractor(config)
        self.form_extractor = FormExtractor(config)
        self.social_extractor = SocialMediaExtractor(config)
        self.ocr_extractor = OCRContactExtractor(config)
        self.pdf_extractor = PDFContactExtractor(config)
        
        # Initialize crawler
        if self.settings.smart_crawling:
            self.crawler = SmartContactCrawler(config)
        else:
            self.crawler = ContactCrawler(config)
        
        # Initialize scoring and validation
        self.scoring_engine = ContactScoringEngine(config)
        self.validator = ContactValidator(
            enable_smtp_verification=self.settings.smtp_verification,
            enable_dns_verification=self.settings.dns_verification,
            rate_limit_seconds=self.settings.rate_limit_seconds
        )
        
        # Discovery state
        self.discovery_cache = {}
        self.extraction_stats = DiscoveryStats()
        
        logger.info(f"Contact discovery engine initialized (smart_crawling: {self.settings.smart_crawling})")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.email_extractor.__aenter__()
        await self.phone_extractor.__aenter__()
        await self.form_extractor.__aenter__()
        await self.social_extractor.__aenter__()
        await self.ocr_extractor.__aenter__()
        await self.pdf_extractor.__aenter__()
        await self.crawler.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.email_extractor.__aexit__(exc_type, exc_val, exc_tb)
        await self.phone_extractor.__aexit__(exc_type, exc_val, exc_tb)
        await self.form_extractor.__aexit__(exc_type, exc_val, exc_tb)
        await self.social_extractor.__aexit__(exc_type, exc_val, exc_tb)
        await self.ocr_extractor.__aexit__(exc_type, exc_val, exc_tb)
        await self.pdf_extractor.__aexit__(exc_type, exc_val, exc_tb)
        await self.crawler.__aexit__(exc_type, exc_val, exc_tb)
    
    async def discover_contacts(self, url: str, context: Optional[DiscoveryContext] = None,
                              enable_crawling: bool = True, enable_validation: bool = True,
                              extraction_methods: Optional[List[str]] = None) -> ExtractionResult:
        """
        Main discovery method to extract contacts from a URL.
        
        Args:
            url: URL to analyze for contact information
            context: Discovery context (optional)
            enable_crawling: Whether to enable web crawling
            enable_validation: Whether to validate discovered contacts
            extraction_methods: Specific extraction methods to use (optional)
            
        Returns:
            ExtractionResult with discovered contacts and metadata
        """
        start_time = time.time()
        
        if context is None:
            parsed_url = urlparse(url)
            context = DiscoveryContext(
                base_url=url,
                domain=parsed_url.netloc,
                allowed_domains=[parsed_url.netloc]
            )
        
        logger.info(f"Starting contact discovery for: {url}")
        
        try:
            # Check cache first
            cache_key = f"{url}_{context.language_preference}_{enable_crawling}"
            if cache_key in self.discovery_cache:
                logger.debug(f"Using cached results for {url}")
                return self.discovery_cache[cache_key]
            
            # Extract contacts from the main URL
            main_result = await self._extract_from_url(url, context, extraction_methods)
            
            # Crawl for additional contacts if enabled
            if enable_crawling and context.can_crawl_deeper:
                crawl_contacts, crawl_forms, crawl_stats = await self.crawler.crawl_for_contacts(url, context)
                main_result.contacts.extend(crawl_contacts)
                main_result.forms.extend(crawl_forms)
                self.extraction_stats.urls_processed += crawl_stats.urls_crawled
            
            # Deduplicate results
            main_result.contacts = self._deduplicate_contacts(main_result.contacts)
            main_result.forms = self._deduplicate_forms(main_result.forms)
            
            # Score contacts
            scored_contacts = await self._score_contacts(main_result.contacts, context)
            main_result.contacts = scored_contacts
            
            # Validate contacts if enabled
            if enable_validation and self.settings.validation_enabled:
                validated_contacts = await self._validate_contacts(main_result.contacts)
                main_result.contacts = validated_contacts
            
            # Filter by confidence threshold
            filtered_contacts = self._filter_by_confidence(main_result.contacts, context.confidence_threshold)
            main_result.contacts = filtered_contacts
            
            # Update statistics
            extraction_time = time.time() - start_time
            self._update_stats(main_result, extraction_time)
            
            # Cache results
            self.discovery_cache[cache_key] = main_result
            
            logger.info(f"Contact discovery completed for {url}: "
                       f"{len(main_result.contacts)} contacts, "
                       f"{len(main_result.forms)} forms, "
                       f"duration: {extraction_time:.1f}s")
            
            return main_result
            
        except Exception as e:
            logger.error(f"Contact discovery failed for {url}: {e}")
            return ExtractionResult(
                source_url=url,
                extraction_time=time.time() - start_time,
                error=str(e)
            )
    
    async def _extract_from_url(self, url: str, context: DiscoveryContext,
                              extraction_methods: Optional[List[str]] = None) -> ExtractionResult:
        """
        Extract contacts from a single URL using multiple methods.
        
        Args:
            url: URL to extract from
            context: Discovery context
            extraction_methods: Specific methods to use (optional)
            
        Returns:
            ExtractionResult with extracted data
        """
        start_time = time.time()
        contacts = []
        forms = []
        social_profiles = []
        
        try:
            # Fetch the page
            response = await self._fetch_url(url, context)
            if not response:
                return ExtractionResult(
                    source_url=url,
                    extraction_time=time.time() - start_time,
                    error="Failed to fetch URL"
                )
            
            # Parse HTML
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            page_text = soup.get_text()
            
            # Extract using specified methods
            methods = extraction_methods or context.extraction_methods
            
            # Email extraction
            if "email" in methods:
                emails = await self.email_extractor.extract_emails(page_text, url, context)
                contacts.extend(emails)
                logger.debug(f"Extracted {len(emails)} emails from {url}")
            
            # Phone extraction
            if "phone" in methods:
                phones = await self.phone_extractor.extract_phones(page_text, url, context)
                contacts.extend(phones)
                logger.debug(f"Extracted {len(phones)} phones from {url}")
            
            # Form extraction
            if "form" in methods:
                page_forms = await self.form_extractor.extract_forms(soup, url, context)
                forms.extend(page_forms)
                logger.debug(f"Extracted {len(page_forms)} forms from {url}")
            
            # Social media extraction
            if "social_media" in methods:
                profiles = await self.social_extractor.extract_social_media(page_text, url, context)
                social_profiles.extend(profiles)
                contacts.extend([profile.to_contact() for profile in profiles])
                logger.debug(f"Extracted {len(profiles)} social profiles from {url}")
            
            # OCR extraction for images
            if "ocr" in methods:
                images = soup.find_all('img')
                for img in images[:5]:  # Limit to first 5 images
                    img_src = img.get('src')
                    if img_src:
                        img_url = self._resolve_url(img_src, url)
                        ocr_contacts = await self.ocr_extractor.extract_from_image(img_url, url, context)
                        contacts.extend(ocr_contacts)
            
            # PDF extraction for links
            if "pdf" in methods:
                pdf_links = [a.get('href') for a in soup.find_all('a', href=True) 
                           if a.get('href', '').lower().endswith('.pdf')]
                for pdf_link in pdf_links[:3]:  # Limit to first 3 PDFs
                    pdf_url = self._resolve_url(pdf_link, url)
                    pdf_contacts = await self.pdf_extractor.extract_from_pdf(pdf_url, url, context)
                    contacts.extend(pdf_contacts)
            
            extraction_time = time.time() - start_time
            
            return ExtractionResult(
                contacts=contacts,
                forms=forms,
                social_media_profiles=social_profiles,
                source_url=url,
                extraction_time=extraction_time,
                metadata={
                    'extraction_methods': methods,
                    'response_status': response.status_code,
                    'content_length': len(response.text)
                }
            )
            
        except Exception as e:
            logger.error(f"Extraction failed for {url}: {e}")
            return ExtractionResult(
                source_url=url,
                extraction_time=time.time() - start_time,
                error=str(e)
            )
    
    async def _fetch_url(self, url: str, context: DiscoveryContext) -> Optional[Any]:
        """Fetch URL with proper headers and timeout."""
        try:
            headers = {
                'User-Agent': context.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': f"{context.language_preference},en;q=0.5",
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            async with httpx.AsyncClient(timeout=context.timeout) as client:
                response = await client.get(url, headers=headers, follow_redirects=True)
                response.raise_for_status()
                return response
                
        except Exception as e:
            logger.warning(f"Failed to fetch {url}: {e}")
            return None
    
    def _resolve_url(self, url: str, base_url: str) -> str:
        """Resolve relative URLs to absolute URLs."""
        from urllib.parse import urljoin
        return urljoin(base_url, url)
    
    async def _score_contacts(self, contacts: List[Contact], context: DiscoveryContext) -> List[Contact]:
        """Score contacts using the scoring engine."""
        if not contacts:
            return contacts
        
        # Create scoring context
        scoring_context = {
            'cultural_context': context.cultural_context,
            'language_preference': context.language_preference,
            'source_domain': context.domain
        }
        
        # Score all contacts
        scored_results = self.scoring_engine.score_batch(contacts, scoring_context)
        
        # Update contacts with scores
        for contact, score in scored_results:
            contact.confidence = self.scoring_engine.convert_to_confidence_level(score)
            contact.metadata['confidence_score'] = score
        
        return contacts
    
    async def _validate_contacts(self, contacts: List[Contact]) -> List[Contact]:
        """Validate contacts using the validator."""
        if not contacts or not self.settings.validation_enabled:
            return contacts
        
        validation_start = time.time()
        
        # Validate contacts in batches
        validation_results = await self.validator.validate_contacts_batch(
            contacts, 
            validation_level=self.settings.get('validation_level', 'standard')
        )
        
        # Update contacts with validation results
        for i, (contact, result) in enumerate(zip(contacts, validation_results)):
            contact.verification_status = ContactStatus.VERIFIED if result.is_valid else ContactStatus.INVALID
            contact.metadata['validation_result'] = result.to_dict()
            contact.metadata['validation_confidence'] = result.confidence_score
        
        validation_time = time.time() - validation_start
        self.extraction_stats.validation_time += validation_time
        
        logger.debug(f"Validated {len(contacts)} contacts in {validation_time:.1f}s")
        
        return contacts
    
    def _deduplicate_contacts(self, contacts: List[Contact]) -> List[Contact]:
        """Remove duplicate contacts based on method and value."""
        seen = set()
        unique_contacts = []
        
        for contact in contacts:
            key = (contact.method, contact.value.lower())
            if key not in seen:
                seen.add(key)
                unique_contacts.append(contact)
        
        logger.debug(f"Deduplicated {len(contacts)} contacts to {len(unique_contacts)} unique")
        return unique_contacts
    
    def _deduplicate_forms(self, forms: List[ContactForm]) -> List[ContactForm]:
        """Remove duplicate forms based on action URL."""
        seen = set()
        unique_forms = []
        
        for form in forms:
            key = form.action_url
            if key not in seen:
                seen.add(key)
                unique_forms.append(form)
        
        return unique_forms
    
    def _filter_by_confidence(self, contacts: List[Contact], min_confidence: ConfidenceLevel) -> List[Contact]:
        """Filter contacts by minimum confidence threshold."""
        confidence_order = {
            ConfidenceLevel.HIGH: 4,
            ConfidenceLevel.MEDIUM: 3,
            ConfidenceLevel.LOW: 2,
            ConfidenceLevel.UNCERTAIN: 1
        }
        
        min_level = confidence_order.get(min_confidence, 1)
        
        filtered_contacts = [
            contact for contact in contacts
            if confidence_order.get(contact.confidence, 1) >= min_level
        ]
        
        logger.debug(f"Filtered {len(contacts)} contacts to {len(filtered_contacts)} by confidence threshold")
        return filtered_contacts
    
    def _update_stats(self, result: ExtractionResult, extraction_time: float) -> None:
        """Update discovery statistics."""
        self.extraction_stats.contacts_found += len(result.contacts)
        self.extraction_stats.forms_found += len(result.forms)
        self.extraction_stats.social_profiles_found += len(result.social_media_profiles)
        self.extraction_stats.extraction_time += extraction_time
        self.extraction_stats.total_time += extraction_time
        
        # Count high confidence and verified contacts
        high_confidence = sum(1 for c in result.contacts if c.confidence == ConfidenceLevel.HIGH)
        verified = sum(1 for c in result.contacts if c.verification_status == ContactStatus.VERIFIED)
        
        self.extraction_stats.high_confidence_contacts += high_confidence
        self.extraction_stats.verified_contacts += verified
        
        # Calculate success rate
        if self.extraction_stats.urls_processed > 0:
            self.extraction_stats.success_rate = (
                self.extraction_stats.contacts_found / self.extraction_stats.urls_processed * 100
            )
    
    async def discover_contacts_batch(self, urls: List[str], contexts: Optional[List[DiscoveryContext]] = None,
                                    enable_crawling: bool = True, enable_validation: bool = True) -> List[ExtractionResult]:
        """
        Discover contacts from multiple URLs in batch.
        
        Args:
            urls: List of URLs to analyze
            contexts: List of discovery contexts (optional)
            enable_crawling: Whether to enable web crawling
            enable_validation: Whether to validate discovered contacts
            
        Returns:
            List of ExtractionResult objects
        """
        logger.info(f"Starting batch contact discovery for {len(urls)} URLs")
        
        results = []
        
        # Process URLs concurrently with rate limiting
        semaphore = asyncio.Semaphore(5)  # Limit concurrent requests
        
        async def process_url(url: str, context: Optional[DiscoveryContext]) -> ExtractionResult:
            async with semaphore:
                return await self.discover_contacts(
                    url, context, enable_crawling, enable_validation
                )
        
        # Create tasks
        tasks = []
        for i, url in enumerate(urls):
            context = contexts[i] if contexts and i < len(contexts) else None
            task = asyncio.create_task(process_url(url, context))
            tasks.append(task)
        
        # Execute tasks
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Batch processing failed for URL {i}: {result}")
                error_result = ExtractionResult(
                    source_url=urls[i],
                    extraction_time=0,
                    error=str(result)
                )
                final_results.append(error_result)
            else:
                final_results.append(result)
        
        logger.info(f"Batch contact discovery completed: {len(final_results)} results")
        
        return final_results
    
    def get_discovery_stats(self) -> DiscoveryStats:
        """Get current discovery statistics."""
        return self.extraction_stats
    
    def reset_stats(self) -> None:
        """Reset discovery statistics."""
        self.extraction_stats = DiscoveryStats()
        self.discovery_cache.clear()
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the discovery cache."""
        return {
            'cache_size': len(self.discovery_cache),
            'cache_keys': list(self.discovery_cache.keys()),
            'performance_history_size': len(self.scoring_engine.performance_history)
        }
    
    def clear_cache(self) -> None:
        """Clear the discovery cache."""
        self.discovery_cache.clear()
        logger.info("Discovery cache cleared")


# Convenience functions for quick discovery
async def discover_contacts(url: str, config: Settings, context: Optional[DiscoveryContext] = None,
                          enable_crawling: bool = True, enable_validation: bool = True) -> ExtractionResult:
    """
    Quick function to discover contacts from a single URL.
    
    Args:
        url: URL to analyze
        config: Application configuration
        context: Discovery context (optional)
        enable_crawling: Whether to enable web crawling
        enable_validation: Whether to validate discovered contacts
        
    Returns:
        ExtractionResult with discovered contacts
    """
    async with ContactDiscoveryEngine(config) as engine:
        return await engine.discover_contacts(url, context, enable_crawling, enable_validation)


async def discover_contacts_batch(urls: List[str], config: Settings, 
                                contexts: Optional[List[DiscoveryContext]] = None,
                                enable_crawling: bool = True, 
                                enable_validation: bool = True) -> List[ExtractionResult]:
    """
    Quick function to discover contacts from multiple URLs.
    
    Args:
        urls: List of URLs to analyze
        config: Application configuration
        contexts: List of discovery contexts (optional)
        enable_crawling: Whether to enable web crawling
        enable_validation: Whether to validate discovered contacts
        
    Returns:
        List of ExtractionResult objects
    """
    async with ContactDiscoveryEngine(config) as engine:
        return await engine.discover_contacts_batch(urls, contexts, enable_crawling, enable_validation)