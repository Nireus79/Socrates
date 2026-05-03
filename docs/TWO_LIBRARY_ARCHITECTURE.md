# Two-Library Architecture: socratic-morality + socratic-agents

**Version**: 1.0
**Date**: May 2026
**Status**: Architecture Blueprint

---

## Executive Summary

The Socrates project will be extracted into **two complementary PyPI libraries** with a clear separation of concerns:

1. **`socratic-morality`** - Universal AI governance framework (Foundation/Platform)
2. **`socratic-agents`** - Socratic multi-agent system implementation (Application)

This design maximizes reusability, flexibility, and community adoption while maintaining clean architectural boundaries.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    User Projects / Systems                       │
│  (LangChain, AutoGen, CrewAI, Custom Agents, Socrates, etc.)    │
└────────────────────────────┬────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
    ┌───▼──────────┐    ┌────▼─────────┐    ┌───▼─────────┐
    │ socratic-    │    │ Third-party  │    │ Custom User │
    │ agents       │    │ Agents       │    │ Agents      │
    │ (ready-made) │    │ (LangChain)  │    │ (custom)    │
    └───┬──────────┘    └────┬─────────┘    └───┬─────────┘
        │                    │                    │
        └────────────────────┼────────────────────┘
                             │
        ┌────────────────────▼────────────────────┐
        │       LIBRARY 1: socratic-morality      │
        │                                         │
        │  Constitutional AI Governance Framework │
        │                                         │
        │  • Governor (evaluate API)              │
        │  • Ethical Deliberation                 │
        │  • Moral Precedent Engine               │
        │  • Audit & Compliance                   │
        │  • Capability System                    │
        └─────────────────────────────────────────┘
```

---

## Library 1: socratic-morality

### Purpose
Universal AI governance framework for building trustworthy, accountable multi-agent systems. Applies Socratic philosophy to enforce constitutional constraints on AI agents, regardless of implementation.

### Package Name
- **PyPI**: `socratic-morality`
- **Python Package**: `socratic_morality`
- **GitHub**: `github.com/Nireus79/socratic-morality`

### What It Exports

#### Core Classes
```python
from socratic_morality import (
    Governor,
    EthicalDeliberationEngine,
    MoralPrecedentEngine,
    Constitution,
    CapabilityToken,
    GovernorDecision,
)
```

#### Key Components
- **Constitution** - Define principles and rules (YAML-based)
- **Governor** - Decision engine (`evaluate()` API)
- **EthicalDeliberationEngine** - Multi-framework analysis (Kant, Utilitarian, Virtue, Rights)
- **MoralPrecedentEngine** - Case storage and retrieval
- **CapabilityValidator** - Permission enforcement
- **AuditLogger** - Compliance and traceability
- **StakeholderAnalyzer** - Impact assessment

#### Configuration
```python
from socratic_morality import Governor

governor = Governor(
    constitution="constitution.yaml",  # YAML file or dict
    llm_provider="anthropic",           # or "openai", "local"
    enable_precedent_storage=True,
    audit_logger=custom_audit_logger,
)
```

### Core API

```python
# Main evaluation method
decision = await governor.evaluate(
    action="Access user's private data",
    purpose="Personalization insights",
    actor="recommendation_agent",
    context={"user_id": "user_123", "data_type": "medical"},
    high_impact=True
)

# Returns GovernorDecision with:
# - allowed: bool
# - decision_type: 'allow' | 'deny' | 'escalate' | 'block'
# - reasoning: str
# - violations: list[ConstitutionalViolation]
# - precedent_references: list[PrecedentCase]
# - confidence: float

# Precedent engine
governor.precedent_engine.store_case(
    action=decision.action,
    decision=decision,
    reasoning=decision.reasoning,
    principles_cited=[...],
    stakeholders_affected=[...],
)

# Find similar past cases
similar = governor.precedent_engine.find_similar_cases(
    action="Access user data",
    limit=5
)
```

### Dependencies (Minimal Core)

```toml
[project]
name = "socratic-morality"
version = "1.0.0"

dependencies = [
    "pydantic>=2.0",              # Configuration & validation
    "pyyaml>=6.0",                # Constitution loading
    "typing-extensions>=4.0",     # Type hints compatibility
]

