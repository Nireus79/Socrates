# Security Checklist for Development

Use this checklist when implementing new features, agents, or API endpoints.

## Pre-Development

- [ ] Review SECURITY.md for compliance requirements
- [ ] Identify data sensitivity level (public, internal, confidential, restricted)
- [ ] List resources the feature will access (database, files, APIs)
- [ ] Check if feature requires constitutional governance approval
- [ ] Identify if feature is high-risk (code execution, data modification, etc.)

## Design Phase

- [ ] Define agent capabilities in constitution.yaml
  - [ ] List all actions the agent can perform
  - [ ] Specify resource access requirements
  - [ ] Set resource limits (timeout, memory)
  - [ ] Mark sensitive operations
- [ ] Identify authentication requirements
  - [ ] Does feature need user authentication?
  - [ ] Does feature need API key?
  - [ ] Does feature need MFA?
- [ ] Plan authorization
  - [ ] What scopes are required?
  - [ ] Which users/agents can use this?
  - [ ] What's the approval workflow?
- [ ] Design audit logging
  - [ ] What events should be logged?
  - [ ] What details should be captured?
  - [ ] What's the retention requirement?

## Implementation Phase

### Input Validation
- [ ] All user input validated against schema (Pydantic)
- [ ] Input length limits enforced
- [ ] File type validation (magic bytes, not just extension)
- [ ] SQL injection prevention (parameterized queries only)
- [ ] Path traversal prevention (normalize paths)
- [ ] XSS prevention (escape user content)

### Data Protection
- [ ] Sensitive data encrypted at rest
  - [ ] User PII
  - [ ] API keys
  - [ ] Conversation history
  - [ ] Custom project data
- [ ] Sensitive data not logged or exposed in errors
- [ ] Password hashing with salt (bcrypt)
- [ ] API keys hashed before storage

### Access Control
- [ ] User authorization checked (scope-based)
- [ ] Agent authorization checked (capability-based)
- [ ] Data ownership verified (only owner can access)
- [ ] Admin-only features protected
- [ ] Rate limiting implemented

### Logging & Audit
- [ ] Audit log entries for significant actions
- [ ] Failed access attempts logged
- [ ] Data modifications logged
- [ ] Admin actions logged
- [ ] Security decisions logged
- [ ] No sensitive data in logs

### Error Handling
- [ ] Generic error messages (no internals exposed)
- [ ] Detailed errors logged server-side only
- [ ] Request ID provided for support investigation
- [ ] Graceful degradation on errors
- [ ] No stack traces in responses

### External Integrations
- [ ] API calls use HTTPS only
- [ ] API credentials not hardcoded
- [ ] External API responses validated
- [ ] Timeouts enforced
- [ ] Rate limiting respected
- [ ] Failure handling implemented

### Code Execution (if applicable)
- [ ] Code validated for dangerous patterns
- [ ] Code executed in sandbox (subprocess)
- [ ] Resource limits enforced (timeout, memory)
- [ ] Output captured and sanitized
- [ ] Errors captured safely
- [ ] Process terminated on failure

## Testing Phase

### Unit Tests
- [ ] Happy path tests
- [ ] Error case tests
- [ ] Authorization tests (should be denied)
- [ ] Input validation tests
- [ ] Boundary condition tests

### Security Tests
- [ ] SQL injection attempts
- [ ] XSS attempts
- [ ] Path traversal attempts
- [ ] Unauthorized access attempts
- [ ] Resource exhaustion attempts
- [ ] Code injection (if applicable)

### Audit Tests
- [ ] Actions logged correctly
- [ ] Sensitive data not logged
- [ ] Audit entries complete and accurate

## Before Deployment

### Pre-Deployment Review
- [ ] Code review completed
- [ ] Security review completed
- [ ] All tests passing
- [ ] No hardcoded secrets
- [ ] Dependencies checked for vulnerabilities
- [ ] OWASP Top 10 addressed

