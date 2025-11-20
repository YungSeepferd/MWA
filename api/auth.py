"""
Authentication and authorization for MWA Core API.

Provides OAuth2 password flow with JWT tokens and role-based access control.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from pathlib import Path
import json

from fastapi import (
    HTTPException, Depends, status, Security
)
from fastapi.security import (
    OAuth2PasswordBearer, OAuth2PasswordRequestForm
)
from fastapi.security.base import SecurityBase
from fastapi.security.utils import get_authorization_scheme_param
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel, Field
import bcrypt

from mwa_core.config.settings import get_settings

logger = logging.getLogger(__name__)

# Security configuration
settings = get_settings()
SECRET_KEY = settings.security.secret_key or "your-secret-key-here-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = settings.security.access_token_expire_minutes or 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/api/v1/auth/token",
    scheme_name="JWT"
)


# User models
class User(BaseModel):
    """User model for authentication."""
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    disabled: bool = False
    roles: List[str] = Field(default_factory=lambda: ["user"])
    
    class Config:
        schema_extra = {
            "example": {
                "username": "admin",
                "email": "admin@example.com",
                "full_name": "Administrator",
                "disabled": False,
                "roles": ["admin"]
            }
        }


class UserInDB(User):
    """User model with hashed password."""
    hashed_password: str


class Token(BaseModel):
    """Token response model."""
    access_token: str
    token_type: str
    expires_in: int
    scope: str = "read write"


class TokenData(BaseModel):
    """Token data for dependency injection."""
    username: Optional[str] = None


class Role(BaseModel):
    """Role model."""
    name: str
    description: str
    permissions: List[str]


# Default users (in production, this would be in a database)
def get_default_users():
    """Get default users with hashed passwords."""
    return {
        "admin": {
            "username": "admin",
            "email": "admin@localhost",
            "full_name": "Administrator",
            "disabled": False,
            "roles": ["admin", "user", "read-only"],
            "hashed_password": pwd_context.hash("admin123")  # Change this in production
        },
        "user": {
            "username": "user",
            "email": "user@localhost",
            "full_name": "Regular User",
            "disabled": False,
            "roles": ["user", "read-only"],
            "hashed_password": pwd_context.hash("user123")  # Change this in production
        },
        "readonly": {
            "username": "readonly",
            "email": "readonly@localhost",
            "full_name": "Read Only User",
            "disabled": False,
            "roles": ["read-only"],
            "hashed_password": pwd_context.hash("readonly123")  # Change this in production
        }
    }

# Lazy initialization of default users
DEFAULT_USERS = None

def _get_default_users():
    """Get default users (lazy initialization)."""
    global DEFAULT_USERS
    if DEFAULT_USERS is None:
        DEFAULT_USERS = get_default_users()
    return DEFAULT_USERS

# Default roles
DEFAULT_ROLES = {
    "admin": Role(
        name="admin",
        description="Administrator with full access",
        permissions=[
            "read:config", "write:config",
            "read:listings", "write:listings", "delete:listings",
            "read:contacts", "write:contacts", "delete:contacts",
            "read:scraper", "write:scraper",
            "read:scheduler", "write:scheduler", "delete:scheduler",
            "read:system", "write:system",
            "read:auth", "write:auth",
            "read:users", "write:users"
        ]
    ),
    "user": Role(
        name="user",
        description="Regular user with read/write access",
        permissions=[
            "read:config",
            "read:listings", "write:listings",
            "read:contacts", "write:contacts",
            "read:scraper", "write:scraper",
            "read:scheduler", "write:scheduler",
            "read:system"
        ]
    ),
    "read-only": Role(
        name="read-only",
        description="Read-only access to most data",
        permissions=[
            "read:config",
            "read:listings",
            "read:contacts",
            "read:scraper",
            "read:scheduler",
            "read:system"
        ]
    )
}


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def get_user(username: str) -> Optional[UserInDB]:
    """Get user by username from in-memory storage."""
    users = _get_default_users()
    if username in users:
        user_data = users[username].copy()
        return UserInDB(**user_data)
    return None


def authenticate_user(username: str, password: str) -> Optional[UserInDB]:
    """Authenticate user with username and password."""
    user = get_user(username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def verify_token(token: str) -> Optional[TokenData]:
    """Verify JWT token and return token data."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        token_data = TokenData(username=username)
        return token_data
    except JWTError:
        return None


