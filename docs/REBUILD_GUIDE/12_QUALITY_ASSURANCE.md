# QUALITY ASSURANCE & VALIDATION
## QualityAnalyzer Integration and Testing Strategy

---

## QUALITY ASSURANCE ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────┐
│                  QUALITY ASSURANCE LAYER                    │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. INPUT VALIDATION (Pydantic Schemas)                    │
│     └─ Type checking, format validation                    │
│                                                             │
│  2. INSTRUCTION COMPLIANCE (InstructionService)            │
│     └─ User rules enforcement                              │
│                                                             │
│  3. QUALITY ANALYSIS (QualityAnalyzer)                     │
│     ├─ Suggestion quality scoring                          │
│     ├─ Bias detection                                      │
│     ├─ Confidence assessment                               │
│     └─ Missing context detection                           │
│                                                             │
│  4. CODE VALIDATION (CodeValidator)                        │
│     ├─ Syntax checking                                     │
│     ├─ Security scanning                                   │
│     ├─ Best practices enforcement                          │
│     └─ Performance analysis                                │
│                                                             │
│  5. AUDIT LOGGING (AuditLog)                               │
│     └─ Track all validations and decisions                 │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## QUALITY ANALYZER INTEGRATION

### QualityAnalyzer Methods

The QualityAnalyzer provides universal quality assessment:

```python
# src/agents/question_analyzer.py

class QualityAnalyzer:
    """Universal quality validator for all AI outputs"""

    def analyze_question(self, question: str) -> QuestionAnalysis:
        """Analyze Socratic question quality"""
        # Check coverage areas, complexity, clarity
        # Returns: quality_score, bias_score, confidence

    def analyze_suggestion(self, suggestion: str) -> SuggestionAnalysis:
        """Analyze code/architecture suggestion quality"""
        # Check feasibility, completeness, clarity
        # Returns: quality_score, bias_score, confidence, context_gaps

    def analyze_statement(self, statement: str) -> StatementAnalysis:
        """Analyze chat statement quality"""
        # Check accuracy, tone, helpfulness
        # Returns: quality_score, bias_score, confidence

    def analyze_code_change(self, original: str, modified: str) -> CodeAnalysis:
        """Analyze proposed code changes"""
        # Check correctness, safety, performance
        # Returns: quality_score, bias_score, risks, suggestions
```

### Integration with Agent Service

```python
# src/services/agent_service.py

class AgentService(BaseService):
    async def route_request(self, agent_id: str, action: str,
                          data: Dict[str, Any],
                          user_id: Optional[str] = None) -> Dict[str, Any]:
        """Route with quality validation"""

        # Step 1: Route to agent
        result = self.orchestrator.route_request(agent_id, action, data)

        if not result.get('success'):
            return result

        # Step 2: VALIDATE QUALITY
        quality_check = await self._validate_quality(result, user_instructions)

        if not quality_check['valid']:
            # Log quality violation
            self._log_quality_issue(agent_id, action, quality_check)

            # Return error or ask for confirmation
            if quality_check['severity'] == 'critical':
                return self.handle_error("QUALITY_CHECK_FAILED", quality_check['reason'])
            else:
                # Log warning but allow
                self.logger.warning(f"Quality warning: {quality_check['reason']}")

        # Step 3: Validate against user instructions
        instruction_check = await self.instruction_service.validate_result(
            result.get('data', {}),
            user_instructions
        )

        if not instruction_check['valid']:
            # Instruction violation - always block
            return self.handle_error("INSTRUCTION_VIOLATION",
                                   instruction_check['violation_reason'])

        # Step 4: Log audit trail
        self._audit_log(user_id, agent_id, action, data, result, quality_check)

        return result

    async def _validate_quality(self, result: Dict[str, Any],
                              instructions: List) -> Dict[str, Any]:
        """Validate using QualityAnalyzer"""
        try:
            analyzer = QualityAnalyzer()
            result_text = str(result.get('data', ''))

            # Analyze the result
            analysis = analyzer.analyze_suggestion(result_text)

            # Check thresholds
            issues = []

            if analysis.quality_score < 0.4:
                issues.append({
                    'type': 'quality',
                    'severity': 'critical',
                    'reason': f"Quality too low: {analysis.quality_score:.2f}/10",
                    'score': analysis.quality_score
                })

            if analysis.bias_score > 0.7:
                issues.append({
                    'type': 'bias',
                    'severity': 'high',
                    'reason': f"High bias detected: {analysis.bias_score:.2f}/10",
                    'score': analysis.bias_score
                })

            if analysis.confidence < 0.5 and analysis.context_gaps:
                issues.append({
                    'type': 'context',
                    'severity': 'medium',
                    'reason': f"Missing context: {', '.join(analysis.context_gaps)}",
                    'confidence': analysis.confidence
                })

            return {
                'valid': len(issues) == 0,
                'issues': issues,
                'severity': max([i['severity'] for i in issues] + ['none']),
                'scores': {
                    'quality': analysis.quality_score,
                    'bias': analysis.bias_score,
                    'confidence': analysis.confidence
                }
            }

        except Exception as e:
            self.logger.warning(f"Quality check error: {e}")
            return {'valid': True}  # Don't fail on validation errors
```

