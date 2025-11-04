from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select, func

from app import models
from app.api import deps

router = APIRouter()


@router.get("/airports", response_model=models.AirportsPublic)
def read_airports(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    type: str | None = Query(None, description="Filter by type: 'international' or 'domestic'"),
) -> Any:
    """
    Retrieve airports.
    
    Filter by type: 'international' or 'domestic'
    """
    # Build query with optional filtering
    query = select(models.Airport)
    
    if type:
        if type.lower() not in ['international', 'domestic']:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid type '{type}'. Must be 'international' or 'domestic'"
            )
        query = query.where(models.Airport.type == type.lower())
    
    # Get total count
    count_query = select(func.count(models.Airport.id))
    if type:
        count_query = count_query.where(models.Airport.type == type.lower())
    total_count = db.exec(count_query).one()
    
    # Get paginated results
    airports = db.exec(query.offset(skip).limit(limit)).all()
    
    return models.AirportsPublic(data=airports, count=total_count)


@router.get("/airports/{airport_id}", response_model=models.AirportPublic)
def read_airport(
    *,
    db: Session = Depends(deps.get_db),
    airport_id: int,
) -> Any:
    """
    Get airport by ID.
    """
    airport = db.get(models.Airport, airport_id)
    if not airport:
        available_airports = db.exec(select(models.Airport.id)).all()
        available_ids = [str(a) for a in available_airports[:10]]
        raise HTTPException(
            status_code=404,
            detail=f"Airport '{airport_id}' not found. Available airport IDs: {', '.join(available_ids)}"
        )
    return airport


@router.get("/ports", response_model=models.PortsPublic)
def read_ports(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve ports.
    """
    # Get total count
    total_count = db.exec(select(func.count(models.Port.id))).one()
    
    # Get paginated results
    ports = db.exec(select(models.Port).offset(skip).limit(limit)).all()
    
    return models.PortsPublic(data=ports, count=total_count)


@router.get("/ports/{port_id}", response_model=models.PortPublic)
def read_port(
    *,
    db: Session = Depends(deps.get_db),
    port_id: int,
) -> Any:
    """
    Get port by ID.
    """
    port = db.get(models.Port, port_id)
    if not port:
        available_ports = db.exec(select(models.Port.id)).all()
        available_ids = [str(p) for p in available_ports[:10]]
        raise HTTPException(
            status_code=404,
            detail=f"Port '{port_id}' not found. Available port IDs: {', '.join(available_ids)}"
        )
    return port


@router.get("/checkpoints", response_model=models.CheckpointsPublic)
def read_checkpoints(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
) -> Any:
    """
    Retrieve checkpoints.
    """
    # Get total count
    total_count = db.exec(select(func.count(models.Checkpoint.id))).one()
    
    # Get paginated results
    checkpoints = db.exec(select(models.Checkpoint).offset(skip).limit(limit)).all()
    
    return models.CheckpointsPublic(data=checkpoints, count=total_count)


@router.get("/checkpoints/{checkpoint_id}", response_model=models.CheckpointPublic)
def read_checkpoint(
    *,
    db: Session = Depends(deps.get_db),
    checkpoint_id: int,
) -> Any:
    """
    Get checkpoint by ID.
    """
    checkpoint = db.get(models.Checkpoint, checkpoint_id)
    if not checkpoint:
        available_checkpoints = db.exec(select(models.Checkpoint.id)).all()
        available_ids = [str(c) for c in available_checkpoints[:10]]
        raise HTTPException(
            status_code=404,
            detail=f"Checkpoint '{checkpoint_id}' not found. Available checkpoint IDs: {', '.join(available_ids)}"
        )
    return checkpoint
