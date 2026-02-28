@echo off
echo ========================================
echo FarmIntel V1 - Quick Start Script
echo ========================================
echo.

REM Check if AWS CLI is installed
echo [1/5] Checking AWS CLI...
aws --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: AWS CLI not found!
    echo.
    echo Please install AWS CLI first:
    echo 1. Download: https://awscli.amazonaws.com/AWSCLIV2.msi
    echo 2. Run the installer
    echo 3. Restart this script
    echo.
    echo See INSTALL_AWS_CLI.md for detailed instructions.
    pause
    exit /b 1
)
echo ✓ AWS CLI installed
echo.

REM Check if SAM CLI is installed
echo [2/5] Checking SAM CLI...
sam --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: SAM CLI not found!
    echo.
    echo Installing SAM CLI...
    pip install aws-sam-cli
    if %errorlevel% neq 0 (
        echo ERROR: Failed to install SAM CLI
        pause
        exit /b 1
    )
)
echo ✓ SAM CLI installed
echo.

REM Check AWS credentials
echo [3/5] Checking AWS credentials...
aws sts get-caller-identity >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: AWS credentials not configured!
    echo.
    echo Please configure AWS CLI:
    echo.
    aws configure
    echo.
    echo You'll need:
    echo - AWS Access Key ID
    echo - AWS Secret Access Key
    echo - Region: ap-south-1
    echo - Output: json
    echo.
    echo See INSTALL_AWS_CLI.md for how to get access keys.
    pause
    exit /b 1
)
echo ✓ AWS credentials configured
echo.

REM Install Python dependencies
echo [4/5] Installing Python dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo WARNING: Some dependencies failed to install
    echo This might be okay - continuing...
)
echo ✓ Dependencies installed
echo.

REM Build SAM application
echo [5/5] Building SAM application...
sam build
if %errorlevel% neq 0 (
    echo ERROR: SAM build failed!
    echo.
    echo Check the error messages above.
    pause
    exit /b 1
)
echo ✓ Build successful
echo.

echo ========================================
echo Setup Complete! 🎉
echo ========================================
echo.
echo Next steps:
echo 1. Deploy: sam deploy --guided
echo 2. Follow the prompts
echo 3. Wait for deployment to complete
echo 4. Setup AWS Connect (see SETUP_GUIDE.md Step 5)
echo.
echo For detailed instructions, see SETUP_GUIDE.md
echo.
pause
