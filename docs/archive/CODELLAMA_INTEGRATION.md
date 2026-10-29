# CodeLlama Integration Guide for Socrates

## Overview

Socrates supports **multi-provider LLM routing** out of the box. CodeLlama (via Ollama) can be integrated to handle code generation, code review, and code analysis tasks locally.

## Architecture

Socrates has a modular LLM provider system:

```
Agents
  ↓
SocraticAgentsSystem
  ↓
LLMProviderRouter
  ↓
[Claude | OpenAI | Gemini | Ollama/CodeLlama]
```

## Setup Steps

### 1. Start Ollama with CodeLlama

```bash
# Install Ollama from https://ollama.ai
# Then pull CodeLlama model:

ollama pull codellama          # Latest version
ollama pull codellama:13b      # 13B model (faster, less memory)
ollama pull codellama:7b       # 7B model (lightweight)

# Start Ollama server (default: http://localhost:11434)
ollama serve
```

### 2. Verify Ollama Connection

```bash
# Test the endpoint
curl http://localhost:11434/api/tags

# Or from Python
import requests
response = requests.get("http://localhost:11434/api/tags")
print(response.json())
```

### 3. Configure CodeLlama as Default for Code Tasks

Via environment variables or the `socratic_system/config/` module:

```python
# Option A: Environment variables
export OLLAMA_BASE_URL=http://localhost:11434
export CODE_GENERATION_PROVIDER=ollama
export CODE_GENERATION_MODEL=codellama:13b

# Option B: In configuration
{
    "llm_providers": {
        "default": "claude",
        "code_generation": "ollama",  # CodeLlama for code
        "code_review": "ollama",
        "documentation": "claude"     # Keep Claude for docs
    },
    "ollama_config": {
        "base_url": "http://localhost:11434",
        "model": "codellama:13b",
        "temperature": 0.3,
        "top_p": 0.9
    }
}
```

## Integration Points

### 1. Code Generation Agent

The `CodeGeneratorSandboxWrapper` already supports custom LLM providers:

```python
from socratic_system.agents import CodeGeneratorSandboxWrapper
from socratic_system.models.llm_provider import LLMProviderConfig

# Create CodeLlama provider config
codellama_config = LLMProviderConfig(
    id="codellama-13b",
    provider="ollama",
    user_id="user_123",
    is_default=False,
    settings={
        "model": "codellama:13b",
        "temperature": 0.3,
        "max_tokens": 4096,
        "api_endpoint": "http://localhost:11434"
    }
)

# Use with code generator
code_agent = CodeGeneratorSandboxWrapper(
    base_agent=CodeGeneratorAgent(),
    llm_provider=codellama_config
)
```

### 2. Routing Code Tasks to CodeLlama

Update the agent orchestrator to route based on task type:

```python
# In socratic_system/orchestration/agent_router.py (or create it)

def route_to_provider(request: dict) -> str:
    """Route requests to appropriate LLM provider."""
    task_type = request.get("task_type")
    
    if task_type in ["code_generation", "code_review", "code_refactoring"]:
        return "ollama"  # CodeLlama
    elif task_type == "documentation":
        return "claude"  # Claude for natural language
    else:
        return "default"  # Default provider
```

### 3. API Endpoint Configuration

In `socrates_api/routes.py`:

```python
@app.post("/api/agents/code-generate")
async def generate_code(request: CodeGenerationRequest):
    """Generate code using CodeLlama via Ollama."""
    config = LLMProviderConfig(
        id="codellama",
        provider="ollama",
        user_id=request.user_id,
        settings={
            "model": "codellama:13b",
            "temperature": 0.3,
        }
    )
    
    result = await code_agent.generate(
        prompt=request.prompt,
        language=request.language,
        context=request.context,
        llm_config=config
    )
    return result
```

## CodeLlama Capabilities

CodeLlama is specialized for code with these strengths:

| Task | Recommended Model | Config |
|------|-------------------|--------|
| Code generation | `codellama:13b` | `temp=0.3` |
| Code review | `codellama:13b` | `temp=0.2` |
| Bug fixing | `codellama:13b` | `temp=0.4` |
| Documentation | `codellama:34b` | `temp=0.5` |
| Refactoring | `codellama:13b` | `temp=0.3` |

