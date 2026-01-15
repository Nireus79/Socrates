# Real-World GitHub Integration Testing Guide

## Pre-Testing Setup

### 1. Create GitHub Test Account (or use existing)
```bash
# Option A: Use existing GitHub account
# Option B: Create new test account at https://github.com/join
#   - Email: your-email+socrates-test@domain.com
#   - Username: socrates-test-[randomnumber]
#   - Keep credentials secure
```

### 2. Generate Personal Access Token (PAT)
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Click "Generate new token" → "Generate new token (classic)"
3. Set token name: `socrates-test-token`
4. Set expiration: 90 days (for testing)
5. Select scopes:
   - ✅ `repo` (full control of repositories)
   - ✅ `public_repo` (access public repos)
   - ✅ `user:email` (read user email)
6. Click "Generate token"
7. **Copy token immediately** - it won't be shown again
8. Store in safe location: `GITHUB_TEST_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxx`

### 3. Test Token Validity
```bash
# Test the token works
curl -H "Authorization: token YOUR_TOKEN" \
     https://api.github.com/user

# Expected response: Your GitHub user information
```

## Export Functionality Testing

### Test 1: Export Project as ZIP
```bash
# 1. Create a test project in Socrates
curl -X POST http://localhost:8000/api/projects \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test-project-export",
    "description": "Testing export functionality",
    "type": "software",
    "requirements": ["REST API", "Database integration"]
  }'

# 2. Finalize the project
curl -X POST http://localhost:8000/api/projects/{project_id}/finalize \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 3. Export as ZIP
curl -X GET "http://localhost:8000/api/projects/{project_id}/export?format=zip" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -o test-project.zip

# 4. Verify ZIP contents
unzip -l test-project.zip
# Should contain: main.py, README.md, requirements.txt, .gitignore,
#                 pyproject.toml, setup.py, Dockerfile, etc.

# 5. Extract and verify structure
unzip test-project.zip -d test-project
ls -la test-project/
python test-project/main.py --help  # Should work without errors
```

### Test 2: Export as TAR.GZ
```bash
# 1. Export as TAR.GZ
curl -X GET "http://localhost:8000/api/projects/{project_id}/export?format=tar.gz" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -o test-project.tar.gz

# 2. Verify TAR contents
tar -tzf test-project.tar.gz | head -20

# 3. Extract and verify
tar -xzf test-project.tar.gz
ls -la test-project/
```

### Test 3: Different Export Formats
```bash
# Test all supported formats
for format in zip tar tar.gz tar.bz2; do
  echo "Testing export format: $format"
  curl -X GET "http://localhost:8000/api/projects/{project_id}/export?format=$format" \
    -H "Authorization: Bearer YOUR_JWT_TOKEN" \
    -o "test-project.$format"

  if [ -f "test-project.$format" ]; then
    echo "✓ Export successful for format: $format"
    ls -lh "test-project.$format"
  else
    echo "✗ Export failed for format: $format"
  fi
done
```

## GitHub Publishing Testing

### Test 1: Basic Repository Creation
```bash
# 1. Publish project to GitHub
curl -X POST http://localhost:8000/api/projects/{project_id}/publish-to-github \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_name": "socrates-test-repo-1",
    "description": "Test repository created by Socrates",
    "private": true
  }'

# Expected response:
# {
#   "success": true,
#   "data": {
#     "repo_url": "https://github.com/socrates-test-user/socrates-test-repo-1",
#     "clone_url": "https://github.com/socrates-test-user/socrates-test-repo-1.git"
#   }
# }

# 2. Verify repository was created
# Go to https://github.com/YOUR_USERNAME/socrates-test-repo-1
# Verify:
#   - Repository exists
#   - Is marked as private/public correctly
#   - Description matches
#   - All files are present
#   - README.md is rendered correctly
#   - .gitignore is present
#   - GitHub Actions workflows are present
```

### Test 2: Repository with Specific Visibility
```bash
# Test Public Repository
curl -X POST http://localhost:8000/api/projects/{project_id}/publish-to-github \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_name": "socrates-test-public",
    "description": "Public test repository",
    "private": false
  }'

# Test Private Repository
curl -X POST http://localhost:8000/api/projects/{project_id}/publish-to-github \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_name": "socrates-test-private",
    "description": "Private test repository",
    "private": true
  }'

# Verify both repositories were created with correct visibility
```

