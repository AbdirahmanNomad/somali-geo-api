#!/usr/bin/env python3
"""
Filter and clean transport data to only include Somalia locations.
Removes all airports, ports, and checkpoints outside Somalia bounding box.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.db import engine
from app import models
from sqlmodel import Session, select

# Somalia bounding box
SOMALIA_LAT_MIN = -1.646
SOMALIA_LAT_MAX = 12.0
SOMALIA_LON_MIN = 40.993
SOMALIA_LON_MAX = 51.417


def is_in_somalia(lat: float, lon: float) -> bool:
    """Check if coordinates are within Somalia."""
    return (SOMALIA_LAT_MIN <= lat <= SOMALIA_LAT_MAX) and (SOMALIA_LON_MIN <= lon <= SOMALIA_LON_MAX)


def filter_airports():
    """Filter airports to only Somalia locations."""
    print("\n✈️  Filtering Airports...")
    
    with Session(engine) as db:
        airports = db.exec(select(models.Airport)).all()
        total = len(airports)
        removed = 0
        
        for airport in airports:
            if not is_in_somalia(airport.latitude, airport.longitude):
                db.delete(airport)
                removed += 1
        
        db.commit()
        remaining = total - removed
        
        print(f"  Total airports: {total}")
        print(f"  Removed (non-Somalia): {removed}")
        print(f"  Remaining (Somalia only): {remaining}")
        
        return remaining


def filter_ports():
    """Filter ports to only Somalia locations."""
    print("\n⚓ Filtering Ports...")
    
    with Session(engine) as db:
        ports = db.exec(select(models.Port)).all()
        total = len(ports)
        removed = 0
        
        for port in ports:
            if not is_in_somalia(port.latitude, port.longitude):
                db.delete(port)
                removed += 1
        
        db.commit()
        remaining = total - removed
        
        print(f"  Total ports: {total}")
        print(f"  Removed (non-Somalia): {removed}")
        print(f"  Remaining (Somalia only): {remaining}")
        
        return remaining


def filter_checkpoints():
    """Filter checkpoints to only Somalia locations."""
    print("\n🛂 Filtering Checkpoints...")
    
    with Session(engine) as db:
        checkpoints = db.exec(select(models.Checkpoint)).all()
        total = len(checkpoints)
        removed = 0
        
        for checkpoint in checkpoints:
            if not is_in_somalia(checkpoint.latitude, checkpoint.longitude):
                db.delete(checkpoint)
                removed += 1
        
        db.commit()
        remaining = total - removed
        
        print(f"  Total checkpoints: {total}")
        print(f"  Removed (non-Somalia): {removed}")
        print(f"  Remaining (Somalia only): {remaining}")
        
        return remaining


def main():
    """Filter all transport data to Somalia only."""
    print("="*70)
    print("Somalia Geography - Data Filtering")
    print("Filtering transport data to Somalia locations only")
    print("="*70)
    print(f"\nSomalia Bounding Box:")
    print(f"  Latitude: {SOMALIA_LAT_MIN}° to {SOMALIA_LAT_MAX}°")
    print(f"  Longitude: {SOMALIA_LON_MIN}° to {SOMALIA_LON_MAX}°")
    
    airports_count = filter_airports()
    ports_count = filter_ports()
    checkpoints_count = filter_checkpoints()
    
    print("\n" + "="*70)
    print("✅ Filtering Complete!")
    print("="*70)
    print(f"\nFinal Counts (Somalia Only):")
    print(f"  Airports:    {airports_count}")
    print(f"  Ports:       {ports_count}")
    print(f"  Checkpoints: {checkpoints_count}")
    print("="*70)


if __name__ == "__main__":
    main()

