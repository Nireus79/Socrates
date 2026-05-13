# Package README Template for Socratic-* Libraries

This document provides a template for each `socratic-*` package README to ensure consistent visibility, badges, and integration examples across all repositories.

## Overview

Each Socratic package should include:
1. **PyPI badges** (version, downloads, GitHub stars)
2. **Quick installation**
3. **Real-world example code**
4. **Integration with main platform**
5. **Links to main documentation**

---

## Template Structure

### Header Section

```markdown
# socratic-[feature]

[![PyPI](https://img.shields.io/pypi/v/socratic-[feature].svg)](https://pypi.org/project/socratic-[feature]/)
[![Downloads](https://img.shields.io/pypi/dm/socratic-[feature].svg)](https://pypi.org/project/socratic-[feature]/)
[![GitHub](https://img.shields.io/github/stars/Nireus79/Socratic-[feature].svg?style=social)](https://github.com/Nireus79/Socratic-[feature])
[![License](https://img.shields.io/github/license/Nireus79/Socratic-[feature].svg)](LICENSE)

**[One-line description of what this package does]**

This is a production-ready component of [Socrates AI](https://github.com/Nireus79/Socrates), a complete platform for building intelligent agent networks. You can use this package independently or as part of the full platform.

---

## Quick Start

### Installation

```bash
pip install socratic-[feature]
```

### Basic Usage

[Include actual working code example]

```python
from socratic_[feature] import [MainClass]

# Initialize
instance = [MainClass]()

# Use the feature
result = await instance.method()
```

---

## When to Use This Package

✅ Use this if you need to: [list specific use cases]
❌ Don't use this if you: [list when it's overkill or not needed]

---

## Features

- **Feature 1** - Description
- **Feature 2** - Description
- **Feature 3** - Description

---

## Integration with Socrates

This package is a component of the larger [Socrates AI](https://github.com/Nireus79/Socrates) platform:

```python
# As part of Socrates platform
pip install socrates-ai  # Includes this package + 36 others

# With specific components
pip install socratic-agents socratic-[feature] socratic-knowledge
```

**See full integration examples:** [ECOSYSTEM.md - socratic-[feature]](https://github.com/Nireus79/Socrates/blob/main/ECOSYSTEM.md)

---

## API Reference

[Include main classes/functions and their signatures]

### Class: [MainClass]

**Methods:**
- `method_name(param: Type) -> ReturnType` - Description

---

## Examples

### Example 1: [Use Case]

[Working code example]

### Example 2: [Use Case]

[Working code example]

---

## Configuration

[Include any environment variables or config options]

---

## Performance

[Include any performance characteristics relevant to this package]

---

## Contributing

To contribute to this package:

1. Fork the repo
2. Create a feature branch
3. Make your changes
4. Submit a PR to `dev` branch

See [CONTRIBUTING.md](../CONTRIBUTING.md) in main Socrates repo.

---

## Support

- **Issues:** [GitHub Issues](https://github.com/Nireus79/Socratic-[feature]/issues)
- **Discussions:** [Socrates Discussions](https://github.com/Nireus79/Socrates/discussions)
- **Documentation:** [Socrates Docs](https://github.com/Nireus79/Socrates/tree/main/docs)

---

## Related Packages

Often used with:
- `socratic-[related]` - Related functionality
- `socratic-[related]` - Related functionality

See [Socrates Ecosystem](https://github.com/Nireus79/Socrates/blob/main/ECOSYSTEM.md) for complete package map.

---

## License

MIT License - See [LICENSE](LICENSE) file
```

---

## Package-Specific Templates

### socratic-morality

**Header:** Constitutional AI & Ethical Governance

**Key Classes:** `EthicalGovernor`, `EthicalFramework`

**Use Case:** "Add ethical decision-making to ANY AI system"

**Example:**
```python
from socratic_morality import EthicalGovernor
governor = EthicalGovernor()
is_ethical = await governor.evaluate(decision)
```

---

### socratic-agents

**Header:** 14+ Specialized AI Agents

**Key Classes:** `CodeGeneratorAgent`, `QualityControllerAgent`, etc.

**Use Case:** "Drop-in agents for multi-agent systems"

**Example:**
```python
from socratic_agents import CodeGeneratorAgent
agent = CodeGeneratorAgent()
code = await agent.generate(spec)
```

---

### socratic-knowledge

**Header:** RAG & Semantic Search

**Key Classes:** `KnowledgeBase`, `SemanticSearcher`

