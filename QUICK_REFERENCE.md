# SOCRATES RESTORATION - QUICK REFERENCE

## 📋 Documents Created

1. **DIAGNOSTIC_REPORT_COMPLETE.md** - Comprehensive analysis of all broken systems
2. **IMPLEMENTATION_ROADMAP.md** - Step-by-step fixing instructions  
3. **QUICK_REFERENCE.md** - This file

---

## 🎯 Critical Issues (6 Total)

### Tier 1: System-Breaking
1. **`claude_client` attribute error** (6 locations) → **Task 1.1** (5 min)
2. **Socratic spec detection missing** → **Task 1.2** (2 hours)
3. **Conflict detection not wired** → **Task 1.2** (included)
4. **Debug mode returns no data** → **Task 1.3** (1 hour)
5. **Hints endpoint missing** → **Task 2.1** (1.5 hours)
6. **NLU dialogue broken** → Depends on Task 1.1

---

## ⚡ Implementation Order

START: Task 1.1 (5 minutes)
  → Task 1.2 (2 hours) - CORE
  → Task 1.3 (1 hour)
  → Task 1.4 (1.5 hours)
  → Task 2.1 (1.5 hours)
  → Task 2.2 (1 hour)
  → Task 2.3 (1.5 hours)
  → Task 2.4 (30 minutes)

TOTAL: ~13 hours for full restoration

---

## 🔧 File Changes by Task

| Task | File | Action | Lines |
|------|------|--------|-------|
| 1.1 | free_session.py | Replace claude_client | 278,306,139 |
| 1.1 | nlu.py | Replace claude_client | 91,139,182 |
| 1.2 | orchestrator.py | Implement handler | 1255-1272 |
| 1.3 | projects_chat.py | Add debug mode | 862-878,797-817 |
| 1.4 | projects_chat.py | Add endpoint | ~line 1050 |
| 2.1 | projects_chat.py | Add endpoint | ~line 950 |
| 2.2 | nlu.py | Add spec detection | After interpret_input |
| 2.3 | system.py | Enhance toggle | debug endpoint |
| 2.4 | free_session.py | Add spec extraction | ask_question |

---

## ✅ Success Milestones

**After Task 1.1**: NLU and free_session stop crashing
**After Task 1.2**: Specs detected in Socratic mode
**After Task 1.3**: Debug mode shows specs inline
**After Task 1.4**: Users can resolve conflicts
**After Task 2.1**: Hints system works
**After All**: Full dialogue restored (~95% working)

---

## 📊 Debug Mode Architecture (Option B)

Inline Annotations: Show extracted specs after each dialogue turn when debug enabled.

Response includes `debugInfo`:
```json
{
  "debugInfo": {
    "extracted_specs": {...},
    "spec_changes": {...},
    "conflicts_detected": [...],
    "timestamp": "..."
  }
}
```

Frontend displays inline without cluttering dialogue.

---

## 🎓 Core Mechanisms Restored

1. **Spec Detection**: User input → ContextAnalyzer → Extract specs
2. **Conflict Detection**: New specs vs existing → AgentConflictDetector → Return conflicts
3. **User Resolution**: Conflicts shown → User chooses strategy → Project updated
4. **Hints System**: User stuck → SkillGeneratorAgent → 4 suggestions
5. **Debug Visibility**: Debug enabled → Always extract specs → Show inline

---

See DIAGNOSTIC_REPORT_COMPLETE.md and IMPLEMENTATION_ROADMAP.md for full details.

