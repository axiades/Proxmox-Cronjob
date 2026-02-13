# LXC Deployment - Was wird alles automatisch eingerichtet?

Das `deploy-lxc.sh` Script richtet den kompletten LXC Container mit allem ein, was du brauchst:

## ✅ Automatische Installation

### System-Level
- ✓ Debian 12 LXC Container erstellen
- ✓ System-Updates durchführen
- ✓ Alle System-Dependencies instalieren

### Datenbank
- ✓ PostgreSQL installieren und starten
- ✓ `proxmox_cronjob` User erstellen
- ✓ `proxmox_cronjob` Datenbank erstellen
- ✓ **Komplettes Schema laden** (users, schedules, logs, etc.)
- ✓ **Default Admin-User erstellen** (admin / admin)
- ✓ Berechtigungen konfigurieren
- ✓ Datenbank verifizieren

### Backend
- ✓ Python 3.11 installieren
- ✓ Virtual Environment erstellen
- ✓ Alle Python-Dependencies installieren (FastAPI, Proxmoxer, etc.)
- ✓ `.env` Datei generieren mit:
  - DATABASE_URL (PostgreSQL Connection)
  - SECRET_KEY (generiert)
  - ENCRYPTION_KEY (generiert)
  - PROXMOX_HOST, USER, TOKEN (deine eingabe)
  - CORS konfiguriert

### Frontend
- ✓ Node.js 20 installieren
- ✓ npm Dependencies installieren
- ✓ Vue.js Frontend bauen (npm run build)
- ✓ In `/var/www/proxmox-cronjob` deployen

### Web-Server
- ✓ Nginx installieren
- ✓ Reverse Proxy konfigurieren
- ✓ SSL-Zertifikat generieren (Self-Signed)
- ✓ Frontend static files bereitstellen

### Dienste
- ✓ Systemd Services installieren:
  - `proxmox-cronjob-api` (FastAPI Server)
  - `proxmox-cronjob-scheduler` (Scheduler Daemon)
- ✓ Services starten
- ✓ Autostart konfigurieren (systemctl enable)

### Verifikation
- ✓ Alle Services gehören zu `www-data` User
- ✓ Log-Verzeichnisse erstellen
- ✓ API Health-Check durchführen
- ✓ Service-Status prüfen
- ✓ Erfolgs-Message anzeigen

## 🚀 Nach dem Deployment - Sofort verwendbar

```bash
# Nach ~10 Minuten Deployment-Zeit:
https://<CONTAINER_IP>       # Web Interface öffnen
Login:   admin / admin       # Standard-Credentials
```

### Was funktioniert sofort:

1. **Web Interface** - Vollständig konfiguriert und erreichbar
2. **PostgreSQL Datenbank** - Mit Daten initialisiert
3. **Admin-Account** - Bereits erstellt und login bereit
4. **FastAPI Backend** - Läuft und antwortet auf API-Calls
5. **Scheduler** - Startet automatisch
6. **Proxmox-Integration** - Mit deinen Credentials konfiguriert

## 📝 Was du noch tun musst

### 1. Password ändern (WICHTIG!)
```
Login → Admin Profil → Passwort ändern
```

### 2. VMs synchronisieren
```
Dashboard → Button "Sync VMs"
```

### 3. Erste Schedule erstellen
```
Schedules Tab → Create Schedule
Cron: */5 * * * *
Action: Restart
VMs: wählen
```

Das war's! 🎉

## 🔧 Troubleshooting

Falls etwas nicht lädt:

```bash
# SSH zum Container
pct enter 100  # ID anpassen

# Logs anschauen
journalctl -u proxmox-cronjob-api -f
journalctl -u proxmox-cronjob-scheduler -f

# Services neu starten
systemctl restart proxmox-cronjob-api
systemctl restart proxmox-cronjob-scheduler

# Nginx neu starten
systemctl reload nginx

# Datenbank prüfen
sudo -u postgres psql proxmox_cronjob
```

## 📊 Was alles eingerichtet wurde (nach Deployment)

```
LXC Container Status:
├── PostgreSQL        ✓ running
├── FastAPI API       ✓ running (port 8000)
├── Scheduler         ✓ running
├── Nginx             ✓ running (port 80/443)
├── Frontend          ✓ compiled und served
├── Database          ✓ initialized
└── Certificates      ✓ self-signed SSL ready
```

---

**TL;DR:** Einfach Script ausführen, 10 Min warten, https://container-ip eingebenen - fertig! ✨
