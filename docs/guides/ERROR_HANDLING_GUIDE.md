# Error Handling Guide

**Version:** 1.0
**Status:** Complete
**Last Updated:** 2026-03-24

---

## Table of Contents

1. [Error Categories](#error-categories)
2. [Exception Hierarchy](#exception-hierarchy)
3. [Common Errors](#common-errors)
4. [Recovery Patterns](#recovery-patterns)
5. [Monitoring and Alerts](#monitoring-and-alerts)
6. [Best Practices](#best-practices)

---

## Error Categories

Socrates errors fall into five categories:

### 1. Configuration Errors
Issues with system setup and initialization.

```python
# Missing required configuration
if not config.api_key:
    raise ConfigurationError("API key required")

# Invalid database path
if not os.path.isdir(db_path):
    raise ConfigurationError(f"Database path does not exist: {db_path}")

# Incompatible settings
if config.log_level not in ["DEBUG", "INFO", "WARNING", "ERROR"]:
    raise ConfigurationError(f"Invalid log_level: {config.log_level}")
```

### 2. Validation Errors
Input validation failures.

```python
from socratic_core import ValidationError

# Missing required field
if "agent" not in request:
    raise ValidationError("Request missing required field: 'agent'")

# Invalid value type
if not isinstance(request.get("parameters"), dict):
    raise ValidationError("'parameters' must be a dictionary")

# Out of range
if maturity_score < 0 or maturity_score > 1.0:
    raise ValidationError(f"Maturity score must be between 0.0 and 1.0, got {maturity_score}")
```

### 3. Operational Errors
Runtime failures during normal operation.

```python
from socratic_core import AgentError, DatabaseError

# Agent execution failure
try:
    result = agent.process(request)
except AgentError as e:
    print(f"Agent failed: {e}")
    # May be retryable

# Database connection failure
try:
    db.save_project(project)
except DatabaseError as e:
    print(f"Database error: {e}")
    # Consider reconnecting
```

### 4. Integration Errors
Issues with external systems.

```python
from socratic_agents import LLMAgentError

# LLM API failure
try:
    llm_agent.process(request)
except LLMAgentError as e:
    if "rate_limit" in str(e):
        # Wait and retry
        pass
    elif "api_key" in str(e):
        # Fix configuration
        pass
```

### 5. System Errors
Unexpected system-level issues.

```python
# Out of memory
try:
    large_result = process_large_dataset()
except MemoryError:
    # Reduce batch size or fail gracefully

# Timeout
try:
    result = orchestrator.process_request(request, timeout=30)
except TimeoutError:
    # Operation took too long
```

---

## Exception Hierarchy

### Core Exceptions

```python
# Base exception
from socratic_core import SocratesError

# Configuration issues
from socratic_core import ConfigurationError

# Validation failures
from socratic_core import ValidationError

# Agent execution
from socratic_core import AgentError

# Event system
from socratic_core import EventError

# Database operations
from socratic_system.database import DatabaseError

# Knowledge base
from socratic_knowledge import KnowledgeError
```

### Catching Exceptions

```python
from socratic_core import SocratesError, ConfigurationError, ValidationError, AgentError

try:
    # Attempt operation
    result = orchestrator.process_request(request)

except ConfigurationError as e:
    # Handle configuration issues (usually startup)
    logger.error(f"Configuration error: {e}")
    sys.exit(1)

except ValidationError as e:
    # Handle invalid input
    logger.warning(f"Invalid request: {e}")
    return {"status": "error", "reason": "invalid_input", "message": str(e)}

except AgentError as e:
    # Handle agent failure
    logger.error(f"Agent failed: {e}")
    # Could retry with different parameters

except SocratesError as e:
    # Handle any Socrates error
    logger.error(f"Socrates error: {e}")

except Exception as e:
    # Catch unexpected errors
    logger.critical(f"Unexpected error: {e}", exc_info=True)
    raise
```

---

## Common Errors

### Error: "Agent 'X' not found"

**Cause:** Agent not registered or typo in name

**Solution:**

```python
# Check available agents
available = orchestrator.agents.keys()
print(f"Available agents: {available}")

# Verify agent name
requested = "QualityController"
if requested not in available:
    raise ValueError(f"Agent '{requested}' not found. Available: {available}")
```

### Error: "Database is locked"

**Cause:** Multiple concurrent connections or long transaction

**Solution:**

```python
# Use connection pooling
db = ProjectDatabase()  # Manages connections

# Or explicit transaction management
try:
    db.start_transaction()
    # ... operations ...
    db.commit()
except Exception as e:
    db.rollback()
    raise

# Wait and retry
import time
max_retries = 3
for attempt in range(max_retries):
    try:
        db.save_project(project)
        break
    except DatabaseError as e:
        if "locked" in str(e) and attempt < max_retries - 1:
            time.sleep(2 ** attempt)  # Exponential backoff
            continue
        raise
```

### Error: "API key invalid"

**Cause:** Missing or incorrect API key

**Solution:**

```python
import os
from socratic_core import ConfigurationError

# Check environment variable
api_key = os.getenv("ANTHROPIC_API_KEY")
if not api_key:
    raise ConfigurationError(
        "ANTHROPIC_API_KEY not set. "
        "Set it: export ANTHROPIC_API_KEY='sk-...'"
    )

# Verify format
if not api_key.startswith("sk-"):
    raise ConfigurationError("API key should start with 'sk-'")

# Create config
config = SocratesConfig(api_key=api_key)
```

### Error: "Request timeout"

**Cause:** Operation exceeded time limit

**Solution:**

```python
# Increase timeout for slow operations
result = orchestrator.process_request(
    request,
    timeout=60  # Default 30s, increased to 60s
)

# Or break into smaller operations
requests = split_large_request(original_request)
results = []
for req in requests:
    result = orchestrator.process_request(req, timeout=30)
    results.append(result)
```

### Error: "Memory exceeded"

**Cause:** Processing too much data at once

**Solution:**

```python
# Process in batches
def batch_process(items, batch_size=100):
    results = []
    for i in range(0, len(items), batch_size):
        batch = items[i:i+batch_size]

        try:
            result = process_batch(batch)
            results.extend(result)
        except MemoryError:
            # Reduce batch size
            logger.warning("Memory exceeded, reducing batch size")
            batch_size = batch_size // 2
            if batch_size < 1:
                raise
            continue

    return results

# Or use generators for streaming
def stream_process(items):
    for item in items:
        yield process_item(item)
```

---

## Recovery Patterns

### Pattern 1: Retry with Exponential Backoff

```python
import time
from random import uniform

def retry_with_backoff(func, max_retries=3, base_delay=1):
    """Retry function with exponential backoff"""

    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if attempt == max_retries - 1:
                raise

            # Calculate delay with jitter
            delay = base_delay * (2 ** attempt)
            jitter = uniform(0, delay * 0.1)
            wait_time = delay + jitter

            logger.warning(
                f"Attempt {attempt + 1} failed: {e}. "
                f"Retrying in {wait_time:.1f}s"
            )
            time.sleep(wait_time)

# Usage
result = retry_with_backoff(
    lambda: orchestrator.process_request(request),
    max_retries=3,
    base_delay=1
)
```

### Pattern 2: Fallback to Alternative

```python
def process_with_fallback(request: dict) -> dict:
    """Try primary agent, fallback to alternative"""

    primary_agent = request.get("agent", "QualityController")
    fallback_agent = "CodeValidator"  # Safe fallback

    try:
        # Try primary
        result = orchestrator.process_request({
            **request,
            "agent": primary_agent
        })

        if result["status"] == "success":
            return result

    except Exception as e:
        logger.warning(f"Primary agent failed: {e}")

    # Fallback
    try:
        logger.info(f"Falling back to {fallback_agent}")
        result = orchestrator.process_request({
            **request,
            "agent": fallback_agent
        })
        result["used_fallback"] = True
        return result

    except Exception as e:
        logger.error(f"Both primary and fallback failed: {e}")
        return {
            "status": "error",
            "agent": primary_agent,
            "error": str(e),
            "recovery_attempted": True
        }
```

### Pattern 3: Graceful Degradation

```python
def enhanced_orchestration(request: dict) -> dict:
    """Process with graceful degradation"""

    features = {
        "learning_tracking": True,
        "maturity_gating": True,
        "llm_enhancement": True,
        "knowledge_search": True
    }

    # Try full-featured
    try:
        orchestrator = EnhancedOrchestrator(
            use_learning=features["learning_tracking"],
            use_maturity=features["maturity_gating"],
            use_llm=features["llm_enhancement"],
            use_knowledge=features["knowledge_search"]
        )
        return orchestrator.process_request(request)

    except Exception as e:
        logger.error(f"Enhanced processing failed: {e}")

    # Degrade features one by one
    for feature in features:
        features[feature] = False

        try:
            logger.warning(f"Disabling {feature}, retrying")
            orchestrator = EnhancedOrchestrator(**features)
            result = orchestrator.process_request(request)
            result["degraded_mode"] = True
            result["disabled_features"] = [f for f, v in features.items() if not v]
            return result

        except Exception as e:
            logger.error(f"Failed even without {feature}: {e}")
            continue

    # Complete failure
    return {
        "status": "error",
        "error": "All processing modes failed",
        "degraded_to": "none"
    }
```

### Pattern 4: Circuit Breaker

```python
from enum import Enum
from datetime import datetime, timedelta

class CircuitState(Enum):
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing recovery

class CircuitBreaker:
    """Circuit breaker for failing services"""

    def __init__(self, failure_threshold=5, recovery_timeout=60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED

    def call(self, func, *args, **kwargs):
        """Execute function with circuit breaker"""

        if self.state == CircuitState.OPEN:
            # Check if should recover
            if datetime.now() - self.last_failure_time > timedelta(seconds=self.recovery_timeout):
                self.state = CircuitState.HALF_OPEN
                logger.info("Circuit breaker entering half-open state")
            else:
                raise Exception(f"Circuit breaker is OPEN. Service unavailable.")

        try:
            result = func(*args, **kwargs)

            # Success - reset
            if self.state == CircuitState.HALF_OPEN:
                logger.info("Circuit breaker closed (recovery successful)")
                self.state = CircuitState.CLOSED
            self.failure_count = 0
            return result

        except Exception as e:
            self.failure_count += 1
            self.last_failure_time = datetime.now()

            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.error(f"Circuit breaker opened after {self.failure_count} failures")

            raise

# Usage
breaker = CircuitBreaker(failure_threshold=5, recovery_timeout=60)

try:
    result = breaker.call(
        orchestrator.process_request,
        request
    )
except Exception as e:
    logger.error(f"Service unavailable: {e}")
    return {"status": "error", "reason": "service_unavailable"}
```

---

## Monitoring and Alerts

### Error Tracking

```python
import logging
from collections import defaultdict

class ErrorTracker:
    """Track error patterns"""

    def __init__(self):
        self.errors = defaultdict(int)
        self.logger = logging.getLogger("error_tracker")

    def record_error(self, error_type: str, agent: str = None):
        """Record error occurrence"""
        key = f"{error_type}:{agent}" if agent else error_type
        self.errors[key] += 1

        # Alert if threshold exceeded
        if self.errors[key] > 10:
            self.logger.critical(
                f"Error threshold exceeded for {key}: "
                f"{self.errors[key]} occurrences"
            )

    def get_error_stats(self) -> dict:
        """Get error statistics"""
        return dict(self.errors)

# Usage
tracker = ErrorTracker()

try:
    result = orchestrator.process_request(request)
except AgentError as e:
    tracker.record_error("AgentError", request.get("agent"))
    # Handle error
```

### Alerts

```python
def send_alert(severity: str, message: str, context: dict = None):
    """Send alert for critical errors"""

    alert = {
        "severity": severity,  # "info", "warning", "error", "critical"
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "context": context or {}
    }

    if severity == "critical":
        # Send to ops team
        send_email_alert(alert)
        send_slack_alert(alert)

    # Log alert
    logger.error(f"Alert [{severity}]: {message}", extra=alert)

# Usage
try:
    result = orchestrator.process_request(request)
except Exception as e:
    send_alert(
        severity="critical",
        message=f"Orchestrator failure: {e}",
        context={
            "agent": request.get("agent"),
            "project_id": request.get("project_id"),
            "error": str(e)
        }
    )
```

---

## Best Practices

### 1. Always Include Context

```python
# Good: Rich error information
raise AgentError(
    f"Agent 'QualityController' failed to process project 'proj_123': "
    f"Model 'claude-3' requires at least 50K tokens, got 120K tokens"
)

# Avoid: Vague errors
raise AgentError("Agent failed")
```

### 2. Distinguish Between Recoverable and Fatal Errors

```python
# Recoverable: Retry may help
if e.status_code == 429:  # Rate limited
    retry_with_backoff(func)

# Fatal: Retrying won't help
if e.status_code == 401:  # Unauthorized
    raise ConfigurationError("Invalid API credentials")
```

### 3. Log at Appropriate Levels

```python
# Use correct log levels
logger.debug("Processing item 123")  # Detailed, development
logger.info("Project 123 analyzed successfully")  # Normal operation
logger.warning("Agent timeout, using fallback")  # Unexpected but recoverable
logger.error("Database connection failed")  # Error, requires action
logger.critical("Out of memory, shutting down")  # System failure
```

### 4. Use Custom Exception Classes

```python
# Good: Specific exception types
class InvalidProjectError(SocratesError):
    """Raised when project data is invalid"""
    pass

class AgentTimeoutError(AgentError):
    """Raised when agent execution exceeds timeout"""
    pass

# Avoid: Generic Exception
raise Exception("Something went wrong")
```

### 5. Clean Up Resources

```python
# Good: Ensure cleanup with try/finally
lock = None
try:
    lock = acquire_lock(item_id)
    # Do work
finally:
    if lock:
        release_lock(item_id, lock)

# Or use context manager
with lock_context(item_id):
    # Do work (automatically cleaned up)
```

---

## Related Documentation

- [Architecture Overview](../ARCHITECTURE.md)
- [Configuration Guide](./CONFIGURATION_GUIDE.md)
- [Common Integration Patterns](./COMMON_INTEGRATION_PATTERNS.md)

