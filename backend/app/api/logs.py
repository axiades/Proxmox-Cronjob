"""
Execution Logs API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.schemas import ExecutionLogResponse
from app.models import ExecutionLog, User
from app.dependencies import get_current_user

router = APIRouter(prefix="/logs", tags=["Execution Logs"])


@router.get("", response_model=List[ExecutionLogResponse])
def get_execution_logs(
    limit: int = 100,
    offset: int = 0,
    status: Optional[str] = None,
    vmid: Optional[int] = None,
    schedule_id: Optional[int] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get execution logs with pagination and filtering
    
    Args:
        limit: Maximum number of logs to return
        offset: Number of logs to skip
        status: Filter by status ('success', 'failed', 'skipped')
        vmid: Filter by VM ID
        schedule_id: Filter by schedule ID
        db: Database session
        current_user: Authenticated user
        
    Returns:
        List of execution logs
    """
    query = db.query(ExecutionLog).order_by(ExecutionLog.executed_at.desc())
    
    if status:
        query = query.filter(ExecutionLog.status == status)
    if vmid:
        query = query.filter(ExecutionLog.vmid == vmid)
    if schedule_id:
        query = query.filter(ExecutionLog.schedule_id == schedule_id)
    
    logs = query.offset(offset).limit(limit).all()
    return logs


@router.get("/schedule/{schedule_id}", response_model=List[ExecutionLogResponse])
def get_schedule_logs(
    schedule_id: int,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get execution logs for specific schedule
    
    Args:
        schedule_id: Schedule ID
        limit: Maximum number of logs to return
        db: Database session
        current_user: Authenticated user
        
    Returns:
        List of execution logs
    """
    logs = db.query(ExecutionLog).filter(
        ExecutionLog.schedule_id == schedule_id
    ).order_by(
        ExecutionLog.executed_at.desc()
    ).limit(limit).all()
    
    return logs


@router.get("/vm/{vmid}", response_model=List[ExecutionLogResponse])
def get_vm_logs(
    vmid: int,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get execution logs for specific VM
    
    Args:
        vmid: VM ID
        limit: Maximum number of logs to return
        db: Database session
        current_user: Authenticated user
        
    Returns:
        List of execution logs
    """
    logs = db.query(ExecutionLog).filter(
        ExecutionLog.vmid == vmid
    ).order_by(
        ExecutionLog.executed_at.desc()
    ).limit(limit).all()
    
    return logs


@router.get("/stats")
def get_log_stats(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get execution statistics
    
    Args:
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Log statistics
    """
    total = db.query(ExecutionLog).count()
    success = db.query(ExecutionLog).filter(ExecutionLog.status == 'success').count()
    failed = db.query(ExecutionLog).filter(ExecutionLog.status == 'failed').count()
    skipped = db.query(ExecutionLog).filter(ExecutionLog.status == 'skipped').count()
    
    return {
        "total": total,
        "success": success,
        "failed": failed,
        "skipped": skipped,
        "success_rate": (success / total * 100) if total > 0 else 0
    }
