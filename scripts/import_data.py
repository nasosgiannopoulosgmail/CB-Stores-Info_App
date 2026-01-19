"""
Database Import Script
Imports normalized store and polygon data into PostgreSQL database
"""
import json
import sys
import os
from pathlib import Path
from typing import List, Dict
import psycopg2
from psycopg2.extras import execute_values
from psycopg2.extras import RealDictCursor
import argparse


# Add parent directory to path to import models
sys.path.insert(0, str(Path(__file__).parent.parent))

from shapely.geometry import Polygon, Point
from shapely.wkb import dumps as wkb_dumps
from shapely.ops import transform
import pyproj


class DatabaseImporter:
    """Imports normalized data into PostgreSQL database"""
    
    def __init__(self, database_url: str):
        self.conn = psycopg2.connect(database_url)
        self.conn.autocommit = False
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type:
            self.conn.rollback()
        else:
            self.conn.commit()
        self.conn.close()
    
    def import_stores(self, stores: List[Dict], dry_run: bool = False) -> Dict:
        """Import stores into database"""
        imported = []
        errors = []
        
        for store in stores:
            try:
                if dry_run:
                    print(f"Would import store: {store['normalized_name']}")
                    imported.append(store)
                    continue
                
                cursor = self.conn.cursor()
                
                # Check if store already exists (by entersoft_key, inorder_key, or name+location)
                cursor.execute("""
                    SELECT id FROM stores 
                    WHERE (entersoft_key = %s AND entersoft_key IS NOT NULL)
                       OR (inorder_key = %s AND inorder_key IS NOT NULL)
                       OR (name = %s AND latitude = %s AND longitude = %s)
                    LIMIT 1
                """, (
                    store.get('entersoft_key'),
                    store.get('inorder_key'),
                    store.get('normalized_name'),
                    store['latitude'],
                    store['longitude']
                ))
                
                existing = cursor.fetchone()
                
                if existing:
                    store_id = existing[0]
                    # Update existing store
                    cursor.execute("""
                        UPDATE stores 
                        SET name = %s,
                            latitude = %s,
                            longitude = %s,
                            entersoft_key = COALESCE(%s, entersoft_key),
                            inorder_key = COALESCE(%s, inorder_key),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE id = %s
                    """, (
                        store.get('normalized_name'),
                        store['latitude'],
                        store['longitude'],
                        store.get('entersoft_key'),
                        store.get('inorder_key'),
                        store_id
                    ))
                    print(f"Updated store: {store.get('normalized_name')} (ID: {store_id})")
                else:
                    # Insert new store
                    cursor.execute("""
                        INSERT INTO stores (name, latitude, longitude, entersoft_key, inorder_key, future_proof_key, active)
                        VALUES (%s, %s, %s, %s, %s, %s, true)
                        RETURNING id
                    """, (
                        store.get('normalized_name'),
                        store['latitude'],
                        store['longitude'],
                        store.get('entersoft_key'),
                        store.get('inorder_key'),
                        store.get('future_proof_key')
                    ))
                    store_id = cursor.fetchone()[0]
                    print(f"Imported store: {store.get('normalized_name')} (ID: {store_id})")
                
                imported.append({**store, 'db_id': store_id})
                cursor.close()
                
            except Exception as e:
                errors.append({
                    'store': store.get('normalized_name'),
                    'error': str(e)
                })
                print(f"Error importing store {store.get('normalized_name')}: {e}")
        
        return {'imported': len(imported), 'errors': errors, 'store_mappings': {s.get('store_id'): s.get('db_id') for s in imported if s.get('store_id')}}
    
    def import_polygons(self, polygons: List[Dict], store_mappings: Dict[str, int], dry_run: bool = False) -> Dict:
        """Import polygons into database"""
        imported = []
        errors = []
        
        for polygon in polygons:
            try:
                store_id = None
                
                # Find store ID from mapping
                if polygon.get('store_id'):
                    store_id = store_mappings.get(polygon['store_id'])
                
                if not store_id:
                    errors.append({
                        'polygon': polygon.get('original_name'),
                        'error': f"Store ID {polygon.get('store_id')} not found in imported stores"
                    })
                    continue
                
                if dry_run:
                    print(f"Would import polygon: {polygon.get('original_name')} for store ID {store_id}")
                    imported.append(polygon)
                    continue
                
                # Convert coordinates to PostGIS geometry
                coords = polygon.get('coordinates', [])
                if len(coords) < 3:
                    errors.append({
                        'polygon': polygon.get('original_name'),
                        'error': "Polygon must have at least 3 coordinates"
                    })
                    continue
                
                # Ensure polygon is closed (first and last coordinates are the same)
                if coords[0] != coords[-1]:
                    coords.append(coords[0])
                
                # Create PostGIS geometry
                # PostGIS expects: POLYGON((lon1 lat1, lon2 lat2, ...))
                coords_str = ', '.join([f"{lon} {lat}" for lon, lat in coords])
                geometry_wkt = f"POLYGON(({coords_str}))"
                
                cursor = self.conn.cursor()
                
                # Check for existing current polygon of this type
                cursor.execute("""
                    SELECT id, version_number FROM polygon_versions
                    WHERE store_id = %s AND polygon_type = %s AND is_current = true AND inactive = false
                    LIMIT 1
                """, (store_id, polygon.get('polygon_type', 'delivery')))
                
                existing = cursor.fetchone()
                next_version = existing[1] + 1 if existing else 1
                
                if existing:
                    # Set previous version as inactive
                    cursor.execute("""
                        UPDATE polygon_versions
                        SET is_current = false
                        WHERE id = %s
                    """, (existing[0],))
                
                # Insert new polygon version
                cursor.execute("""
                    INSERT INTO polygon_versions 
                    (store_id, polygon_type, geometry, version_number, is_current, inactive, notes)
                    VALUES (%s, %s, ST_SetSRID(ST_GeomFromText(%s), 4326), %s, true, false, %s)
                    RETURNING id
                """, (
                    store_id,
                    polygon.get('polygon_type', 'delivery'),
                    geometry_wkt,
                    next_version,
                    f"Imported from KML. Original name: {polygon.get('original_name', '')}"
                ))
                
                polygon_id = cursor.fetchone()[0]
                print(f"Imported polygon: {polygon.get('original_name')} (Version {next_version}, ID: {polygon_id})")
                
                imported.append({**polygon, 'db_id': polygon_id, 'db_store_id': store_id})
                cursor.close()
                
            except Exception as e:
                errors.append({
                    'polygon': polygon.get('original_name'),
                    'error': str(e)
                })
                print(f"Error importing polygon {polygon.get('original_name')}: {e}")
        
        return {'imported': len(imported), 'errors': errors}
    
    def validate_import(self) -> Dict:
        """Validate imported data"""
        cursor = self.conn.cursor(cursor_factory=RealDictCursor)
        
        # Count stores
        cursor.execute("SELECT COUNT(*) as count FROM stores")
        store_count = cursor.fetchone()['count']
        
        # Count polygons
        cursor.execute("SELECT COUNT(*) as count FROM polygon_versions")
        polygon_count = cursor.fetchone()['count']
        
        # Count current polygons
        cursor.execute("SELECT COUNT(*) as count FROM polygon_versions WHERE is_current = true")
        current_polygon_count = cursor.fetchone()['count']
        
        # Count stores with polygons
        cursor.execute("""
            SELECT COUNT(DISTINCT store_id) as count 
            FROM polygon_versions 
            WHERE is_current = true
        """)
        stores_with_polygons = cursor.fetchone()['count']
        
        # Check for overlaps (basic check)
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM polygon_versions p1
            JOIN polygon_versions p2 ON p1.id < p2.id
            WHERE p1.is_current = true 
              AND p2.is_current = true
              AND ST_Overlaps(p1.geometry, p2.geometry)
        """)
        overlaps = cursor.fetchone()['count']
        
        cursor.close()
        
        return {
            'stores': store_count,
            'polygons': polygon_count,
            'current_polygons': current_polygon_count,
            'stores_with_polygons': stores_with_polygons,
            'overlapping_polygons': overlaps
        }


def main():
    parser = argparse.ArgumentParser(description='Import normalized data into database')
    parser.add_argument('input_json', help='Path to normalized JSON file')
    parser.add_argument('--database-url', help='Database connection URL', 
                       default=os.getenv('DATABASE_URL', 'postgresql://postgres:changeme@localhost:5432/coffee_berry'))
    parser.add_argument('--dry-run', action='store_true', help='Perform dry run without importing')
    args = parser.parse_args()
    
    # Load normalized data
    with open(args.input_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    stores = data.get('stores', [])
    polygons = data.get('polygons', [])
    
    print(f"Loading {len(stores)} stores and {len(polygons)} polygons...")
    
    with DatabaseImporter(args.database_url) as importer:
        # Import stores
        print("\n=== Importing Stores ===")
        store_result = importer.import_stores(stores, dry_run=args.dry_run)
        print(f"Imported: {store_result['imported']}, Errors: {len(store_result['errors'])}")
        
        if store_result['errors']:
            print("\nStore import errors:")
            for error in store_result['errors']:
                print(f"  - {error['store']}: {error['error']}")
        
        # Import polygons
        print("\n=== Importing Polygons ===")
        polygon_result = importer.import_polygons(
            polygons, 
            store_result.get('store_mappings', {}),
            dry_run=args.dry_run
        )
        print(f"Imported: {polygon_result['imported']}, Errors: {len(polygon_result['errors'])}")
        
        if polygon_result['errors']:
            print("\nPolygon import errors:")
            for error in polygon_result['errors']:
                print(f"  - {error['polygon']}: {error['error']}")
        
        # Validate
        if not args.dry_run:
            print("\n=== Validation ===")
            validation = importer.validate_import()
            print(json.dumps(validation, indent=2))


if __name__ == '__main__':
    main()
