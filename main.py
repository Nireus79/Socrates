# socratic-rag-enhanced/
# │
# ├── 📋 README.md
# ├── 📋 requirements.txt
# ├── ⚙️  config.yaml
# ├── 🚀 run.py                        # Main application entry point
# │
# ├── 📁 src/
# │   ├── __init__.py
# │   │
# │   ├── 🔧 core.py                   # Config, exceptions, logging, database, events
# │   ├── 📊 models.py                 # User, Project, Module, Task, Role, TechnicalSpec
# │   ├── 🗄️  database.py              # SQLite manager + All repositories
# │   ├── 🔨 utils.py                  # File processor, Document parser, Validation
# │   │
# │   ├── 📁 agents/                   # ✨ MODULAR AGENT ARCHITECTURE
# │   │   ├── __init__.py              # ~50 lines  - Exports & initialization
# │   │   ├── base.py                  # ~200 lines - BaseAgent + utilities + decorators
# │   │   ├── orchestrator.py          # ~150 lines - AgentOrchestrator only
# │   │   ├── socratic.py              # ~300 lines - SocraticCounselorAgent
# │   │   ├── code.py                  # ~400 lines - CodeGeneratorAgent
# │   │   ├── project.py               # ~300 lines - ProjectManagerAgent
# │   │   ├── user.py                  # ~200 lines - UserManagerAgent
# │   │   ├── context.py               # ~300 lines - ContextAnalyzerAgent
# │   │   ├── document.py              # ~200 lines - DocumentProcessorAgent
# │   │   ├── monitor.py               # ~250 lines - SystemMonitorAgent
# │   │   └── services.py              # ~300 lines - ServicesAgent
# │   │
# │   └── 📁 services/                 # Service layer for external integrations
# │       ├── __init__.py
# │       ├── claude_service.py        # Claude API integration
# │       ├── vector_service.py        # ChromaDB integration
# │       ├── git_service.py           # Git operations
# │       └── ide_service.py           # IDE integration
# │
# ├── 📁 web/
# │   ├── __init__.py
# │   ├── 🌐 app.py                    # Flask app + All routes + All forms
# │   │
# │   ├── 📁 templates/
# │   │   ├── 🎨 base.html             # Navigation & layout
# │   │   ├── 📈 dashboard.html        # Main dashboard & analytics
# │   │   ├── 🔐 auth.html             # Login, register, profile
# │   │   ├── 📂 projects.html         # Project & module management
# │   │   ├── 💬 sessions.html         # Socratic sessions & conflicts
# │   │   ├── 💻 code.html             # Code generation & testing
# │   │   ├── 📊 reports.html          # Reports & exports
# │   │   └── ⚙️  admin.html           # Admin & system monitoring
# │   │
# │   └── 📁 static/
# │       ├── 📁 css/
# │       │   └── main.css             # All custom styles
# │       ├── 📁 js/
# │       │   └── main.js              # All custom JavaScript
# │       └── 📁 img/
# │           └── logo.png
# │
# ├── 📁 tests/
# │   ├── __init__.py
# │   ├── 🔬 test_core.py              # Core system tests
# │   ├── 📁 test_agents/              # ✨ Modular agent tests
# │   │   ├── __init__.py
# │   │   ├── test_base.py             # BaseAgent tests
# │   │   ├── test_orchestrator.py     # Orchestrator tests
# │   │   ├── test_socratic.py         # SocraticCounselorAgent tests
# │   │   ├── test_code.py             # CodeGeneratorAgent tests
# │   │   ├── test_project.py          # ProjectManagerAgent tests
# │   │   ├── test_user.py             # UserManagerAgent tests
# │   │   ├── test_context.py          # ContextAnalyzerAgent tests
# │   │   ├── test_document.py         # DocumentProcessorAgent tests
# │   │   ├── test_monitor.py          # SystemMonitorAgent tests
# │   │   └── test_services.py         # ServicesAgent tests
# │   ├── 🛠️  test_services.py         # External service tests
# │   ├── 🌐 test_web.py               # Web interface tests
# │   └── 🔗 test_integration.py       # End-to-end tests
# │
# ├── 📁 data/                         # (Created at runtime)
# │   ├── 🗄️  projects.db             # SQLite database
# │   ├── 📁 vector_db/               # ChromaDB storage
# │   ├── 📁 uploads/                 # File uploads
# │   ├── 📁 exports/                 # Generated exports
# │   ├── 📁 generated_projects/      # Generated application code
# │   └── 📁 logs/                    # Application logs
# │
# └── 📁 docs/
#     ├── 📖 README.md                 # Installation & getting started
#     ├── 👤 user_guide.md             # User documentation
#     ├── 👩‍💻 developer_guide.md        # Expansion guidelines
#     └── 📁 agents/                   # ✨ Agent-specific documentation
#         ├── agent_overview.md        # Agent architecture overview
#         ├── base_agent.md           # BaseAgent documentation
#         ├── orchestrator.md         # Orchestrator documentation
#         └── [agent_name].md         # Individual agent documentation
