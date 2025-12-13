"""
Analytics calculator for maturity tracking insights and recommendations.

Pure computation logic for analyzing project maturity data and generating
actionable recommendations for improvement.
"""

import logging
from typing import Dict, List

from socratic_system.core.project_categories import get_phase_categories
from socratic_system.models import ProjectContext

logger = logging.getLogger(__name__)


class AnalyticsCalculator:
    """
    Pure analytics computation logic for maturity tracking.

    Analyzes maturity data to provide insights, recommendations, and trends.
    No side effects - all methods are pure computations based on input data.
    """

    def __init__(self, project_type: str = "software"):
        """
        Initialize analytics calculator for a project type.

        Args:
            project_type: Type of project (software, business, creative, etc.)
        """
        logger.debug(f"Initializing AnalyticsCalculator with project_type={project_type}")
        self.project_type = project_type
        self.phase_categories = get_phase_categories(project_type)
        logger.info(
            f"AnalyticsCalculator initialized with {len(self.phase_categories)} phases for project type: {project_type}"
        )

    # ============================================================================
    # Category Analysis Methods
    # ============================================================================

    def analyze_category_performance(self, project: ProjectContext) -> Dict:
        """
        Analyze category strengths/weaknesses across current phase.

        Returns:
            Dict with weak_categories, strong_categories, missing_categories, balance
        """
        logger.debug(f"Analyzing category performance for phase: {project.phase}")

        current_phase = project.phase
        category_scores = project.category_scores.get(current_phase, {})

        weak_categories = []
        strong_categories = []
        missing_categories = []

        for category, score_data in category_scores.items():
            if isinstance(score_data, dict):
                current = score_data.get("current_score", 0.0)
                target = score_data.get("target_score", 1.0)
            else:
                continue

            percentage = (current / target * 100) if target > 0 else 0.0
            spec_count = score_data.get("spec_count", 0) if isinstance(score_data, dict) else 0

            if spec_count == 0:
                missing_categories.append(category)
                logger.debug(f"Category '{category}' is missing (0 specs)")
            elif percentage < 30:
                weak_categories.append(
                    {
                        "category": category,
                        "percentage": percentage,
                        "current": current,
                        "target": target,
                        "spec_count": spec_count,
                    }
                )
                logger.debug(f"Category '{category}' is weak: {percentage:.1f}%")
            elif percentage > 70:
                strong_categories.append(
                    {
                        "category": category,
                        "percentage": percentage,
                        "current": current,
                        "target": target,
                        "spec_count": spec_count,
                    }
                )
                logger.debug(f"Category '{category}' is strong: {percentage:.1f}%")

        # Sort by percentage
        weak_categories.sort(key=lambda x: x["percentage"])
        strong_categories.sort(key=lambda x: x["percentage"], reverse=True)

        logger.info(
            f"Category analysis: {len(strong_categories)} strong, {len(weak_categories)} weak, {len(missing_categories)} missing"
        )

        # Analyze balance
        balance = self.analyze_category_balance(project)

        return {
            "phase": current_phase,
            "weak_categories": weak_categories,
            "strong_categories": strong_categories,
            "missing_categories": missing_categories,
            "balance": balance,
        }

    def identify_weak_categories(self, project: ProjectContext) -> List[str]:
        """Find categories consistently scoring < 30% in current phase."""
        logger.debug(f"Identifying weak categories for phase: {project.phase}")
        current_phase = project.phase
        category_scores = project.category_scores.get(current_phase, {})

        weak = []
        for category, score_data in category_scores.items():
            if isinstance(score_data, dict):
                current = score_data.get("current_score", 0.0)
                target = score_data.get("target_score", 1.0)
                percentage = (current / target * 100) if target > 0 else 0.0

                if percentage < 30:
                    weak.append(category)

        logger.info(f"Found {len(weak)} weak categories (< 30%) in {current_phase}: {weak}")
        return weak

    def identify_strong_categories(self, project: ProjectContext) -> List[str]:
        """Find categories consistently scoring > 70% in current phase."""
        logger.debug(f"Identifying strong categories for phase: {project.phase}")
        current_phase = project.phase
        category_scores = project.category_scores.get(current_phase, {})

        strong = []
        for category, score_data in category_scores.items():
            if isinstance(score_data, dict):
                current = score_data.get("current_score", 0.0)
                target = score_data.get("target_score", 1.0)
                percentage = (current / target * 100) if target > 0 else 0.0

                if percentage > 70:
                    strong.append(category)

        logger.info(f"Found {len(strong)} strong categories (> 70%) in {current_phase}: {strong}")
        return strong

    def analyze_category_balance(self, project: ProjectContext) -> Dict:
        """
        Detect over/under investment in categories.

        Returns:
            Dict with status (BALANCED/IMBALANCED) and recommendations
        """
        logger.debug(f"Analyzing category balance for phase: {project.phase}")
        current_phase = project.phase
        category_scores = project.category_scores.get(current_phase, {})

        if not category_scores:
            logger.debug(f"No category scores found for phase {current_phase}")
            return {"status": "UNKNOWN", "messages": []}

        # Calculate percentages for all categories
        percentages = []
        for category, score_data in category_scores.items():
            if isinstance(score_data, dict):
                current = score_data.get("current_score", 0.0)
                target = score_data.get("target_score", 1.0)
                percentage = (current / target * 100) if target > 0 else 0.0
                percentages.append((category, percentage))

        if not percentages:
            logger.debug("No percentage data available for balance analysis")
            return {"status": "UNKNOWN", "messages": []}

        max_pct = max(p[1] for p in percentages)
        min_pct = min(p[1] for p in percentages)
        gap = max_pct - min_pct

        logger.debug(f"Balance gap: {gap:.1f}% (max: {max_pct:.1f}%, min: {min_pct:.1f}%)")

        messages = []

        if gap > 50:
            status = "IMBALANCED"
            max_cat = [p[0] for p in percentages if p[1] == max_pct][0]
            min_cat = [p[0] for p in percentages if p[1] == min_pct][0]
            logger.warning(
                f"Category balance imbalanced: {max_cat}={max_pct:.0f}% vs {min_cat}={min_pct:.0f}%"
            )
            messages.append(
                f"{max_cat.replace('_', ' ').title()} well-developed ({max_pct:.0f}%) "
                f"but {min_cat.replace('_', ' ')} weak ({min_pct:.0f}%)"
            )
            messages.append("Recommend balancing investment across categories")
        else:
            status = "BALANCED"
            logger.debug(f"Category balance is good (gap: {gap:.0f}%)")
            messages.append(f"Good category balance (gap: {gap:.0f}%)")

        return {"status": status, "messages": messages}

    def get_missing_categories(self, project: ProjectContext) -> Dict[str, List[str]]:
        """Get categories with 0 specs per phase."""
        logger.debug("Identifying missing categories across all phases")
        missing = {}

        for phase in ["discovery", "analysis", "design", "implementation"]:
            phase_categories = self.phase_categories.get(phase, {})
            category_scores = project.category_scores.get(phase, {})

            missing_in_phase = []
            for category in phase_categories.keys():
                if category not in category_scores:
                    missing_in_phase.append(category)
                else:
                    score_data = category_scores.get(category, {})
                    if isinstance(score_data, dict):
                        if score_data.get("spec_count", 0) == 0:
                            missing_in_phase.append(category)

            if missing_in_phase:
                missing[phase] = missing_in_phase
                logger.warning(f"Phase {phase} has {len(missing_in_phase)} missing categories")

        logger.info(
            f"Total missing categories across phases: {sum(len(v) for v in missing.values())}"
        )
        return missing

    # ============================================================================
    # Progression Analysis Methods
    # ============================================================================

    def calculate_velocity(self, project: ProjectContext) -> float:
        """
        Calculate average maturity points gained per Q&A session.

        Returns:
            Float: Average points per session
        """
        logger.debug("Calculating velocity from maturity history")

        if not project.maturity_history:
            logger.debug("No maturity history available, velocity = 0.0")
            return 0.0

        qa_events = [
            e for e in project.maturity_history if e.get("event_type") == "response_processed"
        ]

        if not qa_events:
            logger.debug("No Q&A response events found, velocity = 0.0")
            return 0.0

        total_gain = sum(e.get("delta", 0.0) for e in qa_events)
        velocity = total_gain / len(qa_events) if qa_events else 0.0
        logger.info(
            f"Calculated velocity: {velocity:.2f} points/session from {len(qa_events)} Q&A sessions (total gain: {total_gain:.1f})"
        )
        return velocity

    def analyze_progression_trends(self, project: ProjectContext) -> Dict:
        """
        Analyze maturity progression over time.

        Returns:
            Dict with velocity, trends, insights
        """
        logger.debug(f"Analyzing progression trends for project in phase: {project.phase}")

        velocity = self.calculate_velocity(project)

        qa_events = [
            e for e in project.maturity_history if e.get("event_type") == "response_processed"
        ]

        logger.debug(f"Analyzed {len(qa_events)} Q&A events for trend analysis")

        insights = self._generate_insights(qa_events, velocity)

        result = {
            "velocity": velocity,
            "total_sessions": len(qa_events),
            "current_phase": project.phase,
            "current_score": project.phase_maturity_scores.get(project.phase, 0.0),
            "insights": insights,
        }

        logger.info(
            f"Progression trend analysis: {len(qa_events)} sessions, velocity={velocity:.2f}, score={result['current_score']:.1f}%"
        )
        return result

    def identify_plateaus(self, project: ProjectContext) -> List[Dict]:
        """Find periods where maturity stagnates."""
        logger.debug("Identifying plateau periods in maturity progression")

        qa_events = [
            e for e in project.maturity_history if e.get("event_type") == "response_processed"
        ]

        if len(qa_events) < 3:
            logger.debug(
                f"Not enough Q&A events ({len(qa_events)}) to identify plateaus (need >= 3)"
            )
            return []

        plateaus = []
        consecutive_low_delta = 0
        plateau_start = None

        for i, event in enumerate(qa_events):
            delta = event.get("delta", 0.0)

            if delta < 0.5:  # Threshold for stagnation
                if consecutive_low_delta == 0:
                    plateau_start = i
                consecutive_low_delta += 1
            else:
                if consecutive_low_delta >= 2:  # At least 2 stagnant sessions
                    plateau_info = {
                        "start_session": plateau_start + 1,
                        "duration": consecutive_low_delta,
                        "avg_delta": sum(e.get("delta", 0) for e in qa_events[plateau_start:i])
                        / consecutive_low_delta,
                    }
                    plateaus.append(plateau_info)
                    logger.warning(
                        f"Plateau detected: Q{plateau_info['start_session']} for {plateau_info['duration']} sessions, avg_delta={plateau_info['avg_delta']:.2f}"
                    )
                consecutive_low_delta = 0

        logger.info(f"Found {len(plateaus)} plateau periods in progression")
        return plateaus

    # ============================================================================
    # Recommendation Methods
    # ============================================================================

    def generate_recommendations(self, project: ProjectContext) -> List[Dict]:
        """
        Generate prioritized recommendations based on weak areas.

        Returns:
            List of recommendation dicts sorted by priority
        """
        logger.debug(f"Generating recommendations for phase: {project.phase}")

        recommendations = []
        current_phase = project.phase
        category_scores = project.category_scores.get(current_phase, {})
        phase_categories = self.phase_categories.get(current_phase, {})

        # 1. Weak categories
        weak_count = 0
        for category, score_data in category_scores.items():
            if isinstance(score_data, dict):
                current = score_data.get("current_score", 0.0)
                target = score_data.get("target_score", 1.0)
                percentage = (current / target * 100) if target > 0 else 0.0
                spec_count = score_data.get("spec_count", 0)

                if percentage < 30:
                    priority = "high" if percentage < 20 else "medium"
                    gap = 70.0 - percentage
                    weak_count += 1

                    logger.debug(
                        f"Adding weak category recommendation: {category} ({percentage:.1f}%), priority={priority}, gap={gap:.1f}"
                    )

                    recommendations.append(
                        {
                            "priority": priority,
                            "category": category,
                            "phase": current_phase,
                            "current": percentage,
                            "target": 70.0,
                            "gap": gap,
                            "spec_count": spec_count,
                            "action": self._generate_action_for_category(category),
                        }
                    )

        logger.debug(f"Found {weak_count} weak categories (< 30%)")

        # 2. Missing categories
        missing_count = 0
        for category, _target in phase_categories.items():
            if category not in category_scores:
                missing_count += 1
                logger.debug(f"Adding missing category recommendation: {category}")
                recommendations.append(
                    {
                        "priority": "high",
                        "category": category,
                        "phase": current_phase,
                        "current": 0.0,
                        "target": 70.0,
                        "gap": 70.0,
                        "spec_count": 0,
                        "action": self._generate_action_for_category(category),
                    }
                )
            elif isinstance(category_scores.get(category), dict):
                if category_scores[category].get("spec_count", 0) == 0:
                    missing_count += 1
                    logger.debug(f"Adding zero-spec category recommendation: {category}")
                    recommendations.append(
                        {
                            "priority": "high",
                            "category": category,
                            "phase": current_phase,
                            "current": 0.0,
                            "target": 70.0,
                            "gap": 70.0,
                            "spec_count": 0,
                            "action": self._generate_action_for_category(category),
                        }
                    )

        logger.debug(f"Found {missing_count} missing/zero-spec categories")

        # 3. Balance issues
        balance = self.analyze_category_balance(project)
        if balance.get("status") == "IMBALANCED":
            logger.debug("Adding balance recommendation due to imbalanced category distribution")
            recommendations.append(
                {
                    "priority": "medium",
                    "category": "balance",
                    "phase": current_phase,
                    "current": 0.0,
                    "target": 0.0,
                    "gap": 0.0,
                    "spec_count": None,
                    "action": "Focus on weaker categories to create balanced coverage",
                }
            )

        # Sort by priority (high first) and gap (largest first)
        recommendations.sort(key=lambda r: (r["priority"] != "high", -r["gap"]))

        final_count = min(len(recommendations), 10)
        logger.info(
            f"Generated {len(recommendations)} recommendations, returning top {final_count}"
        )
        return recommendations[:10]  # Top 10 recommendations

    def suggest_next_questions(self, project: ProjectContext, count: int = 5) -> List[str]:
        """Suggest questions targeting weak categories."""
        logger.debug(f"Suggesting next {count} questions for phase: {project.phase}")

        recommendations = self.generate_recommendations(project)
        questions = []

        for rec in recommendations[:count]:
            if rec["category"] == "balance":
                logger.debug("Skipping balance category in question generation")
                continue

            question = self._generate_question_for_category(rec["category"])
            if question:
                questions.append(question)
                logger.debug(
                    f"Generated question for category '{rec['category']}': {question[:60]}..."
                )

        logger.info(f"Generated {len(questions)} suggested questions targeting weak areas")
        return questions

    # ============================================================================
    # Helper Methods
    # ============================================================================

    def _generate_action_for_category(self, category: str) -> str:
        """Generate specific actionable advice for a category."""
        actions = {
            "goals": "Clearly define what you want to achieve with this project",
            "problem_definition": "Describe the core problem your project solves",
            "target_audience": "Identify who will use or benefit from your project",
            "competitive_analysis": "Research existing solutions and competitors",
            "scope": "Define what's included and excluded from your project",
            "constraints": "List technical, budget, time, or resource limitations",
            "requirements": "Detail functional and non-functional requirements",
            "tech_stack": "Specify technologies, frameworks, and tools to use",
            "security": "Address authentication, authorization, and data protection",
            "performance": "Define speed, scalability, and efficiency requirements",
            "testing_strategy": "Plan testing approach and quality assurance",
            "scalability": "Address growth and scaling considerations",
            "integrations": "Specify external systems and integrations needed",
            "data_management": "Define data storage, retention, and management",
            "architecture": "Design system structure and component relationships",
            "design_patterns": "Define reusable design patterns and structures",
            "code_organization": "Plan code organization and module structure",
            "api_design": "Define endpoints, data formats, and interfaces",
            "workflow": "Design user workflows and interaction flows",
            "error_handling": "Plan error handling and recovery strategies",
            "state_management": "Define state management and data flow",
            "ui_ux": "Plan user interface and user experience design",
            "deployment": "Plan hosting, CI/CD, and release strategy",
            "monitoring": "Establish logging, metrics, and alerting systems",
            "documentation": "Create comprehensive project documentation",
            "devops": "Define DevOps practices and infrastructure",
            "maintenance": "Plan ongoing maintenance and support",
            "rollback_strategy": "Define rollback and disaster recovery plans",
            "performance_optimization": "Optimize performance and efficiency",
        }

        return actions.get(category, f"Provide more details about {category.replace('_', ' ')}")

    def _generate_question_for_category(self, category: str) -> str:
        """Generate a Socratic question targeting a category."""
        questions = {
            "goals": "What are the top 3 objectives you want to achieve?",
            "problem_definition": "What specific problem does your project solve?",
            "target_audience": "Who are the primary users or beneficiaries?",
            "competitive_analysis": "What similar solutions exist, and how is yours different?",
            "scope": "What features are must-haves vs. nice-to-haves?",
            "constraints": "What limitations (time, budget, tech) do you have?",
            "requirements": "What must the system do to be considered successful?",
            "tech_stack": "Which technologies or frameworks are you considering?",
            "security": "How will you protect user data and prevent unauthorized access?",
            "performance": "What are your speed and scalability requirements?",
            "testing_strategy": "What testing approach will ensure quality?",
            "scalability": "How will your system handle growth?",
            "integrations": "What external systems need to integrate?",
            "data_management": "How should data be stored and managed?",
            "architecture": "What system architecture will you use?",
            "api_design": "How will your API be structured?",
            "deployment": "How will you deploy and manage releases?",
            "monitoring": "What metrics and logs will you track?",
            "documentation": "What documentation is needed?",
        }

        return questions.get(category, f"Can you elaborate on {category.replace('_', ' ')}?")

    def _generate_insights(self, qa_events: List[Dict], velocity: float) -> List[str]:
        """Generate insights from progression data."""
        logger.debug(
            f"Generating insights from {len(qa_events)} Q&A events, velocity={velocity:.2f}"
        )

        insights = []

        if not qa_events:
            logger.debug("No Q&A events provided, returning empty insights")
            return insights

        if velocity > 0:
            insights.append(f"Steady growth with velocity of {velocity:.1f} points per session")

        self._detect_plateaus(qa_events, insights)
        self._detect_acceleration(qa_events, velocity, insights)

        result = insights if insights else ["No significant patterns detected yet"]
        logger.debug(f"Generated {len(result)} insights")
        return result

    def _detect_plateaus(self, qa_events: List[Dict], insights: List[str]) -> None:
        """Detect plateau patterns in Q&A events and add to insights."""
        plateaus = []
        consecutive_low = 0
        plateau_start = None

        for i, event in enumerate(qa_events):
            delta = event.get("delta", 0.0)
            if delta < 0.5:
                if consecutive_low == 0:
                    plateau_start = i
                consecutive_low += 1
            else:
                if consecutive_low >= 2:
                    plateaus.append((plateau_start + 1, consecutive_low))
                consecutive_low = 0

        if plateaus:
            start, duration = plateaus[0]  # Show first plateau
            insights.append(f"Plateau detected at Q{start} for {duration} sessions")
            logger.debug(f"Detected plateau: Q{start} for {duration} sessions")

    def _detect_acceleration(
        self, qa_events: List[Dict], velocity: float, insights: List[str]
    ) -> None:
        """Detect acceleration patterns in recent Q&A events and add to insights."""
        if len(qa_events) >= 5:
            recent_deltas = [e.get("delta", 0) for e in qa_events[-3:]]
            if all(d > velocity for d in recent_deltas):
                insights.append("Recent acceleration in progress")
                logger.debug("Detected recent acceleration in progress")
