from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from app.db.database import get_db
from app.crud import hazards as crud
from app.schemas.hazard import HazardCreate, HazardOut, HazardFilter
from app.core.mqtt_client import publish_hazard_alert

router = APIRouter(prefix="/hazards", tags=["Hazards"])


@router.post("/", response_model=HazardOut, status_code=201)
def create_hazard(
    hazard: HazardCreate,
    db: Session = Depends(get_db)
):
    """
    Report a new road hazard (from device or app).
    
    - **lat**: Latitude of the hazard location
    - **lon**: Longitude of the hazard location
    - **hazard_type**: Type of hazard (e.g., "pothole", "debris", "collision")
    - **severity**: Severity score (0.0 to 1.0)
    - **confidence**: Detection confidence (0.0 to 1.0)
    - **device_id**: ID of the reporting device
    """
    try:
        db_hazard = crud.create_hazard(db, hazard)
        # Extract lat/lon from geometry for response. Guard if id is missing.
        hazard_id = getattr(db_hazard, "id", None)
        if hazard_id is None:
            raise HTTPException(status_code=500, detail="Failed to determine created hazard id")
        hazard_with_location = crud.get_hazard_with_location(db, int(hazard_id))
        if hazard_with_location:
            # Publish MQTT alert after successful hazard creation
            try:
                timestamp_str = hazard_with_location["ts"].isoformat() if isinstance(hazard_with_location["ts"], datetime) else str(hazard_with_location["ts"])
                publish_hazard_alert(
                    hazard_id=hazard_with_location["id"],
                    hazard_type=hazard_with_location["hazard_type"],
                    latitude=hazard_with_location["lat"],
                    longitude=hazard_with_location["lon"],
                    timestamp=timestamp_str
                )
            except Exception as mqtt_error:
                # Log MQTT error but don't fail the request
                print(f"⚠ Warning: Failed to publish MQTT alert: {str(mqtt_error)}")
            
            return HazardOut(**hazard_with_location)
        raise HTTPException(status_code=500, detail="Failed to extract hazard location")
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to create hazard: {str(e)}")


@router.get("/nearby", response_model=List[HazardOut])
def get_hazards_nearby(
    lat: float = Query(..., description="Latitude of search point"),
    lon: float = Query(..., description="Longitude of search point"),
    radius_m: float = Query(500.0, description="Search radius in meters (default: 500)"),
    db: Session = Depends(get_db)
):
    """
    Get hazards within a given radius (e.g., 500m) from a location.
    
    - **lat**: Latitude of the search center
    - **lon**: Longitude of the search center
    - **radius_m**: Search radius in meters (default: 500)
    """
    try:
        hazards = crud.get_hazards_nearby(db, lat, lon, radius_m)
        # Convert hazards to output format with lat/lon
        result = []
        for hazard in hazards:
            hid = getattr(hazard, "id", None)
            if hid is None:
                # skip malformed result
                continue
            hazard_data = crud.get_hazard_with_location(db, int(hid))
            if hazard_data:
                result.append(HazardOut(**hazard_data))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch nearby hazards: {str(e)}")


@router.get("/{hazard_id}", response_model=HazardOut)
def get_hazard(
    hazard_id: int,
    db: Session = Depends(get_db)
):
    """
    Get details of a specific hazard.
    
    - **hazard_id**: ID of the hazard to retrieve
    """
    hazard_data = crud.get_hazard_with_location(db, hazard_id)
    if not hazard_data:
        raise HTTPException(status_code=404, detail="Hazard not found")
    return HazardOut(**hazard_data)


@router.get("/", response_model=List[HazardOut])
def get_all_hazards(
    hazard_type: Optional[str] = Query(None, description="Filter by hazard type"),
    severity_min: Optional[float] = Query(None, description="Minimum severity"),
    severity_max: Optional[float] = Query(None, description="Maximum severity"),
    start_date: Optional[datetime] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date (ISO format)"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db)
):
    """
    Get all hazards with optional filters.
    
    - **hazard_type**: Filter by type (e.g., "pothole", "debris")
    - **severity_min**: Minimum severity score
    - **severity_max**: Maximum severity score
    - **start_date**: Filter hazards from this date onwards
    - **end_date**: Filter hazards up to this date
    - **skip**: Pagination offset
    - **limit**: Maximum number of results (1-1000)
    """
    try:
        filters = HazardFilter(
            hazard_type=hazard_type,
            severity_min=severity_min,
            severity_max=severity_max,
            start_date=start_date,
            end_date=end_date
        )
        hazards = crud.get_all_hazards(db, filters, skip, limit)
        
        # Convert to output format
        result = []
        for hazard in hazards:
            hid = getattr(hazard, "id", None)
            if hid is None:
                continue
            hazard_data = crud.get_hazard_with_location(db, int(hid))
            if hazard_data:
                result.append(HazardOut(**hazard_data))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch hazards: {str(e)}")


@router.delete("/{hazard_id}", status_code=204)
def delete_hazard(
    hazard_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete hazard (admin or verified user).
    
    - **hazard_id**: ID of the hazard to delete
    """
    success = crud.delete_hazard(db, hazard_id)
    if not success:
        raise HTTPException(status_code=404, detail="Hazard not found")
    return None

