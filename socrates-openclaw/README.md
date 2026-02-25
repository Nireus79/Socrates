# Socrates AI - OpenClaw Integration

Official integration of Socrates AI with OpenClaw, the personal AI assistant platform.

Transform conversations into structured project specifications using Socratic discovery.

## Features

🎓 **Socratic Discovery** - Claude-guided questioning for project discovery
📚 **RAG Knowledge Base** - Vector embeddings with ChromaDB for context-aware responses
📊 **Specification Generation** - Auto-generate requirements, architecture, and project specs
💾 **Session Persistence** - Resume discoveries anytime
🔄 **Multi-turn Conversations** - Natural dialogue flow with context tracking
⚡ **Production Ready** - Built on battle-tested socrates-ai library

## Installation
```bash
pip install socrates-ai-openclaw
```

## Quick Start

### Basic Usage
```python
from socrates_openclaw import SocraticDiscoverySkill

# Initialize the skill
skill = SocraticDiscoverySkill()

# Start a discovery session
result = await skill.start_discovery("AI-powered SaaS application")
print(result["question"])
# Output: "What problem does this solve for your target users?"

# Respond to the question
result = await skill.respond(result["session_id"], "Helps teams manage projects efficiently")
print(result["question"])
# Output: "Who is your primary target user?"

# Continue for several more turns...

# Generate a specification
result = await skill.generate(result["session_id"])
print(result["spec"])
# Output: Complete project specification in Markdown
```

### With OpenClaw
```bash
# Install OpenClaw
pip install openclaw

# Socratic discovery is automatically available
# Users can start a discovery session in their preferred channel
```

In OpenClaw chat:
User: "Help me plan a new project"
OpenClaw: "I'll guide you through Socratic discovery. Question 1: What problem does this solve?"
User: "Tracks team time efficiently"
OpenClaw: "Question 2: Who are your target users?"
... (continues for 5-8 turns)
User: "Generate a spec"
OpenClaw: "Here's your project specification..."

## How It Works

### Discovery Process

1. **Initialization** - User starts discovery with a project topic
2. **Socratic Questions** - AI asks probing questions using Socratic method
3. **Context Accumulation** - System tracks all responses in knowledge base
4. **Adaptive Follow-up** - Questions adapt based on previous responses
5. **Specification Generation** - After sufficient responses, AI synthesizes a complete spec
6. **Storage** - Projects are saved locally with all artifacts

### Architecture

User Input (OpenClaw)
↓
SocraticDiscoverySkill
↓
├─ SessionManager (track sessions)
├─ QuestionEngine (generate questions)
├─ ResponseProcessor (handle answers)
├─ SpecGenerator (create specs)
└─ StorageHandler (persist data)
↓
socrates-ai Library
↓
├─ Claude API (LLM)
├─ ChromaDB (RAG)
└─ Multi-Agent System

## Configuration

### Environment Variables
```bash
# Required
export ANTHROPIC_API_KEY="sk-ant-..."

# Optional
export SOCRATIC_MODEL="claude-opus-4-6"
export SOCRATIC_TEMPERATURE="0.7"
export SOCRATIC_WORKSPACE_ROOT="~/.openclaw/workspace"
```

### Programmatic Configuration
```python
from socrates_openclaw import SocraticDiscoverySkill
from pathlib import Path

skill = SocraticDiscoverySkill(
    workspace_root=Path.home() / ".openclaw" / "workspace",
    model="claude-opus-4-6",
    temperature=0.7
)
```

## API Reference

### SocraticDiscoverySkill

#### `start_discovery(topic: str) -> Dict`

Start a new Socratic discovery session.

**Parameters:**
- `topic` (str): The project or concept to discover

**Returns:**
```python
{
    "status": "started",
    "session_id": "discover_1234567890_abc",
    "topic": "AI-powered expense tracker",
    "question": "What problem does this solve?",
    "progress": {"step": 1}
}
```

#### `respond(session_id: str, response: str) -> Dict`

Record user response and get next question.

**Parameters:**
- `session_id` (str): Session ID from start_discovery
- `response` (str): User's response to previous question