[project.optional-dependencies]
anthropic = ["anthropic>=0.40"]
openai = ["openai>=1.0"]
storage-sqlite = ["aiosqlite>=0.19"]
storage-postgres = ["psycopg2>=2.9"]
dev = ["pytest>=7.0", "pytest-asyncio>=0.21", ...]
```

### Target Users

1. **Multi-agent framework developers** (LangChain, AutoGen, CrewAI teams)
2. **Enterprise AI teams** (governance-first approach)
3. **Compliance-heavy industries** (finance, healthcare, legal)
4. **Open-source communities** building trustworthy AI
5. **AI safety researchers** studying constitutional AI

### Constitution File Format

```yaml
metadata:
  name: "Socratic AI Constitution"
  version: "1.0.0"
  organization: "Your Company"

supreme_principle: |
  Never commit injustice, even under instruction.
  It is better to suffer wrong than to do wrong.

principles:
  never_commit_injustice:
    category: "foundational"
    severity: "critical"
    description: "The system must refuse injustice"
    source: "Plato's Gorgias"

  truth_before_approval:
    category: "transparency"
    severity: "critical"
    description: "Truth is more important than approval"

  preserve_human_agency:
    category: "autonomy"
    severity: "critical"

  # ... more principles

rules:
  - name: "No Hidden Manipulation"
    principle: "truth_before_approval"
    condition: "agent uses persuasion without disclosure"
    action: "block"
    severity: "critical"

  - name: "Require Privacy Consent"
    principle: "preserve_human_agency"
    condition: "agent accesses personal data"
    action: "escalate"
    requires_human_approval: true
```

### Use Case: Custom Agent System

```python
# User building their own multi-agent system
from socratic_morality import Governor

# Define their constitution
governor = Governor(constitution={
    "supreme_principle": "Transparent and ethical AI",
    "principles": {
        "transparency": {...},
        "consent": {...},
    }
})

# In their custom agent
class MyLLMAgent:
    def __init__(self, governor: Governor):
        self.governor = governor

    async def execute(self, request):
        # Check constitution before acting
        decision = await self.governor.evaluate(
            action=request.action,
            actor=self.__class__.__name__,
            context=request.context
        )

        if not decision.allowed:
            raise ConstituionalViolationError(decision.reasoning)

        # Execute with confidence
        result = await self.process(request)

        # Store precedent
        await self.governor.precedent_engine.store_case(
            action=request.action,
            decision=decision,
            ...
        )

        return result
```

---

## Library 2: socratic-agents

### Purpose
Production-ready multi-agent system implementing the Socratic method for collaborative development. Provides pre-built agents governed by socratic-morality for educational, professional, and development workflows.

### Package Name
- **PyPI**: `socratic-agents`
- **Python Package**: `socratic_agents`
- **GitHub**: `github.com/Nireus79/socratic-agents`

### What It Exports

#### Core Classes
```python
from socratic_agents import (
    ProjectManager,
    SocraticCounselor,
    CodeGenerator,
    QualityController,
    KnowledgeAnalysis,
    SocratesAgentClient,
    SocratesAgentOrchestrator,
)
```

#### Agents Included
1. **ProjectManager** - Project creation and management
2. **SocraticCounselor** - Socratic dialogue engine
3. **CodeGenerator** - Generate code/documentation
4. **QualityController** - Quality and maturity assessment
5. **ConflictDetector** - Identify conflicts/inconsistencies
6. **KnowledgeAnalysis** - Knowledge base management
7. **DocumentProcessor** - Document parsing/embedding
8. **CodeValidation** - GitHub integration/validation
9. **UserLearning** - User learning tracking
10. **WorkflowOptimizer** - Workflow recommendations

#### Client Library
```python
from socratic_agents import SocratesAgentClient

client = SocratesAgentClient(
    api_url="http://socrates-api.internal:8000",
    auth_token="api_key_xxx"
)

# Call agents
project = await client.project_manager.create({
    "name": "E-Commerce Platform",
    "description": "..."
})

question = await client.socratic_counselor.get_question({
    "project_id": project["id"],
    "phase": "discovery"
})

