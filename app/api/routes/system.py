from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from typing import Any, cast

from app.db.database import get_db
from app.crud import system as crud
from app.schemas.device import DeviceRegister, DeviceOut, SystemHealth, SystemConfig

router = APIRouter(prefix="/system", tags=["System"])


@router.get("/health", response_model=SystemHealth)
def get_system_health(
    db: Session = Depends(get_db)
):
    """
    Returns API and DB status.
    
    Returns:
    - **api_status**: Status of the API ("healthy" or "unhealthy")
    - **db_status**: Status of the database connection ("healthy" or "unhealthy")
    - **timestamp**: Current timestamp
    """
    try:
        db_healthy = crud.check_database_health(db)
        db_status = "healthy" if db_healthy else "unhealthy"
        api_status = "healthy"  # API is running if we can reach this endpoint
        
        return SystemHealth(
            api_status=api_status,
            db_status=db_status,
            timestamp=datetime.now(timezone.utc)
        )
    except Exception as e:
        return SystemHealth(
            api_status="unhealthy",
            db_status="unhealthy",
            timestamp=datetime.now(timezone.utc)
        )


@router.post("/register", response_model=DeviceOut, status_code=200)
def register_device(
    device: DeviceRegister,
    db: Session = Depends(get_db)
):
    """
    Registers or updates a device.
    
    - **device_id**: Unique identifier for the device
    - **device_type**: Type of device (e.g., "dashcam", "android", "ios")
    - **model**: Device model (optional)
    - **firmware_version**: Firmware version (optional)
    
    Returns the registered/updated device information.
    """
    try:
        db_device = crud.register_or_update_device(
            db,
            device.device_id,
            device.device_type,
            device.model,
            device.firmware_version
        )
        return DeviceOut.model_validate(db_device)
    except Exception as e:
        raise HTTPException(
            status_code=422,
            detail=f"Failed to register device: {str(e)}"
        )


@router.get("/config/{device_id}", response_model=SystemConfig)
def get_device_config(
    device_id: str,
    db: Session = Depends(get_db)
):
    """
    Fetches device runtime configuration.
    
    - **device_id**: Device ID to fetch configuration for
    
    Returns:
    - **device_id**: Device identifier
    - **detection_interval**: Detection interval in seconds
    - **alert_radius**: Alert radius in meters
    - **min_confidence_threshold**: Minimum confidence threshold (0.0-1.0)
    - **last_updated**: Last update timestamp
    """
    config = crud.get_device_config(db, device_id)
    if not config:
        raise HTTPException(
            status_code=404,
            detail=f"Device '{device_id}' not found"
        )
    
    # Get device to return device_id string
    device = crud.get_device_by_device_id(db, device_id)
    if not device:
        # This should not normally happen because we looked up config by device id,
        # but guard against it to avoid AttributeError when accessing device.device_id
        raise HTTPException(
            status_code=404,
            detail=f"Device '{device_id}' not found"
        )
    return SystemConfig(
        device_id=str(device.device_id),
        detection_interval=int(cast(Any, config.detection_interval)),
        alert_radius=int(cast(Any, config.alert_radius)),
        min_confidence_threshold=float(cast(Any, config.min_confidence_threshold)),
        last_updated=cast(datetime, config.last_updated)
    )
    


@router.put("/heartbeat/{device_id}", response_model=DeviceOut)
def update_heartbeat(
    device_id: str,
    db: Session = Depends(get_db)
):
    """
    Updates last active timestamp for a device.
    
    - **device_id**: Device ID to update heartbeat for
    
    Returns the updated device information.
    """
    device = crud.update_device_heartbeat(db, device_id)
    if not device:
        raise HTTPException(
            status_code=404,
            detail=f"Device '{device_id}' not found"
        )
    
    return DeviceOut.model_validate(device)

