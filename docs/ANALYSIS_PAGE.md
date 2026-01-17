# Analysis Page - Code Analysis & Testing

Complete guide to using the Analysis page in Socrates for code validation, testing, structure analysis, and code quality improvements.

## Overview

The Analysis page provides comprehensive code analysis and testing tools for your Socrates projects. It allows you to:

- **Validate** your code for syntax errors and style issues
- **Test** your code with automated test suites
- **Analyze** project structure and complexity
- **Review** code quality and get recommendations
- **Assess** code maturity for the current phase
- **Fix** identified issues automatically
- **Report** comprehensive analysis findings

All in one integrated interface!

---

## Quick Start

1. **Navigate** to the **Analysis** section in Socrates
2. **Select** a project from the dropdown
3. **Click** any analysis button to run that analysis
4. **View** the detailed results below
5. **Iterate** by running different analyses or fixing issues

---

## Features

### 1. Code Validation ✅

**Purpose:** Validate code for syntax errors, style issues, and dependency problems.

**What it checks:**
- Syntax errors in source files
- Code style violations
- Missing or unused imports
- Dependency conflicts
- Code quality metrics

**How to use:**
1. Click the **"Validate Code"** button
2. Wait for validation to complete
3. Review the results showing:
   - Total files analyzed
   - Files with valid code
   - Files with issues
   - Detailed issues with severity
   - Overall code quality score

**Example output:**
```json
{
  "total_files": 15,
  "valid_files": 12,
  "files_with_issues": 3,
  "code_quality_score": 85,
  "issues": [
    {
      "file": "main.py",
      "line": 42,
      "column": 8,
      "severity": "warning",
      "message": "Unused variable 'temp'",
      "code": "W0612"
    }
  ]
}
```

---

### 2. Run Tests 🧪

**Purpose:** Execute test suites and measure code coverage.

**What it does:**
- Runs all configured tests (pytest, jest, mocha, etc.)
- Measures test coverage
- Reports passing and failing tests
- Shows test execution time
- Identifies failing test suites

**How to use:**
1. Click the **"Run Tests"** button
2. Wait for test execution
3. Review the results showing:
   - Test framework and type
   - Total number of tests
   - Passed, failed, and skipped counts
   - Code coverage percentage
   - Test execution duration
   - Details of any failures

**Example output:**
```json
{
  "test_type": "pytest",
  "total_tests": 45,
  "passed": 42,
  "failed": 2,
  "skipped": 1,
  "duration": 3.24,
  "coverage": 92.5,
  "failures": [
    {
      "test_name": "test_user_login",
      "error": "AssertionError: Expected 200, got 401",
      "stack_trace": "..."
    }
  ]
}
```

---

### 3. Code Review 📋

**Purpose:** Analyze code quality, best practices, and get recommendations.

**What it checks:**
- Code complexity and maintainability
- Best practice violations
- Security concerns
- Performance issues
- Design pattern violations
- Documentation completeness

**How to use:**
1. Click the **"Code Review"** button
2. Wait for analysis to complete
3. Review the findings showing:
   - Review type and scope
   - Total issues found
   - Issues by severity (critical, major, minor)
   - Suggestions for improvement
   - Detailed findings with descriptions
   - Recommendations for each issue

**Example output:**
```json
{
  "review_type": "comprehensive",
  "total_issues": 8,
  "critical": 1,
  "major": 3,
  "minor": 4,
  "suggestions": 2,
  "findings": [
    {
      "severity": "major",
      "category": "performance",
      "title": "Nested loop inefficiency",
      "description": "O(n²) algorithm detected in user filtering",
      "location": "services/user_service.py:142",
      "recommendation": "Use set intersection or hash-based lookup"
    }
  ],
  "summary": "Found 8 issues that should be addressed..."
}
```

---

### 4. Assess Maturity 📈

**Purpose:** Evaluate code maturity level for the current project phase.

**What it measures:**
- Code readiness for current phase
- Completeness of implementation
- Quality relative to phase expectations
- Readiness to advance to next phase
- Risk assessment

**How to use:**
1. Click the **"Assess Maturity"** button
2. Assessment runs for the current project phase
3. Review the maturity report showing:
   - Current phase maturity score
   - Phase completion percentage
   - Readiness assessment
   - Issues blocking phase advancement
   - Recommendations for phase completion

