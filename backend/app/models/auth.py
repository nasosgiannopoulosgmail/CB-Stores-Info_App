"""
Authentication models (API Keys and OAuth2)
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, ARRAY, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class APIKey(Base):
    __tablename__ = "api_keys"

    id = Column(Integer, primary_key=True, index=True)
    key_hash = Column(String(255), unique=True, nullable=False)  # Hashed API key (bcrypt)
    name = Column(String(255), nullable=False)
    client_system = Column(String(100), nullable=True, index=True)  # 'bi', 'erp', 'eorder'
    
    # Status
    active = Column(Boolean, default=True, index=True)
    
    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    last_used_at = Column(DateTime(timezone=True), nullable=True)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    # Rate limiting
    rate_limit_per_minute = Column(Integer, default=60)
    
    def __repr__(self):
        return f"<APIKey(id={self.id}, name='{self.name}', client_system='{self.client_system}')>"


class OAuthClient(Base):
    __tablename__ = "oauth_clients"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String(255), unique=True, nullable=False)
    client_secret_hash = Column(String(255), nullable=False)  # Hashed client secret (bcrypt)
    name = Column(String(255), nullable=False)
    redirect_uris = Column(ARRAY(Text), nullable=True)  # Array of allowed redirect URIs
    
    # Status
    active = Column(Boolean, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    tokens = relationship("OAuthToken", back_populates="client")
    
    def __repr__(self):
        return f"<OAuthClient(id={self.id}, client_id='{self.client_id}', name='{self.name}')>"


class OAuthToken(Base):
    __tablename__ = "oauth_tokens"

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(String(255), ForeignKey("oauth_clients.client_id"), nullable=False, index=True)
    access_token_hash = Column(String(255), unique=True, nullable=False)  # Hashed access token
    refresh_token_hash = Column(String(255), unique=True, nullable=True)  # Hashed refresh token
    
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    scopes = Column(ARRAY(Text), default=[])  # Array of permission scopes
    
    # Relationships
    client = relationship("OAuthClient", back_populates="tokens")
    
    def __repr__(self):
        return f"<OAuthToken(id={self.id}, client_id='{self.client_id}')>"
