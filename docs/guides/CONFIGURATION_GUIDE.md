# Socrates Configuration Guide

**Version:** 2.0
**Status:** Stable
**Last Updated:** 2026-03-24

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Configuration Methods](#configuration-methods)
3. [Configuration Options](#configuration-options)
4. [Environment Variables](#environment-variables)
5. [Configuration Files](#configuration-files)
6. [Advanced Configuration](#advanced-configuration)
7. [Troubleshooting](#troubleshooting)
8. [Best Practices](#best-practices)

---

## Quick Start

### Minimal Setup

```python
from socratic_core import SocratesConfig

# Create basic config
config = SocratesConfig(api_key="sk-...")

# Use with orchestrator
from socratic_system.orchestration import AgentOrchestrator
orchestrator = AgentOrchestrator(config)
```

### Recommended Setup

```python
from socratic_core import ConfigBuilder

config = (ConfigBuilder("sk-...")
    .with_log_level("INFO")
    .with_debug(False)
    .build())

orchestrator = AgentOrchestrator(config)
```

### Production Setup

```python
import os
from pathlib import Path
from socratic_core import ConfigBuilder

config = (ConfigBuilder(os.environ["ANTHROPIC_API_KEY"])
    .with_log_level("INFO")
    .with_debug(False)
    .with_data_dir(Path("/opt/socrates/data"))
    .with_claude_model("claude-3-5-sonnet-20241022")
    .build())

orchestrator = AgentOrchestrator(config)
```

---

## Configuration Methods

### Method 1: Direct Instantiation

Create SocratesConfig directly with all parameters.

```python
from socratic_core import SocratesConfig
from pathlib import Path

config = SocratesConfig(
    api_key="sk-...",
    data_dir=Path("/home/user/.socrates"),
    projects_db_path=Path("/home/user/.socrates/projects.db"),
    vector_db_path=Path("/home/user/.socrates/vector_db"),
    embedding_model="text-embedding-3-small",
    claude_model="claude-3-5-sonnet-20241022",
    log_level="INFO",
    debug=False
)
```

**When to use:**
- Simple scripts
- One-time usage
- All parameters known upfront

### Method 2: ConfigBuilder (Recommended)

Use fluent builder pattern for clarity.

```python
from socratic_core import ConfigBuilder

config = (ConfigBuilder("sk-...")
    .with_log_level("DEBUG")
    .with_debug(True)
    .with_embedding_model("text-embedding-3-large")
    .with_claude_model("claude-opus-4")
    .with_option("custom_param", "value")
    .build())
```

**When to use:**
- Most applications
- Clear configuration intent
- Chaining options
- Optional parameters

### Method 3: From Dictionary

Load configuration from dictionary (useful for configuration files).

```python
from socratic_core import SocratesConfig

config_dict = {
    "api_key": "sk-...",
    "log_level": "INFO",
    "debug": False,
    "claude_model": "claude-3-5-sonnet-20241022"
}

config = SocratesConfig.from_dict(config_dict)
```

**When to use:**
- Loading from JSON/YAML files
- Configuration from environment
- API payloads

### Method 4: From Environment Variables

```python
import os
from socratic_core import ConfigBuilder

config = (ConfigBuilder(os.environ["ANTHROPIC_API_KEY"])
    .with_log_level(os.environ.get("LOG_LEVEL", "INFO"))
    .with_debug(os.environ.get("DEBUG", "false").lower() == "true")
    .build())
```

**When to use:**
- Docker/Kubernetes deployments
- Cloud platforms
- CI/CD pipelines

---

## Configuration Options

### api_key (Required)

API key for LLM provider authentication.

```python
# Anthropic
config = SocratesConfig(api_key="sk-ant-...")

# OpenAI (if using socratic-nexus)
config = SocratesConfig(api_key="sk-...")
```

**Security:**
- Never hardcode in source
- Use environment variables
- Use secrets management systems
- Mask in logs and output

### data_dir

Base directory for all Socrates data.

**Default:** `~/.socrates`

```python
from pathlib import Path

config = (ConfigBuilder("sk-...")
    .with_data_dir(Path("/var/lib/socrates"))
    .build())
```

**Created subdirectories:**
- `projects.db` - Projects database
- `vector_db/` - Vector embeddings
- `logs/` - Log files
- `cache/` - Cached data

### projects_db_path

Path to SQLite database for projects.

**Default:** `{data_dir}/projects.db`

```python
config = (ConfigBuilder("sk-...")
    .with_projects_db(Path("/var/lib/socrates/data.db"))
    .build())
```

**Notes:**
- Must be writable directory
- Creates database if doesn't exist
- Supports any SQLite path

### vector_db_path

Path to vector database directory.

**Default:** `{data_dir}/vector_db`

```python
config = (ConfigBuilder("sk-...")
    .with_vector_db(Path("/var/lib/socrates/vectors"))
    .build())
```

**Notes:**
- Must be writable directory
- Creates directory if doesn't exist
- Stores embeddings for similarity search

### embedding_model

Model to use for text embeddings.

**Default:** `text-embedding-3-small`

```python
config = (ConfigBuilder("sk-...")
    .with_embedding_model("text-embedding-3-large")
    .build())
```

**Available models:**
- `text-embedding-3-small` - Fast, good quality
- `text-embedding-3-large` - Slower, better quality
- `text-embedding-ada-002` - Legacy, still supported

### claude_model

Claude model for LLM operations.

**Default:** `claude-3-5-sonnet-20241022`

```python
config = (ConfigBuilder("sk-...")
    .with_claude_model("claude-opus-4")
    .build())
```

**Available models:**
- `claude-3-opus-20250219` - Most capable, slower
- `claude-3-5-sonnet-20241022` - Balanced (recommended)
- `claude-3-haiku-20240307` - Fast, good for simple tasks

### log_level

Logging verbosity level.

**Default:** `INFO`

```python
config = (ConfigBuilder("sk-...")
    .with_log_level("DEBUG")
    .build())
```

**Levels:**
- `DEBUG` - Verbose logging (development)
- `INFO` - Normal logging (recommended)
- `WARNING` - Only warnings and errors
- `ERROR` - Only errors
- `CRITICAL` - Critical errors only

### debug

Enable debug mode.

**Default:** `False`

```python
config = (ConfigBuilder("sk-...")
    .with_debug(True)
    .build())
```

**When debug=True:**
- Verbose logging
- Stack traces for errors
- Performance timing
- Development-friendly output

---

## Environment Variables

Set Socrates configuration via environment variables.

### Variable Mapping

| Variable | Maps To | Example |
|----------|---------|---------|
| `ANTHROPIC_API_KEY` | `api_key` | `sk-ant-...` |
| `SOCRATES_LOG_LEVEL` | `log_level` | `DEBUG` |
| `SOCRATES_DEBUG` | `debug` | `true` |
| `SOCRATES_DATA_DIR` | `data_dir` | `/var/lib/socrates` |
| `SOCRATES_CLAUDE_MODEL` | `claude_model` | `claude-opus-4` |

### Loading from Environment

```python
import os
from socratic_core import ConfigBuilder

# Automatic loading
api_key = os.environ.get("ANTHROPIC_API_KEY")
if not api_key:
    raise ValueError("ANTHROPIC_API_KEY not set")

config = (ConfigBuilder(api_key)
    .with_log_level(os.environ.get("SOCRATES_LOG_LEVEL", "INFO"))
    .with_debug(os.environ.get("SOCRATES_DEBUG", "false").lower() == "true")
    .build())
```

### Docker Environment

```dockerfile
FROM python:3.12

ENV ANTHROPIC_API_KEY=sk-...
ENV SOCRATES_LOG_LEVEL=INFO
ENV SOCRATES_DATA_DIR=/var/lib/socrates

RUN mkdir -p $SOCRATES_DATA_DIR

COPY . /app
WORKDIR /app

CMD ["python", "-m", "socrates"]
```

---

## Configuration Files

### JSON Configuration

`socrates.json`:
```json
{
    "api_key": "sk-...",
    "log_level": "INFO",
    "debug": false,
    "data_dir": "/var/lib/socrates",
    "claude_model": "claude-3-5-sonnet-20241022"
}
```

Loading:
```python
import json
from socratic_core import SocratesConfig

with open("socrates.json") as f:
    config_dict = json.load(f)

config = SocratesConfig.from_dict(config_dict)
```

### YAML Configuration

`socrates.yaml`:
```yaml
api_key: sk-...
log_level: INFO
debug: false
data_dir: /var/lib/socrates
claude_model: claude-3-5-sonnet-20241022
```

Loading:
```python
import yaml
from socratic_core import SocratesConfig

with open("socrates.yaml") as f:
    config_dict = yaml.safe_load(f)

config = SocratesConfig.from_dict(config_dict)
```

### Environment-Specific Configs

```
configs/
├── development.json
├── staging.json
└── production.json
```

Loading:
```python
import json
import os
from socratic_core import SocratesConfig

env = os.environ.get("ENVIRONMENT", "development")
config_file = f"configs/{env}.json"

with open(config_file) as f:
    config_dict = json.load(f)

config = SocratesConfig.from_dict(config_dict)
```

---

## Advanced Configuration

### Custom Options

```python
config = (ConfigBuilder("sk-...")
    .with_option("max_retries", 3)
    .with_option("timeout_seconds", 30)
    .with_option("cache_ttl_minutes", 5)
    .build())

# Access custom options
max_retries = config.extra["max_retries"]
```

### Configuration Validation

```python
from socratic_core import ConfigurationError

def validate_config(config):
    if not config.api_key:
        raise ConfigurationError("API key required")

    if config.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR"]:
        raise ConfigurationError(f"Invalid log level: {config.log_level}")

    if not config.data_dir.exists():
        try:
            config.data_dir.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ConfigurationError(f"Cannot create data directory: {e}")

config = (ConfigBuilder("sk-...")
    .with_log_level("INFO")
    .build())

validate_config(config)
```

### Configuration Profiles

```python
class ConfigProfile:
    @staticmethod
    def development():
        return (ConfigBuilder("sk-...")
            .with_debug(True)
            .with_log_level("DEBUG")
            .build())

    @staticmethod
    def production():
        return (ConfigBuilder(os.environ["ANTHROPIC_API_KEY"])
            .with_debug(False)
            .with_log_level("INFO")
            .build())

    @staticmethod
    def testing():
        return (ConfigBuilder("sk-test")
            .with_debug(True)
            .with_log_level("WARNING")
            .build())

# Use profiles
config = ConfigProfile.production()
```

### Configuration Merging

```python
def merge_configs(base_config_dict, overrides_dict):
    """Merge override config into base config."""
    merged = {**base_config_dict, **overrides_dict}
    return merged

base = {
    "log_level": "INFO",
    "debug": False
}

overrides = {
    "debug": True  # Override debug setting
}

merged = merge_configs(base, overrides)
config = SocratesConfig.from_dict(merged)
```

---

## Troubleshooting

### API Key Issues

**Problem:** `ConfigurationError: API key not provided`

```python
# Solution 1: Set in code
config = SocratesConfig(api_key="sk-...")

# Solution 2: Set environment variable
os.environ["ANTHROPIC_API_KEY"] = "sk-..."
config = ConfigBuilder(os.environ["ANTHROPIC_API_KEY"]).build()

# Solution 3: Check if key is set
if not os.environ.get("ANTHROPIC_API_KEY"):
    print("Error: ANTHROPIC_API_KEY environment variable not set")
```

### Database Path Issues

**Problem:** `PermissionError: Cannot create database`

```python
# Check directory permissions
import os
data_dir = Path("/var/lib/socrates")

if not os.access(data_dir, os.W_OK):
    print(f"Error: No write permission to {data_dir}")
    # Solution: Change permissions or use different directory

# Solution: Use user directory
config = (ConfigBuilder("sk-...")
    .with_data_dir(Path.home() / ".socrates")
    .build())
```

### Model Name Issues

**Problem:** `APIError: Model not found`

```python
# Check available models
valid_models = [
    "claude-3-opus-20250219",
    "claude-3-5-sonnet-20241022",
    "claude-3-haiku-20240307"
]

model = "claude-invalid"
if model not in valid_models:
    print(f"Error: Invalid model '{model}'")
    print(f"Available: {valid_models}")

# Solution: Use valid model
config = (ConfigBuilder("sk-...")
    .with_claude_model("claude-3-5-sonnet-20241022")
    .build())
```

### Log Level Issues

**Problem:** `ValueError: Invalid log level`

```python
valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

level = "invalid"
if level not in valid_levels:
    raise ValueError(f"Invalid log level: {level}")

# Solution: Use valid level
config = (ConfigBuilder("sk-...")
    .with_log_level("INFO")
    .build())
```

---

## Best Practices

### 1. Use Environment Variables for Secrets

```python
# Good: Secrets from environment
api_key = os.environ["ANTHROPIC_API_KEY"]
config = SocratesConfig(api_key=api_key)

# Bad: Hardcoded secrets
config = SocratesConfig(api_key="sk-...")  # Don't do this!
```

### 2. Create Configuration Factory

```python
def create_config(environment="production"):
    """Factory function for creating configs."""
    base_builder = ConfigBuilder(os.environ["ANTHROPIC_API_KEY"])

    if environment == "development":
        return (base_builder
            .with_debug(True)
            .with_log_level("DEBUG")
            .build())
    elif environment == "production":
        return (base_builder
            .with_debug(False)
            .with_log_level("INFO")
            .build())
    else:
        raise ValueError(f"Unknown environment: {environment}")

# Use factory
config = create_config(os.environ.get("ENVIRONMENT", "production"))
```

### 3. Validate Configuration on Startup

```python
def validate_and_configure():
    """Validate and create configuration."""
    try:
        config = (ConfigBuilder(os.environ["ANTHROPIC_API_KEY"])
            .with_log_level(os.environ.get("LOG_LEVEL", "INFO"))
            .build())

        # Verify paths are accessible
        assert config.data_dir.exists() or config.data_dir.mkdir(parents=True)

        return config
    except KeyError as e:
        raise ConfigurationError(f"Missing required env var: {e}")
    except Exception as e:
        raise ConfigurationError(f"Configuration failed: {e}")

config = validate_and_configure()
```

### 4. Export Configuration for Debugging

```python
def get_config_summary(config):
    """Get configuration summary (safe to log)."""
    config_dict = config.to_dict()
    # API key is already masked
    return {
        "api_key": config_dict["api_key"],  # "***"
        "log_level": config.log_level,
        "debug": config.debug,
        "data_dir": str(config.data_dir)
    }

config = SocratesConfig(api_key="sk-...")
summary = get_config_summary(config)
print("Configuration loaded:", summary)
```

### 5. Use Type Hints with Configuration

```python
from typing import Optional
from pathlib import Path
from socratic_core import SocratesConfig

def setup_socrates(
    api_key: str,
    log_level: str = "INFO",
    debug: bool = False,
    data_dir: Optional[Path] = None
) -> SocratesConfig:
    """Setup Socrates with typed configuration."""
    builder = ConfigBuilder(api_key).with_log_level(log_level)

    if debug:
        builder = builder.with_debug(True)

    if data_dir:
        builder = builder.with_data_dir(data_dir)

    return builder.build()

# Use with type hints
config = setup_socrates(
    api_key="sk-...",
    log_level="DEBUG",
    debug=True
)
```

---

## Configuration Profiles Reference

### Development Profile

```python
config = (ConfigBuilder(os.environ["ANTHROPIC_API_KEY"])
    .with_debug(True)
    .with_log_level("DEBUG")
    .with_data_dir(Path.home() / ".socrates-dev")
    .build())
```

**Characteristics:**
- Debug mode enabled
- Verbose logging
- Local data directory
- Fast iteration

### Staging Profile

```python
config = (ConfigBuilder(os.environ["ANTHROPIC_API_KEY"])
    .with_debug(False)
    .with_log_level("INFO")
    .with_data_dir(Path("/opt/socrates-staging"))
    .build())
```

**Characteristics:**
- Debug mode disabled
- Normal logging
- Shared data directory
- Pre-production testing

### Production Profile

```python
config = (ConfigBuilder(os.environ["ANTHROPIC_API_KEY"])
    .with_debug(False)
    .with_log_level("WARNING")
    .with_data_dir(Path("/var/lib/socrates"))
    .with_option("max_retries", 3)
    .build())
```

**Characteristics:**
- Debug mode disabled
- Minimal logging
- Shared production directory
- Reliability focus
- Error handling configured

---

## Security Checklist

Before deploying to production:

- [ ] API key from environment variable
- [ ] Debug mode disabled
- [ ] Log level set to INFO or higher
- [ ] Data directory has proper permissions (700)
- [ ] Database path is on secure storage
- [ ] Configuration file not in version control
- [ ] Secrets not logged anywhere
- [ ] HTTPS enabled for API calls
- [ ] Regular backups configured
- [ ] Monitoring and alerting enabled

---

## Performance Tuning

### High-Throughput Configuration

```python
config = (ConfigBuilder("sk-...")
    .with_option("connection_pool_size", 20)
    .with_option("max_concurrent_agents", 10)
    .with_option("cache_ttl_minutes", 30)
    .build())
```

### Low-Resource Configuration

```python
config = (ConfigBuilder("sk-...")
    .with_option("connection_pool_size", 2)
    .with_option("max_concurrent_agents", 1)
    .with_option("cache_ttl_minutes", 5)
    .build())
```

---

## See Also

- [Architecture Overview](../ARCHITECTURE.md)
- [socratic-core API Reference](./SOCRATIC_CORE_API.md)
- [Orchestration API Reference](./ORCHESTRATION_API.md)
- [Deployment Guide](../DEPLOYMENT.md)
