"""
Project-type-specific phase categories for maturity tracking.

Defines category targets for different project types across all 4 phases.
Each category has a target point value (max contribution to phase maturity).
Total per phase: 90 points (ensures balanced, normalized scoring across types).
"""

# Generic categories - work for any project type
GENERIC_PHASE_CATEGORIES = {
    "discovery": {
        "objectives": 20,  # What are we trying to achieve?
        "scope": 15,  # What's included/excluded?
        "constraints": 15,  # Time, budget, resources, limitations?
        "stakeholders": 10,  # Who's involved/affected?
        "risks": 10,  # What could go wrong?
        "success_criteria": 10,  # How do we measure success?
    },
    "analysis": {
        "requirements": 20,  # What's needed?
        "assumptions": 12,  # What are we assuming?
        "dependencies": 12,  # What relies on what?
        "resources": 12,  # Tools, people, budget, materials?
        "timeline": 12,  # Phases, milestones, deadlines?
        "feasibility": 10,  # Can we realistically do this?
        "alternatives": 2,  # Other approaches considered?
    },
    "design": {
        "structure": 20,  # How is it organized/architected?
        "workflow": 15,  # What are the key processes/steps?
        "interfaces": 12,  # How do components interact?
        "standards": 10,  # What guidelines/best practices apply?
        "quality_metrics": 10,  # How do we ensure quality?
        "error_handling": 8,  # How do we handle problems?
        "customization": 5,  # Can it adapt to variations?
    },
    "implementation": {
        "milestones": 20,  # Key phases and deliverables?
        "execution_plan": 15,  # Step-by-step implementation?
        "monitoring": 12,  # How do we track progress?
        "documentation": 12,  # How is it documented?
        "handoff": 10,  # How is it delivered/deployed?
        "maintenance": 10,  # Ongoing support and updates?
        "rollback": 6,  # What if we need to undo?
        "optimization": 5,  # Performance and efficiency improvements?
    },
}

# Software/Technology Projects
SOFTWARE_PHASE_CATEGORIES = {
    "discovery": {
        "problem_definition": 20,
        "target_audience": 15,
        "goals": 15,
        "competitive_analysis": 10,
        "scope": 12,
        "constraints": 10,
        "success_metrics": 8,
    },
    "analysis": {
        "requirements": 20,
        "tech_stack": 15,
        "security": 12,
        "performance": 10,
        "integrations": 10,
        "testing_strategy": 10,
        "scalability": 8,
        "data_management": 5,
    },
    "design": {
        "architecture": 20,
        "design_patterns": 15,
        "code_organization": 12,
        "api_design": 10,
        "workflow": 10,
        "error_handling": 10,
        "state_management": 8,
        "ui_ux": 5,
    },
    "implementation": {
        "milestones": 20,
        "deployment": 15,
        "monitoring": 12,
        "documentation": 12,
        "devops": 10,
        "maintenance": 10,
        "rollback_strategy": 6,
        "performance_optimization": 5,
    },
}

# Business/Product Projects
BUSINESS_PHASE_CATEGORIES = {
    "discovery": {
        "market_opportunity": 20,
        "target_customer": 15,
        "business_model": 15,
        "competitive_landscape": 10,
        "value_proposition": 12,
        "constraints": 10,
        "success_metrics": 8,
    },
    "analysis": {
        "financial_projections": 20,
        "market_sizing": 15,
        "customer_needs": 12,
        "revenue_model": 10,
        "go_to_market": 10,
        "resources_required": 10,
        "scalability_plan": 8,
        "risk_mitigation": 5,
    },
    "design": {
        "product_roadmap": 20,
        "feature_prioritization": 15,
        "user_experience": 12,
        "business_processes": 10,
        "operational_flow": 10,
        "quality_standards": 10,
        "expansion_strategy": 8,
        "partnerships": 5,
    },
    "implementation": {
        "phase_milestones": 20,
        "launch_plan": 15,
        "performance_tracking": 12,
        "stakeholder_communication": 12,
        "team_structure": 10,
        "operations_setup": 10,
        "contingency_planning": 6,
        "growth_optimization": 5,
    },
}

# Creative/Design Projects (Art, Content, Design, Media)
CREATIVE_PHASE_CATEGORIES = {
    "discovery": {
        "creative_vision": 20,
        "target_audience": 15,
        "artistic_direction": 15,
        "inspiration_research": 10,
        "style_guide": 12,
        "constraints": 10,
        "success_criteria": 8,
    },
    "analysis": {
        "content_analysis": 20,
        "audience_insights": 15,
        "market_trends": 12,
        "creative_references": 10,
        "technical_requirements": 10,
        "resource_needs": 10,
        "timeline_phases": 8,
        "feedback_mechanisms": 5,
    },
    "design": {
        "creative_concept": 20,
        "visual_identity": 15,
        "component_design": 12,
        "narrative_structure": 10,
        "user_journey": 10,
        "interaction_design": 10,
        "accessibility": 8,
        "brand_consistency": 5,
    },
    "implementation": {
        "production_schedule": 20,
        "creative_execution": 15,
        "quality_assurance": 12,
        "version_documentation": 12,
        "asset_management": 10,
        "collaboration_workflow": 10,
        "revision_process": 6,
        "optimization_refinement": 5,
    },
}

