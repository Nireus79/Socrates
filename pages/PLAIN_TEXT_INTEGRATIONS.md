INTEGRATIONS - Socrates AI

Connect Socrates to Your Workflow

Socrates integrates with the tools you already use.

NATIVE INTEGRATIONS STATUS

Available Today:
- REST API (Full API access)
- Webhooks (Real-time events)
- CLI Integration (Command-line tools)
- Python/JavaScript/Go SDKs

Coming v1.4 (Q1 2026):
- GitHub Integration (auto-create repos, auto-commit code)
- Jira Integration (auto-create tickets from specifications)
- Slack Integration (notify team of updates)
- Azure DevOps (full pipeline integration)

REST API

Full API access for programmatic control.

Quick Start:

Get your API key:
1. Log into Socrates
2. Go to Settings → API Keys
3. Click "Create new API key"
4. Copy the key

Make Your First Request:

curl -X GET https://api.socrates-ai.com/v1/projects \
  -H "Authorization: Bearer YOUR_API_KEY"

Response:
Your list of projects appears here

Core Endpoints:

List Projects:
GET /v1/projects
Get all your projects with their specs

Create Project:
POST /v1/projects
Create new project programmatically

Get Project:
GET /v1/projects/{id}
Retrieve project details and specification

Generate Code:
POST /v1/projects/{id}/generate
Generate code from specification

Update Project:
PUT /v1/projects/{id}
Update project details or specification

Delete Project:
DELETE /v1/projects/{id}
Delete a project

Get Specification:
GET /v1/projects/{id}/specification
Export specification in various formats

Rate Limits by Tier:

Free Tier:
- 100 requests per day
- 10 requests per minute

Basic Tier:
- 1,000 requests per day
- 100 requests per minute

Pro Tier:
- 10,000 requests per day
- 500 requests per minute

Enterprise:
- Custom limits
- Dedicated support

Webhook Integration

Real-time event notifications for automation.

Event Types:

project.created - New project created
project.updated - Project specification updated
dialogue.question_answered - Question answered in dialogue
code.generated - Code generation completed
code.failed - Code generation failed
specification.exported - Specification exported
team.member_added - Team member added to project

Setting Up Webhooks:

1. Go to Settings → Webhooks
2. Click "Create new webhook"
3. Enter webhook URL (where to send events)
4. Select which events to listen for
5. Save
6. We'll send a test event

Webhook Payload Example:

Event: project.created
{
  "event": "project.created",
  "timestamp": "2026-01-18T10:30:00Z",
  "project_id": "proj_123abc",
  "project_name": "Task Manager App",
  "created_by": "user_456def"
}

Event: code.generated
{
  "event": "code.generated",
  "timestamp": "2026-01-18T10:35:00Z",
  "project_id": "proj_123abc",
  "language": "python",
  "code_url": "https://api.socrates-ai.com/v1/code/proj_123abc/python",
  "lines_of_code": 1250
}

Use Webhooks For:
- Trigger external workflows
- Notify team on Slack
- Create tickets in Jira
- Update project management tools
- Start CI/CD pipelines
- Log events to analytics

Community Integrations

Popular integrations built by community members.

GitHub Actions Integration:

Trigger Socrates from GitHub Actions workflow:

on: [push]
jobs:
  generate-code:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Generate Socrates Code
        uses: community/socrates-action@v1
        with:
          project-id: ${{ secrets.SOCRATES_PROJECT_ID }}
          api-key: ${{ secrets.SOCRATES_API_KEY }}

Zapier Integration (Coming):

Connect Socrates to 5,000+ apps through Zapier.

Example workflows:
- When new GitHub issue → Create Socrates project
- When Socrates code generated → Notify Slack
- When specification updated → Create Jira ticket

INTEGRATION EXAMPLES

Example 1: Auto-Generate Code in CI/CD

Workflow:
1. Developer pushes to GitHub
2. GitHub Actions triggered
3. Calls Socrates API to generate code
4. Code committed back to repo
5. Tests run automatically
6. Deploy on success

Implementation:

name: Generate Code with Socrates
on: [push]
jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Generate Code
        run: |
          curl -X POST https://api.socrates-ai.com/v1/projects/proj_123/generate \
            -H "Authorization: Bearer ${{ secrets.SOCRATES_API_KEY }}" \
            -H "Content-Type: application/json" \
            -d '{"language":"python"}'
      - name: Commit Code
        run: |
          git add .
          git commit -m "feat: auto-generated code"
          git push

Example 2: Slack Notifications

