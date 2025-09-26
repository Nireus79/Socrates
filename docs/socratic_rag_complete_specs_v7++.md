# Socratic RAG System - Complete Architecture & Specifications v7++ (Modular)

## Development Rules
1. **Never write code unless explicitly requested**
2. **Always ask before writing code**
3. **Never take initiative to change anything beyond what's requested**
4. **Never rewrite entire scripts unless specifically told to**
5. **Ask for clarification on controversial answers instead of assuming**

## Final Goal & Vision
**Primary Objective**: Transform project ideas into complete, working applications through intelligent Socratic questioning and automated code generation.

### **Evolution from Legacy Socratic:**
```
❌ OLD APPROACH (Legacy Socratic):
Questions → Basic Specs → ONE MONOLITHIC SCRIPT → Manual Implementation

✅ NEW APPROACH (Socratic RAG Enhanced - Modular):
Role-Based Questions → Detailed Specifications → Architectural Breakdown → 
Organized Multi-File Structure → IDE Integration → Testing → Correction → 
Working Application
```

### **Complete Development Pipeline:**
```
1. Socratic Discovery    → Gather comprehensive requirements through role-based questioning
2. Architectural Design  → Break down into proper file structure and dependencies  
3. Code Generation      → Generate organized, production-ready code files
4. IDE Integration      → Push files to development environment
5. Testing & Validation → Automated testing with failure analysis
6. Intelligent Correction → Fix issues and re-generate corrected code
7. Deployment Ready     → Complete working application with tests and documentation
```

## Project Overview
Building an enterprise-grade Socratic RAG System that uses role-based questioning to guide project development through structured conversations, automatically generating complete application codebases with proper architecture, comprehensive testing, IDE integration, and intelligent error correction capabilities.

## Enhanced Architecture Overview (Socratic7++ Modular)

```
┌─────────────────────────────────────────────────────────────────────┐
│              Web UI Layer (Flask + HTML Templates + HTMX)           │
│  ├── Dashboard Pages  ├── Form Interfaces  ├── Progress Views       │
├─────────────────────────────────────────────────────────────────────┤
│        IDE Integration Layer (VS Code Extension + Local API)        │
│  ├── Multi-File Code Push  ├── Git Operations  ├── Live Testing     │
├─────────────────────────────────────────────────────────────────────┤
│                   Complete Modular Agent Architecture               │
│  ├── BaseAgent (Foundation)        ├── AgentOrchestrator            │
│  ├── SocraticCounselorAgent       ├── CodeGeneratorAgent            │
│  ├── ProjectManagerAgent          ├── UserManagerAgent              │
│  ├── ContextAnalyzerAgent         ├── DocumentProcessorAgent        │
│  ├── SystemMonitorAgent           ├── ServicesAgent                 │
│  └── EventHandlerService (Internal Events)                          │
├─────────────────────────────────────────────────────────────────────┤
│  Database Layer: SQLite + ChromaDB (+ PostgreSQL upgrade path)      │
├─────────────────────────────────────────────────────────────────────┤
│  Cross-Platform Deployment (Python Package + Executables)           │
└─────────────────────────────────────────────────────────────────────┘
```

## Core Architecture Principles
- **Modular Agent Design**: Each agent in separate, focused modules (~200-400 lines)
- **Clean Separation of Concerns**: Base classes, orchestration, and specialized agents
- **End-to-End Code Generation**: From questions to working applications
- **Organized Code Architecture**: Proper file structure, not monolithic scripts
- **Agent-Based Processing**: Specialized agents for different concerns
- **Role-Aware Questioning**: 7+ role types with specialized question generation
- **Hierarchical Project Management**: Projects → Modules → Tasks
- **Multi-Level Phase Management**: Project and module-level phases
- **Intelligent Testing & Correction**: Automated error detection and code fixes
- **Full IDE Integration**: Complete development environment integration
- **Cross-Platform Support**: Windows, Linux, macOS deployment

## Complete Modular Directory Structure

