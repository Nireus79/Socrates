# Socrates AI - Complete Documentation

Welcome to **Socrates AI**, an AI-powered software development companion that guides you through projects using the Socratic method—asking thoughtful questions to help you clarify requirements, design systems, and write better code.

## Table of Contents

- [Quick Start](#quick-start)
- [What is Socratic?](#what-is-socratic)
- [Key Features](#key-features)
- [System Overview](#system-overview)
- [What's New in v1.3.0](#whats-new-in-v130)
- [Documentation Structure](#documentation-structure)
- [Getting Help](#getting-help)

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/Nireus79/Socrates.git
cd Socrates

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set API key
export ANTHROPIC_API_KEY="sk-ant-your-key-here"  # Or your API key
```

### Run the System

**Quick Start - Choose Your Interface:**

| Command | Description | Use Case |
|---------|-------------|----------|
| `python socrates.py` | CLI-only (default) | Interactive terminal, quick testing, learning |
| `python socrates.py --full` | Full stack (API + Frontend) | Web UI + programmatic access, full experience |
| `python socrates.py --api` | API server only | Integration with other tools, headless mode |
| `python socrates.py --frontend` | CLI + React frontend | Hybrid mode, visual + terminal interface |
| `python socrates.py --help` | Show all options | See all available commands |

**Example: Full Stack (Recommended for First Time)**
```bash
python socrates.py --full

# This starts:
# - API Server: http://localhost:8000
# - Web Frontend: http://localhost:5173
# - Browser opens automatically
```

**Example: API Server Only**
```bash
python socrates.py --api

# Starts API server
# API available at http://localhost:8000
# Auto-detects available port if 8000 is busy
```

**Example: Interactive CLI**
```bash
python socrates.py

# Starts command-line interface
# Interactive prompt for Socratic dialogue
```

**API Server with Custom Port:**
```bash
python socrates.py --api --port 9000

# Start on custom port (auto-detects if busy)
# Disable auto-detection with --no-auto-port
```

> **Note**: All startup commands are run from the project root directory where `socrates.py` is located.

---

## What is Socratic?

**Socrates AI** is a multi-agent AI system that:

1. **Guides Discovery** - Asks clarifying questions to deeply understand your project goals
2. **Ensures Consistency** - Detects conflicts between requirements, goals, and constraints
3. **Generates Code** - Creates production-ready code based on your project context
4. **Manages Knowledge** - Builds and maintains a knowledge base specific to your projects
5. **Tracks Progress** - Monitors project phases (discovery → analysis → design → implementation)

Named after **Socrates**, the ancient Greek philosopher who taught through questioning rather than lecturing, this system uses the same approach—helping you think through problems deeply by asking the right questions at the right time.

---

## Key Features

### Core Capabilities

| Feature | Description |
|---------|-------------|
| **Socratic Dialogue** | Multi-phase guided conversations (discovery, analysis, design, implementation) |
| **Smart Questioning** | AI-powered questions that adapt to your project context |
| **Conflict Detection** | Automatically identifies contradictions in requirements, goals, tech stack |
| **Code Generation** | Generates complete, documented code from project specifications |
| **Knowledge Management** | RAG-powered knowledge base with semantic search |
| **Project Tracking** | Track progress across multiple projects with detailed context |
| **Multi-User Support** | Collaboration-ready with user authentication and project sharing |
| **Event-Driven Architecture** | Real-time system notifications and integrations |

### Advanced Features

- **Vector Database (ChromaDB)** - Semantic search over documentation and project context
- **Conflict Resolution System** - Detects conflicts across tech stack, requirements, goals, constraints
- **Natural Language Understanding** - Type plain English commands instead of slash commands
- **Document Embedding** - Import PDFs, code files, and documentation to enrich context
- **Token Usage Tracking** - Monitor API costs and usage
- **Debug Mode** - Deep visibility into system operations for development

---

## System Overview

```
┌─────────────────────────────────────────────────────┐
│           User Interface (CLI / Web)                │
│    ┌─────────────────────────────────────────────┐  │
│    │  Project Management  │  Socratic Dialogue   │  │
│    │  Code Generation     │  Knowledge Search   │  │
│    │  Document Import     │  Collaboration      │  │
│    └─────────────────────────────────────────────┘  │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│         AgentOrchestrator (Central Hub)             │
│    Routes requests to 10 specialized agents        │
└──────────────────────┬──────────────────────────────┘
                       │
        ┌──────────────┼──────────────┐
        │              │              │
   ┌────▼────┐  ┌─────▼─────┐  ┌────▼────┐
   │ Project │  │ Socratic  │  │   Code  │
   │ Manager │  │ Counselor │  │Generator│
   └─────────┘  └───────────┘  └─────────┘
        │              │              │
        ├──────────────┼──────────────┤
        │              │              │
   ┌────▼────┐  ┌─────▼─────┐  ┌────▼────┐
   │ Context │  │ Conflict  │  │Knowledge│
   │Analyzer │  │ Detector  │  │ Manager │
   └─────────┘  └───────────┘  └─────────┘
        │              │              │
        └──────────────┼──────────────┘
                       │
        ┌──────────────┴──────────────┐
        │                             │
   ┌────▼──────────┐        ┌────────▼────┐
   │  Databases    │        │ Claude API  │
   │  ├─ Projects  │        │   (GPT)     │
   │  ├─ Users     │        │             │
   │  └─ Knowledge │        └─────────────┘
   │   (Vector DB) │
   └───────────────┘
```

---

## Documentation Structure

This documentation is organized for different audiences:

### For End Users

Start here if you want to **use the system**:
- **[USER_GUIDE.md](USER_GUIDE.md)** - How to create projects, ask questions, generate code
- **[INSTALLATION.md](INSTALLATION.md)** - Setup and first-time configuration
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions
- **[CONFIGURATION.md](CONFIGURATION.md)** - Customize system behavior

### For Developers

Start here if you want to **extend or contribute**:
- **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)** - Setting up dev environment, testing, submitting PRs
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - Deep dive into system design
- **[API_REFERENCE.md](API_REFERENCE.md)** - Complete API documentation for programmatic use

### For Project Stakeholders

Start here for **strategic information**:
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design and scalability
- **[API_REFERENCE.md](API_REFERENCE.md)** - Integration capabilities
- **[CONFIGURATION.md](CONFIGURATION.md)** - Enterprise deployment options

---

## Getting Help

### Documentation

- **[Architecture Guide](ARCHITECTURE.md)** - Understand how the system works
- **[API Reference](API_REFERENCE.md)** - Complete API documentation
- **[User Guide](USER_GUIDE.md)** - Step-by-step usage instructions
- **[Troubleshooting](TROUBLESHOOTING.md)** - Solve common problems
- **[Configuration](CONFIGURATION.md)** - Customize your setup
- **[Developer Guide](DEVELOPER_GUIDE.md)** - Contribute to the project

### In-System Help

Once running:
```
/help              # Show all available commands
/help command      # Show help for specific command
/info              # Display system information
/status            # Check system status
```

### Common Commands

```
# Project Management
/project create    # Create a new project
/project load      # Load existing project
/project list      # List all projects

# Socratic Dialogue
/continue          # Continue dialogue with next question
/advance           # Advance to next project phase
/hint              # Get a hint on current phase

# Code & Documentation
/code generate     # Generate code for current project
/docs generate     # Generate documentation

# Knowledge Management
/knowledge add     # Add to knowledge base
/document import   # Import PDF or code files

# Collaboration
/add_collaborator  # Add team member to project
/list_collaborators# Show project collaborators
```

---

## Project Phases

Every Socratic project progresses through 4 phases:

1. **Discovery** - What problem are we solving? Who are the users?
2. **Analysis** - What are the requirements and constraints?
3. **Design** - How will we build it? What's the architecture?
4. **Implementation** - Let's generate code and documentation!

Each phase includes guided questions and conflict detection to ensure clarity before moving forward.

---

## Core Concepts

### ProjectContext
Your project's complete specification including goals, requirements, tech stack, team structure, and conversation history. All information needed to generate code and continue dialogue.

### Agents
Specialized AI components that handle specific tasks (project management, code generation, conflict detection, etc.). The system has 10 agents working in concert.

### Knowledge Base
A semantic search engine (RAG) containing your project documentation, code standards, and best practices. Automatically populated and searchable.

### Conflict Detection
System that identifies contradictions between:
- Requirements vs. Goals
- Tech Stack compatibility
- Goals vs. Constraints
- Requirements vs. Constraints

---

## System Requirements

- **Python 3.8+**
- **4GB RAM** minimum
- **Internet connection** (for Claude API)
- **API Key** - Get one at [console.anthropic.com](https://console.anthropic.com)

---

## Architecture Highlights

- **Multi-Agent System** - 10 specialized agents coordinating via orchestrator
- **Event-Driven** - Pub/sub architecture for extensibility
- **Persistent Storage** - SQLite for project data, ChromaDB for knowledge
- **Semantic Search** - RAG-powered knowledge retrieval
- **Async-Ready** - Full async/await support for concurrent operations
- **Extensible** - Pluggable conflict checkers, custom agents, event listeners

---

## What's New in v1.3.0

### Spec Persistence System

**Persistent Project Specifications** - Project specifications are now automatically saved and retrieved, enabling:
- Specifications persist across sessions without loss
- Complete project context maintained in database
- Ability to load previous project specifications instantly
- Project specifications included in all knowledge base queries

**Impact**: Your project specifications are now truly persistent. No more worrying about losing critical project context between sessions.

### Improved Maturity Scoring

**Enhanced Project Maturity Calculation** - The system now provides more accurate project maturity assessment:
- Refined scoring algorithm for better accuracy
- More nuanced maturity levels (not just binary)
- Better detection of project completeness across phases
- Improved feedback on what's needed to advance

**Impact**: Get more reliable guidance on when your project specification is ready for code generation.

### Bug Fixes & Improvements

- Fixed issue where current question wasn't loading in suggestions modal
- Improved overall system stability and performance
- Enhanced documentation and examples

For a detailed changelog, see the commit history or [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Next Steps

1. **[Install the system](INSTALLATION.md)** (5 minutes)
2. **[Follow the user guide](USER_GUIDE.md)** (30 minutes)
3. **[Create your first project](USER_GUIDE.md#creating-your-first-project)** (15 minutes)
4. **[Explore advanced features](USER_GUIDE.md#advanced-usage)** (varies)

---

## Contributing

Interested in contributing? See [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) for:
- Development environment setup
- Code style and testing requirements
- How to add new agents or features
- Pull request process

---

## License

Socrates AI is released under the **MIT License**. See [LICENSE](../LICENSE) file for full details.

---

## Support

For issues, questions, or feature requests:
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Review [API_REFERENCE.md](API_REFERENCE.md)
- Submit an issue on GitHub
- Contact support at: [issues@github.com/Nireus79/Socrates](https://github.com/Nireus79/Socrates/issues)

---

## Citation

If you use Socratic in your research or project, please cite:

```bibtex
@software{socrates_ai_2025,
  title = {Socrates AI},
  author = {[Author Name]},
  year = {2025},
  url = {https://github.com/Nireus79/Socrates}
}
```

---

**Last Updated**: January 2026
**Version**: 1.3.0
