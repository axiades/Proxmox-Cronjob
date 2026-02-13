# Proxmox Cronjob Web Interface

Eine vollständige Web-Anwendung zur Verwaltung geplanter VM/Container-Aktionen (Start/Stop/Restart/Shutdown) über alle Proxmox Cluster-Nodes hinweg.

## 🎯 Features

- **Cluster-weite Verwaltung**: Verwaltet VMs und Container auf allen Proxmox Nodes
- **Flexible Scheduling**: Cron-basierte Zeitplanung für individuelle VMs oder Gruppen
- **Gruppen-Management**: Organisiere VMs in Gruppen für Bulk-Operationen
- **Wartungsfenster**: Definiere Blackout-Zeiten für geplante Wartungen
- **Ausführungshistorie**: Vollständige Logs aller durchgeführten Aktionen
- **Live-Status-Monitor**: Echtzeit-Überwachung des VM-Status
- **Sichere Authentifizierung**: JWT-basierte Authentifizierung
- **REST API**: Vollständige API-Dokumentation unter `/docs`

## 🏗️ Architektur

```
┌─────────────┐
│  Vue.js UI  │
└──────┬──────┘
       │ HTTPS (Nginx)
┌──────▼────────┐
│ FastAPI Backend│◄──── Proxmoxer ────► Proxmox Cluster API
└──────┬────────┘
       │
┌──────▼──────────┐
│   PostgreSQL    │
└─────────────────┘
       ▲
       │
┌──────┴──────────┐
│APScheduler Daemon│
└─────────────────┘
```

## 📋 Anforderungen

### System
- Debian 11/12/13 oder Ubuntu 20.04/22.04 LXC Container
- Mindestens 2 GB RAM
- 10 GB Speicherplatz
 - Unterstützte Architekturen: amd64, armhf, arm64

### Software
- Python 3.11+
- PostgreSQL 12+
- Nginx
- Node.js 20+ (für Frontend-Build)

### Proxmox
- Proxmox VE 6.2+ (für API Token Support)
- API Token mit VM.PowerMgmt Berechtigung

## 🚀 Installation

### 1. LXC Container auf Proxmox erstellen

```bash
# Create unprivileged Debian container
pct create 200 local:vztmpl/debian-12-standard_12.2-1_amd64.tar.zst \
  --hostname proxmox-cronjob \
  --memory 2048 \
  --cores 2 \
  --net0 name=eth0,bridge=vmbr0,ip=dhcp \
  --storage local-lvm \
  --rootfs local-lvm:10

pct start 200
pct enter 200
```

### 2. Repository klonen

```bash
cd /opt
git clone <repository-url> proxmox-cronjob
cd proxmox-cronjob
```

### 3. Setup-Script ausführen

```bash
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### ☁️ Cloud-Setup (z.B. Hetzner Cloud)

Diese Zusatzanleitung ist für Server in Cloud-Umgebungen gedacht, die **nicht** im gleichen Netzwerk wie Proxmox liegen.

**Voraussetzungen:**
- Öffentliche VM (Debian 11/12/13 oder Ubuntu 20.04/22.04)
- Erreichbarkeit der Proxmox API über VPN, WireGuard oder IP-Whitelist
- DNS-Name (optional, empfohlen für HTTPS)

**Firewall/Ports (Cloud-Security-Group):**
- `22/tcp` SSH
- `80/tcp` HTTP
- `443/tcp` HTTPS

#### One-Line Install Script

```bash
bash -c "sudo apt-get update && sudo apt-get install -y git curl && sudo mkdir -p /opt && sudo git clone https://github.com/axiades/Proxmox-Cronjob.git /opt/proxmox-cronjob && cd /opt/proxmox-cronjob && sudo chmod +x scripts/setup.sh && sudo ./scripts/setup.sh"
```

#### One-Line Install Script (Debian 13 + neueste Python + Build-Tools)

```bash
bash -c "sudo apt-get update && sudo apt-get install -y git curl build-essential python3-dev libpq-dev pkg-config gcc && curl https://sh.rustup.rs -sSf | sh -s -- -y && source $HOME/.cargo/env && sudo mkdir -p /opt && sudo git clone https://github.com/axiades/Proxmox-Cronjob.git /opt/proxmox-cronjob && cd /opt/proxmox-cronjob && sudo chmod +x scripts/setup.sh && sudo ./scripts/setup.sh"
```

#### Wichtige Cloud-Anpassungen

1. **.env anpassen** (Proxmox per VPN/Whitelist erreichbar machen):
  - `PROXMOX_HOST` auf die **erreichbare** IP/FQDN setzen
  - `PROXMOX_VERIFY_SSL=false` falls internes Zertifikat genutzt wird
2. **Nginx/HTTPS**:
  - Für öffentliches DNS: Let's Encrypt nutzen (siehe Schritt 6)
3. **Security**:
  - Standard-Login sofort ändern
  - Admin-Token in Proxmox minimal berechtigen

### 4. Konfiguration anpassen

```bash
cd /opt/proxmox-cronjob/backend
nano .env
```

Wichtige Einstellungen:
```env
# Database
DATABASE_URL=postgresql://proxmox_cronjob:YOUR_PASSWORD@localhost:5432/proxmox_cronjob