**Use Case:** "Add semantic search to your application"

**Example:**
```python
from socratic_knowledge import KnowledgeBase
kb = KnowledgeBase()
results = await kb.search("query")
```

---

### socratic-nexus

**Header:** Event-Driven Component Communication

**Key Classes:** `EventEmitter`, `EventBus`

**Use Case:** "Coordinate between independent services"

**Example:**
```python
from socratic_nexus import EventEmitter
emitter = EventEmitter()
await emitter.publish("event_name", payload)
```

---

### socratic-conflict

**Header:** Conflict Detection & Resolution

**Key Classes:** `ConflictDetector`

**Use Case:** "Validate specifications and detect contradictions"

**Example:**
```python
from socratic_conflict import ConflictDetector
detector = ConflictDetector()
conflicts = detector.detect(spec)
```

---

### socratic-analyzer

**Header:** Analytics & Insight Categorization

**Key Classes:** `InsightAnalyzer`

**Use Case:** "Analyze patterns and categorize insights"

**Example:**
```python
from socratic_analyzer import InsightAnalyzer
analyzer = InsightAnalyzer()
insights = await analyzer.analyze(data)
```

---

### socratic-maturity

**Header:** Project Maturity Scoring

**Key Classes:** `MaturityCalculator`

**Use Case:** "Track project readiness and progress"

**Example:**
```python
from socratic_maturity import MaturityCalculator
calc = MaturityCalculator()
score = calc.score(project_data)
```

---

### socratic-learning

**Header:** User Learning Analytics

**Key Classes:** `LearningTracker`

**Use Case:** "Track how users interact and learn"

**Example:**
```python
from socratic_learning import LearningTracker
tracker = LearningTracker()
progress = tracker.get_progress(user_id)
```

---

### socratic-workflow

**Header:** Workflow Execution & Automation

**Key Classes:** `WorkflowEngine`, `Workflow`

**Use Case:** "Define and execute multi-step workflows"

**Example:**
```python
from socratic_workflow import WorkflowEngine, Workflow
engine = WorkflowEngine()
result = await engine.execute(workflow)
```

---

### socratic-performance

**Header:** Performance Profiling & Metrics

**Key Classes:** `PerformanceMonitor`

**Use Case:** "Monitor and optimize system performance"

**Example:**
```python
from socratic_performance import PerformanceMonitor
monitor = PerformanceMonitor()
metrics = monitor.get_metrics()
```

---

### socratic-docs

**Header:** Documentation Generation

**Key Classes:** `DocumentationGenerator`

**Use Case:** "Auto-generate documentation from code"

**Example:**
```python
from socratic_docs import DocumentationGenerator
gen = DocumentationGenerator()
docs = await gen.generate(spec)
```

---

## Implementation Checklist

For each package repository, add to README.md:

- [ ] PyPI badge (version)
- [ ] Downloads badge
- [ ] GitHub stars badge
- [ ] License badge
- [ ] "Part of Socrates AI" section with link
- [ ] Quick installation instructions
- [ ] Real working code example
- [ ] "When to use" / "When not to use" section
- [ ] Features list
- [ ] Full API reference
- [ ] 2-3 detailed examples
- [ ] Configuration section (if applicable)
- [ ] Performance characteristics (if applicable)
- [ ] Contributing guidelines
- [ ] Links to related packages
- [ ] Link to full Socrates ECOSYSTEM.md

---

## Badge Markdown Snippets

Copy-paste ready badge sections for each package:

### socratic-morality
```markdown
[![PyPI](https://img.shields.io/pypi/v/socratic-morality.svg)](https://pypi.org/project/socratic-morality/)
[![Downloads](https://img.shields.io/pypi/dm/socratic-morality.svg)](https://pypi.org/project/socratic-morality/)
[![GitHub](https://img.shields.io/github/stars/Nireus79/Socratic-morality.svg?style=social)](https://github.com/Nireus79/Socratic-morality)
```

### socratic-agents
```markdown
[![PyPI](https://img.shields.io/pypi/v/socratic-agents.svg)](https://pypi.org/project/socratic-agents/)
[![Downloads](https://img.shields.io/pypi/dm/socratic-agents.svg)](https://pypi.org/project/socratic-agents/)
[![GitHub](https://img.shields.io/github/stars/Nireus79/Socratic-agents.svg?style=social)](https://github.com/Nireus79/Socratic-agents)
```

