#!/usr/bin/env python3
"""
Data loader script for Somalia Geography & Governance API.

Loads GeoJSON data into the database.
"""

import json
import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy.orm import Session
from sqlmodel import SQLModel
from app.core.config import settings
from app.core.db import engine
from app import models


def normalize_field(props: dict, field_variations: list, default=None):
    """Try multiple field name variations to find a value."""
    for variation in field_variations:
        if variation in props:
            return props[variation]
    return default


def load_regions(db: Session, data_file: str):
    """Load regions from GeoJSON file.
    
    Handles different field name variations from different data sources:
    - GADM: NAME_1, VARNAME_1
    - HDX: admin1Name, admin1Pcode
    - Custom: name, code
    """
    print(f"Loading regions from {data_file}...")

    with open(data_file, 'r') as f:
        data = json.load(f)

    loaded_count = 0
    
    for feature in data['features']:
        props = feature['properties']
        geom = feature['geometry']

        # Try multiple field name variations
        name = normalize_field(props, [
            'name', 'NAME_1', 'VARNAME_1', 'admin1Name', 'ADMIN1',
            'region', 'Region', 'REGION'
        ])
        
        code = normalize_field(props, [
            'code', 'CODE', 'admin1Pcode', 'pcode', 'PCODE'
        ])
        
        # Generate code from name if not present
        if not code and name:
            # Simple code generation
            code = f"SOM-{name[:3].upper()}" if len(name) >= 3 else f"SOM-{name.upper()}"
        
        # Try to get population and area
        population = normalize_field(props, [
            'population', 'Population', 'POPULATION', 'pop', 'Pop'
        ])
        
        area_km2 = normalize_field(props, [
            'area_km2', 'area', 'Area', 'AREA', 'areaKm2'
        ])

        if not name:
            print(f"Warning: Skipping region with no name: {props}")
            continue

        region = models.Region(
            name=name,
            code=code,
            population=int(population) if population else None,
            area_km2=float(area_km2) if area_km2 else None,
            geometry=geom
        )
        db.add(region)
        loaded_count += 1

    db.commit()
    print(f"Loaded {loaded_count} regions")


def calculate_centroid(geom: dict) -> dict | None:
    """
    Calculate centroid from GeoJSON geometry.
    Handles Point, Polygon, and MultiPolygon geometries.
    """
    geom_type = geom.get('type')
    coords = geom.get('coordinates')
    
    if not coords:
        return None
    
    if geom_type == 'Point':
        return {"lat": coords[1], "lon": coords[0]}
    elif geom_type == 'Polygon':
        # For Polygon, use the first ring (exterior ring) and calculate simple centroid
        ring = coords[0]
        if not ring:
            return None
        # Calculate average of all points in the ring
        lons = [point[0] for point in ring]
        lats = [point[1] for point in ring]
        return {"lat": sum(lats) / len(lats), "lon": sum(lons) / len(lons)}
    elif geom_type == 'MultiPolygon':
        # For MultiPolygon, use the first polygon's first ring
        if coords and coords[0] and coords[0][0]:
            ring = coords[0][0]
            lons = [point[0] for point in ring]
            lats = [point[1] for point in ring]
            return {"lat": sum(lats) / len(lats), "lon": sum(lons) / len(lons)}
    
    return None


