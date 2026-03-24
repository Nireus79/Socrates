# Phase 9: New Features User Guide

Comprehensive guide to using the new features introduced in Phase 9 of Socrates, including conflict detection, workflow orchestration, security monitoring, performance optimization, and more.

## Overview

Phase 9 introduces **7 major feature modules** with **28 new CLI commands**, providing comprehensive tools for:

- **Conflict Detection & Resolution** - Identify and resolve specification conflicts
- **Workflow Orchestration** - Automate multi-agent workflows
- **Security Monitoring** - Track and prevent security incidents
- **Performance Analysis** - Optimize code execution and caching
- **Learning Recommendations** - Get AI-powered improvement suggestions
- **Code Quality Analysis** - Analyze code for issues and patterns
- **Documentation Generation** - Auto-generate project documentation

---

## Getting Started

### Prerequisites
- Socrates CLI installed and configured
- Valid API key set up
- A project loaded or ready to create

### Quick Start Workflow

```bash
# 1. Create or load a project
project load my_project

# 2. Check project health
status

# 3. Analyze for conflicts
conflict analyze

# 4. Run security validation
security status

# 5. Check performance
performance status

# 6. Get recommendations
learning recommendations my_agent
```

---

## Module 1: Conflict Detection & Resolution

Identify and manage conflicts in project specifications.

### Use Cases

**Identifying Specification Conflicts**
When you have multiple agents with potentially conflicting requirements or specifications:

```bash
conflict analyze
```

Output shows:
- Conflicting requirements
- Affected specification areas
- Severity levels
- Suggested resolutions

**Managing Known Conflicts**
View and track all conflicts in your project:

```bash
conflict list
```

Filter by status:
```bash
conflict list open          # Only unresolved conflicts
conflict list resolved      # Only resolved conflicts
```

**Resolving Conflicts**
When multiple solutions exist, use consensus or voting:

```bash
conflict resolve conflict_123 voting
```

**Tracking Acknowledged Issues**
Some conflicts may not need resolution but should be tracked:

```bash
conflict ignore conflict_123 "Acceptable architectural trade-off"
```

### Best Practices

1. **Regular Analysis**: Run `conflict analyze` during architecture reviews
2. **Document Decisions**: Use reason parameters to document why conflicts were ignored
3. **Team Consensus**: Use voting strategy for team decisions
4. **Progressive Resolution**: Resolve high-severity conflicts first

### Common Scenarios

**Scenario 1: Architecture Design Conflict**
```bash
# Team proposes different architectures
conflict analyze

# Team votes on preferred approach
conflict resolve conflict_456 voting

# Document architectural decision
conflict ignore conflict_456 "Monolithic architecture selected by team vote"
```

**Scenario 2: Technology Stack Decision**
```bash
# Different teams prefer different technologies
conflict analyze

# Use consensus strategy for critical decision
conflict resolve conflict_789 consensus

# Track decision with timestamp
conflict list resolved
```

---

## Module 2: Workflow Orchestration

Automate complex multi-agent workflows with automatic retry and error handling.

### Creating Workflows

Define a workflow with sequential agent steps:

```bash
workflow create data_pipeline
```

Interactive prompts:
- Name: `data_pipeline`
- Steps: `validator, transformer, analyzer, reporter`
- Description: `Complete data processing pipeline`

### Executing Workflows

Run a workflow with automatic error handling:

```bash
workflow execute wf_data_pipeline
```

Features:
- Automatic retry (3 attempts)
- Progress tracking
- Detailed error reporting
- Execution metrics

### Monitoring Workflow Execution

```bash
workflow list
```

Shows:
- Workflow names and IDs
- Number of steps
- Last execution status
- Success/failure counts

### Advanced Usage

**Chaining Workflows**
```bash
# Execute data validation workflow
workflow execute wf_validate

# Then execute transformation workflow
workflow execute wf_transform

# Finally execute reporting workflow
workflow execute wf_report
```

**Error Handling**
Workflows automatically retry failed steps:
- Step 1 fails → Retry (2 attempts remaining)
- All attempts exhausted → Error logged
- Previous steps' results preserved

### Use Cases

**Data Processing Pipeline**
```
Input Data → Validator → Transformer → Analyzer → Reporter → Output
```

**Code Review Workflow**
```
Code Submission → Analyzer → Security Check → Performance Review → Approval
```

**Deployment Workflow**
```
Build → Test → Security Scan → Performance Test → Deploy
```

### Best Practices

