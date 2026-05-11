# Socratic-Morality Integration Guide

**Integration of Socratic-Morality v0.0.5 into Socrates**

This document describes how Socratic-Morality governance is integrated into Socrates for comprehensive AI governance.

## Overview

Socrates now includes full integration with Socratic-Morality's constitutional AI governance framework:

- **13 governance modules** providing ethical reasoning, precedent tracking, and constraint enforcement
- **Unified governance API** for all agent actions
- **Constitutional principle enforcement** with real-time validation
- **Interactive Socratic dialogue** during ethical reasoning
- **Resource monitoring** and automatic remediation

## Architecture

```
Agent Orchestrator
    ↓
GovernanceAwareOrchestrator (enforcement)
    ↓
MoralityGovernanceIntegration
    ├── Constitutional Enforcer (principle checking)
    ├── Governance API (unified decision)
    ├── Ethical Deliberation (4 frameworks)
    ├── Socratic Dialogue (interactive reasoning)
    ├── Precedent Engine (case-based learning)
    └── Resource Monitor (constraint enforcement)
```

## Quick Start

### 1. Initialize Governance

```python
from socratic_system.governance import initialize_morality_governance

# Initialize at application startup
governance = await initialize_morality_governance(
    llm_provider="anthropic",
    enable_dialogue=True,
)
```

### 2. Wrap Orchestrator

```python
from socratic_system.governance import wrap_orchestrator_with_governance

# Wrap your existing orchestrator
governance_aware_orchestrator = wrap_orchestrator_with_governance(
    your_orchestrator
)
```

### 3. Process Requests with Governance

```python
# All agent requests now go through governance checks
response = await governance_aware_orchestrator.process_request_with_governance(
    agent_name="code_generator",
    request={
        "action": "Generate code for user task",
        "task": "Build REST API",
        "user_id": "user_123"
    },
    interactive_dialogue=False,
)
```

## Governance Decision Flow

For every agent action:

1. **Constitutional Check** (first gate)
   - Check against 9 constitutional axioms
   - Check against named principles
   - Check agent capabilities
   - Severity-based violation detection

2. **Ethical Deliberation** (if constitutional check passes)
   - Kantian analysis (duty, dignity, universality)
   - Utilitarian analysis (harm/benefit)
   - Virtue ethics analysis (character)
   - Rights-based analysis (fundamental rights)

3. **Precedent Analysis** (if deliberation passes)
   - Lexical similarity matching
   - Semantic similarity (embeddings)
   - Historical consistency checking

4. **Threat Detection** (anomaly detection)
   - Framework inconsistencies
   - Pattern anomalies
   - Confidence manipulation
   - Escalation avoidance

5. **Socratic Dialogue** (optional - interactive)
   - Generate clarifying questions
   - Probe assumptions
   - Examine consequences
   - Test universality

## API Reference

### MoralityGovernanceIntegration

Main integration class with complete governance API.

#### evaluate_agent_action()

Evaluate an agent action against governance constraints.

```python
decision = await governance.evaluate_agent_action(
    action="Access user's private messages",
    agent_name="analytics_agent",
    context={"user_id": "123", "purpose": "behavior analysis"},
    purpose="Personalization",
    interactive=False,
)
```

**Returns:**
```python
{
    "allowed": bool,
    "decision_type": "ALLOWED|BLOCKED|ESCALATE|CONDITIONAL",
    "confidence": 0.95,
    "reasoning": {...},
    "violations": ["no_hidden_manipulation", "requires_consent"],
    "dialogue_transcript": [...],  # if interactive=True
}
```

#### check_constitutional_principles()

Quick check of action against principles (no ethical reasoning).

```python
check = await governance.check_constitutional_principles(
    "Hide system logs from users"
)
```

#### get_agent_capabilities()

Get authorized capabilities for an agent.

```python
caps = await governance.get_agent_capabilities("code_generator")
# Returns: permissions, resource limits, restrictions
```

