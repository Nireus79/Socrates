# Workflow Comparison Bugs: Monolithic vs Modular

## CRITICAL FINDING: Spec Extraction & Persistence Workflows Are Broken

Based on comprehensive workflow comparison between monolithic (working) and modular (broken) implementations, 7 critical bugs were identified in spec extraction and database persistence layers.

---

## BUG #8.1: DIRECT MODE SPECS NOT PERSISTED TO DATABASE

**Severity:** CRITICAL - Data Loss

**Location:** `backend/src/socrates_api/routers/projects_chat.py` lines 667-754

**Issue:**
In DIRECT mode, extracted specs are returned to frontend for user confirmation but **never saved to database if user doesn't explicitly confirm**. The specs exist only in memory and are lost if session ends.

**What Happens:**
1. Lines 667-708: Specs extracted from user message + assistant answer
2. Line 722: Specs returned in response for user confirmation
3. Line 754: Only conversation history saved, NOT extracted specs
4. If user closes browser: Specs completely lost

**Difference from Monolithic:**
Monolithic immediately persists specs to `extracted_specs_metadata` table with confidence scores and source tracking, regardless of user confirmation.

**Impact:**
- Users lose all spec work if they don't explicitly confirm
- No audit trail of spec extraction
- Data inconsistency between what user sees and what's persisted

**Fix Priority:** CRITICAL - Implement immediately

---

## BUG #8.2: PROJECT SPECS NOT PERSISTED AFTER EXTRACTION

**Severity:** CRITICAL - Data Loss & Logic Error

**Location:** `backend/src/socrates_api/routers/projects_chat.py` lines 737-754 (socratic mode) and `orchestrator.py` lines 3376-3680

**Issue:**
Extracted specs are saved to metadata table but **NOT merged into project.goals, project.requirements, etc.**

