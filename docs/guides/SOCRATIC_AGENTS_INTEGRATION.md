# Socratic Agents Integration Guide

**Version:** 1.0
**Status:** Complete
**Last Updated:** 2026-03-24

---

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Agent Categories](#agent-categories)
4. [Agent Reference](#agent-reference)
5. [Integration Patterns](#integration-patterns)
6. [LLM-Enhanced Wrappers](#llm-enhanced-wrappers)
7. [Examples](#examples)
8. [Best Practices](#best-practices)

---

## Overview

**socratic-agents** is a multi-agent orchestration system providing 17+ specialized agents for different aspects of AI workflows. It integrates with Socrates to:

- **Analyze code quality** and identify improvements
- **Generate skills** for specific learning areas
- **Validate code** against standards
- **Manage projects** and track progress
- **Detect conflicts** in agent outputs
- **Process documents** and extract knowledge
- **Synchronize with GitHub** for version control
- **Monitor system health** and performance
- **Manage user interactions** and learning

### Architecture Overview

```
Socratic Agents
├── Base Agent (Abstract)
├── Analysis Agents (Quality, Code Validation, Knowledge)
├── Generation Agents (Code, Skills, Documentation)
├── Management Agents (Projects, Users, Notes)
├── Integration Agents (GitHub, Knowledge Base)
└── LLM-Enhanced Wrappers (For complex tasks)
```

### Why Use Socratic Agents?

| Feature | Benefit |
|---------|---------|
| **Specialized** | Each agent has specific domain expertise |
| **Composable** | Agents can be combined into workflows |
| **LLM-Ready** | Optional LLM enhancement for complex tasks |
| **Async-Capable** | Both sync and async processing supported |
| **Observable** | Built-in logging and monitoring |

---

## Installation

### Prerequisites

- Python 3.8+
- socratic-core >= 0.1.0

### From PyPI

```bash
pip install socratic-agents
```

### From Source

```bash
git clone https://github.com/anthropics/socratic-agents.git
cd socratic-agents
pip install -e .
```

### Verify Installation

```python
from socratic_agents import (
    BaseAgent,
    CodeGenerator,
    QualityController,
    SkillGeneratorAgent
)

print(f"Agents imported: {[CodeGenerator, QualityController, SkillGeneratorAgent]}")
```

---

## Agent Categories

### Analysis Agents

Agents that analyze code, documents, and knowledge.

#### QualityController
Analyzes code quality across multiple dimensions.

```python
from socratic_agents import QualityController

agent = QualityController()
result = agent.process({
    "code": source_code,
    "depth": "thorough"
})

# Returns: {quality_score, issues, recommendations}
```

#### CodeValidator
Validates code against style and quality standards.

```python
from socratic_agents import CodeValidator

agent = CodeValidator()
result = agent.process({
    "code": source_code,
    "standards": ["pep8", "type_checking"]
})

# Returns: {valid, violations, fixes}
```

#### ContextAnalyzer
Analyzes code context and dependencies.

```python
from socratic_agents import ContextAnalyzer

agent = ContextAnalyzer()
result = agent.process({
    "code": source_code,
    "context": "project_structure"
})

# Returns: {dependencies, imports, context}
```

#### KnowledgeAnalysis
Extracts knowledge from documents and code.

```python
from socratic_agents import KnowledgeAnalysis

agent = KnowledgeAnalysis()
result = agent.process({
    "content": document_content,
    "extract_type": "concepts"
})

# Returns: {concepts, relationships, insights}
```

### Generation Agents

Agents that generate code, skills, and documentation.

#### CodeGenerator
Generates code based on specifications.

```python
from socratic_agents import CodeGenerator

agent = CodeGenerator()
result = agent.process({
    "specification": task_description,
    "language": "python",
    "style": "professional"
})

# Returns: {code, explanation, tests}
```

#### SkillGeneratorAgent
Generates learning skills for specific areas.

```python
from socratic_agents import SkillGeneratorAgent

agent = SkillGeneratorAgent()
result = agent.process({
    "domain": "testing",
    "level": "intermediate",
    "focus": ["unit_tests", "mocking"]
})

# Returns: {skills, exercises, resources}
```

### Management Agents

Agents that manage projects, users, and system state.

#### ProjectManager
Manages project state and progress.

```python
from socratic_agents import ProjectManager

agent = ProjectManager()
result = agent.process({
    "action": "update_status",
    "project_id": "proj_123",
    "new_status": "in_progress"
})

# Returns: {project, updated_fields}
```

#### UserManager
Manages user information and preferences.

```python
from socratic_agents import UserManager

agent = UserManager()
result = agent.process({
    "action": "update_preferences",
    "user_id": "user_123",
    "preferences": {"language": "python"}
})

# Returns: {user, changes}
```

#### NoteManager
Manages notes and documentation.

```python
from socratic_agents import NoteManager

agent = NoteManager()
result = agent.process({
    "action": "create",
    "title": "Learning Notes",
    "content": "Important concepts..."
})

# Returns: {note_id, created_at}
```

### Integration Agents

Agents that integrate with external systems.

#### GithubSyncHandler
Synchronizes with GitHub repositories.

```python
from socratic_agents import GithubSyncHandler

agent = GithubSyncHandler()
result = agent.process({
    "action": "sync",
    "repo_url": "https://github.com/user/repo",
    "branch": "main"
})

# Returns: {status, synced_files, conflicts}
```

#### DocumentProcessor
Processes documents for knowledge extraction.

```python
from socratic_agents import DocumentProcessor

agent = DocumentProcessor()
result = agent.process({
    "document": document_content,
    "format": "markdown",
    "extract": ["code_blocks", "concepts"]
})

# Returns: {extracted_items, metadata}
```

### Monitoring Agents

Agents that monitor system health and performance.

#### SystemMonitor
Monitors system health and performance.

```python
from socratic_agents import SystemMonitor

agent = SystemMonitor()
result = agent.process({
    "check_type": "health"
})

# Returns: {status, metrics, alerts}
```

#### LearningAgent
Tracks learning progress and effectiveness.

```python
from socratic_agents import LearningAgent

agent = LearningAgent()
result = agent.process({
    "user_id": "user_123",
    "action": "track_progress"
})

# Returns: {progress, velocity, recommendations}
```

---

## Agent Reference

### BaseAgent Interface

All agents inherit from `BaseAgent` and implement this interface:

```python
from socratic_agents import BaseAgent

class CustomAgent(BaseAgent):
    def __init__(self, name: str, llm_client=None):
        super().__init__(name, llm_client)

    def process(self, request: dict) -> dict:
        """Synchronous processing"""
        return {"result": "data"}

    async def process_async(self, request: dict) -> dict:
        """Asynchronous processing (optional override)"""
        return await super().process_async(request)
```

### Data Models

#### AgentSkill

Represents a learnable skill.

```python
from socratic_agents import AgentSkill

skill = AgentSkill(
    name="Unit Testing",
    domain="testing",
    level="intermediate",
    description="Write effective unit tests",
    prerequisites=["Python Basics"],
    resources=["link1", "link2"]
)
```

#### SkillRecommendation

Recommends skills for learning.

```python
from socratic_agents import SkillRecommendation

recommendation = SkillRecommendation(
    skill_id="skill_123",
    confidence=0.85,
    reasoning="Code lacks test coverage",
    priority="high"
)
```

#### SkillApplicationResult

Result of applying a skill.

```python
from socratic_agents import SkillApplicationResult

result = SkillApplicationResult(
    skill_id="skill_123",
    applied_successfully=True,
    before_state=old_code,
    after_state=new_code,
    improvements=["test_coverage: 20% → 85%"]
)
```

---

## Integration Patterns

### Pattern 1: Serial Agent Execution

Execute agents one after another.

```python
from socratic_agents import QualityController, SkillGeneratorAgent, CodeGenerator

def quality_improvement_workflow(code: str) -> dict:
    """Execute quality improvement workflow"""

    # Step 1: Analyze quality
    quality_agent = QualityController()
    quality_result = quality_agent.process({
        "code": code,
        "depth": "thorough"
    })

    if quality_result.get("quality_score", 0) > 0.8:
        return {"status": "excellent", "result": code}

    # Step 2: Generate improving skills
    skill_agent = SkillGeneratorAgent()
    skill_result = skill_agent.process({
        "domain": "code_quality",
        "weak_areas": quality_result.get("issues", []),
        "level": "intermediate"
    })

    # Step 3: Generate improved code
    code_agent = CodeGenerator()
    code_result = code_agent.process({
        "specification": code,
        "skills": skill_result.get("skills", []),
        "apply_improvements": True
    })

    return {
        "original_score": quality_result.get("quality_score"),
        "improved_code": code_result.get("code"),
        "applied_skills": skill_result.get("skills", [])
    }

# Usage
improved = quality_improvement_workflow(source_code)
print(f"Quality: {improved['original_score']:.1%}")
```

### Pattern 2: Parallel Agent Execution

Execute agents concurrently.

```python
import asyncio
from socratic_agents import (
    QualityController,
    CodeValidator,
    ContextAnalyzer
)

async def analyze_code_parallel(code: str) -> dict:
    """Analyze code from multiple angles"""

    agents = [
        QualityController(),
        CodeValidator(),
        ContextAnalyzer()
    ]

    # Execute all agents in parallel
    results = await asyncio.gather(*[
        agent.process_async({"code": code})
        for agent in agents
    ])

    return {
        "quality": results[0],
        "validation": results[1],
        "context": results[2]
    }

# Usage
analysis = asyncio.run(analyze_code_parallel(source_code))
```

### Pattern 3: Conditional Agent Execution

Execute agents based on conditions.

```python
from socratic_agents import (
    QualityController,
    CodeValidator,
    DocumentProcessor
)

def conditional_workflow(request: dict) -> dict:
    """Execute agents conditionally based on input"""

    workflow_type = request.get("type")

    if workflow_type == "code_review":
        agent = QualityController()
        return agent.process(request)

    elif workflow_type == "validation":
        agent = CodeValidator()
        return agent.process(request)

    elif workflow_type == "documentation":
        agent = DocumentProcessor()
        return agent.process(request)

    else:
        return {"error": f"Unknown workflow type: {workflow_type}"}

# Usage
result = conditional_workflow({
    "type": "code_review",
    "code": source_code
})
```

### Pattern 4: Agent with LLM Enhancement

Use LLM-powered wrapper for complex tasks.

```python
from socratic_agents import LLMPoweredCodeGenerator
from socratic_nexus import LLMClient

# Initialize LLM client
llm_client = LLMClient(api_key="sk-...")

# Create LLM-enhanced agent
agent = LLMPoweredCodeGenerator(llm_client)

result = agent.process({
    "specification": "Create a function to parse JSON with error handling",
    "language": "python",
    "complexity": "advanced"
})

# LLM is used for complex reasoning
print(f"Generated: {result['code']}")
```

### Pattern 5: Chained Agent Workflow

Chain multiple agents where output of one feeds into next.

```python
from socratic_agents import (
    QualityController,
    SkillGeneratorAgent,
    CodeGenerator
)

class CodeImprovementChain:
    def __init__(self):
        self.quality_agent = QualityController()
        self.skill_agent = SkillGeneratorAgent()
        self.code_agent = CodeGenerator()

    def execute(self, code: str, max_iterations: int = 3) -> dict:
        """Iteratively improve code quality"""

        current_code = code
        history = []

        for iteration in range(max_iterations):
            # Analyze quality
            quality = self.quality_agent.process({
                "code": current_code
            })

            score = quality.get("quality_score", 0)
            history.append({"iteration": iteration, "score": score})

            if score > 0.9:
                break

            # Generate improvements
            issues = quality.get("issues", [])
            skills = self.skill_agent.process({
                "domain": "code_quality",
                "weak_areas": issues
            })

            # Generate improved code
            current_code = self.code_agent.process({
                "code": current_code,
                "issues": issues,
                "skills": skills.get("skills", [])
            }).get("code", current_code)

        return {
            "final_code": current_code,
            "improvement_history": history,
            "final_score": history[-1]["score"] if history else 0
        }

# Usage
chain = CodeImprovementChain()
result = chain.execute(source_code, max_iterations=3)
print(f"Improved from {result['improvement_history'][0]['score']:.1%} to {result['final_score']:.1%}")
```

---

## LLM-Enhanced Wrappers

### Available Wrappers

| Wrapper | Purpose |
|---------|---------|
| **LLMPoweredCodeGenerator** | Generate complex code with reasoning |
| **LLMPoweredCodeValidator** | Validate with contextual understanding |
| **LLMPoweredQualityController** | Deep quality analysis with reasoning |
| **LLMPoweredProjectManager** | Smart project management decisions |
| **LLMPoweredKnowledgeManager** | Semantic knowledge management |
| **LLMPoweredContextAnalyzer** | Advanced context understanding |
| **LLMPoweredCounselor** | Interactive learning guidance |

### Using LLM Wrappers

```python
from socratic_agents import LLMPoweredQualityController
from socratic_nexus import LLMClient

# Create LLM client
llm = LLMClient(api_key="sk-...", model="claude-3-sonnet")

# Create LLM-enhanced agent
quality = LLMPoweredQualityController(llm_client=llm)

# Process with LLM reasoning
result = quality.process({
    "code": source_code,
    "depth": "comprehensive"
})

# LLM provides detailed explanations
print(f"Issues: {result['issues']}")
print(f"Reasoning: {result['reasoning']}")
```

---

## Examples

### Example 1: Complete Code Review Workflow

```python
"""Full code review with quality analysis and improvement suggestions"""

from socratic_agents import (
    QualityController,
    CodeValidator,
    SkillGeneratorAgent
)

def complete_code_review(code: str) -> dict:
    """Perform comprehensive code review"""

    # 1. Quality analysis
    quality_agent = QualityController()
    quality = quality_agent.process({
        "code": code,
        "depth": "thorough"
    })

    # 2. Code validation
    validator = CodeValidator()
    validation = validator.process({
        "code": code,
        "standards": ["pep8", "type_hints"]
    })

    # 3. Skill recommendations
    skill_agent = SkillGeneratorAgent()
    skills = skill_agent.process({
        "domain": "code_quality",
        "weak_areas": quality.get("issues", []),
        "level": "intermediate"
    })

    return {
        "overall_score": quality.get("quality_score"),
        "quality_analysis": quality,
        "validation_results": validation,
        "recommended_skills": skills.get("skills", []),
        "review_summary": {
            "quality_score": quality.get("quality_score"),
            "violations": len(validation.get("violations", [])),
            "learning_opportunities": len(skills.get("skills", []))
        }
    }

# Usage
code = '''
def calculate(a, b):
    return a + b
'''

review = complete_code_review(code)
print(f"Quality Score: {review['overall_score']:.1%}")
print(f"Violations: {review['review_summary']['violations']}")
print(f"Learning Opportunities: {review['review_summary']['learning_opportunities']}")
```

### Example 2: GitHub Integration Workflow

```python
"""Integrate with GitHub for automated code review"""

from socratic_agents import GithubSyncHandler, QualityController

def review_github_repo(repo_url: str, branch: str = "main") -> dict:
    """Review code in GitHub repository"""

    # 1. Sync with GitHub
    github_agent = GithubSyncHandler()
    sync_result = github_agent.process({
        "action": "sync",
        "repo_url": repo_url,
        "branch": branch
    })

    if not sync_result.get("success"):
        return {"error": "Failed to sync with GitHub"}

    # 2. Analyze all Python files
    quality_agent = QualityController()
    files = sync_result.get("synced_files", [])

    analysis_results = {}
    for file_path in files:
        if file_path.endswith(".py"):
            with open(file_path, 'r') as f:
                code = f.read()

            result = quality_agent.process({"code": code})
            analysis_results[file_path] = {
                "quality_score": result.get("quality_score"),
                "issues": result.get("issues", [])
            }

    return {
        "repo": repo_url,
        "branch": branch,
        "files_analyzed": len(analysis_results),
        "analysis": analysis_results
    }

# Usage
results = review_github_repo("https://github.com/user/repo")
```

### Example 3: Learning Path Generation

```python
"""Generate personalized learning path based on code gaps"""

from socratic_agents import (
    QualityController,
    SkillGeneratorAgent,
    LearningAgent
)

def generate_learning_path(code: str, user_id: str) -> dict:
    """Generate learning path for skill development"""

    # 1. Identify gaps
    quality_agent = QualityController()
    quality = quality_agent.process({"code": code})

    # 2. Generate skills for gaps
    skill_agent = SkillGeneratorAgent()
    skills = skill_agent.process({
        "domain": "code_quality",
        "weak_areas": quality.get("issues", []),
        "level": "intermediate"
    })

    # 3. Track learning progress
    learning_agent = LearningAgent()
    learning_path = learning_agent.process({
        "user_id": user_id,
        "action": "create_learning_path",
        "skills": skills.get("skills", []),
        "current_level": "intermediate"
    })

    return {
        "user_id": user_id,
        "identified_gaps": quality.get("issues", []),
        "recommended_skills": skills.get("skills", []),
        "learning_path": learning_path.get("path", []),
        "estimated_duration_hours": learning_path.get("duration_hours", 0)
    }

# Usage
path = generate_learning_path(source_code, "user_123")
print(f"Learning Path Length: {len(path['learning_path'])} steps")
print(f"Estimated Duration: {path['estimated_duration_hours']} hours")
```

---

## Best Practices

### 1. Use Appropriate Agent for Task

```python
# Good: Match agent to task
if task == "validate_syntax":
    agent = CodeValidator()  # Correct for validation
elif task == "improve_code":
    agent = CodeGenerator()  # Correct for generation

# Avoid: Using wrong agent
agent = QualityController()
result = agent.process({"action": "fix_code"})  # Not designed for this
```

### 2. Handle Agent Errors

```python
from socratic_agents import BaseAgent

try:
    agent = QualityController()
    result = agent.process({"code": code})

    if not result.get("success"):
        print(f"Agent reported: {result.get('error')}")

except Exception as e:
    print(f"Agent failed: {e}")
    # Fallback behavior
    result = {"quality_score": 0, "error": str(e)}
```

### 3. Use Async When Possible

```python
import asyncio

async def analyze_multiple_files(files: list) -> dict:
    """Analyze multiple files in parallel"""

    agent = QualityController()
    results = await asyncio.gather(*[
        agent.process_async({"code": open(f).read()})
        for f in files
    ])

    return {
        "files_analyzed": len(files),
        "scores": [r.get("quality_score", 0) for r in results]
    }

# Usage
results = asyncio.run(analyze_multiple_files(["file1.py", "file2.py"]))
```

### 4. Cache Agent Results

```python
from socratic_core.utils import TTLCache

class CachedQualityChecker:
    def __init__(self):
        self.agent = QualityController()
        self.cache = TTLCache(ttl_minutes=60)

    def check_quality(self, code: str) -> dict:
        """Check quality with caching"""

        code_hash = hash(code)

        if code_hash in self.cache:
            return self.cache[code_hash]

        result = self.agent.process({"code": code})
        self.cache[code_hash] = result

        return result

# Usage
checker = CachedQualityChecker()
result1 = checker.check_quality(code)  # Computed
result2 = checker.check_quality(code)  # Cached
```

### 5. Log Agent Activities

```python
import logging

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger("agents")

def logged_agent_execution(agent, request):
    """Execute agent with logging"""

    logger.info(f"Agent: {agent.name}, Request: {request}")

    try:
        result = agent.process(request)
        logger.info(f"Agent {agent.name} succeeded")
        return result

    except Exception as e:
        logger.error(f"Agent {agent.name} failed: {e}")
        raise
```

---

## Troubleshooting

### Agent Process Fails

**Problem:** Agent returns error or unexpected result.

**Solution:** Check request format and agent capabilities.

```python
# Verify agent is initialized
agent = QualityController()
print(f"Agent: {agent.name}")

# Check request format
request = {
    "code": source_code,
    "depth": "thorough"
}

# Validate request has required fields
required_fields = ["code"]
for field in required_fields:
    if field not in request:
        raise ValueError(f"Missing required field: {field}")

result = agent.process(request)
```

### LLM Wrapper Errors

**Problem:** LLM-enhanced agent fails or produces poor results.

**Solution:** Ensure LLM client is properly configured.

```python
from socratic_agents import LLMPoweredCodeGenerator
from socratic_nexus import LLMClient

# Verify LLM is available
try:
    llm = LLMClient(api_key="sk-...", model="claude-3-sonnet")
    agent = LLMPoweredCodeGenerator(llm_client=llm)

    # Test with simple request first
    result = agent.process({
        "specification": "hello world function",
        "language": "python"
    })

    if result.get("success"):
        print("LLM agent working correctly")

except Exception as e:
    print(f"LLM setup failed: {e}")
```

### Memory Issues with Large Batches

**Problem:** Processing many items causes memory issues.

**Solution:** Process in batches with explicit cleanup.

```python
from socratic_agents import QualityController
import gc

def batch_analyze(files: list, batch_size: int = 10) -> dict:
    """Analyze files in batches to manage memory"""

    agent = QualityController()
    results = []

    for i in range(0, len(files), batch_size):
        batch = files[i:i+batch_size]

        for file_path in batch:
            code = open(file_path).read()
            result = agent.process({"code": code})
            results.append(result)

        # Cleanup between batches
        gc.collect()

    return {"total_analyzed": len(results), "results": results}
```

---

## Related Documentation

- [Architecture Overview](../ARCHITECTURE.md)
- [Adding New Agents](./ADDING_NEW_AGENTS.md)
- [Common Integration Patterns](./COMMON_INTEGRATION_PATTERNS.md)
- [Common Recipes](./COMMON_RECIPES.md)

---

## Support

For issues, bugs, or feature requests:
- GitHub: https://github.com/anthropics/socratic-agents
- Documentation: https://socratic-agents.readthedocs.io
