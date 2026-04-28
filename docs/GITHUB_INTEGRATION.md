# GitHub Integration & Code Management Guide

> **Note**: For basic installation and setup instructions, see [Installation Guide](INSTALLATION.md) or [Quick Start Guide](QUICK_START_GUIDE.md). This guide covers advanced GitHub repository management features.

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

This will analyze the project's code structure, dependencies, and potential issues.

---

## Advanced Features

(Content continues with GitHub integration features...)

For more details, see the [Installation Guide](INSTALLATION.md).
