#!/usr/bin/env python3
"""
Test API endpoints directly (without HTTP) to verify functionality.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.core.db import engine
from app import models
from sqlmodel import Session

# Import endpoints directly to avoid auth dependencies
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import endpoint functions directly
from app.api.v1.endpoints.regions import read_regions, read_region
from app.api.v1.endpoints.districts import read_districts, read_district
from app.api.v1.endpoints.roads import read_roads, read_road
from app.api.v1.endpoints.location_codes import generate_location_code, resolve_location_code
from app.api.v1.endpoints.places import search_places
from app.api.v1.endpoints.transport import read_airports, read_ports, read_checkpoints

def test_regions():
    """Test regions endpoints."""
    print("\n🗺️  Testing Regions:")
    with Session(engine) as db:
        # Test list
        result = read_regions(db=db, skip=0, limit=10)
        print(f"  ✓ GET /regions - Found {result.count} regions, returned {len(result.data)}")
        assert result.count == 18, f"Expected 18 regions, got {result.count}"
        
        # Test get by ID
        if result.data:
            region = read_region(db=db, region_id=result.data[0].id)
            print(f"  ✓ GET /regions/{result.data[0].id} - {region.name}")
            assert region.name is not None

def test_districts():
    """Test districts endpoints."""
    print("\n📍 Testing Districts:")
    with Session(engine) as db:
        # Test list
        result = read_districts(db=db, skip=0, limit=10)
        print(f"  ✓ GET /districts - Found {result.count} districts, returned {len(result.data)}")
        assert result.count == 74, f"Expected 74 districts, got {result.count}"
        
        # Test filter by region
        result = read_districts(db=db, region="Banadir")
        print(f"  ✓ GET /districts?region=Banadir - Found {result.count} districts")
        
        # Test get by ID
        if result.data:
            district = read_district(db=db, district_id=result.data[0].id)
            print(f"  ✓ GET /districts/{result.data[0].id} - {district.name}")
            assert district.name is not None

def test_roads():
    """Test roads endpoints."""
    print("\n🛣️  Testing Roads:")
    with Session(engine) as db:
        result = read_roads(db=db, skip=0, limit=10)
        print(f"  ✓ GET /roads - Found {result.count} roads")
        assert result.count == 0, "Should have 0 roads (sample data removed)"

def test_location_codes():
    """Test location code endpoints."""
    print("\n🧭 Testing Location Codes:")
    # Test generate
    result = generate_location_code(lat=2.0144, lon=45.3047)
    print(f"  ✓ GET /locationcode/generate?lat=2.0144&lon=45.3047")
    print(f"    Code: {result.code}")
    assert result.code is not None
    assert abs(result.latitude_center - 2.0144) < 0.01
    assert abs(result.longitude_center - 45.3047) < 0.01
    
    # Test resolve
    if result.code:
        resolved = resolve_location_code(code=result.code)
        print(f"  ✓ GET /locationcode/resolve?code={result.code}")
        assert resolved.latitude_center is not None

def test_places_search():
    """Test places search."""
    print("\n🔍 Testing Places Search:")
    with Session(engine) as db:
        result = search_places(db=db, name="mogadishu", limit=10)
        print(f"  ✓ GET /places/search?name=mogadishu - Found {result.count} results")
        if result.data:
            print(f"    First result: {result.data[0].name} ({result.data[0].type})")

def test_transport():
    """Test transport endpoints."""
    print("\n✈️  Testing Transport:")
    with Session(engine) as db:
        # Airports
        result = read_airports(db=db)
        print(f"  ✓ GET /transport/airports - Found {result.count} airports")
        
        # Ports
        result = read_ports(db=db)
        print(f"  ✓ GET /transport/ports - Found {result.count} ports")
        
        # Checkpoints
        result = read_checkpoints(db=db)
        print(f"  ✓ GET /transport/checkpoints - Found {result.count} checkpoints")

def main():
    """Run all tests."""
    print("="*60)
    print("Somalia Geography API - Direct Testing")
    print("="*60)
    
    tests_passed = 0
    tests_failed = 0
    
    try:
        test_regions()
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ Error: {e}")
        tests_failed += 1
    
    try:
        test_districts()
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ Error: {e}")
        tests_failed += 1
    
    try:
        test_roads()
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ Error: {e}")
        tests_failed += 1
    
    try:
        test_location_codes()
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ Error: {e}")
        tests_failed += 1
    
    try:
        test_places_search()
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ Error: {e}")
        tests_failed += 1
    
    try:
        test_transport()
        tests_passed += 1
    except Exception as e:
        print(f"  ✗ Error: {e}")
        tests_failed += 1
    
    print("\n" + "="*60)
    print(f"Test Summary: {tests_passed} passed, {tests_failed} failed")
    print("="*60)
    
    if tests_failed == 0:
        print("\n✅ All tests passed!")
    else:
        print(f"\n❌ {tests_failed} test(s) failed.")
    
    return tests_failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