### Production Checklist
- [ ] Secrets in environment variables (not .env)
- [ ] Database encryption key rotated
- [ ] SSL/TLS configured
- [ ] CORS properly configured
- [ ] Security headers enabled
- [ ] Rate limiting enabled
- [ ] Monitoring/alerting set up
- [ ] Audit logging verified
- [ ] Database backups configured
- [ ] Incident response plan reviewed

### Monitoring Setup
- [ ] Failed auth attempt alerts
- [ ] Unusual API usage alerts
- [ ] Resource limit alerts
- [ ] Error rate alerts
- [ ] Slow query alerts
- [ ] Security event dashboards

## Common Vulnerabilities & Fixes

### SQL Injection
```python
# ❌ UNSAFE
query = f"SELECT * FROM projects WHERE id = '{project_id}'"

# ✅ SAFE
query = "SELECT * FROM projects WHERE id = ?"
cursor.execute(query, (project_id,))
```

### XSS
```python
# ❌ UNSAFE
html = f"<p>{user_input}</p>"

# ✅ SAFE
from markupsafe import escape
html = f"<p>{escape(user_input)}</p>"
```

### Hardcoded Secrets
```python
# ❌ UNSAFE
API_KEY = "sk-ant-v1-abc123"

# ✅ SAFE
import os
API_KEY = os.environ.get("ANTHROPIC_API_KEY")
if not API_KEY:
    raise ValueError("ANTHROPIC_API_KEY not set")
```

### Path Traversal
```python
# ❌ UNSAFE
file_path = f"/uploads/{user_filename}"

# ✅ SAFE
from pathlib import Path
safe_path = (Path("/uploads") / user_filename).resolve()
if not str(safe_path).startswith("/uploads/"):
    raise ValueError("Invalid file path")
```

### Missing Authorization
```python
# ❌ UNSAFE
def get_project(project_id):
    return db.get_project(project_id)

# ✅ SAFE
def get_project(project_id, current_user):
    project = db.get_project(project_id)
    if project.owner_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return project
```

## Agent Capability Checklist

When adding a new agent capability:

- [ ] Action added to constitution.yaml
- [ ] Resource access specified (database:read, file_system:write, etc.)
- [ ] Resource limits defined (timeout, memory, file size)
- [ ] Risk level assessed (low, medium, high, critical)
- [ ] Approval requirements specified
- [ ] Audit logging configured
- [ ] Tests written for capability
- [ ] Documentation updated

## Security Review Checklist

When reviewing code for security:

- [ ] No hardcoded secrets or credentials
- [ ] All inputs validated
- [ ] All outputs escaped
- [ ] SQL injection prevention (parameterized queries)
- [ ] XSS prevention (output escaping)
- [ ] Path traversal prevention (path normalization)
- [ ] Authorization checked (user scopes, agent capabilities)
- [ ] Sensitive data not logged
- [ ] Error messages generic (no internals exposed)
- [ ] Encryption used for sensitive data
- [ ] Audit logging comprehensive
- [ ] Rate limiting implemented
- [ ] Timeout enforced
- [ ] Resource limits enforced

## Incident Response

If a security issue is discovered:

1. **Stop**: Cease any automated processes
2. **Preserve**: Don't delete logs or evidence
3. **Investigate**: Check audit logs for scope
4. **Contain**: Revoke credentials if compromised
5. **Document**: Record timeline and findings
6. **Notify**: Inform affected users if required
7. **Patch**: Fix the vulnerability
8. **Review**: Update this checklist

## Resources

- OWASP Top 10: https://owasp.org/www-project-top-ten/
- OWASP Cheat Sheet: https://cheatsheetseries.owasp.org/
- CWE Top 25: https://cwe.mitre.org/top25/
- Bandit (Python security): https://bandit.readthedocs.io/
- NIST Guidelines: https://csrc.nist.gov/publications/detail/sp/800-53/rev-5/final

## Questions?

Contact the security team or review SECURITY.md for more details.

---

**Last Updated**: May 2026
**Version**: 1.0
**Effective Date**: Immediately
