# LLM Provider Deployment Guide

This guide explains how to configure Ollama and other LLM providers across different deployment scenarios.

## Architecture: Option 4 (Delegation Pattern)

Socrates implements **Option 4 (Delegation Pattern)**:
- **Orchestrator** discovers available resources and their locations
- **Configuration** is provided by the deployment environment
- **Agents** consume what they're told, not what they assume exists
- **Result**: Works in any deployment (local, Docker, Kubernetes, cloud)

---

## Ollama Endpoint Configuration

The system auto-detects Ollama in this order:

1. **Environment Variable** (highest priority)
   ```bash
   export OLLAMA_HOST=http://your-ollama-location:11434
   ```

2. **Docker Networks** (if running in Docker)
   - `http://ollama:11434` - Ollama container on same network
   - `http://host.docker.internal:11434` - Docker Desktop host

3. **Local Development**
   - `http://localhost:11434`

4. **Kubernetes Service Discovery**
   - `http://ollama.default.svc.cluster.local:11434`

---

## Deployment Scenarios

### 1. Local Development

**Setup**: Ollama running on your machine

```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Start Socrates
docker-compose up -d
```

**Environment**:
- ✅ Auto-detected: `http://localhost:11434`
- No configuration needed

---

### 2. Docker Compose with Ollama on Host

**Scenario**: Running on Linux server with Ollama on host machine

```bash
# docker-compose.yml
services:
  api:
    environment:
      OLLAMA_HOST: http://150.140.174.214:11434  # Your server IP
```

Or set via environment:
```bash
export OLLAMA_HOST=http://150.140.174.214:11434
docker-compose up -d
```

**Logs should show**:
```
Deployment scenario: docker_compose
✓ Detected Ollama at http://150.140.174.214:11434
Discovered X Ollama models
```

---

### 3. Docker Compose with Ollama in Container

**Scenario**: Ollama running as a Docker container on same network

```bash
# docker-compose.yml
services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    networks:
      - socrates-network
  
  api:
    environment:
      OLLAMA_HOST: http://ollama:11434  # Service name on network

volumes:
  ollama_data:
```

**Logs should show**:
```
Deployment scenario: docker_compose
✓ Detected Ollama at http://ollama:11434
Discovered X Ollama models
```

---

### 4. Docker Desktop (Mac/Windows)

**Scenario**: Ollama running on your Mac/Windows host

```bash
# docker-compose.yml
services:
  api:
    environment:
      OLLAMA_HOST: http://host.docker.internal:11434
```

**Logs should show**:
```
Deployment scenario: docker_desktop
✓ Detected Ollama at http://host.docker.internal:11434
Discovered X Ollama models
```

---

### 5. Kubernetes

**Scenario**: Ollama deployed as Kubernetes service

```bash
# Set OLLAMA_HOST to Kubernetes service name
export OLLAMA_HOST=http://ollama.default.svc.cluster.local:11434

# Or in deployment.yaml
env:
  - name: OLLAMA_HOST
    value: "http://ollama.default.svc.cluster.local:11434"
```

**Logs should show**:
```
Deployment scenario: kubernetes
✓ Detected Ollama at http://ollama.default.svc.cluster.local:11434
Discovered X Ollama models
```

---

### 6. Cloud/Remote Deployment

**Scenario**: Ollama on a remote server or cloud service

```bash
# Set OLLAMA_HOST to remote server
export OLLAMA_HOST=http://ollama.example.com:11434
# or
export OLLAMA_HOST=http://your-cloud-server-ip:11434

docker-compose up -d
```

**Logs should show**:
```
Deployment scenario: local_development
✓ Detected Ollama at http://ollama.example.com:11434
Discovered X Ollama models
```

---

## Troubleshooting

### Ollama Not Detected

**Symptom**: Logs show `Using fallback Ollama model list`

**Solution**:
1. Check Ollama is running
2. Set `OLLAMA_HOST` environment variable
3. Check network connectivity

```bash
# Verify Ollama is running
curl http://your-ollama-location:11434/api/tags

# Set OLLAMA_HOST if needed
export OLLAMA_HOST=http://your-ollama-location:11434
docker-compose down && docker-compose up -d

# Check logs
docker-compose logs api | grep -i "ollama\|discovery"
```

### Models Not Appearing in Frontend

**Symptom**: CodeLlama, Mistral, etc. don't show in dropdown

**Solution**:
1. Verify Ollama is discoverable
2. Check models are installed in Ollama

```bash
# List installed models in Ollama
curl http://localhost:11434/api/tags | jq '.models[].name'

# Pull a model if missing
ollama pull codellama:latest
```

### Discovery Succeeds but No Models

**Symptom**: Logs show discovery succeeded but empty model list

**Possible causes**:
- Ollama running but no models installed
- Wrong Ollama endpoint (different Ollama instance)

**Solution**:
```bash
# Verify correct Ollama instance
curl $OLLAMA_HOST/api/tags

# Pull models
ollama pull mistral:latest
ollama pull codellama:latest
```

---

## Configuration Priority

The system checks configuration in this order (first match wins):

1. **OLLAMA_HOST environment variable** (explicit)
2. **Ollama service on Docker network** (if in container)
3. **host.docker.internal** (if on Docker Desktop)
4. **localhost:11434** (if local)
5. **Kubernetes service discovery** (if in K8s)

To override, always use:
```bash
export OLLAMA_HOST=http://your-location:11434
```

---

## Environment Variables

| Variable | Purpose | Example |
|----------|---------|---------|
| `OLLAMA_HOST` | Override Ollama endpoint | `http://ollama:11434` |
| `ANTHROPIC_API_KEY` | Claude API access | (set from secrets) |
| `OPENAI_API_KEY` | OpenAI API access | (set from secrets) |

---

## Next Steps

1. **Set OLLAMA_HOST** for your deployment scenario
2. **Restart Socrates**: `docker-compose down && docker-compose up -d`
3. **Verify discovery**: `docker-compose logs api | grep ollama`
4. **Test in frontend**: Settings > LLM Configuration > Ollama section

---

## Support

If issues persist:
1. Check `/docs/DEBUG_LLM.md` for detailed logging
2. Review deployment scenario above
3. Verify network connectivity: `curl $OLLAMA_HOST/api/tags`
4. Check Socrates logs: `docker-compose logs api -f`
