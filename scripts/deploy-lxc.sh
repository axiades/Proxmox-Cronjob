#!/usr/bin/env bash

# Proxmox Cronjob Web Interface - LXC Deployment Script
# Based on Proxmox Helper Scripts pattern
# Run this script on your Proxmox host

# Copyright (c) 2026
# Author: Proxmox Cronjob Project
# License: MIT

set -euo pipefail
shopt -s inherit_errexit nullglob

# Colors
RD="\033[01;31m"
YW="\033[33m"
GN="\033[1;92m"
CL="\033[m"
BFR="\\r\\033[K"
HOLD="-"
CM="${GN}✓${CL}"
CROSS="${RD}✗${CL}"

# Functions
msg_info() { echo -ne " ${HOLD} ${YW}$1...${CL}"; }
msg_ok() { echo -e "${BFR} ${CM} ${GN}$1${CL}"; }
msg_error() { echo -e "${BFR} ${CROSS} ${RD}$1${CL}"; }

# Default values
CTID=""
CT_NAME="proxmox-cronjob"
CT_HOSTNAME="proxmox-cronjob"
CT_DISK="10"
CT_CORES="2"
CT_RAM="2048"
CT_SWAP="512"
CT_PASSWORD=""
CT_BRIDGE="vmbr0"
CT_NET="dhcp"
CT_GATEWAY=""
CT_VLAN=""
CT_STORAGE="local-lvm"
CT_TEMPLATE="debian-12-standard_12.2-1_amd64.tar.zst"
UNPRIVILEGED=1
START_ON_BOOT=1

# Proxmox Configuration
PROXMOX_HOST=""
PROXMOX_USER="root@pam"
PROXMOX_TOKEN_NAME=""
PROXMOX_TOKEN_VALUE=""

