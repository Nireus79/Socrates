# GitHub Integration & Code Management Guide

> **Note**: For basic installation and setup instructions, see [Installation Guide](INSTALLATION.md). This guide covers GitHub repository management features.

## Overview

Socrates AI supports importing GitHub repositories, analyzing code, running tests, and applying fixes - all without needing a Socratic chat session!

---

## Basic Workflow

### 1. Import a GitHub Repository

```bash
/github import https://github.com/username/repo-name [optional-project-name]
```

**Example:**
```bash
/github import https://github.com/torvalds/linux My Linux Project
```

**What Happens:**
- Repository is cloned to a temporary directory
- Code is analyzed (syntax, dependencies, tests)
- Project is saved to the database
- Validation results are displayed

**Expected Output:**
```
[OK] Repository imported as project 'linux'!

Repository Information:
  Language: C | Files: 67234 | Tests: Yes

Code Validation:
  Overall Status: PASS | Issues: 0 | Warnings: 5
```

---

## Project Analysis Commands

### 2. Analyze Project Code

```bash
/project analyze [project-id]
```

**What It Does:**
- Counts files and lines of code
- Detects programming languages
- Assesses code complexity
- Identifies code patterns
- Provides quality metrics

**Example:**
```bash
$ /project analyze

Code Structure Analysis:
  Total Files: 42 | Lines of Code: 5,234
  Languages: Python (85%), JavaScript (15%)
  Complexity: Medium
  Quality Score: 75/100
```

### 3. Run Tests

```bash
/project test [project-id] [--verbose]
```

**What It Does:**
- Auto-detects test framework (pytest, unittest, jest, mocha)
- Runs all tests
- Reports pass/fail/skip counts
- Shows failure details with line numbers

**Example:**
```bash
$ /project test

Running tests with pytest...
Tests Passed: 145
Tests Failed: 2
Tests Skipped: 5

Failures:
  • test_auth.py:45 - AssertionError: Expected 200, got 404
```

### 4. Validate Project

```bash
/project validate [project-id]
```

**What It Does:**
- Checks Python syntax in all files
- Validates dependencies (requirements.txt)
- Runs test suite
- Provides overall quality assessment

**Example:**
```bash
$ /project validate

Phase 1: Syntax Check
  ✓ All files have valid syntax

Phase 2: Dependencies
  ✓ All dependencies available
  ! 2 unused imports detected

Phase 3: Tests
  ✓ 145 tests passed

Overall Status: PASS
```

### 5. Fix Code Issues

```bash
/project fix [issue-type]
```

**Issue Types:**
- `syntax` - Fix syntax errors
- `style` - Fix style/PEP 8 violations
- `dependencies` - Add missing dependencies
- `all` - Try to fix all issues

**Example:**
```bash
$ /project fix syntax

Found 3 syntax errors:
  • main.py:42 - Missing colon in function definition
  • utils.py:15 - Unclosed parenthesis
  • config.py:8 - Invalid indentation

Apply fixes? (yes/no): yes
[OK] 3 fixes applied!
```

### 6. Review Code

```bash
/project review [project-id]
```

**What It Does:**
- Comprehensive code review by Claude
- Rates code quality (1-10)
- Identifies strengths
- Suggests improvements
- Detects design patterns

**Example:**
```bash
$ /project review

Code Review Results:
  Quality Rating: 7/10

Strengths:
  ✓ Good separation of concerns
  ✓ Comprehensive error handling
  ✓ Well-documented functions

Improvements:
  • Add type hints for better IDE support
  • Reduce function complexity in auth.py
  • Add more integration tests

Design Patterns Found:
  • Factory pattern in data layer
  • Strategy pattern in handlers
```

### 7. Compare Validation Results

```bash
/project diff <validation1> <validation2>
```

**What It Does:**
- Shows changes between two validation runs
- Tracks improvements over time
- Highlights issues resolved or introduced

**Example:**
```bash
$ /project diff validation_old validation_new

Improvement Summary:
  Issues Resolved: 5
  New Issues: 0
  Quality Change: +15 points

  Files Modified: 8
  Lines Added: 245
  Lines Removed: 123
```

