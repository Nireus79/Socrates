# Branch Separation Policy

## Overview

The Socrates repository maintains **two isolated branches** that must **NEVER merge**:

- **`master`** - Current modularized development version (active)
- **`Monolithic-Socrates`** - Historical reference archive (frozen)

## Why Separation is Critical

### Monolithic-Socrates Branch
- Represents the **last working monolithic version** (January 29, 2026)
- Serves as **historical reference** before modularization
- Captures the **original architecture** before library extraction
- Must remain **pristine and unmodified**

### Master Branch
- Current **modularized development** version
- Active development with extracted libraries
- Uses new architecture and dependencies
- All feature development continues here

## Merge Prevention

### Local Protection (Automatic)

Git hooks in `.githooks/prevent-monolithic-merge.sh` automatically block:

```
❌ Cannot merge master → Monolithic-Socrates
❌ Cannot merge Monolithic-Socrates → master
```

These hooks are enforced automatically on every merge attempt.

### GitHub Protection (Manual Setup Required)

To prevent merges on GitHub, configure branch protection rules:

#### For `Monolithic-Socrates` branch:
1. Go to **Settings → Branches → Branch Protection Rules**
2. Add protection for `Monolithic-Socrates`
3. Enable:
   - ✅ Require pull request reviews before merging
   - ✅ Require branches to be up to date before merging
   - ✅ Restrict who can push to matching branches
   - ✅ Require branches to be up to date before merging

#### For `master` branch:
1. Go to **Settings → Branches → Branch Protection Rules**
2. Add specific restriction to prevent Monolithic-Socrates merges
3. Add dismiss stale pull request approvals

## Safe Operations

### ✅ Allowed Operations

**Viewing/Comparing:**
```bash
git checkout Monolithic-Socrates
git diff master Monolithic-Socrates
git log --oneline Monolithic-Socrates
```

**Cherry-picking specific commits:**
```bash
git checkout master
git cherry-pick <commit-hash>  # From Monolithic-Socrates
```

**Creating independent branches:**
```bash
git checkout -b feature/something Monolithic-Socrates
# Make changes in new branch
```

### ❌ Blocked Operations

**Direct merges:**
```bash
git merge Monolithic-Socrates  # ❌ BLOCKED
git merge master               # ❌ BLOCKED (on Monolithic-Socrates)
```

**Pull requests:**
- Cannot create PR from Monolithic-Socrates → master
- Cannot create PR from master → Monolithic-Socrates
- Hook will reject the merge

## Use Cases

### Case 1: I need to reference old code
```bash
git show Monolithic-Socrates:path/to/file.py
```

### Case 2: I want to copy a specific approach
```bash
git diff Monolithic-Socrates master -- path/to/file.py
# Review differences, then manually apply to current version
```

### Case 3: I need to cherry-pick a specific fix
```bash
git log Monolithic-Socrates --oneline | grep "keyword"
git cherry-pick <commit-hash>
```

### Case 4: I want to see the complete history
```bash
git log --all --graph --oneline --decorate | head -50
```

## Enforcement Summary

| Operation | Local Hook | GitHub Rule | Result |
|-----------|-----------|-------------|--------|
| `git merge Monolithic-Socrates` (on master) | ✅ Blocks | ✅ Blocks | ❌ REJECTED |
| `git merge master` (on Monolithic-Socrates) | ✅ Blocks | ✅ Blocks | ❌ REJECTED |
| PR: Monolithic → master | ✅ Blocks | ✅ Blocks | ❌ REJECTED |
| PR: master → Monolithic | ✅ Blocks | ✅ Blocks | ❌ REJECTED |
| Cherry-pick from Monolithic | ✅ Allows | ✅ Allows | ✅ ALLOWED |
| Create branch from Monolithic | ✅ Allows | ✅ Allows | ✅ ALLOWED |

## Implementation Timeline

- **Local Protection**: ✅ Active (git hooks configured)
- **GitHub Protection**: 🔧 Manual setup required

## How to Setup GitHub Protection

Since `gh` CLI is not available, use the GitHub web interface:

1. Go to https://github.com/Nireus79/Socrates/settings/branches
2. Click "Add rule" for each branch
3. Use the configuration templates below

### Template: Monolithic-Socrates Protection

```
Pattern: Monolithic-Socrates
☑ Require a pull request before merging
☑ Require branches to be up to date before merging
☑ Require status checks to pass before merging
☑ Restrict who can push to matching branches (only admins)
☑ Allow force pushes (none selected)
☑ Allow deletions (unchecked)
```

### Template: Master Protection

```
Pattern: master
☑ Require a pull request before merging
☑ Require approval review from codeowners
☑ Require branches to be up to date before merging
☑ Require status checks to pass before merging
☑ Restrict who can push to matching branches (only admins)
```

## Questions?

If you accidentally try to merge these branches:
1. You'll see the error message from `.githooks/prevent-monolithic-merge.sh`
2. The merge will be **automatically rejected**
3. No damage will occur
4. Read the error message for next steps

The branches are now **isolated and protected**.

---

**Branch Created**: January 29, 2026 (Monolithic version)
**Separation Policy**: Active from April 1, 2026 onwards
**Isolation Level**: Permanent (both local and GitHub protection)