# Research/Academic Projects
RESEARCH_PHASE_CATEGORIES = {
    "discovery": {
        "research_question": 20,
        "literature_review": 15,
        "research_gap": 15,
        "theoretical_framework": 10,
        "scope_boundaries": 12,
        "constraints": 10,
        "success_metrics": 8,
    },
    "analysis": {
        "methodology": 20,
        "data_collection_plan": 15,
        "ethical_considerations": 12,
        "research_tools": 10,
        "sample_design": 10,
        "analysis_approach": 10,
        "timeline": 8,
        "resource_requirements": 5,
    },
    "design": {
        "research_design": 20,
        "experiment_protocol": 15,
        "measurement_approach": 12,
        "data_structure": 10,
        "validation_method": 10,
        "quality_controls": 10,
        "reproducibility": 8,
        "documentation_standards": 5,
    },
    "implementation": {
        "research_milestones": 20,
        "data_collection": 15,
        "data_analysis": 12,
        "findings_documentation": 12,
        "collaboration_coordination": 10,
        "results_presentation": 10,
        "contingency_protocols": 6,
        "impact_planning": 5,
    },
}

# Marketing/Campaign Projects
MARKETING_PHASE_CATEGORIES = {
    "discovery": {
        "campaign_objective": 20,
        "target_audience": 15,
        "market_positioning": 15,
        "competitive_analysis": 10,
        "messaging_core": 12,
        "constraints": 10,
        "success_metrics": 8,
    },
    "analysis": {
        "audience_insights": 20,
        "channel_strategy": 15,
        "content_pillars": 12,
        "budget_allocation": 10,
        "timeline_phases": 10,
        "tools_platforms": 10,
        "competitor_moves": 8,
        "resource_plan": 5,
    },
    "design": {
        "content_strategy": 20,
        "creative_direction": 15,
        "messaging_framework": 12,
        "campaign_flow": 10,
        "touchpoint_design": 10,
        "brand_guidelines": 10,
        "personalization": 8,
        "multi_channel_coordination": 5,
    },
    "implementation": {
        "content_calendar": 20,
        "campaign_execution": 15,
        "performance_monitoring": 12,
        "audience_engagement": 12,
        "team_coordination": 10,
        "asset_production": 10,
        "contingency_plans": 6,
        "optimization_tactics": 5,
    },
}

# Educational/Curriculum Projects
EDUCATIONAL_PHASE_CATEGORIES = {
    "discovery": {
        "learning_objectives": 20,
        "target_learners": 15,
        "subject_scope": 15,
        "prerequisite_analysis": 10,
        "learning_outcomes": 12,
        "constraints": 10,
        "success_metrics": 8,
    },
    "analysis": {
        "content_analysis": 20,
        "pedagogical_approach": 15,
        "learner_needs": 12,
        "assessment_strategy": 10,
        "resource_inventory": 10,
        "technology_platform": 10,
        "pacing_timeline": 8,
        "accessibility_needs": 5,
    },
    "design": {
        "curriculum_structure": 20,
        "lesson_design": 15,
        "learning_activities": 12,
        "assessment_design": 10,
        "content_sequencing": 10,
        "engagement_strategy": 10,
        "inclusion_design": 8,
        "feedback_mechanisms": 5,
    },
    "implementation": {
        "development_milestones": 20,
        "content_creation": 15,
        "assessment_preparation": 12,
        "delivery_planning": 12,
        "instructor_training": 10,
        "learner_support": 10,
        "iteration_process": 6,
        "outcome_optimization": 5,
    },
}

# All project types
PROJECT_TYPE_CATEGORIES = {
    "software": SOFTWARE_PHASE_CATEGORIES,
    "business": BUSINESS_PHASE_CATEGORIES,
    "creative": CREATIVE_PHASE_CATEGORIES,
    "research": RESEARCH_PHASE_CATEGORIES,
    "marketing": MARKETING_PHASE_CATEGORIES,
    "educational": EDUCATIONAL_PHASE_CATEGORIES,
}

# Valid project types
VALID_PROJECT_TYPES = list(PROJECT_TYPE_CATEGORIES.keys())

# Project type descriptions
PROJECT_TYPE_DESCRIPTIONS = {
    "software": "Software/Technology (apps, web, systems, APIs, tools)",
    "business": "Business/Product (startups, services, products, ventures)",
    "creative": "Creative/Design (art, content, design, media, branding)",
    "research": "Research/Academic (studies, experiments, analysis, papers)",
    "marketing": "Marketing/Campaigns (promotions, campaigns, content strategy)",
    "educational": "Educational/Training (courses, curriculum, training programs)",
}


def get_phase_categories(project_type: str = "software"):
    """
    Get phase categories for a specific project type.

    Args:
        project_type: Type of project (software, business, creative, research, marketing, educational)

    Returns:
        Dict of phase categories for that project type, or generic categories if type unknown
    """
    return PROJECT_TYPE_CATEGORIES.get(project_type, GENERIC_PHASE_CATEGORIES)


def get_all_project_types():
    """Get list of all supported project types"""
    return VALID_PROJECT_TYPES


def get_project_type_description(project_type: str):
    """Get human-readable description of a project type"""
    return PROJECT_TYPE_DESCRIPTIONS.get(project_type, "Unknown project type")
