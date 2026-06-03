<#
.SYNOPSIS
Builds and deploys the Travel Advisory System to AWS using AWS SAM.

.DESCRIPTION
This script first runs `sam build` to resolve dependencies and build the deployment package.
Then it runs `sam deploy --guided` to interactively deploy the stack to AWS.
During the guided deployment, it will prompt for the AWS Region and an optional NotificationEmail.
#>

$ErrorActionPreference = "Stop"

Write-Host "=============================================" -ForegroundColor Cyan
Write-Host " Building Travel Advisory System using SAM" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan

# Ensure we run the build from the project root (parent directory of this script)
$ProjectRoot = Split-Path -Path $PSScriptRoot -Parent
Set-Location -Path $ProjectRoot

# Bypass SAM Build strictness by installing dependencies directly to the folder
Write-Host "Installing dependencies directly to avoid version mismatch..." -ForegroundColor Yellow
pip install requests -t .

Write-Host ""
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host " Deploying to AWS" -ForegroundColor Cyan
Write-Host "=============================================" -ForegroundColor Cyan
Write-Host "You will be prompted for some parameters. You can accept the defaults for most." -ForegroundColor Yellow
Write-Host "When asked for 'NotificationEmail', enter your email if you want automatic alerts, or leave it blank." -ForegroundColor Yellow
Write-Host ""

# Run SAM Deploy Guided (this will package the directory as-is)
sam deploy --guided --resolve-s3

Write-Host ""
Write-Host "=============================================" -ForegroundColor Green
Write-Host " Deployment process finished." -ForegroundColor Green
Write-Host "=============================================" -ForegroundColor Green
