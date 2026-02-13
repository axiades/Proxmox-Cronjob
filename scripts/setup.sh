#!/bin/bash
# Setup script for Proxmox Cronjob Web Interface

set -e

echo "==================================="
echo "Proxmox Cronjob Web Interface Setup"
echo "==================================="

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "Please run as root"
    exit 1
fi

# Variables
INSTALL_DIR="/opt/proxmox-cronjob"
DB_NAME="proxmox_cronjob"
DB_USER="proxmox_cronjob"

echo ""
echo "1. Installing system dependencies..."
apt-get update
apt-get install -y python3 python3-pip python3-venv postgresql nginx git curl

echo ""
echo "2. Setting up PostgreSQL database..."
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD 'changeme';" || true
sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" || true
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;"

echo ""
echo "3. Creating installation directory..."
mkdir -p $INSTALL_DIR
mkdir -p /var/www/proxmox-cronjob
mkdir -p /var/log/proxmox-cronjob
chown -R www-data:www-data $INSTALL_DIR
chown -R www-data:www-data /var/www/proxmox-cronjob
chown -R www-data:www-data /var/log/proxmox-cronjob

echo ""
echo "4. Setting up Python virtual environment..."
cd $INSTALL_DIR/backend
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo ""
echo "5. Creating .env file..."
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Please edit $INSTALL_DIR/backend/.env with your configuration!"
fi

echo ""
echo "6. Loading database schema..."
sudo -u postgres psql -d $DB_NAME -f ../database/schema.sql

echo ""
echo "7. Installing systemd services..."
cp ../deployment/systemd/proxmox-cronjob-api.service /etc/systemd/system/
cp ../deployment/systemd/proxmox-cronjob-scheduler.service /etc/systemd/system/
systemctl daemon-reload

echo ""
echo "8. Installing Nginx configuration..."
cp ../deployment/nginx/proxmox-cronjob.conf /etc/nginx/sites-available/
ln -sf /etc/nginx/sites-available/proxmox-cronjob.conf /etc/nginx/sites-enabled/
nginx -t

echo ""
echo "9. Building frontend..."
cd ../frontend
curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
apt-get install -y nodejs
npm install
npm run build
cp -r dist/* /var/www/proxmox-cronjob/

echo ""
echo "10. Setting permissions..."
chown -R www-data:www-data $INSTALL_DIR
chown -R www-data:www-data /var/www/proxmox-cronjob

echo ""
echo "==================================="
echo "Setup Complete!"
echo "==================================="
echo ""
echo "Next steps:"
echo "1. Edit $INSTALL_DIR/backend/.env with your configuration"
echo "2. Generate SSL certificates (or use Let's Encrypt)"
echo "3. Update Nginx configuration with correct SSL paths"
echo "4. Start services:"
echo "   systemctl start proxmox-cronjob-api"
echo "   systemctl start proxmox-cronjob-scheduler"
echo "   systemctl enable proxmox-cronjob-api"
echo "   systemctl enable proxmox-cronjob-scheduler"
echo "   systemctl restart nginx"
echo ""
echo "5. Access the interface at https://your-server-ip"
echo "   Default credentials: admin / admin"
echo "   !!! CHANGE THE PASSWORD IMMEDIATELY !!!"
echo ""
