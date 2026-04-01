# Monolith Workflow Analysis: The Missing Context Problem

**Date:** 2026-04-01
**Investigation Focus:** Why user responses like "+ -" are not being captured as specs
**Root Cause:** Context-unaware specs extraction breaking the dialogue→specs→database pipeline

---

## THE PROBLEM: Context Lost During Modularization

### What the User Reported
When asked "What operations (like adding or subtracting) would you want your calculator to perform?":
- User answered: `+ -` (meaning addition and subtraction)
- Expected result: Specs extraction maps this to tech_stack or operations
- Actual result: Empty specs, response not captured

### Why It's Broken

**Current Flow (Broken):**
```
1. generate_question() creates: "What operations (like adding or subtracting) would you want your calculator to perform?"
2. Question is stored in: project.current_question_text
3. User responds: "+ -"
4. process_response() receives: {"response": "+ -", "project": {...}}
5. _extract_insights_fallback(response) is called with ONLY: "+ -"
   → No context about what question was asked
   → Can't map "+ -" to appropriate spec field
   → Returns empty specs {}
```

**What Should Happen (Original Monolith Logic):**
```
1. Question generated with metadata: "What operations..."
2. Response captured: "+ -"
3. Specs extraction receives BOTH:
   - Response text: "+ -"
   - Question context: "What operations..."
   - Question type/category: e.g., "operations", "tech_stack", "features"
4. Context-aware parser maps: "+ -" → ["addition", "subtraction"] → tech_stack field
5. Specs {"tech_stack": ["addition", "subtraction"]} returned
6. Specs auto-saved to database
```

---

## WHERE THE CONTEXT BREAKS

### Location 1: Response Processing in Orchestrator
**File:** `backend/src/socrates_api/orchestrator.py:1800`

```python
# CURRENT (BROKEN):
extracted_specs = self._extract_insights_fallback(response)
# Only receives: "+ -"
# Loses: current_question_text context

# SHOULD BE:
extracted_specs = self._extract_insights_fallback(
    response,
    question=project.current_question_text,  # ADD THIS
    question_context=project.current_question_metadata  # ADD THIS
)
```

### Location 2: Specs Extraction Method
**File:** `backend/src/socrates_api/orchestrator.py:2275`

```python
def _extract_insights_fallback(self, text: str) -> Dict[str, Any]:
    # CURRENT (BROKEN):
    # Only receives text parameter, no context
    # ContextAnalyzer agent gets called with {"action": "analyze", "content": text}
    # But ContextAnalyzer doesn't know what question was asked

    # SHOULD BE:
    def _extract_insights_fallback(
        self,
        text: str,
        question: str = None,  # ADD THIS
        question_context: Dict = None  # ADD THIS
    ) -> Dict[str, Any]:
        # If question is about "operations", map answer to tech_stack
        # If question is about "goals", map answer to goals field
        # If question is about "requirements", map answer to requirements field
```

### Location 3: Question Tracking
**File:** `backend/src/socrates_api/routers/projects_chat.py:663-667`

```python
# Questions ARE tracked when generated:
question_id = f"q_{uuid.uuid4().hex[:12]}"
project.current_question_id = question_id
project.current_question_text = question
# But when response is processed, this context is never passed to specs extraction
```

---

## THE MISSING METADATA: Question Categories

The original monolith likely had question metadata that classified each question:

```python
QUESTION_CATEGORIES = {
    "operations": "tech_stack",        # "What operations?" → tech_stack field
    "goals": "goals",                   # "What are the goals?" → goals field
    "requirements": "requirements",    # "What are the requirements?" → requirements field
    "constraints": "constraints",      # "What are the constraints?" → constraints field
    "technologies": "tech_stack",      # "What technologies?" → tech_stack field
    "platforms": "tech_stack",         # "What platforms?" → tech_stack field
}
```

When a question is generated, it should have metadata:
```python
question_metadata = {
    "id": "q_abc123",
    "text": "What operations (like adding or subtracting) would you want your calculator to perform?",
    "category": "operations",           # Maps to which spec field
    "target_field": "tech_stack",       # Where to save the answer
    "expected_format": "comma_separated",  # How to parse the answer
}
```

---

## THE WORKFLOW THAT WAS LOST

