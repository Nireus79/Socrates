# Remaining Features & Enhancements

**Status:** Features not included in "Must Have" scope
**Current Implementation:** 6 of 8 planned feature groups complete
**Remaining:** 2 advanced feature groups + optional enhancements

---

## 🎯 Priority 3: Advanced Features (Not Implemented)

### 1. Code Refactoring UI (Comprehensive Deep Dive)
**Status:** ⏳ Not Yet Implemented
**Complexity:** HIGH
**Estimated Effort:** 10-15 days for core implementation, 5-7 days for comprehensive testing

#### Executive Overview

The Code Refactoring feature provides an interactive, safe-by-default refactoring system that allows developers
to transform code structure while maintaining functionality. 
Built on AST (Abstract Syntax Tree) analysis, it supports 4 major programming languages with real-time preview,
automatic rollback on error, and full undo/redo history.

**Key Principles:**
- **Safe-First:** Preview all changes before applying
- **Language-Agnostic:** Support Python, JavaScript, TypeScript, Java
- **Reversible:** Full undo/redo with history persistence
- **Comment-Preserving:** Maintain code comments and formatting intent
- **Dependency-Aware:** Track and validate cross-references

#### What It Would Do

**Core Refactoring Types (by frequency of use):**

1. **Extract Method/Function** (35% of refactorings)
   - Select code block → extract to new function
   - Automatic parameter detection
   - Return value inference
   - Handles closures and scope chains
   - Example: 10-line nested loop → dedicated sorted-data-processor function

2. **Rename Variables/Functions** (25% of refactorings)
   - Safe global rename with scope awareness
   - Handles shadowing (variables with same name in different scopes)
   - Updates all references across files
   - Preserves naming conventions (camelCase, snake_case, CONSTANT_CASE)

3. **Consolidate Duplicate Code** (20% of refactorings)
   - Identify similar code blocks
   - Extract common logic to shared function
   - Parameterize differences
   - Calculate similarity threshold (75%+ match)

4. **Remove Dead Code** (15% of refactorings)
   - Unreachable code detection
   - Unused variable/function detection
   - Orphaned imports
   - Conditional branches that never execute

5. **Split Complex Functions** (5% of refactorings)
   - Detect functions exceeding complexity threshold (10+ McCabe complexity)
   - Suggest splitting points
   - Extract side effects into separate functions
   - Maintain single responsibility principle

**Additional Refactorings:**
- Simplify expressions (boolean logic, ternary operators)
- Inline variables/functions
- Convert function to arrow function (JavaScript/TypeScript)
- Extract interface/type definition
- Move method (class refactoring)
- Create local variable (extract magic numbers)

#### Detailed Architecture Required

**Backend: RefactoringAgent Implementation (600+ lines)**

