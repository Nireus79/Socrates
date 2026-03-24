# Phase 9 Deployment Verification Guide

Post-deployment verification procedures for Phase 9 features and functionality.

---

## Quick Verification (5 minutes)

Quick sanity check to verify deployment was successful.

### 1. System Health

```bash
# Check application is running
curl http://localhost:8000/health

# Expected response:
# {"status": "healthy", "version": "2025.3.24-phase9"}
```

### 2. Database Connectivity

```bash
# Verify database is accessible
sqlite3 data/socrates.db ".tables"

# Should show tables including:
# conflicts, workflows, security_incidents, performance_metrics, etc.
```

### 3. Command Availability

```bash
# Verify commands are available
socrates help | grep -E "conflict|workflow|security|performance|learning|analyze|docs"

# Should list all 28 new commands
```

### 4. Basic Command Test

```bash
# Test each module with a simple command
socrates conflict list
socrates workflow list
socrates security status
socrates performance status
socrates learning recommendations test
socrates analyze project ./src
socrates docs generate all test ./src
```

**Expected Result:** All commands return without errors

---

## Comprehensive Verification (30 minutes)

Detailed verification of all Phase 9 features.

### Section 1: Conflict Detection

```bash
# 1. Analyze conflicts
socrates conflict analyze
# Expected: Returns list of conflicts or "No conflicts detected"

# 2. List conflicts
socrates conflict list
# Expected: Shows existing conflicts with status

# 3. Verify database storage
sqlite3 data/socrates.db "SELECT COUNT(*) FROM conflicts;"
# Expected: Returns a number (0 or more)
```

**Verification Checklist:**
- [ ] `conflict analyze` completes without error
- [ ] `conflict list` shows conflicts or empty list
- [ ] Database table exists and is accessible
- [ ] Conflict status tracking works

### Section 2: Workflow Orchestration

```bash
# 1. List workflows
socrates workflow list
# Expected: Shows available workflows or empty list

# 2. Verify database
sqlite3 data/socrates.db "SELECT COUNT(*) FROM workflows;"
# Expected: Returns a number (0 or more)

# 3. Check workflow execution tracking
sqlite3 data/socrates.db "SELECT COUNT(*) FROM workflow_executions;"
# Expected: Returns a number (0 or more)
```

**Verification Checklist:**
- [ ] `workflow list` completes without error
- [ ] Workflow tables exist in database
- [ ] Workflow execution tracking functional

### Section 3: Security Monitoring

```bash
# 1. Check security status
socrates security status
# Expected: Shows security status (Secure/Alert)

# 2. List security incidents
socrates security incidents
# Expected: Shows incidents or "No incidents found"

# 3. Verify incident logging
sqlite3 data/socrates.db "SELECT COUNT(*) FROM security_incidents;"
# Expected: Returns a number (0 or more)

# 4. Test security validation
echo "SELECT * FROM users;" | socrates security validate
# Expected: Shows security analysis with threats detected
```

**Verification Checklist:**
- [ ] `security status` shows correct status
- [ ] `security incidents` accessible
- [ ] Incident database logging works
- [ ] Validation detects SQL injection threat
- [ ] Security score calculated correctly

### Section 4: Performance Monitoring

```bash
# 1. Check performance status
socrates performance status
# Expected: Shows execution and cache metrics

# 2. List agent performance
socrates performance agents
# Expected: Shows agent metrics or empty list

# 3. Check cache statistics
socrates performance cache
# Expected: Shows cache hit rate and size

# 4. Find bottlenecks
socrates performance bottlenecks 1000
# Expected: Shows slow operations or "No bottlenecks found"

# 5. Verify metrics storage
sqlite3 data/socrates.db "SELECT COUNT(*) FROM performance_metrics;"
# Expected: Returns a number (0 or more)
```

**Verification Checklist:**
- [ ] `performance status` shows metrics
- [ ] `performance agents` accessible
- [ ] `performance cache` shows hit rate
- [ ] `performance bottlenecks` functional
- [ ] Metrics table exists and populated

### Section 5: Learning & Recommendations

