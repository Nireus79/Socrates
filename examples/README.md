# Socrates AI Integration Examples

This directory contains complete integration examples for using the Socrates AI library in different environments:

1. **PyCharm Plugin** - Direct Python integration
2. **VS Code Extension** - JSON-RPC server integration
3. **React Frontend** - REST API server with WebSocket support

## Overview

Each example demonstrates best practices for:
- Initializing the Socrates library
- Handling configuration and credentials
- Processing requests asynchronously
- Forwarding events to the frontend
- Error handling
- User interaction patterns

## Prerequisites

Install the Socrates library:

```bash
pip install socrates-ai
```

Set your Claude API key:

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

## 1. PyCharm Plugin Integration

**File**: `pycharm_plugin.py`

### Overview

Demonstrates direct integration of Socrates into a PyCharm IDE plugin using the Python plugin API.

### Key Components

- **SocratesBridge**: Main class that manages Socrates orchestrator and event forwarding
- **SocratesToolWindowFactory**: PyCharm tool window implementation
- **GenerateCodeAction**: Example PyCharm action for code generation

### Features

- Direct Python library access
- Event listener registration
- IDE-native UI components
- Real-time feedback in editor

### Usage in Your Plugin

```python
from pycharm_plugin import SocratesBridge

# Initialize
bridge = SocratesBridge(
    api_key="sk-ant-...",
    project_dir="/path/to/pycharm/project"
)

# Register event handlers
bridge.on_question_generated(lambda data: display_question(data))
bridge.on_code_generated(lambda data: insert_code(data))
bridge.on_error(lambda data: show_error(data))

# Use the bridge
result = bridge.ask_question("proj_abc123", topic="FastAPI")
if result['success']:
    print(f"Question: {result['question']}")
```

### Integration Steps

1. Create a PyCharm plugin project structure
2. Add `socrates-ai` to `build.gradle.kts`
3. Create a service class that initializes SocratesBridge
4. Implement tool window or action that uses the bridge
5. Register in `plugin.xml`:

```xml
<extensions defaultExtensionNs="com.intellij">
    <toolWindow id="Socrates" secondary="true" icon="/icons/socrates.svg"
                factoryClass="com.example.socrates.SocratesToolWindowFactory"/>
</extensions>
```

### Event-Driven Architecture

The bridge converts library events to IDE-friendly callbacks:

```
Socrates Library Events → SocratesBridge → IDE Callbacks → UI Updates
PROJECT_CREATED        → on_project_created()       → Update project list
CODE_GENERATED         → on_code_generated()        → Open file
AGENT_ERROR            → on_error()                 → Show notification
```

## 2. VS Code Extension Integration

**File**: `vscode_extension.py`

### Overview

Demonstrates JSON-RPC server integration for VS Code extensions written in TypeScript/JavaScript.

### Key Components

- **SocratesRPCServer**: Main server class implementing JSON-RPC methods
- **JSONRPCHandler**: Protocol handler for stdin/stdout communication
- **Extension TypeScript**: Example VS Code extension code

### Features

- Subprocess-based communication
- JSON-RPC 2.0 protocol
- Stdio-based communication (no network)
- Method-based API
- Error handling with JSON-RPC errors

### Architecture

```
VS Code Extension (TypeScript)
    ↓ child_process.spawn()
    ↓ stdin/stdout communication
Socrates RPC Server (Python)
    ↓ import socrates
Socrates Library
    ↓
Claude API
```

### Usage in Your Extension

```typescript
import * as cp from 'child_process';
import * as rpc from 'vscode-jsonrpc/node';

// Start server
const server = cp.spawn('python', ['-m', 'socrates_vscode_server']);
const connection = rpc.createMessageConnection(
    new rpc.StreamMessageReader(server.stdout),
    new rpc.StreamMessageWriter(server.stdin)
);
connection.listen();

// Call RPC methods
const result = await connection.sendRequest('initialize', {
    api_key: 'sk-ant-...',
    workspace_dir: vscode.workspace.rootPath
});

const question = await connection.sendRequest('askQuestion', {
    project_id: 'proj_abc123',
    topic: 'REST API design'
});
```

