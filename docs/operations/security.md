# Security Guide

## Overview
This guide covers security best practices, implementation guidelines, and compliance measures for MAFA production systems. It includes authentication, authorization, data protection, infrastructure security, and security monitoring procedures.

---

**Last Updated:** November 19, 2025  
**Version:** 1.0.0  
**Maintainer:** MAFA Security Team  
**Estimated Reading Time:** 30-35 minutes

---

## Security Architecture Overview

### Security Layers
```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                        │
│                  (MAFA Dashboard/API)                      │
└─────────────────────┬───────────────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────────────┐
│                  Authentication & Authorization             │
│                  (JWT, OAuth2, RBAC)                       │
└─────────────────────┼───────────────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────────────┐
│                   Data Protection Layer                    │
│            (Encryption, Hashing, Secure Storage)           │
└─────────────────────┼───────────────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────────────┐
│                  Infrastructure Security                   │
│            (Network, Container, OS Security)              │
└─────────────────────┼───────────────────────────────────────┘
                      │
┌─────────────────────┼───────────────────────────────────────┐
│                 Monitoring & Compliance                    │
│            (SIEM, Audit Logs, Compliance)                 │
└─────────────────────────────────────────────────────────────┘
```

### Security Principles
- **Defense in Depth**: Multiple layers of security controls
- **Zero Trust**: Never trust, always verify
- **Principle of Least Privilege**: Minimal access rights
- **Data Minimization**: Collect and store only necessary data
- **Security by Design**: Security integrated from the start

---

## Authentication and Authorization

### JWT Token Implementation
```python
# mafa/auth/jwt_manager.py
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status

class JWTManager:
    def __init__(self, secret_key: str, algorithm: str = "HS256"):
        self.secret_key = secret_key
        self.algorithm = algorithm
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.token_expire_minutes = 30
        self.refresh_expire_days = 7
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token."""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.token_expire_minutes)
        
        to_encode.update({"exp": expire, "type": "access"})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token."""
        expire = datetime.utcnow() + timedelta(days=self.refresh_expire_days)
        to_encode = data.copy()
        to_encode.update({"exp": expire, "type": "refresh"})
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Dict[str, Any]:
        """Verify and decode JWT token."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token has expired",
                headers={"WWW-Authenticate": "Bearer"},
            )
        except jwt.JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def hash_password(self, password: str) -> str:
        """Hash password using bcrypt."""
        return self.pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return self.pwd_context.verify(plain_password, hashed_password)

# Security middleware
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "connect-src 'self' wss: https:; "
            "font-src 'self'; "
            "object-src 'none'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = (
            "camera=(), "
            "microphone=(), "
            "geolocation=(), "
            "payment=(), "
            "usb=()"
        )
        
        return response
```

### Role-Based Access Control (RBAC)
```python
# mafa/auth/rbac.py
from enum import Enum
from typing import List, Dict, Any
from functools import wraps
from fastapi import HTTPException, status
import logging

logger = logging.getLogger(__name__)

class Permission(Enum):
    """System permissions."""
    # User management
    USER_CREATE = "user:create"
    USER_READ = "user:read"
    USER_UPDATE = "user:update"
    USER_DELETE = "user:delete"
    
    # Contact management
    CONTACT_CREATE = "contact:create"
    CONTACT_READ = "contact:read"
    CONTACT_UPDATE = "contact:update"
    CONTACT_DELETE = "contact:delete"
    
    # Search management
    SEARCH_CREATE = "search:create"
    SEARCH_READ = "search:read"
    SEARCH_UPDATE = "search:update"
    SEARCH_DELETE = "search:delete"
    
    # System administration
    SYSTEM_CONFIG = "system:config"
    SYSTEM_MONITOR = "system:monitor"
    SYSTEM_BACKUP = "system:backup"
    SYSTEM_RESTORE = "system:restore"

class Role(Enum):
    """System roles."""
    ADMIN = "admin"
    USER = "user"
    READONLY = "readonly"
    GUEST = "guest"

# Role-permission mapping
ROLE_PERMISSIONS = {
    Role.ADMIN: [
        Permission.USER_CREATE,
        Permission.USER_READ,
        Permission.USER_UPDATE,
        Permission.USER_DELETE,
        Permission.CONTACT_CREATE,
        Permission.CONTACT_READ,
        Permission.CONTACT_UPDATE,
        Permission.CONTACT_DELETE,
        Permission.SEARCH_CREATE,
        Permission.SEARCH_READ,
        Permission.SEARCH_UPDATE,
        Permission.SEARCH_DELETE,
        Permission.SYSTEM_CONFIG,
        Permission.SYSTEM_MONITOR,
        Permission.SYSTEM_BACKUP,
        Permission.SYSTEM_RESTORE,
    ],
    Role.USER: [
        Permission.CONTACT_CREATE,
        Permission.CONTACT_READ,
        Permission.CONTACT_UPDATE,
        Permission.CONTACT_DELETE,
        Permission.SEARCH_CREATE,
        Permission.SEARCH_READ,
        Permission.SEARCH_UPDATE,
        Permission.SEARCH_DELETE,
    ],
    Role.READONLY: [
        Permission.CONTACT_READ,
        Permission.SEARCH_READ,
    ],
    Role.GUEST: [
        Permission.CONTACT_READ,
    ],
}

class RBACManager:
    """Role-Based Access Control Manager."""
    
    def __init__(self):
        self.role_permissions = ROLE_PERMISSIONS
    
    def check_permission(self, user_role: Role, required_permission: Permission) -> bool:
        """Check if user role has required permission."""
        user_permissions = self.role_permissions.get(user_role, [])
        return required_permission in user_permissions
    
    def check_permissions(self, user_role: Role, required_permissions: List[Permission]) -> bool:
        """Check if user role has all required permissions."""
        user_permissions = self.role_permissions.get(user_role, [])
        return all(perm in user_permissions for perm in required_permissions)
    
    def get_user_permissions(self, user_role: Role) -> List[Permission]:
        """Get all permissions for a user role."""
        return self.role_permissions.get(user_role, [])

def require_permission(permission: Permission):
    """Decorator to require specific permission."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get user from request context (implement your auth logic)
            request = None
            for arg in args:
                if hasattr(arg, 'user'):  # Assuming request has user attribute
                    request = arg
                    break
            
            if not request or not hasattr(request.user, 'role'):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            rbac = RBACManager()
            if not rbac.check_permission(request.user.role, permission):
                logger.warning(
                    f"Access denied for user {request.user.id} "
                    f"on permission {permission.value}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions: {permission.value}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator

def require_role(role: Role):
    """Decorator to require specific role."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Get user from request context
            request = None
            for arg in args:
                if hasattr(arg, 'user'):
                    request = arg
                    break
            
            if not request or not hasattr(request.user, 'role'):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )
            
            if request.user.role != role:
                logger.warning(
                    f"Access denied for user {request.user.id} "
                    f"required role: {role.value}, "
                    f"actual role: {request.user.role.value}"
                )
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Required role: {role.value}"
                )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
```