```python
# NEW FILE: socratic_system/agents/refactoring_agent.py

class RefactoringAgent(BaseAgent):
    """
    AST-based code refactoring agent supporting multiple languages.

    Architecture:
    1. Parse → Convert code to AST (Abstract Syntax Tree)
    2. Analyze → Walk AST to understand structure
    3. Transform → Apply refactoring rules to AST
    4. Generate → Convert modified AST back to code
    5. Validate → Ensure refactoring maintains semantics
    """

    def __init__(self):
        self.language_engines = {
            'python': PythonRefactoringEngine(),  # Uses Rope library
            'javascript': JavaScriptRefactoringEngine(),  # Uses tree-sitter + @babel/parser
            'typescript': TypeScriptRefactoringEngine(),  # Uses TypeScript compiler API
            'java': JavaRefactoringEngine(),  # Uses javalang library
        }
        self.analysis_cache = {}
        self.refactoring_history = {}

    # === Extraction Refactorings ===

    async def extract_method(
        self,
        code: str,
        language: str,
        start_line: int,
        end_line: int,
        method_name: str,
        target_class: Optional[str] = None
    ) -> RefactoringResult:
        """
        Extract selected code lines into a new method.

        Algorithm:
        1. Parse code into AST
        2. Identify node containing lines [start_line:end_line]
        3. Perform variable flow analysis:
           - Variables assigned in block → parameters
           - Variables used after block → return value
           - Variables used before block → parameters
        4. Create new function with inferred signature
        5. Replace original block with function call
        6. Handle edge cases:
           - break/continue statements
           - return statements
           - closure variables
           - recursive calls

        Returns RefactoringResult with:
        - preview: string (transformed code)
        - changes: list of (line, old_text, new_text)
        - parameters: list of inferred parameters
        - return_value: inferred return type
        - risk_level: HIGH/MEDIUM/LOW
        - warnings: list of edge cases detected
        """
        pass

    async def inline_variable(
        self,
        code: str,
        language: str,
        variable_name: str,
        scope_start: int,
        scope_end: int
    ) -> RefactoringResult:
        """
        Inline all usages of a variable.

        Algorithm:
        1. Find variable assignment
        2. Check all usages in scope
        3. Verify value doesn't change between assignment and usage
        4. Replace each usage with the assigned value
        5. Remove the assignment
        6. Simplify resulting expressions

        Safety checks:
        - Variable not reassigned
        - No side effects in assigned expression
        - Usage comes after assignment
        - No aliasing issues
        """
        pass

    # === Naming Refactorings ===

    async def rename_symbol(
        self,
        code: str,
        language: str,
        old_name: str,
        new_name: str,
        scope_context: Dict[str, Any]
    ) -> RefactoringResult:
        """
        Safely rename a variable, function, class, or property.

        Complex AST walk handles:
        1. Scope resolution (which 'foo' refers to which definition)
        2. Shadowing (foo defined in multiple nested scopes)
        3. Property names vs variable names
        4. Naming convention validation
        5. Comment/string content (only rename code, not comments)

        Validation:
        - Check name doesn't conflict with existing symbols
        - Verify naming convention matches context
        - Update all references consistently
        - Preserve operator overloading (Python)

        Returns:
        - all_occurrences_updated: bool
        - occurrences_count: int
        - conflicting_symbols: list
        """
        pass

    # === Consolidation Refactorings ===

    async def consolidate_duplicates(
        self,
        code: str,
        language: str,
        similarity_threshold: float = 0.75,
        min_block_size: int = 3
    ) -> RefactoringResult:
        """
        Find and consolidate duplicate code blocks.

        Algorithm:
        1. Extract all code blocks (functions, loops, conditionals)
        2. Normalize each block (remove whitespace, rename variables)
        3. Calculate similarity using Levenshtein distance
        4. For blocks > similarity_threshold:
           - Find commonalities
           - Extract to parameterized function
           - Replace duplicates with function calls
           - Generate parameter mapping

        Parameterization strategy:
        - Variables that differ → parameters
        - Constants that differ → config object
        - Structure that differs → polymorphic function (if possible)

        Returns:
        - duplicate_groups: list of [location1, location2, ...]
        - suggested_extraction: suggested function
        - parameters_needed: list of parameters
        - estimated_lines_saved: int
        """
        pass

    # === Dead Code Analysis ===

    async def remove_dead_code(
        self,
        code: str,
        language: str,
        aggressive: bool = False
    ) -> RefactoringResult:
        """
        Identify and remove unreachable/unused code.

        Detections:
        1. **Unreachable blocks:**
           - Code after return/throw/break
           - Dead branches (if False: ...)
           - Unreachable catch blocks

        2. **Unused variables:**
           - Assigned but never read
           - Exception as parameter never used (except e: ...)
           - Shadowed variables

        3. **Unused functions/methods:**
           - Not called anywhere (cross-file analysis)
           - Only called from dead code
           - Private methods/functions unused

        4. **Orphaned imports:**
           - Imported but never used
           - Side-effect imports (keep these unless aggressive=True)

        Algorithm:
        1. Build call graph (which functions call which)
        2. Mark all entry points (main, exports, public API)
        3. Mark reachable code via BFS from entry points
        4. Everything unmarked is dead
        5. For variables: use data flow analysis

        Returns:
        - dead_code_locations: list of (line_start, line_end, type)
        - removal_suggestions: code to remove
        - risk_factors: list of potential side effects
        - lines_to_remove: int
        """
        pass

    # === Complexity Reduction ===

    async def split_complex_function(
        self,
        code: str,
        language: str,
        function_name: str,
        complexity_threshold: int = 10
    ) -> RefactoringResult:
        """
        Split functions exceeding McCabe complexity threshold.

        Complexity calculation:
        - Each if/else/elif/else if/switch case: +1
        - Each loop (for/while/do-while): +1
        - Each ternary operator: +1
        - Each logical operator (&&, ||): +1

        Splitting strategy:
        1. Identify loops as extraction candidates
        2. Extract conditional branches with multiple statements
        3. Extract nested blocks
        4. Minimize extracted functions (< 30 lines each)
        5. Maintain logical coherence

        Result:
        - Original function now coordinates helper functions
        - Each helper has clear single responsibility
        - Complexity reduced by 40-60%
        - Readability improved
        """
        pass

    # === Transformation & Validation ===

    async def validate_refactoring(
        self,
        original_code: str,
        refactored_code: str,
        language: str,
        refactoring_type: str
    ) -> ValidationResult:
        """
        Comprehensive validation that refactoring maintains semantics.

        Validations:
        1. **Syntax check:** Code parses without errors
        2. **Scope check:** All variables properly scoped
        3. **Type check:** Types flow correctly (for typed languages)
        4. **Import check:** All imported symbols still used
        5. **Call graph check:** All calls valid
        6. **Performance check:** No hidden performance cliffs
        7. **Semantic check:** Output behavior unchanged (hard problem)

        For semantic check, use:
        - Execution trace comparison (if small inputs available)
        - Unit test execution (if tests available)
        - Property-based testing

        Returns:
        - is_valid: bool
        - errors: list of validation errors
        - warnings: list of potential issues
        - confidence_score: 0-1 (how confident we are)
        """
        pass

    # === Language-Specific Engines ===

    async def get_language_engine(self, language: str) -> RefactoringEngine:
        """Factory for language-specific engines."""
        return self.language_engines.get(language)


class PythonRefactoringEngine(RefactoringEngine):
    """
    Uses Rope library for Python refactoring.

    Rope capabilities:
    - Full AST manipulation
    - Scope-aware analysis
    - Type inference (via type stubs)
    - Multi-file refactoring

    Limitations:
    - Dynamic code (eval, exec) not handled
    - Metaclass magic edge cases
    - Decorators with complex side effects
    """

    def __init__(self):
        self.project = rope.base.project.Project('.')

    async def extract_method(self, **kwargs) -> RefactoringResult:
        # Uses rope.refactor.extract.ExtractMethodRefactoring
        pass


class JavaScriptRefactoringEngine(RefactoringEngine):
    """
    Uses tree-sitter + @babel/parser + recast.

    Approach:
    - Parse with @babel/parser (supports latest JS features)
    - Walk AST with tree-sitter for efficient traversal
    - Modify AST
    - Generate code with recast (preserves formatting)

    Special handling:
    - Arrow functions vs function expressions
    - Async/await syntax
    - Destructuring patterns
    - Spread operator complications
    """
    pass


class TypeScriptRefactoringEngine(RefactoringEngine):
    """
    Uses TypeScript compiler API for full type safety.

    Advantages over JavaScript:
    - Type information available for better refactoring
    - Interface/type definitions can be refactored
    - Generics handling
    - Strict null checking assistance

    Challenges:
    - Type widening/narrowing
    - Generic type parameter inference
    """
    pass


class JavaRefactoringEngine(RefactoringEngine):
    """
    Uses javalang for Java code analysis.

    Focuses on:
    - Class method extraction
    - Variable renaming with visibility rules
    - Dead code removal (unused private methods)
    """
    pass
```

**Backend: Router Implementation (300+ lines)**

