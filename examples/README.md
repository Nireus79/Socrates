# Socrates Examples

Comprehensive examples demonstrating how to use Socrates libraries with different orchestration frameworks.

## Core Principle

**Socrates libraries are framework-agnostic.** They provide reusable components that work with any orchestration framework:
- LangGraph
- Openclaw
- Custom orchestrators
- Your own framework

## Key Files

- `langgraph_integration.py` - Complete LangGraph + Socrates example
- `openclaw_integration.py` - Complete Openclaw + Socrates example
- `README.md` - This file

## Quick Start

### With LangGraph

```python
from socratic_core import SocratesConfig, EventEmitter
from langgraph.graph import StateGraph

config = SocratesConfig.from_env()
workflow = StateGraph(YourState)

# Emit events from your nodes
@config.emitter.on(EventType.AGENT_START)
def on_start(data):
    print(f"Agent started: {data}")
```

### With Openclaw

```python
from socratic_core import SocratesConfig
from openclaw import Agent

config = SocratesConfig.from_env()

class MyAgent(Agent):
    def run(self, input_data):
        config.emitter.emit(EventType.AGENT_START, {...})
        # Your logic
        return result
```

## Architecture Pattern

All Socrates libraries sit on top of `socratic-core`:

```
┌────────────────────────────────┐
│  Your Framework (LangGraph,    │
│  Openclaw, Custom, etc.)       │
└───────────────┬────────────────┘
                │
  ┌─────────────┼─────────────┐
  │             │             │
  ▼             ▼             ▼
socratic-   socratic-   socratic-
  rag         agents     analyzer
  
  └─────────────┼─────────────┘
                │
      ┌─────────▼──────────┐
      │  socratic-core     │
      │  • Config          │
      │  • Events          │
      │  • Exceptions      │
      │  • Logging         │
      │  • Utilities       │
      └────────────────────┘
```

## Key Benefits

1. **No Framework Lock-in** - Use any orchestration framework
2. **Consistent Configuration** - All agents use SocratesConfig
3. **Unified Events** - All components emit through EventEmitter
4. **Modular Components** - Use only what you need
5. **Easy to Extend** - Add custom agents and workflows

## Running Examples

### Prerequisites
```bash
pip install socratic-core
export ANTHROPIC_API_KEY="your-key"
```

### LangGraph Example
```bash
pip install langgraph
python langgraph_integration.py
```

### Openclaw Example
```bash
pip install openclaw
python openclaw_integration.py
```

## Integration Patterns

### Pattern 1: Configuration Only
```python
config = SocratesConfig.from_env()
# Use in your framework
```

### Pattern 2: Configuration + Events
```python
config = SocratesConfig.from_env()
config.emitter.on(EventType.AGENT_START, callback)
```

### Pattern 3: Full Integration
```python
from socratic_rag import RAGClient
from socratic_agents import AgentOrchestrator
from socratic_core import SocratesConfig

config = SocratesConfig.from_env()
rag = RAGClient(config)
agents = AgentOrchestrator(config)
# All working together with events
```

## Library Examples

### socratic-rag
```python
from socratic_rag import RAGClient
rag = RAGClient(config)
docs = rag.retrieve("your query")
```

### socratic-agents
```python
from socratic_agents import AgentOrchestrator
orchestrator = AgentOrchestrator(config)
result = orchestrator.run("agent_name", {...})
```

### socratic-analyzer
```python
from socratic_analyzer import CodeAnalyzer
analyzer = CodeAnalyzer(config)
analysis = analyzer.analyze(code)
```

## Framework Integration Comparison

| Feature | LangGraph | Openclaw | Direct |
|---------|-----------|----------|--------|
| Config | ✓ | ✓ | ✓ |
| Events | ✓ | ✓ | ✓ |
| Agents | ✓ | ✓ | ✓ |
| State | StateGraph | Workflow | Events |

## Testing Integration

```python
def test_with_socrates_config():
    config = SocratesConfig(api_key="test")
    events = []
    
    config.emitter.on(EventType.AGENT_START, 
                      lambda d: events.append(d))
    
    # Run your agent
    result = my_agent.run(config)
    
    assert len(events) > 0
```

## Key Takeaways

1. **Socrates is modular** - use individual libraries
2. **Framework agnostic** - works with any orchestration
3. **Event-driven** - all events flow through EventEmitter
4. **No lock-in** - swap frameworks without losing functionality
5. **Progressive adoption** - start small, add complexity

## More Information

- **Architecture**: See [../ARCHITECTURE.md](../ARCHITECTURE.md)
- **Migration**: See [../MIGRATION_GUIDE.md](../MIGRATION_GUIDE.md)
- **Quick Start**: See [../QUICKSTART.md](../QUICKSTART.md)

## Issues & Questions

- GitHub: https://github.com/themsou/Socrates/issues
- Documentation: https://github.com/themsou/Socrates

---

All Socrates libraries are designed to work *with* your framework, not *instead of* it.
