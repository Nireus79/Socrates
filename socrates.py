#!/usr/bin/env python3
"""
Socrates AI - Unified Entry Point

Integrates CLI, API, and Frontend into a single executable.

Usage:
    python socrates.py                 # Start CLI (default)
    python socrates.py --api           # Start API server only
    python socrates.py --full          # Start full stack (API + Frontend)
    python socrates.py --version       # Show version
"""

import argparse
import os
import signal
import socket
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path
from typing import Optional

__version__ = "1.0.0"

# Ensure LOCAL code is used, not installed package
_current_dir = Path(__file__).parent
if str(_current_dir) not in sys.path:
    sys.path.insert(0, str(_current_dir))

# Add socrates-api/src to path
_api_src_dir = _current_dir / "socrates-api" / "src"
if str(_api_src_dir) not in sys.path:
    sys.path.insert(0, str(_api_src_dir))


def _find_available_port(preferred_port: int = 8000, host: str = "localhost") -> int:
    """Find an available port starting from preferred_port."""
    port = preferred_port
    max_attempts = 100

    for _attempt in range(max_attempts):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind((host, port))
                sock.close()
                return port
        except OSError:
            port += 1

    raise RuntimeError(f"Could not find available port from {preferred_port} to {preferred_port + max_attempts}")