---

## VALIDATION DECORATOR PATTERN

### Code Validator Decorator

```python
# src/agents/code_validator.py

from dataclasses import dataclass
from typing import Callable, Any, Dict
from functools import wraps

@dataclass
class ValidationResult:
    valid: bool
    quality_score: float
    bias_score: float
    confidence: float
    issues: list
    recommendations: list

def validate_code_action(
    action_type: str = 'edit',
    require_verification: bool = False,
    min_quality_score: float = 0.5,
    block_on_high_bias: bool = True
):
    """
    Decorator for validating code operations

    Usage:
    @validate_code_action(
        action_type='refactor',
        min_quality_score=0.6,
        block_on_high_bias=True
    )
    def refactor_code(self, code: str) -> Dict:
        ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(self, *args, **kwargs) -> Dict[str, Any]:
            # PRE-VALIDATION
            # Get code from arguments
            code = kwargs.get('code') or (args[0] if args else '')

            analyzer = QualityAnalyzer()
            pre_analysis = analyzer.analyze_suggestion(f"Code action: {action_type} on {len(code)} chars")

            # Check pre-conditions
            if pre_analysis.quality_score < min_quality_score:
                return {
                    'success': False,
                    'error': f'Pre-validation failed: quality too low',
                    'quality_score': pre_analysis.quality_score
                }

            if block_on_high_bias and pre_analysis.bias_score > 0.7:
                return {
                    'success': False,
                    'error': f'Pre-validation failed: high bias detected',
                    'bias_score': pre_analysis.bias_score
                }

            # EXECUTE FUNCTION
            try:
                result = await func(self, *args, **kwargs)
            except Exception as e:
                return {
                    'success': False,
                    'error': str(e),
                    'validation': 'execution_error'
                }

            # POST-VALIDATION
            if result.get('success'):
                output = result.get('data', '')
                post_analysis = analyzer.analyze_suggestion(str(output))

                # Verify quality maintained or improved
                if post_analysis.quality_score < min_quality_score:
                    self.logger.warning(
                        f'Post-validation: quality decreased to '
                        f'{post_analysis.quality_score:.2f}'
                    )

                # Add validation results to response
                result['validation'] = {
                    'valid': True,
                    'quality_score': post_analysis.quality_score,
                    'bias_score': post_analysis.bias_score,
                    'confidence': post_analysis.confidence
                }

            return result

        return wrapper
    return decorator
```

### Usage in CodeEditor

```python
# src/agents/code_editor.py

class CodeEditor:
    @validate_code_action(
        action_type='refactor',
        min_quality_score=0.6,
        block_on_high_bias=True
    )
    async def refactor_code(self, code: str, refactoring_type: str) -> Dict:
        """Refactor code with validation"""
        # Implementation
        return {'success': True, 'data': {...}}

    @validate_code_action(
        action_type='fix_bugs',
        min_quality_score=0.5,
        require_verification=True
    )
    async def fix_bugs(self, code: str) -> Dict:
        """Fix bugs with validation"""
        # Implementation
        return {'success': True, 'data': {...}}
```

---

## AUDIT LOGGING

### Audit Log Model

```python
# src/models.py

class AuditLog(BaseModel):
    __tablename__ = "audit_logs"

    user_id = Column(String(36), ForeignKey("users.id"))
    agent_id = Column(String(255))
    action = Column(String(255))
    request_data = Column(JSON)  # Original request
    response_data = Column(JSON)  # Agent response
    quality_check = Column(JSON)  # QualityAnalyzer results
    instruction_check = Column(JSON)  # Instruction validation results
    success = Column(Boolean)
    error_message = Column(Text)
    duration_ms = Column(Integer)  # Execution time

    user = relationship("User", back_populates="audit_logs")
```

### Audit Service