code = await client.code_generator.generate({
    "project_id": project["id"],
    "language": "python"
})
```

### Dependencies

```toml
[project]
name = "socratic-agents"
version = "1.0.0"

dependencies = [
    "socratic-morality>=1.0.0",      # CRITICAL: Governance foundation
    "anthropic>=0.40.0",
    "chromadb>=0.5.0",
    "sentence-transformers>=3.0.0",
    "sqlalchemy>=2.0.0",
    "pydantic>=2.0.0",
    # ... other agent dependencies
]

[project.optional-dependencies]
server = ["fastapi>=0.100", "uvicorn>=0.23"]
dev = ["pytest>=7.0", ...]
```

### Agent Architecture

Each agent is **governed by socratic-morality**:

```python
class ProjectManager(Agent):
    def __init__(
        self,
        name: str,
        governor: Governor,           # ← From socratic-morality!
        agent_bus: AgentBus,
        database: ProjectDatabase,
        claude_client: ClaudeClient,
    ):
        super().__init__(name)
        self.governor = governor
        self.agent_bus = agent_bus
        self.database = database
        self.claude_client = claude_client

    async def process_async(self, request: dict) -> dict:
        # ✅ FIRST: Check constitution
        decision = await self.governor.evaluate(
            action="create_project",
            purpose=request.get("description", ""),
            actor="project_manager",
            context={
                "user_id": request["user_id"],
                "project_name": request["name"]
            }
        )

        if not decision.allowed:
            return {
                "error": "constitutional_violation",
                "violations": [v.principle for v in decision.violations]
            }

        # ✅ EXECUTE
        # ... business logic ...

        # ✅ STORE PRECEDENT
        await self.governor.precedent_engine.store_case(
            action="create_project",
            decision=decision,
            reasoning=decision.reasoning,
            ...
        )

        return result
```

### Target Users

1. **Educators** - Teaching Socratic method
2. **Development teams** - Collaborative coding
3. **Product managers** - Feature discovery
4. **Consultants** - Client onboarding
5. **Enterprises** - Internal workflows with governance
6. **Open-source maintainers** - Community learning

### Default Constitution

Comes with a pre-defined Socratic constitution based on Platonic philosophy:

```yaml
metadata:
  name: "Socratic Method Constitution"
  version: "1.0.0"
  basis: "Plato's Dialogues (Apology, Gorgias, Crito, Meno, Republic)"

supreme_principle: |
  It is better to suffer injustice than to commit it.

principles:
  never_commit_injustice:
    source: "Gorgias"
  truth_before_approval:
    source: "Apology"
  preserve_human_agency:
    source: "Crito"
  seek_understanding:
    source: "Meno"
  pursue_virtue:
    source: "Republic"
```

### Example Usage

```python
from socratic_agents import SocratesAgentClient, Governor
from socratic_morality import Constitution

# Load custom constitution
constitution = Constitution.load_from_file("my_constitution.yaml")

# Create governed client
client = SocratesAgentClient(
    api_url="http://localhost:8000",
    governor=Governor(constitution=constitution)
)

# Use agents with governance
async def main():
    # Create project
    project = await client.project_manager.create({
        "name": "My App",
        "description": "Web application",
        "user_id": "user_123"
    })

    # Ask Socratic questions
    for phase in ["discovery", "planning", "implementation"]:
        question = await client.socratic_counselor.get_question({
            "project_id": project["id"],
            "phase": phase,
            "user_id": "user_123"
        })

        print(f"Question: {question['content']}")

        # Get user response...
        response = await client.socratic_counselor.process_response({
            "project_id": project["id"],
            "response": user_input,
            "user_id": "user_123"
        })

    # Generate code
    code = await client.code_generator.generate({
        "project_id": project["id"],
        "language": "python",
        "user_id": "user_123"
    })

asyncio.run(main())
```

---

## Dependency Relationship

```
┌──────────────────────────────────────────────────────────┐
│ User's Application (e.g., Socrates, custom projects)     │
│                                                           │
│  dependencies:                                            │
│    - socratic-agents>=1.0                                │
│    - socratic-morality>=1.0 (also pulled in by agents)   │
│    - other app dependencies                              │
└──────────────┬───────────────────────────────────────────┘
               │
               │ depends on
               ↓
