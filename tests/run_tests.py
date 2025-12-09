#!/usr/bin/env python
import sys

import pytest

import socratic_system

sys.path.insert(0, ".")

# Create module alias
sys.modules["socrates"] = socratic_system

# Run with minimal output
exit_code = pytest.main(["tests/", "--co", "-q"])  # Collect only, don't run
