# Quick Start Guide

Get up and running with Socrates in 5 minutes.

## Installation

### Option 1: Full Platform (Recommended for Most Users)
```bash
pip install socrates-ai
```

This installs everything: core framework, CLI, API, and all libraries.

### Option 2: Just the Framework
```bash
pip install socratic-core
```

Lightweight installation for developers building on top of Socrates.

### Option 3: Modular Installation
```bash
# Core + RAG only
pip install socratic-core socratic-rag

# Core + Agents only
pip install socratic-core socratic-agents

# Core + API
pip install socratic-core socrates-api

# Core + CLI
pip install socratic-core socrates-cli
```

## Setup

### 1. Set Your API Key
```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

Or create a `.env` file in your project:
```
ANTHROPIC_API_KEY=your-api-key-here
```

### 2. Start the API Server (Optional but Recommended)
```bash
socrates-api
```

The API server runs on `http://localhost:8000` by default.

### 3. Use the CLI
In another terminal, try creating a project:
```bash
socrates project create --name "My Project" --owner "your-name"
```

## Common Tasks

### Create a Project
```bash
socrates project create \
  --name "My Project" \
  --owner "your-name" \
  --description "A sample project"
```

### List Your Projects
```bash
socrates project list
```

### Generate Code
```bash
socrates code generate \
  --project-id proj_xxxxx \
  --prompt "Create a REST API endpoint for user registration"
```

### Use the API Directly
```python
import httpx

# Create a project
response = httpx.post(
    "http://localhost:8000/projects",
    json={
        "name": "My Project",
        "owner": "your-name"
    }
)

project = response.json()
print(f"Created project: {project['id']}")
```

## Next Steps

- **Explore the CLI**: `socrates --help`
- **View API Docs**: http://localhost:8000/docs (when API running)
- **Read Full Documentation**: See [ARCHITECTURE.md](ARCHITECTURE.md)
- **Migrate Existing Code**: See [MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)

## Troubleshooting

### "Cannot connect to API server"
Make sure the API is running:
```bash
socrates-api
```

### "Invalid API key"
Check that your API key is set:
```bash
echo $ANTHROPIC_API_KEY
```

### "Command not found"
Reinstall the package:
```bash
pip install --upgrade socrates-ai
```

## Environment Variables

Common environment variables you might need:

```bash
# API Configuration (required)
export ANTHROPIC_API_KEY=your-api-key

# API Server (optional)
export SOCRATES_API_URL=http://localhost:8000
export SOCRATES_API_PORT=8000

# Data Storage (optional)
export SOCRATES_DATA_DIR=$HOME/.socrates
export SOCRATES_DB_PATH=$HOME/.socrates/socrates.db

# Logging (optional)
export SOCRATES_LOG_LEVEL=INFO
export SOCRATES_LOG_FILE=socrates.log
```

## What's Next?

### For CLI Users
```bash
# View all available commands
socrates --help

# Get help for a specific command
socrates project --help
socrates code --help
```

### For Python Developers
```python
from socratic_core import SocratesConfig, EventEmitter, EventType

# Load configuration
config = SocratesConfig.from_env()

# Create event emitter
emitter = EventEmitter()

# Listen for events
@emitter.on(EventType.PROJECT_CREATED)
def on_project_created(data):
    print(f"Project created: {data}")
```

### For API Integration
```bash
# Start API server
socrates-api

# Check health
curl http://localhost:8000/health

# View interactive documentation
# Open: http://localhost:8000/docs
```

## Additional Resources

- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Complete system architecture
- **[MIGRATION_GUIDE.md](MIGRATION_GUIDE.md)** - Migrating from old versions
- **[TRANSFORMATION_STORY.md](TRANSFORMATION_STORY.md)** - Story of monolith-to-modular transformation
- **[BLOG_POST_MONOLITH_TO_MODULAR.md](BLOG_POST_MONOLITH_TO_MODULAR.md)** - Marketing blog post
- **[MODULAR_VS_MONOLITH_COMPARISON.md](MODULAR_VS_MONOLITH_COMPARISON.md)** - Detailed comparison

## Need Help?

- **Issues**: https://github.com/themsou/Socrates/issues
- **Documentation**: See the [docs/](docs/) directory
- **API Docs**: http://localhost:8000/docs (when API running)