### API Security Implementation
```python
# mafa/api/security.py
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from starlette.middleware.cors import CORSMiddleware
import time
import hashlib
import hmac
from typing import Optional

# Security schemes
security = HTTPBearer()

class SecurityManager:
    """Central security management for MAFA API."""
    
    def __init__(self):
        self.rate_limits = {}
        self.failed_attempts = {}
        self.blocked_ips = set()
    
    def check_rate_limit(self, client_ip: str, endpoint: str, limit: int = 100, window: int = 3600) -> bool:
        """Check and update rate limit for client."""
        current_time = int(time.time())
        window_start = current_time - window
        
        # Clean old entries
        if client_ip in self.rate_limits:
            self.rate_limits[client_ip] = [
                timestamp for timestamp in self.rate_limits[client_ip] 
                if timestamp > window_start
            ]
        else:
            self.rate_limits[client_ip] = []
        
        # Check limit
        if len(self.rate_limits[client_ip]) >= limit:
            return False
        
        # Add current request
        self.rate_limits[client_ip].append(current_time)
        return True
    
    def check_failed_attempts(self, client_ip: str, max_attempts: int = 5, window: int = 900) -> bool:
        """Check for brute force attacks."""
        current_time = int(time.time())
        window_start = current_time - window
        
        if client_ip in self.failed_attempts:
            recent_failures = [
                timestamp for timestamp in self.failed_attempts[client_ip] 
                if timestamp > window_start
            ]
            self.failed_attempts[client_ip] = recent_failures
        else:
            self.failed_attempts[client_ip] = []
        
        if len(self.failed_attempts[client_ip]) >= max_attempts:
            self.blocked_ips.add(client_ip)
            return False
        
        return True
    
    def record_failed_attempt(self, client_ip: str):
        """Record failed authentication attempt."""
        current_time = int(time.time())
        if client_ip not in self.failed_attempts:
            self.failed_attempts[client_ip] = []
        self.failed_attempts[client_ip].append(current_time)
    
    def is_blocked(self, client_ip: str) -> bool:
        """Check if IP is blocked."""
        return client_ip in self.blocked_ips

security_manager = SecurityManager()

def verify_api_signature(request_data: str, signature: str, secret_key: str) -> bool:
    """Verify API request signature."""
    expected_signature = hmac.new(
        secret_key.encode('utf-8'),
        request_data.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)

# Secure API endpoints
app = FastAPI(title="MAFA API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://mafa.app", "https://dashboard.mafa.app"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["Authorization", "Content-Type", "X-API-Signature"],
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining"],
)

@app.middleware("http")
async def security_middleware(request, call_next):
    """Global security middleware."""
    client_ip = request.client.host
    
    # Check if IP is blocked
    if security_manager.is_blocked(client_ip):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="IP address temporarily blocked due to repeated failures"
        )
    
    # Rate limiting
    endpoint = request.url.path
    if not security_manager.check_rate_limit(client_ip, endpoint):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={
                "X-RateLimit-Limit": "100",
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time()) + 3600)
            }
        )
    
    # API signature verification for sensitive endpoints
    if endpoint.startswith("/api/admin/") or endpoint.startswith("/api/config/"):
        signature = request.headers.get("X-API-Signature")
        if not signature:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="API signature required"
            )
        
        # Get request body for signature verification
        body = await request.body()
        if not verify_api_signature(body.decode('utf-8'), signature, "your-secret-key"):
            security_manager.record_failed_attempt(client_ip)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API signature"
            )
    
    response = await call_next(request)
    return response

@app.get("/api/contacts/", dependencies=[Depends(require_permission(Permission.CONTACT_READ))])
async def get_contacts():
    """Get contacts with security check."""
    # Implementation here
    pass

@app.post("/api/contacts/", dependencies=[Depends(require_permission(Permission.CONTACT_CREATE))])
async def create_contact():
    """Create contact with security check."""
    # Implementation here
    pass
```

---

## Data Protection and Encryption

### Database Encryption
```python
# mafa/security/encryption.py
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64
import os
from typing import Optional
from sqlalchemy import Column, String, LargeBinary
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import json

class EncryptedMixin:
    """Mixin for encrypting sensitive database fields."""
    
    def encrypt_field(self, field_name: str, key: bytes) -> None:
        """Encrypt a specific field."""
        if hasattr(self, field_name):
            fernet = Fernet(key)
            field_value = getattr(self, field_name)
            if field_value:
                encrypted_value = fernet.encrypt(field_value.encode())
                setattr(self, field_name, base64.b64encode(encrypted_value).decode())
    
    def decrypt_field(self, field_name: str, key: bytes) -> Optional[str]:
        """Decrypt a specific field."""
        if hasattr(self, field_name):
            fernet = Fernet(key)
            encrypted_value = getattr(self, field_name)
            if encrypted_value:
                try:
                    decoded_value = base64.b64decode(encrypted_value.encode())
                    decrypted_value = fernet.decrypt(decoded_value)
                    return decrypted_value.decode()
                except Exception:
                    return None
        return None

class Contact(Base, EncryptedMixin):
    """Contact model with encryption."""
    __tablename__ = "contacts"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    phone_encrypted = Column(LargeBinary, nullable=True)
    email_encrypted = Column(LargeBinary, nullable=True)
    address_encrypted = Column(LargeBinary, nullable=True)
    notes_encrypted = Column(LargeBinary, nullable=True)
    
    # Encryption key (should be from environment or key management service)
    ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY', Fernet.generate_key())
    
    def set_phone(self, phone: str) -> None:
        """Set encrypted phone number."""
        self.encrypt_field('phone_encrypted', self.ENCRYPTION_KEY)
        if hasattr(self, '_phone_cache'):
            delattr(self, '_phone_cache')
    
    def get_phone(self) -> Optional[str]:
        """Get decrypted phone number."""
        if hasattr(self, '_phone_cache'):
            return self._phone_cache
        
        phone = self.decrypt_field('phone_encrypted', self.ENCRYPTION_KEY)
        if phone:
            self._phone_cache = phone
        return phone
    
    def set_email(self, email: str) -> None:
        """Set encrypted email."""
        self.encrypt_field('email_encrypted', self.ENCRYPTION_KEY)
    
    def get_email(self) -> Optional[str]:
        """Get decrypted email."""
        return self.decrypt_field('email_encrypted', self.ENCRYPTION_KEY)

# Field-level encryption utility
def encrypt_sensitive_data(data: dict, fields_to_encrypt: list, key: bytes) -> dict:
    """Encrypt specific fields in a data dictionary."""
    fernet = Fernet(key)
    encrypted_data = data.copy()
    
    for field in fields_to_encrypt:
        if field in encrypted_data and encrypted_data[field]:
            encrypted_data[field] = fernet.encrypt(
                encrypted_data[field].encode()
            ).decode()
    
    return encrypted_data

def decrypt_sensitive_data(data: dict, fields_to_decrypt: list, key: bytes) -> dict:
    """Decrypt specific fields in a data dictionary."""
    fernet = Fernet(key)
    decrypted_data = data.copy()
    
    for field in fields_to_decrypt:
        if field in decrypted_data and decrypted_data[field]:
            try:
                decrypted_value = fernet.decrypt(
                    decrypted_data[field].encode()
                ).decode()
                decrypted_data[field] = decrypted_value
            except Exception:
                # Handle decryption errors gracefully
                pass
    
    return decrypted_data

# Password hashing with salt
import secrets
import hashlib

class SecurePasswordManager:
    """Secure password management with salt and hashing."""
    
    @staticmethod
    def generate_salt() -> str:
        """Generate a cryptographically secure salt."""
        return secrets.token_hex(32)
    
    @staticmethod
    def hash_password(password: str, salt: str) -> str:
        """Hash password with salt using PBKDF2."""
        pwdhash = hashlib.pbkdf2_hmac('sha256', 
                                      password.encode('utf-8'), 
                                      salt.encode('utf-8'), 
                                      100000)
        return pwdhash.hex()
    
    @staticmethod
    def verify_password(password: str, salt: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        computed_hash = SecurePasswordManager.hash_password(password, salt)
        return hmac.compare_digest(computed_hash, hashed_password)
    
    @classmethod
    def create_secure_password(cls, password: str) -> dict:
        """Create a secure password with salt and hash."""
        salt = cls.generate_salt()
        hashed = cls.hash_password(password, salt)
        return {
            'salt': salt,
            'hashed_password': hashed
        }
```

