#!/usr/bin/env python3
"""
DesignPatternValidator - Advanced Architecture Pattern Analysis
================================================================

Validates architecture patterns and detects anti-patterns that lead to
technical debt and maintenance issues. Part of C6 Architecture Optimizer.

Capabilities:
- Architecture pattern validation (MVC, Microservices, Layered, etc.)
- Anti-pattern detection (God Object, Spaghetti Code, etc.)
- Coupling and cohesion analysis
- SOLID principles validation
- Design smell detection
"""

from typing import Dict, List, Any
from enum import Enum
from dataclasses import dataclass


class ArchitecturePattern(Enum):
    """Supported architecture patterns"""
    MVC = "mvc"
    MICROSERVICES = "microservices"
    LAYERED = "layered"
    HEXAGONAL = "hexagonal"
    CLEAN_ARCHITECTURE = "clean_architecture"
    EVENT_DRIVEN = "event_driven"
    SERVERLESS = "serverless"
    MONOLITHIC = "monolithic"
    UNKNOWN = "unknown"


class AntiPattern(Enum):
    """Common anti-patterns"""
    GOD_OBJECT = "god_object"
    SPAGHETTI_CODE = "spaghetti_code"
    LAVA_FLOW = "lava_flow"
    GOLDEN_HAMMER = "golden_hammer"
    TIGHT_COUPLING = "tight_coupling"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    MAGIC_NUMBERS = "magic_numbers"
    HARD_CODING = "hard_coding"
    NO_SEPARATION_OF_CONCERNS = "no_separation_of_concerns"
    BIG_BALL_OF_MUD = "big_ball_of_mud"
    REINVENTING_WHEEL = "reinventing_wheel"
    PREMATURE_OPTIMIZATION = "premature_optimization"
    CARGO_CULT = "cargo_cult"


class DesignSmell(Enum):
    """Design smells that indicate potential problems"""
    LARGE_CLASS = "large_class"
    LONG_METHOD = "long_method"
    DUPLICATE_CODE = "duplicate_code"
    MISSING_ABSTRACTION = "missing_abstraction"
    INAPPROPRIATE_INTIMACY = "inappropriate_intimacy"
    FEATURE_ENVY = "feature_envy"
    DATA_CLUMPS = "data_clumps"
    PRIMITIVE_OBSESSION = "primitive_obsession"
    SHOTGUN_SURGERY = "shotgun_surgery"
    DIVERGENT_CHANGE = "divergent_change"


@dataclass
class PatternIssue:
    """Issue found in pattern validation"""
    type: str  # 'anti_pattern', 'design_smell', 'pattern_violation'
    name: str
    severity: str  # 'low', 'medium', 'high', 'critical'
    description: str
    location: str  # Where the issue was found
    impact: str
    estimated_fix_hours: int
    recommendations: List[str]
    references: List[str]  # Links to documentation


@dataclass
class PatternValidationResult:
    """Result of pattern validation"""
    pattern_detected: ArchitecturePattern
    pattern_confidence: float  # 0.0 to 1.0
    pattern_correctly_implemented: bool
    issues_found: List[PatternIssue]
    pattern_strengths: List[str]
    pattern_weaknesses: List[str]
    overall_quality_score: float  # 0.0 to 1.0
    recommendations: List[str]


