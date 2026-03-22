# Building Socrates.exe for Windows

This guide explains how to build the Windows executable and distribute it to users.

## Quick Start: Build in 3 Steps

### Step 1: Install Dependencies
```bash
pip install Pillow PyInstaller
```

### Step 2: Run the Build Script
```bash
python build_exe.py
```

### Step 3: Find Your Executable
```
dist/windows/socrates.exe  ← Ready to distribute!
```

That's it! The build script handles:
- Converting `logo.png` to `socrates.ico`
- Packaging Python runtime + all dependencies
- Creating installer script
- Embedding the icon

## What Gets Built

### Main Executable
- **`dist/windows/socrates.exe`** (~500-800 MB)
  - Fully self-contained Windows application
  - Includes Python runtime, all libraries, and dependencies
  - Logo embedded as icon
  - Launches in **FULL STACK mode by default** (API + Frontend + Browser)

### Support Scripts
- **`install_socrates.bat`** - Professional installer
  - Creates `C:\Program Files\Socrates` installation
  - Adds desktop shortcut with `--full` flag
  - Adds Start Menu shortcuts
  - Launches immediately after install

- **`launch_socrates.bat`** - Quick launcher (optional)
  - Simple batch script to launch with `--full` flag
  - Can be placed anywhere

### Configuration
- **`socrates.ico`** - Icon file (converted from logo.png)
- **`socrates_windows_entry.py`** - Wrapper that defaults to `--full`
- **`socrates_build.spec`** - PyInstaller configuration

## Default Behavior

When users double-click `socrates.exe`:
1. **Console window opens** (shows server logs and status)
2. Python runtime initializes (5-10 seconds first time)
3. Socrates launches in **FULL STACK mode** (`--full`)
4. API server starts on auto-detected localhost port
5. React frontend UI loads
6. Browser opens automatically with the interface

**Important:** The console window is intentionally visible so users can:
- See server status and activity logs
- Press **Ctrl+C** to gracefully shut down the application
- Prevent accidental background processes if only browser is closed

Users can still access other modes via command line:
```cmd
socrates.exe --api       # API server only
socrates.exe             # CLI only (no --full)
socrates.exe --frontend  # CLI with React frontend
```

## Console Window Design

**Why keep the console window visible?**

```
YES ✓ - Console window visible:
  • Users can see server status and logs
  • Users can press Ctrl+C for graceful shutdown
  • Clean termination of processes
  • No risk of orphaned background processes

NO ✗ - Hidden console (--windowed):
  • Browser closes but server keeps running
  • Users can't see what's happening
  • Only way to stop: Task Manager (force kill)
  • Risk of data loss from improper shutdown
```

The console window is intentional - it provides control and visibility.

## How the `--full` Default Works

### The Wrapper Script
`socrates_windows_entry.py` is the entry point for the exe:
```python
# If no explicit mode is specified, add --full automatically
if not has_explicit_mode:
    sys.argv.append("--full")
```

### PyInstaller Configuration
- `build_exe.py` uses `socrates_windows_entry.py` as the entry point
- `socrates_build.spec` references the wrapper script
- `console=True` keeps the console window visible
- When exe runs without args, wrapper adds `--full` automatically

## Distribution Package

Create a package for users:

```
socrates-v1.3.0-windows.zip
├── socrates.exe                    # Main executable
├── install_socrates.bat            # Professional installer
├── launch_socrates.bat             # Quick launcher
├── README_WINDOWS_PACKAGE.txt      # Quick reference
├── INSTALL_WINDOWS.md              # Detailed instructions
└── WINDOWS_DISTRIBUTION.md         # Advanced guide (optional)
```

### Create ZIP Distribution
```bash
# Using PowerShell
$files = @(
    'dist\windows\socrates.exe',
    'install_socrates.bat',
    'launch_socrates.bat',
    'README_WINDOWS_PACKAGE.txt',
    'INSTALL_WINDOWS.md'
)
Compress-Archive -Path $files -DestinationPath socrates-v1.3.0-windows.zip
```