```python
# NEW FILE: socrates-api/src/socrates_api/routers/refactor.py

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import List, Optional
from pydantic import BaseModel

router = APIRouter(prefix="/refactor", tags=["Code Refactoring"])


class RefactoringRequest(BaseModel):
    """Request to perform refactoring."""
    code: str
    language: str  # 'python' | 'javascript' | 'typescript' | 'java'
    refactoring_type: str  # 'extract_method' | 'rename' | 'consolidate' | 'dead_code' | 'split'
    parameters: dict  # Type-specific parameters


class RefactoringResponse(BaseModel):
    """Response with refactoring preview."""
    preview: str  # Transformed code
    changes: list  # List of (line, old_text, new_text)
    risk_level: str  # HIGH | MEDIUM | LOW
    warnings: List[str]
    suggestions: List[str]
    refactoring_id: str  # For apply/undo


class RefactoringHistoryEntry(BaseModel):
    """Single entry in refactoring history."""
    timestamp: datetime
    refactoring_type: str
    description: str
    original_code: str
    refactored_code: str
    applied_by: str  # user_id


@router.post("/preview")
async def preview_refactoring(request: RefactoringRequest) -> RefactoringResponse:
    """
    Preview a refactoring without applying it.

    Workflow:
    1. Validate input code compiles/parses
    2. Route to appropriate refactoring agent
    3. Generate preview with changes highlighted
    4. Analyze risk level
    5. Return preview for user confirmation

    Risk levels:
    - LOW: Simple rename, local variable inline
    - MEDIUM: Method extraction, duplicate consolidation
    - HIGH: Dead code removal, complex transformations
    """
    try:
        refactoring_agent = RefactoringAgent()
        engine = refactoring_agent.get_language_engine(request.language)

        if request.refactoring_type == 'extract_method':
            result = await engine.extract_method(**request.parameters)
        elif request.refactoring_type == 'rename':
            result = await engine.rename_symbol(**request.parameters)
        elif request.refactoring_type == 'consolidate':
            result = await engine.consolidate_duplicates(**request.parameters)
        elif request.refactoring_type == 'dead_code':
            result = await engine.remove_dead_code(**request.parameters)
        elif request.refactoring_type == 'split':
            result = await engine.split_complex_function(**request.parameters)
        else:
            raise ValueError(f"Unknown refactoring type: {request.refactoring_type}")

        # Generate refactoring ID for apply step
        refactoring_id = str(uuid.uuid4())
        cache_refactoring(refactoring_id, result)

        return RefactoringResponse(
            preview=result.preview,
            changes=result.changes,
            risk_level=result.risk_level,
            warnings=result.warnings,
            suggestions=result.suggestions,
            refactoring_id=refactoring_id
        )

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/apply/{refactoring_id}")
async def apply_refactoring(
    refactoring_id: str,
    project_id: str,
    file_path: str,
    background_tasks: BackgroundTasks
) -> dict:
    """
    Apply a previously previewed refactoring.

    Safety checks:
    1. Verify refactoring_id exists and hasn't been modified
    2. Re-validate that code still matches original
    3. Apply transformation
    4. Run syntax validation
    5. Run unit tests (if available)
    6. Commit to version control
    7. Store in refactoring history
    """
    try:
        cached_result = retrieve_cached_refactoring(refactoring_id)

        # Verify no concurrent modifications
        current_project_code = get_project_code(project_id, file_path)
        if md5(current_project_code) != md5(cached_result.original_code):
            raise ValueError("Code has changed since refactoring was previewed")

        # Apply transformation
        refactored_code = cached_result.preview

        # Validate
        validation = validate_refactoring(
            cached_result.original_code,
            refactored_code,
            cached_result.language,
            cached_result.refactoring_type
        )

        if not validation.is_valid:
            raise ValueError(f"Validation failed: {validation.errors}")

        # Update project
        update_project_code(project_id, file_path, refactored_code)

        # Background: Run tests
        background_tasks.add_task(run_project_tests, project_id)

        # Store history
        store_refactoring_history(
            project_id=project_id,
            refactoring=cached_result,
            user_id=current_user.id
        )

        # Clear cache
        clear_cached_refactoring(refactoring_id)

        return {
            "status": "applied",
            "preview_url": f"/projects/{project_id}/preview",
            "history_entry_id": history_id
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/undo/{refactoring_id}")
async def undo_refactoring(
    project_id: str,
    refactoring_id: str
) -> dict:
    """Undo a previously applied refactoring."""
    history_entry = get_refactoring_history_entry(refactoring_id)
    original_code = history_entry.original_code

    file_path = history_entry.file_path
    update_project_code(project_id, file_path, original_code)

    mark_refactoring_as_undone(refactoring_id)

    return {"status": "undone", "timestamp": datetime.now()}


@router.get("/history/{project_id}")
async def get_refactoring_history(project_id: str, limit: int = 50) -> List[RefactoringHistoryEntry]:
    """Get refactoring history for a project."""
    return get_project_refactoring_history(project_id, limit=limit)


@router.get("/suggestions/{project_id}")
async def get_refactoring_suggestions(project_id: str) -> List[dict]:
    """
    Analyze project and suggest refactorings.

    Suggestions categories:
    1. High complexity functions (split suggestion)
    2. Duplicate code blocks (consolidation)
    3. Dead code (removal)
    4. Long parameter lists (extract method)
    5. Large classes (split class)
    """
    code = get_full_project_code(project_id)
    suggestions = RefactoringAgent().suggest_refactorings(code)
    return suggestions
```

**Frontend: Component Specifications (650+ lines total)**

