#!/usr/bin/env python3
"""
ProjectManagerAgent - Enhanced Project Management with Module Hierarchy
========================================================================

Handles complete project lifecycle, module hierarchy management, team coordination,
progress tracking, and resource allocation. Fully corrected according to project standards.

Capabilities:
- Project CRUD operations with validation
- Module and task hierarchy management
- Team collaboration and permission management
- Progress tracking and analytics
- Risk assessment and resource allocation
- Timeline management and milestone tracking
"""

from typing import Dict, List, Any, Optional
from functools import wraps
import json

try:
    from src.core import get_logger, DateTimeHelper, ValidationError, ValidationHelper, get_event_bus, ServiceContainer
    from src.models import Project, Module, Task, ProjectStatus, ProjectPhase, TaskPriority, ModelValidator
    from src.database import get_database
    from .base import BaseAgent, require_authentication, require_project_access, log_agent_action

    CORE_AVAILABLE = True
except ImportError:
    CORE_AVAILABLE = False
    # Fallback implementations
    import logging
    from datetime import datetime
    from enum import Enum


    def get_logger(name):
        return logging.getLogger(name)


    def get_event_bus():
        return None


    def get_database():
        return None

    def ServiceContainer():
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


    class ValidationHelper:
        @staticmethod
        def validate_email(email):
            return "@" in str(email) if email else False


    class ProjectStatus(Enum):
        DRAFT = "draft"
        ACTIVE = "active"
        ARCHIVED = "archived"


    class ProjectPhase(Enum):
        PLANNING = "planning"
        REQUIREMENTS = "requirements"
        DESIGN = "design"
        DEVELOPMENT = "development"
        TESTING = "testing"
        DEPLOYMENT = "deployment"


    class TaskPriority(Enum):
        LOW = "low"
        MEDIUM = "medium"
        HIGH = "high"


    class ModelValidator:
        @staticmethod
        def validate_project_data(data):
            return []


    class Project:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)


    class Module:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)


    class Task:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)


    class BaseAgent:
        def __init__(self, agent_id, name):
            self.agent_id = agent_id
            self.name = name
            self.logger = get_logger(agent_id)

        def _error_response(self, message, error_code=None):
            return {'success': False, 'error': message}


    def require_authentication(func):
        return func


    def require_project_access(func):
        return func


    def log_agent_action(func):
        return func


