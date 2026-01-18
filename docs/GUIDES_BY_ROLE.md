# Getting Started by Role

Choose your role to find the documentation that's right for you.

---

## 👤 End User (Non-Technical)

**You want to**: Use Socrates AI to clarify project requirements and get guidance.

**Start here**:
1. **[WINDOWS_SETUP_GUIDE.md](WINDOWS_SETUP_GUIDE.md)** (if on Windows)
   - Download and install the .exe file
   - First-run walkthrough
   - Troubleshooting for common issues

2. **[INSTALLATION.md](INSTALLATION.md)** (if on Mac/Linux)
   - Setup instructions for your OS
   - Creating virtual environment
   - Running the application

3. **[USER_GUIDE.md](USER_GUIDE.md)** ⭐ **Start here!**
   - How to create your first project
   - Understanding the Socratic dialogue
   - Step-by-step project walkthrough
   - Common commands explained in plain English

4. **[v1.3.0_RELEASE_NOTES.md](v1.3.0_RELEASE_NOTES.md)** (optional)
   - What's new in the latest version
   - Feature highlights

**When you need help**:
- **Can't login?** → [TROUBLESHOOTING.md](TROUBLESHOOTING.md) → "Installation Issues"
- **Project not saving?** → [TROUBLESHOOTING.md](TROUBLESHOOTING.md) → "Dialogue & Project Issues"
- **Computer running slow?** → [TROUBLESHOOTING.md](TROUBLESHOOTING.md) → "Performance Issues"
- **Want to manage projects?** → [PROJECT_MAINTENANCE.md](PROJECT_MAINTENANCE.md)

---

## 💼 Team Lead / Project Manager

**You want to**: Manage multiple projects and help your team use Socrates effectively.

**Start here**:
1. **[USER_GUIDE.md](USER_GUIDE.md)** ⭐ **Start here!**
   - Master all features so you can guide your team
   - Understand the full workflow

2. **[PROJECT_MAINTENANCE.md](PROJECT_MAINTENANCE.md)**
   - How to organize and archive projects
   - Managing team projects
   - Storage quotas and limits
   - Backup and recovery procedures

3. **[CONFIGURATION.md](CONFIGURATION.md)** - Optional
   - Setting up shared data directory
   - Team authentication setup
   - Custom knowledge base for team standards

4. **[v1.3.0_RELEASE_NOTES.md](v1.3.0_RELEASE_NOTES.md)**
   - What's new for your team
   - Upgrade planning

**Team Management Tasks**:
- Organizing projects by team/phase
- Cleaning up old projects
- Sharing project contexts
- Setting team standards in knowledge base

**Recommended workflow**:
1. Create project for each team initiative
2. Document team's architecture standards in knowledge base
3. Archive completed projects regularly
4. Refer team members to [USER_GUIDE.md](USER_GUIDE.md) for learning

---

## 🔧 Developer / Engineer

**You want to**: Integrate Socrates into your development workflow and contribute to the project.

**Start here**:
1. **[INSTALLATION.md](INSTALLATION.md)** or **[WINDOWS_SETUP_GUIDE.md](WINDOWS_SETUP_GUIDE.md)**
   - Get it running on your machine

2. **[USER_GUIDE.md](USER_GUIDE.md)**
   - Learn the full workflow
   - Understand all features

3. **[ARCHITECTURE.md](ARCHITECTURE.md)** ⭐ **Start here for technical details!**
   - How the system works internally
   - Multi-agent architecture
   - Event-driven communication
   - Database design

4. **[API_REFERENCE.md](API_REFERENCE.md)**
   - Complete API documentation
   - Programmatic integration examples
   - All available endpoints

5. **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)**
   - Setting up dev environment
   - Running tests
   - Code style and standards
   - How to contribute

**Common Development Tasks**:
```bash
# Run in API-only mode for integration
python socrates.py --api

# Run with debug logging
export SOCRATES_LOG_LEVEL=DEBUG
python socrates.py

# Use programmatic API
from socratic_system.orchestration import AgentOrchestrator
orchestrator = AgentOrchestrator("sk-ant-...")
```

**Contributing**:
- Fork the repository
- Follow [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)
- Submit pull requests
- Report issues on GitHub

---

## 📊 API Integrator

**You want to**: Integrate Socrates AI into your existing systems and applications.

**Start here**:
1. **[API_REFERENCE.md](API_REFERENCE.md)** ⭐ **Start here!**
   - Complete API documentation
   - All available endpoints
   - Request/response formats
   - Error handling

2. **[CONFIGURATION.md](CONFIGURATION.md)**
   - Programmatic configuration
   - Using ConfigBuilder
   - Environment variables

3. **[ARCHITECTURE.md](ARCHITECTURE.md)**
   - System design (background knowledge)
   - Event system for notifications
   - Database models

