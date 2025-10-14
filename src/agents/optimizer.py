#!/usr/bin/env python3
"""
ArchitectureOptimizerAgent - Meta-Level Optimization and Greedy Algorithm Prevention
====================================================================================

This agent provides global optimization analysis to prevent myopic/greedy decisions
across the entire system. It validates architecture choices, detects anti-patterns,
calculates total cost of ownership, and suggests optimal alternatives.

Core Purpose:
- Prevent greedy algorithm behavior in design decisions
- Validate architectural choices against best practices
- Calculate total cost of ownership (dev + maintenance + scaling)
- Analyze trade-offs and suggest alternatives
- Ensure requirements completeness

Capabilities:
- Global cost analysis (not local optimization)
- Greedy pattern detection in designs and questions
- Architecture anti-pattern identification
- Total Cost of Ownership (TCO) calculation
- Design trade-off analysis and alternative suggestions
- Question quality validation for completeness
"""

from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from enum import Enum

try:
    from src.core import ServiceContainer, DateTimeHelper, ValidationError
    from src.models import Project, TechnicalSpec, ProjectStatus, ProjectPhase
    from .base import BaseAgent, require_authentication, require_project_access

    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False
    # Fallback implementations
    import logging
    from datetime import datetime

    def get_logger(name):
        return logging.getLogger(name)

    class ServiceContainer:
        def get_logger(self, name):
            return logging.getLogger(name)
        def get_config(self):
            return {}
        def get_db_manager(self):
            return None

    class DateTimeHelper:
        @staticmethod
        def now():
            return datetime.now()
        @staticmethod
        def to_iso_string(dt):
            return dt.isoformat() if dt else None

    class ValidationError(Exception):
        pass

    class ProjectStatus:
        DRAFT = "draft"
        ACTIVE = "active"

    class ProjectPhase:
        PLANNING = "planning"
        DESIGN = "design"
        DEVELOPMENT = "development"


