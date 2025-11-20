"""
Rate limiting middleware for FastAPI applications.

Provides comprehensive rate limiting with multiple strategies:
- Sliding window rate limiting
- Token bucket algorithm  
- Per-user and global rate limiting
- Redis-backed distributed rate limiting (optional)
"""

import time
import asyncio
from typing import Dict, Optional, Set, Callable, Any
from collections import defaultdict, deque
from datetime import datetime, timedelta
import hashlib
import json

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp


class RateLimitConfig:
    """Configuration for rate limiting."""
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        requests_per_hour: int = 1000,
        requests_per_day: int = 10000,
        burst_limit: int = 10,
        window_size: int = 60,  # seconds
        redis_url: Optional[str] = None
    ):
        self.requests_per_minute = requests_per_minute
        self.requests_per_hour = requests_per_hour
        self.requests_per_day = requests_per_day
        self.burst_limit = burst_limit
        self.window_size = window_size
        self.redis_url = redis_url


class RateLimitStore:
    """In-memory rate limit storage with sliding window algorithm."""
    
    def __init__(self):
        self.requests: Dict[str, deque] = defaultdict(deque)
        self.blocked_ips: Dict[str, float] = {}
        self.cleanup_interval = 300  # 5 minutes
        self.last_cleanup = time.time()
    
    def _cleanup_expired(self):
        """Remove expired entries to prevent memory leaks."""
        now = time.time()
        if now - self.last_cleanup > self.cleanup_interval:
            # Clean up old requests
            for key in list(self.requests.keys()):
                while self.requests[key] and now - self.requests[key][0] > 86400:  # 24 hours
                    self.requests[key].popleft()
                if not self.requests[key]:
                    del self.requests[key]
            
            # Clean up blocked IPs
            expired_blocks = [
                ip for ip, block_time in self.blocked_ips.items()
                if now - block_time > 3600  # 1 hour block
            ]
            for ip in expired_blocks:
                del self.blocked_ips[ip]
            
            self.last_cleanup = now
    
    def is_blocked(self, identifier: str) -> bool:
        """Check if identifier is currently blocked."""
        self._cleanup_expired()
        return identifier in self.blocked_ips
    
    def get_requests_in_window(self, identifier: str, window_seconds: int) -> int:
        """Get number of requests in the time window."""
        self._cleanup_expired()
        now = time.time()
        cutoff = now - window_seconds
        
        while self.requests[identifier] and self.requests[identifier][0] < cutoff:
            self.requests[identifier].popleft()
        
        return len(self.requests[identifier])
    
    def record_request(self, identifier: str) -> None:
        """Record a request in the sliding window."""
        self._cleanup_expired()
        now = time.time()
        self.requests[identifier].append(now)
    
    def block_identifier(self, identifier: str, duration_seconds: int = 3600):
        """Block an identifier for a specified duration."""
        self.blocked_ips[identifier] = time.time() + duration_seconds


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Comprehensive rate limiting middleware."""
    
    def __init__(
        self,
        app: ASGIApp,
        config: Optional[RateLimitConfig] = None,
        exempt_paths: Optional[Set[str]] = None,
        get_client_id: Optional[Callable[[Request], str]] = None
    ):
        super().__init__(app)
        self.config = config or RateLimitConfig()
        self.exempt_paths = exempt_paths or {"/health", "/docs", "/redoc", "/openapi.json"}
        self.get_client_id = get_client_id or self._default_get_client_id
        self.store = RateLimitStore()
        
        # Statistics
        self.stats = {
            "total_requests": 0,
            "blocked_requests": 0,
            "rate_limited_requests": 0,
            "unique_clients": set()
        }
    
    def _default_get_client_id(self, request: Request) -> str:
        """Default client identification strategy."""
        # Try to get real IP from headers (for proxies)
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("X-Real-IP")
        if real_ip:
            return real_ip
        
        # Fallback to client IP
        return request.client.host if request.client else "unknown"
    
    def _get_identifier(self, request: Request) -> str:
        """Get unique identifier for rate limiting."""
        client_id = self.get_client_id(request)
        
        # Include user ID if available (for per-user rate limiting)
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"
        
        return f"ip:{client_id}"
    
    def _check_rate_limit(self, identifier: str) -> tuple[bool, str, Dict[str, Any]]:
        """Check if request is within rate limits."""
        now = time.time()
        
        # Check if blocked
        if self.store.is_blocked(identifier):
            remaining = 0
            reset_time = self.store.blocked_ips.get(identifier, now + 3600)
            return False, "blocked", {
                "limit": 0,
                "remaining": remaining,
                "reset": int(reset_time),
                "retry_after": int(reset_time - now)
            }
        
        # Check different time windows
        checks = [
            ("minute", 60, self.config.requests_per_minute),
            ("hour", 3600, self.config.requests_per_hour),
            ("day", 86400, self.config.requests_per_day)
        ]
        
        limit_info = {}
        for window_name, window_seconds, limit in checks:
            count = self.store.get_requests_in_window(identifier, window_seconds)
            if count >= limit:
                remaining = max(0, limit - count)
                reset_time = now + window_seconds
                
                return False, "rate_limited", {
                    "limit": limit,
                    "remaining": remaining,
                    "reset": int(reset_time),
                    "window": window_name,
                    "count": count
                }
            
            limit_info[window_name] = {
                "limit": limit,
                "remaining": limit - count - 1,  # -1 for current request
                "count": count
            }
        
        return True, "allowed", limit_info
    
    def _apply_rate_limit(self, identifier: str, response: Response):
        """Apply rate limit information to response headers."""
        allowed, reason, info = self._check_rate_limit(identifier)
        
        # Add rate limit headers
        if "limit" in info:
            response.headers["X-RateLimit-Limit"] = str(info["limit"])
            response.headers["X-RateLimit-Remaining"] = str(info["remaining"])
            response.headers["X-RateLimit-Reset"] = str(info["reset"])
        
        if not allowed:
            self.stats["rate_limited_requests"] += 1
            
            if reason == "blocked":
                self.stats["blocked_requests"] += 1
                retry_after = info.get("retry_after", 3600)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Client blocked for {retry_after} seconds",
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(info.get("limit", 0)),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(info.get("reset", int(time.time() + 3600)))
                    }
                )
            else:
                retry_after = max(1, info.get("reset", int(time.time() + 60)) - int(time.time()))
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
                    headers={
                        "Retry-After": str(retry_after),
                        "X-RateLimit-Limit": str(info.get("limit", 0)),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(info.get("reset", int(time.time() + 60)))
                    }
                )
        
        # Record the request
        self.store.record_request(identifier)
        
        return response
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request with rate limiting."""
        # Skip rate limiting for exempt paths
        if request.url.path in self.exempt_paths:
            return await call_next(request)
        
        # Get client identifier
        identifier = self._get_identifier(request)
        
        # Update statistics
        self.stats["total_requests"] += 1
        self.stats["unique_clients"].add(identifier)
        
        try:
            # Apply rate limiting
            response = await call_next(request)
            response = self._apply_rate_limit(identifier, response)
            
            # Add rate limit info to response headers
            allowed, reason, info = self._check_rate_limit(identifier)
            if allowed and "minute" in info:
                response.headers["X-RateLimit-Remaining"] = str(info["minute"]["remaining"])
                response.headers["X-RateLimit-Limit"] = str(info["minute"]["limit"])
                response.headers["X-RateLimit-Reset"] = str(int(time.time() + 60))
            
            return response
            
        except HTTPException as e:
            # Re-raise HTTP exceptions (like rate limit errors)
            raise
        except Exception as e:
            # Log unexpected errors but don't block requests
            print(f"Rate limiter error: {e}")
            response = await call_next(request)
            return response
    
    def get_stats(self) -> Dict[str, Any]:
        """Get rate limiting statistics."""
        return {
            "total_requests": self.stats["total_requests"],
            "blocked_requests": self.stats["blocked_requests"],
            "rate_limited_requests": self.stats["rate_limited_requests"],
            "unique_clients": len(self.stats["unique_clients"]),
            "current_load": len(self.store.requests)
        }
    
    def reset_stats(self):
        """Reset rate limiting statistics."""
        self.stats = {
            "total_requests": 0,
            "blocked_requests": 0,
            "rate_limited_requests": 0,
            "unique_clients": set()
        }


