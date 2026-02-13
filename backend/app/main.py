"""
FastAPI Application Main Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.config import settings
from app.api import auth, vms, groups, schedules, blackouts, logs, actions
from app.services.scheduler import get_scheduler_service
from app.services.vm_sync import get_vm_sync_service
from apscheduler.schedulers.background import BackgroundScheduler
import atexit

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="Proxmox Cronjob Web Interface",
    description="Cluster-wide VM/Container scheduling and management",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(auth.router, prefix="/api")
app.include_router(vms.router, prefix="/api")
app.include_router(groups.router, prefix="/api")
app.include_router(schedules.router, prefix="/api")
app.include_router(blackouts.router, prefix="/api")
app.include_router(logs.router, prefix="/api")
app.include_router(actions.router, prefix="/api")


@app.on_event("startup")
async def startup_event():
    """Application startup event"""
    logger.info("Starting Proxmox Cronjob Web Interface")
    
    # Start scheduler service
    scheduler_service = get_scheduler_service()
    scheduler_service.start()
    logger.info("Scheduler service started")
    
    # Setup periodic VM sync
    vm_sync_service = get_vm_sync_service()
    
    # Create background scheduler for VM sync
    vm_sync_scheduler = BackgroundScheduler()
    vm_sync_scheduler.add_job(
        func=vm_sync_service.sync_vms,
        trigger='interval',
        minutes=settings.VM_SYNC_INTERVAL_MINUTES,
        id='vm_sync_job'
    )
    vm_sync_scheduler.start()
    
    # Store scheduler in app state for shutdown
    app.state.vm_sync_scheduler = vm_sync_scheduler
    
    logger.info(f"VM sync scheduled every {settings.VM_SYNC_INTERVAL_MINUTES} minutes")
    
    # Run initial VM sync
    try:
        logger.info("Running initial VM synchronization")
        vm_sync_service.sync_vms()
    except Exception as e:
        logger.error(f"Initial VM sync failed: {str(e)}")


@app.on_event("shutdown")
async def shutdown_event():
    """Application shutdown event"""
    logger.info("Shutting down Proxmox Cronjob Web Interface")
    
    # Stop scheduler service
    scheduler_service = get_scheduler_service()
    scheduler_service.stop()
    logger.info("Scheduler service stopped")
    
    # Stop VM sync scheduler
    if hasattr(app.state, 'vm_sync_scheduler'):
        app.state.vm_sync_scheduler.shutdown()
        logger.info("VM sync scheduler stopped")


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "message": "Proxmox Cronjob Web Interface API",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/api/health")
def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "scheduler": "running" if get_scheduler_service()._running else "stopped"
    }


@app.get("/api/stats")
def get_dashboard_stats(db = None):
    """Get dashboard statistics"""
    from app.database import SessionLocal
    from app.models import VM, Schedule, Group, ExecutionLog
    from datetime import datetime, timedelta
    
    db = SessionLocal()
    try:
        total_vms = db.query(VM).count()
        running_vms = db.query(VM).filter(VM.status == 'running').count()
        stopped_vms = db.query(VM).filter(VM.status == 'stopped').count()
        
        total_schedules = db.query(Schedule).count()
        active_schedules = db.query(Schedule).filter(Schedule.enabled == True).count()
        
        total_groups = db.query(Group).count()
        
        # Recent executions (last 24 hours)
        yesterday = datetime.now() - timedelta(days=1)
        recent_executions = db.query(ExecutionLog).filter(
            ExecutionLog.executed_at >= yesterday
        ).count()
        
        failed_executions = db.query(ExecutionLog).filter(
            ExecutionLog.executed_at >= yesterday,
            ExecutionLog.status == 'failed'
        ).count()
        
        return {
            "total_vms": total_vms,
            "running_vms": running_vms,
            "stopped_vms": stopped_vms,
            "total_schedules": total_schedules,
            "active_schedules": active_schedules,
            "total_groups": total_groups,
            "recent_executions": recent_executions,
            "failed_executions": failed_executions
        }
    finally:
        db.close()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
