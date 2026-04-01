# Implementation Plan: Fix Context-Aware Specs Extraction

**Status:** Ready for Implementation
**Priority:** CRITICAL - Blocks core dialogue→specs→database workflow
**Estimated Changes:** 4 files, ~200 lines of code

---

## OBJECTIVE

Restore the context-aware specs extraction pipeline that was broken during modularization. The system must map user responses to the correct specification field based on the question that was asked.

**Key Requirement:** When a user answers "+ -" to "What operations do you want?", the system must:
1. Understand the question category
2. Map the answer format to the appropriate spec field
3. Parse "+ -" into ["addition", "subtraction"]
4. Save to database as tech_stack or operations

---

## IMPLEMENTATION STEPS

### STEP 1: Add Question Metadata Model

**File:** `socratic_system/models.py`

Add to ProjectContext dataclass:

```python
@dataclass
class ProjectContext:
    # ... existing fields ...

    # NEW: Question metadata for context-aware specs extraction
    current_question_metadata: Dict[str, Any] = field(default_factory=dict)
    """
    Metadata about the current question being asked.
    Format:
    {
        "id": "q_abc123",
        "text": "What operations would you want?",
        "category": "operations",  # operations, goals, requirements, constraints, tech_stack
        "target_field": "tech_stack",  # Where answer should map to
        "expected_format": "comma_separated",  # How to parse the answer
        "timestamp": "2026-04-01T10:00:00Z",
    }
    """
```

---

### STEP 2: Capture Question Metadata When Generating Questions

**File:** `backend/src/socrates_api/routers/projects_chat.py`
**Location:** Around line 663-677 in `get_question()` endpoint

```python
# AFTER question is generated but BEFORE saving project

# Create question metadata for context-aware specs extraction
def _categorize_question(question_text: str) -> Dict[str, str]:
    """Categorize a question and determine target spec field"""
    q_lower = question_text.lower()

    # Map keywords to categories
    if any(word in q_lower for word in ["operation", "function", "do", "perform"]):
        return {"category": "operations", "target_field": "tech_stack"}
    elif any(word in q_lower for word in ["goal", "purpose", "objective", "want to build"]):
        return {"category": "goals", "target_field": "goals"}
    elif any(word in q_lower for word in ["requirement", "feature", "capability", "need"]):
        return {"category": "requirements", "target_field": "requirements"}
    elif any(word in q_lower for word in ["constraint", "limit", "restriction", "avoid"]):
        return {"category": "constraints", "target_field": "constraints"}
    elif any(word in q_lower for word in ["technology", "tool", "framework", "language", "use"]):
        return {"category": "tech_stack", "target_field": "tech_stack"}
    else:
        return {"category": "generic", "target_field": "requirements"}

question_id = f"q_{uuid.uuid4().hex[:12]}"
question_category_info = _categorize_question(question)

question_metadata = {
    "id": question_id,
    "text": question,
    **question_category_info,  # Includes category and target_field
    "expected_format": "comma_separated",
    "timestamp": datetime.now(timezone.utc).isoformat(),
}

# Store on project object
project.current_question_id = question_id
project.current_question_text = question
project.current_question_metadata = question_metadata  # NEW

db.save_project(project)

logger.debug(f"Current question tracked: {question_id}")
logger.debug(f"Question category: {question_metadata['category']}, target_field: {question_metadata['target_field']}")
```

---

### STEP 3: Pass Question Context to Specs Extraction

**File:** `backend/src/socrates_api/orchestrator.py`
**Location:** Around line 1798-1810 in `_handle_socratic_counselor()`

