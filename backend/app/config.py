"""
Application configuration
"""
import os
from typing import List, Optional
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings"""
    
    # Application
    app_name: str = "Coffee-Berry Stores Management API"
    app_version: str = "1.0.0"
    environment: str = os.getenv("ENVIRONMENT", "development")
    debug: bool = os.getenv("ENVIRONMENT", "development") == "development"
    
    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://postgres:changeme@localhost:5432/coffee_berry"
    )
    
    # Redis (optional)
    redis_url: Optional[str] = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    
    # Security
    secret_key: str = os.getenv("SECRET_KEY", "changeme-secret-key-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = int(os.getenv("JWT_ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    refresh_token_expire_days: int = int(os.getenv("JWT_REFRESH_TOKEN_EXPIRE_DAYS", "7"))
    
    # CORS
    cors_origins: List[str] = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:5173"
    ).split(",")
    
    # API Rate Limiting
    rate_limit_per_minute: int = int(os.getenv("RATE_LIMIT_PER_MINUTE", "60"))
    
    # Media Storage
    media_root: str = os.getenv("MEDIA_ROOT", "/app/media")
    max_upload_size: int = int(os.getenv("MAX_UPLOAD_SIZE", "10485760"))  # 10MB
    
    # Google Maps API (for frontend)
    google_maps_api_key: Optional[str] = os.getenv("GOOGLE_MAPS_API_KEY")
    
    class Config:
        env_file = ".env"
        case_sensitive = False


settings = Settings()