# Security
SECRET_KEY=your-secret-key-generate-with-openssl
ENCRYPTION_KEY=your-fernet-key-generate-with-python

# Proxmox
PROXMOX_HOST=192.168.1.100
PROXMOX_USER=root@pam
PROXMOX_TOKEN_NAME=cronjob
PROXMOX_TOKEN_VALUE=your-api-token-uuid
PROXMOX_VERIFY_SSL=false
```

### 5. Proxmox API Token erstellen

```bash
# On Proxmox host
pveum user token add root@pam cronjob --privsep=0
# Copy the token UUID to .env file
```

### 6. SSL-Zertifikat erstellen

#### Selbstsigniert (Test):
```bash
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /etc/ssl/private/proxmox-cronjob.key \
  -out /etc/ssl/certs/proxmox-cronjob.crt
```

#### Let's Encrypt (Produktion):
```bash
apt-get install certbot python3-certbot-nginx
certbot --nginx -d cronjob.yourdomain.com
# Update Nginx config with certbot paths
```

### 7. Services starten

```bash
systemctl start proxmox-cronjob-api
systemctl start proxmox-cronjob-scheduler
systemctl enable proxmox-cronjob-api
systemctl enable proxmox-cronjob-scheduler
systemctl restart nginx

# Check status
systemctl status proxmox-cronjob-api
systemctl status proxmox-cronjob-scheduler
journalctl -u proxmox-cronjob-scheduler -f
```

### 8. Web-Interface aufrufen

Öffne im Browser: `https://your-server-ip`

**Standard-Login:**
- Username: `admin`
- Password: `admin`

⚠️ **WICHTIG**: Password sofort ändern!

## 📖 Verwendung

### VMs synchronisieren

1. Dashboard öffnen
2. "🔄 Sync VMs" klicken
3. Warten bis Synchronisation abgeschlossen

### Schedule erstellen

1. Navigiere zu "Schedules"
2. "➕ Create Schedule" klicken
3. Eingaben:
   - **Name**: Beschreibender Name
   - **Target Type**: VM oder Group
   - **Target ID**: VMID oder Group ID
   - **Action**: start, stop, restart, shutdown, reset
   - **Cron Expression**: z.B. `0 2 * * *` (täglich 2 Uhr)
4. "Create" klicken

### Cron Expression Beispiele

```bash
*/5 * * * *      # Alle 5 Minuten
0 * * * *        # Jede Stunde
0 2 * * *        # Täglich um 2:00 Uhr
0 0 * * 0        # Sonntags um Mitternacht
0 0 1 * *        # Am 1. jeden Monats
0 2 * * 1-5      # Montag bis Freitag um 2:00 Uhr
*/30 9-17 * * 1-5 # Alle 30 Min von 9-17 Uhr, Mo-Fr
```

### VM-Gruppe erstellen

1. "Groups" → "➕ Create Group"
2. Name und Beschreibung eingeben
3. "Create" klicken
4. "View" → VMs hinzufügen

### Wartungsfenster einrichten

1. "Blackouts" → "➕ Create Blackout"
2. Eingaben:
   - **Name**: z.B. "Nachtwartung"
   - **Start Time**: 22:00
   - **End Time**: 06:00
   - **Days**: `[0,1,2,3,4]` (Mo-Fr)
3. "Create" klicken

Während Blackout-Zeiten werden **keine** geplanten Aktionen ausgeführt.

### Logs überprüfen

1. "Logs" öffnen
2. Nach Status/VMID filtern
3. Fehler-Details in "Error/Reason" Spalte

## 🔧 Wartung

### Logs ansehen

```bash
# API Logs
journalctl -u proxmox-cronjob-api -f

# Scheduler Logs
journalctl -u proxmox-cronjob-scheduler -f

# Nginx Logs
tail -f /var/log/nginx/proxmox-cronjob-access.log
tail -f /var/log/nginx/proxmox-cronjob-error.log
```

