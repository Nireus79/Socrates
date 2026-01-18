# Socrates AI - Windows Distribution Guide

This guide explains how to build and distribute the `socrates.exe` executable for Windows users.

## Quick Start for Building

### Prerequisites
- Python 3.8 or higher
- Pillow (`pip install Pillow`)
- PyInstaller (installed automatically by the build script)

### Build the Executable

```bash
python build_exe.py
```

This script will:
1. Convert `logo.png` to `socrates.ico`
2. Build `socrates.exe` using PyInstaller
3. Create an installer batch script

The resulting executable will be in: `dist/windows/socrates.exe`

## Distribution Package Contents

When distributing to users, include:

```
socrates-windows/
├── socrates.exe                 # Main executable (with embedded logo)
├── README.md                    # Quick start guide
├── install_socrates.bat         # Optional installer script
└── REQUIREMENTS.txt             # System requirements (optional)
```

### System Requirements

Users need:
- Windows 7 or later (64-bit recommended)
- 2 GB RAM minimum
- 1 GB free disk space
- Internet connection for API features

## Installation Methods

### Method 1: Direct Execution (Simplest)

Users can simply double-click `socrates.exe` to launch the application.

### Method 2: Using Installer Batch Script

Users can run `install_socrates.bat` which will:
- Create an installation directory in `Program Files\Socrates`
- Copy the executable
- Create a desktop shortcut
- Add to Start Menu (optional)

**Note:** Requires administrator privileges on some Windows systems.

### Method 3: Command Line

Users can run from Command Prompt or PowerShell:

```cmd
socrates.exe
```

## Packaging for Distribution

### Option 1: ZIP Archive
```bash
# Create a distributable ZIP
mkdir socrates-windows
copy dist\windows\socrates.exe socrates-windows\
copy install_socrates.bat socrates-windows\
copy README.md socrates-windows\QUICKSTART.md
Compress-Archive -Path socrates-windows -DestinationPath socrates-v1.3.0-windows.zip
```

### Option 2: Self-Extracting Archive
Use a tool like 7-Zip to create a self-extracting archive:
```bash
7z a socrates-v1.3.0-windows.exe socrates-windows\*
```

### Option 3: Professional Installer
For a professional installer, use:
- **InnoSetup** (free, highly recommended)
- **NSIS** (free, lightweight)
- **Advanced Installer** (commercial, feature-rich)

#### Example InnoSetup Script
Create `socrates_installer.iss`:
```ini
[Setup]
AppName=Socrates AI
AppVersion=1.3.0
DefaultDirName={pf}\Socrates
DefaultGroupName=Socrates AI
OutputDir=dist\installers
OutputBaseFilename=socrates-1.3.0-setup
SetupIconFile=socrates.ico

[Files]
Source: "dist\windows\socrates.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{commondesktop}\Socrates AI"; Filename: "{app}\socrates.exe"
Name: "{group}\Socrates AI"; Filename: "{app}\socrates.exe"

[Run]
Filename: "{app}\socrates.exe"; Description: "Launch Socrates"; Flags: postinstall skipifsilent
```

## Building for Different Python Versions

If you need to support multiple Python versions:

```bash
# Test with different Python versions
py -3.8 build_exe.py
py -3.9 build_exe.py
py -3.10 build_exe.py
py -3.11 build_exe.py
py -3.12 build_exe.py
```

## Troubleshooting

### Issue: "socrates.exe has stopped working"
**Solution:** Ensure all dependencies are installed. Run the build script's hidden imports verification.

### Issue: Missing dependencies at runtime
**Solution:** Add more `--collect-all` or `--hidden-import` flags in `build_exe.py`

### Issue: Antivirus flags the executable
**Solution:** This is normal for PyInstaller executables. It's a false positive. Sign the executable with a code signing certificate for production distribution.

### Issue: Large file size
**Solution:** Expected - includes Python runtime and all dependencies (~400-800 MB). Consider:
- Using UPX compression (slower startup, smaller file)
- Distributing as 7z with high compression
- Providing both standalone and installer versions

## Adding Digital Signature (Optional but Recommended)

To reduce antivirus false positives:

```bash
# Using Windows signtool (requires code signing certificate)
signtool sign /f certificate.pfx /p password /t http://timestamp.server.com socrates.exe
```

## Updating the Executable

When releasing a new version:

1. Update version in `pyproject.toml`
2. Rebuild the executable: `python build_exe.py`
3. Test thoroughly on Windows 7, 10, and 11
4. Create new distribution package with version number
5. Update release notes

## Distribution Channels

### GitHub Releases
```bash
# Create a GitHub release with the executable
gh release create v1.3.0 dist/windows/socrates.exe
```

### PyPI (Alternative)
Users can still install via pip:
```bash
pip install socrates-ai
```

Then run via:
```bash
python -m socratic_system
```

### Direct Download Website
Host on your website or cloud storage (AWS S3, Google Cloud Storage, etc.)

## Performance Notes

- First launch: 2-5 seconds (Python runtime initialization)
- Subsequent launches: 1-2 seconds
- Memory usage: 150-300 MB at startup
- With dependencies loaded: 500-1000 MB

## Security Considerations

1. **Code Signing:** Sign the executable with your certificate
2. **Checksum Verification:** Provide SHA-256 checksums for downloads
3. **Virus Scanning:** Scan with multiple AV engines before release
4. **Dependency Updates:** Keep dependencies current for security patches
5. **Auto-Update:** Consider implementing automatic updates

## Support Resources

- **Documentation:** https://github.com/Nireus79/Socrates/tree/master/docs
- **Issues:** https://github.com/Nireus79/Socrates/issues
- **PyPI:** https://pypi.org/project/socrates-ai/

## License

Socrates AI is released under the MIT License. The Windows executable includes all open-source dependencies with their respective licenses.
