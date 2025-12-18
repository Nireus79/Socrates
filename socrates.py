#!/usr/bin/env python
"""
Socrates AI - Unified Entry Point

Serves as both a Python library and CLI application.

As a Library:
    >>> import socrates
    >>> config = socrates.SocratesConfig.from_env()
    >>> orchestrator = socrates.AgentOrchestrator(config)

As a CLI Application:
    python socrates.py                 # Start CLI (default)
    python socrates.py --api           # Start API server only
    python socrates.py --dev           # Start development environment (API + Frontend)
    python socrates.py --frontend      # Start CLI with React frontend
    python socrates.py --version       # Show version
    python socrates.py --help          # Show help
"""

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
import sys
import os
import socket
from pathlib import Path


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

    uvicorn.run(
        "socrates_api.main:app",
        host=host,
        port=port,
        reload=reload
    )


def start_dev() -> None:
    """Start development environment (API + Frontend)"""
    import subprocess
    import threading
    import time

    project_root = Path(__file__).parent

    # Auto-detect available ports
    api_port = _find_available_port(8000, "localhost")
    frontend_port = _find_available_port(5173, "localhost")

    def start_api_server():
        """Start API in background thread"""
        try:
            start_api(host="localhost", port=api_port, reload=True, auto_port=False)
        except Exception as e:
            print(f"[ERROR] API server failed: {e}")

    def start_frontend_server():
        """Start frontend in separate process"""
        frontend_dir = project_root / "socrates-frontend"
        if not frontend_dir.exists():
            print("[ERROR] Frontend directory not found at", frontend_dir)
            return

        try:
            # Install dependencies
            subprocess.run(["npm", "install"], cwd=frontend_dir, check=False)

            # Set frontend port via environment variable
            env = os.environ.copy()
            env["VITE_PORT"] = str(frontend_port)

            # Start dev server
            subprocess.run(["npm", "run", "dev"], cwd=frontend_dir, env=env)
        except Exception as e:
            print(f"[ERROR] Frontend server failed: {e}")

    # Display startup information
    print("[INFO] Development environment starting...")
    print(f"[INFO] API server will start on http://localhost:{api_port}")
    print(f"[INFO] Frontend will start on http://localhost:{frontend_port}")

    # Start API in background thread
    api_thread = threading.Thread(target=start_api_server, daemon=True)
    api_thread.start()

    time.sleep(2)  # Wait for API to start

    # Start frontend (blocks)
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
  python socrates.py --api                   Start API server (auto-detects port)
  python socrates.py --api --port 9000       Start API on port 9000 (auto-detects if busy)
  python socrates.py --api --no-auto-port    Start API on exact port (fails if busy)
  python socrates.py --dev                   Start development environment
  python socrates.py --frontend              Start CLI with React frontend
  python socrates.py --version               Show version

Port Detection:
  - By default, if a port is in use, the next available port is automatically selected
  - Use --no-auto-port to force the exact port (fails if in use)
  - Both API and dev modes support automatic port detection
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
        "--dev",
        action="store_true",
        help="Start development environment (API + Frontend)"
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
        elif args.dev:
            print("[INFO] Starting development environment (API + Frontend)")
            start_dev()
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
