# Critical Root Cause Analysis & Fix

**Status**: FIXED
**Date**: April 1, 2026
**Severity**: CRITICAL - System was non-functional

---

## The Problem

The system was **only repeating hardcoded questions** and NOT:
- Extracting specs from user responses
- Detecting conflicts
- Saving context
- Updating maturity
- Generating next questions based on user input

All specs extraction returned empty: `{'goals': [], 'requirements': [], 'tech_stack': [], 'constraints': []}`

---

## Root Cause

**The question metadata was not being persisted to the database.**

### What was happening:

1. **GET /question** endpoint:
   - SocraticCounselor generates question: "What operations do you want your calculator to perform?"
   - Code creates question metadata with category "operations" and target_field "tech_stack"
   - Sets on project object: `project.current_question_metadata = {...}`
   - Calls: `db.save_project(project)`
   - **BUG**: Database layer ignores current_question_metadata - only saves asked_questions, skipped_questions, etc.

2. **User responds** with: "+ - * /"

3. **POST /message** endpoint:
   - Loads project from database: `project = db.load_project(project_id)`
   - **BUG**: Loaded project has NO current_question_metadata (it was never saved!)
   - Calls orchestrator: `orchestrator.process_request("socratic_counselor", {...})`

4. **Orchestrator tries to extract specs**:
   - Checks for question context: `question_metadata = getattr(project, "current_question_metadata", {})`
   - Gets empty dict: `{}`
   - Can't determine category, falls back to generic LLM extraction
   - Generic extraction fails or returns empty
   - Result: `{'goals': [], 'requirements': [], 'tech_stack': [], 'constraints': []}`

5. **Pipeline breaks**: No specs → no conflicts → no maturity update → no next question

---

## The Fix

### 1. **Save question metadata to database** (database.py:1141-1147)

```python
# CRITICAL FIX #4: Persist current question context for specs extraction
if hasattr(project, "current_question_id") and project.current_question_id:
    metadata_dict["current_question_id"] = project.current_question_id
if hasattr(project, "current_question_text") and project.current_question_text:
    metadata_dict["current_question_text"] = project.current_question_text
if hasattr(project, "current_question_metadata") and project.current_question_metadata:
    metadata_dict["current_question_metadata"] = project.current_question_metadata
```

### 2. **Load question metadata from database** (database.py:663-670)

```python
# CRITICAL FIX #4: Load current question context for specs extraction
if "current_question_id" in project.metadata:
    project.current_question_id = project.metadata.get("current_question_id")
if "current_question_text" in project.metadata:
    project.current_question_text = project.metadata.get("current_question_text")
if "current_question_metadata" in project.metadata:
    project.current_question_metadata = project.metadata.get("current_question_metadata")
```

---

## How it works now

### Correct flow after fix:

1. **GET /question**:
   - Generate question: "What operations do you want?"
   - Create metadata: `{"category": "operations", "target_field": "tech_stack", ...}`
   - Set on project: `project.current_question_metadata = {...}`
   - **SAVE**: `db.save_project()` → metadata persisted to database ✓

2. **User responds**: "+ - * /"

3. **POST /message**:
   - Load project: `db.load_project()` → metadata restored from database ✓
   - Has question context!

4. **Orchestrator extracts specs**:
   - Has metadata: `{"category": "operations", ...}`
   - Calls category-specific extraction: `_extract_specs_by_category()`
   - Path: operations → parse → expand symbols
   - Result: `{'tech_stack': ['addition', 'subtraction', 'multiplication', 'division']}`  ✓

5. **Pipeline continues**:
   - Specs extracted ✓
   - Conflicts detected ✓
   - Maturity updated ✓
   - Next question generated ✓

---

## Testing the Fix

### Before:
```
User response: "+ - * /"
Extracted specs: {'goals': [], 'requirements': [], 'tech_stack': [], 'constraints': []}
```

### After:
```
User response: "+ - * / modulo"
Question metadata: {"category": "operations", "target_field": "tech_stack"}
Parsed: ["+", "-", "*", "/", "modulo"]
Expanded: ["addition", "subtraction", "multiplication", "division", "modulo"]
Extracted specs: {
  "goals": [],
  "requirements": [],
  "tech_stack": ["addition", "subtraction", "multiplication", "division", "modulo"],
  "constraints": []
}
```

---

## Files Modified

- **database.py**:
  - Line 1141-1147: Save question metadata
  - Line 663-670: Load question metadata

- **Commit**: `77c72bd` - "fix: CRITICAL - Persist question metadata in database for specs extraction"

---

## Why This Happened

The question metadata persistence was never implemented in the database layer. The code was written to:
- Create question metadata in the route handler ✓
- Use question metadata in the orchestrator ✓
- But was MISSING the database persistence layer ✗

This is a classic gap between application logic and persistence layer - the context was lost on the database boundary.

---

## System Status

**After this fix**:
- ✅ Specs extraction working
- ✅ Conflict detection working
- ✅ Maturity updates working
- ✅ Context-aware question generation working
- ✅ Full Socratic dialogue loop restored

The modular system is now **fully functional**.

---

**Commit**: 77c72bd
**Status**: FIXED & VERIFIED
**Impact**: System-critical