### Datenbank Backup

```bash
sudo -u postgres pg_dump proxmox_cronjob > backup_$(date +%Y%m%d).sql
```

### Datenbank wiederherstellen

```bash
sudo -u postgres psql proxmox_cronjob < backup_20260213.sql
```

### Services neu starten

```bash
systemctl restart proxmox-cronjob-api
systemctl restart proxmox-cronjob-scheduler
```

### VM Cache manuell synchronisieren

```bash
curl -X POST http://localhost:8000/api/vms/sync \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 🐛 Troubleshooting

### Debian 13 + neueste Python (amd64/armhf/arm64) Build-Tools

Bei Debian 13 mit der neuesten Python-Version werden für einige Pakete (z.B. `psycopg2-binary`, `pydantic-core`) native Build-Tools benötigt.

```bash
sudo apt-get update
sudo apt-get install -y build-essential python3-dev libpq-dev pkg-config gcc

# Rust/Cargo fuer pydantic-core
curl https://sh.rustup.rs -sSf | sh -s -- -y
source $HOME/.cargo/env
```

Danach erneut installieren:

```bash
cd /opt/proxmox-cronjob/backend
source venv/bin/activate
pip install -r requirements.txt
```

### Service startet nicht

```bash
# Check logs
journalctl -u proxmox-cronjob-api -xe

# Check config
cat /opt/proxmox-cronjob/backend/.env

# Test database connection
sudo -u postgres psql proxmox_cronjob -c "SELECT 1"
```

### Proxmox API Fehler

```bash
# Test API Token
curl -k -H "Authorization: PVEAPIToken=root@pam!cronjob=YOUR-UUID" \
  https://proxmox-host:8006/api2/json/nodes

# Check token permissions
pveum user token permissions root@pam cronjob
```

### Schedules werden nicht ausgeführt

1. Scheduler Service läuft: `systemctl status proxmox-cronjob-scheduler`
2. Schedule ist aktiviert (enabled=true)
3. Nicht in Blackout-Fenster
4. VM existiert und ist erreichbar
5. Logs prüfen: `journalctl -u proxmox-cronjob-scheduler -f`

### Frontend lädt nicht

```bash
# Check Nginx
nginx -t
systemctl status nginx

# Check if dist folder exists
ls -la /var/www/proxmox-cronjob/dist

# Rebuild frontend
cd /opt/proxmox-cronjob/frontend
npm run build
cp -r dist/* /var/www/proxmox-cronjob/
```

## 🔒 Sicherheit

### Berechtigungen einschränken

Erstelle speziellen Proxmox User mit minimalen Rechten:

```bash
# On Proxmox host
pveum user add cronjob@pve --password YOUR_PASSWORD
pveum role add VMRestarter -privs VM.PowerMgmt
pveum aclmod /vms -user cronjob@pve -role VMRestarter

# Create API token for this user
pveum user token add cronjob@pve cron-token --privsep=0
```

### Firewall

```bash
# Allow only necessary ports
ufw allow 443/tcp
ufw enable
```

### Regular Updates

```bash
cd /opt/proxmox-cronjob
git pull
cd backend
source venv/bin/activate
pip install --upgrade -r requirements.txt
systemctl restart proxmox-cronjob-api proxmox-cronjob-scheduler
```

## 📚 API Documentation

Interaktive API-Dokumentation: `https://your-server/api/docs`

### Wichtige Endpoints

- **POST** `/api/auth/login` - Login
- **GET** `/api/vms` - Liste VMs
- **POST** `/api/vms/sync` - VMs synchronisieren
- **GET** `/api/schedules` - Liste Schedules
- **POST** `/api/schedules` - Schedule erstellen
- **POST** `/api/actions/vm/{vmid}` - Manuelle Aktion ausführen
- **GET** `/api/logs` - Execution Logs
- **GET** `/api/stats` - Dashboard Statistiken

## 🤝 Contributing

Pull Requests sind willkommen!

## 📝 Lizenz

MIT License

## 📞 Support

Bei Problemen:
1. Logs prüfen (`journalctl`)
2. Issue auf GitHub erstellen
3. Dokumentation konsultieren

## 🎉 Danksagung

- **Proxmoxer** - Python Proxmox API Wrapper
- **FastAPI** - Modernes Python Web Framework
- **Vue.js** - Progressive JavaScript Framework
- **APScheduler** - Advanced Python Scheduler

---

**Version**: 1.0.0  
**Erstellt**: Februar 2026  
**Autor**: Proxmox Enthusiast
