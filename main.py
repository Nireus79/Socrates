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
# │   ├── 🤖 agents.py                 # All 12+ agents (BaseAgent → Enhanced → New)
# │   ├── 🛠️  services.py              # Summary, Git, Testing, Export, Claude, VectorDB
# │   ├── ❓ questioning.py            # Role adapters (7) + Phase generators (4)
# │   ├── 🗄️  database.py              # SQLite manager + All repositories
# │   └── 🔨 utils.py                  # File processor, Document parser, Validation
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
# │       │   ├── bootstrap.min.css
# │       │   └── main.css             # All custom styles
# │       ├── 📁 js/
# │       │   ├── bootstrap.bundle.min.js
# │       │   ├── chart.min.js
# │       │   ├── htmx.min.js
# │       │   └── main.js              # All custom JavaScript
# │       └── 📁 img/
# │           └── logo.png
# │
# ├── 📁 tests/
# │   ├── __init__.py
# │   ├── 🔬 test_core.py              # Core system tests
# │   ├── 🤖 test_agents.py            # All agent tests
# │   ├── 🛠️  test_services.py         # All service tests
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
#     └── 👩‍💻 developer_guide.md        # Expansion guidelines