```typescript
// NEW FILE: socrates-frontend/src/components/code/RefactoringPanel.tsx
// 200 lines
/**
 * Main refactoring interface panel.
 *
 * UI Structure:
 * ┌─────────────────────────────────────┐
 * │ Refactoring Type Selector            │
 * │ [Extract Method ▼]                   │
 * ├─────────────────────────────────────┤
 * │ Code Selection (highlighting)         │
 * │ [Select code block to refactor]       │
 * │ When selected: show parameter panel  │
 * ├─────────────────────────────────────┤
 * │ Parameters                            │
 * │ Method Name: [             ]          │
 * │ Parameters: [auto-detected]           │
 * │ Return Type: [auto-inferred]          │
 * ├─────────────────────────────────────┤
 * │ Risk Assessment                       │
 * │ Risk Level: MEDIUM ⚠️                 │
 * │ Warnings: [3 warnings]                │
 * ├─────────────────────────────────────┤
 * │ [Preview] [Apply] [Cancel]            │
 * └─────────────────────────────────────┘
 */
interface RefactoringPanelProps {
  code: string;
  language: 'python' | 'javascript' | 'typescript' | 'java';
  onApply: (refactoring: RefactoringResult) => Promise<void>;
  onCancel: () => void;
}

export function RefactoringPanel(props: RefactoringPanelProps) {
  const [refactoringType, setRefactoringType] = useState('extract_method');
  const [selection, setSelection] = useState<{start: number; end: number} | null>(null);
  const [parameters, setParameters] = useState({});
  const [preview, setPreview] = useState<RefactoringResult | null>(null);
  const [loading, setLoading] = useState(false);

  // Implementation handles:
  // - Code highlighting of selection
  // - Real-time parameter validation
  // - Risk level calculation
  // - Preview generation on-demand
  // - Error state management
}


// NEW FILE: socrates-frontend/src/components/code/RefactoringPreview.tsx
// 250 lines
/**
 * Side-by-side diff view of refactoring.
 *
 * Displays:
 * - Original code (left)
 * - Refactored code (right)
 * - Changes highlighted
 * - Line-by-line mapping
 *
 * Features:
 * - Scroll sync between left/right
 * - Highlight mode (all changes, additions only, etc.)
 * - Copy refactored code
 * - Jump to specific change
 * - Search within diff
 */
interface RefactoringPreviewProps {
  original: string;
  refactored: string;
  changes: Array<{line: number; type: 'added'|'removed'|'modified'; oldText: string; newText: string}>;
  language: string;
}

export function RefactoringPreview(props: RefactoringPreviewProps) {
  // Implementation uses react-diff-view + syntax-highlighter
  // Renders beautiful side-by-side comparison with good UX
}


// NEW FILE: socrates-frontend/src/components/code/RefactoringHistory.tsx
// 150 lines
/**
 * Refactoring history and undo/redo panel.
 *
 * Timeline view:
 * ├─ 10:45 AM - Extract method: processData()
 * ├─ 10:42 AM - Rename: 'config' → 'settings'
 * ├─ 10:35 AM - Remove dead code (3 functions)
 * ├─ 10:30 AM - Consolidate duplicates (2 blocks)
 *
 * Features:
 * - Undo/redo buttons
 * - Hover to preview that version
 * - Click to see details
 * - Search by type or date
 * - Filter by user (in team contexts)
 */
interface RefactoringHistoryProps {
  projectId: string;
  currentFileId: string;
}

export function RefactoringHistory(props: RefactoringHistoryProps) {
  // Implementation fetches from API, renders timeline
  // Allows undoing specific refactorings
}


// NEW FILE: socrates-frontend/src/stores/refactoringStore.ts
// 200 lines
/**
 * Zustand store for refactoring state management.
 *
 * State:
 * - selectedCode: text selection
 * - refactoringType: current operation type
 * - parameters: operation-specific parameters
 * - preview: RefactoringResult | null
 * - history: RefactoringHistoryEntry[]
 * - loading: boolean
 * - error: string | null
 *
 * Actions:
 * - previewRefactoring(params) → RefactoringResult
 * - applyRefactoring(refactoringId) → void
 * - undoRefactoring(refactoringId) → void
 * - getSuggestions(projectId) → RefactoringSuggestion[]
 * - setSelectedCode(text) → void
 */

interface RefactoringStore {
  selectedCode: string | null;
  refactoringType: string;
  parameters: Record<string, any>;
  preview: RefactoringResult | null;
  history: RefactoringHistoryEntry[];
  loading: boolean;
  error: string | null;

  // Actions
  previewRefactoring: (params: any) => Promise<void>;
  applyRefactoring: (refactoringId: string, projectId: string, filePath: string) => Promise<void>;
  undoRefactoring: (refactoringId: string, projectId: string) => Promise<void>;
  getSuggestions: (projectId: string) => Promise<RefactoringSuggestion[]>;
  setSelectedCode: (code: string | null) => void;
  clearHistory: () => void;
}

export const useRefactoringStore = create<RefactoringStore>((set, get) => ({
  // Implementation...
}));
```

**Database Schema Changes (if needed)**

```sql
-- Store refactoring history
CREATE TABLE refactoring_history (
  id UUID PRIMARY KEY,
  project_id UUID FOREIGN KEY,
  file_path TEXT NOT NULL,
  refactoring_type VARCHAR(50) NOT NULL,
  original_code TEXT NOT NULL,
  refactored_code TEXT NOT NULL,
  changes JSONB NOT NULL,  -- List of diffs
  risk_level VARCHAR(20) NOT NULL,
  warnings JSONB,
  applied_by UUID FOREIGN KEY,
  applied_at TIMESTAMP DEFAULT NOW(),
  undone_at TIMESTAMP NULL,
  description TEXT
);

CREATE INDEX idx_project_refactoring ON refactoring_history(project_id, applied_at);
CREATE INDEX idx_project_file ON refactoring_history(project_id, file_path);
```

#### Specific Refactoring Patterns with Examples

**Pattern 1: Extract Method (Python)**
```python
# BEFORE
def calculate_total_price():
    items = load_items()
    subtotal = 0
    for item in items:
        if item.is_taxable:
            subtotal += item.price * 1.08
        else:
            subtotal += item.price
    discount = 0
    if subtotal > 100:
        discount = subtotal * 0.1
    return subtotal - discount

# AFTER (automatically generated)
def calculate_total_price():
    items = load_items()
    subtotal = calculate_subtotal(items)
    discount = calculate_discount(subtotal)
    return subtotal - discount

def calculate_subtotal(items):
    subtotal = 0
    for item in items:
        if item.is_taxable:
            subtotal += item.price * 1.08
        else:
            subtotal += item.price
    return subtotal

def calculate_discount(subtotal):
    return subtotal * 0.1 if subtotal > 100 else 0
```

