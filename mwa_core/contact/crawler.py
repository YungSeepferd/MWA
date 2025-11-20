"""
Enhanced web crawler for contact discovery with depth limiting and domain restrictions.

Provides intelligent crawling capabilities for finding contact information:
- Depth-limited crawling
- Domain restrictions and allowlists
- Rate limiting and politeness policies
- Robots.txt compliance
- User agent management
- Link prioritization
- Contact page detection
"""

import asyncio
import logging
import re
import time
from typing import List, Dict, Optional, Set, Tuple, Any
from urllib.parse import urljoin, urlparse, urlunparse
from urllib.robotparser import RobotFileParser
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta

import httpx
from bs4 import BeautifulSoup

from .models import DiscoveryContext, Contact, ContactForm, ConfidenceLevel
from .extractors import EmailExtractor, PhoneExtractor, FormExtractor, SocialMediaExtractor
from ..config.settings import Settings

logger = logging.getLogger(__name__)


@dataclass
class CrawlResult:
    """Result of a crawling operation."""
    url: str
    status_code: int
    contacts: List[Contact] = field(default_factory=list)
    forms: List[ContactForm] = field(default_factory=list)
    links_found: List[str] = field(default_factory=list)
    crawl_time: float = 0.0
    error: Optional[str] = None


@dataclass
class CrawlStats:
    """Statistics for crawling operations."""
    urls_crawled: int = 0
    contacts_found: int = 0
    forms_found: int = 0
    errors_encountered: int = 0
    robots_blocked: int = 0
    start_time: datetime = field(default_factory=datetime.now)
    
    @property
    def duration(self) -> float:
        """Get duration in seconds."""
        return (datetime.now() - self.start_time).total_seconds()
    
    @property
    def success_rate(self) -> float:
        """Get success rate as percentage."""
        if self.urls_crawled == 0:
            return 0.0
        return ((self.urls_crawled - self.errors_encountered) / self.urls_crawled) * 100


