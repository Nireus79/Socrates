# Windows Setup Guide - Socrates AI

Complete step-by-step guide for Windows users installing and running Socrates AI from the .exe file.

## Table of Contents

- [System Requirements](#system-requirements)
- [Installation](#installation)
- [First Run](#first-run)
- [Creating Shortcuts](#creating-shortcuts)
- [Windows-Specific Troubleshooting](#windows-specific-troubleshooting)
- [Uninstalling](#uninstalling)

---

## System Requirements

**Minimum Requirements:**
- Windows 10 or later (Windows 11 recommended)
- 4 GB RAM
- 500 MB free disk space
- Internet connection (for Claude API)

**Optional:**
- Modern web browser (Chrome, Edge, Firefox recommended)
- Administrator access for system-wide installation

---

## Installation

### Method 1: Automatic Installation (Recommended)

1. **Download the installer**
   - Download `socrates-installer.exe` from the releases page
   - Save to your Downloads folder

2. **Run the installer**
   - Double-click `socrates-installer.exe`
   - Windows may show a "Windows Defender SmartScreen" warning
     - Click "More info" → "Run anyway" (this is normal for new applications)

3. **Installation completes automatically**
   - The installer will:
     - Extract Socrates AI to `C:\Program Files\Socrates`
     - Create desktop shortcut "Socrates AI"
     - Create Start Menu entry
     - Launch Socrates AI automatically

4. **First time setup**
   - On first run, you'll see the Socrates AI banner and login prompt
   - Browser automatically opens to http://localhost:5173

### Method 2: Manual Installation

1. **Download the executable**
   - Download `socrates.exe` from the releases page
   - Save to a folder (e.g., `C:\Users\YourName\Socrates`)

2. **Set API Key (one-time only)**
   - Right-click on the folder where you saved `socrates.exe`
   - Select "Open PowerShell window here"
   - Run this command:
     ```powershell
     [Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "sk-ant-your-key-here", "User")
     ```
   - Replace `sk-ant-your-key-here` with your actual API key from https://console.anthropic.com

3. **Run Socrates AI**
   - Double-click `socrates.exe`
   - Wait 10-15 seconds for the application to start
   - Browser should automatically open

---

## First Run

### Initial Setup

1. **Browser opens automatically**
   - You'll see "Welcome to Socrates AI"
   - If not, manually go to: http://localhost:5173

2. **Login/Register**
   - Create a new account or login with existing credentials
   - Choose a username and strong password

3. **Create Your First Project**
   - Click "New Project"
   - Enter a project name (e.g., "My First Project")
   - Click "Create"

4. **Start the Socratic Dialogue**
   - You'll see the first phase: "Discovery"
   - Answer the system's guiding questions
   - Continue with /continue or click "Next Question"

### Understanding the Console Window

You'll see a black console window in addition to the browser:
- This shows system logs and debug information
- **Do NOT close this window** while using Socrates AI
- You can minimize it, but keep it running
- To exit: Close this window or press Ctrl+C

---

## Creating Shortcuts

### Desktop Shortcut (After Installation)

The installer creates this automatically. If you need to recreate it:

1. **Right-click on Desktop**
   - Select "New" → "Shortcut"

2. **Enter the target path**
   - For default installation: `C:\Program Files\Socrates\socrates.exe`
   - For custom location: `C:\path\to\socrates.exe`

3. **Name the shortcut**
   - Enter: "Socrates AI"
   - Click "Finish"

### Start Menu Pinning

1. **Press Windows key** and type "Socrates"
2. **Right-click** the Socrates AI result
3. **Select "Pin to Start"**

### Quick Launch Bar (Taskbar)

1. **Run Socrates AI** (click the shortcut)
2. **Right-click the Socrates AI icon** in the taskbar
3. **Select "Pin to taskbar"**
4. Now you can launch Socrates from the taskbar anytime

---

## Windows-Specific Troubleshooting

### Application Won't Start

**Problem**: Double-clicking socrates.exe does nothing

**Solutions**:

1. **Check API Key**
   ```powershell
   echo $env:ANTHROPIC_API_KEY
   ```
   Should show your key starting with `sk-ant-`. If empty:
   ```powershell
   [Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "sk-ant-your-key", "User")
   ```
   Then restart Windows or close/reopen all terminals.

2. **Run from Command Prompt**
   - Press Windows + R
   - Type: `powershell`
   - Run: `C:\path\to\socrates.exe`
   - This shows you the actual error message

3. **Check Windows Defender**
   - Windows Defender may be blocking execution
   - Open Windows Defender
   - Go to "Virus & threat protection" → "Manage settings"
   - Temporarily disable "Real-time protection" to test
   - If it works, add socrates.exe to exclusions

### Console Window Closes Immediately

**Problem**: Black window opens and closes quickly

**Causes**:
- Missing API key
- Corrupted installation
- Missing Python runtime (shouldn't happen with .exe)

**Solution**:
- Run from PowerShell to see the error:
  ```powershell
  cd "C:\path\to\socrates"
  .\socrates.exe
  ```

### Browser Won't Connect

**Problem**: Console window runs but browser shows "Cannot reach localhost"

**Solutions**:

1. **Wait longer**
   - Application takes 10-15 seconds to start
   - Wait and refresh the browser (F5)

2. **Manual browser access**
   - Open your browser
   - Go to: http://localhost:5173
   - If still nothing, check if port is in use:
     ```powershell
     netstat -ano | findstr :5173
     ```

3. **Check Firewall**
   - Windows Defender Firewall might be blocking port 5173
   - Open Windows Defender Firewall
   - Click "Allow an app through firewall"
   - Add python.exe or socrates.exe

4. **Try custom port**
   - Open PowerShell in the socrates folder
   - Run: `.\socrates.exe --api --port 9000`
   - Then open: http://localhost:9000

### High CPU/Memory Usage

**Problem**: Computer slows down significantly

**Solutions**:

1. **Reduce context length**
   ```powershell
   [Environment]::SetEnvironmentVariable("SOCRATES_MAX_CONTEXT", "4000", "User")
   ```
   Then restart the application.

2. **Use Haiku model (faster)**
   ```powershell
   [Environment]::SetEnvironmentVariable("CLAUDE_MODEL", "claude-haiku-4-5-20251001", "User")
   ```

3. **Disable debug logging**
   ```powershell
   [Environment]::SetEnvironmentVariable("SOCRATES_LOG_LEVEL", "WARNING", "User")
   ```

4. **Close other applications**
   - Free up RAM by closing browsers, IDEs, etc.

### "Port Already in Use" Error

**Problem**: Error message: "Port 5173 already in use"

**Solutions**:

1. **Check for other instances**
   - Task Manager (Ctrl+Shift+Esc)
   - Look for running `socrates.exe` or `python.exe`
   - End the process

2. **Or use a different port**
   - Open PowerShell in socrates folder
   - Run: `.\socrates.exe --api --port 9000 --frontend --port 9001`

### Network/API Key Errors

**Problem**: "401 Unauthorized" or "Connection timeout"

**Solutions**:

1. **Verify API key is valid**
   - Go to https://console.anthropic.com
   - Check if your key is active
   - Generate a new one if needed

2. **Check internet connection**
   - Try: `ping google.com`
   - Or test in browser: https://www.anthropic.com

3. **If behind corporate proxy**
   ```powershell
   [Environment]::SetEnvironmentVariable("HTTP_PROXY", "http://proxy:port", "User")
   [Environment]::SetEnvironmentVariable("HTTPS_PROXY", "https://proxy:port", "User")
   ```
   Then restart application.

### 401 Unauthorized in Browser

**Problem**: After login, API calls return 401

**Solutions**:

1. **Clear browser cache**
   - Chrome: Ctrl+Shift+Delete
   - Edge: Ctrl+Shift+Delete
   - Firefox: Ctrl+Shift+Delete
   - Select "All time" and clear

2. **Try incognito/private mode**
   - Sometimes browser cache causes issues
   - Open browser's incognito/private window
   - Go to http://localhost:5173 and login again

3. **Restart the application**
   - Close the console window (Ctrl+C)
   - Wait 5 seconds
   - Double-click socrates.exe again

### Database Errors

**Problem**: "Database is locked" or "Database corrupt"

**Solutions**:

1. **Locate data directory**
   - In PowerShell: `echo $env:SOCRATES_DATA_DIR`
   - If blank, it's at: `$env:USERPROFILE\.socrates`

2. **Backup your data**
   ```powershell
   cd $env:USERPROFILE\.socrates
   copy projects.db projects.db.backup
   ```

3. **For locked database**
   - Close all running instances of socrates.exe
   - Wait 10 seconds
   - Start again

4. **For corrupted database**
   - Delete `projects.db` (you have a backup!)
   - Restart Socrates
   - It will recreate the database

---

## Uninstalling

### Method 1: Control Panel

1. **Open Settings**
   - Press Windows + I
   - Go to "Apps" → "Apps & features"

2. **Find Socrates AI**
   - Scroll down and find "Socrates AI"
   - Click it and select "Uninstall"
   - Follow the prompts

3. **Optional: Clean up data**
   - Open File Explorer
   - Navigate to: `%USERPROFILE%\.socrates`
   - Delete this folder to remove all projects and data

### Method 2: Manual Deletion

1. **Stop the application**
   - Close Socrates AI completely

2. **Delete the folder**
   - Open File Explorer
   - Go to: `C:\Program Files\Socrates`
   - Right-click and "Delete"

3. **Remove shortcuts**
   - Right-click desktop shortcut → Delete
   - Right-click Start Menu shortcut → Delete

4. **Optional: Remove data**
   - Navigate to: `%USERPROFILE%\.socrates`
   - Delete the entire folder

---

## Environment Variables (Advanced)

You can customize Socrates behavior using environment variables:

```powershell
# View all Socrates variables
Get-ChildItem env: | findstr ANTHROPIC,SOCRATES,CLAUDE

# Set a variable (permanent)
[Environment]::SetEnvironmentVariable("VARIABLE_NAME", "value", "User")

# Unset a variable
[Environment]::RemoveEnvironmentVariable("VARIABLE_NAME", "User")
```

**Common Variables**:
- `ANTHROPIC_API_KEY` - Your Claude API key
- `CLAUDE_MODEL` - Which Claude model to use
- `SOCRATES_LOG_LEVEL` - DEBUG, INFO, WARNING, ERROR
- `SOCRATES_DATA_DIR` - Where to store data

---

## Getting Help

- **Can't find something?** Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **Configuration help?** See [CONFIGURATION.md](CONFIGURATION.md)
- **API issues?** Visit [API_REFERENCE.md](API_REFERENCE.md)
- **Report a bug?** Open an issue on [GitHub](https://github.com/Nireus79/Socrates/issues)

---

**Last Updated**: January 2026
**Version**: 1.3.0