### API Request/Response Encryption
```python
# mafa/security/api_encryption.py
import json
from cryptography.fernet import Fernet
from typing import Any, Dict
import base64
from fastapi import Request, Response

class APIEncryption:
    """API request/response encryption utilities."""
    
    def __init__(self, key: bytes):
        self.fernet = Fernet(key)
    
    def encrypt_response_data(self, data: Dict[str, Any]) -> str:
        """Encrypt API response data."""
        try:
            json_data = json.dumps(data, default=str)
            encrypted_data = self.fernet.encrypt(json_data.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            raise ValueError(f"Failed to encrypt response data: {str(e)}")
    
    def decrypt_request_data(self, encrypted_data: str) -> Dict[str, Any]:
        """Decrypt API request data."""
        try:
            decoded_data = base64.b64decode(encrypted_data.encode())
            decrypted_json = self.fernet.decrypt(decoded_data)
            return json.loads(decrypted_json.decode())
        except Exception as e:
            raise ValueError(f"Failed to decrypt request data: {str(e)}")

# Secure API middleware
async def encrypt_sensitive_responses(request: Request, call_next):
    """Middleware to encrypt sensitive API responses."""
    response = await call_next(request)
    
    # Only encrypt responses for sensitive endpoints
    if request.url.path.startswith("/api/contacts/") or request.url.path.startswith("/api/users/"):
        # Get original response body
        response_body = response.body
        
        if response_body:
            try:
                # Parse and encrypt response data
                data = json.loads(response_body.decode())
                encryption_manager = APIEncryption(request.app.encryption_key)
                encrypted_data = encryption_manager.encrypt_response_data(data)
                
                # Create new response with encrypted data
                return Response(
                    content=encrypted_data,
                    status_code=response.status_code,
                    headers={
                        **response.headers,
                        "X-Content-Encrypted": "true",
                        "X-Content-Type": "application/json"
                    },
                    media_type="application/json"
                )
            except Exception as e:
                # Log encryption error but don't break the request
                print(f"Encryption error: {e}")
    
    return response

@app.middleware("http")
async def security_middleware(request: Request, call_next):
    """Combined security middleware."""
    # Rate limiting
    client_ip = request.client.host
    if not security_manager.check_rate_limit(client_ip, request.url.path):
        return Response(
            content=json.dumps({"error": "Rate limit exceeded"}),
            status_code=429,
            media_type="application/json"
        )
    
    # Check for encrypted request data
    if request.headers.get("X-Content-Encrypted") == "true":
        try:
            encryption_manager = APIEncryption(request.app.encryption_key)
            body = await request.body()
            if body:
                decrypted_data = encryption_manager.decrypt_request_data(body.decode())
                # Store decrypted data for use by endpoint
                request.state.decrypted_body = decrypted_data
        except Exception as e:
            return Response(
                content=json.dumps({"error": "Failed to decrypt request data"}),
                status_code=400,
                media_type="application/json"
            )
    
    response = await call_next(request)
    return response
```

---

## Infrastructure Security

### Docker Security Configuration
```dockerfile
# Dockerfile.secure
# Use official Python image with specific version
FROM python:3.11-slim-bullseye

# Create non-root user
RUN groupadd --gid 1000 appuser && \
    useradd --uid 1000 --gid appuser --shell /bin/bash --create-home appuser

# Install security updates
RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
        curl \
        netcat \
        fail2ban \
        logrotate \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir safety bandit

# Run security checks
RUN safety check --json --output safety-report.json || true
RUN bandit -r . -f json -o bandit-report.json || true

# Copy application code
COPY --chown=appuser:appuser . .

# Set file permissions
RUN chmod -R 755 /app && \
    chmod -R 644 /app/scripts/*.sh

# Remove unnecessary packages and clean up
RUN apt-get purge -y --auto-remove \
        build-essential \
        gcc \
        g++ \
        make \
        && apt-get clean \
        && rm -rf /var/cache/apt/* \
        && rm -rf /tmp/*

# Switch to non-root user
USER appuser

# Set environment variables for security
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/app/.local/bin:$PATH"

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port (non-privileged)
EXPOSE 8000

# Use non-root port
ENV PORT=8000

# Run application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
```

