# CI/CD Pipeline Documentation

Socrates uses GitHub Actions for continuous integration, continuous deployment, and automated testing.

## Overview

The CI/CD pipeline consists of four main workflows:

1. **Tests** (`test.yml`) - Automated testing on every push and PR
2. **Code Quality** (`lint.yml`) - Linting, formatting, and type checking
3. **Publishing** (`publish.yml`) - Publishing to PyPI on releases
4. **Release Management** (`release.yml`) - Version bumping and release creation

## Workflows

### 1. Test Workflow (test.yml)

**Triggers:**
- Push to `main`, `master`, or `develop` branches
- Pull requests to those branches
- Daily schedule (2 AM UTC)

**Jobs:**
- `test` - Runs pytest across Python 3.8-3.12 on Ubuntu, Windows, and macOS
- `test-cli` - Tests CLI commands and installation
- `test-api` - Tests REST API endpoints
- `coverage-badge` - Updates coverage badge on main branch

**What it does:**
1. Sets up Python environment
2. Installs dependencies
3. Runs linting (ruff, black)
4. Runs type checking (mypy)
5. Runs all pytest tests
6. Generates coverage reports
7. Uploads to Codecov

**Matrix Optimization:**
- Tests on Python 3.8-3.12
- Tests on Ubuntu, Windows, and macOS
- Reduces full matrix on Windows and macOS for speed

**Artifacts:**
- Test results
- HTML coverage reports
- Coverage XML files

### 2. Code Quality Workflow (lint.yml)

**Triggers:**
- Push to main branches
- Pull requests

**Jobs:**
- `ruff` - Python linter for code quality issues
- `black` - Code formatter check
- `mypy` - Static type checker
- `security` - Security audit with bandit and safety
- `dependencies` - Checks for outdated packages
- `docs` - Docstring validation with pydocstyle
- `code-coverage` - Enforces minimum coverage threshold (70%)

**What it does:**
1. Checks code style with ruff
2. Verifies formatting with black
3. Validates type hints with mypy
4. Audits security with bandit
5. Checks dependencies for vulnerabilities
6. Validates documentation
7. Enforces coverage threshold

**Output:**
- GitHub annotations for issues found
- Pass/fail status for PR checks

### 3. Publishing Workflow (publish.yml)

**Triggers:**
- When a release is created
- Manual workflow dispatch (with dry-run option)

**Jobs:**
- `test` - Runs tests before publishing
- `build` - Builds distributions for all three packages
- `publish` - Publishes to PyPI
- `publish-test` - Dry-run publish to TestPyPI
- `release-notes` - Updates GitHub release with notes

**What it does:**
1. Runs all tests to ensure quality
2. Builds wheel and sdist distributions
3. Validates distributions with twine
4. Publishes to PyPI using tokens
5. Creates detailed release notes
6. Notifies of successful publishing

**Secrets Required:**
- `PYPI_API_TOKEN` - PyPI token for publishing (socrates-ai)
- `TEST_PYPI_API_TOKEN` - TestPyPI token for dry runs (optional)

**Packages Published:**
- `socrates-ai` - Core library
- `socrates-cli` - CLI tool
- `socrates-api` - REST API server

### 4. Release Management Workflow (release.yml)

**Triggers:**
- Manual workflow dispatch with version type

**Inputs:**
- `version-type` - major, minor, or patch
- `release-notes` - Optional custom release notes

**Jobs:**
- `create-release` - Bumps version and creates git tag
- `verify-release` - Verifies release integrity
- `notify-release` - Sends notification

**What it does:**
1. Reads current version from pyproject.toml
2. Bumps version based on semver
3. Updates all pyproject.toml files
4. Updates __init__.py version strings
5. Creates git commit with version bump
6. Creates and pushes git tag
7. Creates GitHub release
8. Triggers publish.yml workflow

**Version Bumping:**
- Major: 8.0.0 → 9.0.0
- Minor: 8.0.0 → 8.1.0
- Patch: 8.0.0 → 8.0.1

## Using the CI/CD Pipeline

### Running Tests Locally

Before pushing, run tests locally:

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_config.py -v

# Run with coverage
pytest --cov=socratic_system --cov-report=html

