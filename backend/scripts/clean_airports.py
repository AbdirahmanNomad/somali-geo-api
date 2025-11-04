#!/usr/bin/env python3
"""
Clean airports database:
1. Remove duplicates (keep only one entry per unique location)
2. Remove airports from neighboring countries (Djibouti, Ethiopia, Kenya)
3. Use stricter Somalia bounding box
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.db import engine
from app import models
from sqlmodel import Session, select

# Stricter Somalia bounding box (excludes Djibouti and Ethiopia border areas)
# Somalia proper: roughly 2°N to 11°N, 41°E to 51°E
SOMALIA_LAT_MIN = 1.5  # More conservative to exclude border areas
SOMALIA_LAT_MAX = 11.5
SOMALIA_LON_MIN = 41.0
SOMALIA_LON_MAX = 51.5

# Known airports in neighboring countries (by IATA/ICAO codes)
DJIBOUTI_CODES = ['AII', 'HDAS', 'OBC', 'HDOB', 'JIB', 'HDAM', 'TDJ', 'HDTJ', 
                  'MHI', 'HDMO', 'HDDK', 'HDYO', 'HDHC', 'Z09C', 'HDMO']
ETHIOPIA_CODES = ['JIJ', 'HAJJ', 'DIR', 'HADR', 'ABK', 'HAKD', 'HIL', 'HASL', 
                  'GDE', 'HAGO', 'HDAE']
KENYA_CODES = ['NDE', 'HKMA']

def is_in_somalia_strict(lat: float, lon: float) -> bool:
    """Check if coordinates are within stricter Somalia bounds."""
    return (SOMALIA_LAT_MIN <= lat <= SOMALIA_LAT_MAX) and (SOMALIA_LON_MIN <= lon <= SOMALIA_LON_MAX)


def is_neighboring_country_airport(airport: models.Airport) -> bool:
    """Check if airport is in a neighboring country by IATA/ICAO code."""
    if airport.iata_code and airport.iata_code in DJIBOUTI_CODES + ETHIOPIA_CODES + KENYA_CODES:
        return True
    if airport.icao_code and airport.icao_code in DJIBOUTI_CODES + ETHIOPIA_CODES + KENYA_CODES:
        return True
    return False


def clean_airports():
    """Remove duplicates and non-Somalia airports."""
    print("="*70)
    print("Cleaning Airports Database")
    print("="*70)
    print()
    
    with Session(engine) as db:
        all_airports = db.exec(select(models.Airport)).all()
        print(f"Starting with {len(all_airports)} airports")
        print()
        
        # Step 1: Group by coordinates to find duplicates
        coord_groups = {}
        for airport in all_airports:
            # Round to 4 decimal places (~11 meters precision)
            key = (round(airport.latitude, 4), round(airport.longitude, 4))
            if key not in coord_groups:
                coord_groups[key] = []
            coord_groups[key].append(airport)
        
        duplicates_removed = 0
        non_somalia_removed = 0
        
        # Step 2: For each group, keep only one and check if it's in Somalia
        airports_to_keep = []
        airports_to_delete = []
        
        for coord, airports_group in coord_groups.items():
            # Keep the first one (or one with IATA/ICAO code if available)
            airport_to_keep = airports_group[0]
            for airport in airports_group:
                if airport.iata_code or airport.icao_code:
                    airport_to_keep = airport
                    break
            
            # Mark others as duplicates
            for airport in airports_group:
                if airport.id != airport_to_keep.id:
                    airports_to_delete.append(airport)
                    duplicates_removed += 1
            
            # Check if the one to keep is in Somalia
            lat, lon = coord
            
            # Check by code first (more reliable)
            if is_neighboring_country_airport(airport_to_keep):
                airports_to_delete.append(airport_to_keep)
                non_somalia_removed += 1
                print(f"  ✗ Removing {airport_to_keep.name} ({airport_to_keep.iata_code or airport_to_keep.icao_code or ''}) - neighboring country")
            # Check by coordinates
            elif not is_in_somalia_strict(lat, lon):
                airports_to_delete.append(airport_to_keep)
                non_somalia_removed += 1
                print(f"  ✗ Removing {airport_to_keep.name} - outside Somalia bounds ({lat:.4f}°N, {lon:.4f}°E)")
            else:
                airports_to_keep.append(airport_to_keep)
        
        # Delete all airports marked for removal
        for airport in airports_to_delete:
            db.delete(airport)
        
        db.commit()
        
        print()
        print("="*70)
        print("✅ Cleaning Complete!")
        print("="*70)
        print(f"  Removed duplicates: {duplicates_removed}")
        print(f"  Removed non-Somalia: {non_somalia_removed}")
        print(f"  Remaining airports: {len(airports_to_keep)}")
        print("="*70)
        
        return len(airports_to_keep)


def verify_airports():
    """Verify remaining airports are in Somalia."""
    print()
    print("="*70)
    print("Verification")
    print("="*70)
    
    with Session(engine) as db:
        airports = db.exec(select(models.Airport)).all()
        
        all_valid = True
        for airport in airports:
            if is_neighboring_country_airport(airport):
                print(f"  ✗ {airport.name} - neighboring country code detected")
                all_valid = False
            elif not is_in_somalia_strict(airport.latitude, airport.longitude):
                print(f"  ✗ {airport.name} - outside bounds ({airport.latitude:.4f}°N, {airport.longitude:.4f}°E)")
                all_valid = False
        
        if all_valid:
            print(f"  ✅ All {len(airports)} airports are in Somalia")
        
        print()
        print(f"Total airports: {len(airports)}")
        print()
        
        # Show some examples
        if airports:
            print("Sample Somalia Airports:")
            for airport in airports[:10]:
                codes = []
                if airport.iata_code:
                    codes.append(f"IATA: {airport.iata_code}")
                if airport.icao_code:
                    codes.append(f"ICAO: {airport.icao_code}")
                code_str = f" ({', '.join(codes)})" if codes else ""
                print(f"  • {airport.name}{code_str} - {airport.latitude:.4f}°N, {airport.longitude:.4f}°E")


def main():
    """Clean airports database."""
    remaining = clean_airports()
    verify_airports()
    
    print()
    print("="*70)
    print(f"✅ Final count: {remaining} unique Somalia airports")
    print("="*70)


if __name__ == "__main__":
    main()

