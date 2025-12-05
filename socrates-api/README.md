# Socrates API

REST API server for the Socrates AI tutoring system. Built with FastAPI, this server provides endpoints for project management, Socratic questioning, code generation, and more.

## Installation

```bash
pip install socrates-api
```

## Quick Start

### 1. Set Environment Variables

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
export SOCRATES_DATA_DIR="~/.socrates"  # Optional
export SOCRATES_API_HOST="0.0.0.0"      # Optional, default: 127.0.0.1
export SOCRATES_API_PORT="8000"         # Optional, default: 8000
```

### 2. Run the Server

```bash
socrates-api
```

Or use Python directly:

```bash
python -m socrates_api.main
```

### 3. Access the API

- **Swagger Documentation**: http://localhost:8000/docs
- **ReDoc Documentation**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

## API Endpoints

### System Management

- `GET /health` - Health check
- `POST /initialize` - Initialize API with configuration
- `GET /info` - Get system information

### Projects

- `POST /projects` - Create a new project
- `GET /projects` - List projects (optionally filtered by owner)

### Socratic Questions

- `POST /projects/{project_id}/question` - Get a Socratic question
- `POST /projects/{project_id}/response` - Process user response

### Code Generation

- `POST /code/generate` - Generate code for a project

## Usage Examples

### Initialize the API

```bash
curl -X POST http://localhost:8000/initialize \
  -H "Content-Type: application/json" \
  -d '{"api_key": "sk-ant-..."}'
```

### Create a Project

```bash
curl -X POST http://localhost:8000/projects \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Python API Development",
    "owner": "alice",
    "description": "Building REST APIs with FastAPI"
  }'
```

### List Projects

```bash
curl http://localhost:8000/projects
```

### Ask a Socratic Question

```bash
curl -X POST http://localhost:8000/projects/proj_abc123/question \
  -H "Content-Type: application/json" \
  -d '{
    "topic": "REST API design",
    "difficulty_level": "intermediate"
  }'
```

### Process a Response

```bash
curl -X POST http://localhost:8000/projects/proj_abc123/response \
  -H "Content-Type: application/json" \
  -d '{
    "question_id": "q_xyz789",
    "user_response": "REST APIs should follow resource-oriented design principles...",
    "project_id": "proj_abc123"
  }'
```

### Generate Code

```bash
curl -X POST http://localhost:8000/code/generate \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "proj_abc123",
    "specification": "Create a FastAPI endpoint for user registration",
    "language": "python"
  }'
```

## Python Client Example

```python
import requests
import json

BASE_URL = "http://localhost:8000"

# Initialize
resp = requests.post(f"{BASE_URL}/initialize", json={
    "api_key": "sk-ant-..."
})
print(resp.json())

# Create project
resp = requests.post(f"{BASE_URL}/projects", json={
    "name": "My Project",
    "owner": "alice",
    "description": "Learning FastAPI"
})
project = resp.json()
project_id = project["project_id"]

# Get a question
resp = requests.post(f"{BASE_URL}/projects/{project_id}/question", json={
    "topic": "FastAPI basics",
    "difficulty_level": "beginner"
})
question = resp.json()
print(f"Question: {question['question']}")

# Process response
resp = requests.post(f"{BASE_URL}/projects/{project_id}/response", json={
    "question_id": question["question_id"],
    "user_response": "FastAPI is a modern Python web framework...",
    "project_id": project_id
})
feedback = resp.json()
print(f"Feedback: {feedback['feedback']}")
```

## Async Integration Example

The API is built with FastAPI and uses asyncio internally. For high-throughput scenarios:

```python
import asyncio
import httpx

async def main():
    async with httpx.AsyncClient() as client:
        # Initialize
        resp = await client.post("http://localhost:8000/initialize", json={
            "api_key": "sk-ant-..."
        })
        print(resp.json())

        # Create multiple projects concurrently
        tasks = [
            client.post("http://localhost:8000/projects", json={
                "name": f"Project {i}",
                "owner": "alice"
            })
            for i in range(5)
        ]

        results = await asyncio.gather(*tasks)
        for r in results:
            print(r.json())

asyncio.run(main())
```

## Event Integration

The API automatically registers event listeners with the Socrates library. Events are logged and can be monitored via the logging system:

```python
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("socrates_api.main")

