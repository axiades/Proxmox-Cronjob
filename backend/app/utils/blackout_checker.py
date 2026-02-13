"""
Blackout window checker utility
"""
from datetime import datetime, time
from typing import List, Tuple
import json
from sqlalchemy.orm import Session

from app.models import BlackoutWindow


def is_in_blackout(db: Session, check_time: datetime = None) -> Tuple[bool, str]:
    """
    Check if current time is within any active blackout window
    
    Args:
        db: Database session
        check_time: Time to check (default: now)
        
    Returns:
        Tuple of (is_in_blackout, reason)
    """
    if check_time is None:
        check_time = datetime.now()
    
    current_time = check_time.time()
    current_weekday = check_time.weekday()  # 0 = Monday, 6 = Sunday
    
    # Get all enabled blackout windows
    blackouts = db.query(BlackoutWindow).filter(
        BlackoutWindow.enabled == True
    ).all()
    
    for blackout in blackouts:
        # Check if current time is within blackout time range
        if is_time_in_range(current_time, blackout.start_time, blackout.end_time):
            # Check if current day is in the blackout days
            if blackout.days_of_week:
                try:
                    days = json.loads(blackout.days_of_week)
                    if current_weekday in days:
                        return True, f"Blackout window: {blackout.name}"
                except json.JSONDecodeError:
                    continue
            else:
                # No specific days means all days
                return True, f"Blackout window: {blackout.name}"
    
    return False, ""


def is_time_in_range(check_time: time, start_time: time, end_time: time) -> bool:
    """
    Check if a time is within a time range
    
    Handles ranges that cross midnight
    
    Args:
        check_time: Time to check
        start_time: Range start time
        end_time: Range end time
        
    Returns:
        True if time is in range
    """
    if start_time <= end_time:
        # Normal range (doesn't cross midnight)
        return start_time <= check_time <= end_time
    else:
        # Range crosses midnight
        return check_time >= start_time or check_time <= end_time
