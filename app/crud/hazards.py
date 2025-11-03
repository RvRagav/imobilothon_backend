from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload, Session
from geoalchemy2 import WKTElement
from geoalchemy2.functions import ST_MakePoint
from geoalchemy2.types import Geography
from sqlalchemy import cast
from typing import List, Optional
from datetime import datetime

from app.db.models import Hazard, Device
from app.schemas.hazard import HazardCreate, HazardFilter


def create_hazard(db: Session, hazard: HazardCreate) -> Hazard:
    """Create a new hazard record."""
    # Get or create device
    device_result = db.execute(
        select(Device).where(Device.device_id == hazard.device_id)
    )
    device = device_result.scalar_one_or_none()

    if not device:
        # Create device with default type if not registered
        device = Device(
            device_id=hazard.device_id,
            device_type="unknown"  # Default type if device not registered
        )
        db.add(device)
        db.flush()

    # Create geometry point using WKTElement
    point = WKTElement(f"POINT({hazard.lon} {hazard.lat})", srid=4326)

    db_hazard = Hazard(
        hazard_type=hazard.hazard_type,
        severity=hazard.severity,
        confidence=hazard.confidence,
        geom=point,
        device_id=device.id
    )

    db.add(db_hazard)
    db.commit()
    db.refresh(db_hazard)
    return db_hazard


def get_hazard(db: Session, hazard_id: int) -> Optional[Hazard]:
    """Get a hazard by ID."""
    result = db.execute(
        select(Hazard)
        .where(Hazard.id == hazard_id)
        .options(selectinload(Hazard.device))
    )
    return result.scalar_one_or_none()


def get_hazards_nearby(
    db: Session,
    lat: float,
    lon: float,
    radius_m: float = 500.0
) -> List[Hazard]:
    """Get hazards within a given radius (in meters) from a point."""
    # Create point for the search location and set SRID=4326
    search_point = func.ST_SetSRID(ST_MakePoint(lon, lat), 4326)

    # Use geography distance to get meters reliably. Cast both geometry columns
    # to Geography so ST_Distance returns meters on spheroid.
    distance_expr = func.ST_Distance(
        cast(Hazard.geom, Geography),
        cast(search_point, Geography)
    )

    result = db.execute(
        select(Hazard)
        .where(distance_expr <= radius_m)
        .options(selectinload(Hazard.device))
        .order_by(Hazard.ts.desc())
    )

    return list(result.scalars().all())


def get_all_hazards(
    db: Session,
    filters: Optional[HazardFilter] = None,
    skip: int = 0,
    limit: int = 100
) -> List[Hazard]:
    """Get all hazards with optional filters."""
    query = select(Hazard).options(selectinload(Hazard.device))

    if filters:
        conditions = []

        if filters.hazard_type:
            conditions.append(Hazard.hazard_type == filters.hazard_type)

        if filters.severity_min is not None:
            conditions.append(Hazard.severity >= filters.severity_min)

        if filters.severity_max is not None:
            conditions.append(Hazard.severity <= filters.severity_max)

        if filters.start_date:
            conditions.append(Hazard.ts >= filters.start_date)

        if filters.end_date:
            conditions.append(Hazard.ts <= filters.end_date)

        if conditions:
            query = query.where(and_(*conditions))

    query = query.order_by(Hazard.ts.desc()).offset(skip).limit(limit)

    result = db.execute(query)
    return list(result.scalars().all())


def delete_hazard(db: Session, hazard_id: int) -> bool:
    """Delete a hazard by ID."""
    hazard = get_hazard(db, hazard_id)
    if not hazard:
        return False

    db.delete(hazard)
    db.commit()
    return True


def get_hazard_with_location(db: Session, hazard_id: int) -> Optional[dict]:
    """Get hazard with lat/lon extracted from geometry."""
    hazard = get_hazard(db, hazard_id)
    if not hazard:
        return None

    # Extract lat/lon from geometry using PostGIS functions
    result = db.execute(
        select(
            Hazard.id,
            Hazard.hazard_type,
            Hazard.severity,
            Hazard.confidence,
            Hazard.ts,
            func.ST_X(Hazard.geom).label("lon"),
            func.ST_Y(Hazard.geom).label("lat")
        ).where(Hazard.id == hazard_id)
    )
    row = result.first()

    if row:
        return {
            "id": row.id,
            "hazard_type": row.hazard_type,
            "severity": row.severity,
            "confidence": row.confidence,
            "ts": row.ts,
            "lat": row.lat,
            "lon": row.lon
        }
    return None

