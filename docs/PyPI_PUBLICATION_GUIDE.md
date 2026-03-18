# PyPI Publication Guide

## Overview
All 8 extracted Socratic libraries are now ready for PyPI publication. Release tags (v0.1.0) have been created and pushed to GitHub.

## Released Libraries

| Library | Repository | Status | PyPI Package |
|---------|-----------|--------|--------------|
| socratic-learning | Socratic-learning | ✅ Tagged v0.1.0 | [Link](https://pypi.org/project/socratic-learning/) |
| socratic-workflow | Socratic-workflow | ✅ Tagged v0.1.0 | [Link](https://pypi.org/project/socratic-workflow/) |
| socratic-analyzer | Socratic-analyzer | ✅ Tagged v0.1.0 | [Link](https://pypi.org/project/socratic-analyzer/) |
| socratic-rag | Socratic-rag | ✅ Tagged v0.1.0 | [Link](https://pypi.org/project/socratic-rag/) |
| socratic-performance | Socratic-performance | ✅ Tagged v0.1.0 | [Link](https://pypi.org/project/socratic-performance/) |
| socratic-docs | Socratic-docs | ✅ Tagged v0.1.0 | [Link](https://pypi.org/project/socratic-docs/) |
| socratic-knowledge | Socratic-knowledge | ✅ Tagged v0.1.0 | [Link](https://pypi.org/project/socratic-knowledge/) |
| socratic-agents | Socratic-agents | ✅ Tagged v0.1.0 | [Link](https://pypi.org/project/socratic-agents/) |
| socratic-conflict | Socratic-conflict | ✅ Tagged v0.1.0 | [Link](https://pypi.org/project/socratic-conflict/) |

## Completion Checklist

### ✅ Completed
- [x] All libraries extracted and organized in separate repositories
- [x] Comprehensive documentation created for each library
- [x] CI/CD workflows configured (test.yml, lint.yml, publish.yml)
- [x] Code quality verified (ruff and mypy passing)
- [x] GitHub Sponsors configured (FUNDING.yml)
- [x] All repositories pushed to GitHub
- [x] Release tags (v0.1.0) created and pushed
- [x] pyproject.toml properly configured with metadata and dependencies

### ⏳ Pending - Manual GitHub Configuration
To complete PyPI publication, you need to:

1. **Create PyPI API Token**
   ```bash
   # Go to https://pypi.org/manage/account/
   # Create an API token for publishing
   # Copy the token (format: pypi-AgEIcHlwaS5vcmc...)
   ```

2. **Add PYPI_API_KEY Secret to Each Repository**

   For each of the 8 library repositories:
   - Go to GitHub repo → Settings → Secrets and variables → Actions
   - Click "New repository secret"
   - Name: `PYPI_API_KEY`
   - Value: [Your PyPI API Token]
   - Click "Add secret"

   Repositories requiring this secret:
   - Socratic-learning
   - Socratic-workflow
   - Socratic-analyzer
   - Socratic-rag
   - Socratic-performance
   - Socratic-docs
   - Socratic-knowledge
   - Socratic-agents
   - Socratic-conflict

3. **Create Releases on GitHub**

   After adding the PYPI_API_KEY secret to each repository:

   - Go to each repository on GitHub
   - Click "Releases" on the right sidebar
   - Click "Create a new release" or select the v0.1.0 tag
   - Fill in release notes (optional but recommended)
   - Click "Publish release"

   This will trigger the GitHub Actions publish.yml workflow automatically.

## How Publication Works

When you create/edit a release on GitHub:
1. The `publish.yml` workflow is triggered
2. The workflow checks out the code
3. Builds the Python package using `python -m build`
4. Uses the `pypa/gh-action-pypi-publish` action to upload to PyPI
5. The PYPI_API_KEY secret is used for authentication

## Verify Publication

After creating releases, verify that packages are published:

```bash
# Check PyPI for each package
pip index versions socratic-learning
pip index versions socratic-workflow
# etc.

# Or install them
pip install socratic-learning
pip install socratic-workflow
```

## Main Socrates Package

The main `socrates-ai` package (v1.3.3) is already configured in `pyproject.toml` to depend on all 8 extracted libraries:

```toml
dependencies = [
    "socratic-agents>=0.1.0",
    "socratic-analyzer>=0.1.0",
    "socratic-conflict>=0.1.0",
    "socratic-knowledge>=0.1.0",
    "socratic-learning>=0.1.0",
    "socratic-rag>=0.1.0",
    "socratic-workflow>=0.1.0",
]
```

This means when users install `socrates-ai`, all dependencies will be automatically installed from PyPI.

## Architecture

```
PyPI Registry
    ↓
    ├─ socratic-learning (0.1.0)
    ├─ socratic-workflow (0.1.0)
    ├─ socratic-analyzer (0.1.0)
    ├─ socratic-rag (0.1.0)
    ├─ socratic-performance (0.1.0)
    ├─ socratic-docs (0.1.0)
    ├─ socratic-knowledge (0.1.0)
    ├─ socratic-agents (0.1.0)
    └─ socratic-conflict (0.1.0)
        ↓
    socrates-ai (1.3.3) - main package
```

## Next Steps After Publication

1. **Update Installation Documentation**
   ```bash
   # Users can now install with
   pip install socrates-ai
   ```

2. **Update Main Repository README**
   - Add PyPI badges
   - Update installation instructions
   - Link to each library's documentation

3. **Announce Release**
   - Create release notes for socrates-ai
   - Announce on GitHub discussions/releases
   - Update community channels

## Support

For issues with any library:
- Check the library's GitHub repository Issues
- Each library has comprehensive documentation in its `/docs` directory
- See main Socrates repo for integration guides

## Package Versions

- All 8 libraries: **0.1.0** (Alpha status - API may change)
- Main Socrates: **1.3.3** (Production/Stable)
- Python version support: **3.9+** (libraries), **3.8+** (main package)

