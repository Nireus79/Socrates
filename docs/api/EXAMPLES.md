# Socratic Ecosystem - Integration Examples

Complete examples showing how to combine Socratic packages for real-world applications.

## Quick Start Examples

### 1. AI Code Review System (Analyzer + Nexus + Agents)

**What it does**: Analyzes code and provides intelligent review feedback

```python
from socrates_nexus import AsyncClient
from socratic_analyzer import CodeAnalyzer
from socratic_agents import SocraticCounselor

async def code_review_system():
    # Analyze code
    analyzer = CodeAnalyzer()
    analysis = analyzer.analyze_file("app.py")

    # Get LLM insights
    client = AsyncClient()
    issues_text = f"Code has {len(analysis.issues)} issues: {analysis.issues}"
    review = await client.chat([
        {"role": "user", "content": f"Review these code issues: {issues_text}"}
    ])

    # Provide guidance
    counselor = SocraticCounselor()
    guidance = counselor.process({
        "analysis": analysis,
        "review": review,
        "goal": "improve code quality"
    })

    return guidance
```

**Packages Used**:
- `socratic-analyzer` - Code analysis
- `socrates-nexus` - LLM integration
- `socratic-agents` - Guidance generation

---

### 2. Intelligent RAG System (RAG + Nexus + Knowledge)

**What it does**: Retrieves documents and generates answers using knowledge base

```python
from socratic_rag import RAGClient
from socratic_knowledge import KnowledgeManager
from socrates_nexus import AsyncClient

async def intelligent_rag():
    # Initialize systems
    rag = RAGClient()
    knowledge = KnowledgeManager()
    llm = AsyncClient()

    # Index documents in knowledge base
    docs = await knowledge.add_documents([
        "path/to/doc1.md",
        "path/to/doc2.pdf"
    ])

    # Retrieve relevant context
    query = "How do I use Socratic Agents?"
    context = rag.retrieve(query, top_k=3)

    # Generate answer
    answer = await llm.chat([
        {"role": "user", "content": f"""
        Context: {context}
        Question: {query}
        """}
    ])

    return answer
```

**Packages Used**:
- `socratic-rag` - Retrieval system
- `socratic-knowledge` - Knowledge management
- `socrates-nexus` - Answer generation

---

### 3. Learning-Enhanced Agents (Agents + Learning + Conflict)

**What it does**: Agents that learn from interactions and resolve conflicts

```python
from socratic_agents import MultiLlmAgent, SocraticCounselor
from socratic_learning import LearningTool
from socratic_conflict import ConflictDetector, VotingStrategy

async def learning_agents_system():
    # Initialize components
    agents = [SocraticCounselor(), MultiLlmAgent()]
    learning = LearningTool()
    conflict_detector = ConflictDetector()

    # Create a session
    session_id = learning.create_session("user123")

    # Get responses from multiple agents
    query = "How should I structure my project?"
    responses = []
    for agent in agents:
        response = agent.process({"query": query})
        responses.append(response)

        # Log interaction
        learning.log_interaction(
            session_id=session_id,
            agent_name=agent.__class__.__name__,
            input_data={"query": query},
            output_data=response,
            success=True
        )

    # Detect conflicts in responses
    proposals = [
        {"agent": "Counselor", "response": responses[0]},
        {"agent": "MultiLLM", "response": responses[1]}
    ]
    conflicts = conflict_detector.detect_conflicts(proposals)

    # Resolve using voting
    strategy = VotingStrategy()
    resolution = strategy.resolve(proposals)

    # Get metrics
    metrics = learning.get_metrics()
    recommendations = learning.get_recommendations()

    return {
        "resolution": resolution,
        "metrics": metrics,
        "recommendations": recommendations
    }
```

**Packages Used**:
- `socratic-agents` - Multi-agent system
- `socratic-learning` - Learning tracking
- `socratic-conflict` - Conflict resolution

---

### 4. Workflow Orchestration (Workflow + Analyzer + RAG)

**What it does**: Orchestrates complex workflows with quality checking and knowledge retrieval

```python
from socratic_workflow import WorkflowDefinition, WorkflowExecutor
from socratic_analyzer import CodeQualityAnalyzer
from socratic_rag import RAGClient

async def workflow_with_quality():
    # Define workflow
    workflow = WorkflowDefinition("data_processing")
    workflow.add_task("fetch_data", handler=fetch_data)
    workflow.add_task("analyze_code", handler=analyze_quality)
    workflow.add_task("retrieve_context", handler=retrieve_docs)
    workflow.add_dependency("analyze_code", "fetch_data")
    workflow.add_dependency("retrieve_context", "fetch_data")

    # Execute with tracking
    executor = WorkflowExecutor()
    results = await executor.execute(workflow)

    # Analyze results
    analyzer = CodeQualityAnalyzer()
    quality_report = analyzer.generate_report(results)

    # Retrieve relevant docs for issues
    rag = RAGClient()
    if quality_report.issues:
        solutions = rag.retrieve(
            f"Fix for: {quality_report.issues[0]}",
            top_k=3
        )
        quality_report.add_solutions(solutions)

    return quality_report
```

