"""
Geospatial service - optimized queries for point-in-polygon checks
"""
from sqlalchemy.orm import Session
from sqlalchemy import text
from typing import List, Dict, Tuple, Optional
from app.models.store import Store
from app.models.polygon import PolygonVersion


class GeospatialService:
    """Service for geospatial queries optimized with PostGIS"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def check_point_in_polygons(
        self,
        latitude: float,
        longitude: float,
        polygon_type: Optional[str] = None,
        store_id: Optional[int] = None
    ) -> List[Dict]:
        """
        Check if a point is contained in any polygons
        Optimized query using PostGIS spatial indexes
        Returns list of stores with polygons containing the point
        """
        point_wkt = f"POINT({longitude} {latitude})"
        
        query = """
            SELECT DISTINCT 
                s.id as store_id,
                s.name as store_name,
                s.latitude,
                s.longitude,
                pv.id as polygon_id,
                pv.polygon_type,
                pv.version_number
            FROM stores s
            INNER JOIN polygon_versions pv ON s.id = pv.store_id
            WHERE pv.is_current = true 
              AND pv.inactive = false
              AND s.active = true
              AND ST_Contains(pv.geometry, ST_SetSRID(ST_GeomFromText(:point_wkt), 4326))
        """
        
        params = {"point_wkt": point_wkt}
        
        if polygon_type:
            query += " AND pv.polygon_type = :polygon_type"
            params["polygon_type"] = polygon_type
        
        if store_id:
            query += " AND s.id = :store_id"
            params["store_id"] = store_id
        
        result = self.db.execute(text(query), params)
        rows = result.fetchall()
        
        return [
            {
                "store_id": row.store_id,
                "store_name": row.store_name,
                "latitude": float(row.latitude),
                "longitude": float(row.longitude),
                "polygon_id": row.polygon_id,
                "polygon_type": row.polygon_type,
                "version_number": row.version_number
            }
            for row in rows
        ]
    
    def check_bulk_points(
        self,
        points: List[Tuple[float, float]],  # List of (latitude, longitude)
        polygon_type: Optional[str] = None
    ) -> List[Dict]:
        """
        Bulk point-in-polygon check
        Optimized for multiple points (up to 1000)
        Returns list of results for each point
        """
        results = []
        
        for lat, lon in points:
            stores = self.check_point_in_polygons(lat, lon, polygon_type)
            results.append({
                "point": {"latitude": lat, "longitude": lon},
                "contained": len(stores) > 0,
                "stores": stores
            })
        
        return results
    
    def find_overlaps(
        self,
        store_id: Optional[int] = None,
        polygon_type: Optional[str] = None,
        between_stores: bool = False
    ) -> List[Dict]:
        """
        Find overlapping polygons
        Returns list of overlapping polygon pairs
        """
        query = """
            SELECT 
                p1.id as polygon1_id,
                p1.store_id as polygon1_store_id,
                s1.name as polygon1_store_name,
                p2.id as polygon2_id,
                p2.store_id as polygon2_store_id,
                s2.name as polygon2_store_name,
                p1.polygon_type,
                ST_Area(ST_Intersection(p1.geometry, p2.geometry)) as overlap_area
            FROM polygon_versions p1
            JOIN stores s1 ON p1.store_id = s1.id
            JOIN polygon_versions p2 ON p1.id < p2.id
            JOIN stores s2 ON p2.store_id = s2.id
            WHERE p1.is_current = true 
              AND p2.is_current = true
              AND p1.inactive = false
              AND p2.inactive = false
              AND ST_Overlaps(p1.geometry, p2.geometry)
        """
        
        params = {}
        
        if polygon_type:
            query += " AND p1.polygon_type = :polygon_type AND p2.polygon_type = :polygon_type"
            params["polygon_type"] = polygon_type
        
        if store_id:
            query += " AND (p1.store_id = :store_id OR p2.store_id = :store_id)"
            params["store_id"] = store_id
        
        if between_stores:
            query += " AND p1.store_id != p2.store_id"
        
        result = self.db.execute(text(query), params)
        rows = result.fetchall()
        
        return [
            {
                "polygon1_id": row.polygon1_id,
                "polygon1_store_id": row.polygon1_store_id,
                "polygon1_store_name": row.polygon1_store_name,
                "polygon2_id": row.polygon2_id,
                "polygon2_store_id": row.polygon2_store_id,
                "polygon2_store_name": row.polygon2_store_name,
                "polygon_type": row.polygon_type,
                "overlap_area": float(row.overlap_area) if row.overlap_area else 0.0
            }
            for row in rows
        ]
    
    def get_store_by_point(
        self,
        latitude: float,
        longitude: float,
        polygon_type: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Get store(s) for a given point
        Returns first matching store or None
        """
        stores = self.check_point_in_polygons(latitude, longitude, polygon_type)
        return stores[0] if stores else None