def start_cli() -> None:
    """Start the CLI application."""
    try:
        from socratic_system.ui.main_app import SocraticRAGSystem
        app = SocraticRAGSystem(start_frontend=False)
        app.start()
    except ImportError as e:
        print(f"[ERROR] Failed to import CLI: {e}")
        print("[ERROR] Make sure socratic_system is properly installed")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] CLI failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def start_api(host: str = "127.0.0.1", port: int = 8000, reload: bool = False, auto_port: bool = True) -> None:
    """Start the REST API server."""
    try:
        from socrates_api.main import run as run_api

        # Auto-detect available port if requested
        if auto_port:
            original_port = port
            port = _find_available_port(port, host)
            if port != original_port:
                print(f"[INFO] Port {original_port} is in use, using port {port} instead")

        display_host = "localhost" if host in ("127.0.0.1", "0.0.0.0") else host
        print(f"[INFO] Starting API server on http://{display_host}:{port}")

        # Set environment variables for API
        os.environ['SOCRATES_API_HOST'] = host
        os.environ['SOCRATES_API_PORT'] = str(port)
        os.environ['SOCRATES_API_RELOAD'] = "true" if reload else "false"

        # Run the API
        run_api()

    except ImportError as e:
        print(f"[ERROR] Failed to import API: {e}")
        print("[ERROR] Make sure socrates_api is properly installed")
        sys.exit(1)
    except Exception as e:
        print(f"[ERROR] API failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def start_full_stack() -> None:
    """Start the complete stack: API + Frontend."""
    try:
        import json
        import requests
    except ImportError:
        print("[ERROR] Missing required packages for full stack mode")
        print("[INFO] Install with: pip install requests")
        sys.exit(1)

    project_root = Path(__file__).parent

    # Auto-detect available ports
    api_port = _find_available_port(8000, "localhost")
    frontend_port = _find_available_port(5173, "localhost")

    # Write port configuration for frontend
    config_dir = project_root / "socrates-frontend" / "public"
    config_dir.mkdir(parents=True, exist_ok=True)
    config_file = config_dir / "server-config.json"
    with open(config_file, "w") as f:
        json.dump({"api_url": f"http://localhost:{api_port}"}, f)

    print(f"[INFO] Wrote server config to {config_file}")

    # Process management
    processes = []
    api_ready = threading.Event()
    api_process: Optional[subprocess.Popen] = None

    def start_api_process():
        """Start API in subprocess."""
        nonlocal api_process
        try:
            env = os.environ.copy()
            env['SOCRATES_API_HOST'] = 'localhost'
            env['SOCRATES_API_PORT'] = str(api_port)
            env['SOCRATES_API_RELOAD'] = 'false'

            api_process = subprocess.Popen(
                [sys.executable, "-c", f"""
import sys
import os
sys.path.insert(0, r'{project_root}')
sys.path.insert(0, r'{project_root / "socrates-api" / "src"}')
os.environ['SOCRATES_API_HOST'] = 'localhost'
os.environ['SOCRATES_API_PORT'] = '{api_port}'
os.environ['SOCRATES_API_RELOAD'] = 'false'
from socrates_api.main import run
run()
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
            print(f"[ERROR] API process failed: {e}")

    def wait_for_api(max_retries: int = 30, retry_delay: float = 1.0) -> bool:
        """Wait for API to be ready."""
        print("[INFO] Waiting for API server...")
        for attempt in range(max_retries):
            try:
                response = requests.get(f"http://localhost:{api_port}/health", timeout=2)
                if response.status_code == 200:
                    print("[INFO] API is ready!")
                    api_ready.set()
                    return True
            except:
                if attempt < max_retries - 1:
                    print(f"[INFO] API not ready yet... ({attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)

        print("[ERROR] API did not start in time")
        return False

    def wait_for_frontend_and_open_browser(max_retries: int = 30, retry_delay: float = 1.0) -> None:
        """Wait for frontend and open browser."""
        frontend_url = f"http://localhost:{frontend_port}"
        print(f"[INFO] Waiting for frontend at {frontend_url}...")

        for attempt in range(max_retries):
            try:
                response = requests.get(frontend_url, timeout=2)
                if response.status_code == 200:
                    print("[INFO] Frontend is ready! Opening browser...")
                    webbrowser.open(frontend_url)
                    return
            except:
                if attempt < max_retries - 1:
                    print(f"[INFO] Frontend not ready yet... ({attempt + 1}/{max_retries})")
                    time.sleep(retry_delay)

        print("[WARN] Frontend did not start in time")

    def start_frontend_process():
        """Start frontend in subprocess."""
        frontend_dir = project_root / "socrates-frontend"
        if not frontend_dir.exists():
            print(f"[ERROR] Frontend directory not found: {frontend_dir}")
            return

        # Wait for API
        if not api_ready.wait(timeout=60):
            print("[ERROR] Frontend startup cancelled: API failed to start")
            return

        try:
            # Install dependencies
            print("[INFO] Installing frontend dependencies...")
            subprocess.run(
                "npm install",
                cwd=frontend_dir,
                check=False,
                capture_output=True,
                shell=True,
                timeout=300
            )

            # Start dev server
            env = os.environ.copy()
            env["VITE_PORT"] = str(frontend_port)
            env["VITE_API_URL"] = f"http://localhost:{api_port}"

            print(f"[INFO] Starting frontend on port {frontend_port}...")
            proc = subprocess.Popen(
                "npm run dev",
                cwd=frontend_dir,
                env=env,
                shell=True
            )
            processes.append(proc)

            # Wait for frontend and open browser
            browser_thread = threading.Thread(
                target=wait_for_frontend_and_open_browser,
                daemon=True
            )
            browser_thread.start()

            proc.wait()
        except Exception as e:
            print(f"[ERROR] Frontend failed: {e}")

    def signal_handler(sig, frame):
        """Handle Ctrl+C."""
        print("\n[INFO] Shutting down...")

        if api_process and api_process.poll() is None:
            try:
                api_process.terminate()
                api_process.wait(timeout=5)
            except:
                try:
                    api_process.kill()
                except:
                    pass

        for proc in processes:
            try:
                proc.terminate()
                proc.wait(timeout=5)
            except:
                try:
                    proc.kill()
                except:
                    pass

        sys.exit(0)

    # Setup signal handler
    signal.signal(signal.SIGINT, signal_handler)

    # Print startup info
    print("=" * 70)
    print("SOCRATES FULL STACK")
    print("=" * 70)
    print(f"[INFO] API: http://localhost:{api_port}")
    print(f"[INFO] Frontend: http://localhost:{frontend_port}")
    print("[INFO] Press Ctrl+C to shutdown")
    print("=" * 70 + "\n")

    # Start processes
    api_thread = threading.Thread(target=start_api_process, daemon=True)
    api_thread.start()

    health_thread = threading.Thread(target=wait_for_api, daemon=True)
    health_thread.start()

    # Start frontend (blocks)
    start_frontend_process()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="socrates",
        description="Socrates AI - Socratic method tutoring system",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python socrates.py            Start CLI
  python socrates.py --api      Start API on port 8000
  python socrates.py --full     Start full stack (API + Frontend)
        """
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"Socrates AI {__version__}"
    )

    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--api",
        action="store_true",
        help="Start API server only"
    )
    mode_group.add_argument(
        "--full",
        action="store_true",
        help="Start full stack (API + Frontend)"
    )

    parser.add_argument("--host", default="127.0.0.1", help="API host")
    parser.add_argument("--port", type=int, default=8000, help="API port")
    parser.add_argument("--reload", action="store_true", help="Enable reload")

    args = parser.parse_args()

    try:
        if args.api:
            start_api(host=args.host, port=args.port, reload=args.reload, auto_port=True)
        elif args.full:
            start_full_stack()
        else:
            start_cli()
    except KeyboardInterrupt:
        print("\n[INFO] Shutdown requested")
        sys.exit(0)
    except Exception as e:
        print(f"[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
