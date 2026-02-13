# Netzwerk-Konfiguration für verschiedene Umgebungen

Das `deploy-lxc.sh` Script fragt jetzt ab, wie der Service erreichbar sein soll. Hier sind die Optionen:

## 1️⃣ Local Mode (Standard)

**Nutzung:** Interne RZ-Netzwerke, sichere Unternehmensumgebungen

```
Choose access mode (1-3) [1]: 1
```

**Was wird konfiguriert:**
- ✓ HTTP only (kein SSL nötig)
- ✓ Läuft auf Port 80
- ✓ Nur für private Netzwerke erreichbar:
  - `192.168.0.0/16`
  - `10.0.0.0/8`
  - `172.16.0.0/12`
  - `127.0.0.1` (localhost)
- ✓ Host-basierte Zugriffskontrolle

**Zugriff:**
```
http://<CONTAINER_IP>
```

**Ideal für:**
- Kleine/mittlere Unternehmen
- Interne Nutzung nur
- VMware / Hypervisor-Umgebungen mit Firewall-Schutz

---

## 2️⃣ Internet Mode

**Nutzung:** Öffentlich erreichbare Services mit eigenem DNS

```
Choose access mode (1-3) [1]: 2
Enter fully qualified domain name (FQDN) [proxmox-cronjob.local]: cronjob.example.com
```

**Was wird konfiguriert:**
- ✓ HTTPS (Port 443) mit selbstsigniertem SSL
- ✓ Automatisches Redirect von HTTP → HTTPS
- ✓ Security-Header (HSTS, X-Frame-Options, etc.)
- ✓ FQDN wird validiert
- ✓ Moderne TLS Ciphers (TLSv1.2+)

**Zugriff:**
```
https://cronjob.example.com
```

**DNS Setup erforderlich:**
```bash
# Beispiel: A-Record in deiner DNS-Zone
cronjob.example.com  A  <PUBLIC_IP>
```

**Ideal für:**
- Öffentlich erreichbare Services
- Multi-Standort Unternehmen
- Cloud-basierte Infrastruktur
- Services mit echter Internet-Domain

---

## 3️⃣ Corporate Proxy Mode (Hardware Firewall)

**Nutzung:** Für deine Firma mit Hardware Firewall! 🎯

```
Choose access mode (1-3) [1]: 3
Enter proxy backend address (e.g., cronjob.internal.company.local): cronjob.rz.mycompany.com
Is this behind a corporate firewall? (Y/n) [Y]: Y
```

**Was wird konfiguriert:**
- ✓ HTTP on Port 8080 (HTTPS auf Firewall-Ebene)
- ✓ Vertraut X-Forwarded-* Headers aus Firewall
- ✓ Keine Host-Restrictions (Firewall kontrolliert Zugang)
- ✓ Perfekt für Reverse Proxy Setups

**Netzwerk-Architektur:**

```
┌─────────────────────────────────────────┐
│         Corporate Netzwerk              │
│                                         │
│  ┌──────────────────────────────────┐  │
│  │  Hardware Firewall               │  │
│  │  (reverse proxy + SSL)           │  │
│  │                                  │  │
│  │ Port 443 (HTTPS)                │  │
│  │ + WAF                           │  │
│  │ + Logging                       │  │
│  └────────────┬─────────────────────┘  │
│               │                         │
│            (HTTP)                       │
│               │                         │
│  ┌────────────▼─────────────────────┐  │
│  │ Proxmox Cronjob LXC Container    │  │
│  │                                  │  │
│  │ Port 8080 (HTTP)                │  │
│  │ + Nginx Reverse Proxy           │  │
│  │ + FastAPI Backend               │  │
│  │ + PostgreSQL DB                 │  │
│  │ + Vue.js Frontend               │  │
│  └──────────────────────────────────┘  │
└─────────────────────────────────────────┘
```

**Hardware Firewall Konfiguration:**

Beispiel Regel (Fortinet, Paloalto, etc.):

```
Firewall Rule:
  Name: Proxmox-Cronjob
  
  Inbound:
    Protocol: HTTPS (443)
    Destination: cronjob.mycompany.com
  
  Action: Forward
    to Backend: http://CONTAINER_IP:8080
    Add X-Forwarded-For: Yes
    Add X-Forwarded-Proto: https
    Add X-Forwarded-Host: cronjob.mycompany.com
  
  SSL/TLS:
    Certificate: (dein Firewalls Root-CA)
    Keep-Alive: enabled
```

