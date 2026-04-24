# LLM Clients Quick Reference

## Installation

### Required SDK Dependencies
```bash
pip install openai>=1.0.0
pip install google-generativeai
pip install requests  # For Ollama
```

### Environment Setup
```bash
# .env or export
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=AIza...
SOCRATES_ENCRYPTION_KEY=your-secret-key  # Optional, uses default if not set
```

---

## Usage Examples

### Initialize a Client
```python
from socratic_system.clients import OpenAIClient, GoogleClient, OllamaClient
from socratic_system.orchestration.orchestrator import AgentOrchestrator

# Get orchestrator instance (provides config, database, event emitter)
orchestrator = AgentOrchestrator(...)

# Create client with default API key
openai_client = OpenAIClient(
    api_key=os.getenv("OPENAI_API_KEY"),
    orchestrator=orchestrator
)

# Or for Google
google_client = GoogleClient(
    api_key=os.getenv("GOOGLE_API_KEY"),
    orchestrator=orchestrator
)

# Or for Ollama (doesn't require API key for local)
ollama_client = OllamaClient(
    orchestrator=orchestrator
)
```

### Generate Response
```python
# Synchronous
response = openai_client.generate_response(
    prompt="What is the capital of France?",
    max_tokens=100,
    temperature=0.7,
    user_id="user123"  # Will fetch user's API key from database
)
print(response)

# Asynchronous
response = await openai_client.generate_response_async(
    prompt="What is the capital of France?",
    max_tokens=100,
    temperature=0.7,
    user_id="user123"
)
```

### Generate Socratic Question
```python
question = openai_client.generate_socratic_question(
    prompt="The user wants to build a social media app. What should they think about?",
    user_id="user123"
)
print(question)
```

### Extract Insights from User Response
```python
project = ProjectContext(
    name="My App",
    phase="discovery",
    goals="Build a productivity app",
    tech_stack=["Python", "React"]
)

insights = google_client.extract_insights(
    user_response="We need real-time collaboration and offline support",
    project=project,
    user_id="user123"
)
# Returns: {
#     "requirements": ["real-time collaboration", "offline support"],
#     "tech_stack": [...],
#     ...
# }
```

### Generate Code
```python
code = openai_client.generate_code(
    context="Building authentication module for Django app using JWT tokens",
    user_id="user123"
)
print(code)  # Returns executable Python code
```

### Test Connection
```python
try:
    is_connected = openai_client.test_connection()
    print(f"Connected: {is_connected}")
except APIError as e:
    print(f"Error: {e.message}")
```

---

## User-Specific API Keys

### Save User API Key
```python
import os
from cryptography.fernet import Fernet
import hashlib
import base64

# Encrypt the key
encryption_key_base = os.getenv("SOCRATES_ENCRYPTION_KEY", "default-socrates-key")
key_hash = hashlib.sha256(encryption_key_base.encode()).digest()
encryption_key = base64.urlsafe_b64encode(key_hash)
cipher = Fernet(encryption_key)
encrypted_key = cipher.encrypt(user_api_key.encode()).decode()

# Save to database
orchestrator.database.save_api_key(
    user_id="user123",
    provider="openai",  # "claude", "google", "ollama"
    encrypted_key=encrypted_key,
    key_hash=hashlib.sha256(user_api_key.encode()).hexdigest()
)
```

### Retrieve User API Key
```python
# Automatic in client's _get_user_api_key() method
# Simply pass user_id to any method:
response = openai_client.generate_response(
    prompt="...",
    user_id="user123"  # Client will fetch from database
)
```

### Delete User API Key
```python
orchestrator.database.delete_api_key(
    user_id="user123",
    provider="openai"
)
```

---

## Configuration

### Via Config Object
```python
from socratic_system.config import Config

config = Config()
config.openai_model = "gpt-4"           # Default: "gpt-4-turbo"
config.google_model = "gemini-pro-vision"  # Default: "gemini-pro"
config.ollama_model = "llama2"          # Default: "mistral"
config.ollama_url = "http://custom:11434"  # Default: "http://localhost:11434"
```

