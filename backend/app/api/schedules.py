"""
Schedules Management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas import ScheduleCreate, ScheduleUpdate, ScheduleResponse
from app.models import Schedule, VM, Group, User
from app.dependencies import get_current_user
from app.services.scheduler import get_scheduler_service
from app.utils.cron_validator import get_next_run_time

router = APIRouter(prefix="/schedules", tags=["Schedules"])


@router.get("", response_model=List[ScheduleResponse])
def get_schedules(
    enabled: bool = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of all schedules
    
    Args:
        enabled: Filter by enabled status
        db: Database session
        current_user: Authenticated user
        
    Returns:
        List of schedules
    """
    query = db.query(Schedule)
    
    if enabled is not None:
        query = query.filter(Schedule.enabled == enabled)
    
    schedules = query.all()
    return schedules


@router.get("/{schedule_id}", response_model=ScheduleResponse)
def get_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get specific schedule
    
    Args:
        schedule_id: Schedule ID
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Schedule details
    """
    schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    
    if not schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    return schedule


@router.post("", response_model=ScheduleResponse, status_code=201)
def create_schedule(
    schedule: ScheduleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create new schedule
    
    Args:
        schedule: Schedule data
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Created schedule
    """
    # Validate target exists
    if schedule.target_type == 'vm':
        target = db.query(VM).filter(VM.id == schedule.target_id).first()
        if not target:
            raise HTTPException(status_code=404, detail="Target VM not found")
    elif schedule.target_type == 'group':
        target = db.query(Group).filter(Group.id == schedule.target_id).first()
        if not target:
            raise HTTPException(status_code=404, detail="Target group not found")
    
    # Calculate next_run
    next_run = get_next_run_time(schedule.cron_expression)
    
    # Create schedule
    db_schedule = Schedule(
        name=schedule.name,
        target_type=schedule.target_type,
        target_id=schedule.target_id,
        action=schedule.action,
        cron_expression=schedule.cron_expression,
        enabled=schedule.enabled,
        next_run=next_run
    )
    db.add(db_schedule)
    db.commit()
    db.refresh(db_schedule)
    
    # Add to scheduler if enabled
    if schedule.enabled:
        scheduler_service = get_scheduler_service()
        scheduler_service.add_schedule(db_schedule.id, schedule.cron_expression)
    
    return db_schedule


@router.put("/{schedule_id}", response_model=ScheduleResponse)
def update_schedule(
    schedule_id: int,
    schedule: ScheduleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update schedule
    
    Args:
        schedule_id: Schedule ID
        schedule: Updated schedule data
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Updated schedule
    """
    db_schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    
    if not db_schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    # Update fields
    if schedule.name is not None:
        db_schedule.name = schedule.name
    
    if schedule.target_type is not None:
        db_schedule.target_type = schedule.target_type
    
    if schedule.target_id is not None:
        # Validate target exists
        if db_schedule.target_type == 'vm':
            target = db.query(VM).filter(VM.id == schedule.target_id).first()
            if not target:
                raise HTTPException(status_code=404, detail="Target VM not found")
        elif db_schedule.target_type == 'group':
            target = db.query(Group).filter(Group.id == schedule.target_id).first()
            if not target:
                raise HTTPException(status_code=404, detail="Target group not found")
        db_schedule.target_id = schedule.target_id
    
    if schedule.action is not None:
        db_schedule.action = schedule.action
    
    if schedule.cron_expression is not None:
        db_schedule.cron_expression = schedule.cron_expression
        # Recalculate next_run
        db_schedule.next_run = get_next_run_time(schedule.cron_expression)
    
    if schedule.enabled is not None:
        db_schedule.enabled = schedule.enabled
    
    db.commit()
    db.refresh(db_schedule)
    
    # Update scheduler
    scheduler_service = get_scheduler_service()
    if db_schedule.enabled:
        scheduler_service.update_schedule(schedule_id, db_schedule.cron_expression)
    else:
        scheduler_service.remove_schedule(schedule_id)
    
    return db_schedule


@router.delete("/{schedule_id}")
def delete_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete schedule
    
    Args:
        schedule_id: Schedule ID
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Success message
    """
    db_schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    
    if not db_schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    # Remove from scheduler
    scheduler_service = get_scheduler_service()
    scheduler_service.remove_schedule(schedule_id)
    
    # Delete from database
    db.delete(db_schedule)
    db.commit()
    
    return {"message": "Schedule deleted successfully"}


@router.post("/{schedule_id}/toggle")
def toggle_schedule(
    schedule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Toggle schedule enabled/disabled
    
    Args:
        schedule_id: Schedule ID
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Updated schedule
    """
    db_schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
    
    if not db_schedule:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    # Toggle enabled
    db_schedule.enabled = not db_schedule.enabled
    db.commit()
    db.refresh(db_schedule)
    
    # Update scheduler
    scheduler_service = get_scheduler_service()
    if db_schedule.enabled:
        scheduler_service.add_schedule(schedule_id, db_schedule.cron_expression)
    else:
        scheduler_service.remove_schedule(schedule_id)
    
    return {
        "message": f"Schedule {'enabled' if db_schedule.enabled else 'disabled'}",
        "enabled": db_schedule.enabled
    }
