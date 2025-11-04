#!/usr/bin/env python3
"""
Download and process real Somalia geographic data from various sources.

Sources:
- GADM: Administrative boundaries
- OCHA/HDX: Humanitarian administrative boundaries
- OpenStreetMap: Roads, airports, ports, cities
- FAO: Agricultural and land use data (optional)
"""

import json
import os
import sys
import zipfile
from pathlib import Path
from typing import Any, Dict, List
from urllib.request import urlretrieve

try:
    import requests
except ImportError:
    print("Error: requests library required. Install with: pip install requests")
    sys.exit(1)

try:
    import geopandas as gpd
except ImportError:
    print("Warning: geopandas not installed. Install with: pip install geopandas")
    print("This script will work but may have limited functionality.")
    gpd = None

# Data directory
DATA_DIR = Path(__file__).parent.parent / "app" / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Somalia region name mappings (to normalize different sources)
REGION_NAME_MAPPINGS = {
    # Common variations
    "banadir": "Banadir",
    "benadir": "Banadir",
    "banaadir": "Banadir",
    "hiiraan": "Hiiraan",
    "hiiran": "Hiiraan",
    "hirshabelle": "Hirshabelle",
    "shabelle": "Shabelle",
    "middle shabelle": "Shabelle",
    "lower shabelle": "Lower Shabelle",
    "jubaland": "Jubaland",
    "lower juba": "Jubaland",
    "middle juba": "Jubaland",
    "somaliland": "Somaliland",
    "puntland": "Puntland",
    "galmudug": "Galmudug",
    "south west": "South West",
    "southwest": "South West",
}


def normalize_region_name(name: str) -> str:
    """Normalize region names to standard format."""
    name_lower = name.lower().strip()
    return REGION_NAME_MAPPINGS.get(name_lower, name.title())


def generate_region_code(name: str) -> str:
    """Generate standard region code from name."""
    code_mappings = {
        "Banadir": "SOM-BNR",
        "Hiiraan": "SOM-HRS",
        "Hirshabelle": "SOM-HSH",
        "Shabelle": "SOM-SHB",
        "Lower Shabelle": "SOM-LSH",
        "Jubaland": "SOM-JBL",
        "Somaliland": "SOM-SML",
        "Puntland": "SOM-PTL",
        "Galmudug": "SOM-GLD",
        "South West": "SOM-SWS",
    }
    return code_mappings.get(name, f"SOM-{name[:3].upper()}")


def download_gadm_data():
    """
    Download GADM administrative boundaries for Somalia.
    
    GADM provides administrative boundaries at multiple levels:
    - Level 0: Country
    - Level 1: Regions (states)
    - Level 2: Districts
    """
    print("=" * 60)
    print("Downloading GADM data...")
    print("=" * 60)
    
    # GADM download URL (this is the general pattern, actual URL may vary)
    # Users need to download manually from https://gadm.org/download_country.html
    print("\nNOTE: GADM requires manual download.")
    print("Steps:")
    print("1. Visit: https://gadm.org/download_country.html")
    print("2. Select 'Somalia'")
    print("3. Download 'Shapefile' or 'GeoPackage' format")
    print("4. Extract and place in: app/data/gadm/")
    print("\nAlternatively, use direct download:")
    
    gadm_url = "https://geodata.ucdavis.edu/gadm/gadm4.1/shp/gadm41_SOM_shp.zip"
    gadm_dir = DATA_DIR / "gadm"
    gadm_dir.mkdir(exist_ok=True)
    
    zip_path = gadm_dir / "gadm41_SOM_shp.zip"
    
    if not zip_path.exists():
        print(f"Downloading from: {gadm_url}")
        try:
            urlretrieve(gadm_url, zip_path)
            print(f"Downloaded to: {zip_path}")
        except Exception as e:
            print(f"Error downloading: {e}")
            print("Please download manually and place in app/data/gadm/")
            return None
    
    return gadm_dir


