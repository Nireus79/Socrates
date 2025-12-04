"""
Concrete conflict checker implementations for Socratic RAG System
"""

from typing import Dict, List, Optional, Any

from socratic_system.models import ProjectContext, ConflictInfo
from .base import ConflictChecker
from .rules import CONFLICT_RULES, find_conflict_category


class TechStackConflictChecker(ConflictChecker):
    """Checks for technology stack conflicts"""

    def _extract_values(self, insights: Dict[str, Any]) -> Any:
        """Extract tech stack from insights"""
        return insights.get('tech_stack', [])

    def _get_existing_values(self, project: ProjectContext) -> List[str]:
        """Get existing tech stack from project"""
        return project.tech_stack

    def _find_conflict(
        self,
        new_value: str,
        existing_values: List[str],
        project: ProjectContext,
        current_user: str
    ) -> Optional[ConflictInfo]:
        """Check if new tech conflicts with existing tech"""
        for existing_value in existing_values:
            # Skip identical values - not a conflict if same tech is being added again
            if new_value.lower().strip() == existing_value.lower().strip():
                continue

            conflict_category = find_conflict_category(new_value, existing_value)
            if conflict_category:
                severity = 'high' if conflict_category in ['databases', 'languages'] else 'medium'
                suggestions = [
                    f"Consider if both {conflict_category} can coexist",
                    f"Research integration patterns between {new_value} and {existing_value}",
                    "Evaluate performance and maintenance implications",
                    "Consider team expertise with both technologies"
                ]
                return self._build_conflict_info(
                    'tech_stack',
                    existing_value,
                    new_value,
                    project,
                    current_user,
                    severity=severity,
                    suggestions=suggestions
                )
        return None


class RequirementsConflictChecker(ConflictChecker):
    """Checks for requirement conflicts using semantic analysis"""

    def _extract_values(self, insights: Dict[str, Any]) -> Any:
        """Extract requirements from insights"""
        return insights.get('requirements', [])

    def _get_existing_values(self, project: ProjectContext) -> List[str]:
        """Get existing requirements from project"""
        return project.requirements

    def _find_conflict(
        self,
        new_value: str,
        existing_values: List[str],
        project: ProjectContext,
        current_user: str
    ) -> Optional[ConflictInfo]:
        """Check if new requirement conflicts with existing requirements"""
        # Skip identical values - not a conflict if same requirement is being added again
        for existing_value in existing_values:
            if new_value.lower().strip() == existing_value.lower().strip():
                return None

        # Use Claude for semantic conflict detection
        semantic_conflicts = self._check_semantic_conflicts(
            new_value,
            existing_values,
            'requirements'
        )
        if semantic_conflicts:
            conflict_data = semantic_conflicts[0]
            return self._build_conflict_info(
                'requirements',
                conflict_data['existing'],
                new_value,
                project,
                current_user,
                severity=conflict_data.get('severity', 'medium'),
                suggestions=conflict_data.get('suggestions', [])
            )
        return None

    def _check_semantic_conflicts(
        self,
        new_requirement: str,
        existing_requirements: List[str],
        field_type: str
    ) -> List[Dict]:
        """Use Claude to detect semantic conflicts"""
        if not self.orchestrator:
            return []

        try:
            prompt = f"""Analyze if this new {field_type} item conflicts with existing {field_type}.

New item: {new_requirement}
Existing {field_type}: {', '.join(existing_requirements)}

Respond in JSON format:
{{
    "has_conflict": boolean,
    "conflicting_with": "which existing item conflicts",
    "severity": "low/medium/high",
    "explanation": "why they conflict",
    "suggestions": ["list", "of", "suggestions"]
}}

Only respond with valid JSON."""

            claude_client = self.orchestrator.claude_client
            response = claude_client.client.messages.create(
                model=claude_client.model,
                max_tokens=300,
                messages=[{"role": "user", "content": prompt}]
            )

            import json
            response_text = response.content[0].text.strip()
            # Remove markdown code blocks if present
            if response_text.startswith('```'):
                response_text = response_text.split('```')[1]
                if response_text.startswith('json'):
                    response_text = response_text[4:]
                response_text = response_text.strip()

            data = json.loads(response_text)

            if data.get('has_conflict'):
                return [{
                    'existing': data.get('conflicting_with', existing_requirements[0]),
                    'severity': data.get('severity', 'medium'),
                    'suggestions': data.get('suggestions', [])
                }]
        except Exception:
            pass

        return []


