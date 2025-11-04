#!/usr/bin/env python3
"""
Alternative method to download roads - try smaller areas or use Geofabrik.
"""

import json
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("Installing requests...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

DATA_DIR = Path(__file__).parent.parent / "app" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

def try_smaller_areas():
    """Try downloading roads from smaller areas (cities) where roads are more likely to be mapped."""
    print("="*60)
    print("Downloading Roads - Alternative Approach")
    print("="*60)
    print("\nTrying smaller areas where roads are more likely mapped...")
    
    overpass_url = "https://overpass-api.de/api/interpreter"
    
    # Major cities in Somalia where roads are more likely to be mapped
    cities = [
        ("Mogadishu", 2.0469, 45.3182, 0.1),  # lat, lon, radius
        ("Hargeisa", 9.5616, 44.0650, 0.1),
        ("Bosaso", 11.2750, 49.1494, 0.1),
        ("Kismayo", -0.3583, 42.5456, 0.1),
    ]
    
    all_features = []
    
    for city_name, lat, lon, radius in cities:
        print(f"\n📡 Fetching roads near {city_name}...")
        
        # Create bbox around city
        min_lat = lat - radius
        max_lat = lat + radius
        min_lon = lon - radius
        max_lon = lon + radius
        
        query = f"""
        [out:json][timeout:60];
        (
          way["highway"~"^(motorway|trunk|primary|secondary|tertiary|unclassified|residential)"]({min_lat},{min_lon},{max_lat},{max_lon});
        );
        (._;>;);
        out geom;
        """
        
        try:
            response = requests.post(overpass_url, data=query, timeout=90)
            if response.status_code == 200:
                data = response.json()
                elements = data.get("elements", [])
                
                # Process same as before
                ways = {}
                nodes = {}
                
                for element in elements:
                    if element.get("type") == "node":
                        node_id = element.get("id")
                        nodes[node_id] = {
                            "lat": element.get("lat"),
                            "lon": element.get("lon")
                        }
                    elif element.get("type") == "way":
                        way_id = element.get("id")
                        ways[way_id] = {
                            "tags": element.get("tags", {}),
                            "nodes": element.get("nodes", [])
                        }
                
                # Build features
                for way_id, way_data in ways.items():
                    props = way_data.get("tags", {})
                    highway = props.get("highway")
                    
                    if not highway:
                        continue
                    
                    name = props.get("name") or props.get("ref") or f"{highway} road"
                    node_ids = way_data.get("nodes", [])
                    coords = []
                    
                    for node_id in node_ids:
                        if node_id in nodes:
                            node = nodes[node_id]
                            lon = node.get("lon")
                            lat = node.get("lat")
                            if lon and lat:
                                coords.append([lon, lat])
                    
                    if len(coords) >= 2:
                        type_mapping = {
                            "motorway": "primary",
                            "trunk": "primary",
                            "primary": "primary",
                            "secondary": "secondary",
                            "tertiary": "secondary",
                            "unclassified": "secondary",
                            "residential": "secondary"
                        }
                        
                        road_type = type_mapping.get(highway, "secondary")
                        
                        all_features.append({
                            "type": "Feature",
                            "properties": {
                                "name": name,
                                "type": road_type,
                                "highway": highway,
                                "ref": props.get("ref"),
                                "surface": props.get("surface"),
                            },
                            "geometry": {
                                "type": "LineString",
                                "coordinates": coords
                            }
                        })
                
                print(f"  Found {len(ways)} ways near {city_name}")
            else:
                print(f"  Error: {response.status_code}")
        except Exception as e:
            print(f"  Error for {city_name}: {e}")
    
    # Remove duplicates (same way ID)
    seen_ways = set()
    unique_features = []
    for feature in all_features:
        # Create a simple hash from coordinates
        coords = feature["geometry"]["coordinates"]
        coord_hash = tuple([tuple(c) for c in coords[:2]])  # Use first 2 points
        if coord_hash not in seen_ways:
            seen_ways.add(coord_hash)
            unique_features.append(feature)
    
    output_file = DATA_DIR / "somalia_roads_osm.geojson"
    with open(output_file, 'w') as f:
        json.dump({"type": "FeatureCollection", "features": unique_features}, f, indent=2)
    
    print(f"\n✓ Saved {len(unique_features)} unique roads to {output_file}")
    
    if len(unique_features) == 0:
        print("\n⚠️  No roads found in OSM for Somalia.")
        print("This is likely because:")
        print("  1. Roads in Somalia are not extensively mapped in OpenStreetMap")
        print("  2. OSM data for Somalia is sparse")
        print("  3. Alternative: Use Geofabrik shapefiles or manual data entry")
    
    return output_file if unique_features else None

def main():
    """Try alternative road download."""
    roads_file = try_smaller_areas()
    
    if roads_file:
        import shutil
        target = DATA_DIR / "somalia_roads.geojson"
        if target.exists():
            shutil.copy(target, DATA_DIR / "somalia_roads.backup.geojson")
        shutil.copy(roads_file, target)
        print(f"\n✓ Copied roads to {target}")
    
    print("\n" + "="*60)
    print("Note: If no roads found, consider:")
    print("  1. Using Geofabrik shapefiles: https://download.geofabrik.de/africa/somalia.html")
    print("  2. Manual data entry from official sources")
    print("  3. Using other mapping services")
    print("="*60)

if __name__ == "__main__":
    main()

