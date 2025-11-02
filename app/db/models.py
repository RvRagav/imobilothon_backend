from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, text
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from datetime import datetime
from app.db.base import Base

# ========== DEVICE MODEL ==========
class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String, unique=True, index=True)
    device_type = Column(String, nullable=True)   # e.g., "Android", "Dashcam"
    registered_at = Column(DateTime, server_default=text("NOW()"))
    last_seen = Column(DateTime, server_default=text("NOW()"))

    hazards = relationship("Hazard", back_populates="device")


# ========== HAZARD MODEL ==========
class Hazard(Base):
    __tablename__ = "hazards"

    id = Column(Integer, primary_key=True, index=True)
    hazard_type = Column(String, index=True)          # pothole, debris, collision
    severity = Column(Float)
    confidence = Column(Float)
    geom = Column(Geometry("POINT", srid=4326))       # PostGIS field for lat/lon
    ts = Column(DateTime, default=datetime.utcnow)

    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"))
    device = relationship("Device", back_populates="hazards")

    verifications = relationship("EventVerification", back_populates="hazard")


# ========== EVENT VERIFICATION MODEL (optional) ==========
class EventVerification(Base):
    __tablename__ = "event_verifications"

    id = Column(Integer, primary_key=True, index=True)
    hazard_id = Column(Integer, ForeignKey("hazards.id", ondelete="CASCADE"))
    verified_by = Column(String, nullable=True)     # admin username or system
    status = Column(String, default="pending")      # pending, verified, rejected
    verified_at = Column(DateTime, nullable=True)

    hazard = relationship("Hazard", back_populates="verifications")
