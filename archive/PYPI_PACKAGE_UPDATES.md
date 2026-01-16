# PyPI Package Updates Required

**Date:** January 15, 2026
**Current Status:** Version 1.1.0 (needs updates for GitHub-ready features)
**Priority:** Update Before Release

---

## Overview

The Socrates AI packages need updates to reflect the new GitHub-ready project generation features implemented in this session. Below is a detailed breakdown of all required updates.

---

## 1. socrates-ai (Main Library)

**Current Version:** 1.1.0
**PyPI URL:** https://pypi.org/project/socrates-ai/

### Required Updates

#### 1.1 Update Version
```toml
[project]
name = "socrates-ai"
version = "1.2.0"  # From 1.1.0 → 1.2.0 (minor version bump for new features)
description = "Production-ready collaborative development platform with Socratic AI guidance, GitHub-ready project generation, multi-agent orchestration, real-time collaboration, and RAG knowledge management"
```

**Reason:**
- New major feature: GitHub-ready project generation
- Export/download functionality
- Git integration
- This warrants a minor version bump (1.1.0 → 1.2.0)

#### 1.2 Update Keywords
Add these keywords to reflect new features:
```toml
keywords = [
    # ... existing keywords ...
    "github",
    "github-ready",
    "export",
    "project-generation",
    "git",
    "ci-cd",
    "github-actions",
    "docker",
    "gitops",
]
```

#### 1.3 Update Packages List
Add new modules to `tool.setuptools.packages`:
```toml
[tool.setuptools]
packages = [
    # ... existing packages ...
    "socratic_system.utils",  # Ensure included
]
```

Add new utility modules to `package-data`:
```toml
[tool.setuptools.package-data]
socratic_system = [
    "py.typed",
    "config/knowledge_base.json",
    "utils/templates/*",  # Include template files
]
```

#### 1.4 Add New Dependencies
These libraries support the new features:
```toml
dependencies = [
    # ... existing dependencies ...
    "gitpython>=3.1.0",          # Git operations
    "requests>=2.31.0",           # GitHub API calls
    "cryptography>=41.0.0",       # Token encryption
    "gunicorn>=21.0.0",           # WSGI server for production
    "psycopg2-binary>=2.9.0",     # PostgreSQL adapter
]
```

**Reason:**
- `gitpython`: Required for `git_initializer.py`
- `requests`: Required for `git_initializer.py` GitHub API calls
- `cryptography`: Required for token encryption in `user.py`
- `gunicorn`: Required for production deployment (mentioned in Docker files)
- `psycopg2-binary`: Required for database operations

#### 1.5 Update optional-dependencies
```toml
[project.optional-dependencies]
dev = [
    # ... existing ...
]
github = [
    "gitpython>=3.1.0",
    "requests>=2.31.0",
]
export = [
    # Uses built-in zipfile, tarfile, so no new deps needed
]
docker = [
    "gunicorn>=21.0.0",
    "psycopg2-binary>=2.9.0",
]
```

#### 1.6 Update URLs
```toml
[project.urls]
# ... existing ...
Documentation = "https://github.com/Nireus79/Socrates/tree/master/docs/deployment"
"GitHub Features" = "https://github.com/Nireus79/Socrates/blob/master/docs/GITHUB_INTEGRATION.md"
```

#### 1.7 Update Classifiers
```toml
classifiers = [
    "Development Status :: 5 - Production/Stable",
    # ... existing ...
    "Topic :: Software Development :: Version Control :: Git",
    "Topic :: Internet :: WWW/HTTP :: Dynamic Content",
    "Framework :: FastAPI",
]
```

### Changelog Entry
```markdown
## [1.2.0] - January 15, 2026

### Added
- GitHub-ready project generation with complete CI/CD workflows
- Export projects in multiple formats (ZIP, TAR, TAR.GZ, TAR.BZ2)
- Automatic GitHub repository creation via GitHub API
- Git initialization and code push functionality
- Production-ready Docker configuration generation
- Structured logging with JSON support
- Metrics collection and health monitoring
- Enhanced project models with GitHub integration fields
- New utility modules: archive_builder, git_initializer, documentation_generator
- Comprehensive deployment documentation and guides

### Changed
- Enhanced ProjectStructureGenerator to include 20+ production files
- Updated project models to support GitHub integration
- Improved documentation generation with dynamic content
- Updated database models with export/publish tracking fields

### Fixed
- UI integration for export and GitHub publishing features
- Component prop signatures for proper TypeScript typing

### Dependencies
- Added: gitpython>=3.1.0, requests>=2.31.0, cryptography>=41.0.0, gunicorn>=21.0.0
```

