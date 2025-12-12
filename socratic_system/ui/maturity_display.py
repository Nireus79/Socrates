"""
Maturity display component for terminal UI visualization
"""

from typing import Dict, List

from colorama import Fore, Style


class MaturityDisplay:
    """Display maturity information to users in the terminal"""

    @staticmethod
    def display_maturity_update(maturity: Dict) -> None:
        """
        Display maturity update after each question/response.

        Shows quick progress bar and key warnings/suggestions.
        Called after SocraticCounselorAgent processes a response.
        """
        score = maturity.get("overall_score", 0.0)
        phase = maturity.get("phase", "unknown")
        warnings = maturity.get("warnings", [])

        # Determine color and status based on score
        if score >= 80:
            color = Fore.GREEN
            status = "Excellent"
        elif score >= 60:
            color = Fore.CYAN
            status = "Good"
        elif score >= 40:
            color = Fore.YELLOW
            status = "Moderate"
        else:
            color = Fore.RED
            status = "Low"

        # Create progress bar (30 characters wide)
        bar_length = 30
        filled = int((score / 100) * bar_length)
        bar = "█" * filled + "░" * (bar_length - filled)

        # Display maturity progress
        print(f"\n{color}┌─ {phase.upper()} PHASE MATURITY " f"─────────────────────┐")
        print(f"│ {bar} {score:5.1f}% ({status})      │")
        print(f"└────────────────────────────────────────────────┘{Style.RESET_ALL}")

        # Display warnings if present
        if warnings:
            print(f"\n{Fore.YELLOW}Suggestions:{Style.RESET_ALL}")
            for warning in warnings[:3]:  # Top 3 warnings
                print(f"  • {warning}")

        # Notify if ready to advance
        if score >= 100:
            print(
                f"{Fore.GREEN}✓ Phase complete! Use /advance to move to "
                f"next phase or continue enriching.{Style.RESET_ALL}"
            )
        elif score >= 60:
            print(
                f"{Fore.CYAN}✓ Ready to advance when you'd like. "
                f"Current maturity is sufficient.{Style.RESET_ALL}"
            )

    @staticmethod
    def display_detailed_maturity(maturity: Dict) -> None:
        """
        Display detailed maturity breakdown for /maturity command.

        Shows complete category breakdown, strongest/weakest areas,
        missing coverage, and detailed statistics.
        """
        score = maturity.get("overall_score", 0.0)
        phase = maturity.get("phase", "unknown")
        category_scores = maturity.get("category_scores", {})
        total_specs = maturity.get("total_specs", 0)
        is_ready = maturity.get("is_ready_to_advance", False)
        strongest = maturity.get("strongest_categories", [])
        weakest = maturity.get("weakest_categories", [])
        missing = maturity.get("missing_categories", [])

        # Header
        print(f"\n{Fore.CYAN}{'=' * 65}")
        print(f"{phase.upper()} PHASE MATURITY REPORT")
        print(f"{'=' * 65}{Style.RESET_ALL}\n")

        # Overall summary
        status = "Ready to Advance" if is_ready else "Needs More Work"
        ready_color = Fore.GREEN if is_ready else Fore.RED
        print(f"Overall Maturity: {Fore.CYAN}{score:.1f}%{Style.RESET_ALL}")
        print(f"Total Specifications: {total_specs}")
        print(f"Status: {ready_color}{status}{Style.RESET_ALL}")
        print("Threshold for Advancement: 60%\n")

        # Category breakdown with bars
        print(f"{Fore.CYAN}Category Breakdown:{Style.RESET_ALL}")
        print(f"{'Category':<25} {'Progress':<35} {'Score':<15} {'Specs':<6}")
        print(f"{'-' * 80}")

        for category in sorted(category_scores.keys()):
            cat_data = category_scores[category]
            percentage = cat_data.get("percentage", 0.0)
            current = cat_data.get("current_score", 0.0)
            target = cat_data.get("target_score", 0.0)
            spec_count = cat_data.get("spec_count", 0)

            # Color based on percentage
            if percentage >= 80:
                color = Fore.GREEN
            elif percentage >= 50:
                color = Fore.YELLOW
            else:
                color = Fore.RED

            # Progress bar (20 chars wide)
            bar_width = 20
            filled = int((percentage / 100) * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)

            print(
                f"{category:<25} {color}{bar}{Style.RESET_ALL} "
                f"{percentage:5.1f}% {current:4.1f}/{target:4.1f} "
                f"{spec_count:3} specs"
            )

        # Strengths
        if strongest:
            print(f"\n{Fore.GREEN}Strongest Areas (>80% complete):{Style.RESET_ALL}")
            for category in strongest:
                if category in category_scores:
                    pct = category_scores[category].get("percentage", 0.0)
                    print(f"  {Fore.GREEN}✓{Style.RESET_ALL} {category} ({pct:.1f}%)")

        # Weaknesses
        if weakest:
            print(f"\n{Fore.YELLOW}Areas Needing Attention (<50% complete):{Style.RESET_ALL}")
            for category in weakest:
                if category in category_scores:
                    pct = category_scores[category].get("percentage", 0.0)
                    print(f"  {Fore.YELLOW}•{Style.RESET_ALL} {category} ({pct:.1f}%)")

        # Missing coverage
        if missing:
            print(f"\n{Fore.RED}Missing Coverage (no specifications):{Style.RESET_ALL}")
            # Group by 3 per line for readability
            for i in range(0, len(missing), 3):
                categories = missing[i : i + 3]
                print(f"  {Fore.RED}✗{Style.RESET_ALL} " + ", ".join(categories))

        # Recommendations
        print(f"\n{Fore.CYAN}Recommendations:{Style.RESET_ALL}")
        if score < 40:
            print(
                "  • Phase maturity is low. Consider answering more questions "
                "to build a solid foundation."
            )
        elif score < 60:
            print(
                "  • Phase maturity is below recommended (60%). "
                "You can advance, but be prepared for rework."
            )
        else:
            print("  • Phase maturity is good. Ready to advance to next phase.")

        if missing:
            print(f"  • Focus on these missing categories: " f"{', '.join(missing[:3])}")

        if weakest:
            weak_categories = ", ".join(weakest[:3])
            print(f"  • Strengthen these weak areas: {weak_categories}")

        print(f"\n{Fore.CYAN}{'=' * 65}{Style.RESET_ALL}\n")

    @staticmethod
    def display_maturity_summary_all_phases(summary: Dict) -> None:
        """
        Display maturity summary across all phases.

        Shows one-line summary for each phase.
        """
        print(f"\n{Fore.CYAN}{'=' * 65}")
        print("PROJECT MATURITY ACROSS ALL PHASES")
        print(f"{'=' * 65}{Style.RESET_ALL}\n")

        print(f"{'Phase':<20} {'Maturity':<35} {'Status':<15}")
        print(f"{'-' * 70}")

        for phase in ["discovery", "analysis", "design", "implementation"]:
            phase_data = summary.get(phase, {})
            score = phase_data.get("score", 0.0)
            is_ready = phase_data.get("ready", False)
            is_complete = phase_data.get("complete", False)

            # Determine color
            if is_complete:
                color = Fore.GREEN
                status = "COMPLETE"
            elif is_ready:
                color = Fore.CYAN
                status = "READY"
            elif score >= 25:
                color = Fore.YELLOW
                status = "IN PROGRESS"
            else:
                color = Fore.RED
                status = "NOT STARTED"

            # Progress bar
            bar_width = 20
            filled = int((score / 100) * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)

            print(
                f"{phase.capitalize():<20} {color}{bar}{Style.RESET_ALL} "
                f"{score:5.1f}% {status:>15}"
            )

        print(f"\n{Fore.CYAN}{'=' * 65}{Style.RESET_ALL}\n")

    @staticmethod
    def display_maturity_history(history: List[Dict]) -> None:
        """
        Display maturity progression history.

        Shows timeline of maturity changes with events and deltas.
        """
        if not history:
            print(f"{Fore.YELLOW}No maturity history available yet.{Style.RESET_ALL}\n")
            return

        print(f"\n{Fore.CYAN}{'=' * 80}")
        print("MATURITY PROGRESSION TIMELINE")
        print(f"{'=' * 80}{Style.RESET_ALL}\n")

        print(f"{'Timestamp':<25} {'Phase':<15} {'Score':<10} " f"{'Delta':<10} {'Event Type':<20}")
        print(f"{'-' * 80}")

        # Show last 15 events
        for event in history[-15:]:
            timestamp = event.get("timestamp", "")
            phase = event.get("phase", "")
            score_after = event.get("score_after", 0.0)
            delta = event.get("delta", 0.0)
            event_type = event.get("event_type", "")

            # Format timestamp (show only time portion if today, full date if older)
            if len(timestamp) > 10:
                time_str = timestamp[11:19]  # HH:MM:SS
            else:
                time_str = timestamp

            # Color delta
            if delta > 0:
                delta_color = Fore.GREEN
                delta_str = f"+{delta:.1f}%"
            elif delta < 0:
                delta_color = Fore.RED
                delta_str = f"{delta:.1f}%"
            else:
                delta_color = Fore.YELLOW
                delta_str = "0.0%"

            print(
                f"{time_str:<25} {phase:<15} {score_after:5.1f}%   "
                f"{delta_color}{delta_str:<10}{Style.RESET_ALL} {event_type:<20}"
            )

        print(f"\n{Fore.CYAN}{'=' * 80}{Style.RESET_ALL}\n")

    @staticmethod
    def display_phase_completion_status(
        all_maturity_scores: Dict[str, float],
    ) -> None:
        """
        Display which phases are complete and eligible for advancement.
        """
        print(f"\n{Fore.CYAN}Phase Completion Status:{Style.RESET_ALL}")

        for phase in ["discovery", "analysis", "design", "implementation"]:
            score = all_maturity_scores.get(phase, 0.0)

            if score >= 100:
                print(
                    f"  {Fore.GREEN}✓{Style.RESET_ALL} {phase.capitalize():<15} "
                    f"{Fore.GREEN}100% (Complete){Style.RESET_ALL}"
                )
            elif score >= 60:
                print(
                    f"  {Fore.CYAN}→{Style.RESET_ALL} {phase.capitalize():<15} "
                    f"{Fore.CYAN}{score:.1f}% (Ready){Style.RESET_ALL}"
                )
            elif score > 0:
                print(
                    f"  {Fore.YELLOW}◐{Style.RESET_ALL} {phase.capitalize():<15} "
                    f"{Fore.YELLOW}{score:.1f}% (In Progress){Style.RESET_ALL}"
                )
            else:
                print(
                    f"  {Fore.RED}◯{Style.RESET_ALL} {phase.capitalize():<15} "
                    f"{Fore.RED}0% (Not Started){Style.RESET_ALL}"
                )

        print()