┌──────────────────────────────────────────────────────────┐
│ socratic-agents (application library)                     │
│                                                           │
│  dependencies:                                            │
│    - socratic-morality>=1.0 ← REQUIRED                   │
│    - anthropic>=0.40                                      │
│    - chromadb>=0.5                                        │
│    - sqlalchemy>=2.0                                      │
│    - ... other agent runtime dependencies               │
└──────────────┬───────────────────────────────────────────┘
               │
               │ depends on
               ↓
┌──────────────────────────────────────────────────────────┐
│ socratic-morality (foundation library)                    │
│                                                           │
│  dependencies (minimal):                                  │
│    - pydantic>=2.0                                        │
│    - pyyaml>=6.0                                          │
│    - typing-extensions>=4.0                              │
│                                                           │
│  optional dependencies:                                   │
│    - anthropic, openai, chromadb (for examples)          │
│    - aiosqlite, psycopg2 (for storage backends)          │
└──────────────────────────────────────────────────────────┘

IMPORT PATHS:

User's project:
    from socratic_agents import SocratesAgentClient
    from socratic_morality import Governor

Third-party (building custom agents):
    from socratic_morality import Governor

Socrates app:
    from socratic_agents import SocratesAgentOrchestrator
    from socratic_morality import Governor
```

---

## Extraction & Release Timeline

### Stage 1: Extract socratic-morality (Weeks 1-6)

**Repository Structure**:
```
socratic-morality/
├── src/socratic_morality/
│   ├── __init__.py
│   ├── constitution/
│   │   ├── loader.py
│   │   ├── models.py
│   │   ├── validator.py
│   │   └── __init__.py
│   ├── governor/
│   │   ├── core.py
│   │   ├── decision.py
│   │   ├── evaluator.py
│   │   ├── escalation.py
│   │   └── __init__.py
│   ├── ethics/
│   │   ├── deliberation.py
│   │   ├── frameworks.py
│   │   ├── stakeholder.py
│   │   └── __init__.py
│   ├── precedent/
│   │   ├── engine.py
│   │   ├── storage.py
│   │   ├── models.py
│   │   └── __init__.py
│   ├── security/
│   │   ├── capabilities.py
│   │   ├── sandbox.py
│   │   └── __init__.py
│   ├── storage/
│   │   ├── base.py
│   │   ├── memory.py
│   │   ├── sqlite.py
│   │   └── __init__.py
│   └── utils/
│       ├── logger.py
│       ├── serialization.py
│       └── __init__.py
├── tests/
├── examples/
├── docs/
├── pyproject.toml
├── README.md
└── LICENSE
```

**Milestones**:
- Week 1-2: Extract Governor core + Constitution framework
- Week 3: Add Ethical Deliberation Engine + frameworks
- Week 4: Implement Moral Precedent Engine + storage
- Week 5: Security layer + audit hooks
- Week 6: Testing, documentation, PyPI publication

**Release**: v1.0.0 to PyPI

### Stage 2: Extract socratic-agents (Weeks 7-14)

**Repository Structure**:
```
socratic-agents/
├── src/socratic_agents/
│   ├── __init__.py
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── project_manager.py
│   │   ├── socratic_counselor.py
│   │   ├── code_generator.py
│   │   ├── quality_controller.py
│   │   ├── conflict_detector.py
│   │   ├── knowledge_analysis.py
│   │   ├── document_processor.py
│   │   ├── code_validation.py
│   │   ├── user_learning.py
│   │   └── workflow_optimizer.py
│   ├── orchestrator.py
│   ├── bus.py
│   ├── client.py
│   ├── storage/
│   │   ├── base.py
│   │   ├── sqlite.py
│   │   └── __init__.py
│   └── api/
│       ├── routes.py
│       ├── models.py
│       └── __init__.py
├── examples/
├── tests/
├── docs/
├── pyproject.toml
├── README.md
└── LICENSE
```

**Milestones**:
- Week 7-8: Extract agent classes (ProjectManager, SocraticCounselor, CodeGenerator)
- Week 9: Extract remaining agents + orchestrator
- Week 10: Build REST API adapter + SocratesAgentClient
- Week 11: Integration testing with socratic-morality
- Week 12-13: Documentation + examples
- Week 14: Publication to PyPI

**Release**: v1.0.0 to PyPI

### Stage 3: Refactor Socrates App (Week 15+)

**Changes**:
- Replace internal agent code with imports from socratic-agents
- Replace governance code with imports from socratic-morality
- Remove extracted modules from codebase
- Keep: UI, API orchestration, project-specific logic

**Example**:
```python
# Before extraction
from socratic_system.agents.project_manager import ProjectManager
from socratic_system.governor import Governor