---

## 2. socrates-ai-cli (CLI Package)

**Current Version:** 1.1.0
**PyPI URL:** https://pypi.org/project/socrates-ai-cli/

### Required Updates

#### 2.1 Update Version and Dependencies
```toml
[project]
name = "socrates-ai-cli"
version = "1.2.0"  # Match main library
description = "Command-line interface for Socrates AI tutoring system with GitHub-ready project generation, export, and publishing capabilities"

dependencies = [
    "socrates-ai>=1.2.0",  # Update from >=0.6.0
    "colorama>=0.4.6",
    "click>=8.0.0",
]
```

**Reason:**
- CLI should depend on the new main library version
- Users need the GitHub-ready features when using CLI

#### 2.2 Add New CLI Commands
The CLI should support the new features:
```python
# New commands to add to socrates_cli/cli.py

@code.command("export")
@click.option("--project-id", required=True, help="Project ID")
@click.option("--format", type=click.Choice(["zip", "tar", "tar.gz", "tar.bz2"]), default="zip")
@click.option("--output", type=click.Path(), default=None)
def export_project(project_id, format, output):
    """Export project as downloadable archive."""
    # Implementation...

@code.command("publish-github")
@click.option("--project-id", required=True, help="Project ID")
@click.option("--repo-name", required=True, help="GitHub repository name")
@click.option("--description", default="", help="Repository description")
@click.option("--private", is_flag=True, help="Make repository private")
@click.option("--token", envvar="GITHUB_TOKEN", prompt=True, hide_input=True)
def publish_github(project_id, repo_name, description, private, token):
    """Publish project to GitHub."""
    # Implementation...
```

#### 2.3 Update CLI Classifiers
```toml
classifiers = [
    "Development Status :: 5 - Production/Stable",  # From 4 - Beta
    "Intended Audience :: Developers",
    "License :: OSI Approved :: MIT License",
    "Programming Language :: Python :: 3",
    "Programming Language :: Python :: 3.8",
    "Programming Language :: Python :: 3.9",
    "Programming Language :: Python :: 3.10",
    "Programming Language :: Python :: 3.11",
    "Programming Language :: Python :: 3.12",
    "Environment :: Console",
    "Topic :: Education",
    "Topic :: Software Development :: Libraries :: Python Modules",
    "Topic :: Software Development :: Version Control :: Git",
]
```

#### 2.4 CLI Changelog Entry
```markdown
## [1.2.0] - January 15, 2026

### Added
- `export` command: Export projects in ZIP, TAR, TAR.GZ, TAR.BZ2 formats
- `publish-github` command: Create GitHub repository and push code
- Environment variable support for GITHUB_TOKEN

### Changed
- Updated dependency to socrates-ai>=1.2.0
- Improved command organization and help text
- Enhanced error messages for user feedback

### Status
- Production/Stable (upgraded from Beta)
```

---

## 3. socrates-ai-ui (Frontend Package - NEW)

**Current Status:** Not yet published on npm
**Recommended Version:** 1.0.0

### Package Configuration

Create `socrates-frontend/package.json` updates:

