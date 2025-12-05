#!/usr/bin/env python
import sys
sys.path.insert(0, '.')

# Create module alias
import socratic_system
sys.modules['socrates'] = socratic_system

# Import pytest and run tests
import pytest

# Run with minimal output
exit_code = pytest.main([
    'tests/',
    '--co',  # Collect only, don't run
    '-q'
])
