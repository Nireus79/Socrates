# Integrations - Socrates AI

## Integrations Header

**Connect Socrates with your favorite tools.**

Socrates integrates with GitHub, Jira, Slack, and more. Build custom integrations with our powerful API.

---

## Native Integrations (Coming v1.4)

### GitHub
**Status**: 🔄 In Development (Q1 2026)

**What it does:**
- Automatically create Socrates projects from GitHub repos
- Link GitHub issues to project requirements
- Auto-commit generated code to branches
- Sync pull requests with project status

**How it will work:**
1. Connect your GitHub account
2. Select repos to sync
3. Socrates creates project for each
4. Generated code auto-commits to GitHub

**Coming**: Q1 2026

---

### Jira
**Status**: 🔄 In Development (Q2 2026)

**What it does:**
- Create Jira issues from project specifications
- Link requirements to Jira tickets
- Update issue status as project progresses
- Export code to Jira attachments

**How it will work:**
1. Connect your Jira workspace
2. Select projects to sync
3. Specifications auto-create issues
4. Generated code attached to issues

**Coming**: Q2 2026

---

### Slack
**Status**: 🔄 In Development (Q2 2026)

**What it does:**
- Post project updates to Slack
- Notify team when code is generated
- Get Slack reminders for pending questions
- Share project specs via Slack threads

**How it will work:**
1. Install Slack app from Socrates
2. Select channels for notifications
3. Receive real-time project updates
4. Share results with your team

**Coming**: Q2 2026

---

### VS Code Extension
**Status**: 🔄 Planned (Q3 2026)

**What it does:**
- Open Socrates inside VS Code
- Generate code without leaving IDE
- View specifications inline
- Debug with Socrates suggestions

**Coming**: Q3 2026

---

### Azure DevOps
**Status**: 🔄 Planned (Q3 2026)

**What it does:**
- Sync with Azure Repos
- Create work items from specs
- Link pull requests to projects
- Pipeline integration

**Coming**: Q3 2026

---

## REST API - Build Custom Integrations

### Quick Start

**Base URL**: `https://api.socrates-ai.com/v1`

**Authentication**:
```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  https://api.socrates-ai.com/v1/projects
```

### Core Endpoints

**Projects:**
```
GET    /projects              # List projects
POST   /projects              # Create project
GET    /projects/{id}         # Get project details
DELETE /projects/{id}         # Delete project
PUT    /projects/{id}         # Update project
```

**Code Generation:**
```
POST   /projects/{id}/code    # Generate code
GET    /projects/{id}/code    # Get generated code
```

**Specifications:**
```
GET    /projects/{id}/spec    # Get full specification
POST   /projects/{id}/spec    # Update specification
```

**Dialogue:**
```
POST   /projects/{id}/question  # Get next question
POST   /projects/{id}/answer    # Submit answer
GET    /projects/{id}/history   # Get dialogue history
```

### Example: Create Project & Generate Code

```bash
# 1. Create project
curl -X POST https://api.socrates-ai.com/v1/projects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Task Manager",
    "description": "A simple task management app"
  }'

# Response: {"id": "proj_123", "status": "created"}

# 2. Add project details (via API or dialogue)
curl -X POST https://api.socrates-ai.com/v1/projects/proj_123/answer \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"answer": "For personal use initially"}'

# 3. Generate code after specifications complete
curl -X POST https://api.socrates-ai.com/v1/projects/proj_123/code \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"language": "python"}'

# Response: {"code": "...", "documentation": "..."}
```

[Full API Documentation →](api-docs-link)

---

## Webhook Integration

### Receive Real-Time Events

Socrates can send webhooks when important events happen:

**Events:**
- `project.created`
- `project.updated`
- `dialogue.completed`
- `code.generated`
- `specification.finalized`

### Setup Webhook

```bash
curl -X POST https://api.socrates-ai.com/v1/webhooks \
  -H "Authorization: Bearer $TOKEN" \
  -d '{
    "url": "https://yourapp.com/webhooks/socrates",
    "events": ["code.generated", "dialogue.completed"],
    "secret": "your-secret-key"
  }'
```

### Webhook Payload Example

```json
{
  "id": "evt_123",
  "event_type": "code.generated",
  "timestamp": "2026-01-18T10:30:00Z",
  "project_id": "proj_123",
  "data": {
    "language": "python",
    "lines_of_code": 342,
    "generation_time_ms": 5234
  },
  "signature": "sha256=..."
}
```

### Verify Webhook Signature

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
```

---

## Community Integrations

### GitHub Actions

**Socrates GitHub Action** - Run Socrates in your CI/CD pipeline

```yaml
- name: Generate with Socrates
  uses: Nireus79/socrates-action@v1
  with:
    project-spec: 'project-spec.json'
    output-dir: './generated'
```

[View on GitHub Marketplace](marketplace-link)

### Zapier (Coming Q2 2026)

Connect Socrates to 5,000+ apps:
- Trigger Socrates from Google Forms
- Save generated code to Google Drive
- Create Todoist tasks from specifications

---

## Integration Examples

### Example 1: Auto-Generate Code from GitHub PR

**Scenario**: PR submitted with project spec → Auto-generate code

```python
from github import Github
from socrates import SocratesAPI

