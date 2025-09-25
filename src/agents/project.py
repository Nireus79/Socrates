"""
Socratic RAG Enhanced - Project Management Agent
Handles project lifecycle, module hierarchy, team coordination, and progress tracking
"""

import json
import logging
import time
from dataclasses import asdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from src.agents.base import BaseAgent
from src.models import (
    ProjectContext, ModuleContext, TaskContext, User
)
from src.utils import validate_project_data


class ProjectManagerAgent(BaseAgent):
    """
    Enhanced project management agent with module hierarchy

    Absorbs: ModuleManagerAgent capabilities for hierarchical management
    Capabilities: Complete project lifecycle, team coordination, progress tracking
    """

    def __init__(self):
        super().__init__("project_manager", "Project Manager")

    def get_capabilities(self) -> List[str]:
        return [
            "create_project", "update_project", "archive_project", "manage_modules",
            "assign_tasks", "track_progress", "manage_collaborators", "generate_reports",
            "risk_assessment", "resource_allocation", "timeline_management"
        ]

    def _create_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new project with full setup"""
        project_data = {
            'name': data.get('name'),
            'description': data.get('description'),
            'owner': data.get('owner'),
            'collaborators': data.get('collaborators', []),
            'goals': data.get('goals', ''),
            'requirements': data.get('requirements', []),
            'tech_stack': data.get('tech_stack', []),
            'constraints': data.get('constraints', []),
            'team_structure': data.get('team_structure', ''),
            'language_preferences': data.get('language_preferences', []),
            'deployment_target': data.get('deployment_target', ''),
            'code_style': data.get('code_style', ''),
            'architecture_pattern': data.get('architecture_pattern', 'MVC'),
            'phase': 'discovery'
        }

        # Validate project data
        if not validate_project_data(project_data):
            raise ValueError("Invalid project data")

        # Create project
        project_id = self.db.projects.create(project_data)

        # Create default modules if specified
        default_modules = data.get('default_modules', [])
        for module_data in default_modules:
            module_data['project_id'] = project_id
            self.db.modules.create(module_data)

        # Initialize project tracking
        self._initialize_project_tracking(project_id)

        return {
            'project_id': project_id,
            'status': 'created',
            'modules_created': len(default_modules)
        }

    def _initialize_project_tracking(self, project_id: str):
        """Initialize tracking systems for new project"""
        # Create initial progress metrics
        metrics = {
            'discovery_progress': 0.0,
            'analysis_progress': 0.0,
            'design_progress': 0.0,
            'implementation_progress': 0.0,
            'overall_progress': 0.0
        }

        # Initialize risk tracking
        risks = []

        # Set up basic project structure
        self.events.emit('project_created', {
            'project_id': project_id,
            'timestamp': datetime.now().isoformat()
        })

    def _update_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update project information"""
        project_id = data.get('project_id')
        updates = data.get('updates', {})

        if not project_id:
            raise ValueError("Project ID is required")

        # Get existing project
        project = self.db.projects.get_by_id(project_id)
        if not project:
            raise ValueError("Project not found")

        # Update allowed fields
        allowed_fields = [
            'name', 'description', 'goals', 'requirements', 'tech_stack',
            'constraints', 'team_structure', 'language_preferences',
            'deployment_target', 'code_style', 'architecture_pattern', 'phase'
        ]

        updated_fields = []
        for field in allowed_fields:
            if field in updates:
                setattr(project, field, updates[field])
                updated_fields.append(field)

        # Update timestamp
        project.updated_at = datetime.now()

        # Save changes
        self.db.projects.update(project_id, asdict(project))

        # Emit update event
        self.events.emit('project_updated', {
            'project_id': project_id,
            'updated_fields': updated_fields,
            'timestamp': datetime.now().isoformat()
        })

        return {
            'project_id': project_id,
            'updated_fields': updated_fields,
            'status': 'updated'
        }

    def _archive_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Archive project and all related data"""
        project_id = data.get('project_id')
        archive_reason = data.get('reason', 'User requested')

        if not project_id:
            raise ValueError("Project ID is required")

        # Get project
        project = self.db.projects.get_by_id(project_id)
        if not project:
            raise ValueError("Project not found")

        # Archive project
        project.is_archived = True
        project.archived_at = datetime.now()
        project.updated_at = datetime.now()

        # Save changes
        self.db.projects.update(project_id, asdict(project))

        # Archive related modules and tasks
        modules = self.db.modules.get_by_project_id(project_id)
        tasks = self.db.tasks.get_by_project_id(project_id)

        for module in modules:
            module.status = 'archived'
            self.db.modules.update(module.module_id, asdict(module))

        for task in tasks:
            task.status = 'archived'
            self.db.tasks.update(task.task_id, asdict(task))

        # Emit archive event
        self.events.emit('project_archived', {
            'project_id': project_id,
            'reason': archive_reason,
            'timestamp': datetime.now().isoformat()
        })

        return {
            'project_id': project_id,
            'status': 'archived',
            'modules_archived': len(modules),
            'tasks_archived': len(tasks)
        }

    def _manage_modules(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive module management"""
        action = data.get('action')  # create, update, delete, assign
        project_id = data.get('project_id')

        if action == 'create':
            return self._create_module(data)
        elif action == 'update':
            return self._update_module(data)
        elif action == 'delete':
            return self._delete_module(data)
        elif action == 'assign':
            return self._assign_module_tasks(data)
        elif action == 'progress':
            return self._update_module_progress(data)
        else:
            raise ValueError(f"Unknown module action: {action}")

    def _create_module(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new module within project"""
        module_data = {
            'project_id': data.get('project_id'),
            'name': data.get('name'),
            'description': data.get('description'),
            'module_type': data.get('module_type', 'feature'),
            'phase': data.get('phase', 'not_started'),
            'dependencies': data.get('dependencies', []),
            'assigned_roles': data.get('assigned_roles', []),
            'estimated_hours': data.get('estimated_hours', 0),
            'priority': data.get('priority', 'medium'),
            'status': data.get('status', 'not_started')
        }

        module_id = self.db.modules.create(module_data)

        # Create associated tasks if provided
        tasks = data.get('tasks', [])
        created_tasks = []
        for task_data in tasks:
            task_data['module_id'] = module_id
            task_data['project_id'] = data.get('project_id')
            task_id = self.db.tasks.create(task_data)
            created_tasks.append(task_id)

        return {
            'module_id': module_id,
            'tasks_created': len(created_tasks),
            'task_ids': created_tasks
        }

    def _update_module(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing module"""
        module_id = data.get('module_id')
        updates = data.get('updates', {})

        if not module_id:
            raise ValueError("Module ID is required")

        # Get existing module
        module = self.db.modules.get_by_id(module_id)
        if not module:
            raise ValueError("Module not found")

        # Update allowed fields
        allowed_fields = [
            'name', 'description', 'module_type', 'phase', 'dependencies',
            'assigned_roles', 'estimated_hours', 'actual_hours', 'priority', 'status'
        ]

        updated_fields = []
        for field in allowed_fields:
            if field in updates:
                setattr(module, field, updates[field])
                updated_fields.append(field)

        # Update timestamp
        module.updated_at = datetime.now()

        # Save changes
        self.db.modules.update(module_id, asdict(module))

        return {
            'module_id': module_id,
            'updated_fields': updated_fields,
            'status': 'updated'
        }

    def _delete_module(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Delete module and associated tasks"""
        module_id = data.get('module_id')

        if not module_id:
            raise ValueError("Module ID is required")

        # Get module
        module = self.db.modules.get_by_id(module_id)
        if not module:
            raise ValueError("Module not found")

        # Get and delete associated tasks
        tasks = self.db.tasks.get_by_module_id(module_id)
        for task in tasks:
            self.db.tasks.delete(task.task_id)

        # Delete module
        self.db.modules.delete(module_id)

        return {
            'module_id': module_id,
            'tasks_deleted': len(tasks),
            'status': 'deleted'
        }

    def _assign_module_tasks(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assign tasks to module members"""
        module_id = data.get('module_id')
        assignments = data.get('assignments', [])  # [{'task_id': str, 'user_id': str, 'role': str}]

        if not module_id:
            raise ValueError("Module ID is required")

        # Get module
        module = self.db.modules.get_by_id(module_id)
        if not module:
            raise ValueError("Module not found")

        assigned_tasks = []
        for assignment in assignments:
            task_id = assignment.get('task_id')
            user_id = assignment.get('user_id')
            role = assignment.get('role', 'contributor')

            # Get task
            task = self.db.tasks.get_by_id(task_id)
            if task and task.module_id == module_id:
                task.assigned_to = user_id
                task.assigned_role = role
                task.assigned_at = datetime.now()
                task.status = 'assigned'

                # Save task
                self.db.tasks.update(task_id, asdict(task))
                assigned_tasks.append(task_id)

        return {
            'module_id': module_id,
            'tasks_assigned': len(assigned_tasks),
            'assigned_task_ids': assigned_tasks
        }

    def _update_module_progress(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update module progress based on task completion"""
        module_id = data.get('module_id')
        progress_updates = data.get('progress_updates', {})

        if not module_id:
            raise ValueError("Module ID is required")

        # Get module
        module = self.db.modules.get_by_id(module_id)
        if not module:
            raise ValueError("Module not found")

        # Update progress fields
        if 'progress_percentage' in progress_updates:
            module.progress_percentage = progress_updates['progress_percentage']

        if 'actual_hours' in progress_updates:
            module.actual_hours = progress_updates['actual_hours']

        if 'status' in progress_updates:
            module.status = progress_updates['status']

        # Calculate progress from tasks if not provided
        if 'progress_percentage' not in progress_updates:
            module.progress_percentage = self._calculate_module_progress(module_id)

        # Update timestamp
        module.updated_at = datetime.now()

        # Save changes
        self.db.modules.update(module_id, asdict(module))

        return {
            'module_id': module_id,
            'progress_percentage': module.progress_percentage,
            'status': module.status
        }

    def _calculate_module_progress(self, module_id: str) -> float:
        """Calculate module progress based on task completion"""
        tasks = self.db.tasks.get_by_module_id(module_id)

        if not tasks:
            return 0.0

        completed_tasks = len([task for task in tasks if task.status == 'completed'])
        total_tasks = len(tasks)

        return (completed_tasks / total_tasks) * 100.0

    def _assign_tasks(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Assign individual tasks to team members"""
        assignments = data.get('assignments', [])  # [{'task_id': str, 'user_id': str, 'role': str}]

        assigned_tasks = []
        for assignment in assignments:
            task_id = assignment.get('task_id')
            user_id = assignment.get('user_id')
            role = assignment.get('role', 'contributor')

            # Get task
            task = self.db.tasks.get_by_id(task_id)
            if not task:
                continue

            # Update assignment
            task.assigned_to = user_id
            task.assigned_role = role
            task.assigned_at = datetime.now()
            task.status = 'assigned'

            # Save task
            self.db.tasks.update(task_id, asdict(task))
            assigned_tasks.append(task_id)

        return {
            'tasks_assigned': len(assigned_tasks),
            'assigned_task_ids': assigned_tasks
        }

    def _track_progress(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Track and analyze project progress"""
        project_id = data.get('project_id')
        level = data.get('level', 'all')  # all, project, module, task

        if level == 'all':
            return self._get_comprehensive_progress(project_id)
        elif level == 'project':
            return self._get_project_progress(project_id)
        elif level == 'modules':
            return self._get_modules_progress(project_id)
        else:
            return self._get_task_progress(project_id)

    def _get_comprehensive_progress(self, project_id: str) -> Dict[str, Any]:
        """Get comprehensive progress across all levels"""
        project = self.db.projects.get_by_id(project_id)
        modules = self.db.modules.get_by_project_id(project_id)
        tasks = self.db.tasks.get_by_project_id(project_id)

        # Calculate progress metrics
        progress = {
            'project_phase': project.phase if project else 'unknown',
            'overall_progress': 0.0,
            'modules_total': len(modules),
            'modules_completed': 0,
            'tasks_total': len(tasks),
            'tasks_completed': 0,
            'estimated_hours': 0,
            'actual_hours': 0,
            'completion_percentage': 0.0
        }

        # Calculate module progress
        for module in modules:
            if module.status == 'completed':
                progress['modules_completed'] += 1
            progress['estimated_hours'] += module.estimated_hours
            progress['actual_hours'] += module.actual_hours

        # Calculate task progress
        for task in tasks:
            if task.status == 'completed':
                progress['tasks_completed'] += 1

        # Overall completion
        if progress['tasks_total'] > 0:
            progress['completion_percentage'] = (progress['tasks_completed'] / progress['tasks_total']) * 100

        return progress

    def _get_project_progress(self, project_id: str) -> Dict[str, Any]:
        """Get project-level progress"""
        project = self.db.projects.get_by_id(project_id)
        if not project:
            raise ValueError("Project not found")

        return {
            'project_id': project_id,
            'name': project.name,
            'phase': project.phase,
            'created_at': project.created_at.isoformat(),
            'updated_at': project.updated_at.isoformat(),
            'requirements_count': len(project.requirements),
            'tech_stack_count': len(project.tech_stack),
            'constraints_count': len(project.constraints)
        }

    def _get_modules_progress(self, project_id: str) -> Dict[str, Any]:
        """Get progress for all modules in project"""
        modules = self.db.modules.get_by_project_id(project_id)

        module_progress = []
        for module in modules:
            module_progress.append({
                'module_id': module.module_id,
                'name': module.name,
                'type': module.module_type,
                'status': module.status,
                'progress_percentage': module.progress_percentage,
                'estimated_hours': module.estimated_hours,
                'actual_hours': module.actual_hours,
                'priority': module.priority
            })

        return {
            'project_id': project_id,
            'total_modules': len(modules),
            'modules': module_progress
        }

    def _get_task_progress(self, project_id: str) -> Dict[str, Any]:
        """Get progress for all tasks in project"""
        tasks = self.db.tasks.get_by_project_id(project_id)

        task_progress = []
        for task in tasks:
            task_progress.append({
                'task_id': task.task_id,
                'module_id': task.module_id,
                'title': task.title,
                'status': task.status,
                'priority': task.priority,
                'assigned_to': task.assigned_to,
                'assigned_role': getattr(task, 'assigned_role', None),
                'estimated_hours': task.estimated_hours,
                'actual_hours': task.actual_hours
            })

        return {
            'project_id': project_id,
            'total_tasks': len(tasks),
            'tasks': task_progress
        }

    def _manage_collaborators(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Manage project collaborators and permissions"""
        action = data.get('action')  # add, remove, update_role, list
        project_id = data.get('project_id')

        if action == 'add':
            return self._add_collaborator(project_id, data)
        elif action == 'remove':
            return self._remove_collaborator(project_id, data.get('user_id'))
        elif action == 'update_role':
            return self._update_collaborator_role(project_id, data)
        elif action == 'list':
            return self._list_collaborators(project_id)
        else:
            raise ValueError(f"Unknown collaborator action: {action}")

    def _add_collaborator(self, project_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Add collaborator to project"""
        user_id = data.get('user_id')
        role = data.get('role', 'contributor')
        permissions = data.get('permissions', [])

        # Get project
        project = self.db.projects.get_by_id(project_id)
        if not project:
            raise ValueError("Project not found")

        # Check if user already exists as collaborator
        existing_collaborator = None
        for collaborator in project.collaborators:
            if collaborator.get('user_id') == user_id:
                existing_collaborator = collaborator
                break

        if existing_collaborator:
            return {'error': 'User is already a collaborator'}

        # Add collaborator
        collaborator = {
            'user_id': user_id,
            'role': role,
            'permissions': permissions,
            'added_at': datetime.now().isoformat()
        }

        project.collaborators.append(collaborator)
        project.updated_at = datetime.now()
        self.db.projects.update(project_id, asdict(project))

        return {
            'message': 'Collaborator added successfully',
            'collaborator_id': user_id,
            'role': role
        }

    def _remove_collaborator(self, project_id: str, user_id: str) -> Dict[str, Any]:
        """Remove collaborator from project"""
        # Get project
        project = self.db.projects.get_by_id(project_id)
        if not project:
            raise ValueError("Project not found")

        # Remove collaborator
        original_count = len(project.collaborators)
        project.collaborators = [
            collab for collab in project.collaborators
            if collab.get('user_id') != user_id
        ]

        if len(project.collaborators) == original_count:
            return {'error': 'Collaborator not found'}

        project.updated_at = datetime.now()
        self.db.projects.update(project_id, asdict(project))

        return {
            'message': 'Collaborator removed successfully',
            'removed_user_id': user_id
        }

    def _update_collaborator_role(self, project_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Update collaborator role and permissions"""
        user_id = data.get('user_id')
        new_role = data.get('role')
        new_permissions = data.get('permissions', [])

        # Get project
        project = self.db.projects.get_by_id(project_id)
        if not project:
            raise ValueError("Project not found")

        # Find and update collaborator
        collaborator_found = False
        for collaborator in project.collaborators:
            if collaborator.get('user_id') == user_id:
                collaborator['role'] = new_role
                collaborator['permissions'] = new_permissions
                collaborator['updated_at'] = datetime.now().isoformat()
                collaborator_found = True
                break

        if not collaborator_found:
            return {'error': 'Collaborator not found'}

        project.updated_at = datetime.now()
        self.db.projects.update(project_id, asdict(project))

        return {
            'message': 'Collaborator role updated successfully',
            'user_id': user_id,
            'new_role': new_role
        }

    def _list_collaborators(self, project_id: str) -> Dict[str, Any]:
        """List all project collaborators"""
        project = self.db.projects.get_by_id(project_id)
        if not project:
            raise ValueError("Project not found")

        return {
            'project_id': project_id,
            'total_collaborators': len(project.collaborators),
            'collaborators': project.collaborators
        }

    def _generate_reports(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate various project reports"""
        project_id = data.get('project_id')
        report_type = data.get('report_type', 'progress')
        format_type = data.get('format', 'json')

        if report_type == 'progress':
            report_data = self._generate_progress_report(project_id)
        elif report_type == 'team':
            report_data = self._generate_team_report(project_id)
        elif report_type == 'risk':
            report_data = self._generate_risk_report(project_id)
        elif report_type == 'summary':
            report_data = self._generate_summary_report(project_id)
        else:
            raise ValueError(f"Unknown report type: {report_type}")

        return {
            'report_type': report_type,
            'format': format_type,
            'data': report_data,
            'generated_at': datetime.now().isoformat()
        }

    def _generate_progress_report(self, project_id: str) -> Dict[str, Any]:
        """Generate detailed progress report"""
        progress = self._get_comprehensive_progress(project_id)
        project = self.db.projects.get_by_id(project_id)

        return {
            'project_name': project.name if project else 'Unknown',
            'current_phase': project.phase if project else 'unknown',
            'progress_metrics': progress,
            'timeline': {
                'created_at': project.created_at.isoformat() if project else None,
                'last_updated': project.updated_at.isoformat() if project else None,
                'estimated_completion': self._estimate_completion_date(project_id)
            },
            'recommendations': self._generate_progress_recommendations(progress)
        }

    def _generate_team_report(self, project_id: str) -> Dict[str, Any]:
        """Generate team performance report"""
        project = self.db.projects.get_by_id(project_id)
        tasks = self.db.tasks.get_by_project_id(project_id)

        # Analyze team performance
        team_metrics = {}
        for task in tasks:
            if task.assigned_to:
                if task.assigned_to not in team_metrics:
                    team_metrics[task.assigned_to] = {
                        'total_tasks': 0,
                        'completed_tasks': 0,
                        'estimated_hours': 0,
                        'actual_hours': 0
                    }

                team_metrics[task.assigned_to]['total_tasks'] += 1
                team_metrics[task.assigned_to]['estimated_hours'] += task.estimated_hours
                team_metrics[task.assigned_to]['actual_hours'] += task.actual_hours

                if task.status == 'completed':
                    team_metrics[task.assigned_to]['completed_tasks'] += 1

        return {
            'project_name': project.name if project else 'Unknown',
            'total_collaborators': len(project.collaborators) if project else 0,
            'team_performance': team_metrics,
            'summary': {
                'total_assigned_tasks': len([t for t in tasks if t.assigned_to]),
                'unassigned_tasks': len([t for t in tasks if not t.assigned_to])
            }
        }

    def _generate_risk_report(self, project_id: str) -> Dict[str, Any]:
        """Generate risk assessment report"""
        progress = self._get_comprehensive_progress(project_id)
        project = self.db.projects.get_by_id(project_id)

        risks = []

        # Timeline risks
        if progress['completion_percentage'] < 25 and project:
            days_since_creation = (datetime.now() - project.created_at).days
            if days_since_creation > 30:
                risks.append({
                    'type': 'timeline',
                    'severity': 'medium',
                    'description': 'Project progress slower than expected',
                    'recommendation': 'Review scope and resource allocation'
                })

        # Resource risks
        if progress['actual_hours'] > progress['estimated_hours'] * 1.3:
            risks.append({
                'type': 'resource',
                'severity': 'high',
                'description': 'Actual hours significantly exceed estimates',
                'recommendation': 'Re-evaluate time estimates and scope'
            })

        # Scope risks
        if project and len(project.requirements) > 20:
            risks.append({
                'type': 'scope',
                'severity': 'medium',
                'description': 'High number of requirements may increase complexity',
                'recommendation': 'Consider phased delivery approach'
            })

        return {
            'project_name': project.name if project else 'Unknown',
            'risk_count': len(risks),
            'risks': risks,
            'overall_risk_level': self._calculate_overall_risk_level(risks)
        }

    def _generate_summary_report(self, project_id: str) -> Dict[str, Any]:
        """Generate executive summary report"""
        project = self.db.projects.get_by_id(project_id)
        progress = self._get_comprehensive_progress(project_id)

        return {
            'project_overview': {
                'name': project.name if project else 'Unknown',
                'phase': project.phase if project else 'unknown',
                'created': project.created_at.isoformat() if project else None,
                'last_updated': project.updated_at.isoformat() if project else None
            },
            'progress_summary': {
                'completion_percentage': progress['completion_percentage'],
                'modules_completed': f"{progress['modules_completed']}/{progress['modules_total']}",
                'tasks_completed': f"{progress['tasks_completed']}/{progress['tasks_total']}"
            },
            'resource_utilization': {
                'estimated_hours': progress['estimated_hours'],
                'actual_hours': progress['actual_hours'],
                'efficiency_ratio': (progress['estimated_hours'] / progress['actual_hours']) if progress[
                                                                                                    'actual_hours'] > 0 else 1.0
            },
            'next_steps': self._get_next_steps(project),
            'key_metrics': {
                'requirements_count': len(project.requirements) if project else 0,
                'tech_stack_size': len(project.tech_stack) if project else 0,
                'team_size': len(project.collaborators) if project else 0
            }
        }

    def _calculate_overall_risk_level(self, risks: List[Dict[str, Any]]) -> str:
        """Calculate overall risk level from individual risks"""
        if not risks:
            return 'low'

        high_risks = len([r for r in risks if r.get('severity') == 'high'])
        medium_risks = len([r for r in risks if r.get('severity') == 'medium'])

        if high_risks > 0:
            return 'high'
        elif medium_risks > 2:
            return 'medium'
        else:
            return 'low'

    def _estimate_completion_date(self, project_id: str) -> str:
        """Estimate project completion date"""
        progress = self._get_comprehensive_progress(project_id)
        project = self.db.projects.get_by_id(project_id)

        if not project or progress['completion_percentage'] <= 0:
            return "Unable to estimate"

        # Simple linear projection
        days_since_creation = (datetime.now() - project.created_at).days
        if days_since_creation == 0:
            return "Unable to estimate"

        total_days_estimated = days_since_creation / (progress['completion_percentage'] / 100)
        remaining_days = total_days_estimated - days_since_creation

        completion_date = datetime.now() + timedelta(days=remaining_days)
        return completion_date.isoformat()

    def _generate_progress_recommendations(self, progress: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on progress"""
        recommendations = []

        if progress['completion_percentage'] < 25:
            recommendations.append("Consider breaking down large tasks into smaller, manageable pieces")

        if progress['actual_hours'] > progress['estimated_hours'] * 1.2:
            recommendations.append("Review time estimates and adjust scope if necessary")

        if progress['modules_completed'] == 0 and progress['modules_total'] > 0:
            recommendations.append("Focus on completing at least one module to build momentum")

        if progress['tasks_total'] > 50:
            recommendations.append("Consider using task management tools for better organization")

        return recommendations

    def _get_next_steps(self, project: ProjectContext) -> List[str]:
        """Generate next steps recommendations"""
        if not project:
            return ["Project not found"]

        next_steps = []

        if project.phase == 'discovery':
            next_steps.append("Complete requirements gathering")
            next_steps.append("Define project scope and constraints")

        elif project.phase == 'analysis':
            next_steps.append("Finalize technical specifications")
            next_steps.append("Validate architecture decisions")

        elif project.phase == 'design':
            next_steps.append("Create detailed implementation plan")
            next_steps.append("Set up development environment")

        elif project.phase == 'implementation':
            next_steps.append("Begin code development")
            next_steps.append("Set up testing processes")

        return next_steps

    def _risk_assessment(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Perform comprehensive risk assessment"""
        project_id = data.get('project_id')
        assessment_type = data.get('type', 'full')  # full, timeline, resource, technical

        if assessment_type == 'full':
            return self._generate_risk_report(project_id)
        else:
            # Focused risk assessment
            return self._assess_specific_risks(project_id, assessment_type)

    def _assess_specific_risks(self, project_id: str, risk_type: str) -> Dict[str, Any]:
        """Assess specific type of risks"""
        project = self.db.projects.get_by_id(project_id)
        progress = self._get_comprehensive_progress(project_id)

        risks = []

        if risk_type == 'timeline':
            risks = self._assess_timeline_risks(project, progress)
        elif risk_type == 'resource':
            risks = self._assess_resource_risks(project, progress)
        elif risk_type == 'technical':
            risks = self._assess_technical_risks(project)

        return {
            'risk_type': risk_type,
            'project_id': project_id,
            'risks': risks,
            'risk_level': self._calculate_overall_risk_level(risks)
        }

    def _assess_timeline_risks(self, project: ProjectContext, progress: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Assess timeline-related risks"""
        risks = []

        if project:
            days_since_creation = (datetime.now() - project.created_at).days
            expected_progress = min(days_since_creation * 2, 50)  # Simple heuristic

            if progress['completion_percentage'] < expected_progress:
                risks.append({
                    'type': 'timeline',
                    'severity': 'medium',
                    'description': f"Progress ({progress['completion_percentage']}%) below expected ({expected_progress}%)",
                    'recommendation': 'Review project timeline and resource allocation'
                })

        return risks

    def _assess_resource_risks(self, project: ProjectContext, progress: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Assess resource-related risks"""
        risks = []

        # Hour overrun risk
        if progress['actual_hours'] > progress['estimated_hours'] * 1.2 and progress['estimated_hours'] > 0:
            risks.append({
                'type': 'resource',
                'severity': 'high',
                'description': 'Actual hours exceed estimates by more than 20%',
                'recommendation': 'Re-evaluate task complexity and time estimates'
            })

        # Team size risk
        if project and len(project.collaborators) > 10:
            risks.append({
                'type': 'resource',
                'severity': 'medium',
                'description': 'Large team size may create coordination challenges',
                'recommendation': 'Consider team structure and communication protocols'
            })

        return risks

    def _assess_technical_risks(self, project: ProjectContext) -> List[Dict[str, Any]]:
        """Assess technical risks"""
        risks = []

        if project:
            # Technology complexity risk
            if len(project.tech_stack) > 8:
                risks.append({
                    'type': 'technical',
                    'severity': 'medium',
                    'description': 'Complex technology stack may increase development time',
                    'recommendation': 'Validate technology choices and consider simplification'
                })

            # Requirements complexity risk
            if len(project.requirements) > 25:
                risks.append({
                    'type': 'technical',
                    'severity': 'medium',
                    'description': 'High number of requirements increases implementation complexity',
                    'recommendation': 'Prioritize requirements and consider phased approach'
                })

        return risks

    def _resource_allocation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize resource allocation across modules and tasks"""
        project_id = data.get('project_id')
        optimization_type = data.get('type', 'balanced')  # balanced, time_focused, quality_focused

        modules = self.db.modules.get_by_project_id(project_id)
        tasks = self.db.tasks.get_by_project_id(project_id)

        allocation_plan = {
            'project_id': project_id,
            'optimization_type': optimization_type,
            'recommendations': [],
            'module_allocations': [],
            'task_assignments': []
        }

        # Analyze current allocation
        for module in modules:
            module_tasks = [t for t in tasks if t.module_id == module.module_id]
            allocation_plan['module_allocations'].append({
                'module_id': module.module_id,
                'name': module.name,
                'priority': module.priority,
                'estimated_hours': module.estimated_hours,
                'task_count': len(module_tasks),
                'assigned_tasks': len([t for t in module_tasks if t.assigned_to]),
                'completion_percentage': module.progress_percentage
            })

        # Generate allocation recommendations
        allocation_plan['recommendations'] = self._generate_allocation_recommendations(modules, tasks)

        return allocation_plan

    def _generate_allocation_recommendations(self, modules: List[ModuleContext], tasks: List[TaskContext]) -> List[str]:
        """Generate resource allocation recommendations"""
        recommendations = []

        # High priority modules with low allocation
        high_priority_modules = [m for m in modules if m.priority == 'high']
        for module in high_priority_modules:
            module_tasks = [t for t in tasks if t.module_id == module.module_id]
            assigned_tasks = len([t for t in module_tasks if t.assigned_to])

            if len(module_tasks) > 0 and assigned_tasks / len(module_tasks) < 0.5:
                recommendations.append(f"Increase resource allocation to high-priority module: {module.name}")

        # Overallocated team members
        assignee_workload = {}
        for task in tasks:
            if task.assigned_to and task.status not in ['completed', 'cancelled']:
                if task.assigned_to not in assignee_workload:
                    assignee_workload[task.assigned_to] = 0
                assignee_workload[task.assigned_to] += task.estimated_hours

        for assignee, hours in assignee_workload.items():
            if hours > 40:  # Assuming 40 hours per week as threshold
                recommendations.append(f"Consider redistributing tasks from overloaded team member: {assignee}")

        return recommendations

    def _timeline_management(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Manage project timeline and milestones"""
        project_id = data.get('project_id')
        action = data.get('action')  # analyze_delays, overview

        if action == 'analyze_delays':
            return self._analyze_project_delays(project_id)
        else:
            return self._get_timeline_overview(project_id)

    def _analyze_project_delays(self, project_id: str) -> Dict[str, Any]:
        """Analyze project delays and bottlenecks"""
        project = self.db.projects.get_by_id(project_id)
        progress = self._get_comprehensive_progress(project_id)

        if not project:
            raise ValueError("Project not found")

        days_since_creation = (datetime.now() - project.created_at).days
        expected_progress = min(days_since_creation * 2, 50)  # Simple heuristic

        delays = {
            'project_id': project_id,
            'days_since_creation': days_since_creation,
            'current_progress': progress['completion_percentage'],
            'expected_progress': expected_progress,
            'is_delayed': progress['completion_percentage'] < expected_progress,
            'delay_analysis': []
        }

        if delays['is_delayed']:
            delays['delay_analysis'].append({
                'type': 'timeline',
                'severity': 'medium' if progress['completion_percentage'] < expected_progress * 0.7 else 'low',
                'description': f"Project progress is {expected_progress - progress['completion_percentage']:.1f}% behind schedule"
            })

        return delays

    def _get_timeline_overview(self, project_id: str) -> Dict[str, Any]:
        """Get comprehensive timeline overview"""
        project = self.db.projects.get_by_id(project_id)
        modules = self.db.modules.get_by_project_id(project_id)
        progress = self._get_comprehensive_progress(project_id)

        timeline = {
            'project_id': project_id,
            'start_date': project.created_at.isoformat() if project else None,
            'estimated_completion': self._estimate_completion_date(project_id),
            'current_phase': project.phase if project else 'unknown',
            'progress_percentage': progress['completion_percentage'],
            'modules_timeline': []
        }

        for module in modules:
            timeline['modules_timeline'].append({
                'module_id': module.module_id,
                'name': module.name,
                'status': module.status,
                'progress_percentage': module.progress_percentage,
                'estimated_hours': module.estimated_hours,
                'actual_hours': module.actual_hours
            })

        return timeline