**Quick Start**:
```python
from socratic_system.orchestration import AgentOrchestrator
from socratic_system.config import ConfigBuilder

# Configure
config = ConfigBuilder("sk-ant-...") \
    .with_log_level("INFO") \
    .build()

# Create orchestrator
orchestrator = AgentOrchestrator(config)

# Use API
result = orchestrator.process_request('project_manager', {
    'action': 'create_project',
    'project_name': 'My Integrated Project',
    'owner': 'system'
})

project_id = result['project']['id']
```

**Common Integration Patterns**:
- Create projects programmatically
- Generate code for specifications
- Monitor project progress
- Export results to external systems
- Emit events for system integration

---

## 🔬 Data Scientist / Researcher

**You want to**: Use Socrates for research projects and data analysis.

**Start here**:
1. **[USER_GUIDE.md](USER_GUIDE.md)**
   - Learn the basic workflow
   - Understand project phases

2. **[API_REFERENCE.md](API_REFERENCE.md)**
   - Programmatic access to data
   - Batch processing capabilities

3. **[CONFIGURATION.md](CONFIGURATION.md)**
   - Tuning for your use case
   - Performance optimization
   - Using different Claude models

4. **[ARCHITECTURE.md](ARCHITECTURE.md)**
   - Understanding the knowledge base
   - Vector search capabilities
   - Data structures

**Research Workflows**:
```python
# Batch create projects from dataset
for dataset_item in my_dataset:
    result = orchestrator.process_request('project_manager', {
        'action': 'create_project',
        'project_name': dataset_item['name']
    })

# Export results for analysis
orchestrator.process_request('project_manager', {
    'action': 'export_project',
    'project_id': project_id,
    'format': 'json'
})
```

**Recommended Setup**:
- Use Haiku model for cost efficiency
- Reduce context length for faster processing
- Batch operations for multiple projects
- Export results in JSON for analysis

---

## 📝 Technical Writer / Documentation

**You want to**: Understand the system to write effective documentation.

**Start here**:
1. **[USER_GUIDE.md](USER_GUIDE.md)**
   - Feature overview from user perspective

2. **[ARCHITECTURE.md](ARCHITECTURE.md)** ⭐ **Start here for technical content!**
   - System design and components
   - Technical concepts and terminology
   - Data flow diagrams

3. **[API_REFERENCE.md](API_REFERENCE.md)**
   - API details for technical docs
   - Code examples and use cases

4. **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)**
   - Development workflows for how-tos

**Documentation Areas**:
- Getting started guides
- Feature explanations
- API documentation
- Troubleshooting guides
- Tutorial videos/content

---

## 🏢 System Administrator / DevOps

**You want to**: Deploy and maintain Socrates at scale.

**Start here**:
1. **[INSTALLATION.md](INSTALLATION.md)** → Kubernetes section
   - Docker deployment
   - Kubernetes configuration
   - Production setup

2. **[CONFIGURATION.md](CONFIGURATION.md)**
   - Environment variables
   - Security configuration
   - Performance tuning
   - Multi-user setup
   - Data directory permissions

3. **[PROJECT_MAINTENANCE.md](PROJECT_MAINTENANCE.md)**
   - Backup strategies
   - Database maintenance
   - Monitoring and logs
   - Cleanup procedures

4. **[ARCHITECTURE.md](ARCHITECTURE.md)**
   - System scalability
   - Database design
   - Storage requirements

**Deployment Tasks**:
```bash
# Docker deployment
docker build -t socrates:1.3.0 .
docker run -e ANTHROPIC_API_KEY="sk-ant-..." \
  -v socrates_data:/data \
  -p 8000:8000 \
  -p 5173:5173 \
  socrates:1.3.0

# Kubernetes
kubectl apply -f k8s/deployment.yaml
kubectl apply -f k8s/service.yaml
```

**Operational Checklists**:
- [ ] Regular backups scheduled
- [ ] Logs monitored and rotated
- [ ] Database optimized monthly
- [ ] Security patches applied
- [ ] Resource usage monitored

---

## 🚀 Open Source Contributor

**You want to**: Contribute code, documentation, or features to Socrates.

**Start here**:
1. **[CONTRIBUTING.md](../CONTRIBUTING.md)** ⭐ **Start here!**
   - Contribution guidelines
   - Ways to help (code, docs, community)
   - PR process

2. **[DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md)**
   - Development environment setup
   - Testing procedures
   - Code style standards

3. **[ARCHITECTURE.md](ARCHITECTURE.md)**
   - System design understanding
   - How to add new features
   - How to add new agents

4. **[GITHUB_SPONSORS_SETUP.md](../GITHUB_SPONSORS_SETUP.md)** (Optional)
   - Learn about sponsorship system
   - Consider contributing code for paid tier features

**Ways to Contribute**:
- Fix bugs from GitHub Issues
- Add new features
- Improve documentation
- Write tests
- Report issues
- Help in discussions

