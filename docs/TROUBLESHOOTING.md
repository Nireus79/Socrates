# Troubleshooting Guide

Solutions to common problems and error messages.

## Table of Contents

1. [Installation Issues](#installation-issues)
2. [Runtime Errors](#runtime-errors)
3. [API & Network Issues](#api--network-issues)
4. [Database Problems](#database-problems)
5. [Performance Issues](#performance-issues)
6. [Dialogue & Project Issues](#dialogue--project-issues)
7. [Debugging](#debugging)

---

## Installation Issues

### Python Not Found

**Error**:
```
Command 'python' not found
```

**Solutions**:

1. Use `python3` explicitly:
```bash
python3 Socrates.py
```

2. Create alias:
```bash
alias python=python3
```

3. Install Python:
   - Ubuntu: `sudo apt install python3.11`
   - macOS: `brew install python@3.11`
   - Windows: Download from python.org

### Virtual Environment Not Activating

**Error**:
```
(.venv) $ # prefix doesn't appear after activation
```

**Solutions**:

1. Linux/macOS:
```bash
source .venv/bin/activate
# Should show (.venv) prefix
```

2. Windows Command Prompt:
```cmd
.venv\Scripts\activate.bat
```

3. Windows PowerShell (if blocked):
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.venv\Scripts\Activate.ps1
```

### Module Not Found

**Error**:
```
ModuleNotFoundError: No module named 'anthropic'
```

**Solutions**:

1. Verify virtual environment is active:
```bash
which python  # Linux/macOS - should show .venv path
where python  # Windows - should show .venv path
```

2. Reinstall dependencies:
```bash
pip install -r requirements.txt --force-reinstall
```

3. Check pip:
```bash
pip --version
pip list | grep anthropic
```

### Pip Installation Fails

**Error**:
```
ERROR: Could not build wheels for chromadb
```

**Solutions**:

1. Update tools:
```bash
pip install --upgrade pip setuptools wheel
```

2. Install build tools:
   - Ubuntu: `sudo apt install build-essential python3-dev`
   - macOS: `brew install python3-dev`
   - Windows: Install Visual C++ Build Tools

3. Try again:
```bash
pip install -r requirements.txt
```

---

## Runtime Errors

### API Key Not Found

**Error**:
```
ValueError: API key required. Set ANTHROPIC_API_KEY environment variable
```

**Solutions**:

1. Set environment variable:
```bash
export ANTHROPIC_API_KEY="sk-ant-..."
```

2. Or use .env file:
```bash
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env
```

3. Or provide when prompted:
```
API Key: sk-ant-...
```

### Invalid API Key Format

**Error**:
```
anthropic.AuthenticationError: 401 Unauthorized
```

**Solutions**:

1. Check key format (starts with `sk-ant-`):
```bash
echo $ANTHROPIC_API_KEY
# Should print: sk-ant-...
```

2. Get new key:
   - Visit https://console.anthropic.com
   - Navigate to "API Keys"
   - Create new key
   - Copy and set as environment variable

3. Verify it's correct:
```bash
# Test with curl
curl -H "Authorization: Bearer sk-ant-..." \
     https://api.anthropic.com/health
```

### Import Errors

**Error**:
```
ImportError: cannot import name 'AgentOrchestrator'
```

**Solutions**:

1. Check module path:
```python
import sys
print(sys.path)  # Verify project in path
```

2. Install as editable:
```bash
pip install -e .
```

3. Run from project root:
```bash
cd /path/to/socrates
python Socrates.py
```

### Out of Memory

**Error**:
```
MemoryError: Unable to allocate 4.00 GiB
```

**Solutions**:

1. Reduce context length:
```python
config = ConfigBuilder("sk-ant-...") \
    .with_max_context_length(4000) \
    .build()
```

2. Use smaller model:
```python
.with_model("claude-haiku-4-5-20251001") \
```

3. Close other applications
4. Increase available RAM

---

## API & Network Issues

### Connection Timeout

**Error**:
```
ConnectTimeout: Attempt to connect to api.anthropic.com timed out
```

**Solutions**:

1. Check internet connection:
```bash
ping google.com
```

2. Check Anthropic API status:
   - https://status.anthropic.com

3. Try with longer timeout:
```python
config = ConfigBuilder("sk-ant-...") \
    .with_retry_delay(5.0) \
    .with_max_retries(5) \
    .build()
```

4. Use VPN if behind corporate proxy:
```bash
# Proxy configuration
pip install --proxy [user:passwd@]proxy:port ...
```

### Rate Limited

**Error**:
```
RateLimitError: 429 Too Many Requests
```

**Solutions**:

1. Wait before retrying (system auto-retries)
2. Reduce request frequency
3. Upgrade API plan at console.anthropic.com
4. Check usage:
```bash
/status  # In CLI
```

### SSL Certificate Error

**Error**:
```
SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]
```

**Solutions**:

1. Update certificates:
```bash
python -m certifi  # Verify path
```

2. Trust certificate:
```bash
export REQUESTS_CA_BUNDLE=/path/to/cert
```

3. Upgrade packages:
```bash
pip install --upgrade requests urllib3
```

### Network Behind Proxy

**Error**:
```
ProxyError: Unable to connect to proxy
```

**Solutions**:

1. Configure proxy environment:
```bash
export HTTP_PROXY=http://proxy:port
export HTTPS_PROXY=https://proxy:port
```

2. Or use pip config:
```bash
pip config set global.proxy "[user:passwd@]proxy:port"
```

---

## Database Problems

### Database Locked

**Error**:
```
sqlite3.OperationalError: database is locked
```

**Solutions**:

1. Close all running instances:
```bash
# Kill any running Socrates processes
pkill -f Socrates.py  # Linux/macOS
taskkill /IM python.exe /F  # Windows
```

2. Wait a moment and retry (locks self-clear)

3. Remove lock file (if exists):
```bash
rm ~/.socrates/.db.lock
```

### Database Corrupt

**Error**:
```
sqlite3.DatabaseError: database disk image is malformed
```

**Solutions**:

1. Backup and reset database:
```bash
cp ~/.socrates/projects.db ~/.socrates/projects.db.backup
rm ~/.socrates/projects.db
```

2. Restart Socrates (will recreate)

3. Recover backup if needed:
```bash
cp ~/.socrates/projects.db.backup ~/.socrates/projects.db
```

### Vector DB Issues

**Error**:
```
Expected where operator to be one of $gt, $gte, $lt, $lte, $ne, $eq, $in, $nin
```

**Solutions**:

1. Reset vector database:
```bash
rm -rf ~/.socrates/vector_db
python Socrates.py  # Will reinitialize
```

2. Reimport knowledge:
```bash
orchestrator.load_knowledge_base()
```

### Can't Find Project

**Error**:
```
Project not found: proj_123
```

**Solutions**:

1. List available projects:
```bash
/project list
```

2. Use exact project name
3. Check if project was archived:
```bash
/project restore <name>
```

---

## Performance Issues

### Slow Dialogue

**Problem**: System takes long to generate questions

**Solutions**:

1. Use faster model:
```python
.with_model("claude-haiku-4-5-20251001")
```

2. Reduce context length:
```python
.with_max_context_length(4000)
```

3. Check internet connection
4. Check system resources:
```bash
top  # Linux
Activity Monitor  # macOS
Task Manager  # Windows
```

### Slow Code Generation

**Problem**: Code takes very long to generate

**Solutions**:

1. Reduce project context:
   - Archive old conversations
   - Summarize dialogue history

2. Use Haiku model for drafts
3. Split into smaller modules
4. Check token usage:
```bash
/status
```

### Vector Search Slow

**Problem**: Knowledge base search takes too long

**Solutions**:

1. Reduce search results:
```python
results = vector_db.search_similar(
    query="...",
    top_k=3  # Lower value
)
```

2. Filter by project:
```python
results = vector_db.search_similar(
    query="...",
    project_id="proj_123"  # Filter reduces space
)
```

3. Reduce knowledge base size
4. Check disk I/O performance

### High CPU Usage

**Problem**: System uses too much CPU

**Solutions**:

1. Lower update frequency
2. Use smaller embedding model
3. Reduce concurrent operations
4. Check for background tasks:
```bash
/logs  # View logs
```

---

## Dialogue & Project Issues

### Questions Keep Repeating

**Error**: Same question asked multiple times

**Solutions**:

1. Advance phase when ready:
```bash
/advance
```

2. Reset if stuck:
```bash
/back
/continue
```

3. Check project phase:
```bash
/prompt  # Shows current phase
```

### Can't Load Project

**Error**: Project loads but data missing

**Solutions**:

1. Check project exists:
```bash
/project list
```

2. Verify project name spelling
3. Check database:
```bash
# Database should be at ~/.socrates/projects.db
ls -la ~/.socrates/projects.db
```

### Dialogue Won't Save

**Error**: Project changes not persisted

**Solutions**:

1. Manually save:
```bash
/done  # Complete phase
```

2. Check disk space:
```bash
df -h  # Linux/macOS
dir C:\ /s  # Windows
```

3. Verify write permissions:
```bash
touch ~/.socrates/test.txt
```

### Conflicts Not Detected

**Problem**: Contradictory requirements not flagged

**Solutions**:

1. Be more specific in responses:
   - "We need 10,000 users" is vague
   - "We need to support 10,000 daily active users" is clear

2. Explicitly state constraints:
```
Constraint: $50/month budget
Requirement: Support 10,000 users
```

3. Check conflict detection:
```bash
/status  # Should show conflicts if any
```

---

## Code Generation Issues

### Generated Code Incomplete

**Problem**: Missing functionality or empty output

**Solutions**:

1. Complete all dialogue phases:
```bash
/prompt  # Check phase progress
/advance  # Move to next phase
/code generate  # Try again
```

2. Ensure detailed requirements:
```bash
/continue  # Answer more questions
/code generate  # Regenerate
```

3. Check context:
```bash
/prompt  # View entire project spec
```

### Syntax Errors in Generated Code

**Problem**: Generated code has Python/JS errors

**Solutions**:

1. Specify language preference:
   - During dialogue: Mention your language
   - Or: `ConfigBuilder().with_model(...)`

2. Request simpler version:
```bash
/code generate  # Retry
```

3. Manually fix and report issue

### Code Doesn't Match Requirements

**Problem**: Generated code doesn't match specifications

**Solutions**:

1. Review project specification:
```bash
/prompt
```

2. Add clarifications:
```bash
/note add "Need JWT authentication, not OAuth"
/code generate  # Regenerate
```

3. Provide examples in dialogue

---

## Debugging

### Enable Debug Mode

```bash
/debug on
```

Shows detailed logs including:
- API calls
- Token usage
- Database operations
- Event emissions
- Knowledge searches

### View Logs

```bash
# Last 20 lines
/logs

# Last 50 lines
/logs 50

# From file
tail -f ~/.socrates/logs/socratic.log
```

### Common Log Messages

**DEBUG messages indicate**:
- What's being processed
- Database queries
- API calls
- Event emissions

**INFO messages indicate**:
- Major operations
- Phase changes
- Project saves
- Code generation

**WARNING messages indicate**:
- Deprecated features
- Unusual conditions
- High token usage
- Performance issues

**ERROR messages indicate**:
- Failed operations
- Connection problems
- Invalid input
- System failures

### Check System Status

```bash
/status
```

Shows:
- Debug mode: On/Off
- Log file location
- Current user/project
- Token usage
- API health

### Test API Connection

```python
from socratic_system.clients import ClaudeClient
from socratic_system.config import ConfigBuilder

config = ConfigBuilder("sk-ant-...").build()
client = ClaudeClient(config)

# This will test the API
response = client.client.messages.create(
    model=config.claude_model,
    max_tokens=100,
    messages=[{"role": "user", "content": "Hello"}]
)
print(f"API OK: {response.usage}")
```

### Verify Installation

```bash
# Check Python
python --version

# Check packages
pip list | grep -E "anthropic|chromadb|sentence-transformers"

# Check directories
ls -la ~/.socrates/
ls -la ~/.socrates/logs/

# Check permissions
touch ~/.socrates/test.txt
rm ~/.socrates/test.txt
```

---

## Getting Help

### Before Reporting Issue

1. **Enable debug mode**:
```bash
/debug on
/logs 100
```

2. **Collect information**:
```bash
python --version
pip list
echo $ANTHROPIC_API_KEY | head -c 10  # Just first 10 chars
```

3. **Try latest version**:
```bash
pip install --upgrade -r requirements.txt
```

### When Reporting Bug

Include:
- Error message (full traceback)
- Steps to reproduce
- Debug logs (last 50 lines)
- System info (Python version, OS)
- Configuration (omit API key)

**Format**:
```
**Error**:
[Full error message and traceback]

**Steps to reproduce**:
1. [Step 1]
2. [Step 2]

**Logs**:
[Relevant log lines]

**System**:
- Python: [version]
- OS: [OS and version]
- Packages: [key versions]
```

### Resources

- [INSTALLATION.md](INSTALLATION.md) - Setup issues
- [CONFIGURATION.md](CONFIGURATION.md) - Configuration problems
- [USER_GUIDE.md](USER_GUIDE.md) - Usage questions
- [API_REFERENCE.md](API_REFERENCE.md) - API issues
- [ARCHITECTURE.md](ARCHITECTURE.md) - Design questions

---

## Quick Diagnosis

### System won't start

```
✓ Check API key: echo $ANTHROPIC_API_KEY
✓ Check Python: python --version
✓ Check packages: pip list | grep anthropic
✓ Check data dir: ls ~/.socrates/
✓ Enable debug: /debug on
```

### Dialogue stuck

```
✓ Check phase: /prompt
✓ Try hint: /hint
✓ Go back: /back
✓ Advance: /advance
```

### Code generation fails

```
✓ Complete all phases: /prompt
✓ Answer all questions: /continue
✓ Check requirements: /prompt
✓ Try again: /code generate
```

### Network issues

```
✓ Check internet: ping google.com
✓ Check API: curl https://api.anthropic.com
✓ Check logs: /logs 20
✓ Try VPN if needed
```

---

**Last Updated**: December 2025
**Version**: 7.0