### Docker Compose Security
```yaml
# docker-compose.secure.yml
version: '3.8'

services:
  mafa-api:
    build:
      context: .
      dockerfile: Dockerfile.secure
    container_name: mafa-api-secure
    restart: unless-stopped
    environment:
      - PYTHONUNBUFFERED=1
      - DATABASE_URL=postgresql://mafa:${DB_PASSWORD}@postgres:5432/mwa_core
      - REDIS_URL=redis://redis:6379/0
      - JWT_SECRET_KEY=${JWT_SECRET_KEY}
      - ENCRYPTION_KEY=${ENCRYPTION_KEY}
    volumes:
      - ./logs:/var/log/mafa
      - ./backups:/var/backups
      - /etc/localtime:/etc/localtime:ro
    networks:
      - mafa-network
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    read_only: true
    tmpfs:
      - /tmp
      - /var/run
    ulimits:
      nofile:
        soft: 65536
        hard: 65536
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s

  postgres:
    image: postgres:15-alpine
    container_name: mafa-postgres-secure
    restart: unless-stopped
    environment:
      - POSTGRES_DB=mwa_core
      - POSTGRES_USER=mafa
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      - POSTGRES_INITDB_ARGS=--auth-host=scram-sha-256
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/sql:/docker-entrypoint-initdb.d:ro
      - ./backups:/backups
    networks:
      - mafa-network
    security_opt:
      - no-new-privileges:true
    command: >
      postgres
        -c ssl=on
        -c ssl_cert_file=/etc/ssl/certs/server.crt
        -c ssl_key_file=/etc/ssl/private/server.key
        -c log_connections=on
        -c log_disconnections=on
        -c log_statement=all
        -c shared_preload_libraries=pg_stat_statements
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mafa -d mwa_core"]
      interval: 30s
      timeout: 10s
      retries: 5

  redis:
    image: redis:7-alpine
    container_name: mafa-redis-secure
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD} --appendonly yes
    volumes:
      - redis_data:/data
      - ./redis.conf:/etc/redis/redis.conf:ro
    networks:
      - mafa-network
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - SETUID
      - SETGID
    read_only: true
    tmpfs:
      - /tmp

  nginx:
    image: nginx:1.24-alpine
    container_name: mafa-nginx-secure
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - ./nginx/logs:/var/log/nginx
      - ./static:/var/www/static:ro
    networks:
      - mafa-network
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    read_only: true
    depends_on:
      - mafa-api

volumes:
  postgres_data:
    driver: local
  redis_data:
    driver: local

networks:
  mafa-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

### Nginx Security Configuration
```nginx
# nginx/nginx.conf
worker_processes auto;
worker_rlimit_nofile 65536;

events {
    worker_connections 4096;
    use epoll;
    multi_accept on;
}

http {
    # Basic Settings
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    keepalive_requests 100;
    types_hash_max_size 2048;
    server_tokens off;
    
    # MIME types
    include /etc/nginx/mime.types;
    default_type application/octet-stream;
    
    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self' data:;" always;
    
    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;
    
    # Connection Limiting
    limit_conn_zone $binary_remote_addr zone=conn_limit_per_ip:10m;
    limit_conn_zone $server_name zone=conn_limit_per_server:10m;
    
    # SSL Settings
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:50m;
    ssl_session_timeout 1d;
    ssl_session_tickets off;
    ssl_stapling on;
    ssl_stapling_verify on;
    
    # HTTP/2
    http2_max_field_size 16k;
    http2_max_header_size 32k;
    
    # Gzip Compression
    gzip on;
    gzip_vary on;
    gzip_min_length 10240;
    gzip_proxied expired no-cache no-store private must-revalidate auth;
    gzip_types
        text/plain
        text/css
        text/xml
        text/javascript
        application/x-javascript
        application/xml+rss
        application/javascript
        application/json;
    
    # Hide server information
    server_tokens off;
    
    # Rate limiting for login endpoints
    map $request_uri $limit_key {
        ~^/api/auth/login.* $binary_remote_addr;
        default "";
    }
    
    # Upstream configuration
    upstream mafa_backend {
        least_conn;
        server mafa-api:8000 max_fails=3 fail_timeout=30s;
        keepalive 32;
    }
    
    # HTTP Server (redirect to HTTPS)
    server {
        listen 80;
        server_name mafa.app www.mafa.app;
        
        # Security
        location /.well-known/acme-challenge/ {
            root /var/www/certbot;
        }
        
        location / {
            return 301 https://$server_name$request_uri;
        }
    }
    
    # HTTPS Server
    server {
        listen 443 ssl http2;
        server_name mafa.app www.mafa.app;
        
        # SSL Configuration
        ssl_certificate /etc/nginx/ssl/fullchain.pem;
        ssl_certificate_key /etc/nginx/ssl/privkey.pem;
        
        # Security
        add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
        add_header X-Frame-Options DENY;
        add_header X-Content-Type-Options nosniff;
        
        # Rate limiting
        limit_req zone=api burst=20 nodelay;
        limit_conn conn_limit_per_ip 10;
        limit_conn conn_limit_per_server 100;
        
        # Client settings
        client_max_body_size 10M;
        client_body_timeout 60s;
        client_header_timeout 60s;
        send_timeout 60s;
        
        # API endpoints
        location /api/ {
            # Apply rate limiting
            limit_req zone=api burst=20 nodelay;
            
            # Security headers for API
            add_header Cache-Control "no-cache, no-store, must-revalidate";
            add_header Pragma "no-cache";
            add_header Expires "0";
            
            # Proxy to backend
            proxy_pass http://mafa_backend;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection 'upgrade';
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_cache_bypass $http_upgrade;
            
            # Timeouts
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
            
            # Buffer settings
            proxy_buffering on;
            proxy_buffer_size 128k;
            proxy_buffers 4 256k;
            proxy_busy_buffers_size 256k;
        }
        
        # Login endpoint with stricter rate limiting
        location /api/auth/login {
            limit_req zone=login burst=5 nodelay;
            
            proxy_pass http://mafa_backend;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Additional security for login
            add_header Cache-Control "no-cache, no-store, must-revalidate";
            proxy_set_header X-Forwarded-Proto https;
        }
        
        # Static files
        location /static/ {
            alias /var/www/static/;
            expires 1y;
            add_header Cache-Control "public, immutable";
            
            # Security
            add_header X-Frame-Options SAMEORIGIN;
            add_header X-Content-Type-Options nosniff;
        }
        
        # Health check
        location /health {
            access_log off;
            return 200 "healthy\n";
            add_header Content-Type text/plain;
        }
        
        # Block access to sensitive files
        location ~ /\. {
            deny all;
            access_log off;
            log_not_found off;
        }
        
        location ~ \.(sql|json|log|conf|ini)$ {
            deny all;
            access_log off;
            log_not_found off;
        }
    }
}
```

---

## Security Monitoring and Auditing

### Security Event Logging
```python
# mafa/security/audit.py
import logging
import json
import time
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import Request, HTTPException
from sqlalchemy import Column, String, DateTime, Text, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID
import structlog

