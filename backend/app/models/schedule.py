"""
Store schedule model
"""
from sqlalchemy import Column, Integer, Boolean, Date, DateTime, ForeignKey, CheckConstraint, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.database import Base


class StoreSchedule(Base):
    __tablename__ = "store_schedules"

    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Day of week: 0=Monday, 1=Tuesday, ..., 6=Sunday
    day_of_week = Column(Integer, nullable=False)
    
    # Multiple time ranges per day stored as JSONB
    # Format: [{"start": "08:00", "end": "14:00"}, {"start": "17:00", "end": "20:00"}]
    time_ranges = Column(JSONB, nullable=False, server_default='[]')
    
    # Special dates
    is_holiday = Column(Boolean, default=False)
    date_override = Column(Date, nullable=True)  # For specific date overrides
    
    # Status
    active = Column(Boolean, default=True, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    store = relationship("Store", back_populates="schedules")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("day_of_week BETWEEN 0 AND 6", name="check_day_of_week"),
        UniqueConstraint("store_id", "day_of_week", "date_override", name="uq_store_schedule"),
    )
    
    def __repr__(self):
        return f"<StoreSchedule(id={self.id}, store_id={self.store_id}, day={self.day_of_week})>"
