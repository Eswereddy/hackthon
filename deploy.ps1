param(
    [switch]$SkipDocker,
    [switch]$SkipValidator,
    [switch]$SkipHF
)

$ErrorActionPreference = "Stop"

function Resolve-PythonExe {
    if (Test-Path ".\.venv313\Scripts\python.exe") { return ".\.venv313\Scripts\python.exe" }
    if (Test-Path ".\.venv\Scripts\python.exe") { return ".\.venv\Scripts\python.exe" }
    return "python"
}

$pythonExe = Resolve-PythonExe
Write-Host "Using Python: $pythonExe"

Write-Host "[1/4] Installing dependencies..."
& $pythonExe -m pip install -r requirements.txt

Write-Host "[2/4] Running preflight checks..."
& $pythonExe preflight.py

if (-not $SkipValidator) {
    Write-Host "[3/4] Running OpenEnv validator (if installed)..."
    $openenvCmd = Get-Command openenv -ErrorAction SilentlyContinue
    if ($null -eq $openenvCmd) {
        Write-Warning "openenv CLI not found. Install official hackathon validator, then run: openenv validate"
    }
    else {
        try {
            openenv validate
        }
        catch {
            Write-Warning "openenv validate failed in this environment. Run it on the submission machine after installing the official validator."
        }
    }
}
else {
    Write-Host "[3/4] Skipped OpenEnv validation."
}

if (-not $SkipDocker) {
    Write-Host "[4/4] Building Docker image..."
    $dockerCmd = Get-Command docker -ErrorAction SilentlyContinue
    if ($null -eq $dockerCmd) {
        Write-Warning "Docker is not installed. Install Docker Desktop and run docker build/docker run."
    }
    else {
        try {
            if ($env:DOCKER_API_VERSION) {
                Remove-Item Env:DOCKER_API_VERSION -ErrorAction SilentlyContinue
            }
            docker info | Out-Null
            docker build -t real-world-openenv .
            if ($LASTEXITCODE -ne 0) {
                throw "Docker build failed."
            }
            Write-Host "Running container on http://localhost:7860"
            docker run --rm -p 7860:7860 real-world-openenv
            if ($LASTEXITCODE -ne 0) {
                throw "Docker run failed."
            }
        }
        catch {
            Write-Warning "Docker daemon is not ready or build/run failed. Start Docker Desktop and rerun deploy.ps1."
        }
    }
}
else {
    Write-Host "[4/4] Skipped Docker build/run."
}

if (-not $SkipHF) {
    Write-Host "[5/5] Deploying Hugging Face Space..."
    if (-not $env:HF_TOKEN) {
        Write-Warning "HF_TOKEN is not set. Set HF_TOKEN then rerun deploy.ps1 (or run deploy_hf_space.py directly)."
    }
    else {
        try {
            & $pythonExe deploy_hf_space.py
            if ($LASTEXITCODE -ne 0) {
                throw "Hugging Face deployment failed."
            }
        }
        catch {
            Write-Warning "Hugging Face deployment failed. Verify HF_TOKEN permissions and network access, then rerun."
        }
    }
}
else {
    Write-Host "[5/5] Skipped Hugging Face deployment."
}
