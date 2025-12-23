#!/usr/bin/env python
"""Run the Socrates API."""
import sys
from pathlib import Path

# Add paths
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "socrates-api" / "src"))

import uvicorn

if __name__ == "__main__":
    uvicorn.run("socrates_api.main:app", host="0.0.0.0", port=8000, reload=False)
