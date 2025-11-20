"""
Enhanced scoring system for Market Intelligence Contacts.

Provides advanced scoring algorithms specifically designed for market intelligence
features including business context, engagement metrics, and market relevance.
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta

from .market_intelligence import MarketIntelligenceContact, AgencyType, LeadSource
from .scoring import ContactScoringEngine, ScoringFactors


class MarketIntelligenceScoringEngine(ContactScoringEngine):
    """
    Enhanced scoring engine for market intelligence contacts.
    
    Extends the base scoring engine with market-specific factors:
    - Business context and agency type scoring
    - Market area relevance scoring
    - Engagement and outreach effectiveness
    - Data completeness and quality metrics
    - Lead source reliability scoring
    """
    
    # Agency type scoring weights
    AGENCY_TYPE_SCORES = {
        AgencyType.PROPERTY_MANAGER: 0.9,  # High value - direct decision makers
        AgencyType.REAL_ESTATE_AGENT: 0.8,  # Medium value - intermediaries
        AgencyType.LANDLORD: 0.7,  # Lower value - individual owners
        AgencyType.OTHER: 0.5,  # Unknown/other types
    }
    
    # Lead source reliability scores
    LEAD_SOURCE_SCORES = {
        LeadSource.WEB_SCRAPING: 0.8,  # Automated discovery
        LeadSource.PARTNER: 0.9,  # Trusted partnerships
        LeadSource.REFERRAL: 0.95,  # Personal referrals
        LeadSource.MANUAL: 0.7,  # Manual entry
    }
    
    # Market area relevance factors (German market specific)
    MARKET_AREA_RELEVANCE = {
        # Munich areas - high relevance for German market
        'munich center': 0.95, 'schwabing': 0.9, 'maxvorstadt': 0.9,
        'haidhausen': 0.85, 'neuhausen': 0.85, 'glockenbach': 0.85,
        'sendling': 0.8, 'au': 0.8, 'giesing': 0.8,
        
        # Other major German cities
        'berlin': 0.8, 'hamburg': 0.8, 'frankfurt': 0.8,
        'cologne': 0.8, 'stuttgart': 0.8, 'düsseldorf': 0.8,
    }
    
    def __init__(self, config=None):
        """Initialize the market intelligence scoring engine."""
        super().__init__(config)
        self.market_intel_cache = {}
    
    def score_market_intelligence_contact(self, contact: MarketIntelligenceContact, 
                                        context: Optional[Dict[str, Any]] = None) -> float:
        """
        Calculate comprehensive score for market intelligence contact.
        
        Args:
            contact: Market intelligence contact to score
            context: Additional context information
            
        Returns:
            Enhanced confidence score (0.0 - 1.0)
        """
        cache_key = f"mi_{contact.contact_hash}"
        
        if cache_key in self.market_intel_cache:
            return self.market_intel_cache[cache_key]
        
        try:
            # Get base contact score
            base_score = self.score_contact(contact, context)
            
            # Calculate market intelligence factors
            mi_factors = self._calculate_market_intelligence_factors(contact, context)
            
            # Combine scores with weighted approach
            final_score = self._combine_market_intelligence_scores(base_score, mi_factors)
            
            # Cache the result
            self.market_intel_cache[cache_key] = final_score
            
            return final_score
            
        except Exception as e:
            # Fallback to base scoring on error
            return self.score_contact(contact, context)
    
    def _calculate_market_intelligence_factors(self, contact: MarketIntelligenceContact,
                                             context: Optional[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate market intelligence specific scoring factors."""
        factors = {}
        
        # Business context factor
        factors['business_context'] = self._score_business_context(contact)
        
        # Market area relevance factor
        factors['market_relevance'] = self._score_market_relevance(contact)
        
        # Engagement factor
        factors['engagement'] = self._score_engagement(contact)
        
        # Data completeness factor
        factors['data_completeness'] = self._score_data_completeness(contact)
        
        # Lead source reliability factor
        factors['source_reliability'] = self._score_source_reliability(contact)
        
        return factors
    
    def _score_business_context(self, contact: MarketIntelligenceContact) -> float:
        """Score based on business context and agency type."""
        score = 0.5  # Base score
        
        # Agency type scoring
        if contact.agency_type:
            score = self.AGENCY_TYPE_SCORES.get(contact.agency_type, 0.5)
        
        # Company name presence
        if contact.company_name:
            score += 0.1
        
        # Position title presence
        if contact.position:
            score += 0.1
        
        # Professional indicators in company/position
        professional_terms = ['immobilien', 'property', 'real estate', 'verwaltung', 'management']
        text_to_check = f"{contact.company_name or ''} {contact.position or ''}".lower()
        
        for term in professional_terms:
            if term in text_to_check:
                score += 0.05
        
        return min(score, 1.0)
    
    def _score_market_relevance(self, contact: MarketIntelligenceContact) -> float:
        """Score based on market area relevance."""
        if not contact.market_areas:
            return 0.3  # Low score for no market areas
        
        # Calculate average relevance across all market areas
        total_relevance = 0.0
        valid_areas = 0
        
        for area in contact.market_areas:
            area_lower = area.lower()
            
            # Check exact matches first
            if area_lower in self.MARKET_AREA_RELEVANCE:
                total_relevance += self.MARKET_AREA_RELEVANCE[area_lower]
                valid_areas += 1
            else:
                # Check partial matches
                for known_area, relevance in self.MARKET_AREA_RELEVANCE.items():
                    if known_area in area_lower or area_lower in known_area:
                        total_relevance += relevance * 0.8  # Partial match penalty
                        valid_areas += 1
                        break
        
        if valid_areas > 0:
            return total_relevance / valid_areas
        else:
            return 0.3  # Default for unrecognized areas
    
    def _score_engagement(self, contact: MarketIntelligenceContact) -> float:
        """Score based on engagement metrics."""
        engagement_score = contact.calculate_engagement_score()
        
        # Additional engagement factors
        if contact.last_contacted:
            days_since_contact = (datetime.now() - contact.last_contacted).days
            
            # Recent contact bonus
            if days_since_contact <= 7:
                engagement_score += 0.2
            elif days_since_contact <= 30:
                engagement_score += 0.1
        
        # Outreach frequency factor
        total_outreach = len(contact.outreach_history)
        if total_outreach >= 5:
            engagement_score += 0.1
        elif total_outreach >= 2:
            engagement_score += 0.05
        
        return min(engagement_score, 1.0)
    
    def _score_data_completeness(self, contact: MarketIntelligenceContact) -> float:
        """Score based on data completeness."""
        completeness_score = 0.0
        
        # Basic contact info (inherited from base contact)
        if contact.value:
            completeness_score += 0.2
        
        # Market intelligence fields
        required_fields = [
            ('position', 0.15),
            ('company_name', 0.15),
            ('agency_type', 0.15),
            ('market_areas', 0.15),
            ('preferred_contact_method', 0.1),
            ('tags', 0.1),
        ]
        
        for field_name, weight in required_fields:
            if getattr(contact, field_name):
                completeness_score += weight
        
        return completeness_score
    
    def _score_source_reliability(self, contact: MarketIntelligenceContact) -> float:
        """Score based on lead source reliability."""
        if contact.lead_source:
            return self.LEAD_SOURCE_SCORES.get(contact.lead_source, 0.5)
        
        # Fallback to extraction method if no lead source
        if contact.extraction_method:
            method_scores = {
                'html_scrape': 0.7,
                'api': 0.9,
                'ocr': 0.6,
                'manual_entry': 0.8,
            }
            return method_scores.get(contact.extraction_method, 0.5)
        
        return 0.5  # Default score
    
    def _combine_market_intelligence_scores(self, base_score: float, 
                                          mi_factors: Dict[str, float]) -> float:
        """Combine base score with market intelligence factors."""
        # Weight factors for final combination
        weights = {
            'base_score': 0.4,  # Base contact scoring
            'business_context': 0.2,
            'market_relevance': 0.15,
            'engagement': 0.1,
            'data_completeness': 0.1,
            'source_reliability': 0.05,
        }
        
        # Calculate weighted sum
        weighted_sum = base_score * weights['base_score']
        
        for factor_name, factor_score in mi_factors.items():
            if factor_name in weights:
                weighted_sum += factor_score * weights[factor_name]
        
        return min(weighted_sum, 1.0)
    
    def get_market_intelligence_scoring_explanation(self, contact: MarketIntelligenceContact,
                                                  context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Get detailed explanation of market intelligence scoring.
        
        Args:
            contact: Market intelligence contact to explain
            context: Additional context information
            
        Returns:
            Dictionary with detailed scoring explanation
        """
        base_score = self.score_contact(contact, context)
        mi_factors = self._calculate_market_intelligence_factors(contact, context)
        final_score = self._combine_market_intelligence_scores(base_score, mi_factors)
        
        explanation = {
            'final_score': final_score,
            'base_contact_score': base_score,
            'market_intelligence_factors': {},
            'weight_breakdown': {},
            'recommendations': []
        }
        
        # Factor explanations
        for factor_name, factor_score in mi_factors.items():
            explanation['market_intelligence_factors'][factor_name] = {
                'score': factor_score,
                'explanation': self._get_factor_explanation(factor_name, contact, factor_score)
            }
        
        # Weight breakdown
        weights = {
            'base_contact_score': 0.4,
            'business_context': 0.2,
            'market_relevance': 0.15,
            'engagement': 0.1,
            'data_completeness': 0.1,
            'source_reliability': 0.05,
        }
        
        explanation['weight_breakdown'] = weights
        
        # Recommendations
        explanation['recommendations'] = self._generate_mi_recommendations(contact, mi_factors)
        
        return explanation
    
    def _get_factor_explanation(self, factor_name: str, contact: MarketIntelligenceContact,
                              factor_score: float) -> str:
        """Get human-readable explanation for a scoring factor."""
        explanations = {
            'business_context': f"Business context score based on agency type ({contact.agency_type}), company name, and position",
            'market_relevance': f"Market relevance score based on {len(contact.market_areas)} market areas",
            'engagement': f"Engagement score based on {len(contact.outreach_history)} outreach attempts",
            'data_completeness': "Data completeness score based on filled market intelligence fields",
            'source_reliability': f"Source reliability score based on lead source ({contact.lead_source})"
        }
        
        return explanations.get(factor_name, f"{factor_name} scoring factor")
    
    def _generate_mi_recommendations(self, contact: MarketIntelligenceContact,
                                   mi_factors: Dict[str, float]) -> List[str]:
        """Generate recommendations for improving market intelligence score."""
        recommendations = []
        
        # Business context recommendations
        if mi_factors.get('business_context', 0) < 0.6:
            if not contact.agency_type:
                recommendations.append("Specify agency type for better business context")
            if not contact.company_name:
                recommendations.append("Add company name for business identification")
        
        # Market relevance recommendations
        if mi_factors.get('market_relevance', 0) < 0.6:
            if not contact.market_areas:
                recommendations.append("Add market areas for geographic targeting")
            else:
                recommendations.append("Consider adding more specific market areas")
        
        # Engagement recommendations
        if mi_factors.get('engagement', 0) < 0.5:
            if not contact.outreach_history:
                recommendations.append("Start outreach to build engagement history")
            else:
                recommendations.append("Increase outreach frequency for better engagement")
        
        # Data completeness recommendations
        if mi_factors.get('data_completeness', 0) < 0.7:
            recommendations.append("Complete missing market intelligence fields")
        
        return recommendations


# Convenience functions for market intelligence scoring
def score_market_intelligence_contact(contact: MarketIntelligenceContact,
                                    context: Optional[Dict[str, Any]] = None) -> float:
    """Quick function to score a market intelligence contact."""
    engine = MarketIntelligenceScoringEngine()
    return engine.score_market_intelligence_contact(contact, context)


def get_market_intelligence_scoring_explanation(contact: MarketIntelligenceContact,
                                              context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Quick function to get market intelligence scoring explanation."""
    engine = MarketIntelligenceScoringEngine()
    return engine.get_market_intelligence_scoring_explanation(contact, context)