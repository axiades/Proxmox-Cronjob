"""
Blackout Windows Management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas import BlackoutWindowCreate, BlackoutWindowUpdate, BlackoutWindowResponse
from app.models import BlackoutWindow, User
from app.dependencies import get_current_user

router = APIRouter(prefix="/blackouts", tags=["Blackout Windows"])


@router.get("", response_model=List[BlackoutWindowResponse])
def get_blackout_windows(
    enabled: bool = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of all blackout windows
    
    Args:
        enabled: Filter by enabled status
        db: Database session
        current_user: Authenticated user
        
    Returns:
        List of blackout windows
    """
    query = db.query(BlackoutWindow)
    
    if enabled is not None:
        query = query.filter(BlackoutWindow.enabled == enabled)
    
    blackouts = query.all()
    return blackouts


@router.get("/{blackout_id}", response_model=BlackoutWindowResponse)
def get_blackout_window(
    blackout_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get specific blackout window
    
    Args:
        blackout_id: Blackout window ID
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Blackout window details
    """
    blackout = db.query(BlackoutWindow).filter(BlackoutWindow.id == blackout_id).first()
    
    if not blackout:
        raise HTTPException(status_code=404, detail="Blackout window not found")
    
    return blackout


@router.post("", response_model=BlackoutWindowResponse, status_code=201)
def create_blackout_window(
    blackout: BlackoutWindowCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create new blackout window
    
    Args:
        blackout: Blackout window data
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Created blackout window
    """
    db_blackout = BlackoutWindow(
        name=blackout.name,
        description=blackout.description,
        start_time=blackout.start_time,
        end_time=blackout.end_time,
        days_of_week=blackout.days_of_week,
        enabled=blackout.enabled
    )
    db.add(db_blackout)
    db.commit()
    db.refresh(db_blackout)
    
    return db_blackout


@router.put("/{blackout_id}", response_model=BlackoutWindowResponse)
def update_blackout_window(
    blackout_id: int,
    blackout: BlackoutWindowUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update blackout window
    
    Args:
        blackout_id: Blackout window ID
        blackout: Updated blackout window data
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Updated blackout window
    """
    db_blackout = db.query(BlackoutWindow).filter(BlackoutWindow.id == blackout_id).first()
    
    if not db_blackout:
        raise HTTPException(status_code=404, detail="Blackout window not found")
    
    # Update fields
    if blackout.name is not None:
        db_blackout.name = blackout.name
    if blackout.description is not None:
        db_blackout.description = blackout.description
    if blackout.start_time is not None:
        db_blackout.start_time = blackout.start_time
    if blackout.end_time is not None:
        db_blackout.end_time = blackout.end_time
    if blackout.days_of_week is not None:
        db_blackout.days_of_week = blackout.days_of_week
    if blackout.enabled is not None:
        db_blackout.enabled = blackout.enabled
    
    db.commit()
    db.refresh(db_blackout)
    
    return db_blackout


@router.delete("/{blackout_id}")
def delete_blackout_window(
    blackout_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete blackout window
    
    Args:
        blackout_id: Blackout window ID
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Success message
    """
    db_blackout = db.query(BlackoutWindow).filter(BlackoutWindow.id == blackout_id).first()
    
    if not db_blackout:
        raise HTTPException(status_code=404, detail="Blackout window not found")
    
    db.delete(db_blackout)
    db.commit()
    
    return {"message": "Blackout window deleted successfully"}
