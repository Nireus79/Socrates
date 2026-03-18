"""
Code Validation Agent for Socrates AI

Orchestrates comprehensive code validation pipeline:
1. Syntax validation (all files)
2. Dependency validation
3. Test execution
4. Report generation with recommendations
"""

import logging
from typing import Any, Dict, List

from socratic_system.agents.base import Agent
from socratic_system.events import EventType
from socratic_system.utils.validators import (
    DependencyValidator,
    SyntaxValidator,
    TestExecutor,
)

logger = logging.getLogger("socrates.agents.code_validation_agent")


class CodeValidationAgent(Agent):
    """Orchestrates code validation pipeline"""

    def __init__(self, orchestrator):
        super().__init__("CodeValidation", orchestrator)
        self.syntax_validator = SyntaxValidator()
        self.dependency_validator = DependencyValidator()
        self.test_executor = TestExecutor()

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process code validation requests"""
        action = request.get("action")

        action_handlers = {
            "validate_project": self._validate_project,
            "validate_file": self._validate_file,
            "run_tests": self._run_tests,
            "check_syntax": self._check_syntax,
            "check_dependencies": self._check_dependencies,
        }

        handler = action_handlers.get(action)
        if handler:
            return handler(request)

        return {"status": "error", "message": "Unknown action"}

    def _validate_project(self, request: Dict) -> Dict:
        """
        Run complete validation pipeline on project

        Pipeline:
        1. Syntax validation (all files)
        2. Dependency validation
        3. Test execution (if syntax and deps pass)
        4. Generate comprehensive report
        """
        project_path = request.get("project_path")
        timeout = request.get("timeout", 300)

        if not project_path:
            return {"status": "error", "message": "project_path is required"}

        try:
            self.log(f"Starting complete validation pipeline for {project_path}")

            # Phase 1: Syntax Validation
            self.log("Phase 1: Validating syntax...")
            syntax_result = self.syntax_validator.validate(project_path)

            # Phase 2: Dependency Validation
            self.log("Phase 2: Validating dependencies...")
            dependency_result = self.dependency_validator.validate(project_path)

            # Phase 3: Test Execution (only if syntax and deps pass)
            test_result = None
            if syntax_result.get("valid") and dependency_result.get("valid"):
                self.log("Phase 3: Running tests...")
                test_result = self.test_executor.validate(project_path, timeout)
            else:
                self.log("Skipping tests: syntax or dependency validation failed")
                test_result = {
                    "status": "skipped",
                    "tests_found": False,
                    "tests_passed": 0,
                    "tests_failed": 0,
                    "tests_skipped": 0,
                    "duration_seconds": 0,
                    "framework": "unknown",
                    "failures": [],
                    "output": "Skipped due to syntax/dependency issues",
                }

            # Generate summary
            summary = self._generate_summary(syntax_result, dependency_result, test_result)

            # Generate recommendations
            recommendations = self._generate_recommendations(
                syntax_result, dependency_result, test_result
            )

            # Emit event
            self.emit_event(
                EventType.CODE_ANALYSIS_COMPLETE,
                {
                    "validation_status": summary["overall_status"],
                    "issues": summary["issues_count"],
                    "warnings": summary["warnings_count"],
                },
            )

            self.log(
                f"Validation complete: {summary['overall_status']} "
                f"({summary['issues_count']} issues, {summary['warnings_count']} warnings)"
            )

            return {
                "status": "success",
                "validation_summary": summary,
                "validation_results": {
                    "syntax": syntax_result,
                    "dependencies": dependency_result,
                    "tests": test_result,
                },
                "recommendations": recommendations,
            }

        except Exception as e:
            self.log(f"ERROR: Validation pipeline failed: {e}", level="ERROR")
            return {
                "status": "error",
                "message": f"Validation pipeline failed: {str(e)}",
                "validation_summary": {
                    "overall_status": "error",
                    "issues_count": 0,
                    "warnings_count": 0,
                },
            }

    def _validate_file(self, request: Dict) -> Dict:
        """Validate single file syntax"""
        file_path = request.get("file_path")

        if not file_path:
            return {"status": "error", "message": "file_path is required"}

        try:
            self.log(f"Validating file: {file_path}")
            result = self.syntax_validator.validate(file_path)

            return {
                "status": "success",
                "validation_result": result,
            }
        except Exception as e:
            self.log(f"ERROR: File validation failed: {e}", level="ERROR")
            return {
                "status": "error",
                "message": f"File validation failed: {str(e)}",
            }

    def _run_tests(self, request: Dict) -> Dict:
        """Run tests only"""
        project_path = request.get("project_path")
        timeout = request.get("timeout", 300)

        if not project_path:
            return {"status": "error", "message": "project_path is required"}

        try:
            self.log(f"Running tests for project: {project_path}")
            result = self.test_executor.validate(project_path, timeout)

            return {
                "status": "success",
                "test_results": result,
            }
        except Exception as e:
            self.log(f"ERROR: Test execution failed: {e}", level="ERROR")
            return {
                "status": "error",
                "message": f"Test execution failed: {str(e)}",
            }

    def _check_syntax(self, request: Dict) -> Dict:
        """Check syntax only"""
        target = request.get("target")

        if not target:
            return {"status": "error", "message": "target is required"}

        try:
            self.log(f"Checking syntax: {target}")
            result = self.syntax_validator.validate(target)

            return {
                "status": "success",
                "syntax_result": result,
            }
        except Exception as e:
            self.log(f"ERROR: Syntax check failed: {e}", level="ERROR")
            return {
                "status": "error",
                "message": f"Syntax check failed: {str(e)}",
            }

    def _check_dependencies(self, request: Dict) -> Dict:
        """Check dependencies only"""
        project_path = request.get("project_path")

        if not project_path:
            return {"status": "error", "message": "project_path is required"}

        try:
            self.log(f"Checking dependencies: {project_path}")
            result = self.dependency_validator.validate(project_path)

            return {
                "status": "success",
                "dependency_result": result,
            }
        except Exception as e:
            self.log(f"ERROR: Dependency check failed: {e}", level="ERROR")
            return {
                "status": "error",
                "message": f"Dependency check failed: {str(e)}",
            }

    def _generate_summary(
        self, syntax_result: Dict, dependency_result: Dict, test_result: Dict
    ) -> Dict:
        """
        Generate validation summary from results

        Returns:
            {
                "overall_status": "pass" | "warning" | "fail",
                "issues_count": int,
                "warnings_count": int,
                "syntax_valid": bool,
                "dependencies_valid": bool,
                "tests_status": str,
                "details": str
            }
        """
        issues_count = 0
        warnings_count = 0
        overall_status = "pass"

        # Count syntax issues
        syntax_valid = syntax_result.get("valid", True)
        issues_count += len(syntax_result.get("issues", []))
        warnings_count += len(syntax_result.get("warnings", []))

        # Count dependency issues
        dependencies_valid = dependency_result.get("valid", True)
        issues_count += len(dependency_result.get("issues", []))
        warnings_count += len(dependency_result.get("warnings", []))

        # Check test results
        tests_status = "not_run"
        if test_result:
            if test_result.get("status") == "timeout":
                tests_status = "timeout"
                issues_count += 1
            elif test_result.get("tests_failed", 0) > 0:
                tests_status = "failed"
                issues_count += test_result.get("tests_failed", 0)
            elif test_result.get("tests_found", False):
                tests_status = "passed"
            else:
                tests_status = "not_found"

        # Determine overall status
        if issues_count > 0:
            overall_status = "fail"
        elif warnings_count > 0 or (test_result and test_result.get("status") == "error"):
            overall_status = "warning"
        else:
            overall_status = "pass"

        return {
            "overall_status": overall_status,
            "issues_count": issues_count,
            "warnings_count": warnings_count,
            "syntax_valid": syntax_valid,
            "dependencies_valid": dependencies_valid,
            "tests_status": tests_status,
            "details": self._format_summary_details(syntax_result, dependency_result, test_result),
        }

    def _generate_recommendations(
        self, syntax_result: Dict, dependency_result: Dict, test_result: Dict
    ) -> List[str]:
        """Generate actionable recommendations based on validation results"""
        recommendations = []
        recommendations.extend(self._syntax_recommendations(syntax_result))
        recommendations.extend(self._dependency_recommendations(dependency_result))
        recommendations.extend(self._test_recommendations(test_result))
        recommendations.extend(self._general_recommendations(syntax_result, dependency_result))
        recommendations.extend(self._codebase_recommendations(syntax_result))
        return recommendations[:5]  # Limit to 5 recommendations

    def _syntax_recommendations(self, syntax_result: Dict) -> List[str]:
        """Generate syntax-related recommendations"""
        if not syntax_result.get("valid"):
            issues = syntax_result.get("issues", [])
            if issues:
                return [f"Fix {len(issues)} syntax error(s) before proceeding"]
        return []

    def _dependency_recommendations(self, dependency_result: Dict) -> List[str]:
        """Generate dependency-related recommendations"""
        recommendations = []
        if not dependency_result.get("valid"):
            issues = dependency_result.get("issues", [])
            for issue in issues:
                if "missing" in issue.get("message", "").lower():
                    missing = issue.get("missing_modules", [])
                    if missing:
                        recommendations.append(
                            f"Install missing dependencies: {', '.join(missing)}"
                        )
        return recommendations

    def _test_recommendations(self, test_result: Dict) -> List[str]:
        """Generate test-related recommendations"""
        if not test_result:
            return []
        if test_result.get("tests_found", False):
            if test_result.get("tests_failed", 0) > 0:
                return [f"Fix {test_result.get('tests_failed', 0)} failing test(s)"]
        else:
            return ["Consider adding unit tests to improve code quality"]
        return []

    def _general_recommendations(self, syntax_result: Dict, dependency_result: Dict) -> List[str]:
        """Generate general recommendations"""
        if not syntax_result.get("issues") and not dependency_result.get("issues"):
            return ["Code structure looks good"]
        return []

    def _codebase_recommendations(self, syntax_result: Dict) -> List[str]:
        """Generate codebase-specific recommendations"""
        if syntax_result.get("metadata", {}).get("files_checked", 0) > 100:
            return ["Large codebase detected - consider code organization review"]
        return []

    def _format_summary_details(
        self, syntax_result: Dict, dependency_result: Dict, test_result: Dict
    ) -> str:
        """Format detailed summary text"""
        details = []

        # Syntax summary
        syntax_meta = syntax_result.get("metadata", {})
        if syntax_meta.get("files_checked", 0) > 0:
            details.append(
                f"Syntax: {syntax_meta.get('files_valid', 0)}/{syntax_meta.get('files_checked', 0)} files valid"
            )

        # Dependency summary
        dep_meta = dependency_result.get("metadata", {})
        total_deps = dep_meta.get("total_dependencies", 0)
        if total_deps > 0:
            missing = len(dep_meta.get("missing_imports", []))
            unused = len(dep_meta.get("unused_dependencies", []))
            details.append(f"Dependencies: {total_deps} total, {missing} missing, {unused} unused")

        # Test summary
        if test_result:
            if test_result.get("tests_found", False):
                passed = test_result.get("tests_passed", 0)
                failed = test_result.get("tests_failed", 0)
                skipped = test_result.get("tests_skipped", 0)
                details.append(f"Tests: {passed} passed, {failed} failed, {skipped} skipped")

        return "; ".join(details) if details else "No validation details available"