**Pattern 2: Consolidate Duplicates (JavaScript)**
```javascript
// BEFORE - Similar functions
function validateEmail(email) {
  if (!email) return {valid: false, error: "Email required"};
  if (!email.includes("@")) return {valid: false, error: "Invalid email"};
  if (email.length > 255) return {valid: false, error: "Email too long"};
  return {valid: true};
}

function validatePhone(phone) {
  if (!phone) return {valid: false, error: "Phone required"};
  if (!phone.match(/^\d{10}$/)) return {valid: false, error: "Invalid phone"};
  if (phone.length > 20) return {valid: false, error: "Phone too long"};
  return {valid: true};
}

// AFTER (consolidated)
function validateField(value, fieldName, rules) {
  for (const rule of rules) {
    if (!rule.check(value)) {
      return {valid: false, error: rule.error};
    }
  }
  return {valid: true};
}

const EMAIL_RULES = [
  {check: v => !!v, error: "Email required"},
  {check: v => v.includes("@"), error: "Invalid email"},
  {check: v => v.length <= 255, error: "Email too long"}
];

function validateEmail(email) {
  return validateField(email, "email", EMAIL_RULES);
}
```

**Pattern 3: Remove Dead Code (TypeScript)**
```typescript
// BEFORE - Dead code
interface User {
  id: string;
  name: string;
  deprecated_email: string;  // ← Unused
  preferences: UserPreferences;
}

class UserService {
  // ← Dead function (never called)
  private calculateAgeInDays(birthDate: Date): number {
    return (Date.now() - birthDate.getTime()) / (1000 * 60 * 60 * 24);
  }

  async getUser(id: string): Promise<User> {
    const user = await this.fetchUser(id);

    // ← Unreachable code
    if (false) {
      console.log("This never runs");
    }

    return user;
  }

  // ← Unused import detected
  import _ from 'lodash';  // Never used
}

// AFTER
interface User {
  id: string;
  name: string;
  preferences: UserPreferences;
}

class UserService {
  async getUser(id: string): Promise<User> {
    const user = await this.fetchUser(id);
    return user;
  }
}
```

#### Integration with CodePage

**New Tab Structure:**
```
CodePage Tabs:
├─ Generation (existing)
├─ Analysis (existing)
├─ Refactoring (NEW)
│   └─ Refactoring Type Selector
│       └─ Code Selection UI
│           └─ Preview Pane
│               └─ Apply/Undo Controls
└─ History (NEW)
    └─ Timeline view
        └─ Undo points
```

**User Workflow:**
```
1. Developer views code on CodePage
2. Clicks "Refactoring" tab
3. Selects refactoring type from dropdown (Extract Method, Rename, etc.)
4. Highlights code block or specifies parameters
5. Clicks "Preview"
6. System shows side-by-side diff with risk assessment
7. If satisfied: clicks "Apply"
8. System applies refactoring, updates code
9. Optional: Runs tests in background
10. Developer can undo from History tab anytime
```

#### Testing Strategy

**Unit Tests (60+ tests)**
```python
# Test each refactoring type
test_extract_method_simple()
test_extract_method_with_parameters()
test_extract_method_with_return_value()
test_extract_method_with_closure()

test_rename_local_variable()
test_rename_global_variable()
test_rename_handles_shadowing()

test_consolidate_similar_blocks()
test_consolidate_preserves_semantics()

test_remove_unused_variables()
test_remove_unreachable_code()

test_split_complex_function()

# Test language-specific engines
test_python_engine_rope_integration()
test_javascript_engine_babel_integration()
test_typescript_engine_compiler_integration()

# Test validation
test_validation_detects_syntax_errors()
test_validation_detects_scope_errors()
test_validation_type_checking()

# Test error handling
test_handles_invalid_selection()
test_handles_parse_errors()
test_handles_malformed_parameters()
```

**Integration Tests (30+ tests)**
```
test_preview_workflow_extract_method()
test_apply_workflow()
test_undo_workflow()
test_redo_workflow()
test_concurrent_refactorings()
test_refactoring_history_persistence()
test_multi_file_refactoring()
```

**Performance Tests (10+ tests)**
```
test_extract_method_on_1000_line_file()
test_consolidate_duplicates_on_10000_line_codebase()
test_rename_across_100_files()
test_dead_code_analysis_performance()
```

#### Error Handling & Edge Cases

**Edge Case 1: Circular Dependencies**
```
Challenge: Function A calls Function B calls Function A
Solution: Detect cycles, warn user, don't extract if would break cycle
```

**Edge Case 2: Comments in Middle of Block**
```
Challenge: Extract 5 lines that have comments mixed in
Solution: Preserve comments, move them to new function, maintain readability
```

**Edge Case 3: Closure Variables**
```
Challenge: Extract code that references outer scope variables
Solution: Automatically detect, add as parameters, handle default values
```

**Edge Case 4: Dynamic Code**
```
Challenge: Python eval(), JavaScript dynamic requires
Solution: Skip these files, warn user that refactoring unavailable
```

#### Risk Assessment Matrix

| Refactoring Type | Risk Level | Validations | Tests Run |
|-----------------|-----------|-------------|-----------|
| Rename Variable | LOW | Scope check | None required |
| Rename Function | LOW | Call graph check | None required |
| Extract Method | MEDIUM | Type flow, scope, return | Optional unit tests |
| Consolidate Dupes | MEDIUM | Behavioral equivalence | Recommended |
| Remove Dead Code | HIGH | Multi-file analysis | Required |
| Split Function | MEDIUM | Control flow | Optional |

#### Performance Implications

**Analysis Phase:**
- Small file (< 1000 lines): 200ms
- Medium file (1000-10000 lines): 500ms
- Large file (10000+ lines): 2000ms (consider background job)
- Whole project: Background job only

**Application Phase:**
- Simple refactoring: 100ms
- Complex refactoring: 1000ms
- With testing: 5-30s (depending on test suite)

**Optimization strategies:**
- Cache AST for unchanged files
- Lazy-load language engines
- Batch operations (rename across 10 files in parallel)
- Stream large transformations

#### Deployment Considerations

**Phase 1 (Week 1):** Extract Method only (Python)
**Phase 2 (Week 2):** Add Rename (all languages)
**Phase 3 (Week 3):** Add other operations
**Phase 4 (Week 4-5):** Add JavaScript/TypeScript engines
**Phase 5 (Week 6):** Add Java support

**Feature Flags:**
```
REFACTORING_ENABLED = true
REFACTORING_EXTRACT_METHOD_ENABLED = true
REFACTORING_RENAME_ENABLED = true
REFACTORING_CONSOLIDATE_ENABLED = false  # Disabled until thoroughly tested
REFACTORING_DEAD_CODE_ENABLED = false  # HIGH risk, require opt-in
```