**Example output:**
```json
{
  "phase": "implementation",
  "maturity_score": 78,
  "phase_complete": false,
  "readiness": "partially_ready",
  "completion_percentage": 78,
  "blocking_issues": [
    "Test coverage below 80% threshold",
    "5 critical code review issues"
  ],
  "recommendations": [
    "Write additional unit tests",
    "Address critical code review findings",
    "Document API endpoints"
  ]
}
```

---

### 5. Analyze Structure 🏗️

**Purpose:** Analyze project architecture, file structure, and complexity metrics.

**What it analyzes:**
- Total files and lines of code
- Module organization and structure
- Dependency relationships
- Cyclomatic complexity
- Maintainability index
- Code organization patterns

**How to use:**
1. Click the **"Analyze Structure"** button
2. Wait for structural analysis
3. Review the findings showing:
   - Total project statistics
   - Module breakdown with details
   - Dependencies and relationships
   - Complexity scores
   - Maintainability rating
   - Structural recommendations

**Example output:**
```json
{
  "files": 42,
  "total_lines": 8234,
  "modules": [
    {
      "name": "user_service",
      "path": "services/user_service.py",
      "lines": 340,
      "functions": 12
    }
  ],
  "dependencies": ["django", "requests", "pandas"],
  "complexity_score": 42,
  "maintainability_index": 85
}
```

---

### 6. Fix Issues 🔧

**Purpose:** Automatically fix identified issues in your code.

**What it can fix:**
- Import organization and cleanup
- Code style violations
- Common anti-patterns
- Performance bottlenecks
- Security issues
- Documentation gaps

**How to use:**
1. Click the **"Fix Issues"** button
2. System analyzes and generates fixes
3. Review proposed changes showing:
   - Files to be modified
   - Number of issues fixed
   - Specific changes for each file
   - Any warnings about the changes
   - Estimated impact

**Note:** Changes are proposed but NOT automatically applied. Review before accepting.

**Example output:**
```json
{
  "apply_changes": false,
  "files_modified": 5,
  "issues_fixed": 12,
  "changes": [
    {
      "file": "main.py",
      "change_type": "modify",
      "description": "Remove unused imports, fix spacing"
    }
  ],
  "warnings": [
    "Manual review recommended for refactoring suggestions"
  ]
}
```

---

### 7. View Report 📊

**Purpose:** Get a comprehensive analysis report summarizing all key metrics.

**What it includes:**
- Overall code quality grade
- Validation status and issues
- Test coverage and results
- Project structure metrics
- Recommendations and next steps
- Maturity assessment
- Summary and action items

**How to use:**
1. Click the **"View Report"** button
2. Wait for report generation
3. Review the comprehensive report showing:
   - Executive summary
   - Code quality score and grade
   - Key metrics and statistics
   - Issues and recommendations
   - Actionable next steps

**Example output:**
```json
{
  "project_id": "proj-123",
  "generated_at": "2024-01-15T10:30:00Z",
  "code_quality": {
    "score": 82,
    "grade": "B"
  },
  "validation": {
    "status": "passed",
    "issues": 3
  },
  "tests": {
    "status": "passed",
    "coverage": 92
  },
  "structure": {
    "complexity": 42,
    "maintainability": 85
  },
  "recommendations": [
    "Address 3 validation warnings",
    "Increase test coverage to 95%",
    "Refactor high-complexity module"
  ]
}
```

---

## Workflow Examples

### Example 1: New Project Setup

1. **Create** a new project
2. Click **"Analyze Structure"** to understand organization
3. Click **"Run Tests"** to verify test suite is working
4. Click **"Code Review"** to identify early issues
5. Use **"Fix Issues"** to address code style
6. Click **"View Report"** to get baseline metrics

### Example 2: Phase Completion Check

1. Click **"Assess Maturity"** for current phase
2. Address any blocking issues shown
3. Run **"Run Tests"** to ensure all tests pass
4. Click **"Code Review"** to fix remaining issues
5. Run **"Validate Code"** to confirm no errors
6. Click **"View Report"** to confirm ready for next phase

### Example 3: Continuous Quality Monitoring

1. **Regularly** click **"Run Tests"** after changes
2. **Weekly** run **"Code Review"** to maintain quality
3. **Before release** run full **"View Report"**
4. **Iterate** using **"Fix Issues"** as needed
5. **Track** improvements in each report

---

## Tips & Best Practices

### General Tips

1. **Start with Validation**
   - Always run code validation first to catch obvious issues
   - Fix validation errors before other analyses

2. **Review Test Coverage**
   - Ensure tests are passing before code review
   - Aim for >80% code coverage minimum

