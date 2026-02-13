"""
Scheduler Service
Manages scheduled tasks using APScheduler
"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.jobstores.memory import MemoryJobStore
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from app.database import SessionLocal
from app.models import Schedule, ExecutionLog, VM, Group, GroupMember
from app.services.proxmox import get_proxmox_service
from app.utils.blackout_checker import is_in_blackout
from app.utils.cron_validator import get_next_run_time

logger = logging.getLogger(__name__)


class SchedulerService:
    """Service for managing scheduled VM/container actions"""
    
    def __init__(self):
        """Initialize the scheduler"""
        jobstores = {
            'default': MemoryJobStore()
        }
        
        self.scheduler = BackgroundScheduler(jobstores=jobstores)
        self.proxmox_service = get_proxmox_service()
        self._running = False
    
    def start(self):
        """Start the scheduler"""
        if not self._running:
            self.scheduler.start()
            self._running = True
            logger.info("Scheduler started")
            
            # Load all enabled schedules
            self.load_schedules()
    
    def stop(self):
        """Stop the scheduler"""
        if self._running:
            self.scheduler.shutdown()
            self._running = False
            logger.info("Scheduler stopped")
    
    def load_schedules(self):
        """Load all enabled schedules from database"""
        db = SessionLocal()
        try:
            schedules = db.query(Schedule).filter(Schedule.enabled == True).all()
            
            for schedule in schedules:
                self.add_schedule(schedule.id, schedule.cron_expression)
            
            logger.info(f"Loaded {len(schedules)} schedules")
        finally:
            db.close()
    
    def add_schedule(self, schedule_id: int, cron_expression: str):
        """
        Add a schedule to the scheduler
        
        Args:
            schedule_id: Schedule ID
            cron_expression: Cron expression
        """
        try:
            # Create job ID
            job_id = f"schedule_{schedule_id}"
            
            # Remove existing job if present
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
            
            # Add new job
            self.scheduler.add_job(
                func=self.execute_schedule,
                trigger=CronTrigger.from_crontab(cron_expression),
                args=[schedule_id],
                id=job_id,
                replace_existing=True
            )
            
            logger.info(f"Added schedule {schedule_id} with cron: {cron_expression}")
            
            # Update next_run time in database
            self.update_next_run(schedule_id, cron_expression)
        
        except Exception as e:
            logger.error(f"Error adding schedule {schedule_id}: {str(e)}")
    
    def remove_schedule(self, schedule_id: int):
        """
        Remove a schedule from the scheduler
        
        Args:
            schedule_id: Schedule ID
        """
        try:
            job_id = f"schedule_{schedule_id}"
            if self.scheduler.get_job(job_id):
                self.scheduler.remove_job(job_id)
                logger.info(f"Removed schedule {schedule_id}")
        except Exception as e:
            logger.error(f"Error removing schedule {schedule_id}: {str(e)}")
    
    def update_schedule(self, schedule_id: int, cron_expression: str):
        """
        Update a schedule
        
        Args:
            schedule_id: Schedule ID
            cron_expression: New cron expression
        """
        self.add_schedule(schedule_id, cron_expression)
    
    def update_next_run(self, schedule_id: int, cron_expression: str):
        """
        Update next_run timestamp in database
        
        Args:
            schedule_id: Schedule ID
            cron_expression: Cron expression
        """
        db = SessionLocal()
        try:
            schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
            if schedule:
                next_run = get_next_run_time(cron_expression)
                schedule.next_run = next_run
                db.commit()
        finally:
            db.close()
    
    def execute_schedule(self, schedule_id: int):
        """
        Execute a scheduled task
        
        Args:
            schedule_id: Schedule ID
        """
        db = SessionLocal()
        try:
            logger.info(f"Executing schedule {schedule_id}")
            
            # Get schedule
            schedule = db.query(Schedule).filter(Schedule.id == schedule_id).first()
            if not schedule:
                logger.error(f"Schedule {schedule_id} not found")
                return
            
            # Check if in blackout window
            in_blackout, reason = is_in_blackout(db)
            if in_blackout:
                logger.info(f"Schedule {schedule_id} skipped: {reason}")
                self._log_execution(db, schedule, None, 'skipped', skipped_reason=reason)
                return
            
            # Get target VMs
            vms = self._get_target_vms(db, schedule)
            
            if not vms:
                logger.warning(f"No VMs found for schedule {schedule_id}")
                return
            
            # Execute action on each VM
            for vm in vms:
                self._execute_vm_action(db, schedule, vm)
            
            # Update last_run and next_run
            schedule.last_run = datetime.now()
            schedule.next_run = get_next_run_time(schedule.cron_expression)
            db.commit()
        
        except Exception as e:
            logger.error(f"Error executing schedule {schedule_id}: {str(e)}")
            db.rollback()
        
        finally:
            db.close()
    
    def _get_target_vms(self, db: Session, schedule: Schedule) -> list:
        """Get list of VMs to execute action on"""
        vms = []
        
        if schedule.target_type == 'vm':
            # Single VM
            vm = db.query(VM).filter(VM.id == schedule.target_id).first()
            if vm:
                vms.append(vm)
        
        elif schedule.target_type == 'group':
            # Group of VMs
            group_members = db.query(GroupMember).filter(
                GroupMember.group_id == schedule.target_id
            ).all()
            
            for member in group_members:
                if member.vm:
                    vms.append(member.vm)
        
        return vms
    
    def _execute_vm_action(self, db: Session, schedule: Schedule, vm: VM):
        """Execute action on a single VM"""
        start_time = datetime.now()
        
        try:
            logger.info(f"Executing {schedule.action} on {vm.type}/{vm.vmid} ({vm.name})")
            
            # Execute action via Proxmox API
            upid = None
            if schedule.action == 'start':
                upid = self.proxmox_service.start_vm(vm.node, vm.vmid, vm.type)
            elif schedule.action == 'stop':
                upid = self.proxmox_service.stop_vm(vm.node, vm.vmid, vm.type)
            elif schedule.action == 'restart':
                upid = self.proxmox_service.reboot_vm(vm.node, vm.vmid, vm.type)
            elif schedule.action == 'shutdown':
                upid = self.proxmox_service.shutdown_vm(vm.node, vm.vmid, vm.type)
            elif schedule.action == 'reset':
                upid = self.proxmox_service.reset_vm(vm.node, vm.vmid, vm.type)
            else:
                raise ValueError(f"Unknown action: {schedule.action}")
            
            # Calculate duration
            duration = int((datetime.now() - start_time).total_seconds())
            
            # Log success
            self._log_execution(
                db, schedule, vm, 'success',
                duration_seconds=duration,
                upid=upid
            )
            
            logger.info(f"Successfully executed {schedule.action} on {vm.vmid}")
        
        except Exception as e:
            # Calculate duration
            duration = int((datetime.now() - start_time).total_seconds())
            
            # Log failure
            error_message = str(e)
            self._log_execution(
                db, schedule, vm, 'failed',
                duration_seconds=duration,
                error_message=error_message
            )
            
            logger.error(f"Failed to execute {schedule.action} on {vm.vmid}: {error_message}")
    
    def _log_execution(self, db: Session, schedule: Schedule, vm: VM, status: str,
                       duration_seconds: int = None, error_message: str = None,
                       upid: str = None, skipped_reason: str = None):
        """Log execution to database"""
        log = ExecutionLog(
            schedule_id=schedule.id,
            vm_id=vm.id if vm else None,
            vmid=vm.vmid if vm else None,
            vm_name=vm.name if vm else None,
            action=schedule.action,
            status=status,
            executed_at=datetime.now(),
            duration_seconds=duration_seconds,
            error_message=error_message,
            upid=upid,
            skipped_reason=skipped_reason
        )
        db.add(log)
        db.commit()


# Singleton instance
_scheduler_service = None


def get_scheduler_service() -> SchedulerService:
    """Get singleton scheduler service instance"""
    global _scheduler_service
    if _scheduler_service is None:
        _scheduler_service = SchedulerService()
    return _scheduler_service
