from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime


class DeviceRegister(BaseModel):
    device_id: str
    device_type: str  # e.g., "dashcam", "android", "ios"
    model: Optional[str] = None
    firmware_version: Optional[str] = None


class DeviceOut(BaseModel):
    id: int
    device_id: str
    device_type: str
    model: Optional[str]
    firmware_version: Optional[str]
    registered_at: datetime
    last_active: datetime

    class Config:
        from_attributes = True
        orm_mode = True  # For backward compatibility


class SystemHealth(BaseModel):
    api_status: str
    db_status: str
    timestamp: datetime


class SystemConfig(BaseModel):
    device_id: str
    detection_interval: int       # e.g., 5 seconds
    alert_radius: int             # e.g., 500 meters
    min_confidence_threshold: float  # e.g., 0.7
    last_updated: datetime

    class Config:
        from_attributes = True