# API will log events like:
# [Event] PROJECT_CREATED: {'project_id': 'proj_abc123', ...}
# [Event] CODE_GENERATED: {'lines': 150, ...}
# [Event] AGENT_ERROR: {'agent_name': 'code_generator', ...}
```

## Configuration

The API respects these environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | None | Claude API key (required) |
| `SOCRATES_DATA_DIR` | `~/.socrates` | Directory for storing data |
| `SOCRATES_API_HOST` | `127.0.0.1` | Server host |
| `SOCRATES_API_PORT` | `8000` | Server port |
| `SOCRATES_API_RELOAD` | `false` | Enable auto-reload in development |

## Error Handling

The API returns structured error responses:

```json
{
  "error": "ProjectNotFoundError",
  "message": "Project 'proj_abc123' not found",
  "error_code": "PROJECT_NOT_FOUND",
  "details": {"project_id": "proj_abc123"}
}
```

All Socrates library errors are caught and returned with appropriate HTTP status codes.

## Deployment

### Using Gunicorn (Production)

```bash
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker socrates_api.main:app
```

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app

RUN pip install socrates-api

ENV SOCRATES_API_HOST=0.0.0.0

CMD ["socrates-api"]
```

```bash
docker build -t socrates-api .
docker run -e ANTHROPIC_API_KEY="sk-ant-..." -p 8000:8000 socrates-api
```

### Using Docker Compose

```yaml
version: '3.8'

services:
  socrates-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      ANTHROPIC_API_KEY: ${ANTHROPIC_API_KEY}
      SOCRATES_DATA_DIR: /data
    volumes:
      - socrates_data:/data

volumes:
  socrates_data:
```

## Development

### Setup

```bash
git clone https://github.com/Nireus79/Socrates
cd socrates-api
pip install -e ".[dev]"
```

### Run Tests

```bash
pytest tests/ -v --cov=socrates_api
```

### Run in Development Mode

```bash
export SOCRATES_API_RELOAD=true
socrates-api
```

## API Response Examples

### Successful Project Creation

```json
{
  "project_id": "proj_abc123",
  "name": "Python API Development",
  "owner": "alice",
  "description": "Building REST APIs with FastAPI",
  "phase": "active",
  "created_at": "2025-12-04T10:00:00Z",
  "updated_at": "2025-12-04T10:30:00Z",
  "is_archived": false
}
```

### Successful Question Generation

```json
{
  "question_id": "q_xyz789",
  "question": "What are the main principles of RESTful API design?",
  "context": "You are designing an API for a tutoring system",
  "hints": [
    "Think about resource-oriented design",
    "Consider HTTP methods and status codes"
  ]
}
```

### Successful Code Generation

```json
{
  "code": "@app.post('/api/users/register')\nasync def register_user(user: User):\n    # Implementation here",
  "explanation": "This endpoint handles user registration using FastAPI...",
  "language": "python",
  "token_usage": {
    "input_tokens": 150,
    "output_tokens": 200,
    "total_tokens": 350
  }
}
```

## Architecture

The API is built on three layers:

1. **FastAPI Application** (`main.py`) - HTTP request handling, routing, and middleware
2. **Pydantic Models** (`models.py`) - Request/response validation and serialization
3. **Socrates Library** - Business logic via `socrates` package

Event flow:
```
HTTP Request → FastAPI Route → Socrates Library → Event Emission → HTTP Response
                                      ↓
                              Event Listeners (Logging)
```

## Monitoring

The API emits events for all significant operations. Monitor them via logging:

```python
import logging
logging.basicConfig(level=logging.INFO)

# All events will be logged like:
# [Event] PROJECT_CREATED: {...}
# [Event] AGENT_COMPLETE: {...}
# [Event] TOKEN_USAGE: {...}
```

Or set up custom event listeners by extending the API:

```python
def setup_monitoring(orchestrator):
    def on_token_usage(event_type, data):
        # Send to monitoring system
        send_metrics(data)

    orchestrator.event_emitter.on(socrates.EventType.TOKEN_USAGE, on_token_usage)
```

## Support

For issues, feature requests, or contributions, visit:
- GitHub: https://github.com/Nireus79/Socrates
- Issues: https://github.com/Nireus79/Socrates/issues
- Documentation: https://socrates-ai.readthedocs.io

## License

MIT