---

## GitHub Synchronization

### 8. Pull Latest Changes

```bash
/github pull [project-id]
```

**What It Does:**
- Fetches latest changes from GitHub
- Shows what changed (files added/modified/deleted)
- Re-runs validation on new code

**Example:**
```bash
$ /github pull

Pulling latest changes from GitHub...
[OK] Successfully pulled latest changes!

Changes Summary:
  +5 lines | -3 lines
  2 files modified

Validation Results:
  Overall Status: PASS
```

### 9. Push Changes Back to GitHub

```bash
/github push [project-id] [commit-message]
```

**What It Does:**
- Shows what will be pushed (git diff)
- Requires explicit confirmation (type "yes")
- Pushes changes to GitHub
- Requires GITHUB_TOKEN environment variable

**Example:**
```bash
$ /github push "Fixed authentication bug"

Changes to push:
  +import hashlib
  -import md5
  +def hash_password(pwd):
  -def md5_hash(pwd):

Proceed with push? (yes/no): yes
[OK] Push completed successfully!
```

**Setup Required:**
```bash
export GITHUB_TOKEN=ghp_your_token_here
```

### 10. Sync with GitHub (Pull + Push)

```bash
/github sync [project-id]
```

**What It Does:**
- Pulls latest changes from GitHub
- Pushes local changes back
- Shows unified status

**Example:**
```bash
$ /github sync

Step 1: Pulling latest changes from GitHub
[OK] Pulled successfully

Step 2: Pushing local changes to GitHub
Commit message: Updated dependencies
Proceed with push? (yes/no): yes
[OK] Pushed successfully

Summary:
  • Pulled latest changes from GitHub
  • Pushed local changes to GitHub
```

---

## Common Workflows

### Workflow A: Import and Analyze

```bash
1. /github import https://github.com/user/project
2. /project analyze
3. /project test
```

### Workflow B: Fix Issues

```bash
1. /project validate                    # Find issues
2. /project fix syntax                  # Fix syntax errors
3. /project fix dependencies            # Add missing deps
4. /project test                        # Verify fixes work
5. /github push "Fixed issues"          # Push to GitHub
```

### Workflow C: Continuous Improvement

```bash
1. /project analyze                     # Get baseline
2. /project review                      # Get recommendations
3. /project fix all                     # Apply automated fixes
4. /project test                        # Verify tests pass
5. /project diff old new                # Show improvement
6. /github sync                         # Sync with GitHub
```

### Workflow D: Track Progress

```bash
1. /github pull                         # Get latest
2. /project validate                    # Full validation
3. /project diff prev_validation now    # See improvement
4. /project analyze                     # Current state
```

---

## NLU Commands (Natural Language)

You can use natural language in presession mode:

```bash
"analyze the project"              → /project analyze
"test the code"                    → /project test
"check project quality"            → /project validate
"fix syntax errors"                → /project fix syntax
"review my code"                   → /project review
"pull from github"                 → /github pull
"push to github"                   → /github push
"sync with github"                 → /github sync
```

---

## Tips & Tricks

### Tip 1: View Project Status Quickly
```bash
/project status                 # Shows current project info
```

### Tip 2: Load a Different Project
```bash
/project load project-id        # Switch to different project
```

### Tip 3: List All Projects
```bash
/project list                   # View all saved projects
```

### Tip 4: Large Repository?
Use `--timeout` for longer operations:
```bash
/project test --timeout 600     # 10 minute timeout instead of default
```

### Tip 5: Verbose Output
Get more details:
```bash
/project test --verbose         # Show full test output
/project analyze                # Already shows details
```

---

## Troubleshooting

### Issue: "Not linked to a GitHub repository"

**Cause:** Project was created locally, not imported from GitHub

**Solution:** Use `/github import` to import a GitHub repo, or import the project's code

### Issue: "Must be logged in"

**Cause:** User authentication required

**Solution:** Use `/user login` first

### Issue: "Authentication failed" on push

**Cause:** GITHUB_TOKEN not set or invalid

