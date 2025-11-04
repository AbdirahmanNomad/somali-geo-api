from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func

from app import models
from app.api import deps

router = APIRouter()


@router.get("/", response_model=models.RoadsPublic)
def read_roads(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    district: str | None = Query(None, description="Filter by district name"),
    type: str | None = Query(None, description="Filter by road type: 'primary' or 'secondary'"),
) -> Any:
    """
    Retrieve roads.
    Filter by type: 'primary' or 'secondary'
    Note: District filtering not yet implemented (requires spatial queries).
    """
    # Build query
    query = select(models.Road)
    count_query = select(func.count(models.Road.id))
    
    # Apply filters
    if district:
        district_str = str(district) if district else None
        if district_str:
            query = query.where(models.Road.name.contains(district_str))
            count_query = count_query.where(models.Road.name.contains(district_str))
    
    if type:
        if type.lower() not in ['primary', 'secondary']:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid type '{type}'. Must be 'primary' or 'secondary'"
            )
        type_str = type.lower()
        query = query.where(models.Road.type == type_str)
        count_query = count_query.where(models.Road.type == type_str)
    
    total_count = db.exec(count_query).one()
    
    # Get paginated results
    roads = db.exec(query.offset(skip).limit(limit)).all()
    
    return models.RoadsPublic(data=roads, count=total_count)


@router.get("/{road_id}", response_model=models.RoadPublic)
def read_road(
    *,
    db: Session = Depends(deps.get_db),
    road_id: int,
) -> Any:
    """
    Get road by ID.
    """
    road = db.get(models.Road, road_id)
    if not road:
        available_roads = db.exec(select(models.Road.id)).all()
        available_ids = [str(r) for r in available_roads[:10]]
        raise HTTPException(
            status_code=404,
            detail=f"Road '{road_id}' not found. Available road IDs: {', '.join(available_ids)}"
        )
    return road
