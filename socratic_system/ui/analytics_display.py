"""
Analytics display utilities for CLI visualization.

Provides ASCII-based charts and formatting for analytics reports.
No external dependencies - pure text-based rendering.
"""

from typing import Any, Dict, List


class AnalyticsDisplay:
    """CLI display utilities for analytics reports."""

    @staticmethod
    def display_category_analysis(analysis: Dict, phase: str) -> None:
        """
        Display detailed category analysis for a phase.

        Shows weak/strong/missing categories with progress bars.
        """
        print("\n" + "=" * 70)
        print(f"CATEGORY ANALYSIS - {phase.upper()} PHASE")
        print("=" * 70)

        weak = analysis.get("weak_categories", [])
        strong = analysis.get("strong_categories", [])
        missing = analysis.get("missing_categories", [])
        balance = analysis.get("balance", {})

        # Weak categories
        if weak:
            print("\nWeak Categories (< 30%):")
            for cat_info in weak:
                bar = AnalyticsDisplay._create_progress_bar(cat_info["percentage"])
                cat_display = cat_info["category"].replace("_", " ").title()
                print(
                    f"  - {cat_display}: {cat_info['percentage']:.1f}% {bar} "
                    f"({cat_info['current']:.1f}/{cat_info['target']:.0f} pts)"
                )

        # Strong categories
        if strong:
            print("\nStrong Categories (> 70%):")
            for cat_info in strong:
                bar = AnalyticsDisplay._create_progress_bar(cat_info["percentage"])
                cat_display = cat_info["category"].replace("_", " ").title()
                print(
                    f"  - {cat_display}: {cat_info['percentage']:.1f}% {bar} "
                    f"({cat_info['current']:.1f}/{cat_info['target']:.0f} pts)"
                )

        # Missing categories
        if missing:
            print("\nMissing Categories (0 specs):")
            for cat in missing[:5]:
                cat_display = cat.replace("_", " ").title()
                print(f"  - {cat_display}")
            if len(missing) > 5:
                print(f"  ... and {len(missing) - 5} more")

        # Balance assessment
        print(f"\nCategory Balance: {balance.get('status', 'UNKNOWN')}")
        for message in balance.get("messages", []):
            print(f"  - {message}")

        print()

    @staticmethod
    def display_recommendations(recommendations: List[Dict], questions: List[str]) -> None:
        """
        Display actionable recommendations for improvement.

        Groups recommendations by priority and suggests targeted questions.
        """
        print("\n" + "=" * 70)
        print("RECOMMENDATIONS FOR IMPROVEMENT")
        print("=" * 70)

        high_priority = [r for r in recommendations if r["priority"] == "high"]
        medium_priority = [r for r in recommendations if r["priority"] == "medium"]

        if high_priority:
            print(f"\nHigh Priority ({len(high_priority)}):")
            for i, rec in enumerate(high_priority[:5], 1):
                cat_display = rec["category"].replace("_", " ").title()
                current = rec.get("current", 0.0)
                target = rec.get("target", 70.0)
                gap = rec.get("gap", 0.0)

                print(f"\n  {i}. {cat_display}")
                print(f"     Current: {current:.0f}% -> Target: {target:.0f}% (gap: {gap:.0f}%)")
                print(f"     Action: {rec['action']}")

        if medium_priority:
            print(f"\nMedium Priority ({len(medium_priority)}):")
            for i, rec in enumerate(medium_priority[:3], 1):
                cat_display = rec["category"].replace("_", " ").title()
                current = rec.get("current", 0.0)
                print(f"  {i}. {cat_display} ({current:.0f}%)")

        # Suggested questions
        if questions:
            print("\nSuggested Next Questions:")
            for i, question in enumerate(questions, 1):
                print(f"  {i}. {question}")

        print()

    @staticmethod
    def display_trends(trends: Dict, history: List[Dict]) -> None:
        """
        Display maturity progression trends with ASCII chart.

        Shows velocity, progression over time, and key insights.
        """
        print("\n" + "=" * 70)
        print("MATURITY PROGRESSION TRENDS")
        print("=" * 70)

        velocity = trends.get("velocity", 0.0)
        total_sessions = trends.get("total_sessions", 0)
        current_phase = trends.get("current_phase", "unknown")
        current_score = trends.get("current_score", 0.0)
        insights = trends.get("insights", [])

        print(f"\nVelocity: {velocity:.1f} points per Q&A session")
        print(f"Total Sessions: {total_sessions}")
        print(f"Current Phase: {current_phase.capitalize()} ({current_score:.1f}%)")

        # ASCII chart of score over time
        qa_events = [e for e in history if e.get("event_type") == "response_processed"]
        if qa_events:
            print("\nScore Over Time:")
            chart = AnalyticsDisplay._create_trend_chart(qa_events)
            print(chart)

        # Insights
        if insights:
            print("\nKey Insights:")
            for insight in insights:
                print(f"  - {insight}")

        print()

    @staticmethod
    def display_summary(metrics: Dict, project: Any) -> None:
        """
        Display quick overview of all analytics metrics.

        Shows real-time metrics tracked in ProjectContext.
        """
        print("\n" + "=" * 70)
        print("ANALYTICS SUMMARY")
        print("=" * 70)

        velocity = metrics.get("velocity", 0.0)
        total_sessions = metrics.get("total_qa_sessions", 0)
        avg_confidence = metrics.get("avg_confidence", 0.0)
        weak = metrics.get("weak_categories", [])
        strong = metrics.get("strong_categories", [])

        print(f"\nVelocity: {velocity:.2f} points/session")
        print(f"Q&A Sessions: {total_sessions}")
        print(f"Avg Confidence: {avg_confidence:.1%}")
        print(f"Current Phase: {project.phase.capitalize()}")
        print(f"Phase Maturity: {project.phase_maturity_scores.get(project.phase, 0.0):.1f}%")

        if weak:
            print(f"\nWeak Categories ({len(weak)}):")
            for cat in weak[:3]:
                print(f"  - {cat.replace('_', ' ').title()}")
            if len(weak) > 3:
                print(f"  ... and {len(weak) - 3} more")

        if strong:
            print(f"\nStrong Categories ({len(strong)}):")
            for cat in strong[:3]:
                print(f"  - {cat.replace('_', ' ').title()}")
            if len(strong) > 3:
                print(f"  ... and {len(strong) - 3} more")

        print()

    # ========================================================================
    # Helper Methods for ASCII Charts
    # ========================================================================

    @staticmethod
    def _create_progress_bar(percentage: float, width: int = 20) -> str:
        """
        Create ASCII progress bar.

        Args:
            percentage: Percentage filled (0-100)
            width: Width of bar in characters

        Returns:
            String representation of progress bar
        """
        filled = int((percentage / 100.0) * width)
        empty = width - filled
        return "[" + "=" * filled + "-" * empty + "]"

    @staticmethod
    def _create_trend_chart(qa_events: List[Dict], height: int = 8) -> str:
        """
        Create ASCII line chart of maturity progression.

        Args:
            qa_events: List of Q&A events with score_after
            height: Height of chart in lines

        Returns:
            String representation of ASCII chart
        """
        if not qa_events:
            return "No data available"

        scores = [e.get("score_after", 0) for e in qa_events]

        if not scores:
            return "No Q&A sessions yet"

        # Find max score for scaling
        max_score = max(scores) if scores else 100
        if max_score < 10:
            max_score = 10

        chart_lines = []

        # Y-axis labels and data
        for level in range(height, -1, -1):
            threshold = (level / height) * max_score
            line = f"{threshold:4.0f}% |"

            for score in scores:
                if score >= threshold:
                    line += " * "
                else:
                    line += "   "

            chart_lines.append(line)

        # X-axis
        x_axis = "     |" + "---" * len(scores) + ">"
        chart_lines.append(x_axis)

        # X-axis labels
        if len(scores) <= 20:
            labels = "     " + "".join(f"Q{i:<3}" for i in range(1, len(scores) + 1))
        else:
            # For many sessions, show every 5th label
            labels = "     "
            for i in range(len(scores)):
                if i % 5 == 0:
                    labels += f"Q{i+1:<3}"
                else:
                    labels += "   "

        chart_lines.append(labels)

        return "\n".join(chart_lines)

    @staticmethod
    def display_detailed_breakdown(project: Any) -> None:
        """
        Display detailed breakdown of all categories and phases.

        Useful for comprehensive assessment across entire project.
        """
        print("\n" + "=" * 70)
        print("DETAILED MATURITY BREAKDOWN")
        print("=" * 70)

        phases = ["discovery", "analysis", "design", "implementation"]

        for phase in phases:
            score = project.phase_maturity_scores.get(phase, 0.0)
            category_scores = project.category_scores.get(phase, {})

            status = "READY" if score >= 60 else "IN PROGRESS" if score > 0 else "NOT STARTED"
            bar = AnalyticsDisplay._create_progress_bar(score)

            print(f"\n{phase.upper()}: {score:.1f}% {bar} [{status}]")

            if category_scores:
                for category, score_data in sorted(category_scores.items()):
                    if isinstance(score_data, dict):
                        current = score_data.get("current_score", 0.0)
                        target = score_data.get("target_score", 1.0)
                        pct = (current / target * 100) if target > 0 else 0.0
                        cat_bar = AnalyticsDisplay._create_progress_bar(pct, width=15)
                        cat_display = category.replace("_", " ").title()
                        print(f"  {cat_display:30} {pct:5.1f}% {cat_bar}")

        print()

    @staticmethod
    def display_completion_status(project: Any) -> None:
        """
        Display phase completion status and readiness.

        Helps users understand progression toward goals.
        """
        print("\n" + "=" * 70)
        print("PHASE COMPLETION STATUS")
        print("=" * 70)

        phases = ["discovery", "analysis", "design", "implementation"]
        current_phase = project.phase

        for phase in phases:
            score = project.phase_maturity_scores.get(phase, 0.0)

            if phase == current_phase:
                marker = ">> "
                status = "CURRENT"
            elif phases.index(phase) < phases.index(current_phase):
                marker = "[X]"
                status = "COMPLETED"
            else:
                marker = "   "
                status = "UPCOMING"

            bar = AnalyticsDisplay._create_progress_bar(score, width=30)
            print(f"{marker} {phase.upper():20} {score:5.1f}% {bar} [{status}]")

        print()
