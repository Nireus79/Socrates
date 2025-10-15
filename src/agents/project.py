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

try:
    from src.core import ServiceContainer, DateTimeHelper, ValidationError, ValidationHelper
    from src.models import Project, Module, Task, ProjectStatus, ProjectPhase, TaskPriority, ModelValidator
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

    class ServiceContainer:
        def get_logger(self, name):
            import logging
            return logging.getLogger(name)

        def get_config(self):
            return {}

        def get_event_bus(self):
            return None

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


    def require_authentication(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper


    def require_project_access(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper


    def log_agent_action(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper


class ProjectManagerAgent(BaseAgent):
    """
    Enhanced project management agent with module hierarchy

    Absorbs: ModuleManagerAgent capabilities for hierarchical management
    Capabilities: Complete project lifecycle, team coordination, progress tracking
    """

    def __init__(self, services: Optional[ServiceContainer] = None):
        """Initialize ProjectManagerAgent with ServiceContainer dependency injection"""
        super().__init__("project_manager", "Project Manager", services)
        if self.logger:
            self.logger.info("ProjectManagerAgent initialized successfully")

    def get_capabilities(self) -> List[str]:
        """Return list of capabilities this agent provides"""
        return [
            "create_project", "update_project", "archive_project",
            "delete_project", "manage_modules",
            "assign_tasks", "track_progress", "manage_collaborators",
            "generate_reports", "risk_assessment", "resource_allocation",
            "timeline_management", "get_project_info", "list_projects",
            "project_analytics", "toggle_solo_mode", "get_solo_projects"  # C2: Solo mode
        ]

    @require_authentication
    @log_agent_action
    def _create_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new project with full setup and validation"""
        username = data.get('username')

        try:
            # Extract and validate project data
            project_data = {
                'name': data.get('name'),
                'description': data.get('description', ''),
                'owner_id': data.get('owner_id') or username,
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
                'is_solo_project': data.get('is_solo_project', False),  # C2: Solo mode field
                'created_at': DateTimeHelper.now(),
                'updated_at': DateTimeHelper.now()
            }

            # C2: Auto-detect solo mode if not explicitly set
            if not data.get('is_solo_project') and self._should_be_solo_mode(project_data):
                project_data['is_solo_project'] = True

            # Validate required fields
            if not project_data['name']:
                raise ValidationError("Project name is required")
            if not project_data['owner_id']:
                raise ValidationError("Project owner is required")

            # Validate data using model validator
            validation_issues = ModelValidator.validate_project_data(project_data)
            if validation_issues:
                raise ValidationError(f"Project validation failed: {', '.join(validation_issues)}")

            # Create project in database
            project = Project(**project_data)
            try:
                if not self.db:
                    return self._error_response("Database service not available", "DB_UNAVAILABLE")
                created_project = self.db.projects.create(project)
            except Exception as e:
                return self._error_response(f"Failed to create project: {e}", "DB_ERROR")

            # Check if creation was successful
            if not created_project:
                raise ValidationError("Failed to create project in database")

            # Initialize project tracking systems
            self._initialize_project_tracking(created_project.id)

            # Emit project creation event
            if self.events:
                self.events.emit('project_created', {
                    'project_id': created_project.id,
                    'owner_id': username,
                    'name': project_data['name']
                })

            self.logger.info(f"Project created successfully: {created_project.id} by {username}")

            return self._success_response(
                "Project created successfully",
                {
                    'project_id': created_project.id,
                    'name': created_project.name,
                    'status': created_project.status.value,
                    'phase': created_project.phase.value,
                    'is_solo_project': created_project.is_solo_project,  # C2: Include solo mode
                    'created_at': DateTimeHelper.to_iso_string(created_project.created_at)
                }
            )

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
        project_id = data.get('project_id')
        username = data.get('username')

        try:
            updates = data.get('updates', {})

            if not project_id:
                raise ValidationError("Project ID is required")

            # Get existing project
            project = self.db.projects.get_by_id(project_id)
            if not project:
                self.logger.warning(f"Project update failed: Project {project_id} not found")
                raise ValidationError("Project not found")

            # Update allowed fields with validation
            allowed_fields = [
                'name', 'description', 'requirements', 'technology_stack',
                'constraints', 'success_criteria', 'team_members', 'stakeholders',
                'estimated_hours', 'budget', 'priority', 'tags', 'phase', 'status'
            ]

            updated_fields = []
            for field in allowed_fields:
                if field in updates:
                    setattr(project, field, updates[field])
                    updated_fields.append(field)

            # Update timestamp
            project.updated_at = DateTimeHelper.now()

            # Save updated project
            try:
                if not self.db:
                    return self._error_response("Database service not available", "DB_UNAVAILABLE")
                updated_project = self.db.projects.update(project)
            except Exception as e:
                return self._error_response(f"Failed to update project: {e}", "DB_ERROR")

            # C6: Trigger architecture analysis if phase is changing to DESIGN
            optimizer_analysis = None
            if 'phase' in updated_fields:
                new_phase = updates.get('phase')
                if new_phase in [ProjectPhase.DESIGN, 'design'] or (hasattr(ProjectPhase, 'DESIGN') and new_phase == ProjectPhase.DESIGN.value):
                    try:
                        optimizer_analysis = self._call_optimizer_for_project(project_id)
                        if optimizer_analysis and optimizer_analysis.get('success'):
                            analysis_data = optimizer_analysis.get('data', {})
                            risk_level = analysis_data.get('risk_level', 'unknown')
                            issues_found = analysis_data.get('issues_found', 0)

                            if issues_found > 0:
                                self.logger.warning(
                                    f"C6: Project {project_id} entering DESIGN phase with {issues_found} "
                                    f"architecture issues (Risk: {risk_level}). Review recommended."
                                )
                    except Exception as e:
                        self.logger.warning(f"C6 optimizer analysis failed: {e}")

            # Emit update event
            if self.events:
                self.events.emit('project_updated', {
                    'project_id': project_id,
                    'updated_by': username,
                    'fields_updated': updated_fields
                })

            self.logger.info(f"Project {project_id} updated successfully by {username}")

            response_data = {
                'project_id': updated_project.id,
                'fields_updated': updated_fields,
                'updated_at': DateTimeHelper.to_iso_string(updated_project.updated_at)
            }

            # Include C6 analysis if available
            if optimizer_analysis and optimizer_analysis.get('success'):
                response_data['c6_architecture_analysis'] = optimizer_analysis.get('data', {})

            return self._success_response(
                "Project updated successfully",
                response_data
            )

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error updating project {project_id or 'unknown'}: {e}")
            return self._error_response(f"Failed to update project: {str(e)}")

    @require_authentication
    @require_project_access
    @log_agent_action
    def _archive_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Archive project with proper cleanup"""
        project_id = data.get('project_id')
        username = data.get('username')

        try:
            if not project_id:
                raise ValidationError("Project ID is required")

            # Get project
            try:
                if not self.db:
                    return self._error_response("Database service not available", "DB_UNAVAILABLE")
                project = self.db.projects.get_by_id(project_id)
                if not project:
                    raise ValidationError("Project not found")

                # Update status to archived
                project.status = ProjectStatus.ARCHIVED
                project.updated_at = DateTimeHelper.now()

                # Save changes
                self.db.projects.update(project)
            except Exception as e:
                if isinstance(e, ValidationError):
                    raise
                return self._error_response(f"Database error: {e}", "DB_ERROR")

            # Emit archive event
            if self.events:
                self.events.emit('project_archived', {
                    'project_id': project_id,
                    'archived_by': username
                })

            self.logger.info(f"Project {project_id} archived by {username}")

            return self._success_response(
                "Project archived successfully",
                {
                    'project_id': project_id,
                    'status': 'archived',
                    'archived_at': DateTimeHelper.to_iso_string(project.updated_at)
                }
            )

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error archiving project {project_id or 'unknown'}: {e}")
            return self._error_response(f"Failed to archive project: {str(e)}")

    def _delete_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Permanently delete project and all related data (hard delete)"""
        project_id = data.get('project_id')
        username = data.get('username')
        user_id = data.get('user_id')

        try:
            if not project_id:
                raise ValidationError("Project ID is required")

            # Get project
            project = self.db.projects.get_by_id(project_id)
            if not project:
                raise ValidationError("Project not found")

            # Authorization check: Only owner can delete
            if project.owner_id != user_id:
                raise ValidationError("Only the project owner can delete this project")

            # Delete the project (cascade handled by database if foreign keys exist)
            deleted = self.db.projects.delete(project_id)

            if not deleted:
                raise ValidationError("Failed to delete project")

            # Emit deletion event
            if self.events:
                self.events.emit('project_deleted', {
                    'project_id': project_id,
                    'project_name': project.name,
                    'deleted_by': username
                })

            self.logger.info(f"Project {project_id} permanently deleted by {username}")

            return self._success_response(
                "Project deleted successfully",
                {'project_id': project_id}
            )

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error deleting project {project_id or 'unknown'}: {e}")
            return self._error_response(f"Failed to delete project: {str(e)}")

    @require_authentication
    @require_project_access
    @log_agent_action
    def _manage_modules(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Manage project modules (create, update, delete)"""
        action = data.get('action')
        project_id = data.get('project_id')

        try:
            if not project_id:
                raise ValidationError("Project ID is required")

            if action == 'create':
                return self._create_module(data)
            elif action == 'update':
                return self._update_module(data)
            elif action == 'delete':
                return self._delete_module(data)
            elif action == 'list':
                return self._list_modules(data)
            else:
                raise ValidationError(f"Unknown module action: {action}")

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error managing modules: {e}")
            return self._error_response(f"Failed to manage modules: {str(e)}")

    def _create_module(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new module in project"""
        try:
            module_data = {
                'project_id': data.get('project_id'),
                'name': data.get('name'),
                'description': data.get('description', ''),
                'order': data.get('order', 0),
                'phase': data.get('phase', ProjectPhase.PLANNING),
                'estimated_hours': data.get('estimated_hours'),
                'dependencies': data.get('dependencies', []),
                'created_at': DateTimeHelper.now(),
                'updated_at': DateTimeHelper.now()
            }

            # Validate required fields
            if not module_data['name']:
                raise ValidationError("Module name is required")

            # Create module
            module = Module(**module_data)
            created_module = self.db.modules.create(module)

            self.logger.info(f"Module created: {created_module.id} in project {module_data['project_id']}")

            return self._success_response(
                "Module created successfully",
                {
                    'module_id': created_module.id,
                    'name': created_module.name,
                    'project_id': created_module.project_id
                }
            )

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error creating module: {e}")
            return self._error_response(f"Failed to create module: {str(e)}")

    def _update_module(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing module"""
        module_id = data.get('module_id')

        try:
            if not module_id:
                raise ValidationError("Module ID is required")

            try:
                if not self.db:
                    return self._error_response("Database service not available", "DB_UNAVAILABLE")
                module = self.db.modules.get_by_id(module_id)
                if not module:
                    raise ValidationError("Module not found")

                # Update fields
                updates = data.get('updates', {})
                allowed_fields = ['name', 'description', 'order', 'phase', 'estimated_hours', 'dependencies']

                for field in allowed_fields:
                    if field in updates:
                        setattr(module, field, updates[field])

                module.updated_at = DateTimeHelper.now()
                updated_module = self.db.modules.update(module)
            except Exception as e:
                if isinstance(e, ValidationError):
                    raise
                return self._error_response(f"Database error: {e}", "DB_ERROR")

            return self._success_response(
                "Module updated successfully",
                {'module_id': updated_module.id}
            )

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error updating module: {e}")
            return self._error_response(f"Failed to update module: {str(e)}")

    def _delete_module(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Delete module from project"""
        module_id = data.get('module_id')

        try:
            if not module_id:
                raise ValidationError("Module ID is required")

            # Delete module
            try:
                if not self.db:
                    return self._error_response("Database service not available", "DB_UNAVAILABLE")
                deleted = self.db.modules.delete(module_id)
            except Exception as e:
                return self._error_response(f"Failed to delete module: {e}", "DB_ERROR")

            if deleted:
                return self._success_response("Module deleted successfully", {'module_id': module_id})
            else:
                raise ValidationError("Module not found")

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error deleting module: {e}")
            return self._error_response(f"Failed to delete module: {str(e)}")

    def _list_modules(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """List all modules for a project"""
        project_id = data.get('project_id')

        try:
            if not project_id:
                raise ValidationError("Project ID is required")

            try:
                if not self.db:
                    return self._error_response("Database service not available", "DB_UNAVAILABLE")
                modules = self.db.modules.get_by_project_id(project_id)
            except Exception as e:
                return self._error_response(f"Failed to retrieve modules: {e}", "DB_ERROR")

            module_list = []
            for module in modules:
                module_list.append({
                    'id': module.id,
                    'name': module.name,
                    'description': module.description,
                    'phase': module.phase.value if hasattr(module.phase, 'value') else module.phase,
                    'estimated_hours': module.estimated_hours,
                    'order': module.order
                })

            return self._success_response(
                "Modules retrieved successfully",
                {'modules': module_list, 'count': len(module_list)}
            )

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error listing modules: {e}")
            return self._error_response(f"Failed to list modules: {str(e)}")

    @require_authentication
    @require_project_access
    @log_agent_action
    def _track_progress(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Track and calculate project progress"""
        project_id = data.get('project_id')

        try:
            if not project_id:
                raise ValidationError("Project ID is required")

            # Get comprehensive progress metrics
            progress = self._get_comprehensive_progress(project_id)

            # Update project with calculated progress
            try:
                if self.db:
                    project = self.db.projects.get_by_id(project_id)
                    if project:
                        project.progress_percentage = progress.get('completion_percentage', 0.0)
                        project.updated_at = DateTimeHelper.now()
                        self.db.projects.update(project)
            except Exception as e:
                self.logger.warning(f"Could not update project progress: {e}")

            self.logger.info(f"Progress tracked for project {project_id}: {progress.get('completion_percentage')}%")

            return self._success_response(
                "Progress tracked successfully",
                progress
            )

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
            try:
                if not self.db:
                    return {'error': 'Database not available', 'completion_percentage': 0.0}
                modules = self.db.modules.get_by_project_id(project_id)
                tasks = self.db.tasks.get_by_project_id(project_id)
            except Exception as e:
                self.logger.error(f"Error getting project data: {e}")
                return {'error': str(e), 'completion_percentage': 0.0}
            progress['modules_total'] = len(modules)

            for module in modules:
                if getattr(module, 'status', '') == 'completed':
                    progress['modules_completed'] += 1
                elif getattr(module, 'status', '') == 'in_progress':
                    progress['modules_in_progress'] += 1

                progress['estimated_hours'] += getattr(module, 'estimated_hours', 0) or 0
                progress['actual_hours'] += getattr(module, 'actual_hours', 0) or 0

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
    @log_agent_action
    def _list_projects(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """List projects with filtering and pagination"""
        username = data.get('username')

        try:
            # Get filter parameters
            status_filter = data.get('status')
            phase_filter = data.get('phase')
            owner_filter = data.get('owner')
            limit = data.get('limit', 50)
            offset = data.get('offset', 0)

            # Get all projects for user
            try:
                if not self.db:
                    return self._error_response("Database service not available", "DB_UNAVAILABLE")
                all_projects = self.db.projects.get_by_owner(username)
            except Exception as e:
                return self._error_response(f"Failed to retrieve projects: {e}", "DB_ERROR")

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
                    'is_solo_project': getattr(project, 'is_solo_project', False),  # C2: Include solo mode
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
        project_id = data.get('project_id')

        try:
            if not project_id:
                raise ValidationError("Project ID is required")

            try:
                if not self.db:
                    return self._error_response("Database service not available", "DB_UNAVAILABLE")
                project = self.db.projects.get_by_id(project_id)
            except Exception as e:
                return self._error_response(f"Database error: {e}", "DB_ERROR")

            if not project:
                self.logger.warning(f"Project info request failed: Project {project_id} not found")
                raise ValidationError("Project not found")
            if not project:
                self.logger.warning(f"Project info request failed: Project {project_id} not found")
                raise ValidationError("Project not found")

            # Get related data
            try:
                modules = self.db.modules.get_by_project_id(project_id)
                tasks = self.db.tasks.get_by_project_id(project_id)
            except Exception as e:
                return self._error_response(f"Failed to retrieve project data: {e}", "DB_ERROR")

            # Format response
            project_info = {
                'id': project.id,
                'name': project.name,
                'description': project.description,
                'owner_id': project.owner_id,
                'status': project.status.value,
                'phase': project.phase.value,
                'progress_percentage': project.progress_percentage,
                'is_solo_project': getattr(project, 'is_solo_project', False),  # C2: Include solo mode
                'requirements': project.requirements,
                'technology_stack': project.technology_stack,
                'constraints': project.constraints,
                'success_criteria': project.success_criteria,
                'team_members': project.team_members,
                'stakeholders': project.stakeholders,
                'estimated_hours': project.estimated_hours,
                'budget': project.budget,
                'priority': project.priority,
                'tags': project.tags,
                'created_at': DateTimeHelper.to_iso_string(project.created_at),
                'updated_at': DateTimeHelper.to_iso_string(project.updated_at),
                'modules_count': len(modules),
                'tasks_count': len(tasks)
            }

            return self._success_response(
                "Project information retrieved successfully",
                project_info
            )

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error getting project info for {project_id or 'unknown'}: {e}")
            return self._error_response(f"Failed to get project info: {str(e)}")

    @require_authentication
    @require_project_access
    @log_agent_action
    def _risk_assessment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive risk assessment for project"""
        project_id = data.get('project_id')

        try:
            if not project_id:
                raise ValidationError("Project ID is required")

            project = self.db.projects.get_by_id(project_id)
            if not project:
                raise ValidationError("Project not found")

            # Analyze various risk factors
            risks = {
                'timeline_risks': self._assess_timeline_risks(project),
                'resource_risks': self._assess_resource_risks(project),
                'technical_risks': self._assess_technical_risks(project),
                'team_risks': self._assess_team_risks(project),
                'overall_risk_level': 'low'
            }

            # Calculate overall risk level
            risk_counts = {'high': 0, 'medium': 0, 'low': 0}
            for risk_category in ['timeline_risks', 'resource_risks', 'technical_risks', 'team_risks']:
                for risk in risks[risk_category]:
                    risk_counts[risk.get('severity', 'low')] += 1

            if risk_counts['high'] > 0:
                risks['overall_risk_level'] = 'high'
            elif risk_counts['medium'] > 1:
                risks['overall_risk_level'] = 'medium'
            else:
                risks['overall_risk_level'] = 'low'

            return self._success_response(
                "Risk assessment completed",
                risks
            )

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error performing risk assessment: {e}")
            return self._error_response(f"Failed to assess risks: {str(e)}")

    def _assess_timeline_risks(self, project: Project) -> List[Dict[str, Any]]:
        """Assess timeline-related risks"""
        risks = []

        # Check if estimated hours are reasonable
        if project.estimated_hours and project.estimated_hours < 10:
            risks.append({
                'risk': 'Underestimated project timeline',
                'severity': 'medium',
                'description': 'Project estimated hours seem very low'
            })

        return risks

    def _assess_resource_risks(self, project: Project) -> List[Dict[str, Any]]:
        """Assess resource-related risks"""
        risks = []

        # Check team size
        team_size = len(project.team_members or [])
        if team_size == 0:
            risks.append({
                'risk': 'No team members assigned',
                'severity': 'high',
                'description': 'Project has no team members assigned'
            })
        elif team_size < 2:
            risks.append({
                'risk': 'Single person project',
                'severity': 'medium',
                'description': 'Project relies on single team member'
            })

        return risks

    def _assess_technical_risks(self, project: Project) -> List[Dict[str, Any]]:
        """Assess technical risks"""
        risks = []

        # Check if technology stack is defined
        if not project.technology_stack or len(project.technology_stack) == 0:
            risks.append({
                'risk': 'Undefined technology stack',
                'severity': 'medium',
                'description': 'Technology stack not clearly defined'
            })

        return risks

    def _assess_team_risks(self, project: Project) -> List[Dict[str, Any]]:
        """Assess team-related risks"""
        risks = []

        # Check if stakeholders are defined
        if not project.stakeholders or len(project.stakeholders) == 0:
            risks.append({
                'risk': 'No stakeholders identified',
                'severity': 'low',
                'description': 'Project stakeholders not clearly identified'
            })

        return risks

    def _should_be_solo_mode(self, project_data: Dict[str, Any]) -> bool:
        """
        C2: Determine if project should be in solo mode based on team configuration

        Args:
            project_data: Project data dictionary

        Returns:
            True if project should be solo mode, False otherwise
        """
        try:
            # Check team_members list
            team_members = project_data.get('team_members', [])
            stakeholders = project_data.get('stakeholders', [])

            # Solo mode if no team members and no stakeholders
            if len(team_members) == 0 and len(stakeholders) == 0:
                return True

            # Solo mode if only owner is in team (no collaborators yet)
            if len(team_members) <= 1:
                return True

            return False
        except Exception as e:
            self.logger.warning(f"Error detecting solo mode: {e}")
            return False

    @require_authentication
    @require_project_access
    @log_agent_action
    def _toggle_solo_mode(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        C2: Toggle solo mode for a project

        Args:
            data: Contains project_id, is_solo_project (boolean), user_id

        Returns:
            Success response with updated project data
        """
        project_id = data.get('project_id')
        is_solo = data.get('is_solo_project')
        username = data.get('username')

        try:
            if not project_id:
                raise ValidationError("Project ID is required")

            if is_solo is None:
                raise ValidationError("is_solo_project value is required")

            # Get project
            project = self.db.projects.get_by_id(project_id)
            if not project:
                raise ValidationError("Project not found")

            # Update solo mode
            project.is_solo_project = bool(is_solo)
            project.updated_at = DateTimeHelper.now()

            # Save changes
            updated_project = self.db.projects.update(project)

            # Emit event
            if self.events:
                self.events.emit('project_solo_mode_toggled', {
                    'project_id': project_id,
                    'is_solo_project': is_solo,
                    'updated_by': username
                })

            self.logger.info(f"Project {project_id} solo mode set to {is_solo} by {username}")

            return self._success_response(
                f"Project solo mode {'enabled' if is_solo else 'disabled'}",
                {
                    'project_id': project_id,
                    'is_solo_project': updated_project.is_solo_project,
                    'updated_at': DateTimeHelper.to_iso_string(updated_project.updated_at)
                }
            )

        except ValidationError:
            raise
        except Exception as e:
            self.logger.error(f"Error toggling solo mode for project {project_id or 'unknown'}: {e}")
            return self._error_response(f"Failed to toggle solo mode: {str(e)}")

    @require_authentication
    @log_agent_action
    def _get_solo_projects(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        C2: Get all solo projects for a user

        Args:
            data: Contains user_id

        Returns:
            List of solo projects
        """
        username = data.get('username')

        try:
            # Get all projects for user
            all_projects = self.db.projects.get_by_owner(username)

            # Filter for solo projects
            solo_projects = [p for p in all_projects if getattr(p, 'is_solo_project', False)]

            # Format project list
            project_list = []
            for project in solo_projects:
                project_list.append({
                    'id': project.id,
                    'name': project.name,
                    'description': project.description,
                    'status': project.status.value,
                    'phase': project.phase.value,
                    'progress_percentage': project.progress_percentage,
                    'created_at': DateTimeHelper.to_iso_string(project.created_at),
                    'updated_at': DateTimeHelper.to_iso_string(project.updated_at)
                })

            self.logger.info(f"Retrieved {len(project_list)} solo projects for {username}")

            return self._success_response(
                "Solo projects retrieved successfully",
                {
                    'projects': project_list,
                    'count': len(project_list)
                }
            )

        except Exception as e:
            self.logger.error(f"Error getting solo projects for {username or 'unknown'}: {e}")
            return self._error_response(f"Failed to get solo projects: {str(e)}")

    def _call_optimizer_for_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """
        C6: Call Architecture Optimizer to analyze project architecture

        Args:
            project_id: Project identifier

        Returns:
            Optimizer analysis result or None if optimizer unavailable
        """
        try:
            # Get project and technical spec
            project = self.db.projects.get_by_id(project_id)
            if not project:
                self.logger.warning(f"C6: Cannot analyze project {project_id} - not found")
                return None

            # Get latest technical specification
            tech_specs = []
            try:
                tech_specs = self.db.technical_specifications.get_by_project_id(project_id)
            except Exception as e:
                self.logger.debug(f"C6: No tech specs found for project: {e}")

            tech_spec = tech_specs[0] if tech_specs else None

            # If no tech spec, create basic spec from project data
            if not tech_spec:
                tech_spec_data = {
                    'project_id': project_id,
                    'architecture_type': '',
                    'technology_stack': project.technology_stack or {},
                    'functional_requirements': project.requirements or [],
                    'non_functional_requirements': [],
                    'security_requirements': [],
                    'performance_requirements': {},
                    'scalability_requirements': {},
                    'testing_strategy': {},
                    'monitoring_requirements': []
                }
            else:
                # Convert tech spec to dict
                tech_spec_data = {
                    'architecture_type': tech_spec.architecture_type,
                    'technology_stack': tech_spec.technology_stack,
                    'functional_requirements': tech_spec.functional_requirements,
                    'non_functional_requirements': tech_spec.non_functional_requirements,
                    'security_requirements': tech_spec.security_requirements,
                    'performance_requirements': tech_spec.performance_requirements,
                    'scalability_requirements': tech_spec.scalability_requirements,
                    'testing_strategy': tech_spec.testing_strategy,
                    'monitoring_requirements': tech_spec.monitoring_requirements
                }

            # Import and initialize optimizer
            try:
                from .optimizer import ArchitectureOptimizerAgent
            except ImportError:
                self.logger.debug("C6: ArchitectureOptimizerAgent not available")
                return None

            optimizer = ArchitectureOptimizerAgent(self.services)

            # Call optimizer
            result = optimizer.process_request('analyze_architecture', {
                'project_id': project_id,
                'technical_spec': tech_spec_data,
                'analysis_depth': 'deep',
                'user_id': 'system',
                '_skip_auth': True
            })

            if result and result.get('success'):
                self.logger.info(f"C6: Architecture analysis complete for project {project_id}")
                return result
            else:
                error = result.get('error', 'Unknown error') if result else 'No result'
                self.logger.warning(f"C6: Architecture analysis failed for project {project_id}: {error}")
                return None

        except Exception as e:
            self.logger.error(f"C6: Error calling optimizer for project {project_id}: {e}")
            return None


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = ['ProjectManagerAgent']

if __name__ == "__main__":
    print("ProjectManagerAgent module - use via AgentOrchestrator")