**Returns:**
```python
{
    "status": "question_asked",
    "session_id": "discover_...",
    "question": "Who is your target user?",
    "progress": {"questions_asked": 2, "responses_recorded": 1}
}
```

#### `generate(session_id: str) -> Dict`

Generate project specification from discovery.

**Parameters:**
- `session_id` (str): Session ID from start_discovery

**Returns:**
```python
{
    "status": "spec_generated",
    "session_id": "discover_...",
    "spec": "# Expense Tracker\n\n## Overview\n...",
    "saved_to": "~/.openclaw/workspace/projects/expense-tracker/PROJECT.md",
    "artifacts": ["PROJECT.md", "REQUIREMENTS.md", "ARCHITECTURE.md"]
}
```

## Storage

Projects are stored in your workspace directory:

~/.openclaw/workspace/
├── projects/
│   ├── project-name-1/
│   │   ├── PROJECT.md
│   │   ├── REQUIREMENTS.md
│   │   ├── ARCHITECTURE.md
│   │   └── .session-*.json
│   └── project-name-2/
│
├── .socrates-vectors/     (ChromaDB embeddings)
├── .socrates-kb/          (Knowledge base)
└── .socratic-sessions.json (Session tracking)

All data is stored locally - no cloud upload.

## Examples

### Example 1: SaaS Product Discovery
```python
skill = SocraticDiscoverySkill()

# Start
result = await skill.start_discovery("SaaS collaboration platform")
print(f"Q1: {result['question']}")
# Q1: What problem does this solve for your target users?

# Respond
result = await skill.respond(result["session_id"], 
    "Helps distributed teams stay synchronized in real-time")
print(f"Q2: {result['question']}")
# Q2: Who is your primary target user segment?

# Continue...
result = await skill.respond(result["session_id"],
    "Engineering teams at startups and SMBs")

result = await skill.respond(result["session_id"],
    "Real-time presence, shared context, instant notifications")

# Generate
result = await skill.generate(result["session_id"])
print(result["spec"])
```

### Example 2: Integration with Custom Logic
```python
from socrates_openclaw import SocraticDiscoverySkill

class CustomProjectManager:
    def __init__(self):
        self.skill = SocraticDiscoverySkill()
    
    async def discover_and_save(self, topic: str):
        # Start discovery
        result = await self.skill.start_discovery(topic)
        session_id = result["session_id"]
        
        # Gather responses (e.g., from user input)
        responses = [
            "Tracks expenses automatically",
            "Finance managers",
            "Real-time categorization, receipt scanning",
            "Cloud-based, works offline"
        ]
        
        # Process each response
        for response in responses:
            result = await self.skill.respond(session_id, response)
        
        # Generate specification
        spec_result = await self.skill.generate(session_id)
        
        return spec_result
```

## Troubleshooting

### API Key Issues
```python
# Error: OpenAI key not found
# Solution:
export ANTHROPIC_API_KEY="sk-ant-..."

# Or in code:
import os
os.environ["ANTHROPIC_API_KEY"] = "your-key"
```

### Missing Dependencies
```bash
# If you get import errors:
pip install socrates-ai-openclaw[dev]

# This installs all dependencies including dev tools
```

### Storage Issues
```python
# Reset vector store (careful!)
import shutil
from pathlib import Path

vectors_dir = Path.home() / ".openclaw" / "workspace" / ".socrates-vectors"
if vectors_dir.exists():
    shutil.rmtree(vectors_dir)
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Write tests
4. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

## Support

- **GitHub Issues**: [Report bugs](https://github.com/Nireus79/Socrates/issues)
- **Documentation**: [Full docs](docs/)
- **Email**: support@socrates-ai.dev

## License

MIT License - see [LICENSE](LICENSE) file

## Acknowledgments

Built with:
- [socrates-ai](https://pypi.org/project/socrates-ai/) - Core library
- [Anthropic Claude](https://anthropic.com) - LLM
- [ChromaDB](https://www.trychroma.com/) - Vector storage
- [OpenClaw](https://openclaw.ai) - AI assistant platform

---

**Made with ❤️ for the Socrates and OpenClaw communities**