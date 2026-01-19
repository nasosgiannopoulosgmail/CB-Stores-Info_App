"""
KML/KMZ Parser for Coffee-Berry Stores Data
Extracts store locations and polygons from KMZ/KML files
"""
import zipfile
import xml.etree.ElementTree as ET
import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass


# KML namespace
KML_NS = {'kml': 'http://www.opengis.net/kml/2.2'}


@dataclass
class StorePoint:
    """Store location point"""
    name: str
    longitude: float
    latitude: float
    folder: Optional[str] = None
    style: Optional[str] = None


@dataclass
class StorePolygon:
    """Store polygon (dedicated or delivery area)"""
    name: str
    coordinates: List[Tuple[float, float]]  # List of (lon, lat) tuples
    folder: Optional[str] = None
    style: Optional[str] = None
    polygon_type: Optional[str] = None  # 'dedicated' or 'delivery'


class KMLParser:
    """Parser for KML/KMZ files"""
    
    def __init__(self, kmz_path: str):
        self.kmz_path = Path(kmz_path)
        self.root = None
        self.stores: List[StorePoint] = []
        self.polygons: List[StorePolygon] = []
        
    def parse(self) -> Tuple[List[StorePoint], List[StorePolygon]]:
        """Parse KMZ/KML file and extract stores and polygons"""
        if self.kmz_path.suffix.lower() == '.kmz':
            self._parse_kmz()
        elif self.kmz_path.suffix.lower() == '.kml':
            self._parse_kml()
        else:
            raise ValueError(f"Unsupported file format: {self.kmz_path.suffix}")
        
        self._extract_data()
        return self.stores, self.polygons
    
    def _parse_kmz(self):
        """Extract and parse KML from KMZ archive"""
        with zipfile.ZipFile(self.kmz_path, 'r') as kmz:
            # Find doc.kml file
            kml_files = [f for f in kmz.namelist() if f.endswith('.kml')]
            if not kml_files:
                raise ValueError("No KML file found in KMZ archive")
            
            # Parse the main KML file (usually doc.kml)
            kml_file = next((f for f in kml_files if 'doc.kml' in f), kml_files[0])
            kml_content = kmz.read(kml_file).decode('utf-8')
            self.root = ET.fromstring(kml_content)
    
    def _parse_kml(self):
        """Parse KML file directly"""
        with open(self.kmz_path, 'r', encoding='utf-8') as f:
            self.root = ET.parse(f).getroot()
    
    def _extract_data(self):
        """Extract stores and polygons from parsed KML"""
        if self.root is None:
            raise ValueError("KML not parsed yet. Call parse() first.")
        
        # Process folders first
        folders = self.root.findall('.//kml:Folder', KML_NS)
        for folder in folders:
            folder_name = folder.find('kml:name', KML_NS)
            folder_name = folder_name.text if folder_name is not None else None
            
            # Extract Placemarks from this folder
            placemarks = folder.findall('.//kml:Placemark', KML_NS)
            for placemark in placemarks:
                self._process_placemark(placemark, folder_name)
        
        # Also process top-level Placemarks (not in folders)
        top_level_placemarks = self.root.findall('.//kml:Placemark', KML_NS)
        for placemark in top_level_placemarks:
            # Skip if already processed in a folder
            if not any(p.name == self._get_placemark_name(placemark) for p in self.stores + [StorePolygon(name=self._get_placemark_name(placemark), coordinates=[])]) if hasattr(self, 'processed_placemarks') else True:
                self._process_placemark(placemark, None)
    
    def _process_placemark(self, placemark: ET.Element, folder: Optional[str]):
        """Process a single Placemark element"""
        name = self._get_placemark_name(placemark)
        style_url = placemark.find('kml:styleUrl', KML_NS)
        style = style_url.text if style_url is not None else None
        
        # Check if it's a Point (store location)
        point = placemark.find('.//kml:Point', KML_NS)
        if point is not None:
            coords = self._parse_coordinates(point.find('kml:coordinates', KML_NS))
            if coords:
                lon, lat, _ = coords[0]  # Point has single coordinate
                self.stores.append(StorePoint(
                    name=name,
                    longitude=lon,
                    latitude=lat,
                    folder=folder,
                    style=style
                ))
        
        # Check if it's a Polygon (delivery/dedicated area)
        polygon = placemark.find('.//kml:Polygon', KML_NS)
        if polygon is not None:
            coords = self._parse_polygon_coordinates(polygon)
            if coords:
                # Infer polygon type from style or name
                polygon_type = self._infer_polygon_type(name, style)
                
                self.polygons.append(StorePolygon(
                    name=name,
                    coordinates=coords,
                    folder=folder,
                    style=style,
                    polygon_type=polygon_type
                ))
    
    def _get_placemark_name(self, placemark: ET.Element) -> str:
        """Extract name from Placemark"""
        name_elem = placemark.find('kml:name', KML_NS)
        return name_elem.text if name_elem is not None else "Unnamed"
    
    def _parse_coordinates(self, coords_elem: Optional[ET.Element]) -> List[Tuple[float, float, float]]:
        """Parse coordinates element into list of (lon, lat, alt) tuples"""
        if coords_elem is None or coords_elem.text is None:
            return []
        
        coords = []
        for line in coords_elem.text.strip().split('\n'):
            line = line.strip()
            if not line:
                continue
            parts = line.split(',')
            if len(parts) >= 2:
                try:
                    lon = float(parts[0].strip())
                    lat = float(parts[1].strip())
                    alt = float(parts[2].strip()) if len(parts) > 2 else 0.0
                    coords.append((lon, lat, alt))
                except ValueError:
                    continue
        return coords
    
    def _parse_polygon_coordinates(self, polygon: ET.Element) -> List[Tuple[float, float]]:
        """Parse polygon coordinates from LinearRing"""
        outer_boundary = polygon.find('.//kml:outerBoundaryIs', KML_NS)
        if outer_boundary is None:
            return []
        
        linear_ring = outer_boundary.find('.//kml:LinearRing', KML_NS)
        if linear_ring is None:
            return []
        
        coords_elem = linear_ring.find('kml:coordinates', KML_NS)
        coords_3d = self._parse_coordinates(coords_elem)
        
        # Convert to 2D (lon, lat) tuples
        return [(lon, lat) for lon, lat, _ in coords_3d]
    
    def _infer_polygon_type(self, name: str, style: Optional[str]) -> Optional[str]:
        """
        Infer polygon type (dedicated or delivery) from name or style
        Heuristics:
        - Names containing 'delivery' or 'del' -> delivery
        - Names containing 'dedicated' or 'ded' -> dedicated
        - By default, try to match with store names (smaller area likely delivery)
        """
        name_lower = name.lower()
        
        if any(keyword in name_lower for keyword in ['delivery', 'del ', 'παραγγελ']):
            return 'delivery'
        elif any(keyword in name_lower for keyword in ['dedicated', 'ded ', 'αφοσιωμένο']):
            return 'dedicated'
        
        # Default: assume delivery (smaller area)
        # This can be refined based on actual data patterns
        return 'delivery'
    
    def export_json(self, output_path: str):
        """Export parsed data to JSON"""
        data = {
            'stores': [
                {
                    'name': s.name,
                    'longitude': s.longitude,
                    'latitude': s.latitude,
                    'folder': s.folder,
                    'style': s.style
                }
                for s in self.stores
            ],
            'polygons': [
                {
                    'name': p.name,
                    'coordinates': p.coordinates,
                    'folder': p.folder,
                    'style': p.style,
                    'polygon_type': p.polygon_type
                }
                for p in self.polygons
            ]
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Exported {len(self.stores)} stores and {len(self.polygons)} polygons to {output_path}")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python parse_kmz.py <kmz_file> [output_json]")
        sys.exit(1)
    
    kmz_path = sys.argv[1]
    output_json = sys.argv[2] if len(sys.argv) > 2 else 'parsed_data.json'
    
    parser = KMLParser(kmz_path)
    stores, polygons = parser.parse()
    
    print(f"Parsed {len(stores)} stores and {len(polygons)} polygons")
    
    parser.export_json(output_json)