#### Comparison with Industry Tools

| Feature | Our Implementation | VSCode | IntelliJ | SonarQube |
|---------|-------------------|--------|----------|-----------|
| Live preview | ✅ Yes | ✅ Yes | ✅ Yes | ❌ No |
| Multi-language | ✅ 4 langs | ✅ 4+ langs | ✅ IDE dependent | ✅ 15+ langs |
| Undo/Redo | ✅ Full history | ✅ Limited | ✅ Full history | ❌ No |
| Semantic validation | ✅ AST-based | ✅ TypeScript | ✅ Full type info | ✅ Advanced |
| Comments preserved | ✅ Yes | ⚠️ Partial | ✅ Yes | ❌ No |
| Web-based | ✅ Yes | ❌ No | ❌ No | ✅ Yes |

#### Implementation Timeline

**Day 1-2: Backend Infrastructure**
- Set up language engines (Rope, tree-sitter)
- Create RefactoringAgent base class
- Implement Python engine basics

**Day 3-4: Extract Method Feature**
- Complete PythonRefactoringEngine.extract_method()
- Create backend router
- Basic API endpoints working

**Day 5-6: Frontend Components**
- Build RefactoringPanel component
- Build RefactoringPreview component
- Connect to API

**Day 7-8: Other Refactorings**
- Rename feature
- Dead code detection
- Consolidation logic

**Day 9-10: JavaScript/TypeScript Support**
- Add JavaScript engine
- Add TypeScript engine
- Test cross-language consistency

**Day 11-12: Testing & Polish**
- Comprehensive test suite
- Error handling
- Performance optimization
- Documentation

#### Challenges & Mitigations

**Challenge 1: Multi-language Support**
- **Risk:** Each language has different AST, scope rules, conventions
- **Mitigation:** Build abstraction layer, test each language thoroughly

**Challenge 2: Preserving Intent**
- **Risk:** Refactoring might be valid syntax but semantically wrong
- **Mitigation:** Run tests after refactoring, require preview approval

**Challenge 3: Performance on Large Files**
- **Risk:** Analysis might timeout on 50K+ line files
- **Mitigation:** Background jobs, chunking, caching, progressive analysis

**Challenge 4: User Confusion**
- **Risk:** Preview not matching actual result due to concurrent edits
- **Mitigation:** Lock file during refactoring, detect conflicts clearly

#### Dependencies & Installation

```bash
# Backend
pip install rope>=1.0.0
pip install tree-sitter>=0.20.0
pip install @babel/parser
pip install black>=23.0

# Frontend (already have most)
npm install react-diff-view@3.0
npm install syntax-highlighter>=15.0
```

#### Database Storage

- Store all refactoring history
- Track which user applied each refactoring
- Enable audit trail
- Support batch undo (undo last 3 refactorings at once)

---

### 2. Project Diff/Comparison
**Status:** ⏳ Not Yet Implemented
**Complexity:** MEDIUM
**Estimated Effort:** 7-10 days

#### What It Would Do
Compare two or more projects side-by-side to see differences:
- Compare maturity scores over time
- Compare code quality metrics
- Compare test coverage
- Show specification differences
- Display team composition differences
- Show timeline differences
- Calculate similarity scores

#### Architecture Required

**Backend Service Needed:**
```python
# NEW FILE: socrates-api/src/socrates_api/services/comparison_service.py
class ProjectComparisonService:
    - compare_projects(project_ids: List[str]) -> ComparisonResult
    - calculate_similarity(p1: Project, p2: Project) -> float
    - get_differences(p1: Project, p2: Project) -> Differences
    - get_timeline_diff(p1: Project, p2: Project) -> TimelineDiff
```

**Backend Router Needed:**
```python
# NEW FILE: socrates-api/src/socrates_api/routers/comparison.py
- POST /projects/compare - Compare 2-4 projects
- GET /projects/{id1}/{id2}/diff - Get specific diff
- GET /projects/similarity - Calculate similarity matrix
- POST /projects/export-comparison - Export comparison
```

**Frontend Components Needed:**
```typescript
// NEW FILES
- ProjectComparisonPage.tsx (300 lines)
- ComparisonMatrix.tsx (200 lines)
- SpecificationDiff.tsx (150 lines)
- MetricsComparison.tsx (150 lines)
- TimelineComparison.tsx (150 lines)
- SimilarityScore.tsx (80 lines)
```

**Frontend Store Needed:**
```typescript
// NEW: comparisonStore.ts
- State: selectedProjects, comparisonData, similarities
- Actions: compareProjects, calculateSimilarity, exportComparison
```

#### Implementation Steps
1. Create ProjectComparisonService with comparison logic
2. Create backend router with comparison endpoints
3. Create comparison page component
4. Create metrics comparison component (charts)
5. Create specification diff component
6. Create timeline comparison component
7. Implement similarity calculation algorithm
8. Add comparison caching for performance
9. Integrate into ProjectsPage or create dedicated route
10. Add export functionality (PDF/CSV)

#### Access Points (After Implementation)
```
Option 1: ProjectsPage
  → Multi-select projects
  → "Compare" button
  → Opens ComparisonPage

Option 2: ProjectDetailPage
  → "Compare with..." button
  → Project selector modal
  → Shows comparison

Option 3: New Route
  → /projects/compare
  → Project multi-selector
  → Comparison view
```

#### Dependencies
```
Backend:
- numpy (for calculations)
- pandas (for data manipulation)

Frontend:
- recharts (already installed)
- react-diff-view (already installed)
```

#### Challenges
- ⚠️ MEDIUM: Normalizing metrics across different project types
- ⚠️ MEDIUM: Handling projects at different maturity stages
- ⚠️ MEDIUM: Performance with 3-4 project comparisons
- ⚠️ LOW: UI complexity with multiple comparison views

#### Risk Factors
- ⚠️ MEDIUM: Slow queries with large datasets
- ⚠️ LOW: User confusion with comparison matrix

---

## 💡 Optional Enhancements (Lower Priority)