async def get_current_user(token: str = Security(oauth2_scheme)) -> UserInDB:
    """Get current authenticated user."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    token_data = verify_token(token)
    if token_data is None:
        raise credentials_exception
    
    user = get_user(username=token_data.username)
    if user is None:
        raise credentials_exception
    
    return user


async def get_current_active_user(current_user: UserInDB = Depends(get_current_user)) -> UserInDB:
    """Get current active user (not disabled)."""
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user
# Initialize router with endpoints
from fastapi import APIRouter
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/token", response_model=Token, summary="Obtain access token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    OAuth2 compatible token login, get an access token for future requests.
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "scopes": " ".join(user.roles)},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "scope": " ".join(user.roles)
    }

@router.get("/me", response_model=User, summary="Get current user info")
async def read_users_me(current_user: UserInDB = Depends(get_current_active_user)):
    """
    Get current user information.
    """
    return current_user

@router.get("/roles", response_model=Dict[str, Role], summary="Get available roles")
async def get_roles(current_user: UserInDB = Depends(get_current_active_user)):
    """
    Get list of available roles and their permissions.
    """
    return DEFAULT_ROLES

@router.post("/refresh", response_model=Token, summary="Refresh access token")
async def refresh_token(current_user: UserInDB = Depends(get_current_active_user)):
    """
    Refresh the access token.
    """
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": current_user.username, "scopes": " ".join(current_user.roles)},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer", 
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        "scope": " ".join(current_user.roles)
    }


def require_permissions(required_permissions: List[str]):
    """Decorator to require specific permissions."""
    async def permission_checker(current_user: UserInDB = Depends(get_current_active_user)) -> UserInDB:
        user_permissions = set()
        for role_name in current_user.roles:
            if role_name in DEFAULT_ROLES:
                user_permissions.update(DEFAULT_ROLES[role_name].permissions)
        
        for permission in required_permissions:
            if permission not in user_permissions:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Not enough permissions. Required: {permission}"
                )
        
        return current_user
    
    return permission_checker


# Permission requirements for different endpoints
require_admin = require_permissions(["admin:*"])
require_config_read = require_permissions(["read:config"])
require_config_write = require_permissions(["write:config"])
require_listings_read = require_permissions(["read:listings"])
require_listings_write = require_permissions(["write:listings"])
require_contacts_read = require_permissions(["read:contacts"])
require_contacts_write = require_permissions(["write:contacts"])
require_scraper_read = require_permissions(["read:scraper"])
require_scraper_write = require_permissions(["write:scraper"])
require_scheduler_read = require_permissions(["read:scheduler"])
require_scheduler_write = require_permissions(["write:scheduler"])
require_system_read = require_permissions(["read:system"])
require_system_write = require_permissions(["write:system"])


# Security scheme for Swagger documentation
class JWTSecurity(SecurityBase):
    """JWT security scheme for FastAPI."""
    def __init__(self, bearer_format: str = "JWT"):
        self.bearer_format = bearer_format
        self.scheme_name = "JWT"
        self.type = "http"
        self.scheme = "bearer"
        self.bearer_format = bearer_format

    async def __call__(self, request):
        authorization = request.headers.get("Authorization")
        scheme, credentials = get_authorization_scheme_param(authorization)
        if scheme.lower() != "bearer":
            return None
        return credentials


# Export router and dependencies
__all__ = [
    "User", "UserInDB", "Token", "TokenData",
    "get_current_user", "get_current_active_user",
    "require_admin", "require_config_read", "require_config_write",
    "require_listings_read", "require_listings_write",
    "require_contacts_read", "require_contacts_write", 
    "require_scraper_read", "require_scraper_write",
    "require_scheduler_read", "require_scheduler_write",
    "require_system_read", "require_system_write",
    "oauth2_scheme", "JWTSecurity", "DEFAULT_ROLES"
]