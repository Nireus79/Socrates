#!/usr/bin/env python
"""
Development Mode Startup Script

Starts the entire Socrates system in development mode:
1. Backend API (FastAPI)
2. Frontend Dev Server (Vite)
3. Database (SQLite)
4. All services in parallel with proper signal handling

Usage:
    python scripts/start-dev.py

Stops with: Ctrl+C (graceful shutdown)
"""

import os
import sys
import subprocess
import signal
import time
from pathlib import Path

# Color output
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    CYAN = '\033[96m'
    END = '\033[0m'

def print_header(text):
    """Print formatted header"""
    print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BLUE}{text:^60}{Colors.END}")
    print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")

def print_status(component, status, details=""):
    """Print component status"""
    symbol = "[+]" if status == "starting" else "[!]"
    color = Colors.GREEN if status == "ok" else Colors.YELLOW
    print(f"{color}{symbol} {component:20} {status:15} {details}{Colors.END}")

def check_prerequisites():
    """Check if all prerequisites are installed"""
    print_header("Checking Prerequisites")

    requirements = {
        "Python 3.9+": ["python", "--version"],
        "pip": ["pip", "--version"],
        "Node.js": ["node", "--version"],
        "npm": ["npm.cmd" if os.name == 'nt' else "npm", "--version"],
    }

    all_ok = True
    missing_tools = []

    for tool, cmd in requirements.items():
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
            if result.returncode == 0:
                version = result.stdout.strip().split('\n')[0]
                print_status(tool, "ok", version)
            else:
                print_status(tool, "missing")
                all_ok = False
                missing_tools.append(tool)
        except Exception as e:
            print_status(tool, "missing")
            all_ok = False
            missing_tools.append(tool)

    if not all_ok:
        print(f"\n{Colors.RED}Some prerequisites are missing:{Colors.END}\n")

        if "Node.js" in missing_tools or "npm" in missing_tools:
            print(f"{Colors.YELLOW}[ERROR] Node.js & npm not found{Colors.END}")
            print(f"\n{Colors.CYAN}To install Node.js:{Colors.END}")
            print(f"  1. Visit: https://nodejs.org/")
            print(f"  2. Download: LTS version (14.x or higher)")
            print(f"  3. Run the installer")
            print(f"  4. Verify installation:")
            print(f"     node --version")
            print(f"     npm --version")
            print(f"  5. Then try again:")
            print(f"     python scripts/start-dev.py")

        if "Python 3.9+" in missing_tools:
            print(f"\n{Colors.YELLOW}[ERROR] Python 3.9+ not found{Colors.END}")
            print(f"\n{Colors.CYAN}To install Python:{Colors.END}")
            print(f"  1. Visit: https://www.python.org/")
            print(f"  2. Download: Python 3.9 or higher")
            print(f"  3. Run the installer (check 'Add Python to PATH')")
            print(f"  4. Verify: python --version")

        if "pip" in missing_tools:
            print(f"\n{Colors.YELLOW}[ERROR] pip not found{Colors.END}")
            print(f"\n{Colors.CYAN}pip comes with Python 3.4+{Colors.END}")
            print(f"  Reinstall Python and ensure pip is selected during install")

        print(f"\n{Colors.RED}Please install missing prerequisites and try again.{Colors.END}\n")
        return False

    print_status("All checks", "ok", "[OK]")
    return True

def install_dependencies():
    """Install Python and Node dependencies if needed"""
    print_header("Installing Dependencies")

    # Check if requirements installed
    try:
        import fastapi
        import uvicorn
        print_status("Python deps", "ok", "Already installed")
    except ImportError:
        print_status("Python deps", "starting", "Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-q", "-r", "requirements.txt"],
                      check=True)
        print_status("Python deps", "ok", "Installed")

    # Check if npm dependencies installed
    frontend_dir = Path("socrates-frontend")
    if frontend_dir.exists():
        node_modules = frontend_dir / "node_modules"
        if not node_modules.exists():
            print_status("Node deps", "starting", "Installing...")
            npm_cmd = "npm.cmd" if os.name == 'nt' else "npm"
            os.chdir(frontend_dir)
            subprocess.run([npm_cmd, "install", "-q"], check=True)
            os.chdir("..")
            print_status("Node deps", "ok", "Installed")
        else:
            print_status("Node deps", "ok", "Already installed")