# Header
clear
cat << "EOF"
    ____                                          ______                 _       __  
   / __ \_________ __  ______ ___  ____  _  __  / ____/________  ____  (_)___  / /_ 
  / /_/ / ___/ __ \/ |/_/ __ `__ \/ __ \| |/_/ / /   / ___/ __ \/ __ \/ / __ \/ __ \
 / ____/ /  / /_/ />  </ / / / / / /_/ />  <  / /___/ /  / /_/ / / / / / /_/ / /_/ /
/_/   /_/   \____/_/|_/_/ /_/ /_/\____/_/|_|  \____/_/   \____/_/ /_/ /\____/_.___/ 
                                                                    /___/             
           ╦  ═╗ ╦╔═╗  ╔╦╗╔═╗╔═╗╦  ╔═╗╦ ╦╔╦╗╔═╗╔╗╔╔╦╗
           ║  ╔╩╦╝║    ║║║╣ ╠═╝║  ║ ║╚╦╝║║║║╣ ║║║ ║ 
           ╩═╝╩ ╚═╩═╝  ╩═╩╚═╝╩  ╩═╝╚═╝ ╩ ╩ ╩╚═╝╝╚╝ ╩ 
                                                       
EOF
echo -e "\nAutomated Deployment Script for Proxmox VE\n"

# Check if running on Proxmox
if ! command -v pveversion &> /dev/null; then
    msg_error "This script must be run on a Proxmox VE host!"
    exit 1
fi

msg_ok "Running on Proxmox VE $(pveversion | cut -d'/' -f2)"

# Interactive Configuration
echo -e "\n${YW}Container Configuration${CL}"
echo "────────────────────────────────────────"

# Container ID
while true; do
    read -rp "Enter Container ID (next available: $(pvesh get /cluster/nextid)): " CTID
    CTID=${CTID:-$(pvesh get /cluster/nextid)}
    
    if pct status "$CTID" &>/dev/null; then
        msg_error "Container ID $CTID already exists!"
    else
        msg_ok "Using Container ID: $CTID"
        break
    fi
done

# Container Password
while true; do
    read -rsp "Enter root password for container: " CT_PASSWORD
    echo
    read -rsp "Confirm password: " CT_PASSWORD_CONFIRM
    echo
    
    if [ "$CT_PASSWORD" = "$CT_PASSWORD_CONFIRM" ]; then
        msg_ok "Password set"
        break
    else
        msg_error "Passwords do not match!"
    fi
done

# Network Configuration
echo -e "\n${YW}Network Configuration${CL}"
read -rp "Use DHCP? (Y/n): " USE_DHCP
USE_DHCP=${USE_DHCP:-Y}

if [[ ! "$USE_DHCP" =~ ^[Yy]$ ]]; then
    read -rp "Enter IP Address (CIDR): " CT_NET
    read -rp "Enter Gateway: " CT_GATEWAY
fi

# Storage
echo -e "\n${YW}Storage Configuration${CL}"
echo "Available storage:"
pvesm status | grep -v 'NAME' | awk '{print "  - " $1 " (" $2 ")"}'
read -rp "Enter storage name [$CT_STORAGE]: " INPUT_STORAGE
CT_STORAGE=${INPUT_STORAGE:-$CT_STORAGE}

# Resources
echo -e "\n${YW}Resource Allocation${CL}"
read -rp "CPU Cores [$CT_CORES]: " INPUT_CORES
CT_CORES=${INPUT_CORES:-$CT_CORES}

read -rp "RAM (MB) [$CT_RAM]: " INPUT_RAM
CT_RAM=${INPUT_RAM:-$CT_RAM}

read -rp "Disk Size (GB) [$CT_DISK]: " INPUT_DISK
CT_DISK=${INPUT_DISK:-$CT_DISK}

# Proxmox API Configuration
echo -e "\n${YW}Proxmox API Configuration${CL}"
echo "────────────────────────────────────────"
read -rp "Proxmox Host (IP/Hostname) [$(hostname -I | awk '{print $1}')]: " PROXMOX_HOST
PROXMOX_HOST=${PROXMOX_HOST:-$(hostname -I | awk '{print $1}')}

read -rp "Create API Token now? (Y/n): " CREATE_TOKEN
CREATE_TOKEN=${CREATE_TOKEN:-Y}

if [[ "$CREATE_TOKEN" =~ ^[Yy]$ ]]; then
    PROXMOX_TOKEN_NAME="cronjob"
    
    msg_info "Creating API token"
    TOKEN_OUTPUT=$(pveum user token add root@pam "$PROXMOX_TOKEN_NAME" --privsep=0 2>&1 || true)
    
    if echo "$TOKEN_OUTPUT" | grep -q "full-tokenid"; then
        PROXMOX_TOKEN_VALUE=$(echo "$TOKEN_OUTPUT" | grep "value" | awk '{print $2}')
        msg_ok "API Token created: $PROXMOX_TOKEN_NAME"
    else
        msg_error "Failed to create token automatically"
        read -rp "Enter existing API Token Name: " PROXMOX_TOKEN_NAME
        read -rp "Enter API Token UUID: " PROXMOX_TOKEN_VALUE
    fi
else
    read -rp "Enter API Token Name: " PROXMOX_TOKEN_NAME
    read -rp "Enter API Token UUID: " PROXMOX_TOKEN_VALUE
fi

# Summary
echo -e "\n${YW}Deployment Summary${CL}"
echo "────────────────────────────────────────"
echo "Container ID:     $CTID"
echo "Container Name:   $CT_NAME"
echo "Hostname:         $CT_HOSTNAME"
echo "CPU Cores:        $CT_CORES"
echo "RAM:              ${CT_RAM}MB"
echo "Disk:             ${CT_DISK}GB"
echo "Storage:          $CT_STORAGE"
echo "Network:          $CT_NET"
echo "Proxmox Host:     $PROXMOX_HOST"
echo "────────────────────────────────────────"

read -rp "Proceed with deployment? (Y/n): " CONFIRM
CONFIRM=${CONFIRM:-Y}

if [[ ! "$CONFIRM" =~ ^[Yy]$ ]]; then
    msg_error "Deployment cancelled"
    exit 0
fi

# Start Deployment
echo -e "\n${GN}Starting Deployment...${CL}\n"

# Download template if not exists
msg_info "Checking container template"
TEMPLATE_PATH="/var/lib/vz/template/cache/$CT_TEMPLATE"

if [ ! -f "$TEMPLATE_PATH" ]; then
    msg_info "Downloading Debian 12 template"
    pveam update
    pveam download local "$CT_TEMPLATE"
    msg_ok "Template downloaded"
else
    msg_ok "Template exists"
fi

# Build network configuration
if [[ "$CT_NET" == "dhcp" ]]; then
    NET_CONFIG="name=eth0,bridge=$CT_BRIDGE,ip=dhcp"
else
    NET_CONFIG="name=eth0,bridge=$CT_BRIDGE,ip=$CT_NET,gw=$CT_GATEWAY"
fi

# Create Container
msg_info "Creating LXC container"
pct create "$CTID" "$TEMPLATE_PATH" \
    --hostname "$CT_HOSTNAME" \
    --cores "$CT_CORES" \
    --memory "$CT_RAM" \
    --swap "$CT_SWAP" \
    --rootfs "$CT_STORAGE:$CT_DISK" \
    --net0 "$NET_CONFIG" \
    --unprivileged "$UNPRIVILEGED" \
    --onboot "$START_ON_BOOT" \
    --features nesting=1 \
    --password "$CT_PASSWORD" \
    --start 1

msg_ok "Container created (ID: $CTID)"

# Wait for container to start
msg_info "Waiting for container to start"
sleep 10

# Check if container is running
if pct status "$CTID" | grep -q "running"; then
    msg_ok "Container is running"
else
    msg_error "Container failed to start"
    exit 1
fi

# Setup function to run inside container
msg_info "Installing system dependencies"
pct exec "$CTID" -- bash -c "apt-get update && apt-get upgrade -y"
pct exec "$CTID" -- bash -c "apt-get install -y git curl wget sudo ca-certificates gnupg lsb-release"
msg_ok "System updated"

# Install Python
msg_info "Installing Python 3.11"
pct exec "$CTID" -- bash -c "apt-get install -y python3 python3-pip python3-venv python3-dev build-essential"
msg_ok "Python installed"

# Install PostgreSQL
msg_info "Installing PostgreSQL"
pct exec "$CTID" -- bash -c "apt-get install -y postgresql postgresql-contrib"
pct exec "$CTID" -- bash -c "systemctl enable postgresql"
msg_ok "PostgreSQL installed"

# Install Nginx
msg_info "Installing Nginx"
pct exec "$CTID" -- bash -c "apt-get install -y nginx"
pct exec "$CTID" -- bash -c "systemctl enable nginx"
msg_ok "Nginx installed"

# Install Node.js
msg_info "Installing Node.js 20"
pct exec "$CTID" -- bash -c "curl -fsSL https://deb.nodesource.com/setup_20.x | bash -"
pct exec "$CTID" -- bash -c "apt-get install -y nodejs"
msg_ok "Node.js installed"

# Clone repository
msg_info "Cloning repository"
pct exec "$CTID" -- bash -c "cd /opt && git clone https://github.com/YOUR-USERNAME/Proxmox-Cronjob.git proxmox-cronjob || true"

# If git clone fails (no remote repo), copy files from host
if ! pct exec "$CTID" -- bash -c "[ -d /opt/proxmox-cronjob ]"; then
    msg_info "Copying files from host"
    
    # Create directory
    pct exec "$CTID" -- bash -c "mkdir -p /opt/proxmox-cronjob"
    
    # Copy files (adjust path as needed)
    if [ -d "/root/Proxmox-Cronjob" ]; then
        pct push "$CTID" /root/Proxmox-Cronjob /opt/proxmox-cronjob --recursive
    else
        msg_error "Source directory not found. Please manually copy files."
    fi
fi
msg_ok "Application files ready"

# Setup PostgreSQL
msg_info "Configuring PostgreSQL"
pct exec "$CTID" -- bash -c "sudo -u postgres psql -c \"CREATE USER proxmox_cronjob WITH PASSWORD 'ProxmoxCron2026!';\" || true"
pct exec "$CTID" -- bash -c "sudo -u postgres psql -c \"CREATE DATABASE proxmox_cronjob OWNER proxmox_cronjob;\" || true"
pct exec "$CTID" -- bash -c "sudo -u postgres psql -c \"GRANT ALL PRIVILEGES ON DATABASE proxmox_cronjob TO proxmox_cronjob;\""
msg_ok "PostgreSQL configured"

# Load database schema
msg_info "Loading database schema"
pct exec "$CTID" -- bash -c "sudo -u postgres psql proxmox_cronjob < /opt/proxmox-cronjob/database/schema.sql"
msg_ok "Database schema loaded"

# Setup Python environment
msg_info "Setting up Python virtual environment"
pct exec "$CTID" -- bash -c "cd /opt/proxmox-cronjob/backend && python3 -m venv venv"
pct exec "$CTID" -- bash -c "cd /opt/proxmox-cronjob/backend && source venv/bin/activate && pip install --upgrade pip && pip install -r requirements.txt"
msg_ok "Python environment ready"

# Create .env file
msg_info "Creating configuration file"
pct exec "$CTID" -- bash -c "cat > /opt/proxmox-cronjob/backend/.env << 'ENVEOF'
DATABASE_URL=postgresql://proxmox_cronjob:ProxmoxCron2026!@localhost:5432/proxmox_cronjob

SECRET_KEY=$(openssl rand -hex 32)
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=1440

ENCRYPTION_KEY=$(python3 -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')

PROXMOX_HOST=$PROXMOX_HOST
PROXMOX_PORT=8006
PROXMOX_USER=$PROXMOX_USER
PROXMOX_TOKEN_NAME=$PROXMOX_TOKEN_NAME
PROXMOX_TOKEN_VALUE=$PROXMOX_TOKEN_VALUE
PROXMOX_VERIFY_SSL=false

CORS_ORIGINS=http://localhost:5173
VM_SYNC_INTERVAL_MINUTES=5
LOG_LEVEL=INFO
ENVEOF"
msg_ok "Configuration created"

# Build frontend
msg_info "Building frontend"
pct exec "$CTID" -- bash -c "cd /opt/proxmox-cronjob/frontend && npm install"
pct exec "$CTID" -- bash -c "cd /opt/proxmox-cronjob/frontend && npm run build"
msg_ok "Frontend built"

# Setup web directory
msg_info "Setting up web directory"
pct exec "$CTID" -- bash -c "mkdir -p /var/www/proxmox-cronjob"
pct exec "$CTID" -- bash -c "cp -r /opt/proxmox-cronjob/frontend/dist/* /var/www/proxmox-cronjob/"
msg_ok "Web files deployed"

# Generate self-signed certificate
msg_info "Generating SSL certificate"
pct exec "$CTID" -- bash -c "openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout /etc/ssl/private/proxmox-cronjob.key \
    -out /etc/ssl/certs/proxmox-cronjob.crt \
    -subj '/C=DE/ST=State/L=City/O=Organization/CN=$CT_HOSTNAME'"
msg_ok "SSL certificate generated"

# Install systemd services
msg_info "Installing systemd services"
pct exec "$CTID" -- bash -c "cp /opt/proxmox-cronjob/deployment/systemd/proxmox-cronjob-api.service /etc/systemd/system/"
pct exec "$CTID" -- bash -c "cp /opt/proxmox-cronjob/deployment/systemd/proxmox-cronjob-scheduler.service /etc/systemd/system/"
pct exec "$CTID" -- bash -c "systemctl daemon-reload"
msg_ok "Systemd services installed"

# Install Nginx configuration
msg_info "Configuring Nginx"
pct exec "$CTID" -- bash -c "cp /opt/proxmox-cronjob/deployment/nginx/proxmox-cronjob.conf /etc/nginx/sites-available/"
pct exec "$CTID" -- bash -c "ln -sf /etc/nginx/sites-available/proxmox-cronjob.conf /etc/nginx/sites-enabled/"
pct exec "$CTID" -- bash -c "rm -f /etc/nginx/sites-enabled/default"
pct exec "$CTID" -- bash -c "nginx -t"
msg_ok "Nginx configured"

# Set permissions
msg_info "Setting permissions"
pct exec "$CTID" -- bash -c "chown -R www-data:www-data /opt/proxmox-cronjob"
pct exec "$CTID" -- bash -c "chown -R www-data:www-data /var/www/proxmox-cronjob"
pct exec "$CTID" -- bash -c "mkdir -p /var/log/proxmox-cronjob"
pct exec "$CTID" -- bash -c "chown -R www-data:www-data /var/log/proxmox-cronjob"
msg_ok "Permissions set"

# Start services
msg_info "Starting services"
pct exec "$CTID" -- bash -c "systemctl start proxmox-cronjob-api"
pct exec "$CTID" -- bash -c "systemctl start proxmox-cronjob-scheduler"
pct exec "$CTID" -- bash -c "systemctl enable proxmox-cronjob-api"
pct exec "$CTID" -- bash -c "systemctl enable proxmox-cronjob-scheduler"
pct exec "$CTID" -- bash -c "systemctl restart nginx"
msg_ok "Services started"

# Get container IP
msg_info "Getting container IP address"
sleep 5
CONTAINER_IP=$(pct exec "$CTID" -- ip -4 addr show eth0 | grep -oP '(?<=inet\s)\d+(\.\d+){3}' || echo "Unable to determine")
msg_ok "Container IP: $CONTAINER_IP"

# Final message
echo -e "\n${GN}═══════════════════════════════════════════════════════${CL}"
echo -e "${GN}  Deployment Complete!${CL}"
echo -e "${GN}═══════════════════════════════════════════════════════${CL}\n"

echo -e "${YW}Container Information:${CL}"
echo "  ID:           $CTID"
echo "  Name:         $CT_HOSTNAME"
echo "  IP Address:   $CONTAINER_IP"
echo ""
echo -e "${YW}Access Information:${CL}"
echo "  Web Interface:  https://$CONTAINER_IP"
echo "  Username:       admin"
echo "  Password:       admin"
echo ""
echo -e "${RD}⚠ IMPORTANT: Change the default password immediately!${CL}"
echo ""
echo -e "${YW}Service Status:${CL}"
pct exec "$CTID" -- systemctl status proxmox-cronjob-api --no-pager | grep "Active:"
pct exec "$CTID" -- systemctl status proxmox-cronjob-scheduler --no-pager | grep "Active:"
echo ""
echo -e "${YW}Useful Commands:${CL}"
echo "  Enter container:    pct enter $CTID"
echo "  View API logs:      pct exec $CTID -- journalctl -u proxmox-cronjob-api -f"
echo "  View scheduler:     pct exec $CTID -- journalctl -u proxmox-cronjob-scheduler -f"
echo "  Restart services:   pct exec $CTID -- systemctl restart proxmox-cronjob-api proxmox-cronjob-scheduler"
echo ""
echo -e "${GN}Documentation: /opt/proxmox-cronjob/README.md${CL}"
echo -e "${GN}API Docs: https://$CONTAINER_IP/api/docs${CL}\n"

# Cleanup
msg_info "Cleaning up"
msg_ok "Done"

echo -e "\n${GN}Thank you for using Proxmox Cronjob Manager!${CL}\n"
