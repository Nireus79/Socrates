"""
Example: Using Socrates Libraries with Openclaw

This example demonstrates how to integrate Socrates components with Openclaw
for multi-agent orchestration while using Socrates' configuration and event system.

Framework Agnostic: Socrates libraries can work with any orchestration framework.
"""

from typing import Any, Dict, List, Optional

from socratic_core import SocratesConfig, EventEmitter, EventType


# ============================================================================
# Openclaw Simulation (Replace with real imports when available)
# ============================================================================

class ClawAgent:
    """Simulated Openclaw Agent base class."""

    def __init__(self, name: str):
        self.name = name
        self.state = {}

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Run the agent."""
        raise NotImplementedError


class ClawOrchestrator:
    """Simulated Openclaw Orchestrator."""

    def __init__(self):
        self.agents: Dict[str, ClawAgent] = {}
        self.workflows = []

    def register_agent(self, name: str, agent: ClawAgent):
        """Register an agent."""
        self.agents[name] = agent

    def add_workflow(self, workflow: 'ClawWorkflow'):
        """Add a workflow."""
        self.workflows.append(workflow)

    async def execute(self, workflow_name: str, input_data: Dict[str, Any]):
        """Execute a workflow."""
        # Find and execute workflow
        for workflow in self.workflows:
            if workflow.name == workflow_name:
                return await workflow.execute(input_data, self)


class ClawWorkflow:
    """Simulated Openclaw Workflow."""

    def __init__(self, name: str):
        self.name = name
        self.steps = []

    def add_step(self, agent_name: str, condition: Optional[Any] = None):
        """Add a step to the workflow."""
        self.steps.append({"agent": agent_name, "condition": condition})
        return self

    async def execute(self, input_data: Dict[str, Any], orchestrator: ClawOrchestrator):
        """Execute the workflow."""
        result = {"input": input_data, "outputs": {}, "steps_executed": []}

        for step in self.steps:
            agent_name = step["agent"]
            agent = orchestrator.agents.get(agent_name)

            if agent:
                output = await agent.run(input_data)
                result["outputs"][agent_name] = output
                result["steps_executed"].append(agent_name)

        return result


# ============================================================================
# Socrates + Openclaw Integration
# ============================================================================

class SocratesOpenclawConfig:
    """Unified configuration for Socrates + Openclaw integration."""

    def __init__(self):
        # Load Socrates configuration
        self.config = SocratesConfig.from_env()

        # Create Socrates event emitter
        self.emitter = EventEmitter()

        # Initialize Openclaw orchestrator
        self.orchestrator = ClawOrchestrator()

    def emit_event(self, event_type: EventType, data: Dict[str, Any]):
        """Emit event through Socrates event system."""
        self.emitter.emit(event_type, data)


# ============================================================================
# Socrates Agents for Openclaw
# ============================================================================

class SocratesCodeAnalyzerAgent(ClawAgent):
    """Code analyzer agent using Socrates framework."""

    def __init__(self, config: SocratesOpenclawConfig):
        super().__init__("code_analyzer")
        self.config = config

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze code."""
        self.config.emit_event(
            EventType.AGENT_START,
            {"agent": self.name, "task": "code_analysis"}
        )

        code = input_data.get("code", "")

        # Simulated analysis (in real: call socratic_analyzer)
        analysis_result = {
            "complexity": "medium",
            "lines": len(code.split('\n')),
            "issues": ["missing error handling", "unused imports"],
            "quality_score": 7.5
        }

        self.config.emit_event(
            EventType.AGENT_COMPLETE,
            {"agent": self.name, "quality_score": analysis_result["quality_score"]}
        )

        return analysis_result


class SocratesCodeGeneratorAgent(ClawAgent):
    """Code generator agent using Socrates framework."""

    def __init__(self, config: SocratesOpenclawConfig):
        super().__init__("code_generator")
        self.config = config

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code."""
        self.config.emit_event(
            EventType.AGENT_START,
            {"agent": self.name, "task": "code_generation"}
        )

        prompt = input_data.get("prompt", "")

        # Simulated generation (in real: call socratic_agents CodeGenerator)
        generated_code = f"""
# Generated code
def solution(data):
    \"\"\"Implementation of: {prompt}\"\"\"
    # TODO: Implement based on {prompt}
    return result
"""

        self.config.emit_event(
            EventType.CODE_GENERATED,
            {"agent": self.name, "lines": len(generated_code.split('\n'))}
        )

        return {"code": generated_code, "language": "python"}


class SocratesRAGAgent(ClawAgent):
    """RAG agent using Socratic RAG library."""

    def __init__(self, config: SocratesOpenclawConfig):
        super().__init__("rag_retrieval")
        self.config = config

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Retrieve knowledge using RAG."""
        self.config.emit_event(
            EventType.AGENT_START,
            {"agent": self.name, "task": "knowledge_retrieval"}
        )

        query = input_data.get("query", "")

        # Simulated retrieval (in real: call socratic_rag)
        documents = [
            {
                "id": "doc_1",
                "source": "documentation",
                "content": "Relevant documentation...",
                "score": 0.95
            },
            {
                "id": "doc_2",
                "source": "examples",
                "content": "Example code...",
                "score": 0.87
            }
        ]

        self.config.emit_event(
            EventType.KNOWLEDGE_LOADED,
            {"agent": self.name, "document_count": len(documents)}
        )

        return {"documents": documents, "query": query}


