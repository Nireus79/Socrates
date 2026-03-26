"""
Socrates API - REST API server for Socrates AI

A FastAPI-based REST API that provides access to the Socrates AI tutoring system.
Enables integration with web frontends, mobile apps, and custom clients.
"""

# Load environment variables FIRST, before anything else
import os as _os
from dotenv import load_dotenv

# Find and load .env file from project root
# __file__ is in src/socrates_api/, so go up 3 levels to get to project root
_package_dir = _os.path.dirname(_os.path.abspath(__file__))
_src_dir = _os.path.dirname(_package_dir)
_project_root = _os.path.dirname(_src_dir)
_env_path = _os.path.join(_project_root, ".env")
if _os.path.exists(_env_path):
    load_dotenv(_env_path)
else:
    # Fallback to default behavior (current working directory)
    load_dotenv()

__version__ = "0.5.0"
__author__ = "Socrates AI Contributors"
__license__ = "MIT"

__all__ = ["__version__", "__author__", "__license__"]
