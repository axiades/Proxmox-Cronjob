# ══════════════════════════════════════════════════
# Proxmox Cronjob - Push to GitHub Instructions
# ══════════════════════════════════════════════════

## 🎯 Current Status

✅ Git repository initialized
✅ All files committed  
✅ Branch renamed to 'main'
✅ deploy-lxc.sh updated with your username

## 📝 Next Steps

### Step 1: Create GitHub Repository

A browser window should have opened to https://github.com/new

Fill in the form:
- **Repository name:** Proxmox-Cronjob
- **Description:** Automated Proxmox VM/LXC Cronjob Manager with Web Interface
- **Visibility:** Public (or Private, your choice)
- **DO NOT** initialize with README, .gitignore, or license
- Click **"Create repository"**

### Step 2: Authenticate GitHub CLI

Open a PowerShell terminal and run:

```powershell
gh auth login
```

Follow the prompts:
- Choose: `GitHub.com`
- Protocol: `HTTPS`
- Authenticate Git: `Yes`
- How: `Login with a web browser`
- Copy the code and press Enter
- Paste in browser and authorize

### Step 3: Push to GitHub

After authentication, run these commands:

```powershell
# Navigate to project directory
cd D:\Web_Dev\Proxmox-Cronjob

# Add remote
git remote add origin https://github.com/axiades/Proxmox-Cronjob.git

# Push to GitHub
git push -u origin main
```

## 🚀 Alternative: Manual Method (if gh CLI doesn't work)

If GitHub CLI authentication fails, use a Personal Access Token:

1. Go to: https://github.com/settings/tokens/new
2. Token name: `Proxmox-Cronjob`
3. Expiration: `No expiration` or choose your preference
4. Scopes: Select `repo` (Full control of private repositories)
5. Click **"Generate token"**
6. **COPY THE TOKEN** (you can't see it again!)

Then run:

```powershell
# Add remote (if not already done)
git remote add origin https://github.com/axiades/Proxmox-Cronjob.git

# Push (will prompt for credentials)
git push -u origin main
# Username: axiades
# Password: <paste your token here>
```

## 📦 Repository Contents

Your repository will contain:

```
Proxmox-Cronjob/
├── backend/               # FastAPI application
│   ├── app/
│   │   ├── api/          # REST API endpoints
│   │   ├── services/     # Business logic
│   │   ├── models.py     # Database models
│   │   └── ...
│   ├── scheduler_daemon.py
│   └── requirements.txt
├── frontend/              # Vue.js 3 application
│   ├── src/
│   │   ├── components/
│   │   ├── views/
│   │   └── ...
│   └── package.json
├── database/              # PostgreSQL schema
│   └── schema.sql
├── deployment/            # Systemd & Nginx configs
│   ├── nginx/
│   └── systemd/
├── scripts/               # Deployment scripts
│   ├── deploy-lxc.sh     # Automated LXC deployment
│   ├── setup.sh          # Manual setup
│   └── create_admin.py   # Create admin user
├── README.md              # German documentation
└── .gitignore

50+ files, ~5000 lines of code
```

## 🔍 Verify Push

After pushing, verify by opening:
https://github.com/axiades/Proxmox-Cronjob

You should see:
- All files and folders
- Initial commit message
- README.md displayed at the bottom

## 📋 Future Updates

To push updates later:

```powershell
git add .
git commit -m "Your commit message"
git push
```

## 🆘 Troubleshooting

**Problem:** `git push` asks for password but token doesn't work

**Solution:** Use Git Credential Manager:
```powershell
git config --global credential.helper manager
git push -u origin main
```
Then enter username and token when prompted.

**Problem:** `remote origin already exists`

**Solution:**
```powershell
git remote remove origin
git remote add origin https://github.com/axiades/Proxmox-Cronjob.git
```

**Problem:** Authentication failed / 403 error

**Solution:** Make sure you created a Personal Access Token with `repo` scope and use it as password.

## ✨ Bonus: Update README Badge

After pushing, you can add a badge to your README:

```markdown
[![GitHub](https://img.shields.io/github/stars/axiades/Proxmox-Cronjob?style=social)](https://github.com/axiades/Proxmox-Cronjob)
```

## 🎉 Done!

Once pushed, share your repository or deploy using the LXC script:

```bash
# On Proxmox host
wget https://raw.githubusercontent.com/axiades/Proxmox-Cronjob/main/scripts/deploy-lxc.sh
chmod +x deploy-lxc.sh
./deploy-lxc.sh
```

═══════════════════════════════════════════════════