3. **Use Reports for Tracking**
   - Generate reports periodically to track trends
   - Compare reports over time to see improvements

4. **Fix Issues Strategically**
   - Address critical and major issues first
   - Minor issues can be batched for efficiency

5. **Assess Before Phase Changes**
   - Always assess maturity before advancing phases
   - Use assessment to plan what's needed for next phase

### Performance Tips

- **Validate** is fast (good for quick checks)
- **Tests** can take time (depends on test suite size)
- **Review** is comprehensive (takes longer for large projects)
- **Fix** is safe (doesn't apply changes, just proposes)
- **Report** is slowest (aggregates all data)

### Workflow Tips

1. **Keep results open** - Results stay on screen until you run another analysis
2. **Compare results** - Run the same analysis twice to see improvements
3. **Use for debugging** - Structure analysis helps understand project organization
4. **Test after changes** - Always run tests after applying fixes
5. **Review regularly** - Run reviews weekly to maintain code quality

---

## Understanding Results

### Code Quality Score

Range: 0-100
- **90+**: Excellent (A grade)
- **80-89**: Good (B grade)
- **70-79**: Fair (C grade)
- **60-69**: Poor (D grade)
- **<60**: Critical (F grade)

### Issue Severity Levels

- **Critical**: Must fix immediately, prevents functionality
- **Major**: Should fix, impacts quality/performance
- **Minor**: Could fix, code smell or style issue
- **Suggestion**: Optional improvements

### Test Coverage

- **>95%**: Excellent
- **80-95%**: Good
- **70-80%**: Acceptable
- **<70%**: Poor

### Complexity Score

Lower is better:
- **<10**: Simple and maintainable
- **10-20**: Moderate complexity
- **20-50**: High complexity
- **>50**: Very high complexity (needs refactoring)

---

## Troubleshooting

### "No Results Available"

**Cause:** Analysis hasn't been run yet
**Solution:** Click an analysis button and wait for completion

### "Error: Failed to [action]"

**Possible causes:**
1. Project ID invalid
2. Project files have syntax errors (try validation first)
3. Tests not configured
4. Network connection issue

**Solutions:**
1. Verify project is selected correctly
2. Check project files for obvious errors
3. Ensure test framework is installed
4. Try again in a few moments

### "Unexpected Result Format"

**Cause:** Analysis returned unexpected data
**Solution:** This may happen if analysis tools aren't installed. Check project setup.

### Tests Show Red (Failed)

**Causes:**
1. Code changes broke tests
2. Tests need new fixtures or setup
3. Tests have timing issues
4. Missing test dependencies

**Solutions:**
1. Review failing tests in detail
2. Check test output for error messages
3. Fix the issues causing test failures
4. Run tests again to verify fixes

---

## API Integration

If you want to use analysis programmatically via API:

```bash
# Validate code
POST /analysis/validate?project_id=PROJECT_ID

# Run tests
POST /analysis/test?project_id=PROJECT_ID

# Analyze structure
POST /analysis/structure?project_id=PROJECT_ID

# Code review
POST /analysis/review?project_id=PROJECT_ID

# Assess maturity
POST /analysis/{project_id}/maturity

# Fix issues
POST /analysis/fix?project_id=PROJECT_ID

# Get report
GET /analysis/report/{project_id}
```

---

## Next Steps

After running analysis:

1. **Review findings** - Read through all identified issues
2. **Prioritize fixes** - Address critical issues first
3. **Plan improvements** - Use recommendations to improve code
4. **Track progress** - Run analyses periodically to measure improvement
5. **Advance phases** - Use maturity assessment to guide phase transitions

---

## FAQ

**Q: Why do I need to select a project?**
A: Different projects have different configurations, tests, and codebases.

**Q: Can I run multiple analyses at once?**
A: Currently one at a time. Previous results stay visible while running new analysis.

**Q: Are fixes automatically applied?**
A: No. Fixes are proposed and reviewed before application.

**Q: How often should I run analyses?**
A: Validation/Tests should be frequent (daily), Reviews weekly, Reports monthly.

**Q: Can I see historical analysis results?**
A: Results display in the UI. Save reports for long-term tracking.

**Q: What if my project has no tests?**
A: You can still use validation, review, and structure analysis. Set up tests for best results.

---

## Related Features

- **Analytics Page** - Track project progress and metrics over time
- **Chat Sessions** - Discuss analysis results with AI guidance
- **Code Generation** - Generate improved code based on review findings
- **Knowledge Management** - Document analysis findings and solutions

---

**Last Updated:** January 2024