class GoalsConflictChecker(ConflictChecker):
    """Checks for goal conflicts"""

    def _extract_values(self, insights: Dict[str, Any]) -> Any:
        """Extract goals from insights"""
        return insights.get('goals', '')

    def _get_existing_values(self, project: ProjectContext) -> List[str]:
        """Get existing goals from project"""
        return [project.goals] if project.goals else []

    def _find_conflict(
        self,
        new_value: str,
        existing_values: List[str],
        project: ProjectContext,
        current_user: str
    ) -> Optional[ConflictInfo]:
        """Check if new goal conflicts with existing goal"""
        if not existing_values:
            return None

        existing_goal = existing_values[0]
        # Exact match - no conflict
        if new_value.lower().strip() == existing_goal.lower().strip():
            return None

        # Use semantic analysis
        semantic_conflicts = self._check_semantic_conflicts(
            new_value,
            existing_values,
            'goals'
        )
        if semantic_conflicts:
            return self._build_conflict_info(
                'goals',
                existing_goal,
                new_value,
                project,
                current_user,
                severity='high'
            )
        return None

    def _check_semantic_conflicts(
        self,
        new_goal: str,
        existing_goals: List[str],
        field_type: str
    ) -> List[Dict]:
        """Use Claude to detect semantic conflicts in goals"""
        if not self.orchestrator:
            return []

        try:
            prompt = f"""Analyze if these goals conflict or contradict each other.

New goal: {new_goal}
Existing goal: {existing_goals[0] if existing_goals else 'None'}

Respond in JSON:
{{"has_conflict": boolean, "severity": "low/medium/high"}}"""

            claude_client = self.orchestrator.claude_client
            response = claude_client.client.messages.create(
                model=claude_client.model,
                max_tokens=100,
                messages=[{"role": "user", "content": prompt}]
            )

            import json
            response_text = response.content[0].text.strip()
            data = json.loads(response_text)

            if data.get('has_conflict'):
                return [{'severity': data.get('severity', 'medium')}]
        except Exception:
            pass

        return []


class ConstraintsConflictChecker(ConflictChecker):
    """Checks for constraint conflicts"""

    def _extract_values(self, insights: Dict[str, Any]) -> Any:
        """Extract constraints from insights"""
        return insights.get('constraints', [])

    def _get_existing_values(self, project: ProjectContext) -> List[str]:
        """Get existing constraints from project"""
        return project.constraints

    def _find_conflict(
        self,
        new_value: str,
        existing_values: List[str],
        project: ProjectContext,
        current_user: str
    ) -> Optional[ConflictInfo]:
        """Check if new constraint conflicts with existing constraints"""
        # Skip identical values - not a conflict if same constraint is being added again
        for existing_value in existing_values:
            if new_value.lower().strip() == existing_value.lower().strip():
                return None

        semantic_conflicts = self._check_semantic_conflicts(
            new_value,
            existing_values,
            'constraints'
        )
        if semantic_conflicts:
            conflict_data = semantic_conflicts[0]
            return self._build_conflict_info(
                'constraints',
                conflict_data['existing'],
                new_value,
                project,
                current_user,
                severity=conflict_data.get('severity', 'medium'),
                suggestions=conflict_data.get('suggestions', [])
            )
        return None

    def _check_semantic_conflicts(
        self,
        new_constraint: str,
        existing_constraints: List[str],
        field_type: str
    ) -> List[Dict]:
        """Use Claude to detect semantic conflicts in constraints"""
        if not self.orchestrator:
            return []

        try:
            prompt = f"""Analyze if this new {field_type} item conflicts with existing {field_type}.

New item: {new_constraint}
Existing {field_type}: {', '.join(existing_constraints)}

Respond in JSON:
{{"has_conflict": boolean, "conflicting_with": "which one", "severity": "low/medium/high"}}"""

            claude_client = self.orchestrator.claude_client
            response = claude_client.client.messages.create(
                model=claude_client.model,
                max_tokens=150,
                messages=[{"role": "user", "content": prompt}]
            )

            import json
            response_text = response.content[0].text.strip()
            data = json.loads(response_text)

            if data.get('has_conflict'):
                return [{
                    'existing': data.get('conflicting_with', existing_constraints[0] if existing_constraints else 'unknown'),
                    'severity': data.get('severity', 'medium')
                }]
        except Exception:
            pass

        return []
