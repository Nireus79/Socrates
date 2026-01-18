# Socrates AI - Windows Installation Guide

Welcome! This guide will help you install and run Socrates AI on your Windows computer.

## System Requirements

- **OS:** Windows 7 or later (Windows 10/11 recommended)
- **Architecture:** 64-bit
- **RAM:** 2 GB minimum (4 GB recommended)
- **Disk Space:** 1 GB free
- **Internet:** Required for API features

## Installation Options

### Option 1: Quick Launch (Easiest)

Simply double-click `socrates.exe` to start using Socrates immediately. No installation required!

**What you get:**
- Full stack mode: API Server + React Frontend + Browser
- API runs on localhost (auto-detects available port)
- Frontend UI opens automatically in your default browser
- Press Ctrl+C in console to stop

**First Launch:** The application may take 5-10 seconds to start on first run as it initializes all components.

### Option 2: Installer Script

If you want to install Socrates to your computer:

1. Right-click `install_socrates.bat`
2. Select "Run as administrator"
3. Follow the prompts
4. Desktop and Start Menu shortcuts will be created

**What you get:**
- Installation in `C:\Program Files\Socrates`
- Desktop shortcut (launches full stack: API + Frontend + Browser)
- Start Menu shortcut under Programs > Socrates
- Desktop shortcut launches Socrates immediately with `--full` flag

**Benefits:**
- Professional installation location
- Easy access from Start Menu and Desktop
- Easier to manage and uninstall
- Automatic browser launch on startup

### Option 3: Manual Installation

1. Create a folder: `C:\Program Files\Socrates`
2. Copy `socrates.exe` to this folder
3. Create a desktop shortcut manually:
   - Right-click desktop → New → Shortcut
   - Target: `C:\Program Files\Socrates\socrates.exe`
   - Arguments: `--full` (to launch with frontend)

## Running Socrates

### Default Launch (Recommended)

**Double-click** `socrates.exe` or the desktop shortcut

This launches with `--full` flag:
- API Server on localhost
- React Frontend UI
- Browser opens automatically with the interface

### Command Line Launch

Open Command Prompt or PowerShell:

**Full Stack (Default - Recommended):**
```cmd
socrates.exe --full
```
- Starts API + Frontend + opens browser

**API Server Only:**
```cmd
socrates.exe --api
```
- Just the REST API server (useful for development)

**CLI Mode:**
```cmd
socrates.exe
```
- Text-based CLI interface (no frontend)

**With Custom Port:**
```cmd
socrates.exe --full --port 9000
```
- Runs on custom port (auto-detects if busy)

If installed via installer:
```cmd
"C:\Program Files\Socrates\socrates.exe" --full
```

## Understanding the Console Window

When you launch Socrates, a **console (terminal) window** will appear. This is **normal and necessary**:

```
========================================
SOCRATES FULL STACK
========================================
[INFO] API server starting on http://localhost:8000
[INFO] Frontend starting on http://localhost:5173
[INFO] Press Ctrl+C to shutdown
========================================
[API] Application startup complete
...
```

**This console window shows:**
- API server startup messages
- Frontend status
- Live activity logs
- Instructions to stop the program

**Keep the console window open** while using Socrates. A browser window will open in front of it.

## Stopping Socrates

**Proper way to stop (Recommended):**
1. Keep the console window visible
2. Press **Ctrl+C** in the console
3. Wait for graceful shutdown (5-10 seconds)

```
[INFO] Shutting down Socrates...
✓ Processes terminated cleanly
```

**DO NOT:**
- ❌ Kill the console window without Ctrl+C (data loss risk)
- ❌ Force close via Task Manager (data loss risk)
- ❌ Close only the browser (server keeps running)

## First-Time Setup

On first launch, you may need to:

1. **Configure API Keys:** Set up your Anthropic Claude API key if using AI features
2. **Initialize Database:** The app will create necessary configuration files
3. **Review Settings:** Customize preferences in the settings menu

## Troubleshooting

### Issue: Application won't start

**Solution 1:** Ensure you're using Windows 7 or later
```cmd
winver  # Check your Windows version
```

