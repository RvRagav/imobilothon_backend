from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.crud import alerts as crud
from app.schemas.alert import AlertCreate, AlertOut, AlertAcknowledge

router = APIRouter(prefix="/alerts", tags=["Alerts"])


@router.post("/", response_model=AlertOut, status_code=201)
def create_alert(
    alert: AlertCreate,
    db: Session = Depends(get_db)
):
    """
    Trigger local or V2V alert for detected hazard.
    
    - **hazard_id**: ID of the associated hazard (optional)
    - **sender_device_id**: Device ID sending the alert
    - **receiver_device_id**: Device ID receiving the alert (optional, for V2V)
    - **alert_type**: Type of alert ("local" or "V2V")
    """
    try:
        db_alert = crud.create_alert(db, alert)
        return AlertOut.model_validate(db_alert)
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to create alert: {str(e)}")


@router.get("/device/{device_id}", response_model=List[AlertOut])
def get_alerts_by_device(
    device_id: str,
    db: Session = Depends(get_db)
):
    """
    Get alerts sent/received by a device.
    
    - **device_id**: Device ID to get alerts for
    """
    try:
        alerts = crud.get_alerts_by_device(db, device_id)
        return [AlertOut.model_validate(alert) for alert in alerts]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch alerts: {str(e)}")


@router.post("/acknowledge", response_model=AlertOut)
def acknowledge_alert(
    ack: AlertAcknowledge,
    db: Session = Depends(get_db)
):
    """
    Mark alert as received/acknowledged.
    
    - **alert_id**: ID of the alert to acknowledge
    - **device_id**: Device ID acknowledging the alert
    """
    try:
        alert = crud.acknowledge_alert(db, ack.alert_id, ack.device_id)
        if not alert:
            raise HTTPException(
                status_code=404, 
                detail="Alert not found or device not authorized"
            )
        return AlertOut.model_validate(alert)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=422, detail=f"Failed to acknowledge alert: {str(e)}")


@router.delete("/{alert_id}", status_code=204)
def delete_alert(
    alert_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete old alerts (for housekeeping).
    
    - **alert_id**: ID of the alert to delete
    """
    success = crud.delete_alert(db, alert_id)
    if not success:
        raise HTTPException(status_code=404, detail="Alert not found")
    return None