**Getting Started**:
```bash
git clone https://github.com/Nireus79/Socrates.git
cd Socrates
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install -e .  # Install in editable mode
pytest  # Run tests
```

---

## 💰 Sponsor / Business Partner

**You want to**: Understand business model and sponsorship.

**Start here**:
1. **[SPONSORSHIP.md](../SPONSORSHIP.md)** ⭐ **Start here!**
   - Sponsorship tiers and benefits
   - Payment process
   - FAQ

2. **[TIERS_AND_SUBSCRIPTIONS.md](TIERS_AND_SUBSCRIPTIONS.md)**
   - Detailed tier comparison
   - Feature availability
   - Storage quotas
   - Billing information

3. **[v1.3.0_RELEASE_NOTES.md](v1.3.0_RELEASE_NOTES.md)**
   - Recent improvements
   - Product roadmap

**Sponsorship Benefits**:
- Enhanced storage and quotas
- Priority support
- Early access to new features
- Sponsor recognition

**Sponsor now**: [github.com/sponsors/Nireus79](https://github.com/sponsors/Nireus79)

---

## 🎓 Educator / Trainer

**You want to**: Teach others how to use Socrates AI.

**Start here**:
1. **[USER_GUIDE.md](USER_GUIDE.md)** ⭐ **Start here!**
   - Complete feature overview
   - Step-by-step examples

2. **[INSTALLATION.md](INSTALLATION.md)** or **[WINDOWS_SETUP_GUIDE.md](WINDOWS_SETUP_GUIDE.md)**
   - Setup instructions for students
   - Troubleshooting common issues

3. **[PROJECT_MAINTENANCE.md](PROJECT_MAINTENANCE.md)**
   - Managing student projects
   - Cleanup and organization

4. **[CONFIGURATION.md](CONFIGURATION.md)** (Optional)
   - Setting up shared classroom environment
   - Student account setup

**Teaching Resources**:
- Step-by-step guides: [USER_GUIDE.md](USER_GUIDE.md)
- Troubleshooting: [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- Project management: [PROJECT_MAINTENANCE.md](PROJECT_MAINTENANCE.md)
- Reference: [API_REFERENCE.md](API_REFERENCE.md)

**Course Idea**:
1. Module 1: Getting Started (USER_GUIDE.md)
2. Module 2: Project Management (PROJECT_MAINTENANCE.md)
3. Module 3: Advanced Techniques (API_REFERENCE.md)
4. Module 4: Custom Integration (API_REFERENCE.md)

---

## 🤔 Still Not Sure?

**Quick Reference by Task**:

| I want to... | Go to... |
|---|---|
| Install on Windows | [WINDOWS_SETUP_GUIDE.md](WINDOWS_SETUP_GUIDE.md) |
| Install on Mac/Linux | [INSTALLATION.md](INSTALLATION.md) |
| Create my first project | [USER_GUIDE.md](USER_GUIDE.md) |
| Integrate via API | [API_REFERENCE.md](API_REFERENCE.md) |
| Understand the architecture | [ARCHITECTURE.md](ARCHITECTURE.md) |
| Fix a problem | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| Manage projects | [PROJECT_MAINTENANCE.md](PROJECT_MAINTENANCE.md) |
| Set up for production | [CONFIGURATION.md](CONFIGURATION.md) + [INSTALLATION.md](INSTALLATION.md) |
| Contribute code | [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) |
| Get technical support | [TROUBLESHOOTING.md](TROUBLESHOOTING.md) |
| Learn what's new | [v1.3.0_RELEASE_NOTES.md](v1.3.0_RELEASE_NOTES.md) |
| Sponsor the project | [SPONSORSHIP.md](../SPONSORSHIP.md) |

---

## Documentation Index

**Quick Links to All Documentation:**
- [README.md](README.md) - Project overview
- [INDEX.md](INDEX.md) - Master documentation index
- [INSTALLATION.md](INSTALLATION.md) - Setup guide
- [USER_GUIDE.md](USER_GUIDE.md) - User tutorial
- [WINDOWS_SETUP_GUIDE.md](WINDOWS_SETUP_GUIDE.md) - Windows-specific guide
- [ARCHITECTURE.md](ARCHITECTURE.md) - Technical deep-dive
- [API_REFERENCE.md](API_REFERENCE.md) - API documentation
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) - Development guide
- [CONFIGURATION.md](CONFIGURATION.md) - Configuration reference
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Troubleshooting guide
- [PROJECT_MAINTENANCE.md](PROJECT_MAINTENANCE.md) - Project management
- [v1.3.0_RELEASE_NOTES.md](v1.3.0_RELEASE_NOTES.md) - What's new
- [CONTRIBUTING.md](../CONTRIBUTING.md) - How to contribute
- [SPONSORSHIP.md](../SPONSORSHIP.md) - Sponsorship info

---

**Last Updated**: January 2026
**Version**: 1.3.0
