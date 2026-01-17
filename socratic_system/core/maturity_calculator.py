"""
Independent maturity calculation module - Pure calculation logic without agent dependencies
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from socratic_system.core.insight_categorizer import InsightCategorizer
from socratic_system.core.project_categories import get_phase_categories
from socratic_system.models import CategoryScore, PhaseMaturity

logger = logging.getLogger(__name__)


# Maturity thresholds
READY_THRESHOLD = 20.0  # Minimum to advance without strong warning
COMPLETE_THRESHOLD = 100.0  # Phase fully mature
WARNING_THRESHOLD = 10.0  # Below this = strong warning


class MaturityCalculator:
    """
    Pure maturity calculation logic - independent of agents and orchestration.

    Provides functions to:
    - Calculate phase maturity from specifications
    - Categorize insights into phase categories
    - Generate warnings based on maturity state
    - Calculate category confidence scores
    - Support multiple project types with appropriate categories
    """

    def __init__(self, project_type: str = "software", claude_client: Optional[Any] = None):
        """
        Initialize with phase categories based on project type.

        Args:
            project_type: Type of project (software, business, creative, research, marketing, educational)
            claude_client: Optional Claude API client for intelligent categorization
        """
        logger.debug(
            f"Initializing MaturityCalculator with project_type={project_type}, claude_client={claude_client is not None}"
        )

        self.project_type = project_type
        self.phase_categories = get_phase_categories(project_type)
        self.READY_THRESHOLD = READY_THRESHOLD
        self.COMPLETE_THRESHOLD = COMPLETE_THRESHOLD
        self.WARNING_THRESHOLD = WARNING_THRESHOLD

        logger.info(f"Loaded {len(self.phase_categories)} phases for project type: {project_type}")

        # Initialize categorizer if Claude client provided
        self.categorizer: Optional[InsightCategorizer] = None
        if claude_client:
            self.categorizer = InsightCategorizer(claude_client)
            logger.info(
                "InsightCategorizer initialized with Claude client for intelligent categorization"
            )

    def set_project_type(self, project_type: str) -> None:
        """Change project type and update categories"""
        logger.info(f"Switching project type from {self.project_type} to {project_type}")
        self.project_type = project_type
        self.phase_categories = get_phase_categories(project_type)
        logger.debug(
            f"Project type switched successfully. Loaded {len(self.phase_categories)} phases"
        )

    def set_claude_client(self, claude_client: Any) -> None:
        """Set Claude client for intelligent categorization"""
        logger.info("Setting Claude client for intelligent categorization")
        self.categorizer = InsightCategorizer(claude_client)
        logger.debug("Claude client set successfully")

    def calculate_phase_maturity(self, phase_specs: List[Dict], phase: str) -> PhaseMaturity:
        """
        Calculate maturity for a phase using confidence-weighted, capped algorithm.

        Algorithm:
        1. For each category in the phase:
           a. Get all specs tagged with that category
           b. Calculate weighted sum: sum(spec_value * confidence)
           c. Cap at category target (prevents one category from dominating)
        2. Sum all capped category scores
        3. Calculate percentage: (sum / 90) * 100
        4. Identify strongest/weakest categories and missing coverage

        Args:
            phase_specs: List of spec dicts for this phase
            phase: Phase name (discovery, analysis, design, implementation)

        Returns:
            PhaseMaturity object with complete maturity information
        """
        logger.debug(
            f"Starting maturity calculation for phase={phase} with {len(phase_specs)} specs"
        )

        if phase not in self.phase_categories:
            logger.error(f"Unknown phase requested: {phase}")
            raise ValueError(f"Unknown phase: {phase}")

        # Get category targets for this phase
        category_targets = self.phase_categories[phase]

        # Initialize tracking
        category_scores: Dict[str, CategoryScore] = {}
        total_score = 0.0
        total_specs = len(phase_specs)

        logger.debug(f"Phase {phase} has {len(category_targets)} categories with 90 total points")

        # Calculate score for each category
        for category, target in category_targets.items():
            # Get specs for this category
            category_specs = [s for s in phase_specs if s.get("category") == category]

            # Calculate confidence-weighted score
            weighted_sum = 0.0
            for spec in category_specs:
                # Each spec contributes based on its confidence
                # Typical confidence: 0.9 from Claude extraction
                confidence = spec.get("confidence", 0.9)
                value = spec.get("value", 1.0)  # Base value of spec
                weighted_sum += value * confidence

            # Cap at category target (prevents one category from dominating)
            capped_score = min(weighted_sum, target)
            total_score += capped_score

            # Store category score
            category_scores[category] = CategoryScore(
                category=category,
                current_score=capped_score,
                target_score=target,
                confidence=self._calculate_category_confidence(category_specs),
                spec_count=len(category_specs),
            )

            logger.debug(
                f"Category {category}: {len(category_specs)} specs, "
                f"weighted_sum={weighted_sum:.2f}, capped={capped_score:.2f}/{target}"
            )

        # Calculate overall percentage (out of 90 points)
        overall_percentage = (total_score / 90.0) * 100.0

        logger.info(
            f"Phase {phase} maturity: {overall_percentage:.1f}% ({total_score:.1f}/90 points from {total_specs} specs)"
        )

        # Identify strongest and weakest categories
        sorted_categories = sorted(
            category_scores.items(),
            key=lambda x: x[1].percentage,
            reverse=True,
        )
        strongest = [c[0] for c in sorted_categories[:3] if c[1].spec_count > 0]
        weakest = [c[0] for c in sorted_categories[-3:] if c[1].percentage < 50]

        if strongest:
            logger.debug(f"Strongest categories: {strongest}")
        if weakest:
            logger.debug(f"Weakest categories: {weakest}")

        # Identify missing categories (0 specs)
        missing = [c for c, score in category_scores.items() if score.spec_count == 0]
        if missing:
            logger.info(f"Phase {phase} has {len(missing)} missing categories: {missing[:5]}")

        # Generate warnings
        warnings = self.generate_warnings(overall_percentage, category_scores, missing)
        if warnings:
            logger.info(f"Generated {len(warnings)} warnings for phase {phase}")

        # Create PhaseMaturity result
        maturity = PhaseMaturity(
            phase=phase,
            overall_score=overall_percentage,
            category_scores=category_scores,
            total_specs=total_specs,
            missing_categories=missing,
            strongest_categories=strongest,
            weakest_categories=weakest,
            is_ready_to_advance=overall_percentage >= self.READY_THRESHOLD,
            warnings=warnings,
        )

        return maturity

    def _calculate_category_confidence(self, specs: List[Dict]) -> float:
        """Calculate average confidence for a category's specs"""
        if not specs:
            logger.debug("No specs provided for confidence calculation, returning 0.0")
            return 0.0
        confidences = [s.get("confidence", 0.9) for s in specs]
        avg_confidence = sum(confidences) / len(confidences)
        logger.debug(
            f"Calculated category confidence: {avg_confidence:.3f} from {len(specs)} specs"
        )
        return avg_confidence

    def generate_warnings(
        self, score: float, category_scores: Dict[str, CategoryScore], missing: List[str]
    ) -> List[str]:
        """
        Generate actionable warnings based on maturity state.

        Returns up to 3 most important warnings in priority order.
        """
        logger.debug(
            f"Generating warnings for score={score:.1f}%, missing_count={len(missing)}, categories={len(category_scores)}"
        )
        warnings = []

        # Overall score warnings
        if score < self.WARNING_THRESHOLD:
            logger.debug(f"Score {score:.1f}% below WARNING_THRESHOLD {self.WARNING_THRESHOLD}")
            warnings.append(
                f"Phase maturity very low ({score:.1f}%). "
                f"Consider answering more questions to build a solid foundation."
            )
        elif score < self.READY_THRESHOLD:
            logger.debug(f"Score {score:.1f}% below READY_THRESHOLD {self.READY_THRESHOLD}")
            warnings.append(
                f"Phase maturity below recommended ({score:.1f}% < {self.READY_THRESHOLD}%). "
                f"You can advance, but be prepared for rework later."
            )

        # Missing category warnings
        if missing:
            logger.debug(f"Found {len(missing)} missing categories: {missing[:5]}")
            missing_text = ", ".join(missing[:5])
            if len(missing) > 5:
                missing_text += f" + {len(missing) - 5} more"
            warnings.append(f"No coverage in: {missing_text}")

        # Weak category warnings
        weak = [c for c, s in category_scores.items() if s.spec_count > 0 and s.percentage < 30]
        if weak:
            logger.debug(f"Found {len(weak)} weak categories (< 30%): {weak}")
        if weak and len(warnings) < 3:
            weak_text = ", ".join(weak[:3])
            warnings.append(f"Weak areas: {weak_text}")

        # Imbalance warnings
        strong = [s for s in category_scores.values() if s.percentage > 80]
        if strong:
            logger.debug(f"Found {len(strong)} strong categories (> 80%)")
        if strong and missing and len(warnings) < 3:
            logger.debug("Added imbalance warning: strong categories with missing areas")
            warnings.append(
                "Some categories are well-developed while others are missing. "
                "Try to balance your specification coverage."
            )

        logger.info(f"Generated {len(warnings)} warnings (limited to top 3)")
        return warnings[:3]  # Return top 3 warnings

    def categorize_insights(self, insights: Dict, phase: str, user_id: str = None) -> List[Dict]:
        """
        Categorize extracted insights into phase categories.

        Uses Claude for intelligent semantic categorization if available,
        falls back to simple heuristic mapping if Claude is not configured.

        Args:
            insights: Dict of insights extracted from user (goals, requirements, etc.)
            phase: Current phase (discovery, analysis, design, implementation)
            user_id: Optional user ID for API key lookup in Claude client

        Returns:
            List of categorized spec dicts ready to be stored in project
        """
        logger.debug(
            f"Categorizing insights for phase={phase}, insight_fields={list(insights.keys())}, user_id={user_id}"
        )

        if not insights:
            logger.debug("No insights provided, returning empty list")
            return []

        # Try Claude categorization first if available
        if self.categorizer:
            logger.debug("Using Claude-based intelligent categorization")
            categorized = self.categorizer.categorize_insights(insights, phase, self.project_type, user_id=user_id)
            logger.info(f"Claude categorization produced {len(categorized)} specs")
            return categorized

        # Fall back to simple heuristic mapping
        logger.debug("Claude categorizer not available, falling back to heuristic categorization")
        categorized = self._simple_categorization(insights, phase)
        logger.info(f"Heuristic categorization produced {len(categorized)} specs")
        return categorized

    def _simple_categorization(self, insights: Dict, phase: str) -> List[Dict]:
        """
        Simple heuristic-based categorization (fallback when Claude unavailable).

        Maps known fields to categories.
        """
        logger.debug(f"Starting heuristic categorization for phase={phase}")
        categorized = []

        # Simple field mapping
        field_to_category = {
            "goals": "goals",
            "objectives": "objectives",
            "requirements": "requirements",
            "tech_stack": "tech_stack",
            "technology": "technology",
            "constraints": "constraints",
            "scope": "scope",
            "budget": "constraints",
            "timeline": "timeline",
            "team_structure": "team_structure",
            "resources": "resources",
            "assumptions": "assumptions",
            "risks": "risks",
            "dependencies": "dependencies",
            "language_preferences": "language_preferences",
            "deployment_target": "deployment_target",
            "code_style": "code_style",
        }

        # Get valid categories for this phase
        valid_categories = set(self.phase_categories.get(phase, {}).keys())
        logger.debug(f"Valid categories for {phase}: {valid_categories}")

        # Process each insight field
        for field, values in insights.items():
            if not values:
                logger.debug(f"Skipping empty field: {field}")
                continue

            # Map field to category
            category = field_to_category.get(field, field)
            logger.debug(f"Field '{field}' maps to category '{category}'")

            # Only categorize if it's a valid category for this phase
            # Otherwise try to find a matching category
            if category not in valid_categories:
                # Try to find a matching category
                matching = [c for c in valid_categories if field.lower() in c.lower()]
                if matching:
                    logger.debug(f"Category '{category}' not valid, found matching: {matching[0]}")
                    category = matching[0]
                else:
                    # Skip if no valid category found
                    logger.debug(f"No valid category found for field '{field}', skipping")
                    continue

            # Create spec entries
            spec_count = 0
            if isinstance(values, list):
                for value in values:
                    if value:  # Skip empty values
                        categorized.append(
                            {
                                "category": category,
                                "content": str(value),
                                "confidence": 0.7,  # Lower confidence for heuristic
                                "value": 1.0,
                                "source_field": field,
                                "timestamp": datetime.now().isoformat(),
                            }
                        )
                        spec_count += 1
                logger.debug(f"Field '{field}' created {spec_count} specs in category '{category}'")
            else:
                # Single value
                if values:
                    categorized.append(
                        {
                            "category": category,
                            "content": str(values),
                            "confidence": 0.7,
                            "value": 1.0,
                            "source_field": field,
                            "timestamp": datetime.now().isoformat(),
                        }
                    )
                    logger.debug(f"Field '{field}' created 1 spec in category '{category}'")

        logger.info(
            f"Heuristic categorization complete: {len(categorized)} specs created from {len(insights)} insight fields"
        )
        return categorized

    def is_phase_complete(self, maturity: PhaseMaturity) -> bool:
        """Check if phase maturity is at 100%"""
        is_complete = maturity.overall_score >= self.COMPLETE_THRESHOLD
        logger.debug(
            f"Phase completeness check: {maturity.phase} = {maturity.overall_score:.1f}% >= {self.COMPLETE_THRESHOLD}% ? {is_complete}"
        )
        return is_complete

    def is_ready_to_advance(self, maturity: PhaseMaturity) -> bool:
        """Check if phase maturity meets the ready threshold (recommended threshold)"""
        is_ready = maturity.overall_score >= self.READY_THRESHOLD
        logger.debug(
            f"Phase readiness check: {maturity.phase} = {maturity.overall_score:.1f}% >= {self.READY_THRESHOLD}% ? {is_ready}"
        )
        return is_ready

    def get_phase_categories(self, phase: str) -> Dict[str, int]:
        """Get category targets for a specific phase"""
        categories = self.phase_categories.get(phase, {})
        logger.debug(f"Retrieved {len(categories)} categories for phase: {phase}")
        return categories

    def get_all_phases(self) -> List[str]:
        """Get list of all valid phases"""
        phases = list(self.phase_categories.keys())
        logger.debug(f"Retrieved all phases: {phases}")
        return phases
