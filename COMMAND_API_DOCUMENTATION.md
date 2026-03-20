# Command API Documentation

This document provides API documentation for command classes.

## Command Response Format

All commands return a standardized response dictionary:

```
{
    "status": "success|error|exit",
    "message": "Description",
    "data": { command-specific data }
}
```

### Status Codes

- **success**: Command executed successfully
- **error**: Command failed with error
- **exit**: Application should exit
- **nav_context_changed**: Navigation context changed

## Key Command Classes

### ProjectCreateCommand
Create a new project in the system.

Response data includes:
- project: Project object with id, name, type, owner, status, phase

### ProjectLoadCommand
Load an existing project into current session.

Response data includes:
- project: Selected project object
- nav_context: Navigation context

### ProjectListCommand
List all user projects with optional filtering.

Response data includes:
- projects: Array of project objects

### ProjectAnalyzeCommand
Analyze project structure and quality metrics.

Response data includes:
- analysis: Code quality scores, documentation scores, issues

### ProjectTestCommand
Execute project test suite.

Response data includes:
- tests: Test results with passed/failed/skipped counts

### ProjectValidateCommand
Validate project structure and configuration.

Response data includes:
- valid: Boolean validation result
- issues: Array of any validation issues found

## Analytics Commands

### AnalyticsStatusCommand
Display current analytics status and health score.

### AnalyticsTrendsCommand
Show how metrics have changed over time.

### AnalyticsBreakdownCommand
Break down metrics by component/module.

### AnalyticsRecommendCommand
Get AI-powered recommendations based on analytics.

## Code Commands

### CodeGenerateCommand
Generate code based on specifications.

Response data includes:
- code: Generated code content
- language: Programming language
- file_path: Suggested file path

### CodeDocsCommand
Generate or update code documentation.

Response data includes:
- documentation: Generated documentation content
- format: Documentation format (markdown, etc)

## Document Commands

### DocImportCommand
Import documents into project.

Response data includes:
- imported: Number of documents imported
- documents: Array of imported document objects

### DocListCommand
List all imported documents.

Response data includes:
- documents: Array of document objects with metadata

## System Commands

### HelpCommand
Display command help and usage information.

### ExitCommand
Gracefully exit the application.

### BackCommand
Navigate to previous context in navigation stack.

### MenuCommand
Return to main menu.

## Error Response Format

When a command fails:

```
{
    "status": "error",
    "message": "Error description",
    "data": {}
}
```

Common errors:
- "Must be logged in to [action]"
- "Required context not available"
- "Invalid arguments"

## Context Dictionary

Commands receive context with:

- user: Current authenticated User object
- project: Current ProjectContext (may be None)
- orchestrator: AgentOrchestrator instance
- nav_stack: Navigation history
- app: Main SocraticRAGSystem instance

Validate before use:

```python
orchestrator = context.get("orchestrator")
if not orchestrator:
    return self.error("Orchestrator not available")
```

## Best Practices

1. Always validate required context items
2. Handle exceptions and return error responses
3. Use constants instead of hardcoded strings
4. Log important operations
5. Return consistent response format
6. Provide actionable error messages
7. Test edge cases and error conditions
