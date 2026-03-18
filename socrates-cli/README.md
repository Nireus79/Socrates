# socrates-cli

Command-line interface for the Socrates AI platform. Interact with Socrates through an easy-to-use CLI tool.

## Overview

`socrates-cli` provides a unified command-line interface to the Socrates platform. It communicates with the Socrates API server, making it perfect for:

- Local development and testing
- CI/CD pipelines
- Scripting and automation
- Interactive exploration

## Installation

### Via pip
```bash
pip install socrates-cli
```

### With Full Platform
```bash
pip install socrates-ai  # Includes CLI, API, and all libraries
```

### From Source
```bash
git clone https://github.com/themsou/Socrates.git
cd Socrates/socrates-cli
pip install -e .
```

## Quick Start

### Initialize Socrates
```bash
# Initialize with API server
socrates init

# Or specify API URL explicitly
socrates init --api-url http://localhost:8000
```

### Create a Project
```bash
socrates project create \
  --name "My Project" \
  --owner "your-username" \
  --description "A sample project"
```

### List Projects
```bash
socrates project list

# With formatting
socrates project list --format json
```

### Generate Code
```bash
# Generate code for a project
socrates code generate \
  --project-id proj_xxxxx \
  --prompt "Create a REST API"

# Save to file
socrates code generate \
  --project-id proj_xxxxx \
  --prompt "Create a REST API" \
  --output generated_code.py
```

### System Information
```bash
# Check connection and system info
socrates info

# Check API server health
socrates health
```

## Environment Variables

Configure the CLI with environment variables:

```bash
# API Server
export SOCRATES_API_URL=http://localhost:8000
export SOCRATES_API_PORT=8000

# Authentication (if required)
export SOCRATES_API_KEY=your-api-key

# Logging
export SOCRATES_LOG_LEVEL=INFO
```

## Commands Reference

### Project Management

#### `socrates project create`
Create a new project.

```bash
socrates project create \
  --name "Project Name" \
  --owner "username" \
  --description "Optional description"
```

**Options**:
- `--name` (required): Project name
- `--owner` (required): Project owner
- `--description`: Project description

#### `socrates project list`
List all projects.

```bash
socrates project list

# JSON output
socrates project list --format json

# Filter by owner
socrates project list --owner username
```

**Options**:
- `--format`: Output format (table, json) - default: table
- `--owner`: Filter by owner

#### `socrates project get`
Get project details.

```bash
socrates project get --project-id proj_xxxxx
```

**Options**:
- `--project-id` (required): Project ID

#### `socrates project delete`
Delete a project.

```bash
socrates project delete --project-id proj_xxxxx

# With confirmation
socrates project delete --project-id proj_xxxxx --yes
```

**Options**:
- `--project-id` (required): Project ID
- `--yes`, `-y`: Skip confirmation prompt

### Code Generation

#### `socrates code generate`
Generate code for a project.

```bash
socrates code generate \
  --project-id proj_xxxxx \
  --prompt "Create a REST API for user management"
```

**Options**:
- `--project-id` (required): Project ID
- `--prompt` (required): Code generation prompt
- `--output`, `-o`: Save to file
- `--format`: Output format (text, json)

#### `socrates code analyze`
Analyze generated code.

```bash
socrates code analyze \
  --project-id proj_xxxxx \
  --code-id code_xxxxx
```

**Options**:
- `--project-id` (required): Project ID
- `--code-id` (required): Code ID

### System Information

#### `socrates init`
Initialize CLI configuration.

```bash
socrates init

# Specify API server
socrates init --api-url http://localhost:8000
```

#### `socrates info`
Display system information.

```bash
socrates info
```

#### `socrates health`
Check API server health.

```bash
socrates health
```

#### `socrates version`
Display CLI version.

```bash
socrates version
```

## Configuration

### Configuration File
The CLI creates a configuration file at:
- **Linux/macOS**: `~/.socrates/config.json`
- **Windows**: `%APPDATA%\socrates\config.json`

Example configuration:
```json
{
  "api_url": "http://localhost:8000",
  "api_key": "your-api-key",
  "timeout": 30,
  "output_format": "table",
  "log_level": "INFO"
}
```

### Configuration Precedence
1. Command-line arguments (highest)
2. Environment variables
3. Configuration file
4. Default values (lowest)

## Using with API Server

The CLI requires a running Socrates API server:

```bash
# Terminal 1: Start API server
socrates-api

# Terminal 2: Use CLI
socrates project create --name "My Project" --owner "user"
```

## Standalone Mode (Optional)

For quick testing without a separate API server:

```bash
# Install with standalone support
pip install socrates-cli[standalone]

# Use directly (no API server needed)
socrates project create --name "My Project" --owner "user" --standalone
```

## Output Formats

### Table Format (default)
```bash
socrates project list
```

Output:
```
ID           Name           Owner    Created
proj_abc123  My Project     user     2024-01-15
proj_def456  Another One    user     2024-01-16
```

### JSON Format
```bash
socrates project list --format json
```

Output:
```json
[
  {
    "id": "proj_abc123",
    "name": "My Project",
    "owner": "user",
    "created_at": "2024-01-15T10:30:00Z"
  }
]
```

## Error Handling

The CLI provides clear error messages:

```bash
# Connection refused
socrates info
Error: Cannot connect to API server at http://localhost:8000
Suggestion: Start API server with 'socrates-api'

# Invalid project ID
socrates project get --project-id invalid
Error: Project not found
```

## Scripting Examples

### Bash Script
```bash
#!/bin/bash

# Create project
PROJECT=$(socrates project create \
  --name "Auto-Generated" \
  --owner "bot" \
  --format json)

PROJECT_ID=$(echo $PROJECT | jq -r '.id')

# Generate code
socrates code generate \
  --project-id $PROJECT_ID \
  --prompt "Create a Python function" \
  --output function.py

echo "Code saved to function.py"
```

### Python Script
```python
import subprocess
import json

# Create project
result = subprocess.run([
    'socrates', 'project', 'create',
    '--name', 'MyProject',
    '--owner', 'bot',
    '--format', 'json'
], capture_output=True, text=True)

project = json.loads(result.stdout)
project_id = project['id']

# Generate code
subprocess.run([
    'socrates', 'code', 'generate',
    '--project-id', project_id,
    '--prompt', 'Create a REST API',
    '--output', 'api.py'
])
```

## Troubleshooting

### "Cannot connect to API server"
```bash
# Check if API server is running
socrates health

# Start API server
socrates-api

# Specify custom API URL if needed
export SOCRATES_API_URL=http://your-server:8000
socrates info
```

### "Invalid API key"
```bash
# Set API key
export SOCRATES_API_KEY=your-api-key

# Or add to config file
~/.socrates/config.json
```

### "Command not found"
```bash
# Reinstall CLI
pip install --upgrade socrates-cli

# Or install from source
pip install -e .
```

## Performance Tips

- Use JSON format for scripting: `--format json`
- Batch operations when possible
- Cache API responses when appropriate
- Use pagination for large result sets

## Support

- **Documentation**: See [docs/](../docs/)
- **Issues**: [GitHub Issues](https://github.com/themsou/Socrates/issues)
- **API Documentation**: http://localhost:8000/docs (when API running)

## Contributing

Contributions are welcome! See the main Socrates repository for guidelines.

## License

MIT - see [LICENSE](LICENSE) for details
