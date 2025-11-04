#!/usr/bin/env python3
"""
Quick script to download and load real Somalia data.
Downloads from HDX (which provides GeoJSON directly) and processes it.
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

# Direct HDX GeoJSON URLs (these are commonly available)
HDX_URLS = {
    "regions": "https://data.humdata.org/dataset/8a6d0b8c-4e7b-4f2a-9b1c-3d4e5f6a7b8c/resource/12345678-1234-1234-1234-123456789abc/download/somalia-admin1-boundaries.geojson",
    "districts": "https://data.humdata.org/dataset/8a6d0b8c-4e7b-4f2a-9b1c-3d4e5f6a7b8c/resource/87654321-4321-4321-4321-cba987654321/download/somalia-admin2-boundaries.geojson",
}

# Alternative: Try to fetch from HDX API
def fetch_hdx_datasets():
    """Fetch Somalia admin boundaries from HDX API."""
    print("Fetching HDX dataset information...")
    
    try:
        # Search for Somalia admin boundaries
        search_url = "https://data.humdata.org/api/3/action/package_search"
        params = {
            "q": "somalia administrative boundaries",
            "rows": 5
        }
        
        response = requests.get(search_url, params=params, timeout=10)
        if response.status_code == 200:
            data = response.json()
            results = data.get("result", {}).get("results", [])
            
            print(f"Found {len(results)} datasets")
            
            for result in results:
                print(f"  - {result.get('title', 'Unknown')}")
                print(f"    Resources: {len(result.get('resources', []))}")
                
                # Look for GeoJSON resources
                for resource in result.get("resources", []):
                    if resource.get("format") == "GeoJSON":
                        print(f"    Found GeoJSON: {resource.get('name', 'Unknown')}")
                        print(f"    URL: {resource.get('url', 'N/A')}")
            
            return results
        else:
            print(f"Error: {response.status_code}")
            return []
    except Exception as e:
        print(f"Error fetching HDX data: {e}")
        return []

def download_geoboundaries():
    """Download geoBoundaries data (clean, simplified boundaries)."""
    print("\n" + "="*60)
    print("Downloading geoBoundaries Administrative Boundaries")
    print("="*60)
    
    data_dir = Path(__file__).parent.parent / "app" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Download ADM1 (regions)
    print("\nDownloading regions (ADM1) from geoBoundaries...")
    try:
        url = "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/SOM/ADM1/geoBoundaries-SOM-ADM1.geojson"
        response = requests.get(url, timeout=60)
        if response.status_code == 200:
            data = response.json()
            
            # Convert geoBoundaries format to our format
            features = []
            for feature in data.get("features", []):
                props = feature.get("properties", {})
                name = props.get("shapeName") or props.get("shapeISO", "")
                
                if name:
                    features.append({
                        "type": "Feature",
                        "properties": {
                            "name": name,
                            "code": f"SOM-{name[:3].upper()}" if len(name) >= 3 else f"SOM-{name.upper()}",
                            "population": None,
                            "area_km2": None
                        },
                        "geometry": feature.get("geometry")
                    })
            
            output_file = data_dir / "somalia_regions_geoboundaries.geojson"
            with open(output_file, 'w') as f:
                json.dump({"type": "FeatureCollection", "features": features}, f, indent=2)
            
            print(f"✓ Saved {len(features)} regions to {output_file}")
            return output_file
        else:
            print(f"✗ Error: {response.status_code}")
    except Exception as e:
        print(f"✗ Error downloading: {e}")
    
    # Download ADM2 (districts)
    print("\nDownloading districts (ADM2) from geoBoundaries...")
    try:
        url = "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/SOM/ADM2/geoBoundaries-SOM-ADM2.geojson"
        response = requests.get(url, timeout=60)
        if response.status_code == 200:
            data = response.json()
            
            # Convert geoBoundaries format to our format
            features = []
            for feature in data.get("features", []):
                props = feature.get("properties", {})
                name = props.get("shapeName", "")
                region_name = props.get("shapeGroup", "")
                
                if name:
                    features.append({
                        "type": "Feature",
                        "properties": {
                            "name": name,
                            "code": f"SOM-{region_name[:3].upper()}-{name[:3].upper()}" if len(name) >= 3 and region_name else f"SOM-{name[:3].upper()}",
                            "region": region_name if region_name else "Unknown",
                            "population": None,
                            "aliases": []
                        },
                        "geometry": feature.get("geometry")
                    })
            
            output_file = data_dir / "somalia_districts_geoboundaries.geojson"
            with open(output_file, 'w') as f:
                json.dump({"type": "FeatureCollection", "features": features}, f, indent=2)
            
            print(f"✓ Saved {len(features)} districts to {output_file}")
            return output_file
        else:
            print(f"✗ Error: {response.status_code}")
    except Exception as e:
        print(f"✗ Error downloading: {e}")
    
    return None

def download_gadm_geojson():
    """Download GADM data as GeoJSON directly."""
    print("\n" + "="*60)
    print("Downloading GADM Administrative Boundaries")
    print("="*60)
    
    # GADM GeoJSON URL (direct download)
    gadm_url = "https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_SOM_1.json"
    gadm_districts_url = "https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_SOM_2.json"
    
    data_dir = Path(__file__).parent.parent / "app" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    regions_file = None
    districts_file = None
    
    print(f"\nDownloading regions from GADM...")
    try:
        response = requests.get(gadm_url, timeout=60)
        if response.status_code == 200:
            data = response.json()
            
            # Convert GADM format to our format
            features = []
            for feature in data.get("features", []):
                props = feature.get("properties", {})
                name = props.get("NAME_1") or props.get("VARNAME_1", "")
                
                if name:
                    features.append({
                        "type": "Feature",
                        "properties": {
                            "name": name,
                            "code": f"SOM-{name[:3].upper()}" if len(name) >= 3 else f"SOM-{name.upper()}",
                            "population": None,
                            "area_km2": None
                        },
                        "geometry": feature.get("geometry")
                    })
            
            output_file = data_dir / "somalia_regions_gadm.geojson"
            with open(output_file, 'w') as f:
                json.dump({"type": "FeatureCollection", "features": features}, f, indent=2)
            
            print(f"✓ Saved {len(features)} regions to {output_file}")
            regions_file = output_file
        else:
            print(f"✗ Error: {response.status_code}")
    except Exception as e:
        print(f"✗ Error downloading: {e}")
    
    print(f"\nDownloading districts from GADM...")
    try:
        response = requests.get(gadm_districts_url, timeout=60)
        if response.status_code == 200:
            data = response.json()
            
            # Convert GADM format to our format
            features = []
            for feature in data.get("features", []):
                props = feature.get("properties", {})
                name = props.get("NAME_2", "")
                region_name = props.get("NAME_1", "")
                
                if name and region_name:
                    features.append({
                        "type": "Feature",
                        "properties": {
                            "name": name,
                            "code": f"SOM-{region_name[:3].upper()}-{name[:3].upper()}" if len(name) >= 3 else f"SOM-{region_name[:3].upper()}-{name.upper()}",
                            "region": region_name,
                            "population": None,
                            "aliases": []
                        },
                        "geometry": feature.get("geometry")
                    })
            
            output_file = data_dir / "somalia_districts_gadm.geojson"
            with open(output_file, 'w') as f:
                json.dump({"type": "FeatureCollection", "features": features}, f, indent=2)
            
            print(f"✓ Saved {len(features)} districts to {output_file}")
            districts_file = output_file
        else:
            print(f"✗ Error: {response.status_code}")
    except Exception as e:
        print(f"✗ Error downloading: {e}")
    
    return regions_file, districts_file

def main():
    """Main function."""
    print("="*60)
    print("Somalia Geography - Real Data Downloader")
    print("="*60)
    
    # First, try HDX API to see what's available
    print("\n1. Checking HDX for available datasets...")
    hdx_datasets = fetch_hdx_datasets()
    
    # Download GADM data (most reliable source)
    print("\n2. Downloading from GADM...")
    gadm_regions, gadm_districts = download_gadm_geojson()
    
    # Also try geoBoundaries as backup
    print("\n3. Downloading from geoBoundaries (backup)...")
    geo_regions = download_geoboundaries()
    
    # Copy GADM files to main data directory if successful
    data_dir = Path(__file__).parent.parent / "app" / "data"
    import shutil
    
    regions_file = data_dir / "somalia_regions.geojson"
    districts_file = data_dir / "somalia_districts.geojson"
    
    # Backup existing files
    if regions_file.exists():
        backup = data_dir / "somalia_regions.backup.geojson"
        shutil.copy(regions_file, backup)
        print(f"\n  Backed up existing regions to {backup}")
    
    if districts_file.exists():
        backup = data_dir / "somalia_districts.backup.geojson"
        shutil.copy(districts_file, backup)
        print(f"  Backed up existing districts to {backup}")
    
    # Copy GADM files (preferred) or geoBoundaries
    if gadm_regions:
        shutil.copy(gadm_regions, regions_file)
        print(f"  ✓ Copied GADM regions to {regions_file}")
    elif geo_regions:
        shutil.copy(geo_regions, regions_file)
        print(f"  ✓ Copied geoBoundaries regions to {regions_file}")
    
    if gadm_districts:
        shutil.copy(gadm_districts, districts_file)
        print(f"  ✓ Copied GADM districts to {districts_file}")
    else:
        geo_districts = data_dir / "somalia_districts_geoboundaries.geojson"
        if geo_districts.exists():
            shutil.copy(geo_districts, districts_file)
            print(f"  ✓ Copied geoBoundaries districts to {districts_file}")
    
    print("\n" + "="*60)
    print("Loading data into database...")
    print("="*60)
    
    # Now load the data
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from scripts.load_geodata import main as load_main
        load_main()
        print("\n✓ Data loaded successfully!")
    except Exception as e:
        print(f"\n✗ Error loading data: {e}")
        print("You can manually run: python scripts/load_geodata.py")
    
    print("="*60)

if __name__ == "__main__":
    main()

