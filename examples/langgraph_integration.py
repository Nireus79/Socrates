"""
Example: Using Socrates Libraries with LangGraph

This example demonstrates how to integrate Socrates components with LangGraph
for multi-agent orchestration while using Socrates' configuration and event system.

Framework Agnostic: Socrates libraries can work with any orchestration framework.
"""

from typing import Any, Dict, List

from langgraph.graph import StateGraph, START, END
from pydantic import BaseModel

from socratic_core import SocratesConfig, EventEmitter, EventType


# ============================================================================
# Setup: Configuration and Events (Socrates Framework)
# ============================================================================

class SocratesLangGraphConfig:
    """Unified configuration for Socrates + LangGraph integration."""

    def __init__(self):
        # Load configuration from environment/file
        self.config = SocratesConfig.from_env()

        # Create event emitter for all events
        self.emitter = EventEmitter()

        # LLM would be initialized separately (could use socrates-nexus)
        # For this example, we'll use a simple mock
        self.llm_model = self.config.model

    def emit_event(self, event_type: EventType, data: Dict[str, Any]):
        """Emit event through Socrates event system."""
        self.emitter.emit(event_type, data)


# ============================================================================
# State Definition
# ============================================================================

class AgentState(BaseModel):
    """State passed between LangGraph nodes."""
    input: str
    messages: List[str] = []
    results: Dict[str, Any] = {}
    errors: List[str] = []


# ============================================================================
# Agent Definitions (Could wrap Socrates agents)
# ============================================================================

class CodeAnalysisAgent:
    """Agent that analyzes code using Socrates concepts."""

    def __init__(self, config: SocratesLangGraphConfig):
        self.config = config
        self.name = "code_analyzer"

    def analyze(self, code: str) -> Dict[str, Any]:
        """Analyze code."""
        # In real implementation, would call socratic_analyzer
        self.config.emit_event(
            EventType.AGENT_START,
            {"agent": self.name, "task": "code_analysis"}
        )

        # Simulated analysis
        result = {
            "complexity": "medium",
            "issues": ["missing error handling"],
            "suggestions": ["add try-catch blocks"]
        }

        self.config.emit_event(
            EventType.AGENT_COMPLETE,
            {"agent": self.name, "result": result}
        )

        return result


class CodeGenerationAgent:
    """Agent that generates code."""

    def __init__(self, config: SocratesLangGraphConfig):
        self.config = config
        self.name = "code_generator"

    def generate(self, prompt: str) -> str:
        """Generate code based on prompt."""
        self.config.emit_event(
            EventType.AGENT_START,
            {"agent": self.name, "task": "code_generation"}
        )

        # In real implementation, would call socratic_agents
        # For this example, return simulated code
        generated_code = f"# Generated from: {prompt}\ndef solution():\n    pass"

        self.config.emit_event(
            EventType.CODE_GENERATED,
            {"agent": self.name, "lines": len(generated_code.split('\n'))}
        )

        return generated_code


class KnowledgeRetrieval Agent:
    """Agent that retrieves knowledge using RAG."""

    def __init__(self, config: SocratesLangGraphConfig):
        self.config = config
        self.name = "knowledge_retrieval"

    def retrieve(self, query: str) -> List[Dict[str, str]]:
        """Retrieve relevant knowledge."""
        self.config.emit_event(
            EventType.AGENT_START,
            {"agent": self.name, "task": "knowledge_retrieval"}
        )

        # In real implementation, would call socratic_rag
        results = [
            {"source": "docs", "content": "Relevant knowledge..."},
            {"source": "examples", "content": "Example code..."},
        ]

        self.config.emit_event(
            EventType.KNOWLEDGE_LOADED,
            {"agent": self.name, "count": len(results)}
        )

        return results


# ============================================================================
# LangGraph Node Functions
# ============================================================================

def analyze_code_node(state: AgentState, config: SocratesLangGraphConfig) -> AgentState:
    """LangGraph node: Analyze code."""
    analyzer = CodeAnalysisAgent(config)
    result = analyzer.analyze(state.input)

    state.results["analysis"] = result
    state.messages.append(f"Analysis complete: {result}")
    return state


def retrieve_knowledge_node(state: AgentState, config: SocratesLangGraphConfig) -> AgentState:
    """LangGraph node: Retrieve relevant knowledge."""
    retriever = KnowledgeRetrievalAgent(config)
    docs = retriever.retrieve(state.input)

    state.results["knowledge"] = docs
    state.messages.append(f"Retrieved {len(docs)} documents")
    return state


def generate_code_node(state: AgentState, config: SocratesLangGraphConfig) -> AgentState:
    """LangGraph node: Generate code."""
    generator = CodeGenerationAgent(config)
    code = generator.generate(state.input)

    state.results["generated_code"] = code
    state.messages.append(f"Generated {len(code)} chars of code")
    return state