```bash
# 1. List learning sessions
socrates learning session test_user
# Expected: Creates and returns session ID

# 2. Get recommendations (may need test data)
socrates learning recommendations test_agent
# Expected: Shows recommendations or "No recommendations"

# 3. Analyze patterns
socrates learning patterns test_agent
# Expected: Shows patterns or "No patterns detected"

# 4. Verify session storage
sqlite3 data/socrates.db "SELECT COUNT(*) FROM learning_sessions;"
# Expected: Returns 1 (from session created above)
```

**Verification Checklist:**
- [ ] `learning session` creates new session
- [ ] Session ID returned correctly
- [ ] Learning sessions table populated
- [ ] Pattern analysis functional

### Section 6: Code Analysis

```bash
# 1. Test code analysis
echo "def hello(): pass" | socrates analyze code
# Expected: Returns quality score and analysis

# 2. Analyze a file
socrates analyze file src/cli.py
# Expected: Shows file analysis with quality score

# 3. Project analysis (if src exists)
socrates analyze project ./src
# Expected: Shows project summary with quality metrics

# 4. Issue detection
socrates analysis issues complexity ./src
# Expected: Shows complexity issues or "No issues found"

# 5. Verify results storage
sqlite3 data/socrates.db "SELECT COUNT(*) FROM analysis_results;"
# Expected: Returns a number (0 or more)
```

**Verification Checklist:**
- [ ] Code analysis produces quality scores
- [ ] File analysis shows detailed results
- [ ] Project analysis completes successfully
- [ ] Issue detection works
- [ ] Results stored in database

### Section 7: Documentation Generation

```bash
# 1. Generate README
socrates docs generate readme TestProject
# Expected: Generates or shows README content

# 2. Generate API docs
socrates docs generate api src/main.py 2>/dev/null || true
# Expected: Generates or shows API documentation

# 3. Generate architecture docs
socrates docs generate architecture core ui database 2>/dev/null || true
# Expected: Generates architecture documentation

# 4. Generate complete suite
socrates docs generate all TestProject ./src 2>/dev/null || true
# Expected: Generates all documentation types
```

**Verification Checklist:**
- [ ] `docs generate readme` functional
- [ ] `docs generate api` accessible
- [ ] `docs generate architecture` works
- [ ] `docs generate all` completes

---

## Performance Verification (10 minutes)

Verify performance improvements are working.

### 1. Response Time Baseline

```bash
# Measure command response time
time socrates performance status
# Expected: <100ms

time socrates conflict list
# Expected: <100ms

time socrates analyze project ./src
# Expected: <5 seconds
```

### 2. Caching Verification

```bash
# Run command twice - second should be faster (cached)
socrates status
time socrates status      # First run
time socrates status      # Second run (should be cached)

# Second run should be noticeably faster if caching works
```

### 3. Memory Usage

```bash
# Monitor memory during operations
watch -n 1 'ps aux | grep socrates | grep -v grep'

# Expected: Stable memory usage <500MB
```

### 4. Cache Hit Rates

```bash
socrates performance cache
# Expected: Hit rate >85% after some usage

socrates performance reset all
# Reset for fresh measurement

# Run operations
socrates status
socrates conflict list
socrates security status

# Check again
socrates performance cache
# Expected: Improving hit rate
```

**Verification Checklist:**
- [ ] Response times <100ms for simple commands
- [ ] Memory usage stable <500MB
- [ ] Cache hit rate >85%
- [ ] Second run faster than first (caching)

---

## Security Verification (10 minutes)

Verify security features are working correctly.

### 1. Security Status

```bash
socrates security status
# Expected: Overall status shown with incident counts
```

### 2. Threat Detection

```bash
# Test SQL injection detection
echo "SELECT * FROM users WHERE id=1' OR '1'='1';" | socrates security validate
# Expected: Detects SQL injection threat

# Test XSS detection
echo "<script>alert('xss')</script>" | socrates security validate
# Expected: Detects XSS threat

# Test safe code
echo "x = 1 + 2" | socrates security validate
# Expected: Shows high security score
```

### 3. Incident Logging

