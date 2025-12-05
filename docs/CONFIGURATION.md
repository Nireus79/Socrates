# Configuration Guide

Comprehensive guide to configuring the Socratic RAG System for different use cases.

## Quick Configuration

### Minimal Configuration

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
python Socrates.py
```

Uses all defaults. Everything works locally.

### Recommended Configuration

```bash
export ANTHROPIC_API_KEY="sk-ant-..."
export SOCRATES_LOG_LEVEL="INFO"
export SOCRATES_DATA_DIR="~/.socrates"
python Socrates.py
```

---

## Environment Variables

All configuration via environment:

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `ANTHROPIC_API_KEY` | Claude API key (required) | None | `sk-ant-...` |
| `CLAUDE_MODEL` | Claude model to use | `claude-sonnet-4-5-20250929` | `claude-opus-4-1-20250805` |
| `SOCRATES_DATA_DIR` | Data storage location | `~/.socrates` | `/data/socrates` |
| `SOCRATES_LOG_LEVEL` | Logging level | `INFO` | `DEBUG` / `WARNING` / `ERROR` |
| `SOCRATES_LOG_FILE` | Log file path | `{DATA_DIR}/logs/socratic.log` | `/var/log/socratic.log` |

### Setting Environment Variables

**Linux/macOS**:
```bash
# Temporary (this session)
export ANTHROPIC_API_KEY="sk-ant-..."
export SOCRATES_LOG_LEVEL="DEBUG"

# Permanent (add to ~/.bashrc, ~/.zshrc)
echo 'export ANTHROPIC_API_KEY="sk-ant-..."' >> ~/.bashrc
source ~/.bashrc
```

**Windows Command Prompt**:
```cmd
setx ANTHROPIC_API_KEY sk-ant-...
setx SOCRATES_LOG_LEVEL DEBUG
# Restart terminal
```

**Windows PowerShell**:
```powershell
[Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "sk-ant-...", "User")
[Environment]::SetEnvironmentVariable("SOCRATES_LOG_LEVEL", "DEBUG", "User")
# Restart PowerShell
```

---

## Programmatic Configuration

### Using ConfigBuilder

```python
from socratic_system.config import ConfigBuilder
from pathlib import Path

config = ConfigBuilder("sk-ant-...") \
    .with_data_dir(Path("/custom/data")) \
    .with_model("claude-opus-4-1-20250805") \
    .with_log_level("DEBUG") \
    .with_max_retries(5) \
    .with_token_warning_threshold(0.7) \
    .build()

from socratic_system.orchestration import AgentOrchestrator
orchestrator = AgentOrchestrator(config)
```

### Using SocratesConfig

```python
from socratic_system.config import SocratesConfig
from pathlib import Path

config = SocratesConfig(
    api_key="sk-ant-...",
    claude_model="claude-opus-4-1-20250805",
    data_dir=Path("/data"),
    log_level="DEBUG",
    max_context_length=8000,
    max_retries=5,
    retry_delay=2.0,
    token_warning_threshold=0.7,
    session_timeout=7200,
    custom_knowledge=["Knowledge 1", "Knowledge 2"]
)

orchestrator = AgentOrchestrator(config)
```

### From Dictionary

```python
config = SocratesConfig.from_dict({
    "api_key": "sk-ant-...",
    "data_dir": "/data",
    "log_level": "DEBUG"
})
```

---

## Configuration Parameters

### API & Model Configuration

**api_key** (required)
- Claude API key
- Get from [console.anthropic.com](https://console.anthropic.com)
- Pattern: `sk-ant-...`

**claude_model**
- Default: `claude-sonnet-4-5-20250929`
- Options:
  - `claude-opus-4-1-20250805` - Most capable, higher cost
  - `claude-sonnet-4-5-20250929` - Balanced (default)
  - `claude-haiku-4-5-20251001` - Fast, lower cost

**embedding_model**
- Default: `all-MiniLM-L6-v2`
- Used for generating vector embeddings
- Must be compatible with Sentence Transformers

### Storage Configuration

**data_dir**
- Default: `~/.socrates`
- Location for all persistent data
- Must have write permissions
- Required space: ~1GB minimum

**projects_db_path**
- Default: `{data_dir}/projects.db`
- SQLite database for projects/users
- Auto-created if missing

**vector_db_path**
- Default: `{data_dir}/vector_db`
- ChromaDB storage directory
- Auto-created if missing

**knowledge_base_path**
- Default: Auto-detected from package
- Path to JSON knowledge base file

### Behavior Configuration

**max_context_length**
- Default: `8000`
- Max tokens in Claude prompts
- Adjust based on model context window
- Range: 1000-100000

**max_retries**
- Default: `3`
- Retry API calls on failure
- Exponential backoff applied
- Range: 1-10

**retry_delay**
- Default: `1.0`
- Initial delay between retries (seconds)
- Increases exponentially
- Range: 0.1-10.0

**token_warning_threshold**
- Default: `0.8` (80%)
- Warn when token usage exceeds this %
- Helps control API costs
- Range: 0.1-1.0

**session_timeout**
- Default: `3600` (1 hour)
- Inactivity timeout (seconds)
- Range: 60-86400

### Logging Configuration

**log_level**
- Options: `DEBUG`, `INFO`, `WARNING`, `ERROR`
- Default: `INFO`
- `DEBUG` - Detailed operation logs
- `INFO` - Important events (recommended)
- `WARNING` - Warnings and errors only
- `ERROR` - Only errors

**log_file**
- Default: `{data_dir}/logs/socratic.log`
- Set to `None` for console only
- Auto-rotates at 10MB

### Knowledge Configuration

**custom_knowledge**
- Default: `[]`
- List of custom knowledge strings
- Loaded into vector DB on startup
- Useful for company standards, guidelines

**knowledge_base_path**
- Path to JSON knowledge base
- Auto-detected from package
- Can be overridden for custom KB

---

## Common Configuration Scenarios

### Development

```python
config = ConfigBuilder("sk-ant-...") \
    .with_data_dir(Path("./data")) \
    .with_log_level("DEBUG") \
    .with_token_warning_threshold(0.5) \
    .build()
