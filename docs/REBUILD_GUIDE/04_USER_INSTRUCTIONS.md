# USER INSTRUCTIONS SYSTEM
## AI Behavior Rules & Constraints

**This is the most critical feature for user control over AI behavior**

---

## OVERVIEW

The User Instructions System allows users to define fundamental rules that ALL agents MUST follow. This is a constraint layer that sits above the agents and validates every action against user-defined rules.

**Key Principle:** User rules are **binding constraints**, not suggestions.

---

## ARCHITECTURE

```
┌─────────────────────────────────────┐
│  Frontend: Instructions Panel        │
│  (Text area for entering rules)      │
└──────────────┬──────────────────────┘
               │ Save instructions
               ↓
┌─────────────────────────────────────┐
│  InstructionService                 │
│  - Parse rules                      │
│  - Store in database                │
│  - Validate against rules           │
│  - Log violations                   │
└──────────────┬──────────────────────┘
               │ Retrieve rules
               ↓
┌─────────────────────────────────────┐
│  Agent Processing Pipeline          │
│  1. Input validation                │
│  2. Apply user instructions         │
│  3. Route to agent                  │
│  4. Validate result vs rules        │
│  5. Return result or error          │
└──────────────┬──────────────────────┘
               │
               ↓
┌─────────────────────────────────────┐
│  AuditLog                           │
│  - Rules applied                    │
│  - Violations detected              │
│  - Actions taken                    │
└─────────────────────────────────────┘
```

---

## DATABASE MODEL

```python
# backend/src/models/instruction.py

class UserInstruction(Base):
    __tablename__ = "user_instructions"

    id: UUID = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: UUID = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    project_id: Optional[UUID] = Column(UUID(as_uuid=True), ForeignKey("projects.id"))

    # Raw rules text
    rules: str = Column(Text)

    # Parsed rules (JSON)
    parsed_rules: List[Dict] = Column(JSON)

    # Rule categories
    security_rules: List[str] = Column(JSON, default=[])
    performance_rules: List[str] = Column(JSON, default=[])
    quality_rules: List[str] = Column(JSON, default=[])
    architecture_rules: List[str] = Column(JSON, default=[])
    custom_rules: List[str] = Column(JSON, default=[])

    # Status
    is_active: bool = Column(Boolean, default=True)
    is_global: bool = Column(Boolean, default=False)  # Apply to all projects

    # Metadata
    created_at: datetime = Column(DateTime, default=datetime.utcnow)
    updated_at: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    violation_count: int = Column(Integer, default=0)

    # Relationship
    user = relationship("User", backref="instructions")
```

---

## SERVICE IMPLEMENTATION