```
socratic-rag-enhanced/
│
├── 📋 README.md
├── 📋 requirements.txt  
├── ⚙️  config.yaml
├── 🚀 run.py                        # Main application entry point
│
├── 📁 src/
│   ├── __init__.py
│   │
│   ├── 🔧 core.py                   # Config, exceptions, logging, database, events
│   ├── 📊 models.py                 # User, Project, Module, Task, Role, TechnicalSpec
│   ├── 🗄️  database.py              # SQLite manager + All repositories
│   ├── 🔨 utils.py                  # File processor, Document parser, Validation
│   │
│   ├── 📁 agents/                   # ✨ MODULAR AGENT ARCHITECTURE
│   │   ├── __init__.py              # ~50 lines  - Exports & initialization
│   │   ├── base.py                  # ~200 lines - BaseAgent + utilities + decorators
│   │   ├── orchestrator.py          # ~150 lines - AgentOrchestrator only
│   │   ├── socratic.py              # ~300 lines - SocraticCounselorAgent
│   │   ├── code.py                  # ~400 lines - CodeGeneratorAgent
│   │   ├── project.py               # ~300 lines - ProjectManagerAgent
│   │   ├── user.py                  # ~200 lines - UserManagerAgent
│   │   ├── context.py               # ~300 lines - ContextAnalyzerAgent
│   │   ├── document.py              # ~200 lines - DocumentProcessorAgent
│   │   ├── monitor.py               # ~250 lines - SystemMonitorAgent
│   │   └── services.py              # ~300 lines - ServicesAgent
│   │
│   └── 📁 services/                 # Service layer for external integrations
│       ├── __init__.py
│       ├── claude_service.py        # Claude API integration
│       ├── vector_service.py        # ChromaDB integration
│       ├── git_service.py           # Git operations
│       └── ide_service.py           # IDE integration
│
├── 📁 web/
│   ├── __init__.py
│   ├── 🌐 app.py                    # Flask app + All routes + All forms
│   │
│   ├── 📁 templates/
│   │   ├── 🎨 base.html             # Navigation & layout
│   │   ├── 📈 dashboard.html        # Main dashboard & analytics  
│   │   ├── 🔐 auth.html             # Login, register, profile
│   │   ├── 📂 projects.html         # Project & module management
│   │   ├── 💬 sessions.html         # Socratic sessions & conflicts
│   │   ├── 💻 code.html             # Code generation & testing
│   │   ├── 📊 reports.html          # Reports & exports
│   │   └── ⚙️  admin.html           # Admin & system monitoring
│   │
│   └── 📁 static/
│       ├── 📁 css/
│       │   ├── bootstrap.min.css
│       │   └── main.css             # All custom styles
│       ├── 📁 js/  
│       │   ├── bootstrap.bundle.min.js
│       │   ├── chart.min.js
│       │   ├── htmx.min.js
│       │   └── main.js              # All custom JavaScript
│       └── 📁 img/
│           └── logo.png
│
├── 📁 tests/
│   ├── __init__.py
│   ├── 🔬 test_core.py              # Core system tests
│   ├── 📁 test_agents/              # ✨ Modular agent tests
│   │   ├── __init__.py
│   │   ├── test_base.py             # BaseAgent tests
│   │   ├── test_orchestrator.py     # Orchestrator tests
│   │   ├── test_socratic.py         # SocraticCounselorAgent tests
│   │   ├── test_code.py             # CodeGeneratorAgent tests
│   │   ├── test_project.py          # ProjectManagerAgent tests
│   │   ├── test_user.py             # UserManagerAgent tests
│   │   ├── test_context.py          # ContextAnalyzerAgent tests
│   │   ├── test_document.py         # DocumentProcessorAgent tests
│   │   ├── test_monitor.py          # SystemMonitorAgent tests
│   │   └── test_services.py         # ServicesAgent tests
│   ├── 🛠️  test_services.py         # External service tests
│   ├── 🌐 test_web.py               # Web interface tests
│   └── 🔗 test_integration.py       # End-to-end tests
│
├── 📁 data/                         # (Created at runtime)
│   ├── 🗄️  projects.db             # SQLite database
│   ├── 📁 vector_db/               # ChromaDB storage
│   ├── 📁 uploads/                 # File uploads
│   ├── 📁 exports/                 # Generated exports
│   ├── 📁 generated_projects/      # Generated application code
│   └── 📁 logs/                    # Application logs
│
└── 📁 docs/
    ├── 📖 README.md                 # Installation & getting started  
    ├── 👤 user_guide.md             # User documentation
    ├── 👩‍💻 developer_guide.md        # Expansion guidelines
    └── 📁 agents/                   # ✨ Agent-specific documentation
        ├── agent_overview.md        # Agent architecture overview
        ├── base_agent.md           # BaseAgent documentation
        ├── orchestrator.md         # Orchestrator documentation
        └── [agent_name].md         # Individual agent documentation
```