### Extension Example

The file includes a complete TypeScript extension example (VSCODE_EXTENSION_EXAMPLE constant) showing:
- Command registration
- RPC request/response handling
- Integration with VS Code APIs
- Code insertion into editor

### RPC Methods Available

- `initialize(api_key, workspace_dir)` - Initialize Socrates
- `createProject(name, owner, description)` - Create project
- `listProjects(owner)` - List projects
- `askQuestion(project_id, topic, difficulty)` - Get question
- `evaluateResponse(project_id, question_id, response)` - Evaluate response
- `generateCode(project_id, specification, language)` - Generate code
- `getInfo()` - Get server information

## 3. React Frontend Server

**File**: `react_frontend_server.py`

### Overview

Complete FastAPI server for a React frontend with REST API and WebSocket support.

### Key Components

- **SocratesAppState**: Application state management and event broadcasting
- **FastAPI Routes**: REST endpoints for all functionality
- **WebSocket Endpoint**: Real-time event streaming
- **SSE Endpoint**: Alternative event streaming (Server-Sent Events)

### Features

- REST API with OpenAPI documentation
- WebSocket for bidirectional communication
- Server-Sent Events (SSE) for server-to-client events
- CORS support for cross-origin requests
- Event history and broadcasting
- Comprehensive error handling

### Architecture

```
React Frontend (Browser)
    ↓ HTTP/WebSocket
FastAPI Server
    ↓ import socrates
Socrates Library
    ↓
Claude API

Event Flow:
Socrates Events → Event Listeners → WebSocket Broadcast → React State Update
```

### Installation & Running

```bash
# Install dependencies
pip install fastapi uvicorn socrates-ai python-dotenv

# Set environment variables
export ANTHROPIC_API_KEY="sk-ant-..."
export HOST="0.0.0.0"
export PORT="8000"

# Run server
python react_frontend_server.py

# Access API docs
# http://localhost:8000/docs
```

### REST API Endpoints

```
GET    /health                          - Health check
GET    /info                             - Server information
POST   /api/projects                     - Create project
GET    /api/projects                     - List projects
POST   /api/projects/{id}/question       - Ask question
POST   /api/projects/{id}/response       - Submit response
POST   /api/projects/{id}/code/generate  - Generate code
GET    /api/events/history               - Get event history
WS     /ws/events                        - WebSocket events
GET    /api/events/stream                - SSE events
POST   /api/test-connection              - Test API connection
```

### React Component Example

```typescript
import React, { useEffect, useState } from 'react';

function ProjectQuestion({ projectId }) {
    const [question, setQuestion] = useState(null);
    const [loading, setLoading] = useState(false);
    const [response, setResponse] = useState('');

    const askQuestion = async () => {
        setLoading(true);
        const res = await fetch(`/api/projects/${projectId}/question`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                topic: 'REST API design',
                difficulty_level: 'intermediate'
            })
        });
        const data = await res.json();
        setQuestion(data);
        setLoading(false);
    };

    const submitResponse = async () => {
        const res = await fetch(`/api/projects/${projectId}/response`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question_id: question.question_id,
                user_response: response
            })
        });
        const feedback = await res.json();
        console.log('Feedback:', feedback);
        // Show feedback to user...
    };

    return (
        <div>
            <button onClick={askQuestion} disabled={loading}>
                {loading ? 'Loading...' : 'Ask Question'}
            </button>
            {question && (
                <div>
                    <h3>{question.question}</h3>
                    <textarea
                        value={response}
                        onChange={(e) => setResponse(e.target.value)}
                        placeholder="Your response..."
                    />
                    <button onClick={submitResponse}>Submit Response</button>
                </div>
            )}
        </div>
    );
}

export default ProjectQuestion;
```

### WebSocket Event Integration

