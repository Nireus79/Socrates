# GitHub Actions Workflows

Automated CI/CD workflows for Socrates.

## Workflows Overview

### 1. `docker-publish.yml`

**Purpose:** Build and push Docker images to GitHub Container Registry (GHCR)

**Triggers:**
- Push to `master` branch
- Push of version tags (`v*`)
- Release publication
- Manual trigger (workflow_dispatch)

**Jobs:**
1. **build-api** - Build and push API Docker image
   - Multi-platform builds (linux/amd64, linux/arm64)
   - Generates SBOM (Software Bill of Materials)
   - Optional image signing with Cosign

2. **build-frontend** - Build and push frontend Docker image
   - Same multi-platform support as API
   - SBOM generation
   - Environment variable substitution

3. **scan-images** - Security vulnerability scanning with Trivy
   - Scans both API and frontend images
   - Uploads SARIF results to GitHub Security tab
   - Checks for CRITICAL and HIGH severity vulnerabilities

4. **test-images** - Validates built images
   - Tests API image compilation
   - Tests API health check endpoint
   - Tests frontend serving content
   - Reports image sizes

5. **publish-release** - Creates GitHub release notes
   - Includes SBOM files as artifacts
   - Provides deployment instructions
   - Only runs on version tags

6. **notify-deployment** - Sends notifications
   - Slack notification with image details
   - Discord notification with embed
   - Links to workflow run

7. **summary** - Generates GitHub step summary
   - Status table
   - Build metadata

**Outputs:**
- Docker images pushed to `ghcr.io/<owner>/socrates/<component>:<tag>`
- SBOM files for transparency
- Security scan results in GitHub Security tab
- Release notes for tagged versions

**Environment Variables (Optional):**
```yaml
secrets:
  SLACK_WEBHOOK_URL: "https://hooks.slack.com/..."
  DISCORD_WEBHOOK_URL: "https://discord.com/api/webhooks/..."
```

**Example Usage:**

```bash
# Automatic on push to master
git push origin master

# Automatic on version tag
git tag v1.0.0
git push origin v1.0.0

# Manual trigger
gh workflow run docker-publish.yml \
  -f push_images=true \
  -r master
```

**Image Tags:**
- `latest` - Latest on master branch
- `master` - Current master branch
- `v1.0.0` - Semantic version tag
- `master-abc1234` - Commit SHA on master
- `develop-abc1234` - Commit SHA on other branches

---

### 2. `tests.yml`

**Purpose:** Run test suite on every pull request and push

**Triggers:**
- Pull requests
- Push to any branch
- Schedule (daily at 2 AM UTC)

**Jobs:**
1. **test** - Run pytest test suite
   - Python 3.10, 3.11, 3.12
   - Runs unit, integration, and e2e tests
   - Generates coverage report
   - Uploads coverage to Codecov

2. **lint** - Code quality checks
   - Black code formatting
   - isort import sorting
   - Ruff linting
   - MyPy type checking
   - Bandit security checks

3. **test-summary** - Generate test summary
   - Success/failure counts
   - Coverage percentage
   - Performance metrics

---

### 3. `code-quality.yml`

**Purpose:** Comprehensive code quality and security analysis

**Triggers:**
- Every push
- Pull requests
- Manual trigger

**Jobs:**
1. **static-analysis** - Static code analysis
   - Ruff linting
   - MyPy type checking
   - Complexity analysis

2. **security** - Security scanning
   - Bandit vulnerability scanning
   - Dependency vulnerability checks (pip-audit)
   - SAST scanning

3. **code-coverage** - Coverage enforcement
   - Minimum 90% coverage requirement
   - Per-file coverage reports
   - Trend analysis

---

## Setting Up Workflows

### Prerequisites

1. **GitHub Repository Access**
   - Admin access to enable workflows
   - Permissions for secrets management

2. **Container Registry**
   - GitHub Container Registry (automatic with GHCR)
   - Or configure Docker Hub / other registry

3. **Optional Notifications**
   - Slack workspace with incoming webhook
   - Discord server with webhook URL

### Configuration

#### 1. Enable Workflows

```bash
# Workflows are automatically enabled when .github/workflows/*.yml exists
# No additional setup needed for GitHub Actions
```

#### 2. Configure Secrets (Optional)

```bash
# Add notification secrets for notifications
gh secret set SLACK_WEBHOOK_URL --body "https://hooks.slack.com/..."
gh secret set DISCORD_WEBHOOK_URL --body "https://discord.com/api/webhooks/..."

# View configured secrets
gh secret list
```

#### 3. Configure Branch Protection

Go to **Settings > Branches > Branch Protection Rules** and:
- Select `master` branch
- ✅ Require status checks to pass before merging
- ✅ Require all status checks to pass:
  - `build-api` / `build-frontend`
  - `tests`
  - `lint`
  - `code-quality`
- ✅ Require branches to be up to date before merging
- ✅ Dismiss stale review approvals
- ✅ Require code review from 1+ reviewer
- ✅ Require commit signatures
- ✅ Allow force pushes: No
- ✅ Allow deletions: No

