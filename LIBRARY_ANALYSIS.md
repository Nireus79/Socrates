# Socratic Ecosystem Library Analysis

**Date**: 2026-03-30
**Purpose**: Document what functionality already exists in installed libraries vs. what needs to be implemented

## Installed Packages Summary

```
socratic-agents          0.2.3
socratic-analyzer        0.1.2
socratic-conflict        0.1.3
socratic-core            0.1.2
socratic-docs            0.1.1
socratic-knowledge       0.1.3
socratic-learning        0.1.3
socratic-maturity        0.1.0
socratic-performance     0.1.1
socratic-rag             0.1.1
socratic-security        0.4.0
socratic-workflow        0.1.2
```

---

## Task 3.1: Question Caching - ✅ COMPLETED

### What We Built
- Custom SQLite-based caching system in `backend/src/socrates_api/database.py`
- Question cache table with: cache_id, project_id, phase, category, question_text, created_at, used_count, last_used_at
- Methods: save_cached_question(), get_cached_questions(), increment_question_usage(), clear_question_cache(), prune_question_cache()
- Integrated into orchestrator for cache-first question generation

### Library Capability
- **socratic-performance** (0.1.1) provides:
  - `TTLCache` class with configurable TTL (time-to-live)
  - Basic get/set/delete operations
  - Cache stats and cleanup_expired() method
  - Hit ratio tracking

### Why Custom Implementation Was Correct
- socratic-performance's TTLCache is in-memory only (expires by time)
- Our requirement: persist across sessions, track usage counts, categorize by phase/category
- socratic-performance doesn't meet our persistence/categorization needs
- ✅ Decision: Custom implementation was the right choice

---

## Task 3.2: Phase Completion Detection - ✅ COMPLETED

### What We Built
- Integrated existing `MaturityCalculator` from socratic-maturity library
- Added two orchestrator methods:
  - `calculate_phase_maturity(project)` - Single phase maturity
  - `get_all_phases_maturity(project)` - All phases comparison
- Created two API endpoints:
  - `GET /projects/{id}/maturity/{phase}` - Phase details
  - `GET /projects/{id}/maturity` - All phases summary
- Integrated automatic maturity notifications in dialogue responses

### Library Capability
- **socratic-maturity** (0.1.0) provides:
  - `MaturityCalculator` class (now being used ✅)
  - `calculate_phase_maturity(phase_specs, phase)` - calculates based on spec values in categories
  - Returns: maturity_percentage, category_scores, is_ready, warnings
  - **Thresholds**: 20% = READY, 100% = COMPLETE, 10% = WARNING

- **socratic-learning** (0.1.3) provides:
  - `MaturityCalculator` (same implementation, imported from socratic-maturity)
  - Additional analytics tools but not needed for basic maturity calculation

### Why We Used the Library
- MaturityCalculator already existed and provides exactly what we needed
- Thresholds already defined (20% = ready, 100% = complete)
- Terminal UI (MaturityDisplay) already existed for visualization
- ✅ Decision: Integrated library rather than reimplementing

---

## Task 3.3: Conflict History Tracking - READY FOR IMPLEMENTATION

### What Needs to Be Built
API endpoints and database integration for conflict history, analytics, and insights

### Library Capability - socratic-conflict (0.1.3)
- **HistoryTracker** class (`socratic_conflict.history.tracker`):
  - `add_conflict(conflict)` - Track new conflicts
  - `add_resolution(resolution)` - Track resolution attempts
  - `add_decision(decision)` - Track final decisions
  - `get_conflict_history(conflict_id)` - Get full conflict timeline
  - `get_agent_conflict_history(agent_name)` - Get conflicts by agent
  - `get_statistics()` - **Built-in analytics**:
    - total_conflicts, resolved, unresolved, resolution_rate
    - conflict_types dict, severities dict, strategies_used dict
  - `get_decision_versions(conflict_id)` - Track decision revisions
  - `revert_decision(decision_id, reason)` - Revert with history

