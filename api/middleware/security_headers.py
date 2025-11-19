"""
Security headers middleware for FastAPI applications.

Provides comprehensive security headers implementation:
- HTTP Strict Transport Security (HSTS)
- Content Security Policy (CSP)
- X-Frame-Options for clickjacking protection
- X-Content-Type-Options for MIME-type sniffing protection
- X-XSS-Protection for cross-site scripting protection
- Referrer Policy for privacy protection
- Permissions Policy for feature access control
"""

import logging
from typing import Dict, List, Optional, Set, Any
from datetime import timedelta
from urllib.parse import urlparse

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class SecurityHeadersConfig:
    """Configuration for security headers middleware."""
    
    def __init__(
        self,
        hsts_max_age: int = 31536000,  # 1 year
        hsts_include_subdomains: bool = True,
        hsts_preload: bool = False,
        csp_enabled: bool = True,
        csp_directives: Optional[Dict[str, str]] = None,
        frame_options: str = "DENY",
        content_type_options: str = "nosniff",
        xss_protection: str = "1; mode=block",
        referrer_policy: str = "strict-origin-when-cross-origin",
        permissions_policy: Optional[Dict[str, str]] = None,
        allowed_origins: Optional[Set[str]] = None,
        allowed_methods: Optional[Set[str]] = None,
        allowed_headers: Optional[Set[str]] = None,
        allow_credentials: bool = True,
        max_age: Optional[int] = 86400  # 24 hours
    ):
        # HSTS configuration
        self.hsts_max_age = hsts_max_age
        self.hsts_include_subdomains = hsts_include_subdomains
        self.hsts_preload = hsts_preload
        
        # CSP configuration
        self.csp_enabled = csp_enabled
        self.csp_directives = csp_directives or self._get_default_csp_directives()
        
        # Other security headers
        self.frame_options = frame_options.upper()
        self.content_type_options = content_type_options
        self.xss_protection = xss_protection
        self.referrer_policy = referrer_policy
        self.permissions_policy = permissions_policy or {}
        
        # CORS configuration
        self.allowed_origins = allowed_origins or set()
        self.allowed_methods = allowed_methods or {"GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"}
        self.allowed_headers = allowed_headers or {
            "Authorization",
            "Content-Type",
            "X-Requested-With",
            "Accept",
            "Origin",
            "User-Agent",
            "DNT",
            "Cache-Control",
            "X-Mx-ReqToken",
            "Keep-Alive",
            "X-Requested-With",
            "If-Modified-Since"
        }
        self.allow_credentials = allow_credentials
        self.max_age = max_age
    
    def _get_default_csp_directives(self) -> Dict[str, str]:
        """Get default Content Security Policy directives."""
        return {
            "default-src": "'self'",
            "script-src": "'self' 'unsafe-inline' 'unsafe-eval'",
            "style-src": "'self' 'unsafe-inline'",
            "img-src": "'self' data: https:",
            "font-src": "'self'",
            "connect-src": "'self' wss:",
            "frame-src": "'none'",
            "object-src": "'none'",
            "media-src": "'self'",
            "child-src": "'none'",
            "form-action": "'self'",
            "base-uri": "'self'",
            "manifest-src": "'self'",
            "worker-src": "'self'",
            "upgrade-insecure-requests": ""
        }


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Comprehensive security headers middleware."""
    
    def __init__(
        self,
        app: ASGIApp,
        config: Optional[SecurityHeadersConfig] = None
    ):
        super().__init__(app)
        self.config = config or SecurityHeadersConfig()
    
    async def dispatch(self, request: Request, call_next) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        
        # Add HSTS header (only for HTTPS requests)
        if request.url.scheme == "https":
            hsts_value = f"max-age={self.config.hsts_max_age}"
            if self.config.hsts_include_subdomains:
                hsts_value += "; includeSubDomains"
            if self.config.hsts_preload:
                hsts_value += "; preload"
            response.headers["Strict-Transport-Security"] = hsts_value
        
        # Add Content Security Policy
        if self.config.csp_enabled:
            csp_value = self._build_csp_value()
            response.headers["Content-Security-Policy"] = csp_value
        
        # Add other security headers
        response.headers["X-Frame-Options"] = self.config.frame_options
        response.headers["X-Content-Type-Options"] = self.config.content_type_options
        response.headers["X-XSS-Protection"] = self.config.xss_protection
        response.headers["Referrer-Policy"] = self.config.referrer_policy
        
        # Add Permissions Policy
        if self.config.permissions_policy:
            permissions_value = self._build_permissions_value()
            response.headers["Permissions-Policy"] = permissions_value
        
        # Add custom security headers
        response.headers["X-Permitted-Cross-Domain-Policies"] = "none"
        response.headers["X-Download-Options"] = "noopen"
        
        return response
    
    def _build_csp_value(self) -> str:
        """Build Content Security Policy header value."""
        directives = []
        for directive, value in self.config.csp_directives.items():
            if value:
                directives.append(f"{directive} {value}")
            else:
                directives.append(directive)
        return "; ".join(directives)
    
    def _build_permissions_value(self) -> str:
        """Build Permissions Policy header value."""
        policies = []
        for feature, policy in self.config.permissions_policy.items():
            policies.append(f"{feature}={policy}")
        return ", ".join(policies)
    
    def validate_origin(self, origin: str, request_origin: str) -> bool:
        """Validate if request origin is allowed."""
        if not self.config.allowed_origins:
            return True
        
        # Check exact match
        if request_origin in self.config.allowed_origins:
            return True
        
        # Check wildcard matches
        for allowed_origin in self.config.allowed_origins:
            if allowed_origin.startswith("*."):
                domain = allowed_origin[2:]
                if request_origin.endswith("." + domain) or request_origin == domain:
                    return True
        
        # Check protocol-relative URLs
        if origin.startswith("//"):
            return origin[2:] in self.config.allowed_origins
        
        return False
    
    def is_https_only_endpoint(self, path: str) -> bool:
        """Check if endpoint should only be accessible via HTTPS."""
        https_only_paths = {
            "/api/v1/auth/login",
            "/api/v1/auth/refresh",
            "/api/v1/auth/change-password",
            "/api/v1/config",
            "/api/v1/websocket/connect"
        }
        return path in https_only_paths


class CORSMiddleware:
    """Enhanced CORS middleware with better security."""
    
    def __init__(self, config: SecurityHeadersConfig):
        self.config = config
    
    def preflight_request(self, request: Request) -> Optional[Response]:
        """Handle CORS preflight requests."""
        if request.method != "OPTIONS":
            return None
        
        origin = request.headers.get("Origin")
        access_control_request_method = request.headers.get("Access-Control-Request-Method")
        access_control_request_headers = request.headers.get("Access-Control-Request-Headers")
        
        response = JSONResponse({"message": "OK"})
        response.status_code = 200
        
        # Add CORS headers
        if origin and self.config.allowed_origins:
            if self.validate_origin("", origin):
                response.headers["Access-Control-Allow-Origin"] = origin
        
        response.headers["Access-Control-Allow-Methods"] = ", ".join(sorted(self.config.allowed_methods))
        
        if access_control_request_headers:
            headers = self._get_allowed_headers(access_control_request_headers)
            response.headers["Access-Control-Allow-Headers"] = headers
        
        if self.config.allow_credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        if self.config.max_age:
            response.headers["Access-Control-Max-Age"] = str(self.config.max_age)
        
        response.headers["Access-Control-Allow-Private-Network"] = "true"
        
        return response
    
    def _get_allowed_headers(self, requested_headers: str) -> str:
        """Get allowed headers for CORS."""
        requested_headers_set = set(header.strip() for header in requested_headers.split(","))
        allowed_headers = self.config.allowed_headers.intersection(requested_headers_set)
        
        # Always allow some essential headers
        allowed_headers.update({"Content-Type", "Authorization"})
        
        return ", ".join(sorted(allowed_headers))
    
    def add_cors_headers(self, response: Response, request: Request) -> None:
        """Add CORS headers to response."""
        origin = request.headers.get("Origin")
        
        if origin and self.config.allowed_origins:
            if self.validate_origin("", origin):
                response.headers["Access-Control-Allow-Origin"] = origin
        
        if self.config.allow_credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        # Add vary header for cache management
        response.headers["Vary"] = "Origin"


# Predefined security configurations
SECURITY_CONFIGS = {
    "development": SecurityHeadersConfig(
        csp_enabled=False,  # Disable CSP for development
        hsts_max_age=0,     # Disable HSTS for development
        allowed_origins={
            "http://localhost:3000",
            "http://localhost:8000",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8000",
            "ws://localhost:3000",
            "ws://localhost:8000"
        }
    ),
    
    "staging": SecurityHeadersConfig(
        hsts_max_age=86400,  # 1 day
        csp_enabled=True,
        allowed_origins={
            "https://staging.example.com",
            "https://staging.mwa.example.com"
        }
    ),
    
    "production": SecurityHeadersConfig(
        hsts_max_age=31536000,  # 1 year
        hsts_include_subdomains=True,
        hsts_preload=True,
        csp_enabled=True,
        frame_options="DENY",
        referrer_policy="strict-origin-when-cross-origin",
        allowed_origins={
            "https://app.mwa.example.com",
            "https://dashboard.mwa.example.com"
        }
    )
}


def create_security_middleware(
    environment: str = "development",
    custom_config: Optional[SecurityHeadersConfig] = None
) -> tuple[SecurityHeadersMiddleware, CORSMiddleware]:
    """Create security middleware with predefined or custom configuration."""
    if custom_config:
        config = custom_config
    else:
        config = SECURITY_CONFIGS.get(environment, SECURITY_CONFIGS["development"])
    
    security_middleware = SecurityHeadersMiddleware(None, config)  # App will be set later
    cors_middleware = CORSMiddleware(config)
    
    return security_middleware, cors_middleware


def get_production_security_config() -> SecurityHeadersConfig:
    """Get production-ready security configuration."""
    return SECURITY_CONFIGS["production"]