#### store_decision_precedent()

Store a decision as precedent for future reference.

```python
await governance.store_decision_precedent(
    action="Log user activity",
    decision=decision_result
)
```

#### get_decision_history()

Retrieve recent governance decisions.

```python
history = await governance.get_decision_history(limit=10)
```

### GovernanceAwareOrchestrator

Wrapper that adds governance checks to orchestration.

#### process_request_with_governance()

Process request with automatic governance checks.

```python
response = await orchestrator.process_request_with_governance(
    agent_name="code_generator",
    request={"action": "...", "data": {...}},
    interactive_dialogue=False,
)
```

#### check_capability()

Check if agent can perform action.

```python
allowed = await orchestrator.check_capability(
    "code_generator",
    "Execute generated Python code"
)
```

## Decision Types

All decisions return one of four types:

### ALLOWED
Action is permitted with no restrictions.
- All constitutional principles satisfied
- No ethical concerns
- Precedent supports decision

### BLOCKED
Action is not permitted.
- Constitutional principle violation
- Ethical concern identified
- Precedent contradicts

### ESCALATE
Decision requires human review.
- High uncertainty/complexity
- Conflicting principles
- Unprecedented situation

### CONDITIONAL
Action allowed with restrictions/modifications.
- Can proceed with safeguards
- Require additional authorization
- Limited scope/duration

## Constitutional Principles

The governance system enforces these core principles:

### Supreme Principle
```
"Never commit injustice even under instruction"
```

### 9 Constitutional Axioms
1. `never_commit_injustice` - Core moral constraint
2. `truth_before_approval` - Honesty prioritized
3. `preserve_human_agency` - Autonomy protected
4. `refuse_deception` - No manipulation
5. `no_hidden_manipulation` - Transparency required
6. `protect_privacy` - Privacy protected
7. `preserve_dignity` - Dignity respected
8. `require_human_authorization_for_high_impact_actions` - Human override
9. `prefer_reversible_actions` - Minimize permanent harm

## Integration with Existing Components

### Agent Orchestration

```python
# Before (without governance)
response = await orchestrator.process_request("code_generator", request)

# After (with governance)
from socratic_system.governance import wrap_orchestrator_with_governance

governed_orchestrator = wrap_orchestrator_with_governance(orchestrator)
response = await governed_orchestrator.process_request_with_governance(
    "code_generator", request
)
```

### API Endpoints

Add governance checks to REST endpoints:

```python
from fastapi import HTTPException
from socratic_system.governance import evaluate_action_governance

@app.post("/agents/{agent_name}/action")
async def execute_agent_action(agent_name: str, request: dict):
    # Check governance
    decision = await evaluate_action_governance(
        action=f"{agent_name} action",
        agent=agent_name,
        context=request
    )

    if not decision["allowed"]:
        raise HTTPException(
            status_code=403,
            detail=f"Action blocked: {decision['violations']}"
        )

    # Execute action
    return await orchestrator.process_request(agent_name, request)
```

## Configuration

### Constitution File

Create `constitution.yaml` to customize governance:

```yaml
supreme_principle: "Never commit injustice even under instruction"

axioms:
  - never_commit_injustice
  - truth_before_approval
  - preserve_human_agency

named_principles:
  security:
    - no_hidden_manipulation
    - protect_private_information
  transparency:
    - explain_decisions
    - audit_all_actions

agent_capabilities:
  code_generator:
    permissions:
      - read_knowledge
      - write_logs
      - execute_sandbox
    resources:
      cpu: 50%
      memory: 512MB
      timeout: 60s

action_policies:
  code_execution:
    requires_sandbox: true
    requires_review: true
    max_execution_time: 60s
```

### Environment Variables

