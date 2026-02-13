-- Proxmox Cronjob Web Interface - Database Schema
-- PostgreSQL 12+

-- Extension for UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users table for web interface authentication
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

-- Proxmox cluster credentials
CREATE TABLE proxmox_credentials (
    id SERIAL PRIMARY KEY,
    cluster_name VARCHAR(100) NOT NULL,
    host VARCHAR(255) NOT NULL,
    port INTEGER DEFAULT 8006,
    user_name VARCHAR(100) NOT NULL,
    token_name VARCHAR(100) NOT NULL,
    token_value TEXT NOT NULL, -- Encrypted
    verify_ssl BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- VM/Container cache from Proxmox cluster
CREATE TABLE vms (
    id SERIAL PRIMARY KEY,
    vmid INTEGER NOT NULL,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(10) NOT NULL, -- 'qemu' or 'lxc'
    node VARCHAR(100) NOT NULL,
    status VARCHAR(20), -- 'running', 'stopped', 'paused'
    maxmem BIGINT,
    maxdisk BIGINT,
    uptime INTEGER,
    last_synced TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(vmid)
);

CREATE INDEX idx_vms_type ON vms(type);
CREATE INDEX idx_vms_node ON vms(node);
CREATE INDEX idx_vms_status ON vms(status);

-- VM Groups for bulk operations
CREATE TABLE groups (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Group membership
CREATE TABLE group_members (
    id SERIAL PRIMARY KEY,
    group_id INTEGER NOT NULL REFERENCES groups(id) ON DELETE CASCADE,
    vm_id INTEGER NOT NULL REFERENCES vms(id) ON DELETE CASCADE,
    added_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(group_id, vm_id)
);

CREATE INDEX idx_group_members_group ON group_members(group_id);
CREATE INDEX idx_group_members_vm ON group_members(vm_id);

-- Scheduled tasks
CREATE TABLE schedules (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    target_type VARCHAR(10) NOT NULL, -- 'vm' or 'group'
    target_id INTEGER NOT NULL, -- vmid or group_id
    action VARCHAR(20) NOT NULL, -- 'start', 'stop', 'restart', 'shutdown', 'reset'
    cron_expression VARCHAR(100) NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_run TIMESTAMP,
    next_run TIMESTAMP
);

CREATE INDEX idx_schedules_enabled ON schedules(enabled);
CREATE INDEX idx_schedules_target ON schedules(target_type, target_id);

-- Blackout windows (maintenance windows where no actions should run)
CREATE TABLE blackout_windows (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    days_of_week VARCHAR(50), -- JSON array: [0,1,2,3,4,5,6] where 0=Monday
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_blackout_enabled ON blackout_windows(enabled);

-- Execution logs
CREATE TABLE execution_logs (
    id SERIAL PRIMARY KEY,
    schedule_id INTEGER REFERENCES schedules(id) ON DELETE SET NULL,
    vm_id INTEGER REFERENCES vms(id) ON DELETE SET NULL,
    vmid INTEGER, -- Store vmid even if VM is deleted
    vm_name VARCHAR(255),
    action VARCHAR(20) NOT NULL,
    status VARCHAR(20) NOT NULL, -- 'success', 'failed', 'skipped'
    executed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    duration_seconds INTEGER,
    error_message TEXT,
    upid VARCHAR(255), -- Proxmox task UPID
    skipped_reason VARCHAR(100) -- 'blackout', 'vm_not_found', etc.
);

CREATE INDEX idx_logs_schedule ON execution_logs(schedule_id);
CREATE INDEX idx_logs_vm ON execution_logs(vm_id);
CREATE INDEX idx_logs_status ON execution_logs(status);
CREATE INDEX idx_logs_executed ON execution_logs(executed_at DESC);

-- Function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_proxmox_credentials_updated_at BEFORE UPDATE ON proxmox_credentials
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_schedules_updated_at BEFORE UPDATE ON schedules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Insert default admin user (password: 'admin' - CHANGE THIS!)
-- Password hash for 'admin' using bcrypt
INSERT INTO users (username, password_hash) VALUES 
    ('admin', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5NU7qLdAiJrEy');

-- Example data comments
-- To create a Proxmox credential:
-- INSERT INTO proxmox_credentials (cluster_name, host, user_name, token_name, token_value) 
-- VALUES ('production', '192.168.1.100', 'root@pam', 'cronjob', 'your-encrypted-token-here');
