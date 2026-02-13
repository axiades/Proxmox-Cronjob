"""
Groups Management API endpoints
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.schemas import GroupCreate, GroupUpdate, GroupResponse, GroupWithMembers, GroupMemberAdd
from app.models import Group, GroupMember, VM, User
from app.dependencies import get_current_user

router = APIRouter(prefix="/groups", tags=["Groups"])


@router.get("", response_model=List[GroupResponse])
def get_groups(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get list of all groups
    
    Args:
        db: Database session
        current_user: Authenticated user
        
    Returns:
        List of groups
    """
    groups = db.query(Group).all()
    
    # Add member count to each group
    result = []
    for group in groups:
        group_dict = GroupResponse.from_orm(group).dict()
        group_dict['member_count'] = len(group.members)
        result.append(group_dict)
    
    return result


@router.get("/{group_id}", response_model=GroupWithMembers)
def get_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get specific group with members
    
    Args:
        group_id: Group ID
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Group details with members
    """
    group = db.query(Group).filter(Group.id == group_id).first()
    
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Get members
    members = [member.vm for member in group.members if member.vm]
    
    return {
        **GroupResponse.from_orm(group).dict(),
        "members": members
    }


@router.post("", response_model=GroupResponse, status_code=201)
def create_group(
    group: GroupCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create new group
    
    Args:
        group: Group data
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Created group
    """
    # Check if group name already exists
    existing = db.query(Group).filter(Group.name == group.name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Group name already exists")
    
    db_group = Group(
        name=group.name,
        description=group.description
    )
    db.add(db_group)
    db.commit()
    db.refresh(db_group)
    
    return db_group


@router.put("/{group_id}", response_model=GroupResponse)
def update_group(
    group_id: int,
    group: GroupUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update group
    
    Args:
        group_id: Group ID
        group: Updated group data
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Updated group
    """
    db_group = db.query(Group).filter(Group.id == group_id).first()
    
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Update fields
    if group.name is not None:
        # Check name uniqueness
        existing = db.query(Group).filter(
            Group.name == group.name,
            Group.id != group_id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="Group name already exists")
        db_group.name = group.name
    
    if group.description is not None:
        db_group.description = group.description
    
    db.commit()
    db.refresh(db_group)
    
    return db_group


@router.delete("/{group_id}")
def delete_group(
    group_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete group
    
    Args:
        group_id: Group ID
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Success message
    """
    db_group = db.query(Group).filter(Group.id == group_id).first()
    
    if not db_group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    db.delete(db_group)
    db.commit()
    
    return {"message": "Group deleted successfully"}


@router.post("/{group_id}/members")
def add_member(
    group_id: int,
    member: GroupMemberAdd,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Add VM to group
    
    Args:
        group_id: Group ID
        member: Member data (vm_id)
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Success message
    """
    # Check group exists
    group = db.query(Group).filter(Group.id == group_id).first()
    if not group:
        raise HTTPException(status_code=404, detail="Group not found")
    
    # Check VM exists
    vm = db.query(VM).filter(VM.id == member.vm_id).first()
    if not vm:
        raise HTTPException(status_code=404, detail="VM not found")
    
    # Check if already a member
    existing = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.vm_id == member.vm_id
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="VM is already a member of this group")
    
    # Add member
    group_member = GroupMember(group_id=group_id, vm_id=member.vm_id)
    db.add(group_member)
    db.commit()
    
    return {"message": "Member added successfully"}


@router.delete("/{group_id}/members/{vm_id}")
def remove_member(
    group_id: int,
    vm_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Remove VM from group
    
    Args:
        group_id: Group ID
        vm_id: VM ID
        db: Database session
        current_user: Authenticated user
        
    Returns:
        Success message
    """
    member = db.query(GroupMember).filter(
        GroupMember.group_id == group_id,
        GroupMember.vm_id == vm_id
    ).first()
    
    if not member:
        raise HTTPException(status_code=404, detail="Member not found in group")
    
    db.delete(member)
    db.commit()
    
    return {"message": "Member removed successfully"}