class ContactCrawler:
    """
    Enhanced web crawler for contact discovery with intelligent link following.
    
    Features:
    - Depth-limited crawling with configurable limits
    - Domain restrictions and allowlists
    - Rate limiting with politeness policies
    - Robots.txt compliance
    - User agent rotation
    - Contact page prioritization
    - Link relevance scoring
    """
    
    # Contact-related keywords for link prioritization
    CONTACT_KEYWORDS = {
        'kontakt', 'contact', 'impressum', 'about', 'über', 'contactus',
        'vermieter', 'hausverwaltung', 'landlord', 'owner', 'agenzia',
        'kontaktformular', 'kontaktseite', 'contactform', 'reach-us',
        'get-in-touch', 'contact-info', 'contact-details'
    }
    
    # URL patterns that indicate contact pages
    CONTACT_URL_PATTERNS = [
        r'/kontakt',
        r'/contact',
        r'/impressum',
        r'/about',
        r'/uber',
        r'/contact-us',
        r'/contactus',
        r'/kontaktformular',
        r'/contact-form',
        r'/vermieter',
        r'/landlord',
        r'/owner',
        r'/team',
        r'/staff',
        r'/directory'
    ]
    
    # File extensions to ignore
    IGNORED_EXTENSIONS = {
        '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx',
        '.zip', '.rar', '.tar', '.gz', '.7z',
        '.mp3', '.mp4', '.avi', '.mov', '.wmv',
        '.jpg', '.jpeg', '.png', '.gif', '.svg', '.webp',
        '.css', '.js', '.xml', '.json'
    }
    
    def __init__(self, config: Settings):
        """
        Initialize the contact crawler.
        
        Args:
            config: Application configuration
        """
        self.config = config
        self.settings = config.contact_discovery
        self.session = httpx.AsyncClient(
            timeout=self.settings.request_timeout,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10)
        )
        
        # Initialize extractors
        self.email_extractor = EmailExtractor(config)
        self.phone_extractor = PhoneExtractor(config)
        self.form_extractor = FormExtractor(config)
        self.social_extractor = SocialMediaExtractor(config)
        
        # Crawling state
        self.visited_urls: Set[str] = set()
        self.robots_cache: Dict[str, RobotFileParser] = {}
        self.domain_rate_limits: Dict[str, float] = {}
        self.crawl_stats = CrawlStats()
        
        # Queue for URLs to crawl
        self.url_queue: deque = deque()
        
        logger.info(f"Contact crawler initialized (max_depth: {self.settings.max_crawl_depth})")
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self.email_extractor.__aenter__()
        await self.phone_extractor.__aenter__()
        await self.form_extractor.__aenter__()
        await self.social_extractor.__aenter__()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.session.aclose()
        await self.email_extractor.__aexit__(exc_type, exc_val, exc_tb)
        await self.phone_extractor.__aexit__(exc_type, exc_val, exc_tb)
        await self.form_extractor.__aexit__(exc_type, exc_val, exc_tb)
        await self.social_extractor.__aexit__(exc_type, exc_val, exc_tb)
    
    async def crawl_for_contacts(self, start_url: str, context: Optional[DiscoveryContext] = None) -> Tuple[List[Contact], List[ContactForm], CrawlStats]:
        """
        Main crawling method to discover contacts starting from a URL.
        
        Args:
            start_url: Starting URL for crawling
            context: Discovery context (optional)
            
        Returns:
            Tuple of (contacts, forms, crawl_stats)
        """
        if context is None:
            parsed_url = urlparse(start_url)
            context = DiscoveryContext(
                base_url=start_url,
                domain=parsed_url.netloc,
                allowed_domains=[parsed_url.netloc]
            )
        
        logger.info(f"Starting contact crawl from: {start_url}")
        
        # Initialize crawling
        self.url_queue.append((start_url, context.current_depth))
        all_contacts = []
        all_forms = []
        
        try:
            while self.url_queue and context.can_crawl_deeper:
                current_url, current_depth = self.url_queue.popleft()
                
                # Skip if already visited
                if current_url in self.visited_urls:
                    continue
                
                # Check rate limiting
                await self._enforce_rate_limit(current_url)
                
                # Crawl the page
                result = await self._crawl_page(current_url, context)
                
                if result.error:
                    logger.warning(f"Crawl error for {current_url}: {result.error}")
                    self.crawl_stats.errors_encountered += 1
                    continue
                
                # Process results
                self.visited_urls.add(current_url)
                self.crawl_stats.urls_crawled += 1
                self.crawl_stats.contacts_found += len(result.contacts)
                self.crawl_stats.forms_found += len(result.forms)
                
                all_contacts.extend(result.contacts)
                all_forms.extend(result.forms)
                
                # Add discovered links to queue
                for link in result.links_found:
                    if self._should_crawl_link(link, current_depth, context):
                        self.url_queue.append((link, current_depth + 1))
                
                # Log progress
                if self.crawl_stats.urls_crawled % 10 == 0:
                    logger.info(f"Crawl progress: {self.crawl_stats.urls_crawled} URLs, "
                              f"{self.crawl_stats.contacts_found} contacts, "
                              f"{self.crawl_stats.forms_found} forms")
                
        except Exception as e:
            logger.error(f"Crawling failed: {e}")
        
        logger.info(f"Crawling completed: {self.crawl_stats.urls_crawled} URLs, "
                   f"{self.crawl_stats.contacts_found} contacts, "
                   f"{self.crawl_stats.forms_found} forms, "
                   f"duration: {self.crawl_stats.duration:.1f}s")
        
        return all_contacts, all_forms, self.crawl_stats
    
    async def _crawl_page(self, url: str, context: DiscoveryContext) -> CrawlResult:
        """
        Crawl a single page and extract contacts.
        
        Args:
            url: URL to crawl
            context: Discovery context
            
        Returns:
            CrawlResult with extracted data
        """
        start_time = time.time()
        
        try:
            # Check robots.txt compliance
            if not await self._check_robots_txt(url):
                self.crawl_stats.robots_blocked += 1
                return CrawlResult(url=url, status_code=403, error="Blocked by robots.txt")
            
            # Fetch the page
            headers = {
                'User-Agent': context.user_agent,
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Accept-Language': f"{context.language_preference},en;q=0.5",
                'Accept-Encoding': 'gzip, deflate',
                'Connection': 'keep-alive',
            }
            
            response = await self.session.get(url, headers=headers, follow_redirects=True)
            response.raise_for_status()
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract contacts
            contacts = []
            forms = []
            
            # Extract emails
            page_text = soup.get_text()
            emails = await self.email_extractor.extract_emails(page_text, url, context)
            contacts.extend(emails)
            
            # Extract phone numbers
            phones = await self.phone_extractor.extract_phones(page_text, url, context)
            contacts.extend(phones)
            
            # Extract contact forms
            page_forms = await self.form_extractor.extract_forms(soup, url, context)
            forms.extend(page_forms)
            
            # Extract social media profiles
            social_profiles = await self.social_extractor.extract_social_media(page_text, url, context)
            contacts.extend([profile.to_contact() for profile in social_profiles])
            
            # Find links for further crawling
            links = self._extract_links(soup, url, context)
            
            crawl_time = time.time() - start_time
            
            return CrawlResult(
                url=url,
                status_code=response.status_code,
                contacts=contacts,
                forms=forms,
                links_found=links,
                crawl_time=crawl_time
            )
            
        except httpx.RequestError as e:
            return CrawlResult(url=url, status_code=0, error=f"Request error: {str(e)}")
        except httpx.HTTPStatusError as e:
            return CrawlResult(url=url, status_code=e.response.status_code, error=f"HTTP error: {e.response.status_code}")
        except Exception as e:
            return CrawlResult(url=url, status_code=0, error=f"Unexpected error: {str(e)}")
    
    def _extract_links(self, soup: BeautifulSoup, base_url: str, context: DiscoveryContext) -> List[str]:
        """
        Extract and prioritize links for further crawling.
        
        Args:
            soup: BeautifulSoup object
            base_url: Base URL for resolving relative links
            context: Discovery context
            
        Returns:
            List of prioritized URLs
        """
        links = []
        link_elements = soup.find_all('a', href=True)
        
        for link_elem in link_elements:
            try:
                href = link_elem.get('href', '').strip()
                link_text = link_elem.get_text(strip=True).lower()
                
                # Skip empty links
                if not href:
                    continue
                
                # Skip non-HTTP links
                if href.startswith(('javascript:', 'mailto:', 'tel:', '#')):
                    continue
                
                # Skip file downloads
                if any(href.lower().endswith(ext) for ext in self.IGNORED_EXTENSIONS):
                    continue
                
                # Resolve relative URLs
                if not href.startswith(('http://', 'https://')):
                    absolute_url = urljoin(base_url, href)
                else:
                    absolute_url = href
                
                # Parse URL for validation
                parsed_url = urlparse(absolute_url)
                
                # Check domain restrictions
                if parsed_url.netloc not in context.allowed_domains:
                    continue
                
                # Score link for prioritization
                score = self._score_link(absolute_url, link_text, context)
                
                links.append((absolute_url, score))
                
            except Exception as e:
                continue
        
        # Sort by score and return URLs
        links.sort(key=lambda x: x[1], reverse=True)
        return [url for url, score in links[:20]]  # Limit to top 20 links
    
    def _score_link(self, url: str, link_text: str, context: DiscoveryContext) -> float:
        """
        Score a link for prioritization based on contact relevance.
        
        Args:
            url: Absolute URL
            link_text: Text content of the link
            context: Discovery context
            
        Returns:
            Priority score (higher is better)
        """
        score = 0.0
        
        # URL pattern matching
        for pattern in self.CONTACT_URL_PATTERNS:
            if re.search(pattern, url, re.IGNORECASE):
                score += 10.0
        
        # Link text matching
        for keyword in self.CONTACT_KEYWORDS:
            if keyword in link_text:
                score += 5.0
        
        # Language context
        if context.language_preference == 'de':
            german_keywords = ['kontakt', 'impressum', 'vermieter', 'hausverwaltung']
            if any(keyword in link_text for keyword in german_keywords):
                score += 3.0
        
        # Depth penalty
        score -= context.current_depth * 2.0
        
        return max(score, 0.0)
    
    def _should_crawl_link(self, url: str, current_depth: int, context: DiscoveryContext) -> bool:
        """
        Determine if a link should be crawled.
        
        Args:
            url: URL to check
            current_depth: Current crawling depth
            context: Discovery context
            
        Returns:
            True if link should be crawled
        """
        # Check depth limit
        if current_depth >= context.max_depth:
            return False
        
        # Check if already visited
        if url in self.visited_urls:
            return False
        
        # Parse URL
        parsed_url = urlparse(url)
        
        # Check domain restrictions
        if parsed_url.netloc not in context.allowed_domains:
            return False
        
        # Skip ignored file extensions
        if any(parsed_url.path.lower().endswith(ext) for ext in self.IGNORED_EXTENSIONS):
            return False
        
        return True
    
    async def _check_robots_txt(self, url: str) -> bool:
        """
        Check robots.txt compliance for the URL.
        
        Args:
            url: URL to check
            
        Returns:
            True if crawling is allowed
        """
        if not self.settings.respect_robots:
            return True
        
        try:
            parsed_url = urlparse(url)
            domain = parsed_url.netloc
            robots_url = f"{parsed_url.scheme}://{domain}/robots.txt"
            
            # Check cache
            if domain in self.robots_cache:
                robots_parser = self.robots_cache[domain]
            else:
                # Fetch and parse robots.txt
                robots_parser = RobotFileParser()
                robots_parser.set_url(robots_url)
                
                try:
                    robots_parser.read()
                    self.robots_cache[domain] = robots_parser
                except Exception:
                    # If robots.txt can't be fetched, allow crawling
                    return True
            
            # Check if our user agent is allowed
            user_agent = self.config.contact_discovery.user_agent or '*'
            return robots_parser.can_fetch(user_agent, url)
            
        except Exception as e:
            logger.debug(f"Robots.txt check failed for {url}: {e}")
            return True  # Allow crawling on error
    
    async def _enforce_rate_limit(self, url: str) -> None:
        """
        Enforce rate limiting for the domain.
        
        Args:
            url: URL being accessed
        """
        parsed_url = urlparse(url)
        domain = parsed_url.netloc
        
        # Get last access time for this domain
        last_access = self.domain_rate_limits.get(domain, 0)
        current_time = time.time()
        
        # Calculate time since last access
        time_since_last = current_time - last_access
        
        # If we need to wait, sleep for the required time
        if time_since_last < self.settings.rate_limit_seconds:
            sleep_time = self.settings.rate_limit_seconds - time_since_last
            await asyncio.sleep(sleep_time)
        
        # Update last access time
        self.domain_rate_limits[domain] = time.time()
    
    def get_crawl_stats(self) -> CrawlStats:
        """Get current crawling statistics."""
        return self.crawl_stats
    
    def reset_stats(self) -> None:
        """Reset crawling statistics."""
        self.crawl_stats = CrawlStats()
        self.visited_urls.clear()
        self.domain_rate_limits.clear()