**Packages Used**:
- `socratic-workflow` - Orchestration
- `socratic-analyzer` - Quality checking
- `socratic-rag` - Solution retrieval

---

### 5. Complete Agent System (All packages)

**What it does**: Full-featured system combining all ecosystem capabilities

```python
from socratic_agents import QualityController
from socratic_analyzer import CodeAnalyzer
from socratic_rag import RAGClient
from socratic_knowledge import KnowledgeManager
from socratic_learning import LearningTool
from socratic_conflict import ConflictDetector, WeightedStrategy
from socratic_workflow import WorkflowExecutor
from socrates_nexus import AsyncClient

async def full_ecosystem_system(project_path):
    # Initialize all systems
    analyzer = CodeAnalyzer()
    rag = RAGClient()
    knowledge = KnowledgeManager()
    learning = LearningTool()
    conflict = ConflictDetector()
    workflow = WorkflowExecutor()
    llm = AsyncClient()

    # Analyze project
    analysis = analyzer.analyze_directory(project_path)

    # Add to knowledge base
    doc_ids = await knowledge.add_documents(analysis.files)

    # Get recommendations from LLM
    insights = await llm.chat([
        {"role": "user", "content": f"Analyze: {analysis.summary}"}
    ])

    # Log everything for learning
    session = learning.create_session(project_path)
    learning.log_interaction(
        session_id=session,
        agent_name="FullSystem",
        input_data={"project": project_path},
        output_data={
            "analysis": analysis,
            "insights": insights
        },
        success=True
    )

    # Retrieve similar projects
    similar = rag.retrieve(analysis.summary, top_k=3)

    # Get recommendations
    recommendations = learning.get_recommendations()

    return {
        "analysis": analysis,
        "insights": insights,
        "recommendations": recommendations,
        "similar_projects": similar
    }
```

**Packages Used**: All 8 packages

---

## Framework Integration Examples

### Openclaw Skill Chain

```python
from socratic_agents.integrations.openclaw import SocraticAgentsSkill
from socratic_conflict.integrations.openclaw import SocraticConflictSkill
from socratic_knowledge.integrations.openclaw import SocraticKnowledgeSkill

# Use in Openclaw workflow
skills = [
    SocraticAgentsSkill(),
    SocraticConflictSkill(),
    SocraticKnowledgeSkill()
]

# Register with Openclaw executor
for skill in skills:
    executor.register_skill(skill)
```

### LangChain Tool Chain

```python
from socratic_agents.integrations.langchain import AgentsTool
from socratic_conflict.integrations.langchain import ConflictResolutionTool
from socratic_knowledge.integrations.langchain import KnowledgeManagerTool
from langchain import AgentExecutor, initialize_agent

tools = [
    AgentsTool(),
    ConflictResolutionTool(),
    KnowledgeManagerTool()
]

agent = initialize_agent(tools, llm, agent="zero-shot-react-description")
result = agent.run("Use all tools to solve this complex problem...")
```

---

## Performance Considerations

### Package Loading Time (First Import)
- `socrates-nexus`: ~100ms
- `socratic-rag`: ~200ms (includes vector store init)
- `socratic-agents`: ~150ms
- `socratic-knowledge`: ~120ms
- `socratic-learning`: ~180ms
- `socratic-analyzer`: ~140ms
- `socratic-workflow`: ~130ms
- `socratic-conflict`: ~100ms

**Recommendation**: Import packages on-demand rather than all at startup.

### Memory Usage
- Minimal footprint for standalone use
- RAG with ChromaDB: ~50-200MB depending on index size
- Knowledge Manager: ~20-100MB for typical database
- Learning system: ~10-50MB per 10K interactions

---

## Best Practices

1. **Use AsyncClient from Nexus** for LLM calls - it's optimized for performance
2. **Enable Learning** on production systems to track agent performance
3. **Use Conflict Detection** when multiple agents might disagree
4. **Store Knowledge** for repeated queries - RAG is faster with indexed data
5. **Monitor Workflows** with built-in metrics and cost tracking
6. **Combine Analyzer + Learning** to detect performance regressions

---

## Community Examples

See individual package repositories for more examples:
- [Socratic Agents Examples](https://github.com/Nireus79/Socratic-agents/tree/main/examples)
- [Socratic RAG Examples](https://github.com/Nireus79/Socratic-rag/tree/main/examples)
- [Socratic Workflow Examples](https://github.com/Nireus79/Socratic-workflow/tree/main/examples)

---

**Questions?** Open an issue on any repository or [become a sponsor](https://github.com/sponsors/Nireus79)!