# After extraction
from socratic_agents import ProjectManager
from socratic_morality import Governor
```

---

## Comparison: One vs Two Libraries

| Aspect | Single Library | Two Libraries |
|--------|---|---|
| **socratic-agents package size** | N/A | ~15-25K LOC |
| **socratic-morality size** | Part of monolith | ~8-15K LOC (focused) |
| **Dependencies** | Heavy (all features) | Lean core + optional extras |
| **Reusability** | LangChain/AutoGen can't use governance | Any framework can use morality |
| **Community adoption** | Limited to Socrates use case | Unlimited governance adoptions |
| **Maintenance** | Update everything together | Update independently |
| **Version compatibility** | Major breaks affect both | Can update one without other |
| **Testing** | Monolithic test suite | Separate test suites |
| **Documentation** | Complex and long | Clear separation of concerns |
| **User choice** | "Take it or leave it" | Mix and match as needed |

---

## Versioning Strategy

### socratic-morality
```
v1.0.0 - Initial release (Governor, constitution, precedent)
v1.1.0 - Add storage backends (SQLite, PostgreSQL)
v1.2.0 - Add adapters for LangChain, AutoGen, CrewAI
v2.0.0 - Major: Different governance model (if needed)
```

### socratic-agents
```
v1.0.0 - Initial 10 agents + client
v1.1.0 - Add more agents (11+)
v1.2.0 - Performance optimizations
v1.3.0 - New governance features from socratic-morality v1.2
v2.0.0 - Major: New agent architecture (if needed)
```

**Compatibility Rule**: socratic-agents will always be compatible with the latest socratic-morality v1.x

---

## PyPI Publishing Checklist

### For socratic-morality
- [ ] Create separate GitHub repository
- [ ] Set up CI/CD pipeline
- [ ] Create PyPI account and project
- [ ] Configure publish workflow (GitHub Actions)
- [ ] Create documentation site (ReadTheDocs)
- [ ] Publish v1.0.0 to PyPI
- [ ] Create release notes
- [ ] Announce on Python forums

### For socratic-agents
- [ ] Create separate GitHub repository
- [ ] Set up CI/CD pipeline
- [ ] Create PyPI account and project
- [ ] Configure publish workflow
- [ ] Create documentation site
- [ ] Publish v1.0.0 to PyPI
- [ ] Create release notes

### For Socrates App
- [ ] Update to depend on both libraries
- [ ] Remove extracted code
- [ ] Test thoroughly with library dependencies
- [ ] Update CI/CD to test against published versions
- [ ] Update documentation with new structure

---

## Marketing & Positioning

### socratic-morality
**Tagline**: "Constitutional governance for trustworthy AI agents"

**Message**:
> Socratic Morality is an open-source framework for building accountable, governed multi-agent systems. Based on Socratic philosophy, it provides the Constitutional Governor pattern for any agent framework.

**Key Selling Points**:
- ✅ Works with any agent framework (LangChain, AutoGen, CrewAI, custom)
- ✅ Minimal dependencies (Pydantic + PyYAML only)
- ✅ Grounded in Socratic philosophy (not generic "AI safety")
- ✅ Production-ready governance layer
- ✅ Community-driven development

**Target Audiences**:
- Enterprise AI teams needing governance
- Open-source projects prioritizing trustworthiness
- Regulated industries (finance, healthcare, legal)
- AI safety researchers and practitioners

---

### socratic-agents
**Tagline**: "Socratic multi-agent system for collaborative development"

**Message**:
> Socratic Agents provides a production-ready multi-agent system implementing the Socratic method. Powered by Socratic Morality for trustworthy operation.

**Key Selling Points**:
- ✅ 10+ pre-built agents for development workflows
- ✅ Built on Socratic Morality governance framework
- ✅ Educational and professional use cases
- ✅ REST API + Python client library
- ✅ Extensible architecture

**Target Audiences**:
- Educators teaching collaborative methods
- Development teams (startup/enterprise)
- Product managers and strategists
- Open-source communities

---

### Socrates App
**Tagline**: "Collaborative development platform powered by Socratic AI"

**Message**:
> Socrates is a collaborative development platform that uses Socratic agents and morality-based governance to guide you through building better software.

**Powered By**:
- Socratic Agents (multi-agent orchestration)
- Socratic Morality (trustworthy AI governance)

---

## Installation Examples

### Using socratic-morality only

```bash
pip install socratic-morality
```

```python
from socratic_morality import Governor