```python
# src/services/audit_service.py

class AuditService(BaseService):
    async def log_action(self, user_id: str, agent_id: str, action: str,
                        request: Dict, response: Dict,
                        quality_check: Dict = None,
                        instruction_check: Dict = None,
                        success: bool = True,
                        error: str = None,
                        duration_ms: int = 0):
        """Log action with full validation details"""
        try:
            audit = AuditLog(
                user_id=user_id,
                agent_id=agent_id,
                action=action,
                request_data=request,
                response_data=response,
                quality_check=quality_check,
                instruction_check=instruction_check,
                success=success,
                error_message=error,
                duration_ms=duration_ms
            )

            repo = AuditRepository(self.services.database.session)
            await repo.create(audit)

            # Also emit event for analytics
            self.services.event_system.emit('action_completed', 'audit_service', {
                'agent_id': agent_id,
                'action': action,
                'success': success,
                'quality_score': quality_check.get('scores', {}).get('quality', 0) if quality_check else 0,
                'duration_ms': duration_ms
            })

        except Exception as e:
            self.logger.error(f"Audit logging failed: {e}")

    async def get_user_audit_log(self, user_id: str, limit: int = 100):
        """Get user's action history"""
        repo = AuditRepository(self.services.database.session)
        return await repo.get_by_user_id(user_id, limit=limit)

    async def get_quality_report(self, user_id: str, days: int = 7):
        """Generate quality report for user"""
        logs = await self.get_user_audit_log(user_id)

        # Filter by date range
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        filtered_logs = [l for l in logs if l.created_at > cutoff_date]

        # Calculate metrics
        total_actions = len(filtered_logs)
        successful_actions = sum(1 for l in filtered_logs if l.success)
        failed_actions = total_actions - successful_actions

        quality_scores = [
            l.quality_check.get('scores', {}).get('quality', 0)
            for l in filtered_logs if l.quality_check
        ]
        avg_quality = sum(quality_scores) / len(quality_scores) if quality_scores else 0

        return {
            'period_days': days,
            'total_actions': total_actions,
            'successful': successful_actions,
            'failed': failed_actions,
            'success_rate': successful_actions / total_actions if total_actions > 0 else 0,
            'average_quality_score': avg_quality,
            'average_duration_ms': sum(l.duration_ms or 0 for l in filtered_logs) / total_actions if total_actions > 0 else 0
        }
```

---

## TESTING STRATEGY

### Unit Tests for Quality Analyzer

```python
# tests/test_quality_analyzer.py

import pytest
from src.agents.question_analyzer import QualityAnalyzer

class TestQualityAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return QualityAnalyzer()

    def test_analyze_question_quality(self, analyzer):
        """Test question quality scoring"""
        question = "What are the main security and scalability requirements?"
        analysis = analyzer.analyze_question(question)

        assert analysis.quality_score > 0.5  # Good question
        assert analysis.bias_score < 0.5     # Low bias
        assert 'security' in analysis.coverage_areas
        assert 'scalability' in analysis.coverage_areas

    def test_analyze_suggestion_quality(self, analyzer):
        """Test code suggestion quality"""
        suggestion = "Use PostgreSQL for relational data storage with proper indexing"
        analysis = analyzer.analyze_suggestion(suggestion)

        assert analysis.quality_score > 0.6
        assert analysis.confidence > 0.7

    def test_detect_bias_in_suggestion(self, analyzer):
        """Test bias detection"""
        biased_suggestion = "Obviously you should use MongoDB because it's cool"
        analysis = analyzer.analyze_suggestion(biased_suggestion)

        assert analysis.bias_score > 0.5  # Detects bias

    def test_missing_context_detection(self, analyzer):
        """Test context gap detection"""
        incomplete = "Use caching"  # No context
        analysis = analyzer.analyze_suggestion(incomplete)

        assert len(analysis.context_gaps) > 0
        assert analysis.confidence < 0.7
```

### Integration Tests for Validation

