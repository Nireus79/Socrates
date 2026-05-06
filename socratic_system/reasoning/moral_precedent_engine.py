"""
Moral Precedent Engine

Stores, retrieves, and analyzes moral precedents to ensure consistency
in ethical decisions and learn from historical patterns.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import logging
import json


class PrecedentType(Enum):
    """Types of moral precedents."""
    ALLOWED = "allowed"
    BLOCKED = "blocked"
    ESCALATED = "escalated"
    CONDITIONAL = "conditional"


@dataclass
class MoralPrecedent:
    """Represents a stored moral precedent."""
    id: str
    action_description: str
    conclusion: PrecedentType
    confidence: float  # 0.0-1.0
    reasoning: str
    principles_involved: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)
    stakeholders_affected: List[str] = field(default_factory=list)
    created_date: datetime = field(default_factory=datetime.utcnow)
    usage_count: int = 0  # How many times this precedent was referenced
    related_precedents: List[str] = field(default_factory=list)

    def __hash__(self):
        return hash((self.id, self.action_description))

    def similarity_to(self, action: str, threshold: float = 0.5) -> float:
        """
        Calculate similarity between this precedent and an action.

        Args:
            action: Description of action to compare
            threshold: Minimum similarity score

        Returns:
            Similarity score 0.0-1.0
        """
        # Simple keyword-based similarity
        precedent_words = set(self.action_description.lower().split())
        action_words = set(action.lower().split())

        if not precedent_words or not action_words:
            return 0.0

        # Jaccard similarity
        intersection = len(precedent_words & action_words)
        union = len(precedent_words | action_words)

        if union == 0:
            return 0.0

        return intersection / union


@dataclass
class PrecedentQuery:
    """Query parameters for finding similar precedents."""
    action: str
    similarity_threshold: float = 0.5
    max_results: int = 5
    principle_filter: Optional[List[str]] = None
    conclusion_filter: Optional[List[PrecedentType]] = None


@dataclass
class PrecedentMatch:
    """Result of querying for similar precedents."""
    precedent: MoralPrecedent
    similarity_score: float
    relevance_score: float  # Combination of similarity and other factors
    consistency_with_query: bool  # Whether conclusion matches expected pattern


@dataclass
class PrecedentAnalysis:
    """Analysis of precedents related to a deliberation."""
    action: str
    matching_precedents: List[PrecedentMatch] = field(default_factory=list)
    precedent_consistency: bool = True  # Are precedents consistent with each other?
    consistency_explanation: str = ""
    recommended_conclusion: Optional[PrecedentType] = None
    historical_pattern: str = ""  # Description of pattern in precedents
    timestamp: datetime = field(default_factory=datetime.utcnow)


class MoralPrecedentEngine:
    """
    Manages moral precedents for consistent ethical decision-making.

    Stores historical ethical decisions and enables:
    - Retrieval of similar past cases
    - Consistency checking across decisions
    - Pattern analysis and learning
    - Precedent-based reasoning support
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """Initialize moral precedent engine.

        Args:
            logger: Optional logger instance
        """
        self.logger = logger or logging.getLogger(__name__)
        self.precedents: Dict[str, MoralPrecedent] = {}
        self._id_counter = 0

    def store_precedent(
        self,
        action_description: str,
        conclusion: PrecedentType,
        confidence: float,
        reasoning: str,
        principles_involved: Optional[List[str]] = None,
        context: Optional[Dict[str, Any]] = None,
        stakeholders_affected: Optional[List[str]] = None,
    ) -> str:
        """
        Store a new moral precedent.

        Args:
            action_description: Description of the action
            conclusion: Conclusion reached
            confidence: Confidence in the conclusion (0.0-1.0)
            reasoning: Detailed reasoning
            principles_involved: Relevant principles
            context: Context information
            stakeholders_affected: List of affected stakeholders

        Returns:
            Precedent ID
        """
        precedent_id = f"prec_{self._id_counter:06d}"
        self._id_counter += 1

        precedent = MoralPrecedent(
            id=precedent_id,
            action_description=action_description,
            conclusion=conclusion,
            confidence=confidence,
            reasoning=reasoning,
            principles_involved=principles_involved or [],
            context=context or {},
            stakeholders_affected=stakeholders_affected or [],
        )

        self.precedents[precedent_id] = precedent

        self.logger.info(
            f"[Precedent Store] {precedent_id}: {action_description} -> {conclusion.value}"
        )

        return precedent_id

    def query_precedents(self, query: PrecedentQuery) -> List[PrecedentMatch]:
        """
        Find precedents similar to a given action.

        Args:
            query: Query parameters

        Returns:
            List of matching precedents, sorted by relevance
        """
        matches = []

        for precedent in self.precedents.values():
            # Calculate similarity
            similarity = precedent.similarity_to(
                query.action, query.similarity_threshold
            )

            if similarity < query.similarity_threshold:
                continue

            # Check principle filter
            if query.principle_filter:
                shared_principles = set(query.principle_filter) & set(
                    precedent.principles_involved
                )
                if not shared_principles:
                    continue

            # Check conclusion filter
            if query.conclusion_filter:
                if precedent.conclusion not in query.conclusion_filter:
                    continue

            # Calculate relevance (combination of similarity and other factors)
            relevance = similarity
            if query.principle_filter:
                principle_boost = (
                    len(shared_principles) / len(query.principle_filter) * 0.2
                )
                relevance = min(1.0, relevance + principle_boost)

            match = PrecedentMatch(
                precedent=precedent,
                similarity_score=similarity,
                relevance_score=relevance,
                consistency_with_query=True,
            )

            matches.append(match)

        # Sort by relevance and limit results
        matches.sort(key=lambda m: m.relevance_score, reverse=True)
        matches = matches[: query.max_results]

        self.logger.debug(
            f"[Precedent Query] Found {len(matches)} matches for: {query.action}"
        )

        return matches

    def analyze_precedents(
        self, action: str, principles: Optional[List[str]] = None
    ) -> PrecedentAnalysis:
        """
        Analyze precedents related to an action.

        Args:
            action: Action description
            principles: Relevant principles

        Returns:
            Analysis of matching precedents
        """
        query = PrecedentQuery(
            action=action,
            similarity_threshold=0.3,
            principle_filter=principles,
            max_results=10,
        )

        matches = self.query_precedents(query)
        analysis = PrecedentAnalysis(action=action, matching_precedents=matches)

        if not matches:
            analysis.consistency_explanation = "No similar precedents found"
            return analysis

        # Check consistency among matching precedents
        conclusions = [m.precedent.conclusion for m in matches]
        unique_conclusions = set(conclusions)

        if len(unique_conclusions) == 1:
            analysis.precedent_consistency = True
            analysis.recommended_conclusion = conclusions[0]
            analysis.consistency_explanation = (
                f"All {len(matches)} precedents recommend {conclusions[0].value}"
            )
        else:
            analysis.precedent_consistency = False
            analysis.consistency_explanation = (
                f"Precedents disagree: {', '.join(str(c.value) for c in unique_conclusions)}"
            )

        # Identify historical pattern
        allowed_count = sum(
            1 for c in conclusions if c == PrecedentType.ALLOWED
        )
        blocked_count = sum(
            1 for c in conclusions if c == PrecedentType.BLOCKED
        )
        escalated_count = sum(
            1 for c in conclusions if c == PrecedentType.ESCALATED
        )

        if allowed_count > blocked_count and allowed_count > escalated_count:
            analysis.historical_pattern = (
                f"Actions like this are usually allowed ({allowed_count}/{len(matches)})"
            )
        elif blocked_count > allowed_count and blocked_count > escalated_count:
            analysis.historical_pattern = (
                f"Actions like this are usually blocked ({blocked_count}/{len(matches)})"
            )
        elif escalated_count > allowed_count and escalated_count > blocked_count:
            analysis.historical_pattern = (
                f"Actions like this usually require escalation ({escalated_count}/{len(matches)})"
            )
        else:
            analysis.historical_pattern = "Mixed precedents without clear pattern"

        self.logger.info(
            f"[Precedent Analysis] {action}: {len(matches)} precedents found. "
            f"Consistency: {analysis.precedent_consistency}"
        )

        return analysis

    def check_consistency(
        self, new_conclusion: PrecedentType, matching_precedents: List[MoralPrecedent]
    ) -> Tuple[bool, str]:
        """
        Check if a new conclusion is consistent with precedents.

        Args:
            new_conclusion: Proposed conclusion
            matching_precedents: Relevant precedents

        Returns:
            Tuple of (is_consistent, explanation)
        """
        if not matching_precedents:
            return True, "No precedents to compare against"

        precedent_conclusions = [p.conclusion for p in matching_precedents]
        unique_conclusions = set(precedent_conclusions)

        # If all precedents agree
        if len(unique_conclusions) == 1:
            precedent_conclusion = precedent_conclusions[0]
            if new_conclusion == precedent_conclusion:
                return True, f"Consistent with all {len(matching_precedents)} precedents"
            else:
                return (
                    False,
                    f"Contradicts all {len(matching_precedents)} precedents "
                    f"which conclude {precedent_conclusion.value}",
                )

        # If precedents disagree
        agreement_level = max(precedent_conclusions.count(c) for c in unique_conclusions)
        agreement_pct = agreement_level / len(matching_precedents)

        if agreement_pct > 0.7:
            dominant_conclusion = max(
                unique_conclusions,
                key=lambda c: precedent_conclusions.count(c),
            )
            if new_conclusion == dominant_conclusion:
                return True, f"Consistent with {agreement_pct:.0%} of precedents"
            else:
                return (
                    False,
                    f"Contradicts {agreement_pct:.0%} of precedents "
                    f"which conclude {dominant_conclusion.value}",
                )

        # Mixed precedents
        return True, "Precedents mixed; new conclusion could go either way"

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about stored precedents."""
        if not self.precedents:
            return {
                "total_precedents": 0,
                "allowed_count": 0,
                "blocked_count": 0,
                "escalated_count": 0,
                "conditional_count": 0,
                "average_confidence": 0.0,
            }

        conclusions = [p.conclusion for p in self.precedents.values()]
        confidences = [p.confidence for p in self.precedents.values()]

        return {
            "total_precedents": len(self.precedents),
            "allowed_count": sum(1 for c in conclusions if c == PrecedentType.ALLOWED),
            "blocked_count": sum(1 for c in conclusions if c == PrecedentType.BLOCKED),
            "escalated_count": sum(
                1 for c in conclusions if c == PrecedentType.ESCALATED
            ),
            "conditional_count": sum(
                1 for c in conclusions if c == PrecedentType.CONDITIONAL
            ),
            "average_confidence": sum(confidences) / len(confidences),
            "most_common_conclusion": max(
                set(conclusions), key=conclusions.count
            ).value,
        }

    def export_precedents(self, filepath: str) -> None:
        """Export precedents to JSON file."""
        data = {
            "exported_at": datetime.utcnow().isoformat(),
            "precedent_count": len(self.precedents),
            "precedents": [
                {
                    "id": p.id,
                    "action_description": p.action_description,
                    "conclusion": p.conclusion.value,
                    "confidence": p.confidence,
                    "reasoning": p.reasoning,
                    "principles_involved": p.principles_involved,
                    "stakeholders_affected": p.stakeholders_affected,
                    "created_date": p.created_date.isoformat(),
                    "usage_count": p.usage_count,
                }
                for p in self.precedents.values()
            ],
        }

        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)

        self.logger.info(f"[Precedent Export] Exported {len(self.precedents)} precedents")

    def import_precedents(self, filepath: str) -> None:
        """Import precedents from JSON file."""
        try:
            with open(filepath, "r") as f:
                data = json.load(f)

            for prec_data in data.get("precedents", []):
                precedent_id = prec_data["id"]
                precedent = MoralPrecedent(
                    id=precedent_id,
                    action_description=prec_data["action_description"],
                    conclusion=PrecedentType(prec_data["conclusion"]),
                    confidence=prec_data["confidence"],
                    reasoning=prec_data["reasoning"],
                    principles_involved=prec_data.get(
                        "principles_involved", []
                    ),
                    stakeholders_affected=prec_data.get(
                        "stakeholders_affected", []
                    ),
                    usage_count=prec_data.get("usage_count", 0),
                )
                self.precedents[precedent_id] = precedent
                self._id_counter = max(self._id_counter, int(precedent_id.split("_")[1]) + 1)

            self.logger.info(
                f"[Precedent Import] Imported {len(self.precedents)} precedents"
            )

        except Exception as e:
            self.logger.error(f"[Precedent Import] Failed to import: {e}")