```typescript
useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/events');

    ws.onmessage = (event) => {
        const eventRecord = JSON.parse(event.data);
        console.log(`Event: ${eventRecord.event_type}`, eventRecord.data);

        // Update UI based on event type
        switch (eventRecord.event_type) {
            case 'PROJECT_CREATED':
                // Refresh project list
                break;
            case 'CODE_GENERATED':
                // Show generated code
                break;
            case 'TOKEN_USAGE':
                // Update token usage display
                break;
        }
    };

    return () => ws.close();
}, []);
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY react_frontend_server.py .

ENV HOST=0.0.0.0
ENV PORT=8000

CMD ["python", "react_frontend_server.py"]
```

```bash
docker build -t socrates-server .
docker run -e ANTHROPIC_API_KEY="sk-ant-..." -p 8000:8000 socrates-server
```

## Comparison

| Aspect | PyCharm | VS Code | React |
|--------|---------|---------|-------|
| **Integration Type** | Direct import | RPC server | REST/WebSocket |
| **Communication** | Function calls | stdin/stdout | HTTP/WS |
| **Setup Complexity** | Medium | High | Low |
| **Real-time Events** | Callbacks | RPC notifications | WebSocket/SSE |
| **Use Case** | IDE plugin | Extension | Web frontend |
| **Concurrency** | Callback-based | RPC async | FastAPI async |

## Common Patterns

### 1. Error Handling

All examples follow a consistent error handling pattern:

```python
result = bridge.ask_question(project_id)
if result['success']:
    # Process result
else:
    # Handle error
    print(f"Error: {result['error']}")
```

### 2. Configuration Management

```python
config_builder = socrates.ConfigBuilder(api_key)
config = config_builder \
    .with_data_dir(Path(data_dir)) \
    .with_log_level("INFO") \
    .build()

orchestrator = socrates.create_orchestrator(config)
```

### 3. Event Forwarding

All examples forward Socrates events to their respective frontends:

```
Library Events (EventType) → Bridge/Server → Frontend Events → UI
```

### 4. Async Operations

All examples support asynchronous operations:

- **PyCharm**: Event callbacks (implicit async)
- **VS Code**: JSON-RPC async methods
- **React**: FastAPI async endpoints

## Advanced Topics

### Custom Event Handlers

Each example can be extended with custom event handlers:

```python
def on_token_usage(event_type, data):
    # Send to monitoring system
    send_metrics(data)

orchestrator.event_emitter.on(
    socrates.EventType.TOKEN_USAGE,
    on_token_usage
)
```

### Concurrent Requests

React server automatically handles concurrent requests with FastAPI:

```python
# Multiple users can ask questions simultaneously
await asyncio.gather(
    ask_question(project_1),
    ask_question(project_2),
    ask_question(project_3)
)
```

### Session Management

Extend examples with session/user management:

```python
class UserSession:
    def __init__(self, user_id: str, api_key: str):
        self.user_id = user_id
        self.bridge = SocratesBridge(api_key)
        self.projects = {}
```

## Troubleshooting

### API Key Issues
- Verify `ANTHROPIC_API_KEY` is set
- Check API key is valid
- Ensure account has sufficient credits

### Connection Issues
- Check Claude API is accessible
- Verify firewall allows HTTPS
- Test with `test_connection()` endpoint

### Event Streaming Issues
- WebSocket: Check browser WebSocket support
- SSE: Check proxy supports streaming responses
- Verify event history is not empty

## Further Reading

- [Socrates Library Documentation](../README.md)
- [REST API Documentation](../socrates-api/README.md)
- [CLI Documentation](../socrates-cli/README.md)
- [PyCharm Plugin Development](https://plugins.jetbrains.com/docs/intellij/welcome.html)
- [VS Code Extension Development](https://code.visualstudio.com/api)
- [FastAPI Documentation](https://fastapi.tiangolo.com/)

## Support

For questions or issues:
- GitHub Issues: https://github.com/Nireus79/Socrates/issues
- Documentation: https://socrates-ai.readthedocs.io