Base = declarative_base()

class SecurityEvent(Base):
    """Security event logging model."""
    __tablename__ = "security_events"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String(100), nullable=False)
    user_id = Column(String(255), nullable=True)
    session_id = Column(String(255), nullable=True)
    ip_address = Column(String(45), nullable=False)
    user_agent = Column(Text, nullable=True)
    endpoint = Column(String(500), nullable=True)
    method = Column(String(10), nullable=True)
    status_code = Column(Integer, nullable=True)
    risk_score = Column(Integer, nullable=False, default=0)
    event_data = Column(Text, nullable=True)  # JSON
    timestamp = Column(DateTime, default=datetime.utcnow)
    processed = Column(Boolean, default=False)

class SecurityLogger:
    """Security event logging and analysis."""
    
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.logger = structlog.get_logger("security")
        self.risk_weights = {
            'failed_login': 10,
            'successful_login': 2,
            'privilege_escalation': 50,
            'data_access': 5,
            'configuration_change': 15,
            'suspicious_activity': 25,
            'rate_limit_exceeded': 8,
            'invalid_signature': 20
        }
    
    def log_security_event(self, event_type: str, request: Request, 
                          additional_data: Optional[Dict[str, Any]] = None,
                          status_code: Optional[int] = None) -> None:
        """Log security event to database and structured logging."""
        
        # Calculate risk score
        risk_score = self.risk_weights.get(event_type, 0)
        
        # Prepare event data
        event_data = {
            'request_id': getattr(request.state, 'request_id', str(uuid.uuid4())),
            'timestamp': datetime.utcnow().isoformat(),
            'additional_data': additional_data or {}
        }
        
        # Create security event record
        security_event = SecurityEvent(
            event_type=event_type,
            user_id=getattr(request.state, 'user_id', None),
            session_id=getattr(request.state, 'session_id', None),
            ip_address=request.client.host,
            user_agent=request.headers.get('user-agent', ''),
            endpoint=str(request.url.path),
            method=request.method,
            status_code=status_code,
            risk_score=risk_score,
            event_data=json.dumps(event_data)
        )
        
        # Store in database
        try:
            with self.session_factory() as session:
                session.add(security_event)
                session.commit()
        except Exception as e:
            self.logger.error("Failed to log security event", error=str(e))
        
        # Structured logging
        self.logger.info(
            "Security event logged",
            event_type=event_type,
            user_id=getattr(request.state, 'user_id', None),
            ip_address=request.client.host,
            endpoint=str(request.url.path),
            method=request.method,
            status_code=status_code,
            risk_score=risk_score
        )
        
        # Alert on high-risk events
        if risk_score >= 20:
            self.logger.warning(
                "High-risk security event detected",
                event_type=event_type,
                risk_score=risk_score,
                ip_address=request.client.host
            )
    
    def log_login_attempt(self, request: Request, success: bool, 
                         user_id: Optional[str] = None) -> None:
        """Log login attempt with security details."""
        event_type = 'successful_login' if success else 'failed_login'
        
        additional_data = {
            'login_success': success,
            'authentication_method': 'password',  # or 'token', 'oauth', etc.
        }
        
        self.log_security_event(event_type, request, additional_data)
    
    def log_data_access(self, request: Request, resource_type: str, 
                       resource_id: Optional[str] = None) -> None:
        """Log sensitive data access."""
        additional_data = {
            'resource_type': resource_type,
            'resource_id': resource_id
        }
        
        self.log_security_event('data_access', request, additional_data)
    
    def log_configuration_change(self, request: Request, 
                                config_path: str, old_value: Any, 
                                new_value: Any) -> None:
        """Log configuration changes."""
        additional_data = {
            'config_path': config_path,
            'old_value': str(old_value),
            'new_value': str(new_value)
        }
        
        self.log_security_event('configuration_change', request, additional_data)
    
    def log_suspicious_activity(self, request: Request, reason: str,
                               severity: str = 'medium') -> None:
        """Log suspicious activity."""
        additional_data = {
            'reason': reason,
            'severity': severity
        }
        
        self.log_security_event('suspicious_activity', request, additional_data)

# Security monitoring middleware
class SecurityMonitoringMiddleware:
    """Middleware for security monitoring and logging."""
    
    def __init__(self, app, security_logger: SecurityLogger):
        self.app = app
        self.security_logger = security_logger
    
    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return
        
        request = Request(scope, receive, send)
        request.state.request_id = str(uuid.uuid4())
        start_time = time.time()
        
        try:
            # Process request
            await self.app(scope, receive, send)
            
            # Log successful requests for sensitive endpoints
            if self._is_sensitive_endpoint(request.url.path):
                processing_time = time.time() - start_time
                self.security_logger.log_security_event(
                    'api_access', 
                    request,
                    additional_data={'processing_time': processing_time}
                )
                
        except HTTPException as e:
            # Log security-related errors
            if e.status_code in [401, 403, 429]:
                self.security_logger.log_security_event(
                    f'http_error_{e.status_code}',
                    request,
                    additional_data={'error_detail': e.detail},
                    status_code=e.status_code
                )
            raise
        
        except Exception as e:
            # Log unexpected errors
            processing_time = time.time() - start_time
            self.security_logger.log_security_event(
                'internal_error',
                request,
                additional_data={
                    'processing_time': processing_time,
                    'error_type': type(e).__name__,
                    'error_message': str(e)
                }
            )
            raise
    
    def _is_sensitive_endpoint(self, path: str) -> bool:
        """Check if endpoint is sensitive and should be logged."""
        sensitive_patterns = [
            '/api/contacts',
            '/api/users',
            '/api/config',
            '/api/admin',
            '/api/auth/login'
        ]
        return any(path.startswith(pattern) for pattern in sensitive_patterns)
```

### Security Analysis and Reporting
```python
# mfa/security/analysis.py
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc, func
import pandas as pd
import json

