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
apt-get install -y python3 python3-pip python3-venv postgresql nginx git curl \
    build-essential python3-dev libpq-dev pkg-config gcc

ARCH=$(dpkg --print-architecture)
if [ "$ARCH" = "armhf" ] || [ "$ARCH" = "arm64" ]; then
        echo "Installing Rust toolchain for ARM builds..."
        if ! command -v cargo >/dev/null 2>&1; then
                curl https://sh.rustup.rs -sSf | sh -s -- -y
                source /root/.cargo/env
        fi
fi

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
echo "5.0 Generating secrets and database URL..."
DB_PASS="changeme"
DATABASE_URL="postgresql+psycopg://$DB_USER:$DB_PASS@localhost:5432/$DB_NAME"
SECRET_KEY=$(openssl rand -hex 32)
ENCRYPTION_KEY=$(python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")

sed -i "s|^DATABASE_URL=.*|DATABASE_URL=$DATABASE_URL|" .env
sed -i "s|^SECRET_KEY=.*|SECRET_KEY=$SECRET_KEY|" .env
sed -i "s|^ENCRYPTION_KEY=.*|ENCRYPTION_KEY=$ENCRYPTION_KEY|" .env

echo ""
echo "5.1 Writing credentials file..."
cat > /root/proxmox-cronjob-credentials.txt << EOF
Proxmox Cronjob Credentials
===========================
Database:
    User: $DB_USER
    Password: $DB_PASS
    Database: $DB_NAME
    Host: localhost
    Port: 5432
    URL: $DATABASE_URL

Security:
    SECRET_KEY: $SECRET_KEY
    ENCRYPTION_KEY: $ENCRYPTION_KEY

Config:
    .env path: $INSTALL_DIR/backend/.env

Note:
    Change the database password and update DATABASE_URL in .env.
EOF
chmod 600 /root/proxmox-cronjob-credentials.txt

echo ""
echo "6. Loading database schema..."
sudo -u postgres psql -d $DB_NAME -f ../database/schema.sql

echo ""
echo "7. Installing systemd services..."
cp ../deployment/systemd/proxmox-cronjob-api.service /etc/systemd/system/
cp ../deployment/systemd/proxmox-cronjob-scheduler.service /etc/systemd/system/
systemctl daemon-reload

echo ""
echo "8. Installing Nginx configuration (interactive)..."

read -r -p "Domain (FQDN, z.B. cronjob.example.com) oder IP: " NGINX_DOMAIN
if [ -z "$NGINX_DOMAIN" ]; then
    NGINX_DOMAIN="_"
fi

echo "Choose SSL/ACME mode:"
echo "  1) HTTP only (no TLS)"
echo "  2) HTTPS with existing certificate paths"
echo "  3) Let's Encrypt via certbot (webroot)"
echo "  4) ACME via acme.sh (webroot)"
read -r -p "Select [1-4]: " SSL_MODE

WEBROOT="/var/www/proxmox-cronjob"
CERT_PATH=""
KEY_PATH=""

create_http_config() {
cat > /etc/nginx/sites-available/proxmox-cronjob.conf << EOF
server {
    listen 80;
    listen [::]:80;
    server_name $NGINX_DOMAIN;

    root $WEBROOT;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location / {
        try_files \$uri \$uri/ /index.html;
    }
}
EOF
}

create_https_config() {
cat > /etc/nginx/sites-available/proxmox-cronjob.conf << EOF
server {
    listen 80;
    listen [::]:80;
    server_name $NGINX_DOMAIN;
    return 301 https://\$host\$request_uri;
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    http2 on;
    server_name $NGINX_DOMAIN;

    ssl_certificate $CERT_PATH;
    ssl_certificate_key $KEY_PATH;

    root $WEBROOT;
    index index.html;

    location /api/ {
        proxy_pass http://127.0.0.1:8000/;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    location / {
        try_files \$uri \$uri/ /index.html;
    }
}
EOF
}

case "$SSL_MODE" in
    1)
        create_http_config
        ;;
    2)
        read -r -p "Path to certificate (fullchain.pem or .crt): " CERT_PATH
        read -r -p "Path to private key (.key): " KEY_PATH
        create_https_config
        ;;
    3)
        read -r -p "Email for Let's Encrypt: " LE_EMAIL
        create_http_config
        ln -sf /etc/nginx/sites-available/proxmox-cronjob.conf /etc/nginx/sites-enabled/
        nginx -t && systemctl reload nginx || true
        apt-get install -y certbot python3-certbot-nginx
        if certbot certonly --webroot -w "$WEBROOT" -d "$NGINX_DOMAIN" \
            -m "$LE_EMAIL" --agree-tos --non-interactive; then
            CERT_PATH="/etc/letsencrypt/live/$NGINX_DOMAIN/fullchain.pem"
            KEY_PATH="/etc/letsencrypt/live/$NGINX_DOMAIN/privkey.pem"
            create_https_config
        else
            echo "Let's Encrypt failed, falling back to HTTP only."
            create_http_config
        fi
        ;;
    4)
        create_http_config
        ln -sf /etc/nginx/sites-available/proxmox-cronjob.conf /etc/nginx/sites-enabled/
        nginx -t && systemctl reload nginx || true
        if [ ! -d "/root/.acme.sh" ]; then
            curl https://get.acme.sh | sh
        fi
        if /root/.acme.sh/acme.sh --issue --webroot "$WEBROOT" -d "$NGINX_DOMAIN"; then
            CERT_PATH="/root/.acme.sh/$NGINX_DOMAIN/fullchain.cer"
            KEY_PATH="/root/.acme.sh/$NGINX_DOMAIN/$NGINX_DOMAIN.key"
            create_https_config
        else
            echo "acme.sh failed, falling back to HTTP only."
            create_http_config
        fi
        ;;
    *)
        echo "Invalid option, defaulting to HTTP only."
        create_http_config
        ;;
esac

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
echo "2. Start services:"
echo "   systemctl start proxmox-cronjob-api"
echo "   systemctl start proxmox-cronjob-scheduler"
echo "   systemctl enable proxmox-cronjob-api"
echo "   systemctl enable proxmox-cronjob-scheduler"
echo "   systemctl restart nginx"
echo ""
echo "3. Access the interface at https://your-server-ip or http://your-server-ip"
echo "   Default credentials: admin / admin"
echo "   !!! CHANGE THE PASSWORD IMMEDIATELY !!!"
echo ""