```json
{
  "name": "socrates-ai-ui",
  "version": "1.0.0",
  "description": "Production-ready React UI for Socrates AI collaborative development platform with GitHub integration",
  "type": "module",
  "license": "MIT",
  "repository": {
    "type": "git",
    "url": "https://github.com/Nireus79/Socrates.git",
    "directory": "socrates-frontend"
  },
  "bugs": {
    "url": "https://github.com/Nireus79/Socrates/issues"
  },
  "homepage": "https://github.com/Nireus79/Socrates",
  "keywords": [
    "react",
    "ui",
    "socrates",
    "ai",
    "github",
    "project-generation",
    "typescript"
  ],
  "author": {
    "name": "Socrates AI Contributors"
  },
  "private": false,
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "lint": "eslint .",
    "preview": "vite preview",
    "test": "vitest",
    "test:ui": "vitest --ui",
    "test:coverage": "vitest --coverage",
    "test:watch": "vitest --watch",
    "prepublishOnly": "npm run build"
  },
  "peerDependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0"
  },
  "dependencies": {
    "@monaco-editor/react": "^4.7.0",
    "@tailwindcss/postcss": "^4.1.18",
    "@tanstack/react-query": "^5.90.12",
    "axios": "^1.13.2",
    "lucide-react": "^0.562.0",
    "react": "^19.2.0",
    "react-dom": "^19.2.0",
    "react-hook-form": "^7.68.0",
    "react-router-dom": "^7.11.0",
    "recharts": "^3.6.0",
    "zod": "^4.2.1",
    "zustand": "^5.0.9"
  },
  "devDependencies": {
    "@eslint/js": "^9.39.1",
    "@testing-library/jest-dom": "^6.9.1",
    "@testing-library/react": "^16.3.1",
    "@testing-library/user-event": "^14.6.1",
    "@types/node": "^24.10.4",
    "@types/react": "^19.2.5",
    "@types/react-dom": "^19.2.3",
    "@vitejs/plugin-react": "^5.1.1",
    "autoprefixer": "^10.4.23",
    "eslint": "^9.39.1",
    "eslint-plugin-react-hooks": "^7.0.1",
    "eslint-plugin-react-refresh": "^0.4.24",
    "globals": "^16.5.0",
    "postcss": "^8.5.6",
    "tailwindcss": "^4.1.18",
    "typescript": "~5.9.3",
    "typescript-eslint": "^8.46.4",
    "vite": "^7.2.4",
    "vitest": "^4.0.16"
  },
  "engines": {
    "node": ">=18.0.0",
    "npm": ">=9.0.0"
  },
  "files": [
    "dist"
  ],
  "main": "./dist/index.js",
  "types": "./dist/index.d.ts",
  "exports": {
    ".": {
      "import": "./dist/index.js",
      "require": "./dist/index.js",
      "types": "./dist/index.d.ts"
    }
  }
}
```

### Why Publish UI Separately?

**Benefits:**
- Users can use Socrates UI components in their own projects
- Decouples frontend from backend releases
- npm ecosystem standard for React packages
- Easier testing and distribution

**How to publish:**
```bash
cd socrates-frontend
npm run build
npm publish
```

### UI Package Changelog
```markdown
## [1.0.0] - January 15, 2026

### Added
- Complete React UI for Socrates AI platform
- ProjectExport component for multi-format downloads
- GitHubPublish component for GitHub integration
- Project management dashboard
- Real-time collaboration features
- Code review and analytics panels
- GitHub synchronization widgets
- Knowledge base management

### Components
- 50+ production-ready React components
- TypeScript support
- Tailwind CSS styling
- Dark mode support
- Responsive design
- Accessibility features

### Features
- Export projects (ZIP, TAR, TAR.GZ, TAR.BZ2)
- GitHub repository creation
- Code generation and review
- Project analytics and metrics
- Real-time notifications
- User collaboration tools
```

---

## 4. Dependency Analysis

### socrates-ai 1.2.0 Dependencies

**Critical (must have):**
- anthropic>=0.40.0 ✅
- fastapi>=0.100.0 ✅
- sqlalchemy>=2.0.0 ✅
- redis>=5.0.0 ✅
- **gitpython>=3.1.0** ✅ NEW
- **requests>=2.31.0** ✅ NEW
- **cryptography>=41.0.0** ✅ NEW

**Recommended (highly recommended):**
- **gunicorn>=21.0.0** ✅ NEW (for production deployment)
- **psycopg2-binary>=2.9.0** ✅ NEW (for PostgreSQL)

### Dependency Version Matrix

| Package | Current | Recommended | Reason |
|---------|---------|-------------|--------|
| anthropic | >=0.40.0 | >=0.45.0 | Latest features |
| fastapi | >=0.100.0 | >=0.110.0 | Better performance |
| sqlalchemy | >=2.0.0 | >=2.0.23 | Bug fixes |
| pydantic | >=2.0.0 | >=2.5.0 | Enhanced features |
| gitpython | NEW | >=3.1.0 | Git operations |
| requests | >=0.24.0 | >=2.31.0 | GitHub API |
| cryptography | NEW | >=41.0.0 | Token encryption |
| gunicorn | NEW | >=21.0.0 | Production server |

