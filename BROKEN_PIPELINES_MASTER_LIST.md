# MASTER LIST: All Broken Pipelines in Socrates

**Date:** 2026-04-01
**Investigation Status:** Complete - All broken pipelines identified
**Next Action Required:** Systematic reconnection of all pipelines

---

## SUMMARY

The modularization of Socrates broke **7 critical pipelines**. The system still "works" in the sense that individual endpoints function, but the **interconnected workflows** that made the system intelligent and adaptive are broken.

**Broken Pipelines:**
1. ❌ Dialogue → Specs → Maturity (CRITICAL)
2. ❌ Specs → Maturity Recalculation (CRITICAL)
3. ❌ Code Generation → Quality Control (CRITICAL)
4. ❌ Document Upload → Knowledge Base (CRITICAL)
5. ❌ User Interaction → Learning Analytics (CRITICAL)
6. ❌ Project Lifecycle Events (CRITICAL)
7. ❌ System Monitoring → Alerts (CRITICAL)

---

## PIPELINE #1: DIALOGUE → SPECS EXTRACTION

**Status:** ❌ PARTIALLY FIXED
- I added context-aware specs extraction
- But it's still not connected to the rest of the system

**Monolithic Flow (Feb 2026):**
```
User asks question
    ↓ (SocraticCounselor)
Generate question
    ↓
Store question metadata: {"category": "operations", "target_field": "tech_stack"}
    ↓
User responds: "+ -"
    ↓ (ContextAnalyzer + SocraticCounselor)
Extract specs with CONTEXT
    → Understand "+" means "addition"
    → Map to tech_stack field
    ↓
Return: {"tech_stack": ["addition", "subtraction"]}
    ↓
(THEN TRIGGERS PIPELINE #2)
```

**Current Flow:**
```
User asks question
    ↓
Generate question
    ↓
Store question metadata ✓ (FIXED)
    ↓
User responds: "+ -"
    ↓
Extract specs with CONTEXT ✓ (FIXED)
    ↓
Return: {"tech_stack": ["addition", "subtraction"]} ✓
    ↓
(STOPS HERE - Pipeline #2 not triggered)
```

**Code Location:** `backend/src/socrates_api/orchestrator.py:1798-1873`

**Missing Step:** Does NOT call quality_controller's `update_after_response` ❌

---

## PIPELINE #2: SPECS → MATURITY RECALCULATION (CRITICAL BROKEN)

**Status:** ❌ **COMPLETELY BROKEN** - Silent failure

**What Should Happen:**
```
Specs extracted: {"tech_stack": ["addition", "subtraction"]}
    ↓
quality_controller.update_after_response(insights)
    ↓
QualityController receives request and:
    - Receives extracted specs
    - Analyzes against current project specs
    - Calculates NEW phase maturity score
    - Updates project.phase_maturity_scores
    - Updates project.overall_maturity
    - Emits PROJECT_MATURITY_UPDATED event
    ↓
Project.maturity = NEW VALUE (calculated from new specs)
    ↓
User sees updated maturity in dashboard
```

**What Currently Happens:**
```
Specs extracted: {"tech_stack": ["addition", "subtraction"]}
    ↓
(NO CALL TO quality_controller)
    ↓
Project.maturity = OLD VALUE (unchanged)
    ↓
User sees stale maturity
```

**Code Location:** `backend/src/socrates_api/orchestrator.py:1798-1873`

**The Missing Code:**
```python
# After extracting specs, this should happen but DOESN'T:
maturity_result = orchestrator.process_request(
    "quality_controller",
    {
        "action": "update_after_response",
        "project": project,
        "insights": extracted_specs,
    }
)

if maturity_result.get("status") == "success":
    maturity = maturity_result.get("maturity", {})
    project.phase_maturity_scores = maturity.get("phase_scores")
    project.overall_maturity = maturity.get("overall_score")
    db.save_project(project)
```

**Symptom User Experiences:**
- Dialogue works fine
- Answers are captured
- But maturity score NEVER CHANGES
- User: "Why isn't my progress updating?"

---

## PIPELINE #3: CODE GENERATION → QUALITY CONTROL (BROKEN)

**Status:** ❌ **COMPLETELY BROKEN**

