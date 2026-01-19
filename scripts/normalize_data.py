"""
Data Normalization Script
Cleans and normalizes parsed store data
- Extracts store IDs from names
- Matches polygons to stores
- Normalizes store names
"""
import json
import re
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class NormalizedStore:
    """Normalized store data"""
    name: str
    normalized_name: str
    store_id: Optional[str]  # Extracted from name like "(005)"
    longitude: float
    latitude: float
    entersoft_key: Optional[str] = None
    inorder_key: Optional[str] = None
    future_proof_key: Optional[str] = None


@dataclass
class NormalizedPolygon:
    """Normalized polygon data"""
    store_id: Optional[str]  # Matched to store
    store_name: Optional[str]  # Matched store name
    polygon_type: str  # 'dedicated' or 'delivery'
    coordinates: List[Tuple[float, float]]
    original_name: str
    matched_confidence: float = 0.0  # 0.0 to 1.0


class DataNormalizer:
    """Normalizes parsed store and polygon data"""
    
    # Store ID patterns: (005), [005], #005, etc.
    STORE_ID_PATTERNS = [
        r'\((\d+)\)',  # (005)
        r'\[(\d+)\]',  # [005]
        r'#(\d+)',     # #005
        r'^(\d+)\s',   # 005 at start
    ]
    
    def __init__(self):
        self.stores: List[NormalizedStore] = []
        self.polygons: List[NormalizedPolygon] = []
        self.store_name_mappings: Dict[str, str] = {}
    
    def normalize_stores(self, raw_stores: List[Dict]) -> List[NormalizedStore]:
        """Normalize store data"""
        normalized = []
        
        for store in raw_stores:
            name = store.get('name', '').strip()
            store_id = self._extract_store_id(name)
            normalized_name = self._normalize_store_name(name)
            
            # Extract external keys from name or create from store_id
            entersoft_key = store.get('entersoft_key') or store_id
            inorder_key = store.get('inorder_key') or store_id
            
            normalized_store = NormalizedStore(
                name=name,
                normalized_name=normalized_name,
                store_id=store_id,
                longitude=float(store['longitude']),
                latitude=float(store['latitude']),
                entersoft_key=entersoft_key,
                inorder_key=inorder_key,
                future_proof_key=None  # To be filled manually or from another source
            )
            
            normalized.append(normalized_store)
            if store_id:
                self.store_name_mappings[store_id] = normalized_name
                self.store_name_mappings[normalized_name.lower()] = normalized_name
                self.store_name_mappings[name.lower()] = normalized_name
        
        self.stores = normalized
        return normalized
    
    def normalize_polygons(self, raw_polygons: List[Dict]) -> List[NormalizedPolygon]:
        """Normalize polygon data and match to stores"""
        normalized = []
        
        for polygon in raw_polygons:
            original_name = polygon.get('name', '').strip()
            polygon_type = polygon.get('polygon_type', 'delivery')
            coordinates = polygon.get('coordinates', [])
            
            # Try to match polygon to a store
            store_id, store_name, confidence = self._match_polygon_to_store(original_name)
            
            normalized_polygon = NormalizedPolygon(
                store_id=store_id,
                store_name=store_name,
                polygon_type=polygon_type,
                coordinates=coordinates,
                original_name=original_name,
                matched_confidence=confidence
            )
            
            normalized.append(normalized_polygon)
        
        self.polygons = normalized
        return normalized
    
    def _extract_store_id(self, name: str) -> Optional[str]:
        """Extract store ID from name"""
        for pattern in self.STORE_ID_PATTERNS:
            match = re.search(pattern, name)
            if match:
                return match.group(1).zfill(3)  # Pad to 3 digits: 005
        return None
    
    def _normalize_store_name(self, name: str) -> str:
        """Normalize store name by removing ID patterns and cleaning"""
        # Remove store ID patterns
        for pattern in self.STORE_ID_PATTERNS:
            name = re.sub(pattern, '', name)
        
        # Remove common prefixes
        prefixes = ['CB ', 'cb ', 'Coffee Berry ', 'COFFEE BERRY ']
        for prefix in prefixes:
            if name.startswith(prefix):
                name = name[len(prefix):].strip()
        
        # Clean up whitespace
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name
    
    def _match_polygon_to_store(self, polygon_name: str) -> Tuple[Optional[str], Optional[str], float]:
        """
        Match polygon to a store by name similarity
        Returns: (store_id, store_name, confidence)
        """
        polygon_name_lower = polygon_name.lower()
        
        # Strategy 1: Extract store ID from polygon name
        polygon_store_id = self._extract_store_id(polygon_name)
        if polygon_store_id:
            for store in self.stores:
                if store.store_id == polygon_store_id:
                    return store.store_id, store.normalized_name, 1.0
        
        # Strategy 2: Exact name match
        polygon_normalized = self._normalize_store_name(polygon_name)
        for store in self.stores:
            if store.normalized_name.lower() == polygon_normalized.lower():
                return store.store_id, store.normalized_name, 0.9
        
        # Strategy 3: Partial name match (fuzzy)
        best_match = None
        best_confidence = 0.0
        
        for store in self.stores:
            confidence = self._calculate_name_similarity(
                polygon_normalized.lower(),
                store.normalized_name.lower()
            )
            if confidence > best_confidence and confidence > 0.5:
                best_confidence = confidence
                best_match = store
        
        if best_match:
            return best_match.store_id, best_match.normalized_name, best_confidence
        
        # Strategy 4: Check for location keywords in polygon name
        # This is a fallback - polygon might be for a region, not a specific store
        return None, None, 0.0
    
    def _calculate_name_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity between two names (simple Jaccard similarity)"""
        words1 = set(name1.split())
        words2 = set(name2.split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def generate_report(self) -> Dict:
        """Generate normalization report"""
        matched_polygons = [p for p in self.polygons if p.store_id is not None]
        unmatched_polygons = [p for p in self.polygons if p.store_id is None]
        
        return {
            'stores': {
                'total': len(self.stores),
                'with_store_id': len([s for s in self.stores if s.store_id]),
                'without_store_id': len([s for s in self.stores if not s.store_id])
            },
            'polygons': {
                'total': len(self.polygons),
                'matched': len(matched_polygons),
                'unmatched': len(unmatched_polygons),
                'dedicated': len([p for p in self.polygons if p.polygon_type == 'dedicated']),
                'delivery': len([p for p in self.polygons if p.polygon_type == 'delivery'])
            },
            'unmatched_polygons': [
                {'name': p.original_name, 'type': p.polygon_type}
                for p in unmatched_polygons
            ]
        }
    
    def export_json(self, output_path: str):
        """Export normalized data to JSON"""
        data = {
            'stores': [asdict(s) for s in self.stores],
            'polygons': [
                {
                    'store_id': p.store_id,
                    'store_name': p.store_name,
                    'polygon_type': p.polygon_type,
                    'coordinates': p.coordinates,
                    'original_name': p.original_name,
                    'matched_confidence': p.matched_confidence
                }
                for p in self.polygons
            ],
            'report': self.generate_report()
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"Exported normalized data to {output_path}")
        print(f"Report: {json.dumps(data['report'], indent=2)}")


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python normalize_data.py <parsed_json> [output_json]")
        sys.exit(1)
    
    input_json = sys.argv[1]
    output_json = sys.argv[2] if len(sys.argv) > 2 else 'normalized_data.json'
    
    # Load parsed data
    with open(input_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    normalizer = DataNormalizer()
    
    # Normalize stores
    stores = normalizer.normalize_stores(data.get('stores', []))
    print(f"Normalized {len(stores)} stores")
    
    # Normalize polygons
    polygons = normalizer.normalize_polygons(data.get('polygons', []))
    print(f"Normalized {len(polygons)} polygons")
    
    # Export
    normalizer.export_json(output_json)
