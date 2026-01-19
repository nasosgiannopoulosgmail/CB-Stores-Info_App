"""
Store model
"""
from sqlalchemy import Column, Integer, String, Numeric, Boolean, Text, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from app.db.database import Base


class Store(Base):
    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    latitude = Column(Numeric(10, 8), nullable=False)
    longitude = Column(Numeric(11, 8), nullable=False)
    
    # External system keys
    entersoft_key = Column(String(100), unique=True, index=True)
    inorder_key = Column(String(100), unique=True, index=True)
    future_proof_key = Column(String(100), unique=True, index=True)
    
    # Current franchisee
    current_franchisee_id = Column(Integer, ForeignKey("franchisees.id", ondelete="SET NULL"), nullable=True)
    
    # Contact information
    address = Column(Text, nullable=True)
    phone = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    
    # Status
    active = Column(Boolean, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships (lazy loading to avoid circular imports)
    franchisee = relationship("Franchisee", foreign_keys=[current_franchisee_id], back_populates="managed_stores")
    polygons = relationship("PolygonVersion", back_populates="store", cascade="all, delete-orphan")
    schedules = relationship("StoreSchedule", back_populates="store", cascade="all, delete-orphan")
    media = relationship("StoreMedia", back_populates="store", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Store(id={self.id}, name='{self.name}')>"
