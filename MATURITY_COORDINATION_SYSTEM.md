# Maturity-Driven Coordination System

## Overview

The Socrates system uses a **dynamic maturity calculation** as the KEY to coordinating 19 specialized agents. Rather than static workflows, agent behavior adapts based on how mature the project is across 4 phases and 5 quality categories.

---

## Where Maturity is Calculated

### Primary Location: `socratic_system/models/project.py:221-246`

```python
def _calculate_overall_maturity(self) -> float:
    """
    Calculate overall project maturity using weighted phase contributions.

    Instead of averaging (which penalizes starting new phases), this uses:
    - All completed phases (with scores) contribute equally
    - Current/active phase (even if just started) contributes its current score
    - Result: advancing to new phases doesn't decrease overall maturity

    Example:
    - Discovery: 100% → overall = 100%
    - Discovery: 100%, Analysis: 0% → overall = 100% (not 50%)
    - Discovery: 100%, Analysis: 30% → overall = (100 + 30) / 2 = 65%
    """
    if not self.phase_maturity_scores:
        return 0.0

    scored_phases = [s for s in self.phase_maturity_scores.values() if s > 0]
    if not scored_phases:
        return 0.0

    return sum(scored_phases) / len(scored_phases)
```

### Data Models: `socratic_system/models/maturity.py`

**CategoryScore** (tracks per-phase quality):
```python
@dataclass
class CategoryScore:
    category: str              # "code_quality", "testing_coverage", etc.
    current_score: float       # 0.0-1.0
    target_score: float        # 0.0-1.0
    confidence: float          # How confident we are in the score
    spec_count: int           # Number of specs in this category
```

**PhaseMaturity** (tracks overall phase progress):
```python
@dataclass
class PhaseMaturity:
    phase: str                                    # "discovery"|"analysis"|"design"|"implementation"
    overall_score: float                          # 0.0-1.0
    category_scores: Dict[str, CategoryScore]    # Per-category scores
    is_ready_to_advance: bool                     # Can move to next phase?
    missing_categories: List[str]                 # Categories below target
    strongest_categories: List[str]               # Categories at/above target
    weakest_categories: List[str]                 # Categories furthest from target
```

### Initialization: `socratic_system/models/project.py`

Project tracks:
```python
self.phase_maturity_scores = {
    "discovery": 0.0,
    "analysis": 0.0,
    "design": 0.0,
    "implementation": 0.0
}

self.category_scores = {
    "discovery": {...},
    "analysis": {...},
    "design": {...},
    "implementation": {...}
}

self.categorized_specs = {}  # Specs organized by phase and category
self.maturity_history = []   # List of MaturityEvent entries
```

---

## The Four Maturity Phases

| Phase | Completion % | Focus | Duration |
|-------|--------------|-------|----------|
| **Discovery** | 0-25% | Problem definition, scope, target audience | Initial analysis |
| **Analysis** | 25-50% | Requirements (functional & non-functional), data analysis | Data gathering |
| **Design** | 50-75% | Technology stack, architecture, integration strategy | Planning |
| **Implementation** | 75-100% | Code development, testing, documentation | Execution |

---

## Five Quality Categories (Per Phase)

Each phase has 5 quality categories tracked independently:

1. **Code Quality** (implementation phase)
   - Assessed by: Code length, TODOs, structure complexity
   - Weak if < 0.6 score

2. **Testing Coverage** (implementation phase)
   - Assessed by: Test presence, assertions, coverage percentage
   - Weak if < 0.6 score

3. **Documentation** (all phases)
   - Assessed by: Docstrings, comments, README, guides
   - Weak if < 0.6 score

4. **Architecture** (design + implementation)
   - Assessed by: Classes, functions, modularity, patterns
   - Weak if < 0.6 score

5. **Performance** (implementation phase)
   - Assessed by: Loop density, import density, optimization
   - Weak if < 0.6 score

---

## How Maturity Drives Agent Coordination

### Step 1: Calculate Current Maturity

**File**: `socratic_system/models/project.py`

