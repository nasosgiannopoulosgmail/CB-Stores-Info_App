"""
FastAPI dependencies
"""
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional
import bcrypt
import hashlib
from datetime import datetime, timezone

from app.db.database import get_db
from app.models.auth import APIKey, OAuthToken
from app.config import settings


security = HTTPBearer()


def get_database(db: Session = Depends(get_db)):
    """Dependency to get database session"""
    return db


async def verify_api_key(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    db: Session = Depends(get_db)
) -> APIKey:
    """
    Verify API key from header
    Usage: @app.get("/endpoint", dependencies=[Depends(verify_api_key)])
    """
    if not x_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key required"
        )
    
    # Hash the provided API key
    key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
    
    # Find API key in database
    api_key = db.query(APIKey).filter(APIKey.key_hash == key_hash).first()
    
    if not api_key or not api_key.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or inactive API key"
        )
    
    # Check expiration
    if api_key.expires_at and api_key.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key has expired"
        )
    
    # Update last used timestamp
    api_key.last_used_at = datetime.now(timezone.utc)
    db.commit()
    
    return api_key


async def verify_oauth_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> OAuthToken:
    """
    Verify OAuth2 access token
    Usage: @app.get("/endpoint", dependencies=[Depends(verify_oauth_token)])
    """
    token = credentials.credentials
    
    # Hash the token to compare
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    
    # Find token in database
    oauth_token = db.query(OAuthToken).filter(
        OAuthToken.access_token_hash == token_hash
    ).first()
    
    if not oauth_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid access token"
        )
    
    # Check expiration
    if oauth_token.expires_at < datetime.now(timezone.utc):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Access token has expired"
        )
    
    # Get client
    from app.models.auth import OAuthClient
    client = db.query(OAuthClient).filter(
        OAuthClient.client_id == oauth_token.client_id
    ).first()
    
    if not client or not client.active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Client is inactive"
        )
    
    return oauth_token


def require_auth(
    api_key: Optional[APIKey] = Depends(verify_api_key),
    oauth_token: Optional[OAuthToken] = Depends(verify_oauth_token)
):
    """
    Dependency that accepts either API key or OAuth token
    Usage: @app.get("/endpoint", dependencies=[Depends(require_auth)])
    """
    # This will raise an exception if neither is valid
    # The actual check is done in the individual verify functions
    pass