def load_districts(db: Session, data_file: str):
    """Load districts from GeoJSON file.
    
    Handles different field name variations from different data sources:
    - GADM: NAME_2, NAME_1 (for region)
    - HDX: admin2Name, admin1Name, admin2Pcode
    - Custom: name, region, code
    """
    print(f"Loading districts from {data_file}...")

    with open(data_file, 'r') as f:
        data = json.load(f)

    loaded_count = 0
    
    for feature in data['features']:
        props = feature['properties']
        geom = feature['geometry']

        # Try multiple field name variations
        name = normalize_field(props, [
            'name', 'NAME_2', 'VARNAME_2', 'admin2Name', 'ADMIN2',
            'district', 'District', 'DISTRICT'
        ])
        
        region_name = normalize_field(props, [
            'region', 'Region', 'REGION', 'NAME_1', 'admin1Name', 'ADMIN1'
        ])
        
        code = normalize_field(props, [
            'code', 'CODE', 'admin2Pcode', 'pcode', 'PCODE'
        ])
        
        # Generate code if not present
        if not code and name and region_name:
            code = f"SOM-{region_name[:3].upper()}-{name[:3].upper()}" if len(name) >= 3 else f"SOM-{region_name[:3].upper()}-{name.upper()}"
        
        # Get aliases
        aliases = props.get('aliases', [])
        if isinstance(aliases, str):
            aliases = [aliases] if aliases else []
        
        # Get population
        population = normalize_field(props, [
            'population', 'Population', 'POPULATION', 'pop', 'Pop'
        ])

        if not name:
            print(f"Warning: Skipping district with no name: {props}")
            continue

        if not region_name:
            print(f"Warning: Skipping district '{name}' with no region")
            continue

        # Get region by name (try exact match first, then case-insensitive)
        region = db.query(models.Region).filter(models.Region.name == region_name).first()
        if not region:
            # Try case-insensitive
            from sqlalchemy import func
            region = db.query(models.Region).filter(
                func.lower(models.Region.name) == region_name.lower()
            ).first()
        
        if not region:
            print(f"Warning: Region '{region_name}' not found for district '{name}'. Creating placeholder region.")
            # Create placeholder region
            region = models.Region(
                name=region_name,
                code=f"SOM-{region_name[:3].upper()}" if len(region_name) >= 3 else f"SOM-{region_name.upper()}",
            )
            db.add(region)
            db.flush()  # Get the ID

        # Extract centroid from geometry (handles Point, Polygon, MultiPolygon)
        centroid = calculate_centroid(geom)

        district = models.District(
            name=name,
            code=code,
            region_name=region_name,
            population=int(population) if population else None,
            aliases=aliases if aliases else [],
            centroid=centroid,
            geometry=geom,
            region_id=region.id
        )
        db.add(district)
        loaded_count += 1

    db.commit()
    print(f"Loaded {loaded_count} districts")


def load_roads(db: Session, data_file: str):
    """Load roads from GeoJSON file.
    
    Handles different field name variations from different data sources:
    - OSM: name, fclass, highway
    - Custom: name, type, length_km
    """
    print(f"Loading roads from {data_file}...")

    with open(data_file, 'r') as f:
        data = json.load(f)

    # Road type mappings from OSM to our types
    osm_type_mapping = {
        'motorway': 'primary',
        'trunk': 'primary',
        'primary': 'primary',
        'secondary': 'secondary',
        'tertiary': 'secondary',
        'unclassified': 'secondary',
        'residential': 'secondary',
        'track': 'secondary',
    }
    
    loaded_count = 0
    
    for feature in data['features']:
        props = feature['properties']
        geom = feature['geometry']

        # Try multiple field name variations
        name = normalize_field(props, [
            'name', 'Name', 'NAME', 'ref', 'Ref'
        ], 'Unnamed Road')
        
        # Get road type
        road_type = normalize_field(props, [
            'type', 'Type', 'TYPE', 'fclass', 'FCLASS', 'highway', 'HIGHWAY'
        ], 'secondary')
        
        # Map OSM types to our types
        if road_type in osm_type_mapping:
            road_type = osm_type_mapping[road_type]
        
        # Get length
        length_km = normalize_field(props, [
            'length_km', 'length', 'Length', 'LENGTH', 'lengthKm'
        ])
        
        # Get condition and surface
        condition = normalize_field(props, [
            'condition', 'Condition', 'CONDITION', 'surface_condition'
        ])
        
        surface = normalize_field(props, [
            'surface', 'Surface', 'SURFACE', 'paved', 'Paved'
        ])
        
        # Handle geometry - OSM LineString coordinates
        if geom['type'] == 'LineString':
            coordinates = geom['coordinates']
        elif geom['type'] == 'MultiLineString':
            # Flatten MultiLineString
            coordinates = []
            for line in geom['coordinates']:
                coordinates.extend(line)
        else:
            print(f"Warning: Unsupported geometry type {geom['type']} for road '{name}'")
            continue

        road = models.Road(
            name=name if name else 'Unnamed Road',
            type=road_type,
            length_km=float(length_km) if length_km else None,
            condition=condition,
            surface=surface,
            geometry=coordinates
        )
        db.add(road)
        loaded_count += 1

    db.commit()
    print(f"Loaded {loaded_count} roads")


def is_in_somalia(lat: float, lon: float) -> bool:
    """
    Check if coordinates are within Somalia bounding box.
    
    Using stricter bounds to exclude Djibouti/Ethiopia border areas:
    - Latitude: 1.5 to 11.5 (South to North) - excludes border areas
    - Longitude: 41.0 to 51.5 (West to East)
    """
    return (1.5 <= lat <= 11.5) and (41.0 <= lon <= 51.5)