**Total: ~35 files** 📊 (increased modularity for better maintainability)

## Modular Agent Architecture

### **Agent File Organization & Responsibilities:**

#### **📋 agents/__init__.py** (~50 lines)
- **Purpose**: Module exports and initialization
- **Features**: 
  - Smart imports with graceful degradation
  - Global orchestrator management
  - Convenience functions for agent operations
  - Module status and health checking

#### **🏗️ agents/base.py** (~200 lines)
- **Purpose**: Foundation classes and utilities
- **Features**:
  - BaseAgent abstract class with common functionality
  - Agent decorators for validation, caching, error handling
  - Common utilities (logging, config access, database connections)
  - Event system integration
  - Claude API client management

#### **🎯 agents/orchestrator.py** (~150 lines)
- **Purpose**: Agent coordination and request routing
- **Features**:
  - AgentOrchestrator class for managing all agents
  - Request routing based on capabilities
  - Agent health monitoring and lifecycle management
  - Cross-agent communication and event handling
  - Load balancing and performance optimization

#### **💬 agents/socratic.py** (~300 lines)
- **Purpose**: Intelligent Socratic questioning system
- **Features**:
  - Role-based question generation (7 role types)
  - Context-aware conversation management
  - Learning from user response patterns
  - Conflict mediation and insight extraction
  - Dynamic vs static questioning modes

#### **💻 agents/code.py** (~400 lines)
- **Purpose**: Complete code generation pipeline
- **Features**:
  - Architecture design and file structure planning
  - Multi-file code generation (not monolithic!)
  - Comprehensive testing (unit, integration, security)
  - Intelligent error correction and optimization
  - Performance analysis and security scanning

#### **📊 agents/project.py** (~300 lines)
- **Purpose**: Project lifecycle and team management
- **Features**:
  - Complete project CRUD operations
  - Module and task hierarchy management
  - Team collaboration and permissions
  - Progress tracking and analytics
  - Risk assessment and resource allocation

#### **👥 agents/user.py** (~200 lines)
- **Purpose**: User management and authentication
- **Features**:
  - User lifecycle management
  - Role-based access control
  - Team coordination and skill assessment
  - Activity tracking and productivity analytics
  - Authentication and session management

#### **🧠 agents/context.py** (~300 lines)
- **Purpose**: Context analysis and conflict detection
- **Features**:
  - Advanced conversation pattern analysis
  - Multi-user context synthesis
  - Conflict detection and resolution
  - Technology compatibility checking
  - Intelligent insights and recommendations

#### **📄 agents/document.py** (~200 lines)
- **Purpose**: Document processing and knowledge management
- **Features**:
  - Multi-format file processing
  - GitHub repository analysis
  - Knowledge extraction and chunking
  - Vector storage integration
  - Document summarization

#### **🔍 agents/monitor.py** (~250 lines)
- **Purpose**: System monitoring and analytics
- **Features**:
  - Health checking and performance monitoring
  - API usage tracking and cost analysis
  - User activity analytics
  - Alert management and notifications
  - Resource utilization monitoring

#### **🛠️ agents/services.py** (~300 lines)
- **Purpose**: External services and integrations
- **Features**:
  - Complete Git operations and workflow
  - Multi-format export system (ZIP, JSON, Docker)
  - IDE integration and file synchronization
  - Deployment automation and backup
  - Documentation generation

### **Agent Import and Usage Pattern:**

```python
# Import specific agents
from src.agents import (
    get_orchestrator,
    process_agent_request,
    create_agent,
    ProjectManagerAgent,
    CodeGeneratorAgent,
    DocumentProcessorAgent,
    ServicesAgent
)

# Use orchestrator for coordinated operations
orchestrator = get_orchestrator()
result = orchestrator.route_request('code_generator', 'generate_project_files', data)

# Or use direct agent creation
code_agent = create_agent('code_generator')
result = code_agent.process_request('generate_project_files', data)

# Convenience function for quick operations
result = process_agent_request('project_manager', 'create_project', project_data)
```

## Enhanced Role System

### Role Hierarchy & Specializations:
1. **Project Manager**: Strategic oversight, resource allocation, timeline management, stakeholder communication
2. **Technical Lead**: Architecture decisions, technical direction, code reviews, technology selection
3. **Developer**: Implementation details, algorithms, data structures, API design
4. **Designer (UI/UX)**: User interface, user experience, design systems, accessibility
5. **QA/Tester**: Test planning, edge cases, quality assurance, validation scenarios
6. **Business Analyst**: Requirements gathering, business rules, compliance, reporting
7. **DevOps Engineer**: Infrastructure, deployment, monitoring, CI/CD, security

