# LLM Configuration Data Contract

## Overview

This document defines the data contract between the Socrates database layer and the `socratic-agents` library for LLM provider configuration management.

## Problem Statement

The `socratic-agents` library (external PyPI package) contains the `MultiLLMAgent` class which manages LLM provider configurations. This agent expects configuration data to be returned with specific fields at the top level of the returned dictionary.

The Socrates database stores LLM configurations as JSON in the `config_data` column. To maintain compatibility with the agent's expectations, the database methods must flatten this structure.

## Data Structure Contract

### Database Storage (SQLite)

```sql
CREATE TABLE llm_provider_configs (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    provider TEXT NOT NULL,
    config_data TEXT,        -- JSON blob containing settings
    created_at TEXT,
    updated_at TEXT,
    UNIQUE(user_id, provider)
);
```

The `config_data` column contains a JSON string with structure:
```json
{
    "id": "config-id",
    "is_default": true,
    "enabled": true,
    "settings": {
        "model": "gpt-4",
        "max_tokens": 4096,
        "temperature": 0.7
    }
}
```

### Database Interface (Return Structure)

Methods `ProjectDatabase.get_user_llm_config()` and `get_user_llm_configs()` must return **flattened** dictionaries:

```python
{
    "id": str,                  # Config record ID (from DB)
    "user_id": str,             # User ID (from DB)
    "provider": str,            # Provider name (from DB)
    "created_at": str,          # ISO timestamp (from DB)
    "updated_at": str,          # ISO timestamp (from DB)
    # Merged from config_data JSON:
    "is_default": bool,         # Whether default for this user
    "enabled": bool,            # Whether config is active
    "settings": dict,           # Provider-specific settings
}
```

### Agent Expectations

The `socratic-agents.MultiLLMAgent` class (in methods `_set_default_provider()` and `_set_provider_model()`) expects the returned configuration to have these fields accessible at the top level:

```python
# Agent code expects this structure:
config = db.get_user_llm_config(user_id, provider)
if config:
    config.get("settings")      # ← Must be at top level
    config.get("is_default")    # ← Must be at top level
    config.get("enabled")       # ← Must be at top level
```

## Implementation Details

### Why Flatten?

The agent was designed to work with a flat configuration dictionary. Rather than modify the external `socratic-agents` library (which requires PyPI republication), the Socrates database layer flattens the structure before returning it.

**Socrates database** (project_db.py):
```python
def get_user_llm_config(self, user_id: str, provider: str):
    # Fetch from DB
    row = cursor.fetchone()
    
    # Start with metadata
    config_dict = {
        "id": row["id"],
        "user_id": row["user_id"],
        "provider": row["provider"],
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }
    
    # Merge JSON config data at top level
    if row["config_data"]:
        parsed_config = json.loads(row["config_data"])
        config_dict.update(parsed_config)  # ← Flattens structure
    
    return config_dict
```

## Modification Guidelines

### If you need to change the config structure:

1. **Add a new field to config_data JSON**: Just add it to the JSON, it will be automatically merged at the top level. No changes needed.

2. **Remove a field**: Remove it from the JSON. Update agent code if it relies on the field.

3. **Change field naming**: Must update BOTH:
   - The JSON storage in `save_llm_config()`
   - The agent code in `socratic-agents` (will require PyPI republication)

4. **Change agent expectations**: Update the agent code, republish to PyPI, update `pyproject.toml` dependency version.

### Testing the contract:

```python
# In tests, verify the flattened structure:
config = db.get_user_llm_config("user123", "claude")
assert "settings" in config  # Top level
assert "is_default" in config  # Top level
assert "enabled" in config  # Top level
assert "config" not in config  # NOT nested under "config" key
```

## Related Code

- **Database**: `socratic_system/database/project_db.py`
  - `get_user_llm_config()`
  - `get_user_llm_configs()`
  - `save_llm_config()`

- **Agent**: External package `socratic-agents` (PyPI)
  - `socratic_agents/multi_llm_agent.py`
  - `MultiLLMAgent._set_default_provider()`
  - `MultiLLMAgent._set_provider_model()`

- **Configuration**: `pyproject.toml`
  - `socratic-agents>=0.3.9` dependency

## Version History

- **v0.3.9 (2026-06-16)**: Implemented flattened structure in Socrates database to match agent expectations. Removed subscription checks from agent layer.
