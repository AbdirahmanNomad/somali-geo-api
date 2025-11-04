from typing import Any
from fastapi import APIRouter, HTTPException, Query
from openlocationcode import openlocationcode as olc

from app import models
from app.utils.olc_helper import generate_somalia_olc, decode_somalia_olc

router = APIRouter()


@router.get("/generate", response_model=models.LocationCodeResponse)
def generate_location_code(
    *,
    lat: float = Query(..., ge=-90, le=90, description="Latitude (-90 to 90)"),
    lon: float = Query(..., ge=-180, le=180, description="Longitude (-180 to 180)"),
) -> Any:
    """
    Generate Open Location Code for given coordinates.
    Returns Somalia-specific location code with region prefix if available.
    """
    try:
        # Generate Somalia-specific OLC with region prefix
        code = generate_somalia_olc(lat, lon)
        
        # Decode to get center coordinates
        decoded = decode_somalia_olc(code)
        
        # Extract region code if present
        region_code = decoded.get("region_code")
        
        return models.LocationCodeResponse(
            code=code,
            latitude_center=decoded["latitude_center"],
            longitude_center=decoded["longitude_center"],
            region_code=region_code
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid coordinates: {str(e)}")


@router.get("/resolve", response_model=models.LocationCodeResponse)
def resolve_location_code(
    *,
    code: str = Query(..., description="Open Location Code (e.g., '8FJ53+PM' or 'SOM-BNR:8FJ53+PM')"),
) -> Any:
    """
    Resolve Open Location Code to coordinates.
    Supports both standard OLC codes and Somalia-specific codes with region prefix.
    """
    try:
        decoded = decode_somalia_olc(code)
        
        return models.LocationCodeResponse(
            code=code,
            latitude_center=decoded["latitude_center"],
            longitude_center=decoded["longitude_center"],
            region_code=decoded.get("region_code")
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid location code: {str(e)}")
