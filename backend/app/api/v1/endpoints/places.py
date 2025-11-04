from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, or_
from sqlalchemy import func

from app import models
from app.api import deps

router = APIRouter()


@router.get("/search", response_model=models.PlacesSearchResponse)
def search_places(
    *,
    db: Session = Depends(deps.get_db),
    name: str,
    limit: int = 10,
) -> Any:
    """
    Search for places (districts and regions) by name with fuzzy matching.
    Searches in district names, region names, and aliases.
    """
    name_lower = name.lower()
    results = []
    seen_ids = set()

    # Search in districts - match by name or region name
    districts = db.exec(
        select(models.District).where(
            or_(
                func.lower(models.District.name).contains(name_lower),
                func.lower(models.District.region_name).contains(name_lower),
            )
        ).limit(limit * 2)  # Get more to account for alias filtering
    ).all()

    for district in districts:
        # Check if name matches district name, region name, or any alias
        matches = (
            name_lower in district.name.lower() or
            name_lower in district.region_name.lower()
        )
        
        # Also check aliases
        aliases = district.aliases or []
        if not matches:
            matches = any(name_lower in alias.lower() for alias in aliases)

        if matches:
            district_id = district.code or f"SOM-{district.region_name[:3].upper()}-{district.name[:3].upper()}"
            if district_id not in seen_ids:
                result = models.PlaceSearchResult(
                    id=district_id,
                    name=district.name,
                    region=district.region_name,
                    type="district",
                    aliases=district.aliases,
                    centroid=district.centroid,
                    population=district.population,
                )
                results.append(result)
                seen_ids.add(district_id)
                
                if len(results) >= limit:
                    break

    # Also search in regions if we haven't reached the limit
    if len(results) < limit:
        regions = db.exec(
            select(models.Region).where(
                func.lower(models.Region.name).contains(name_lower)
            ).limit(limit - len(results))
        ).all()

        for region in regions:
            if region.code not in seen_ids:
                result = models.PlaceSearchResult(
                    id=region.code,
                    name=region.name,
                    region=region.name,
                    type="region",
                    centroid=None,  # Could calculate from geometry
                    population=region.population,
                )
                results.append(result)
                seen_ids.add(region.code)

    return models.PlacesSearchResponse(data=results, count=len(results))
