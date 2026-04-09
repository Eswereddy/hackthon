param(
    [Parameter(Mandatory=$true)]
    [string]$HfToken,
    
    [string]$SpaceId = "jakkireddyeswar/eswar"
)

$ErrorActionPreference = "Stop"

Write-Host "`n" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host "Deploying to Hugging Face Space" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host "Space ID: $SpaceId" -ForegroundColor Cyan
Write-Host "Space URL: https://huggingface.co/spaces/$SpaceId" -ForegroundColor Cyan

# Set environment variable for Python
$env:HF_TOKEN = $HfToken

# Get Python executable
$pythonExe = ".\.venv313\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = ".\.venv\Scripts\python.exe"
}
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

Write-Host "Using Python: $pythonExe" -ForegroundColor Yellow

try {
    Write-Host "`nDeploying files..." -ForegroundColor Yellow
    & $pythonExe deploy_hf_space.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n" -ForegroundColor Green
        Write-Host "================================================" -ForegroundColor Green
        Write-Host "✓ DEPLOYMENT SUCCESSFUL!" -ForegroundColor Green
        Write-Host "================================================" -ForegroundColor Green
        Write-Host "Your updated code is now live at:" -ForegroundColor Cyan
        Write-Host "https://huggingface.co/spaces/$SpaceId" -ForegroundColor Cyan
        Write-Host "`nThe HF Space will rebuild automatically with" -ForegroundColor Green
        Write-Host "the latest code from your GitHub repository." -ForegroundColor Green
        Write-Host "`nChanges deployed:" -ForegroundColor Yellow
        Write-Host "  ✓ Fixed OpenAI API call (client.chat.completions.create)" -ForegroundColor White
        Write-Host "  ✓ Fixed response parsing" -ForegroundColor White
        Write-Host "  ✓ Added comprehensive error handling" -ForegroundColor White
        Write-Host "`nYou can now resubmit your hackathon:" -ForegroundColor Cyan
        Write-Host "https://www.scaler.com/hackathons/openenv" -ForegroundColor Cyan
        Write-Host "`n"
    } else {
        throw "Deployment script failed with exit code $LASTEXITCODE"
    }
} catch {
    Write-Host "`nERROR: Deployment failed" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
