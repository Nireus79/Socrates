# CodeLlama Setup Guide

CodeLlama is integrated with Socrates via **Ollama** for local, free code generation.

## Prerequisites

### 1. Install Ollama
Download from: https://ollama.ai

**macOS/Linux**:
```bash
curl https://ollama.ai/install.sh | sh
```

**Windows**: Download installer from https://ollama.ai

### 2. Start Ollama Service
```bash
ollama serve
```

Ollama will start listening on `http://localhost:11434`

### 3. Pull CodeLlama Models

In a new terminal, pull the CodeLlama model(s) you want:

```bash
# Recommended: 13B model (8GB RAM required)
ollama pull codellama:13b

# Or other sizes:
ollama pull codellama:7b    # Smaller, faster (4GB RAM)
ollama pull codellama:34b   # Larger, better quality (20GB RAM)
ollama pull codellama:latest # Latest version
```

Check what models are available:
```bash
curl http://localhost:11434/api/tags
```

## Using CodeLlama in Socrates

### Via Docker

Ensure Ollama is running on your host machine (not in container):

```yaml
# docker-compose.yml
services:
  api:
    environment:
      # Tell API where to find Ollama
      OLLAMA_BASE_URL: "http://host.docker.internal:11434"
    extra_hosts:
      - "host.docker.internal:host-gateway"
```

### Via Local Installation

If running Socrates locally (not Docker):
```bash
# Ollama should be running
ollama serve

# In another terminal, run Socrates
python -m socrates_api.main
```

## Selecting CodeLlama

1. Go to **Settings** → **LLM Providers**
2. Look for **Ollama (Local)** provider
3. Should see CodeLlama models:
   - codellama:latest
   - codellama:13b
   - codellama:7b
   - codellama:34b
4. Select desired model and confirm

## Performance Tips

| Model | RAM Required | Speed | Quality |
|-------|--------------|-------|---------|
| codellama:7b | 4GB | Very Fast | Good |
| codellama:13b | 8GB | Fast | Excellent |
| codellama:34b | 20GB | Slow | Best |

**Recommended**: Start with `codellama:13b` for balanced performance.

## GPU Acceleration (Optional)

For faster inference, enable GPU:

**NVIDIA GPUs**:
```bash
OLLAMA_CUDA=1 ollama serve
```

**Apple Silicon (macOS)**:
Automatic - no setup needed

## Troubleshooting

### "CodeLlama not in dropdown"
- ✓ Ollama is running? `curl http://localhost:11434/api/tags`
- ✓ CodeLlama models pulled? `ollama list`
- ✓ Socrates restarted after installing Ollama?

### "Response too slow"
- Use smaller model: `codellama:7b`
- Enable GPU acceleration (see above)
- Increase available RAM

### "Connection refused"
- Check Ollama is running: `ollama serve`
- Check port is 11434: `netstat -an | grep 11434`
- If Docker: use `host.docker.internal` instead of `localhost`

## More Info

- [Ollama Documentation](https://ollama.ai)
- [CodeLlama on Ollama](https://ollama.ai/library/codellama)
- [Socrates CodeLlama Integration](./docs/CODELLAMA_INTEGRATION.md)
