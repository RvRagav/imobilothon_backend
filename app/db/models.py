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
    device_type = Column(String, nullable=False)   # e.g., "dashcam", "android", "ios"
    model = Column(String, nullable=True)
    firmware_version = Column(String, nullable=True)
    registered_at = Column(DateTime, server_default=text("NOW()"))
    last_seen = Column(DateTime, server_default=text("NOW()"))
    last_active = Column(DateTime, server_default=text("NOW()"))

    hazards = relationship("Hazard", back_populates="device")


# ========== HAZARD MODEL ==========
class Hazard(Base):
    __tablename__ = "hazards"

    id = Column(Integer, primary_key=True, index=True)
    hazard_type = Column(String, index=True)          # pothole, debris, collision
    severity = Column(Float)
    confidence = Column(Float)
    geom = Column(Geometry("POINT", srid=4326))       # PostGIS field for lat/lon
    ts = Column(DateTime, server_default=text("NOW()"))

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


# ========== ALERT MODEL ==========
class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    hazard_id = Column(Integer, ForeignKey("hazards.id", ondelete="CASCADE"), nullable=True)
    sender_device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"))
    receiver_device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), nullable=True)
    alert_type = Column(String, default="local")   # local, V2V
    status = Column(String, default="sent")        # sent, received, acknowledged
    created_at = Column(DateTime, server_default=text("NOW()"))
    acknowledged_at = Column(DateTime, nullable=True)

    hazard = relationship("Hazard", foreign_keys=[hazard_id])


# ========== DEVICE CONFIG MODEL ==========
class DeviceConfig(Base):
    __tablename__ = "device_configs"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id", ondelete="CASCADE"), unique=True, index=True)
    detection_interval = Column(Integer, default=5)  # seconds
    alert_radius = Column(Integer, default=500)      # meters
    min_confidence_threshold = Column(Float, default=0.7)
    last_updated = Column(DateTime, server_default=text("NOW()"))

    device = relationship("Device", foreign_keys=[device_id])