**What Should Happen:**
```
CodeGenerator produces code
    ↓ (Event: CODE_GENERATED)
QualityController listens and:
    - Runs style checks
    - Runs security scans
    - Runs type checking
    - Measures complexity
    - Generates quality report
    ↓
Code updated with issues fixed
Project.code_quality_metrics updated
Event: CODE_QUALITY_REPORT emitted
    ↓
User sees quality warnings/badges
```

**What Currently Happens:**
```
CodeGenerator produces code
    ↓
Code stored directly (NO QUALITY CHECKS)
    ↓
User gets potentially broken/insecure code
```

**Code Location:** `backend/src/socrates_api/routers/code_generation.py`

**Evidence:** No quality controller calls in code generation router

---

## PIPELINE #4: DOCUMENT UPLOAD → KNOWLEDGE BASE (BROKEN)

**Status:** ❌ **COMPLETELY BROKEN** - Vector DB empty

**What Should Happen:**
```
User uploads document or code
    ↓ (Event: DOCUMENT_ADDED)
KnowledgeManager listens:
    - Extracts text from document
    - Chunks text into manageable pieces
    - Generates embeddings
    - Stores in vector database with metadata
    ↓
Vector database grows with project knowledge
    ↓
When question generated:
SocraticCounselor.search_knowledge_base()
    - Finds relevant previous decisions
    - Finds related requirements
    - Finds similar patterns
    ↓
Questions become project-specific
Questions become increasingly sophisticated
```

**What Currently Happens:**
```
User uploads document
    ↓
Document stored (NO VECTOR INDEXING)
    ↓
KnowledgeManager NEVER CALLED
    ↓
Vector database REMAINS EMPTY
    ↓
Questions stay GENERIC
User frustrated: "You're asking the same questions"
```

**Code Location:** `backend/src/socrates_api/routers/knowledge.py`

**Evidence:** No KnowledgeManager event listeners

---

## PIPELINE #5: USER INTERACTION → LEARNING ANALYTICS (BROKEN)

**Status:** ❌ **COMPLETELY BROKEN** - No events emitted

**What Should Happen:**
```
User interactions happen:
    - Asks question
    - Provides response
    - Reviews code
    ↓ (Events emitted: QUESTION_ANSWERED, RESPONSE_QUALITY_ASSESSED, CODE_REVIEWED)
UserLearningAgent listens:
    - Tracks question effectiveness
    - Analyzes response quality
    - Identifies knowledge gaps
    - Detects learning patterns
    - Builds user profile
    ↓
System learns user's:
    - Preferred learning pace
    - Weak areas
    - Misconceptions
    - Learning style
    ↓
SocraticCounselor adjusts:
    - Question difficulty
    - Topic selection
    - Explanation depth
    ↓
System improves over time
```

**What Currently Happens:**
```
User interactions happen
    ↓
NO EVENTS EMITTED
    ↓
UserLearningAgent NEVER TRIGGERED
    ↓
NO DATA COLLECTED
    ↓
System NEVER learns user patterns
    ↓
User always gets same generic questions
User frustration: "Why doesn't it remember anything?"
```

**Code Location:** `backend/src/socrates_api/routers/learning.py`

**Evidence:** Learning endpoints exist but are never called from dialogue/interaction points

---

## PIPELINE #6: PROJECT LIFECYCLE MANAGEMENT (BROKEN)

**Status:** ❌ **COMPLETELY BROKEN** - No initialization/cleanup

**What Should Happen:**
```
Project Created
    ↓ (Event: PROJECT_CREATED)
All agents respond:
    - ProjectManager: initializes structure
    - SystemMonitor: starts tracking
    - KnowledgeManager: prepares knowledge base
    - UserLearningAgent: starts learning session
    - QualityController: initializes maturity scores
    ↓
Project progresses through lifecycle:
    Discovery → Design → Implementation → Deployment
    ↓ (Event: PHASE_CHANGED at each transition)
    QualityController, SystemMonitor update project
    ↓
Project Completed/Deleted
    ↓ (Event: PROJECT_DELETED or PROJECT_COMPLETED)
All agents clean up:
    - KnowledgeManager: removes from vector DB
    - UserLearningAgent: archives learning session
    - SystemMonitor: finalizes metrics
    ↓
Project fully cleaned up
```

**What Currently Happens:**
```
Project Created
    ↓
Project object created in database
    ↓
NO INITIALIZATION EVENTS
    ↓
Agents not notified
    ↓
Project deleted
    ↓
Orphaned data remains in:
    - Vector database
    - Learning sessions
    - Metrics
    ↓
Data corruption
```

