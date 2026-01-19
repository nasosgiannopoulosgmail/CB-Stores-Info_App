"""
Geospatial query schemas
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class Point(BaseModel):
    """Geographic point"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)


class PointCheckRequest(BaseModel):
    """Single point check request"""
    point: Point
    polygon_type: Optional[str] = Field(None, pattern="^(dedicated|delivery)$")
    store_id: Optional[int] = None


class PointCheckResponse(BaseModel):
    """Point check response"""
    point: Point
    contained: bool
    stores: List[dict]  # List of stores containing the point


class BulkPointCheckRequest(BaseModel):
    """Bulk point check request"""
    points: List[Point] = Field(..., max_length=1000)
    polygon_type: Optional[str] = Field(None, pattern="^(dedicated|delivery)$")


class BulkPointCheckResponse(BaseModel):
    """Bulk point check response"""
    results: List[PointCheckResponse]
    total_checked: int
    total_contained: int


class OverlapRequest(BaseModel):
    """Overlap detection request"""
    store_id: Optional[int] = None
    polygon_type: Optional[str] = Field(None, pattern="^(dedicated|delivery)$")
    between_stores: bool = False  # Only check overlaps between different stores


class OverlapResponse(BaseModel):
    """Overlap response"""
    polygon1_id: int
    polygon1_store_id: int
    polygon1_store_name: str
    polygon2_id: int
    polygon2_store_id: int
    polygon2_store_name: str
    polygon_type: str
    overlap_area: float  # In square degrees (approximate)
