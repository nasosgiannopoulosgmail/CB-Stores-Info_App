"""
Database connection and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
from typing import Generator

# Database URL from environment or default
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:changeme@localhost:5432/coffee_berry"
)

# Create engine with connection pooling
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,  # Verify connections before using
    pool_size=10,  # Number of connections to maintain
    max_overflow=20,  # Additional connections beyond pool_size
    echo=os.getenv("ENVIRONMENT") == "development",  # SQL query logging in dev
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db() -> Generator:
    """
    Dependency for FastAPI to get database session.
    Usage:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Initialize database - create all tables.
    This should typically be done via Alembic migrations instead.
    """
    Base.metadata.create_all(bind=engine)
