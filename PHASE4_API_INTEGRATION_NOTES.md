# Phase 4 API Integration Notes

## Current API Router Structure
Located in: `socrates-api/src/socrates_api/routers/`

### Routers to Update
- `agents.py` - Agent execution and management endpoints
- `code_generation.py` - Code generation using CodeGeneratorAgent
- `analysis.py` - Analysis endpoints
- `knowledge.py` - Knowledge management endpoints
- `collaboration.py` - Collaboration features
- `github.py` - GitHub integration
- And others...

## Integration Points

### 1. Agent Import Updates
All routers that import agents should be updated to:
```python
# Old: from socratic_system.agents import SomeAgent
# New: from socratic_agents import SomeAgent
```

### 2. API Endpoint Changes
- Governance endpoints now available through socratic-morality:
  - GET /api/governance/decisions
  - GET /api/governance/constitution
  - GET /api/governance/principles

- Agent Bus endpoints through socratic-agents:
  - POST /api/agents/bus/send-message
  - GET /api/agents/bus/history

- Precedent endpoints through socratic-morality:
  - GET /api/precedents/
  - POST /api/precedents/search
  - GET /api/precedents/{id}

### 3. Backward Compatibility
- All existing endpoints continue to work
- Agent behavior remains unchanged
- Library versions are drop-in replacements

## Status
- ✅ Dependencies added to pyproject.toml
- ✅ Agent imports updated to use library
- 🟡 API router imports need updating
- ⏳ New library endpoints to be exposed
- ⏳ Testing required

## Next Steps
1. Update all router imports to use socratic_agents library
2. Expose governance and precedent endpoints
3. Add agent bus message routing endpoints
4. Run integration tests
5. Deploy Socrates v2.0.0