### Upload Locations
- **GitHub Releases:**
  ```bash
  gh release create v1.3.0 dist/windows/socrates.exe
  ```

- **PyPI Alternative:**
  Users can still install via `pip install socrates-ai`

- **Website/Cloud Storage:**
  Direct download from your server

## Updating the Build

When you release a new version:

1. Update version in `pyproject.toml`
2. Rebuild: `python build_exe.py`
3. Test the exe on Windows
4. Create new distribution package
5. Upload to GitHub releases/website

## Troubleshooting Build Issues

### Issue: PyInstaller not found
```bash
pip install PyInstaller
```

### Issue: Pillow not found
```bash
pip install Pillow
```

### Issue: Build fails due to missing modules
Add to `build_exe.py` in `hiddenimports`:
```python
"--hidden-import=new_module_name",
```

### Issue: EXE won't start on target machine
- Ensure target has 64-bit Windows 7+
- Check antivirus isn't blocking the exe
- Verify 1+ GB free disk space

## Build Performance Notes

- **First build:** 10-15 minutes (fetches all dependencies)
- **Subsequent builds:** 5-10 minutes (cached)
- **Output size:** 500-800 MB (includes Python runtime)
- **Compression:** ZIP to ~200-300 MB, 7z to ~150 MB

## Optimization Options

### Reduce File Size
```python
# In build_exe.py, add UPX compression:
"--upx-dir=<path-to-upx>"

# Or use high compression in distribution:
7z a -t7z socrates.7z dist/windows/socrates.exe
```

### Faster Startup
Keep file at 500-800 MB - decompression overhead isn't worth the savings.

### Test Build Quality
```bash
# Test that dependencies load correctly
dist\windows\socrates.exe --help
dist\windows\socrates.exe --version
```

## Environment Variables

Users may need to set for full functionality:

```cmd
set ANTHROPIC_API_KEY=sk-...
set DATABASE_URL=postgresql://...
set REDIS_URL=redis://...
```

These can be set in:
- System environment variables
- `.env` file in working directory
- Command line before launching exe

## Security Considerations

### Code Signing (Production Recommended)
```bash
# Sign the executable to reduce antivirus warnings
signtool sign /f certificate.pfx /p password socrates.exe
```

### Distribution Security
- Always provide SHA-256 checksums
- Host on HTTPS-only servers
- Consider scanning with VirusTotal before release

### User Trust
- Host on official channels (GitHub, website)
- Provide clear documentation
- Consider adding publisher info to installer

## Rollback Procedure

If there's an issue with a release:

1. Keep previous `socrates.exe` builds
2. Tag failing release as broken in GitHub
3. Revert to previous exe
4. Redistribute from previous tag

## Platform-Specific Testing

Test the exe on:
- Windows 7 64-bit (minimum)
- Windows 10 64-bit (common)
- Windows 11 64-bit (current)

### Test Scenarios
1. Fresh user (first install)
2. Update (replacing existing exe)
3. Network interruption (API startup)
4. Admin/non-admin launch
5. Custom port collision

## Continuous Integration

For automated builds, add to CI/CD:

```yaml
- name: Build Windows Exe
  if: matrix.os == 'windows-latest'
  run: |
    pip install Pillow PyInstaller
    python build_exe.py

- name: Upload Release
  uses: actions/upload-artifact@v3
  with:
    name: socrates-windows
    path: dist/windows/socrates.exe
```

## Next Steps

1. ✅ Run `python build_exe.py` to create the executable
2. ✅ Test the exe thoroughly
3. ✅ Create distribution package (ZIP or installer)
4. ✅ Upload to GitHub releases or your server
5. ✅ Update user documentation with download link
6. ✅ Monitor for user feedback and issues

## Support

For build issues:
- Check PyInstaller documentation: https://pyinstaller.readthedocs.io/
- Review build_exe.py comments
- Check GitHub issues for similar problems

For user distribution help:
- See WINDOWS_DISTRIBUTION.md for detailed distribution options
- See INSTALL_WINDOWS.md for end-user installation guide