### Role-Based Question Adaptation:
- **Strategic Questions** for Managers (timeline, resources, priorities, stakeholder needs)
- **Technical Questions** for Developers (implementation, architecture, patterns, algorithms)
- **Quality Questions** for Testers (edge cases, validation, user scenarios, error handling)
- **User Experience Questions** for Designers (usability, workflows, accessibility, responsive design)
- **Business Logic Questions** for Analysts (requirements, stakeholder needs, compliance, reporting)
- **Infrastructure Questions** for DevOps (deployment, scaling, monitoring, security, performance)

## Complete Code Generation Workflow (Modular)

### **Phase 1: Socratic Discovery & Requirements Gathering**
```
SocraticCounselorAgent (agents/socratic.py):
├── Project Manager Role:
│   ├── "What's the project timeline and budget constraints?"
│   ├── "Who are the key stakeholders and decision makers?"
│   └── "What are the success criteria and KPIs?"
├── Technical Lead Role:
│   ├── "What's the expected user load and performance requirements?"
│   ├── "What existing systems need integration?"
│   └── "What are the security and compliance requirements?"
├── Developer Role:
│   ├── "What are the core features and user workflows?"
│   ├── "What data needs to be stored and how will it flow?"
│   └── "What external APIs or services are needed?"
├── QA/Tester Role:
│   ├── "What are the edge cases and error scenarios?"
│   ├── "How will you measure quality and user satisfaction?"
│   └── "What browsers/devices need to be supported?"
└── Business Analyst Role:
    ├── "What business rules and validation logic are required?"
    ├── "What reports and analytics are needed?"
    └── "How does this integrate with existing business processes?"
```

### **Phase 2: Architectural Design & File Structure Planning**
```
CodeGeneratorAgent (agents/code.py) - Architecture Design Methods:
├── Analyze complete specifications and requirements
├── Design proper application architecture (not monolithic!)
├── Plan organized file structure:
│   ├── backend/ (API, business logic, data models)
│   ├── frontend/ (UI components, pages, styles)
│   ├── database/ (schemas, migrations, seeders)
│   ├── tests/ (unit, integration, e2e tests)
│   ├── config/ (environment, deployment configs)
│   └── docs/ (API docs, user guides, technical specs)
├── Define module dependencies and interfaces
├── Plan implementation order and deployment strategy
└── Generate technical specification document
```

### **Phase 3: Multi-File Code Generation**
```
CodeGeneratorAgent (agents/code.py) - Enhanced Multi-File Generation:
├── Backend Code Generation:
│   ├── Database Models (SQLAlchemy, Prisma, etc.)
│   ├── API Routes & Controllers (Flask, FastAPI, Express)
│   ├── Business Logic Services
│   ├── Authentication & Authorization
│   ├── Data Validation & Error Handling
│   └── Configuration Management
├── Frontend Code Generation:
│   ├── React/Vue/Angular Components
│   ├── Pages & Routing Configuration
│   ├── State Management (Redux, Vuex, etc.)
│   ├── API Integration & HTTP Clients
│   ├── CSS/SCSS Styling with responsive design
│   └── Form Handling & Validation
├── Database & Infrastructure:
│   ├── Database Schema & Migration Scripts
│   ├── Docker & Docker Compose files
│   ├── CI/CD Pipeline Configuration
│   ├── Environment Configuration Files
│   └── Deployment Scripts & Documentation
├── Comprehensive Testing Suite:
│   ├── Unit Tests for all components
│   ├── Integration Tests for API endpoints
│   ├── End-to-End Tests for user workflows
│   ├── Performance & Load Tests
│   └── Security & Vulnerability Tests
└── Documentation & Guides:
    ├── API Documentation (OpenAPI/Swagger)
    ├── User Guides & Tutorials
    ├── Developer Setup Instructions
    ├── Deployment & Maintenance Guides
    └── Architecture Decision Records (ADRs)
```

### **Phase 4: IDE Integration & File Distribution**
```
ServicesAgent (agents/services.py) - IDE Integration:
├── Create organized project structure in IDE
├── Push all generated files to appropriate directories
├── Set up development environment configuration
├── Initialize Git repository with proper .gitignore
├── Install dependencies and configure package managers
├── Set up debugging and development server configuration
└── Provide real-time progress updates and file creation status
```

