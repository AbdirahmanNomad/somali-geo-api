"""
Open Location Code (OLC) helper utilities for Somalia Geography API.

Uses Google's Open Location Code library with Somalia-specific extensions.
"""

from typing import Optional, Tuple
from openlocationcode import openlocationcode as olc


def generate_olc(lat: float, lon: float, code_length: Optional[int] = None) -> str:
    """
    Generate Open Location Code for given coordinates.

    Args:
        lat: Latitude (-90 to 90)
        lon: Longitude (-180 to 180)
        code_length: Optional code length (default uses library default)

    Returns:
        Open Location Code string
    """
    if code_length:
        return olc.encode(lat, lon, code_length)
    return olc.encode(lat, lon)


def decode_olc(code: str) -> dict:
    """
    Decode Open Location Code to coordinates.

    Args:
        code: Open Location Code string

    Returns:
        Dictionary with decoded information
    """
    area = olc.decode(code)
    return {
        "code": code,
        "latitude_center": area.latitudeCenter,
        "longitude_center": area.longitudeCenter,
        "latitude_lo": area.latitudeLo,
        "longitude_lo": area.longitudeLo,
        "latitude_hi": area.latitudeHi,
        "longitude_hi": area.longitudeHi,
        "code_length": area.codeLength,
    }


def generate_somalia_olc(lat: float, lon: float, region_code: Optional[str] = None) -> str:
    """
    Generate Somalia-specific Open Location Code with region prefix.

    Args:
        lat: Latitude
        lon: Longitude
        region_code: Optional region code (e.g., "SOM-BNR" for Banadir)

    Returns:
        Somalia-specific location code
    """
    base_code = generate_olc(lat, lon)

    if region_code:
        return f"{region_code}:{base_code}"

    # Try to determine region based on coordinates (simplified)
    # This is a placeholder - in production, you'd use spatial queries
    region = _get_region_from_coords(lat, lon)
    if region:
        return f"SOM-{region}:{base_code}"

    return base_code


def decode_somalia_olc(code: str) -> dict:
    """
    Decode Somalia-specific Open Location Code.

    Args:
        code: Somalia location code (may include region prefix)

    Returns:
        Dictionary with decoded information
    """
    if ":" in code:
        region_part, olc_part = code.split(":", 1)
        result = decode_olc(olc_part)
        result["region_code"] = region_part
        return result
    else:
        return decode_olc(code)


def _get_region_from_coords(lat: float, lon: float) -> Optional[str]:
    """
    Determine Somalia region code from coordinates.

    This is a simplified implementation. In production, use spatial database queries.

    Args:
        lat: Latitude
        lon: Longitude

    Returns:
        Region code or None
    """
    # Simplified bounding boxes for Somali regions
    # These are approximate and should be replaced with actual spatial data
    regions = {
        "BNR": {"lat_min": 1.8, "lat_max": 2.2, "lon_min": 45.0, "lon_max": 45.6},  # Banadir
        "HRS": {"lat_min": 9.0, "lat_max": 10.0, "lon_min": 43.0, "lon_max": 45.0},  # Hiiraan
        "SHB": {"lat_min": 2.0, "lat_max": 3.0, "lon_min": 42.0, "lon_max": 43.0},  # Shabelle
        # Add more regions as needed
    }

    for code, bounds in regions.items():
        if (bounds["lat_min"] <= lat <= bounds["lat_max"] and
            bounds["lon_min"] <= lon <= bounds["lon_max"]):
            return code

    return None


def shorten_olc(code: str, lat: float, lon: float) -> str:
    """
    Shorten Open Location Code relative to reference point.

    Args:
        code: Full Open Location Code
        lat: Reference latitude
        lon: Reference longitude

    Returns:
        Shortened code
    """
    return olc.shorten(code, lat, lon)


def recover_olc(short_code: str, lat: float, lon: float) -> str:
    """
    Recover full Open Location Code from shortened version.

    Args:
        short_code: Shortened code
        lat: Reference latitude
        lon: Reference longitude

    Returns:
        Full Open Location Code
    """
    return olc.recoverNearest(short_code, lat, lon)
