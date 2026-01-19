"""
Polygon version model with PostGIS geometry
"""
from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey, DateTime, CheckConstraint, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from geoalchemy2 import Geometry
from app.db.database import Base


class PolygonVersion(Base):
    __tablename__ = "polygon_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    store_id = Column(Integer, ForeignKey("stores.id", ondelete="CASCADE"), nullable=False, index=True)
    polygon_type = Column(String(20), nullable=False, index=True)  # 'dedicated' or 'delivery'
    
    # PostGIS geometry (POLYGON in WGS84/EPSG:4326)
    geometry = Column(Geometry('POLYGON', srid=4326), nullable=False, index=True)
    
    # Versioning fields
    version_number = Column(Integer, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    created_by = Column(Integer, nullable=True)  # user_id if user management is added
    inactive = Column(Boolean, default=False, index=True)
    is_current = Column(Boolean, default=False, index=True)
    
    # Metadata
    notes = Column(Text, nullable=True)
    
    # Relationships
    store = relationship("Store", back_populates="polygons")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("polygon_type IN ('dedicated', 'delivery')", name="check_polygon_type"),
        UniqueConstraint("store_id", "polygon_type", "version_number", name="uq_polygon_version"),
    )
    
    def __repr__(self):
        return f"<PolygonVersion(id={self.id}, store_id={self.store_id}, type='{self.polygon_type}', version={self.version_number}, current={self.is_current})>"
