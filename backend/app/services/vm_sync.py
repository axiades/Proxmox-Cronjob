"""
VM Synchronization Service
Periodically syncs VM/Container list from Proxmox cluster to database
"""
from datetime import datetime
from sqlalchemy.orm import Session
import logging

from app.services.proxmox import get_proxmox_service
from app.models import VM
from app.database import SessionLocal

logger = logging.getLogger(__name__)


class VMSyncService:
    """Service for synchronizing VM data from Proxmox to database"""
    
    def __init__(self):
        self.proxmox_service = get_proxmox_service()
    
    def sync_vms(self, db: Session = None) -> dict:
        """
        Sync all VMs/containers from Proxmox cluster to database
        
        Args:
            db: Database session (optional, will create if not provided)
            
        Returns:
            Dictionary with sync statistics
        """
        should_close_db = False
        if db is None:
            db = SessionLocal()
            should_close_db = True
        
        try:
            logger.info("Starting VM synchronization from Proxmox cluster")
            
            # Get all VMs from Proxmox
            proxmox_vms = self.proxmox_service.get_all_vms()
            
            stats = {
                'total': len(proxmox_vms),
                'added': 0,
                'updated': 0,
                'errors': 0
            }
            
            # Get existing VMs from database
            existing_vms = {vm.vmid: vm for vm in db.query(VM).all()}
            
            for vm_data in proxmox_vms:
                try:
                    vmid = vm_data['vmid']
                    
                    if vmid in existing_vms:
                        # Update existing VM
                        vm = existing_vms[vmid]
                        vm.name = vm_data['name']
                        vm.type = vm_data['type']
                        vm.node = vm_data['node']
                        vm.status = vm_data['status']
                        vm.maxmem = vm_data.get('maxmem')
                        vm.maxdisk = vm_data.get('maxdisk')
                        vm.uptime = vm_data.get('uptime')
                        vm.last_synced = datetime.now()
                        stats['updated'] += 1
                    else:
                        # Add new VM
                        vm = VM(
                            vmid=vmid,
                            name=vm_data['name'],
                            type=vm_data['type'],
                            node=vm_data['node'],
                            status=vm_data['status'],
                            maxmem=vm_data.get('maxmem'),
                            maxdisk=vm_data.get('maxdisk'),
                            uptime=vm_data.get('uptime'),
                            last_synced=datetime.now()
                        )
                        db.add(vm)
                        stats['added'] += 1
                
                except Exception as e:
                    logger.error(f"Error syncing VM {vm_data.get('vmid')}: {str(e)}")
                    stats['errors'] += 1
            
            # Commit all changes
            db.commit()
            
            logger.info(f"VM sync completed: {stats}")
            return stats
        
        except Exception as e:
            logger.error(f"VM synchronization failed: {str(e)}")
            if db:
                db.rollback()
            raise
        
        finally:
            if should_close_db and db:
                db.close()
    
    def get_vm_by_vmid(self, db: Session, vmid: int) -> VM:
        """
        Get VM from database by VMID
        
        Args:
            db: Database session
            vmid: VM ID
            
        Returns:
            VM object or None
        """
        return db.query(VM).filter(VM.vmid == vmid).first()


# Singleton instance
_vm_sync_service = None


def get_vm_sync_service() -> VMSyncService:
    """Get singleton VM sync service instance"""
    global _vm_sync_service
    if _vm_sync_service is None:
        _vm_sync_service = VMSyncService()
    return _vm_sync_service
