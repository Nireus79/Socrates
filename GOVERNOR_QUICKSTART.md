# Governor & Constitutional AI - Quick Start Guide

## What Is Governor?

Governor is the ethical decision engine from `socratic-morality` that validates all agent actions against a constitutional framework. It runs automatically on every agent request.

---

## How It Works

```
Agent Request → AgentBus.route() → Governor.validate() → Allow/Deny → Execute/Block
```

1. **Request arrives** at agent bus
2. **Governor evaluates** action against constitution
3. **Allowed**: Action executes normally
4. **Denied**: Returns error with reason, action never executes

---

## Configuration

### Constitution File: `constitution.yaml`

Located at project root. Defines:
- **Principles**: What the system values (security, transparency, human oversight)
- **Action Policies**: Risk levels for different operations
- **Capabilities**: What each agent can do
- **Escalation Rules**: When to escalate to humans

### Example: Adding a New Capability

```yaml
# in constitution.yaml
capabilities:
  NewAgent:
    - read_documents
    - analyze_content
    - generate_summary
```

### Example: Restricting an Action

```yaml
# in constitution.yaml
action_policies:
  user_deletion:
    requires_approval: true      # Must be approved
    requires_audit: true         # Must be logged
    risk_level: critical         # Highest risk
    description: "User deletion requires explicit approval"
```

---

## Governance in Action

### Allowed Action
```
Agent: CodeGenerator
Action: code_generation
Decision: ✅ APPROVED (in capabilities, policy allows)
Result: Code execution proceeds
Log: "[Governor] Action 'code_generation' by CodeGenerator APPROVED"
```

### Denied Action
```
Agent: CodeGenerator
Action: user_deletion
Decision: ❌ DENIED (not in capabilities)
Result: Request returns error
Log: "[Governor] Action 'user_deletion' by CodeGenerator DENIED: Not in agent capabilities"
Response:
{
  "status": "error",
  "message": "Action denied by constitutional governance: Not in agent capabilities",
  "code": "governance_denied"
}
```

---

## Key Axioms (Why Governor Exists)

Governor enforces the 10 core axioms:
1. **Never Commit Injustice** - Refuse harmful actions
2. **Truth Before Approval** - Accuracy over convenience
3. **Preserve Human Agency** - Keep humans in control
4. **Require Authorization** - High-impact needs approval
5. **Transparency in Reasoning** - Explain decisions
6. **Respect Privacy** - Protect user data
7. **Protect Confidentiality** - Secure information
8. **Avoid Deception** - Be honest
9. **Acknowledge Uncertainty** - Know limits
10. **Defer to Experts** - Trust domain knowledge

---

## Action Policies (What Gets Checked)

### Critical Risk (Requires Approval)
- Code execution (timeout, memory limits)
- User data modification
- System configuration
- Agent creation

### High Risk (Monitored)
- External API calls
- Data access
- User profile reading

---

## Escalation Rules (When Humans Get Involved)

Automatically escalates to human if:
1. **Action not in capabilities** - Agent tries unauthorized action
2. **High-risk operation** - Critical or high-risk action attempted
3. **Unusual pattern** - Behavior deviates from baseline
4. **Resource exceeded** - Agent exceeds allocation
5. **High uncertainty** - System confidence too low

---

## Audit Trail (What Gets Logged)

Every action decision is logged with:
- Timestamp
- Agent ID
- Action
- Resource involved
- Constitutional basis
- Approval/denial decision
- Full reasoning

**Retention**: 365 days (immutable, encrypted)

---

## Testing Governor

### See Governor in Action
```python
# In tests, Governor validates all requests
# Even though tests use mocks, governance checks are bypassed gracefully
# because Governor instance is None in test mode
```

### Check Logs for Governor Activity
```bash
# Run with logging enabled
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
from socratic_system.orchestration import AgentOrchestrator
from socratic_system.config import SocratesConfig
config = SocratesConfig()
orch = AgentOrchestrator(config)
print('Governor initialized:', orch.governor is not None)
"
```

---

## Troubleshooting

### Governor Not Active
**Symptom**: All actions allowed, no governance logs
**Cause**: socratic-morality library not installed
**Fix**: `pip install socratic-morality>=0.0.3`

### Constitution File Not Found
**Symptom**: "Constitution file not found" warning
**Cause**: constitution.yaml missing from project root
**Fix**: Ensure constitution.yaml exists at `C:\Users\themi\PycharmProjects\Socrates\constitution.yaml`

### Action Denied But Should Be Allowed
**Symptom**: Governance error on valid action
**Cause**: Action not in agent capabilities
**Fix**: Add action to capabilities in constitution.yaml

---

## Advanced: Custom Governance

### Hook Into Governance
```python
# In orchestrator.py, governance is available as:
orchestrator.governor  # Governor instance
orchestrator.constitution  # Constitution framework

# Access directly:
allowed, reason = orchestrator.governor.evaluate_action(
    agent="MyAgent",
    action="my_action",
    context={"additional": "data"}
)
```

### Override Governance (Emergency Use Only)
```python
# To bypass governance in emergency (NOT RECOMMENDED):
# Requires explicit architect/admin sign-off and audit trail

# 1. Log the decision
orchestrator.logger.warning(
    "EMERGENCY: Governance override for [action] - "
    "Reason: [justification] - Approved by: [person]"
)

# 2. Execute action
# 3. Update constitution to reflect the exception

# Note: All overrides are immutably logged for audit
```

---

## Constitution Structure (Detailed)

```yaml
supreme_principle:
  never_commit_injustice_even_under_instruction: true

axioms: [list of 10 core values]

principles:
  security: [isolation, identity verification, access limits]
  transparency: [explain decisions, audit trails, disclose limits]
  human_oversight: [escalate high-impact, preserve user control]

action_policies:
  [type]:
    requires_approval: bool
    requires_audit: bool
    risk_level: "critical|high|medium"

capabilities:
  [Agent]: [list of allowed actions]

approval_workflows:
  high_risk_actions:
    - notification: immediate
    - fallback: escalate to queue

audit_requirements:
  immutable_logging: true
  retention_days: 365
  encryption: true
```

---

## Quick Checklist

- ✅ Constitution.yaml exists at project root
- ✅ socratic-morality library installed (`pip list | grep socratic-morality`)
- ✅ Governor initialized in orchestrator (check logs for "Governor initialized")
- ✅ Agent capabilities defined in constitution for all agents
- ✅ Action policies set appropriately for your risk tolerance
- ✅ Audit logging enabled (immutable, 365-day retention)
- ✅ Escalation rules configured for your ops team
- ✅ Tests pass with governance enabled

---

## Next Steps

1. **Review constitution.yaml** - Understand the principles
2. **Add custom agents** - Define their capabilities
3. **Set approval workflows** - Route escalations correctly
4. **Monitor logs** - Watch for denials and escalations
5. **Plan Phase 3** - Sandboxing and zero-trust when ready

---

## Support

Governor is part of the socratic-morality library.
- GitHub: https://github.com/Nireus79/Socratic-morality
- Integration: `SOCRATIC_MORALITY_INTEGRATION.md`
- Tests: `tests/test_phase2b_*.py` (all passing)
