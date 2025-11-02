from pydantic import BaseModel
from datetime import datetime

class DeviceCreate(BaseModel):
    device_id: str
    device_type: str | None = None

class DeviceOut(BaseModel):
    id: int
    device_id: str
    device_type: str | None
    registered_at: datetime

    class Config:
        orm_mode = True
