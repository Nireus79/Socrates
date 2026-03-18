# PyPI Release Action Plan

## Current Status Analysis

### Already Published on PyPI ✅

| Library | Published Version | Local Version | Status |
|---------|-------------------|---------------|--------|
| socratic-learning | 0.1.0 | 0.1.0 | ✅ Matching |
| socratic-workflow | 0.1.0 | 0.1.0 | ✅ Matching |
| socratic-analyzer | 0.1.0 | 0.1.0 | ✅ Matching |
| socratic-rag | 0.1.0 | 0.1.0 | ✅ Matching |
| socratic-knowledge | 0.1.0, 0.1.1 | 0.1.1 | ✅ Matching |
| socratic-agents | 0.1.0, 0.1.1, 0.1.2 | 0.1.2 | ✅ Matching |
| socratic-conflict | 0.1.0, 0.1.1 | 0.1.1 | ✅ Matching |

### Not Yet Published ⏳

| Library | Local Version | Status |
|---------|---------------|--------|
| socratic-docs | 0.1.0 | ⏳ Ready to publish |
| socratic-performance | 0.1.0 | ⏳ Ready to publish |

## Key Finding: Git Tag Mismatch

The issue is that all git tags are v0.1.0, but some libraries have higher versions published:
- socratic-knowledge: published 0.1.1, git tag is v0.1.0 ❌
- socratic-agents: published 0.1.2, git tag is v0.1.0 ❌
- socratic-conflict: published 0.1.1, git tag is v0.1.0 ❌

## Action Required

### Step 1: Create Correct Version Tags

For libraries with published versions > 0.1.0:

**socratic-knowledge:**
```bash
cd /c/Users/themi/Socratic-knowledge
git tag -d v0.1.0
git push origin :refs/tags/v0.1.0
git tag -a v0.1.1 -m "Release v0.1.1: Socratic Knowledge Management"
git push origin v0.1.1
```

**socratic-agents:**
```bash
cd /c/Users/themi/Socratic-agents
git tag -d v0.1.0
git push origin :refs/tags/v0.1.0
git tag -a v0.1.2 -m "Release v0.1.2: Socratic Agents"
git push origin v0.1.2
```

**socratic-conflict:**
```bash
cd /c/Users/themi/Socratic-conflict
git tag -d v0.1.0
git push origin :refs/tags/v0.1.0
git tag -a v0.1.1 -m "Release v0.1.1: Socratic Conflict Detection"
git push origin v0.1.1
```

### Step 2: Create GitHub Releases

After tags are correct, for each repository:

1. Go to GitHub: `https://github.com/Nireus79/[repository-name]`
2. Click "Releases" in the right sidebar
3. Click "Create a new release"
4. Select the appropriate tag:
   - socratic-learning → v0.1.0
   - socratic-workflow → v0.1.0
   - socratic-analyzer → v0.1.0
   - socratic-rag → v0.1.0
   - socratic-knowledge → v0.1.1 (after creating tag)
   - socratic-agents → v0.1.2 (after creating tag)
   - socratic-conflict → v0.1.1 (after creating tag)
   - socratic-docs → v0.1.0
   - socratic-performance → v0.1.0
5. Add release notes
6. Check "This is a pre-release" (optional, since v0.1.x is alpha)
7. Click "Publish release"

### Step 3: GitHub Actions Will Handle Publishing

- For already published versions (0.1.0, 0.1.1, 0.1.2): Workflows may skip or fail with "version already exists" - this is normal, the version is already on PyPI
- For unpublished versions (socratic-docs, socratic-performance): Workflows will successfully publish to PyPI

## Why This Approach?

✅ Versions are already on PyPI and working
✅ Cannot downgrade or re-publish same versions
✅ Only need to create GitHub releases for version visibility
✅ Unpublished libraries will auto-publish via workflow
✅ No version bumping needed - all versions match local code

## Timeline

1. Create new git tags (5 min)
2. Push new tags (1 min)
3. Create GitHub releases (15 min for all 9 repos)
4. Watch GitHub Actions execute publish workflows (5-10 min)
5. Verify PyPI has all versions (2 min)

**Total: ~30 minutes to complete**

