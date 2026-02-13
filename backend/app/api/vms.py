"""
VM/Container Management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db
from app.schemas import VMResponse, VMStatusResponse
from app.models import VM, User
from app.dependencies import get_current_user
from app.services.proxmox import get_proxmox_service
from app.services.vm_sync import get_vm_sync_service

router = APIRouter(prefix="/vms", tags=["VMs"])


@router.get("", response_model=List[VMResponse])
def get_vms(
    type: Optional[str] = None,
    node: Optional[str] = None,
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of all VMs/containers from database cache
    
    Args:
        type: Filter by type ('qemu' or 'lxc')
        node: Filter by node
        status: Filter by status
        db: Database session
        current_user: Authenticated user
        
    Returns:
        List of VMs
    """
    query = db.query(VM)
    
    if type:
        query = query.filter(VM.type == type)
    if node:
        query = query.filter(VM.node == node)
    if status:
        query = query.filter(VM.status == status)
    
    vms = query.all()
    return vms


@router.get("/{vmid}", response_model=VMResponse)
def get_vm(
    vmid: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get specific VM/container by VMID
    
    Args:
        vmid: VM ID
        db: Database session
        current_user: Authenticated user
        
    Returns:
        VM details
    """
    vm = db.query(VM).filter(VM.vmid == vmid).first()
    
    if not vm:
        raise HTTPException(status_code=404, detail="VM not found")
    
    return vm


@router.get("/{vmid}/status", response_model=VMStatusResponse)
def get_vm_status(
    vmid: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get live status of VM/container from Proxmox
    
    Args:
        vmid: VM ID
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Live VM status
    """
    # Get VM from database to know node and type
    vm = db.query(VM).filter(VM.vmid == vmid).first()
    
    if not vm:
        raise HTTPException(status_code=404, detail="VM not found")
    
    try:
        # Get live status from Proxmox
        proxmox_service = get_proxmox_service()
        status = proxmox_service.get_vm_status(vm.node, vm.vmid, vm.type)
        
        return {
            "vmid": vm.vmid,
            "name": vm.name,
            "status": status.get('status'),
            "uptime": status.get('uptime'),
            "cpu": status.get('cpu'),
            "mem": status.get('mem'),
            "maxmem": status.get('maxmem')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get VM status: {str(e)}")


@router.post("/sync")
def sync_vms(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Manually trigger VM synchronization from Proxmox cluster
    
    Args:
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Sync statistics
    """
    try:
        vm_sync_service = get_vm_sync_service()
        stats = vm_sync_service.sync_vms(db)
        return {
            "message": "VM synchronization completed",
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Sync failed: {str(e)}")