class SecurityAnalyzer:
    """Security event analysis and reporting."""
    
    def __init__(self, session_factory):
        self.session_factory = session_factory
    
    def get_security_summary(self, days: int = 30) -> Dict[str, Any]:
        """Get security summary for the last N days."""
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        with self.session_factory() as session:
            # Total events by type
            event_summary = session.query(
                SecurityEvent.event_type,
                func.count(SecurityEvent.id).label('count')
            ).filter(
                SecurityEvent.timestamp >= start_date
            ).group_by(SecurityEvent.event_type).all()
            
            # Daily event counts
            daily_summary = session.query(
                func.date(SecurityEvent.timestamp).label('date'),
                func.count(SecurityEvent.id).label('count')
            ).filter(
                SecurityEvent.timestamp >= start_date
            ).group_by(func.date(SecurityEvent.timestamp)).all()
            
            # High-risk events
            high_risk_events = session.query(
                SecurityEvent
            ).filter(
                SecurityEvent.timestamp >= start_date,
                SecurityEvent.risk_score >= 20
            ).order_by(desc(SecurityEvent.timestamp)).limit(10).all()
            
            # IP address analysis
            ip_analysis = session.query(
                SecurityEvent.ip_address,
                func.count(SecurityEvent.id).label('event_count'),
                func.sum(SecurityEvent.risk_score).label('total_risk')
            ).filter(
                SecurityEvent.timestamp >= start_date
            ).group_by(SecurityEvent.ip_address).order_by(desc('total_risk')).limit(10).all()
            
            return {
                'period': f'{start_date.date()} to {end_date.date()}',
                'total_events': sum(event.count for event in event_summary),
                'event_breakdown': {event.event_type: event.count for event in event_summary},
                'daily_counts': {str(event.date): event.count for event in daily_summary},
                'high_risk_events': [
                    {
                        'timestamp': event.timestamp.isoformat(),
                        'event_type': event.event_type,
                        'ip_address': event.ip_address,
                        'risk_score': event.risk_score,
                        'endpoint': event.endpoint
                    }
                    for event in high_risk_events
                ],
                'top_risk_ips': [
                    {
                        'ip_address': ip.ip_address,
                        'event_count': ip.event_count,
                        'total_risk': float(ip.total_risk or 0)
                    }
                    for ip in ip_analysis
                ]
            }
    
    def detect_anomalies(self, days: int = 7) -> List[Dict[str, Any]]:
        """Detect security anomalies."""
        anomalies = []
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        with self.session_factory() as session:
            # Detect unusual login patterns
            login_events = session.query(
                SecurityEvent
            ).filter(
                SecurityEvent.event_type == 'failed_login',
                SecurityEvent.timestamp >= start_date
            ).all()
            
            # Group by IP and time window
            ip_failures = {}
            for event in login_events:
                hour_key = event.timestamp.strftime('%Y-%m-%d-%H')
                ip = event.ip_address
                
                if ip not in ip_failures:
                    ip_failures[ip] = {}
                
                if hour_key not in ip_failures[ip]:
                    ip_failures[ip][hour_key] = 0
                ip_failures[ip][hour_key] += 1
            
            # Check for brute force attempts
            for ip, failures in ip_failures.items():
                for hour, count in failures.items():
                    if count >= 10:  # 10+ failed logins in an hour
                        anomalies.append({
                            'type': 'brute_force_attempt',
                            'severity': 'high',
                            'ip_address': ip,
                            'time_window': hour,
                            'failure_count': count,
                            'description': f'{count} failed login attempts in {hour}'
                        })
            
            # Detect privilege escalation attempts
            priv_events = session.query(SecurityEvent).filter(
                SecurityEvent.event_type == 'privilege_escalation',
                SecurityEvent.timestamp >= start_date
            ).all()
            
            for event in priv_events:
                anomalies.append({
                    'type': 'privilege_escalation',
                    'severity': 'critical',
                    'ip_address': event.ip_address,
                    'timestamp': event.timestamp.isoformat(),
                    'user_id': event.user_id,
                    'endpoint': event.endpoint,
                    'description': 'Privilege escalation attempt detected'
                })
        
        return anomalies
    
    def generate_security_report(self, format: str = 'json') -> str:
        """Generate comprehensive security report."""
        summary = self.get_security_summary()
        anomalies = self.detect_anomalies()
        
        report = {
            'generated_at': datetime.utcnow().isoformat(),
            'summary': summary,
            'anomalies': anomalies,
            'recommendations': self._generate_recommendations(summary, anomalies)
        }
        
        if format == 'json':
            return json.dumps(report, indent=2)
        elif format == 'text':
            return self._format_text_report(report)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _generate_recommendations(self, summary: Dict, anomalies: List) -> List[str]:
        """Generate security recommendations based on analysis."""
        recommendations = []
        
        # Analyze failure rates
        total_events = summary.get('total_events', 0)
        failed_logins = summary.get('event_breakdown', {}).get('failed_login', 0)
        
        if failed_logins > 0:
            failure_rate = (failed_logins / total_events) * 100
            if failure_rate > 5:
                recommendations.append(
                    f"High login failure rate detected ({failure_rate:.1f}%). "
                    "Consider implementing additional security measures."
                )
        
        # Analyze anomalies
        critical_anomalies = [a for a in anomalies if a.get('severity') == 'critical']
        if critical_anomalies:
            recommendations.append(
                f"Critical security anomalies detected ({len(critical_anomalies)} events). "
                "Immediate investigation required."
            )
        
        # Risk IP analysis
        top_risk_ips = summary.get('top_risk_ips', [])
        if len(top_risk_ips) > 5:
            recommendations.append(
                "Multiple high-risk IP addresses detected. "
                "Consider implementing IP-based blocking."
            )
        
        if not recommendations:
            recommendations.append("No immediate security concerns detected.")
        
        return recommendations
    
    def _format_text_report(self, report: Dict) -> str:
        """Format report as human-readable text."""
        lines = []
        lines.append("=== MAFA Security Report ===")
        lines.append(f"Generated: {report['generated_at']}")
        lines.append("")
        
        # Summary
        summary = report['summary']
        lines.append("--- Summary ---")
        lines.append(f"Period: {summary['period']}")
        lines.append(f"Total Events: {summary['total_events']}")
        lines.append("")
        
        # Event breakdown
        lines.append("--- Event Breakdown ---")
        for event_type, count in summary['event_breakdown'].items():
            lines.append(f"{event_type}: {count}")
        lines.append("")
        
        # Anomalies
        if report['anomalies']:
            lines.append("--- Security Anomalies ---")
            for anomaly in report['anomalies']:
                lines.append(f"[{anomaly['severity'].upper()}] {anomaly['type']}")
                lines.append(f"  Description: {anomaly['description']}")
                lines.append(f"  IP: {anomaly.get('ip_address', 'N/A')}")
                lines.append("")
        
        # Recommendations
        lines.append("--- Recommendations ---")
        for i, rec in enumerate(report['recommendations'], 1):
            lines.append(f"{i}. {rec}")
        
        return "\n".join(lines)
```

---

## Compliance and Data Protection

### GDPR Compliance Implementation
```python
# mafa/compliance/gdpr.py
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import HTTPException, status
import logging
from sqlalchemy import Column, String, DateTime, Boolean
from sqlalchemy.dialects.postgresql import UUID
import uuid

logger = logging.getLogger(__name__)