class RiskLevel(Enum):
    """Risk assessment levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class OptimizationIssueType(Enum):
    """Types of optimization issues detected"""
    GREEDY_ALGORITHM = "greedy_algorithm"
    ANTI_PATTERN = "anti_pattern"
    MISSING_REQUIREMENT = "missing_requirement"
    OVER_ENGINEERING = "over_engineering"
    UNDER_ENGINEERING = "under_engineering"
    POOR_SCALABILITY = "poor_scalability"
    HIGH_COMPLEXITY = "high_complexity"
    TECHNICAL_DEBT = "technical_debt"
    INCOMPLETE_ANALYSIS = "incomplete_analysis"


class ArchitectureOptimizerAgent(BaseAgent):
    """
    Meta-level agent for global optimization and greedy algorithm prevention

    This agent operates at a higher level than other agents, analyzing their
    outputs and decisions to ensure global optimization rather than local.
    """

    def __init__(self, services: Optional[ServiceContainer] = None):
        """Initialize Architecture Optimizer Agent"""
        super().__init__("architecture_optimizer", "Architecture Optimizer", services)

        # Initialize analysis thresholds
        self.complexity_threshold = 7.5  # Maximum acceptable complexity score
        self.tco_variance_threshold = 1.3  # Alert if alternative is 30% cheaper
        self.completeness_threshold = 0.75  # Minimum requirement coverage

        # C6.3: Initialize Design Pattern Validator
        try:
            from .pattern_validator import DesignPatternValidator
            self.pattern_validator = DesignPatternValidator()
            if self.logger:
                self.logger.info("C6.3 Design Pattern Validator initialized")
        except ImportError as e:
            self.pattern_validator = None
            if self.logger:
                self.logger.warning(f"Design Pattern Validator not available: {e}")

        # C6.4: Initialize Global Cost Calculator
        try:
            from .cost_calculator import GlobalCostCalculator, TeamSize, TeamExperience, CloudProvider
            self.cost_calculator = GlobalCostCalculator()
            # Store enums for easy access
            self.TeamSize = TeamSize
            self.TeamExperience = TeamExperience
            self.CloudProvider = CloudProvider
            if self.logger:
                self.logger.info("C6.4 Global Cost Calculator initialized")
        except ImportError as e:
            self.cost_calculator = None
            if self.logger:
                self.logger.warning(f"Global Cost Calculator not available: {e}")

        if self.logger:
            self.logger.info("ArchitectureOptimizerAgent initialized successfully")

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this agent provides"""
        return [
            "analyze_architecture",
            "detect_greedy_patterns",
            "validate_requirements",
            "calculate_tco",
            "suggest_alternatives",
            "review_questions",
            "validate_design_patterns",
            "assess_complexity",
            "analyze_tradeoffs"
        ]

    # ========================================================================
    # CORE OPTIMIZATION METHODS
    # ========================================================================

    @require_authentication
    @require_project_access
    def _analyze_architecture(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive architecture analysis for a project

        Analyzes:
        - Global optimization vs local optimization
        - Greedy algorithm patterns
        - Architecture anti-patterns
        - Total cost of ownership
        - Alternative approaches

        Args:
            data: {
                'project_id': str,
                'technical_spec': Dict (optional),
                'analysis_depth': str ('quick' | 'deep' | 'comprehensive')
            }

        Returns:
            {
                'success': bool,
                'risk_level': str,
                'issues': List[Dict],
                'recommendations': List[Dict],
                'tco_analysis': Dict,
                'alternatives': List[Dict]
            }
        """
        try:
            project_id = data.get('project_id')
            analysis_depth = data.get('analysis_depth', 'deep')

            if not project_id:
                raise ValidationError("Project ID is required for architecture analysis")

            # Get project and technical spec
            project = self.db.projects.get_by_id(project_id)
            if not project:
                raise ValidationError(f"Project {project_id} not found")

            # Get technical specification if available
            tech_specs = self.db.technical_specifications.get_by_project_id(project_id)
            tech_spec = tech_specs[0] if tech_specs else None

            # Perform multi-level analysis
            analysis_result = {
                'project_id': project_id,
                'analysis_timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                'analysis_depth': analysis_depth
            }

            # 1. Detect greedy patterns
            greedy_issues = self._detect_greedy_patterns(project, tech_spec)

            # 2. Validate architecture patterns
            pattern_issues = self._validate_architecture_patterns(project, tech_spec)

            # 2b. C6.3: Advanced pattern validation with pattern validator
            pattern_validation_result = None
            if self.pattern_validator and tech_spec:
                try:
                    pattern_validation_result = self._validate_design_patterns(project, tech_spec)
                    # Add pattern validator issues to main issues list
                    if pattern_validation_result:
                        pattern_validator_issues = self._convert_pattern_issues_to_dict(
                            pattern_validation_result.issues_found
                        )
                        pattern_issues.extend(pattern_validator_issues)
                except Exception as e:
                    self.logger.warning(f"C6.3: Pattern validation failed: {e}")

            # 3. Calculate total cost of ownership
            tco_analysis = self._calculate_tco(project, tech_spec)

            # 4. Generate alternatives
            alternatives = self._generate_alternatives(project, tech_spec, greedy_issues + pattern_issues)

            # 5. Assess overall risk
            all_issues = greedy_issues + pattern_issues
            risk_level = self._assess_risk_level(all_issues, tco_analysis)

            # 6. Generate recommendations
            recommendations = self._generate_recommendations(all_issues, alternatives, tco_analysis)

            analysis_result.update({
                'risk_level': risk_level.value,
                'issues_found': len(all_issues),
                'issues': all_issues,
                'recommendations': recommendations,
                'tco_analysis': tco_analysis,
                'alternatives': alternatives[:5] if alternatives else []  # Top 5 alternatives
            })

            # Include C6.3 pattern validation if available
            if pattern_validation_result:
                analysis_result['c6_pattern_validation'] = {
                    'pattern_detected': pattern_validation_result.pattern_detected.value,
                    'pattern_confidence': pattern_validation_result.pattern_confidence,
                    'pattern_correctly_implemented': pattern_validation_result.pattern_correctly_implemented,
                    'overall_quality_score': pattern_validation_result.overall_quality_score,
                    'pattern_strengths': pattern_validation_result.pattern_strengths,
                    'pattern_weaknesses': pattern_validation_result.pattern_weaknesses,
                    'pattern_recommendations': pattern_validation_result.recommendations
                }

            # Store analysis in database
            self._store_architecture_review(project_id, analysis_result)

            self.logger.info(f"Architecture analysis complete for project {project_id}: "
                           f"Risk={risk_level.value}, Issues={len(all_issues)}")

            return self._success_response(
                f"Architecture analysis complete: {len(all_issues)} issues found",
                analysis_result
            )

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Architecture analysis failed: {e}")
            return self._error_response(f"Architecture analysis failed: {str(e)}")

    def _detect_greedy_patterns(self, project: Any, tech_spec: Optional[Any]) -> List[Dict[str, Any]]:
        """
        Detect greedy algorithm patterns in design decisions

        Greedy patterns include:
        - Choosing technology without considering long-term consequences
        - Optimizing for immediate development speed over maintainability
        - Selecting simple solutions that won't scale
        - Making decisions without considering alternatives
        """
        issues = []

        # Pattern 1: Technology choice without consideration of requirements
        if tech_spec and tech_spec.technology_stack:
            tech_stack = tech_spec.technology_stack
            requirements = tech_spec.functional_requirements + tech_spec.non_functional_requirements

            # Check for MongoDB with relational requirements
            if 'mongodb' in str(tech_stack).lower():
                relational_keywords = ['relationship', 'join', 'foreign key', 'transaction', 'acid']
                if any(keyword in str(requirements).lower() for keyword in relational_keywords):
                    issues.append({
                        'type': OptimizationIssueType.GREEDY_ALGORITHM.value,
                        'severity': 'high',
                        'title': 'MongoDB chosen for relational data',
                        'description': 'MongoDB selected but requirements indicate relational data patterns. '
                                     'This is a greedy choice optimizing for simplicity over correctness.',
                        'consequence': 'Will require complex workarounds or eventual migration to relational DB',
                        'estimated_waste_hours': 40,
                        'recommendation': 'Consider PostgreSQL or MySQL for relational requirements'
                    })

        # Pattern 2: No scalability consideration in planning phase
        if project.phase == ProjectPhase.PLANNING:
            requirements = project.requirements
            scalability_keywords = ['scale', 'users', 'concurrent', 'load', 'performance']

            has_scalability_requirements = any(
                keyword in str(requirements).lower() for keyword in scalability_keywords
            )

            if not has_scalability_requirements and len(requirements) > 0:
                issues.append({
                    'type': OptimizationIssueType.INCOMPLETE_ANALYSIS.value,
                    'severity': 'medium',
                    'title': 'No scalability requirements defined',
                    'description': 'Project requirements don\'t mention scaling, load, or performance. '
                                 'This is greedy questioning - not exploring full problem space.',
                    'consequence': 'Architecture may not handle growth, requiring costly refactoring',
                    'estimated_waste_hours': 20,
                    'recommendation': 'Ask: How many users? What load? What are performance requirements?'
                })

        # Pattern 3: Technology stack has too many or too few components
        if tech_spec and tech_spec.technology_stack:
            stack_size = len(tech_spec.technology_stack)

            if stack_size > 15:
                issues.append({
                    'type': OptimizationIssueType.OVER_ENGINEERING.value,
                    'severity': 'high',
                    'title': 'Over-engineered technology stack',
                    'description': f'Technology stack has {stack_size} components. This is likely over-engineered.',
                    'consequence': 'High complexity, difficult maintenance, increased costs',
                    'estimated_waste_hours': 60,
                    'recommendation': 'Simplify stack. Use fewer, more powerful tools.'
                })
            elif stack_size < 3 and len(project.requirements) > 5:
                issues.append({
                    'type': OptimizationIssueType.UNDER_ENGINEERING.value,
                    'severity': 'medium',
                    'title': 'Under-specified technology stack',
                    'description': f'Only {stack_size} technologies specified for {len(project.requirements)} requirements.',
                    'consequence': 'May miss critical infrastructure needs',
                    'estimated_waste_hours': 15,
                    'recommendation': 'Consider database, caching, monitoring, logging, deployment tools'
                })

        return issues

    def _validate_architecture_patterns(self, project: Any, tech_spec: Optional[Any]) -> List[Dict[str, Any]]:
        """
        Validate architecture against known patterns and anti-patterns

        Checks for:
        - God objects / monolithic designs
        - Missing separation of concerns
        - No error handling strategy
        - No monitoring/logging plan
        - Missing security considerations
        """
        issues = []

        if not tech_spec:
            return issues

        # Check 1: Architecture type validation
        arch_type = tech_spec.architecture_type.lower() if tech_spec.architecture_type else ""

        if not arch_type or arch_type == "":
            issues.append({
                'type': OptimizationIssueType.INCOMPLETE_ANALYSIS.value,
                'severity': 'high',
                'title': 'No architecture pattern specified',
                'description': 'No architectural pattern chosen (MVC, microservices, layered, etc.)',
                'consequence': 'Developers will create inconsistent structure',
                'estimated_waste_hours': 30,
                'recommendation': 'Choose explicit architecture: MVC, Clean Architecture, Hexagonal, etc.'
            })

        # Check 2: Security requirements
        security_reqs = tech_spec.security_requirements
        if not security_reqs or len(security_reqs) == 0:
            issues.append({
                'type': OptimizationIssueType.MISSING_REQUIREMENT.value,
                'severity': 'critical',
                'title': 'No security requirements defined',
                'description': 'Security not considered in technical specification',
                'consequence': 'Vulnerabilities, data breaches, compliance issues',
                'estimated_waste_hours': 80,
                'recommendation': 'Define: authentication, authorization, data encryption, input validation'
            })

        # Check 3: Performance requirements
        perf_reqs = tech_spec.performance_requirements
        if not perf_reqs or len(perf_reqs) == 0:
            issues.append({
                'type': OptimizationIssueType.INCOMPLETE_ANALYSIS.value,
                'severity': 'medium',
                'title': 'No performance requirements specified',
                'description': 'No performance targets defined (response time, throughput, etc.)',
                'consequence': 'Cannot validate if architecture meets needs',
                'estimated_waste_hours': 25,
                'recommendation': 'Define: max response time, requests/second, data volume limits'
            })

        # Check 4: Testing strategy
        testing_strategy = tech_spec.testing_strategy
        if not testing_strategy or len(testing_strategy) == 0:
            issues.append({
                'type': OptimizationIssueType.TECHNICAL_DEBT.value,
                'severity': 'high',
                'title': 'No testing strategy defined',
                'description': 'Testing approach not specified',
                'consequence': 'Bugs in production, difficult refactoring, technical debt',
                'estimated_waste_hours': 50,
                'recommendation': 'Define: unit test coverage, integration tests, E2E tests'
            })

        # Check 5: Monitoring requirements
        monitoring_reqs = tech_spec.monitoring_requirements
        if not monitoring_reqs or len(monitoring_reqs) == 0:
            issues.append({
                'type': OptimizationIssueType.MISSING_REQUIREMENT.value,
                'severity': 'medium',
                'title': 'No monitoring/observability plan',
                'description': 'No strategy for monitoring system health',
                'consequence': 'Cannot detect issues, slow incident response',
                'estimated_waste_hours': 20,
                'recommendation': 'Define: logging, metrics, alerting, tracing strategy'
            })

        return issues

    def _calculate_tco(self, project: Any, tech_spec: Optional[Any]) -> Dict[str, Any]:
        """
        C6.4: Calculate Total Cost of Ownership using GlobalCostCalculator

        TCO includes:
        - Initial development time (adjusted for team velocity)
        - Maintenance burden (with complexity factors)
        - Cloud hosting costs
        - Technical debt accumulation (with interest)
        - Refactoring probability

        Returns both basic TCO (for backward compatibility) and enhanced TCO
        """
        # If cost calculator unavailable, fall back to basic calculation
        if not self.cost_calculator:
            return self._calculate_basic_tco(project, tech_spec)

        try:
            # Convert project to dict format
            project_data = {
                'requirements': project.requirements if hasattr(project, 'requirements') else [],
                'technology_stack': project.technology_stack if hasattr(project, 'technology_stack') else {}
            }

            # Convert tech spec to dict format
            tech_spec_dict = None
            if tech_spec:
                tech_spec_dict = {
                    'architecture_type': tech_spec.architecture_type if hasattr(tech_spec, 'architecture_type') else '',
                    'technology_stack': tech_spec.technology_stack if hasattr(tech_spec, 'technology_stack') else {},
                    'functional_requirements': tech_spec.functional_requirements if hasattr(tech_spec, 'functional_requirements') else [],
                    'security_requirements': tech_spec.security_requirements if hasattr(tech_spec, 'security_requirements') else [],
                    'performance_requirements': tech_spec.performance_requirements if hasattr(tech_spec, 'performance_requirements') else {},
                    'testing_strategy': tech_spec.testing_strategy if hasattr(tech_spec, 'testing_strategy') else {},
                    'monitoring_requirements': tech_spec.monitoring_requirements if hasattr(tech_spec, 'monitoring_requirements') else [],
                    'system_components': tech_spec.system_components if hasattr(tech_spec, 'system_components') else []
                }

            # Detect team parameters (can be enhanced to read from project metadata)
            team_size = self.TeamSize.SMALL  # Default to small team
            team_experience = self.TeamExperience.MID  # Default to mid-level
            cloud_provider = self._detect_cloud_provider(tech_spec_dict)
            scale_multiplier = 1.0  # Default to baseline scale

            # Calculate enhanced TCO
            enhanced_tco = self.cost_calculator.calculate_enhanced_tco(
                project_data,
                tech_spec_dict,
                team_size=team_size,
                team_experience=team_experience,
                cloud_provider=cloud_provider,
                expected_scale_multiplier=scale_multiplier
            )

            # Convert to dict format (backward compatible + enhanced data)
            tco_result = {
                # Basic TCO (backward compatible)
                'development_hours': enhanced_tco.development_hours,
                'maintenance_hours_per_year': enhanced_tco.maintenance_burden.total_hours_per_year,
                'scaling_cost_multiplier': 1.0,  # Deprecated
                'technical_debt_hours': enhanced_tco.technical_debt.initial_debt_hours,
                'refactoring_probability': enhanced_tco.technical_debt.probability_of_major_refactor,
                'total_3_year_hours': enhanced_tco.year_3_hours,

                # C6.4: Enhanced TCO data
                'c6_enhanced_tco': {
                    # Development
                    'development_with_velocity': enhanced_tco.development_with_velocity,
                    'onboarding_hours': enhanced_tco.onboarding_hours,

                    # Team factors
                    'team_size': team_size.value,
                    'team_experience': team_experience.value,
                    'velocity_multiplier': enhanced_tco.team_velocity.velocity_multiplier,
                    'effective_hourly_rate': enhanced_tco.effective_hourly_rate,

                    # Maintenance
                    'maintenance_complexity_multiplier': enhanced_tco.maintenance_burden.complexity_multiplier,
                    'maintenance_breakdown': enhanced_tco.maintenance_burden.breakdown_by_category,
                    'burnout_risk_score': enhanced_tco.maintenance_burden.burnout_risk_score,

                    # Cloud costs
                    'cloud_provider': cloud_provider.value,
                    'cloud_monthly_cost_usd': enhanced_tco.cloud_costs.monthly_cost_usd if enhanced_tco.cloud_costs else 0,
                    'cloud_cost_breakdown': enhanced_tco.cloud_costs.cost_breakdown if enhanced_tco.cloud_costs else {},
                    'cloud_cost_at_10x_scale': enhanced_tco.cloud_costs.cost_at_10x_scale if enhanced_tco.cloud_costs else 0,

                    # Technical debt
                    'debt_accumulation_rate': enhanced_tco.technical_debt.accumulation_rate_per_year,
                    'debt_interest_rate': enhanced_tco.technical_debt.interest_rate,
                    'debt_at_year_3': enhanced_tco.technical_debt.debt_at_year_3,
                    'debt_at_year_5': enhanced_tco.technical_debt.debt_at_year_5,
                    'refactor_cost_hours': enhanced_tco.technical_debt.estimated_refactor_cost_hours,

                    # Costs over time
                    'year_1_hours': enhanced_tco.year_1_hours,
                    'year_1_cost_usd': enhanced_tco.year_1_cost_usd,
                    'year_3_hours': enhanced_tco.year_3_hours,
                    'year_3_cost_usd': enhanced_tco.year_3_cost_usd,
                    'year_5_hours': enhanced_tco.year_5_hours,
                    'year_5_cost_usd': enhanced_tco.year_5_cost_usd,

                    # Risk and optimization
                    'risk_factors': enhanced_tco.risk_factors,
                    'cost_optimization_opportunities': enhanced_tco.cost_optimization_opportunities
                }
            }

            self.logger.info(
                f"C6.4: Enhanced TCO calculated - "
                f"Year 1: ${int(enhanced_tco.year_1_cost_usd)} ({int(enhanced_tco.year_1_hours)}h), "
                f"Year 3: ${int(enhanced_tco.year_3_cost_usd)} ({int(enhanced_tco.year_3_hours)}h), "
                f"Year 5: ${int(enhanced_tco.year_5_cost_usd)} ({int(enhanced_tco.year_5_hours)}h)"
            )

            return tco_result

        except Exception as e:
            self.logger.error(f"C6.4: Enhanced TCO calculation failed: {e}, falling back to basic")
            return self._calculate_basic_tco(project, tech_spec)

    def _calculate_basic_tco(self, project: Any, tech_spec: Optional[Any]) -> Dict[str, Any]:
        """
        Basic TCO calculation (fallback when GlobalCostCalculator unavailable)
        """
        tco = {
            'development_hours': 0,
            'maintenance_hours_per_year': 0,
            'scaling_cost_multiplier': 1.0,
            'technical_debt_hours': 0,
            'refactoring_probability': 0.0,
            'total_3_year_hours': 0
        }

        # Estimate development hours based on requirements
        if project.requirements:
            req_count = len(project.requirements)
            tco['development_hours'] = req_count * 8  # 8 hours per requirement (average)

        # Estimate maintenance based on complexity
        if tech_spec and tech_spec.technology_stack:
            stack_complexity = len(tech_spec.technology_stack)
            tco['maintenance_hours_per_year'] = stack_complexity * 20  # 20h/year per technology

        # Estimate technical debt from missing requirements
        if tech_spec:
            missing_security = not tech_spec.security_requirements or len(tech_spec.security_requirements) == 0
            missing_tests = not tech_spec.testing_strategy or len(tech_spec.testing_strategy) == 0
            missing_monitoring = not tech_spec.monitoring_requirements or len(tech_spec.monitoring_requirements) == 0

            debt = 0
            if missing_security:
                debt += 80
            if missing_tests:
                debt += 50
            if missing_monitoring:
                debt += 20

            tco['technical_debt_hours'] = debt

        # Calculate total 3-year cost
        tco['total_3_year_hours'] = (
            tco['development_hours'] +
            (tco['maintenance_hours_per_year'] * 3) +
            tco['technical_debt_hours']
        )

        return tco

    def _detect_cloud_provider(self, tech_spec_dict: Optional[Dict[str, Any]]) -> Any:
        """Detect cloud provider from technology stack"""
        if not tech_spec_dict or not self.cost_calculator:
            return self.CloudProvider.UNKNOWN

        tech_stack = tech_spec_dict.get('technology_stack', {})
        tech_str = str(tech_stack).lower()

        if 'aws' in tech_str or 'lambda' in tech_str or 'dynamodb' in tech_str:
            return self.CloudProvider.AWS
        elif 'azure' in tech_str or 'cosmos' in tech_str:
            return self.CloudProvider.AZURE
        elif 'gcp' in tech_str or 'firebase' in tech_str or 'bigquery' in tech_str:
            return self.CloudProvider.GCP
        elif 'heroku' in tech_str:
            return self.CloudProvider.HEROKU
        elif 'digitalocean' in tech_str or 'droplet' in tech_str:
            return self.CloudProvider.DIGITALOCEAN
        else:
            return self.CloudProvider.AWS  # Default to AWS

    def _generate_alternatives(self, project: Any, tech_spec: Optional[Any],
                              issues: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        C6.4: Generate alternative architectural approaches with cost analysis
        """
        alternatives = []

        # Generate alternatives based on detected issues
        for issue in issues:
            if issue['type'] == OptimizationIssueType.GREEDY_ALGORITHM.value:
                if 'mongodb' in issue.get('title', '').lower():
                    alternatives.append({
                        'title': 'Use PostgreSQL instead of MongoDB',
                        'description': 'PostgreSQL handles relational data natively with ACID guarantees',
                        'estimated_time_savings_hours': 40,
                        'pros': ['Native relational support', 'ACID compliance', 'Strong ecosystem'],
                        'cons': ['Slightly more complex setup', 'Less flexible schema'],
                        'recommendation_strength': 'strong'
                    })

        # C6.4: Add cost optimization opportunities as alternatives
        if self.cost_calculator and tech_spec:
            try:
                # Get current TCO to extract optimization opportunities
                tco_analysis = self._calculate_tco(project, tech_spec)
                enhanced_tco = tco_analysis.get('c6_enhanced_tco')

                if enhanced_tco and 'cost_optimization_opportunities' in enhanced_tco:
                    for opportunity in enhanced_tco['cost_optimization_opportunities']:
                        alternatives.append({
                            'title': opportunity.get('title', 'Cost optimization'),
                            'description': opportunity.get('description', ''),
                            'estimated_time_savings_hours': opportunity.get('estimated_savings_hours_per_year', 0),
                            'estimated_cost_savings_usd': opportunity.get('estimated_savings_usd_per_year', 0),
                            'implementation_hours': opportunity.get('implementation_hours', 0),
                            'category': opportunity.get('category', 'optimization'),
                            'pros': ['Reduces long-term costs', 'Improves maintainability'],
                            'cons': [f"Requires {opportunity.get('implementation_hours', 0)}h upfront investment"],
                            'recommendation_strength': 'medium'
                        })

            except Exception as e:
                self.logger.warning(f"C6.4: Could not add cost optimization alternatives: {e}")

        return alternatives

    def _assess_risk_level(self, issues: List[Dict[str, Any]], tco_analysis: Dict[str, Any]) -> RiskLevel:
        """Assess overall risk level based on issues and TCO"""
        if not issues:
            return RiskLevel.LOW

        # Count issues by severity
        critical_count = sum(1 for issue in issues if issue.get('severity') == 'critical')
        high_count = sum(1 for issue in issues if issue.get('severity') == 'high')

        if critical_count > 0:
            return RiskLevel.CRITICAL
        elif high_count >= 3:
            return RiskLevel.HIGH
        elif high_count >= 1 or len(issues) >= 5:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _generate_recommendations(self, issues: List[Dict[str, Any]],
                                 alternatives: List[Dict[str, Any]],
                                 tco_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate prioritized recommendations"""
        recommendations = []

        # Sort issues by estimated waste hours (highest first)
        sorted_issues = sorted(issues, key=lambda x: x.get('estimated_waste_hours', 0), reverse=True)

        for issue in sorted_issues[:5]:  # Top 5 issues
            recommendations.append({
                'priority': 'high' if issue.get('estimated_waste_hours', 0) > 30 else 'medium',
                'action': issue.get('recommendation', ''),
                'reason': issue.get('description', ''),
                'impact': f"Saves ~{issue.get('estimated_waste_hours', 0)} hours"
            })

        return recommendations

    def _store_architecture_review(self, project_id: str, analysis: Dict[str, Any]) -> bool:
        """Store architecture review in database"""
        try:
            # Store in architecture_reviews table
            review_data = {
                'project_id': project_id,
                'review_type': 'architecture',
                'timestamp': DateTimeHelper.now(),
                'concerns': analysis.get('issues', []),
                'recommendations': analysis.get('recommendations', []),
                'tco_analysis': analysis.get('tco_analysis', {}),
                'risk_level': analysis.get('risk_level', 'unknown')
            }

            # Note: Will need to create architecture_reviews table
            # For now, just log it
            self.logger.info(f"Architecture review for project {project_id}: "
                           f"Risk={review_data['risk_level']}, "
                           f"Issues={len(review_data['concerns'])}")

            return True
        except Exception as e:
            self.logger.error(f"Failed to store architecture review: {e}")
            return False

    def _validate_design_patterns(self, project: Any, tech_spec: Any):
        """
        C6.3: Validate design patterns using DesignPatternValidator

        Args:
            project: Project object
            tech_spec: Technical specification

        Returns:
            PatternValidationResult or None
        """
        if not self.pattern_validator:
            return None

        try:
            # Extract architecture pattern from tech spec
            declared_pattern = tech_spec.architecture_type or 'unknown'

            # Extract components from tech spec
            components = tech_spec.system_components if hasattr(tech_spec, 'system_components') else []

            # Convert to list of dicts if needed
            if components and not isinstance(components[0], dict):
                components = [{'name': str(c)} for c in components]

            # Convert tech spec to dict for validator
            tech_spec_dict = {
                'architecture_type': tech_spec.architecture_type,
                'technology_stack': tech_spec.technology_stack,
                'functional_requirements': tech_spec.functional_requirements,
                'security_requirements': tech_spec.security_requirements,
                'performance_requirements': tech_spec.performance_requirements
            }

            # Run pattern validation
            result = self.pattern_validator.validate_architecture(
                declared_pattern,
                components,
                tech_spec_dict
            )

            self.logger.info(
                f"C6.3: Pattern validation complete - "
                f"Detected: {result.pattern_detected.value}, "
                f"Quality: {result.overall_quality_score:.2f}, "
                f"Issues: {len(result.issues_found)}"
            )

            return result

        except Exception as e:
            self.logger.error(f"C6.3: Pattern validation error: {e}")
            return None

    def _convert_pattern_issues_to_dict(self, pattern_issues: List) -> List[Dict[str, Any]]:
        """
        Convert PatternIssue objects to dict format for main issues list

        Args:
            pattern_issues: List of PatternIssue objects

        Returns:
            List of issue dicts
        """
        converted = []

        for issue in pattern_issues:
            converted.append({
                'type': issue.type,
                'severity': issue.severity,
                'title': issue.name.replace('_', ' ').title(),
                'description': issue.description,
                'consequence': issue.impact,
                'estimated_waste_hours': issue.estimated_fix_hours,
                'recommendation': ' | '.join(issue.recommendations),
                'location': issue.location,
                'references': issue.references
            })

        return converted


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = ['ArchitectureOptimizerAgent', 'RiskLevel', 'OptimizationIssueType']

if __name__ == "__main__":
    print("ArchitectureOptimizerAgent - use via AgentOrchestrator")
