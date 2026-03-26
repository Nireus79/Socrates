# Using PyPI Libraries in Socrates

Complete guide to using the PyPI libraries in the Socrates ecosystem. These libraries provide reusable, pure components that can be used independently or within Socrates.

---

## Table of Contents

1. [Overview](#overview)
2. [Available Libraries](#available-libraries)
3. [Installation](#installation)
4. [Core Concepts](#core-concepts)
5. [Using socratic-agents](#using-socratic-agents)
6. [Using socrates-nexus](#using-socrates-nexus)
7. [Using socratic-learning](#using-socratic-learning)
8. [Library Patterns](#library-patterns)
9. [Dependency Injection](#dependency-injection)
10. [Error Handling](#error-handling)
11. [Integration Examples](#integration-examples)

---

## Overview

The Socrates ecosystem consists of 10+ PyPI libraries that provide:

- **Pure Functions**: No database coupling, no side effects
- **Reusable Components**: Can be used in any Python project
- **Dependency Injection**: All dependencies explicitly passed in
- **Event-Driven**: Callback-based communication
- **Type-Safe**: Full type hints throughout

### Architecture

```
Your Application
  └─> socratic-agents (14 specialized agents)
  └─> socrates-nexus (LLM client wrapper)
  └─> socratic-learning (learning system)
  └─> 7 other specialized libraries
```

Each library:
- ✅ Works standalone
- ✅ Has no database access
- ✅ Uses dependency injection
- ✅ Provides clear interfaces
- ✅ Can be swapped/extended

---

## Available Libraries

### Core Libraries

#### 1. socratic-agents
**Purpose**: Agent framework for AI-powered tasks
**Use When**: You need specialized AI agents for code generation, validation, analysis, etc.

```python
from socratic_agents import CodeGenerator, CodeValidator, Agent
```

#### 2. socrates-nexus
**Purpose**: LLM client and API wrapper
**Use When**: You need to call Claude, GPT, or other LLMs

```python
from socrates_nexus import LLMClient
```

#### 3. socratic-learning
**Purpose**: Learning system and user profiling
**Use When**: You need to track learning, generate skills, or manage user progress

```python
from socratic_learning import LearningSystem, SkillGenerator
```

### Specialized Libraries

#### 4. socratic-maturity
**Purpose**: Maturity calculation and gating
**Use When**: You need to gate features based on user skill level

#### 5. socratic-code-analysis
**Purpose**: Code analysis and validation
**Use When**: You need to analyze code quality, detect issues, suggest improvements

#### 6. socratic-conflict-detection
**Purpose**: Conflict detection in project specifications
**Use When**: You need to identify inconsistencies in user requirements

#### 7-10. Other Specialized Libraries
- socratic-documentation
- socratic-orchestration
- socratic-persistence
- socratic-events

---

## Installation

### Install Single Library

```bash
pip install socratic-agents
pip install socrates-nexus
pip install socratic-learning
```

### Install Multiple Libraries

```bash
pip install socratic-agents socrates-nexus socratic-learning
```

### Install with Socrates

```bash
cd socrates
pip install -r requirements.txt  # Includes all libraries
```

### Install from Source (Development)

```bash
# Clone library repository
git clone https://github.com/anthropics/socratic-agents.git
cd socratic-agents

# Install in editable mode
pip install -e .
```

### Verify Installation

```python
import socratic_agents
import socrates_nexus
import socratic_learning

print(socratic_agents.__version__)
print(socrates_nexus.__version__)
print(socratic_learning.__version__)
```

---

## Core Concepts

### 1. Pure Functions

Libraries provide pure functions with no side effects:

```python
# Good - Pure function
def analyze_code(code: str, language: str) -> Dict[str, Any]:
    """Analyze code without side effects."""
    # No database access
    # No file I/O
    # No global state changes
    return {"issues": [...], "quality_score": 85}

# Bad - Not pure (has side effects)
def analyze_code(code: str, language: str) -> Dict[str, Any]:
    db.save_analysis(code)  # Side effect!
    return {"issues": [...]}
```

### 2. Dependency Injection

All dependencies passed explicitly:

```python
# Constructor injection
agent = CodeValidator(llm_client=llm_client)

# Parameter injection
result = agent.process(code, language="python")

# Callback injection
orchestrator = PureOrchestrator(
    get_maturity=get_maturity_function,
    on_event=event_callback_function
)
```

### 3. Callback-Based Communication

Instead of direct calls, use callbacks:

```python
# Register callbacks
def on_analysis_complete(event_data):
    """Called when analysis is done."""
    print(f"Analysis complete: {event_data}")

# Use callbacks
orchestrator = Orchestrator(
    on_event=on_analysis_complete
)
```

### 4. Graceful Degradation

Libraries work without optional dependencies:

```python
# Works without LLM
agent = CodeGenerator(llm_client=None)
result = agent.process({"prompt": "..."})  # Returns stub response

# Works with LLM
agent = CodeGenerator(llm_client=llm_client)
result = agent.process({"prompt": "..."})  # Returns real response
```

---

## Using socratic-agents

### Basic Agent Usage

```python
from socratic_agents import CodeGenerator, LLMClient

# Create LLM client
llm = LLMClient(
    provider="anthropic",
    api_key="sk-ant-..."
)

# Create agent
generator = CodeGenerator(llm_client=llm)

# Use agent
result = generator.process({
    "prompt": "Write a Python function that sorts a list",
    "language": "python",
    "requirements": "Must handle empty lists"
})

print(result["code"])
```

### Available Agents

```python
from socratic_agents import (
    CodeGenerator,      # Generate code from specs
    CodeValidator,      # Validate code syntax/semantics
    QualityController,  # Analyze code quality
    SocraticCounselor,  # Provide learning guidance
    LearningAgent,      # Track learning progress
    SkillGeneratorAgent,# Generate skills for weak areas
    ProjectManager,     # Manage project lifecycle
    ContextAnalyzer     # Analyze project context
)
```

### Agent Pattern

All agents follow this pattern:

```python
from socratic_agents import Agent
from typing import Dict, Any, Optional

class MyAgent(Agent):
    def __init__(self, llm_client: Optional[LLMClient]):
        super().__init__(llm_client)

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process request and return result."""
        try:
            # Handle request
            result = self._handle_request(request)
            return {
                "status": "success",
                "data": result
            }
        except Exception as e:
            return {
                "status": "error",
                "message": str(e)
            }

    def _handle_request(self, request: Dict[str, Any]) -> Any:
        """Implementation details."""
        pass
```

### Chaining Agents

```python
# Generate code with one agent, validate with another
generator = CodeGenerator(llm_client=llm)
validator = CodeValidator(llm_client=llm)

# Generate
code_result = generator.process({
    "prompt": "...",
    "language": "python"
})

# Validate generated code
if code_result["status"] == "success":
    validation = validator.process({
        "code": code_result["data"]["code"],
        "language": "python"
    })

    print(f"Valid: {validation['data']['valid']}")
```

---

## Using socrates-nexus

### LLMClient Basics

```python
from socrates_nexus import LLMClient

# Create client
llm = LLMClient(
    provider="anthropic",
    model="claude-3-sonnet",
    api_key="sk-ant-..."
)

# Make request
response = llm.chat(
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ],
    temperature=0.7,
    max_tokens=1000
)

print(response)
```

### Supported Providers

```python
# Anthropic Claude
llm = LLMClient(
    provider="anthropic",
    model="claude-3-sonnet",
    api_key="sk-ant-..."
)

# OpenAI GPT
llm = LLMClient(
    provider="openai",
    model="gpt-4",
    api_key="sk-..."
)

# Google Gemini
llm = LLMClient(
    provider="google",
    model="gemini-pro",
    api_key="..."
)
```

### Request Options

```python
response = llm.chat(
    messages=[...],
    temperature=0.7,        # Creativity (0-1)
    top_p=0.9,              # Diversity
    max_tokens=2000,        # Response length limit
    top_k=40,               # Token selection
    stop_sequences=["END"]  # Stop generation
)
```

### Streaming Responses

```python
# Stream response (for large outputs)
stream = llm.chat_stream(
    messages=[...],
    temperature=0.7
)

for chunk in stream:
    print(chunk, end="", flush=True)
```

### Error Handling

```python
try:
    response = llm.chat(messages=[...])
except LLMError as e:
    print(f"LLM error: {e}")
except RateLimitError as e:
    print(f"Rate limit exceeded: {e}")
    # Implement backoff
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

## Using socratic-learning

### Learning System Basics

```python
from socratic_learning import LearningSystem

# Create system
learning = LearningSystem()

# Record interaction
learning.record_interaction({
    "user_id": "user_123",
    "action": "code_generation",
    "success": True,
    "difficulty": 3,
    "timestamp": datetime.now()
})

# Get user profile
profile = learning.get_user_profile("user_123")
print(f"Maturity: {profile['maturity']}")
print(f"Skills: {profile['skills']}")
```

### Skill Generation

```python
from socratic_learning import SkillGenerator

generator = SkillGenerator()

# Analyze user weaknesses
skills = generator.generate_skills({
    "user_id": "user_123",
    "weak_areas": ["async_programming", "error_handling"],
    "learning_style": "hands_on"
})

for skill in skills:
    print(f"Skill: {skill['name']}")
    print(f"Difficulty: {skill['difficulty']}")
    print(f"Duration: {skill['estimated_duration']}")
```

### Learning Effectiveness

```python
# Track effectiveness of learning
learning.record_learning_outcome({
    "user_id": "user_123",
    "skill_id": "async_programming_1",
    "effectiveness": 0.85,  # 0-1 scale
    "completion_time": 45,  # minutes
    "notes": "User understood concepts well"
})

# Get effectiveness metrics
metrics = learning.get_learning_metrics("user_123")
print(f"Average effectiveness: {metrics['avg_effectiveness']}")
```

---

## Library Patterns

### Pattern 1: Agent Chaining

Process data through multiple agents sequentially:

```python
def chain_agents(input_data):
    # Step 1: Generate
    generator = CodeGenerator(llm_client=llm)
    generated = generator.process(input_data)

    # Step 2: Validate
    validator = CodeValidator(llm_client=llm)
    validated = validator.process({
        "code": generated["data"]["code"]
    })

    # Step 3: Analyze quality
    quality = QualityController(llm_client=llm)
    analysis = quality.process({
        "code": generated["data"]["code"]
    })

    return {
        "generated": generated,
        "validated": validated,
        "quality": analysis
    }
```

### Pattern 2: Orchestrated Workflow

Use orchestrator to manage agent selection:

```python
from socratic_agents import PureOrchestrator

# Define callbacks
def get_user_maturity(user_id):
    return 0.7  # From your database

def on_event(event_type, event_data):
    print(f"Event: {event_type} - {event_data}")

# Create orchestrator
orchestrator = PureOrchestrator(
    agents={
        "code_gen": CodeGenerator(llm_client=llm),
        "validator": CodeValidator(llm_client=llm),
        "quality": QualityController(llm_client=llm)
    },
    get_maturity=get_user_maturity,
    on_event=on_event
)

# Execute based on maturity
result = orchestrator.execute_agents_for_phase(
    user_id="user_123",
    phase="advanced"
)
```

### Pattern 3: Custom Callbacks

Implement custom behavior via callbacks:

```python
def my_event_handler(event_type, event_data):
    """Handle events from agents."""
    if event_type == "code_generated":
        # Save generated code
        save_to_database(event_data["code"])
        # Log event
        logger.info(f"Generated code for {event_data['project_id']}")
    elif event_type == "validation_complete":
        # Update validation status
        update_status("validation", event_data["valid"])

# Use with orchestrator
orchestrator = PureOrchestrator(
    agents={...},
    on_event=my_event_handler
)
```

---

## Dependency Injection

### Method 1: Constructor Injection

```python
class MyService:
    def __init__(self,
                 agent: CodeGenerator,
                 llm_client: LLMClient):
        self.agent = agent
        self.llm_client = llm_client

    def process(self, request):
        return self.agent.process(request)

# Usage
service = MyService(
    agent=CodeGenerator(llm_client=llm),
    llm_client=llm
)
```

### Method 2: Factory Pattern

```python
class AgentFactory:
    @staticmethod
    def create_agent(agent_type: str,
                    llm_client: Optional[LLMClient]):
        agents = {
            "code_gen": CodeGenerator(llm_client),
            "validator": CodeValidator(llm_client),
            "quality": QualityController(llm_client)
        }
        return agents[agent_type]

# Usage
agent = AgentFactory.create_agent("code_gen", llm)
```

### Method 3: Configuration Object

```python
from dataclasses import dataclass

@dataclass
class AgentConfig:
    llm_client: Optional[LLMClient]
    temperature: float = 0.7
    max_tokens: int = 2000

# Usage
config = AgentConfig(llm_client=llm, temperature=0.8)
agent = CodeGenerator(**vars(config))
```

---

## Error Handling

### Agent Errors

```python
from socratic_agents import AgentError

try:
    result = agent.process(request)
except AgentError as e:
    print(f"Agent error: {e.message}")
    print(f"Error code: {e.code}")
    # Graceful degradation
except Exception as e:
    print(f"Unexpected error: {e}")
```

### LLM Errors

```python
from socrates_nexus import LLMError, RateLimitError

try:
    response = llm.chat(messages=[...])
except RateLimitError as e:
    # Implement exponential backoff
    time.sleep(2 ** retry_count)
    response = llm.chat(messages=[...])
except LLMError as e:
    # Log and handle gracefully
    logger.error(f"LLM error: {e}")
```

### Graceful Degradation

```python
# Create agent without LLM
agent = CodeGenerator(llm_client=None)

# Still works with stub responses
result = agent.process(request)

# Check if using real LLM or stub
if result.get("mode") == "stub":
    print("Using placeholder responses (no LLM configured)")
else:
    print("Using real LLM responses")
```

---

## Integration Examples

### Example 1: Standalone Agent Usage

```python
from socratic_agents import CodeGenerator
from socrates_nexus import LLMClient

# Create LLM client
llm = LLMClient(
    provider="anthropic",
    api_key="sk-ant-..."
)

# Create agent
generator = CodeGenerator(llm_client=llm)

# Generate code
result = generator.process({
    "prompt": "Create a function to calculate fibonacci numbers",
    "language": "python",
    "style": "functional"
})

if result["status"] == "success":
    print("Generated code:")
    print(result["data"]["code"])
```

### Example 2: With Learning Tracking

```python
from socratic_agents import CodeGenerator
from socratic_learning import LearningSystem

llm = LLMClient(provider="anthropic", api_key="sk-ant-...")
generator = CodeGenerator(llm_client=llm)
learning = LearningSystem()

# Generate code
result = generator.process({
    "prompt": "...",
    "language": "python"
})

# Track in learning system
learning.record_interaction({
    "user_id": "user_123",
    "action": "code_generation",
    "success": result["status"] == "success",
    "difficulty": 3,
    "timestamp": datetime.now()
})
```

### Example 3: Multi-Agent Workflow

```python
from socratic_agents import (
    CodeGenerator, CodeValidator, QualityController
)

def complete_code_workflow(request):
    """Generate, validate, and analyze code."""

    # Step 1: Generate
    generator = CodeGenerator(llm_client=llm)
    code_result = generator.process(request)

    if code_result["status"] != "success":
        return {"status": "error", "stage": "generation"}

    # Step 2: Validate
    validator = CodeValidator(llm_client=llm)
    validation = validator.process({
        "code": code_result["data"]["code"],
        "language": request["language"]
    })

    if not validation["data"]["valid"]:
        return {"status": "error", "stage": "validation"}

    # Step 3: Quality analysis
    quality = QualityController(llm_client=llm)
    analysis = quality.process({
        "code": code_result["data"]["code"],
        "language": request["language"]
    })

    return {
        "status": "success",
        "code": code_result["data"]["code"],
        "quality_score": analysis["data"]["score"],
        "issues": analysis["data"]["issues"]
    }
```

### Example 4: Orchestrated Learning Path

```python
from socratic_agents import PureOrchestrator
from socratic_learning import SkillGenerator

def create_personalized_learning_path(user_id):
    """Create learning path based on user maturity."""

    # Get user maturity
    learning_system = LearningSystem()
    user_profile = learning_system.get_user_profile(user_id)
    maturity = user_profile["maturity"]

    # Generate skills for weak areas
    skill_gen = SkillGenerator()
    skills = skill_gen.generate_skills({
        "user_id": user_id,
        "weak_areas": user_profile["weak_areas"],
        "maturity": maturity
    })

    # Create orchestrator with maturity gating
    orchestrator = PureOrchestrator(
        agents={
            "beginner": CodeGenerator(llm_client=llm),
            "intermediate": CodeValidator(llm_client=llm),
            "advanced": QualityController(llm_client=llm)
        },
        get_maturity=lambda: maturity,
        on_event=lambda evt, data: learning_system.log_event(evt, data)
    )

    return {
        "skills": skills,
        "orchestrator": orchestrator,
        "maturity": maturity
    }
```

---

## Best Practices

1. **Always use dependency injection** - Pass dependencies explicitly
2. **Handle errors gracefully** - Never let exceptions bubble up uncaught
3. **Test agents independently** - Mock LLM for unit tests
4. **Use callbacks for events** - Don't tightly couple components
5. **Configure graceful degradation** - Support stub mode without LLM
6. **Type hint everything** - Make code self-documenting
7. **Log important events** - Track agent execution for debugging
8. **Cache when possible** - Avoid redundant LLM calls
9. **Implement rate limiting** - Respect LLM API limits
10. **Document custom agents** - Make extensions clear for others

---

**Last Updated**: 2026-03-26
**Version**: 1.0.0