```python
# CHANGE THIS:
else action == "process_response":
    response = request_data.get("response", "")
    project = request_data.get("project", {})
    current_user = request_data.get("current_user", "")

    logger.info(f"Processing response in Socratic mode: {response[:50]}...")

    # ... intent detection code ...

    try:
        # CURRENT (BROKEN):
        # extracted_specs = self._extract_insights_fallback(response)

        # FIXED (ADD THIS):
        question_text = getattr(project, "current_question_text", None)
        question_metadata = getattr(project, "current_question_metadata", {})

        logger.debug(f"Processing response with question context:")
        logger.debug(f"  Question: {question_text}")
        logger.debug(f"  Category: {question_metadata.get('category', 'unknown')}")
        logger.debug(f"  Target field: {question_metadata.get('target_field', 'unknown')}")

        extracted_specs = self._extract_insights_fallback(
            response_text=response,
            question_text=question_text,
            question_metadata=question_metadata,  # NEW PARAMETER
        )
        logger.info(f"Extracted specs from response: {extracted_specs}")
```

---

### STEP 4: Implement Context-Aware Specs Extraction

**File:** `backend/src/socrates_api/orchestrator.py`
**Location:** Replace `_extract_insights_fallback()` method (currently at line 2275)

```python
def _extract_insights_fallback(
    self,
    response_text: str,
    question_text: str = None,
    question_metadata: Dict[str, Any] = None,
) -> Dict[str, Any]:
    """
    Extract specs from user response using question context.

    Args:
        response_text: The user's response text (e.g., "+ -")
        question_text: The question that was asked (e.g., "What operations would you want?")
        question_metadata: Metadata about the question including category and target field

    Returns:
        Dictionary with extracted specs: {goals, requirements, tech_stack, constraints}
    """

    import json
    import re

    logger.debug(f"Extracting insights from: '{response_text}' (question_category: {question_metadata.get('category') if question_metadata else 'none'})")

    # Initialize empty specs structure
    empty_specs = {
        "goals": [],
        "requirements": [],
        "tech_stack": [],
        "constraints": []
    }

    # Handle empty response
    if not response_text or not response_text.strip():
        logger.debug("Empty response text, returning empty specs")
        return empty_specs

    # Determine target field from question metadata
    target_field = None
    category = None

    if question_metadata:
        target_field = question_metadata.get("target_field")
        category = question_metadata.get("category")
        logger.debug(f"Using question metadata: target_field={target_field}, category={category}")

    # If we have a target field, use category-specific parsing
    if target_field and category:
        return self._extract_specs_by_category(
            response_text=response_text,
            category=category,
            target_field=target_field,
            question_text=question_text
        )

    # Fallback: Try to detect category from question
    if question_text:
        detected_category = self._detect_question_category(question_text)
        detected_field = self._map_category_to_field(detected_category)

        logger.debug(f"Detected category from question: {detected_category} → field: {detected_field}")

        return self._extract_specs_by_category(
            response_text=response_text,
            category=detected_category,
            target_field=detected_field,
            question_text=question_text
        )

    # Last resort: Use generic LLM-based extraction
    logger.debug("No question context available, using generic LLM extraction")
    return self._generic_llm_extraction(response_text)

def _extract_specs_by_category(
    self,
    response_text: str,
    category: str,
    target_field: str,
    question_text: str = None
) -> Dict[str, Any]:
    """Extract specs based on question category with targeted parsing"""

    empty_specs = {
        "goals": [],
        "requirements": [],
        "tech_stack": [],
        "constraints": []
    }

    logger.debug(f"Extracting {category} specs from response: '{response_text}'")

    # Category-specific extraction
    if category == "operations":
        items = self._parse_comma_or_symbol_separated(response_text)
        items = self._expand_symbols(items)
        logger.debug(f"Parsed operations: {items}")
        empty_specs[target_field] = items
        return empty_specs

    elif category == "goals":
        goals = self._parse_goal_statement(response_text)
        logger.debug(f"Parsed goals: {goals}")
        empty_specs[target_field] = goals
        return empty_specs

    elif category == "requirements":
        requirements = self._parse_requirement_list(response_text)
        logger.debug(f"Parsed requirements: {requirements}")
        empty_specs[target_field] = requirements
        return empty_specs

    elif category == "constraints":
        constraints = self._parse_constraint_list(response_text)
        logger.debug(f"Parsed constraints: {constraints}")
        empty_specs[target_field] = constraints
        return empty_specs

    elif category == "tech_stack":
        tech_items = self._parse_comma_or_symbol_separated(response_text)
        logger.debug(f"Parsed tech stack: {tech_items}")
        empty_specs[target_field] = tech_items
        return empty_specs

    else:
        # Generic category - use generic extraction
        return self._generic_llm_extraction(response_text)

def _parse_comma_or_symbol_separated(self, text: str) -> List[str]:
    """Parse comma-separated or symbol-separated values like '+ -' or 'a, b, c'"""
    import re

    text = text.strip()

    # Handle symbol-separated format: "+ -" → ["+", "-"]
    # Also handle: ", and , or"

    # Split on comma, semicolon, "and", "or", or multiple spaces
    items = re.split(r'[,;\s]+(?:and\s+|or\s+)?', text)

    # Clean up and filter empty items
    items = [item.strip() for item in items if item.strip()]

    logger.debug(f"Parsed items from '{text}': {items}")
    return items

def _expand_symbols(self, items: List[str]) -> List[str]:
    """Expand mathematical/programming symbols to full names"""

    symbol_map = {
        "+": "addition",
        "-": "subtraction",
        "*": "multiplication",
        "x": "multiplication",
        "/": "division",
        "%": "modulo",
        "**": "exponentiation",
        "^": "exponentiation",
        "&&": "logical_and",
        "&": "and",
        "||": "logical_or",
        "|": "or",
        "!": "logical_not",
        "~": "bitwise_not",
        "==": "equals",
        "!=": "not_equals",
        "<": "less_than",
        ">": "greater_than",
        "<=": "less_than_or_equal",
        ">=": "greater_than_or_equal",
    }

    expanded = []
    for item in items:
        if item in symbol_map:
            expanded.append(symbol_map[item])
        else:
            expanded.append(item)

    logger.debug(f"Expanded symbols: {items} → {expanded}")
    return expanded

def _parse_goal_statement(self, text: str) -> List[str]:
    """Parse a goal statement into individual goals"""

    text = text.strip()

    # Single-line goal
    if '\n' not in text and len(text) < 200:
        return [text] if text else []

    # Multiple goals (split on newline or numbering)
    import re
    goals = re.split(r'\n|^\d+\.\s*', text)
    goals = [g.strip() for g in goals if g.strip()]

    logger.debug(f"Parsed goals: {goals}")
    return goals

def _parse_requirement_list(self, text: str) -> List[str]:
    """Parse a requirements list"""

    text = text.strip()

    # Split on newlines or bullet points or numbering
    import re
    requirements = re.split(
        r'\n+|^[\-\*\+]\s*|^\d+\.\s*',
        text
    )
    requirements = [r.strip() for r in requirements if r.strip()]

    # Further split on "and" if single items are long
    final_requirements = []
    for req in requirements:
        if " and " in req and len(req) > 50:
            # Split compound requirements
            parts = re.split(r'\s+and\s+', req)
            final_requirements.extend([p.strip() for p in parts])
        else:
            final_requirements.append(req)

    logger.debug(f"Parsed requirements: {final_requirements}")
    return final_requirements

def _parse_constraint_list(self, text: str) -> List[str]:
    """Parse a constraints list"""
    # Same as requirement parsing for now
    return self._parse_requirement_list(text)

def _detect_question_category(self, question_text: str) -> str:
    """Detect what category a question belongs to based on keywords"""

    if not question_text:
        return "generic"

    q_lower = question_text.lower()

    # Check for each category in order of specificity
    if any(word in q_lower for word in ["operation", "perform", "function", "can do", "compute", "calculate"]):
        return "operations"

    elif any(word in q_lower for word in ["goal", "purpose", "objective", "want to build", "main goal", "aim", "target"]):
        return "goals"

    elif any(word in q_lower for word in ["requirement", "feature", "capability", "need", "should", "must", "requirement"]):
        return "requirements"

    elif any(word in q_lower for word in ["constraint", "limit", "limitation", "restriction", "avoid", "prevent", "not"]):
        return "constraints"

    elif any(word in q_lower for word in ["technology", "tool", "framework", "language", "library", "platform", "use", "tech"]):
        return "tech_stack"

    return "generic"

def _map_category_to_field(self, category: str) -> str:
    """Map question category to project spec field"""

    mapping = {
        "operations": "tech_stack",
        "goals": "goals",
        "requirements": "requirements",
        "constraints": "constraints",
        "tech_stack": "tech_stack",
        "generic": "requirements",  # Default fallback
    }

    return mapping.get(category, "requirements")

def _generic_llm_extraction(self, response_text: str) -> Dict[str, Any]:
    """Fallback: Use LLM to generically extract specs (current behavior)"""

    # This is the existing implementation from earlier in _extract_insights_fallback
    # ... keep existing code ...

    return {
        "goals": [],
        "requirements": [],
        "tech_stack": [],
        "constraints": []
    }
```