**Code Location:** `backend/src/socrates_api/routers/projects.py`

**Evidence:** No event emission on project lifecycle changes

---

## PIPELINE #7: SYSTEM MONITORING & ALERTS (BROKEN)

**Status:** ❌ **COMPLETELY BROKEN**

**What Should Happen:**
```
System events occur:
    - Project stalled (no activity)
    - Quality issues detected
    - User confusion detected
    - Performance degradation
    ↓ (Events: PROJECT_STALLED, QUALITY_ISSUE, etc.)
SystemMonitor listens:
    - Analyzes patterns
    - Detects anomalies
    - Generates alerts
    ↓
Sends notifications to:
    - User
    - Admin
    - Logging system
    ↓
User gets proactive guidance
Admin can intervene
```

**What Currently Happens:**
```
System events occur
    ↓
NO EVENTS EMITTED (no events exist)
    ↓
SystemMonitor has nothing to monitor
    ↓
No alerts generated
    ↓
Silent failures
```

**Code Location:** `backend/src/socrates_api/orchestrator.py`

**Evidence:** SystemMonitor exists but has no event listeners

---

## ROOT CAUSE ANALYSIS

### Why All Pipelines Broke

**In Monolithic System:**
- Single orchestrator instance
- All agents co-located
- Direct method calls
- Event bus for decoupling
- Tight integration

**After Modularization:**
- **External libraries:** socratic-*, socrates-nexus
- **Orchestrator:** Just a wrapper, not a coordinator
- **Agents:** Local copies, disconnected from libraries
- **Event System:** Exists but unused
- **No Integration Points:** Libraries don't call each other

### The Fundamental Issue

The modularization split the system into:
1. External libraries (PyPI packages)
2. API layer (routers)
3. Local agents (socratic_system/)
4. Database layer

**But there's NO COMMUNICATION between them.**

In the monolith:
```
User Request → Orchestrator → Agents → Database → Events → Other Agents → Result
```

After modularization:
```
User Request → API Router ↘
                         → Database (direct read/write)
                External Lib (maybe?) ↗

Local Agents (disconnected)
Events (not used)
Other Agents (not called)
```

---

## RECONNECTION STRATEGY

To fix all pipelines requires reconnecting the flow:

### Layer 1: Event System
- Restore event emission at critical points
- Agents must listen and respond to events
- Events must trigger pipeline steps

### Layer 2: Agent Coordination
- Orchestrator must coordinate agents
- Agents must call each other (quality_controller after specs extraction)
- Maintain state consistency across agents

### Layer 3: Database Hooks
- Database changes must trigger events
- Events must trigger agent actions
- Agents must update database
- Changes must propagate through system

### Layer 4: Integration
- External libraries must be called at right times
- Results must be properly integrated
- State must be maintained across boundaries

---

## IMPLEMENTATION PRIORITY

**CRITICAL (Breaks User Workflows):**
1. ✅ **Pipeline #1 (Partial)** - Context-aware specs extraction (I fixed part of this)
2. ❌ **Pipeline #2** - Maturity recalculation after specs (MUST FIX)
3. ❌ **Pipeline #3** - Code quality control
4. ❌ **Pipeline #4** - Knowledge base integration

**HIGH (Breaks System Adaptation):**
5. ❌ **Pipeline #5** - Learning analytics
6. ❌ **Pipeline #6** - Project lifecycle
7. ❌ **Pipeline #7** - System monitoring

---

## NEXT STEPS

1. **Fix Pipeline #2** (Maturity) - Most critical, most obvious to user
2. **Fix Pipeline #4** (Knowledge Base) - Enables project-specific questions
3. **Fix Pipeline #3** (Quality) - Ensures code is validated
4. **Fix Pipeline #5** (Learning) - Enables system to improve
5. **Fix Pipeline #6** (Lifecycle) - Ensures data consistency
6. **Fix Pipeline #7** (Monitoring) - Enables debugging

---

## CONCLUSION

The system isn't broken in individual components - it's broken in **interconnections**. Each pipeline worked in isolation in the monolith because the agents talked to each other. After modularization, they don't.

**The fix requires reconnecting ALL of these pipelines systematically.**

This is NOT a specs extraction issue or a maturity calculation issue - it's a **SYSTEMIC ARCHITECTURAL ISSUE** with modularization breaking the event-driven coordination that held everything together.
