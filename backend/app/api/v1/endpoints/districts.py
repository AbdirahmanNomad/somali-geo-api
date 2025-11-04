from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func

from app import models
from app.api import deps

router = APIRouter()


@router.get("/", response_model=models.DistrictsPublic)
def read_districts(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    region: str | None = Query(None, description="Filter by region name"),
) -> Any:
    """
    Retrieve districts.
    """
    # Build query
    query = select(models.District)
    count_query = select(func.count(models.District.id))
    
    if region:
        query = query.where(models.District.region_name == region)
        count_query = count_query.where(models.District.region_name == region)

    # Get total count
    total_count = db.exec(count_query).one()
    
    # Get paginated results
    districts = db.exec(query.offset(skip).limit(limit)).all()
    
    return models.DistrictsPublic(data=districts, count=total_count)


@router.get("/{district_id}", response_model=models.DistrictPublic)
def read_district(
    *,
    db: Session = Depends(deps.get_db),
    district_id: int,
) -> Any:
    """
    Get district by ID.
    """
    district = db.get(models.District, district_id)
    if not district:
        # Get available district IDs for better error message
        available_districts = db.exec(select(models.District.id)).all()
        available_ids = [str(d) for d in available_districts[:10]]
        raise HTTPException(
            status_code=404,
            detail=f"District '{district_id}' not found. Available district IDs: {', '.join(available_ids)}"
        )
    return district