```python
# backend/src/services/instruction_service.py

from typing import Dict, List, Any, Optional, Tuple
from src.repositories.instruction_repository import InstructionRepository
from src.repositories.audit_repository import AuditRepository
import re
import logging

logger = logging.getLogger(__name__)

class InstructionService:
    def __init__(self,
                 instruction_repo: InstructionRepository,
                 audit_repo: AuditRepository):
        self.instruction_repo = instruction_repo
        self.audit_repo = audit_repo

    async def create_instruction(
        self,
        user_id: str,
        rules: str,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create new user instructions

        Args:
            user_id: User creating rules
            rules: Rule text (newline separated or bullet points)
            project_id: Optional project scope

        Returns:
            Created instruction object
        """
        try:
            # Parse rules
            parsed_rules = self.parse_rules(rules)

            if not parsed_rules:
                return {
                    'success': False,
                    'error': 'No valid rules provided'
                }

            # Categorize rules
            categorized = self.categorize_rules(parsed_rules)

            # Create instruction
            instruction = await self.instruction_repo.create({
                'user_id': user_id,
                'project_id': project_id,
                'rules': rules,
                'parsed_rules': parsed_rules,
                'security_rules': categorized['security'],
                'performance_rules': categorized['performance'],
                'quality_rules': categorized['quality'],
                'architecture_rules': categorized['architecture'],
                'custom_rules': categorized['custom']
            })

            logger.info(f"Created {len(parsed_rules)} rules for user {user_id}")

            # Log to audit
            await self.audit_repo.log({
                'user_id': user_id,
                'action': 'create_instruction',
                'resource_type': 'instruction',
                'resource_id': instruction['id'],
                'changes': {'rules_count': len(parsed_rules)}
            })

            return {
                'success': True,
                'instruction': instruction,
                'rules_count': len(parsed_rules)
            }

        except Exception as e:
            logger.error(f"Failed to create instruction: {e}")
            return {'success': False, 'error': str(e)}

    def parse_rules(self, text: str) -> List[Dict[str, str]]:
        """
        Parse rule text into structured format

        Args:
            text: Raw rule text

        Returns:
            List of parsed rules
        """
        rules = []

        # Split by newlines and bullet points
        lines = re.split(r'[\n•-]\s*', text.strip())

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Extract rule and optional rationale
            if ':' in line:
                rule, rationale = line.split(':', 1)
                rules.append({
                    'rule': rule.strip(),
                    'rationale': rationale.strip(),
                    'priority': 'high'  # Default priority
                })
            else:
                rules.append({
                    'rule': line,
                    'rationale': '',
                    'priority': 'medium'  # Default priority
                })

        return rules

    def categorize_rules(self, rules: List[Dict]) -> Dict[str, List]:
        """
        Categorize rules by type

        Args:
            rules: Parsed rules

        Returns:
            Categorized rules
        """
        categories = {
            'security': [],
            'performance': [],
            'quality': [],
            'architecture': [],
            'custom': []
        }

        security_keywords = ['security', 'auth', 'encrypt', 'private', 'access']
        performance_keywords = ['performance', 'speed', 'optimize', 'cache', 'latency']
        quality_keywords = ['test', 'quality', 'coverage', 'review', 'check']
        architecture_keywords = ['architecture', 'design', 'pattern', 'structure', 'component']

        for rule_obj in rules:
            rule = rule_obj['rule'].lower()

            if any(kw in rule for kw in security_keywords):
                categories['security'].append(rule_obj)
            elif any(kw in rule for kw in performance_keywords):
                categories['performance'].append(rule_obj)
            elif any(kw in rule for kw in quality_keywords):
                categories['quality'].append(rule_obj)
            elif any(kw in rule for kw in architecture_keywords):
                categories['architecture'].append(rule_obj)
            else:
                categories['custom'].append(rule_obj)

        return categories

    async def get_user_instructions(
        self,
        user_id: str,
        project_id: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get active instructions for user (optionally scoped to project)

        Args:
            user_id: User ID
            project_id: Optional project scope

        Returns:
            Active instruction or None
        """
        # First check project-specific instructions
        if project_id:
            project_instruction = await self.instruction_repo.get_by_user_and_project(
                user_id, project_id
            )
            if project_instruction and project_instruction['is_active']:
                return project_instruction

        # Fall back to global instructions
        global_instruction = await self.instruction_repo.get_global_by_user(user_id)
        if global_instruction and global_instruction['is_active']:
            return global_instruction

        return None

    async def validate_result(
        self,
        result: Dict[str, Any],
        instruction: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate result against user instructions

        Args:
            result: Agent result to validate
            instruction: User instructions

        Returns:
            (is_valid, violation_reason)
        """
        try:
            # Check each rule
            for rule_obj in instruction['parsed_rules']:
                rule = rule_obj['rule'].lower()

                # Security rules
                if any(kw in rule for kw in ['security', 'auth', 'encrypt']):
                    if not self._check_security_compliance(result, rule):
                        return False, f"Violates security rule: {rule}"

                # Quality rules
                if any(kw in rule for kw in ['test', 'quality', 'review']):
                    if not self._check_quality_compliance(result, rule):
                        return False, f"Violates quality rule: {rule}"

                # Architecture rules
                if any(kw in rule for kw in ['architecture', 'design']):
                    if not self._check_architecture_compliance(result, rule):
                        return False, f"Violates architecture rule: {rule}"

                # Performance rules
                if any(kw in rule for kw in ['performance', 'optimize']):
                    if not self._check_performance_compliance(result, rule):
                        return False, f"Violates performance rule: {rule}"

            return True, None

        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False, f"Validation error: {str(e)}"

    def _check_security_compliance(self, result: Dict, rule: str) -> bool:
        """Check security compliance"""
        # Example checks
        if 'requires auth' in rule:
            return result.get('requires_authentication', False)
        if 'encrypt' in rule:
            return result.get('encrypted', False)
        return True

    def _check_quality_compliance(self, result: Dict, rule: str) -> bool:
        """Check quality compliance"""
        # Example checks
        if 'requires test' in rule:
            return result.get('has_tests', False)
        if 'requires review' in rule:
            return result.get('requires_review', False)
        return True

    def _check_architecture_compliance(self, result: Dict, rule: str) -> bool:
        """Check architecture compliance"""
        # Example checks
        if 'must use' in rule:
            # Extract technology requirement
            pass
        return True

    def _check_performance_compliance(self, result: Dict, rule: str) -> bool:
        """Check performance compliance"""
        # Example checks
        if 'cache' in rule:
            return result.get('uses_cache', False)
        return True

    async def log_rule_violation(
        self,
        user_id: str,
        instruction_id: str,
        violated_rule: str,
        action: str,
        result: Dict
    ) -> None:
        """Log rule violation"""
        await self.audit_repo.log({
            'user_id': user_id,
            'action': 'instruction_violation',
            'resource_type': 'instruction',
            'resource_id': instruction_id,
            'changes': {
                'violated_rule': violated_rule,
                'action': action,
                'result_summary': result.get('message', '')
            }
        })

        # Increment violation count
        await self.instruction_repo.increment_violation_count(instruction_id)

        logger.warning(f"Rule violation: User {user_id} violated rule: {violated_rule}")
```

