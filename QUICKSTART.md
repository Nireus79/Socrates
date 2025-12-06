# Socrates AI - Quick Start Guide

Socrates AI is a complete, production-ready Python library for building intelligent tutoring systems using Claude AI. You can install it with one command and start using it immediately.

## Installation

```bash
pip install socrates-ai
```

That's it! The library is fully self-contained and includes everything you need.

## Setup

### 1. Set Your API Key

```bash
export ANTHROPIC_API_KEY="your-claude-api-key"
```

Or in Python:
```python
import os
os.environ['ANTHROPIC_API_KEY'] = 'your-key'
```

### 2. Create Your First Project

```python
import socrates_ai

# Initialize with your API key (reads from ANTHROPIC_API_KEY by default)
config = socrates_ai.ConfigBuilder("your-api-key").build()
orchestrator = socrates_ai.create_orchestrator(config)

# Or use quick_start for minimal setup
orchestrator = socrates_ai.quick_start("your-api-key")
```

## Core Concepts

### ConfigBuilder
Configure how Socrates runs:

```python
config = socrates_ai.ConfigBuilder("your-api-key") \
    .with_data_dir("/custom/path") \
    .with_log_level("INFO") \
    .build()
```

### AgentOrchestrator
The main interface for Socrates:

```python
orchestrator = socrates_ai.create_orchestrator(config)

# Process requests to different agents
result = orchestrator.process_request("project_manager", {
    "action": "create_project",
    "project_name": "My Project",
    "owner": "alice"
})
```

### Available Agents

- **project_manager**: Create and manage projects
- **socratic_counselor**: Generate Socratic questions
- **code_generator**: Generate code from specifications
- **knowledge_manager**: Manage knowledge bases
- **user_manager**: Manage users and preferences
- **document_processor**: Process and analyze documents

## Common Tasks

### Create a Project

```python
result = orchestrator.process_request("project_manager", {
    "action": "create_project",
    "project_name": "REST API Design",
    "owner": "alice",
    "description": "Learn API design"
})
```

### Generate a Socratic Question

```python
result = orchestrator.process_request("socratic_counselor", {
    "action": "generate_question",
    "project_id": "proj_123",
    "user_id": "user_alice",
    "topic": "API Design",
    "difficulty": "intermediate"
})
```

### Generate Code

```python
result = orchestrator.process_request("code_generator", {
    "action": "generate_code",
    "project_id": "proj_123",
    "specification": "Create a Flask GET endpoint for users",
    "language": "python"
})
```

### Add Knowledge

```python
result = orchestrator.process_request("knowledge_manager", {
    "action": "add_knowledge",
    "project_id": "proj_123",
    "title": "REST Principles",
    "content": "REST is an architectural style...",
    "tags": ["api", "rest"]
})
```

## Event Handling

Listen to Socrates events:

```python
def on_question_generated(event_type, data):
    print(f"Question: {data['question']}")

orchestrator.event_emitter.on(
    socrates_ai.EventType.QUESTION_GENERATED,
    on_question_generated
)
```

Available events:
- `QUESTION_GENERATED`
- `CODE_GENERATED`
- `KNOWLEDGE_ADDED`
- `PROJECT_CREATED`
- `AGENT_START`
- `AGENT_COMPLETE`
- `AGENT_ERROR`
- `TOKEN_USAGE`

## Data Storage

Socrates automatically creates and manages data in:
- **Linux/Mac**: `~/.socrates/`
- **Windows**: `C:\Users\<username>\.socrates\`

This includes:
- Project database (SQLite)
- Vector database (ChromaDB)
- Knowledge base
- User data

## Example: Complete Workflow

```python
import socrates_ai

# Initialize
orchestrator = socrates_ai.quick_start("your-api-key")

# Create project
project = orchestrator.process_request("project_manager", {
    "action": "create_project",
    "project_name": "My Learning Project",
    "owner": "user_123"
})
project_id = project["project"]["project_id"]

# Add knowledge
orchestrator.process_request("knowledge_manager", {
    "action": "add_knowledge",
    "project_id": project_id,
    "title": "Python Basics",
    "content": "Python is a high-level programming language..."
})

# Generate question
question = orchestrator.process_request("socratic_counselor", {
    "action": "generate_question",
    "project_id": project_id,
    "topic": "Python Functions",
    "difficulty": "beginner"
})
print(question)

# Generate code
code = orchestrator.process_request("code_generator", {
    "action": "generate_code",
    "project_id": project_id,
    "specification": "Write a function that calculates factorial",
    "language": "python"
})
print(code)
```

## Integration Examples

See the `examples/` directory for:
- **complete_workflow.py**: Full end-to-end workflow
- **react_frontend_server.py**: FastAPI web server
- **pycharm_plugin.py**: PyCharm IDE integration
- **vscode_extension.py**: VS Code extension integration

Run examples:
```bash
# Full workflow
python examples/complete_workflow.py

# Web server
python examples/react_frontend_server.py

# PyCharm integration
python examples/pycharm_plugin.py

# VS Code integration
python examples/vscode_extension.py
```

## Troubleshooting

### "ANTHROPIC_API_KEY not set"
```bash
export ANTHROPIC_API_KEY="your-key"
```

### "Cannot create project"
Make sure the `~/.socrates` directory exists and is writable.

### "Model not found"
Ensure you're using a valid Claude model. Default is `claude-sonnet-4-5-20250929`.

## API Reference

### ConfigBuilder

```python
socrates_ai.ConfigBuilder(api_key)
    .with_data_dir(Path)          # Custom data directory
    .with_log_level("DEBUG")      # Logging level
    .with_claude_model("claude-opus-4-1")  # Model selection
    .build()
```

### AgentOrchestrator

```python
orchestrator.process_request(agent_name, params)
orchestrator.event_emitter.on(event_type, callback)
orchestrator.claude_client.test_connection()
```

## Next Steps

1. **Read the documentation**: Check the docs/ directory
2. **Run the examples**: Explore examples/ to see real usage
3. **Build your app**: Use Socrates in your project
4. **Join the community**: Contribute and share feedback

## Support

- **GitHub**: https://github.com/Nireus79/Socrates
- **Issues**: https://github.com/Nireus79/Socrates/issues
- **Discussions**: https://github.com/Nireus79/Socrates/discussions

---

**Socrates AI**: Building intelligent tutoring systems with Claude AI
