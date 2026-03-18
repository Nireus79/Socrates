"""
Pytest configuration for socrates-cli tests.

Ensures that socrates_ai and socrates_cli modules are available for import.
"""

import sys
from pathlib import Path

# Add the src directory to Python path for socrates_cli imports
cli_src_dir = Path(__file__).parent.parent / "src"
if str(cli_src_dir) not in sys.path:
    sys.path.insert(0, str(cli_src_dir))

# Add the root directory to Python path for socrates_ai imports
root_dir = Path(__file__).parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
