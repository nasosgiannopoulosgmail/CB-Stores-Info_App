"""
Polygon management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import Optional, List
from app.db.database import get_db
from app.models.polygon import PolygonVersion
from app.models.store import Store
from app.schemas.polygon import PolygonCreate, PolygonUpdate, PolygonResponse, PolygonListResponse
from app.api.dependencies import verify_api_key

router = APIRouter()


def _extract_coordinates_from_geometry(geometry_wkb) -> List[tuple]:
    """Extract coordinates from PostGIS geometry"""
    # Query geometry as WKT
    from sqlalchemy import text
    result = text("SELECT ST_AsText(:geom) as wkt")
    # This is a simplified version - in production, use proper geometry parsing
    # For now, we'll extract coordinates via SQL
    return []


@router.get("/stores/{store_id}/polygons", response_model=PolygonListResponse)
async def get_store_polygons(
    store_id: int,
    current_only: bool = Query(True),
    polygon_type: Optional[str] = None,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key)
):
    """Get all polygons for a store"""
    # Verify store exists
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store {store_id} not found"
        )
    
    query = db.query(PolygonVersion).filter(PolygonVersion.store_id == store_id)
    
    if current_only:
        query = query.filter(
            PolygonVersion.is_current == True,
            PolygonVersion.inactive == False
        )
    
    if polygon_type:
        query = query.filter(PolygonVersion.polygon_type == polygon_type)
    
    polygons = query.order_by(PolygonVersion.version_number.desc()).all()
    
    # Extract coordinates from geometry
    polygon_responses = []
    for pv in polygons:
        # Get coordinates via SQL
        result = db.execute(
            text("""
                SELECT ST_AsText(geometry) as wkt
                FROM polygon_versions
                WHERE id = :id
            """),
            {"id": pv.id}
        )
        wkt = result.scalar()
        
        # Parse WKT to extract coordinates
        # Simplified: POLYGON((lon1 lat1, lon2 lat2, ...))
        coords = []
        if wkt:
            # Extract coordinates from WKT string
            import re
            coord_pattern = r'([\d\.-]+)\s+([\d\.-]+)'
            matches = re.findall(coord_pattern, wkt)
            coords = [(float(lon), float(lat)) for lon, lat in matches]
        
        polygon_responses.append(PolygonResponse(
            id=pv.id,
            store_id=pv.store_id,
            polygon_type=pv.polygon_type,
            coordinates=coords,
            version_number=pv.version_number,
            is_current=pv.is_current,
            inactive=pv.inactive,
            created_at=pv.created_at,
            notes=pv.notes
        ))
    
    return PolygonListResponse(
        polygons=polygon_responses,
        total=len(polygon_responses)
    )


@router.get("/stores/{store_id}/polygons/current", response_model=List[PolygonResponse])
async def get_current_polygons(
    store_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key)
):
    """Get current polygons for a store"""
    return await get_store_polygons(store_id, current_only=True, polygon_type=None, db=db, _=_)


@router.post("/stores/{store_id}/polygons", response_model=PolygonResponse, status_code=status.HTTP_201_CREATED)
async def create_polygon(
    store_id: int,
    polygon: PolygonCreate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key)
):
    """Create a new polygon version"""
    # Verify store exists
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store {store_id} not found"
        )
    
    # Get next version number
    latest = db.query(PolygonVersion).filter(
        PolygonVersion.store_id == store_id,
        PolygonVersion.polygon_type == polygon.polygon_type
    ).order_by(PolygonVersion.version_number.desc()).first()
    
    next_version = (latest.version_number + 1) if latest else 1
    
    # If there's a current version, set it to inactive
    if latest and latest.is_current:
        latest.is_current = False
    
    # Ensure polygon is closed
    coords = polygon.coordinates
    if coords[0] != coords[-1]:
        coords.append(coords[0])
    
    # Create PostGIS geometry WKT
    coords_str = ', '.join([f"{lon} {lat}" for lon, lat in coords])
    geometry_wkt = f"POLYGON(({coords_str}))"
    
    # Create polygon version using raw SQL for geometry
    from sqlalchemy import text
    result = db.execute(
        text("""
            INSERT INTO polygon_versions 
            (store_id, polygon_type, geometry, version_number, is_current, inactive, notes)
            VALUES (:store_id, :polygon_type, ST_SetSRID(ST_GeomFromText(:geometry_wkt), 4326), 
                    :version_number, true, false, :notes)
            RETURNING id, created_at
        """),
        {
            "store_id": store_id,
            "polygon_type": polygon.polygon_type,
            "geometry_wkt": geometry_wkt,
            "version_number": next_version,
            "notes": polygon.notes or ""
        }
    )
    row = result.fetchone()
    polygon_id = row[0]
    
    db.commit()
    
    # Fetch the created polygon
    db_polygon = db.query(PolygonVersion).filter(PolygonVersion.id == polygon_id).first()
    
    # Extract coordinates for response
    result = db.execute(
        text("SELECT ST_AsText(geometry) as wkt FROM polygon_versions WHERE id = :id"),
        {"id": polygon_id}
    )
    wkt = result.scalar()
    import re
    coord_pattern = r'([\d\.-]+)\s+([\d\.-]+)'
    matches = re.findall(coord_pattern, wkt)
    extracted_coords = [(float(lon), float(lat)) for lon, lat in matches]
    
    return PolygonResponse(
        id=db_polygon.id,
        store_id=db_polygon.store_id,
        polygon_type=db_polygon.polygon_type,
        coordinates=extracted_coords,
        version_number=db_polygon.version_number,
        is_current=db_polygon.is_current,
        inactive=db_polygon.inactive,
        created_at=db_polygon.created_at,
        notes=db_polygon.notes
    )


@router.put("/{polygon_id}", response_model=PolygonResponse)
async def update_polygon(
    polygon_id: int,
    polygon: PolygonUpdate,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key)
):
    """Update polygon (creates new version)"""
    old_polygon = db.query(PolygonVersion).filter(PolygonVersion.id == polygon_id).first()
    
    if not old_polygon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Polygon {polygon_id} not found"
        )
    
    # Create new version
    update_data = polygon.dict(exclude_unset=True)
    coords = update_data.get('coordinates', None)
    
    if coords:
        # Ensure polygon is closed
        if coords[0] != coords[-1]:
            coords.append(coords[0])
        
        coords_str = ', '.join([f"{lon} {lat}" for lon, lat in coords])
        geometry_wkt = f"POLYGON(({coords_str}))"
    else:
        # Use existing geometry - cannot update without new coordinates
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New coordinates required for polygon update"
        )
    
    # Get next version
    next_version = old_polygon.version_number + 1
    
    # Set old version as inactive
    old_polygon.is_current = False
    
    # Create new version using raw SQL
    result = db.execute(
        text("""
            INSERT INTO polygon_versions 
            (store_id, polygon_type, geometry, version_number, is_current, inactive, notes)
            VALUES (:store_id, :polygon_type, ST_SetSRID(ST_GeomFromText(:geometry_wkt), 4326), 
                    :version_number, true, false, :notes)
            RETURNING id, created_at
        """),
        {
            "store_id": old_polygon.store_id,
            "polygon_type": old_polygon.polygon_type,
            "geometry_wkt": geometry_wkt,
            "version_number": next_version,
            "notes": update_data.get('notes', old_polygon.notes) or ""
        }
    )
    row = result.fetchone()
    new_polygon_id = row[0]
    
    db.commit()
    
    # Fetch the created polygon
    new_polygon = db.query(PolygonVersion).filter(PolygonVersion.id == new_polygon_id).first()
    
    # Extract coordinates for response
    result = db.execute(
        text("SELECT ST_AsText(geometry) as wkt FROM polygon_versions WHERE id = :id"),
        {"id": new_polygon_id}
    )
    wkt = result.scalar()
    import re
    coord_pattern = r'([\d\.-]+)\s+([\d\.-]+)'
    matches = re.findall(coord_pattern, wkt)
    final_coords = [(float(lon), float(lat)) for lon, lat in matches]
    
    return PolygonResponse(
        id=new_polygon.id,
        store_id=new_polygon.store_id,
        polygon_type=new_polygon.polygon_type,
        coordinates=final_coords,
        version_number=new_polygon.version_number,
        is_current=new_polygon.is_current,
        inactive=new_polygon.inactive,
        created_at=new_polygon.created_at,
        notes=new_polygon.notes
    )


@router.get("/{polygon_id}/history", response_model=PolygonListResponse)
async def get_polygon_history(
    polygon_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key)
):
    """Get version history for a polygon"""
    polygon = db.query(PolygonVersion).filter(PolygonVersion.id == polygon_id).first()
    
    if not polygon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Polygon {polygon_id} not found"
        )
    
    # Get all versions for this store+type
    all_versions = db.query(PolygonVersion).filter(
        PolygonVersion.store_id == polygon.store_id,
        PolygonVersion.polygon_type == polygon.polygon_type
    ).order_by(PolygonVersion.version_number.asc()).all()
    
    # Extract coordinates (simplified - same as above)
    polygon_responses = []
    for pv in all_versions:
        result = db.execute(
            text("SELECT ST_AsText(geometry) as wkt FROM polygon_versions WHERE id = :id"),
            {"id": pv.id}
        )
        wkt = result.scalar()
        import re
        coords = []
        if wkt:
            coord_pattern = r'([\d\.-]+)\s+([\d\.-]+)'
            matches = re.findall(coord_pattern, wkt)
            coords = [(float(lon), float(lat)) for lon, lat in matches]
        
        polygon_responses.append(PolygonResponse(
            id=pv.id,
            store_id=pv.store_id,
            polygon_type=pv.polygon_type,
            coordinates=coords,
            version_number=pv.version_number,
            is_current=pv.is_current,
            inactive=pv.inactive,
            created_at=pv.created_at,
            notes=pv.notes
        ))
    
    return PolygonListResponse(
        polygons=polygon_responses,
        total=len(polygon_responses)
    )


@router.delete("/{polygon_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_polygon(
    polygon_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key)
):
    """Mark polygon version as inactive"""
    polygon = db.query(PolygonVersion).filter(PolygonVersion.id == polygon_id).first()
    
    if not polygon:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Polygon {polygon_id} not found"
        )
    
    polygon.inactive = True
    polygon.is_current = False
    
    db.commit()
    
    return None