### Via Environment
```bash
export OPENAI_MODEL="gpt-4-turbo"
export GOOGLE_MODEL="gemini-pro"
export OLLAMA_MODEL="mistral"
export OLLAMA_URL="http://localhost:11434"
```

---

## Error Handling

### API Errors
```python
from socratic_system.exceptions import APIError

try:
    response = openai_client.generate_response(prompt="...", user_id="user123")
except APIError as e:
    if e.error_type == "MISSING_API_KEY":
        print(f"Configure API key: {e.message}")
    elif e.error_type == "CONNECTION_ERROR":
        print(f"Server error: {e.message}")
    elif e.error_type == "GENERATION_ERROR":
        print(f"Generation failed: {e.message}")
```

### Graceful Fallbacks
```python
# Client handles missing user API key - falls back to default
response = openai_client.generate_response(
    prompt="...",
    user_id="nonexistent_user"  # Will use OPENAI_API_KEY env var
)
```

---

## Token Tracking

### Automatic Tracking
All operations automatically emit `EventType.TOKEN_USAGE` events:

```python
# Subscribe to token tracking events
@orchestrator.event_emitter.on(EventType.TOKEN_USAGE)
def on_token_usage(data):
    print(f"Operation: {data['operation']}")
    print(f"Tokens: {data['input_tokens']} input, {data['output_tokens']} output")
    print(f"Cost estimate: ${data['cost_estimate']:.4f}")
```

### Cost Calculation
```
Claude:  $0.003 per 1K input,  $0.015 per 1K output
OpenAI:  $0.01  per 1K input,  $0.03  per 1K output
Google:  $0.00025 per 1K chars input, $0.0005 per 1K chars output
Ollama:  $0 (free - local)
```

---

## Async Operations

### Available Async Methods
```python
# All clients support async versions:
await client.generate_response_async(prompt, max_tokens, temperature, user_id)
await client.generate_socratic_question_async(prompt, user_id)
await client.extract_insights_async(user_response, project)
```

### Example
```python
import asyncio

async def main():
    tasks = [
        openai_client.generate_socratic_question_async("Question 1"),
        google_client.generate_socratic_question_async("Question 2"),
        ollama_client.generate_socratic_question_async("Question 3"),
    ]

    results = await asyncio.gather(*tasks)
    return results

questions = asyncio.run(main())
```

---

## Client Switching

### Same Interface Across All Clients
```python
def generate_answer(client, prompt, user_id):
    # Works with any client - same signature
    return client.generate_response(
        prompt=prompt,
        max_tokens=2000,
        temperature=0.7,
        user_id=user_id
    )

# Use with different clients
answer1 = generate_answer(openai_client, "...", "user123")
answer2 = generate_answer(google_client, "...", "user123")
answer3 = generate_answer(ollama_client, "...", "user123")
```

---

## Caching

### Insights Cache
```python
# First call - executes API request
insights1 = client.extract_insights(
    user_response="The user said this...",
    project=project
)

# Second identical call - returns from cache
insights2 = client.extract_insights(
    user_response="The user said this...",
    project=project
)  # No API call - returned from cache!

# Different response - new API call
insights3 = client.extract_insights(
    user_response="Different response...",
    project=project
)
```

### Clear Cache (if needed)
```python
client._insights_cache.clear()
```

---

## Logging

### Enable Debug Logging
```python
import logging

logging.getLogger("socrates.clients.openai").setLevel(logging.DEBUG)
logging.getLogger("socrates.clients.google").setLevel(logging.DEBUG)
logging.getLogger("socrates.clients.ollama").setLevel(logging.DEBUG)
```

