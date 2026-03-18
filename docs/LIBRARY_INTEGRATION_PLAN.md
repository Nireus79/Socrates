# Library Integration Plan for Socrates

## Overview
Integrate 16 extracted features from Socratic libraries back into the main Socrates codebase. This involves replacing internal implementations with library imports while maintaining backward compatibility.

## Integration Strategy

### Phase 1: Replace Internal Implementations with Library Imports

Replace internal modules with adapter/wrapper classes that import from the published libraries.

**Pattern:**
```python
# OLD: from socratic_system.core.workflow_optimizer import WorkflowOptimizer
# NEW: from socratic_workflow.optimization import WorkflowOptimizer
```

## Detailed Feature Mapping

### 1. Workflow Features (socratic-workflow) - 6 features

**Files to integrate:**
- `socratic_system/core/workflow_builder.py`
- `socratic_system/core/workflow_cost_calculator.py`
- `socratic_system/core/workflow_optimizer.py`
- `socratic_system/core/workflow_path_finder.py`
- `socratic_system/core/workflow_risk_calculator.py`
- `socratic_system/core/workflow_integration.py`

**Library to use:** `socratic-workflow`

**Available classes:**
- `WorkflowOptimizer` from `socratic_workflow.optimization.optimizer`
- `CostCalculator` from `socratic_workflow.optimization.cost_calculator`
- `RiskCalculator` from `socratic_workflow.optimization.risk_calculator`
- `PathFinder` from `socratic_workflow.optimization.path_finder`

**Integration approach:**
Create adapter modules that re-export library classes with any needed Socrates-specific extensions.

---

### 2. Learning & Analytics Features - 5 features

**Files to integrate:**
- `socratic_system/core/learning_engine.py` → `socratic-learning`
- `socratic_system/core/learning_integration.py` → `socratic-learning`
- `socratic_system/core/maturity_calculator.py` → `socratic-learning`
- `socratic_system/core/analytics_calculator.py` → `socratic-analyzer`
- `socratic_system/core/analyzer_integration.py` → `socratic-analyzer`

**Libraries to use:**
- `socratic-learning` - Learning system and maturity tracking
- `socratic-analyzer` - Code analysis and quality metrics

**Available classes:**
- `LearningEngine` from `socratic_learning.analytics.learning_engine`
- `MaturityCalculator` from `socratic_learning.analytics.maturity_calculator`
- `AnalyticsCalculator` from `socratic_learning.analytics.analytics_calculator`

---

### 3. Conflict Resolution Features - 1 feature (3 files)

**Files to integrate:**
- `socratic_system/conflict_resolution/detector.py`
- `socratic_system/conflict_resolution/checkers.py`
- `socratic_system/conflict_resolution/rules.py`

**Library to use:** `socratic-conflict`

**Available classes:**
- Conflict detection and resolution logic from `socratic-conflict`

---

### 4. Knowledge Management Features - 1 feature

**File to integrate:**
- `socratic_system/core/insight_categorizer.py`

**Library to use:** `socratic-knowledge`

---

### 5. Other Features - 2 features

**Files to integrate:**
- `socratic_system/core/question_selector.py` → `socratic-learning` or `socratic-agents`
- `socratic_system/core/project_categories.py` → `socratic-analyzer`

---

## Implementation Steps

### Step 1: Create Adapter Modules
For each extracted feature, create an adapter module that:
1. Imports the library version
2. Re-exports with original class name for backward compatibility
3. Adds any Socrates-specific wrapper logic if needed

**Example adapter structure:**
```python
# socratic_system/core/workflow_optimizer.py (NEW - adapter)
"""
Adapter for WorkflowOptimizer from socratic-workflow library.

Maintains backward compatibility while using the library implementation.
"""

from socratic_workflow.optimization.optimizer import WorkflowOptimizer as _WorkflowOptimizer

# Re-export for backward compatibility
WorkflowOptimizer = _WorkflowOptimizer

__all__ = ["WorkflowOptimizer"]
```

### Step 2: Update Dependencies
- Ensure `pyproject.toml` includes all 9 libraries
- Update `requirements.txt` if needed

### Step 3: Test Integration
- Run existing tests to ensure backward compatibility
- Verify that library features work correctly in Socrates context

### Step 4: Documentation
- Update integration documentation
- Document any behavioral changes

---

## Benefits of Integration

✅ **Code Reuse:** Eliminate duplicate code
✅ **Maintainability:** Update features in one place (libraries)
✅ **Consistency:** Ensure same logic across all tools
✅ **Testing:** Libraries are already tested and published
✅ **Collaboration:** Libraries can be used independently or with Socrates

---

## Risk Mitigation

- **Backward Compatibility:** Adapters maintain same interfaces
- **Gradual Migration:** Can integrate one feature at a time
- **Testing:** Comprehensive test coverage for each adapter
- **Documentation:** Clear integration patterns documented

---

## Timeline

- Phase 1: Create adapters for workflow features (6 files)
- Phase 2: Create adapters for learning/analytics (5 files)
- Phase 3: Create adapters for conflict resolution (3 files)
- Phase 4: Create adapters for knowledge/other (3 files)
- Phase 5: Testing and validation
- Phase 6: Documentation update

---

## Success Criteria

✅ All internal implementations replaced with library imports
✅ Backward compatibility maintained
✅ All tests passing
✅ No breaking changes to Socrates API
✅ Features work identically to before