---

## TESTING PROTOCOL

### Test Case 1: Operations Question

```
Input:
  Question: "What operations (like adding or subtracting) would you want your calculator to perform?"
  Response: "+ -"

Expected Output:
  specs = {
    "goals": [],
    "requirements": [],
    "tech_stack": ["addition", "subtraction"],
    "constraints": []
  }

Verification:
  - extract_insights_fallback() called with question_metadata
  - Category detected as "operations"
  - Target field mapped to "tech_stack"
  - "+ -" parsed and expanded to ["addition", "subtraction"]
  - Specs saved to database with source_text="+ -"
```

### Test Case 2: Goals Question

```
Input:
  Question: "What is the main goal of your project?"
  Response: "Build a calculator that can perform multiple mathematical operations"

Expected Output:
  specs = {
    "goals": ["Build a calculator that can perform multiple mathematical operations"],
    "requirements": [],
    "tech_stack": [],
    "constraints": []
  }
```

### Test Case 3: Requirements Question

```
Input:
  Question: "What features do you need the application to have?"
  Response: "User interface, real-time calculation, error handling"

Expected Output:
  specs = {
    "goals": [],
    "requirements": ["User interface", "real-time calculation", "error handling"],
    "tech_stack": [],
    "constraints": []
  }
```

---

