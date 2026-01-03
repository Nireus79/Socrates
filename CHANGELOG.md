# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- **Package Naming** - Standardized package names to follow AI naming convention
  - `socrates-ai-cli` - Command-line interface package
  - `socrates-ai-api` - REST API server package
  - Previous generic naming has been deprecated
  - This change ensures consistency with AI-focused branding

### Fixed

- **Docker Workflow** - Fixed Docker build and publish pipeline
  - Fixed Alpine-incompatible healthcheck in frontend Dockerfile (wget → shell-based check)
  - Improved frontend container testing with proper wait times and error diagnostics
  - Improved API health check test robustness with 45-second wait for startup completion
  - Frontend Dockerfile now uses Node 20 Alpine + Nginx Alpine multi-stage build
  - All health checks use Alpine-compatible shell commands

- **Code Quality** - Reduced C901 cyclomatic complexity violations (4 critical functions)
  - `dependency_validator.py`: `_validate_python_dependencies` (24 → 7 complexity)
    - Extracted 5 helper methods for requirements reading, import extraction, analysis
  - `multi_file_splitter.py`: `_split_python` (23 → 6 complexity)
    - Extracted 7 helper methods for code categorization and file building
  - `file_change_tracker.py`: `update_vector_db` (12 → 6) and `update_database` (11 → 6)
    - Extracted 6 helper methods for processing deleted/modified/added files
  - Total: 4 violations fixed, 17 remaining

## [0.6.1] - 2025-12-05

### Fixed

- **Code Quality** - Resolved all 14 remaining Ruff violations (C901, E722)
  - Reduced cyclomatic complexity in 7 files by extracting helper methods
  - Replaced bare `except:` statements with specific exception handling
  - Files improved: config.py, command_handler.py, collab_commands.py, project_commands.py, session_commands.py, user_commands.py, main_app.py
  - All changes are pure refactoring with zero functional changes
  - Improved code maintainability and adherence to Python best practices

- **CI/CD** - Infrastructure improvements
  - Updated deprecated GitHub Actions to v4
  - Configured workflows to trigger only on master branch
  - Removed Python 3.8 and 3.9 from test matrix

## [0.6.0] - 2025-12-05

### Added

- **Comprehensive Documentation Suite** - 8 new documentation files (71,000+ words)
  - `docs/README.md` - System overview and quick start guide
  - `docs/INSTALLATION.md` - Complete installation and setup guide
  - `docs/USER_GUIDE.md` - End-user tutorial and CLI command reference
  - `docs/ARCHITECTURE.md` - Technical architecture and design patterns
  - `docs/API_REFERENCE.md` - Complete API documentation with examples
  - `docs/CONFIGURATION.md` - Configuration options and scenarios
  - `docs/TROUBLESHOOTING.md` - Common issues and solutions
  - `docs/DEVELOPER_GUIDE.md` - Contributing and extension guide

- **Expanded Test Suite** - 15+ new test cases for recent fixes
  - Vector database filter tests (4 tests)
  - Logger initialization tests (5 tests)
  - Exit command formatting tests (4 tests)
  - Integration tests (2 tests)

### Fixed

- **ChromaDB Compatibility** - Removed unsupported `$exists` operator
  - VectorDatabase now uses `$eq` filters for project-scoped queries
  - Fixed `_build_project_filter()` to handle None case properly
  - Ensures compatibility with ChromaDB filtering API

- **Logger Configuration** - Debug mode now defaults to OFF
  - Console handler initializes with INFO level (not DEBUG)
  - Reduces log noise in normal operation mode
  - Debug mode can be enabled per-session when needed

- **Exit Message Formatting** - Fixed f-string rendering
  - Exit command now properly displays Greek philosophical quote
  - Colors and styling render correctly using f-string interpolation
  - Thanking message displays as intended

- **Code Quality Improvements**
  - Resolved all F821 (undefined name) violations with TYPE_CHECKING imports
  - Fixed F841 (unused variable) violations throughout codebase
  - Updated pyproject.toml ruff configuration to use [tool.ruff.lint] section
  - Removed deprecated W503 rule from linting rules

### Improved

- **Type Hints** - Better forward reference handling
  - AgentOrchestrator, ClaudeClient, CommandHandler now properly imported in TYPE_CHECKING blocks
  - Prevents circular import issues while maintaining type safety
  - Improved IDE autocomplete and type checking support

- **CI/CD Pipeline** - All GitHub Actions checks passing
  - ✅ Ruff linting (E, W, F, I, C, B, UP rules)
  - ✅ Black formatting (100-character line length)
  - ✅ PyTest suite (all tests passing)
  - ✅ MyPy type checking
  - ✅ Security audit

## [0.5.0] - 2025-12-04

### Versioning

- **CORRECTED VERSION**: Reverted from 8.0.0 → 0.5.0
  - Socrates is pre-alpha software and should use 0.x.x versioning per semantic versioning
  - Version 1.0.0 will indicate the first production-ready release
  - Previous jump from 0.4.1 → 8.0.0 was incorrect (implied mature, stable product)
  - Future path: 0.5.0 → 0.6.0 → ... → 1.0.0

### Added

