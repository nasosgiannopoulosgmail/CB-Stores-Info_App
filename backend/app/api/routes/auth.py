"""
Authentication endpoints (OAuth2 and API Keys)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasicCredentials, HTTPBasic
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta, timezone
import secrets
import bcrypt
import hashlib

from app.db.database import get_db
from app.models.auth import APIKey, OAuthClient, OAuthToken
from app.config import settings

router = APIRouter()
security_basic = HTTPBasic()


class OAuthTokenRequest(BaseModel):
    """OAuth2 token request"""
    grant_type: str = "client_credentials"
    scope: str = ""


class OAuthTokenResponse(BaseModel):
    """OAuth2 token response"""
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    refresh_token: Optional[str] = None


class APIKeyCreate(BaseModel):
    """Create API key request"""
    name: str
    client_system: Optional[str] = None
    expires_days: Optional[int] = None
    rate_limit_per_minute: int = 60


class APIKeyResponse(BaseModel):
    """API key response (only on creation)"""
    id: int
    name: str
    api_key: str  # Only shown once!
    client_system: Optional[str]
    created_at: datetime


@router.post("/oauth/token", response_model=OAuthTokenResponse)
async def get_oauth_token(
    request: OAuthTokenRequest,
    credentials: HTTPBasicCredentials = Depends(security_basic),
    db: Session = Depends(get_db)
):
    """
    OAuth2 client credentials flow token endpoint
    Requires HTTP Basic Auth with client_id and client_secret
    """
    # Find client
    client = db.query(OAuthClient).filter(
        OAuthClient.client_id == credentials.username
    ).first()
    
    if not client or not client.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client credentials"
        )
    
    # Verify client secret (hashed with bcrypt)
    if not bcrypt.checkpw(
        credentials.password.encode('utf-8'),
        client.client_secret_hash.encode('utf-8')
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid client credentials"
        )
    
    # Generate access token
    access_token = secrets.token_urlsafe(32)
    refresh_token = secrets.token_urlsafe(32)
    
    # Hash tokens for storage
    access_token_hash = hashlib.sha256(access_token.encode()).hexdigest()
    refresh_token_hash = hashlib.sha256(refresh_token.encode()).hexdigest()
    
    # Create token record
    expires_at = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    
    oauth_token = OAuthToken(
        client_id=client.client_id,
        access_token_hash=access_token_hash,
        refresh_token_hash=refresh_token_hash,
        expires_at=expires_at,
        scopes=request.scope.split() if request.scope else []
    )
    
    db.add(oauth_token)
    db.commit()
    
    return OAuthTokenResponse(
        access_token=access_token,
        token_type="Bearer",
        expires_in=settings.access_token_expire_minutes * 60,
        refresh_token=refresh_token
    )


@router.post("/api-key/create", response_model=APIKeyResponse)
async def create_api_key(
    request: APIKeyCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new API key
    Note: The key is only shown once on creation!
    """
    # Generate API key
    api_key = f"cb_{secrets.token_urlsafe(32)}"
    
    # Hash the key for storage
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    
    # Create API key record
    expires_at = None
    if request.expires_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=request.expires_days)
    
    api_key_record = APIKey(
        key_hash=key_hash,
        name=request.name,
        client_system=request.client_system,
        active=True,
        expires_at=expires_at,
        rate_limit_per_minute=request.rate_limit_per_minute
    )
    
    db.add(api_key_record)
    db.commit()
    db.refresh(api_key_record)
    
    return APIKeyResponse(
        id=api_key_record.id,
        name=api_key_record.name,
        api_key=api_key,  # Only time the key is shown!
        client_system=api_key_record.client_system,
        created_at=api_key_record.created_at
    )


@router.post("/api-key/validate")
async def validate_api_key(
    x_api_key: str,
    db: Session = Depends(get_db)
):
    """Validate an API key"""
    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    
    api_key = db.query(APIKey).filter(APIKey.key_hash == key_hash).first()
    
    if not api_key or not api_key.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key"
        )
    
    if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired"
        )
    
    return {
        "valid": True,
        "name": api_key.name,
        "client_system": api_key.client_system
    }
