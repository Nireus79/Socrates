#!/usr/bin/env python3
"""
Build script to create socrates.exe for Windows using PyInstaller.
This script converts the logo PNG to ICO and builds the executable.
"""

import os
import sys
import subprocess
from pathlib import Path
from PIL import Image


def convert_png_to_ico():
    """Convert logo.png to an ICO file for the Windows executable."""
    logo_path = Path("logo.png")
    ico_path = Path("socrates.ico")

    if not logo_path.exists():
        print(f"Error: {logo_path} not found!")
        return False

    print(f"Converting {logo_path} to {ico_path}...")

    try:
        # Open the PNG image
        img = Image.open(logo_path)

        # Resize to standard icon sizes and convert to RGB
        # Windows icons typically use 256x256 as the largest size
        img_rgb = img.convert("RGB")
        img_resized = img_rgb.resize((256, 256), Image.Resampling.LANCZOS)

        # Save as ICO file
        img_resized.save(ico_path, format="ICO")
        print(f"[OK] Successfully created {ico_path}")
        return True
    except Exception as e:
        print(f"Error converting PNG to ICO: {e}")
        return False


def build_executable():
    """Build the socrates.exe using PyInstaller."""

    # Check if PyInstaller is installed
    try:
        import PyInstaller
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "PyInstaller"])

    ico_path = Path("socrates.ico")
    spec_file = Path("socrates.spec")

    if not ico_path.exists():
        print(f"Error: {ico_path} not found! Run icon conversion first.")
        return False

    print("\nBuilding socrates.exe with PyInstaller...")
    print("This may take a few minutes...\n")

    try:
        # Use the Windows entry point wrapper that defaults to --full mode
        entry_point = "socrates_windows_entry.py"
        print(f"Using entry point: {entry_point} (defaults to --full mode)")

        pyinstaller_cmd = [
            sys.executable, "-m", "PyInstaller",
            f"--name=socrates",
            f"--icon={ico_path}",
            "--onefile",
            # NOTE: NOT using --windowed so console stays visible
            # This allows users to press Ctrl+C to cleanly shut down the server
            # If console is hidden, users would need Task Manager to stop the program
            "--distpath=dist/windows",
            "--workpath=build",
            "--specpath=.",
            "--collect-all=socratic_system",
            "--collect-all=anthropic",
            "--collect-all=chromadb",
            "--hidden-import=socratic_system",
            "--hidden-import=socratic_system.agents",
            "--hidden-import=socratic_system.clients",
            "--hidden-import=socratic_system.database",
            "--hidden-import=socratic_system.models",
            "--hidden-import=socratic_system.orchestration",
            entry_point,
        ]

        result = subprocess.run(pyinstaller_cmd, check=True)

        exe_path = Path("dist/windows/socrates.exe")
        if exe_path.exists():
            file_size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"\n✓ Successfully built {exe_path} ({file_size_mb:.1f} MB)")
            return True
        else:
            print(f"Error: Expected executable not found at {exe_path}")
            return False

    except subprocess.CalledProcessError as e:
        print(f"Error building executable: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


def create_installer_script():
    """Create a simple installer batch script."""
    installer_content = '''@echo off
REM Socrates AI - Windows Installer
REM This batch script helps users install Socrates locally

echo.
echo ========================================
echo Socrates AI - Windows Installer
echo ========================================
echo.

REM Check if the executable exists
if not exist "socrates.exe" (
    echo Error: socrates.exe not found in the current directory!
    echo Please ensure socrates.exe is in the same folder as this installer.
    pause
    exit /b 1
)

REM Create installation directory
set INSTALL_DIR=%PROGRAMFILES%\\Socrates
echo Installing Socrates to: %INSTALL_DIR%
mkdir "%INSTALL_DIR%" 2>nul

REM Copy executable
echo Copying files...
copy /Y "socrates.exe" "%INSTALL_DIR%\\" >nul 2>&1

REM Create desktop shortcut with --full argument (launches API + Frontend + Browser)
echo Creating desktop shortcut...
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%USERPROFILE%\\Desktop\\Socrates.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\\socrates.exe'; $Shortcut.Arguments = '--full'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.Save()"

REM Create Start Menu shortcut
echo Creating Start Menu shortcut...
set START_MENU=%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs
if not exist "%START_MENU%\\Socrates" mkdir "%START_MENU%\\Socrates" 2>nul
powershell -Command "$WshShell = New-Object -ComObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Socrates\\Socrates.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\\socrates.exe'; $Shortcut.Arguments = '--full'; $Shortcut.WorkingDirectory = '%INSTALL_DIR%'; $Shortcut.IconLocation = '%INSTALL_DIR%\\socrates.exe'; $Shortcut.Save()"

echo.
echo ✓ Installation complete!
echo.
echo Socrates has been installed to: %INSTALL_DIR%
echo.
echo Shortcuts created:
echo   • Desktop: Socrates shortcut
echo   • Start Menu: Programs ^> Socrates ^> Socrates
echo.
echo Launching Socrates with full stack (API + Frontend)...
echo Press Ctrl+C in the console to stop the server.
echo A browser window will open automatically.
echo.
"%INSTALL_DIR%\\socrates.exe" --full
'''

    installer_path = Path("install_socrates.bat")
    installer_path.write_text(installer_content)
    print(f"[OK] Created {installer_path}")


def main():
    print("Socrates AI - Windows EXE Build Script")
    print("=" * 50)
    print()

    # Step 1: Convert PNG to ICO
    if not convert_png_to_ico():
        sys.exit(1)

    # Step 2: Build executable
    if not build_executable():
        sys.exit(1)

    # Step 3: Create installer script
    print("\nCreating installer script...")
    create_installer_script()

    print("\n" + "=" * 50)
    print("Build complete!")
    print("=" * 50)
    print("\nDistribution files:")
    print("  - dist/windows/socrates.exe")
    print("    Launches with --full flag (API + Frontend + Browser)")
    print("  - install_socrates.bat")
    print("    Creates desktop/Start Menu shortcuts with --full flag")
    print("  - launch_socrates.bat")
    print("    Convenient launcher script (optional)")
    print("\nDefaults:")
    print("  • Double-click socrates.exe → Full stack mode (--full)")
    print("  • Desktop shortcut → Full stack mode (--full)")
    print("  • With --api flag → API server only")
    print("  • With no args → CLI mode")
    print("\nTo distribute:")
    print("  1. Archive dist/windows/socrates.exe")
    print("  2. Include: install_socrates.bat, launch_socrates.bat")
    print("  3. Include: INSTALL_WINDOWS.md, README_WINDOWS_PACKAGE.txt")
    print("  4. Include: WINDOWS_DISTRIBUTION.md (for advanced users)")
    print()


if __name__ == "__main__":
    main()
