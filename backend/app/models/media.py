"""
Store media model (pictures)
"""
from sqlalchemy import Column, Integer, String, BigInteger, Text, Boolean, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class StoreMedia(Base):
    __tablename__ = "store_media"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    franchisee_id = Column(Integer, ForeignKey("franchisees.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # File information
    file_path = Column(String(500), nullable=False)
    file_name = Column(String(255), nullable=False)
    file_size = Column(BigInteger, nullable=True)
    mime_type = Column(String(100), nullable=True)
    
    # Metadata
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    uploaded_by = Column(Integer, nullable=True)  # user_id if user management is added
    description = Column(Text, nullable=True)
    is_primary = Column(Boolean, default=False)
    
    # Relationships
    store = relationship("Store", back_populates="media")
    franchisee = relationship("Franchisee", back_populates="media")
    
    # Constraints - only one primary image per store
    __table_args__ = (
        # Using partial unique index - handled at database level via trigger or application logic
    )
    
    def __repr__(self):
        return f"<StoreMedia(id={self.id}, store_id={self.store_id}, file_name='{self.file_name}')>"