**What Happens:**
1. User answers question → specs extracted (line 3462)
2. Specs saved to `extracted_specs_metadata` table (line 3506) ✓
3. Project.goals/requirements/tech_stack/constraints NOT updated ✗
4. Project saved without spec changes (line 754) ✓ but with empty spec fields ✗
5. User reloads project → no specs available (they're only in metadata table)

**Data Dual-Path Problem:**
- Specs stored in: `extracted_specs_metadata` table (metadata)
- Specs NOT in: `projects` table spec columns
- But application only uses project fields, never queries metadata table

**Difference from Monolithic:**
Monolithic merges specs into project fields before saving, ensuring they're available on next load.

**Impact:**
- Specs extracted but invisible to application
- Conflict detection fails (based on empty project fields)
- Users see empty specs even though extraction happened
- Data in database but inaccessible

**Fix Priority:** CRITICAL - Blocks all spec-based functionality

---

## BUG #8.3: _orchestrate_answer_processing() METHOD NEVER CALLED

**Severity:** HIGH - Missing Core Workflow

**Location:** `backend/src/socrates_api/orchestrator.py` lines 2375-2712

**Issue:**
Complete method exists for orchestrating answer processing (extracting specs, detecting conflicts, updating maturity) but **is never called anywhere in the codebase**.

**Evidence:**
```bash
grep -r "_orchestrate_answer_processing" backend/
# Returns: definition only (line 2375), ZERO usages
```

**What's Broken:**
- Method 2375-2712 implements full spec merging workflow
- It's not called from process_response action
- Instead, inline code at 3376-3680 does partial implementation
- This creates code duplication and inconsistency

**Impact:**
- Duplication of logic
- Inconsistent spec merging between methods
- Unused production code
- Maintenance nightmare

**Fix Priority:** HIGH - Code cleanup + consistency

---

## BUG #8.4: _auto_save_extracted_specs() MISSING METADATA PERSISTENCE

**Severity:** HIGH - Incomplete Data Persistence

**Location:** `backend/src/socrates_api/orchestrator.py` lines 5810-5893

**Issue:**
Method merges specs into project fields and saves project, but **doesn't persist metadata about extraction** (confidence score, source, timestamp).

**What's Missing:**
```python
# After line 5884 (db.save_project), should add:
db.save_extracted_specs(
    project_id=project.project_id,
    specs=insights,
    extraction_method="auto_save",
    confidence_score=0.9,
    metadata={"auto_merged": True}
)
```

**Impact:**
- Specs saved to project fields ✓
- But metadata lost ✗
- No audit trail of extraction
- Can't trace specs back to source

**Fix Priority:** HIGH - Completes the persistence story

---

## BUG #8.5: EXTRACTED_SPECS TABLE POPULATED BUT NEVER USED

**Severity:** HIGH - Dead Code

**Location:**
- Write: `database.py` lines 2940-2947 (save_extracted_specs)
- Read: `database.py` lines 3051-3096 (get_extracted_specs)
- Usage: ZERO locations in codebase

**Issue:**
`extracted_specs_metadata` table is being populated with specs but **never queried**. The data is written but never read.

**Evidence:**
```bash
grep -r "get_extracted_specs" backend/
# Returns: definition only (line 3051), ZERO usages
```

**Impact:**
- Specs stored in write-only table
- Data exists but inaccessible to application
- Resource wasted on persistence that's never used
- When project fields empty, application has no fallback to metadata table

**Fix Priority:** HIGH - Either use the data or remove dead code

---

## BUG #8.6: CONFIDENCE SCORES NOT VALIDATED IN CONFLICT DETECTION

**Severity:** MEDIUM - Quality Issue

**Location:** `backend/src/socrates_api/orchestrator.py` lines 4737-4871

**Issue:**
Extracted specs have confidence scores (saved at line 3498) but confidence is **never used in conflict detection**.

**Problem:**
- Low-confidence specs (< 0.7) should be deprioritized in conflict detection
- Currently all specs treated equally regardless of confidence
- Could lead to false conflicts based on low-confidence extractions

**Fix Priority:** MEDIUM - Quality improvement

---

## BUG #8.7: CONVERSATION HISTORY NOT LINKED TO SPEC EXTRACTIONS

**Severity:** MEDIUM - Auditability Issue

**Location:** `backend/src/socrates_api/routers/projects_chat.py` lines 667-722 and `orchestrator.py` lines 3506-3518

**Issue:**
When specs are extracted, the `response_turn` parameter is set to `None` (line 3512), breaking ability to trace specs back to conversation.

**Problem:**
- User can't see which message led to which specs
- No auditability or debugging capability
- Can't replay conversation to verify specs

**Fix Priority:** MEDIUM - Improves UX and debugging

---

## SUMMARY OF REQUIRED FIXES

### CRITICAL (Must fix before production):
1. **BUG #8.1**: Persist specs in direct mode immediately
2. **BUG #8.2**: Merge extracted specs into project fields before saving

### HIGH (Fix in next sprint):
3. **BUG #8.3**: Remove _orchestrate_answer_processing duplication
4. **BUG #8.4**: Add metadata persistence to _auto_save_extracted_specs
5. **BUG #8.5**: Query extracted_specs table or remove dead code

### MEDIUM (Nice to have):
6. **BUG #8.6**: Use confidence scores in conflict detection
7. **BUG #8.7**: Link specs to conversation turns for auditability

---

## IMPACT ASSESSMENT

**Broken Workflows:**
- ✗ Spec extraction in direct mode (data lost)
- ✗ Spec persistence (dual-path inconsistency)
- ✗ Spec retrieval (metadata table not queried)
- ✗ Conflict detection (based on empty project fields)
- ✗ Maturity calculation (based on missing specs)

**Data Loss Risk:** CRITICAL
- Users see empty specs despite extraction happening
- Specs in database but inaccessible
- Session loss = complete spec loss

**Functional Impact:** CRITICAL
- Spec-based features don't work correctly
- Project context incomplete
- Conflict detection fails
- Users can't trust the system

---

## COMPARISON TABLE: MONOLITHIC vs MODULAR

| Workflow Step | Monolithic | Modular | Status |
|---------------|-----------|---------|--------|
| Extract specs | ✓ Extracts | ✓ Extracts | ✓ OK |
| Save to metadata table | ✓ Saves | ✓ Saves | ✓ OK |
| Merge to project fields | ✓ Merges | ✗ Skips | **✗ BUG #8.2** |
| Save merged project | ✓ Saves | ✓ Saves | ✓ OK |
| Query metadata table | ✓ Used as fallback | ✗ Never queried | **✗ BUG #8.5** |
| Link to conversation | ✓ Links | ✗ Sets to None | **✗ BUG #8.7** |
| Use confidence scores | ✓ Uses in decisions | ✗ Ignores | **✗ BUG #8.6** |
| Persist in direct mode | ✓ Persists | ✗ Loses on close | **✗ BUG #8.1** |

---

## ROOT CAUSE ANALYSIS

The modular version created a **dual-path persistence architecture** without proper synchronization:

**Path 1 (Metadata Table):**
- Specs extracted and saved → `extracted_specs_metadata`
- But never read back

**Path 2 (Project Fields):**
- Specs extracted but not saved → project.goals/requirements/tech_stack/constraints
- So project fields remain empty

**Result:** Specs exist in database but application can't find them.

---

## RECOMMENDATIONS

### Immediate (Before Production):
1. Fix BUG #8.1: Auto-persist specs in direct mode
2. Fix BUG #8.2: Merge specs into project fields after extraction
3. Test complete spec lifecycle end-to-end

### Short-term (Next Sprint):
4. Fix BUG #8.3: Remove orchestration method duplication
5. Fix BUG #8.4: Complete metadata persistence
6. Fix BUG #8.5: Query metadata table or remove dead code

### Medium-term:
7. Fix BUG #8.6: Use confidence scores in decisions
8. Fix BUG #8.7: Link specs to conversation turns
9. Implement comprehensive integration tests for spec workflows

---

**Status:** 8 Critical workflow bugs found comparing monolithic vs modular
**Priority:** CRITICAL - Fix before any production deployment
**Impact:** Data loss, missing functionality, user-facing failures
