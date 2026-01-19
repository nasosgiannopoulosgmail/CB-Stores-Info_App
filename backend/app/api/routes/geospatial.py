"""
Geospatial query endpoints (optimized for data warehouse)
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db.database import get_db
from app.schemas.geospatial import (
    PointCheckRequest, PointCheckResponse,
    BulkPointCheckRequest, BulkPointCheckResponse,
    OverlapRequest, OverlapResponse
)
from app.services.geospatial import GeospatialService
from app.api.dependencies import verify_api_key

router = APIRouter()


@router.post("/check-point", response_model=PointCheckResponse)
async def check_point(
    request: PointCheckRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key)
):
    """
    Check if a single point is contained in any polygons
    Optimized query using PostGIS spatial indexes
    """
    service = GeospatialService(db)
    
    stores = service.check_point_in_polygons(
        latitude=request.point.latitude,
        longitude=request.point.longitude,
        polygon_type=request.polygon_type,
        store_id=request.store_id
    )
    
    return PointCheckResponse(
        point=request.point,
        contained=len(stores) > 0,
        stores=stores
    )


@router.post("/check-bulk", response_model=BulkPointCheckResponse)
async def check_bulk_points(
    request: BulkPointCheckRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key)
):
    """
    Bulk point-in-polygon check
    Accepts up to 1000 points for batch processing
    Optimized for data warehouse queries
    """
    if len(request.points) > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Maximum 1000 points allowed per request"
        )
    
    service = GeospatialService(db)
    
    # Convert to list of tuples
    points_tuples = [(p.latitude, p.longitude) for p in request.points]
    
    results = service.check_bulk_points(
        points=points_tuples,
        polygon_type=request.polygon_type
    )
    
    total_contained = sum(1 for r in results if r['contained'])
    
    return BulkPointCheckResponse(
        results=[
            PointCheckResponse(**r) for r in results
        ],
        total_checked=len(results),
        total_contained=total_contained
    )


@router.get("/store-by-point")
async def get_store_by_point(
    latitude: float,
    longitude: float,
    polygon_type: str = None,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key)
):
    """
    Get store(s) for a given point
    Returns first matching store or null
    """
    service = GeospatialService(db)
    
    store = service.get_store_by_point(
        latitude=latitude,
        longitude=longitude,
        polygon_type=polygon_type
    )
    
    return store if store else None


@router.get("/overlaps", response_model=List[OverlapResponse])
async def find_overlaps(
    store_id: int = None,
    polygon_type: str = None,
    between_stores: bool = False,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key)
):
    """
    Find overlapping polygons
    Returns list of overlapping polygon pairs
    """
    service = GeospatialService(db)
    
    overlaps = service.find_overlaps(
        store_id=store_id,
        polygon_type=polygon_type,
        between_stores=between_stores
    )
    
    return [
        OverlapResponse(**overlap) for overlap in overlaps
    ]
