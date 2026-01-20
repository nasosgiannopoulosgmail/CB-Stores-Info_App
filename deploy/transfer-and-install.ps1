# PowerShell script to transfer setup script to VM and run it
# Usage: .\transfer-and-install.ps1

$VM_IP = "192.168.88.75"
$VM_USER = "nasos"
$SCRIPT_PATH = "deploy\install-vm.sh"

Write-Host "Transferring setup script to VM..." -ForegroundColor Green

# Transfer the script using SCP (if available) or provide manual instructions
# Note: This requires SSH/SCP to be installed or use WinSCP

# For manual transfer, the user can:
# 1. Use WinSCP or similar tool
# 2. Copy the script content and paste it on the VM
# 3. Use git clone on the VM directly

Write-Host ""
Write-Host "Option 1: Manual Connection" -ForegroundColor Yellow
Write-Host "================================"
Write-Host "1. Connect to your VM:"
Write-Host "   ssh $VM_USER@$VM_IP" -ForegroundColor Cyan
Write-Host ""
Write-Host "2. Once connected, run:"
Write-Host "   mkdir -p ~/setup" -ForegroundColor Cyan
Write-Host "   cd ~/setup" -ForegroundColor Cyan
Write-Host "   git clone https://github.com/nasosgiannopoulosgmail/CB-Stores-Info_App.git ." -ForegroundColor Cyan
Write-Host "   chmod +x deploy/install-vm.sh" -ForegroundColor Cyan
Write-Host "   sudo ./deploy/install-vm.sh" -ForegroundColor Cyan
Write-Host ""

Write-Host "Option 2: Direct Installation Commands" -ForegroundColor Yellow
Write-Host "================================"
Write-Host "Connect via SSH and run these commands directly:"
Write-Host ""
$scriptContent = Get-Content $SCRIPT_PATH -Raw
Write-Host $scriptContent -ForegroundColor Gray
