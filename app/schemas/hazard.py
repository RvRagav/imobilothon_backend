from pydantic import BaseModel
from datetime import datetime
from typing import Optional


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
        from_attributes = True
        orm_mode = True  # For backward compatibility


class HazardFilter(BaseModel):
    hazard_type: Optional[str] = None
    severity_min: Optional[float] = None
    severity_max: Optional[float] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class NearbyHazardParams(BaseModel):
    lat: float
    lon: float
    radius_m: float = 500.0  # Default 500 meters
