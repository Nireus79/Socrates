# SocratesAgentClient - Library API Documentation

The `SocratesAgentClient` provides a clean Python interface for accessing Socrates agents without requiring knowledge of internal Socrates architecture or dependencies.

## Installation

### Minimal Installation (Client Only)
```bash
pip install socrates-agents
```

### Full Installation (with API server)
```bash
pip install socrates-agents[full]
```

### API Server Installation
```bash
pip install socrates-agents[api]
```

## Quick Start

### Asynchronous Usage

```python
import asyncio
from socratic_system.api.client import SocratesAgentClient

async def main():
    # Initialize client (defaults to localhost:8000)
    client = SocratesAgentClient(
        api_url="http://localhost:8000",
        auth_token="your-api-key"
    )

    # Create a project
    project = await client.project_manager({
        "action": "create",
        "name": "My Awesome Project",
        "description": "Building an e-commerce platform",
        "user_id": "user_123"
    })
    print(f"Created project: {project['id']}")

    # Get a Socratic question
    question = await client.socratic_counselor({
        "action": "get_question",
        "project_id": project["id"],
        "phase": "discovery",
        "user_id": "user_123"
    })
    print(f"Question: {question['content']}")

    # Process user response
    response = await client.socratic_counselor({
        "action": "process_response",
        "project_id": project["id"],
        "response": "We're targeting small businesses initially",
        "user_id": "user_123"
    })

    # Get analysis results (polling)
    analysis = await client.socratic_counselor({
        "action": "get_analysis",
        "project_id": project["id"],
        "user_id": "user_123"
    })
    print(f"Quality Score: {analysis.get('maturity', 'pending')}")

asyncio.run(main())
```

### Synchronous Usage

```python
from socratic_system.api.client import SocratesAgentClientSync

# Initialize client
client = SocratesAgentClientSync(
    api_url="http://localhost:8000",
    auth_token="your-api-key"
)

# All methods are synchronous
project = client.project_manager({
    "action": "create",
    "name": "My Project",
    "user_id": "user_123"
})

question = client.socratic_counselor({
    "action": "get_question",
    "project_id": project["id"],
    "user_id": "user_123"
})
```

## API Reference

### SocratesAgentClient (Async)

```python
class SocratesAgentClient:
    """Asynchronous client for Socrates agents."""

    def __init__(
        self,
        api_url: str = "http://localhost:8000",
        auth_token: Optional[str] = None,
        timeout: float = 30.0
    ):
        """
        Initialize the client.

        Args:
            api_url: API endpoint URL
            auth_token: Authentication token (optional)
            timeout: Request timeout in seconds
        """
```

#### Methods

All methods are async and return dictionaries with agent responses.

##### Project Management

```python
# Create a new project
await client.project_manager({
    "action": "create",
    "name": str,              # Required: Project name
    "description": str,       # Optional: Project description
    "user_id": str,           # Required: User ID
    "project_type": str,      # Optional: Type (default: "software")
})

# Load an existing project
await client.project_manager({
    "action": "load",
    "project_id": str,        # Required: Project ID
    "user_id": str            # Required: User ID
})

# Save project changes
await client.project_manager({
    "action": "save",
    "project": dict,          # Required: Project object
    "user_id": str            # Required: User ID
})

# List all projects for a user
await client.project_manager({
    "action": "list",
    "user_id": str            # Required: User ID
})

# Archive a project
await client.project_manager({
    "action": "archive",
    "project_id": str,        # Required: Project ID
    "user_id": str            # Required: User ID
})

# Restore an archived project
await client.project_manager({
    "action": "restore",
    "project_id": str,        # Required: Project ID
    "user_id": str            # Required: User ID
})
```

##### Socratic Questioning

```python
# Get a question for the current phase
await client.socratic_counselor({
    "action": "get_question",
    "project_id": str,        # Required: Project ID
    "phase": str,             # Optional: Current phase
    "user_id": str            # Required: User ID
})

# Process a user response
await client.socratic_counselor({
    "action": "process_response",
    "project_id": str,        # Required: Project ID
    "response": str,          # Required: User's answer
    "user_id": str            # Required: User ID
})

# Get analysis results
await client.socratic_counselor({
    "action": "get_analysis",
    "project_id": str,        # Required: Project ID
    "user_id": str            # Required: User ID
})

# Advance to next phase
await client.socratic_counselor({
    "action": "advance_phase",
    "project_id": str,        # Required: Project ID
    "user_id": str            # Required: User ID
})
```