```

**Benefits**:
- Local data directory
- Detailed logs for debugging
- Warnings at 50% token usage

### Production

```python
config = ConfigBuilder("sk-ant-...") \
    .with_data_dir(Path("/var/socrates")) \
    .with_log_level("WARNING") \
    .with_log_file(Path("/var/log/socratic.log")) \
    .with_max_retries(5) \
    .with_token_warning_threshold(0.9) \
    .build()
```

**Benefits**:
- Shared data directory
- Minimal logging (performance)
- Robust retry logic
- Cost monitoring

### Enterprise

```python
config = ConfigBuilder("sk-ant-...") \
    .with_data_dir(Path("/shared/socrates")) \
    .with_log_level("INFO") \
    .with_max_retries(10) \
    .with_token_warning_threshold(0.7) \
    .with_custom_knowledge([
        "Company coding standards...",
        "Architecture guidelines...",
        "Security best practices..."
    ]) \
    .build()
```

**Benefits**:
- Shared infrastructure
- Custom company knowledge
- Robust error handling
- Detailed logging

### Research/Experimentation

```python
config = ConfigBuilder("sk-ant-...") \
    .with_model("claude-opus-4-1-20250805") \
    .with_max_context_length(20000) \
    .with_log_level("DEBUG") \
    .with_token_warning_threshold(1.0) \
    .build()