governor = Governor(constitution="my_constitution.yaml")
decision = await governor.evaluate(...)
```

### Using socratic-agents (includes socratic-morality)

```bash
pip install socratic-agents
```

```python
from socratic_agents import SocratesAgentClient

client = SocratesAgentClient(api_url="http://localhost:8000")
project = await client.project_manager.create(...)
```

### Using Socrates app (includes both)

```bash
git clone https://github.com/Nireus79/Socrates.git
pip install -e .
```

```python
from socratic_agents import SocratesAgentOrchestrator
from socratic_morality import Governor

orchestrator = SocratesAgentOrchestrator(
    governor=Governor(constitution="..."),
    database_url="...",
)
```

---

## Repository Structure After Extraction

### socratic-morality (GitHub)
```
github.com/Nireus79/socratic-morality/
    ├── Governance framework
    ├── No specific agents
    ├── Minimal dependencies
    └── Focus: Constitutional AI governance
```

### socratic-agents (GitHub)
```
github.com/Nireus79/socratic-agents/
    ├── Agent implementations (10+)
    ├── Depends on socratic-morality
    ├── REST API
    ├── Python client library
    └── Focus: Socratic multi-agent system
```

### Socrates App (GitHub)
```
github.com/Nireus79/Socrates/
    ├── Web UI (frontend)
    ├── Application logic (orchestration, business rules)
    ├── Depends on socratic-agents
    ├── Depends on socratic-morality
    └── Focus: Full-featured collaborative platform
```

---

## Success Metrics

### socratic-morality v1.0.0
- ✅ Published to PyPI
- ✅ 200+ GitHub stars
- ✅ 10+ third-party projects using it
- ✅ Active community contributions
- ✅ Documentation complete
- ✅ Test coverage >80%

### socratic-agents v1.0.0
- ✅ Published to PyPI
- ✅ 150+ GitHub stars
- ✅ Used by Socrates app successfully
- ✅ 5+ example implementations
- ✅ Complete API documentation
- ✅ Test coverage >75%

### Socrates App
- ✅ Lightweight (<20K LOC app-specific code)
- ✅ Depends on published libraries
- ✅ Faster releases (decoupled from library changes)
- ✅ Easier contribution (clear separation)

---

## Risks & Mitigation

| Risk | Probability | Mitigation |
|------|-------------|-----------|
| Breaking changes in morality | Medium | Semantic versioning + deprecation period |
| Dependency conflicts | Low | Minimal core deps for morality |
| Community fragmentation | Low | Clear positioning + good docs |
| Maintenance burden | Medium | Community contributions + governance model |
| Integration complexity | Low | Comprehensive examples + integration tests |

---

## Conclusion

The two-library architecture provides:

1. **Clear Separation**: Governance (universal) vs. Implementation (specific)
2. **Maximum Reusability**: Anyone can use socratic-morality for their agents
3. **Easier Maintenance**: Update libraries independently
4. **Better Adoption**: Lower barrier to entry (use just what you need)
5. **Strong Community**: Foundation for ecosystem of Socratic-governed agents

This design positions Socratic Morality as **infrastructure for trustworthy AI** while Socratic Agents remains the **reference implementation**.

---

**Document Version**: 1.0
**Status**: Ready for Implementation
**Next Step**: Begin Phase 1 (socratic-morality extraction)