## MIGRATION PATH

1. **Phase 1:** Add question metadata model to ProjectContext (non-breaking)
2. **Phase 2:** Update question generation to capture metadata (backward compatible)
3. **Phase 3:** Update response processing to pass context (no impact on existing code)
4. **Phase 4:** Implement context-aware extraction (replaces fallback method)
5. **Phase 5:** Test with actual dialogue flow and verify specs are captured

---

## ROLLBACK PLAN

If anything breaks:
1. Remove `question_metadata` parameter from `_extract_insights_fallback()` calls
2. Specs extraction reverts to generic LLM extraction
3. System continues working in "context-unaware" mode (current state)
4. No database changes required

---

## METRICS FOR SUCCESS

- [ ] "+ -" response maps to ["addition", "subtraction"] in tech_stack field
- [ ] Goal statements captured in goals field
- [ ] Requirements lists captured in requirements field
- [ ] Constraint lists captured in constraints field
- [ ] All extracted specs saved to database with proper metadata
- [ ] No regressions in existing dialogue flow
- [ ] API endpoints continue to work

---

## FILES MODIFIED

1. `socratic_system/models.py` - Add question_metadata field (~5 lines)
2. `backend/src/socrates_api/routers/projects_chat.py` - Capture and store metadata (~30 lines)
3. `backend/src/socrates_api/orchestrator.py` - Pass context and implement extraction (~200 lines)

**Total Changes:** ~235 lines across 3 files
**Complexity:** Medium (parsing logic, question categorization)
**Risk Level:** Low (non-breaking changes, fallback available)