class ProcessManager:
    """Manages subprocess lifecycle"""

    def __init__(self):
        self.processes = {}
        self.running = True

        # Handle signals
        signal.signal(signal.SIGINT, self.handle_shutdown)
        signal.signal(signal.SIGTERM, self.handle_shutdown)

    def handle_shutdown(self, signum, frame):
        """Graceful shutdown handler"""
        print(f"\n\n{Colors.YELLOW}Shutting down services...{Colors.END}\n")
        self.running = False
        self.stop_all()
        sys.exit(0)

    def start_process(self, name, command, cwd=None, env=None):
        """Start a subprocess"""
        try:
            print_status(name, "starting", f"Running: {' '.join(command)}")

            # Prepare environment
            process_env = os.environ.copy()
            if env:
                process_env.update(env)

            # Start process
            process = subprocess.Popen(
                command,
                cwd=cwd,
                env=process_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            self.processes[name] = process
            time.sleep(1)  # Give it a moment to start

            if process.poll() is None:
                print_status(name, "ok", f"PID {process.pid}")
                return True
            else:
                print_status(name, "error", "Failed to start")
                return False

        except Exception as e:
            print_status(name, "error", str(e))
            return False

    def stop_all(self):
        """Stop all processes gracefully"""
        for name, process in self.processes.items():
            if process and process.poll() is None:
                print_status(name, "stopping")
                try:
                    process.terminate()
                    try:
                        process.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        process.kill()
                    print_status(name, "stopped")
                except Exception as e:
                    print(f"{Colors.RED}Error stopping {name}: {e}{Colors.END}")

    def monitor(self):
        """Monitor processes and report if any crash"""
        while self.running:
            time.sleep(2)
            for name, process in self.processes.items():
                if process and process.poll() is not None:
                    print(f"\n{Colors.RED}✗ {name} crashed (exit code {process.returncode}){Colors.END}")
                    # Optionally restart
                    # self.restart_process(name)

def main():
    """Main startup orchestration"""

    # Get repo root
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent
    os.chdir(repo_root)

    print_header("Socrates AI - Development Startup")

    # Check prerequisites
    if not check_prerequisites():
        sys.exit(1)

    # Install dependencies
    install_dependencies()

    # Start services
    print_header("Starting Services")

    manager = ProcessManager()

    # 1. Backend API (FastAPI on port 8000)
    # Use the Python from the Socrates project's venv, not the currently active one
    venv_python = repo_root / ".venv" / ("Scripts" if os.name == 'nt' else "bin") / ("python.exe" if os.name == 'nt' else "python")
    if not venv_python.exists():
        venv_python = sys.executable  # Fallback if venv not found

    backend_env = os.environ.copy()
    # Set PYTHONPATH to include both the root and socrates-api/src
    pythonpath_parts = [
        str(repo_root),
        str(repo_root / "socrates-api" / "src")
    ]
    backend_env["PYTHONPATH"] = os.pathsep.join(pythonpath_parts)
    manager.start_process(
        "Backend API",
        [
            str(venv_python), "-m", "uvicorn",
            "socrates_api.main:app",
            "--host", "0.0.0.0",
            "--port", "8000",
            "--reload"
        ],
        cwd=repo_root,
        env=backend_env
    )

    # 2. Frontend Dev Server (Vite on port 5173)
    npm_cmd = "npm.cmd" if os.name == 'nt' else "npm"
    manager.start_process(
        "Frontend Dev",
        [npm_cmd, "run", "dev"],
        cwd=repo_root / "socrates-frontend",
        env={
            "VITE_API_URL": "http://localhost:8000"
        }
    )

    # Print access information
    print_header("System Ready")
    print(f"{Colors.GREEN}")
    print("Frontend:       http://localhost:5173")
    print("Backend API:    http://localhost:8000")
    print("API Docs:       http://localhost:8000/docs")
    print(f"{Colors.END}")
    print("Press Ctrl+C to stop all services\n")

    # Monitor processes
    manager.monitor()

if __name__ == "__main__":
    main()
