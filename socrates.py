#!/usr/bin/env python
"""
Socrates AI - Unified Entry Point

Serves as both a Python library and CLI application.

As a Library:
    # >>> import socrates
    # >>> config = socrates.SocratesConfig.from_env()
    # >>> orchestrator = socrates.AgentOrchestrator(config)

As a CLI Application:
    python socrates.py                 # Start CLI (default)
    python socrates.py --api           # Start API server only
    python socrates.py --dev           # Start development environment (API + Frontend)
    python socrates.py --frontend      # Start CLI with React frontend
    python socrates.py --version       # Show version
    python socrates.py --help          # Show help
"""

# ============================================================================
# Ensure LOCAL code is used, not installed package
# ============================================================================

import sys
from pathlib import Path

# Add current directory to path FIRST (before any socratic_system imports)
# This ensures we use the local code, not the installed package
_current_dir = Path(__file__).parent
if str(_current_dir) not in sys.path:
    sys.path.insert(0, str(_current_dir))

# ============================================================================
# Library Exports (for programmatic use)
# ============================================================================

__version__ = "0.6.6"

# Import orchestrator
from socratic_system.orchestration import AgentOrchestrator

# Import configuration
from socratic_system.config import SocratesConfig

# Import exceptions
try:
    from socratic_system.exceptions import SocratesError, ProjectNotFoundError
except ImportError:
    class SocratesError(Exception):
        """Base Socrates exception"""
        pass


    class ProjectNotFoundError(SocratesError):
        """Project not found exception"""
        pass

# Import events
try:
    from socratic_system.events.event_types import EventType
except ImportError:
    try:
        from socratic_system.events import EventType
    except ImportError:
        class EventType:
            PROJECT_CREATED = "project_created"
            CODE_GENERATED = "code_generated"
            AGENT_ERROR = "agent_error"

__all__ = [
    "__version__",
    "AgentOrchestrator",
    "SocratesConfig",
    "SocratesError",
    "ProjectNotFoundError",
    "EventType",
]

# ============================================================================
# CLI Application (for direct execution)
# ============================================================================

import argparse
import os
import socket