```

**Benefits**:
- Most capable model
- Large context for complex tasks
- Full logging visibility
- No token warnings

---

## Data Directory Structure

```
~/.socrates/
├── projects.db                  # SQLite database
│   └── Tables: projects, users, project_notes
├── vector_db/                   # ChromaDB storage
│   ├── chroma.sqlite3           # Metadata
│   └── {collection_uuid}/       # Vector data
├── logs/
│   └── socratic.log             # Application log
└── [imported_documents]/        # Document cache (optional)
```

### Directory Permissions

**Linux/macOS**:
```bash
chmod 700 ~/.socrates        # Owner access only
chmod 600 ~/.socrates/*.db   # Restrict database files
```

**Windows**:
```cmd
# Use NTFS permissions for restricted access
icacls "%USERPROFILE%\.socrates" /grant:r "%USERNAME%:F" /inheritance:r
```

---

## Model Selection Guide

### By Use Case

**Code Generation** (recommended):
- Use: `claude-sonnet-4-5-20250929`
- Reason: Good balance of capability and cost

**Complex Analysis**:
- Use: `claude-opus-4-1-20250805`
- Reason: Most capable, handles complex logic
- Cost: ~2x Sonnet

**Budget-Conscious**:
- Use: `claude-haiku-4-5-20251001`
- Reason: Faster, lower cost
- Limitation: May miss nuances

**Balanced (Default)**:
- Use: `claude-sonnet-4-5-20250929`
- Works well for most projects

### Model Capabilities Comparison

| Model | Speed | Reasoning | Cost | Best For |
|-------|-------|-----------|------|----------|
| Haiku | Fast | Good | Low | Dialogue, simple tasks |
| Sonnet | Medium | Very Good | Medium | General use (default) |
| Opus | Slow | Excellent | High | Complex code, analysis |

---

## Performance Tuning

### Token Optimization

```python
config = ConfigBuilder("sk-ant-...") \
    .with_max_context_length(4000) \  # Reduce context
    .with_model("claude-haiku-4-5-20251001") \  # Faster model
    .build()
```

**Result**: Faster responses, lower cost, simpler tasks

### Vector Database Performance

```python
# Larger top_k = more search results but slower
results = vector_db.search_similar(
    query="...",
    top_k=3  # Lower value = faster search
)
```

### Concurrent Operations

```python
# Use async methods for parallel requests
import asyncio

tasks = [
    orchestrator.process_request_async('agent1', req1),
    orchestrator.process_request_async('agent2', req2),
    orchestrator.process_request_async('agent3', req3)
]

results = asyncio.run(asyncio.gather(*tasks))
```

---

## Multi-User Setup

### Shared Data Directory

```python
config = ConfigBuilder("sk-ant-...") \
    .with_data_dir(Path("/shared/socrates")) \
    .build()
```

**Considerations**:
- Ensure directory has correct permissions
- SQLite file locking handled automatically
- Each user has own projects and credentials

### Docker Deployment

```dockerfile
FROM python:3.11
WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY socratic_system/ socratic_system/
COPY Socrates.py .

ENV ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
ENV SOCRATES_DATA_DIR=/data

VOLUME ["/data"]
CMD ["python", "Socrates.py"]
```

Run:
```bash
docker run -it \
  -e ANTHROPIC_API_KEY="sk-ant-..." \
  -v /shared/socrates:/data \
  socratic-rag
```

---

## Cost Management

### Monitor Token Usage

```bash
/status  # View token usage and costs
```

**Set warning threshold**:
```python
config.token_warning_threshold = 0.5  # Warn at 50%
```

**View logs**:
```bash
grep TOKEN_USAGE ~/.socrates/logs/socratic.log
```

### Reduce Costs

1. **Use Haiku model** for simple tasks
2. **Reduce max_context_length** for shorter prompts
3. **Limit knowledge base size**
4. **Cache generated code** to avoid regeneration
5. **Monitor token usage** regularly

---

## Logging Configuration

### Log Levels Explained

**DEBUG**
- Shows all operations
- Useful for troubleshooting
- High performance impact
- ~10x more logs than INFO

**INFO** (default)
- Shows important events
- Good for monitoring
- Minimal performance impact
- Recommended for production

**WARNING**
- Shows warnings and errors
- Good for minimal logging
- Low performance impact

**ERROR**
- Shows only errors
- Minimal logging
- Use only if debugging is not needed

### Viewing Logs

```bash
# Last 20 lines
tail ~/.socrates/logs/socratic.log

# Last 50 lines
tail -n 50 ~/.socrates/logs/socratic.log

# Follow logs (live)
tail -f ~/.socrates/logs/socratic.log

# Search logs
grep "CODE_GENERATED" ~/.socrates/logs/socratic.log
grep "CONFLICT_DETECTED" ~/.socrates/logs/socratic.log

# Count log entries by level
grep -c "\[DEBUG\]" ~/.socrates/logs/socratic.log
grep -c "\[INFO\]" ~/.socrates/logs/socratic.log
```

### Log Rotation

Logs auto-rotate at 10MB. Old logs are named `socratic.log.1`, `socratic.log.2`, etc.

---

## Security Configuration

### API Key Protection

**Never commit API keys**:
```bash
# Good - use environment variable
export ANTHROPIC_API_KEY="sk-ant-..."

# Good - use .env file (add to .gitignore)
echo "ANTHROPIC_API_KEY=sk-ant-..." > .env

# BAD - don't commit to git
# echo 'export ANTHROPIC_API_KEY="..."' >> script.sh  ❌
```

### Database Security

**Local deployment**:
```bash
chmod 700 ~/.socrates        # Owner only
chmod 600 ~/.socrates/*.db   # No read for others
```

**Shared deployment**:
```bash
# Use file permissions or volume mounts
docker run -v /secure/path:/data socratic-rag
```

### Passcode Security

- Hashed with SHA256
- Never stored in plaintext
- Set strong passcodes

---

## Troubleshooting Configuration

### API Key Not Working

```bash
# Verify key format
echo $ANTHROPIC_API_KEY  # Should start with sk-ant-

# Test with curl
curl -H "Authorization: Bearer $ANTHROPIC_API_KEY" \
     https://api.anthropic.com/health
```

### Data Directory Issues

```bash
# Check permissions
ls -ld ~/.socrates
ls -la ~/.socrates/

# Check disk space
df -h ~/.socrates

# Fix permissions
chmod 700 ~/.socrates
chmod 600 ~/.socrates/*.db
```

### Wrong Log Location

```python
# Check config
print(config.log_file)

# Verify directory exists
mkdir -p ~/.socrates/logs

# Check write permissions
touch ~/.socrates/logs/test.log
```

---

## Advanced Configuration

### Custom Knowledge Base

```python
from pathlib import Path

config = ConfigBuilder("sk-ant-...") \
    .with_knowledge_base(Path("/custom/kb.json")) \
    .build()
```

### Multiple Instances

```python
# Instance 1 - Project A
config1 = ConfigBuilder("sk-ant-...") \
    .with_data_dir(Path("/data/project_a")) \
    .build()
orch1 = AgentOrchestrator(config1)

# Instance 2 - Project B
config2 = ConfigBuilder("sk-ant-...") \
    .with_data_dir(Path("/data/project_b")) \
    .build()
orch2 = AgentOrchestrator(config2)
```

### Custom Embedding Model

```python
config = ConfigBuilder("sk-ant-...") \
    .with_embedding_model("all-mpnet-base-v2") \
    .build()

# Note: Must be compatible with Sentence Transformers
```

---

**Last Updated**: December 2025
**Version**: 7.0
