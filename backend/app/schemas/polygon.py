"""
Polygon schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Tuple
from datetime import datetime


class Coordinate(BaseModel):
    """Coordinate pair (lon, lat)"""
    longitude: float = Field(..., ge=-180, le=180)
    latitude: float = Field(..., ge=-90, le=90)


class PolygonBase(BaseModel):
    """Base polygon schema"""
    store_id: int
    polygon_type: str = Field(..., pattern="^(dedicated|delivery)$")
    coordinates: List[Tuple[float, float]] = Field(..., min_length=3)
    notes: Optional[str] = None


class PolygonCreate(PolygonBase):
    """Create polygon request"""
    pass


class PolygonUpdate(BaseModel):
    """Update polygon request (creates new version)"""
    coordinates: Optional[List[Tuple[float, float]]] = Field(None, min_length=3)
    notes: Optional[str] = None


class PolygonResponse(BaseModel):
    """Polygon response"""
    id: int
    store_id: int
    polygon_type: str
    coordinates: List[Tuple[float, float]]  # Extracted from geometry
    version_number: int
    is_current: bool
    inactive: bool
    created_at: datetime
    notes: Optional[str] = None
    
    class Config:
        from_attributes = True


class PolygonListResponse(BaseModel):
    """List of polygons response"""
    polygons: list[PolygonResponse]
    total: int
