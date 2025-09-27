# 🧠 Socratic RAG Enhanced

**AI-Powered Project Development Through Intelligent Questioning**

![Version](https://img.shields.io/badge/version-7.3.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)
![Status](https://img.shields.io/badge/status-active-success.svg)

---

## 🎯 Vision & Mission

Transform project ideas into complete, working applications through intelligent Socratic questioning and automated code generation. Socratic RAG Enhanced uses role-based AI agents to guide project development through structured conversations, automatically generating enterprise-grade code with proper architecture, comprehensive testing, and IDE integration.

### **Evolution from Legacy Approach:**

```
❌ OLD: Questions → Basic Specs → ONE MONOLITHIC SCRIPT → Manual Implementation

✅ NEW: Role-Based Questions → Detailed Specifications → Architectural Breakdown → 
        Organized Multi-File Structure → IDE Integration → Testing → Correction → 
        Working Application
```

---

## ✨ Key Features

### 🤖 **Intelligent Agent System**
- **8 Specialized Agents**: Each with focused responsibilities and capabilities
- **Role-Based Questioning**: 7+ role types (PM, Tech Lead, Developer, Designer, QA, Business Analyst, DevOps)
- **Agent Orchestration**: Coordinated multi-agent workflows
- **Context-Aware Processing**: Agents learn and adapt to project context

### 💻 **Advanced Code Generation**
- **Multi-File Architecture**: Generates organized project structures (not monolithic scripts)
- **Enterprise-Grade Code**: Proper separation of concerns, design patterns, best practices
- **Comprehensive Testing**: Unit, integration, security, and performance tests
- **Intelligent Error Correction**: Automatic detection and fixing of code issues

### 🔧 **Complete Development Pipeline**
- **Socratic Discovery**: Deep requirements gathering through intelligent questioning
- **Architectural Design**: Proper application architecture planning
- **Code Generation**: Multi-file, production-ready code
- **IDE Integration**: Seamless integration with VS Code and other IDEs
- **Testing & Validation**: Automated testing with failure analysis
- **Deployment Ready**: Complete applications ready for production

### 🌐 **Web Interface & Services**
- **Modern Web UI**: Flask-based interface with real-time updates
- **Multiple Integrations**: Claude API, ChromaDB, Git, IDE services
- **Project Management**: Full project lifecycle management
- **Team Collaboration**: Multi-user support with role-based access

---

## 🏗️ System Architecture

### **Modular Agent Architecture**

```
📊 Complete Modular Agent Architecture
├── 🎯 AgentOrchestrator        # Coordination and request routing
├── 💬 SocraticCounselorAgent   # Intelligent questioning system
├── 💻 CodeGeneratorAgent       # Multi-file code generation
├── 📊 ProjectManagerAgent      # Project lifecycle management
├── 👥 UserManagerAgent         # User authentication & management
├── 🧠 ContextAnalyzerAgent     # Context analysis & conflict detection
├── 📄 DocumentProcessorAgent   # Document processing & knowledge extraction
├── 🔍 SystemMonitorAgent       # System monitoring & analytics
└── 🛠️ ServicesAgent           # External services & integrations
```

### **Technology Stack**
- **Backend**: Python 3.8+, Flask, SQLite/PostgreSQL
- **AI/ML**: Anthropic Claude API, ChromaDB, SentenceTransformers
- **Frontend**: HTML5, CSS3, JavaScript, HTMX, Bootstrap
- **Services**: Git integration, VS Code extension, Docker support
- **Testing**: pytest, coverage, security scanning

---

## 🚀 Quick Start

### **Prerequisites**

- Python 3.8 or higher
- pip package manager
- Git (for code generation features)
- VS Code (recommended for IDE integration)

### **Installation**

1. **Clone the repository**
   ```bash
   git clone https://github.com/your-username/socratic-rag-enhanced.git
   cd socratic-rag-enhanced
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure the system**
   ```bash
   cp config.yaml.example config.yaml
   # Edit config.yaml with your settings
   ```

5. **Set up API keys** (optional but recommended)
   ```bash
   export ANTHROPIC_API_KEY="your-claude-api-key"
   ```

6. **Run the application**
   ```bash
   python run.py
   ```

7. **Access the web interface**
   - Open your browser to http://127.0.0.1:5000
   - Start your first intelligent project development session!

---

## 📖 Usage Guide

### **Basic Workflow**

1. **Create a New Project**
   - Access the web interface
   - Click "New Project" and provide basic project information
   - The system will guide you through role-based questioning

2. **Socratic Discovery Phase**
   - Answer questions from different role perspectives:
     - **Project Manager**: Timeline, resources, stakeholders
     - **Technical Lead**: Architecture, performance, security
     - **Developer**: Features, data flow, APIs
     - **QA/Tester**: Edge cases, quality metrics
     - **Business Analyst**: Requirements, compliance, reporting

3. **Code Generation**
   - System analyzes your responses and designs architecture
   - Generates complete, organized multi-file project structure
   - Includes backend, frontend, database, tests, and documentation

4. **Testing & Validation**
   - Automatic execution of comprehensive test suite
   - Performance benchmarking and security scanning
   - Intelligent error detection and correction

5. **IDE Integration**
   - Generated files pushed directly to your development environment
   - Ready-to-run application with proper configuration
   - Complete with debugging setup and development server

### **Advanced Features**

- **Conflict Detection**: Identifies and resolves requirement conflicts
- **Team Collaboration**: Multi-user projects with role-based access
- **Version Control**: Integrated Git workflows
- **Export Options**: ZIP, JSON, Docker containerization
- **Analytics**: Project insights and development metrics

---

## ⚙️ Configuration

### **Basic Configuration**

Edit `config.yaml` to customize your installation:

```yaml
# Core application settings
app:
  name: "Socratic RAG Enhanced"
  version: "7.3.0"
  debug: true
  secret_key: "your-secret-key-change-in-production"

# Database configuration
database:
  sqlite:
    path: "data/projects.db"
  vector:
    path: "data/vector_db"

# Agent system settings
agents:
  global:
    max_concurrent: 5
    timeout_seconds: 300
  
  code_generator:
    max_files_per_project: 500
    testing_enabled: true
    security_scanning: true

# External services
services:
  claude:
    api_key: "your-anthropic-api-key"
    model: "claude-3-5-sonnet-20241022"
    max_tokens: 8192
```

### **Environment Variables**

```bash
# Required for full AI functionality
ANTHROPIC_API_KEY=your-claude-api-key

# Optional overrides
SOCRATIC_DEBUG=true
SOCRATIC_DATABASE_PATH=custom/path/projects.db
SOCRATIC_LOG_LEVEL=INFO
```

---

## 🧪 Development & Testing

### **Running Tests**

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test categories
pytest tests/test_agents/        # Agent tests
pytest tests/test_core.py        # Core system tests
pytest tests/test_integration.py # Integration tests
```

### **Development Mode**

```bash
# Run with debug mode and auto-reload
python run.py --debug

# Run with custom configuration
python run.py --config development.yaml

# Run on custom host/port
python run.py --host 0.0.0.0 --port 8080
```

### **Code Quality**

```bash
# Linting and formatting
flake8 src/
black src/
isort src/

# Type checking
mypy src/

# Security scanning
bandit -r src/
```

---

## 📁 Project Structure

```
socratic-rag-enhanced/
├── 📋 README.md                    # This file
├── 📋 requirements.txt             # Python dependencies
├── ⚙️ config.yaml                  # System configuration
├── 🚀 run.py                       # Main application entry point
│
├── 📁 src/                         # Core system code
│   ├── 🔧 core.py                  # Core infrastructure
│   ├── 📊 models.py                # Data models
│   ├── 🗄️ database.py             # Database layer
│   ├── 🔨 utils.py                 # Utility functions
│   │
│   ├── 📁 agents/                  # 🤖 Modular agent system
│   │   ├── base.py                 # Base agent class
│   │   ├── orchestrator.py         # Agent coordination
│   │   ├── socratic.py             # Socratic questioning
│   │   ├── code.py                 # Code generation
│   │   ├── project.py              # Project management
│   │   ├── user.py                 # User management
│   │   ├── context.py              # Context analysis
│   │   ├── document.py             # Document processing
│   │   ├── monitor.py              # System monitoring
│   │   └── services.py             # External services
│   │
│   └── 📁 services/                # External integrations
│       ├── claude_service.py       # Claude API
│       ├── vector_service.py       # ChromaDB
│       ├── git_service.py          # Git operations
│       └── ide_service.py          # IDE integration
│
├── 📁 web/                         # Web interface
│   ├── 🌐 app.py                   # Flask application
│   ├── 📁 templates/               # HTML templates
│   └── 📁 static/                  # CSS, JS, images
│
├── 📁 tests/                       # Test suite
│   ├── 🔬 test_core.py             # Core tests
│   ├── 📁 test_agents/             # Agent tests
│   ├── 🛠️ test_services.py         # Service tests
│   ├── 🌐 test_web.py              # Web tests
│   └── 🔗 test_integration.py      # Integration tests
│
├── 📁 data/                        # Runtime data (created automatically)
│   ├── 🗄️ projects.db             # SQLite database
│   ├── 📁 vector_db/               # ChromaDB storage
│   ├── 📁 uploads/                 # File uploads
│   ├── 📁 exports/                 # Generated exports
│   ├── 📁 generated_projects/      # Generated code
│   └── 📁 logs/                    # Application logs
│
└── 📁 docs/                        # Documentation
    ├── 📖 user_guide.md            # User documentation
    ├── 👩‍💻 developer_guide.md        # Development guide
    └── 📁 agents/                   # Agent documentation
```

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### **Development Setup**

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes and add tests
4. Ensure all tests pass: `pytest`
5. Commit your changes: `git commit -m 'Add amazing feature'`
6. Push to the branch: `git push origin feature/amazing-feature`
7. Open a Pull Request

### **Areas for Contribution**

- 🤖 New specialized agents
- 🔧 Enhanced code generation templates
- 🌐 UI/UX improvements
- 📊 Analytics and monitoring features
- 🔌 New service integrations
- 📝 Documentation improvements
- 🧪 Test coverage expansion

---

## 📊 Roadmap

### **Version 7.4.0 (Next Release)**
- [ ] Advanced template system for code generation
- [ ] Real-time collaboration features
- [ ] Enhanced security scanning
- [ ] Performance optimization dashboard

### **Version 8.0.0 (Major Release)**
- [ ] Plugin architecture for custom agents
- [ ] Advanced AI model support (GPT-4, Gemini)
- [ ] Enterprise SSO integration
- [ ] Cloud deployment automation

### **Future Versions**
- [ ] Mobile application
- [ ] Advanced project analytics
- [ ] AI-powered code review
- [ ] Marketplace for templates and agents

---

## 🆘 Support & Documentation

### **Getting Help**

- 📖 **Documentation**: Check the `docs/` directory
- 🐛 **Bug Reports**: Create an issue on GitHub
- 💡 **Feature Requests**: Open a discussion on GitHub
- 💬 **Community**: Join our Discord server
- 📧 **Email**: support@socratic-rag.com

### **Common Issues**

**Q: The system shows "Claude API key not configured" warnings**
A: Add your Anthropic API key to config.yaml or set the ANTHROPIC_API_KEY environment variable.

**Q: Import errors when starting the system**
A: Ensure all dependencies are installed: `pip install -r requirements.txt`

**Q: Database connection errors**
A: Check that the data directory is writable and SQLite is properly installed.

**Q: Web interface not accessible**
A: Verify the port is not in use and firewall settings allow local connections.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Anthropic** for the Claude API that powers our intelligent questioning
- **ChromaDB** for vector storage and similarity search
- **Sentence Transformers** for embedding generation
- **Flask** community for the excellent web framework
- **The Open Source Community** for the amazing tools that make this possible

---

## 📈 Stats & Metrics

![GitHub stars](https://img.shields.io/github/stars/your-username/socratic-rag-enhanced)
![GitHub forks](https://img.shields.io/github/forks/your-username/socratic-rag-enhanced)
![GitHub issues](https://img.shields.io/github/issues/your-username/socratic-rag-enhanced)
![GitHub pull requests](https://img.shields.io/github/issues-pr/your-username/socratic-rag-enhanced)

**Project Metrics:**
- 🤖 8 Specialized Agents
- 🔧 35+ Core Files
- 📊 78 Agent Capabilities
- 🧪 80%+ Test Coverage
- 📦 Multi-Platform Support
- 🌐 Enterprise Ready

---

*Built with ❤️ by the Socratic RAG Enhanced team*

**Transform your ideas into working applications through the power of intelligent questioning.**