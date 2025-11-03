from sqlalchemy import select, text
from typing import Optional
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from app.db.models import Device, DeviceConfig


def check_database_health(db: Session) -> bool:
    """Check if database connection is healthy."""
    try:
        result = db.execute(text("SELECT 1"))
        result.scalar()
        return True
    except Exception:
        return False


def register_or_update_device(
    db: Session,
    device_id: str,
    device_type: str,
    model: Optional[str] = None,
    firmware_version: Optional[str] = None
) -> Device:
    """Register a new device or update existing device."""
    # Check if device exists
    result = db.execute(
        select(Device).where(Device.device_id == device_id)
    )
    device = result.scalar_one_or_none()

    if device:
        # Update existing device using setattr to avoid static typing issues with Column[...] attributes
        setattr(device, "device_type", device_type)
        setattr(device, "model", model)
        setattr(device, "firmware_version", firmware_version)
        setattr(device, "last_active", datetime.now(timezone.utc))
    else:
        # Create new device
        device = Device(
            device_id=device_id,
            device_type=device_type,
            model=model,
            firmware_version=firmware_version,
            last_active=datetime.now(timezone.utc)
        )
        db.add(device)
        db.flush()

        # Create default config for new device
        default_config = DeviceConfig(
            device_id=device.id,
            detection_interval=5,
            alert_radius=500,
            min_confidence_threshold=0.7
        )
        db.add(default_config)

    db.commit()
    db.refresh(device)
    return device


def get_device_by_device_id(db: Session, device_id: str) -> Optional[Device]:
    """Get device by device_id string."""
    result = db.execute(
        select(Device).where(Device.device_id == device_id)
    )
    return result.scalar_one_or_none()


def update_device_heartbeat(
    db: Session,
    device_id: str
) -> Optional[Device]:
    """Update last_active timestamp for a device."""
    device = get_device_by_device_id(db, device_id)
    if not device:
        return None

    setattr(device, "last_active", datetime.now(timezone.utc))
    setattr(device, "last_seen", datetime.now(timezone.utc))

    db.commit()
    db.refresh(device)
    return device


def get_device_config(
    db: Session,
    device_id: str
) -> Optional[DeviceConfig]:
    """Get device configuration by device_id string."""
    # First get the device
    device = get_device_by_device_id(db, device_id)
    if not device:
        return None

    # Get or create config
    result = db.execute(
        select(DeviceConfig).where(DeviceConfig.device_id == device.id)
    )
    config = result.scalar_one_or_none()

    if not config:
        # Create default config if it doesn't exist
        config = DeviceConfig(
            device_id=device.id,
            detection_interval=5,
            alert_radius=500,
            min_confidence_threshold=0.7
        )
        db.add(config)
        db.commit()
        db.refresh(config)

    return config

