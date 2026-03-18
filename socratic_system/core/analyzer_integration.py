"""
Code analyzer integration using socratic-analyzer library.

Provides comprehensive code analysis including quality metrics, security analysis,
and performance recommendations using socratic-analyzer's AnalyzerClient.
"""

import logging
from typing import Any, Dict, List, Optional

from socratic_analyzer import AnalyzerClient, AnalysisConfig, AnalysisType


class AnalyzerIntegration:
    """
    Integrated code analysis system providing:
    - Code quality metrics and analysis
    - Security vulnerability detection
    - Performance analysis and recommendations
    - Architecture analysis and design pattern detection
    """

    def __init__(self, config: Optional[AnalysisConfig] = None):
        """
        Initialize analyzer integration.

        Args:
            config: Optional AnalysisConfig for customization
        """
        self.logger = logging.getLogger("socrates.analyzer")

        try:
            # Use provided config or create default
            if config is None:
                config = AnalysisConfig(
                    enable_security=True,
                    enable_performance=True,
                    enable_quality=True,
                    enable_architecture=True
                )

            self.analyzer = AnalyzerClient(config=config)
            self.logger.info("AnalyzerClient initialized (socratic-analyzer)")

        except Exception as e:
            self.logger.error(f"Failed to initialize analyzer integration: {e}")
            raise

    def analyze_code(
        self,
        code: str,
        language: str = "python",
        file_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Perform comprehensive analysis on code.

        Args:
            code: Source code to analyze
            language: Programming language
            file_path: Optional file path for context

        Returns:
            Analysis result with quality, security, and performance metrics
        """
        try:
            result = self.analyzer.analyze(
                code=code,
                language=language,
                file_path=file_path
            )

            return {
                "language": language,
                "file_path": file_path,
                "quality": self._extract_quality_metrics(result),
                "security": self._extract_security_issues(result),
                "performance": self._extract_performance_issues(result),
                "architecture": self._extract_architecture_insights(result),
                "overall_score": getattr(result, "overall_score", 0.0),
                "recommendations": self._extract_recommendations(result)
            }

        except Exception as e:
            self.logger.error(f"Failed to analyze code: {e}")
            return {
                "error": str(e),
                "language": language,
                "file_path": file_path
            }

    def analyze_quality(
        self,
        code: str,
        language: str = "python"
    ) -> Dict[str, Any]:
        """
        Analyze code quality metrics.

        Args:
            code: Source code to analyze
            language: Programming language

        Returns:
            Quality metrics and issues
        """
        try:
            result = self.analyzer.analyze_quality(
                code=code,
                language=language
            )

            return self._extract_quality_metrics(result)

        except Exception as e:
            self.logger.error(f"Failed to analyze quality: {e}")
            return {"error": str(e)}

    def analyze_security(
        self,
        code: str,
        language: str = "python"
    ) -> Dict[str, Any]:
        """
        Analyze code for security vulnerabilities.

        Args:
            code: Source code to analyze
            language: Programming language

        Returns:
            Security issues and recommendations
        """
        try:
            result = self.analyzer.analyze_security(
                code=code,
                language=language
            )

            return self._extract_security_issues(result)

        except Exception as e:
            self.logger.error(f"Failed to analyze security: {e}")
            return {"error": str(e), "issues": []}

    def analyze_performance(
        self,
        code: str,
        language: str = "python"
    ) -> Dict[str, Any]:
        """
        Analyze code for performance issues.

        Args:
            code: Source code to analyze
            language: Programming language

        Returns:
            Performance issues and optimization suggestions
        """
        try:
            result = self.analyzer.analyze_performance(
                code=code,
                language=language
            )

            return self._extract_performance_issues(result)

        except Exception as e:
            self.logger.error(f"Failed to analyze performance: {e}")
            return {"error": str(e), "issues": []}

    def get_recommendations(
        self,
        code: str,
        language: str = "python",
        priority: str = "high"
    ) -> List[Dict[str, Any]]:
        """
        Get actionable recommendations for code improvement.

        Args:
            code: Source code to analyze
            language: Programming language
            priority: Minimum priority level (high, medium, low)

        Returns:
            List of recommendations
        """
        try:
            result = self.analyzer.get_recommendations(
                code=code,
                language=language,
                min_priority=priority
            )

            recommendations = []
            for rec in getattr(result, "recommendations", []):
                recommendations.append({
                    "type": getattr(rec, "type", "improvement"),
                    "priority": getattr(rec, "priority", "medium"),
                    "description": getattr(rec, "description", ""),
                    "affected_lines": getattr(rec, "affected_lines", []),
                    "suggested_fix": getattr(rec, "suggested_fix", ""),
                    "impact": getattr(rec, "impact", "unknown")
                })

            return recommendations

        except Exception as e:
            self.logger.error(f"Failed to get recommendations: {e}")
            return []

    def check_design_patterns(
        self,
        code: str,
        language: str = "python"
    ) -> Dict[str, Any]:
        """
        Detect and analyze design patterns in code.

        Args:
            code: Source code to analyze
            language: Programming language

        Returns:
            Detected patterns and architectural insights
        """
        try:
            result = self.analyzer.check_design_patterns(
                code=code,
                language=language
            )

            return self._extract_architecture_insights(result)

        except Exception as e:
            self.logger.error(f"Failed to check design patterns: {e}")
            return {"error": str(e), "patterns": []}

    def compare_code(
        self,
        code1: str,
        code2: str,
        language: str = "python"
    ) -> Dict[str, Any]:
        """
        Compare two code samples for quality improvements.

        Args:
            code1: Original code
            code2: Modified/new code
            language: Programming language

        Returns:
            Comparison results and improvement metrics
        """
        try:
            result = self.analyzer.compare(
                code_before=code1,
                code_after=code2,
                language=language
            )

            return {
                "quality_change": getattr(result, "quality_delta", 0.0),
                "security_improvement": getattr(result, "security_delta", 0.0),
                "performance_improvement": getattr(result, "performance_delta", 0.0),
                "complexity_change": getattr(result, "complexity_delta", 0.0),
                "summary": getattr(result, "summary", ""),
                "detailed_changes": self._extract_changes(result)
            }

        except Exception as e:
            self.logger.error(f"Failed to compare code: {e}")
            return {"error": str(e)}

    def estimate_complexity(
        self,
        code: str,
        language: str = "python"
    ) -> Dict[str, Any]:
        """
        Estimate code complexity metrics.

        Args:
            code: Source code
            language: Programming language

        Returns:
            Complexity metrics (cyclomatic, cognitive, etc.)
        """
        try:
            result = self.analyzer.estimate_complexity(
                code=code,
                language=language
            )

            return {
                "cyclomatic_complexity": getattr(result, "cyclomatic", 0),
                "cognitive_complexity": getattr(result, "cognitive", 0),
                "maintainability_index": getattr(result, "maintainability", 0.0),
                "lines_of_code": getattr(result, "loc", 0),
                "comment_ratio": getattr(result, "comment_ratio", 0.0),
                "assessment": getattr(result, "assessment", "unknown")
            }

        except Exception as e:
            self.logger.error(f"Failed to estimate complexity: {e}")
            return {"error": str(e)}

    # ========================================================================
    # Helper methods for extracting analysis results
    # ========================================================================

    def _extract_quality_metrics(self, result: Any) -> Dict[str, Any]:
        """Extract quality metrics from analysis result."""
        return {
            "score": getattr(result, "quality_score", 0.0),
            "maintainability": getattr(result, "maintainability", 0.0),
            "readability": getattr(result, "readability", 0.0),
            "testability": getattr(result, "testability", 0.0),
            "issues": self._extract_quality_issues(result),
            "metrics": {
                "cyclomatic_complexity": getattr(result, "cyclomatic_complexity", 0),
                "cognitive_complexity": getattr(result, "cognitive_complexity", 0),
                "lines_of_code": getattr(result, "loc", 0)
            }
        }

    def _extract_security_issues(self, result: Any) -> Dict[str, Any]:
        """Extract security issues from analysis result."""
        issues = []
        for issue in getattr(result, "security_issues", []):
            issues.append({
                "severity": getattr(issue, "severity", "unknown"),
                "type": getattr(issue, "type", ""),
                "description": getattr(issue, "description", ""),
                "cwe": getattr(issue, "cwe", None),
                "line": getattr(issue, "line", -1),
                "fix_suggestion": getattr(issue, "fix", "")
            })

        return {
            "security_score": getattr(result, "security_score", 0.0),
            "total_issues": len(issues),
            "critical": sum(1 for i in issues if i.get("severity") == "critical"),
            "high": sum(1 for i in issues if i.get("severity") == "high"),
            "medium": sum(1 for i in issues if i.get("severity") == "medium"),
            "low": sum(1 for i in issues if i.get("severity") == "low"),
            "issues": issues
        }

    def _extract_performance_issues(self, result: Any) -> Dict[str, Any]:
        """Extract performance issues from analysis result."""
        issues = []
        for issue in getattr(result, "performance_issues", []):
            issues.append({
                "type": getattr(issue, "type", ""),
                "description": getattr(issue, "description", ""),
                "impact": getattr(issue, "impact", "unknown"),
                "line": getattr(issue, "line", -1),
                "optimization_suggestion": getattr(issue, "suggestion", "")
            })

        return {
            "performance_score": getattr(result, "performance_score", 0.0),
            "total_issues": len(issues),
            "critical": sum(1 for i in issues if i.get("impact") == "critical"),
            "high": sum(1 for i in issues if i.get("impact") == "high"),
            "issues": issues
        }

    def _extract_architecture_insights(self, result: Any) -> Dict[str, Any]:
        """Extract architecture and design pattern insights."""
        patterns = []
        for pattern in getattr(result, "patterns", []):
            patterns.append({
                "name": getattr(pattern, "name", ""),
                "type": getattr(pattern, "type", ""),
                "description": getattr(pattern, "description", ""),
                "instances": getattr(pattern, "instances", [])
            })

        return {
            "patterns_detected": patterns,
            "architecture_score": getattr(result, "architecture_score", 0.0),
            "style_consistency": getattr(result, "style_consistency", 0.0),
            "decoupling_score": getattr(result, "decoupling", 0.0),
            "insights": getattr(result, "insights", [])
        }

    def _extract_recommendations(self, result: Any) -> List[Dict[str, Any]]:
        """Extract actionable recommendations."""
        recommendations = []
        for rec in getattr(result, "recommendations", []):
            recommendations.append({
                "priority": getattr(rec, "priority", "medium"),
                "category": getattr(rec, "category", ""),
                "description": getattr(rec, "description", ""),
                "expected_benefit": getattr(rec, "benefit", ""),
                "effort": getattr(rec, "effort", "unknown")
            })

        return recommendations

    def _extract_quality_issues(self, result: Any) -> List[Dict[str, Any]]:
        """Extract code quality issues."""
        issues = []
        for issue in getattr(result, "quality_issues", []):
            issues.append({
                "type": getattr(issue, "type", ""),
                "description": getattr(issue, "description", ""),
                "severity": getattr(issue, "severity", "medium"),
                "line": getattr(issue, "line", -1),
                "suggestion": getattr(issue, "suggestion", "")
            })

        return issues

    def _extract_changes(self, result: Any) -> List[Dict[str, Any]]:
        """Extract detailed changes from comparison."""
        changes = []
        for change in getattr(result, "changes", []):
            changes.append({
                "type": getattr(change, "type", ""),
                "description": getattr(change, "description", ""),
                "impact": getattr(change, "impact", ""),
                "before": getattr(change, "before", ""),
                "after": getattr(change, "after", "")
            })

        return changes

    def close(self):
        """Close analyzer integration"""
        try:
            self.logger.info("Analyzer integration closed")
        except Exception as e:
            self.logger.error(f"Error closing analyzer integration: {e}")

    def __del__(self):
        """Cleanup on object deletion"""
        try:
            self.close()
        except Exception:
            pass