class DesignPatternValidator:
    """
    Validates architecture patterns and detects anti-patterns
    """

    def __init__(self):
        """Initialize pattern validator with rules and heuristics"""

        # Pattern requirements
        self.pattern_requirements = {
            ArchitecturePattern.MVC: {
                'required_components': ['models', 'views', 'controllers'],
                'separation_required': True,
                'max_component_size': 500  # lines per component
            },
            ArchitecturePattern.MICROSERVICES: {
                'required_components': ['services', 'api_gateway'],
                'max_service_size': 1000,
                'requires_independent_deployment': True,
                'requires_service_discovery': True
            },
            ArchitecturePattern.LAYERED: {
                'required_layers': ['presentation', 'business', 'data'],
                'one_way_dependencies': True,
                'no_layer_skipping': True
            },
            ArchitecturePattern.HEXAGONAL: {
                'required_components': ['domain', 'ports', 'adapters'],
                'dependency_direction': 'inward',
                'framework_independent': True
            },
            ArchitecturePattern.CLEAN_ARCHITECTURE: {
                'required_layers': ['entities', 'use_cases', 'interface_adapters', 'frameworks'],
                'dependency_rule': 'inward_only',
                'framework_independent': True
            }
        }

        # Anti-pattern detection rules
        self.anti_pattern_indicators = {
            AntiPattern.GOD_OBJECT: {
                'indicators': ['too_many_responsibilities', 'large_class', 'high_complexity'],
                'thresholds': {
                    'methods_count': 20,
                    'dependencies': 10,
                    'lines_of_code': 500
                }
            },
            AntiPattern.TIGHT_COUPLING: {
                'indicators': ['direct_dependencies', 'concrete_class_usage', 'no_interfaces'],
                'thresholds': {
                    'coupling_score': 0.7
                }
            },
            AntiPattern.CIRCULAR_DEPENDENCY: {
                'indicators': ['module_imports_cycle', 'class_dependencies_cycle'],
                'severity': 'critical'
            },
            AntiPattern.NO_SEPARATION_OF_CONCERNS: {
                'indicators': ['mixed_responsibilities', 'business_logic_in_ui', 'data_access_in_controller'],
                'common_violations': [
                    'SQL queries in controller',
                    'Business logic in view',
                    'UI code in model'
                ]
            },
            AntiPattern.BIG_BALL_OF_MUD: {
                'indicators': ['no_clear_structure', 'arbitrary_dependencies', 'high_complexity'],
                'thresholds': {
                    'architecture_score': 0.3
                }
            }
        }

    def validate_architecture(
        self,
        declared_pattern: str,
        components: List[Dict[str, Any]],
        tech_spec: Dict[str, Any]
    ) -> PatternValidationResult:
        """
        Validate if architecture follows declared pattern correctly

        Args:
            declared_pattern: Pattern the architecture claims to follow
            components: List of system components
            tech_spec: Technical specification

        Returns:
            PatternValidationResult with detailed analysis
        """
        # Parse pattern
        try:
            pattern = ArchitecturePattern(declared_pattern.lower())
        except ValueError:
            pattern = ArchitecturePattern.UNKNOWN

        # Detect actual pattern from structure
        detected_pattern, confidence = self._detect_pattern_from_structure(components)

        # Check if declared matches detected
        pattern_match = (pattern == detected_pattern) if pattern != ArchitecturePattern.UNKNOWN else False

        # Validate pattern implementation
        issues = []

        if pattern != ArchitecturePattern.UNKNOWN:
            pattern_issues = self._validate_pattern_implementation(pattern, components, tech_spec)
            issues.extend(pattern_issues)

        # Detect anti-patterns
        anti_pattern_issues = self._detect_anti_patterns(components, tech_spec)
        issues.extend(anti_pattern_issues)

        # Detect design smells
        smell_issues = self._detect_design_smells(components, tech_spec)
        issues.extend(smell_issues)

        # Analyze SOLID principles
        solid_issues = self._validate_solid_principles(components, tech_spec)
        issues.extend(solid_issues)

        # Calculate quality score
        quality_score = self._calculate_quality_score(issues, pattern_match)

        # Identify strengths and weaknesses
        strengths = self._identify_pattern_strengths(pattern, components, tech_spec)
        weaknesses = self._identify_pattern_weaknesses(issues)

        # Generate recommendations
        recommendations = self._generate_pattern_recommendations(pattern, issues, quality_score)

        return PatternValidationResult(
            pattern_detected=detected_pattern,
            pattern_confidence=confidence,
            pattern_correctly_implemented=pattern_match,
            issues_found=issues,
            pattern_strengths=strengths,
            pattern_weaknesses=weaknesses,
            overall_quality_score=quality_score,
            recommendations=recommendations
        )

    def _detect_pattern_from_structure(
        self,
        components: List[Dict[str, Any]]
    ) -> tuple[ArchitecturePattern, float]:
        """
        Detect architecture pattern from component structure

        Returns:
            (detected_pattern, confidence_score)
        """
        if not components:
            return ArchitecturePattern.UNKNOWN, 0.0

        component_names = [c.get('name', '').lower() for c in components]

        # Check for MVC
        mvc_score = 0.0
        if 'models' in component_names: mvc_score += 0.33
        if 'views' in component_names: mvc_score += 0.33
        if 'controllers' in component_names: mvc_score += 0.34

        # Check for Microservices
        microservices_score = 0.0
        if any('service' in name for name in component_names):
            microservices_score += 0.4
        if 'api_gateway' in component_names or 'gateway' in component_names:
            microservices_score += 0.3
        if len(components) > 5:  # Multiple services
            microservices_score += 0.3

        # Check for Layered
        layered_score = 0.0
        if 'presentation' in component_names: layered_score += 0.33
        if 'business' in component_names or 'domain' in component_names: layered_score += 0.33
        if 'data' in component_names or 'persistence' in component_names: layered_score += 0.34

        # Check for Hexagonal
        hexagonal_score = 0.0
        if 'domain' in component_names: hexagonal_score += 0.4
        if 'ports' in component_names: hexagonal_score += 0.3
        if 'adapters' in component_names: hexagonal_score += 0.3

        # Select pattern with highest score
        scores = {
            ArchitecturePattern.MVC: mvc_score,
            ArchitecturePattern.MICROSERVICES: microservices_score,
            ArchitecturePattern.LAYERED: layered_score,
            ArchitecturePattern.HEXAGONAL: hexagonal_score
        }

        if max(scores.values()) < 0.5:
            return ArchitecturePattern.MONOLITHIC, 0.6

        detected = max(scores, key=scores.get)
        confidence = scores[detected]

        return detected, confidence

    def _validate_pattern_implementation(
        self,
        pattern: ArchitecturePattern,
        components: List[Dict[str, Any]],
        tech_spec: Dict[str, Any]
    ) -> List[PatternIssue]:
        """Validate if pattern is correctly implemented"""
        issues = []

        if pattern not in self.pattern_requirements:
            return issues

        requirements = self.pattern_requirements[pattern]
        component_names = [c.get('name', '').lower() for c in components]

        # Check required components
        if 'required_components' in requirements:
            for required in requirements['required_components']:
                if required not in component_names:
                    issues.append(PatternIssue(
                        type='pattern_violation',
                        name=f'missing_{required}_component',
                        severity='high',
                        description=f'{pattern.value.upper()} requires {required} component',
                        location='architecture',
                        impact=f'Pattern {pattern.value} not properly implemented',
                        estimated_fix_hours=8,
                        recommendations=[
                            f'Add {required} component to architecture',
                            f'Follow {pattern.value} pattern guidelines'
                        ],
                        references=[
                            f'https://martinfowler.com/architecture/{pattern.value}',
                            'Clean Architecture by Robert C. Martin'
                        ]
                    ))

        # Check component sizes
        if 'max_component_size' in requirements:
            max_size = requirements['max_component_size']
            for component in components:
                size = component.get('estimated_lines', 0)
                if size > max_size:
                    issues.append(PatternIssue(
                        type='design_smell',
                        name='oversized_component',
                        severity='medium',
                        description=f'Component {component.get("name")} is too large ({size} lines)',
                        location=component.get('name', 'unknown'),
                        impact='Difficult to maintain and test',
                        estimated_fix_hours=6,
                        recommendations=[
                            'Break component into smaller, focused modules',
                            'Apply Single Responsibility Principle'
                        ],
                        references=['Refactoring by Martin Fowler']
                    ))

        return issues

    def _detect_anti_patterns(
        self,
        components: List[Dict[str, Any]],
        tech_spec: Dict[str, Any]
    ) -> List[PatternIssue]:
        """Detect common anti-patterns"""
        issues = []

        # Detect God Object
        for component in components:
            responsibilities = component.get('responsibilities', [])
            dependencies = component.get('dependencies', [])

            if len(responsibilities) > 5 or len(dependencies) > 10:
                issues.append(PatternIssue(
                    type='anti_pattern',
                    name=AntiPattern.GOD_OBJECT.value,
                    severity='high',
                    description=f'Component {component.get("name")} has too many responsibilities',
                    location=component.get('name', 'unknown'),
                    impact='Difficult to maintain, test, and modify. High coupling.',
                    estimated_fix_hours=15,
                    recommendations=[
                        'Split into multiple focused components',
                        'Apply Single Responsibility Principle',
                        'Use Facade pattern if needed'
                    ],
                    references=['Head First Design Patterns']
                ))

        # Detect No Separation of Concerns
        component_names = [c.get('name', '').lower() for c in components]
        if len(components) < 3 and len(tech_spec.get('functional_requirements', [])) > 5:
            issues.append(PatternIssue(
                type='anti_pattern',
                name=AntiPattern.NO_SEPARATION_OF_CONCERNS.value,
                severity='high',
                description='Architecture lacks proper separation of concerns',
                location='overall_architecture',
                impact='Mixed responsibilities lead to tight coupling and difficult maintenance',
                estimated_fix_hours=20,
                recommendations=[
                    'Separate presentation, business logic, and data layers',
                    'Apply layered architecture pattern',
                    'Use dependency injection'
                ],
                references=['Clean Architecture by Robert C. Martin']
            ))

        # Detect Circular Dependencies
        dependency_graph = {}
        for component in components:
            name = component.get('name', '')
            deps = component.get('dependencies', [])
            dependency_graph[name] = deps

        cycles = self._detect_cycles(dependency_graph)
        if cycles:
            issues.append(PatternIssue(
                type='anti_pattern',
                name=AntiPattern.CIRCULAR_DEPENDENCY.value,
                severity='critical',
                description=f'Circular dependencies detected: {" -> ".join(cycles[0])}',
                location='architecture',
                impact='Cannot build/deploy, makes system fragile and unpredictable',
                estimated_fix_hours=12,
                recommendations=[
                    'Break circular dependencies with interfaces',
                    'Apply Dependency Inversion Principle',
                    'Use event-driven communication'
                ],
                references=['Dependency Injection Principles']
            ))

        # Detect Golden Hammer (single technology for everything)
        tech_stack = tech_spec.get('technology_stack', {})
        if isinstance(tech_stack, dict) and len(tech_stack) == 1:
            issues.append(PatternIssue(
                type='anti_pattern',
                name=AntiPattern.GOLDEN_HAMMER.value,
                severity='medium',
                description='Using single technology for all problems',
                location='technology_stack',
                impact='May not be optimal for all use cases',
                estimated_fix_hours=10,
                recommendations=[
                    'Evaluate if technology fits all requirements',
                    'Consider polyglot approach for different concerns',
                    'Use right tool for each job'
                ],
                references=['The Pragmatic Programmer']
            ))

        return issues

    def _detect_design_smells(
        self,
        components: List[Dict[str, Any]],
        tech_spec: Dict[str, Any]
    ) -> List[PatternIssue]:
        """Detect design smells"""
        issues = []

        # Check for missing abstraction
        if not any('interface' in c.get('name', '').lower() or 'abstract' in c.get('name', '').lower()
                   for c in components):
            if len(components) > 3:
                issues.append(PatternIssue(
                    type='design_smell',
                    name=DesignSmell.MISSING_ABSTRACTION.value,
                    severity='medium',
                    description='No interfaces or abstractions defined',
                    location='architecture',
                    impact='Tight coupling, difficult to test and extend',
                    estimated_fix_hours=8,
                    recommendations=[
                        'Define interfaces for key components',
                        'Program to interfaces, not implementations',
                        'Apply Dependency Inversion Principle'
                    ],
                    references=['Design Patterns: Elements of Reusable Software']
                ))

        return issues

    def _validate_solid_principles(
        self,
        components: List[Dict[str, Any]],
        tech_spec: Dict[str, Any]
    ) -> List[PatternIssue]:
        """Validate SOLID principles"""
        issues = []

        # Single Responsibility Principle
        for component in components:
            responsibilities = component.get('responsibilities', [])
            if len(responsibilities) > 3:
                issues.append(PatternIssue(
                    type='solid_violation',
                    name='srp_violation',
                    severity='medium',
                    description=f'Component {component.get("name")} violates Single Responsibility Principle',
                    location=component.get('name', 'unknown'),
                    impact='Component has multiple reasons to change',
                    estimated_fix_hours=6,
                    recommendations=[
                        'Split into focused components',
                        'Each component should have one reason to change'
                    ],
                    references=['SOLID Principles by Robert C. Martin']
                ))

        # Dependency Inversion Principle
        has_interfaces = any('interface' in str(c).lower() for c in components)
        has_concrete_dependencies = any(len(c.get('dependencies', [])) > 2 for c in components)

        if has_concrete_dependencies and not has_interfaces:
            issues.append(PatternIssue(
                type='solid_violation',
                name='dip_violation',
                severity='medium',
                description='Components depend on concrete classes instead of abstractions',
                location='architecture',
                impact='Tight coupling, difficult to test and modify',
                estimated_fix_hours=10,
                recommendations=[
                    'Define interfaces for key dependencies',
                    'Depend on abstractions, not concretions',
                    'Use dependency injection'
                ],
                references=['Clean Code by Robert C. Martin']
            ))

        return issues

    def _detect_cycles(self, graph: Dict[str, List[str]]) -> List[List[str]]:
        """Detect cycles in dependency graph"""
        def dfs(node, visited, rec_stack, path):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    cycle = dfs(neighbor, visited, rec_stack, path[:])
                    if cycle:
                        return cycle
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    return path[cycle_start:] + [neighbor]

            rec_stack.remove(node)
            return None

        visited = set()
        for node in graph:
            if node not in visited:
                cycle = dfs(node, visited, set(), [])
                if cycle:
                    return [cycle]

        return []

    def _calculate_quality_score(self, issues: List[PatternIssue], pattern_match: bool) -> float:
        """Calculate overall quality score"""
        base_score = 1.0

        # Penalty for issues
        for issue in issues:
            if issue.severity == 'critical':
                base_score -= 0.25
            elif issue.severity == 'high':
                base_score -= 0.15
            elif issue.severity == 'medium':
                base_score -= 0.08
            elif issue.severity == 'low':
                base_score -= 0.03

        # Penalty if pattern doesn't match
        if not pattern_match:
            base_score -= 0.2

        return max(0.0, min(1.0, base_score))

    def _identify_pattern_strengths(
        self,
        pattern: ArchitecturePattern,
        components: List[Dict[str, Any]],
        tech_spec: Dict[str, Any]
    ) -> List[str]:
        """Identify strengths in the architecture"""
        strengths = []

        if len(components) >= 3:
            strengths.append("Good component separation")

        if any('test' in c.get('name', '').lower() for c in components):
            strengths.append("Testing infrastructure included")

        if tech_spec.get('security_requirements'):
            strengths.append("Security requirements defined")

        if tech_spec.get('monitoring_requirements'):
            strengths.append("Monitoring strategy in place")

        return strengths

    def _identify_pattern_weaknesses(self, issues: List[PatternIssue]) -> List[str]:
        """Identify weaknesses from issues"""
        weaknesses = []

        critical_issues = [i for i in issues if i.severity == 'critical']
        if critical_issues:
            weaknesses.append(f"{len(critical_issues)} critical architecture issues")

        high_issues = [i for i in issues if i.severity == 'high']
        if high_issues:
            weaknesses.append(f"{len(high_issues)} high-severity design issues")

        anti_patterns = [i for i in issues if i.type == 'anti_pattern']
        if anti_patterns:
            weaknesses.append(f"{len(anti_patterns)} anti-patterns detected")

        return weaknesses

    def _generate_pattern_recommendations(
        self,
        pattern: ArchitecturePattern,
        issues: List[PatternIssue],
        quality_score: float
    ) -> List[str]:
        """Generate recommendations for improving the architecture"""
        recommendations = []

        if quality_score < 0.5:
            recommendations.append("⚠️ Architecture quality is low - major refactoring recommended")

        # Group issues by type
        critical_issues = [i for i in issues if i.severity == 'critical']
        if critical_issues:
            recommendations.append(f"🚨 CRITICAL: Fix {len(critical_issues)} critical issues immediately")

        anti_patterns = [i for i in issues if i.type == 'anti_pattern']
        if anti_patterns:
            recommendations.append(f"Address {len(anti_patterns)} anti-patterns to reduce technical debt")

        if quality_score >= 0.7:
            recommendations.append("✅ Architecture is well-structured - minor improvements recommended")

        return recommendations


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    'DesignPatternValidator',
    'PatternValidationResult',
    'PatternIssue',
    'ArchitecturePattern',
    'AntiPattern',
    'DesignSmell'
]
