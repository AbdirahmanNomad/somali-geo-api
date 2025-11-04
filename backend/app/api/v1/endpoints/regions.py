from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select, func

from app import models
from app.api import deps

router = APIRouter()


@router.get("/", response_model=models.RegionsPublic)
def read_regions(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve regions.
    """
    # Get total count
    total_count = db.exec(select(func.count(models.Region.id))).one()
    
    # Get paginated results
    regions = db.exec(select(models.Region).offset(skip).limit(limit)).all()
    
    return models.RegionsPublic(data=regions, count=total_count)


@router.get("/{region_id}", response_model=models.RegionPublic)
def read_region(
    *,
    db: Session = Depends(deps.get_db),
    region_id: int,
) -> Any:
    """
    Get region by ID.
    """
    region = db.get(models.Region, region_id)
    if not region:
        # Get available region IDs for better error message
        available_regions = db.exec(select(models.Region.id)).all()
        available_ids = [str(r) for r in available_regions[:10]]
        raise HTTPException(
            status_code=404,
            detail=f"Region '{region_id}' not found. Available region IDs: {', '.join(available_ids)}"
        )
    return region