def _find_available_port(preferred_port: int = 8000, host: str = "0.0.0.0") -> int:
    """
    Find an available port starting from preferred_port.

    If the preferred port is in use, automatically finds the next available port.

    Args:
        preferred_port: Desired port number (default: 8000)
        host: Host to bind to (default: 0.0.0.0)

    Returns:
        An available port number
    """
    port = preferred_port
    max_attempts = 100

    for attempt in range(max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind((host, port))
                sock.close()
                return port
        except OSError:
            # Port is in use, try next one
            port += 1

    raise RuntimeError(
        f"Could not find an available port starting from {preferred_port}. "
        f"Tried ports {preferred_port} to {preferred_port + max_attempts}"
    )


def start_cli(with_frontend: bool = False) -> None:
    """
    Start CLI application

    Args:
        with_frontend: If True, also start React frontend alongside CLI
    """
    from socratic_system.ui.main_app import SocraticRAGSystem

    app = SocraticRAGSystem(start_frontend=with_frontend)
    app.start()


def start_api(host: str = "0.0.0.0", port: int = 8000, reload: bool = False, auto_port: bool = True) -> None:
    """
    Start API server

    Args:
        host: API server host (default: 0.0.0.0)
        port: API server port (default: 8000)
        reload: Enable auto-reload for development (default: False)
        auto_port: Auto-detect and use available port if preferred port is in use (default: True)
    """
    sys.path.insert(0, str(Path(__file__).parent))
    sys.path.insert(0, str(Path(__file__).parent / "socrates-api" / "src"))

    import uvicorn

    # Auto-detect available port if requested
    if auto_port:
        original_port = port
        port = _find_available_port(port, host)
        if port != original_port:
            print(f"[INFO] Port {original_port} is in use, using port {port} instead")
    else:
        # Still check port availability for user feedback
        try:
            _find_available_port(port, host)
        except RuntimeError:
            print(f"[ERROR] Port {port} is not available and auto-port is disabled")
            raise

    display_host = "localhost" if host == "0.0.0.0" else host
    print(f"[INFO] API server running on http://{display_host}:{port}")

    # Set development environment for local development
    os.environ['ENVIRONMENT'] = 'development'

    uvicorn.run(
        "socrates_api.main:app",
        host=host,
        port=port,
        reload=reload
    )


def start_full_stack() -> None:
    """Start complete Socrates stack (API + Frontend)"""
    import subprocess
    import threading
    import time
    import signal
    import requests
    import json
    import webbrowser

    project_root = Path(__file__).parent

    # Auto-detect available ports
    api_port = _find_available_port(8000, "localhost")
    frontend_port = _find_available_port(5173, "localhost")

    # Write port configuration to file for frontend discovery
    config_dir = project_root / "socrates-frontend" / "public"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "server-config.json"
    with open(config_file, "w") as f:
        json.dump({"api_url": f"http://localhost:{api_port}"}, f)

    print(f"[INFO] Wrote server config to {config_file}")

    # Store process references for cleanup
    processes = []
    api_ready = threading.Event()
    api_process = None
    browser_opened = threading.Event()

    def start_api_server_process():
        """Start API in separate subprocess (not thread)"""
        nonlocal api_process
        try:
            # Create subprocess for API server
            env = os.environ.copy()
            env['ENVIRONMENT'] = 'development'
            api_process = subprocess.Popen(
                [sys.executable, "-c", f"""
import sys
import os
os.environ['ENVIRONMENT'] = 'development'
sys.path.insert(0, r'{project_root}')
sys.path.insert(0, r'{project_root / "socrates-api" / "src"}')
print(f'[STARTUP] ENVIRONMENT={{os.getenv("ENVIRONMENT")}}', flush=True)
import uvicorn
uvicorn.run(
    'socrates_api.main:app',
    host='localhost',
    port={api_port},
    reload=False,
    access_log=True
)
"""],
                cwd=project_root,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            # Stream output
            if api_process.stdout:
                for line in api_process.stdout:
                    print(f"[API] {line.rstrip()}")

        except KeyboardInterrupt:
            pass
        except Exception as e:
            print(f"[ERROR] API server process failed: {e}")

    def wait_for_api(max_retries: int = 30, retry_delay: float = 1.0) -> bool:
        """Wait for API server to be ready"""
        print("[INFO] Waiting for API server to be ready...")
        for attempt in range(max_retries):
            try:
                response = requests.get(f"http://localhost:{api_port}/health", timeout=2)
                if response.status_code == 200:
                    print("[INFO] API server is ready!")
                    api_ready.set()
                    return True
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                if attempt < max_retries - 1:
                    print(f"[INFO] API not ready yet, waiting... ({attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)

        print("[ERROR] API server did not start in time")
        return False

    def wait_for_frontend_and_open_browser(max_retries: int = 30, retry_delay: float = 1.0) -> None:
        """Wait for frontend to be ready and open browser"""
        frontend_url = f"http://localhost:{frontend_port}"
        print(f"[INFO] Waiting for frontend to be ready at {frontend_url}...")

        for attempt in range(max_retries):
            try:
                response = requests.get(frontend_url, timeout=2)
                if response.status_code == 200:
                    print(f"[INFO] Frontend is ready! Opening browser...")
                    webbrowser.open(frontend_url)
                    browser_opened.set()
                    return
            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
                if attempt < max_retries - 1:
                    print(f"[INFO] Frontend not ready yet, waiting... ({attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)

        print("[WARN] Frontend did not start in time, but continuing...")

    def start_frontend_server():
        """Start frontend in separate process"""
        frontend_dir = project_root / "socrates-frontend"
        if not frontend_dir.exists():
            print("[ERROR] Frontend directory not found at", frontend_dir)
            return

        # Wait for API to be ready before starting frontend
        if not api_ready.wait(timeout=60):
            print("[ERROR] Frontend startup cancelled: API server failed to start")
            return

        try:
            # Ensure dependencies are installed
            print("[INFO] Installing frontend dependencies...")
            subprocess.run(
                ["npm", "install"],
                cwd=frontend_dir,
                check=False,
                capture_output=True
            )

            # Set frontend port via environment variable
            env = os.environ.copy()
            env["PORT"] = str(frontend_port)
            env["VITE_API_URL"] = f"http://localhost:{api_port}"

            print(f"[INFO] Starting frontend on port {frontend_port}...")
            # Start dev server
            proc = subprocess.Popen(
                ["npm", "run", "dev"],
                cwd=frontend_dir,
                env=env,
                stdout=None,
                stderr=None
            )
            processes.append(proc)

            # Start a thread to wait for frontend and open browser
            browser_thread = threading.Thread(
                target=wait_for_frontend_and_open_browser,
                daemon=True
            )
            browser_thread.start()

            proc.wait()  # Wait for process to finish
        except Exception as e:
            print(f"[ERROR] Frontend server failed: {e}")

    def signal_handler(sig, frame):
        """Handle Ctrl+C gracefully"""
        print("\n[INFO] Shutting down Socrates...")

        # Kill API process
        if api_process and api_process.poll() is None:
            try:
                api_process.terminate()
                api_process.wait(timeout=5)
            except Exception:
                try:
                    api_process.kill()
                except Exception:
                    pass

        # Kill frontend and other processes
        for proc in processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except Exception:
                try:
                    proc.kill()
                except Exception:
                    pass
        sys.exit(0)

    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)

    # Display startup information
    print("=" * 70)
    print("SOCRATES FULL STACK")
    print("=" * 70)
    print(f"[INFO] API server starting on http://localhost:{api_port}")
    print(f"[INFO] Frontend starting on http://localhost:{frontend_port}")
    print(f"[INFO] Press Ctrl+C to shutdown")
    print("=" * 70)

    # Start API in separate subprocess (not thread)
    api_thread = threading.Thread(target=start_api_server_process, daemon=True)
    api_thread.start()

    # Start health check in separate thread
    health_check_thread = threading.Thread(target=wait_for_api, daemon=True)
    health_check_thread.start()

    # Start frontend (blocks until user interrupts)
    start_frontend_server()


def main():
    """Main entry point with argument parsing"""
    parser = argparse.ArgumentParser(
        prog="socrates",
        description="Socrates AI - A Socratic method tutoring system powered by Claude AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python socrates.py                         Start CLI (default)
  python socrates.py --api                   Start API server only (auto-detects port)
  python socrates.py --api --port 9000       Start API on port 9000 (auto-detects if busy)
  python socrates.py --api --no-auto-port    Start API on exact port (fails if busy)
  python socrates.py --full                  Start full stack (API + Frontend)
  python socrates.py --frontend              Start CLI with React frontend
  python socrates.py --version               Show version

Port Detection:
  - By default, if a port is in use, the next available port is automatically selected
  - Use --no-auto-port to force the exact port (fails if in use)
  - Full stack and API modes support automatic port detection
        """
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"Socrates AI {__version__}"
    )

    # Mode selection (mutually exclusive)
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--api",
        action="store_true",
        help="Start API server only (default: localhost:8000)"
    )
    mode_group.add_argument(
        "--full",
        action="store_true",
        help="Start full stack (API + Frontend together)"
    )
    mode_group.add_argument(
        "--frontend",
        action="store_true",
        help="Start CLI with React frontend"
    )

    # API server options
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="API server host (default: 0.0.0.0)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="API server port (default: 8000)"
    )
    parser.add_argument(
        "--no-auto-port",
        action="store_true",
        help="Disable automatic port detection (fail if preferred port is in use)"
    )
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for API (development only)"
    )

    args = parser.parse_args()

    try:
        if args.api:
            auto_port = not args.no_auto_port
            start_api(
                host=args.host,
                port=args.port,
                reload=args.reload,
                auto_port=auto_port
            )
        elif args.full:
            start_full_stack()
        elif args.frontend:
            print("[INFO] Starting CLI with React frontend")
            start_cli(with_frontend=True)
        else:
            # Default: CLI only
            print("[INFO] Starting Socrates CLI")
            start_cli(with_frontend=False)

    except KeyboardInterrupt:
        print("\n[INFO] Shutdown requested")
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
