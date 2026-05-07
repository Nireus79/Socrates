# Framework Integrations

Socrates agents can be seamlessly integrated into external frameworks and orchestration systems. This document covers integration patterns for **LangChain**, **LangGraph**, and **OpenClaw**.

## Table of Contents

1. [LangChain Integration](#langchain-integration)
2. [LangGraph Integration](#langgraph-integration)
3. [OpenClaw Integration](#openclaw-integration)
4. [Installation & Setup](#installation--setup)
5. [Quick Start](#quick-start)
6. [Advanced Usage](#advanced-usage)

---

## LangChain Integration

### Overview

Socrates agents can be exposed as LangChain Tools, enabling them to be used within LangChain agent workflows and LCEL chains.

**Benefits:**
- Use Socrates agents as LangChain tools in agent workflows
- Combine Socrates with LangChain's ecosystem
- Leverage LangChain's agent frameworks (ReAct, OpenAI, etc.)

### Basic Usage

```python
from socratic_system.api.adapters.langchain_integration import create_socrates_tools
from langchain.agents import initialize_agent, AgentType
from langchain_openai import ChatOpenAI

# Create Socrates tools
tools = create_socrates_tools(
    api_url="http://localhost:8000",
    agent_names=["code_generator", "code_validation", "socratic_counselor"]
)

# Initialize LangChain agent
llm = ChatOpenAI(model="gpt-4", temperature=0.7)
agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
    verbose=True
)

# Run agent workflow
result = agent.run("Generate a Python REST API and validate it")
```

### Available Tools

```
- socrates_code_generator: Generate code from specifications
- socrates_counselor: Get architectural advice and design guidance
- socrates_validator: Validate code quality and run tests
- socrates_quality: Assess code maturity and quality metrics
- socrates_conflict: Detect architectural and technical conflicts
```

### Advanced: Custom Tool Composition

```python
from socratic_system.api.adapters.langchain_integration import SocratesTool
from socratic_system.clients.socrates_agent_client import SocratesAgentClientSync

class CodeQualityPipelineTool(SocratesTool):
    """Combined tool that generates code and validates quality."""

    name = "code_quality_pipeline"
    description = "Generate code and immediately assess quality"

    def _run(self, query: str, **kwargs) -> str:
        # Step 1: Generate
        code_result = self.client.invoke_agent(
            "code_generator", action="process", query=query
        )

        # Step 2: Validate
        validation = self.client.invoke_agent(
            "code_validation", action="process",
            query=f"Validate: {code_result}"
        )

        return f"Generated:\n{code_result}\n\nValidation:\n{validation}"
```

### Using SocratesAgentExecutor

For direct control without LangChain's agent framework:

```python
from socratic_system.api.adapters.langchain_integration import SocratesAgentExecutor

async with SocratesAgentExecutor(api_url="http://localhost:8000") as executor:
    # Sync execution
    result = executor.execute(
        "code_generator",
        action="process",
        project_id="proj_123",
        spec="Build a login system"
    )

    # Async execution
    result = await executor.execute_async(
        "socratic_counselor",
        query="Best practices for Python web apps"
    )
```

---

## LangGraph Integration

### Overview

Build complex multi-agent workflows using LangGraph with Socrates nodes for specialized tasks.

**Benefits:**
- Define state machines with Socrates agents as nodes
- Support conditional routing and parallel execution
- Persistent state across agent calls
- Visual workflow representation

### Basic Usage

```python
from langgraph.graph import StateGraph, END
from socratic_system.api.adapters.langgraph_integration import (
    SocratesState, create_socrates_nodes, create_initial_state
)

# Create workflow
workflow = StateGraph(SocratesState)

# Add Socrates nodes
nodes = create_socrates_nodes(
    api_url="http://localhost:8000",
    agents=["code_generator", "code_validation", "quality_controller"]
)

for node_name, node_fn in nodes.items():
    workflow.add_node(node_name, node_fn)

# Define execution flow
workflow.set_entry_point("code_generator")
workflow.add_edge("code_generator", "code_validation")
workflow.add_edge("code_validation", "quality_controller")
workflow.add_edge("quality_controller", END)

# Compile and run
app = workflow.compile()
result = app.invoke(create_initial_state(
    query="Generate and analyze a microservice",
    project_id="proj_123"
))

print(f"Agents executed: {list(result['agent_results'].keys())}")
```

### Conditional Routing

```python
def route_based_on_query(state: SocratesState) -> str:
    """Route to different agents based on query content."""
    if "test" in state["query"].lower():
        return "code_validation"
    return "code_generator"

workflow.add_conditional_edges(
    "code_generator",
    route_based_on_query,
    {
        "code_validation": "code_validation",
        "code_generator": "quality_controller"
    }
)
```

### Parallel Execution

```python
# All three agents run in parallel after code generation
workflow.add_edge("code_generator", "code_validation")
workflow.add_edge("code_generator", "quality_controller")
workflow.add_edge("code_generator", "conflict_detector")

# All converge to END
workflow.add_edge("code_validation", END)
workflow.add_edge("quality_controller", END)
workflow.add_edge("conflict_detector", END)
```

### Using SocratesGraphBuilder

```python
from socratic_system.api.adapters.langgraph_integration import SocratesGraphBuilder

builder = (
    SocratesGraphBuilder(api_url="http://localhost:8000")
    .add_agent("code_generator", node_name="generate")
    .add_agent("code_validation", node_name="validate")
    .add_agent("quality_controller", node_name="assess")
)

nodes = builder.get_all_nodes()
# Use with StateGraph as above
```

### Async Nodes

```python
async def process_async(state: SocratesState) -> SocratesState:
    node = SocratesNode("code_generator")
    return await node.acall(state)

workflow.add_node("code_generator", process_async)
```

---

## OpenClaw Integration

### Overview

Integrate Socrates agents as OpenClaw actions and event handlers for rule-based orchestration.

**Benefits:**
- Use Socrates in rule engines and workflows
- Map OpenClaw events to Socrates actions
- Build complex orchestration with rules

### Basic Usage

```python
from socratic_system.api.adapters.openclaw_integration import SocratesClawAdapter

# Create adapter
adapter = SocratesClawAdapter(api_url="http://localhost:8000")

# Get all available actions
actions = adapter.get_actions()  # Dict of action names to handlers

# Execute action directly
result = adapter.execute_action(
    "socrates_code",
    {
        "spec": "REST API with authentication",
        "project_id": "proj_123",
        "language": "python"
    }
)
```

### Available Actions

```
- socrates_code: Code generation
- socrates_validate: Code validation and testing
- socrates_quality: Quality assessment
- socrates_conflict: Conflict detection
```

### Integration with OpenClaw Engine

```python
# Assuming you have an OpenClaw engine instance
engine = create_claw_engine()
adapter = SocratesClawAdapter(api_url="http://localhost:8000")

# Register all Socrates actions
adapter.register_with_engine(engine)

# Execute through engine
result = engine.execute_action(
    "socrates_code",
    params={"spec": "Generate auth module", "project_id": "proj_auth"}
)
```

### Event-Driven Integration

```python
from socratic_system.api.adapters.openclaw_integration import ClawEventListener

# Create listener
listener = ClawEventListener(api_url="http://localhost:8000")

# Map events to actions
listener.on("project.created", "socrates_code")
listener.on("code.ready_for_review", "socrates_quality")
listener.on("tests.required", "socrates_validate")
listener.on("architecture.review", "socrates_conflict")

# Register with engine
listener.register_with_engine(engine)

# Events now trigger Socrates actions automatically
engine.trigger_event("project.created", {
    "spec": "New project spec",
    "project_id": "proj_new"
})
```

### Custom Actions

```python
from socratic_system.api.adapters.openclaw_integration import ClawAction

class CustomAnalysisAction(ClawAction):
    def __init__(self, api_url="http://localhost:8000"):
        super().__init__("socratic_counselor", "process", api_url)

    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        analysis = self._invoke_agent(query=params.get("question"))
        return {"analysis": analysis, "success": True}

# Use in OpenClaw
action = CustomAnalysisAction()
result = action.execute({"question": "How should I design this system?"})
```

### Async Execution

```python
# Execute actions asynchronously
result = await adapter.execute_action_async(
    "socrates_code",
    {"spec": "Background job processor", "project_id": "proj_bg"}
)
```

---

## Installation & Setup

### Prerequisites

1. **Socrates API running** (use Docker Compose):
   ```bash
   docker-compose up --build
   ```

2. **Framework dependencies**:

   **LangChain:**
   ```bash
   pip install langchain langchain-openai
   ```

   **LangGraph:**
   ```bash
   pip install langgraph langchain
   ```

   **OpenClaw:**
   ```bash
   pip install openclaw  # If available
   ```

### Configuration

All integrations accept these common parameters:

```python
api_url: str           # Socrates API URL (default: "http://localhost:8000")
auth_token: Optional[str]  # For authenticated requests
timeout: int           # Request timeout in seconds (default: 300)
```

---

## Quick Start

### 1. Start Socrates API

```bash
cd Socrates
docker-compose up --build
```

### 2. Run Examples

**LangChain:**
```bash
python examples/langchain_example.py
```

**LangGraph:**
```bash
python examples/langgraph_example.py
```

**OpenClaw:**
```bash
python examples/openclaw_example.py
```

### 3. Run in Your Code

```python
# LangChain example
from socratic_system.api.adapters.langchain_integration import create_socrates_tools

tools = create_socrates_tools(api_url="http://localhost:8000")
```

---

## Advanced Usage

### Custom Tool with Fallbacks

```python
from socratic_system.api.adapters.langchain_integration import SocratesTool

class ResilientSocratesTool(SocratesTool):
    def _run(self, query: str, **kwargs) -> str:
        try:
            return super()._run(query, **kwargs)
        except Exception as e:
            # Fallback behavior
            return f"Service unavailable: {e}"
```

### Multi-Agent Coordination

```python
# LangGraph: Multiple specialized agents
workflow = StateGraph(SocratesState)

# Add specialized nodes
nodes = create_socrates_nodes(
    agents=[
        "code_generator",    # Generate code
        "code_validation",   # Test it
        "quality_controller" # Assess it
    ]
)

for name, fn in nodes.items():
    workflow.add_node(name, fn)

# Define dependencies
workflow.set_entry_point("code_generator")
workflow.add_edge("code_generator", "code_validation")
workflow.add_edge("code_validation", "quality_controller")
workflow.add_edge("quality_controller", END)

app = workflow.compile()
```

### Error Handling

```python
try:
    result = executor.execute("code_generator", spec="...")
except AgentNotFoundError:
    print("Agent not available")
except AgentTimeoutError:
    print("Agent request timed out")
except SocratesAgentClientError as e:
    print(f"API error: {e}")
```

---

## Troubleshooting

### "Connection refused"
- Ensure Socrates API is running: `docker-compose ps`
- Check correct API URL is configured

### "Agent timeout"
- Increase timeout parameter: `timeout=600`
- Check agent workload

### "Missing dependencies"
- Install framework: `pip install langchain` or `pip install langgraph`
- Ensure Python 3.11+

---

## Architecture Overview

```
Your Application
       ↓
Framework Adapter (LangChain/LangGraph/OpenClaw)
       ↓
SocratesAgentClient/Executor
       ↓
HTTP REST API
       ↓
Socrates API (http://localhost:8000)
       ↓
Agent Bus
       ↓
Socrates Agents (15 specialized agents)
```

---

## Support & Examples

- **LangChain**: `examples/langchain_example.py`
- **LangGraph**: `examples/langgraph_example.py`
- **OpenClaw**: `examples/openclaw_example.py`

All examples are fully functional and can be run with `python examples/<file>.py`

---

## Next Steps

1. Choose your framework (LangChain, LangGraph, or OpenClaw)
2. Follow the Quick Start section above
3. Run the corresponding example
4. Adapt patterns to your use case
5. Deploy with Docker for production

For more details, see the framework adapter source code in:
- `socratic_system/api/adapters/langchain_integration.py`
- `socratic_system/api/adapters/langgraph_integration.py`
- `socratic_system/api/adapters/openclaw_integration.py`