```bash
# Run validation that triggers incident logging
echo "DROP TABLE users;" | socrates security validate

# Check incidents were logged
socrates security incidents
# Expected: Shows new incident

sqlite3 data/socrates.db "SELECT COUNT(*) FROM security_incidents WHERE incident_type='validation_failed';"
# Expected: Count >0
```

### 4. Input Validation

```bash
# Test invalid input handling
socrates conflict resolve ""
# Expected: Error handling for empty input

socrates performance bottlenecks "not_a_number"
# Expected: Error handling for invalid threshold
```

**Verification Checklist:**
- [ ] `security status` shows correct metrics
- [ ] SQL injection detected
- [ ] XSS threats detected
- [ ] Safe code marked as safe
- [ ] Incidents logged to database
- [ ] Invalid input handled gracefully

---

## Database Verification (5 minutes)

Verify database integrity and structure.

### 1. Table Existence

```bash
# Check all tables exist
sqlite3 data/socrates.db ".tables"

# Expected tables:
# - conflicts
# - workflows, workflow_executions
# - security_incidents
# - performance_metrics
# - analysis_results
# - learning_sessions
```

### 2. Index Verification

```bash
# Check indexes for performance
sqlite3 data/socrates.db ".indices"

# Expected indexes:
# - idx_conflicts_status
# - idx_workflows_name
# - idx_security_incidents_type
# - idx_performance_metrics_type
# - idx_analysis_results_file
# - idx_learning_sessions_user
```

### 3. Data Integrity

```bash
# Check for foreign key integrity
sqlite3 data/socrates.db "PRAGMA integrity_check;"
# Expected: "ok"

# Check row counts
sqlite3 data/socrates.db "SELECT name, COUNT(*) FROM (SELECT 'conflicts' as name FROM conflicts UNION ALL SELECT 'workflows' FROM workflows UNION ALL SELECT 'security_incidents' FROM security_incidents) GROUP BY name;"
```

### 4. Backup Verification

```bash
# Verify backup exists
ls -lh data/socrates.db.backup*
# Expected: Backup file exists with recent timestamp

# Test restore capability
cp data/socrates.db data/socrates.db.test
sqlite3 data/socrates.db.test ".tables"
# Expected: All tables accessible
```

**Verification Checklist:**
- [ ] All expected tables exist
- [ ] Indexes created for performance
- [ ] Database integrity check passes
- [ ] Backup file accessible and valid

---

## Documentation Verification (5 minutes)

Verify documentation is accessible and accurate.

### 1. CLI Reference

```bash
# Check CLI reference documentation
ls -l docs/commands/CLI_COMMANDS_REFERENCE.md
# Expected: File exists

# Verify command count in documentation
grep -c "^### " docs/commands/CLI_COMMANDS_REFERENCE.md
# Expected: 28 or more command references
```

### 2. User Guide

```bash
# Check Phase 9 guide exists
ls -l docs/guides/PHASE_9_NEW_FEATURES_GUIDE.md
# Expected: File exists and is substantial (>2000 lines)

# Verify all modules documented
grep -c "^## Module" docs/guides/PHASE_9_NEW_FEATURES_GUIDE.md
# Expected: 7 modules
```

### 3. Help System

```bash
# Test help command
socrates help | grep -E "conflict|workflow|security"
# Expected: New commands listed

socrates conflict --help
# Expected: Help text displayed
```

### 4. CHANGELOG

```bash
# Verify CHANGELOG updated
grep -A 5 "Phase 9" CHANGELOG.md | head -20
# Expected: Phase 9 section with all features listed
```

**Verification Checklist:**
- [ ] CLI reference documentation accessible
- [ ] User guide complete (>2000 lines)
- [ ] All 7 modules documented
- [ ] Help system working
- [ ] CHANGELOG updated

---

## User Acceptance Testing

### Workflow 1: Security Check New Code

```bash
# 1. Create test file with potential security issue
echo "query = f'SELECT * FROM users WHERE id={user_input}'" > test.py

# 2. Validate security
socrates security validate < test.py
# Expected: Detects SQL injection risk

# 3. Review incident
socrates security incidents
# Expected: Shows new validation incident

# Cleanup
rm test.py
```

### Workflow 2: Analyze Project Code Quality

