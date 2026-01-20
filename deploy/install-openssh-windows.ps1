# PowerShell script to install OpenSSH on Windows
# Run this as Administrator

Write-Host "Checking OpenSSH availability..." -ForegroundColor Green

# Check if already installed
$sshPath = Get-Command ssh -ErrorAction SilentlyContinue
if ($sshPath) {
    Write-Host "✓ OpenSSH is already installed at: $($sshPath.Source)" -ForegroundColor Green
    ssh -V
    exit 0
}

# For Windows 10/11 or Windows Server 2019+
Write-Host "Installing OpenSSH Client..." -ForegroundColor Yellow

# Method 1: Using Windows Capabilities (Windows 10 1809+ / Server 2019+)
$capability = Get-WindowsCapability -Online | Where-Object Name -like 'OpenSSH.Client*'

if ($capability) {
    if ($capability.State -eq 'Installed') {
        Write-Host "✓ OpenSSH Client is already installed" -ForegroundColor Green
    } else {
        Write-Host "Installing OpenSSH Client..." -ForegroundColor Yellow
        Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0
        Write-Host "✓ OpenSSH Client installed successfully" -ForegroundColor Green
    }
} else {
    Write-Host "OpenSSH capability not found. Trying alternative method..." -ForegroundColor Yellow
    
    # Method 2: Manual installation via Win32-OpenSSH
    Write-Host "Downloading Win32-OpenSSH..." -ForegroundColor Yellow
    $downloadUrl = "https://github.com/PowerShell/Win32-OpenSSH/releases/latest/download/OpenSSH-Win64.zip"
    $tempPath = "$env:TEMP\OpenSSH-Win64.zip"
    $installPath = "$env:ProgramFiles\OpenSSH"
    
    try {
        Invoke-WebRequest -Uri $downloadUrl -OutFile $tempPath -UseBasicParsing
        Expand-Archive -Path $tempPath -DestinationPath $installPath -Force
        Remove-Item $tempPath
        
        # Add to PATH
        $currentPath = [Environment]::GetEnvironmentVariable("Path", "Machine")
        if ($currentPath -notlike "*$installPath*") {
            [Environment]::SetEnvironmentVariable("Path", "$currentPath;$installPath", "Machine")
            $env:Path += ";$installPath"
        }
        
        Write-Host "✓ OpenSSH installed to $installPath" -ForegroundColor Green
        Write-Host "✓ Added to system PATH" -ForegroundColor Green
        Write-Host "Please restart PowerShell for changes to take effect." -ForegroundColor Yellow
    } catch {
        Write-Host "Error installing OpenSSH: $_" -ForegroundColor Red
        Write-Host "Please install manually from: https://github.com/PowerShell/Win32-OpenSSH/releases" -ForegroundColor Yellow
    }
}

# Verify installation
Start-Sleep -Seconds 2
$sshPath = Get-Command ssh -ErrorAction SilentlyContinue
if ($sshPath) {
    Write-Host "`n✓ SSH is now available!" -ForegroundColor Green
    ssh -V
} else {
    Write-Host "`n✗ SSH installation may require a PowerShell restart." -ForegroundColor Yellow
    Write-Host "Please restart PowerShell and run: ssh -V" -ForegroundColor Yellow
}
