from pydantic import BaseModel
from datetime import datetime

class HazardBase(BaseModel):
    lat: float
    lon: float
    hazard_type: str
    severity: float
    confidence: float
    device_id: str

class HazardCreate(HazardBase):
    pass

class HazardOut(BaseModel):
    id: int
    hazard_type: str
    severity: float
    confidence: float
    ts: datetime
    lat: float
    lon: float

    class Config:
        orm_mode = True
