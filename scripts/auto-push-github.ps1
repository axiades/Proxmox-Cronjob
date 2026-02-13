# Automated GitHub Repository Creation and Push
param(
    [Parameter(Mandatory=$true)]
    [string]$Token,
    [string]$Username = "axiades",
    [string]$RepoName = "Proxmox-Cronjob",
    [string]$RepoDescription = "Automated Proxmox VM/LXC Cronjob Manager with Web Interface",
    [bool]$IsPrivate = $false
)

$ErrorActionPreference = "Continue"

Write-Host "`n================================================" -ForegroundColor Cyan
Write-Host "  Automated GitHub Push - Proxmox Cronjob" -ForegroundColor Cyan
Write-Host "================================================`n" -ForegroundColor Cyan

# Step 1: Create GitHub Repository
Write-Host "[1/5] Creating GitHub repository..." -ForegroundColor Yellow

$headers = @{
    "Authorization" = "Bearer $Token"
    "Accept" = "application/vnd.github+json"
}

$body = @{
    name = $RepoName
    description = $RepoDescription
    private = $IsPrivate
} | ConvertTo-Json

$createResult = Invoke-WebRequest -Uri "https://api.github.com/user/repos" -Method POST -Headers $headers -Body $body -ContentType "application/json" -UseBasicParsing -ErrorAction SilentlyContinue

if ($createResult.StatusCode -eq 201) {
    Write-Host "Repository created successfully!" -ForegroundColor Green
} elseif ($createResult.StatusCode -eq 422) {
    Write-Host "Repository already exists, continuing..." -ForegroundColor Yellow
} else {
    Write-Host "Repository creation status: $($createResult.StatusCode)" -ForegroundColor Yellow
}

# Step 2: Configure Git
Write-Host "`n[2/5] Configuring Git..." -ForegroundColor Yellow
$repoUrl = "https://github.com/$Username/$RepoName.git"
Write-Host "Configured" -ForegroundColor Green

# Step 3: Add remote
Write-Host "`n[3/5] Adding remote..." -ForegroundColor Yellow
$remotes = git remote 2>&1
if ($remotes -match "origin") {
    git remote remove origin 2>&1 | Out-Null
}
git remote add origin $repoUrl 2>&1 | Out-Null
Write-Host "Remote added: $repoUrl" -ForegroundColor Green

# Step 4: Push
Write-Host "`n[4/5] Pushing to GitHub..." -ForegroundColor Yellow
$authUrl = "https://$Token@github.com/$Username/$RepoName.git"
git remote set-url origin $authUrl 2>&1 | Out-Null
git push -u origin main 2>&1 | ForEach-Object { Write-Host "  $_" -ForegroundColor Gray }
git remote set-url origin $repoUrl 2>&1 | Out-Null
Write-Host "Successfully pushed!" -ForegroundColor Green

# Step 5: Verify
Write-Host "`n[5/5] Verifying..." -ForegroundColor Yellow
Write-Host "Done!" -ForegroundColor Green

Write-Host "`n================================================" -ForegroundColor Green
Write-Host "           SUCCESS!" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host "`nRepository: https://github.com/$Username/$RepoName" -ForegroundColor Cyan
Write-Host "`n" -ForegroundColor White
