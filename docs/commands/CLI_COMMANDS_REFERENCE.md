# CLI Commands Reference

Comprehensive reference for all Socrates CLI commands, organized by module and functionality.

## Table of Contents

1. [System Commands](#system-commands)
2. [Project Management](#project-management)
3. [Conflict Detection](#conflict-detection)
4. [Workflow Orchestration](#workflow-orchestration)
5. [Security Monitoring](#security-monitoring)
6. [Performance Monitoring](#performance-monitoring)
7. [Learning & Recommendations](#learning--recommendations)
8. [Code Analysis](#code-analysis)
9. [Documentation Generation](#documentation-generation)
10. [Knowledge Management](#knowledge-management)
11. [User Management](#user-management)

---

## System Commands

Basic system and navigation commands.

### Help
Display available commands and usage information.
```
help
```

### Status
Show current system status and loaded project information.
```
status
```

### Clear
Clear the terminal screen.
```
clear
```

### Exit
Exit the Socrates application.
```
exit
```

### Info
Display system information and configuration details.
```
info
```

### Menu
Display the main menu for command navigation.
```
menu
```

---

## Project Management

Commands for creating, loading, and managing projects.

### Create Project
Create a new Socrates project.
```
project create <project_name>
```
**Parameters:**
- `project_name`: Name of the new project

**Response:**
- Project ID
- Creation timestamp
- Initial project context

### Load Project
Load an existing project from storage.
```
project load <project_id>
```
**Parameters:**
- `project_id`: ID of the project to load

### List Projects
List all available projects.
```
project list
```

### Project Analysis
Analyze project specifications for insights and improvements.
```
project analyze
```

### Project Testing
Run tests on the current project.
```
project test
```

### Project Validation
Validate project configuration and requirements.
```
project validate
```

### Project Review
Get AI-powered review of current project state.
```
project review
```

### Archive Project
Archive a project for storage.
```
project archive <project_id>
```

### Restore Project
Restore an archived project.
```
project restore <project_id>
```

### Delete Project
Permanently delete a project.
```
project delete <project_id>
```

---

## Conflict Detection

Commands for identifying and resolving specification conflicts.

### Analyze Conflicts
Detect conflicts in project specifications and requirements.
```
conflict analyze
```
**Output:**
- List of detected conflicts
- Severity levels (critical, high, medium, low)
- Affected specification areas

### List Conflicts
Display all stored conflicts for the current project.
```
conflict list [status]
```
**Optional Parameters:**
- `status`: Filter by status (open, resolved, ignored)

**Response:**
- Conflict ID
- Type and severity
- Current resolution status
- Timestamps

### Resolve Conflicts
Resolve conflicts using voting or consensus strategies.
```
conflict resolve <conflict_id> [strategy]
```
**Parameters:**
- `conflict_id`: ID of the conflict to resolve
- `strategy`: Resolution strategy (voting, consensus, custom)

**Strategies:**
- **voting**: Each team member votes on preferred resolution
- **consensus**: Requires unanimous agreement
- **custom**: Manual resolution configuration

### Ignore Conflict
Mark a conflict as ignored or acknowledged but not resolved.
```
conflict ignore <conflict_id> [reason]
```
**Parameters:**
- `conflict_id`: ID of the conflict
- `reason`: Optional reason for ignoring

---

## Workflow Orchestration

Commands for creating and managing automated workflows.

### Create Workflow
Define a new workflow with sequential or parallel tasks.
```
workflow create <workflow_name>
```
**Interactive Input:**
- Workflow name
- Workflow steps (comma-separated agent types)
- Optional description

**Example:**
```
workflow create data_processing
Workflow steps: validator, transformer, analyzer, reporter
```

### List Workflows
Display all available workflows.
```
workflow list
```

**Response:**
- Workflow ID
- Name and description
- Number of steps
- Last execution status

### Execute Workflow
Run a workflow with specified parameters.
```
workflow execute <workflow_id>
```
**Parameters:**
- `workflow_id`: ID of the workflow to execute

**Features:**
- Automatic retry (3 attempts)
- Progress tracking
- Error handling and recovery
- Execution duration metrics

**Output:**
- Execution status (success/failed)
- Duration in milliseconds
- Step-by-step results

---

## Security Monitoring

Commands for monitoring and managing security incidents.

### Security Status
Display overall security status and incident summary.
```
security status
```

**Output:**
- Overall status (Secure/Alert)
- Total incidents count
- Critical incidents count
- High-severity incidents count
- Color-coded severity indicators

### Security Incidents
List security incidents with optional filtering.
```
security incidents [severity]
```
**Optional Parameters:**
- `severity`: Filter by severity level (critical, high, medium, low)

**Response:**
- Incident ID
- Type (validation_failed, injection_detected, etc.)
- Severity level
- Detection timestamp
- Associated details

### Validate Input
Validate code or input strings for security vulnerabilities.
```
security validate
```
**Interactive Input:**
- Text to validate (multiline)

**Analysis Includes:**
- SQL injection detection
- XSS vulnerability detection
- Command injection detection
- Prompt injection detection
- Type safety checking
- Code quality assessment

**Output:**
- Security score (0-100)
- Detected threats list
- Recommendations for fixes
- Incident recording for audit trail

### Security Trends
Show security incident trends over time.
```
security trends
```

**Output:**
- Incidents grouped by type
- Trend visualization (ASCII bar chart)
- Historical incident counts
- Most common issue types

---

## Performance Monitoring

Commands for tracking and optimizing system performance.

### Performance Status
Display comprehensive performance metrics.
```
performance status
```

**Output:**
- Execution Performance:
  - Total calls count
  - Average duration (ms)
  - Maximum duration (ms)
- Cache Performance:
  - Cache size
  - Hit rate percentage
  - Number of entries

### Performance Agents
Show per-agent execution statistics.
```
performance agents
```

**Output:**
- Agent name
- Number of calls
- Average execution duration
- Top slowest agents highlighted

### Performance Cache
Display cache statistics and efficiency metrics.
```
performance cache
```

**Output:**
- Cache entries count
- Hit rate percentage
- Miss rate percentage
- Cache utilization

### Performance Bottlenecks
Identify slow operations exceeding a threshold.
```
performance bottlenecks [threshold_ms]
```
**Optional Parameters:**
- `threshold_ms`: Minimum duration to report (default: 1000ms)

**Output:**
- Operation name
- Duration in milliseconds
- Number of occurrences
- Performance impact assessment

### Performance Reset
Clear performance tracking data.
```
performance reset [target]
```
**Optional Parameters:**
- `target`: Reset target (profiler, cache, all) - default: all

---

## Learning & Recommendations

Commands for accessing learning recommendations and pattern analysis.

### Learning Recommendations
Get improvement recommendations for an agent.
```
learning recommendations <agent_name> [limit]
```
**Parameters:**
- `agent_name`: Name of the agent to analyze
- `limit`: Maximum recommendations (default: 5)

**Output:**
- Recommendation ID
- Title and description
- Confidence score (0-100%)
- Impact level (high, medium, low)
- Suggested implementation details

### Learning Patterns
Detect and display patterns in agent behavior.
```
learning patterns <agent_name> [pattern_type]
```
**Parameters:**
- `agent_name`: Agent to analyze
- `pattern_type`: Filter type (usage, error, performance, all)

**Pattern Types:**
- **usage**: Common interaction patterns
- **error**: Recurring error patterns
- **performance**: Performance trend patterns
- **all**: All pattern types (default)

**Output:**
- Pattern name and frequency
- Detection confidence
- Associated metrics
- Recommendations based on patterns

### Learning Session
Start a learning session to track agent interactions.
```
learning session <user_id>
```
**Parameters:**
- `user_id`: User identifier for session tracking

**Interactive Input:**
- Optional session context or goals

**Output:**
- Session ID
- Start timestamp
- User association
- Session context

### Learning Analyze
Generate comprehensive learning insights for an agent.
```
learning analyze <agent_name> [confidence_threshold]
```
**Parameters:**
- `agent_name`: Agent to analyze
- `confidence_threshold`: Minimum confidence (0-1, default: 0.7)

**Output:**
- Summary of patterns detected
- Error patterns identified
- Performance issues found
- Top recommendations
- Implementation priority

---

## Code Analysis

Commands for analyzing code quality and identifying issues.

### Analyze Code
Perform quality analysis on code snippets.
```
analyze code [file_path]
```
**Parameters:**
- `file_path`: Optional path to code file (if not provided, input from stdin)

**Analysis Includes:**
- Type checking
- Docstring validation
- Security analysis
- Performance analysis
- Complexity detection
- Pattern recognition

**Output:**
- Quality score (0-100)
- Issues count and severity breakdown
- Detected design patterns
- Recommendations for improvement

### Analyze File
Detailed analysis of a single file.
```
analyze file <file_path>
```
**Parameters:**
- `file_path`: Path to the file to analyze

**Output:**
- Quality score
- Issue list with:
  - Type (complexity, code_smell, security, etc.)
  - Severity level
  - Location in file
  - Detailed message
  - Suggested fixes

### Analyze Project
Comprehensive analysis of entire project codebase.
```
analyze project <project_path>
```
**Parameters:**
- `project_path`: Root path of the project

**Output:**
- Files analyzed count
- Total issues discovered
- Average quality score across files
- Top files with most issues
- Project-level recommendations

### Analysis Issues
Detect code smells, complexity issues, and patterns.
```
analysis issues <type> [file_path]
```
**Parameters:**
- `type`: Issue type (smells, complexity, patterns)
- `file_path`: Optional specific file

**Issue Types:**
- **smells**: Code smell detection with severity and suggestions
- **complexity**: Cyclomatic complexity analysis
- **patterns**: Design pattern identification

**Output:**
- Issue list with detailed information
- Severity indicators
- Remediation suggestions
- Code locations

---

## Documentation Generation

Commands for automatic documentation creation.

### Generate README
Create a comprehensive README file.
```
docs generate readme <project_name>
```
**Interactive Input:**
- Project description (required)
- Features list (optional, comma-separated)
- Installation instructions (optional)
- Usage examples (optional)

**Generated Content:**
- Project overview
- Feature descriptions
- Installation guide
- Quick start section
- Usage examples
- Contributing guidelines
- License information

### Generate API Docs
Create API documentation from code structure.
```
docs generate api <file_path>
```
**Parameters:**
- `file_path`: Python file containing API definitions

**Generated Documentation:**
- Class and function definitions
- Parameter documentation
- Return value specifications
- Usage examples
- Type hints
- Exception documentation

### Generate Architecture Docs
Create architecture documentation for modules.
```
docs generate architecture <module1> [module2] ...
```
**Parameters:**
- `module1, module2, ...`: Module names to document

**Generated Content:**
- Module overview
- Component relationships
- Data flow diagrams
- Integration points
- Design patterns used
- Configuration guide

### Generate All Docs
Generate complete documentation suite.
```
docs generate all <project_name> <project_path>
```
**Parameters:**
- `project_name`: Name of the project
- `project_path`: Root directory path

**Interactive Input:**
- Project description

**Generated Artifacts:**
- README.md
- API_DOCUMENTATION.md
- ARCHITECTURE.md
- Installation guide
- Usage guide
- Configuration guide

---

## Knowledge Management

Commands for managing project knowledge and insights.

### Knowledge Add
Add a new knowledge entry to the knowledge base.
```
knowledge add <category>
```
**Parameters:**
- `category`: Knowledge category (api_design, patterns, best_practices, etc.)

**Interactive Input:**
- Knowledge content
- Tags (optional)
- Source reference (optional)

### Knowledge List
Display all knowledge entries.
```
knowledge list [category]
```
**Optional Parameters:**
- `category`: Filter by category

**Output:**
- Entry ID
- Title/Summary
- Category
- Creation date
- Associated tags

### Knowledge Search
Search knowledge base by keyword.
```
knowledge search <query>
```
**Parameters:**
- `query`: Search query (supports regex)

**Output:**
- Matching entries
- Relevance score
- Context excerpt
- Full entry ID for retrieval

### Knowledge Export
Export knowledge base to file.
```
knowledge export [format]
```
**Optional Parameters:**
- `format`: Export format (json, markdown, csv - default: json)

---

## User Management

Commands for managing user accounts and authentication.

### User Login
Authenticate a user.
```
user login <username>
```
**Interactive Input:**
- Username
- Passcode/password

**Output:**
- Authentication status
- User profile information
- Available projects
- Session token

### User Create
Create a new user account.
```
user create <username>
```
**Interactive Input:**
- Email address
- Password/passcode
- User role
- Organization (optional)

### User Logout
End the current user session.
```
user logout
```

### User Profile
View or edit current user profile.
```
user profile
```

**Output:**
- Username
- Email
- Account creation date
- Projects owned
- Subscription tier

---

## Command Response Format

All commands return responses in the following format:

### Success Response
```json
{
  "status": "success",
  "message": "Operation completed successfully",
  "data": {
    "key": "value",
    ...
  }
}
```

### Error Response
```json
{
  "status": "error",
  "message": "Error description with details"
}
```

---

## Common Parameters

### Global Options
Available on all commands:

- `--help`: Display command help and usage
- `--verbose`: Enable verbose output
- `--format [json|text|table]`: Output format specification
- `--output <file>`: Save output to file

---

## Environment Variables

Configure Socrates via environment variables:

- `SOCRATES_API_KEY`: Anthropic API key
- `SOCRATES_DATA_DIR`: Local data directory path
- `SOCRATES_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `SOCRATES_DB_PATH`: Database file location

---

## Tips & Best Practices

### Command Chaining
Run multiple commands in sequence:
```
project load proj_001
conflict analyze
workflow execute wf_001
```

### Piping Output
Some commands support piping for automation:
```
knowledge search "pattern" | analysis issues patterns
```

### Error Recovery
Most commands support retry logic with exponential backoff:
```
workflow execute wf_001  # Automatically retries 3 times on failure
```

### Performance
For large projects, use appropriate filtering:
```
security incidents critical  # Only critical incidents
performance bottlenecks 500   # Operations slower than 500ms
```

---

## Related Documentation

- [API Reference](../API_REFERENCE.md) - REST API endpoint documentation
- [Architecture Guide](../architecture/ARCHITECTURE.md) - System architecture
- [Developer Guide](../DEVELOPER_GUIDE.md) - Development setup and practices
- [Deployment Guide](../DEPLOYMENT.md) - Deployment instructions

