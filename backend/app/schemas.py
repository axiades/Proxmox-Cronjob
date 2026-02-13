"""
Pydantic schemas for API request/response validation
"""
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime, time
from croniter import croniter


# Authentication Schemas
class Token(BaseModel):
    access_token: str
    token_type: str


class TokenData(BaseModel):
    username: Optional[str] = None


class UserLogin(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    created_at: datetime
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# VM Schemas
class VMBase(BaseModel):
    vmid: int
    name: str
    type: str  # 'qemu' or 'lxc'
    node: str
    status: Optional[str] = None


class VMCreate(VMBase):
    pass


class VMResponse(VMBase):
    id: int
    maxmem: Optional[int] = None
    maxdisk: Optional[int] = None
    uptime: Optional[int] = None
    last_synced: datetime
    
    class Config:
        from_attributes = True


class VMStatusResponse(BaseModel):
    vmid: int
    status: str
    name: str
    uptime: Optional[int] = None
    cpu: Optional[float] = None
    mem: Optional[int] = None
    maxmem: Optional[int] = None


# Group Schemas
class GroupBase(BaseModel):
    name: str
    description: Optional[str] = None


class GroupCreate(GroupBase):
    pass


class GroupUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None


class GroupResponse(GroupBase):
    id: int
    created_at: datetime
    member_count: Optional[int] = 0
    
    class Config:
        from_attributes = True


class GroupMemberAdd(BaseModel):
    vm_id: int


class GroupWithMembers(GroupResponse):
    members: List[VMResponse] = []


# Schedule Schemas
class ScheduleBase(BaseModel):
    name: str
    target_type: str  # 'vm' or 'group'
    target_id: int
    action: str  # 'start', 'stop', 'restart', 'shutdown', 'reset'
    cron_expression: str
    enabled: bool = True
    
    @validator('target_type')
    def validate_target_type(cls, v):
        if v not in ['vm', 'group']:
            raise ValueError('target_type must be "vm" or "group"')
        return v
    
    @validator('action')
    def validate_action(cls, v):
        if v not in ['start', 'stop', 'restart', 'shutdown', 'reset']:
            raise ValueError('action must be one of: start, stop, restart, shutdown, reset')
        return v
    
    @validator('cron_expression')
    def validate_cron(cls, v):
        try:
            croniter(v)
        except Exception as e:
            raise ValueError(f'Invalid cron expression: {str(e)}')
        return v


class ScheduleCreate(ScheduleBase):
    pass


class ScheduleUpdate(BaseModel):
    name: Optional[str] = None
    target_type: Optional[str] = None
    target_id: Optional[int] = None
    action: Optional[str] = None
    cron_expression: Optional[str] = None
    enabled: Optional[bool] = None


class ScheduleResponse(ScheduleBase):
    id: int
    created_at: datetime
    updated_at: datetime
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# Blackout Window Schemas
class BlackoutWindowBase(BaseModel):
    name: str
    description: Optional[str] = None
    start_time: time
    end_time: time
    days_of_week: Optional[str] = None  # JSON array string: "[0,1,2,3,4,5,6]"
    enabled: bool = True


class BlackoutWindowCreate(BlackoutWindowBase):
    pass


class BlackoutWindowUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    days_of_week: Optional[str] = None
    enabled: Optional[bool] = None


class BlackoutWindowResponse(BlackoutWindowBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True


# Execution Log Schemas
class ExecutionLogResponse(BaseModel):
    id: int
    schedule_id: Optional[int] = None
    vm_id: Optional[int] = None
    vmid: Optional[int] = None
    vm_name: Optional[str] = None
    action: str
    status: str
    executed_at: datetime
    duration_seconds: Optional[int] = None
    error_message: Optional[str] = None
    upid: Optional[str] = None
    skipped_reason: Optional[str] = None
    
    class Config:
        from_attributes = True


# Action Schemas
class ActionRequest(BaseModel):
    action: str  # 'start', 'stop', 'restart', 'shutdown', 'reset'
    
    @validator('action')
    def validate_action(cls, v):
        if v not in ['start', 'stop', 'restart', 'shutdown', 'reset']:
            raise ValueError('action must be one of: start, stop, restart, shutdown, reset')
        return v


class ActionResponse(BaseModel):
    success: bool
    message: str
    upid: Optional[str] = None
    vmid: int


# Proxmox Credentials Schema
class ProxmoxCredentialCreate(BaseModel):
    cluster_name: str
    host: str
    port: int = 8006
    user_name: str
    token_name: str
    token_value: str
    verify_ssl: bool = False


class ProxmoxCredentialResponse(BaseModel):
    id: int
    cluster_name: str
    host: str
    port: int
    user_name: str
    token_name: str
    verify_ssl: bool
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


# Dashboard/Statistics Schemas
class DashboardStats(BaseModel):
    total_vms: int
    running_vms: int
    stopped_vms: int
    total_schedules: int
    active_schedules: int
    total_groups: int
    recent_executions: int
    failed_executions: int