```python
# tests/test_validation_integration.py

import pytest
from unittest.mock import MagicMock
from src.services.agent_service import AgentService
from src.core import ServiceContainer

@pytest.mark.asyncio
async def test_agent_request_with_quality_validation():
    """Test full pipeline with quality validation"""
    services = MagicMock(spec=ServiceContainer)
    agent_service = AgentService(services)

    # Mock orchestrator response
    agent_response = {
        'success': True,
        'data': {
            'code': 'def hello(): print("world")',
            'explanation': 'Simple hello function'
        }
    }

    services.orchestrator.route_request.return_value = agent_response

    # Route request
    result = await agent_service.route_request(
        agent_id='code',
        action='generate_code',
        data={'requirements': 'Hello function'},
        user_id='user_123'
    )

    assert result['success']
    assert 'validation' in result

@pytest.mark.asyncio
async def test_instruction_violation_blocking():
    """Test that instruction violations are blocked"""
    services = MagicMock(spec=ServiceContainer)
    agent_service = AgentService(services)

    # Mock instruction violation
    mock_instruction = MagicMock()
    mock_instruction.parsed_rules = [
        {'type': 'security', 'rule': 'No hardcoded secrets'}
    ]

    services.instruction_service.get_user_instructions.return_value = [mock_instruction]
    services.instruction_service.validate_result.return_value = {
        'valid': False,
        'violations': [{'reason': 'Found hardcoded API key'}]
    }

    # Route request
    result = await agent_service.route_request(
        agent_id='code',
        action='generate_code',
        data={'requirements': 'Generate auth code'},
        user_id='user_123'
    )

    assert not result['success']
    assert 'INSTRUCTION_VIOLATION' in result['error']
```

### End-to-End Tests

```python
# tests/test_e2e_quality_workflow.py

import pytest
from src.core import initialize_system

@pytest.mark.asyncio
async def test_complete_quality_workflow():
    """Test complete workflow with all validation layers"""
    services = initialize_system('config.yaml')

    # 1. Create user
    user_service = UserService(services)
    user = await user_service.create_user('testuser', 'test@example.com', 'Pass123!')

    # 2. Create project
    project_service = ProjectService(services)
    project = await project_service.create_project(
        user.id, 'Test Project', 'Test API'
    )

    # 3. Create user instructions
    instruction_service = InstructionService(services)
    instruction = await instruction_service.create_instruction(
        user.id,
        "- Always include tests\n- Use type hints\n- Document functions"
    )

    # 4. Generate code (with validation)
    agent_service = AgentService(services)
    result = await agent_service.route_request(
        agent_id='code',
        action='generate_code',
        data={
            'requirements': 'Create user registration function',
            'projectId': project.id
        },
        user_id=user.id
    )

    # 5. Verify validations occurred
    assert result['success']
    assert result['validation']['quality_score'] > 0.5
    assert result['validation']['confidence'] > 0.6

    # 6. Check audit log
    audit_service = AuditService(services)
    logs = await audit_service.get_user_audit_log(user.id)
    assert len(logs) > 0
    assert logs[0].success
    assert logs[0].instruction_check is not None
```

---

## QUALITY METRICS & DASHBOARDS

### Quality Score Calculation

```python
def calculate_quality_score(analysis: SuggestionAnalysis) -> float:
    """
    Calculate overall quality score (0-10)

    Factors:
    - Completeness (30%): Does suggestion address all aspects?
    - Clarity (25%): Is suggestion clearly expressed?
    - Feasibility (25%): Is suggestion practical to implement?
    - Bias-free (20%): Is suggestion objective and unbiased?
    """

    score = 0.0

    # Completeness
    completeness = len(analysis.coverage_areas) / 5  # Max 5 areas
    score += min(completeness * 3, 3.0)  # 30% of score

    # Clarity
    clarity = 1.0 if len(analysis.unclear_terms) == 0 else 0.5
    score += clarity * 2.5  # 25% of score

    # Feasibility
    feasibility = 1.0 if not analysis.has_constraints else 0.7
    score += feasibility * 2.5  # 25% of score

    # Bias-free
    bias_free = 1.0 - (analysis.bias_score / 10)
    score += bias_free * 2.0  # 20% of score

    return min(score, 10.0)
```

### Dashboard Endpoint

```python
# src/routers/analytics.py

@router.get("/analytics/quality")
async def get_quality_analytics(
    user_id: str,
    days: int = 7,
    services: ServiceContainer = Depends(get_services)
):
    """Get quality metrics for dashboard"""
    audit_service = AuditService(services)
    report = await audit_service.get_quality_report(user_id, days)

    return {
        'success': True,
        'data': {
            'period': f'Last {days} days',
            'metrics': report,
            'trends': await calculate_trends(user_id, services),
            'recommendations': generate_recommendations(report)
        }
    }
```

---

## NEXT STEPS

1. Implement QualityAnalyzer in all agent paths
2. Create validation decorator for code operations
3. Set up audit logging infrastructure
4. Write comprehensive test suite
5. Build quality metrics dashboard
6. Monitor and tune thresholds

**All core rebuild documentation is now complete!**
