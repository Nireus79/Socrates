#!/usr/bin/env python
"""
Test port conflict detection and auto-port selection feature (LOCAL CODE).
"""

import socket
import sys
from pathlib import Path

# Add parent directory to path (BEFORE importing from local modules)
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def _find_available_port(preferred_port: int = 8000, host: str = "0.0.0.0") -> int:
    """
    Find an available port starting from preferred_port.
    This is the local implementation from socrates.py
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


def test_port_detection():
    """Test the port detection functionality"""
    print("=" * 70)
    print("PORT CONFLICT DETECTION TEST")
    print("=" * 70)

    # Test 1: Port is available
    print("\nTest 1: Finding available port starting from 9000...")
    try:
        port = _find_available_port(9000, "localhost")
        print(f"   [OK] Found available port: {port}")
        assert port >= 9000, f"Port {port} is less than requested 9000"
    except Exception as e:
        print(f"   [FAIL] {e}")
        return False

    # Test 2: Port is in use
    print("\nTest 2: Detecting when port is in use...")
    try:
        # Bind to a port to make it unavailable
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(("localhost", 9999))

            # Now try to find an available port starting from 9999
            port = _find_available_port(9999, "localhost")
            print(f"   [OK] Detected port 9999 in use, suggested port: {port}")
            assert port != 9999, f"Port detection failed: returned {port}"
            assert port > 9999, f"Port {port} should be greater than 9999"
    except Exception as e:
        print(f"   [FAIL] {e}")
        return False

    # Test 3: Multiple consecutive ports in use
    print("\nTest 3: Handling multiple ports in use...")
    try:
        sockets = []
        base_port = 10000
        num_occupied = 5

        # Occupy multiple ports
        for i in range(num_occupied):
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.bind(("localhost", base_port + i))
            sockets.append(sock)

        # Find available port
        port = _find_available_port(base_port, "localhost")
        print(f"   [OK] Found available port after {num_occupied} occupied ports: {port}")
        assert port >= base_port + num_occupied, f"Port {port} should be >= {base_port + num_occupied}"

        # Clean up
        for sock in sockets:
            sock.close()
    except Exception as e:
        print(f"   [FAIL] {e}")
        return False

    # Test 4: Port range testing
    print("\nTest 4: Testing port range discovery...")
    try:
        # Test a high port number
        port = _find_available_port(65000, "localhost")
        print(f"   [OK] Found available port in high range: {port}")
        assert port >= 65000, f"Port {port} should be >= 65000"
        assert port < 65100, f"Port {port} should be < 65100"
    except Exception as e:
        print(f"   [FAIL] {e}")
        return False

    print("\n" + "=" * 70)
    print("ALL PORT DETECTION TESTS PASSED [OK]")
    print("=" * 70)
    return True


if __name__ == "__main__":
    success = test_port_detection()
    sys.exit(0 if success else 1)