### Test 3: Clone and Verify Generated Repository
```bash
# 1. Clone the repository created by Socrates
git clone https://github.com/YOUR_USERNAME/socrates-test-repo-1.git
cd socrates-test-repo-1

# 2. Verify project structure
ls -la
cat README.md
cat pyproject.toml
cat requirements.txt

# 3. Verify it's a valid Python project
python -m pip install -e .
python main.py --help

# 4. Verify tests can run
pytest tests/ -v

# 5. Verify GitHub Actions workflows are present
ls -la .github/workflows/
cat .github/workflows/ci.yml

# 6. Check git history
git log --oneline | head -10
# Should show initial commit from Socrates
```

### Test 4: Error Handling - Duplicate Repository
```bash
# 1. Try to create repository with same name
curl -X POST http://localhost:8000/api/projects/{project_id}/publish-to-github \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_name": "socrates-test-repo-1",
    "description": "Attempting duplicate"
  }'

# Expected error response:
# {
#   "success": false,
#   "error": "Repository already exists",
#   "status_code": 409
# }
```

### Test 5: Error Handling - Invalid Token
```bash
# Try with invalid token
curl -X POST http://localhost:8000/api/projects/{project_id}/publish-to-github \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_name": "socrates-test-invalid",
    "description": "Testing invalid token"
  }' \
  -d '{"github_token": "ghp_invalid_token_12345"}'

# Expected error response:
# {
#   "success": false,
#   "error": "GitHub authentication failed",
#   "status_code": 401
# }
```

### Test 6: GitHub Actions Workflow Execution
```bash
# 1. Navigate to repository on GitHub
# Go to: https://github.com/YOUR_USERNAME/socrates-test-repo-1/actions

# 2. Verify workflows are present:
#   - CI/CD workflow (ci.yml) - runs on push/PR
#   - Lint workflow (lint.yml) - code quality checks
#   - Publish workflow (publish.yml) - PyPI publishing (if configured)

# 3. Wait for workflows to complete
#   - Look for green checkmarks ✓
#   - Click on workflow to see details
#   - Verify all jobs passed

# 4. Check test results
#   - Click on "Run Tests" job
#   - Verify all tests passed
#   - Check coverage percentage

# 5. Verify code quality checks
#   - Click on "Lint" job
#   - Verify linting passed
#   - Check for any warnings
```

## Integration Testing

### Test 7: End-to-End Workflow
```bash
# 1. Create project
PROJECT_RESPONSE=$(curl -X POST http://localhost:8000/api/projects \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "e2e-test-project",
    "description": "End-to-end integration test",
    "type": "api",
    "requirements": ["Authentication", "Rate limiting", "Logging"]
  }')

PROJECT_ID=$(echo $PROJECT_RESPONSE | jq -r '.data.id')
echo "Created project: $PROJECT_ID"

# 2. Finalize project
curl -X POST http://localhost:8000/api/projects/$PROJECT_ID/finalize \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"

# 3. Export project
curl -X GET "http://localhost:8000/api/projects/$PROJECT_ID/export?format=zip" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -o e2e-project.zip

# 4. Publish to GitHub
GITHUB_RESPONSE=$(curl -X POST http://localhost:8000/api/projects/$PROJECT_ID/publish-to-github \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "repo_name": "e2e-test-socrates",
    "description": "E2E test from Socrates"
  }')

REPO_URL=$(echo $GITHUB_RESPONSE | jq -r '.data.repo_url')
echo "Published to GitHub: $REPO_URL"

# 5. Verify everything works
unzip e2e-project.zip
cd e2e-project
git status  # Should show git initialized
python main.py --help  # Should work
```

## Concurrent Operations Testing

### Test 8: Multiple Exports Simultaneously
```bash
# Start 5 export operations concurrently
for i in {1..5}; do
  echo "Starting export $i..."
  curl -X GET "http://localhost:8000/api/projects/{project_id}/export?format=zip" \
    -H "Authorization: Bearer YOUR_JWT_TOKEN" \
    -o "project-export-$i.zip" &
done

# Wait for all to complete
wait

# Verify all exports completed successfully
for i in {1..5}; do
  if [ -f "project-export-$i.zip" ]; then
    echo "✓ Export $i successful"
  else
    echo "✗ Export $i failed"
  fi
done
```

