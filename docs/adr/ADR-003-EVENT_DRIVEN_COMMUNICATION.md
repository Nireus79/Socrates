# ADR-003: Event-Driven Communication

**Date**: January 2026
**Status**: Accepted
**Deciders**: Architecture Team

## Context

With a multi-agent architecture (ADR-001), agents need to coordinate and notify each other of important events without tight coupling.

**Requirements**:
- Loose coupling between agents
- Agents can react to events from other agents
- External systems can listen to Socrates events
- Event-driven extensibility for third-party integrations
- Simple pub/sub pattern

## Decision

We implemented an **Event-Driven Pub/Sub Communication System** where:
- Agents emit events when important actions occur
- Other agents subscribe to events they care about
- External systems can listen via API
- Events contain rich context and metadata

## Event Types

### System Events
- `project_created` - New project created
- `project_deleted` - Project removed
- `project_archived` - Project archived
- `phase_changed` - Project phase advanced

### Dialogue Events
- `question_generated` - New question asked
- `answer_provided` - User provided answer
- `dialogue_completed` - Phase completed

### Code Events
- `code_generated` - Code generated successfully
- `generation_failed` - Code generation failed
- `code_exported` - Code exported/saved

### System Events
- `conflict_detected` - Requirements conflict found
- `token_usage_updated` - API usage tracked
- `database_error` - Database operation failed

## Event Structure

```python
{
    'event_type': 'project_created',
    'timestamp': '2026-01-18T10:30:00Z',
    'source_agent': 'project_manager',
    'project_id': 'proj_123',
    'owner': 'alice',
    'data': {
        'project_name': 'My Project',
        'phase': 'discovery'
    }
}
```

## Advantages

✓ **Loose Coupling**: Agents don't depend on each other directly
✓ **Extensibility**: New listeners can be added without changing agents
✓ **Async-Friendly**: Events enable asynchronous processing
✓ **Observable**: Easy to track system behavior
✓ **Testable**: Events can be mocked and verified
✓ **Integration**: External systems listen to events

## Disadvantages

✗ **Complexity**: Event flow harder to trace
✗ **Eventual Consistency**: Events processed asynchronously
✗ **Error Handling**: Listener errors don't fail emission
✗ **Debugging**: Debugging event chains is complex
✗ **Performance**: Event overhead for every action

## Alternatives Considered

### 1. Direct Agent Communication
- Agents call each other directly
- **Rejected**: Tight coupling, hard to extend

### 2. Message Queue (RabbitMQ/Kafka)
- External message broker
- **Rejected**: Operational overhead, overkill for single machine

### 3. Polling
- Agents poll for changes
- **Rejected**: Inefficient, high latency

## Consequences

- System is highly extensible and observable
- Event flow can be complex to trace
- External systems can react to Socrates events
- Integration points are well-defined
- Performance impact is minimal but measurable

## Implementation Details

**Emitting Events**:
```python
orchestrator.emit_event('project_created', {
    'project_id': 'proj_123',
    'project_name': 'My Project'
})
```

**Listening to Events**:
```python
def on_project_created(event):
    print(f"Project created: {event['data']['project_name']}")

orchestrator.on('project_created', on_project_created)
```

**Event Monitoring via API**:
```python
# WebSocket connection for real-time events
ws = WebSocket("ws://localhost:8000/events")
for event in ws:
    print(f"Event: {event['type']}")
```

## Event Flow Example

```
User Action: /project create "My App"
    ↓
ProjectManager Agent
    ├─ Validate input
    ├─ Create project
    └─ emit('project_created', {...})
        ↓
    [Multiple Listeners]
    ├─ SystemMonitor: Update metrics
    ├─ KnowledgeManager: Initialize KB
    └─ Logger: Record creation
```

## Event Persistence

Events are **not** persisted by default:
- In-memory pub/sub only
- For audit trails, listen and log to file
- For recovery, project state is in database

**Custom Logging**:
```python
def log_all_events(event):
    with open('events.log', 'a') as f:
        f.write(json.dumps(event) + '\n')

orchestrator.on('*', log_all_events)  # Listen to all events
```

## Monitoring Events

**Via CLI**:
```bash
/debug on  # Shows all events in console
```

**Via Programmatic API**:
```python
from socratic_system.events import EventEmitter

emitter = orchestrator.event_emitter
print(f"Events emitted: {emitter.total_events}")
print(f"Active listeners: {emitter.listener_count}")
```

## Future Considerations

**v1.4+**: Event persistence/audit trail
**v1.5+**: Event filtering and advanced routing
**v2.0+**: Multi-instance event coordination

## Related ADRs
- ADR-001: Multi-Agent Architecture
- ADR-004: FastAPI Backend

---

**Decision**: ACCEPTED
**Implementation**: ✓ Complete
**Review Date**: Q3 2026