g = Github(github_token)
socrates = SocratesAPI(api_key)

for pr in repo.get_pulls():
    spec = extract_spec_from_pr(pr)

    project = socrates.create_project(
        name=pr.title,
        spec=spec
    )

    code = socrates.generate_code(project.id)

    pr.create_review_comment(
        f"Generated code:\n{code}"
    )
```

### Example 2: Slack Bot Updates

**Scenario**: Post code generation results to Slack

```python
from slack_sdk import WebClient
from socrates import listen_to_events

slack = WebClient(token=slack_token)

def on_code_generated(event):
    message = f"""
    Code Generated! 🎉
    Project: {event['data']['project_name']}
    Language: {event['data']['language']}
    Lines: {event['data']['lines_of_code']}
    """
    slack.chat_postMessage(
        channel="dev-notifications",
        text=message
    )

listen_to_events('code.generated', on_code_generated)
```

### Example 3: Jira Issue Creator

**Scenario**: Auto-create Jira tickets from specifications

```python
from jira import JIRA
from socrates import SocratesAPI

jira = JIRA(server=jira_url, auth=(user, token))
socrates = SocratesAPI(api_key)

def on_spec_complete(event):
    spec = socrates.get_specification(event['project_id'])

    issue = jira.create_issue(
        project='DEV',
        issuetype='Epic',
        summary=spec['project_name'],
        description=format_spec(spec),
        customfield_requirements=spec['requirements']
    )

    print(f"Created issue: {issue.key}")

listen_to_events('specification.completed', on_spec_complete)
```

### Example 4: Auto-Commit to Git

**Scenario**: Generated code auto-commits to repository

```python
from git import Repo
from socrates import SocratesAPI

repo = Repo('.')
socrates = SocratesAPI(api_key)

def on_code_generated(event):
    code = socrates.get_code(event['project_id'])

    filepath = f"generated/{event['project_name']}.py"
    with open(filepath, 'w') as f:
        f.write(code)

    repo.index.add([filepath])
    repo.index.commit(f"Generated: {event['project_name']}")
    repo.remotes.origin.push()

listen_to_events('code.generated', on_code_generated)
```

---

## Integration Checklist

### Before Building an Integration

- [ ] Understand your use case
- [ ] Check API documentation
- [ ] Get API key/JWT token
- [ ] Review webhook structure
- [ ] Plan error handling
- [ ] Consider rate limits
- [ ] Test with small dataset first

### After Building

- [ ] Test thoroughly
- [ ] Add error handling
- [ ] Document for team
- [ ] Monitor usage
- [ ] Get feedback
- [ ] Iterate

---

## Popular Use Cases

### 1. CI/CD Integration
**Generate code automatically in your pipeline**
- Trigger on PR creation
- Generate code based on spec files
- Auto-commit or create PR review

### 2. IDE Integration
**Embed Socrates in your development environment**
- Launch from IDE toolbar
- Generate inline
- Insert directly into editor

### 3. Documentation System
**Keep documentation in sync with specifications**
- Auto-generate docs from specs
- Update when specs change
- Version control documentation

### 4. Team Collaboration
**Notify team of progress**
- Send updates to Slack
- Create issue tickets
- Update project management tools

### 5. Data Migration
**Generate migration scripts**
- Define old/new schema with Socrates
- Generate migration code
- Test and deploy

---

## Integration Support

### Getting Help

**Documentation**: [Full API Reference](api-docs-link)
**Community**: [GitHub Discussions](discussions-link)
**Issues**: [Report Integration Issues](github-issues-link)

### Reporting Issues

Include:
- Integration name
- Step-by-step reproduction
- Error message
- Expected vs. actual behavior
- API version
- Your OS/environment

### Feature Requests

Want a specific integration?
- [Vote on GitHub](feature-voting-link)
- [Join Discord discussion](discord-link)
- [Contact us](contact-link)

---

## Rate Limits

### API Rate Limits

**Free Tier:**
- 100 requests/day
- 10 requests/minute

**Basic Tier:**
- 1,000 requests/day
- 100 requests/minute

**Pro Tier:**
- 10,000 requests/day
- 500 requests/minute

**Enterprise:**
- Custom limits

### Respecting Limits

- Cache results when possible
- Implement exponential backoff
- Monitor X-RateLimit headers
- Contact support for higher limits

---

## SDKs & Libraries

### Official SDKs

**Python**:
```bash
pip install socrates-ai
```

**JavaScript/Node.js**:
```bash
npm install @socrates/sdk
```

**Go**:
```bash
go get github.com/Nireus79/socrates-go
```

### Community SDKs

- Ruby: `gem install socrates-ruby`
- PHP: `composer require socrates/php`
- C#: `dotnet add package Socrates.SDK`

[View all SDKs →](sdks-link)

---

## API Status & Monitoring

**API Status**: [status.socrates-ai.com](status-link)

**Monitor your integrations:**
- View API usage dashboard
- Check error logs
- Monitor response times
- Set up alerts

---

**Ready to integrate Socrates?**

[View Full API Docs →](api-docs-link)
[Browse Integration Examples →](examples-link)
[Join Developer Community →](discord-link)

---

**Last Updated**: January 2026
**Version**: 1.3.0