### Test 9: Multiple GitHub Publications
```bash
# Start 3 publish operations (different projects)
for i in {1..3}; do
  echo "Publishing project $i..."
  curl -X POST http://localhost:8000/api/projects/project_id_$i/publish-to-github \
    -H "Authorization: Bearer YOUR_JWT_TOKEN" \
    -H "Content-Type: application/json" \
    -d '{
      "repo_name": "concurrent-test-'$i'",
      "description": "Concurrent publish test '$i'"
    }' &
done

# Wait for all to complete
wait

echo "✓ All concurrent operations completed"
```

## Performance Testing

### Test 10: Large Project Export
```bash
# Create project with large codebase
curl -X POST http://localhost:8000/api/projects \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "large-test-project",
    "description": "Large project for performance testing",
    "requirements": ["Module1", "Module2", "Module3", "Module4", "Module5"],
    "file_count": 100
  }'

# Time the export operation
time curl -X GET "http://localhost:8000/api/projects/{project_id}/export?format=zip" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -o large-project.zip

# Should complete in < 5 seconds
# Check file size is reasonable
ls -lh large-project.zip

# Expected: < 10MB for typical project
```

## Cleanup

### After All Tests Complete
```bash
# 1. List created repositories
curl -H "Authorization: token YOUR_TOKEN" \
     https://api.github.com/user/repos?per_page=100 \
     | jq '.[] | select(.name | contains("test")) | .full_name'

# 2. Delete test repositories (optional)
# Go to each repository Settings → Delete repository

# 3. Revoke test token
# Go to GitHub Settings → Developer settings → Personal access tokens
# Find `socrates-test-token` and click Delete

# 4. Remove test account (if created for testing)
# Go to GitHub Settings → Account → Delete account

# 5. Clean up local test files
rm -rf test-project*
rm -rf e2e-project*
```

## Expected Results Checklist

- [ ] ZIP export creates valid archive
- [ ] TAR.GZ export creates valid archive
- [ ] All archive formats supported
- [ ] GitHub repository created successfully
- [ ] Files pushed to GitHub correctly
- [ ] README rendered on GitHub
- [ ] .gitignore applied correctly
- [ ] GitHub Actions workflows trigger
- [ ] Tests run successfully on GitHub Actions
- [ ] Concurrent operations don't cause conflicts
- [ ] Large projects export without issues
- [ ] Error messages are clear and helpful
- [ ] Token validation works correctly
- [ ] Repository visibility settings respected
- [ ] Clone URL provided correctly

## Troubleshooting

### Repository Creation Fails
```bash
# Check GitHub API rate limit
curl -H "Authorization: token YOUR_TOKEN" \
     https://api.github.com/rate_limit

# Check token scopes
curl -H "Authorization: token YOUR_TOKEN" \
     https://api.github.com/user/scopes

# Should include: repo, public_repo, user:email
```

### Workflows Not Running
```bash
# Check workflow file syntax
cat .github/workflows/ci.yml | yq .

# Verify workflow is enabled on GitHub
# Repository → Actions → Check all workflows enabled

# Check recent push triggered workflow
# Repository → Actions → Look for recent workflow runs
```

### Export Takes Too Long
```bash
# Check server logs
tail -f /app/logs/api.log

# Check disk I/O
iostat -x 1 10

# Check memory usage
free -h

# Check CPU usage
top -b -n 1 | grep socrates
```

## Success Criteria

✅ All export formats working
✅ GitHub publishing working
✅ Repositories created successfully
✅ Files pushed correctly
✅ GitHub Actions workflows running
✅ Tests passing on GitHub Actions
✅ No rate limit issues
✅ Performance acceptable (< 5s for typical projects)
✅ Error handling working correctly
✅ Concurrent operations handled properly

---

**Test Date:** [Date]
**Tested By:** [Name]
**GitHub Token Used:** [Token ID/Date]
**Test Status:** ✅ PASS / ❌ FAIL
