"""
NOTE: Responses now use APIResponse format with data wrapped in "data" field.
Security monitoring and incident tracking commands
"""

from typing import Any, Dict, List
from colorama import Fore, Style
from socratic_system.ui.commands.base import BaseCommand


class SecurityStatusCommand(BaseCommand):
    """Display security status and recent incidents"""

    def __init__(self):
        super().__init__(
            name="security status",
            description="Show system security status",
            usage="security status",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        orchestrator = context.get("orchestrator")
        if not orchestrator:
            return self.error("Orchestrator not available")

        try:
            incidents = []
            if hasattr(orchestrator.database, "get_security_incidents"):
                incidents = orchestrator.database.get_security_incidents(limit=10)

            self.print_header("Security Status Report")

            total = len(incidents) if incidents else 0
            critical = sum(1 for i in incidents if i.get("severity") == "critical")
            high = sum(1 for i in incidents if i.get("severity") == "high")

            print(f"\n{Fore.CYAN}Overall Status:{Style.RESET_ALL}")
            status = "Secure" if critical == 0 else "Alert"
            status_color = Fore.GREEN if critical == 0 else Fore.RED
            print(f"  {status_color}{status}{Style.RESET_ALL}")

            print(f"\n{Fore.CYAN}Incident Summary:{Style.RESET_ALL}")
            print(f"  Total: {total}")
            print(f"  Critical: {Fore.RED}{critical}{Style.RESET_ALL}")
            print(f"  High: {Fore.YELLOW}{high}{Style.RESET_ALL}")

            return self.success(data={
                "total_incidents": total,
                "critical": critical,
                "high": high,
            })

        except Exception as e:
            return self.error(f"Failed: {str(e)}")


class SecurityIncidentsCommand(BaseCommand):
    """List security incidents"""

    def __init__(self):
        super().__init__(
            name="security incidents",
            description="List security incidents with optional filter",
            usage="security incidents [severity]",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        orchestrator = context.get("orchestrator")
        if not orchestrator:
            return self.error("Orchestrator not available")

        severity = args[0].lower() if args else None

        try:
            incidents = []
            if hasattr(orchestrator.database, "get_security_incidents"):
                incidents = orchestrator.database.get_security_incidents(severity=severity, limit=50)

            if not incidents:
                self.print_info("No incidents found")
                return self.success(data={"incidents": [], "count": 0})

            self.print_header("Security Incidents")

            incidents_data = []
            for inc in incidents:
                inc_dict = {
                    "id": inc.get("incident_id"),
                    "type": inc.get("incident_type"),
                    "severity": inc.get("severity"),
                    "detected_at": inc.get("detected_at"),
                }
                incidents_data.append(inc_dict)

                sev_color = Fore.RED if inc_dict["severity"] == "critical" else Fore.YELLOW
                print(f"\n{Fore.CYAN}[{inc_dict['id']}]{Style.RESET_ALL}")
                print(f"  Type: {inc_dict['type']}")
                print(f"  Severity: {sev_color}{inc_dict['severity'].upper()}{Style.RESET_ALL}")
                print(f"  Detected: {inc_dict['detected_at']}")

            return self.success(data={
                "incidents": incidents_data,
                "count": len(incidents_data),
            })

        except Exception as e:
            return self.error(f"Failed: {str(e)}")


class SecurityValidateCommand(BaseCommand):
    """Validate input for security threats"""

    def __init__(self):
        super().__init__(
            name="security validate",
            description="Validate input for security vulnerabilities",
            usage="security validate",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        orchestrator = context.get("orchestrator")
        if not orchestrator:
            return self.error("Orchestrator not available")

        library_manager = orchestrator.library_manager
        if not library_manager or not library_manager.security:
            return self.error("Security validation not available")

        user_input = input(f"{Fore.WHITE}Enter text to validate: ").strip()
        if not user_input:
            return self.error("Input cannot be empty")

        try:
            result = library_manager.security.validate_input(user_input)

            self.print_header("Security Validation Result")

            is_valid = result.get("valid", True)
            score = result.get("security_score", 100)
            threats = result.get("threats", [])

            status_color = Fore.GREEN if is_valid else Fore.RED
            status_text = "VALID" if is_valid else "THREATS DETECTED"
            print(f"\n{Fore.CYAN}Status:{Style.RESET_ALL} {status_color}{status_text}{Style.RESET_ALL}")
            print(f"{Fore.CYAN}Security Score:{Style.RESET_ALL} {score}/100")

            if threats:
                print(f"\n{Fore.CYAN}Detected Threats:{Style.RESET_ALL}")
                for threat in threats:
                    print(f"  - {Fore.RED}{threat.upper()}{Style.RESET_ALL}")

                if hasattr(orchestrator.database, "save_security_incident"):
                    orchestrator.database.save_security_incident(
                        incident_type="validation_failed",
                        severity="high" if len(threats) > 2 else "medium",
                        details={"threats": threats, "score": score}
                    )
            else:
                self.print_success("No security threats detected")

            return self.success(data={
                "valid": is_valid,
                "security_score": score,
                "threats": threats,
            })

        except Exception as e:
            return self.error(f"Failed: {str(e)}")


class SecurityTrendsCommand(BaseCommand):
    """Show security trends over time"""

    def __init__(self):
        super().__init__(
            name="security trends",
            description="Display security incident trends",
            usage="security trends",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        orchestrator = context.get("orchestrator")
        if not orchestrator:
            return self.error("Orchestrator not available")

        try:
            trends = {}
            if hasattr(orchestrator.database, "get_security_trends"):
                trends = orchestrator.database.get_security_trends()

            self.print_header("Security Trends")

            if not trends:
                self.print_info("No trend data available")
                return self.success(data={"trends": {}})

            print(f"\n{Fore.CYAN}Incidents by Type:{Style.RESET_ALL}")
            for incident_type, count in sorted(trends.items(), key=lambda x: x[1], reverse=True):
                bar = "=" * (count // 2) if count > 0 else ""
                print(f"  {incident_type:20} {bar} {count}")

            return self.success(data={"trends": trends})

        except Exception as e:
            return self.error(f"Failed: {str(e)}")
