"""
Cron expression validation utilities
"""
from croniter import croniter
from datetime import datetime
from typing import Optional


def validate_cron_expression(expression: str) -> bool:
    """
    Validate a cron expression
    
    Args:
        expression: Cron expression string
        
    Returns:
        True if valid, False otherwise
    """
    try:
        croniter(expression)
        return True
    except Exception:
        return False


def get_next_run_time(expression: str, base_time: Optional[datetime] = None) -> Optional[datetime]:
    """
    Get the next execution time for a cron expression
    
    Args:
        expression: Cron expression string
        base_time: Base time to calculate from (default: now)
        
    Returns:
        Next execution datetime or None if invalid
    """
    try:
        if base_time is None:
            base_time = datetime.now()
        
        cron = croniter(expression, base_time)
        return cron.get_next(datetime)
    except Exception:
        return None


def get_cron_description(expression: str) -> str:
    """
    Get human-readable description of cron expression
    
    Args:
        expression: Cron expression string
        
    Returns:
        Human-readable description
    """
    # Simple descriptions for common patterns
    patterns = {
        "* * * * *": "Every minute",
        "*/5 * * * *": "Every 5 minutes",
        "*/10 * * * *": "Every 10 minutes",
        "*/15 * * * *": "Every 15 minutes",
        "*/30 * * * *": "Every 30 minutes",
        "0 * * * *": "Every hour",
        "0 */2 * * *": "Every 2 hours",
        "0 0 * * *": "Daily at midnight",
        "0 2 * * *": "Daily at 2:00 AM",
        "0 0 * * 0": "Weekly on Sunday",
        "0 0 1 * *": "Monthly on the 1st",
    }
    
    return patterns.get(expression, f"Custom: {expression}")
