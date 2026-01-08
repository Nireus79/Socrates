"""
Dynamic port allocation and management.

Handles finding available ports, checking if ports are in use,
and exporting configuration for frontend discovery.
"""

import json
import logging
import socket
from contextlib import closing
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)


def is_port_available(host: str = "127.0.0.1", port: int = 8008) -> bool:
    """
    Check if a port is available on the given host.

    Args:
        host: Host to check (default: localhost)
        port: Port number to check

    Returns:
        True if port is available, False if in use
    """
    try:
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            result = sock.connect_ex((host, port))
            return result != 0  # 0 means port is in use
    except socket.error as e:
        logger.error(f"Error checking port {port}: {e}")
        return False


def find_available_port(
    preferred_port: int = 8008,
    host: str = "127.0.0.1",
    max_attempts: int = 100,
) -> int:
    """
    Find an available port starting from preferred_port.

    If preferred_port is taken, tries sequential ports up to preferred_port + max_attempts.

    Args:
        preferred_port: Port to try first (default: 8008)
        host: Host to check (default: localhost)
        max_attempts: Maximum ports to try

    Returns:
        Available port number

    Raises:
        RuntimeError: If no available port found in range
    """
    # First, try the preferred port
    if is_port_available(host, preferred_port):
        logger.info(f"Port {preferred_port} is available (preferred port)")
        return preferred_port

    logger.warning(f"Port {preferred_port} is in use, searching for alternative...")

    # Try sequential ports
    for offset in range(1, max_attempts):
        test_port = preferred_port + offset
        if is_port_available(host, test_port):
            logger.warning(f"Using port {test_port} instead of {preferred_port} (original in use)")
            return test_port

    raise RuntimeError(
        f"No available ports found between {preferred_port} and {preferred_port + max_attempts}"
    )


def export_port_config(api_port: int, frontend_port: int, output_dir: Optional[Path] = None) -> Path:
    """
    Export port configuration to a JSON file for frontend discovery.

    Creates a port-config.json file that frontend can read to discover API port.

    Args:
        api_port: API server port
        frontend_port: Frontend server port
        output_dir: Directory to write config file (default: current dir)

    Returns:
        Path to created config file
    """
    if output_dir is None:
        output_dir = Path.cwd()

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    config_file = output_dir / "port-config.json"

    config = {
        "api": {
            "host": "127.0.0.1",
            "port": api_port,
            "url": f"http://127.0.0.1:{api_port}",
        },
        "frontend": {
            "host": "127.0.0.1",
            "port": frontend_port,
            "url": f"http://127.0.0.1:{frontend_port}",
        },
        "info": "Auto-generated port configuration. DO NOT EDIT.",
    }

    with open(config_file, "w") as f:
        json.dump(config, f, indent=2)

    logger.info(f"Port configuration exported to {config_file}")
    logger.info(f"API URL: {config['api']['url']}")
    logger.info(f"Frontend URL: {config['frontend']['url']}")

    return config_file


def read_port_config(config_file: Optional[Path] = None) -> dict:
    """
    Read port configuration from file.

    Args:
        config_file: Path to port-config.json (searches current dir if not provided)

    Returns:
        Configuration dictionary with api and frontend port info

    Raises:
        FileNotFoundError: If config file not found
        json.JSONDecodeError: If config file is invalid JSON
    """
    if config_file is None:
        config_file = Path.cwd() / "port-config.json"

    config_file = Path(config_file)

    if not config_file.exists():
        raise FileNotFoundError(
            f"Port configuration file not found: {config_file}\n"
            f"Make sure the Socrates API has been started first."
        )

    with open(config_file, "r") as f:
        config = json.load(f)

    return config
