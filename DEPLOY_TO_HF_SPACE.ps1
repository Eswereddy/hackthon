# ============================================================================
# DEPLOY TO HUGGING FACE SPACE - SUBMISSION #14 FIX
# ============================================================================
#
# This script deploys the fixed code to your Hugging Face Space
# Requirements: HF_TOKEN environment variable must be set
#
# ============================================================================

param(
    [Parameter(Mandatory=$false)]
    [string]$HfToken = $env:HF_TOKEN,
    
    [string]$SpaceId = "jakkireddyeswar/eswar"
)

# ============================================================================
# STEP 1: Validate inputs
# ============================================================================

if (-not $HfToken) {
    Write-Host "ERROR: HF_TOKEN not provided" -ForegroundColor Red
    Write-Host ""
    Write-Host "HOW TO FIX:" -ForegroundColor Yellow
    Write-Host "1. Go to: https://huggingface.co/settings/tokens" -ForegroundColor Cyan
    Write-Host "2. Copy your 'write' access token" -ForegroundColor Cyan
    Write-Host "3. Set it: `$env:HF_TOKEN = 'your_token_here'" -ForegroundColor Cyan
    Write-Host "4. Re-run this script" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "OR pass it directly:" -ForegroundColor Yellow
    Write-Host ".\DEPLOY_TO_HF_SPACE.ps1 -HfToken 'your_token_here'" -ForegroundColor Cyan
    exit 1
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Green
Write-Host "DEPLOYING TO HUGGING FACE SPACE" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green
Write-Host "Space ID: $SpaceId" -ForegroundColor Cyan
Write-Host "Space URL: https://huggingface.co/spaces/$SpaceId" -ForegroundColor Cyan
Write-Host ""

# ============================================================================
# STEP 2: Set environment variable
# ============================================================================

$env:HF_TOKEN = $HfToken
$env:HF_SPACE_ID = $SpaceId

# ============================================================================
# STEP 3: Verify Python environment
# ============================================================================

$pythonExe = ".\.venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) {
    $pythonExe = "python"
}

Write-Host "Using Python: $pythonExe" -ForegroundColor Yellow

# ============================================================================
# STEP 4: Check dependencies
# ============================================================================

Write-Host ""
Write-Host "Checking dependencies..." -ForegroundColor Yellow
& $pythonExe -c "import huggingface_hub; print('✓ huggingface_hub installed')" 2>$null

if ($LASTEXITCODE -ne 0) {
    Write-Host "Installing huggingface-hub..." -ForegroundColor Yellow
    & $pythonExe -m pip install -q huggingface-hub
    if ($LASTEXITCODE -ne 0) {
        Write-Host "ERROR: Failed to install huggingface-hub" -ForegroundColor Red
        exit 1
    }
}

# ============================================================================
# STEP 5: Deploy to HF Space
# ============================================================================

Write-Host ""
Write-Host "Uploading files to HF Space..." -ForegroundColor Yellow

& $pythonExe deploy_hf_space.py

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host "✓ DEPLOYMENT SUCCESSFUL!" -ForegroundColor Green
    Write-Host "============================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Your updated code is now deployed to:" -ForegroundColor Cyan
    Write-Host "https://huggingface.co/spaces/$SpaceId" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "NEXT STEPS:" -ForegroundColor Green
    Write-Host "1. Wait 2-3 minutes for HF Space to rebuild" -ForegroundColor White
    Write-Host "2. Check build status at: https://huggingface.co/spaces/$SpaceId" -ForegroundColor White
    Write-Host "3. Look for green checkmark ✅ indicating successful build" -ForegroundColor White
    Write-Host "4. Resubmit your hackathon entry" -ForegroundColor White
    Write-Host ""
    Write-Host "WHAT WAS FIXED:" -ForegroundColor Magenta
    Write-Host "  ✓ Exception handling in inference.py" -ForegroundColor White
    Write-Host "  ✓ Graceful fallback when API key missing" -ForegroundColor White
    Write-Host "  ✓ Proper OpenAI API call (client.chat.completions.create)" -ForegroundColor White
    Write-Host "  ✓ Timeout protection (30s)" -ForegroundColor White
    Write-Host "  ✓ All error cases handled" -ForegroundColor White
    Write-Host ""
} else {
    Write-Host ""
    Write-Host "❌ DEPLOYMENT FAILED" -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Yellow
    Write-Host "1. Verify HF_TOKEN is valid (check: https://huggingface.co/settings/tokens)" -ForegroundColor White
    Write-Host "2. Check internet connection" -ForegroundColor White
    Write-Host "3. Verify space exists: https://huggingface.co/spaces/$SpaceId" -ForegroundColor White
    Write-Host "4. Try again in a few minutes (HF might be rate-limiting)" -ForegroundColor White
    exit 1
}