**Zugriff:**
```
https://cronjob.mycompany.com
```

**Wichtig:**
- ✓ Container läuft auf Port 8080
- ✓ Firewall managed SSL/TLS
- ✓ Firewall managed WAF & Logging
- ✓ Container kennt original Client-IP via X-Forwarded-For
- ✓ API authentifiziert über JWT

**Ideal für:**
- Unternehmen mit Hardware Firewall
- Multi-Layer Security Requirements
- Logging/Auditing auf Firewall-Ebene
- Single Sign-On Integration

---

## 🔐 Security-Vergleich

| Feature | Local | Internet | Corporate |
|---------|-------|----------|-----------|
| SSL/TLS | Nein | Selbstgeneriert | Firewall |
| Host-Restriction | Ja | Nein | Nein |
| X-Forwarded Headers | Nein | Nein | Ja |
| WAF möglich | Nein | Nein | Ja |
| Rate-Limiting | Nein | Nein | Firewall |
| DDoS Protection | Nein | Nein | Firewall |
| Threat Updates | Nein | Nein | Firewall |

---

## 📝 Beispiel Setups

### Kleines Unternehmen (50-200 Mitarbeiter)
```
Mode: Local (1)
Zugriff: 192.168.100.0/24 Netzwerk via Nginx
```

### StartUp mit Public Service
```
Mode: Internet (2)
FQDN: cronjob.startup.io
SSL: Self-signed (später Let's Encrypt)
```

### Enterprise mit RZ-Infrastruktur (dein Fall!)
```
Mode: Corporate Proxy (3)
Backend: cronjob.internal.company.local
Firewall: Palo Alto / FortiGate / Cisco ASA
SSL: Company Wildcard Cert
Logging: Splunk / ELK Stack
```

---

## 🚀 Beispiel Deployment

```bash
# Auf Proxmox Host ausführen
wget https://raw.githubusercontent.com/axiades/Proxmox-Cronjob/main/scripts/deploy-lxc.sh
chmod +x deploy-lxc.sh
./deploy-lxc.sh

# Fragen:
# Container ID: 100
# Password: MySecurePass123
# Network: dhcp
# CPU: 4
# RAM: 4096
# Disk: 20
# Proxmox Host: proxmox.local
# API Token: (erstelwn lassen)
#
# ⭐ NEW - Network Access Mode:
#   Choose access mode (1-3) [1]: 3
#   Backend: cronjob-prod.company.local
#   Corporate Firewall: Y
```

Nach ~10 Minuten:
- Container ist fertig
- Port 8080 antwortet auf `http://CONTAINER_IP:8080`
- Firewall forwarded `https://cronjob.company.local` → `http://CONTAINER_IP:8080`
- Alle X-Forwarded Headers sind konfiguriert

---

## 🆘 Häufige Fragen

**F: Kann ich den Modus nachträglich ändern?**

A: Ja! Manuell:
```bash
pct enter 100
nano /etc/nginx/sites-available/proxmox-cronjob.conf
systemctl reload nginx
```

**F: Firewall-Regel funktioniert nicht?**

A: Check:
```bash
# Von Firewall: Proxy Health Check
curl http://CONTAINER_IP:8080

# Container Health
pct exec 100 -- curl localhost:8000/health
```

**F: Kann ich Let's Encrypt statt Self-Signed verwenden?**

A: Ja, aber nur im Internet Mode (2), und nur wenn die FQDN öffentlich erreichbar ist.

**F: Proxy Mode - Was sind X-Forwarded Headers?**

A: Headers die die Firewall setzt:
- `X-Forwarded-For`: Original Client IP
- `X-Forwarded-Proto`: Original Protocol (https)
- `X-Forwarded-Host`: Original Hostname (cronjob.company.local)

Sie ermöglichen dem Backend, die echte Client-IP und das Original-Request zu kennen.

**F: Kann ich verschiedene Container-Modi haben?**

A: Naja - nicht wirklich praktisch. Deploy einen Container für deine Situation, das reicht.

---

## 📞 Support

Für detaillierte Firewall-Konfiguration:
- Palo Alto Networks: Web Application Firewall Config
- Fortinet FortiGate: Reverse Proxy Rules
- Cisco ASA: Access Lists + SSL Inspection

Das Deployment-Script kümmert sich um den Container - deine Firewall um den Rest! 🔒