### **Phase 5: Automated Testing & Quality Validation**
```
CodeGeneratorAgent (agents/code.py) - Testing System:
├── Execute complete test suite in isolated environment
├── Run unit tests with coverage analysis
├── Perform integration testing on API endpoints
├── Execute end-to-end tests for user workflows
├── Run security vulnerability scans
├── Perform performance benchmarking
├── Validate code quality metrics (complexity, maintainability)
└── Generate comprehensive test reports with recommendations
```

### **Phase 6: Intelligent Error Analysis & Code Correction**
```
ContextAnalyzerAgent (agents/context.py) + CodeGeneratorAgent:
├── Parse test failures and error messages
├── Identify root causes (logic errors, missing dependencies, config issues)
├── Analyze code patterns and anti-patterns
├── Cross-reference with project specifications
├── Generate targeted corrections:
│   ├── Logic fixes for failing unit tests
│   ├── Missing imports and dependency resolution
│   ├── Configuration corrections
│   ├── Performance optimizations
│   ├── Security vulnerability patches
│   └── Code style and quality improvements
├── Re-generate corrected files
├── Push updates back to IDE
└── Re-run test suite until all issues resolved
```

### **Phase 7: Final Validation & Deployment Preparation**
```
Complete Application Validation:
├── All tests passing (unit, integration, e2e)
├── Performance benchmarks met
├── Security scans clean
├── Code quality standards achieved
├── Documentation complete and accurate
├── Deployment configuration validated
├── Development environment fully functional
└── Ready for production deployment
```

## Database Architecture & Data Models

### **Primary Storage Strategy**: 
- **Current**: SQLite + ChromaDB (for development/small teams)
- **Upgrade Path**: PostgreSQL + pgvector (for enterprise/large teams)
- **Caching**: In-memory caching with Redis upgrade path
- **Backup Strategy**: Automated backups with point-in-time recovery

### **Enhanced Data Models**:

#### **Generated Code Tracking**:
```python
@dataclass
class GeneratedCodebase:
    codebase_id: str
    project_id: str
    version: str
    architecture_type: str              # MVC, microservices, layered, etc.
    technology_stack: Dict[str, str]    # framework versions, dependencies
    file_structure: Dict[str, Any]      # complete file organization
    generated_files: List[GeneratedFile] # all generated files with metadata
    test_results: List[TestResult]      # comprehensive test outcomes
    deployment_config: Dict[str, Any]   # deployment and infrastructure config
    performance_metrics: Dict[str, float] # benchmarks and performance data
    security_scan_results: List[Dict]   # security vulnerability assessments
    code_quality_metrics: Dict[str, float] # maintainability, complexity, etc.
    generated_at: datetime.datetime
    last_updated: datetime.datetime
    status: str                         # generating, testing, completed, deployed
    deployment_status: str              # not_deployed, staging, production
```

#### **Individual File Tracking**:
```python
@dataclass
class GeneratedFile:
    file_id: str
    codebase_id: str
    file_path: str                      # relative path within project
    file_type: FileType                 # enum: PYTHON, JAVASCRIPT, HTML, etc.
    file_purpose: str                   # model, controller, view, test, config, etc.
    content: str                        # actual file content
    dependencies: List[str]             # other files this depends on
    documentation: str                  # generated documentation
    generated_by_agent: str            # which agent generated this file
    version: str                       # file version for tracking changes
    size_bytes: int                    # file size for optimization tracking
    complexity_score: float            # code complexity metrics
    test_coverage: float               # test coverage percentage
```

#### **Comprehensive Testing Results**:
```python
@dataclass
class TestResult:
    test_id: str
    codebase_id: str
    test_type: TestType                # enum: UNIT, INTEGRATION, SECURITY, etc.
    test_suite: str                    # which test suite was run
    files_tested: List[str]            # files covered by this test
    passed: bool                       # overall pass/fail status
    total_tests: int                   # number of individual tests
    passed_tests: int                  # number of passing tests
    failed_tests: int                  # number of failing tests
    skipped_tests: int                 # number of skipped tests
    coverage_percentage: float         # code coverage achieved
    failure_details: List[Dict]        # detailed failure information
```

## Deployment & Development Strategy

### **Development Phases**:

**Phase 1: Core Infrastructure**
- System configuration and dependency management
- Core infrastructure (logging, events, database, exceptions)
- Complete data models with validation
- Full database layer with repositories
- Processing utilities (file, text, code analysis)

