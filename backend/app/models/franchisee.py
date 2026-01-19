"""
Franchisee model
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class Franchisee(Base):
    __tablename__ = "franchisees"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    company_name = Column(String(255), nullable=True)
    
    # External system keys
    entersoft_key = Column(String(100), unique=True, nullable=True)
    inorder_key = Column(String(100), unique=True, nullable=True)
    future_proof_key = Column(String(100), unique=True, nullable=True)
    
    # Contact information
    contact_email = Column(String(255), nullable=True)
    contact_phone = Column(String(50), nullable=True)
    
    # Status
    active = Column(Boolean, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    managed_stores = relationship("Store", foreign_keys="Store.current_franchisee_id", back_populates="franchisee")
    media = relationship("StoreMedia", back_populates="franchisee")
    
    def __repr__(self):
        return f"<Franchisee(id={self.id}, name='{self.name}')>"
