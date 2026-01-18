# Integrations Guide

Complete guide to integrating Socrates AI with external systems and services.

---

## Table of Contents

- [Integration Overview](#integration-overview)
- [Supported Integrations](#supported-integrations)
- [API-Based Integrations](#api-based-integrations)
- [Event-Based Integrations](#event-based-integrations)
- [Custom Integration Template](#custom-integration-template)
- [Webhook Setup](#webhook-setup)
- [Troubleshooting](#troubleshooting)

---

## Integration Overview

Socrates AI can integrate with external systems in three ways:

1. **REST API** - Make HTTP requests to Socrates endpoints
2. **Events** - Listen to Socrates events and react
3. **CLI/Script** - Call Socrates commands from scripts
4. **Python SDK** - Direct programmatic access

---

## Supported Integrations

### Built-In Integrations

| Integration | Type | Purpose | Status |
|---|---|---|---|
| **GitHub** | Webhook | Trigger project creation from repos | ✓ Planned v1.4 |
| **Slack** | API | Post dialogue summaries to Slack | ✓ Planned v1.4 |
| **Jira** | API | Create issues from generated code | ✓ Planned v1.4 |
| **Google Drive** | API | Auto-upload generated code | ✓ Planned v1.5 |
| **VS Code** | Extension | Integrated IDE extension | ✓ Planned v1.5 |

### Community Integrations

These are maintained by the community. Submit yours!

- [Socrates Slack Bot](https://github.com/community/socrates-slack-bot)
- [Socrates GitHub Action](https://github.com/community/socrates-action)

---

## API-Based Integrations

### Authentication

All API calls require authentication:

**Bearer Token**:
```python
headers = {
    "Authorization": "Bearer YOUR_JWT_TOKEN"
}
```

**Get Token**:
```bash
# Via CLI login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "secret"}'

# Returns: {"access_token": "eyJ...", "token_type": "bearer"}
```

### Common API Endpoints

**Projects**:
```bash
# List projects
GET /projects

# Create project
POST /projects
{
  "name": "My Project",
  "description": "Project description"
}

# Get project
GET /projects/{project_id}

# Delete project
DELETE /projects/{project_id}
```

**Code Generation**:
```bash
# Generate code
POST /projects/{project_id}/code
{
  "language": "python"
}

# Get generated code
GET /projects/{project_id}/code
```

**Complete API**: See [API_REFERENCE.md](API_REFERENCE.md)

### Integration Examples

#### Example 1: Auto-Create Projects from GitHub

```python
from github import Github
from socratic_system.orchestration import AgentOrchestrator

orch = AgentOrchestrator("sk-ant-...")

# GitHub client
g = Github("github-token")

# List repos
for repo in g.get_user().get_repos():
    # Create project in Socrates
    result = orch.process_request('project_manager', {
        'action': 'create_project',
        'project_name': repo.name,
        'owner': 'system'
    })

    print(f"Created: {repo.name}")
```

#### Example 2: Generate Code for Spec in Document

```python
from pathlib import Path
from socratic_system.orchestration import AgentOrchestrator

orch = AgentOrchestrator("sk-ant-...")

# Create project from spec document
spec = Path("project_spec.md").read_text()

result = orch.process_request('project_manager', {
    'action': 'create_project',
    'project_name': 'Generated from Spec',
    'owner': 'system'
})

project_id = result['project']['id']

# Add to knowledge base
orch.process_request('knowledge_manager', {
    'action': 'add_knowledge',
    'project_id': project_id,
    'content': spec
})

# Generate code
code_result = orch.process_request('code_generator', {
    'action': 'generate_script',
    'project_id': project_id
})

print(code_result['code'])
```

#### Example 3: Batch Process Multiple Projects

```python
import json
from socratic_system.orchestration import AgentOrchestrator

orch = AgentOrchestrator("sk-ant-...")

# Read specifications
specs = json.load(open('specifications.json'))

# Process each
for spec in specs:
    result = orch.process_request('project_manager', {
        'action': 'create_project',
        'project_name': spec['name'],
        'owner': 'batch_process'
    })

    project_id = result['project']['id']

    # Generate code
    code = orch.process_request('code_generator', {
        'action': 'generate_script',
        'project_id': project_id
    })

    # Export result
    with open(f"{spec['name']}.py", "w") as f:
        f.write(code['code'])

    print(f"✓ {spec['name']}")
```

---

## Event-Based Integrations

### Listening to Events

**Subscribe to events**:
```python
from socratic_system.orchestration import AgentOrchestrator

orch = AgentOrchestrator("sk-ant-...")

def on_project_created(event):
    print(f"New project: {event['data']['project_name']}")
    # Send notification, create ticket, etc.

def on_code_generated(event):
    print(f"Code ready for {event['data']['project_id']}")
    # Upload to repository, notify team, etc.

# Subscribe
orch.on('project_created', on_project_created)
orch.on('code_generated', on_code_generated)

# Keep running to listen to events
import asyncio
asyncio.run(orch.listen())
```

### Event Types

See [ADR-003](adr/ADR-003-EVENT_DRIVEN_COMMUNICATION.md) for complete list:

**Project Events**:
- `project_created`
- `project_deleted`
- `project_archived`
- `phase_changed`

**Dialogue Events**:
- `question_generated`
- `answer_provided`
- `dialogue_completed`

**Code Events**:
- `code_generated`
- `generation_failed`

### WebSocket Events

**Real-time event stream**:
```javascript
const ws = new WebSocket("ws://localhost:8000/events");

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    console.log("Event:", data.type, data.data);
};

ws.onerror = (error) => {
    console.error("WebSocket error:", error);
};
```

---

## Custom Integration Template

### Create a Custom Integration

**Step 1: Create integration file**:
```python
# integrations/my_integration.py
from socratic_system.orchestration import AgentOrchestrator

class MyIntegration:
    def __init__(self, api_key, external_config):
        self.orch = AgentOrchestrator(api_key)
        self.config = external_config

    def on_project_created(self, event):
        """Handle project creation event"""
        project = event['data']
        # Do something with project
        print(f"Project created: {project['name']}")

    def sync_to_external_system(self, project_id):
        """Sync project to external system"""
        result = self.orch.process_request('project_manager', {
            'action': 'get_project',
            'project_id': project_id
        })

        project = result['project']
        # Upload/sync to external system
        self.external_api.create_project(project['name'])

    def listen(self):
        """Start listening to events"""
        self.orch.on('project_created', self.on_project_created)
```

**Step 2: Use the integration**:
```python
from integrations.my_integration import MyIntegration

integration = MyIntegration(
    api_key="sk-ant-...",
    external_config={"api_key": "external-key"}
)

# Sync project
integration.sync_to_external_system("proj_123")

# Or listen to events
integration.listen()
```

---

## Webhook Setup

### Creating a Webhook

**Register webhook**:
```python
result = orch.process_request('system_monitor', {
    'action': 'register_webhook',
    'url': 'https://your-server.com/socrates-webhook',
    'events': ['project_created', 'code_generated'],
    'secret': 'your-secret-key'  # For validating requests
})
```

### Webhook Payload

**Example**:
```json
{
    "id": "evt_123",
    "event_type": "project_created",
    "timestamp": "2026-01-18T10:30:00Z",
    "data": {
        "project_id": "proj_123",
        "project_name": "My Project",
        "owner": "alice"
    },
    "signature": "sha256=..."
}
```

### Validating Webhook Signature

```python
import hmac
import hashlib

def verify_webhook(payload, signature, secret):
    expected = "sha256=" + hmac.new(
        secret.encode(),
        payload.encode(),
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(signature, expected)

# In webhook handler
@app.post("/socrates-webhook")
async def handle_webhook(request: Request):
    signature = request.headers.get("X-Socrates-Signature")
    body = await request.body()

    if not verify_webhook(body, signature, "your-secret"):
        return {"error": "Invalid signature"}, 401

    event = await request.json()
    # Process event
```

---

## Integration Examples

### Slack Integration

**Send dialogue summary to Slack**:

```python
from slack_sdk import WebClient

slack = WebClient(token="xoxb-...")

def on_dialogue_completed(event):
    project = event['data']
    message = f"""
    Dialogue Complete: {project['name']}
    Phase: {project['phase']}
    Maturity: {project.get('maturity', 'N/A')}
    """
    slack.chat_postMessage(
        channel="#projects",
        text=message
    )

orch.on('dialogue_completed', on_dialogue_completed)
```

### Jira Integration

**Create issue from generated code**:

```python
from jira import JIRA

jira = JIRA(server="https://jira.yourcompany.com",
    auth=("user", "token"))

def on_code_generated(event):
    project = event['data']
    code = event['data']['code']

    # Create issue
    issue = jira.create_issue(
        project="DEV",
        issuetype="Task",
        summary=f"Implement: {project['name']}",
        description=f"Generated code:\n{code}"
    )

    print(f"Created: {issue.key}")

orch.on('code_generated', on_code_generated)
```

### Git Auto-Commit

**Auto-commit generated code to Git**:

```python
from git import Repo
import os

def on_code_generated(event):
    project = event['data']
    code = event['data']['code']

    # Get repo
    repo = Repo(os.getcwd())

    # Write code file
    file_path = f"generated/{project['name']}.py"
    os.makedirs("generated", exist_ok=True)

    with open(file_path, "w") as f:
        f.write(code)

    # Commit
    repo.index.add([file_path])
    repo.index.commit(f"Generated: {project['name']}")
    repo.remotes.origin.push()

    print(f"Committed: {file_path}")

orch.on('code_generated', on_code_generated)
```

---

## Troubleshooting Integrations

### API Connection Fails

**Error**: "Connection refused" or "HTTP 500"

**Solutions**:
1. Verify Socrates is running: `python socrates.py --api`
2. Check firewall allows port 8000
3. Verify API key is correct
4. Check logs: `tail ~/.socrates/logs/socratic.log`

### Events Not Firing

**Problem**: Registered event listener not triggered

**Solutions**:
1. Verify event type name is correct
2. Check listener is registered before event occurs
3. Enable debug logging: `SOCRATES_LOG_LEVEL=DEBUG`
4. Verify event is actually being emitted

### Webhook Not Called

**Problem**: Webhook registered but not invoked

**Solutions**:
1. Verify webhook URL is accessible from Socrates
2. Check firewall/network allows outbound connections
3. Verify webhook secret is set correctly
4. Check webhook registration confirmed

### Authentication Issues

**Error**: "401 Unauthorized"

**Solutions**:
1. Regenerate and verify token
2. Check token not expired
3. Include token in Authorization header
4. Use Bearer scheme: `Bearer <token>`

---

## Integration Best Practices

1. **Error Handling**: Wrap integrations in try/catch
2. **Logging**: Log all integration events for debugging
3. **Rate Limiting**: Implement backoff for external APIs
4. **Testing**: Test integrations before production
5. **Security**: Never commit API keys to version control
6. **Monitoring**: Monitor integration health
7. **Documentation**: Document integration setup

---

## Request Integration Support

Have an integration idea? Open a GitHub issue or discussion:
- [GitHub Issues](https://github.com/Nireus79/Socrates/issues)
- [GitHub Discussions](https://github.com/Nireus79/Socrates/discussions)

---

## Related Documentation

- [API_REFERENCE.md](API_REFERENCE.md) - Full API documentation
- [ADR-003: Event-Driven Communication](adr/ADR-003-EVENT_DRIVEN_COMMUNICATION.md)
- [ADR-004: FastAPI Backend](adr/ADR-004-FASTAPI_BACKEND.md)

---

**Last Updated**: January 2026
**Version**: 1.3.0