## Configuration Examples

### Lightweight Setup (7B model, ~4GB RAM)
```json
{
  "model": "codellama:7b",
  "temperature": 0.3,
  "top_p": 0.9,
  "max_tokens": 2048
}
```

### Standard Setup (13B model, ~8GB RAM)
```json
{
  "model": "codellama:13b",
  "temperature": 0.3,
  "top_p": 0.95,
  "max_tokens": 4096
}
```

### High-Quality Setup (34B model, ~20GB RAM)
```json
{
  "model": "codellama:34b",
  "temperature": 0.5,
  "top_p": 0.95,
  "max_tokens": 8192
}
```

## Monitoring CodeLlama Usage

Track CodeLlama usage in the `LLMUsageRecord`:

```python
from socratic_system.models.llm_provider import LLMUsageRecord

usage = LLMUsageRecord(
    id="usage_123",
    user_id="user_123",
    provider="ollama",
    model="codellama:13b",
    input_tokens=256,
    output_tokens=512,
    latency_ms=1234.5,
    cost=0.0  # Local models are free
)

# Log to database
await usage_repository.save(usage)
```

## Fallback Strategy

If CodeLlama is unavailable, route to Claude:

```python
async def generate_with_fallback(prompt: str, language: str):
    """Generate code with automatic fallback."""
    try:
        # Try CodeLlama first
        result = await code_agent.generate(
            prompt=prompt,
            language=language,
            provider="ollama"
        )
        return result
    except ConnectionError:
        logger.warning("Ollama/CodeLlama unavailable, falling back to Claude")
        # Fall back to Claude
        result = await code_agent.generate(
            prompt=prompt,
            language=language,
            provider="claude"
        )
        return result
```

## Performance Tuning

### Memory Optimization
- Use 7B or 13B models for typical workloads
- 34B model for highest quality but requires 20GB+ RAM
- Use quantized versions: `codellama:13b-q4` (4-bit quantization)

### Speed Optimization
- Lower `max_tokens` for faster responses
- Use smaller batch sizes
- Run Ollama on GPU if available: `OLLAMA_CUDA=1 ollama serve`

### Cost Optimization
- CodeLlama is free (local inference)
- Save Claude API calls for complex reasoning tasks
- Route code tasks to CodeLlama, strategic tasks to Claude

## Testing

```bash
# Test CodeLlama integration
pytest tests/ -k "codellama or ollama" -v

# Test with mock Ollama
pytest tests/ -k "code_generation" --mock-ollama

# Load test with concurrent requests
locust -f tests/locustfile.py --host=http://localhost:8000
```

## Troubleshooting

### Issue: Connection refused
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if not running
ollama serve
```

### Issue: Out of memory
```bash
# Use smaller model
ollama pull codellama:7b
# Update config: "model": "codellama:7b"
```

### Issue: Slow responses
```bash
# Check GPU availability
ollama list
# Enable GPU: OLLAMA_CUDA=1 ollama serve
```

## Next Steps

1. ✅ **Start Ollama**: `ollama serve`
2. ✅ **Pull CodeLlama**: `ollama pull codellama:13b`
3. ✅ **Configure provider**: Set `OLLAMA_HOST` environment variable or use LLMEnvironmentConfig
4. ✅ **Test endpoint**: `curl http://localhost:11434/api/tags`
5. ✅ **Route code tasks**: Implement task-based routing
6. ✅ **Monitor usage**: Track CodeLlama requests and latency
7. ✅ **Optimize**: Fine-tune temperature and token limits

## Architecture Diagram

```
User Request
    ↓
API Endpoint (/api/agents/code-generate)
    ↓
Task Router (code_generation → ollama)
    ↓
CodeGeneratorSandboxWrapper
    ↓
LLMProviderRouter
    ↓
OllamaClient (http://localhost:11434)
    ↓
CodeLlama Model
    ↓
Response (code, latency, tokens)
```

## References

- CodeLlama GitHub: https://github.com/meta-llama/codellama
- Ollama: https://ollama.ai
- Socrates LLM Provider: `socratic_system/models/llm_provider.py`
- Code Generator Agent: `socratic_system/agents/code_generator_sandbox_wrapper.py`