**Phase 2: External Services Integration**
- Claude API service integration
- ChromaDB vector storage service
- Git operations service
- VS Code integration service

**Phase 3: Agent System Implementation**
- All 11 modular agents with orchestration
- Role-based Socratic questioning system
- Multi-file code generation pipeline
- Context analysis and conflict detection

**Phase 4: Web Interface Development**
- Flask web application with agent integration
- Real-time dashboard and project management UI
- Agent management interface
- Server-sent events for live updates

**Phase 5: Testing & Quality Assurance**
- Comprehensive test suite (80%+ coverage)
- Performance and integration testing
- Cross-agent communication testing
- End-to-end workflow validation

**Phase 6: Documentation & User Experience**
- Complete API documentation
- User guides and tutorials
- Developer documentation for extensions
- Interactive onboarding experience

**Phase 7: Cross-Platform Deployment**
- Docker containerization with agent separation
- Cross-platform installers (Windows, macOS, Linux)
- Cloud deployment templates (AWS, Azure, GCP)
- VS Code extension development

**Phase 8: Enterprise Features (Optional)**
- Advanced authentication (SSO, LDAP)
- Agent load balancing and scaling
- Advanced analytics and ML insights
- Custom agent development SDK

### **Deployment Options**:

**Development Environment**:
- Local SQLite + ChromaDB setup
- Single-machine deployment for development
- Hot-reload and debugging support

**Production Environment**:
- PostgreSQL + pgvector (enterprise upgrade)
- Multi-container Docker deployment
- Load-balanced agent processing
- Advanced monitoring and logging

**Cloud Deployment**:
- Container orchestration (Kubernetes)
- Auto-scaling based on load
- Distributed agent architecture
- Enterprise security and compliance

## Success Metrics & KPIs

### **Modular Architecture Success Metrics**:
- **Agent Modularity Score**: Clean separation, minimal coupling between agents
- **Agent Performance**: Individual agent response times and resource usage
- **System Reliability**: Graceful degradation when agents fail
- **Development Velocity**: Faster feature development with modular agents
- **Maintainability Score**: Ease of updating and extending individual agents
- **Test Coverage**: Per-agent test coverage and integration test success

### **Code Generation Success Metrics**:
- **Code Generation Success Rate**: Percentage of specifications that result in working applications
- **Test Coverage Achievement**: Average test coverage percentage across generated applications
- **Code Quality Scores**: Maintainability, complexity, and security metrics
- **Time to Working Application**: Reduced time from specification to deployable code
- **Error Correction Efficiency**: Percentage of issues automatically resolved
- **User Code Customization Rate**: How often users modify vs. use generated code as-is

### **Agent-Specific Metrics**:
- **SocraticCounselorAgent**: Question effectiveness, user engagement, insight quality
- **CodeGeneratorAgent**: Code generation speed, quality, test success rate
- **ProjectManagerAgent**: Project completion rate, team coordination efficiency
- **DocumentProcessorAgent**: Knowledge extraction accuracy, processing speed
- **ServicesAgent**: Git operation success, deployment reliability, export quality

## System Evolution & Architecture

### **Evolution from Legacy to Modular Architecture**:

**Legacy Approach (v7.0)**:
```
Questions → Basic Specs → ONE MONOLITHIC SCRIPT → Manual Implementation
```

**Enhanced Modular Approach (v7.2+)**:
```
Role-Based Questions → Detailed Specifications → Architectural Breakdown → 
Organized Multi-File Structure → IDE Integration → Testing → Correction → 
Working Application
```

### **Key Architectural Improvements**:
1. **Modular Agent Design**: Each agent in separate, focused modules (~200-400 lines)
2. **Clean Separation of Concerns**: Base classes, orchestration, and specialized agents
3. **End-to-End Code Generation**: From questions to working applications
4. **Organized Code Architecture**: Proper file structure, not monolithic scripts
5. **Agent-Based Processing**: Specialized agents for different concerns
6. **Full IDE Integration**: Complete development environment integration

### **Agent Addition Process**:
1. Create new agent file in `src/agents/`
2. Implement BaseAgent interface
3. Add to `agents/__init__.py` exports
4. Update orchestrator registration
5. Add tests in `tests/test_agents/`
6. Update documentation

---

This comprehensive modular specification serves as the complete architectural reference for the enhanced Socratic RAG System with proper agent separation, maintainable architecture, and enterprise-grade capabilities. The modular design ensures better maintainability, testability, and extensibility while preserving all the advanced code generation features of the original system.