### socratic-knowledge
```markdown
[![PyPI](https://img.shields.io/pypi/v/socratic-knowledge.svg)](https://pypi.org/project/socratic-knowledge/)
[![Downloads](https://img.shields.io/pypi/dm/socratic-knowledge.svg)](https://pypi.org/project/socratic-knowledge/)
[![GitHub](https://img.shields.io/github/stars/Nireus79/Socratic-knowledge.svg?style=social)](https://github.com/Nireus79/Socratic-knowledge)
```

### socratic-nexus
```markdown
[![PyPI](https://img.shields.io/pypi/v/socratic-nexus.svg)](https://pypi.org/project/socratic-nexus/)
[![Downloads](https://img.shields.io/pypi/dm/socratic-nexus.svg)](https://pypi.org/project/socratic-nexus/)
[![GitHub](https://img.shields.io/github/stars/Nireus79/Socratic-nexus.svg?style=social)](https://github.com/Nireus79/Socratic-nexus)
```

### socratic-conflict
```markdown
[![PyPI](https://img.shields.io/pypi/v/socratic-conflict.svg)](https://pypi.org/project/socratic-conflict/)
[![Downloads](https://img.shields.io/pypi/dm/socratic-conflict.svg)](https://pypi.org/project/socratic-conflict/)
[![GitHub](https://img.shields.io/github/stars/Nireus79/Socratic-conflict.svg?style=social)](https://github.com/Nireus79/Socratic-conflict)
```

### socratic-analyzer
```markdown
[![PyPI](https://img.shields.io/pypi/v/socratic-analyzer.svg)](https://pypi.org/project/socratic-analyzer/)
[![Downloads](https://img.shields.io/pypi/dm/socratic-analyzer.svg)](https://pypi.org/project/socratic-analyzer/)
[![GitHub](https://img.shields.io/github/stars/Nireus79/Socratic-analyzer.svg?style=social)](https://github.com/Nireus79/Socratic-analyzer)
```

### socratic-maturity
```markdown
[![PyPI](https://img.shields.io/pypi/v/socratic-maturity.svg)](https://pypi.org/project/socratic-maturity/)
[![Downloads](https://img.shields.io/pypi/dm/socratic-maturity.svg)](https://pypi.org/project/socratic-maturity/)
[![GitHub](https://img.shields.io/github/stars/Nireus79/Socratic-maturity.svg?style=social)](https://github.com/Nireus79/Socratic-maturity)
```

### socratic-learning
```markdown
[![PyPI](https://img.shields.io/pypi/v/socratic-learning.svg)](https://pypi.org/project/socratic-learning/)
[![Downloads](https://img.shields.io/pypi/dm/socratic-learning.svg)](https://pypi.org/project/socratic-learning/)
[![GitHub](https://img.shields.io/github/stars/Nireus79/Socratic-learning.svg?style=social)](https://github.com/Nireus79/Socratic-learning)
```

### socratic-workflow
```markdown
[![PyPI](https://img.shields.io/pypi/v/socratic-workflow.svg)](https://pypi.org/project/socratic-workflow/)
[![Downloads](https://img.shields.io/pypi/dm/socratic-workflow.svg)](https://pypi.org/project/socratic-workflow/)
[![GitHub](https://img.shields.io/github/stars/Nireus79/Socratic-workflow.svg?style=social)](https://github.com/Nireus79/Socratic-workflow)
```

### socratic-performance
```markdown
[![PyPI](https://img.shields.io/pypi/v/socratic-performance.svg)](https://pypi.org/project/socratic-performance/)
[![Downloads](https://img.shields.io/pypi/dm/socratic-performance.svg)](https://pypi.org/project/socratic-performance/)
[![GitHub](https://img.shields.io/github/stars/Nireus79/Socratic-performance.svg?style=social)](https://github.com/Nireus79/Socratic-performance)
```

### socratic-docs
```markdown
[![PyPI](https://img.shields.io/pypi/v/socratic-docs.svg)](https://pypi.org/project/socratic-docs/)
[![Downloads](https://img.shields.io/pypi/dm/socratic-docs.svg)](https://pypi.org/project/socratic-docs/)
[![GitHub](https://img.shields.io/github/stars/Nireus79/Socratic-docs.svg?style=social)](https://github.com/Nireus79/Socratic-docs)
```

---

## Notes

- Update badges quarterly to ensure they're pulling fresh data
- Keep integration examples working and up-to-date
- Link back to main Socrates repo for context
- Each package should be usable independently
- Package-specific docs can link to ecosystem for cross-references