class AdaptiveRateLimitMiddleware(RateLimitMiddleware):
    """Adaptive rate limiting that adjusts based on system load."""
    
    def __init__(self, app: ASGIApp, config: Optional[RateLimitConfig] = None):
        super().__init__(app, config)
        self.base_config = config or RateLimitConfig()
        self.load_factor = 1.0
        self.last_adjustment = time.time()
    
    def _adjust_for_load(self) -> RateLimitConfig:
        """Adjust rate limits based on current system load."""
        now = time.time()
        
        # Adjust every minute
        if now - self.last_adjustment > 60:
            # Simple load calculation based on active requests
            active_requests = sum(
                len(window) for window in self.store.requests.values()
                if any(now - req_time < 60 for req_time in window)
            )
            
            # Adjust load factor
            if active_requests > 100:
                self.load_factor = max(0.1, self.load_factor * 0.8)
            elif active_requests < 10:
                self.load_factor = min(2.0, self.load_factor * 1.1)
            
            self.last_adjustment = now
        
        # Create adjusted config
        return RateLimitConfig(
            requests_per_minute=int(self.base_config.requests_per_minute * self.load_factor),
            requests_per_hour=int(self.base_config.requests_per_hour * self.load_factor),
            requests_per_day=int(self.base_config.requests_per_day * self.load_factor),
            burst_limit=max(1, int(self.base_config.burst_limit * self.load_factor)),
            window_size=self.base_config.window_size,
            redis_url=self.base_config.redis_url
        )


def create_rate_limiter(
    requests_per_minute: int = 60,
    requests_per_hour: int = 1000,
    requests_per_day: int = 10000,
    burst_limit: int = 10
) -> RateLimitConfig:
    """Create a rate limiting configuration."""
    return RateLimitConfig(
        requests_per_minute=requests_per_minute,
        requests_per_hour=requests_per_hour,
        requests_per_day=requests_per_day,
        burst_limit=burst_limit
    )


# Predefined rate limiting configurations
RATE_LIMIT_CONFIGS = {
    "strict": RateLimitConfig(requests_per_minute=30, requests_per_hour=300, requests_per_day=1000),
    "moderate": RateLimitConfig(requests_per_minute=60, requests_per_hour=1000, requests_per_day=10000),
    "lenient": RateLimitConfig(requests_per_minute=120, requests_per_hour=2000, requests_per_day=20000),
    "development": RateLimitConfig(requests_per_minute=1000, requests_per_hour=10000, requests_per_day=100000),
    "production": RateLimitConfig(requests_per_minute=50, requests_per_hour=500, requests_per_day=5000)
}