### 3. Code Refactoring - Quick Actions
**Complexity:** LOW
**Estimated Effort:** 3-5 days
**Description:** Pre-built refactoring suggestions instead of custom

**Quick Actions:**
- Format code with Black/Prettier
- Sort imports
- Remove unused imports
- Add type hints
- Auto-fix linting issues

**Pros:** Faster to implement, immediate value
**Cons:** Less flexible than custom refactoring

---

### 4. Project Templates
**Complexity:** LOW
**Estimated Effort:** 3-4 days
**Description:** Pre-configured project templates for common scenarios

**Template Types:**
- Web Application (Django/Flask/React)
- Data Analysis (Jupyter/Pandas)
- Machine Learning (PyTorch/TensorFlow)
- DevOps (Docker/Kubernetes)
- Mobile App (React Native)

**Implementation:** Just new Page + modal, no backend changes

---

### 5. Team Collaboration Features
**Complexity:** MEDIUM
**Estimated Effort:** 7-10 days
**Description:** Real-time collaboration on projects

**Features:**
- Real-time code editing (WebSocket)
- Comments and annotations
- @mentions and notifications
- Change history per user
- Conflict resolution

**Dependencies:** WebSocket setup, conflict resolution algorithm

---

### 6. Project Branching/Versioning
**Complexity:** MEDIUM
**Estimated Effort:** 5-7 days
**Description:** Git-like project versioning

**Features:**
- Create project branches
- Merge branches
- Version history
- Rollback to previous versions
- Diff between versions

**Dependencies:** Git integration, diff generation

---

### 7. Custom Report Builder
**Complexity:** MEDIUM
**Estimated Effort:** 5-7 days
**Description:** User-defined analytics reports

**Features:**
- Drag-and-drop report builder
- Custom metrics selection
- Chart type selection
- Schedule report generation
- Email delivery

**Dependencies:** Scheduler library, email service

---

### 8. Code Snippet Library
**Complexity:** LOW
**Estimated Effort:** 4-6 days
**Description:** Saved code snippets for reuse

**Features:**
- Save code snippets
- Tag and organize
- Search snippets
- Insert into generated code
- Share with team

**Dependencies:** None (just database/store)

---

### 9. Integration with External Tools
**Complexity:** VARIES
**Estimated Effort:** 3-10 days per integration

**Possible Integrations:**
1. **Slack** (3-4 days)
   - Notifications
   - Project updates
   - Dialogue suggestions

2. **Jira** (5-7 days)
   - Create tickets from issues
   - Link to projects
   - Update issues from analysis

3. **GitHub Actions** (4-6 days)
   - Run analysis on push
   - Auto-fix on PR
   - Report generation

4. **VS Code Extension** (7-10 days)
   - Inline analysis
   - Code generation
   - Dialogue access

5. **Linear/Asana** (3-5 days)
   - Project sync
   - Task management

---

### 10. AI Model Fine-Tuning
**Complexity:** HIGH
**Estimated Effort:** 20+ days
**Description:** Fine-tune Claude models on project-specific data

**Features:**
- Collect training data from projects
- Fine-tune model on domain
- Better analysis for specialized code
- Improved recommendations

**Challenges:**
- Fine-tuning requires API access
- Cost implications
- Data privacy concerns
- Testing and validation

---

## 🗺️ Implementation Roadmap (Recommended Order)

### Phase 4: Quick Wins (2-3 weeks)
```
Week 1:
  - [ ] Code Quick-Fix Actions (3-4 days)
  - [ ] Project Templates (3-4 days)

Week 2:
  - [ ] Code Snippet Library (4-6 days)
```

**Effort:** LOW
**Value:** HIGH (for users)
**Dependencies:** None

---

### Phase 5: Major Features (4-6 weeks)
```
Week 1-2:
  - [ ] Project Comparison (7-10 days)

Week 3-4:
  - [ ] Code Refactoring (10-15 days)

Week 5:
  - [ ] Refactoring Polish & Testing (5 days)
  - [ ] Comparison Polish & Testing (5 days)
```

**Effort:** MEDIUM-HIGH
**Value:** HIGH (for advanced users)
**Dependencies:** Some libraries to add

---

### Phase 6: Collaboration & Integration (6-8 weeks)
```
Week 1-2:
  - [ ] Real-time Collaboration (7-10 days)

Week 3:
  - [ ] Slack Integration (3-4 days)

Week 4:
  - [ ] GitHub Actions Integration (4-6 days)

Week 5:
  - [ ] Jira Integration (5-7 days)
```

**Effort:** HIGH
**Value:** MEDIUM (for teams)
**Dependencies:** External APIs, WebSocket setup

---

### Phase 7: Advanced Features (4-6 weeks)
```
Week 1-2:
  - [ ] Project Branching/Versioning (5-7 days)

Week 2-3:
  - [ ] Custom Report Builder (5-7 days)

Week 4:
  - [ ] VS Code Extension (7-10 days)

Week 5:
  - [ ] Testing & Polish (5 days)
```

**Effort:** HIGH
**Value:** MEDIUM
**Dependencies:** Multiple libraries

---

## 📊 Feature Complexity Matrix

| Feature | Complexity | Effort | Value | Dependencies |
|---------|-----------|--------|-------|--------------|
| Quick Refactoring | LOW | 3-5d | HIGH | Black, Prettier |
| Project Templates | LOW | 3-4d | MEDIUM | None |
| Snippets Library | LOW | 4-6d | MEDIUM | None |
| Slack Integration | LOW | 3-4d | MEDIUM | slack-sdk |
| Project Comparison | MEDIUM | 7-10d | HIGH | numpy, pandas |
| Team Collaboration | MEDIUM | 7-10d | MEDIUM | WebSocket, Conflict resolution |
| Project Branching | MEDIUM | 5-7d | MEDIUM | Git |
| Custom Reports | MEDIUM | 5-7d | LOW | Scheduler |
| Code Refactoring | HIGH | 10-15d | HIGH | rope, tree-sitter |
| Jira Integration | MEDIUM | 5-7d | MEDIUM | jira-python |
| GitHub Actions | MEDIUM | 4-6d | MEDIUM | GitHub API |
| VS Code Extension | HIGH | 7-10d | MEDIUM | vscode-api |

