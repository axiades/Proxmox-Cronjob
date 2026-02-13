"""
SQLAlchemy ORM Models
"""
from sqlalchemy import Column, Integer, String, Boolean, Text, BigInteger, ForeignKey, TIMESTAMP, Time
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    """User model for authentication"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(TIMESTAMP, server_default=func.now())
    last_login = Column(TIMESTAMP, nullable=True)


class ProxmoxCredential(Base):
    """Proxmox cluster credentials"""
    __tablename__ = "proxmox_credentials"
    
    id = Column(Integer, primary_key=True, index=True)
    cluster_name = Column(String(100), nullable=False)
    host = Column(String(255), nullable=False)
    port = Column(Integer, default=8006)
    user_name = Column(String(100), nullable=False)
    token_name = Column(String(100), nullable=False)
    token_value = Column(Text, nullable=False)  # Encrypted
    verify_ssl = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())


class VM(Base):
    """VM/Container cache"""
    __tablename__ = "vms"
    
    id = Column(Integer, primary_key=True, index=True)
    vmid = Column(Integer, unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    type = Column(String(10), nullable=False)  # 'qemu' or 'lxc'
    node = Column(String(100), nullable=False, index=True)
    status = Column(String(20), index=True)
    maxmem = Column(BigInteger, nullable=True)
    maxdisk = Column(BigInteger, nullable=True)
    uptime = Column(Integer, nullable=True)
    last_synced = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    group_memberships = relationship("GroupMember", back_populates="vm", cascade="all, delete-orphan")
    execution_logs = relationship("ExecutionLog", back_populates="vm")


class Group(Base):
    """VM Groups"""
    __tablename__ = "groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    members = relationship("GroupMember", back_populates="group", cascade="all, delete-orphan")


class GroupMember(Base):
    """Group membership many-to-many"""
    __tablename__ = "group_members"
    
    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False, index=True)
    vm_id = Column(Integer, ForeignKey("vms.id", ondelete="CASCADE"), nullable=False, index=True)
    added_at = Column(TIMESTAMP, server_default=func.now())
    
    # Relationships
    group = relationship("Group", back_populates="members")
    vm = relationship("VM", back_populates="group_memberships")


class Schedule(Base):
    """Scheduled tasks"""
    __tablename__ = "schedules"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    target_type = Column(String(10), nullable=False)  # 'vm' or 'group'
    target_id = Column(Integer, nullable=False, index=True)
    action = Column(String(20), nullable=False)  # 'start', 'stop', 'restart', 'shutdown', 'reset'
    cron_expression = Column(String(100), nullable=False)
    enabled = Column(Boolean, default=True, index=True)
    created_at = Column(TIMESTAMP, server_default=func.now())
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())
    last_run = Column(TIMESTAMP, nullable=True)
    next_run = Column(TIMESTAMP, nullable=True)
    
    # Relationships
    execution_logs = relationship("ExecutionLog", back_populates="schedule")


class BlackoutWindow(Base):
    """Maintenance/blackout windows"""
    __tablename__ = "blackout_windows"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    start_time = Column(Time, nullable=False)
    end_time = Column(Time, nullable=False)
    days_of_week = Column(String(50), nullable=True)  # JSON array string
    enabled = Column(Boolean, default=True, index=True)
    created_at = Column(TIMESTAMP, server_default=func.now())


class ExecutionLog(Base):
    """Execution history logs"""
    __tablename__ = "execution_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    schedule_id = Column(Integer, ForeignKey("schedules.id", ondelete="SET NULL"), nullable=True, index=True)
    vm_id = Column(Integer, ForeignKey("vms.id", ondelete="SET NULL"), nullable=True, index=True)
    vmid = Column(Integer, nullable=True)  # Store even if VM deleted
    vm_name = Column(String(255), nullable=True)
    action = Column(String(20), nullable=False)
    status = Column(String(20), nullable=False, index=True)  # 'success', 'failed', 'skipped'
    executed_at = Column(TIMESTAMP, server_default=func.now(), index=True)
    duration_seconds = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    upid = Column(String(255), nullable=True)
    skipped_reason = Column(String(100), nullable=True)
    
    # Relationships
    schedule = relationship("Schedule", back_populates="execution_logs")
    vm = relationship("VM", back_populates="execution_logs")