class GDPRManager:
    """GDPR compliance management for MAFA."""
    
    def __init__(self, session_factory):
        self.session_factory = session_factory
        self.data_retention_days = 365  # 1 year default retention
    
    def export_user_data(self, user_id: str) -> Dict[str, Any]:
        """Export all user data for GDPR Article 20 (Right to Data Portability)."""
        with self.session_factory() as session:
            # Get user information
            user = session.query(User).filter(User.id == user_id).first()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")
            
            # Get user's contacts
            contacts = session.query(Contact).filter(Contact.user_id == user_id).all()
            
            # Get user's search criteria
            searches = session.query(SearchCriteria).filter(SearchCriteria.user_id == user_id).all()
            
            # Get user's notifications
            notifications = session.query(Notification).filter(Notification.user_id == user_id).all()
            
            # Compile export data
            export_data = {
                'export_date': datetime.utcnow().isoformat(),
                'user_information': {
                    'id': str(user.id),
                    'email': user.email,
                    'created_at': user.created_at.isoformat(),
                    'last_login': user.last_login.isoformat() if user.last_login else None,
                    'preferences': user.preferences or {}
                },
                'contacts': [
                    {
                        'id': str(contact.id),
                        'name': contact.name,
                        'phone': contact.get_phone(),  # Decrypted
                        'email': contact.get_email(),  # Decrypted
                        'created_at': contact.created_at.isoformat(),
                        'updated_at': contact.updated_at.isoformat() if contact.updated_at else None
                    }
                    for contact in contacts
                ],
                'search_criteria': [
                    {
                        'id': str(search.id),
                        'criteria': search.criteria,
                        'created_at': search.created_at.isoformat(),
                        'is_active': search.is_active
                    }
                    for search in searches
                ],
                'notifications': [
                    {
                        'id': str(notification.id),
                        'type': notification.type,
                        'message': notification.message,
                        'created_at': notification.created_at.isoformat(),
                        'read_at': notification.read_at.isoformat() if notification.read_at else None
                    }
                    for notification in notifications
                ]
            }
            
            # Log data export
            logger.info(f"GDPR data export completed for user {user_id}")
            
            return export_data
    
    def delete_user_data(self, user_id: str, verify_deletion: bool = True) -> bool:
        """Delete all user data for GDPR Article 17 (Right to Erasure)."""
        with self.session_factory() as session:
            try:
                # Verify user exists
                user = session.query(User).filter(User.id == user_id).first()
                if not user:
                    if verify_deletion:
                        raise HTTPException(status_code=404, detail="User not found")
                    return False
                
                if verify_deletion and not user.deletion_confirmed:
                    raise HTTPException(
                        status_code=400, 
                        detail="User deletion not confirmed"
                    )
                
                # Delete user data in order (respecting foreign key constraints)
                
                # 1. Delete contacts
                contacts_deleted = session.query(Contact).filter(
                    Contact.user_id == user_id
                ).delete(synchronize_session=False)
                
                # 2. Delete search criteria
                searches_deleted = session.query(SearchCriteria).filter(
                    SearchCriteria.user_id == user_id
                ).delete(synchronize_session=False)
                
                # 3. Delete notifications
                notifications_deleted = session.query(Notification).filter(
                    Notification.user_id == user_id
                ).delete(synchronize_session=False)
                
                # 4. Delete security events related to user
                security_events_deleted = session.query(SecurityEvent).filter(
                    SecurityEvent.user_id == user_id
                ).delete(synchronize_session=False)
                
                # 5. Finally delete the user
                session.query(User).filter(User.id == user_id).delete()
                
                session.commit()
                
                # Log data deletion
                logger.info(
                    f"GDPR data deletion completed for user {user_id}. "
                    f"Deleted: {contacts_deleted} contacts, {searches_deleted} searches, "
                    f"{notifications_deleted} notifications, {security_events_deleted} security events"
                )
                
                return True
                
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to delete user data for {user_id}: {str(e)}")
                raise HTTPException(
                    status_code=500, 
                    detail="Failed to delete user data"
                )
    
    def anonymize_user_data(self, user_id: str) -> bool:
        """Anonymize user data instead of complete deletion."""
        with self.session_factory() as session:
            try:
                # Update user to anonymized state
                user = session.query(User).filter(User.id == user_id).first()
                if user:
                    user.email = f"anonymous_{user_id}@deleted.mafa.app"
                    user.name = "Deleted User"
                    user.preferences = {}
                    user.is_active = False
                    user.deleted_at = datetime.utcnow()
                
                # Anonymize contacts
                contacts = session.query(Contact).filter(Contact.user_id == user_id).all()
                for contact in contacts:
                    contact.name = "Anonymized Contact"
                    contact.set_phone("")  # Clear encrypted phone
                    contact.set_email("")  # Clear encrypted email
                    contact.address = ""   # Clear address
                    contact.notes = ""     # Clear notes
                
                # Anonymize search criteria
                searches = session.query(SearchCriteria).filter(
                    SearchCriteria.user_id == user_id
                ).all()
                for search in searches:
                    search.criteria = {"anonymized": True}
                    search.is_active = False
                
                session.commit()
                
                logger.info(f"User data anonymized for {user_id}")
                return True
                
            except Exception as e:
                session.rollback()
                logger.error(f"Failed to anonymize user data for {user_id}: {str(e)}")
                raise HTTPException(
                    status_code=500, 
                    detail="Failed to anonymize user data"
                )
    
    def get_data_retention_summary(self) -> Dict[str, Any]:
        """Get data retention summary for compliance reporting."""
        with self.session_factory() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=self.data_retention_days)
            
            # Count old records
            old_contacts = session.query(Contact).filter(
                Contact.updated_at < cutoff_date
            ).count()
            
            old_users = session.query(User).filter(
                User.last_login < cutoff_date,
                User.is_active == False
            ).count()
            
            old_logs = session.query(SecurityEvent).filter(
                SecurityEvent.timestamp < cutoff_date
            ).count()
            
            return {
                'retention_policy_days': self.data_retention_days,
                'cutoff_date': cutoff_date.isoformat(),
                'records_for_deletion': {
                    'contacts': old_contacts,
                    'users': old_users,
                    'security_events': old_logs
                },
                'total_records': old_contacts + old_users + old_logs
            }
    
    def cleanup_expired_data(self, dry_run: bool = True) -> Dict[str, Any]:
        """Clean up data that has expired according to retention policy."""
        with self.session_factory() as session:
            cutoff_date = datetime.utcnow() - timedelta(days=self.data_retention_days)
            
            results = {
                'dry_run': dry_run,
                'cutoff_date': cutoff_date.isoformat(),
                'deletions': {
                    'contacts': 0,
                    'users': 0,
                    'security_events': 0,
                    'notifications': 0
                }
            }
            
            try:
                if not dry_run:
                    # Delete old security events (keep for 90 days)
                    event_cutoff = datetime.utcnow() - timedelta(days=90)
                    events_deleted = session.query(SecurityEvent).filter(
                        SecurityEvent.timestamp < event_cutoff
                    ).delete(synchronize_session=False)
                    results['deletions']['security_events'] = events_deleted
                    
                    # Delete old notifications (keep for 30 days)
                    notification_cutoff = datetime.utcnow() - timedelta(days=30)
                    notifications_deleted = session.query(Notification).filter(
                        Notification.created_at < notification_cutoff,
                        Notification.read_at.isnot(None)
                    ).delete(synchronize_session=False)
                    results['deletions']['notifications'] = notifications_deleted
                    
                    session.commit()
                
                return results
                
            except Exception as e:
                session.rollback()
                logger.error(f"Data cleanup failed: {str(e)}")
                raise HTTPException(
                    status_code=500,
                    detail="Data cleanup failed"
                )