- **Data Models**:
  - `Conflict` dataclass: conflict_id, title, description, conflict_type, severity, related_agents, proposals, detected_at
  - `Resolution` dataclass: resolution_id, conflict_id, strategy, confidence (0.0-1.0), votes, created_at
  - `ConflictDecision` dataclass: conflict_id, resolution_id, chosen_proposal_id, decided_by, rationale, version

### Existing Agent Integration Point
- **AgentConflictDetector** in `socratic-agents` (0.2.3):
  - Already instantiated in orchestrator.agents["conflict_detector"]
  - Current actions: "detect", "resolve", "list"
  - `detect_conflicts(items)` - currently detects duplicates only (needs enhancement)
  - `resolve_conflict(conflict_id)` - exists but basic
  - `list_conflicts()` - exists but uses agent's internal list
  - **Opportunity**: Enhance to integrate with socratic-conflict library's HistoryTracker

### Implementation Strategy
1. **Enhance AgentConflictDetector** - Wire to use socratic-conflict HistoryTracker
2. **Add HistoryTracker to database** - Persist tracking data in SQLite
3. **Create API endpoints**:
   - `GET /projects/{id}/conflicts/history` - Get conflict history
   - `GET /projects/{id}/conflicts/analytics` - Get conflict statistics
   - `GET /projects/{id}/conflicts/{conflict_id}/versions` - Get decision versions
4. **Integrate with dialogue flow** - Log conflicts to history automatically

