from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AlertCreate(BaseModel):
    hazard_id: Optional[int] = None
    sender_device_id: str
    receiver_device_id: Optional[str] = None
    alert_type: str = "local"  # local or V2V


class AlertAcknowledge(BaseModel):
    alert_id: int
    device_id: str


class AlertOut(BaseModel):
    id: int
    hazard_id: Optional[int]
    sender_device_id: int
    receiver_device_id: Optional[int]
    alert_type: str
    status: str
    created_at: datetime
    acknowledged_at: Optional[datetime]

    class Config:
        from_attributes = True
        orm_mode = True  # For backward compatibility

