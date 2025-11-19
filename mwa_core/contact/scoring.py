"""
Advanced confidence scoring system for contact discovery.

Provides sophisticated scoring algorithms for different types of contact information:
- Email confidence scoring based on format, domain, and context
- Phone number scoring with format validation and cultural context
- Form scoring based on complexity and user-friendliness
- Social media profile scoring with platform-specific factors
- Overall contact reliability scoring
"""

import re
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
from urllib.parse import urlparse

from .models import Contact, ContactForm, SocialMediaProfile, ConfidenceLevel, ContactStatus, ContactMethod

logger = logging.getLogger(__name__)


@dataclass
class ScoringFactors:
    """Factors used in contact scoring."""
    format_validity: float = 0.0
    domain_reputation: float = 0.0
    contextual_relevance: float = 0.0
    extraction_method: float = 0.0
    cultural_fit: float = 0.0
    verification_status: float = 0.0
    historical_performance: float = 0.0


class ContactScoringEngine:
    """
    Advanced scoring engine for contact discovery results.
    
    Provides multi-factor scoring based on:
    - Format validation and syntax checking
    - Domain reputation and trustworthiness
    - Contextual relevance to real estate/property management
    - Cultural and geographic context fitting
    - Extraction method reliability
    - Historical performance data
    """
    
    # Domain reputation scores (0-1)
    DOMAIN_REPUTATION = {
        # High-reputation German email providers
        'gmx.de': 0.9, 'gmx.net': 0.9, 'web.de': 0.9, 't-online.de': 0.9,
        'freenet.de': 0.8, 'yahoo.de': 0.8, 'hotmail.de': 0.8, 'outlook.de': 0.8,
        
        # International providers
        'gmail.com': 0.7, 'googlemail.com': 0.7, 'yahoo.com': 0.6,
        'hotmail.com': 0.6, 'outlook.com': 0.6, 'live.com': 0.6,
        
        # Business-related domains (high value)
        'immobilien': 0.95, 'verwaltung': 0.95, 'makler': 0.95,
        'realtor': 0.9, 'estate': 0.9, 'property': 0.9,
        'management': 0.85, 'agency': 0.85, 'broker': 0.85,
    }
    
    # Extraction method reliability scores
    EXTRACTION_METHOD_SCORES = {
        'mailto_link': 0.95,
        'standard_pattern': 0.8,
        'obfuscated_text': 0.7,
        'ocr_extracted': 0.6,
        'pdf_extracted': 0.7,
        'social_media': 0.75,
        'form_detection': 0.65,
    }
    
    # Cultural context scores for German market
    GERMAN_CONTEXT_SCORES = {
        'munich_area_code': 0.9,  # 089
        'german_mobile': 0.85,    # +49 15/16/17
        'german_landline': 0.8,   # +49 with valid area code
        'german_email_domain': 0.85,
        'german_social_platform': 0.8,  # XING
    }
    
    def __init__(self, config=None):
        """Initialize the scoring engine."""
        self.config = config
        self.scoring_cache = {}
        self.performance_history = {}
    
    def score_contact(self, contact: Contact, context: Optional[Dict[str, Any]] = None) -> float:
        """
        Calculate comprehensive confidence score for a contact.
        
        Args:
            contact: Contact to score
            context: Additional context information
            
        Returns:
            Confidence score (0.0 - 1.0)
        """
        cache_key = f"{contact.contact_hash}_{contact.verification_status}"
        
        if cache_key in self.scoring_cache:
            return self.scoring_cache[cache_key]
        
        try:
            factors = self._calculate_scoring_factors(contact, context)
            score = self._combine_factors(factors)
            
            # Cache the result
            self.scoring_cache[cache_key] = score
            
            # Update performance history
            self._update_performance_history(contact, score)
            
            return score
            
        except Exception as e:
            logger.error(f"Error scoring contact {contact.value}: {e}")
            return 0.3  # Default low score on error
    
    def score_batch(self, contacts: List[Contact], context: Optional[Dict[str, Any]] = None) -> List[Tuple[Contact, float]]:
        """
        Score a batch of contacts efficiently.
        
        Args:
            contacts: List of contacts to score
            context: Additional context information
            
        Returns:
            List of (contact, score) tuples
        """
        results = []
        
        for contact in contacts:
            score = self.score_contact(contact, context)
            results.append((contact, score))
        
        return results
    
    def _calculate_scoring_factors(self, contact: Contact, context: Optional[Dict[str, Any]]) -> ScoringFactors:
        """Calculate individual scoring factors."""
        factors = ScoringFactors()
        
        # Format validity scoring
        factors.format_validity = self._score_format_validity(contact)
        
        # Domain reputation scoring
        factors.domain_reputation = self._score_domain_reputation(contact)
        
        # Contextual relevance scoring
        factors.contextual_relevance = self._score_contextual_relevance(contact, context)
        
        # Extraction method scoring
        factors.extraction_method = self._score_extraction_method(contact)
        
        # Cultural fit scoring
        factors.cultural_fit = self._score_cultural_fit(contact, context)
        
        # Verification status scoring
        factors.verification_status = self._score_verification_status(contact)
        
        # Historical performance scoring
        factors.historical_performance = self._score_historical_performance(contact)
        
        return factors
    
    def _score_format_validity(self, contact: Contact) -> float:
        """Score based on format validity."""
        if contact.method == ContactMethod.EMAIL:
            return self._score_email_format(contact.value)
        elif contact.method == ContactMethod.PHONE:
            return self._score_phone_format(contact.value)
        elif contact.method == ContactMethod.WEBSITE:
            return self._score_website_format(contact.value)
        elif contact.method == ContactMethod.SOCIAL_MEDIA:
            return self._score_social_format(contact.value)
        else:
            return 0.5
    
    def _score_email_format(self, email: str) -> float:
        """Score email format validity."""
        # Basic format check
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return 0.1
        
        # Length checks
        if len(email) > 254 or len(email.split('@')[0]) > 64:
            return 0.2
        
        # Local part validation
        local_part = email.split('@')[0]
        if not local_part or local_part.startswith('.') or local_part.endswith('.'):
            return 0.3
        
        # Domain validation
        domain = email.split('@')[1]
        if domain.count('.') == 0 or domain.startswith('.') or domain.endswith('.'):
            return 0.3
        
        # Suspicious patterns
        suspicious_patterns = ['noreply', 'no-reply', 'donotreply', 'test', 'example']
        if any(pattern in email.lower() for pattern in suspicious_patterns):
            return 0.4
        
        return 0.9
    
    def _score_phone_format(self, phone: str) -> float:
        """Score phone number format validity."""
        # Remove formatting characters
        clean_phone = re.sub(r'[^\d+]', '', phone)
        
        # Length validation
        if len(clean_phone) < 6 or len(clean_phone) > 16:
            return 0.2
        
        # International format check
        if phone.startswith('+'):
            # Must have country code
            country_code_match = re.match(r'^\+(\d{1,3})', phone)
            if not country_code_match:
                return 0.3
            
            # Valid country code ranges
            country_code = int(country_code_match.group(1))
            if country_code < 1 or country_code > 999:
                return 0.3
        
        # German-specific validation
        if clean_phone.startswith('49') or clean_phone.startswith('0049'):
            # Valid German number format
            if len(clean_phone) >= 10 and len(clean_phone) <= 13:
                return 0.9
        
        # Munich area code validation
        if '089' in clean_phone:
            return 0.95
        
        return 0.7
    
    def _score_website_format(self, website: str) -> float:
        """Score website format validity."""
        try:
            parsed = urlparse(website)
            
            # Basic URL structure
            if not parsed.scheme or not parsed.netloc:
                return 0.2
            
            # Valid scheme
            if parsed.scheme not in ['http', 'https']:
                return 0.3
            
            # Domain validation
            if '.' not in parsed.netloc:
                return 0.3
            
            # Suspicious TLDs
            suspicious_tlds = ['.tk', '.ml', '.ga', '.cf']
            if any(parsed.netloc.endswith(tld) for tld in suspicious_tlds):
                return 0.4
            
            return 0.85
        
        except Exception:
            return 0.2
    
    def _score_social_format(self, social_url: str) -> float:
        """Score social media URL format validity."""
        try:
            parsed = urlparse(social_url)
            
            # Basic validation
            if not parsed.scheme or not parsed.netloc:
                return 0.2
            
            # Platform-specific validation
            platform_domains = {
                'facebook.com': r'/([a-zA-Z0-9._-]+)',
                'instagram.com': r'/([a-zA-Z0-9._-]+)',
                'twitter.com': r'/([a-zA-Z0-9._-]+)',
                'linkedin.com': r'/in/([a-zA-Z0-9._-]+)',
                'xing.com': r'/profile/([a-zA-Z0-9._-]+)',
            }
            
            for domain, pattern in platform_domains.items():
                if domain in parsed.netloc:
                    if re.search(pattern, parsed.path):
                        return 0.9
                    else:
                        return 0.4
            
            return 0.6
        
        except Exception:
            return 0.2
    
    def _score_domain_reputation(self, contact: Contact) -> float:
        """Score based on domain reputation."""
        domain = contact.domain
        if not domain:
            return 0.5
        
        # Check exact domain matches
        if domain in self.DOMAIN_REPUTATION:
            return self.DOMAIN_REPUTATION[domain]
        
        # Check partial matches (for subdomains)
        for key, score in self.DOMAIN_REPUTATION.items():
            if key in domain:
                return score * 0.9  # Slight penalty for subdomains
        
        # Check for business-related keywords in domain
        business_keywords = ['immobilien', 'verwaltung', 'makler', 'realtor', 'estate']
        for keyword in business_keywords:
            if keyword in domain.lower():
                return 0.85
        
        # Default score for unknown domains
        return 0.6
    
    def _score_contextual_relevance(self, contact: Contact, context: Optional[Dict[str, Any]]) -> float:
        """Score based on contextual relevance to real estate."""
        score = 0.5  # Base score
        
        # Source URL analysis
        if contact.source_url:
            parsed_source = urlparse(contact.source_url)
            source_path = parsed_source.path.lower()
            
            # Real estate related paths
            real_estate_paths = [
                'immobilien', 'wohnung', 'miete', 'vermietung', 'kaufen',
                'property', 'apartment', 'rent', 'sale', 'real-estate'
            ]
            
            for path_keyword in real_estate_paths:
                if path_keyword in source_path:
                    score += 0.2
            
            # Contact page indicators
            contact_paths = ['kontakt', 'contact', 'impressum', 'about']
            for contact_keyword in contact_paths:
                if contact_keyword in source_path:
                    score += 0.15
        
        # Discovery path analysis
        if contact.discovery_path:
            for path in contact.discovery_path:
                if any(keyword in path.lower() for keyword in ['contact', 'kontakt', 'impressum']):
                    score += 0.1
        
        # Metadata analysis
        if contact.metadata:
            # Check for real estate related metadata
            if any(keyword in str(contact.metadata).lower() for keyword in ['immobilien', 'property', 'real estate']):
                score += 0.1
            
            # Check for contact-related metadata
            if 'contact' in str(contact.metadata).lower() or 'kontakt' in str(contact.metadata).lower():
                score += 0.1
        
        return min(score, 1.0)
    
    def _score_extraction_method(self, contact: Contact) -> float:
        """Score based on extraction method reliability."""
        method = contact.extraction_method
        
        if method in self.EXTRACTION_METHOD_SCORES:
            return self.EXTRACTION_METHOD_SCORES[method]
        
        # Default scores for unknown methods
        return 0.5
    
    def _score_cultural_fit(self, contact: Contact, context: Optional[Dict[str, Any]]) -> float:
        """Score based on cultural and geographic fit."""
        score = 0.5  # Base score
        
        # German market specific scoring
        if context and context.get('cultural_context') == 'german':
            # Email domain scoring
            if contact.method == ContactMethod.EMAIL and contact.domain:
                german_domains = ['gmx.de', 'gmx.net', 'web.de', 't-online.de', 'freenet.de']
                if any(domain in contact.domain for domain in german_domains):
                    score += 0.3
            
            # Phone number scoring
            elif contact.method == ContactMethod.PHONE:
                if '089' in contact.value:  # Munich area code
                    score += 0.4
                elif contact.value.startswith('+49') or contact.value.startswith('0049'):
                    score += 0.3
            
            # Social media platform scoring
            elif contact.method == ContactMethod.SOCIAL_MEDIA:
                if 'xing.com' in contact.value:
                    score += 0.3  # XING is popular in German-speaking countries
        
        # Language preference scoring
        if context and context.get('language_preference') == 'de':
            if contact.language == 'de':
                score += 0.2
        
        return min(score, 1.0)
    
    def _score_verification_status(self, contact: Contact) -> float:
        """Score based on verification status."""
        if contact.verification_status == ContactStatus.VERIFIED:
            return 1.0
        elif contact.verification_status == ContactStatus.INVALID:
            return 0.1
        elif contact.verification_status == ContactStatus.SUSPICIOUS:
            return 0.3
        elif contact.verification_status == ContactStatus.FLAGGED:
            return 0.2
        else:  # UNVERIFIED
            return 0.6
    
    def _score_historical_performance(self, contact: Contact) -> float:
        """Score based on historical performance of similar contacts."""
        # This would be implemented with actual historical data
        # For now, return neutral score
        return 0.5
    
    def _combine_factors(self, factors: ScoringFactors) -> float:
        """Combine individual scoring factors into final score."""
        # Weighted combination of factors
        weights = {
            'format_validity': 0.25,
            'domain_reputation': 0.20,
            'contextual_relevance': 0.20,
            'extraction_method': 0.15,
            'cultural_fit': 0.10,
            'verification_status': 0.05,
            'historical_performance': 0.05,
        }
        
        weighted_sum = (
            factors.format_validity * weights['format_validity'] +
            factors.domain_reputation * weights['domain_reputation'] +
            factors.contextual_relevance * weights['contextual_relevance'] +
            factors.extraction_method * weights['extraction_method'] +
            factors.cultural_fit * weights['cultural_fit'] +
            factors.verification_status * weights['verification_status'] +
            factors.historical_performance * weights['historical_performance']
        )
        
        return min(weighted_sum, 1.0)
    
    def _update_performance_history(self, contact: Contact, score: float) -> None:
        """Update performance history for future scoring."""
        # Store performance data for future use
        key = f"{contact.method.value}_{contact.domain or 'unknown'}"
        
        if key not in self.performance_history:
            self.performance_history[key] = []
        
        self.performance_history[key].append({
            'score': score,
            'timestamp': datetime.now(),
            'verification_status': contact.verification_status.value
        })
        
        # Keep only recent history (last 100 entries)
        if len(self.performance_history[key]) > 100:
            self.performance_history[key] = self.performance_history[key][-100:]
    
    def convert_to_confidence_level(self, score: float) -> ConfidenceLevel:
        """Convert numeric score to confidence level."""
        if score >= 0.8:
            return ConfidenceLevel.HIGH
        elif score >= 0.6:
            return ConfidenceLevel.MEDIUM
        elif score >= 0.4:
            return ConfidenceLevel.LOW
        else:
            return ConfidenceLevel.UNCERTAIN
    
    def score_contact_form(self, form: ContactForm, context: Optional[Dict[str, Any]] = None) -> float:
        """
        Score a contact form based on various factors.
        
        Args:
            form: Contact form to score
            context: Additional context information
            
        Returns:
            Confidence score (0.0 - 1.0)
        """
        score = 0.5  # Base score
        
        # Required field presence
        if form.has_email_field and form.has_message_field:
            score += 0.3
        elif form.has_email_field:
            score += 0.2
        
        # Complexity scoring (lower complexity is better for contact forms)
        complexity_penalty = form.complexity_score * 0.2
        score -= complexity_penalty
        
        # User-friendliness scoring
        score += form.user_friendly_score * 0.2
        
        # Field count scoring (optimal is 3-5 fields)
        field_count = len(form.fields)
        if 3 <= field_count <= 5:
            score += 0.1
        elif field_count > 8:
            score -= 0.1
        
        # CSRF token presence (security indicator)
        if form.csrf_token:
            score += 0.05
        
        return max(min(score, 1.0), 0.0)
    
    def score_social_media_profile(self, profile: SocialMediaProfile, context: Optional[Dict[str, Any]] = None) -> float:
        """
        Score a social media profile based on various factors.
        
        Args:
            profile: Social media profile to score
            context: Additional context information
            
        Returns:
            Confidence score (0.0 - 1.0)
        """
        score = 0.6  # Base score for social media
        
        # Platform-specific scoring
        platform_scores = {
            'linkedin': 0.9,
            'xing': 0.9,
            'facebook': 0.7,
            'instagram': 0.6,
            'twitter': 0.6,
            'whatsapp': 0.8,
            'telegram': 0.7,
        }
        
        platform_key = profile.platform.value.lower()
        if platform_key in platform_scores:
            score = platform_scores[platform_key]
        
        # Business profile scoring
        if profile.is_business_profile:
            score += 0.1
        
        # Username quality scoring
        username = profile.username.lower()
        
        # Professional indicators
        professional_terms = ['immobilien', 'verwaltung', 'makler', 'property', 'realty']
        for term in professional_terms:
            if term in username:
                score += 0.1
        
        # Spam indicators (reduce score)
        spam_indicators = ['123', 'xxx', 'spam', 'test']
        for indicator in spam_indicators:
            if indicator in username:
                score -= 0.1
        
        return max(min(score, 1.0), 0.0)
    
    def get_scoring_explanation(self, contact: Contact) -> Dict[str, Any]:
        """
        Get detailed explanation of how a contact was scored.
        
        Args:
            contact: Contact to explain
            
        Returns:
            Dictionary with scoring explanation
        """
        factors = self._calculate_scoring_factors(contact)
        final_score = self._combine_factors(factors)
        
        return {
            'final_score': final_score,
            'confidence_level': self.convert_to_confidence_level(final_score).value,
            'factors': {
                'format_validity': {
                    'score': factors.format_validity,
                    'weight': 0.25,
                    'contribution': factors.format_validity * 0.25
                },
                'domain_reputation': {
                    'score': factors.domain_reputation,
                    'weight': 0.20,
                    'contribution': factors.domain_reputation * 0.20
                },
                'contextual_relevance': {
                    'score': factors.contextual_relevance,
                    'weight': 0.20,
                    'contribution': factors.contextual_relevance * 0.20
                },
                'extraction_method': {
                    'score': factors.extraction_method,
                    'weight': 0.15,
                    'contribution': factors.extraction_method * 0.15
                },
                'cultural_fit': {
                    'score': factors.cultural_fit,
                    'weight': 0.10,
                    'contribution': factors.cultural_fit * 0.10
                },
                'verification_status': {
                    'score': factors.verification_status,
                    'weight': 0.05,
                    'contribution': factors.verification_status * 0.05
                },
                'historical_performance': {
                    'score': factors.historical_performance,
                    'weight': 0.05,
                    'contribution': factors.historical_performance * 0.05
                }
            },
            'recommendations': self._generate_scoring_recommendations(factors)
        }
    
    def _generate_scoring_recommendations(self, factors: ScoringFactors) -> List[str]:
        """Generate recommendations for improving contact quality."""
        recommendations = []
        
        if factors.format_validity < 0.5:
            recommendations.append("Improve format validation - contact appears to have syntax issues")
        
        if factors.domain_reputation < 0.5:
            recommendations.append("Domain has low reputation - consider additional verification")
        
        if factors.contextual_relevance < 0.5:
            recommendations.append("Low contextual relevance - contact may not be business-related")
        
        if factors.extraction_method < 0.5:
            recommendations.append("Consider using more reliable extraction methods")
        
        if factors.cultural_fit < 0.5:
            recommendations.append("Contact may not be suitable for target market")
        
        if factors.verification_status < 0.5:
            recommendations.append("Contact verification failed - review validation process")
        
        if not recommendations:
            recommendations.append("Contact quality appears good")
        
        return recommendations


# Convenience functions for quick scoring
def score_contact(contact: Contact, context: Optional[Dict[str, Any]] = None) -> float:
    """Quick function to score a single contact."""
    engine = ContactScoringEngine()
    return engine.score_contact(contact, context)


def score_contacts_batch(contacts: List[Contact], context: Optional[Dict[str, Any]] = None) -> List[Tuple[Contact, float]]:
    """Quick function to score multiple contacts."""
    engine = ContactScoringEngine()
    return engine.score_batch(contacts, context)


def get_contact_confidence_level(contact: Contact, context: Optional[Dict[str, Any]] = None) -> ConfidenceLevel:
    """Get confidence level for a contact."""
    engine = ContactScoringEngine()
    score = engine.score_contact(contact, context)
    return engine.convert_to_confidence_level(score)