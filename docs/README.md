# Socratic RAG Enhanced v7.3.0

> AI-powered project development through intelligent Socratic questioning and automated code generation

[![Python Version](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-3.0.3-green.svg)](https://flask.palletsprojects.com/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Transform your project ideas into working applications through AI-powered Socratic questioning, intelligent code generation, and automated development workflows.

---

## 🌟 Features

### **Intelligent Agent System**
- **8 Specialized AI Agents** working in harmony
- Role-based questioning (Project Manager, Developer, Designer, QA, etc.)
- Context-aware conversation management
- Conflict detection and resolution

### **Automated Code Generation**
- Multi-file project structure generation
- Support for multiple frameworks (Flask, React, FastAPI, etc.)
- Proper architecture (not monolithic scripts)
- Comprehensive testing suite generation
- Documentation auto-generation

### **Web Interface**
- Modern, responsive dashboard
- Real-time agent status monitoring
- Project management interface
- Socratic conversation sessions
- Code generation and testing UI

### **Advanced Features**
- Vector-based knowledge storage (ChromaDB)
- Git integration for version control
- IDE synchronization (VS Code)
- Multi-format export (ZIP, JSON, Docker)
- Performance monitoring and analytics

---

## 📋 Prerequisites

- **Python 3.8+** (Python 3.12 may have compatibility issues with some packages)
- **pip** (Python package manager)
- **Git** (for version control features)
- **Anthropic API Key** (for Claude AI integration)

---

## 🚀 Quick Start

### **1. Clone the Repository**
```bash
git clone https://github.com/your-username/socratic-rag-enhanced.git
cd socratic-rag-enhanced
```

### **2. Create Virtual Environment**
```bash
# Windows
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

### **3. Install Dependencies**
```bash
pip install -r requirements.txt
```

### **4. Configure API Keys (Optional)**
```bash
# Create .env file or edit config.yaml
echo "ANTHROPIC_API_KEY=your-api-key-here" > .env
```

### **5. Run the Application**
```bash
python run.py
```

### **6. Access the Web Interface**
Open your browser and navigate to:
```
http://localhost:5000
```

---

## 📖 Usage

### **Creating Your First Project**

1. **Navigate to Projects**
   - Click "Projects" in the navigation menu
   - Click "Create New Project"

2. **Fill in Project Details**
   - Project name and description
   - Technology stack preferences
   - Requirements and constraints
   - Timeline and priority

3. **Start Socratic Session**
   - Choose your role (Developer, Manager, etc.)
   - Answer AI-generated questions
   - System learns from your responses

4. **Generate Code**
   - Review specifications
   - Click "Generate Code"
   - Download or sync to IDE

### **Working with Agents**

The system includes 8 specialized agents:

| Agent | Purpose |
|-------|---------|
| **Orchestrator** | Coordinates all agent activities |
| **Socratic Counselor** | Manages questioning sessions |
| **Code Generator** | Creates project code and tests |
| **Project Manager** | Tracks progress and resources |
| **User Manager** | Handles authentication and roles |
| **Context Analyzer** | Detects conflicts and insights |
| **Document Processor** | Analyzes uploaded files |
| **System Monitor** | Monitors performance and health |

---

## 🏗️ Architecture

```
socratic-rag-enhanced/
├── src/
│   ├── agents/          # 8 specialized AI agents
│   ├── services/        # External integrations
│   ├── database/        # SQLite + repositories
│   ├── models.py        # Data models
│   └── core.py          # Core utilities
├── web/
│   ├── templates/       # HTML templates
│   ├── static/          # CSS, JS, images
│   └── app.py           # Flask application
├── tests/               # Test suite
├── data/                # Database and uploads
├── docs/                # Documentation
├── config.yaml          # Configuration
├── requirements.txt     # Python dependencies
└── run.py              # Application entry point
```

---

## ⚙️ Configuration

### **config.yaml**
```yaml
app:
  name: "Socratic RAG Enhanced"
  version: "7.3.0"
  debug: false

web:
  host: "0.0.0.0"
  port: 5000
  secret_key: "change-this-in-production"

database:
  path: "data/projects.db"

services:
  anthropic:
    api_key: "${ANTHROPIC_API_KEY}"
    model: "claude-sonnet-4"
  
  vector:
    provider: "chromadb"
    persist_directory: "data/vector_db"
```

### **Environment Variables**
```bash
# Required for AI features
ANTHROPIC_API_KEY=your-api-key

# Optional
FLASK_ENV=development
SOCRATIC_DEBUG=true
```

---

## 🧪 Testing

### **Run All Tests**
```bash
python tests/test_agents_.py
```

### **Expected Output**
```
Total Tests: 45
Passed: 45
Failed: 0
Warnings: 0

🎉 ALL TESTS PASSED!
```

### **Test Individual Components**
```bash
# Test specific agent
pytest tests/test_agents/test_socratic.py

# Test with coverage
pytest --cov=src tests/
```

---

## 📊 System Requirements

### **Minimum**
- **CPU:** Dual-core processor
- **RAM:** 4GB
- **Storage:** 2GB free space
- **OS:** Windows 10/macOS 10.14+/Linux

### **Recommended**
- **CPU:** Quad-core processor
- **RAM:** 8GB or more
- **Storage:** 10GB free space
- **OS:** Windows 11/macOS 12+/Ubuntu 20.04+

---

## 🔧 Troubleshooting

### **Common Issues**

**1. Import Errors**
```bash
# Solution: Reinstall dependencies
pip install --upgrade -r requirements.txt
```

**2. CSRF Token Errors**
```bash
# Check that Flask-WTF is installed
pip install Flask-WTF
```

**3. Database Errors**
```bash
# Delete and recreate database
rm data/projects.db
python run.py
```

**4. Port Already in Use**
```bash
# Run on different port
python run.py --port 8080
```

**5. Agent Health Issues**
```bash
# Check agent status in logs
python run.py --debug
```

---

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

### **Development Setup**
```bash
# Install development dependencies
pip install -r requirements.txt
pip install pytest black flake8

# Format code
black src/ tests/

# Run linter
flake8 src/ tests/

# Run tests
pytest
```

---

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Anthropic** - Claude AI API
- **ChromaDB** - Vector database
- **Flask** - Web framework
- **Sentence Transformers** - Text embeddings
- **Bootstrap** - UI framework

---

## 📞 Support

- **Documentation:** [docs/](docs/)
- **Issues:** [GitHub Issues](https://github.com/your-username/socratic-rag-enhanced/issues)
- **Email:** support@socratic-rag.com

---

## 🗺️ Roadmap

### **Version 7.4.0** (Next)
- [ ] Enhanced role-based questioning
- [ ] Advanced code templates
- [ ] Real-time collaboration

### **Version 8.0.0** (Future)
- [ ] Plugin architecture
- [ ] Multi-AI model support
- [ ] Enterprise features
- [ ] Cloud deployment

---

**Made with ❤️ by the Socratic RAG Team**