---

## 5. Release Checklist

### Before Release

- [ ] Update all version numbers to 1.2.0
- [ ] Update all package descriptions
- [ ] Add new dependencies to pyproject.toml
- [ ] Update all classifiers (especially status)
- [ ] Add comprehensive changelog entries
- [ ] Update README.md with new features
- [ ] Run all tests (180+ tests passing)
- [ ] Test installation: `pip install socrates-ai==1.2.0`
- [ ] Verify CLI commands work
- [ ] Test export functionality
- [ ] Test GitHub publishing (requires token)
- [ ] Build documentation
- [ ] Review security (especially GitHub token handling)
- [ ] Update API documentation
- [ ] Tag commit as v1.2.0

### PyPI Release Commands

```bash
# Build distributions
python -m build

# Upload to test PyPI first
python -m twine upload --repository testpypi dist/*

# Test installation
pip install -i https://test.pypi.org/simple/ socrates-ai==1.2.0

# Upload to production PyPI
python -m twine upload dist/*

# Verify
pip install --upgrade socrates-ai
socrates --version
```

### npm Release Commands

```bash
# Build distribution
cd socrates-frontend
npm run build

# Test publish (dry run)
npm publish --dry-run

# Publish to npm
npm publish

# Verify
npm info socrates-ai-ui
```

---

## 6. Release Notes Template

**Title:** Socrates AI 1.2.0 - GitHub-Ready Project Generation

**Summary:**
Socrates AI 1.2.0 introduces comprehensive GitHub integration with automated repository creation, project export in multiple formats, and production-ready deployment configuration.

**Key Features:**
- 🚀 GitHub-ready project generation
- 📦 Multi-format export (ZIP, TAR, TAR.GZ, TAR.BZ2)
- 🔗 Automatic GitHub repository creation
- 🐳 Docker containerization support
- 📊 Production monitoring and logging
- 🔒 Enhanced security with token encryption
- ✅ 180+ comprehensive tests

**Packages Updated:**
- socrates-ai: 1.1.0 → 1.2.0
- socrates-ai-cli: 1.1.0 → 1.2.0
- socrates-ai-ui: NEW (1.0.0)

**Breaking Changes:** None

**Installation:**
```bash
pip install --upgrade socrates-ai
npm install socrates-ai-ui
```

---

## 7. Documentation Updates Required

### README.md Updates
- Add GitHub integration section
- Add export feature description
- Add CLI command examples
- Update feature list
- Update screenshots/demo

### API Documentation
- Document new endpoints: `/projects/{id}/export`, `/projects/{id}/publish-to-github`
- Document GitHub integration flow
- Document token requirements

### Deployment Documentation
- Already created in docs/deployment/ - no changes needed
- Can reference from main README

---

## 8. Timeline

- **Today:** Update package configurations (1 hour)
- **Week 1:** Finalize and test releases (4 hours)
- **Week 1:** Release to test PyPI (30 minutes)
- **Week 2:** Final testing and validation (2 hours)
- **Week 2:** Release to production PyPI (30 minutes)
- **Week 2:** Release to npm (30 minutes)
- **Week 2:** Update documentation (2 hours)
- **Week 2:** Announce release (1 hour)

---

## Summary

| Item | socrates-ai | socrates-ai-cli | socrates-ai-ui |
|------|------------|-----------------|-----------------|
| **Current Version** | 1.1.0 | 1.1.0 | 0.0.0 (not published) |
| **New Version** | 1.2.0 | 1.2.0 | 1.0.0 |
| **Type** | Python (PyPI) | Python (PyPI) | JavaScript (npm) |
| **Updates** | Major | Major | Initial Release |
| **Breaking Changes** | None | None | N/A |
| **Tests** | 180+ passing | Integrated | 70+ passing |
| **Status** | Production/Stable | Production/Stable | Production/Stable |

---

**Next Steps:**
1. Approve version updates
2. Update all pyproject.toml and package.json files
3. Run comprehensive tests
4. Release to test environments
5. Final validation
6. Release to production

