# Socratic RAG System - Complete Documentation

Welcome to the **Socratic RAG System**, an AI-powered software development companion that guides you through projects using the Socratic method—asking thoughtful questions to help you clarify requirements, design systems, and write better code.

## Table of Contents

- [Quick Start](#quick-start)
- [What is Socratic?](#what-is-socratic)
- [Key Features](#key-features)
- [System Overview](#system-overview)
- [Documentation Structure](#documentation-structure)
- [Getting Help](#getting-help)

---

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/your-org/socrates.git
cd socrates

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set API key
export ANTHROPIC_API_KEY="sk-ant-your-key-here"  # Or your API key
```

### Run the System

**Option 1: Full Stack (API + React Frontend)**
```bash
# Start both API server and web frontend together
python socrates.py --full

# This starts:
# - API Server: http://localhost:8000
# - Web Frontend: http://localhost:5173
```

**Option 2: API Server Only**
```bash
python socrates.py --api
# API Server: http://localhost:8000
```

**Option 3: Interactive CLI (Default)**
```bash
python socrates.py
```

Choose the interface that works best for you:
- **Web Frontend** (`--full`): Visual project management, collaborative features
- **API Server** (`--api`): Programmatic access, integration with other tools
- **CLI** (default): Terminal-based interface, quick testing

---

## What is Socratic?

The **Socratic RAG System** is a multi-agent AI system that:

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

[Specify your license here]

---

## Support

For issues, questions, or feature requests:
- Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Review [API_REFERENCE.md](API_REFERENCE.md)
- Submit an issue on GitHub
- Contact support at [support email]

---

## Citation

If you use Socratic in your research or project, please cite:

```bibtex
@software{socratic_rag_2025,
  title = {Socratic RAG System},
  author = {[Author Name]},
  year = {2025},
  url = {https://github.com/your-org/socrates}
}
```

---

**Last Updated**: December 2025
**Version**: 7.0