#### 4. Configure Environments (Optional)

For production deployments, set up environments:

```bash
# Create production environment
gh api repos/owner/repo/environments -f name=production

# Add environment secrets
gh secret set DATABASE_URL --body "postgresql://..." --env production
gh secret set ANTHROPIC_API_KEY --body "sk-ant-..." --env production
```

## Monitoring Workflows

### View Workflow Status

```bash
# List all workflows
gh workflow list

# View latest runs
gh run list

# View specific workflow runs
gh run list --workflow docker-publish.yml

# View run details
gh run view <RUN_ID>

# Watch workflow in real-time
gh run watch <RUN_ID>
```

### Troubleshooting

#### Docker build fails

```bash
# Check build logs
gh run view <RUN_ID> --log

# Manually test build locally
docker build -f Dockerfile.api -t socrates-api:test .

# Check for syntax errors
docker buildx bake --print
```

#### Tests fail

```bash
# View test logs
gh run view <RUN_ID> --log

# Run tests locally
pytest --cov=socrates_api --cov-report=html

# Run specific test file
pytest tests/test_auth.py -v
```

#### Scanning fails

```bash
# Run Trivy locally
trivy image ghcr.io/owner/socrates/api:latest

# View scan results in GitHub
# Go to Security > Code scanning alerts
```

### Performance Optimization

**Docker build cache:**
- Caching is automatic via GitHub Actions cache
- Layer caching reduces build time significantly

**Test parallelization:**
- Tests run in parallel with pytest-xdist
- Distributes tests across multiple workers

**Artifact management:**
- SBOMs uploaded as artifacts
- Old artifacts automatically cleaned up (90 days)

## Secrets Management

### What to Add

```bash
# Container registry (optional, default is GitHub)
# gh secret set DOCKER_USERNAME
# gh secret set DOCKER_PASSWORD

# Notifications
gh secret set SLACK_WEBHOOK_URL
gh secret set DISCORD_WEBHOOK_URL

# Code quality tools
# gh secret set CODECOV_TOKEN
# gh secret set SONARCLOUD_TOKEN
```

### Security Best Practices

1. **Never commit secrets** to repository
2. **Use GitHub Secrets** for sensitive data
3. **Rotate secrets regularly** (especially API keys)
4. **Use environment-specific secrets** for production
5. **Audit secret access** in GitHub audit log
6. **Limit scope** - only give secrets needed permissions

## Custom Workflows

### Creating New Workflows

1. Create `.github/workflows/<name>.yml`
2. Define triggers and jobs
3. Test locally with `act` CLI

```bash
# Install act
brew install act

# Test workflow
act -j <job-name>
```

### Example: Custom Deployment

```yaml
name: Deploy to Production

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    environment: production
    steps:
      - uses: actions/checkout@v4
      - name: Deploy
        run: |
          kubectl set image deployment/socrates-api \
            socrates-api=ghcr.io/${{ github.repository }}/api:${{ github.ref_name }} \
            -n socrates-prod
```

## Monitoring and Alerts

### GitHub Status Checks

- All workflows must pass before merging to `master`
- Automatic checks on every pull request
- Blocking status if checks fail

### Email Notifications

- GitHub sends email on workflow failures
- Can be customized in **Settings > Notifications**

### Custom Notifications

Workflows include integrations for:
- **Slack** - Rich notifications with thread context
- **Discord** - Embeds with detailed information
- **Email** - Via GitHub notifications

## Troubleshooting Common Issues

### Workflow not running

**Issue:** Workflow not triggering on push

**Solution:**
1. Check `.github/workflows/` directory exists
2. Verify YAML syntax is correct
3. Check workflow file permissions
4. Ensure you're on the trigger branch

### Out of memory during builds

**Issue:** Docker build fails with OOM error

**Solution:**
1. Use lighter base images
2. Remove unnecessary layers
3. Reduce build parallelism
4. Use BuildKit for better caching

### Tests timeout

**Issue:** Tests hang or take too long

**Solution:**
1. Mark slow tests with `@pytest.mark.slow`
2. Skip integration tests in CI
3. Use test parallelization
4. Increase timeout in workflow

## Performance Metrics

### Typical Workflow Times

- **docker-publish.yml**: 8-12 minutes (includes scanning, testing)
- **tests.yml**: 5-8 minutes (pytest across Python versions)
- **code-quality.yml**: 3-5 minutes (linting, type checking)

### Optimization Tips

1. Use workflow cache for dependencies
2. Parallelize jobs where possible
3. Use Ubuntu latest runner (faster)
4. Skip unnecessary jobs for non-code changes

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [GitHub Actions Syntax](https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions)
- [Marketplace Actions](https://github.com/marketplace?type=actions)
- [Workflow Examples](https://github.com/actions/starter-workflows)

## Support

For workflow issues:
1. Check GitHub Actions logs
2. Test commands locally
3. Open GitHub issue in repository
4. Contact GitHub Support (for enterprise)