1. **Single Responsibility**: Each workflow should have a clear purpose
2. **Error Handling**: Design workflows to handle common failure cases
3. **Monitoring**: Check `workflow list` regularly to track execution history
4. **Documentation**: Add meaningful descriptions to workflows

---

## Module 3: Security Monitoring

Monitor and prevent security incidents in your codebase.

### Checking Security Status

Get overall security posture:

```bash
security status
```

Output:
- Overall status (Secure/Alert)
- Incident counts by severity
- Recommended actions

### Validating Input & Code

Scan code or input for security vulnerabilities:

```bash
security validate
```

Paste your code, and analysis covers:
- SQL injection vulnerabilities
- Cross-site scripting (XSS) risks
- Command injection vectors
- Prompt injection attacks
- Code quality issues

**Security Score**: 0-100 (higher is better)

### Viewing Security Incidents

List all recorded incidents:

```bash
security incidents
```

Filter by severity:
```bash
security incidents critical    # Only critical issues
security incidents high        # Only high-severity issues
```

### Security Trends

Understand incident patterns over time:

```bash
security trends
```

Shows:
- Most common incident types
- Frequency trends
- Historical data
- Recommended focus areas

### Security Workflow

**Continuous Security Monitoring**
```bash
# Daily check
security status

# Weekly deep dive
security incidents
security trends

# When adding new code
security validate

# Review critical issues immediately
security incidents critical
```

### Use Cases

**Pre-Deployment Security Check**
```bash
security status           # Ensure no critical incidents
security incidents       # Review all incidents
security validate        # Scan new deployment code
```

**Code Review Integration**
```bash
# For each code change
security validate <new_code>

# Track improvements
security incidents high
security incidents medium
```

**Audit Trail**
```bash
# Regular security audits
security incidents
security trends
```

### Best Practices

1. **Regular Validation**: Use `security validate` for all new code
2. **Monitor Trends**: Review `security trends` weekly
3. **Quick Response**: Act on critical incidents immediately
4. **Documentation**: Document how each critical issue was resolved
5. **Prevention**: Use incident patterns to improve development processes

---

## Module 4: Performance Monitoring & Optimization

Identify and fix performance bottlenecks.

### Checking Performance Status

Get overall performance metrics:

```bash
performance status
```

Shows:
- Total function calls
- Average execution time
- Cache hit rate
- Cache utilization

### Per-Agent Performance

Identify which agents are slowest:

```bash
performance agents
```

Output:
- Agent names
- Call counts
- Average duration
- Performance comparison

### Cache Performance

Monitor cache effectiveness:

```bash
performance cache
```

Metrics:
- Cache size
- Hit rate percentage
- Entry count
- Efficiency score

### Finding Bottlenecks

Identify operations slower than a threshold:

```bash
performance bottlenecks 500      # Operations > 500ms
performance bottlenecks 1000     # Operations > 1 second
```

Shows slowest operations with:
- Operation name
- Duration
- Frequency
- Performance impact

### Performance Optimization Workflow

**Step 1: Establish Baseline**
```bash
performance status    # Record current metrics
```

**Step 2: Identify Issues**
```bash
performance bottlenecks 500      # Find slow operations
performance agents               # Find slow agents
```

**Step 3: Implement Fixes**
Make code optimizations or caching improvements

**Step 4: Reset and Measure**
```bash
performance reset all            # Clear old data
# Run workload again
performance status               # Compare new metrics
```

### Use Cases

**Optimization for Production**
```bash
# Measure current performance
performance status

# Identify bottlenecks
performance bottlenecks 200      # 200ms threshold for production

# Optimize slow operations
# (make code changes)

# Verify improvement
performance reset all
# Run same operations
performance status
```

**Cache Tuning**
```bash
# Check cache efficiency
performance cache

# If hit rate is low (< 80%):
# - Increase cache size
# - Review cache strategy

# Verify improvements
performance cache
```

**Agent Performance Comparison**
```bash
# Which agents are slowest?
performance agents

# Optimize top 3 slowest agents

# Verify improvements
performance agents
```

### Best Practices

1. **Regular Monitoring**: Check `performance status` weekly
2. **Threshold Analysis**: Identify appropriate bottleneck thresholds for your use case
3. **Gradual Optimization**: Optimize highest-impact items first
4. **Measurement**: Always measure before and after optimization
5. **Cache Tuning**: Aim for >85% cache hit rate in production

---

## Module 5: Learning & Recommendations

Get AI-powered recommendations for improving agent performance.

### Getting Recommendations

Request improvement recommendations for an agent:

```bash
learning recommendations code_generator
```

