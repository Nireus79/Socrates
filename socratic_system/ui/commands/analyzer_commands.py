"""
NOTE: Responses now use APIResponse format with data wrapped in "data" field.
Code analysis and quality assessment commands
"""

from typing import Any, Dict, List
from colorama import Fore, Style
from socratic_system.ui.commands.base import BaseCommand


class AnalyzeCodeCommand(BaseCommand):
    """Analyze code for quality issues and metrics"""

    def __init__(self):
        super().__init__(
            name="analyze code",
            description="Analyze code snippet for quality and issues",
            usage="analyze code [file_path]",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute code analysis command"""
        orchestrator = context.get("orchestrator")
        if not orchestrator:
            return self.error("Orchestrator not available")

        library_manager = orchestrator.library_manager
        if not library_manager or not library_manager.analyzer:
            return self.error("Analyzer not available")

        # Get code either from file or from input
        code = None
        file_path = args[0] if args else None

        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    code = f.read()
            except Exception as e:
                return self.error(f"Failed to read file: {str(e)}")
        else:
            print(f"{Fore.WHITE}Paste code (Ctrl+D when done):{Style.RESET_ALL}")
            try:
                lines = []
                while True:
                    line = input()
                    lines.append(line)
            except EOFError:
                code = "\n".join(lines)

        if not code:
            return self.error("No code provided")

        try:
            analysis = library_manager.analyzer.analyze_code(
                code=code,
                filename=file_path or "code.py"
            )

            self.print_header("Code Analysis Report")

            issues_count = analysis.get("issues_count", 0)
            quality_score = analysis.get("quality_score", 0)
            patterns = analysis.get("patterns", [])
            recommendations = analysis.get("recommendations", [])

            print(f"\n{Fore.CYAN}Overall Metrics:{Style.RESET_ALL}")
            quality_color = Fore.GREEN if quality_score >= 80 else Fore.YELLOW if quality_score >= 60 else Fore.RED
            print(f"  Quality Score: {quality_color}{quality_score:.1f}/100{Style.RESET_ALL}")
            print(f"  Issues Found: {Fore.RED if issues_count > 5 else Fore.YELLOW if issues_count > 0 else Fore.GREEN}{issues_count}{Style.RESET_ALL}")

            if patterns:
                print(f"\n{Fore.CYAN}Detected Patterns:{Style.RESET_ALL}")
                for pattern in patterns[:5]:
                    print(f"  - {pattern}")

            if recommendations:
                print(f"\n{Fore.CYAN}Recommendations:{Style.RESET_ALL}")
                for i, rec in enumerate(recommendations[:3], 1):
                    print(f"  {i}. {rec}")

            return self.success(data={
                "issues_count": issues_count,
                "quality_score": quality_score,
                "patterns": patterns,
                "recommendations": recommendations,
                "file": file_path or "stdin",
            })

        except Exception as e:
            return self.error(f"Failed: {str(e)}")


class AnalyzeFileCommand(BaseCommand):
    """Analyze a single file for code quality"""

    def __init__(self):
        super().__init__(
            name="analyze file",
            description="Perform detailed analysis on a file",
            usage="analyze file <file_path>",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute file analysis command"""
        orchestrator = context.get("orchestrator")
        if not orchestrator:
            return self.error("Orchestrator not available")

        library_manager = orchestrator.library_manager
        if not library_manager or not library_manager.analyzer:
            return self.error("Analyzer not available")

        file_path = args[0] if args else input(f"{Fore.WHITE}File path: ").strip()
        if not file_path:
            return self.error("File path cannot be empty")

        try:
            analysis = library_manager.analyzer.analyze_file(file_path)

            if not analysis:
                return self.error(f"Failed to analyze {file_path}")

            self.print_header(f"File Analysis: {file_path}")

            quality_score = analysis.get("quality_score", 0)
            issues = analysis.get("issues", [])

            print(f"\n{Fore.CYAN}File Metrics:{Style.RESET_ALL}")
            quality_color = Fore.GREEN if quality_score >= 80 else Fore.YELLOW if quality_score >= 60 else Fore.RED
            print(f"  Quality Score: {quality_color}{quality_score:.1f}/100{Style.RESET_ALL}")
            print(f"  Total Issues: {len(issues)}")

            if issues:
                print(f"\n{Fore.CYAN}Issues Found:{Style.RESET_ALL}")
                for issue in issues[:10]:
                    severity_color = Fore.RED if issue.get("severity") == "critical" else Fore.YELLOW if issue.get("severity") == "high" else Fore.WHITE
                    print(f"\n  {severity_color}[{issue.get('severity', 'unknown').upper()}]{Style.RESET_ALL} {issue.get('type', 'unknown')}")
                    print(f"    Location: {issue.get('location', 'N/A')}")
                    print(f"    Message: {issue.get('message', 'N/A')}")
            else:
                self.print_success("No issues found")

            return self.success(data={
                "file": file_path,
                "quality_score": quality_score,
                "issues_count": len(issues),
                "issues": issues,
            })

        except Exception as e:
            return self.error(f"Failed: {str(e)}")


class AnalyzeProjectCommand(BaseCommand):
    """Analyze entire project for code quality"""

    def __init__(self):
        super().__init__(
            name="analyze project",
            description="Analyze all files in a project",
            usage="analyze project <project_path>",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute project analysis command"""
        orchestrator = context.get("orchestrator")
        if not orchestrator:
            return self.error("Orchestrator not available")

        library_manager = orchestrator.library_manager
        if not library_manager or not library_manager.analyzer:
            return self.error("Analyzer not available")

        project_path = args[0] if args else input(f"{Fore.WHITE}Project path: ").strip()
        if not project_path:
            return self.error("Project path cannot be empty")

        try:
            analysis = library_manager.analyzer.analyze_project(project_path)

            if not analysis:
                return self.error(f"Failed to analyze project at {project_path}")

            self.print_header(f"Project Analysis: {project_path}")

            files_analyzed = analysis.get("files_analyzed", 0)
            total_issues = analysis.get("total_issues", 0)
            avg_score = analysis.get("average_quality_score", 0)

            print(f"\n{Fore.CYAN}Project Summary:{Style.RESET_ALL}")
            print(f"  Files Analyzed: {files_analyzed}")
            print(f"  Total Issues: {Fore.RED if total_issues > 20 else Fore.YELLOW if total_issues > 5 else Fore.GREEN}{total_issues}{Style.RESET_ALL}")

            avg_color = Fore.GREEN if avg_score >= 80 else Fore.YELLOW if avg_score >= 60 else Fore.RED
            print(f"  Average Quality Score: {avg_color}{avg_score:.1f}/100{Style.RESET_ALL}")

            if analysis.get("files"):
                print(f"\n{Fore.CYAN}Top Files with Issues:{Style.RESET_ALL}")
                files = sorted(analysis.get("files", []), key=lambda x: x.get("issues_count", 0), reverse=True)
                for file_info in files[:5]:
                    print(f"\n  {Fore.YELLOW}{file_info.get('name', 'unknown')}{Style.RESET_ALL}")
                    print(f"    Issues: {file_info.get('issues_count', 0)}")
                    print(f"    Score: {file_info.get('quality_score', 0):.1f}/100")

            return self.success(data={
                "project": project_path,
                "files_analyzed": files_analyzed,
                "total_issues": total_issues,
                "average_quality_score": avg_score,
                "files": analysis.get("files", []),
            })

        except Exception as e:
            return self.error(f"Failed: {str(e)}")


class AnalysisIssuesCommand(BaseCommand):
    """Detect and report code smells and complexity issues"""

    def __init__(self):
        super().__init__(
            name="analysis issues",
            description="Detect code smells and complexity problems",
            usage="analysis issues <type> [file_path]",
        )

    def execute(self, args: List[str], context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute issue detection command"""
        orchestrator = context.get("orchestrator")
        if not orchestrator:
            return self.error("Orchestrator not available")

        library_manager = orchestrator.library_manager
        if not library_manager or not library_manager.analyzer:
            return self.error("Analyzer not available")

        issue_type = args[0].lower() if args else "smells"
        if issue_type not in ["smells", "complexity", "patterns"]:
            return self.error("Type must be: smells, complexity, or patterns")

        # Get code from file or input
        code = None
        file_path = args[1] if len(args) > 1 else None

        if file_path:
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    code = f.read()
            except Exception as e:
                return self.error(f"Failed to read file: {str(e)}")
        else:
            print(f"{Fore.WHITE}Paste code (Ctrl+D when done):{Style.RESET_ALL}")
            try:
                lines = []
                while True:
                    line = input()
                    lines.append(line)
            except EOFError:
                code = "\n".join(lines)

        if not code:
            return self.error("No code provided")

        try:
            issues_data = []

            if issue_type == "smells":
                smells = library_manager.analyzer.detect_smells(code)
                self.print_header("Code Smells Detected")
                issues_data = smells

                for smell in smells:
                    print(f"\n{Fore.YELLOW}{smell.get('type', 'unknown')}{Style.RESET_ALL}")
                    print(f"  Severity: {smell.get('severity', 'unknown')}")
                    print(f"  Issue: {smell.get('message', 'N/A')}")
                    if smell.get("suggestion"):
                        print(f"  Suggestion: {smell.get('suggestion')}")

            elif issue_type == "complexity":
                complex_issues = library_manager.analyzer.detect_complexity(code)
                self.print_header("Complexity Issues Detected")
                issues_data = complex_issues

                for issue in complex_issues:
                    severity_color = Fore.RED if issue.get("severity") == "high" else Fore.YELLOW
                    print(f"\n{severity_color}{issue.get('message', 'High complexity')}{Style.RESET_ALL}")
                    print(f"  Location: {issue.get('location', 'N/A')}")

            elif issue_type == "patterns":
                patterns = library_manager.analyzer.detect_patterns(code)
                self.print_header("Design Patterns Detected")

                if patterns:
                    for pattern in patterns:
                        print(f"  - {pattern}")
                else:
                    self.print_info("No design patterns detected")

                issues_data = patterns

            issue_count = len(issues_data) if isinstance(issues_data, list) else 0
            if issue_count == 0:
                self.print_success(f"No {issue_type} detected")

            return self.success(data={
                "issue_type": issue_type,
                "issues_count": issue_count,
                "issues": issues_data,
                "file": file_path or "stdin",
            })

        except Exception as e:
            return self.error(f"Failed: {str(e)}")