### Log Output
```
DEBUG: Creating client with user-specific API key
DEBUG: Cache hit for insights extraction
DEBUG: Ollama server connection verified
ERROR: All decryption methods failed for API key
```

---

## Troubleshooting

### Ollama Not Connecting
```bash
# Start Ollama server
ollama serve

# Test connection
curl http://localhost:11434/api/tags
```

### API Key Not Found
```
APIError: "No API key configured. Please set your API key in Settings > LLM > OpenAI"
```
**Solution**: Set environment variable or save user-specific key to database

### Token Calculation Mismatch
- **Claude/OpenAI**: Actual token counts from API
- **Google**: Estimated as text_length / 4
- **Ollama**: Estimated as text_length / 4 (plus model overhead)

---

## Common Patterns

### Sequential API Calls
```python
# Process user input
insights = await openai_client.extract_insights_async(user_response, project)

# Generate Socratic question based on insights
if insights.get("goals"):
    question = await google_client.generate_socratic_question_async(
        f"The user mentioned: {insights['goals']}. What else should they consider?"
    )
```

### Fallback to Different Provider
```python
async def generate_question(prompt, user_id):
    try:
        return await openai_client.generate_socratic_question_async(prompt, user_id)
    except APIError:
        # Fallback to Google if OpenAI fails
        return await google_client.generate_socratic_question_async(prompt, user_id)
```

### Cost-Aware API Selection
```python
# Use free local Ollama for simple questions
if is_simple_question:
    return ollama_client.generate_socratic_question(prompt)
else:
    # Use more capable model for complex reasoning
    return openai_client.generate_socratic_question(prompt)
```

---

## Integration with Agents

### In Agent Methods
```python
from socratic_system.agents.base import Agent

class MyAgent(Agent):
    def process(self, data):
        # All agents have orchestrator reference
        client = self.orchestrator.llm_client  # Can be any client

        response = client.generate_response(
            prompt=data["prompt"],
            user_id=data.get("user_id")
        )

        return response
```

---

## Provider Comparison

| Feature | Claude | OpenAI | Google | Ollama |
|---------|--------|--------|--------|--------|
| **Cost** | $$ | $$$ | $ | Free |
| **Speed** | Fast | Fast | Medium | Varies |
| **Accuracy** | Excellent | Excellent | Good | Good |
| **Setup** | Cloud only | Cloud only | Cloud only | Local |
| **Privacy** | Shared server | Shared server | Shared server | Fully local |
| **Use Case** | Production | Production | Cost-sensitive | Private/Dev |

---

## API Reference

### Constructor Signature (All Clients)
```python
Client(
    api_key: str = None,           # Optional - from env or database
    orchestrator: AgentOrchestrator = None,  # Required
    subscription_token: str = None  # Optional - for subscription auth
)
```

### Core Methods (All Clients)
```python
# Synchronous
extract_insights(user_response, project, user_auth_method="api_key", user_id=None) -> Dict
generate_code(context, user_auth_method="api_key", user_id=None) -> str
generate_socratic_question(prompt, user_auth_method="api_key", user_id=None) -> str
generate_response(prompt, max_tokens=2000, temperature=0.7, user_auth_method="api_key", user_id=None) -> str
test_connection(user_auth_method="api_key") -> bool

# Asynchronous
async extract_insights_async(user_response, project, user_auth_method="api_key") -> Dict
async generate_socratic_question_async(prompt, user_auth_method="api_key", user_id=None) -> str
async generate_response_async(prompt, max_tokens=2000, temperature=0.7, user_auth_method="api_key", user_id=None) -> str
```

---

## Final Notes

- **All clients are drop-in replacements** for each other
- **Same signatures** ensure no code changes when switching providers
- **Automatic encryption** handles API key security
- **Per-user API keys** enable multi-tenant usage
- **Token tracking** monitors costs and usage
- **Event emission** integrates with orchestrator's event system
- **Caching** optimizes repeated operations
- **Async support** enables high-concurrency scenarios