```
project.calculate_maturity()
  ├─ Input: phase_maturity_scores = {discovery: 1.0, analysis: 0.3}
  ├─ Calculate: overall_maturity = (1.0 + 0.3) / 2 = 0.65 (65%)
  ├─ Estimate phase: 50-75% → in "design" phase
  └─ Output: PhaseMaturity object with all category breakdowns
```

**Result**:
```python
{
    "current_phase": "analysis",
    "overall_maturity": 0.65,
    "phase_completion": {
        "discovery": 1.0,
        "analysis": 0.3,
        "design": 0.0,
        "implementation": 0.0
    },
    "category_scores": {
        "analysis": {
            "functional_requirements": 0.4,    # WEAK
            "non_functional_requirements": 0.5, # WEAK
            "data_requirements": 0.8            # STRONG
        }
    },
    "weak_categories": [
        "functional_requirements",
        "non_functional_requirements"
    ]
}
```

### Step 2: QualityController Detects Weak Areas

**File**: `Socratic-agents/src/socratic_agents/agents/quality_controller.py`

```
QualityController.detect_weak_areas(code_artifact)
  ├─ Analyze code/specs for 5 categories
  ├─ Calculate per-category scores (0.0-1.0)
  ├─ Estimate maturity phase from average score:
  │   ├─ avg < 0.4  → "discovery"
  │   ├─ avg < 0.6  → "analysis"
  │   ├─ avg < 0.8  → "design"
  │   └─ avg >= 0.8 → "implementation"
  │
  └─ Output: {
      "phase": "analysis",
      "category_scores": {...},
      "weak_categories": [
          "functional_requirements",
          "non_functional_requirements"
      ],
      "weak_severity": [
          ("functional_requirements", 0.4),
          ("non_functional_requirements", 0.5)
      ]
  }
```

### Step 3: SkillGenerator Creates Adaptive Skills

**File**: `Socratic-agents/src/socratic_agents/agents/skill_generator_agent.py`

```
SkillGeneratorAgent.generate(maturity_data, learning_data)
  ├─ Input:
  │   ├─ maturity_data: {
  │   │     "current_phase": "analysis",
  │   │     "weak_categories": ["functional_requirements", "non_functional_requirements"]
  │   │  }
  │   └─ learning_data: {
  │         "learning_velocity": "high",
  │         "engagement_score": 0.8
  │      }
  │
  ├─ Load phase-specific templates:
  │   ├─ Phase "analysis" has 3 skills available:
  │   ├─ 1. "functional_requirements_deep_dive"
  │   ├─ 2. "nonfunctional_requirements_focus"
  │   └─ 3. "data_requirements_analysis"
  │
  ├─ Filter by weak_categories:
  │   ├─ ✓ "functional_requirements_deep_dive" (matches weak category)
  │   ├─ ✓ "nonfunctional_requirements_focus" (matches weak category)
  │   └─ ✗ "data_requirements_analysis" (not weak, skip)
  │
  ├─ Customize from learning_data:
  │   ├─ learning_velocity="high" → skill_intensity="high"
  │   └─ engagement_score=0.8 → confidence = 0.8 + (0.8 * 0.4) = 1.12 (capped at 1.0)
  │
  └─ Output: [
      {
          "skill_id": "functional_requirements_deep_dive",
          "target_agent": "CodeGenerator",
          "trigger_category": "functional_requirements",
          "confidence": 1.0,
          "instructions": "Generate detailed analysis of functional requirements...",
          "config": {"depth": "comprehensive", "focus": "requirements_gaps"}
      },
      {
          "skill_id": "nonfunctional_requirements_focus",
          "target_agent": "CodeGenerator",
          "trigger_category": "non_functional_requirements",
          "confidence": 1.0,
          "instructions": "Focus on non-functional requirements analysis...",
          "config": {"depth": "comprehensive", "focus": "scalability_security"}
      }
  ]
```

### Step 4: Target Agents Receive and Apply Skills

**File**: Target agent implementation (e.g., `CodeGenerator`, `SocraticCounselor`)

