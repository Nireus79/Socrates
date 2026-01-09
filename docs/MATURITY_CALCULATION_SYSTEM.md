# Maturity Calculation System - Complete Technical Documentation

**Version:** 1.0
**Last Updated:** January 2026
**Scope:** Socrates AI System - Project Maturity Calculation Engine

---

## Table of Contents

1. [Overview](#overview)
2. [System Architecture](#system-architecture)
3. [Core Algorithm](#core-algorithm)
4. [Maturity Types and Scoring](#maturity-types-and-scoring)
5. [Confidence and Uncertainty](#confidence-and-uncertainty)
6. [Data Flow](#data-flow)
7. [Category Definitions](#category-definitions)
8. [Thresholds and Warnings](#thresholds-and-warnings)
9. [Analytics and Metrics](#analytics-and-metrics)
10. [Implementation Details](#implementation-details)
11. [Examples](#examples)
12. [API Reference](#api-reference)

---

## Overview

The **Maturity Calculation System** is a sophisticated, confidence-weighted scoring mechanism that measures project progress across multiple phases of the Socratic learning journey. It evaluates project specifications based on their completeness, quality, and user certainty.

### Key Principles

- **Phase-Based**: Projects progress through distinct phases (Discovery → Analysis → Design → Implementation)
- **Category-Driven**: Each phase contains categories that represent different aspects of the project
- **Confidence-Weighted**: Specifications are weighted by their confidence scores to reflect data quality
- **Normalized Scoring**: All projects use a consistent 90-point scale per phase
- **Capped Categories**: Category scores are capped at their targets to prevent single categories from skewing results
- **Goal-Oriented**: Thresholds guide users toward 60% "ready to advance" status

### Quick Facts

| Metric | Value |
|--------|-------|
| **Points per Phase** | 90 (fixed) |
| **Score Range** | 0-100% per phase |
| **Confidence Range** | 0.0-1.0 (Claude: 0.9, Heuristic: 0.7) |
| **Ready Threshold** | 60% |
| **Complete Threshold** | 100% |
| **Warning Threshold** | 40% |
| **Max Warnings** | 3 |

---

## System Architecture

### Component Hierarchy

```
Project Context
├── Phase Maturity Scores (per-phase percentages)
│   ├── Category Scores (per-category breakdown)
│   │   ├── Specifications (individual data points)
│   │   ├── Confidence (weighted average)
│   │   └── Completeness (percentage)
│   ├── Phase Warnings (up to 3)
│   └── Phase Status (Ready/Warning/Critical)
├── Overall Maturity (average of phases)
├── Maturity History (trend data)
└── Analytics Metrics
    ├── Velocity (points per session)
    ├── Total Sessions (Q&A count)
    ├── Average Confidence (overall)
    └── Category Analytics
```

### Key Files

| File | Purpose |
|------|---------|
| `socratic_system/core/maturity_calculator.py` | Main calculation engine |
| `socratic_system/models/maturity.py` | Data models (CategoryScore, PhaseMaturity) |
| `socratic_system/core/project_categories.py` | Category definitions for each phase |
| `socratic_system/core/insight_categorizer.py` | Maps insights to categories with confidence |
| `socratic_system/agents/quality_controller.py` | Orchestration and warnings |
| `socratic_system/ui/maturity_display.py` | Display and visualization logic |
| `socrates-api/src/socrates_api/routers/projects.py` | API endpoints for maturity data |

---

## Core Algorithm

### The Confidence-Weighted, Capped Algorithm

The maturity calculation follows a deterministic, step-by-step process:

### Phase 1: Specification Collection

```python
# For a given phase (e.g., Discovery):
phase_specs = project.categorized_specs.get("discovery", [])

# Each spec has this structure:
{
    "category": "goals",                    # Category name
    "content": "Application should...",     # Spec content
    "confidence": 0.9,                      # Confidence score (0.0-1.0)
    "value": 1.0,                           # Point value (typically 1.0)
    "source_field": "goals",                # Original field name
    "timestamp": "2025-01-09T12:34:56"     # When spec was created
}
```

### Phase 2: Category-Level Scoring

For each category in the phase:

```python
# 1. Collect all specs for this category
category_specs = [s for s in phase_specs if s["category"] == category_name]

# 2. Calculate confidence-weighted sum
weighted_sum = 0.0
for spec in category_specs:
    confidence = spec.get("confidence", 0.9)  # Default to 0.9 if missing
    value = spec.get("value", 1.0)            # Usually 1.0
    contribution = value * confidence
    weighted_sum += contribution

# Example: 10 specs with 0.9 confidence
# weighted_sum = 10 × (1.0 × 0.9) = 9.0

# 3. Cap the score at category target
category_target = category_targets.get(category_name, 15)  # Default 15 if not found
capped_score = min(weighted_sum, category_target)

# Example: min(9.0, 20) = 9.0 points

# 4. Calculate category percentage
category_percentage = (capped_score / category_target) * 100
# Example: (9.0 / 20) * 100 = 45%

# 5. Store category score
category_scores[category_name] = CategoryScore(
    category=category_name,
    current_score=capped_score,
    target_score=category_target,
    confidence=_calculate_category_confidence(category_specs),
    spec_count=len(category_specs),
    percentage=category_percentage,
    is_complete=(capped_score >= category_target)
)
```

### Phase 3: Phase-Level Aggregation

```python
# Sum all capped category scores
total_score = sum(score.current_score for score in category_scores.values())
# Example: 9.0 + 12.5 + 8.0 + 6.5 + ... = 70.5

# Normalize to percentage (90 is the fixed total per phase)
overall_percentage = (total_score / 90.0) * 100.0
# Example: (70.5 / 90) * 100 = 78.3%
```

### Phase 4: Overall Project Maturity

```python
# For each phase with specs (> 0%), get its maturity percentage
phase_percentages = [score for score in phase_scores.values() if score > 0]

# Calculate overall maturity as average
overall_maturity = sum(phase_percentages) / len(phase_percentages)
# Example: (78.3 + 65.2 + 52.1) / 3 = 65.2%
```

### Complete Pseudocode

```python
def calculate_phase_maturity(project, phase_name):
    """
    Calculate maturity for a specific phase.

    Returns: PhaseMaturity object with complete breakdown
    """

    # Get category targets for this project type
    category_targets = get_category_targets(project.project_type, phase_name)

    # Get specs for this phase
    phase_specs = project.categorized_specs.get(phase_name, [])

    if not phase_specs:
        return PhaseMaturity(
            phase=phase_name,
            overall_percentage=0.0,
            category_scores={},
            warnings=["No specifications yet. Answer questions to start."]
        )

    # Calculate scores for each category
    category_scores = {}
    total_score = 0.0
    missing_categories = []

    for category_name, target_score in category_targets.items():
        # Get specs for this category
        category_specs = [s for s in phase_specs if s.get("category") == category_name]

        if not category_specs:
            missing_categories.append(category_name)
            category_scores[category_name] = CategoryScore(
                category=category_name,
                current_score=0.0,
                target_score=target_score,
                confidence=0.0,
                spec_count=0,
                percentage=0.0,
                is_complete=False
            )
            continue

        # Calculate confidence-weighted sum
        weighted_sum = 0.0
        for spec in category_specs:
            confidence = spec.get("confidence", 0.9)
            value = spec.get("value", 1.0)
            weighted_sum += value * confidence

        # Cap at category target
        capped_score = min(weighted_sum, target_score)
        total_score += capped_score

        # Calculate percentage
        percentage = (capped_score / target_score) * 100 if target_score > 0 else 0.0

        # Calculate category confidence (average of all specs)
        confidences = [s.get("confidence", 0.9) for s in category_specs]
        avg_confidence = sum(confidences) / len(confidences)

        # Store category score
        category_scores[category_name] = CategoryScore(
            category=category_name,
            current_score=capped_score,
            target_score=target_score,
            confidence=avg_confidence,
            spec_count=len(category_specs),
            percentage=percentage,
            is_complete=(capped_score >= target_score)
        )

    # Calculate overall percentage
    overall_percentage = (total_score / 90.0) * 100.0 if total_score > 0 else 0.0

    # Generate warnings
    warnings = _generate_warnings(category_scores, missing_categories, overall_percentage)

    # Return results
    return PhaseMaturity(
        phase=phase_name,
        overall_percentage=overall_percentage,
        category_scores=category_scores,
        warnings=warnings,
        missing_categories=missing_categories,
        ready_to_advance=(overall_percentage >= 60.0)
    )
```

---

## Maturity Types and Scoring

### 1. Phase Maturity (Per-Phase Scores)

Each project phase has its own maturity score:

```
Discovery Phase:   0-100%
Analysis Phase:    0-100%
Design Phase:      0-100%
Implementation:    0-100%
```

**Meaning:**
- **0-40%**: Critical gaps, missing essential specifications
- **40-60%**: Adequate foundation but weak areas exist
- **60-80%**: Good coverage, ready to advance
- **80-100%**: Excellent/Complete specification

### 2. Category Maturity

Each category within a phase has its own score:

```
Discovery Phase
├── Goals:                    75% (15/20 points)
├── Requirements:             60% (12/20 points)
├── Target Audience:          85% (12.75/15 points)
├── Constraints:              40% (4/10 points) ⚠️
└── ... (other categories)
```

**Calculation:**
```
category_percentage = (current_score / target_score) × 100
```

### 3. Overall Project Maturity

Average of all phases with specifications:

```
Overall = (Discovery% + Analysis% + Design%) / 3
Example: (75 + 65 + 52) / 3 = 64%
```

**Displayed on:**
- Dashboard
- Project overview page
- Analytics charts

### 4. Maturity Status

| Status | Condition | Color | Action |
|--------|-----------|-------|--------|
| **Critical** | < 40% | Red | Add more specs urgently |
| **Warning** | 40-60% | Yellow | Add specs before advancing |
| **Ready** | 60-100% | Green | Can safely advance phase |
| **Complete** | 100% | Blue | Phase fully specified |

---

## Confidence and Uncertainty

### Understanding Confidence Scores

**Confidence** measures how reliable each specification is. It ranges from **0.0 to 1.0**:

- **1.0**: Completely reliable (rare - reserved for user-verified specs)
- **0.9**: High confidence (Claude-generated specs)
- **0.8-0.85**: Good confidence (refined Claude specs)
- **0.7**: Moderate confidence (Heuristic/fallback specs)
- **0.6**: Low confidence (incomplete categorization)
- **0.0-0.5**: Very low confidence (experimental/unverified)

### How Confidence Affects Scoring

The confidence directly multiplies the spec's contribution:

```
contribution = spec_value × confidence

Example 1: Claude spec (0.9 confidence)
contribution = 1.0 × 0.9 = 0.9 points

Example 2: Heuristic spec (0.7 confidence)
contribution = 1.0 × 0.7 = 0.7 points

Difference: 0.2 points (22% reduction)
```

### Sources of Confidence Scores

#### 1. Claude-Generated Specs (0.9 confidence)

When Claude analyzes user answers:
- Semantic understanding: Analyzes meaning, not just keywords
- Intelligent categorization: Maps insights to appropriate categories
- Contextual awareness: Considers project type and phase
- Multiple-choice extraction: Can find multiple specs per answer

**Example:**
```
User answer: "Our app helps users manage their grocery lists efficiently"

Claude extracts:
1. Spec: "Manage grocery lists" → category: "core_purpose", confidence: 0.9
2. Spec: "Emphasize efficiency" → category: "success_metrics", confidence: 0.9
3. Spec: "User-facing application" → category: "target_audience", confidence: 0.9
```

#### 2. Heuristic/Fallback Specs (0.7 confidence)

When Claude is unavailable or categorization fails:
- Simple field mapping: Direct field-to-category matching
- No semantic analysis: Limited context awareness
- Fallback only: Used when primary method fails
- Pattern matching: Based on keywords and structure

**Example:**
```
User provided: project.goals = ["Reduce costs", "Improve speed"]

Heuristic creates:
1. Spec: "Reduce costs" → category: "goals", confidence: 0.7
2. Spec: "Improve speed" → category: "goals", confidence: 0.7
```

### Uncertainty Detection

When users express uncertainty, the system detects and handles it:

**Detected Uncertainty Phrases:**
- "I don't know"
- "idk"
- "Not sure"
- "No idea"
- "Dunno"
- "Unsure"
- "Haven't thought about it"
- "Not certain"

**System Response:**
```python
# When uncertainty is detected:
return {
    "note": "User expressed uncertainty - may need more guidance",
    "specs_created": 0,
    "maturity_change": 0
}

# No specs are created
# Maturity remains unchanged (neutral, not penalized)
# User receives guidance to provide more information later
```

### Category-Level Confidence

The average confidence for a category is calculated:

```python
category_confidence = sum(spec.confidence for spec in category_specs) / len(category_specs)

Example:
- 10 Claude specs (0.9 each): sum = 9.0
- 5 Heuristic specs (0.7 each): sum = 3.5
- Total: 9.0 + 3.5 = 12.5
- Average: 12.5 / 15 = 0.833 (83.3% confident)
```

### Analytics Confidence Metric

Overall project confidence is tracked:

```python
all_specs = [spec for all_phase_specs in categorized_specs.values()
             for spec in all_phase_specs]

if all_specs:
    avg_confidence = sum(s.get("confidence", 0.9) for s in all_specs) / len(all_specs)
    analytics_metrics["avg_confidence"] = avg_confidence

# Example result: 0.82 (82% average confidence across all specs)
```

---

## Data Flow

### Complete User Input → Maturity Update Flow

```
┌─────────────────────────────────────────────────────────────────┐
│ 1. USER INTERACTION                                             │
│    User answers a question in the Socratic Q&A interface       │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 2. INSIGHT EXTRACTION                                           │
│    - Claude analyzes user response                             │
│    - Extracts relevant insights                                │
│    - Assigns confidence scores (default 0.9)                   │
│                                                                 │
│    Example Output:                                              │
│    [{                                                           │
│      "content": "Build mobile app for iOS/Android",             │
│      "confidence": 0.9,                                         │
│      "category": "platform"                                     │
│    }, ...]                                                      │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 3. UNCERTAINTY DETECTION                                        │
│    - Check if user expressed uncertainty                       │
│    - If "I don't know" → Stop here, return note               │
│    - Otherwise → Continue to categorization                    │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼ (uncertainty not detected)
┌─────────────────────────────────────────────────────────────────┐
│ 4. INSIGHT CATEGORIZATION                                       │
│    - InsightCategorizer receives insights                      │
│    - Maps to phase and category:                               │
│      • Primary: Claude categorization (0.9 confidence)         │
│      • Fallback: Heuristic mapping (0.7 confidence)            │
│    - Creates specs with all metadata                           │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 5. QUALITY CONTROL                                              │
│    - QualityControllerAgent receives categorized specs         │
│    - Validates format and content                              │
│    - Adds to project.categorized_specs[phase]                  │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 6. MATURITY CALCULATION                                         │
│    - MaturityCalculator.calculate_phase_maturity() executes:   │
│      • For each category:                                      │
│        - weighted_sum = Σ(value × confidence)                  │
│        - capped = min(weighted_sum, target)                    │
│        - store category score                                  │
│      • Sum all capped categories                               │
│      • Divide by 90 for percentage                             │
│      • Calculate category breakdown                            │
│    - Generate warnings (priority-ordered)                      │
│    - Calculate overall maturity                                │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 7. PROJECT UPDATES                                              │
│    - project.phase_maturity_scores[phase] = new score         │
│    - project.category_scores[phase] = breakdown                │
│    - project.overall_maturity = average                        │
│    - project.maturity_history.append(delta)                    │
│    - project.analytics_metrics.update(velocity, sessions)      │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 8. EVENT EMISSION                                               │
│    - Emit PHASE_MATURITY_UPDATED                               │
│    - Emit QUALITY_CHECK_WARNING (if warnings exist)            │
│    - Emit PHASE_READY_TO_ADVANCE (if score ≥ 60%)            │
│    - Emit QUESTION_EFFECTIVENESS (analytics)                  │
└──────────────────────┬──────────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────────┐
│ 9. UI UPDATE                                                    │
│    - Frontend receives updated maturity                        │
│    - Display:                                                   │
│      • Progress bar (0-100%)                                   │
│      • Top 3 warnings with icons                               │
│      • Readiness status                                        │
│      • Category breakdown                                      │
│      • Next phase button (if ready)                            │
│    - Optional: Analytics dashboard update                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Category Definitions

### Discovery Phase Categories

| Category | Target | Purpose |
|----------|--------|---------|
| **problem_definition** | 20 | Core problem being solved |
| **target_audience** | 15 | Who will use the solution |
| **goals** | 15 | High-level objectives |
| **competitive_analysis** | 10 | Market landscape |
| **scope** | 12 | What's included/excluded |
| **constraints** | 10 | Limitations and boundaries |
| **success_metrics** | 8 | How to measure success |
| **TOTAL** | **90** | |

**Questions Asked:** ~15-20 (varies based on project type)

### Analysis Phase Categories

| Category | Target | Purpose |
|----------|--------|---------|
| **functional_requirements** | 20 | What the system must do |
| **non_functional_requirements** | 15 | Performance, security, usability |
| **data_requirements** | 12 | Data structures and flow |
| **user_workflows** | 12 | How users interact |
| **technology_stack** | 12 | Recommended technologies |
| **integrations** | 10 | External systems |
| **constraints_validation** | 9 | Feasibility check |
| **TOTAL** | **90** | |

**Questions Asked:** ~20-30

### Design Phase Categories

| Category | Target | Purpose |
|----------|--------|---------|
| **system_architecture** | 18 | High-level structure |
| **database_design** | 15 | Data model and schema |
| **ui_ux_design** | 15 | Interface and experience |
| **api_design** | 12 | Integration points |
| **security_design** | 12 | Protection mechanisms |
| **deployment_strategy** | 10 | Release and infrastructure |
| **testing_strategy** | 8 | Quality assurance approach |
| **TOTAL** | **90** | |

**Questions Asked:** ~25-35

### Implementation Phase Categories

| Category | Target | Purpose |
|----------|--------|---------|
| **feature_breakdown** | 18 | Individual features/tasks |
| **development_timeline** | 15 | Milestones and schedule |
| **team_roles** | 12 | Who does what |
| **code_standards** | 12 | Quality guidelines |
| **testing_plan** | 12 | Test cases and coverage |
| **deployment_plan** | 10 | Release procedures |
| **maintenance_plan** | 8 | Ongoing support |
| **TOTAL** | **90** | |

**Questions Asked:** ~20-30

---

## Thresholds and Warnings

### Maturity Thresholds

```python
# Hard-coded thresholds
READY_THRESHOLD = 60.0          # Minimum to advance
COMPLETE_THRESHOLD = 100.0      # Phase fully mature
WARNING_THRESHOLD = 40.0        # Show strong warning
WEAK_CATEGORY_THRESHOLD = 30.0  # Category needs attention
```

### Threshold Meanings

| Score Range | Status | Message | Recommendation |
|------------|--------|---------|-----------------|
| 0-40% | 🔴 Critical | "Phase maturity very low. Consider answering more questions." | Must add specs |
| 40-60% | 🟡 Warning | "Phase maturity below recommended. You can advance, but prepare for rework." | Can advance but risky |
| 60-80% | 🟢 Ready | "Phase is ready. Use /advance to move to next phase." | Safe to advance |
| 80-100% | 🔵 Complete | "Phase is complete and well-specified." | Fully ready |

### Warning Generation

The system generates up to **3 priority-ordered warnings**:

```python
def _generate_warnings(category_scores, missing_categories, overall_score):
    warnings = []

    # Priority 1: Overall Score Warning
    if overall_score < 40:
        warnings.append(
            "⚠️  Phase maturity very low. "
            "Consider answering more questions to strengthen your specification."
        )
    elif overall_score < 60:
        warnings.append(
            "⚠️  Phase maturity below recommended. "
            "You can advance, but be prepared for rework if gaps emerge."
        )

    # Priority 2: Missing Categories Warning
    if missing_categories:
        missing_str = ", ".join(missing_categories[:5])  # Show first 5
        warnings.append(
            f"⚠️  No coverage in: {missing_str}"
        )

    # Priority 3: Weak Categories Warning
    weak = [c for c, s in category_scores.items()
            if s.spec_count > 0 and s.percentage < 30]
    if weak and len(warnings) < 3:
        weak_str = ", ".join(weak[:3])  # Show first 3
        warnings.append(
            f"⚠️  Weak areas: {weak_str} (< 30%)"
        )

    # Priority 4: Imbalance Warning
    strong = [s for s in category_scores.values() if s.percentage > 80]
    if strong and missing_categories and len(warnings) < 3:
        warnings.append(
            "ℹ️  Some categories well-developed while others missing. "
            "Consider balanced growth."
        )

    return warnings[:3]  # Return top 3 only
```

### Warning Example

For a Discovery phase with 45% maturity:

```
⚠️  Phase maturity below recommended. You can advance, but be prepared for rework.
⚠️  No coverage in: competitive_analysis, success_metrics
⚠️  Weak areas: constraints (15%), scope (25%)
```

---

## Analytics and Metrics

### Tracked Metrics

The system maintains comprehensive analytics:

```python
analytics_metrics = {
    # Maturity metrics
    "current_phase_maturity": 65.2,        # Current phase percentage
    "overall_maturity": 62.5,              # Project average
    "phase_history": {                     # Per-phase progression
        "discovery": [0, 25, 45, 65, 75],
        "analysis": [0, 15, 35, 50]
    },

    # Engagement metrics
    "total_qa_sessions": 12,               # Number of times answered questions
    "sessions_per_phase": {
        "discovery": 8,
        "analysis": 4
    },

    # Velocity metrics
    "velocity": 5.2,                       # Points gained per session
    "velocity_trend": [3.1, 4.5, 5.2],    # Trend over last 3 sessions
    "average_points_per_session": 5.2,

    # Confidence metrics
    "avg_confidence": 0.82,                # Average spec confidence
    "confidence_by_phase": {
        "discovery": 0.85,
        "analysis": 0.78
    },

    # Category analytics
    "strong_categories": [                 # Categories > 80%
        {
            "phase": "discovery",
            "category": "problem_definition",
            "percentage": 95,
            "specs": 15
        }
    ],
    "weak_categories": [                   # Categories < 30%
        {
            "phase": "discovery",
            "category": "constraints",
            "percentage": 15,
            "specs": 2
        }
    ],

    # Missing coverage
    "completely_missing": [                # 0% categories
        {
            "phase": "analysis",
            "category": "integrations",
            "specs": 0
        }
    ]
}
```

### Velocity Calculation

```python
velocity = (new_score - previous_score) / sessions_since_last_calculation

Example:
- Previous phase score: 35%
- Current phase score: 65%
- Sessions since last: 4
- Velocity: (65 - 35) / 4 = 7.5 points per session
```

### Trend Analysis

```python
# Track maturity progression
maturity_history = [
    {"timestamp": "2025-01-01", "phase": "discovery", "score": 25, "delta": +25},
    {"timestamp": "2025-01-03", "phase": "discovery", "score": 45, "delta": +20},
    {"timestamp": "2025-01-05", "phase": "discovery", "score": 65, "delta": +20},
]

# Calculate improvement trend
delta_values = [25, 20, 20]
average_improvement = sum(delta_values) / len(delta_values) = 21.7 points per session
trend = "steady" or "accelerating" or "decelerating"
```

---

## Implementation Details

### Key Classes and Models

#### CategoryScore

```python
@dataclass
class CategoryScore:
    category: str                  # Category name
    current_score: float          # Points earned (0-target)
    target_score: float           # Target points for category
    confidence: float             # Average confidence (0.0-1.0)
    spec_count: int               # Number of specs in category
    percentage: float             # Percentage (0-100%)
    is_complete: bool             # Whether target reached

    # Computed properties
    @property
    def remaining_score(self) -> float:
        """Points needed to reach target"""
        return max(0.0, self.target_score - self.current_score)

    @property
    def specs_needed_estimate(self) -> int:
        """Rough estimate of specs needed to complete"""
        if self.spec_count == 0:
            return math.ceil(self.target_score / 0.9)
        avg_value = self.current_score / self.spec_count
        return math.ceil(self.remaining_score / avg_value)
```

#### PhaseMaturity

```python
@dataclass
class PhaseMaturity:
    phase: str                              # Phase name
    overall_percentage: float               # 0-100%
    category_scores: Dict[str, CategoryScore]  # Breakdown
    warnings: List[str]                     # Up to 3
    missing_categories: List[str]           # Categories with 0 specs
    ready_to_advance: bool                  # >= 60%

    @property
    def status(self) -> str:
        """Returns: critical, warning, ready, or complete"""
        if self.overall_percentage >= 100:
            return "complete"
        elif self.overall_percentage >= 60:
            return "ready"
        elif self.overall_percentage >= 40:
            return "warning"
        else:
            return "critical"
```

#### Project Maturity Fields

```python
class ProjectContext:
    # ... other fields ...

    # Maturity data
    phase_maturity_scores: Dict[str, float] = {
        "discovery": 75.3,
        "analysis": 0.0,  # Not started yet
        "design": 0.0,
        "implementation": 0.0
    }

    category_scores: Dict[str, Dict[str, CategoryScore]] = {
        "discovery": {
            "problem_definition": CategoryScore(...),
            "goals": CategoryScore(...),
            # ... other categories
        }
    }

    overall_maturity: float = 75.3  # Average of phases with specs

    maturity_history: List[Dict] = [
        {
            "timestamp": "2025-01-05T14:30:00",
            "phase": "discovery",
            "old_score": 55.0,
            "new_score": 75.3,
            "delta": +20.3,
            "specs_added": 5,
            "triggered_warnings": ["Weak areas: constraints"]
        }
    ]

    analytics_metrics: Dict = {
        "current_phase_maturity": 75.3,
        "overall_maturity": 75.3,
        "total_qa_sessions": 8,
        "velocity": 9.4,
        "avg_confidence": 0.87,
        "strong_categories": [...],
        "weak_categories": [...]
    }
```

---

## Examples

### Example 1: High Confidence Phase Build-Up

**Scenario:** User completes Discovery phase with Claude questions

**Question:** "What problem does your project solve?"
**Answer:** "Help users manage personal budgets efficiently"

**Claude Extraction:**
```
[
  {
    "content": "Personal budget management",
    "category": "problem_definition",
    "confidence": 0.9
  },
  {
    "content": "Emphasis on efficiency",
    "category": "success_metrics",
    "confidence": 0.9
  }
]
```

**Calculation for problem_definition category (target: 20):**
```
weighted_sum = 1.0 × 0.9 = 0.9 points
capped_score = min(0.9, 20) = 0.9
percentage = (0.9 / 20) × 100 = 4.5%
confidence = 0.9
```

**After 20 questions (20 specs × 0.9 confidence):**
```
weighted_sum = 20 × (1.0 × 0.9) = 18.0 points
capped_score = min(18.0, 20) = 18.0
percentage = (18.0 / 20) × 100 = 90%
confidence = 0.9
status = ready (18/20 points, only 2 away from complete)
```

### Example 2: Mixed Confidence Category

**Scenario:** Category with both Claude and Heuristic specs

**Specs in "Requirements" category (target: 20):**
```
1. "Mobile-first design" (Claude, 0.9) → 0.9 points
2. "Support iOS and Android" (Claude, 0.9) → 0.9 points
3. "Real-time notifications" (Claude, 0.9) → 0.9 points
4. "User registration" (Heuristic, 0.7) → 0.7 points
5. "Payment processing" (Heuristic, 0.7) → 0.7 points
```

**Calculation:**
```
weighted_sum = (3 × 0.9) + (2 × 0.7) = 2.7 + 1.4 = 4.1 points
capped_score = min(4.1, 20) = 4.1
percentage = (4.1 / 20) × 100 = 20.5%
avg_confidence = (0.9 + 0.9 + 0.9 + 0.7 + 0.7) / 5 = 0.82
status = weak (only 20.5%)
```

**Insight:** The 2 heuristic specs contributed less (1.4 points) than if they were Claude specs (1.8 points), a difference of 0.4 points or 2%.

### Example 3: User Uncertainty Handling

**Scenario:** User unsure about constraint

**Q&A:**
```
Socrates: "What are the main constraints (budget, time, resources)?"
User: "I'm not sure about the exact budget right now"
```

**System Response:**
```
1. Detect: "not sure" in response
2. Return: {
     "note": "You expressed uncertainty. Feel free to come back
              to this question later when you have more information.",
     "specs_created": 0,
     "maturity_change": 0
   }
3. Action: Maturity unchanged, user encouraged to return
4. Result: Constraints category still lacks this spec
```

**Later, after user decides:**
```
Q: "What are the constraints?"
A: "Budget is $50k, timeline is 6 months, team is 3 people"

Claude extracts:
[
  {"content": "$50k budget constraint", "category": "constraints", "confidence": 0.9},
  {"content": "6-month timeline", "category": "constraints", "confidence": 0.9},
  {"content": "3-person team limit", "category": "constraints", "confidence": 0.9}
]

Maturity increases by 2.7 points (3 × 0.9)
```

### Example 4: Phase Advancement Decision

**Discovery Phase Status:**
```
Overall: 68% (ready to advance)
Categories:
- problem_definition:    95% (19/20) ✅
- target_audience:       75% (11.25/15) ✅
- goals:                 85% (17/20) ✅
- competitive_analysis:  45% (4.5/10) ⚠️
- scope:                 60% (7.2/12) ⚠️
- constraints:           20% (2/10) ❌
- success_metrics:       50% (4/8) ⚠️

Warnings:
⚠️  No strong warning (above 60%)
⚠️  Weak areas: constraints (20%), competitive_analysis (45%)
ℹ️  Balanced growth recommended in weak areas
```

**User Decision Options:**
1. **Advance Now (68%)** - Risk: rework needed in constraints
2. **Strengthen Weak Areas First** - Add more specs to constraints/competitive_analysis
3. **Advance to Complete (100%)** - Ideal but may take more sessions

**Recommendation:** Based on readiness (≥60%), user can safely advance but should plan to circle back to constraints and competitive analysis during Analysis phase.

### Example 5: Analytics and Trending

**Project over 10 sessions:**
```
Session | Phase      | Score | Delta | Velocity | Confidence
1       | Discovery  | 15    | +15   | 15.0     | 0.90
2       | Discovery  | 28    | +13   | 12.3     | 0.89
3       | Discovery  | 42    | +14   | 13.1     | 0.88
4       | Discovery  | 58    | +16   | 14.5     | 0.87
5       | Discovery  | 72    | +14   | 14.0     | 0.86
6       | Analysis   | 0     | -     | -        | -
7       | Analysis   | 18    | +18   | 18.0     | 0.88
8       | Analysis   | 38    | +20   | 19.0     | 0.87
9       | Analysis   | 55    | +17   | 17.0     | 0.85
10      | Analysis   | 68    | +13   | 13.0     | 0.84

Analysis:
- Average velocity: 15.4 points per session
- Trend: Steady (some variance but consistent)
- Confidence trend: Slight decline (0.90 → 0.84) as more specs added
- Strong phase: Discovery (72%, ready)
- Current focus: Analysis (68%, approaching ready)
```

---

## API Reference

### Maturity Endpoints

#### GET /projects/{project_id}/maturity

Get complete maturity data for a project.

**Response:**
```json
{
  "success": true,
  "data": {
    "project_id": "proj_abc123",
    "phase_maturity_scores": {
      "discovery": 75.3,
      "analysis": 62.5,
      "design": 0.0,
      "implementation": 0.0
    },
    "overall_maturity": 68.9,
    "current_phase": "analysis",
    "category_scores": {
      "discovery": {
        "problem_definition": {
          "current_score": 18.5,
          "target_score": 20,
          "percentage": 92.5,
          "confidence": 0.89,
          "spec_count": 18,
          "is_complete": false
        }
        // ... other categories
      }
    },
    "warnings": [
      "Phase maturity below recommended. You can advance, but be prepared for rework.",
      "No coverage in: integrations"
    ],
    "ready_to_advance": true,
    "analytics_metrics": {
      "current_phase_maturity": 62.5,
      "overall_maturity": 68.9,
      "total_qa_sessions": 10,
      "velocity": 6.2,
      "avg_confidence": 0.85,
      "strong_categories": [...],
      "weak_categories": [...]
    }
  }
}
```

#### GET /projects/{project_id}/maturity/history

Get maturity progression over time.

**Response:**
```json
{
  "success": true,
  "data": {
    "project_id": "proj_abc123",
    "history": [
      {
        "timestamp": "2025-01-05T10:30:00",
        "phase": "discovery",
        "old_score": 55.0,
        "new_score": 65.2,
        "delta": 10.2,
        "specs_added": 5,
        "warnings": ["Weak areas: constraints"]
      }
      // ... more entries
    ]
  }
}
```

#### GET /projects/{project_id}/maturity/analytics

Get detailed analytics and metrics.

**Response:**
```json
{
  "success": true,
  "data": {
    "project_id": "proj_abc123",
    "metrics": {
      "current_phase_maturity": 68.5,
      "overall_maturity": 52.3,
      "total_qa_sessions": 15,
      "velocity": 4.6,
      "velocity_trend": [5.2, 4.8, 4.6, 4.3],
      "avg_confidence": 0.84,
      "strong_categories": [...],
      "weak_categories": [...]
    }
  }
}
```

---

## Conclusion

The Maturity Calculation System is a comprehensive, data-driven approach to measuring project progress. By combining:

- **Weighted confidence** (accounting for data quality)
- **Normalized scoring** (consistent across all projects)
- **Category targets** (ensuring balanced growth)
- **Clear thresholds** (guiding user decisions)
- **Detailed analytics** (tracking engagement and velocity)

The system provides users with accurate, actionable insights into their project's specification maturity and readiness to advance through phases.

### Key Takeaways

1. **Every spec contributes based on confidence**, not just presence
2. **Phases have fixed 90-point scales**, ensuring normalized comparison
3. **60% threshold balances** completion needs vs. user progression
4. **Warnings identify gaps** across 4 priority levels
5. **Analytics drive engagement** by showing velocity and trends

For questions or updates to this documentation, please refer to the main implementation files listed in Section 2.

---

**Document Version:** 1.0
**Created:** January 2026
**Last Modified:** January 2026
**Maintained By:** Socrates Development Team