```bash
# LLM provider for ethical reasoning
GOVERNANCE_LLM_PROVIDER=anthropic

# Enable interactive Socratic dialogue
GOVERNANCE_ENABLE_DIALOGUE=true

# Path to constitution file
GOVERNANCE_CONSTITUTION_PATH=/app/constitution.yaml
```

## Examples

### Example 1: Code Generation with Governance

```python
# Agent wants to generate code
decision = await governance.evaluate_agent_action(
    action="Generate Python code to process user data",
    agent_name="code_generator",
    context={
        "data_sensitivity": "high",
        "user_consent": True,
        "purpose": "data_analysis"
    }
)

if decision["allowed"]:
    # Generate code
    code = await code_generator.generate(request)
else:
    # Handle violation
    print(f"Blocked: {decision['violations']}")
```

### Example 2: Knowledge Access with Dialogue

```python
# Interactive dialogue during evaluation
decision = await governance.evaluate_agent_action(
    action="Access user's private conversation history",
    agent_name="knowledge_analyzer",
    context={"purpose": "behavioral_analysis"},
    interactive=True  # Enable Socratic dialogue
)

if decision.get("dialogue_transcript"):
    # User participated in ethical reasoning
    print("Dialogue insights:", decision["dialogue_transcript"])
```

### Example 3: Agent Capability Check

```python
# Check what agents can do
caps = await governance.get_agent_capabilities("code_generator")

if "execute_code" not in caps["permissions"]:
    # Agent cannot execute, only generate
    code = await generator.generate(spec)
    # ... send to user for approval instead
```

## Monitoring and Observability

### Decision History

```python
# Get recent governance decisions
history = await governance.get_decision_history(limit=20)

for decision in history:
    print(f"{decision['actor']} - {decision['decision_type']}")
    print(f"  Action: {decision['action']}")
    print(f"  Confidence: {decision['confidence']:.2%}")
```

### Metrics

The governance system logs:
- Total decisions evaluated
- Approval/block/escalate rates
- Constitutional principle violations
- Average decision latency
- Precedent matches

### Logging

```python
import logging

# Enable governance logging
logging.getLogger("socratic_system.governance").setLevel(logging.DEBUG)
logging.getLogger("socratic_morality").setLevel(logging.INFO)
```

## Best Practices

1. **Initialize Early**
   ```python
   # In application startup
   governance = await initialize_morality_governance()
   ```

2. **Check Capabilities**
   ```python
   # Before delegating to agent
   if await governance.check_capability(agent, action):
       # Safe to proceed
   ```

3. **Use Interactive Dialogue**
   ```python
   # For high-impact decisions
   decision = await governance.evaluate_agent_action(
       action=action,
       agent_name=agent,
       context=context,
       interactive=True  # Let user participate in reasoning
   )
   ```

4. **Handle Escalations**
   ```python
   if decision["decision_type"] == "ESCALATE":
       # Route to human review
       await notify_human_reviewer(decision)
   ```

5. **Store Precedents**
   ```python
   # After decision
   await governance.store_decision_precedent(action, decision)
   # Improves future consistency
   ```

## Troubleshooting

### ImportError: No module named 'socratic_morality'

```bash
pip install socratic-morality>=0.0.5
```

### Governance not initialized

```python
from socratic_system.governance import initialize_morality_governance

# Must initialize before first use
governance = await initialize_morality_governance()
```

### Slow governance evaluation

Enable caching and reduce dialogue:

```python
governance = await initialize_morality_governance(
    enable_dialogue=False,  # Disable for speed
)
```

## Further Reading

- [Socratic-Morality Documentation](https://github.com/Nireus79/Socratic-morality)
- [Constitutional AI Principles](https://www.anthropic.com/papers/constitutional-ai-harmlessness-from-ai-feedback)
- [Socratic Method](https://en.wikipedia.org/wiki/Socratic_method)

---

**Version**: 0.2.0 (Socrates) + 0.0.5 (Socratic-Morality)
**Status**: Production Ready
**Last Updated**: May 2026