### Phase 1: Question Generation (Still Works)
```
ProjectContext loaded
↓
SocraticCounselor.generate_question()
↓
Question created: "What operations (like adding or subtracting)..."
↓
Question stored in project.current_question_text ✓
Question ID stored in project.current_question_id ✓
```

### Phase 2: Response Capture (Still Works)
```
User submits response
↓
API endpoint receives: POST /projects/{id}/chat/message
↓
Request body: {"message": "+ -"}
↓
Response stored in project.conversation_history ✓
```

### Phase 3: Specs Extraction (BROKEN)
```
Response: "+ -"
Current Question Context: MISSING ✗
↓
_extract_insights_fallback(response)  ← Called with ONLY response text
↓
LLM tries to extract specs from "+ -" without context
↓
Result: {} (empty specs)
↓
Specs saved with: metadata={"extraction_method": "contextanalyzer"}
```

### Phase 4: Conflict Detection (Works, but with empty specs)
```
extracted_specs = {}  ← Empty
project_specs = {...}
↓
_compare_specs({}, {...})
↓
No conflicts detected (because nothing was extracted)
```

### Phase 5: Specs Persistence (Works, but saves nothing)
```
db.save_extracted_specs(
    project_id=...,
    specs={},  ← Empty!
    source_text="+ -",
    metadata={"extraction_method": "contextanalyzer"}
)
↓
Empty specs persisted to database
```

---

## HOW TO FIX: Three-Part Solution

### Step 1: Capture Question Metadata When Generating Questions

**File:** `backend/src/socrates_api/routers/projects_chat.py` (get_question endpoint)

```python
# After question is generated, BEFORE returning to user:

question_metadata = {
    "id": question_id,
    "text": question,
    "category": _detect_question_category(question),  # NEW METHOD
    "target_field": _map_category_to_field(category),  # NEW METHOD
    "expected_format": "comma_separated",  # Could be enhanced
    "examples": _generate_examples(category),  # Help user understand format
}

# Store on project:
project.current_question_metadata = question_metadata
db.save_project(project)

# Return to frontend with metadata:
return {
    "question": question,
    "question_id": question_id,
    "metadata": question_metadata,  # NEW
    ...
}
```

### Step 2: Pass Question Context to Specs Extraction

**File:** `backend/src/socrates_api/orchestrator.py:1800`

```python
# CURRENT (BROKEN):
extracted_specs = self._extract_insights_fallback(response)

# FIXED:
question_text = getattr(project, "current_question_text", None)
question_metadata = getattr(project, "current_question_metadata", {})

extracted_specs = self._extract_insights_fallback(
    response_text=response,
    question_text=question_text,
    question_metadata=question_metadata,
)
```

### Step 3: Implement Context-Aware Specs Extraction

**File:** `backend/src/socrates_api/orchestrator.py:2275`

