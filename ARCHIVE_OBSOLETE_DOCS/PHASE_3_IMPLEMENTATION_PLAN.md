# Phase 3 Implementation Plan - Conflict Resolution Flow

## Overview

Phase 3 implements the complete conflict resolution system that allows users to resolve conflicts detected during Socratic dialogue in a non-blocking, user-friendly manner.

---

## Architecture

### Conflict Lifecycle

```
Answer Submitted
    ↓
Question Marked Answered ✅ (BEFORE conflict detection)
    ↓
Specs Extracted
    ↓
Conflict Detection (Non-blocking)
    ↓
If Conflicts Found:
    ├─ Return conflict modal data
    ├─ User sees conflicts
    ├─ User chooses resolution strategy
    ├─ Call resolve-conflicts endpoint
    └─ Update project specs
```

### Key Principle: Non-Blocking

**Question is answered BEFORE conflict detection** (already implemented in Phase 2)

Benefits:
- User doesn't need to re-answer question
- Dialogue flow never blocked by conflicts
- Conflicts are metadata to resolve
- User has full control of resolution

---

## Detailed Implementation

### Step 1: Conflict Data Structure

**Conflict Object** (returned from detect_conflicts):
```python
{
  "conflict_id": "conflict_1",
  "type": "tech_stack",           # Type of conflict
  "field": "database",             # Which field changed
  "severity": "high",              # low, medium, high
  "existing": {
    "value": "PostgreSQL",
    "source": "q_abc123",          # Which question
    "timestamp": "2024-01-01T09:00:00"
  },
  "new": {
    "value": "MongoDB",
    "source": "q_xyz789",
    "timestamp": "2024-01-01T10:00:00"
  },
  "message": "Database choice changed from PostgreSQL to MongoDB",
  "suggested_resolutions": [
    "Keep PostgreSQL (relational is better for consistency)",
    "Switch to MongoDB (better for document storage)",
    "Use both (polyglot persistence approach)"
  ]
}
```

---

### Step 2: Conflict Explanation Generation

**Purpose**: Generate user-friendly explanations of conflicts

**Method**: `_generate_conflict_explanation(conflicts: List[Dict]) -> str`

**Implementation**:
```python
def _generate_conflict_explanation(conflicts):
    """
    Generate a human-readable explanation of conflicts.

    Helps user understand:
    - What changed
    - Why it's a conflict
    - Options to resolve
    """

    if not conflicts:
        return "No conflicts detected."

    # Build explanation
    lines = [
        f"Found {len(conflicts)} potential conflict(s) in your response:",
        ""
    ]

    for i, conflict in enumerate(conflicts, 1):
        lines.append(f"**{i}. {conflict['field'].replace('_', ' ').title()}**")
        lines.append(f"   Previous: {conflict['existing']['value']}")
        lines.append(f"   Your response: {conflict['new']['value']}")
        lines.append(f"   Severity: {conflict['severity'].upper()}")
        lines.append("")

    lines.append("How would you like to resolve these?")
    lines.append("- Keep existing specs")
    lines.append("- Use new specs from your response")
    lines.append("- Skip adding new specs")
    lines.append("- Manually edit both values")

    return "\n".join(lines)
```

---

### Step 3: Conflict Resolution Endpoint

**Endpoint**: `POST /projects/{project_id}/chat/resolve-conflicts`

**Request Body**:
```python
class ConflictResolution(BaseModel):
    conflict_id: str
    strategy: str  # "keep", "replace", "skip", "manual"
    manual_existing: Optional[str] = None  # For "manual" strategy
    manual_new: Optional[str] = None       # For "manual" strategy

class ConflictResolutionRequest(BaseModel):
    resolutions: List[ConflictResolution]
```

**Response**:
```python
{
  "success": true,
  "status": "success",
  "data": {
    "conflicts_resolved": 2,
    "updated_specs": {
      "tech_stack": ["PostgreSQL", "Python", "React"],
      "constraints": ["Budget $50k"],
      ...
    },
    "next_action": "generate_question"  # Continue dialogue
  }
}
```

---

### Step 4: Conflict Resolution Handler

**Method**: `_handle_conflict_resolution(project, resolutions: List[Dict])`

**Logic**:
```python
async def resolve_conflicts(project_id, request, current_user):
    """
    Resolve detected conflicts and update project specs.

    Strategies:
    - "keep": Keep existing spec, discard new
    - "replace": Replace existing with new
    - "skip": Discard new, keep existing
    - "manual": Use custom values for both
    """

    # 1. Load project
    # 2. Find pending conflicts
    # 3. Apply resolutions based on strategy:

    for resolution in request.resolutions:
        conflict_id = resolution.conflict_id
        strategy = resolution.strategy

        # Find conflict in pending_conflicts
        conflict = find_conflict(project, conflict_id)

        if strategy == "keep":
            # Keep existing, remove conflict
            pass

        elif strategy == "replace":
            # Update spec with new value
            update_project_spec(
                project,
                conflict['field'],
                conflict['new']['value']
            )

        elif strategy == "skip":
            # Discard new, keep existing
            pass

        elif strategy == "manual":
            # Use custom values
            if resolution.manual_existing:
                update_existing_spec(project, conflict['field'], resolution.manual_existing)
            if resolution.manual_new:
                add_new_spec(project, conflict['field'], resolution.manual_new)

    # 4. Clear resolved conflicts from pending_conflicts
    # 5. Save project
    # 6. Return updated specs
```