```
SocraticCounselor.process(request_with_skills)
  ├─ Receive skill: "functional_requirements_deep_dive"
  ├─ Extract: instructions, config (depth="comprehensive", focus="requirements_gaps")
  │
  ├─ Adjust behavior:
  │   ├─ Question strategy: "deep_exploration" (not generic)
  │   ├─ Question depth: "comprehensive" (more detailed)
  │   └─ Focus areas: ["requirements_gaps", "missing_functionality"]
  │
  ├─ Generate questions:
  │   ├─ "What critical functionality might we be missing?"
  │   ├─ "Are there any edge cases we haven't covered?"
  │   └─ "How will this impact system scalability?"
  │
  └─ Output: [
      {
          "type": "guiding_question",
          "question": "What critical functionality might we be missing?",
          "follow_up": ["edge_cases", "integrations"],
          "skill_applied": "functional_requirements_deep_dive",
          "expected_response_depth": "detailed_analysis"
      },
      ...
  ]
```

### Step 5: Learning Agent Tracks Effectiveness

**File**: `Socratic-agents/src/socratic_agents/agents/learning_agent.py`

```
LearningAgent.track_skill_feedback(skill_id, effectiveness)
  ├─ Input:
  │   ├─ skill_id: "functional_requirements_deep_dive"
  │   ├─ effectiveness: 0.85 (1.0 = perfectly effective, 0.0 = not helpful)
  │   └─ context: {"engagement_increased": true, "requirements_clarity": "improved"}
  │
  ├─ Update skill_effectiveness_history:
  │   └─ {
  │       "skill_id": "functional_requirements_deep_dive",
  │       "confidence": 1.0,
  │       "effectiveness": 0.85,
  │       "times_used": 5,
  │       "avg_effectiveness": 0.82
  │     }
  │
  └─ Track patterns:
      ├─ "When learning_velocity=high, effectiveness improves"
      └─ "This skill works best with CodeGenerator in analysis phase"
```

### Step 6: SkillGenerator Learns and Adapts

**File**: `Socratic-agents/src/socratic_agents/agents/skill_generator_agent.py`

```
SkillGeneratorAgent.evaluate(skill_effectiveness_data)
  ├─ Receive feedback:
  │   ├─ "functional_requirements_deep_dive": 0.85 effective (5 uses)
  │   ├─ "nonfunctional_requirements_focus": 0.72 effective (3 uses)
  │   └─ "data_requirements_analysis": not applied (weak area was not selected)
  │
  ├─ Update confidence scores:
  │   ├─ functional_requirements: confidence +10% (working well)
  │   ├─ nonfunctional_requirements: confidence +5% (okay, could improve)
  │   └─ data_requirements: maintain (not yet targeted)
  │
  ├─ Learn patterns:
  │   ├─ "Phase analysis + high learning_velocity = effective"
  │   ├─ "functional_requirements_deep_dive works for CodeGenerator"
  │   └─ "confidence_score correlates with effectiveness"
  │
  └─ Next generation will:
      ├─ Increase confidence in proven skills
      ├─ Adjust instructions based on what worked
      └─ Target new skills to remaining weak categories
```

---

## Complete Coordination Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        PROJECT & MATURITY TRACKING                          │
│                  (socratic_system/models/project.py)                         │
│                                                                              │
│  phase_maturity_scores = {discovery: 1.0, analysis: 0.3}                    │
│  category_scores = {analysis: {functional_reqs: 0.4, ...}}                  │
│  maturity_history = [MaturityEvent(phase, score, delta, ...)]               │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                   calculate_overall_maturity()
                    (65% = (1.0 + 0.3) / 2)
                               │
                               ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                      QUALITY CONTROLLER AGENT                               │
│           (Socratic-agents/src/agents/quality_controller.py)                │
│                                                                              │
│  detect_weak_areas(code)                                                    │
│  ├─ Analyze code against 5 categories                                       │
│  ├─ Score each category (0.0-1.0)                                           │
│  └─ Identify weak_categories (< 0.6):                                       │
│      └─ ["functional_requirements", "non_functional_requirements"]          │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                    Weak Areas Detected
                               │
                               ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                    SKILL GENERATOR AGENT                                    │
