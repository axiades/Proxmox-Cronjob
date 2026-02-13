"""
Manual Actions API endpoints
Execute immediate actions on VMs/containers without scheduling
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime

from app.database import get_db
from app.schemas import ActionRequest, ActionResponse
from app.models import VM, Group, GroupMember, ExecutionLog, User
from app.dependencies import get_current_user
from app.services.proxmox import get_proxmox_service

router = APIRouter(prefix="/actions", tags=["Actions"])


@router.post("/vm/{vmid}", response_model=ActionResponse)
def execute_vm_action(
    vmid: int,
    action_request: ActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Execute immediate action on a VM/container
    
    Args:
        vmid: VM ID
        action_request: Action to perform
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Action result
    """
    # Get VM from database
    vm = db.query(VM).filter(VM.vmid == vmid).first()
    
    if not vm:
        raise HTTPException(status_code=404, detail="VM not found")
    
    try:
        proxmox_service = get_proxmox_service()
        upid = None
        
        # Execute action
        if action_request.action == 'start':
            upid = proxmox_service.start_vm(vm.node, vm.vmid, vm.type)
        elif action_request.action == 'stop':
            upid = proxmox_service.stop_vm(vm.node, vm.vmid, vm.type)
        elif action_request.action == 'restart':
            upid = proxmox_service.reboot_vm(vm.node, vm.vmid, vm.type)
        elif action_request.action == 'shutdown':
            upid = proxmox_service.shutdown_vm(vm.node, vm.vmid, vm.type)
        elif action_request.action == 'reset':
            if vm.type != 'qemu':
                raise HTTPException(status_code=400, detail="Reset is only available for QEMU VMs")
            upid = proxmox_service.reset_vm(vm.node, vm.vmid, vm.type)
        
        # Log execution (manual action, no schedule_id)
        log = ExecutionLog(
            schedule_id=None,
            vm_id=vm.id,
            vmid=vm.vmid,
            vm_name=vm.name,
            action=action_request.action,
            status='success',
            executed_at=datetime.now(),
            upid=upid
        )
        db.add(log)
        db.commit()
        
        return {
            "success": True,
            "message": f"Action '{action_request.action}' executed successfully on VM {vmid}",
            "upid": upid,
            "vmid": vmid
        }
    
    except Exception as e:
        # Log failure
        log = ExecutionLog(
            schedule_id=None,
            vm_id=vm.id,
            vmid=vm.vmid,
            vm_name=vm.name,
            action=action_request.action,
            status='failed',
            executed_at=datetime.now(),
            error_message=str(e)
        )
        db.add(log)
        db.commit()
        
        raise HTTPException(status_code=500, detail=f"Action failed: {str(e)}")


@router.post("/group/{group_id}")
def execute_group_action(
    group_id: int,
    action_request: ActionRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Execute immediate action on all VMs in a group
    
    Args:
        group_id: Group ID
        action_request: Action to perform
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Action results
    """
    # Get group
    group = db.query(Group).filter(Group.id == group_id).first()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Get all members
    members = db.query(GroupMember).filter(GroupMember.group_id == group_id).all()
    
    if not members:
        raise HTTPException(status_code=400, detail="Group has no members")
    
    proxmox_service = get_proxmox_service()
    results = []
    errors = []
    
    # Execute action on each VM
    for member in members:
        vm = member.vm
        if not vm:
            continue
        
        try:
            upid = None
            
            if action_request.action == 'start':
                upid = proxmox_service.start_vm(vm.node, vm.vmid, vm.type)
            elif action_request.action == 'stop':
                upid = proxmox_service.stop_vm(vm.node, vm.vmid, vm.type)
            elif action_request.action == 'restart':
                upid = proxmox_service.reboot_vm(vm.node, vm.vmid, vm.type)
            elif action_request.action == 'shutdown':
                upid = proxmox_service.shutdown_vm(vm.node, vm.vmid, vm.type)
            elif action_request.action == 'reset':
                if vm.type == 'qemu':
                    upid = proxmox_service.reset_vm(vm.node, vm.vmid, vm.type)
                else:
                    raise ValueError("Reset only available for QEMU VMs")
            
            # Log success
            log = ExecutionLog(
                schedule_id=None,
                vm_id=vm.id,
                vmid=vm.vmid,
                vm_name=vm.name,
                action=action_request.action,
                status='success',
                executed_at=datetime.now(),
                upid=upid
            )
            db.add(log)
            
            results.append({
                "vmid": vm.vmid,
                "name": vm.name,
                "success": True,
                "upid": upid
            })
        
        except Exception as e:
            # Log failure
            log = ExecutionLog(
                schedule_id=None,
                vm_id=vm.id,
                vmid=vm.vmid,
                vm_name=vm.name,
                action=action_request.action,
                status='failed',
                executed_at=datetime.now(),
                error_message=str(e)
            )
            db.add(log)
            
            errors.append({
                "vmid": vm.vmid,
                "name": vm.name,
                "error": str(e)
            })
    
    db.commit()
    
    return {
        "message": f"Group action '{action_request.action}' completed",
        "group_name": group.name,
        "total": len(members),
        "successful": len(results),
        "failed": len(errors),
        "results": results,
        "errors": errors
    }
