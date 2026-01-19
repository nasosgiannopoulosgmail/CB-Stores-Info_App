"""
Store schedule management endpoints
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime, date
from app.db.database import get_db
from app.models.schedule import StoreSchedule
from app.models.store import Store
from app.api.dependencies import verify_api_key

router = APIRouter()


class TimeRange(BaseModel):
    """Time range schema"""
    start: str  # Format: "HH:MM"
    end: str    # Format: "HH:MM"


class ScheduleBase(BaseModel):
    """Base schedule schema"""
    day_of_week: int  # 0=Monday, 6=Sunday
    time_ranges: List[TimeRange]
    is_holiday: bool = False
    date_override: Optional[date] = None
    active: bool = True


class ScheduleCreate(ScheduleBase):
    """Create schedule request"""
    pass


class ScheduleUpdate(BaseModel):
    """Update schedule request"""
    time_ranges: Optional[List[TimeRange]] = None
    is_holiday: Optional[bool] = None
    date_override: Optional[date] = None
    active: Optional[bool] = None


class ScheduleResponse(ScheduleBase):
    """Schedule response"""
    id: int
    store_id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


@router.get("/stores/{store_id}/schedules", response_model=List[ScheduleResponse])
async def get_store_schedules(
    store_id: int,
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key)
):
    """Get all schedules for a store"""
    # Verify store exists
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store {store_id} not found"
        )
    
    schedules = db.query(StoreSchedule).filter(
        StoreSchedule.store_id == store_id
    ).all()
    
    # Convert JSONB time_ranges to TimeRange objects
    result = []
    for s in schedules:
        schedule_dict = {
            "id": s.id,
            "store_id": s.store_id,
            "day_of_week": s.day_of_week,
            "time_ranges": [TimeRange(**tr) for tr in (s.time_ranges or [])],
            "is_holiday": s.is_holiday,
            "date_override": s.date_override,
            "active": s.active,
            "created_at": s.created_at,
            "updated_at": s.updated_at
        }
        result.append(ScheduleResponse(**schedule_dict))
    
    return result


@router.put("/stores/{store_id}/schedules", response_model=List[ScheduleResponse])
async def update_store_schedules(
    store_id: int,
    schedules: List[ScheduleCreate],
    db: Session = Depends(get_db),
    _: None = Depends(verify_api_key)
):
    """Update all schedules for a store"""
    # Verify store exists
    store = db.query(Store).filter(Store.id == store_id).first()
    if not store:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Store {store_id} not found"
        )
    
    # Delete existing schedules
    db.query(StoreSchedule).filter(StoreSchedule.store_id == store_id).delete()
    
    # Create new schedules
    created_schedules = []
    for schedule in schedules:
        db_schedule = StoreSchedule(
            store_id=store_id,
            day_of_week=schedule.day_of_week,
            time_ranges=[tr.dict() for tr in schedule.time_ranges],  # Convert to JSONB
            is_holiday=schedule.is_holiday,
            date_override=schedule.date_override,
            active=schedule.active
        )
        db.add(db_schedule)
        created_schedules.append(db_schedule)
    
    db.commit()
    
    # Return created schedules
    result = []
    for s in created_schedules:
        db.refresh(s)
        schedule_dict = {
            "id": s.id,
            "store_id": s.store_id,
            "day_of_week": s.day_of_week,
            "time_ranges": [TimeRange(**tr) for tr in (s.time_ranges or [])],
            "is_holiday": s.is_holiday,
            "date_override": s.date_override,
            "active": s.active,
            "created_at": s.created_at,
            "updated_at": s.updated_at
        }
        result.append(ScheduleResponse(**schedule_dict))
    
    return result