# Run linting
ruff check socratic_system
black --check socratic_system
mypy socratic_system
```

### Creating a Release

1. Go to GitHub Actions
2. Select "Release Management" workflow
3. Click "Run workflow"
4. Select version type (major, minor, patch)
5. Add optional release notes
6. Click "Run workflow"

This will:
- Bump version in all files
- Create git tag
- Create GitHub release
- Trigger automated publishing to PyPI

### Handling CI Failures

#### Test Failures

If tests fail:
1. Check the GitHub Actions log for details
2. Reproduce locally: `pytest tests/test_name.py -v`
3. Fix the issue
4. Push fix to PR

#### Coverage Failures

If coverage drops below 70%:
1. Check which files lost coverage
2. Add tests for uncovered code
3. Run `pytest --cov` locally to verify

#### Linting Failures

If linting fails:
1. View the annotations in the PR
2. Fix issues with: `black socratic_system` and `ruff check --fix socratic_system`
3. Commit and push fixes

### Setting Up Secrets

To enable PyPI publishing, add secrets to GitHub repository:

1. Go to Settings → Secrets and variables → Actions
2. Click "New repository secret"
3. Add `PYPI_API_TOKEN`:
   - Generate token from https://pypi.org/account/
   - Set token value
4. (Optional) Add `TEST_PYPI_API_TOKEN` for dry-run testing

## Workflow Status

View workflow status at:
- https://github.com/Nireus79/Socrates/actions

## Performance

### Test Optimization

- **Matrix parallelization**: Tests run in parallel across Python versions and OSes
- **Caching**: pip cache is used to speed up dependency installation
- **Selective testing**: Different test suites run on different OS to balance load

### Typical Build Time

- **Test workflow**: 10-15 minutes (parallel across platforms)
- **Lint workflow**: 3-5 minutes
- **Publish workflow**: 10-20 minutes (includes building and publishing)
- **Release workflow**: 5-10 minutes

## Troubleshooting

### Workflow Not Running

**Issue**: Workflow doesn't run on push

**Solution:**
1. Check that branch is configured in workflow trigger
2. Verify .github/workflows/ files are in repository
3. Check branch protection rules aren't blocking

### Publishing Fails

**Issue**: Publishing to PyPI fails

**Solution:**
1. Verify `PYPI_API_TOKEN` is set and valid
2. Check package version is unique (not already published)
3. Ensure distributions build successfully locally
4. Check PyPI project settings and access

### Coverage Drops

**Issue**: Coverage check fails

**Solution:**
1. Add tests for new code: `pytest tests/test_name.py::test_func -v`
2. Run coverage locally: `pytest --cov --cov-fail-under=70`
3. Update coverage threshold if needed

## Best Practices

1. **Run tests locally before pushing**
   ```bash
   pytest && black . && ruff check .
   ```

2. **Keep branches up to date**
   - Rebase on main before creating PR
   - Fix any conflicts

3. **Write tests for new features**
   - Unit tests for logic
   - Integration tests for components
   - Target 70%+ coverage

4. **Follow code style**
   - Use black for formatting
   - Use ruff for linting
   - Run mypy for type checking

5. **Document changes**
   - Update CHANGELOG.md
   - Add docstrings
   - Update README if needed

## Environment Variables

### In Workflows

Workflows can use environment variables:

```yaml
env:
  PYTHONPATH: ${GITHUB_WORKSPACE}
  PYTEST_ARGS: "--cov --cov-fail-under=70"
```

### In Repository

Set repository-level environment variables in Settings → Variables

## Monitoring

### Codecov Integration

Coverage reports are automatically uploaded to Codecov:
- https://codecov.io/gh/Nireus79/Socrates

View coverage trends, file-by-file breakdown, and more.

### GitHub Status Checks

PR status checks show:
- ✅ All tests passed
- ✅ Code quality checks passed
- ✅ Coverage threshold met
- ✅ Type checking passed

## Customization

To modify CI/CD:

1. Edit workflow files in `.github/workflows/`
2. Commit changes
3. Workflows apply automatically

Common customizations:
- Add new jobs
- Change Python versions
- Add new linting tools
- Modify test command
- Add new secrets

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Workflow Syntax Reference](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [pytest Documentation](https://docs.pytest.org/)
- [ruff Documentation](https://docs.astral.sh/ruff/)
- [black Documentation](https://black.readthedocs.io/)