**Solution 2:** Check if .NET Framework is installed (for some dependencies)

**Solution 3:** Run from Command Prompt to see detailed error messages
```cmd
socrates.exe --verbose
```

### Issue: "socrates.exe has stopped working"

**Solution:**
- Close the application
- Try running as administrator (right-click → Run as administrator)
- Check available disk space (need at least 1 GB free)

### Issue: "This app can't run on your PC"

**Solution:** You need a 64-bit version of Windows
- Right-click `socrates.exe` → Properties
- Verify it says "64-bit" or contact support

### Issue: Windows Defender warning

**Solution:** This is a false positive for packaged Python applications. Click "Run anyway"
- The application is code-signed (if available) and safe to run
- If you don't trust it, scan with your antivirus first

## Configuration

### API Key Setup

To use Socrates with Claude AI:

1. Get your API key from: https://console.anthropic.com
2. Set environment variable or configure in settings:
   ```cmd
   set ANTHROPIC_API_KEY=your-key-here
   socrates.exe
   ```

### Configuration Files

Socrates stores config in:
```
C:\Users\[YourUsername]\AppData\Local\Socrates\
```

### Enable Verbose Logging

For debugging:
```cmd
socrates.exe --verbose --log-level debug
```

## Updating Socrates

To get the latest version:

1. Download the new `socrates.exe`
2. Replace the old version
3. No configuration data will be lost

**Keeping Backups:**
```cmd
# Backup your configuration before updating
xcopy "%APPDATA%\Local\Socrates" "%APPDATA%\Local\Socrates_backup" /E /I
```

## Uninstalling Socrates

### If installed via installer:
1. Open Settings → Apps → Apps & Features
2. Find "Socrates AI"
3. Click → Uninstall

### If using standalone executable:
1. Delete `socrates.exe`
2. Delete desktop shortcut

**Configuration data remains:** To completely remove, also delete:
```
C:\Users\[YourUsername]\AppData\Local\Socrates\
```

## Getting Help

- **Documentation:** Check the included documentation folder
- **Issues:** Report bugs: https://github.com/Nireus79/Socrates/issues
- **Community:** Join discussions on GitHub

## Advanced Usage

### Command Line Arguments

```cmd
socrates.exe --help           # Show all available options
socrates.exe --api            # Run as API server
socrates.exe --dev            # Development mode
socrates.exe --config file    # Use custom config file
```

### Running Multiple Instances

You can run multiple instances of Socrates if needed:
```cmd
socrates.exe --port 8001
socrates.exe --port 8002
```

### Batch Processing

For automated tasks:
```cmd
socrates.exe --batch --input file.json --output results.json
```

## Performance Tips

- **First Launch:** 2-5 seconds (initializes Python runtime)
- **Memory Usage:** 150-300 MB typical
- **With Full Features:** 500-1000 MB possible

**Optimization:**
- Close other applications when running resource-heavy tasks
- Use SSD for faster file operations
- Ensure sufficient disk space for caching

## Privacy & Security

- Socrates AI stores data locally on your computer
- API calls are made to Anthropic (Claude AI)
- Review privacy policy before enabling cloud features
- Use strong passwords for any saved credentials

## FAQ

**Q: Is Socrates AI free?**
A: The application is free. API usage (Claude) may have associated costs.

**Q: Can I run Socrates without internet?**
A: Yes, but some AI features require an internet connection and API key.

**Q: Is it safe to run .exe files?**
A: This .exe is built from open-source code. You can review the source at:
   https://github.com/Nireus79/Socrates

**Q: Can I run this on Mac/Linux?**
A: Install using Python and pip:
   ```bash
   pip install socrates-ai
   ```

**Q: How do I update to a new version?**
A: Simply download and run the new `.exe` - your settings are preserved.

## Support

For additional help, visit:
- GitHub Repository: https://github.com/Nireus79/Socrates
- Documentation: https://github.com/Nireus79/Socrates/tree/master/docs
- Bug Reports: https://github.com/Nireus79/Socrates/issues

---

**Version:** 1.3.0
**Last Updated:** 2026-01-18
**License:** MIT