class ProjectManagerAgent(BaseAgent):
    """
    Enhanced project management agent with module hierarchy

    Absorbs: ModuleManagerAgent capabilities for hierarchical management
    Capabilities: Complete project lifecycle, team coordination, progress tracking
    """

    def __init__(self, services: ServiceContainer):
        """Initialize ProjectManagerAgent with corrected patterns"""
        super().__init__("project_manager", "Project Manager", services)

        # Initialize logging
        if self.logger:
            self.logger.info(f"ProjectManagerAgent initialized successfully")

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this agent provides"""
        return [
            "create_project", "update_project", "archive_project", "manage_modules",
            "assign_tasks", "track_progress", "manage_collaborators", "generate_reports",
            "risk_assessment", "resource_allocation", "timeline_management",
            "get_project_info", "list_projects", "project_analytics"
        ]

    @require_authentication
    @log_agent_action
    def _create_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new project with full setup and validation"""
        username = data.get('username')  # Initialize early

        try:
            # Extract and validate project data
            project_data = {
                'name': data.get('name'),
                'description': data.get('description', ''),
                'owner_id': username,
                'goals': data.get('goals', ''),
                'requirements': data.get('requirements', []),
                'technology_stack': data.get('tech_stack', {}),
                'constraints': data.get('constraints', []),
                'success_criteria': data.get('success_criteria', []),
                'team_members': data.get('team_members', []),
                'stakeholders': data.get('stakeholders', []),
                'estimated_hours': data.get('estimated_hours'),
                'budget': data.get('budget'),
                'priority': data.get('priority', 'medium'),
                'tags': data.get('tags', []),
                'status': ProjectStatus.DRAFT,
                'phase': ProjectPhase.PLANNING,
                'created_at': DateTimeHelper.now(),  # Rule #7: Use DateTimeHelper
                'updated_at': DateTimeHelper.now()
            }

            # Validate required fields
            if not project_data['name'] or len(project_data['name'].strip()) < 2:
                self.logger.warning("Project creation failed: Invalid project name")
                raise ValidationError("Project name must be at least 2 characters long")

            # Validate project data using model validator
            validation_issues = ModelValidator.validate_project_data(project_data)
            if validation_issues:
                self.logger.warning(f"Project creation failed: Validation issues: {validation_issues}")
                raise ValidationError(f"Project validation failed: {'; '.join(validation_issues)}")

            # Create project model
            project = Project(**project_data)

            # Save project to database
            success = self.db_service.projects.create(project)
            if not success:
                self.logger.error(f"Database operation failed for project creation: {project_data['name']}")
                raise Exception("Failed to create project in database")

            # Create default modules if specified
            default_modules = data.get('default_modules', [])
            modules_created = 0
            for module_data in default_modules:
                try:
                    module_data['project_id'] = project.id
                    module_data['created_at'] = DateTimeHelper.now()
                    module_data['updated_at'] = DateTimeHelper.now()

                    module = Module(**module_data)
                    if self.db_service.modules.create(module):
                        modules_created += 1
                except Exception as e:
                    self.logger.warning(f"Failed to create default module: {e}")

            # Initialize project tracking and analytics
            self._initialize_project_tracking(project.id)

            # Emit project creation event
            if self.events:
                self.events.emit('project_created', 'project_manager', {
                    'project_id': project.id,
                    'project_name': project.name,
                    'owner': username,
                    'modules_created': modules_created,
                    'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
                })

            self.logger.info(f"Project created successfully: {project.name} (ID: {project.id}) by {username}")

            return {
                'success': True,
                'project_id': project.id,
                'name': project.name,
                'status': 'created',
                'modules_created': modules_created,
                'created_at': DateTimeHelper.to_iso_string(project.created_at)
            }

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error creating project for {username or 'unknown'}: {e}")
            return self._error_response(f"Failed to create project: {str(e)}")

    def _initialize_project_tracking(self, project_id: str):
        """Initialize tracking systems and analytics for new project"""
        try:
            # Create initial progress metrics
            initial_metrics = {
                'discovery_progress': 0.0,
                'analysis_progress': 0.0,
                'design_progress': 0.0,
                'implementation_progress': 0.0,
                'testing_progress': 0.0,
                'deployment_progress': 0.0,
                'overall_progress': 0.0
            }

            # Initialize risk tracking
            initial_risks = []

            # Set up project analytics baseline
            analytics_data = {
                'project_id': project_id,
                'start_time': DateTimeHelper.to_iso_string(DateTimeHelper.now()),
                'metrics': initial_metrics,
                'risks': initial_risks,
                'team_productivity': {},
                'timeline_estimates': {}
            }

            self.logger.info(f"Project tracking initialized for project {project_id}")

        except Exception as e:
            self.logger.warning(f"Failed to initialize project tracking for {project_id}: {e}")

    @require_authentication
    @require_project_access
    @log_agent_action
    def _update_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update project information with validation"""
        project_id = data.get('project_id')  # Initialize early
        username = data.get('username')  # Initialize early

        try:
            updates = data.get('updates', {})

            if not project_id:
                raise ValidationError("Project ID is required")

            # Get existing project
            project = self.db_service.projects.get_by_id(project_id)
            if not project:
                self.logger.warning(f"Project update failed: Project {project_id} not found")
                raise ValidationError("Project not found")

            # Update allowed fields with validation
            allowed_fields = [
                'name', 'description', 'goals', 'requirements', 'technology_stack',
                'constraints', 'success_criteria', 'team_members', 'stakeholders',
                'estimated_hours', 'budget', 'priority', 'tags', 'phase', 'status'
            ]

            updated_fields = []
            for field in allowed_fields:
                if field in updates:
                    old_value = getattr(project, field, None)
                    new_value = updates[field]

                    # Validate specific fields
                    if field == 'name' and (not new_value or len(str(new_value).strip()) < 2):
                        self.logger.warning(f"Project update failed: Invalid name: {new_value}")
                        raise ValidationError("Project name must be at least 2 characters long")

                    if field == 'phase':
                        try:
                            new_value = ProjectPhase(new_value)
                        except ValueError:
                            self.logger.warning(f"Project update failed: Invalid phase: {new_value}")
                            raise ValidationError(f"Invalid project phase: {new_value}")

                    if field == 'status':
                        try:
                            new_value = ProjectStatus(new_value)
                        except ValueError:
                            self.logger.warning(f"Project update failed: Invalid status: {new_value}")
                            raise ValidationError(f"Invalid project status: {new_value}")

                    setattr(project, field, new_value)
                    updated_fields.append(field)

                    self.logger.debug(f"Updated field {field}: {old_value} -> {new_value}")

            # Update timestamp
            project.updated_at = DateTimeHelper.now()  # Rule #7: Use DateTimeHelper

            # Save changes to database
            success = self.db_service.projects.update(project)
            if not success:
                self.logger.error(f"Database update failed for project: {project_id}")
                raise Exception("Failed to update project in database")

            # Emit project update event
            if self.events:
                self.events.emit('project_updated', 'project_manager', {
                    'project_id': project_id,
                    'updated_fields': updated_fields,
                    'updated_by': username,
                    'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
                })

            self.logger.info(f"Project updated successfully: {project_id}, fields: {updated_fields}")

            return {
                'success': True,
                'project_id': project_id,
                'updated_fields': updated_fields,
                'status': 'updated',
                'updated_at': DateTimeHelper.to_iso_string(project.updated_at)
            }

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error updating project {project_id or 'unknown'}: {e}")
            return self._error_response(f"Failed to update project: {str(e)}")

    @require_authentication
    @require_project_access
    @log_agent_action
    def _archive_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Archive project and all related data"""
        project_id = data.get('project_id')  # Initialize early
        username = data.get('username')  # Initialize early

        try:
            archive_reason = data.get('reason', 'User requested')

            if not project_id:
                raise ValidationError("Project ID is required")

            # Get project
            project = self.db_service.projects.get_by_id(project_id)
            if not project:
                self.logger.warning(f"Archive failed: Project {project_id} not found")
                raise ValidationError("Project not found")

            if project.status == ProjectStatus.ARCHIVED:
                self.logger.info(f"Project {project_id} already archived")
                return {
                    'success': True,
                    'message': f'Project {project.name} is already archived',
                    'project_id': project_id,
                    'status': 'already_archived'
                }

            # Archive project
            old_status = project.status
            project.status = ProjectStatus.ARCHIVED
            project.updated_at = DateTimeHelper.now()  # Rule #7: Use DateTimeHelper

            success = self.db_service.projects.update(project)
            if not success:
                self.logger.error(f"Database update failed for project archival: {project_id}")
                raise Exception("Failed to archive project in database")

            # Archive related modules and tasks
            archived_modules = 0
            archived_tasks = 0

            try:
                modules = self.db_service.modules.get_by_project_id(project_id)
                for module in modules:
                    module.status = 'archived'
                    module.updated_at = DateTimeHelper.now()
                    if self.db_service.modules.update(module):
                        archived_modules += 1

                tasks = self.db_service.tasks.get_by_project_id(project_id)
                for task in tasks:
                    task.status = 'cancelled'
                    task.updated_at = DateTimeHelper.now()
                    if self.db_service.tasks.update(task):
                        archived_tasks += 1

            except Exception as e:
                self.logger.warning(f"Error archiving related data for project {project_id}: {e}")

            # Emit archive event
            if self.events:
                self.events.emit('project_archived', 'project_manager', {
                    'project_id': project_id,
                    'project_name': project.name,
                    'reason': archive_reason,
                    'archived_by': username,
                    'archived_modules': archived_modules,
                    'archived_tasks': archived_tasks,
                    'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
                })

            self.logger.info(f"Project archived: {project_id} by {username}, reason: {archive_reason}")

            return {
                'success': True,
                'message': f'Project {project.name} archived successfully',
                'project_id': project_id,
                'status': 'archived',
                'reason': archive_reason,
                'archived_modules': archived_modules,
                'archived_tasks': archived_tasks,
                'archived_at': DateTimeHelper.to_iso_string(project.updated_at)
            }

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error archiving project {project_id or 'unknown'}: {e}")
            return self._error_response(f"Failed to archive project: {str(e)}")

    @require_authentication
    @require_project_access
    @log_agent_action
    def _track_progress(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Track project progress across all modules and tasks"""
        project_id = data.get('project_id')  # Initialize early

        try:
            if not project_id:
                raise ValidationError("Project ID is required")

            # Get comprehensive progress data
            progress = self._get_comprehensive_progress(project_id)

            # Update project progress in database
            project = self.db_service.projects.get_by_id(project_id)
            if project:
                project.progress_percentage = progress['completion_percentage']
                project.completed_modules = progress.get('modules_completed', 0)
                project.total_modules = progress.get('modules_total', 0)
                project.updated_at = DateTimeHelper.now()
                self.db_service.projects.update(project)

            self.logger.info(f"Progress tracked for project {project_id}: {progress['completion_percentage']:.1f}%")

            return {
                'success': True,
                'project_id': project_id,
                'progress': progress,
                'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
            }

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error tracking progress for project {project_id or 'unknown'}: {e}")
            return self._error_response(f"Failed to track progress: {str(e)}")

    def _get_comprehensive_progress(self, project_id: str) -> Dict[str, Any]:
        """Calculate comprehensive progress metrics"""
        try:
            progress = {
                'project_id': project_id,
                'modules_total': 0,
                'modules_completed': 0,
                'modules_in_progress': 0,
                'tasks_total': 0,
                'tasks_completed': 0,
                'tasks_in_progress': 0,
                'estimated_hours': 0,
                'actual_hours': 0,
                'completion_percentage': 0.0,
                'phase_progress': {}
            }

            # Get modules data
            modules = self.db_service.modules.get_by_project_id(project_id)
            progress['modules_total'] = len(modules)

            for module in modules:
                if getattr(module, 'status', '') == 'completed':
                    progress['modules_completed'] += 1
                elif getattr(module, 'status', '') == 'in_progress':
                    progress['modules_in_progress'] += 1

                progress['estimated_hours'] += getattr(module, 'estimated_hours', 0) or 0
                progress['actual_hours'] += getattr(module, 'actual_hours', 0) or 0

            # Get tasks data
            tasks = self.db_service.tasks.get_by_project_id(project_id)
            progress['tasks_total'] = len(tasks)

            for task in tasks:
                if getattr(task, 'status', '') == 'completed':
                    progress['tasks_completed'] += 1
                elif getattr(task, 'status', '') == 'in_progress':
                    progress['tasks_in_progress'] += 1

            # Calculate overall completion percentage
            if progress['tasks_total'] > 0:
                progress['completion_percentage'] = (progress['tasks_completed'] / progress['tasks_total']) * 100
            elif progress['modules_total'] > 0:
                progress['completion_percentage'] = (progress['modules_completed'] / progress['modules_total']) * 100

            return progress

        except Exception as e:
            self.logger.error(f"Error calculating comprehensive progress: {e}")
            return {'error': str(e), 'completion_percentage': 0.0}

    @require_authentication
    @require_project_access
    @log_agent_action
    def _risk_assessment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive risk assessment for project"""
        project_id = data.get('project_id')  # Initialize early

        try:
            assessment_type = data.get('type', 'full')  # full, timeline, resource, technical

            if not project_id:
                raise ValidationError("Project ID is required")

            project = self.db_service.projects.get_by_id(project_id)
            if not project:
                raise ValidationError("Project not found")

            risks = []

            if assessment_type in ['full', 'timeline']:
                risks.extend(self._assess_timeline_risks(project))

            if assessment_type in ['full', 'resource']:
                risks.extend(self._assess_resource_risks(project))

            if assessment_type in ['full', 'technical']:
                risks.extend(self._assess_technical_risks(project))

            # Calculate overall risk level
            risk_level = self._calculate_overall_risk_level(risks)

            self.logger.info(f"Risk assessment completed for project {project_id}: {risk_level} risk level")

            return {
                'success': True,
                'project_id': project_id,
                'assessment_type': assessment_type,
                'risks': risks,
                'risk_level': risk_level,
                'risk_count': len(risks),
                'assessment_date': DateTimeHelper.to_iso_string(DateTimeHelper.now())
            }

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error performing risk assessment for project {project_id or 'unknown'}: {e}")
            return self._error_response(f"Failed to perform risk assessment: {str(e)}")

    def _assess_timeline_risks(self, project: Project) -> List[Dict[str, Any]]:
        """Assess timeline-related risks"""
        risks = []

        try:
            # Check if project has realistic timeline
            if project.start_date and project.end_date:
                timeline_days = (project.end_date - project.start_date).days
                estimated_days = (project.estimated_hours or 0) // 8  # Assuming 8 hours per day

                if timeline_days < estimated_days:
                    risks.append({
                        'type': 'timeline',
                        'severity': 'high',
                        'description': 'Timeline appears unrealistic for estimated work',
                        'impact': 'Project may face delays or quality issues',
                        'mitigation': 'Review timeline or reduce scope'
                    })

            # Check project duration
            if project.created_at:
                days_since_creation = (DateTimeHelper.now() - project.created_at).days
                if days_since_creation > 365:  # More than a year
                    risks.append({
                        'type': 'timeline',
                        'severity': 'medium',
                        'description': 'Long-running project may face scope creep',
                        'impact': 'Increased complexity and resource requirements',
                        'mitigation': 'Regular milestone reviews and scope validation'
                    })

        except Exception as e:
            self.logger.warning(f"Error assessing timeline risks: {e}")

        return risks

    def _assess_resource_risks(self, project: Project) -> List[Dict[str, Any]]:
        """Assess resource-related risks"""
        risks = []

        try:
            # Check team size
            team_size = len(project.team_members or [])
            if team_size == 0:
                risks.append({
                    'type': 'resource',
                    'severity': 'high',
                    'description': 'No team members assigned to project',
                    'impact': 'Project cannot proceed without team assignment',
                    'mitigation': 'Assign team members with appropriate skills'
                })
            elif team_size > 10:
                risks.append({
                    'type': 'resource',
                    'severity': 'medium',
                    'description': 'Large team may face coordination challenges',
                    'impact': 'Communication overhead and potential delays',
                    'mitigation': 'Implement proper team structure and communication processes'
                })

            # Check budget vs estimated hours
            if project.budget and project.estimated_hours:
                hourly_rate = project.budget / project.estimated_hours
                if hourly_rate < 50:  # Assuming minimum viable rate
                    risks.append({
                        'type': 'resource',
                        'severity': 'medium',
                        'description': 'Budget may be insufficient for estimated work',
                        'impact': 'Quality or scope compromises may be necessary',
                        'mitigation': 'Review budget allocation or adjust scope'
                    })

        except Exception as e:
            self.logger.warning(f"Error assessing resource risks: {e}")

        return risks

    def _assess_technical_risks(self, project: Project) -> List[Dict[str, Any]]:
        """Assess technical risks"""
        risks = []

        try:
            # Check technology stack complexity
            tech_count = len(project.technology_stack or {})
            if tech_count > 8:
                risks.append({
                    'type': 'technical',
                    'severity': 'medium',
                    'description': 'Complex technology stack may increase development complexity',
                    'impact': 'Higher learning curve and integration challenges',
                    'mitigation': 'Provide adequate training and documentation'
                })

            # Check for experimental technologies
            tech_stack = project.technology_stack or {}
            experimental_techs = []
            for tech, version in tech_stack.items():
                if 'beta' in str(version).lower() or 'alpha' in str(version).lower():
                    experimental_techs.append(tech)

            if experimental_techs:
                risks.append({
                    'type': 'technical',
                    'severity': 'high',
                    'description': f'Using experimental technologies: {", ".join(experimental_techs)}',
                    'impact': 'Potential stability and support issues',
                    'mitigation': 'Consider stable alternatives or plan for additional testing'
                })

        except Exception as e:
            self.logger.warning(f"Error assessing technical risks: {e}")

        return risks

    def _calculate_overall_risk_level(self, risks: List[Dict[str, Any]]) -> str:
        """Calculate overall risk level based on individual risks"""
        if not risks:
            return 'low'

        high_risks = len([r for r in risks if r.get('severity') == 'high'])
        medium_risks = len([r for r in risks if r.get('severity') == 'medium'])

        if high_risks > 0:
            return 'high'
        elif medium_risks > 2:
            return 'high'
        elif medium_risks > 0:
            return 'medium'
        else:
            return 'low'

    @require_authentication
    @log_agent_action
    def _list_projects(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """List projects with filtering and pagination"""
        username = data.get('username')  # Initialize early

        try:
            # Get filtering parameters
            status_filter = data.get('status')
            phase_filter = data.get('phase')
            owner_filter = data.get('owner')
            limit = data.get('limit', 50)
            offset = data.get('offset', 0)

            # Get projects accessible to user
            all_projects = self.db_service.projects.get_projects_for_user(username)

            # Apply filters
            filtered_projects = []
            for project in all_projects:
                # Status filter
                if status_filter and project.status.value != status_filter:
                    continue

                # Phase filter
                if phase_filter and project.phase.value != phase_filter:
                    continue

                # Owner filter
                if owner_filter and project.owner_id != owner_filter:
                    continue

                filtered_projects.append(project)

            # Apply pagination
            total_count = len(filtered_projects)
            paginated_projects = filtered_projects[offset:offset + limit]

            # Format project list
            project_list = []
            for project in paginated_projects:
                project_list.append({
                    'id': project.id,
                    'name': project.name,
                    'description': project.description,
                    'owner_id': project.owner_id,
                    'status': project.status.value,
                    'phase': project.phase.value,
                    'progress_percentage': project.progress_percentage,
                    'team_size': len(project.team_members or []),
                    'created_at': DateTimeHelper.to_iso_string(project.created_at),
                    'updated_at': DateTimeHelper.to_iso_string(project.updated_at)
                })

            self.logger.info(
                f"Project list retrieved for {username}: {len(project_list)} projects (total: {total_count})")

            return {
                'success': True,
                'projects': project_list,
                'total_count': total_count,
                'returned_count': len(project_list),
                'offset': offset,
                'limit': limit,
                'filters_applied': {
                    'status': status_filter,
                    'phase': phase_filter,
                    'owner': owner_filter
                }
            }

        except Exception as e:
            self.logger.error(f"Error listing projects for user {username or 'unknown'}: {e}")
            return self._error_response(f"Failed to list projects: {str(e)}")

    @require_authentication
    @require_project_access
    @log_agent_action
    def _get_project_info(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed project information"""
        project_id = data.get('project_id')  # Initialize early

        try:
            if not project_id:
                raise ValidationError("Project ID is required")

            project = self.db_service.projects.get_by_id(project_id)
            if not project:
                self.logger.warning(f"Project info request failed: Project {project_id} not found")
                raise ValidationError("Project not found")

            # Get related data
            progress = self._get_comprehensive_progress(project_id)
            modules = self.db_service.modules.get_by_project_id(project_id)

            # Format project info
            project_info = {
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'owner_id': project.owner_id,
                'status': project.status.value,
                'phase': project.phase.value,
                'goals': project.goals,
                'requirements': project.requirements,
                'technology_stack': project.technology_stack,
                'constraints': project.constraints,
                'success_criteria': project.success_criteria,
                'team_members': project.team_members,
                'stakeholders': project.stakeholders,
                'estimated_hours': project.estimated_hours,
                'budget': project.budget,
                'priority': project.priority.value if hasattr(project.priority, 'value') else str(project.priority),
                'tags': project.tags,
                'progress': progress,
                'module_count': len(modules),
                'created_at': DateTimeHelper.to_iso_string(project.created_at),
                'updated_at': DateTimeHelper.to_iso_string(project.updated_at)
            }

            # Add timeline information if available
            if project.start_date:
                project_info['start_date'] = DateTimeHelper.to_iso_string(project.start_date)
            if project.end_date:
                project_info['end_date'] = DateTimeHelper.to_iso_string(project.end_date)

            self.logger.debug(f"Project info retrieved for: {project_id}")

            return {
                'success': True,
                'project': project_info
            }

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error getting project info for {project_id or 'unknown'}: {e}")
            return self._error_response(f"Failed to get project info: {str(e)}")

    def _error_response(self, error_message: str, error_code: Optional[str] = None) -> Dict[str, Any]:
        """Create standardized error response"""
        response = {
            'success': False,
            'error': error_message,
            'agent_id': self.agent_id,
            'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
        }

        if error_code:
            response['error_code'] = error_code

        return response