```python
def _extract_insights_fallback(
    self,
    response_text: str,
    question_text: str = None,
    question_metadata: Dict = None,
) -> Dict[str, Any]:
    """Extract specs from response using question context"""

    # Step 1: Detect what field this response should map to
    target_field = None
    if question_metadata:
        target_field = question_metadata.get("target_field")

    if not target_field:
        target_field = self._detect_target_field_from_question(question_text)

    # Step 2: Parse response based on question category
    if target_field == "tech_stack":
        # Parse comma-separated or symbol-separated values
        items = self._parse_comma_or_symbol_separated(response_text)
        # "+ -" → ["addition", "subtraction"]
        items = self._expand_symbols(items)
        return {
            "goals": [],
            "requirements": [],
            "tech_stack": items,
            "constraints": []
        }

    elif target_field == "goals":
        # Parse goal statement
        goals = self._parse_goal_statement(response_text)
        return {
            "goals": goals if goals else [],
            "requirements": [],
            "tech_stack": [],
            "constraints": []
        }

    elif target_field == "requirements":
        # Parse requirement list
        requirements = self._parse_requirement_list(response_text)
        return {
            "goals": [],
            "requirements": requirements if requirements else [],
            "tech_stack": [],
            "constraints": []
        }

    elif target_field == "constraints":
        # Parse constraint list
        constraints = self._parse_constraint_list(response_text)
        return {
            "goals": [],
            "requirements": [],
            "tech_stack": [],
            "constraints": constraints if constraints else []
        }

    # Fallback: Generic LLM extraction (current behavior)
    else:
        return self._generic_llm_extraction(response_text)

def _parse_comma_or_symbol_separated(self, text: str) -> List[str]:
    """Parse comma-separated or symbol-separated values"""
    # Handle: "+ -" → ["+", "-"]
    # Handle: "addition, subtraction" → ["addition", "subtraction"]
    # Handle: "addition and subtraction" → ["addition", "subtraction"]

    # Split on comma, semicolon, "and", or space
    import re
    items = re.split(r'[,;\s]+(?:and\s+)?', text.strip())
    return [item.strip() for item in items if item.strip()]

def _expand_symbols(self, items: List[str]) -> List[str]:
    """Expand mathematical/programming symbols to full names"""
    symbol_map = {
        "+": "addition",
        "-": "subtraction",
        "*": "multiplication",
        "/": "division",
        "%": "modulo",
        "**": "exponentiation",
        "&&": "logical_and",
        "||": "logical_or",
        "!": "logical_not",
    }
    return [symbol_map.get(item, item) for item in items]

def _detect_question_category(self, question_text: str) -> str:
    """Detect what category a question belongs to"""
    question_lower = question_text.lower()

    if any(word in question_lower for word in ["operation", "function", "what can"]):
        return "operations"
    elif any(word in question_lower for word in ["goal", "purpose", "objective"]):
        return "goals"
    elif any(word in question_lower for word in ["requirement", "feature", "capability"]):
        return "requirements"
    elif any(word in question_lower for word in ["constraint", "limit", "restriction"]):
        return "constraints"
    elif any(word in question_lower for word in ["technology", "tool", "framework", "language"]):
        return "tech_stack"

    return "generic"

def _map_category_to_field(self, category: str) -> str:
    """Map question category to spec field"""
    mapping = {
        "operations": "tech_stack",
        "goals": "goals",
        "requirements": "requirements",
        "constraints": "constraints",
        "tech_stack": "tech_stack",
        "generic": "requirements",  # Default fallback
    }
    return mapping.get(category, "requirements")
```

---

## FILES THAT NEED CHANGES

| File | Change | Priority |
|------|--------|----------|
| `backend/src/socrates_api/orchestrator.py` | Add question_text/metadata parameters to specs extraction | HIGH |
| `backend/src/socrates_api/orchestrator.py` | Implement context-aware parsing methods | HIGH |
| `backend/src/socrates_api/routers/projects_chat.py` | Capture and store question metadata on project | MEDIUM |
| `backend/src/socrates_api/routers/projects_chat.py` | Pass question metadata when processing response | MEDIUM |
| `socratic_system/models.py` | Add `current_question_metadata` field to ProjectContext | LOW |

---

## VERIFICATION: How the Fixed Flow Works

### Test Case: "What operations?" Question

```
1. Question generation:
   - Question: "What operations (like adding or subtracting) would you want your calculator to perform?"
   - Metadata: {"category": "operations", "target_field": "tech_stack"}
   - Stored in project.current_question_metadata

2. User responds:
   - Response: "+ -"

3. Response processing:
   - _extract_insights_fallback(
       response_text="+ -",
       question_text="What operations...",
       question_metadata={"target_field": "tech_stack"}
     )

4. Context-aware extraction:
   - Detects target_field = "tech_stack"
   - Parses "+ -" as symbol-separated list
   - Expands symbols: ["+", "-"] → ["addition", "subtraction"]
   - Returns: {"tech_stack": ["addition", "subtraction"]}

5. Specs saved to database:
   - extracted_specs_metadata: {"tech_stack": ["addition", "subtraction"], ...}
   - source_text: "+ -"
   - metadata: {"question_category": "operations"}

6. Conflict detection:
   - Compares new {"tech_stack": ["addition", "subtraction"]}
   - Against existing specs
   - Detects or confirms alignment
```

---

## SUMMARY

The modularization broke the specs extraction pipeline by:
1. **Lost Question Metadata** - Questions are generated but their category/purpose is not tracked
2. **Context-Unaware Extraction** - Specs extraction receives only response text, no question context
3. **Generic LLM Fallback** - Generic "extract structured info" prompt fails on terse answers like "+ -"
4. **Missing Field Mapping** - No logic to map answer to correct spec field based on question asked

The fix requires:
1. **Capture question metadata** when generating questions
2. **Pass context to extraction** method
3. **Implement context-aware parsing** that understands what question was asked
4. **Map answers to spec fields** based on question category