```bash
# 1. Check project status
socrates analyze project ./src
# Expected: Shows overall quality score

# 2. Find complex functions
socrates analysis issues complexity ./src
# Expected: Lists complex functions if any

# 3. Get recommendations
socrates learning analyze test_agent
# Expected: Provides improvement suggestions
```

### Workflow 3: Set Up Monitoring Workflow

```bash
# 1. Create validation workflow
socrates workflow create validation_pipeline
# Follow prompts to add steps

# 2. List workflows
socrates workflow list
# Expected: Shows new workflow

# 3. Execute workflow
socrates workflow execute wf_validation_pipeline
# Expected: Runs and shows results
```

---

## Performance Baseline Report

After deployment, establish performance baseline:

```bash
#!/bin/bash
echo "=== Phase 9 Performance Baseline ==="
echo "Timestamp: $(date)"
echo ""
echo "System Status:"
socrates status
echo ""
echo "Performance Metrics:"
socrates performance status
echo ""
echo "Security Status:"
socrates security status
echo ""
echo "Command Response Times:"
for cmd in "conflict list" "workflow list" "security status" "performance status"
do
    echo -n "$cmd: "
    time socrates $cmd > /dev/null 2>&1
done
echo ""
echo "=== End Baseline Report ==="
```

Save this output for comparison with future metrics.

---

## Rollback Procedures

If verification fails at any point:

### Minor Issues (Recoverable)

1. Review error messages
2. Check logs: `/var/log/socrates/application.log`
3. Verify database integrity: `PRAGMA integrity_check;`
4. Retry specific command with verbose output
5. Check documentation for usage

### Critical Issues (Rollback Required)

```bash
# 1. Stop application
systemctl stop socrates

# 2. Restore database backup
cp data/socrates.db.backup.v9 data/socrates.db

# 3. Revert code to previous version
git revert v2025.3.24-phase9
git push origin master

# 4. Reinstall dependencies
pip install -r requirements.txt --upgrade

# 5. Restart application
systemctl start socrates

# 6. Verify rollback successful
socrates help | grep -c "conflict"  # Should show old count
```

---

## Sign-Off Form

| Check Item | Status | Verified By | Timestamp |
|-----------|--------|-------------|-----------|
| Commands Available | ☐ | | |
| Database Operational | ☐ | | |
| Performance Baseline | ☐ | | |
| Security Tests Passed | ☐ | | |
| Documentation Accessible | ☐ | | |
| No Critical Errors | ☐ | | |
| Users Can Access Features | ☐ | | |

**Final Approval:**
- Development Lead: _________________________ Date: _______
- QA Lead: _________________________ Date: _______
- Operations Lead: _________________________ Date: _______

---

## Monitoring Going Forward

### Daily
- [ ] Check application health: `curl http://localhost:8000/health`
- [ ] Review error logs for critical issues
- [ ] Verify backup completed successfully

### Weekly
- [ ] Review command usage statistics
- [ ] Check performance metrics: `socrates performance status`
- [ ] Review security incidents: `socrates security incidents`
- [ ] Monitor database growth and optimize if needed

### Monthly
- [ ] Full system audit
- [ ] Performance trend analysis
- [ ] Security trend analysis
- [ ] Document learnings and improvements

---

## Support & Escalation

| Issue Type | Action | Escalation |
|-----------|--------|------------|
| Command Not Found | Check help, verify installation | DevOps |
| Database Error | Check integrity, review logs | Database Admin |
| Performance Issue | Check baseline, analyze bottleneck | Performance Team |
| Security Alert | Review incident, check logs | Security Team |
| User Issue | Review docs, check help system | Support Team |

---

## Related Documentation

- [Deployment Checklist](PHASE_9_DEPLOYMENT_CHECKLIST.md) - Pre-deployment verification
- [Release Notes](PHASE_9_RELEASE_NOTES.md) - Feature documentation
- [CLI Commands Reference](../../docs/commands/CLI_COMMANDS_REFERENCE.md) - Command documentation
- [User Guide](../../docs/guides/PHASE_9_NEW_FEATURES_GUIDE.md) - Usage examples