│        (Socratic-agents/src/agents/skill_generator_agent.py)                │
│                                                                              │
│  generate_skills(maturity_data, learning_data)                              │
│  ├─ Input: {phase: "analysis", weak_categories: [...], velocity: "high"}   │
│  ├─ Load templates for "analysis" phase (3 skills)                          │
│  ├─ Filter: Only skills matching weak_categories → 2 skills                 │
│  ├─ Customize: learning_velocity, engagement_score → confidence tuning      │
│  └─ Output: 2 high-confidence skills for weak areas                         │
│      ├─ functional_requirements_deep_dive (confidence: 1.0)                 │
│      └─ nonfunctional_requirements_focus (confidence: 1.0)                  │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                       Skills Generated
                               │
                               ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                    QUALITY CONTROLLER (Apply)                               │
│                                                                              │
│  apply_skills(skills)                                                       │
│  ├─ Log skill application for each skill                                    │
│  ├─ Set quality_focus_area = weak categories                                │
│  └─ Update behavior: "focus on these areas next"                            │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                           Skills Applied
                               │
              ┌────────────────┼────────────────┐
              │                │                │
              ↓                ↓                ↓
   ┌─────────────────┐ ┌─────────────────┐ ┌────────────────┐
   │ CodeGenerator   │ │ SocraticCounselor│ │ CodeValidator  │
   │ (receives skill)│ │ (receives skill) │ │ (receives skill)│
   │                 │ │                  │ │                │
   │ Generates code  │ │ Generates quest- │ │ Validates code │
   │ focused on weak │ │ ions focused on  │ │ focused on weak│
   │ requirements    │ │ weak requirements│ │ requirements   │
   └────────┬────────┘ └────────┬─────────┘ └────────┬───────┘
            │                   │                    │
            └───────────────────┼────────────────────┘
                                │
                        Improved Output
                                │
                                ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                      LEARNING AGENT                                         │
│           (Socratic-agents/src/agents/learning_agent.py)                    │
│                                                                              │
│  track_skill_feedback(skill_id, effectiveness)                              │
│  ├─ functional_requirements_deep_dive: 0.85 effective                       │
│  ├─ nonfunctional_requirements_focus: 0.72 effective                        │
│  └─ Update: skill_effectiveness_history with results                        │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                     Effectiveness Tracked
                               │
                               ↓
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PROJECT MATURITY UPDATE                                  │
│              (socratic_system/models/project.py)                             │
│                                                                              │
│  record_maturity_event(phase, score_before, score_after, event_type)        │
│  ├─ Event: "skill_application_successful"                                   │
│  ├─ Before: analysis phase = 0.3                                            │
│  ├─ After: analysis phase = 0.42 (improved!)                                │
│  ├─ Delta: +0.12 (because skills addressed weak areas)                      │
│  └─ Update: overall_maturity = (1.0 + 0.42) / 2 = 0.71 (71%)                │
│                                                                              │
│  maturity_history.append(MaturityEvent(...))                                │
└──────────────────────────────┬──────────────────────────────────────────────┘
                               │
                        Maturity Updated
                               │
              ┌────────────────┴────────────────┐
              │                                 │
              ↓                                 ↓
    Is phase ready          Continue next
    to advance?             cycle with
                            higher maturity
    Yes: Transition to
    "design" phase
    (triggers new skill
    templates)
