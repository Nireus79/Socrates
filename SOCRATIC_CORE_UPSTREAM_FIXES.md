# Socratic-Core Upstream Fixes - TODO for Next Session

**Status**: ⚠️ NOT YET ADDRESSED
**Priority**: HIGH - Fixes should be made in upstream library, not workarounds in current repo

---

## Overview

The following issues exist in upstream dependencies that should be fixed at source rather than creating compatibility layers or workarounds in the application.

**Repository**: https://github.com/Nireus79/Socratic-core

---

## 1. IDGenerator Missing in socratic-core

### Current State
- Monolithic code imports: `from socratic_core.utils import ProjectIDGenerator`
- This module doesn't exist in new socratic-core
- **Workaround created**: `socratic_core/utils.py` compatibility shim in current repo

### What Needs to be Fixed in socratic-core

Add proper ID generator exports to `src/socratic_core/utils/id_generator.py`:

```python
"""ID generation utilities for consistency across services."""

import uuid
from typing import Final


class IDGenerator:
    """Generate consistent, prefixed IDs for all entity types."""

    PROJECT_PREFIX: Final[str] = "proj"
    USER_PREFIX: Final[str] = "user"
    SESSION_PREFIX: Final[str] = "sess"
    MESSAGE_PREFIX: Final[str] = "msg"
    # ... other prefixes

    @staticmethod
    def generate_id(prefix: str, length: int = 12) -> str:
        """Generate prefixed unique ID."""
        if not prefix:
            raise ValueError("Prefix cannot be empty")
        suffix = uuid.uuid4().hex[:length]
        return f"{prefix}_{suffix}"

    # Entity-specific methods
    @staticmethod
    def project() -> str:
        return IDGenerator.generate_id(IDGenerator.PROJECT_PREFIX)

    @staticmethod
    def user() -> str:
        return IDGenerator.generate_id(IDGenerator.USER_PREFIX)

    # Backward compatibility wrappers for monolithic code
    class ProjectIDGenerator:
        @staticmethod
        def generate() -> str:
            return IDGenerator.project()

    class UserIDGenerator:
        @staticmethod
        def generate() -> str:
            return IDGenerator.user()

    # ... other entity wrapper classes
```

**Export from** `src/socratic_core/__init__.py`:
```python
from .utils.id_generator import (
    IDGenerator,
    ProjectIDGenerator,
    UserIDGenerator,
)
```

### Files to Update in socratic-core
1. Create: `src/socratic_core/utils/id_generator.py`
2. Update: `src/socratic_core/__init__.py` - add exports
3. Create: `tests/test_id_generator.py` - comprehensive tests
4. Update: `docs/API.md` - document ID generation

### Impact if Fixed
- ❌ Can remove `socratic_core/` workaround from current repo
- ✅ Monolithic code imports work natively
- ✅ No compatibility shim needed

---

## 2. socratic-security Library - SQL Injection False Positives

### Current State
- Library flags legitimate keywords: "EXECUTE", "SELECT", "DROP", etc.
- Blocks legitimate user input like "I want to execute calculations"
- **Workaround**: Disabled validation in current system

### What Needs to be Fixed in socratic-security

Update `socratic_security/input_validation/validators.py`:

```python
def validate_no_sql_injection(v: str, context: str = "data") -> str:
    """
    Validate string doesn't contain SQL injection patterns.

    Args:
        v: String to validate
        context: "data" (user input) or "system" (SQL-related input)

    Returns:
        The validated string

    Raises:
        ValueError: If dangerous SQL patterns detected in system context
    """
    if not isinstance(v, str):
        return v

    # Only check for SQL keywords if this is system-level input (variable names, table names, etc.)
    if context == "system":
        # SQL injection patterns that matter in SQL context
        dangerous_patterns = [
            "DROP TABLE", "DELETE FROM", "INSERT INTO",
            "TRUNCATE", "ALTER TABLE", "CREATE TABLE",
            # ... actual SQL injection attack patterns
        ]

        v_upper = v.upper()
        for pattern in dangerous_patterns:
            if pattern in v_upper:
                raise ValueError(f"Potentially dangerous SQL pattern detected: {pattern}")

    # For user data (context="data"), SQL keywords are harmless
    # All database code uses parameterized queries which protect against injection
    return v
```

**Usage Examples**:
```python
# System context - checks SQL keywords
validate_no_sql_injection("DROP TABLE users", context="system")  # ❌ Raises error

# Data context (default) - allows keywords
validate_no_sql_injection("I want to execute operations", context="data")  # ✅ Passes
```

### Files to Update in socratic-security
1. Update: `socratic_security/input_validation/validators.py` - add context parameter
2. Update: `socratic_security/input_validation/__init__.py` - document parameter
3. Create: `tests/test_sql_injection_context.py` - test both contexts
4. Update: `docs/SECURITY.md` - document context awareness

### Impact if Fixed
- ✅ Remove validation override in current system
- ✅ False positives eliminated
- ✅ Legitimate user input accepted

---

## 3. socratic-agents Library - Specs Extraction Status

### Current State
- Extraction methods return empty arrays without indicating success/failure
- No confidence scoring for extraction quality
- Silent failures indistinguishable from "no specs found"
- **Workaround**: Added validation in orchestrator