##### Code Generation

```python
# Generate code/artifacts
await client.code_generator({
    "action": "generate",
    "project_id": str,        # Required: Project ID
    "language": str,          # Optional: Target language
    "user_id": str            # Required: User ID
})

# Generate documentation
await client.code_generator({
    "action": "generate_documentation",
    "project_id": str,        # Required: Project ID
    "user_id": str            # Required: User ID
})
```

##### Code Validation

```python
# Validate code
await client.code_validation({
    "action": "validate",
    "project_id": str,        # Required: Project ID
    "code": str,              # Required: Code to validate
    "language": str,          # Required: Language
    "user_id": str            # Required: User ID
})

# Run tests
await client.code_validation({
    "action": "run_tests",
    "project_id": str,        # Required: Project ID
    "user_id": str            # Required: User ID
})
```

##### Quality Analysis

```python
# Get quality metrics
await client.quality_controller({
    "action": "get_phase_maturity",
    "project_id": str,        # Required: Project ID
    "user_id": str            # Required: User ID
})

# Calculate maturity
await client.quality_controller({
    "action": "calculate_maturity",
    "project_id": str,        # Required: Project ID
    "user_id": str            # Required: User ID
})
```

##### Conflict Detection

```python
# Detect conflicts in project
await client.conflict_detector({
    "action": "detect_conflicts",
    "project_id": str,        # Required: Project ID
    "user_id": str            # Required: User ID
})

# Resolve a conflict
await client.conflict_detector({
    "action": "resolve_conflict",
    "project_id": str,        # Required: Project ID
    "conflict_id": str,       # Required: Conflict ID
    "resolution": str,        # Required: Resolution approach
    "user_id": str            # Required: User ID
})
```

### SocratesAgentClientSync (Synchronous)

```python
class SocratesAgentClientSync:
    """Synchronous wrapper for SocratesAgentClient."""

    def __init__(
        self,
        api_url: str = "http://localhost:8000",
        auth_token: Optional[str] = None,
        timeout: float = 30.0
    ):
        """Initialize the synchronous client."""
```

All methods are identical to `SocratesAgentClient` but are synchronous (no `await`).

## Response Format

All agent responses follow a standard format:

```python
{
    "status": "success" | "error",      # Response status
    "data": {...},                      # Response data (varies by agent)
    "message": str,                     # Optional: Status message
    "timestamp": str,                   # ISO 8601 timestamp
    "request_id": str,                  # Request ID for tracking
}
```

## Error Handling

```python
from socratic_system.api.client import SocratesAgentClient
import httpx

async def safe_call():
    client = SocratesAgentClient()
    try:
        result = await client.project_manager({
            "action": "create",
            "name": "My Project",
            "user_id": "user_123"
        })
        if result.get("status") == "success":
            return result["data"]
        else:
            print(f"Agent error: {result.get('message')}")
    except httpx.HTTPError as e:
        print(f"HTTP error: {e}")
    except httpx.TimeoutException:
        print("Request timed out")
```

## Configuration

### Environment Variables

```bash
# API endpoint
export SOCRATES_API_URL="http://localhost:8000"

# Authentication token
export SOCRATES_AUTH_TOKEN="your-api-key"

# Request timeout (seconds)
export SOCRATES_TIMEOUT="30"
```

### Client Configuration

```python
from socratic_system.api.client import SocratesAgentClient

client = SocratesAgentClient(
    api_url="http://api.socrates.internal:8000",
    auth_token="sk-1234567890abcdef",
    timeout=60.0  # Custom timeout
)

# Use context manager for automatic cleanup
async with client:
    result = await client.project_manager({...})
```

## Common Workflows

### Complete Project Development Workflow