def load_transport_from_geojson(db: Session, data_file: str, transport_type: str):
    """Load transport infrastructure from GeoJSON file.
    
    Only loads locations within Somalia bounding box.
    
    Args:
        db: Database session
        data_file: Path to GeoJSON file
        transport_type: 'airports', 'ports', or 'checkpoints'
    """
    print(f"Loading {transport_type} from {data_file}...")
    
    try:
        with open(data_file, 'r') as f:
            data = json.load(f)
        
        loaded_count = 0
        filtered_count = 0
        
        for feature in data.get('features', []):
            props = feature.get('properties', {})
            geom = feature.get('geometry', {})
            
            # Extract coordinates from geometry
            if geom.get('type') == 'Point':
                coords = geom.get('coordinates', [])
                if len(coords) >= 2:
                    longitude, latitude = coords[0], coords[1]
                else:
                    continue
            else:
                # Try to get from properties
                latitude = props.get('latitude') or props.get('lat') or props.get('y')
                longitude = props.get('longitude') or props.get('lon') or props.get('x')
                
                if not latitude or not longitude:
                    continue
            
            # Filter: Only Somalia locations
            try:
                lat_float = float(latitude)
                lon_float = float(longitude)
                
                if not is_in_somalia(lat_float, lon_float):
                    filtered_count += 1
                    continue
            except (ValueError, TypeError):
                filtered_count += 1
                continue
            
            region = props.get('region') or props.get('region_name') or props.get('admin1Name') or 'Unknown'
            
            if transport_type == 'airports':
                # Determine airport type
                airport_type = props.get('type') or props.get('aerodrome') or props.get('aeroway')
                if not airport_type or airport_type == 'unknown':
                    # Try to infer from IATA/ICAO codes
                    if props.get('iata') or props.get('icao'):
                        airport_type = 'international'
                    else:
                        airport_type = 'domestic'
                
                airport = models.Airport(
                    name=props.get('name', 'Unknown Airport'),
                    iata_code=props.get('iata_code') or props.get('iata'),
                    icao_code=props.get('icao_code') or props.get('icao'),
                    type=airport_type,
                    latitude=float(latitude),
                    longitude=float(longitude),
                    region=region
                )
                db.add(airport)
                loaded_count += 1
                
            elif transport_type == 'ports':
                port = models.Port(
                    name=props.get('name', 'Unknown Port'),
                    type=props.get('type') or props.get('port_type', 'commercial'),
                    latitude=float(latitude),
                    longitude=float(longitude),
                    region=region
                )
                db.add(port)
                loaded_count += 1
                
            elif transport_type == 'checkpoints':
                checkpoint = models.Checkpoint(
                    name=props.get('name', 'Unknown Checkpoint'),
                    type=props.get('type') or props.get('checkpoint_type', 'unknown'),
                    latitude=float(latitude),
                    longitude=float(longitude),
                    region=region,
                    status=props.get('status', 'active')
                )
                db.add(checkpoint)
                loaded_count += 1
        
        db.commit()
        print(f"Loaded {loaded_count} {transport_type}")
        if filtered_count > 0:
            print(f"  Filtered out {filtered_count} non-Somalia locations")
        
    except Exception as e:
        print(f"Error loading {transport_type}: {e}")


def main():
    """Main data loading function."""
    print("Starting Somalia Geography data loading...")

    # Create database tables
    SQLModel.metadata.create_all(bind=engine)

    # Get data directory path
    data_dir = Path(__file__).parent.parent / "app" / "data"

    with Session(engine) as db:
        # Load data in order (regions first, then districts, then roads)
        regions_file = data_dir / "somalia_regions.geojson"
        if regions_file.exists():
            load_regions(db, str(regions_file))
        else:
            print(f"Warning: {regions_file} not found")

        districts_file = data_dir / "somalia_districts.geojson"
        if districts_file.exists():
            load_districts(db, str(districts_file))
        else:
            print(f"Warning: {districts_file} not found")

        roads_file = data_dir / "somalia_roads.geojson"
        if roads_file.exists():
            load_roads(db, str(roads_file))
        else:
            print(f"Warning: {roads_file} not found")

        # Load transport data from OSM GeoJSON files
        airports_file = data_dir / "somalia_airports_osm.geojson"
        if airports_file.exists():
            load_transport_from_geojson(db, str(airports_file), "airports")
        else:
            print(f"Info: {airports_file} not found (optional)")

        ports_file = data_dir / "somalia_ports_osm.geojson"
        if ports_file.exists():
            load_transport_from_geojson(db, str(ports_file), "ports")
        else:
            print(f"Info: {ports_file} not found (optional)")

        checkpoints_file = data_dir / "somalia_checkpoints_osm.geojson"
        if checkpoints_file.exists():
            load_transport_from_geojson(db, str(checkpoints_file), "checkpoints")
        else:
            print(f"Info: {checkpoints_file} not found (optional)")

    print("Data loading completed successfully!")


if __name__ == "__main__":
    main()