# Consent management
class ConsentManager:
    """Manage user consent for GDPR compliance."""
    
    def __init__(self, session_factory):
        self.session_factory = session_factory
    
    def record_consent(self, user_id: str, consent_type: str, 
                      granted: bool, ip_address: str, 
                      user_agent: str) -> bool:
        """Record user consent."""
        with self.session_factory() as session:
            consent = ConsentRecord(
                user_id=user_id,
                consent_type=consent_type,
                granted=granted,
                ip_address=ip_address,
                user_agent=user_agent,
                timestamp=datetime.utcnow()
            )
            
            session.add(consent)
            session.commit()
            
            logger.info(f"Consent recorded for user {user_id}: {consent_type} = {granted}")
            return True
    
    def check_consent(self, user_id: str, consent_type: str) -> bool:
        """Check if user has given consent for specific purpose."""
        with self.session_factory() as session:
            latest_consent = session.query(ConsentRecord).filter(
                ConsentRecord.user_id == user_id,
                ConsentRecord.consent_type == consent_type
            ).order_by(desc(ConsentRecord.timestamp)).first()
            
            return latest_consent.granted if latest_consent else False
    
    def withdraw_consent(self, user_id: str, consent_type: str, 
                        ip_address: str) -> bool:
        """Record consent withdrawal."""
        return self.record_consent(user_id, consent_type, False, ip_address, "")

class ConsentRecord(Base):
    """Database model for consent records."""
    __tablename__ = "consent_records"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(String(255), nullable=False)
    consent_type = Column(String(100), nullable=False)
    granted = Column(Boolean, nullable=False)
    ip_address = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
```

---

## Security Best Practices Checklist

### Development Security Checklist
```markdown
# MAFA Security Development Checklist

## Authentication & Authorization
- [ ] All endpoints require authentication (except health checks)
- [ ] JWT tokens have appropriate expiration times
- [ ] Passwords are hashed with bcrypt (cost factor ≥ 12)
- [ ] Multi-factor authentication implemented for admin accounts
- [ ] Session management is secure (no session fixation)
- [ ] Rate limiting implemented on login endpoints
- [ ] Account lockout after failed login attempts

## Data Protection
- [ ] Sensitive data encrypted at rest (database, backups)
- [ ] Sensitive data encrypted in transit (TLS 1.2+)
- [ ] API keys and secrets stored in environment variables
- [ ] No sensitive data logged (passwords, tokens, PII)
- [ ] Data validation on all inputs
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (proper encoding, CSP headers)

## Infrastructure Security
- [ ] Containers run as non-root user
- [ ] Unnecessary packages removed from containers
- [ ] File system permissions properly set
- [ ] Network segmentation implemented
- [ ] Firewall rules configured
- [ ] Regular security updates applied
- [ ] SSL/TLS certificates valid and up-to-date

## API Security
- [ ] Input validation on all endpoints
- [ ] Output encoding to prevent injection
- [ ] Proper error handling (no information leakage)
- [ ] CORS properly configured
- [ ] Rate limiting implemented
- [ ] API versioning implemented
- [ ] Request size limits enforced

## Logging & Monitoring
- [ ] Security events logged with appropriate details
- [ ] Log files protected from tampering
- [ ] Centralized log collection implemented
- [ ] Real-time security monitoring active
- [ ] Alerting configured for security events
- [ ] Regular security reviews scheduled

## Compliance
- [ ] GDPR compliance measures implemented
- [ ] Data retention policies defined and enforced
- [ ] User consent management implemented
- [ ] Data export functionality available
- [ ] Right to erasure implemented
- [ ] Privacy policy up-to-date

## Testing
- [ ] Security testing included in CI/CD pipeline
- [ ] Regular penetration testing scheduled
- [ ] Dependency vulnerability scanning
- [ ] Code security analysis (SAST/DAST)
- [ ] Container image vulnerability scanning
- [ ] Security regression testing
```

### Production Security Checklist
```markdown
# MAFA Production Security Checklist

## System Hardening
- [ ] SSH key-based authentication only
- [ ] SSH port changed from default (22)
- [ ] Root login disabled
- [ ] Unnecessary services disabled
- [ ] Automatic security updates enabled
- [ ] Firewall configured (ufw/iptables)
- [ ] Fail2ban installed and configured

## Network Security
- [ ] All external connections use HTTPS/TLS
- [ ] SSL/TLS certificates from trusted CA
- [ ] HSTS headers configured
- [ ] Secure cipher suites only
- [ ] Certificate pinning where applicable
- [ ] VPN access for administrative tasks

## Database Security
- [ ] Database user has minimal permissions
- [ ] Database access restricted to application
- [ ] Regular database backups encrypted
- [ ] Database access logged
- [ ] Sensitive data encrypted in database
- [ ] Connection encryption enabled

## Application Security
- [ ] Production configuration review completed
- [ ] Debug mode disabled
- [ ] Error messages don't reveal system details
- [ ] Admin interface protected
- [ ] API rate limiting configured
- [ ] Input validation comprehensive

## Monitoring & Incident Response
- [ ] Security monitoring tools configured
- [ ] Log aggregation system active
- [ ] Alerting thresholds defined
- [ ] Incident response plan documented
- [ ] Backup and recovery tested
- [ ] Security team contacts updated
```

---

## Related Documentation

- [Deployment Guide](deployment.md) - Secure deployment procedures
- [System Monitoring](monitoring.md) - Security monitoring setup
- [Backup and Restore](backup-restore.md) - Secure backup procedures
- [Configuration Reference](../getting-started/configuration.md) - Security configuration options
- [Development Setup](../developer-guide/development-setup.md) - Secure development environment

---

**Security Support**: For security-related issues or questions, contact the security team immediately at security@mafa.app or create an issue with the `security` label.