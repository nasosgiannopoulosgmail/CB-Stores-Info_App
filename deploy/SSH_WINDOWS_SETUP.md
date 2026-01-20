# SSH Setup for Windows

## Quick Install Options

### Option 1: Windows 10/11 or Server 2019+ (Built-in OpenSSH)

**Via PowerShell (Run as Administrator):**

```powershell
# Install OpenSSH Client
Add-WindowsCapability -Online -Name OpenSSH.Client~~~~0.0.1.0

# Verify installation
ssh -V
```

### Option 2: Windows Server 2016 or Older

**Download and Install Win32-OpenSSH:**

1. Download from: https://github.com/PowerShell/Win32-OpenSSH/releases/latest
2. Extract `OpenSSH-Win64.zip` to `C:\Program Files\OpenSSH`
3. Add to PATH:
   - System Properties → Environment Variables
   - Add `C:\Program Files\OpenSSH` to System PATH

**Or use the automated script:**
```powershell
# Run as Administrator
.\deploy\install-openssh-windows.ps1
```

### Option 3: Use PuTTY (GUI Tool)

1. Download from: https://www.putty.org/
2. Install and run
3. Connect to: `nasos@192.168.88.75` on port 22

### Option 4: Use Windows Terminal with OpenSSH

1. Install Windows Terminal from Microsoft Store
2. Install OpenSSH using Option 1 above
3. Use terminal to SSH

## After Installation

Once SSH is installed, connect to your VM:

```bash
ssh nasos@192.168.88.75
```

You'll be prompted for your password.

## Troubleshooting

### "ssh: command not found"
- SSH is not installed. Use one of the options above.

### "Connection refused"
- Check if SSH service is running on VM: `sudo systemctl status ssh`
- Check firewall: `sudo ufw status`

### "Permission denied"
- Verify username is correct: `nasos`
- Check password
- Ensure SSH service allows password authentication

### Windows Firewall Blocking
```powershell
# Allow SSH through Windows Firewall (if needed)
New-NetFirewallRule -DisplayName "OpenSSH-Server-In-TCP" -Direction Inbound -Protocol TCP -Action Allow -LocalPort 22
```

## Recommended Tools

### Windows Terminal (Best Experience)
- Microsoft Store: Windows Terminal
- Supports tabs, multiple sessions
- Better SSH experience

### PuTTY (Simple GUI)
- Classic Windows SSH client
- GUI interface
- SCP file transfer included

### VS Code Remote SSH Extension
- Code directly on remote server
- Integrated development experience
- Install extension: Remote - SSH

## Quick Test

After installation, test SSH:

```powershell
ssh nasos@192.168.88.75
```

If connection works, you'll see the login prompt.