```python
import asyncio

async def develop_project():
    client = SocratesAgentClient("http://localhost:8000")

    user_id = "user_demo"

    # 1. Create project
    project = await client.project_manager({
        "action": "create",
        "name": "Task Management App",
        "description": "A simple web app for managing tasks",
        "user_id": user_id
    })
    project_id = project["id"]
    print(f"Created project: {project_id}")

    # 2. Discovery phase questions
    for i in range(3):
        q = await client.socratic_counselor({
            "action": "get_question",
            "project_id": project_id,
            "phase": "discovery",
            "user_id": user_id
        })
        print(f"Q{i+1}: {q['content']}")

        # Simulate user response
        response = await client.socratic_counselor({
            "action": "process_response",
            "project_id": project_id,
            "response": "A sophisticated response to the question",
            "user_id": user_id
        })
        print(f"Response processed: {response.get('status')}")

        # Check analysis
        analysis = await client.socratic_counselor({
            "action": "get_analysis",
            "project_id": project_id,
            "user_id": user_id
        })
        print(f"Maturity: {analysis.get('maturity', 'pending')}")

    # 3. Advance phases
    await client.socratic_counselor({
        "action": "advance_phase",
        "project_id": project_id,
        "user_id": user_id
    })

    # 4. Generate code
    code_result = await client.code_generator({
        "action": "generate",
        "project_id": project_id,
        "language": "python",
        "user_id": user_id
    })
    print(f"Code generated: {len(code_result.get('files', []))} files")

    # 5. Validate code
    validation = await client.code_validation({
        "action": "run_tests",
        "project_id": project_id,
        "user_id": user_id
    })
    print(f"Tests: {validation.get('passed', 0)}/{validation.get('total', 0)}")

    # 6. Get final quality metrics
    quality = await client.quality_controller({
        "action": "get_phase_maturity",
        "project_id": project_id,
        "user_id": user_id
    })
    print(f"Final maturity: {quality.get('overall_maturity')}%")

asyncio.run(develop_project())
```

## WebSocket Support (Optional)

For real-time updates, use WebSocket subscriptions:

```python
import asyncio
import websockets
import json

async def subscribe_to_updates(project_id: str):
    """Subscribe to real-time analysis updates via WebSocket."""
    uri = "ws://localhost:8000/ws/analysis/" + project_id

    async with websockets.connect(uri) as websocket:
        # Receive subscription confirmation
        confirm = json.loads(await websocket.recv())
        print(f"Subscribed: {confirm['type']}")

        # Receive updates as they complete
        while True:
            message = json.loads(await websocket.recv())
            if message["type"] == "quality.completed":
                print(f"Quality analysis completed: {message['data']}")
            elif message["type"] == "conflicts.completed":
                print(f"Conflict detection completed: {message['data']}")
            elif message["type"] == "insights.completed":
                print(f"Insights analysis completed: {message['data']}")

asyncio.run(subscribe_to_updates("project_123"))
```

## Performance Considerations

### Request Timeout

Long-running operations are handled asynchronously. Use polling or WebSockets for results:

```python
# Bad: Waiting for analysis synchronously
response = await client.socratic_counselor({
    "action": "process_response",
    "project_id": project_id,
    "response": "...",
    "user_id": user_id
})
# This returns immediately with "_background_processing": True

# Good: Poll for results
import asyncio
for attempt in range(10):
    analysis = await client.socratic_counselor({
        "action": "get_analysis",
        "project_id": project_id,
        "user_id": user_id
    })
    if analysis.get("ready"):
        break
    await asyncio.sleep(1)  # Wait before retrying
```

### Batch Operations

Process multiple projects concurrently:

```python
async def process_multiple_projects(user_id: str, project_names: list):
    client = SocratesAgentClient()

    # Create all projects concurrently
    tasks = [
        client.project_manager({
            "action": "create",
            "name": name,
            "user_id": user_id
        })
        for name in project_names
    ]
    projects = await asyncio.gather(*tasks)
    return projects
```

## Support & Troubleshooting

### Common Issues

1. **Connection refused**: Ensure Socrates API server is running
2. **Authentication failed**: Check your API token
3. **Timeout**: Increase timeout parameter or check server load
4. **Invalid request**: Validate required parameters

### Debug Mode

```python
import logging

logging.basicConfig(level=logging.DEBUG)
client = SocratesAgentClient()
# Now all HTTP requests will be logged
```

## License

Socrates is released under the MIT License. See LICENSE file for details.

## Further Reading

- [Architecture Overview](../ARCHITECTURE_ANALYSIS_LIBRARY_EXPORT.md)
- [Agent Bus Documentation](./AGENT_BUS.md)
- [REST API Endpoints](./REST_ENDPOINTS.md)