**Solution:**
```bash
export GITHUB_TOKEN=ghp_your_token_here
```

Get a token: https://github.com/settings/tokens/new

Required scopes:
- `repo` - for repository access
- `push` - for push capability

### Issue: "Test execution timed out"

**Cause:** Tests taking too long

**Solution:** Use custom timeout:
```bash
/project test --timeout 600     # 10 minute timeout
```

### Issue: "Push has nothing to commit"

**Cause:** No changes to push

**Solution:** Make changes to files first, then try again

---

## Requirements

### Environment Setup

```bash
# Set GitHub token for private repos / push access
export GITHUB_TOKEN=ghp_your_github_token

# Optional: Set temp directory for clones (defaults to system temp)
export SOCRATES_TEMP_DIR=/path/to/temp
```

### Dependencies

The system requires:
- Git (for clone, pull, push)
- Python 3.8+ (for syntax validation)
- pytest (for Python tests)
- npm (for JavaScript tests - optional)

---

## Best Practices

### Best Practice 1: Commit Often
```bash
/github push "Fixed typo in docs"
/github push "Added authentication"
/github push "Updated dependencies"
```

### Best Practice 2: Validate Before Pushing
```bash
/project validate                   # Make sure everything works
/project test                       # Ensure tests pass
/github push "Your message"         # Then push
```

### Best Practice 3: Track Improvements
```bash
/project validate                   # Save baseline
# ... make changes ...
/project validate                   # New validation
/project diff old new              # See improvement
```

### Best Practice 4: Review Code Regularly
```bash
/project review                     # Get recommendations
/project analyze                    # Understand structure
/project fix all                    # Apply automated fixes
```

### Best Practice 5: Sync Regularly
```bash
/github pull                        # Get latest from GitHub
# ... do your work ...
/github push "Your changes"         # Push back
```

---

## Security Notes

### 🔒 Token Security
- Never commit GITHUB_TOKEN to repository
- Use environment variables only
- Token scopes should be minimal (repo, push)

### 🔒 Confirmation on Push
- Always review git diff before pushing
- Explicit "yes" required (typos are safe)
- Commit messages shown before confirmation

### 🔒 Automated Fixes
- Review changes before accepting fixes
- Syntax fixes are safer than style fixes
- Keep backups of important code

---

## Getting Help

### View Command Documentation
```bash
/help github import
/help project analyze
/help project test
/help project fix
```

### See Command Status
```bash
/status                             # Current project status
/project list                       # All available projects
```

### Report Issues
Issues or questions? Check the logs:
```bash
/logs                               # View system logs
```

---

## Examples

### Example 1: Fresh Start with GitHub Repo

```bash
$ /github import https://github.com/openai/gpt-3
[OK] Repository imported as project 'gpt-3'!

$ /project analyze
Code Quality: 82/100
Tests: Yes
Languages: Python

$ /project test
Tests Passed: 234
Tests Failed: 0
```

### Example 2: Making Local Changes

```bash
$ /project load my-project
[OK] Project loaded: my-project

$ /project validate
Overall: PASS

$ /project fix syntax
[OK] 2 fixes applied

$ /project test
Tests Passed: 89
Tests Failed: 0

$ /github push "Fixed syntax issues"
Commit message: Fixed syntax issues
Proceed with push? (yes/no): yes
[OK] Pushed successfully
```

### Example 3: Tracking Progress

```bash
$ /project analyze
Quality Score: 65/100

$ /project review
Recommendations:
• Add type hints
• Increase test coverage
• Reduce complexity

$ /project fix all
[OK] Applied 8 fixes

$ /project analyze
Quality Score: 73/100 (+8 points!)

$ /project diff old new
Issues Resolved: 3
New Issues: 0
Improvement: +8 points
```

---

## Summary

The new GitHub integration provides a complete toolkit for:
✅ Importing and analyzing GitHub projects
✅ Running tests and validating code
✅ Applying automated fixes
✅ Getting code reviews
✅ Syncing changes with GitHub

All commands work in **presession mode** without needing a Socratic chat session!

**Start with:** `/github import <your-repo-url>`