def synthesize_node(state: AgentState, config: SocratesLangGraphConfig) -> AgentState:
    """LangGraph node: Synthesize all results."""
    config.emit_event(
        EventType.SYSTEM_INITIALIZED,
        {"stage": "synthesis", "results": list(state.results.keys())}
    )

    state.messages.append("Synthesis complete")
    return state


# ============================================================================
# Router Function
# ============================================================================

def route_analysis(state: AgentState) -> str:
    """Decide next step based on analysis."""
    if "analysis" in state.results:
        issues = state.results["analysis"].get("issues", [])
        if issues:
            return "retrieve_knowledge"
    return "synthesize"


# ============================================================================
# Build LangGraph Workflow
# ============================================================================

def create_socrates_langgraph_workflow(config: SocratesLangGraphConfig) -> StateGraph:
    """Create a LangGraph workflow using Socrates configuration and events."""

    # Create graph
    workflow = StateGraph(AgentState)

    # Add nodes
    workflow.add_node(
        "analyze",
        lambda state: analyze_code_node(state, config)
    )
    workflow.add_node(
        "retrieve_knowledge",
        lambda state: retrieve_knowledge_node(state, config)
    )
    workflow.add_node(
        "generate",
        lambda state: generate_code_node(state, config)
    )
    workflow.add_node(
        "synthesize",
        lambda state: synthesize_node(state, config)
    )

    # Add edges
    workflow.add_edge(START, "analyze")
    workflow.add_conditional_edges("analyze", route_analysis)
    workflow.add_edge("retrieve_knowledge", "generate")
    workflow.add_edge("generate", "synthesize")
    workflow.add_edge("synthesize", END)

    return workflow


# ============================================================================
# Event Listeners (Demonstrating Socrates event integration)
# ============================================================================

def setup_event_listeners(config: SocratesLangGraphConfig):
    """Setup listeners for Socrates events."""

    @config.emitter.on(EventType.AGENT_START)
    def on_agent_start(data):
        agent = data.get("agent", "unknown")
        print(f"[Agent Started] {agent}")

    @config.emitter.on(EventType.AGENT_COMPLETE)
    def on_agent_complete(data):
        agent = data.get("agent", "unknown")
        print(f"[Agent Complete] {agent}")

    @config.emitter.on(EventType.CODE_GENERATED)
    def on_code_generated(data):
        lines = data.get("lines", 0)
        print(f"[Code Generated] {lines} lines")

    @config.emitter.on(EventType.KNOWLEDGE_LOADED)
    def on_knowledge_loaded(data):
        count = data.get("count", 0)
        print(f"[Knowledge Loaded] {count} documents")


# ============================================================================
# Main Usage
# ============================================================================

def main():
    """Run the LangGraph workflow with Socrates integration."""

    # Initialize configuration and event system
    config = SocratesLangGraphConfig()

    # Setup event listeners
    setup_event_listeners(config)

    # Create the workflow
    workflow = create_socrates_langgraph_workflow(config)
    app = workflow.compile()

    # Create initial state
    initial_state = AgentState(input="Create a Python function for data validation")

    # Run the workflow
    print("=" * 60)
    print("Running Socrates + LangGraph Workflow")
    print("=" * 60)

    result = app.invoke(initial_state)

    # Display results
    print("\n" + "=" * 60)
    print("Results")
    print("=" * 60)
    print(f"Messages: {result.messages}")
    print(f"Generated Code:\n{result.results.get('generated_code', 'N/A')}")


# ============================================================================
# Key Takeaways
# ============================================================================

"""
Key Points:

1. **Framework Agnostic**:
   - Socrates core (config, events, exceptions) works with LangGraph
   - No dependencies on Socrates orchestration framework

2. **Agents Can Be Wrapped**:
   - LangGraph nodes can wrap Socrates agents (RAG, Code Gen, etc.)
   - Or use custom implementations

3. **Event System Integration**:
   - All events flow through Socrates EventEmitter
   - Consistent monitoring regardless of agent implementation

4. **Flexible Integration**:
   - Use Socrates libraries as needed
   - Replace with your own implementations
   - Mix and match frameworks

5. **Same Pattern for Other Frameworks**:
   - Openclaw integration would be similar
   - Any orchestration framework can use socratic-core
   - Libraries like socratic-rag, socratic-agents are independent

Usage with Different Frameworks:
- LangGraph: See this file
- Openclaw: Similar pattern, replace StateGraph with Openclaw equivalents
- Custom Orchestrator: Use EventEmitter and Config directly
"""

if __name__ == "__main__":
    main()
