# Proxmox Cronjob - GitHub Push Script
# This script initializes git repository and prepares for GitHub push

param(
    [string]$GitHubUsername = "axiades",
    [string]$RepositoryName = "Proxmox-Cronjob"
)

$ErrorActionPreference = "Continue"

Write-Host "`n═══════════════════════════════════════════════════" -ForegroundColor Green
Write-Host "  Proxmox Cronjob - GitHub Setup" -ForegroundColor Green
Write-Host "═══════════════════════════════════════════════════`n" -ForegroundColor Green

# Check if in correct directory
$currentDir = Get-Location
if (-not (Test-Path ".\backend") -or -not (Test-Path ".\frontend")) {
    Write-Host "Error: Please run this script from the Proxmox-Cronjob root directory!" -ForegroundColor Red
    exit 1
}

# Initialize Git repository
Write-Host "Initializing Git repository..." -ForegroundColor Yellow
if (-not (Test-Path ".git")) {
    git init
    Write-Host "Git repository initialized" -ForegroundColor Green
} else {
    Write-Host "Git repository already exists" -ForegroundColor Green
}

# Create/Update .gitignore if needed
Write-Host "`nChecking .gitignore..." -ForegroundColor Yellow
if (Test-Path ".gitignore") {
    Write-Host ".gitignore exists" -ForegroundColor Green
} else {
    Write-Host ".gitignore not found - should already exist!" -ForegroundColor Yellow
}

# Add all files
Write-Host "`nAdding files to Git..." -ForegroundColor Yellow
git add .
Write-Host "Files added" -ForegroundColor Green

# Create initial commit
Write-Host "`nCreating initial commit..." -ForegroundColor Yellow
$commitMessage = "Initial commit: Proxmox Cronjob Web Interface"
git commit -m $commitMessage 2>&1 | Out-Null
if ($LASTEXITCODE -eq 0) {
    Write-Host "Initial commit created" -ForegroundColor Green
} else {
    Write-Host "Commit may already exist or nothing to commit" -ForegroundColor Green
}

# Rename branch to main
Write-Host "`nSetting default branch to 'main'..." -ForegroundColor Yellow
git branch -M main 2>&1 | Out-Null
Write-Host "Branch renamed to main" -ForegroundColor Green

# Repository URL
$repoUrl = "https://github.com/$GitHubUsername/$RepositoryName.git"

Write-Host "`n═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Next Steps:" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════`n" -ForegroundColor Cyan

Write-Host "1. Create GitHub Repository:" -ForegroundColor Yellow
Write-Host "   a) Go to https://github.com/new" -ForegroundColor White
Write-Host "   b) Repository name: $RepositoryName" -ForegroundColor White
Write-Host "   c) Description: Automated Proxmox VM/LXC Cronjob Manager with Web Interface" -ForegroundColor White
Write-Host "   d) Choose Public or Private" -ForegroundColor White
Write-Host "   e) Do NOT initialize with README, .gitignore, or license" -ForegroundColor White
Write-Host "   f) Click 'Create repository'" -ForegroundColor White
Write-Host ""

Write-Host "2. Authenticate with GitHub:" -ForegroundColor Yellow
Write-Host "   Run one of these commands:" -ForegroundColor White
Write-Host "   - gh auth login" -ForegroundColor Cyan
Write-Host "   OR" -ForegroundColor White
Write-Host "   - Generate a Personal Access Token at https://github.com/settings/tokens/new" -ForegroundColor Cyan
Write-Host "     (Select 'repo' scope)" -ForegroundColor Gray
Write-Host ""

Write-Host "3. Add remote and push:" -ForegroundColor Yellow
Write-Host "   git remote add origin $repoUrl" -ForegroundColor Cyan
Write-Host "   git push -u origin main" -ForegroundColor Cyan
Write-Host ""

Write-Host "4. Update deploy-lxc.sh:" -ForegroundColor Yellow
Write-Host "   Replace 'YOUR-USERNAME' with 'axiades' in:" -ForegroundColor White
Write-Host "   ./scripts/deploy-lxc.sh (line ~193)" -ForegroundColor Gray
Write-Host ""

Write-Host "═══════════════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  Quick Commands Summary:" -ForegroundColor Cyan
Write-Host "═══════════════════════════════════════════════════`n" -ForegroundColor Cyan

Write-Host @"
# After creating the GitHub repository:
git remote add origin $repoUrl
git push -u origin main

# To update the deploy script:
# (Replace 'YOUR-USERNAME' with 'axiades' in deploy-lxc.sh)

# To push updates later:
git add .
git commit -m "Description of changes"
git push
"@ -ForegroundColor White

Write-Host "`n✓ Local Git repository is ready!" -ForegroundColor Green
Write-Host "✓ Complete the steps above to push to GitHub.`n" -ForegroundColor Green