---

### Step 5: Frontend Integration

**Frontend needs to**:
1. Display conflict modal when conflicts returned
2. Show conflict explanations
3. Present resolution options
4. Allow manual editing
5. Call resolve-conflicts endpoint
6. Continue dialogue after resolution

---

## Implementation Steps

### Step 1: Add Conflict Explanation Function (30 min)
- Location: `projects_chat.py`
- Function: `_generate_conflict_explanation(conflicts)`
- Already partially done (line 1090)

### Step 2: Create Resolution Endpoint (1 hour)
- Location: `projects_chat.py`
- Endpoint: `POST /projects/{project_id}/chat/resolve-conflicts`
- Handler: `resolve_conflicts()`
- Test with curl

### Step 3: Integrate with Orchestrator (30 min)
- Location: `orchestrator.py`
- Method: `_handle_conflict_resolution()`
- Coordinate spec updates

### Step 4: Add Conflict Modal Data (30 min)
- Update send_message response to include conflict data
- Format conflicts for frontend
- Add conflict explanations

### Step 5: Testing & Validation (1 hour)
- Test conflict detection
- Test all resolution strategies
- Test database persistence
- Test edge cases

### Step 6: Documentation (1 hour)
- Document conflict data structure
- Document resolution strategies
- Create Phase 3 summary

**Total Time**: ~4 hours

---

## Database Considerations

### Add to Project Schema

```python
# In ProjectContext or Project model:
class Project:
    pending_conflicts: List[Dict] = []  # Conflicts waiting for resolution
    resolved_conflicts: List[Dict] = []  # History of resolved conflicts
```

---

## Error Handling

### Conflict Not Found
```python
raise HTTPException(
    status_code=404,
    detail=f"Conflict {conflict_id} not found"
)
```

### Invalid Strategy
```python
raise HTTPException(
    status_code=400,
    detail=f"Invalid resolution strategy: {strategy}"
)
```

### Project Not Found
```python
raise HTTPException(
    status_code=404,
    detail="Project not found"
)
```

---

## Testing Checklist

- [ ] Conflict detection works correctly
- [ ] Conflict explanation generates proper text
- [ ] "keep" strategy preserves existing spec
- [ ] "replace" strategy updates to new value
- [ ] "skip" strategy discards new value
- [ ] "manual" strategy applies custom values
- [ ] Multiple conflicts can be resolved together
- [ ] Project state persisted correctly
- [ ] Response includes updated specs
- [ ] Frontend can display conflict modal
- [ ] User can select resolution strategy
- [ ] Dialogue continues after resolution

---

## Edge Cases

1. **No conflicts**: Return empty conflicts array
2. **Multiple conflicts**: Handle all in one request
3. **Same field in multiple conflicts**: Merge resolutions
4. **Invalid field name**: Skip with warning
5. **Conflict already resolved**: Return conflict already handled
6. **Project state changed**: Return stale conflict error

---

## Success Criteria

✅ Conflicts detected during Socratic dialogue
✅ User-friendly conflict explanations generated
✅ Multiple resolution strategies available
✅ Conflicts resolved without blocking dialogue
✅ Project specs updated correctly
✅ Full persistence to database
✅ All edge cases handled gracefully
✅ Comprehensive documentation
✅ Code reviewed and tested

---

## Timeline

**Phase 3: 2 weeks (14 days)**

- **Days 1-2**: Planning & setup (DONE - this document)
- **Days 3-4**: Conflict explanation & endpoint
- **Days 5-6**: Resolution handler & orchestration
- **Days 7-8**: Testing & validation
- **Days 9-10**: Edge cases & error handling
- **Days 11-14**: Documentation & cleanup

---

## Deliverables

1. ✅ `/projects/{project_id}/chat/resolve-conflicts` endpoint
2. ✅ Conflict explanation generation
3. ✅ Full resolution handler with all strategies
4. ✅ Orchestrator integration
5. ✅ Complete test coverage
6. ✅ Phase 3 completion summary
7. ✅ Updated documentation

---

## Next Phase Preview

After Phase 3 completes, Phase 4 (Phase Advancement Flow) will:
- Add maturity verification
- Implement phase advancement checks
- Create advancement prompts
- Support phase rollback

---

## Status

**Phase 3 Ready to Start**: ✅ YES

All prerequisite work from Phases 1-2 is complete and working.
Architecture is solid and ready for conflict resolution implementation.

