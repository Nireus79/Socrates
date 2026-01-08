# Datetime Deprecation Fix - datetime.utcnow()

## Issue
`datetime.datetime.utcnow()` is deprecated in Python 3.12+

## Solution
Replace with: `datetime.datetime.now(datetime.timezone.utc)`

## Files to Update

### Priority 1 - Updated in Phase 3.1
1. code_generation.py
   - Lines using: `.utcnow()`
   - Replace all with: `.now(datetime.timezone.utc)`

2. collaboration.py
   - Lines using: `.utcnow()`
   - Replace all with: `.now(datetime.timezone.utc)`

### Fix Pattern

BEFORE:
```python
from datetime import datetime

created_at = datetime.utcnow().isoformat()
```

AFTER:
```python
from datetime import datetime, timezone

created_at = datetime.now(timezone.utc).isoformat()
```

### Quick Fix Script

```python
import re
from pathlib import Path

def fix_utcnow(filepath):
    with open(filepath, 'r') as f:
        content = f.read()

    # Add timezone import if not present
    if 'from datetime import' in content and 'timezone' not in content:
        content = content.replace(
            'from datetime import datetime',
            'from datetime import datetime, timezone'
        )

    # Replace utcnow() calls
    content = content.replace(
        'datetime.utcnow()',
        'datetime.now(timezone.utc)'
    )

    with open(filepath, 'w') as f:
        f.write(content)

# Apply to files
for file in ['code_generation.py', 'collaboration.py']:
    fix_utcnow(f'socrates-api/src/socrates_api/routers/{file}')
```

### Verification

After fixing, check:
```bash
grep -n "utcnow" socrates-api/src/socrates_api/routers/*.py
# Should return no results
```

### When to Apply
- Before final testing
- As part of code cleanup
- Before deployment

### Impact
- No functional change
- Maintains Python 3.12+ compatibility
- No breaking changes to response format
