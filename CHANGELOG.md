# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

Current version: **8.0.0**