```

---

## Where Each Component is Located

### Maturity Calculation
- **Primary**: `socratic_system/models/project.py:221-246` (`_calculate_overall_maturity()`)
- **Data Models**: `socratic_system/models/maturity.py` (CategoryScore, PhaseMaturity)
- **Project Storage**: `socratic_system/models/project.py` (phase_maturity_scores, category_scores)

### Quality Assessment
- **Location**: `Socratic-agents/src/socratic_agents/agents/quality_controller.py`
- **Method**: `detect_weak_areas(code)` → returns (phase, categories, weak_categories)

### Skill Generation
- **Location**: `Socratic-agents/src/socratic_agents/agents/skill_generator_agent.py`
- **Method**: `generate(maturity_data, learning_data)` → returns list of AgentSkill[]
- **Phase 4-6 Extended**: `skill_generator_agent_v2.py` with LLM-powered generation

### Skill Application
- **Location**: Each agent (CodeGenerator, SocraticCounselor, CodeValidator, etc.)
- **Pattern**: Agents check if skills are applied and adjust their `process()` method accordingly

### Learning & Feedback
- **Location**: `Socratic-agents/src/socratic_agents/agents/learning_agent.py`
- **Method**: `track_skill_feedback(skill_id, effectiveness)` → updates effectiveness history

### Orchestration
- **Location**: `socratic_system/orchestration/orchestrator.py`
- **Nexus Integration**: `socratic_system/orchestration/library_integrations.py`

---

## Key Design Principles

### 1. **Dynamic, Not Static**
- Agent behavior changes based on current maturity
- Different skills for each phase
- Adapts to learning patterns

### 2. **Targeted Intervention**
- Skills only generated for weak categories
- Confidence scores guide impact
- Focused effort on actual bottlenecks

### 3. **Self-Improving Loop**
- Skills generate effectiveness data
- Learning agent tracks what works
- Future generations use proven skills

### 4. **Phase-Aware**
- Different skills per maturity phase
- Phase transitions trigger new templates
- Context-specific recommendations

### 5. **Confidence-Driven**
- Every skill has confidence score
- Higher confidence = more reliable
- Can avoid low-confidence skills if needed

---

## How to Use This Knowledge

### For Understanding the System
1. Start with **maturity calculation** (`project.py:221-246`)
2. Understand **QualityController** detection logic
3. See how **SkillGenerator** creates targeted skills
4. Trace how agents **apply skills** and change behavior
5. Follow **LearningAgent** feedback back to SkillGenerator

### For Debugging
1. Check `project.phase_maturity_scores` - what's the current maturity?
2. Run **QualityController.detect_weak_areas()** - what categories are weak?
3. Check **SkillGenerator output** - are the right skills generated?
4. Look at **skill_effectiveness_history** - are skills helping?
5. Trace **maturity_history** - is maturity increasing correctly?

### For Adding New Features
1. Add new category to QualityController assessment
2. Create skill templates in SkillGenerator for that category
3. Target agents receive and implement the new skill
4. Learning agent tracks effectiveness
5. SkillGenerator learns patterns

---

## Files to Read (in order of importance)

1. **Essential** (understand the core):
   - `socratic_system/models/project.py:221-246` - Maturity calculation
   - `socratic_system/models/maturity.py` - Data models
   - `Socratic-agents/src/agents/quality_controller.py` - Weak area detection
   - `Socratic-agents/src/agents/skill_generator_agent.py` - Skill generation

2. **Important** (understand the feedback loop):
   - `Socratic-agents/src/agents/learning_agent.py` - Effectiveness tracking
   - `Socratic-agents/src/agents/base.py` - Base agent interface

3. **Implementation** (see how agents use skills):
   - `Socratic-agents/src/agents/socratic_counselor.py` - Example skill application
   - `Socratic-agents/src/agents/code_generator.py` - Example skill application

4. **Optional** (extended versions):
   - `Socratic-agents/src/agents/skill_generator_agent_v2.py` - LLM-powered skills

---

## Summary

The **maturity-driven coordination system** works like this:

1. **Maturity is calculated** from phase completion and category scores
2. **QualityController detects** which categories are weak
3. **SkillGenerator creates** targeted skills for weak areas
4. **Target agents receive** and apply skills, adjusting behavior
5. **LearningAgent tracks** which skills were effective
6. **SkillGenerator learns** patterns for better future recommendations
7. **Maturity increases** as weak areas improve
8. **Loop repeats** with higher maturity and better-informed skills

This creates a **self-improving system** where agent behavior automatically adapts to project needs without requiring manual intervention or static workflows.
