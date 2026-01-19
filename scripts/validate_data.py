"""
Data Validation Script
Validates imported data and generates quality reports
"""
import json
import sys
import os
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor
import argparse


def validate_database(database_url: str) -> Dict:
    """Validate database contents and generate report"""
    conn = psycopg2.connect(database_url)
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    report = {
        'stores': {},
        'polygons': {},
        'issues': []
    }
    
    # Validate stores
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN active = true THEN 1 END) as active,
            COUNT(CASE WHEN entersoft_key IS NOT NULL THEN 1 END) as with_entersoft_key,
            COUNT(CASE WHEN inorder_key IS NOT NULL THEN 1 END) as with_inorder_key,
            COUNT(CASE WHEN current_franchisee_id IS NOT NULL THEN 1 END) as with_franchisee
        FROM stores
    """)
    report['stores'] = dict(cursor.fetchone())
    
    # Validate polygons
    cursor.execute("""
        SELECT 
            COUNT(*) as total,
            COUNT(CASE WHEN is_current = true AND inactive = false THEN 1 END) as current_active,
            COUNT(CASE WHEN polygon_type = 'dedicated' THEN 1 END) as dedicated,
            COUNT(CASE WHEN polygon_type = 'delivery' THEN 1 END) as delivery,
            COUNT(DISTINCT store_id) as stores_with_polygons
        FROM polygon_versions
    """)
    report['polygons'] = dict(cursor.fetchone())
    
    # Check for issues
    issues = []
    
    # Stores without polygons
    cursor.execute("""
        SELECT s.id, s.name
        FROM stores s
        WHERE s.active = true
          AND NOT EXISTS (
              SELECT 1 FROM polygon_versions pv
              WHERE pv.store_id = s.id 
                AND pv.is_current = true 
                AND pv.inactive = false
          )
    """)
    stores_without_polygons = cursor.fetchall()
    if stores_without_polygons:
        issues.append({
            'type': 'stores_without_polygons',
            'count': len(stores_without_polygons),
            'details': [{'id': s['id'], 'name': s['name']} for s in stores_without_polygons[:10]]
        })
    
    # Stores with multiple current polygons of same type
    cursor.execute("""
        SELECT store_id, polygon_type, COUNT(*) as count
        FROM polygon_versions
        WHERE is_current = true AND inactive = false
        GROUP BY store_id, polygon_type
        HAVING COUNT(*) > 1
    """)
    duplicate_current = cursor.fetchall()
    if duplicate_current:
        issues.append({
            'type': 'duplicate_current_polygons',
            'count': len(duplicate_current),
            'details': [dict(d) for d in duplicate_current]
        })
    
    # Invalid geometries
    cursor.execute("""
        SELECT id, store_id, polygon_type, ST_IsValid(geometry) as is_valid
        FROM polygon_versions
        WHERE is_current = true AND inactive = false
          AND NOT ST_IsValid(geometry)
    """)
    invalid_geometries = cursor.fetchall()
    if invalid_geometries:
        issues.append({
            'type': 'invalid_geometries',
            'count': len(invalid_geometries),
            'details': [dict(d) for d in invalid_geometries]
        })
    
    # Overlapping polygons (between different stores)
    cursor.execute("""
        SELECT 
            p1.store_id as store1_id,
            s1.name as store1_name,
            p2.store_id as store2_id,
            s2.name as store2_name,
            p1.polygon_type
        FROM polygon_versions p1
        JOIN stores s1 ON p1.store_id = s1.id
        JOIN polygon_versions p2 ON p1.id < p2.id
        JOIN stores s2 ON p2.store_id = s2.id
        WHERE p1.is_current = true 
          AND p2.is_current = true
          AND p1.inactive = false
          AND p2.inactive = false
          AND p1.polygon_type = p2.polygon_type
          AND ST_Overlaps(p1.geometry, p2.geometry)
        LIMIT 50
    """)
    overlaps = cursor.fetchall()
    if overlaps:
        issues.append({
            'type': 'overlapping_polygons',
            'count': len(overlaps),
            'details': [dict(o) for o in overlaps[:20]]  # Limit to 20 for report
        })
    
    # Delivery polygons not contained in dedicated polygons
    cursor.execute("""
        SELECT 
            d.store_id,
            s.name as store_name,
            d.id as dedicated_id,
            del.id as delivery_id
        FROM polygon_versions d
        JOIN polygon_versions del ON d.store_id = del.store_id
        JOIN stores s ON d.store_id = s.id
        WHERE d.polygon_type = 'dedicated'
          AND del.polygon_type = 'delivery'
          AND d.is_current = true
          AND del.is_current = true
          AND d.inactive = false
          AND del.inactive = false
          AND NOT ST_Contains(d.geometry, del.geometry)
    """)
    delivery_not_in_dedicated = cursor.fetchall()
    if delivery_not_in_dedicated:
        issues.append({
            'type': 'delivery_not_in_dedicated',
            'count': len(delivery_not_in_dedicated),
            'details': [dict(d) for d in delivery_not_in_dedicated[:10]]
        })
    
    report['issues'] = issues
    
    cursor.close()
    conn.close()
    
    return report


def main():
    parser = argparse.ArgumentParser(description='Validate imported database data')
    parser.add_argument('--database-url', help='Database connection URL',
                       default=os.getenv('DATABASE_URL', 'postgresql://postgres:changeme@localhost:5432/coffee_berry'))
    parser.add_argument('--output', help='Output JSON file for report', default=None)
    args = parser.parse_args()
    
    print("Validating database...")
    report = validate_database(args.database_url)
    
    # Print summary
    print("\n=== Validation Report ===")
    print(f"\nStores: {report['stores']['total']} total, {report['stores']['active']} active")
    print(f"Polygons: {report['polygons']['total']} total, {report['polygons']['current_active']} current active")
    print(f"Stores with polygons: {report['polygons']['stores_with_polygons']}")
    
    if report['issues']:
        print(f"\nIssues found: {len(report['issues'])}")
        for issue in report['issues']:
            print(f"  - {issue['type']}: {issue['count']} occurrences")
            if issue['details'] and len(issue['details']) <= 5:
                for detail in issue['details']:
                    print(f"    {detail}")
    else:
        print("\nNo issues found!")
    
    # Save report to file
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, default=str)
        print(f"\nReport saved to {args.output}")
    
    # Return exit code based on issues
    sys.exit(1 if report['issues'] else 0)


if __name__ == '__main__':
    main()