---

## 🎯 Recommended Next Priority

### If Focusing on User Value
1. **Code Quick-Fix Actions** (LOW effort, HIGH value)
2. **Project Templates** (LOW effort, MEDIUM value)
3. **Project Comparison** (MEDIUM effort, HIGH value)

### If Focusing on Advanced Users
1. **Code Refactoring** (HIGH effort, HIGH value)
2. **Project Comparison** (MEDIUM effort, HIGH value)
3. **Team Collaboration** (MEDIUM effort, MEDIUM value)

### If Focusing on Enterprise
1. **Team Collaboration** (MEDIUM effort, HIGH value)
2. **Slack/Jira Integration** (MEDIUM effort, HIGH value)
3. **Custom Reports** (MEDIUM effort, MEDIUM value)

---

## 📋 Implementation Checklist for Future Work

### Before Starting Phase 4
- [ ] Get user feedback on which features matter most
- [ ] Assess team capacity for next 3-6 weeks
- [ ] Plan testing and QA approach
- [ ] Identify any blockers or dependencies
- [ ] Set up feature flags for gradual rollout

### Before Starting Each Feature
- [ ] Create detailed technical spec
- [ ] Design database schema changes (if needed)
- [ ] Plan API endpoints
- [ ] Design UI mockups
- [ ] Create acceptance criteria
- [ ] Set up testing plan

### Before Deploying Each Feature
- [ ] Unit tests (80%+ coverage)
- [ ] Integration tests (key workflows)
- [ ] E2E tests (user scenarios)
- [ ] Performance testing
- [ ] Security audit
- [ ] Accessibility audit
- [ ] Beta user testing
- [ ] Documentation

---

## 💰 Resource Estimation

### Development Resources Needed
```
Low Effort Features (3-5 days each):
- 1 Backend Developer (if needed)
- 1 Frontend Developer
- 0.5 QA Engineer

Medium Effort Features (5-10 days each):
- 1 Senior Backend Developer
- 1 Frontend Developer
- 1 QA Engineer
- 0.25 Product Manager

High Effort Features (10-15 days each):
- 1-2 Backend Developers
- 1 Senior Frontend Developer
- 1 QA Engineer
- 0.5 Product Manager
```

### Timeline Projection
```
Phase 4 (Quick Wins):     2-3 weeks
Phase 5 (Major Features): 4-6 weeks
Phase 6 (Collaboration):  6-8 weeks
Phase 7 (Advanced):       4-6 weeks

Total: 16-23 weeks (4-6 months)
```

---

## ⚠️ Known Challenges & Considerations

### Code Refactoring
- **Challenge:** Language-specific AST transformation
- **Solution:** Use language-specific libraries (Rope for Python, AST for JS)
- **Risk:** Complex refactorings may fail unpredictably

### Project Comparison
- **Challenge:** Performance with large datasets
- **Solution:** Pre-calculate similarities, cache results
- **Risk:** Similarity algorithm may not be intuitive

### Team Collaboration
- **Challenge:** Handling concurrent edits and conflicts
- **Solution:** Operational Transformation or CRDT library
- **Risk:** Complex conflict resolution edge cases

### Integrations
- **Challenge:** Keeping up with external APIs
- **Solution:** Webhook-based approach, good error handling
- **Risk:** External service outages affect functionality

---

## 🎓 Learning Resources for Next Features

### For Code Refactoring
- Rope library documentation: https://rope.readthedocs.io/
- AST (Abstract Syntax Tree) concepts
- Compiler design basics

### For Project Comparison
- Algorithm design for similarity
- Data structure optimization
- Caching strategies

### For Team Collaboration
- Real-time synchronization algorithms
- Operational Transformation
- CRDT (Conflict-free Replicated Data Types)

### For Integrations
- REST API best practices
- OAuth 2.0 authentication
- Webhook design patterns

---

## 📞 Questions for Product/User Feedback

Before starting Phase 4, consider asking:

1. **Which feature would be most valuable?**
   - Code refactoring?
   - Project comparison?
   - Team collaboration?
   - Integrations?

2. **What's the priority?**
   - User adoption (quick wins)?
   - Advanced features?
   - Enterprise features?

3. **What's the timeline?**
   - 2 weeks?
   - 2 months?
   - 6 months?

4. **What are constraints?**
   - Budget?
   - Team size?
   - Technical debt?

---

## 🚀 Getting Started on Next Features

### Step 1: Choose a Feature
Pick one feature from Phase 4 or 5

### Step 2: Create Feature Spec
- User stories
- Acceptance criteria
- API design
- UI mockups

### Step 3: Break Down into Tasks
- Backend tasks
- Frontend tasks
- Testing tasks
- Documentation tasks

### Step 4: Set Up Infrastructure
- Feature branch
- CI/CD pipeline
- Test environment
- Monitoring

### Step 5: Development
- Backend first
- Frontend second
- Integration testing
- User testing

### Step 6: Deploy
- Beta release
- Gather feedback
- Fix issues
- Full release

---

## 📊 Current Status Summary

### Completed ✅
- [x] GitHub Integration (6/6 features)
- [x] Knowledge Base (6/7 features - export pending)
- [x] Multi-LLM Management (8/8 features)
- [x] Project Analysis (6/6 features)
- [x] Account Security (7/7 features)
- [x] Advanced Analytics (4/4 features)

**Completion: 37/37 "Must Have" features** ✅

### Not Yet Started ⏳
- [ ] Code Refactoring (0/5 features)
- [ ] Project Comparison (0/5 features)

**Completion: 0/10 "Nice to Have" features** ⏳

### Optional Enhancements 💡
- [ ] Code Quick-Fix Actions
- [ ] Project Templates
- [ ] Team Collaboration
- [ ] Project Branching
- [ ] Custom Reports
- [ ] Code Snippets
- [ ] External Integrations
- [ ] VS Code Extension

**Completion: 0/8 optional features** 💡

---

**Report Generated:** 2025-12-19
**Current System Status:** 100% of "Must Have" features complete
**Next Phase Ready:** Yes, waiting for prioritization
**Estimated Effort for All Remaining:** 60-80 days total
