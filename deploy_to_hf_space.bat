@echo off
REM Hugging Face Space Deployment Script for hackathon-openenv
REM Usage: deploy_to_hf_space.bat <YOUR_HF_TOKEN>

if "%1"=="" (
    echo.
    echo ERROR: HF_TOKEN not provided
    echo Usage: deploy_to_hf_space.bat YOUR_HF_TOKEN
    echo.
    echo How to get your HF_TOKEN:
    echo 1. Go to https://huggingface.co/settings/tokens
    echo 2. Create a new token with 'write' access
    echo 3. Copy the token and run this script with it
    echo.
    exit /b 1
)

setlocal enabledelayedexpansion
set HF_TOKEN=%1
set HF_SPACE=jakkireddyeswar/eswar
set HF_SPACE_URL=https://huggingface.co/spaces/!HF_SPACE!

echo.
echo ================================================
echo Deploying to Hugging Face Space
echo ================================================
echo Space ID: !HF_SPACE!
echo Space URL: !HF_SPACE_URL!
echo.

REM Ensure we're in the right directory
cd /d "%~dp0"

REM Run Python deployment script
python -c "
import os
os.environ['HF_TOKEN'] = '%HF_TOKEN%'
"

REM Now run the deployment
python deploy_hf_space.py

if errorlevel 1 (
    echo.
    echo ERROR: Deployment failed
    exit /b 1
)

echo.
echo ================================================
echo Deployment Complete!
echo ================================================
echo Your updated code is now live at:
echo !HF_SPACE_URL!
echo.
echo The HF Space will rebuild automatically with
echo the latest code from your GitHub repository.
echo.
echo Changes pushed:
echo - Fixed OpenAI API call (client.chat.completions.create)
echo - Fixed response parsing
echo - Added error handling
echo.
echo You can now resubmit at:
echo https://www.scaler.com/hackathons/openenv
echo.
