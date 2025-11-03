from sqlalchemy import select
from sqlalchemy.orm import selectinload, Session
from typing import List, Optional
from datetime import datetime, timezone

from app.db.models import Alert, Device
from app.schemas.alert import AlertCreate


def create_alert(db: Session, alert: AlertCreate) -> Alert:
    """Create a new alert."""
    # Get sender device
    sender_result = db.execute(
        select(Device).where(Device.device_id == alert.sender_device_id)
    )
    sender_device = sender_result.scalar_one_or_none()

    if not sender_device:
        # Create device with default type if not registered
        sender_device = Device(
            device_id=alert.sender_device_id,
            device_type="unknown"  # Default type if device not registered
        )
        db.add(sender_device)
        db.flush()

    # Get receiver device if provided
    receiver_device = None
    if alert.receiver_device_id:
        receiver_result = db.execute(
            select(Device).where(Device.device_id == alert.receiver_device_id)
        )
        receiver_device = receiver_result.scalar_one_or_none()

        if not receiver_device:
            # Create device with default type if not registered
            receiver_device = Device(
                device_id=alert.receiver_device_id,
                device_type="unknown"  # Default type if device not registered
            )
            db.add(receiver_device)
            db.flush()

    db_alert = Alert(
        hazard_id=alert.hazard_id,
        sender_device_id=sender_device.id,
        receiver_device_id=receiver_device.id if receiver_device else None,
        alert_type=alert.alert_type,
        status="sent"
    )

    db.add(db_alert)
    db.commit()
    db.refresh(db_alert)
    return db_alert


def get_alert(db: Session, alert_id: int) -> Optional[Alert]:
    """Get an alert by ID."""
    result = db.execute(
        select(Alert)
        .where(Alert.id == alert_id)
        .options(selectinload(Alert.hazard))
    )
    return result.scalar_one_or_none()


def get_alerts_by_device(db: Session, device_id: str) -> List[Alert]:
    """Get all alerts sent or received by a device."""
    # First get the device
    device_result = db.execute(
        select(Device).where(Device.device_id == device_id)
    )
    device = device_result.scalar_one_or_none()

    if not device:
        return []

    # Get alerts where device is sender or receiver
    result = db.execute(
        select(Alert)
        .where(
            (Alert.sender_device_id == device.id) |
            (Alert.receiver_device_id == device.id)
        )
        .options(selectinload(Alert.hazard))
        .order_by(Alert.created_at.desc())
    )
    return list(result.scalars().all())


def acknowledge_alert(
    db: Session,
    alert_id: int,
    device_id: str
) -> Optional[Alert]:
    """Mark an alert as acknowledged."""
    # Get device
    device_result = db.execute(
        select(Device).where(Device.device_id == device_id)
    )
    device = device_result.scalar_one_or_none()

    if not device:
        return None

    # Get alert
    alert = get_alert(db, alert_id)
    if not alert:
        return None

    # Update alert status
    object.__setattr__(alert, "status", "acknowledged")
    object.__setattr__(alert, "acknowledged_at", datetime.now(timezone.utc))

    db.commit()
    db.refresh(alert)
    return alert


def delete_alert(db: Session, alert_id: int) -> bool:
    """Delete an alert by ID."""
    alert = get_alert(db, alert_id)
    if not alert:
        return False

    db.delete(alert)
    db.commit()
    return True

