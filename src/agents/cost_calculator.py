#!/usr/bin/env python3
"""
GlobalCostCalculator - Enhanced TCO Analysis for Architecture Optimizer
========================================================================

C6.4: Provides comprehensive Total Cost of Ownership (TCO) calculations including:
- Development time estimates with team velocity factors
- Maintenance burden scoring with complexity models
- Cloud hosting cost projections
- Technical debt accumulation models
- Refactoring probability assessment
- Team size and skill level adjustments

This module provides more accurate cost analysis than basic estimation,
helping prevent architectural decisions that seem cheap initially but
become expensive over time.
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum
import math


class TeamSize(Enum):
    """Team size categories"""
    SOLO = "solo"  # 1 developer
    SMALL = "small"  # 2-5 developers
    MEDIUM = "medium"  # 6-15 developers
    LARGE = "large"  # 16+ developers


class TeamExperience(Enum):
    """Team experience level"""
    JUNIOR = "junior"  # < 2 years experience
    MID = "mid"  # 2-5 years experience
    SENIOR = "senior"  # 5-10 years experience
    EXPERT = "expert"  # 10+ years experience


class CloudProvider(Enum):
    """Supported cloud providers for cost estimation"""
    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    HEROKU = "heroku"
    DIGITALOCEAN = "digitalocean"
    ON_PREMISE = "on_premise"
    UNKNOWN = "unknown"


class ComplexityFactor(Enum):
    """Factors that increase maintenance complexity"""
    TECHNOLOGY_COUNT = "technology_count"
    MICROSERVICES_COUNT = "microservices_count"
    EXTERNAL_INTEGRATIONS = "external_integrations"
    CUSTOM_PROTOCOLS = "custom_protocols"
    DISTRIBUTED_TRANSACTIONS = "distributed_transactions"
    DATA_CONSISTENCY_REQUIREMENTS = "data_consistency_requirements"
    SECURITY_COMPLIANCE = "security_compliance"
    MULTI_TENANCY = "multi_tenancy"


@dataclass
class TeamVelocity:
    """Team velocity metrics for accurate time estimation"""
    size: TeamSize
    experience: TeamExperience
    velocity_multiplier: float  # 0.5 = half speed, 2.0 = double speed
    onboarding_overhead_hours: int
    communication_overhead_percent: float  # 0.1 = 10% overhead
    context_switching_cost: float  # Hours lost per technology


@dataclass
class CloudCostEstimate:
    """Cloud hosting cost estimate"""
    provider: CloudProvider
    monthly_cost_usd: float
    cost_breakdown: Dict[str, float]  # {'compute': 100, 'storage': 50, ...}
    scaling_cost_curve: str  # 'linear', 'logarithmic', 'exponential'
    cost_at_10x_scale: float
    cost_at_100x_scale: float
    optimization_potential_percent: float  # How much can be saved


@dataclass
class MaintenanceBurden:
    """Maintenance burden analysis"""
    base_hours_per_year: float
    complexity_multiplier: float
    technical_debt_multiplier: float
    total_hours_per_year: float
    breakdown_by_category: Dict[str, float]  # {'bug_fixes': 100, 'updates': 50, ...}
    burnout_risk_score: float  # 0-10 scale


@dataclass
class TechnicalDebtModel:
    """Model for technical debt accumulation"""
    initial_debt_hours: int
    accumulation_rate_per_year: float  # Hours of debt added per year
    interest_rate: float  # Debt makes future work harder (1.1 = 10% slower each year)
    debt_at_year_1: float
    debt_at_year_3: float
    debt_at_year_5: float
    probability_of_major_refactor: float  # 0-1 probability
    estimated_refactor_cost_hours: int


@dataclass
class EnhancedTCO:
    """Comprehensive Total Cost of Ownership calculation"""
    # Development costs
    development_hours: int
    development_with_velocity: float
    onboarding_hours: int

    # Team factors
    team_velocity: TeamVelocity
    effective_hourly_rate: float  # Adjusted for experience level

    # Maintenance costs
    maintenance_burden: MaintenanceBurden

    # Infrastructure costs
    cloud_costs: Optional[CloudCostEstimate]

    # Technical debt
    technical_debt: TechnicalDebtModel

    # Total costs over time
    year_1_hours: float
    year_1_cost_usd: float
    year_3_hours: float
    year_3_cost_usd: float
    year_5_hours: float
    year_5_cost_usd: float

    # Risk factors
    risk_factors: List[str]
    cost_optimization_opportunities: List[Dict[str, Any]]


class GlobalCostCalculator:
    """
    C6.4: Enhanced cost calculator with sophisticated TCO models

    Provides accurate cost analysis by considering:
    - Team size and experience (velocity)
    - Technology complexity (maintenance burden)
    - Cloud infrastructure costs
    - Technical debt accumulation
    - Scaling requirements
    """

    def __init__(self):
        """Initialize cost calculator with baseline data"""

        # Average hourly rates by experience level (USD)
        self.hourly_rates = {
            TeamExperience.JUNIOR: 50,
            TeamExperience.MID: 80,
            TeamExperience.SENIOR: 120,
            TeamExperience.EXPERT: 150
        }

        # Team velocity multipliers (relative to baseline)
        self.velocity_multipliers = {
            (TeamSize.SOLO, TeamExperience.JUNIOR): 0.5,
            (TeamSize.SOLO, TeamExperience.MID): 0.8,
            (TeamSize.SOLO, TeamExperience.SENIOR): 1.2,
            (TeamSize.SOLO, TeamExperience.EXPERT): 1.5,

            (TeamSize.SMALL, TeamExperience.JUNIOR): 0.6,
            (TeamSize.SMALL, TeamExperience.MID): 1.0,  # Baseline
            (TeamSize.SMALL, TeamExperience.SENIOR): 1.4,
            (TeamSize.SMALL, TeamExperience.EXPERT): 1.7,

            (TeamSize.MEDIUM, TeamExperience.JUNIOR): 0.5,  # More communication overhead
            (TeamSize.MEDIUM, TeamExperience.MID): 0.9,
            (TeamSize.MEDIUM, TeamExperience.SENIOR): 1.3,
            (TeamSize.MEDIUM, TeamExperience.EXPERT): 1.6,

            (TeamSize.LARGE, TeamExperience.JUNIOR): 0.4,  # High overhead
            (TeamSize.LARGE, TeamExperience.MID): 0.7,
            (TeamSize.LARGE, TeamExperience.SENIOR): 1.1,
            (TeamSize.LARGE, TeamExperience.EXPERT): 1.4,
        }

        # Communication overhead by team size
        self.communication_overhead = {
            TeamSize.SOLO: 0.0,
            TeamSize.SMALL: 0.15,  # 15% time in meetings/coordination
            TeamSize.MEDIUM: 0.25,
            TeamSize.LARGE: 0.35
        }

        # Base cloud costs (monthly USD) for typical configurations
        self.base_cloud_costs = {
            CloudProvider.AWS: {'compute': 150, 'database': 80, 'storage': 30, 'networking': 20},
            CloudProvider.AZURE: {'compute': 140, 'database': 85, 'storage': 35, 'networking': 25},
            CloudProvider.GCP: {'compute': 145, 'database': 75, 'storage': 25, 'networking': 20},
            CloudProvider.HEROKU: {'compute': 250, 'database': 50, 'storage': 20, 'networking': 0},
            CloudProvider.DIGITALOCEAN: {'compute': 100, 'database': 60, 'storage': 20, 'networking': 10},
            CloudProvider.ON_PREMISE: {'compute': 500, 'database': 200, 'storage': 100, 'networking': 50}
        }

        # Complexity factors for maintenance burden
        self.complexity_weights = {
            ComplexityFactor.TECHNOLOGY_COUNT: 20,  # Hours per tech per year
            ComplexityFactor.MICROSERVICES_COUNT: 40,  # Hours per service per year
            ComplexityFactor.EXTERNAL_INTEGRATIONS: 30,
            ComplexityFactor.CUSTOM_PROTOCOLS: 60,
            ComplexityFactor.DISTRIBUTED_TRANSACTIONS: 50,
            ComplexityFactor.DATA_CONSISTENCY_REQUIREMENTS: 40,
            ComplexityFactor.SECURITY_COMPLIANCE: 80,
            ComplexityFactor.MULTI_TENANCY: 70
        }

    def calculate_enhanced_tco(
            self,
            project_data: Dict[str, Any],
            tech_spec: Optional[Dict[str, Any]],
            team_size: TeamSize = TeamSize.SMALL,
            team_experience: TeamExperience = TeamExperience.MID,
            cloud_provider: CloudProvider = CloudProvider.AWS,
            expected_scale_multiplier: float = 1.0
    ) -> EnhancedTCO:
        """
        Calculate comprehensive Total Cost of Ownership

        Args:
            project_data: Project information (requirements, etc.)
            tech_spec: Technical specification
            team_size: Size of development team
            team_experience: Average experience level
            cloud_provider: Target cloud provider
            expected_scale_multiplier: Expected growth (1.0 = baseline, 10.0 = 10x users)

        Returns:
            EnhancedTCO object with comprehensive cost analysis
        """

        # 1. Calculate team velocity
        team_velocity = self._calculate_team_velocity(team_size, team_experience, tech_spec)

        # 2. Estimate development hours
        base_dev_hours = self._estimate_development_hours(project_data, tech_spec)
        adjusted_dev_hours = base_dev_hours / team_velocity.velocity_multiplier
        onboarding_hours = team_velocity.onboarding_overhead_hours

        # 3. Calculate maintenance burden
        maintenance_burden = self._calculate_maintenance_burden(
            tech_spec, team_velocity, expected_scale_multiplier
        )

        # 4. Estimate cloud costs
        cloud_costs = self._estimate_cloud_costs(
            tech_spec, cloud_provider, expected_scale_multiplier
        ) if cloud_provider != CloudProvider.UNKNOWN else None

        # 5. Model technical debt accumulation
        technical_debt = self._model_technical_debt(tech_spec, maintenance_burden)

        # 6. Calculate costs over time
        hourly_rate = self.hourly_rates[team_experience]

        # Year 1: Development + initial maintenance + onboarding
        year_1_hours = adjusted_dev_hours + onboarding_hours + maintenance_burden.total_hours_per_year
        year_1_dev_cost = year_1_hours * hourly_rate
        year_1_cloud_cost = (cloud_costs.monthly_cost_usd * 12) if cloud_costs else 0
        year_1_cost_usd = year_1_dev_cost + year_1_cloud_cost

        # Year 3: Maintenance + accumulated technical debt
        year_3_maint_hours = maintenance_burden.total_hours_per_year * technical_debt.interest_rate ** 2
        year_3_hours = year_3_maint_hours * 3 + technical_debt.debt_at_year_3
        year_3_dev_cost = year_3_hours * hourly_rate
        year_3_cloud_cost = (cloud_costs.monthly_cost_usd * 12 * 3) if cloud_costs else 0
        year_3_cost_usd = year_3_dev_cost + year_3_cloud_cost

        # Year 5: Likely refactoring + increased complexity
        year_5_maint_hours = maintenance_burden.total_hours_per_year * technical_debt.interest_rate ** 4
        year_5_refactor_hours = (technical_debt.estimated_refactor_cost_hours
                                 * technical_debt.probability_of_major_refactor)
        year_5_hours = (year_5_maint_hours * 5 + technical_debt.debt_at_year_5 + year_5_refactor_hours)
        year_5_dev_cost = year_5_hours * hourly_rate
        year_5_cloud_cost = (cloud_costs.monthly_cost_usd * 12 * 5) if cloud_costs else 0
        year_5_cost_usd = year_5_dev_cost + year_5_cloud_cost

        # 7. Identify risk factors
        risk_factors = self._identify_risk_factors(
            tech_spec, maintenance_burden, technical_debt, cloud_costs
        )

        # 8. Find cost optimization opportunities
        optimizations = self._find_optimization_opportunities(
            tech_spec, cloud_costs, maintenance_burden, technical_debt
        )

        return EnhancedTCO(
            development_hours=base_dev_hours,
            development_with_velocity=adjusted_dev_hours,
            onboarding_hours=onboarding_hours,
            team_velocity=team_velocity,
            effective_hourly_rate=hourly_rate,
            maintenance_burden=maintenance_burden,
            cloud_costs=cloud_costs,
            technical_debt=technical_debt,
            year_1_hours=year_1_hours,
            year_1_cost_usd=year_1_cost_usd,
            year_3_hours=year_3_hours,
            year_3_cost_usd=year_3_cost_usd,
            year_5_hours=year_5_hours,
            year_5_cost_usd=year_5_cost_usd,
            risk_factors=risk_factors,
            cost_optimization_opportunities=optimizations
        )

    def _calculate_team_velocity(
            self,
            team_size: TeamSize,
            team_experience: TeamExperience,
            tech_spec: Optional[Dict[str, Any]]
    ) -> TeamVelocity:
        """Calculate team velocity with all factors"""

        # Base velocity multiplier
        velocity = self.velocity_multipliers.get((team_size, team_experience), 1.0)

        # Onboarding overhead (hours to get team up to speed)
        onboarding_hours = {
            TeamSize.SOLO: 0,
            TeamSize.SMALL: 40,
            TeamSize.MEDIUM: 80,
            TeamSize.LARGE: 160
        }[team_size]

        # Communication overhead
        comm_overhead = self.communication_overhead[team_size]

        # Context switching cost (per technology in stack)
        tech_count = 0
        if tech_spec and tech_spec.get('technology_stack'):
            tech_count = len(tech_spec['technology_stack'])

        context_switching_cost = tech_count * 2  # 2 hours per tech for context switching

        # Adjust velocity for communication overhead
        effective_velocity = velocity * (1 - comm_overhead)

        return TeamVelocity(
            size=team_size,
            experience=team_experience,
            velocity_multiplier=effective_velocity,
            onboarding_overhead_hours=onboarding_hours,
            communication_overhead_percent=comm_overhead,
            context_switching_cost=context_switching_cost
        )

    def _estimate_development_hours(
            self,
            project_data: Dict[str, Any],
            tech_spec: Optional[Dict[str, Any]]
    ) -> int:
        """Estimate base development hours"""

        hours = 0

        # Count requirements
        requirements = project_data.get('requirements', [])
        if requirements:
            # Average 8 hours per requirement (varies by complexity)
            req_count = len(requirements)
            hours += req_count * 8

        # Add hours for architectural complexity
        if tech_spec:
            arch_type = tech_spec.get('architecture_type', '').lower()

            # Architecture complexity factors
            arch_hours = {
                'monolithic': 0,
                'mvc': 20,
                'layered': 30,
                'hexagonal': 50,
                'clean_architecture': 60,
                'microservices': 100,
                'event_driven': 80,
                'serverless': 40
            }
            hours += arch_hours.get(arch_type, 20)

            # Add hours for each technology integration
            tech_stack = tech_spec.get('technology_stack', {})
            if isinstance(tech_stack, dict):
                tech_count = len(tech_stack)
            elif isinstance(tech_stack, list):
                tech_count = len(tech_stack)
            else:
                tech_count = 0

            hours += tech_count * 5  # 5 hours per technology integration

            # Add hours for security requirements
            security_reqs = tech_spec.get('security_requirements', [])
            hours += len(security_reqs) * 15  # 15 hours per security requirement

            # Add hours for testing strategy
            testing_strategy = tech_spec.get('testing_strategy', {})
            if testing_strategy:
                hours += 40  # Base testing setup

        return max(hours, 40)  # Minimum 40 hours (1 week)

    def _calculate_maintenance_burden(
            self,
            tech_spec: Optional[Dict[str, Any]],
            team_velocity: TeamVelocity,
            scale_multiplier: float
    ) -> MaintenanceBurden:
        """Calculate maintenance burden with complexity factors"""

        base_hours = 100  # Base 100 hours/year maintenance
        complexity_multiplier = 1.0

        breakdown = {
            'bug_fixes': 40.0,
            'dependency_updates': 30.0,
            'security_patches': 20.0,
            'performance_optimization': 10.0,
            'monitoring_alerts': 0.0
        }

        if tech_spec:
            # Technology count factor
            tech_stack = tech_spec.get('technology_stack', {})
            tech_count = len(tech_stack) if tech_stack else 0
            complexity_multiplier *= (1 + tech_count * 0.15)  # 15% per tech
            breakdown['dependency_updates'] += tech_count * 10

            # Microservices complexity
            arch_type = tech_spec.get('architecture_type', '').lower()
            if 'microservice' in arch_type:
                components = tech_spec.get('system_components', [])
                service_count = len(components) if components else 3
                complexity_multiplier *= (1 + service_count * 0.2)  # 20% per service
                breakdown['monitoring_alerts'] += service_count * 15

            # Security compliance overhead
            security_reqs = tech_spec.get('security_requirements', [])
            if len(security_reqs) > 0:
                complexity_multiplier *= 1.3  # 30% increase
                breakdown['security_patches'] += 40

            # Performance requirements monitoring
            perf_reqs = tech_spec.get('performance_requirements', {})
            if perf_reqs:
                complexity_multiplier *= 1.2  # 20% increase
                breakdown['performance_optimization'] += 30

        # Scale multiplier (more users = more maintenance)
        scale_factor = 1 + (math.log10(max(scale_multiplier, 1)) * 0.3)

        # Technical debt multiplier (will be calculated by debt model)
        tech_debt_multiplier = 1.0

        total_hours = base_hours * complexity_multiplier * scale_factor * tech_debt_multiplier

        # Burnout risk (0-10 scale)
        # High complexity + low team experience = burnout risk
        burnout_risk = min(10, int(complexity_multiplier * 2))
        if team_velocity.experience == TeamExperience.JUNIOR:
            burnout_risk *= 1.5
        burnout_risk = min(10, burnout_risk)

        return MaintenanceBurden(
            base_hours_per_year=base_hours,
            complexity_multiplier=complexity_multiplier,
            technical_debt_multiplier=tech_debt_multiplier,
            total_hours_per_year=total_hours,
            breakdown_by_category=breakdown,
            burnout_risk_score=burnout_risk
        )

    def _estimate_cloud_costs(
            self,
            tech_spec: Optional[Dict[str, Any]],
            provider: CloudProvider,
            scale_multiplier: float
    ) -> Optional[CloudCostEstimate]:
        """Estimate cloud infrastructure costs"""

        if provider == CloudProvider.UNKNOWN or provider not in self.base_cloud_costs:
            return None

        base_costs = self.base_cloud_costs[provider].copy()

        # Adjust for architecture complexity
        if tech_spec:
            arch_type = tech_spec.get('architecture_type', '').lower()

            if 'microservice' in arch_type:
                # Microservices need more compute
                components = tech_spec.get('system_components', [])
                service_count = len(components) if components else 3
                base_costs['compute'] *= service_count * 0.6  # Each service adds 60% compute

            # Database costs scale with data requirements
            tech_stack = tech_spec.get('technology_stack', {})
            if any('database' in str(tech).lower() for tech in tech_stack):
                base_costs['database'] *= 1.5

        # Scale multiplier effect
        for key in base_costs:
            base_costs[key] *= (1 + math.log10(max(scale_multiplier, 1)) * 0.5)

        monthly_cost = sum(base_costs.values())

        # Estimate scaling costs
        # Most cloud costs scale logarithmically (economies of scale)
        cost_at_10x = monthly_cost * (1 + math.log10(10) * 0.7)
        cost_at_100x = monthly_cost * (1 + math.log10(100) * 0.7)

        # Optimization potential (can typically save 20-40%)
        optimization_potential = 0.30  # 30% average

        return CloudCostEstimate(
            provider=provider,
            monthly_cost_usd=monthly_cost,
            cost_breakdown=base_costs,
            scaling_cost_curve='logarithmic',
            cost_at_10x_scale=cost_at_10x,
            cost_at_100x_scale=cost_at_100x,
            optimization_potential_percent=optimization_potential
        )

    def _model_technical_debt(
            self,
            tech_spec: Optional[Dict[str, Any]],
            maintenance_burden: MaintenanceBurden
    ) -> TechnicalDebtModel:
        """Model technical debt accumulation over time"""

        initial_debt = 0

        if tech_spec:
            # Missing security = debt
            security_reqs = tech_spec.get('security_requirements', [])
            if not security_reqs or len(security_reqs) == 0:
                initial_debt += 80

            # Missing tests = debt
            testing_strategy = tech_spec.get('testing_strategy', {})
            if not testing_strategy:
                initial_debt += 50

            # Missing monitoring = debt
            monitoring_reqs = tech_spec.get('monitoring_requirements', [])
            if not monitoring_reqs:
                initial_debt += 20

            # No architecture pattern = debt
            arch_type = tech_spec.get('architecture_type', '')
            if not arch_type:
                initial_debt += 30

        # Debt accumulation rate (hours per year)
        # Complex systems accumulate debt faster
        accumulation_rate = maintenance_burden.complexity_multiplier * 20

        # Interest rate (debt makes future work harder)
        # Higher complexity = higher interest rate
        interest_rate = 1.0 + (maintenance_burden.complexity_multiplier * 0.05)

        # Calculate debt over time with compound interest
        debt_year_1 = initial_debt + accumulation_rate
        debt_year_3 = initial_debt + (accumulation_rate * 3 * (interest_rate ** 2))
        debt_year_5 = initial_debt + (accumulation_rate * 5 * (interest_rate ** 4))

        # Probability of major refactor (increases with debt)
        refactor_probability = min(0.9, debt_year_5 / 1000)  # 90% max probability

        # Estimated refactor cost (3x the accumulated debt)
        refactor_cost = int(debt_year_5 * 3)

        return TechnicalDebtModel(
            initial_debt_hours=initial_debt,
            accumulation_rate_per_year=accumulation_rate,
            interest_rate=interest_rate,
            debt_at_year_1=debt_year_1,
            debt_at_year_3=debt_year_3,
            debt_at_year_5=debt_year_5,
            probability_of_major_refactor=refactor_probability,
            estimated_refactor_cost_hours=refactor_cost
        )

    def _identify_risk_factors(
            self,
            tech_spec: Optional[Dict[str, Any]],
            maintenance_burden: MaintenanceBurden,
            technical_debt: TechnicalDebtModel,
            cloud_costs: Optional[CloudCostEstimate]
    ) -> List[str]:
        """Identify cost risk factors"""

        risks = []

        # High maintenance burden
        if maintenance_burden.total_hours_per_year > 500:
            risks.append(f"High maintenance burden: {int(maintenance_burden.total_hours_per_year)}h/year")

        # High burnout risk
        if maintenance_burden.burnout_risk_score > 7:
            risks.append(f"Team burnout risk: {maintenance_burden.burnout_risk_score:.1f}/10")

        # High technical debt
        if technical_debt.initial_debt_hours > 100:
            risks.append(f"Starting with {technical_debt.initial_debt_hours}h technical debt")

        # Likely refactoring needed
        if technical_debt.probability_of_major_refactor > 0.5:
            risks.append(
                f"{int(technical_debt.probability_of_major_refactor * 100)}% chance of major refactor (${technical_debt.estimated_refactor_cost_hours}h)")

        # Cloud cost scaling issues
        if cloud_costs and cloud_costs.cost_at_100x_scale > cloud_costs.monthly_cost_usd * 50:
            risks.append(f"Cloud costs scale poorly: ${int(cloud_costs.cost_at_100x_scale)}/mo at 100x scale")

        return risks

    def _find_optimization_opportunities(
            self,
            tech_spec: Optional[Dict[str, Any]],
            cloud_costs: Optional[CloudCostEstimate],
            maintenance_burden: MaintenanceBurden,
            technical_debt: TechnicalDebtModel
    ) -> List[Dict[str, Any]]:
        """Find cost optimization opportunities"""

        opportunities = []

        # Cloud cost optimization
        if cloud_costs and cloud_costs.optimization_potential_percent > 0.2:
            savings_per_year = cloud_costs.monthly_cost_usd * 12 * cloud_costs.optimization_potential_percent
            opportunities.append({
                'category': 'cloud_infrastructure',
                'title': 'Optimize cloud resource usage',
                'description': f'Reserved instances, auto-scaling, and right-sizing can reduce costs by {int(cloud_costs.optimization_potential_percent * 100)}%',
                'estimated_savings_usd_per_year': savings_per_year,
                'implementation_hours': 20
            })

        # Technical debt reduction
        if technical_debt.initial_debt_hours > 50:
            opportunities.append({
                'category': 'technical_debt',
                'title': 'Address initial technical debt',
                'description': f'Fixing {technical_debt.initial_debt_hours}h of technical debt now prevents {int(technical_debt.debt_at_year_5)}h at year 5',
                'estimated_savings_hours': technical_debt.debt_at_year_5 - technical_debt.initial_debt_hours,
                'implementation_hours': technical_debt.initial_debt_hours
            })

        # Maintenance burden reduction
        if maintenance_burden.complexity_multiplier > 2.0:
            hours_saved = maintenance_burden.total_hours_per_year * 0.3  # 30% reduction possible
            opportunities.append({
                'category': 'maintenance',
                'title': 'Simplify architecture',
                'description': f'Reducing complexity multiplier from {maintenance_burden.complexity_multiplier:.1f} can save {int(hours_saved)}h/year',
                'estimated_savings_hours_per_year': hours_saved,
                'implementation_hours': 60
            })

        # Technology stack simplification
        if tech_spec:
            tech_stack = tech_spec.get('technology_stack', {})
            tech_count = len(tech_stack) if tech_stack else 0
            if tech_count > 12:
                opportunities.append({
                    'category': 'technology_stack',
                    'title': 'Consolidate technology stack',
                    'description': f'Reducing from {tech_count} to 8-10 technologies can lower maintenance burden',
                    'estimated_savings_hours_per_year': (tech_count - 10) * 20,
                    'implementation_hours': 40
                })

        return opportunities


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    'GlobalCostCalculator',
    'EnhancedTCO',
    'TeamSize',
    'TeamExperience',
    'CloudProvider',
    'TeamVelocity',
    'CloudCostEstimate',
    'MaintenanceBurden',
    'TechnicalDebtModel'
]

if __name__ == "__main__":
    print("GlobalCostCalculator - use via ArchitectureOptimizerAgent")