Shows:
- Recommended improvements
- Confidence scores
- Expected impact level
- Implementation details

### Analyzing Patterns

Understand agent behavior patterns:

```bash
learning patterns code_generator usage
```

Pattern types:
- **usage**: How the agent is typically used
- **error**: Common error patterns
- **performance**: Performance trends
- **all**: All patterns

### Starting a Learning Session

Track interactions for learning:

```bash
learning session user_123
```

Sessions enable:
- Detailed interaction logging
- Pattern analysis
- Recommendation generation
- Learning history

### Comprehensive Analysis

Get complete learning insights:

```bash
learning analyze code_generator
```

Provides:
- Pattern summary
- Error analysis
- Performance assessment
- Prioritized recommendations

### Learning Workflow

**Continuous Improvement Cycle**
```bash
# Start tracking session
learning session dev_123

# Use agents and tools
# (perform normal work)

# Analyze patterns
learning patterns code_generator

# Get recommendations
learning recommendations code_generator

# Implement improvements
# (make code/config changes)

# Verify improvement
learning analyze code_generator
```

### Use Cases

**Agent Performance Improvement**
```bash
# Analyze underperforming agent
learning recommendations slow_agent

# Understand why it's slow
learning patterns slow_agent performance

# Implement suggested improvements

# Verify improvements
learning analyze slow_agent
```

**Error Prevention**
```bash
# Identify error patterns
learning patterns validator error

# Get recommendations to fix
learning recommendations validator

# Implement error handling improvements
```

**Team Training**
```bash
# Analyze team member's work
learning patterns team_member usage

# Get recommendations for skill improvement
learning recommendations team_member

# Share recommendations with team
```

### Best Practices

1. **Regular Analysis**: Analyze agent performance monthly
2. **Pattern Understanding**: Review patterns before optimizing
3. **Confidence Thresholds**: Prioritize recommendations with >85% confidence
4. **Implementation**: Implement high-impact recommendations first
5. **Feedback Loop**: Re-analyze after implementing changes

---

## Module 6: Code Analysis

Analyze code quality and identify issues automatically.

### Quick Code Analysis

Analyze a code snippet or file:

```bash
analyze code                  # Paste code interactively
analyze code path/to/file.py  # Analyze a file
```

Output:
- Quality score (0-100)
- Issue count and categories
- Design patterns detected
- Recommended improvements

### File Analysis

Deep dive into a single file:

```bash
analyze file src/main.py
```

Detailed output:
- Quality score
- Issues with locations
- Severity breakdown
- Fix suggestions

### Project-Wide Analysis

Analyze entire codebase:

```bash
analyze project ./src
```

Shows:
- Files analyzed
- Total issues
- Average quality score
- Top files needing attention

### Issue Detection

Detect specific issue types:

```bash
# Code smells (maintainability issues)
analysis issues smells

# Complexity problems (hard-to-understand code)
analysis issues complexity

# Design patterns (good practices found)
analysis issues patterns
```

### Analysis Workflow

**Pre-Commit Code Review**
```bash
# Check code before commit
analyze code path/to/new_file.py

# If issues found, fix them
# Re-analyze to verify fix
analyze code path/to/new_file.py
```

**Project Health Check**
```bash
# Weekly analysis
analyze project ./src

# Focus on files with lowest quality
analyze file src/problem_file.py

# Implement improvements
# Re-analyze to confirm
analyze project ./src
```

### Use Cases

**Code Quality Improvement**
```bash
# Initial scan
analyze project ./src

# Focus on top issues
analysis issues smells

# Fix code quality issues

# Verify improvements
analyze project ./src
```

**Performance Analysis**
```bash
# Find performance issues
analysis issues complexity

# Review complex functions
analyze file src/slow_function.py

# Simplify and optimize
# Verify improvements
analyze code src/slow_function.py
```

**Learning from Patterns**
```bash
# Discover design patterns in codebase
analysis issues patterns

# Learn from good examples
# Apply patterns to new code
```

### Best Practices

1. **Early Analysis**: Analyze code early in development
2. **Iterative Improvement**: Fix issues incrementally
3. **Focus on Severity**: Address critical issues first
4. **Learn from Patterns**: Use identified patterns in new code
5. **Regular Reviews**: Analyze project quarterly

---

## Module 7: Documentation Generation

Auto-generate project documentation.

### Creating README

Generate project README automatically:

```bash
docs generate readme MyProject
```

Interactive input:
- Project description
- Key features (comma-separated)
- Installation instructions
- Usage examples

