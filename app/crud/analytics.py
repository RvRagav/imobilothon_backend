from sqlalchemy import select, func, cast, Date, Numeric
from sqlalchemy.orm import selectinload, Session
from typing import Dict, List
from datetime import datetime, timedelta, timezone

from app.db.models import Hazard, Alert, Device


def get_analytics_summary(db: Session) -> Dict:
    """Get summary statistics: total hazards, active alerts, verified count."""
    # Total hazards
    total_hazards_result = db.execute(
        select(func.count(Hazard.id))
    )
    total_hazards = total_hazards_result.scalar() or 0

    # Active alerts (sent or received, not acknowledged)
    active_alerts_result = db.execute(
        select(func.count(Alert.id))
        .where(Alert.status != "acknowledged")
    )
    active_alerts = active_alerts_result.scalar() or 0

    # Verified hazards count (hazards with verification status = "verified")
    # Note: This assumes EventVerification model exists
    # If EventVerification is not linked, we'll use a placeholder
    from app.db.models import EventVerification
    verified_result = db.execute(
        select(func.count(func.distinct(EventVerification.hazard_id)))
        .where(EventVerification.status == "verified")
    )
    verified_count = verified_result.scalar() or 0

    return {
        "total_hazards": total_hazards,
        "active_alerts": active_alerts,
        "verified_count": verified_count
    }


def get_hazard_trends(db: Session, days: int = 30) -> Dict:
    """Get hazard counts per type and per day."""
    # Hazards per type
    hazards_by_type_result = db.execute(
        select(
            Hazard.hazard_type,
            func.count(Hazard.id).label("count")
        )
        .group_by(Hazard.hazard_type)
    )
    hazards_by_type = {
        row.hazard_type: row.count
        for row in hazards_by_type_result.all()
    }

    # Hazards per day (last N days)
    start_date = datetime.now(timezone.utc) - timedelta(days=days)

    hazards_by_day_result = db.execute(
        select(
            cast(Hazard.ts, Date).label("date"),
            func.count(Hazard.id).label("count")
        )
        .where(Hazard.ts >= start_date)
        .group_by(cast(Hazard.ts, Date))
        .order_by(cast(Hazard.ts, Date))
    )
    hazards_by_day = [
        {"date": row.date.isoformat(), "count": row.count}
        for row in hazards_by_day_result.all()
    ]

    return {
        "hazards_by_type": hazards_by_type,
        "hazards_by_day": hazards_by_day
    }


def get_heatmap_data(db: Session) -> List[Dict]:
    """Get spatial clusters of hazards grouped by location."""
    # Group hazards by approximate grid cells (0.01 degree ≈ 1km)
    # This creates a simple spatial clustering
    # Cast ST_X/ST_Y to numeric before rounding because Postgres' round
    # with (double precision, integer) may not be available on all versions.
    lon_expr = func.round(cast(func.ST_X(Hazard.geom), Numeric), 3).label("lon")
    lat_expr = func.round(cast(func.ST_Y(Hazard.geom), Numeric), 3).label("lat")

    result = db.execute(
        select(
            lon_expr,
            lat_expr,
            func.count(Hazard.id).label("count")
        )
        .group_by(lon_expr, lat_expr)
        .having(func.count(Hazard.id) > 0)
    )

    clusters = []
    for row in result.all():
        clusters.append({
            "lat": float(row.lat),
            "lon": float(row.lon),
            "count": row.count
        })

    return clusters