def convert_gadm_to_geojson(gadm_dir: Path):
    """Convert GADM shapefiles to GeoJSON format."""
    if not gpd:
        print("geopandas required for conversion. Install with: pip install geopandas")
        return None
    
    print("\nConverting GADM data to GeoJSON...")
    
    output_dir = DATA_DIR / "processed"
    output_dir.mkdir(exist_ok=True)
    
    # Extract zip if needed
    zip_path = gadm_dir / "gadm41_SOM_shp.zip"
    if zip_path.exists():
        extract_dir = gadm_dir / "extracted"
        extract_dir.mkdir(exist_ok=True)
        
        print(f"Extracting {zip_path}...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
    
    # Find shapefiles
    shp_files = list(gadm_dir.rglob("*.shp"))
    if not shp_files:
        shp_files = list((gadm_dir / "extracted").rglob("*.shp"))
    
    regions_geojson = []
    districts_geojson = []
    
    for shp_file in shp_files:
        if "gadm41_SOM_1" in shp_file.name:  # Level 1 (Regions)
            print(f"Processing regions: {shp_file.name}")
            gdf = gpd.read_file(shp_file)
            
            for idx, row in gdf.iterrows():
                feature = {
                    "type": "Feature",
                    "properties": {
                        "name": normalize_region_name(row.get("NAME_1", row.get("VARNAME_1", ""))),
                        "code": generate_region_code(normalize_region_name(row.get("NAME_1", ""))),
                        "population": None,  # GADM doesn't include population
                        "area_km2": None,
                    },
                    "geometry": json.loads(gpd.GeoSeries([row.geometry]).to_json())["features"][0]["geometry"]
                }
                regions_geojson.append(feature)
        
        elif "gadm41_SOM_2" in shp_file.name:  # Level 2 (Districts)
            print(f"Processing districts: {shp_file.name}")
            gdf = gpd.read_file(shp_file)
            
            for idx, row in gdf.iterrows():
                region_name = normalize_region_name(row.get("NAME_1", ""))
                district_name = row.get("NAME_2", "")
                
                # Calculate centroid
                centroid = row.geometry.centroid
                
                feature = {
                    "type": "Feature",
                    "properties": {
                        "name": district_name,
                        "code": f"SOM-{region_name[:3].upper()}-{district_name[:3].upper()}",
                        "region": region_name,
                        "population": None,
                        "aliases": [],
                    },
                    "geometry": json.loads(gpd.GeoSeries([row.geometry]).to_json())["features"][0]["geometry"]
                }
                districts_geojson.append(feature)
    
    # Save to GeoJSON files
    if regions_geojson:
        regions_file = output_dir / "somalia_regions_gadm.geojson"
        with open(regions_file, 'w') as f:
            json.dump({"type": "FeatureCollection", "features": regions_geojson}, f, indent=2)
        print(f"Saved {len(regions_geojson)} regions to {regions_file}")
    
    if districts_geojson:
        districts_file = output_dir / "somalia_districts_gadm.geojson"
        with open(districts_file, 'w') as f:
            json.dump({"type": "FeatureCollection", "features": districts_geojson}, f, indent=2)
        print(f"Saved {len(districts_geojson)} districts to {districts_file}")
    
    return output_dir


def download_hdx_data():
    """
    Download OCHA/HDX Somalia administrative boundaries.
    
    HDX provides humanitarian-focused administrative data.
    """
    print("\n" + "=" * 60)
    print("Downloading HDX/OCHA data...")
    print("=" * 60)
    
    # HDX API endpoint for Somalia admin boundaries
    hdx_base_url = "https://data.humdata.org/api/3/action/package_show"
    package_id = "somalia-administrative-boundaries"
    
    try:
        response = requests.get(f"{hdx_base_url}?id={package_id}")
        if response.status_code == 200:
            data = response.json()
            resources = data.get("result", {}).get("resources", [])
            
            print(f"Found {len(resources)} resources")
            
            hdx_dir = DATA_DIR / "hdx"
            hdx_dir.mkdir(exist_ok=True)
            
            for resource in resources:
                if resource.get("format") in ["GeoJSON", "ZIP", "SHP"]:
                    url = resource.get("url")
                    name = resource.get("name", "unknown")
                    print(f"Downloading: {name}")
                    
                    file_path = hdx_dir / f"{name}.{resource.get('format', '').lower()}"
                    
                    if not file_path.exists():
                        try:
                            urlretrieve(url, file_path)
                            print(f"  Saved to: {file_path}")
                        except Exception as e:
                            print(f"  Error: {e}")
            
            return hdx_dir
        else:
            print(f"Error: Could not fetch HDX data (status {response.status_code})")
            print("Please download manually from: https://data.humdata.org/dataset/somalia-administrative-boundaries")
    except Exception as e:
        print(f"Error downloading HDX data: {e}")
        print("Please download manually from: https://data.humdata.org/dataset/somalia-administrative-boundaries")
    
    return None


def download_osm_data():
    """
    Download OpenStreetMap data for Somalia.
    
    OSM provides roads, airports, ports, cities, etc.
    """
    print("\n" + "=" * 60)
    print("Downloading OpenStreetMap data...")
    print("=" * 60)
    
    # Geofabrik provides OSM extracts
    osm_url = "https://download.geofabrik.de/africa/somalia-latest-free.shp.zip"
    
    osm_dir = DATA_DIR / "osm"
    osm_dir.mkdir(exist_ok=True)
    
    zip_path = osm_dir / "somalia-latest-free.shp.zip"
    
    if not zip_path.exists():
        print(f"Downloading from: {osm_url}")
        print("This may take a while (file is large)...")
        try:
            urlretrieve(osm_url, zip_path)
            print(f"Downloaded to: {zip_path}")
        except Exception as e:
            print(f"Error downloading: {e}")
            print("Please download manually from: https://download.geofabrik.de/africa/somalia.html")
            return None
    
    return osm_dir


def process_osm_roads(osm_dir: Path):
    """Extract roads from OSM data."""
    if not gpd:
        print("geopandas required for OSM processing")
        return None
    
    print("\nProcessing OSM roads...")
    
    # Extract if needed
    zip_path = osm_dir / "somalia-latest-free.shp.zip"
    if zip_path.exists():
        extract_dir = osm_dir / "extracted"
        extract_dir.mkdir(exist_ok=True)
        
        print("Extracting OSM data...")
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(extract_dir)
    
    # Find roads shapefile
    roads_shp = None
    for pattern in ["*roads*.shp", "*gis_osm_roads*.shp"]:
        found = list((osm_dir / "extracted").rglob(pattern))
        if found:
            roads_shp = found[0]
            break
    
    if not roads_shp:
        print("Could not find roads shapefile in OSM data")
        return None
    
    print(f"Processing roads from: {roads_shp}")
    gdf = gpd.read_file(roads_shp)
    
    roads_geojson = []
    
    for idx, row in gdf.iterrows():
        # OSM road types
        road_type = row.get("fclass", "unknown")
        road_name = row.get("name", "Unnamed Road")
        
        # Map OSM types to our types
        type_mapping = {
            "motorway": "primary",
            "trunk": "primary",
            "primary": "primary",
            "secondary": "secondary",
            "tertiary": "secondary",
            "unclassified": "secondary",
        }
        
        our_type = type_mapping.get(road_type, "secondary")
        
        feature = {
            "type": "Feature",
            "properties": {
                "name": road_name,
                "type": our_type,
                "length_km": None,  # Could calculate from geometry
                "condition": None,
                "surface": None,
            },
            "geometry": json.loads(gpd.GeoSeries([row.geometry]).to_json())["features"][0]["geometry"]
        }
        roads_geojson.append(feature)
    
    output_dir = DATA_DIR / "processed"
    output_dir.mkdir(exist_ok=True)
    
    roads_file = output_dir / "somalia_roads_osm.geojson"
    with open(roads_file, 'w') as f:
        json.dump({"type": "FeatureCollection", "features": roads_geojson}, f, indent=2)
    
    print(f"Saved {len(roads_geojson)} roads to {roads_file}")
    return roads_file


def main():
    """Main function to download and process real data."""
    print("Somalia Geography Data Downloader")
    print("=" * 60)
    print("\nThis script downloads real data from:")
    print("  - GADM: Administrative boundaries")
    print("  - HDX/OCHA: Humanitarian administrative boundaries")
    print("  - OpenStreetMap: Roads, infrastructure")
    print("\n" + "=" * 60)
    
    # Ask user which sources to download
    print("\nWhich data sources would you like to download?")
    print("1. GADM (Administrative boundaries)")
    print("2. HDX/OCHA (Administrative boundaries)")
    print("3. OpenStreetMap (Roads and infrastructure)")
    print("4. All of the above")
    print("5. Exit")
    
    choice = input("\nEnter choice (1-5): ").strip()
    
    if choice == "1" or choice == "4":
        gadm_dir = download_gadm_data()
        if gadm_dir:
            convert_gadm_to_geojson(gadm_dir)
    
    if choice == "2" or choice == "4":
        download_hdx_data()
    
    if choice == "3" or choice == "4":
        osm_dir = download_osm_data()
        if osm_dir:
            process_osm_roads(osm_dir)
    
    print("\n" + "=" * 60)
    print("Download complete!")
    print("\nNext steps:")
    print("1. Review the processed GeoJSON files in: app/data/processed/")
    print("2. Copy the files you want to use to: app/data/")
    print("3. Rename them to replace the sample files:")
    print("   - somalia_regions_gadm.geojson -> somalia_regions.geojson")
    print("   - somalia_districts_gadm.geojson -> somalia_districts.geojson")
    print("   - somalia_roads_osm.geojson -> somalia_roads.geojson")
    print("4. Run: python scripts/load_geodata.py")
    print("=" * 60)


if __name__ == "__main__":
    main()

