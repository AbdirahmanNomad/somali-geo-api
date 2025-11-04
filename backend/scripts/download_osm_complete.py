#!/usr/bin/env python3
"""
Download complete OpenStreetMap data for Somalia including roads, airports, ports, etc.
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

def download_osm_overpass():
    """Download OSM data using Overpass API (more reliable than shapefiles)."""
    print("="*60)
    print("Downloading OpenStreetMap Data for Somalia")
    print("="*60)
    
    # Overpass API query for Somalia
    overpass_url = "https://overpass-api.de/api/interpreter"
    
    # Query for roads - fixed Overpass syntax
    print("\n📡 Fetching roads from OSM...")
    # Somalia bounding box (min_lon, min_lat, max_lon, max_lat)
    # Correct format for Overpass: (south,west,north,east) or (min_lat,min_lon,max_lat,max_lon)
    roads_query = """
    [out:json][timeout:180];
    (
      way["highway"~"^(motorway|trunk|primary|secondary|tertiary|unclassified|residential|track)"](41,-2,52,12);
    );
    (._;>;);
    out geom;
    """
    
    try:
        print("Sending query to Overpass API (this may take a while)...")
        response = requests.post(overpass_url, data=roads_query, timeout=300)
        print(f"Response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            features = []
            elements = data.get("elements", [])
            print(f"Received {len(elements)} elements from OSM")
            
            # Separate ways and nodes
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
            
            print(f"Found {len(ways)} ways and {len(nodes)} nodes")
            
            # Build LineString features from ways
            for way_id, way_data in ways.items():
                props = way_data.get("tags", {})
                highway = props.get("highway")
                
                if not highway:
                    continue
                
                # Skip non-road highways
                if highway not in ["motorway", "trunk", "primary", "secondary", "tertiary", 
                                   "unclassified", "residential", "track", "path", "service"]:
                    continue
                
                name = props.get("name") or props.get("ref") or f"{highway} road"
                
                # Get coordinates from nodes
                node_ids = way_data.get("nodes", [])
                coords = []
                
                for node_id in node_ids:
                    if node_id in nodes:
                        node = nodes[node_id]
                        lon = node.get("lon")
                        lat = node.get("lat")
                        if lon and lat:
                            coords.append([lon, lat])
                
                # Only add if we have at least 2 points
                if len(coords) >= 2:
                    # Map OSM highway types to our types
                    type_mapping = {
                        "motorway": "primary",
                        "trunk": "primary",
                        "primary": "primary",
                        "secondary": "secondary",
                        "tertiary": "secondary",
                        "unclassified": "secondary",
                        "residential": "secondary",
                        "track": "secondary",
                        "path": "secondary",
                        "service": "secondary"
                    }
                    
                    road_type = type_mapping.get(highway, "secondary")
                    
                    features.append({
                        "type": "Feature",
                        "properties": {
                            "name": name,
                            "type": road_type,
                            "highway": highway,
                            "ref": props.get("ref"),
                            "surface": props.get("surface"),
                            "length_km": None,
                            "condition": None
                        },
                        "geometry": {
                            "type": "LineString",
                            "coordinates": coords
                        }
                    })
            
            output_file = DATA_DIR / "somalia_roads_osm.geojson"
            with open(output_file, 'w') as f:
                json.dump({"type": "FeatureCollection", "features": features}, f, indent=2)
            
            print(f"✓ Saved {len(features)} roads to {output_file}")
            return output_file
        else:
            print(f"✗ Error: {response.status_code}")
    except Exception as e:
        print(f"✗ Error: {e}")
    
    return None

def download_osm_airports():
    """Download airports from OSM."""
    print("\n✈️  Fetching airports from OSM...")
    
    overpass_url = "https://overpass-api.de/api/interpreter"
    # Somalia bounding box: (south, west, north, east)
    # Format for Overpass: (min_lat, min_lon, max_lat, max_lon)
    query = """
    [out:json][timeout:60];
    (
      node["aeroway"="aerodrome"](-1.646, 40.993, 12.0, 51.417);
      way["aeroway"="aerodrome"](-1.646, 40.993, 12.0, 51.417);
      relation["aeroway"="aerodrome"](-1.646, 40.993, 12.0, 51.417);
    );
    out center;
    """
    
    try:
        response = requests.post(overpass_url, data=query, timeout=120)
        if response.status_code == 200:
            data = response.json()
            features = []
            
            for element in data.get("elements", []):
                props = element.get("tags", {})
                name = props.get("name", "Unknown Airport")
                
                # Get coordinates
                if element.get("type") == "node":
                    lat = element.get("lat")
                    lon = element.get("lon")
                elif element.get("type") == "way":
                    center = element.get("center", {})
                    lat = center.get("lat")
                    lon = center.get("lon")
                elif element.get("type") == "relation":
                    center = element.get("center", {})
                    lat = center.get("lat")
                    lon = center.get("lon")
                else:
                    continue
                
                if lat and lon:
                    features.append({
                        "type": "Feature",
                        "properties": {
                            "name": name,
                            "iata": props.get("iata"),
                            "icao": props.get("icao"),
                            "type": props.get("aerodrome", "unknown"),
                            "aeroway": props.get("aeroway"),
                        },
                        "geometry": {
                            "type": "Point",
                            "coordinates": [lon, lat]
                        }
                    })
            
            output_file = DATA_DIR / "somalia_airports_osm.geojson"
            with open(output_file, 'w') as f:
                json.dump({"type": "FeatureCollection", "features": features}, f, indent=2)
            
            print(f"✓ Saved {len(features)} airports to {output_file}")
            return output_file
    except Exception as e:
        print(f"✗ Error: {e}")
    
    return None

def download_osm_ports():
    """Download ports from OSM."""
    print("\n⚓ Fetching ports from OSM...")
    
    overpass_url = "https://overpass-api.de/api/interpreter"
    # Somalia bounding box: (south, west, north, east)
    query = """
    [out:json][timeout:60];
    (
      node["harbour"="yes"](-1.646, 40.993, 12.0, 51.417);
      node["seaport"="yes"](-1.646, 40.993, 12.0, 51.417);
      way["harbour"="yes"](-1.646, 40.993, 12.0, 51.417);
      way["seaport"="yes"](-1.646, 40.993, 12.0, 51.417);
    );
    out center;
    """
    
    try:
        response = requests.post(overpass_url, data=query, timeout=120)
        if response.status_code == 200:
            data = response.json()
            features = []
            
            for element in data.get("elements", []):
                props = element.get("tags", {})
                name = props.get("name", "Unknown Port")
                
                # Get coordinates
                if element.get("type") == "node":
                    lat = element.get("lat")
                    lon = element.get("lon")
                elif element.get("type") == "way":
                    center = element.get("center", {})
                    lat = center.get("lat")
                    lon = center.get("lon")
                else:
                    continue
                
                if lat and lon:
                    features.append({
                        "type": "Feature",
                        "properties": {
                            "name": name,
                            "type": props.get("harbour") or props.get("seaport") or "commercial",
                        },
                        "geometry": {
                            "type": "Point",
                            "coordinates": [lon, lat]
                        }
                    })
            
            output_file = DATA_DIR / "somalia_ports_osm.geojson"
            with open(output_file, 'w') as f:
                json.dump({"type": "FeatureCollection", "features": features}, f, indent=2)
            
            print(f"✓ Saved {len(features)} ports to {output_file}")
            return output_file
    except Exception as e:
        print(f"✗ Error: {e}")
    
    return None

def download_osm_checkpoints():
    """Download checkpoints/border crossings from OSM."""
    print("\n🛂 Fetching checkpoints from OSM...")
    
    overpass_url = "https://overpass-api.de/api/interpreter"
    # Somalia bounding box: (south, west, north, east)
    query = """
    [out:json][timeout:60];
    (
      node["barrier"="checkpoint"](-1.646, 40.993, 12.0, 51.417);
      node["barrier"="border_control"](-1.646, 40.993, 12.0, 51.417);
      node["military"="checkpoint"](-1.646, 40.993, 12.0, 51.417);
    );
    out;
    """
    
    try:
        response = requests.post(overpass_url, data=query, timeout=120)
        if response.status_code == 200:
            data = response.json()
            features = []
            
            for element in data.get("elements", []):
                if element.get("type") == "node":
                    props = element.get("tags", {})
                    name = props.get("name", "Unknown Checkpoint")
                    lat = element.get("lat")
                    lon = element.get("lon")
                    
                    if lat and lon:
                        features.append({
                            "type": "Feature",
                            "properties": {
                                "name": name,
                                "type": props.get("barrier") or "security",
                                "status": "active",
                            },
                            "geometry": {
                                "type": "Point",
                                "coordinates": [lon, lat]
                            }
                        })
            
            output_file = DATA_DIR / "somalia_checkpoints_osm.geojson"
            with open(output_file, 'w') as f:
                json.dump({"type": "FeatureCollection", "features": features}, f, indent=2)
            
            print(f"✓ Saved {len(features)} checkpoints to {output_file}")
            return output_file
    except Exception as e:
        print(f"✗ Error: {e}")
    
    return None

def main():
    """Download all OSM data."""
    print("Somalia Geography - OSM Data Downloader")
    
    # Download all data types
    roads_file = download_osm_overpass()
    airports_file = download_osm_airports()
    ports_file = download_osm_ports()
    checkpoints_file = download_osm_checkpoints()
    
    # Copy to main data files
    import shutil
    
    if roads_file:
        target = DATA_DIR / "somalia_roads.geojson"
        if target.exists():
            shutil.copy(target, DATA_DIR / "somalia_roads.backup.geojson")
        shutil.copy(roads_file, target)
        print(f"\n✓ Copied roads to {target}")
    
    print("\n" + "="*60)
    print("Next: Load data into database")
    print("Run: python scripts/load_geodata.py")
    print("="*60)

if __name__ == "__main__":
    main()