### What Needs to be Fixed in socratic-agents

Update specs extraction to return structured result with status:

```python
def extract_specs(self, response_text: str) -> Dict[str, Any]:
    """
    Extract specifications from user response.

    Returns:
        {
            "status": "success|partial|empty|failed",
            "confidence_score": 0.0-1.0,
            "specs": {
                "goals": [...],
                "requirements": [...],
                "tech_stack": [...],
                "constraints": [...]
            },
            "metadata": {
                "extraction_method": "category-specific|generic-llm|fallback",
                "item_count": int,
                "error": str or None
            }
        }
    """
    if not response_text or not response_text.strip():
        return {
            "status": "empty",
            "confidence_score": 0.0,
            "specs": {"goals": [], "requirements": [], "tech_stack": [], "constraints": []},
            "metadata": {"extraction_method": "none", "item_count": 0}
        }

    try:
        extracted = self._do_extraction(response_text)

        # Calculate confidence from results
        item_count = sum(len(v) for v in extracted.values() if isinstance(v, list))

        if item_count == 0:
            status = "failed"
            confidence = 0.0
        elif item_count < 3:
            status = "partial"
            confidence = 0.6
        else:
            status = "success"
            confidence = min(0.85 + (item_count / 10) * 0.1, 0.95)

        return {
            "status": status,
            "confidence_score": confidence,
            "specs": extracted,
            "metadata": {
                "extraction_method": "category-specific",
                "item_count": item_count,
                "error": None
            }
        }

    except Exception as e:
        logger.error(f"Extraction failed: {e}")
        return {
            "status": "failed",
            "confidence_score": 0.0,
            "specs": {"goals": [], "requirements": [], "tech_stack": [], "constraints": []},
            "metadata": {
                "extraction_method": "none",
                "item_count": 0,
                "error": str(e)
            }
        }
```

### Files to Update in socratic-agents
1. Update: `socratic_agents/agents/socratic_counselor.py` - return structured result
2. Update: `socratic_agents/agents/context_analyzer.py` - add status/confidence
3. Create: `tests/test_specs_extraction_validation.py` - test all scenarios
4. Update: `docs/AGENTS.md` - document new return format

### Impact if Fixed
- ✅ Clear success/failure indication
- ✅ Confidence scores help with filtering
- ✅ Debugging easier with error messages

---

## 4. Priority Order for Next Session

### CRITICAL (Blocking functionality)
1. **IDGenerator in socratic-core** - Required for monolithic code to work
2. **SQL Injection validator in socratic-security** - Blocking legitimate user input

### HIGH (Important for quality)
3. **Specs extraction status in socratic-agents** - Helps with debugging and quality

---

## 5. Next Session Action Plan

### Phase 1: Fork/Clone socratic-core
```bash
# Fork https://github.com/Nireus79/Socratic-core
# Clone locally
git clone https://github.com/<your-username>/Socratic-core
cd Socratic-core
```

### Phase 2: Create Feature Branches
```bash
git checkout -b feature/add-id-generator
git checkout -b feature/fix-sql-injection-validator
git checkout -b feature/specs-extraction-status
```

### Phase 3: Implement Each Fix
- Add IDGenerator with backward compatibility wrappers
- Add context awareness to SQL injection validator
- Add status/confidence to specs extraction

### Phase 4: Testing
- Write comprehensive unit tests for each change
- Ensure backward compatibility
- Document the changes

### Phase 5: Create Pull Requests
- Create PRs to https://github.com/Nireus79/Socratic-core
- Link issues if applicable
- Reference current repo workarounds

### Phase 6: Update Current Repo
- Remove workarounds after upstream merges
- Update dependencies to use fixed versions
- Clean up compatibility shims

---

## 6. Impact on Current System

### Current Workarounds to Remove
1. `/socratic_core/` compatibility layer in current repo
2. Disabled SQL injection validation in `models.py`
3. `_validate_extracted_specs()` added to orchestrator

### After Upstream Fixes Applied
- ✅ Remove `socratic_core/` directory
- ✅ Re-enable proper security validation
- ✅ Rely on socratic-agents for extraction status
- ✅ Cleaner, more maintainable codebase

---

## 7. Reference Files

**In this repo (current workarounds)**:
- `socratic_core/__init__.py` - Compatibility layer (DELETE after fix)
- `socratic_core/utils.py` - IDGenerator wrapper (DELETE after fix)
- `backend/src/socrates_api/models.py` - Disabled validation (RE-ENABLE after fix)
- `backend/src/socrates_api/orchestrator.py` - Added validation (REMOVE after fix)

**In socratic-core (to be fixed)**:
- Add: `src/socratic_core/utils/id_generator.py`
- Update: `src/socratic_core/__init__.py`

**In socratic-security (to be fixed)**:
- Update: `socratic_security/input_validation/validators.py`

**In socratic-agents (to be fixed)**:
- Update: Multiple agent files for specs extraction

---

## 8. Notes for Next Session

- Socratic-core is a foundation library serving multiple projects
- Fixes will benefit the entire ecosystem, not just this project
- Consider discussing upstream with maintainer (https://github.com/Nireus79)
- May need to coordinate releases if breaking changes

