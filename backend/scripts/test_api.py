#!/usr/bin/env python3
"""
Test the Somalia Geography API endpoints with real data.
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

BASE_URL = "http://localhost:8000/api/v1"

def test_endpoint(method, endpoint, params=None, data=None, expected_status=200):
    """Test an API endpoint."""
    url = f"{BASE_URL}{endpoint}"
    
    try:
        if method.upper() == "GET":
            response = requests.get(url, params=params, timeout=5)
        elif method.upper() == "POST":
            response = requests.post(url, json=data, timeout=5)
        else:
            print(f"  ✗ Unsupported method: {method}")
            return False
        
        if response.status_code == expected_status:
            result = response.json()
            print(f"  ✓ {method} {endpoint}")
            if isinstance(result, dict):
                if "count" in result:
                    print(f"    Count: {result['count']}")
                if "data" in result and isinstance(result["data"], list):
                    print(f"    Items: {len(result['data'])}")
            return True
        else:
            print(f"  ✗ {method} {endpoint} - Status: {response.status_code}")
            print(f"    Error: {response.text[:200]}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"  ✗ {method} {endpoint} - Cannot connect to API (is it running?)")
        return False
    except Exception as e:
        print(f"  ✗ {method} {endpoint} - Error: {e}")
        return False

def main():
    """Test all API endpoints."""
    print("="*60)
    print("Somalia Geography API - Endpoint Testing")
    print("="*60)
    print(f"\nTesting against: {BASE_URL}")
    print("Make sure the API is running: uvicorn app.main:app --reload\n")
    
    tests_passed = 0
    tests_failed = 0
    
    # Test regions
    print("\n🗺️  Testing Regions Endpoints:")
    if test_endpoint("GET", "/regions"):
        tests_passed += 1
    else:
        tests_failed += 1
    
    if test_endpoint("GET", "/regions/1"):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test districts
    print("\n📍 Testing Districts Endpoints:")
    if test_endpoint("GET", "/districts"):
        tests_passed += 1
    else:
        tests_failed += 1
    
    if test_endpoint("GET", "/districts", params={"region": "Banadir"}):
        tests_passed += 1
    else:
        tests_failed += 1
    
    if test_endpoint("GET", "/districts/1"):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test roads
    print("\n🛣️  Testing Roads Endpoints:")
    if test_endpoint("GET", "/roads"):
        tests_passed += 1
    else:
        tests_failed += 1
    
    if test_endpoint("GET", "/roads/1"):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test location codes
    print("\n🧭 Testing Location Code Endpoints:")
    if test_endpoint("GET", "/locationcode/generate", params={"lat": 2.0144, "lon": 45.3047}):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test places search
    print("\n🔍 Testing Places Search:")
    if test_endpoint("GET", "/places/search", params={"name": "mogadishu"}):
        tests_passed += 1
    else:
        tests_failed += 1
    
    if test_endpoint("GET", "/places/search", params={"name": "beletweyne"}):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Test transport (may be empty)
    print("\n✈️  Testing Transport Endpoints:")
    if test_endpoint("GET", "/transport/airports"):
        tests_passed += 1
    else:
        tests_failed += 1
    
    if test_endpoint("GET", "/transport/ports"):
        tests_passed += 1
    else:
        tests_failed += 1
    
    if test_endpoint("GET", "/transport/checkpoints"):
        tests_passed += 1
    else:
        tests_failed += 1
    
    # Summary
    print("\n" + "="*60)
    print(f"Test Summary: {tests_passed} passed, {tests_failed} failed")
    print("="*60)
    
    if tests_failed == 0:
        print("\n✓ All tests passed!")
    else:
        print(f"\n✗ {tests_failed} test(s) failed. Check API server status.")
    
    return tests_failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)