**Generated Content:**
- Project overview
- Feature list
- Installation guide
- Quick start
- Usage examples
- Contributing info
- License section

### API Documentation

Generate documentation from code:

```bash
docs generate api src/api/main.py
```

Extracts:
- Classes and methods
- Function signatures
- Parameter documentation
- Return types
- Usage examples

### Architecture Documentation

Document system architecture:

```bash
docs generate architecture core ui database orchestration
```

Covers:
- Module overview
- Component relationships
- Data flow
- Integration points
- Design patterns

### Complete Documentation Suite

Generate all documentation types:

```bash
docs generate all MyProject ./src
```

Creates:
- README.md
- API documentation
- Architecture guide
- Installation guide
- Configuration guide
- Contributing guidelines

### Documentation Workflow

**Initial Project Setup**
```bash
# Generate complete documentation suite
docs generate all MyProject ./src

# Review and customize if needed
# Commit to repository
```

**During Development**
```bash
# Update README with new features
docs generate readme MyProject

# Regenerate API docs for new modules
docs generate api src/api/new_feature.py
```

**Before Release**
```bash
# Verify all documentation is current
docs generate all MyProject ./src

# Review for accuracy
# Update any manual sections
```

### Best Practices

1. **Auto-Generate**: Use auto-generation as starting point
2. **Manual Review**: Review generated docs for accuracy
3. **Keep Updated**: Regenerate when code changes significantly
4. **Format**: Ensure consistent formatting with rest of docs
5. **Examples**: Add real-world usage examples manually

---

## Integration Examples

### Complete Project Workflow

```bash
# 1. Create project
project create my_app

# 2. Check for conflicts
conflict analyze
conflict list

# 3. Set up workflows
workflow create validation_pipeline
workflow create deployment_pipeline

# 4. Analyze security
security status
security incidents

# 5. Check performance baseline
performance status

# 6. Get recommendations
learning recommendations my_agent
learning analyze my_agent

# 7. Analyze code quality
analyze project ./src

# 8. Generate documentation
docs generate all my_app ./src
```

### Security-Focused Workflow

```bash
# Initial security assessment
security status
security incidents

# Validate new code
security validate

# Review trends
security trends

# Fix critical issues
# (implement fixes)

# Re-validate
security status
```

### Performance Optimization Workflow

```bash
# Measure baseline
performance status
performance agents

# Find slow operations
performance bottlenecks 500

# Get recommendations
learning recommendations slow_agent

# Implement improvements
# (make code changes)

# Verify improvements
performance reset all
# Re-run operations
performance status

# Measure improvement
performance agents
```

---

## Troubleshooting

### Commands Not Found

**Issue**: Command returns "not available" error

**Solution**: Ensure required library is installed:
```bash
# Check status
status

# Verify all libraries enabled
info
```

### No Data Available

**Issue**: Command shows "No data available"

**Possible Causes:**
- Command hasn't been run yet (performance, learning)
- No incidents/conflicts recorded (security, conflict)
- Project not fully loaded

**Solution:**
- Run relevant commands first (e.g., `security validate` before `security incidents`)
- Ensure project is properly loaded with `project load`

### Slow Command Execution

**Issue**: Command takes too long to run

**Solution:**
- `analyze project` can be slow on large codebases
- Use file-specific analysis: `analyze file src/specific_file.py`
- Check `performance status` to see if system is busy

---

## Tips & Tricks

### Batch Processing

Run multiple analyses with a script:
```bash
#!/bin/bash
security validate code1.py
security validate code2.py
analyze code code3.py
analyze code code4.py
```

### Filtering Results

Use output format options:
```bash
conflict list | grep "critical"
performance bottlenecks 1000 --format json
```

### Automation

Schedule regular checks:
```bash
# Daily security check
0 9 * * * security status

# Weekly performance review
0 10 * * 1 performance status

# Monthly project analysis
0 10 1 * * analyze project ./src
```

### Integration with CI/CD

Use commands in CI/CD pipelines:
```yaml
# GitHub Actions example
- name: Security Validation
  run: socrates security validate ./src

- name: Code Analysis
  run: socrates analyze project ./src

- name: Performance Check
  run: socrates performance status
```

---

## Related Resources

- [CLI Commands Reference](../commands/CLI_COMMANDS_REFERENCE.md) - Detailed command reference
- [Architecture Guide](../architecture/ARCHITECTURE.md) - System architecture
- [Developer Guide](../DEVELOPER_GUIDE.md) - Development practices
- [API Reference](../API_REFERENCE.md) - REST API documentation