---

## FRONTEND COMPONENT

```tsx
// frontend/src/components/InstructionsPanel.tsx

import React, { useState, useEffect } from 'react';
import { useAppDispatch, useAppSelector } from '../redux/hooks';
import { setInstructions, fetchInstructions } from '../redux/slices/instructionSlice';
import axios from 'axios';

export const InstructionsPanel: React.FC = () => {
  const [rules, setRules] = useState('');
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const dispatch = useAppDispatch();
  const { current, loading } = useAppSelector(state => state.instructions);

  useEffect(() => {
    dispatch(fetchInstructions());
  }, [dispatch]);

  useEffect(() => {
    if (current) {
      setRules(current.rules);
    }
  }, [current]);

  const handleSave = async () => {
    setSaving(true);
    setError('');
    setSuccess('');

    try {
      const response = await axios.post('/api/instructions', {
        rules: rules,
        project_id: null  // Or current project
      });

      dispatch(setInstructions(response.data));
      setSuccess('Instructions saved successfully!');
    } catch (err) {
      setError('Failed to save instructions');
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="p-6 bg-white rounded-lg shadow">
      <h2 className="text-2xl font-bold mb-4">AI Behavior Rules</h2>

      <p className="text-gray-600 mb-4">
        Define rules that all AI agents must follow. These are binding constraints.
      </p>

      <div className="space-y-4">
        {/* Rules Textarea */}
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Your Rules (one per line)
          </label>
          <textarea
            value={rules}
            onChange={(e) => setRules(e.target.value)}
            placeholder="Examples:
• Always ask for clarification before major changes
• Prioritize security over performance
• Require tests for all code changes
• Use TypeScript for frontend
• Document breaking changes"
            className="w-full h-64 p-3 border border-gray-300 rounded-lg font-mono text-sm"
          />
        </div>

        {/* Examples */}
        <div className="bg-blue-50 p-4 rounded-lg">
          <h4 className="font-semibold text-blue-900 mb-2">Example Rules:</h4>
          <ul className="text-sm text-blue-800 space-y-1">
            <li>• Always ask for clarification before architectural decisions</li>
            <li>• Require security review for all API changes</li>
            <li>• Maintain backward compatibility</li>
            <li>• Use async/await for I/O operations</li>
            <li>• Include tests with all code submissions</li>
            <li>• Document API changes in CHANGELOG</li>
          </ul>
        </div>

        {/* Error/Success Messages */}
        {error && <div className="text-red-600 bg-red-50 p-3 rounded">{error}</div>}
        {success && <div className="text-green-600 bg-green-50 p-3 rounded">{success}</div>}

        {/* Buttons */}
        <div className="flex gap-2">
          <button
            onClick={handleSave}
            disabled={saving}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50"
          >
            {saving ? 'Saving...' : 'Save Rules'}
          </button>
          <button
            onClick={() => setRules('')}
            className="px-4 py-2 bg-gray-200 text-gray-800 rounded hover:bg-gray-300"
          >
            Clear
          </button>
        </div>
      </div>

      {/* Current Rules Display */}
      {current && (
        <div className="mt-6 p-4 bg-gray-50 rounded-lg">
          <h4 className="font-semibold mb-2">Active Rules ({current.parsed_rules.length})</h4>
          <div className="space-y-2">
            {current.parsed_rules.map((rule, i) => (
              <div key={i} className="text-sm text-gray-700 flex gap-2">
                <span className="text-gray-400">→</span>
                <span>{rule.rule}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
```

