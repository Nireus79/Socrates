#!/usr/bin/env python3
"""
Local development setup script for Socrates AI.

Installs dependencies sequentially to avoid disk space issues on systems
with limited temp space. Torch and heavy ML libraries are installed first,
then other dependencies.

Usage:
    python setup_local.py

This script:
1. Creates a Python virtual environment (.venv)
2. Upgrades pip/setuptools/wheel
3. Installs torch sequentially (largest dependency)
4. Installs other ML dependencies (sentence-transformers, chromadb)
5. Installs Socrates with dev dependencies

Requirements:
- Python 3.8+
- ~5GB free disk space (for torch + CUDA libraries)
- Internet connection for PyPI downloads
"""

import subprocess
import sys
import os
import platform
from pathlib import Path


def run_command(cmd: list[str], description: str, check: bool = True) -> bool:
    """Run a shell command and handle errors gracefully."""
    print(f"\n{'='*60}")
    print(f"📦 {description}")
    print(f"{'='*60}")
    print(f"Running: {' '.join(cmd)}\n")

    try:
        result = subprocess.run(cmd, check=False)
        if result.returncode != 0 and check:
            print(f"\n❌ Failed: {description}")
            return False
        return True
    except Exception as e:
        print(f"\n❌ Error running command: {e}")
        return False


def main():
    """Main setup function."""
    print("\n" + "="*60)
    print("🎓 Socrates AI - Local Development Setup")
    print("="*60)
    print("\nThis script installs dependencies sequentially to avoid")
    print("disk space issues. It will take 10-15 minutes.\n")

    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ required")
        sys.exit(1)

    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}")
    print(f"✓ Platform: {platform.system()}")

    # Get the project root
    project_root = Path(__file__).parent.absolute()
    os.chdir(project_root)
    print(f"✓ Project root: {project_root}\n")

    # Determine venv path and pip executable
    venv_path = project_root / ".venv"
    if sys.platform == "win32":
        pip_executable = venv_path / "Scripts" / "pip"
    else:
        pip_executable = venv_path / "bin" / "pip"

    # Step 1: Create virtual environment
    if not venv_path.exists():
        if not run_command(
            [sys.executable, "-m", "venv", str(venv_path)],
            "Creating Python virtual environment",
        ):
            sys.exit(1)
    else:
        print(f"✓ Virtual environment already exists at {venv_path}")

    # Step 2: Upgrade pip, setuptools, wheel
    if not run_command(
        [str(pip_executable), "install", "--upgrade", "--no-cache-dir", "pip", "setuptools", "wheel"],
        "Upgrading pip, setuptools, and wheel",
    ):
        sys.exit(1)

    # Step 3: Install torch sequentially (CPU-only to save disk space)
    print("\n" + "="*60)
    print("🔥 Installing PyTorch (CPU-only, ~600MB)")
    print("="*60)
    print("\nNote: CPU-only torch is faster to install and sufficient for most")
    print("development. If you need GPU support, install separately:\n")
    print("  pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118\n")

    if not run_command(
        [
            str(pip_executable),
            "install",
            "--no-cache-dir",
            "torch",
            "torchvision",
            "torchaudio",
            "--index-url",
            "https://download.pytorch.org/whl/cpu",
        ],
        "Installing PyTorch (CPU-only)",
    ):
        sys.exit(1)

    # Step 4: Install ML dependencies
    if not run_command(
        [
            str(pip_executable),
            "install",
            "--no-cache-dir",
            "sentence-transformers>=3.0.0",
            "chromadb>=0.5.0",
        ],
        "Installing sentence-transformers and chromadb",
    ):
        sys.exit(1)

    # Step 5: Install Socrates with dev dependencies
    if not run_command(
        [str(pip_executable), "install", "--no-cache-dir", "-e", ".[dev]"],
        "Installing Socrates with dev dependencies",
    ):
        sys.exit(1)

    # Step 6: Verify installation
    print("\n" + "="*60)
    print("✅ Verifying installation")
    print("="*60 + "\n")

    verify_cmd = f"{pip_executable} list | grep -E 'torch|sentence-transformers|chromadb|socrates'"
    if sys.platform == "win32":
        verify_cmd = f"{pip_executable} list | findstr /R \"torch sentence-transformers chromadb socrates\""

    subprocess.run(verify_cmd, shell=True)

    print("\n" + "="*60)
    print("✅ Setup Complete!")
    print("="*60)
    print("\nNext steps:")
    print("1. Activate the virtual environment:")
    if sys.platform == "win32":
        print(f"   .venv\\Scripts\\activate")
    else:
        print(f"   source .venv/bin/activate")

    print("\n2. Run tests to verify everything works:")
    print("   pytest -m unit -q")

    print("\n3. Start development:")
    print("   - See CLAUDE.md for development commands")
    print("   - Or use Docker: docker compose up")

    print("\n📚 Documentation:")
    print("   - CLAUDE.md - Development guide")
    print("   - README.md - Project overview")
    print("   - docs/ - Architecture and guides\n")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Setup interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        sys.exit(1)
