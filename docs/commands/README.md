# Commands Documentation

Complete documentation for Socrates CLI commands, organized by module and functionality.

## Quick Navigation

### By Purpose

- **[System Commands](../guides/PHASE_9_NEW_FEATURES_GUIDE.md#getting-started)** - Navigation and status
- **[Project Management](../guides/PHASE_9_NEW_FEATURES_GUIDE.md#module-1-conflict-detection--resolution)** - Create, load, and manage projects
- **[Conflict Management](../guides/PHASE_9_NEW_FEATURES_GUIDE.md#module-1-conflict-detection--resolution)** - Detect and resolve specification conflicts
- **[Workflows](../guides/PHASE_9_NEW_FEATURES_GUIDE.md#module-2-workflow-orchestration)** - Automate multi-agent workflows
- **[Security](../guides/PHASE_9_NEW_FEATURES_GUIDE.md#module-3-security-monitoring)** - Monitor and prevent security issues
- **[Performance](../guides/PHASE_9_NEW_FEATURES_GUIDE.md#module-4-performance-monitoring--optimization)** - Optimize code and system performance
- **[Learning](../guides/PHASE_9_NEW_FEATURES_GUIDE.md#module-5-learning--recommendations)** - Get AI-powered recommendations
- **[Code Analysis](../guides/PHASE_9_NEW_FEATURES_GUIDE.md#module-6-code-analysis)** - Analyze code quality
- **[Documentation](../guides/PHASE_9_NEW_FEATURES_GUIDE.md#module-7-documentation-generation)** - Auto-generate project docs

## Documentation Files

### Reference Guides

- **[CLI_COMMANDS_REFERENCE.md](CLI_COMMANDS_REFERENCE.md)** - Complete command reference
  - All 28+ commands with syntax, parameters, and examples
  - Response format documentation
  - Common parameters and environment variables
  - Best practices and tips

- **[../guides/PHASE_9_NEW_FEATURES_GUIDE.md](../guides/PHASE_9_NEW_FEATURES_GUIDE.md)** - User guide for new features
  - Practical use cases for each module
  - Workflows and integration examples
  - Troubleshooting and tips
  - Real-world scenarios

### Related Documentation

- **[Architecture Guide](../architecture/ARCHITECTURE.md)** - System design and components
- **[API Reference](../API_REFERENCE.md)** - REST API endpoints
- **[Developer Guide](../DEVELOPER_GUIDE.md)** - Development practices
- **[Deployment Guide](../DEPLOYMENT.md)** - Deployment instructions

## Command Modules (Phase 9)

### Module 1: Conflict Detection (3.1)
Commands for identifying and resolving specification conflicts.
- `conflict analyze`
- `conflict list`
- `conflict resolve`
- `conflict ignore`

### Module 2: Workflow Orchestration (3.2)
Commands for automating multi-agent workflows.
- `workflow create`
- `workflow list`
- `workflow execute`

### Module 3: Security Monitoring (3.3)
Commands for monitoring and preventing security incidents.
- `security status`
- `security incidents`
- `security validate`
- `security trends`

### Module 4: Performance Monitoring (3.4)
Commands for optimizing system and code performance.
- `performance status`
- `performance agents`
- `performance cache`
- `performance bottlenecks`
- `performance reset`

### Module 5: Learning & Recommendations (3.5)
Commands for getting AI-powered improvement suggestions.
- `learning recommendations`
- `learning patterns`
- `learning session`
- `learning analyze`

### Module 6: Code Analysis (3.6)
Commands for analyzing code quality and identifying issues.
- `analyze code`
- `analyze file`
- `analyze project`
- `analysis issues`

### Module 7: Documentation Generation (3.7)
Commands for auto-generating project documentation.
- `docs generate readme`
- `docs generate api`
- `docs generate architecture`
- `docs generate all`

## Getting Started

### First Time Users

1. Start with the **[User Guide](../guides/PHASE_9_NEW_FEATURES_GUIDE.md#getting-started)**
2. Review **[Quick Start Workflow](../guides/PHASE_9_NEW_FEATURES_GUIDE.md#quick-start-workflow)**
3. Explore **[Use Cases](../guides/PHASE_9_NEW_FEATURES_GUIDE.md#use-cases)** for your needs

### Looking for Specific Commands

Use the **[CLI Commands Reference](CLI_COMMANDS_REFERENCE.md)** for:
- Complete command syntax
- All parameters and options
- Response format examples
- Common parameters

### Learning by Module

The **[User Guide](../guides/PHASE_9_NEW_FEATURES_GUIDE.md)** includes:
- Module overview
- Getting started for each module
- Use cases and scenarios
- Best practices
- Integration examples

## Command Response Format

All commands return standardized responses:

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

## Key Features

### Interactive Input
Commands that need parameters can prompt for user input:
```bash
conflict resolve              # Prompts for conflict ID and strategy
workflow create               # Prompts for workflow name and steps
docs generate readme          # Prompts for project description
```

### Filtering & Options
Most list commands support filtering:
```bash
conflict list open            # Filter by status
security incidents critical   # Filter by severity
performance bottlenecks 500    # Custom threshold
```

### Output Formats
Control command output:
```bash
command --format json         # JSON output
command --format table        # Table format
command --output file.json    # Save to file
```

## Common Workflows

### Daily Development
```bash
security validate             # Check new code
analyze code                  # Quick quality check
performance status            # Check system health
```

### Weekly Review
```bash
conflict list                 # Review specification conflicts
security incidents            # Review security issues
analyze project               # Project health check
performance agents            # Agent performance comparison
```

### Monthly Analysis
```bash
learning analyze              # Comprehensive improvements
security trends               # Trend analysis
performance reset all         # Reset and re-measure
```

### Pre-Release
```bash
analyze project ./src         # Full code review
security incidents            # Final security check
docs generate all             # Generate documentation
performance status            # Verify performance
```

## Troubleshooting

### Command Not Found
Ensure you're in a Socrates project directory and have the right permissions.
Check with: `status`

### No Data Available
Some commands require prior execution (performance, learning).
Run the basic commands first:
- Performance: `performance status`
- Learning: `learning session` or use agents first
- Security: `security validate`

### Slow Execution
Large project analysis can take time:
- Use file-specific analysis: `analyze file src/specific.py`
- Increase threshold: `performance bottlenecks 2000`
- Run off-peak hours

## Tips & Best Practices

### 1. Regular Monitoring
Schedule regular command execution:
```bash
# Daily: 9 AM
security status

# Weekly: Monday 10 AM
conflict list
analyze project ./src

# Monthly: 1st of month
learning analyze
security trends
```

### 2. Iterative Improvement
Use commands to measure improvements:
```bash
# Baseline
performance status

# Make improvements

# Verify
performance reset all
# Re-run operations
performance status
```

### 3. Team Collaboration
Share analysis results:
```bash
# Export analysis
learning analyze agent > recommendations.json

# Share with team
security incidents high > security_review.txt
```

### 4. Integration with CI/CD
Use in automated pipelines:
```yaml
# GitHub Actions
- run: socrates security validate ./src
- run: socrates analyze project ./src
```

## Advanced Topics

### Custom Workflows
Combine multiple commands:
```bash
#!/bin/bash
security validate code.py
analyze code code.py
performance bottlenecks 500
```

### Batch Operations
Process multiple files:
```bash
for file in src/**/*.py; do
  socrates analyze code "$file"
done
```

### Output Parsing
Parse JSON output for automation:
```bash
socrates learning recommendations agent --format json | jq '.data.recommendations'
```

## Support & Resources

### Documentation
- [CLI Commands Reference](CLI_COMMANDS_REFERENCE.md) - Complete reference
- [User Guide](../guides/PHASE_9_NEW_FEATURES_GUIDE.md) - Practical guide
- [Architecture](../architecture/ARCHITECTURE.md) - System design

### Learning Resources
- [Developer Guide](../DEVELOPER_GUIDE.md) - Development practices
- [Examples](../api/EXAMPLES.md) - Usage examples
- [CONTRIBUTING](../CONTRIBUTING.md) - Contributing guidelines

### Getting Help
- Check the relevant user guide section
- Review command examples
- Consult the CLI reference
- Open an issue on GitHub

## Version Information

**Phase 9 Release** includes:
- **28 new CLI commands** across 7 modules
- **72 integration & unit tests** (100% coverage)
- **Comprehensive documentation** (2 guides + reference)
- **Performance optimizations** (caching on 9 methods)
- **Security improvements** (7 new monitoring commands)

See [CHANGELOG](../../CHANGELOG.md) for complete Phase 9 details.