class SocratesLearningAgent(ClawAgent):
    """Learning agent using Socrates learning system."""

    def __init__(self, config: SocratesOpenclawConfig):
        super().__init__("learning")
        self.config = config

    async def run(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Track interactions and generate recommendations."""
        self.config.emit_event(
            EventType.AGENT_START,
            {"agent": self.name, "task": "learning_analysis"}
        )

        # Simulated learning (in real: call socratic_learning)
        metrics = {
            "interactions": input_data.get("interaction_count", 0),
            "patterns": ["pattern_A", "pattern_B"],
            "recommendations": [
                "Focus on error handling",
                "Improve code documentation"
            ]
        }

        return {"learning_metrics": metrics}


# ============================================================================
# Openclaw Workflow Setup
# ============================================================================

def setup_openclaw_workflow(config: SocratesOpenclawConfig):
    """Setup Openclaw workflow with Socrates agents."""

    # Register Socrates agents with Openclaw
    config.orchestrator.register_agent(
        "code_analyzer",
        SocratesCodeAnalyzerAgent(config)
    )
    config.orchestrator.register_agent(
        "code_generator",
        SocratesCodeGeneratorAgent(config)
    )
    config.orchestrator.register_agent(
        "rag_retrieval",
        SocratesRAGAgent(config)
    )
    config.orchestrator.register_agent(
        "learning",
        SocratesLearningAgent(config)
    )

    # Create workflow: Analyze → Retrieve Knowledge → Generate → Learn
    workflow = ClawWorkflow("code_development")
    workflow.add_step("code_analyzer")
    workflow.add_step("rag_retrieval")
    workflow.add_step("code_generator")
    workflow.add_step("learning")

    config.orchestrator.add_workflow(workflow)

    return workflow


# ============================================================================
# Event Listeners
# ============================================================================

def setup_event_listeners(config: SocratesOpenclawConfig):
    """Setup listeners for Socrates events."""

    @config.emitter.on(EventType.AGENT_START)
    def on_agent_start(data):
        agent = data.get("agent", "unknown")
        task = data.get("task", "unknown")
        print(f"[Start] {agent}: {task}")

    @config.emitter.on(EventType.AGENT_COMPLETE)
    def on_agent_complete(data):
        agent = data.get("agent", "unknown")
        print(f"[Complete] {agent}")

    @config.emitter.on(EventType.CODE_GENERATED)
    def on_code_generated(data):
        lines = data.get("lines", 0)
        print(f"[Generated] {lines} lines of code")

    @config.emitter.on(EventType.KNOWLEDGE_LOADED)
    def on_knowledge_loaded(data):
        count = data.get("document_count", 0)
        print(f"[Retrieved] {count} documents")


# ============================================================================
# Async Execution
# ============================================================================

import asyncio


async def main():
    """Run the Openclaw workflow with Socrates integration."""

    print("=" * 70)
    print("Socrates + Openclaw Integration Example")
    print("=" * 70)

    # Initialize configuration
    config = SocratesOpenclawConfig()

    # Setup event listeners
    setup_event_listeners(config)

    # Register agents and create workflow
    workflow = setup_openclaw_workflow(config)

    # Execute workflow
    input_data = {
        "prompt": "Create a data validation function",
        "query": "Data validation best practices",
        "interaction_count": 5
    }

    print("\nExecuting workflow...")
    print(f"Input: {input_data}")
    print()

    result = await config.orchestrator.execute("code_development", input_data)

    # Display results
    print("\n" + "=" * 70)
    print("Workflow Results")
    print("=" * 70)
    print(f"Steps executed: {result['steps_executed']}")
    print(f"Agents ran: {len(result['outputs'])}")

    # Show outputs from each agent
    print("\nAgent Outputs:")
    for agent_name, output in result["outputs"].items():
        print(f"\n  {agent_name}:")
        for key, value in output.items():
            if isinstance(value, (str, int, float)):
                print(f"    {key}: {value}")
            else:
                print(f"    {key}: [complex data]")


# ============================================================================
# Architecture Pattern
# ============================================================================

"""
Integration Pattern:

┌─────────────────────────────────────────┐
│     Your Application / Framework         │
│     (Openclaw, LangGraph, etc.)         │
└──────────────────┬──────────────────────┘
                   │
    ┌──────────────┼──────────────┐
    │              │              │
    ▼              ▼              ▼
┌──────────┐ ┌──────────┐ ┌──────────┐
│socratic- │ │socratic- │ │socratic- │
│agents    │ │rag       │ │analyzer  │
└──────────┘ └──────────┘ └──────────┘
    │              │              │
    └──────────────┼──────────────┘
                   │
         ┌─────────▼──────────┐
         │ socratic-core      │
         │ • Config           │
         │ • Events           │
         │ • Exceptions       │
         │ • Logging          │
         │ • Utilities        │
         └────────────────────┘

Key Benefits:
1. **No Framework Lock-in**: Use any orchestration framework
2. **Consistent Configuration**: All agents use SocratesConfig
3. **Unified Events**: All agents emit through EventEmitter
4. **Modular Components**: Use only what you need
5. **Easy to Extend**: Add your own agents easily

Migration Path:
- Start with one framework (Openclaw)
- Integrate Socrates libraries gradually
- Swap frameworks later if needed
- Consistent across all frameworks
"""

if __name__ == "__main__":
    asyncio.run(main())
