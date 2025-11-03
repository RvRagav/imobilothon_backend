from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Dict, List, Optional

from app.db.database import get_db
from app.crud import analytics as crud

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/summary")
def get_analytics_summary(
    db: Session = Depends(get_db)
):
    """
    Returns total hazards, active alerts, and verified count.
    
    Returns:
    - **total_hazards**: Total number of hazards in the system
    - **active_alerts**: Number of non-acknowledged alerts
    - **verified_count**: Number of verified hazards
    """
    try:
        summary = crud.get_analytics_summary(db)
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch analytics summary: {str(e)}")


@router.get("/trends")
def get_hazard_trends(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    db: Session = Depends(get_db)
):
    """
    Returns hazard counts per type and per day.
    
    - **days**: Number of days to include in the analysis (default: 30, max: 365)
    
    Returns:
    - **hazards_by_type**: Dictionary mapping hazard types to counts
    - **hazards_by_day**: List of daily hazard counts with dates
    """
    try:
        trends = crud.get_hazard_trends(db, days)
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch trends: {str(e)}")


@router.get("/heatmap")
def get_heatmap_data(
    db: Session = Depends(get_db)
):
    """
    Returns spatial clusters (grouped by location).
    
    Returns a list of clusters where each cluster contains:
    - **lat**: Latitude of the cluster center
    - **lon**: Longitude of the cluster center
    - **count**: Number of hazards in this cluster
    """
    try:
        heatmap_data = crud.get_heatmap_data(db)
        return {"clusters": heatmap_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch heatmap data: {str(e)}")