Workflow:
1. Project specification updated
2. Webhook sends event to Slack
3. Team sees notification
4. Click link to review changes
5. Collaborate on updates

Setup:

1. Create Slack webhook URL in Slack app
2. In Socrates settings, add webhook
3. Select events to notify (project.updated, code.generated)
4. Slack receives notifications automatically

Example 3: Auto-Create Jira Tickets

Workflow:
1. New project created in Socrates
2. Webhook triggered
3. Script creates Jira ticket
4. Project details → ticket description
5. Team gets notification

Implementation Using Zapier:

1. In Zapier: Trigger on "Socrates Project Created"
2. Action: Create Jira issue
3. Map fields:
   - Project Name → Issue Title
   - Specification → Issue Description
   - Project URL → Issue Link
4. Team automatically notified in Jira

Example 4: GitHub Auto-Commit

Workflow:
1. Generate code in Socrates
2. Webhook triggers
3. Script pulls code from Socrates API
4. Commits to GitHub repo
5. Creates pull request for review

Implementation:

#!/bin/bash
# When code is generated, commit to repo

PROJECT_ID="proj_123"
API_KEY="sk-..."
REPO="my-org/my-repo"

# Get generated code
CODE=$(curl -s -X GET https://api.socrates-ai.com/v1/code/$PROJECT_ID/python \
  -H "Authorization: Bearer $API_KEY")

# Clone repo
git clone https://github.com/$REPO.git
cd repo

# Add code
cp $CODE .
git add .
git commit -m "feat: auto-generated from Socrates"
git push

# Create PR (requires GitHub token)
gh pr create --title "Auto-generated code" \
  --body "Generated from Socrates specification"

AVAILABLE SDKs

Official SDKs:

Python SDK:
pip install socrates-sdk
from socrates import SocratesClient
client = SocratesClient(api_key="sk-...")
projects = client.projects.list()

JavaScript SDK:
npm install @socrates/sdk
const { SocratesClient } = require('@socrates/sdk');
const client = new SocratesClient({ apiKey: 'sk-...' });
const projects = await client.projects.list();

Go SDK:
go get github.com/nireus79/socrates-go
import "github.com/nireus79/socrates-go"
client := socrates.NewClient("sk-...")
projects, _ := client.Projects.List()

Community SDKs:

Ruby (community maintained)
Rust (community maintained)
PHP (community maintained)

See all SDKs: https://github.com/Nireus79/Socrates/tree/master/sdks

POPULAR USE CASES

Use Case 1: Automated Development Pipeline

Setup:
- GitHub Actions workflow triggers on push
- Calls Socrates API to generate code
- Tests run automatically
- Code deployed on success
- Team notified on Slack

Result: Fully automated code generation and deployment

Use Case 2: IDE Integration

Setup:
- VS Code extension (coming v1.5)
- Right-click → "Generate with Socrates"
- New file created with generated code
- Your cursor ready to edit

Result: Seamless code generation within IDE

Use Case 3: Documentation Synchronization

Setup:
- Update specification in Socrates
- Webhook triggers
- Documentation updated automatically
- Published to docs site

Result: Specs and docs always in sync

Use Case 4: Project Management Integration

Setup:
- New project in Socrates
- Jira ticket created automatically
- Specification → ticket description
- Project link in Jira
- Team collaborates in both tools

Result: Single source of truth across tools

Use Case 5: Team Notifications

Setup:
- Slack channel for project updates
- Code generated → Slack notification
- Spec updated → Slack notification
- Team stays informed

Result: No missed updates, team stays aligned

GETTING HELP

API Documentation:
- Full API Reference at https://github.com/Nireus79/Socrates/blob/master/docs/API_REFERENCE.md
- API Examples at https://github.com/Nireus79/Socrates/tree/master/examples/api

Webhook Documentation:
- Webhook Guide at https://github.com/Nireus79/Socrates/blob/master/docs/WEBHOOKS.md
- Event Examples at https://github.com/Nireus79/Socrates/blob/master/docs/WEBHOOK_EVENTS.md

Questions:
- Discord Community at https://discord.gg/socrates
- GitHub Issues at https://github.com/Nireus79/Socrates/issues
- Email support@socrates-ai.com

Coming Next

v1.4 (Q1 2026):
- GitHub integration
- Jira integration
- Slack integration
- Azure DevOps integration

v1.5 (Q2 2026):
- VS Code extension
- More community integrations
- Enhanced API features

Last Updated: January 2026
Version: 1.3.0