### What Not to Duplicate
- ✅ Use HistoryTracker from socratic-conflict (don't reimplement)
- ✅ Use data models from socratic-conflict (Conflict, Resolution, ConflictDecision)
- ✅ Use AgentConflictDetector from socratic-agents (enhance, don't rewrite)

---

## Task 3.4: Context Analysis Improvements - READY FOR IMPLEMENTATION

### What Needs to Be Built
Confidence scoring for spec extraction, feedback tracking, and accuracy analytics

### Library Capability - socratic-learning (0.1.3) ⭐ PRIMARY SOURCE
- **PatternDetector** class - **Confidence calculation algorithms**:
  - Error patterns: `confidence = min(0.95, error_rate * 2)`
  - Success patterns: `confidence = min(0.95, success_rate)`
  - Performance patterns: `confidence = 0.75` (fixed)
  - Feedback patterns: `confidence = min(0.95, positive_rate)`
  - **Output**: Pattern objects with confidence (0.0-1.0) score

- **Pattern** dataclass (core model):
  - pattern_id, pattern_type, name, description
  - **confidence: float = 0.0** (0.0-1.0 score)
  - occurrence_count, evidence (list of supporting data), metadata
  - Full serialization with to_dict() / from_dict()

- **MetricsCollector** class - Metrics calculation:
  - `calculate_metrics(agent_name, session_id, start_time, end_time)`
  - Tracks: success_rate, avg_duration, min/max duration, cost, user feedback
  - **Returns**: Metric object with all calculated values

- **Models tracking spec extraction**:
  - `average_spec_extraction_count` field exists in models
  - `spec_count` collected in analytics_calculator
  - **Shows**: Ecosystem already tracks spec extraction metrics!

- **Feedback system** (`feedback/` module):
  - `FeedbackCollector` - Collect user feedback
  - `FeedbackAnalyzer` - Analyze feedback patterns

### Library Capability - socratic-analyzer (0.1.2)
- **MetricsCalculator** class:
  - `calculate_complexity(code)` → 0.0-1.0
  - `calculate_maintainability(code)` → 0-100
  - `calculate_security_score(issues_count)` → 0.0-1.0
  - `calculate_overall_quality(...)` → Weighted combination
  - `calculate_metrics(code, ...)` → QualityMetrics object

- **InsightGenerator** class:
  - `generate_insights(analysis_data)` - Creates InsightData objects
  - `prioritize_insights(insights)` - Sort by severity/actionability
  - `summarize_insights(insights)` - Count by category

### Implementation Strategy
1. **Use PatternDetector confidence algorithms** - Foundation for spec extraction confidence:
   - Extract success rate from historical attempts
   - Calculate: `confidence = min(0.95, success_rate)`
   - Apply to each extraction method (ContextAnalyzer, LLM, Hardcoded)

2. **Create spec extraction tracking**:
   - Track extraction method, result, user feedback
   - Calculate accuracy: feedback_correct / total_attempts
   - Store Pattern objects for each extraction attempt

3. **Create API endpoints**:
   - `GET /projects/{id}/specs/extraction-analytics` - Extraction metrics
   - `POST /projects/{id}/specs/{spec_id}/feedback` - Record accuracy feedback
   - `GET /projects/{id}/specs/patterns` - Detected extraction patterns

4. **Integrate with existing feedback system** - Use socratic-learning feedback collector/analyzer

### What Can Be Leveraged
- ✅ PatternDetector confidence calculation algorithms (PRIMARY)
- ✅ Pattern dataclass for storing extraction patterns with confidence
- ✅ MetricsCollector for aggregating extraction metrics
- ✅ FeedbackCollector and FeedbackAnalyzer from socratic-learning
- ✅ InsightGenerator for creating actionable insights from extraction data

### What Needs Custom Implementation
- Spec extraction specific database table (patterns, feedback log)
- Wiring between spec extraction and PatternDetector
- API endpoints for feedback and analytics
- Integration point in orchestrator

---

## Summary of Library Usage by Task

| Task | Library Used | Component | Status |
|------|--------------|-----------|--------|
| 3.1 | N/A | Custom SQLite implementation | ✅ Complete |
| 3.2 | socratic-maturity | MaturityCalculator | ✅ Integrated |
| 3.3 | socratic-conflict | HistoryTracker, Conflict, Resolution | 🔄 Ready to integrate |
| 3.3 | socratic-agents | AgentConflictDetector (enhance existing) | 🔄 Ready to enhance |
| 3.4 | **socratic-learning** | **PatternDetector (confidence algorithms)** ⭐ | 🔄 Primary source |
| 3.4 | socratic-learning | MetricsCollector, FeedbackCollector | 🔄 Ready to use |
| 3.4 | socratic-analyzer | MetricsCalculator, InsightGenerator | 🔄 Ready to use |

---

## Recommendations for Tasks 3.3 & 3.4

### Task 3.3: Conflict History Tracking
- **Database**: Add `conflict_history_entries` table to persist HistoryTracker data
- **Integration**: Wire HistoryTracker into existing conflict detection flow
- **API Endpoints**: 3-4 endpoints for history, analytics, versioning
- **Time Estimate**: 1.5 hours (leveraging library components)

### Task 3.4: Context Analysis Improvements
- **Confidence Scoring**: Use MetricsCalculator as base, extend for specs
- **Feedback System**: Integrate with socratic-learning feedback modules
- **Analytics**: Dashboard showing extraction accuracy trends
- **Time Estimate**: 2 hours (using existing library components)

---

## Key Findings

1. **Maturity Tracking**: ✅ Already implemented in socratic-maturity (Task 3.2 leveraged)
2. **Conflict History**: ✅ HistoryTracker exists in socratic-conflict (Task 3.3 should use)
3. **Conflict Detection Agent**: ✅ AgentConflictDetector exists in socratic-agents (Task 3.3 should enhance)
4. **Confidence Scoring**: ✅ PatternDetector with confidence algorithms in socratic-learning (Task 3.4 PRIMARY SOURCE)
5. **Spec Extraction Tracking**: ✅ Ecosystem already tracks average_spec_extraction_count and spec_count
6. **Quality Metrics**: ✅ MetricsCalculator in socratic-analyzer (Task 3.4 should extend)
7. **Feedback System**: ✅ Full feedback system in socratic-learning (Task 3.4 should integrate)
8. **Performance Caching**: TTLCache exists but correctly not used (in-memory, Task 3.1 needed persistence)

**Critical Insights**:
- **PatternDetector** (socratic-learning) is the primary source for confidence calculation algorithms
- **Ecosystem already tracks spec extraction metrics** - we should use existing infrastructure
- **AgentConflictDetector** already exists - enhance to integrate with HistoryTracker
- Avoid reimplementing; focus on integration and database persistence

**Conclusion**: For Task 3.3 and 3.4, implementation strategy should be:
1. **Task 3.3**: Enhance existing conflict_detector agent to use socratic-conflict HistoryTracker
2. **Task 3.4**: Use PatternDetector confidence algorithms + existing metrics collection + feedback system
3. Add database persistence for history tracking
4. Create API endpoints to expose library functionality
5. No major new algorithms needed - leverage existing ecosystem

---

## Revised Implementation Roadmap for Tasks 3.3 & 3.4

### Task 3.3: Conflict History Tracking
**Scope**: Database persistence + API endpoints for conflict history/analytics

**Database**:
- `conflict_history` table to persist HistoryTracker data (conflicts, resolutions, decisions)
- Track conflict_id, conflict_type, severity, related_agents, timestamp, status

**Code Changes**:
- Enhance `AgentConflictDetector` in socratic-agents to:
  - Initialize HistoryTracker on startup
  - Call `tracker.add_conflict()` when conflicts detected
  - Call `tracker.add_resolution()` and `tracker.add_decision()` on resolution
- Add database methods to persist tracker state
- Wire into orchestrator's conflict detection flow

**API Endpoints** (3-4 endpoints):
- `GET /projects/{id}/conflicts/history` - Get all conflicts for project
- `GET /projects/{id}/conflicts/{conflict_id}/details` - Get conflict with history
- `GET /projects/{id}/conflicts/analytics` - Get statistics and metrics
- `GET /projects/{id}/conflicts/{conflict_id}/versions` - Get decision versions

**Estimated Effort**: 1.5-2 hours (leveraging HistoryTracker + existing agent)

---

### Task 3.4: Context Analysis Improvements
**Scope**: Confidence scoring for specs + extraction analytics + feedback integration

**Confidence Scoring**:
- Use `PatternDetector` algorithms from socratic-learning:
  - Track spec extraction success rate per method
  - Calculate: `confidence = min(0.95, success_rate)`
  - Store results as Pattern objects

**Database**:
- `spec_extraction_log` table with: spec_id, method, confidence, feedback, timestamp
- `spec_patterns` table for Pattern objects (pattern_type, confidence, occurrence_count)

**Code Changes**:
- Add extraction confidence calculation in orchestrator
- Create database storage for extraction patterns and feedback
- Integrate with existing socratic-learning FeedbackCollector

**API Endpoints** (3-4 endpoints):
- `GET /projects/{id}/specs/extraction-metrics` - Overall extraction stats
- `POST /projects/{id}/specs/{spec_id}/feedback` - Record accuracy feedback
- `GET /projects/{id}/specs/patterns` - List detected extraction patterns
- `GET /projects/{id}/specs/analytics/confidence` - Confidence trends

**Estimated Effort**: 2-2.5 hours (using PatternDetector + metrics collector)

---

## Implementation Priority

**Phase 3A** (Next):
1. **Task 3.3** (1.5-2h): Conflict History Tracking - Foundation for conflict management
2. **Task 3.4** (2-2.5h): Context Analysis - Improves spec extraction quality

**Total Phase 3** (all 4 tasks):
- Task 3.1: ✅ Complete (already done)
- Task 3.2: ✅ Complete (already done)
- Task 3.3: 1.5-2h (upcoming)
- Task 3.4: 2-2.5h (upcoming)
- **Grand Total**: ~3.5-4.5 hours for remaining Phase 3 work
