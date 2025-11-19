"""
API Middleware Package

Provides middleware components for the MWA Core API:
- Rate limiting middleware
- Security headers middleware
- Authentication middleware
"""

from .rate_limiter import (
    RateLimitMiddleware,
    RateLimitConfig,
    AdaptiveRateLimitMiddleware,
    create_rate_limiter,
    RATE_LIMIT_CONFIGS
)

from .security_headers import (
    SecurityHeadersMiddleware,
    SecurityHeadersConfig,
    CORSMiddleware,
    create_security_middleware,
    get_production_security_config,
    SECURITY_CONFIGS
)

__all__ = [
    # Rate Limiting
    "RateLimitMiddleware",
    "RateLimitConfig", 
    "AdaptiveRateLimitMiddleware",
    "create_rate_limiter",
    "RATE_LIMIT_CONFIGS",
    
    # Security Headers
    "SecurityHeadersMiddleware",
    "SecurityHeadersConfig",
    "CORSMiddleware",
    "create_security_middleware",
    "get_production_security_config",
    "SECURITY_CONFIGS"
]