# PyPI Publication Version Status

## Current Local Versions

| Library | Local Version | Git Tag | Status |
|---------|---------------|---------|--------|
| socratic-learning | 0.1.0 | v0.1.0 | ⏳ Ready for release |
| socratic-workflow | 0.1.0 | v0.1.0 | ⏳ Ready for release |
| socratic-analyzer | 0.1.0 | v0.1.0 | ⏳ Ready for release |
| socratic-rag | 0.1.0 | v0.1.0 | ⏳ Ready for release |
| socratic-knowledge | 0.1.1 | v0.1.0 | ⚠️ Version mismatch |
| socratic-agents | 0.1.2 | v0.1.0 | ⚠️ Version mismatch |
| socratic-conflict | 0.1.1 | v0.1.0 | ⚠️ Version mismatch |
| socratic-docs | 0.1.0 | v0.1.0 | ⏳ Ready for release |
| socratic-performance | 0.1.0 | v0.1.0 | ⏳ Ready for release |

## Version Mismatch Issues

Three libraries have version mismatches between their pyproject.toml and git tags:

### socratic-knowledge
- **Current Version**: 0.1.1
- **Git Tag**: v0.1.0
- **Action Required**: Either update git tag to v0.1.1 or downgrade version to 0.1.0

### socratic-agents
- **Current Version**: 0.1.2
- **Git Tag**: v0.1.0
- **Action Required**: Either update git tag to v0.1.2 or downgrade version to 0.1.0

### socratic-conflict
- **Current Version**: 0.1.1
- **Git Tag**: v0.1.0
- **Action Required**: Either update git tag to v0.1.1 or downgrade version to 0.1.0

## What's Already Published on PyPI?

Check published versions:
```bash
# Check each package
pip index versions socratic-learning
pip index versions socratic-workflow
pip index versions socratic-analyzer
pip index versions socratic-rag
pip index versions socratic-knowledge
pip index versions socratic-agents
pip index versions socratic-conflict
pip index versions socratic-docs
pip index versions socratic-performance
```

Or visit:
- https://pypi.org/project/socratic-learning/
- https://pypi.org/project/socratic-workflow/
- https://pypi.org/project/socratic-analyzer/
- https://pypi.org/project/socratic-rag/
- https://pypi.org/project/socratic-knowledge/
- https://pypi.org/project/socratic-agents/
- https://pypi.org/project/socratic-conflict/
- https://pypi.org/project/socratic-docs/
- https://pypi.org/project/socratic-performance/

## Workflow Updates

✅ All publish.yml workflows have been updated to use `PYPI_API_TOKEN` instead of `PYPI_API_KEY`.

The workflows now correctly reference:
```yaml
password: ${{ env.PYPI_API_TOKEN }}
env:
  PYPI_API_TOKEN: ${{ secrets.PYPI_API_TOKEN }}
```

## Next Steps

### Option 1: Fix Version Mismatches (Recommended)

For each library with mismatch, choose:

**A. Update git tags to match versions:**
```bash
# For socratic-knowledge
cd /c/Users/themi/Socratic-knowledge
git tag -d v0.1.0
git push origin :refs/tags/v0.1.0
git tag -a v0.1.1 -m "Release v0.1.1: Socratic-knowledge"
git push origin v0.1.1

# Repeat for socratic-agents (v0.1.2) and socratic-conflict (v0.1.1)
```

**B. Or downgrade versions to 0.1.0:**
```bash
# Edit pyproject.toml
# Change: version = "0.1.1" → version = "0.1.0"
# Commit and push
```

### Option 2: Create Releases Immediately

If versions are already published (check PyPI first), versions need to be incremented before releasing.

## Publishing Process

Once version issues are resolved:

1. **Verify all versions match git tags**
2. **For each repository:**
   - Go to GitHub repo → Releases
   - Click "Create a new release"
   - Select the appropriate version tag
   - Add release notes
   - Click "Publish release"
3. **GitHub Actions will automatically:**
   - Build the package
   - Publish to PyPI using PYPI_API_TOKEN

## GitHub Secrets Verification

Confirm `PYPI_API_TOKEN` is set in each repository:
```bash
# For each repo on GitHub:
# Settings → Secrets and variables → Actions
# Should see: PYPI_API_TOKEN
```

## Troubleshooting

If publish workflow fails:
1. Check GitHub Actions logs for the specific error
2. Verify PYPI_API_TOKEN is correctly set
3. Verify version is not already published on PyPI
4. Check pyproject.toml is valid (no syntax errors)

## Status Summary

- ✅ All workflows updated to use PYPI_API_TOKEN
- ✅ All packages configured for automatic PyPI publishing
- ⚠️ Version mismatches need resolution (3 libraries)
- ⏳ Ready for release creation once versions are aligned