class SmartContactCrawler(ContactCrawler):
    """
    Advanced contact crawler with machine learning-based link prioritization.
    
    Features:
    - Machine learning-based link relevance scoring
    - Content analysis for contact likelihood
    - Adaptive crawling strategies
    - Performance optimization
    """
    
    def __init__(self, config: Settings):
        super().__init__(config)
        self.contact_page_classifier = self._initialize_classifier()
    
    def _initialize_classifier(self):
        """Initialize the contact page classifier."""
        # Placeholder for ML classifier - would be implemented with actual ML model
        # For now, use rule-based approach with enhanced heuristics
        return None
    
    def _score_link(self, url: str, link_text: str, context: DiscoveryContext) -> float:
        """
        Enhanced link scoring with content analysis.
        
        Args:
            url: Absolute URL
            link_text: Text content of the link
            context: Discovery context
            
        Returns:
            Priority score (higher is better)
        """
        base_score = super()._score_link(url, link_text, context)
        
        # Enhanced scoring based on content analysis
        enhanced_score = self._enhanced_content_analysis(url, link_text, context)
        
        return base_score + enhanced_score
    
    def _enhanced_content_analysis(self, url: str, link_text: str, context: DiscoveryContext) -> float:
        """
        Perform enhanced content analysis for link scoring.
        
        Args:
            url: URL to analyze
            link_text: Link text content
            context: Discovery context
            
        Returns:
            Additional score from content analysis
        """
        score = 0.0
        
        # Business-related terms in German context
        if context.cultural_context == 'german':
            business_terms = [
                'immobilien', 'verwaltung', 'makler', 'wohnung', 'miete',
                'vermietung', 'hausverwaltung', 'eigentumswohnung', 'miethaus'
            ]
            
            url_text = f"{url} {link_text}".lower()
            for term in business_terms:
                if term in url_text:
                    score += 2.0
        
        # Professional indicators
        professional_terms = ['prof', 'dr', 'dipl', 'ing', 'mba', 'certified']
        for term in professional_terms:
            if term in link_text.lower():
                score += 1.0
        
        return score


# Convenience functions for quick crawling
async def crawl_for_contacts(url: str, config: Settings, context: Optional[DiscoveryContext] = None) -> Tuple[List[Contact], List[ContactForm], CrawlStats]:
    """
    Convenience function to crawl for contacts.
    
    Args:
        url: Starting URL
        config: Application configuration
        context: Discovery context (optional)
        
    Returns:
        Tuple of (contacts, forms, stats)
    """
    async with ContactCrawler(config) as crawler:
        return await crawler.crawl_for_contacts(url, context)


async def smart_crawl_for_contacts(url: str, config: Settings, context: Optional[DiscoveryContext] = None) -> Tuple[List[Contact], List[ContactForm], CrawlStats]:
    """
    Convenience function for smart crawling with enhanced analysis.
    
    Args:
        url: Starting URL
        config: Application configuration
        context: Discovery context (optional)
        
    Returns:
        Tuple of (contacts, forms, stats)
    """
    async with SmartContactCrawler(config) as crawler:
        return await crawler.crawl_for_contacts(url, context)