- **Multi-Domain Knowledge Base Expansion** - From 5 to 100+ entries across 6 domains
  - **Programming** (30 entries): Python advanced, JavaScript/TypeScript, algorithms, web development, DevOps, testing
  - **Writing** (15 entries): Narrative structure, technical writing, editing/revision, genres/formats
  - **Business** (15 entries): Project management, business strategy, product management, team collaboration
  - **Research** (10 entries): Research methods, analysis techniques, documentation
  - **Design** (10 entries): UX/UI design, visual design, design process
  - **General Skills** (20 entries): Problem-solving, communication, collaboration, learning/adaptation

- **Project-Specific Knowledge Management**
  - VectorDatabase enhanced with project_id metadata support
  - ChromaDB metadata filtering for project-scoped searches
  - Project knowledge isolation (no cross-project contamination)
  - New VectorDatabase methods:
    - `add_project_knowledge(entry, project_id)` - Add project-specific knowledge
    - `get_project_knowledge(project_id)` - Retrieve project knowledge
    - `export_project_knowledge(project_id)` - Export to JSON
    - `import_project_knowledge(project_id, entries)` - Import from JSON
    - `delete_project_knowledge(project_id)` - Remove project knowledge
    - `_build_project_filter(project_id)` - ChromaDB where clause builder
  - Updated `search_similar()` with optional project_id filtering

- **Knowledge Management Command Suite** - 7 new CLI commands
  - `/knowledge add` - Add project knowledge manually
  - `/knowledge list` - List project knowledge entries
  - `/knowledge search` - Search across global and project knowledge
  - `/knowledge export` - Export project knowledge to JSON
  - `/knowledge import` - Import knowledge from JSON
  - `/knowledge remove` - Remove project knowledge entries
  - `/remember` - Quick shortcut for adding knowledge

- **Automatic Knowledge Enrichment System**
  - New `KnowledgeManagerAgent` for managing knowledge suggestions
  - Event-driven knowledge suggestion workflow via `EventType.KNOWLEDGE_SUGGESTION`
  - All agents can suggest knowledge gaps via `suggest_knowledge_addition()` method
  - User approval/rejection workflow for suggested knowledge
  - Per-project suggestion queues with status tracking (pending/approved/rejected)
  - Methods for managing suggestions: get_suggestions, approve_suggestion, reject_suggestion, get_queue_status, clear_suggestions

- **Comprehensive Testing** - 50+ new tests for knowledge system
  - VectorDatabase project-scoped operations (20+ tests)
  - KnowledgeManagerAgent integration tests (10+ tests)
  - End-to-end workflow verification tests
  - All tests passing with 100% success rate

- **Documentation**
  - Complete knowledge enrichment system architecture guide
  - Phase completion summary with detailed implementation info
  - Usage examples and troubleshooting guides
  - Performance benchmarks and metrics

### Changed

- **VectorDatabase API** - Enhanced with optional project_id parameter
  - `search_similar()` now accepts optional `project_id` for filtering
  - Backward compatible (project_id defaults to None for global search)

- **Knowledge Base Format** - Tags field updated for ChromaDB compatibility
  - Tags changed from arrays to comma-separated strings
  - All 100+ entries updated with consistent format
  - Includes new "domain" metadata field

### Performance

- Event propagation: < 100ms
- Suggestion storage: < 10ms per suggestion
- Approval processing: < 50ms (includes vector DB indexing)
- Search latency: < 200ms for 100+ entries

### Previous Infrastructure (from 8.0.0 - still included)

- Event System, Configuration System, Async Support, Public API, CLI/API packages, Integration Examples, Test Suite, CI/CD Pipeline

## [7.0.0] - Previous Release

(See git history for details on earlier releases)

---

## Unreleased

### Planned Features

- [ ] ReadTheDocs documentation site
- [ ] Performance benchmarking and profiling
- [ ] Load testing framework
- [ ] Docker and Docker Compose examples
- [ ] Helm charts for Kubernetes deployment
- [ ] GraphQL API alternative
- [ ] WebSocket real-time collaboration
- [ ] Advanced RAG features
- [ ] Multi-model support (Claude, GPT-4, etc.)
- [ ] Rate limiting and quota management

## Guidelines for Contributors

When adding features:

1. Update this CHANGELOG.md in the [Unreleased] section
2. Follow [Keep a Changelog](https://keepachangelog.com/) format
3. Use these categories:
   - Added: New features
   - Changed: Changes in existing functionality
   - Deprecated: Soon-to-be removed features
   - Removed: Removed features
   - Fixed: Bug fixes
   - Security: Security updates

Example format:
```markdown
### Added
- New feature description

### Changed
- Changed feature description

### Fixed
- Fixed bug description
```

## Release Process

1. Create a new version with `gh workflow run release.yml -f version-type=<major|minor|patch>`
2. GitHub Actions will:
   - Bump version in all pyproject.toml files
   - Create git tag and push
   - Create GitHub release
   - Trigger publishing to PyPI
3. Monitor the publish workflow to ensure success

## Version Numbering

This project uses [Semantic Versioning](https://semver.org/):

- MAJOR version for incompatible API changes
- MINOR version for backwards-compatible functionality additions
- PATCH version for backwards-compatible bug fixes

Current version: **1.1.0**