---

## INTEGRATION WITH AGENT PROCESSING

```python
# In agent_service.py

async def route_request(
    self,
    agent_id: str,
    action: str,
    data: Dict[str, Any],
    user_id: str,
    project_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Route request with user instruction enforcement
    """
    try:
        # 1. Get user instructions
        instructions = await self.instruction_service.get_user_instructions(
            user_id, project_id
        )

        # 2. Apply instructions to request data
        if instructions and instructions['is_active']:
            data['_user_instructions'] = instructions['parsed_rules']
            data['_instruction_id'] = instructions['id']
            logger.info(f"Applied {len(instructions['parsed_rules'])} rules to request")

        # 3. Route to agent
        result = self.orchestrator.route_request(agent_id, action, data)

        # 4. Validate result against instructions
        if instructions and instructions['is_active']:
            is_valid, reason = await self.instruction_service.validate_result(
                result, instructions
            )

            if not is_valid:
                # Log violation
                await self.instruction_service.log_rule_violation(
                    user_id,
                    instructions['id'],
                    reason,
                    action,
                    result
                )

                # Return error
                return {
                    'success': False,
                    'error': f"Result violates your instruction: {reason}",
                    'instruction_violation': True,
                    'violated_rule': reason
                }

        return result

    except Exception as e:
        logger.error(f"Request routing error: {e}")
        return {'success': False, 'error': str(e)}
```

---

## API ENDPOINTS

```
GET    /api/instructions
       Get current user's instructions

POST   /api/instructions
       Create new instruction
       Body: {
         "rules": "string",
         "project_id": "uuid (optional)"
       }

PUT    /api/instructions/{id}
       Update instruction
       Body: {
         "rules": "string"
       }

DELETE /api/instructions/{id}
       Delete instruction

GET    /api/instructions/{id}/violations
       Get rule violations for instruction

POST   /api/instructions/validate
       Validate text as rules
       Body: {
         "rules_text": "string"
       }
       Returns: {
         "is_valid": bool,
         "errors": [],
         "parsed_rules": []
       }
```

---

## EXAMPLES OF EFFECTIVE RULES

### Security-Focused
```
- Always validate user input
- Require authentication for all API endpoints
- Use parameterized queries for database operations
- Encrypt all sensitive data
- Implement rate limiting on public endpoints
```

### Quality-Focused
```
- Include unit tests for all new functions
- Maintain test coverage above 80%
- Require code review before merge
- Add JSDoc comments to all public functions
- Run linter before committing
```

### Architecture-Focused
```
- Follow component composition pattern
- Keep components under 500 lines
- Use dependency injection for services
- Maintain separation of concerns
- Use async/await for all I/O operations
```

### Development-Focused
```
- Use TypeScript strict mode
- Avoid using 'any' type
- Name variables descriptively
- Keep functions pure when possible
- Document breaking changes in CHANGELOG
```

---

## AUDIT LOGGING

Every rule violation is logged:

```json
{
  "timestamp": "2025-10-18T...",
  "user_id": "user_123",
  "action": "instruction_violation",
  "instruction_id": "inst_456",
  "violated_rule": "Requires tests",
  "request_action": "generate_code",
  "agent_id": "code_generator",
  "result_summary": "Generated code without tests"
}
```

---

## BEST PRACTICES

1. **Keep Rules Clear**
   - Use simple, unambiguous language
   - One rule per line

2. **Use Specific Rules**
   - BAD: "Write better code"
   - GOOD: "Include unit tests for all functions"

3. **Prioritize Rules**
   - Put most important rules first
   - System applies rules in order

4. **Review Violations**
   - Check audit log regularly
   - Adjust rules based on violations

5. **Update Rules as Needed**
   - Rules should evolve with project
   - Version control rules changes

---

## TESTING USER INSTRUCTIONS

```bash
# Test instructions endpoint
curl -X POST http://localhost:8000/api/instructions \
  -H "Content-Type: application/json" \
  -d '{
    "rules": "Always ask for approval\nRequire tests\nUse TypeScript"
  }'

# Validate rules text
curl -X POST http://localhost:8000/api/instructions/validate \
  -H "Content-Type: application/json" \
  -d '{
    "rules_text": "Bad rule without colon"
  }'
```

---

## NEXT: Read 05_AGENT_INTEGRATION.md for agent coordination
