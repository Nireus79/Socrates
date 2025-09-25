"""
Socratic RAG Enhanced - Services Agent
Handles Git integration, export services, IDE integration, and deployment automation
"""

import json
import logging
import os
import subprocess
import tempfile
import time
import zipfile
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from src.agents.base import BaseAgent
from src.models import ProjectContext, GeneratedCodebase


class ServicesAgent(BaseAgent):
    """
    Consolidated external services agent

    Handles: Git integration, Export services, Summary generation,
             IDE integration, Deployment automation
    """

    def __init__(self):
        super().__init__("services_agent", "Services Agent")

    def get_capabilities(self) -> List[str]:
        return [
            "git_operations", "export_project", "generate_summary", "ide_integration",
            "deploy_application", "backup_project", "sync_files", "create_documentation"
        ]

    def _git_operations(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Git operations"""
        operation = data.get('operation')  # init, commit, push, pull, branch
        project_id = data.get('project_id')

        if operation == 'init':
            return self._git_init(project_id, data)
        elif operation == 'commit':
            return self._git_commit(project_id, data)
        elif operation == 'push':
            return self._git_push(project_id, data)
        elif operation == 'pull':
            return self._git_pull(project_id, data)
        elif operation == 'branch':
            return self._git_branch(project_id, data)
        elif operation == 'status':
            return self._git_status(project_id, data)
        else:
            raise ValueError(f"Unknown git operation: {operation}")

    def _git_init(self, project_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize Git repository for project"""
        repo_path = data.get('repo_path')
        remote_url = data.get('remote_url')

        if not repo_path:
            raise ValueError("repo_path is required")

        try:
            # Initialize git repository
            result = subprocess.run(['git', 'init'], cwd=repo_path, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(result.stderr)

            # Add remote if provided
            if remote_url:
                result = subprocess.run(['git', 'remote', 'add', 'origin', remote_url],
                                        cwd=repo_path, capture_output=True, text=True)
                if result.returncode != 0:
                    self.logger.warning(f"Failed to add remote: {result.stderr}")

            # Create initial .gitignore
            gitignore_content = self._generate_gitignore(repo_path)
            gitignore_path = Path(repo_path) / '.gitignore'
            gitignore_path.write_text(gitignore_content)

            return {
                'success': True,
                'message': 'Git repository initialized',
                'repo_path': repo_path,
                'remote_url': remote_url,
                'gitignore_created': True
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _generate_gitignore(self, repo_path: str) -> str:
        """Generate appropriate .gitignore content based on project type"""
        gitignore_content = """
# General
.DS_Store
.env
.venv/
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
logs/
*.log

# Dependencies
node_modules/
package-lock.json

# Build outputs
dist/
build/
*.egg-info/

# Testing
.coverage
.pytest_cache/
coverage/

# Database
*.db
*.sqlite
*.sqlite3

# Temporary files
*.tmp
*.temp
.cache/
        """.strip()

        return gitignore_content

    def _git_commit(self, project_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Commit changes to Git repository"""
        repo_path = data.get('repo_path')
        message = data.get('message', f'Automated commit for project {project_id}')
        add_all = data.get('add_all', True)

        if not repo_path:
            raise ValueError("repo_path is required")

        try:
            # Add files
            if add_all:
                result = subprocess.run(['git', 'add', '.'], cwd=repo_path, capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception(f"Git add failed: {result.stderr}")
            else:
                files_to_add = data.get('files', [])
                for file_path in files_to_add:
                    result = subprocess.run(['git', 'add', file_path], cwd=repo_path, capture_output=True, text=True)
                    if result.returncode != 0:
                        self.logger.warning(f"Failed to add {file_path}: {result.stderr}")

            # Check if there are changes to commit
            status_result = subprocess.run(['git', 'status', '--porcelain'],
                                           cwd=repo_path, capture_output=True, text=True)

            if not status_result.stdout.strip():
                return {
                    'success': True,
                    'message': 'No changes to commit',
                    'files_added': 0
                }

            # Commit changes
            result = subprocess.run(['git', 'commit', '-m', message],
                                    cwd=repo_path, capture_output=True, text=True)

            if result.returncode != 0:
                raise Exception(f"Git commit failed: {result.stderr}")

            return {
                'success': True,
                'message': 'Changes committed successfully',
                'commit_message': message,
                'commit_output': result.stdout
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _git_push(self, project_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Push changes to remote repository"""
        repo_path = data.get('repo_path')
        remote = data.get('remote', 'origin')
        branch = data.get('branch', 'main')

        if not repo_path:
            raise ValueError("repo_path is required")

        try:
            # Push to remote
            result = subprocess.run(['git', 'push', remote, branch],
                                    cwd=repo_path, capture_output=True, text=True)

            if result.returncode != 0:
                # Try to push with upstream if first push
                if 'upstream' in result.stderr:
                    result = subprocess.run(['git', 'push', '--set-upstream', remote, branch],
                                            cwd=repo_path, capture_output=True, text=True)

                if result.returncode != 0:
                    raise Exception(f"Git push failed: {result.stderr}")

            return {
                'success': True,
                'message': f'Pushed to {remote}/{branch}',
                'remote': remote,
                'branch': branch,
                'output': result.stdout
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _git_pull(self, project_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Pull changes from remote repository"""
        repo_path = data.get('repo_path')
        remote = data.get('remote', 'origin')
        branch = data.get('branch', 'main')

        if not repo_path:
            raise ValueError("repo_path is required")

        try:
            result = subprocess.run(['git', 'pull', remote, branch],
                                    cwd=repo_path, capture_output=True, text=True)

            if result.returncode != 0:
                raise Exception(f"Git pull failed: {result.stderr}")

            return {
                'success': True,
                'message': f'Pulled from {remote}/{branch}',
                'changes': 'up-to-date' if 'up to date' in result.stdout else 'updated',
                'output': result.stdout
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _git_branch(self, project_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Git branch operations"""
        repo_path = data.get('repo_path')
        action = data.get('action', 'list')  # list, create, switch, delete
        branch_name = data.get('branch_name')

        if not repo_path:
            raise ValueError("repo_path is required")

        try:
            if action == 'list':
                result = subprocess.run(['git', 'branch', '-a'],
                                        cwd=repo_path, capture_output=True, text=True)
                branches = [line.strip().replace('* ', '').replace('remotes/', '')
                            for line in result.stdout.split('\n') if line.strip()]

                return {
                    'success': True,
                    'branches': branches,
                    'current_branch': self._get_current_branch(repo_path)
                }

            elif action == 'create':
                if not branch_name:
                    raise ValueError("branch_name is required for create action")

                result = subprocess.run(['git', 'checkout', '-b', branch_name],
                                        cwd=repo_path, capture_output=True, text=True)

                if result.returncode != 0:
                    raise Exception(f"Branch creation failed: {result.stderr}")

                return {
                    'success': True,
                    'message': f'Created and switched to branch {branch_name}',
                    'branch': branch_name
                }

            elif action == 'switch':
                if not branch_name:
                    raise ValueError("branch_name is required for switch action")

                result = subprocess.run(['git', 'checkout', branch_name],
                                        cwd=repo_path, capture_output=True, text=True)

                if result.returncode != 0:
                    raise Exception(f"Branch switch failed: {result.stderr}")

                return {
                    'success': True,
                    'message': f'Switched to branch {branch_name}',
                    'branch': branch_name
                }

            else:
                raise ValueError(f"Unknown branch action: {action}")

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _get_current_branch(self, repo_path: str) -> str:
        """Get current Git branch"""
        try:
            result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'],
                                    cwd=repo_path, capture_output=True, text=True)
            return result.stdout.strip()
        except:
            return 'unknown'

    def _git_status(self, project_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Get Git repository status"""
        repo_path = data.get('repo_path')

        if not repo_path:
            raise ValueError("repo_path is required")

        try:
            # Get status
            result = subprocess.run(['git', 'status', '--porcelain'],
                                    cwd=repo_path, capture_output=True, text=True)

            # Parse status output
            status_lines = result.stdout.strip().split('\n') if result.stdout.strip() else []

            status = {
                'clean': len(status_lines) == 0,
                'modified_files': [],
                'untracked_files': [],
                'staged_files': []
            }

            for line in status_lines:
                if len(line) < 3:
                    continue

                status_code = line[:2]
                file_path = line[3:]

                if status_code.startswith('M'):
                    status['modified_files'].append(file_path)
                elif status_code.startswith('??'):
                    status['untracked_files'].append(file_path)
                elif status_code.startswith('A') or status_code.endswith('M'):
                    status['staged_files'].append(file_path)

            status['current_branch'] = self._get_current_branch(repo_path)

            return {
                'success': True,
                'status': status
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _export_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Export project in various formats"""
        project_id = data.get('project_id')
        export_format = data.get('format', 'zip')  # zip, pdf, json, docker
        include_code = data.get('include_code', True)
        include_docs = data.get('include_docs', True)

        # Get project data
        project = self.db.projects.get_by_id(project_id)
        if not project:
            raise ValueError("Project not found")

        if export_format == 'zip':
            return self._export_as_zip(project, include_code, include_docs)
        elif export_format == 'pdf':
            return self._export_as_pdf(project)
        elif export_format == 'json':
            return self._export_as_json(project, include_code)
        elif export_format == 'docker':
            return self._export_as_docker(project)
        else:
            raise ValueError(f"Unsupported export format: {export_format}")

    def _export_as_zip(self, project: ProjectContext, include_code: bool, include_docs: bool) -> Dict[str, Any]:
        """Export project as ZIP file"""
        try:
            # Create temporary directory
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = Path(temp_dir) / f"{project.name}_export.zip"

                with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                    # Add project metadata
                    project_data = asdict(project)
                    zip_file.writestr('project.json', json.dumps(project_data, indent=2, default=str))

                    # Add project README
                    readme_content = self._generate_project_readme(project)
                    zip_file.writestr('README.md', readme_content)

                    # Add generated code if requested
                    if include_code:
                        codebase = self.db.generated_code.get_by_project_id(project.project_id)
                        if codebase:
                            for file in codebase.generated_files:
                                zip_file.writestr(f"code/{file.file_path}", file.content)

                            # Add codebase metadata
                            codebase_data = asdict(codebase)
                            zip_file.writestr('code/codebase.json',
                                              json.dumps(codebase_data, indent=2, default=str))

                    # Add documentation if requested
                    if include_docs:
                        knowledge_entries = self.db.knowledge.get_by_project_id(project.project_id)
                        for entry in knowledge_entries:
                            safe_filename = entry.title.replace('/', '_').replace('\\', '_')
                            zip_file.writestr(f"docs/{safe_filename}.txt", entry.content)

                # Read zip content
                zip_content = zip_path.read_bytes()

                return {
                    'success': True,
                    'format': 'zip',
                    'size_bytes': len(zip_content),
                    'filename': f"{project.name}_export.zip",
                    'content_base64': zip_content.hex(),  # Convert to hex for transport
                    'export_timestamp': datetime.now().isoformat()
                }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _generate_project_readme(self, project: ProjectContext) -> str:
        """Generate README content for project export"""
        readme = f"""# {project.name}

## Description
{project.description}

## Goals
{project.goals}

## Requirements
{chr(10).join(f"- {req}" for req in project.requirements)}

## Technology Stack
{chr(10).join(f"- {tech}" for tech in project.tech_stack)}

## Constraints
{chr(10).join(f"- {constraint}" for constraint in project.constraints)}

## Team Structure
{project.team_structure}

## Project Information
- **Phase**: {project.phase}
- **Architecture Pattern**: {project.architecture_pattern}
- **Created**: {project.created_at}
- **Last Updated**: {project.updated_at}

---
*This project was generated using the Socratic RAG Enhanced system.*
"""
        return readme

    def _export_as_pdf(self, project: ProjectContext) -> Dict[str, Any]:
        """Export project as PDF report"""
        # This would require a PDF generation library like reportlab
        # For now, return a placeholder
        return {
            'success': False,
            'error': 'PDF export not yet implemented',
            'suggestion': 'Use ZIP or JSON export instead'
        }

    def _export_as_json(self, project: ProjectContext, include_code: bool) -> Dict[str, Any]:
        """Export project as JSON"""
        try:
            export_data = {
                'project': asdict(project),
                'export_info': {
                    'format': 'json',
                    'timestamp': datetime.now().isoformat(),
                    'include_code': include_code
                }
            }

            # Add generated code if requested
            if include_code:
                codebase = self.db.generated_code.get_by_project_id(project.project_id)
                if codebase:
                    export_data['codebase'] = asdict(codebase)

            # Add knowledge entries
            knowledge_entries = self.db.knowledge.get_by_project_id(project.project_id)
            export_data['knowledge_entries'] = [asdict(entry) for entry in knowledge_entries]

            json_content = json.dumps(export_data, indent=2, default=str)

            return {
                'success': True,
                'format': 'json',
                'size_bytes': len(json_content.encode()),
                'content': json_content,
                'export_timestamp': datetime.now().isoformat()
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _export_as_docker(self, project: ProjectContext) -> Dict[str, Any]:
        """Export project with Docker configuration"""
        try:
            codebase = self.db.generated_code.get_by_project_id(project.project_id)
            if not codebase:
                return {
                    'success': False,
                    'error': 'No generated code found for Docker export'
                }

            docker_files = self._generate_docker_files(project, codebase)

            return {
                'success': True,
                'format': 'docker',
                'files': docker_files,
                'instructions': [
                    'Save the files to your project directory',
                    'Run: docker build -t project-name .',
                    'Run: docker-compose up'
                ]
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _generate_docker_files(self, project: ProjectContext, codebase: GeneratedCodebase) -> Dict[str, str]:
        """Generate Docker configuration files"""
        tech_stack = codebase.technology_stack

        # Generate Dockerfile based on tech stack
        if tech_stack.get('backend') == 'Flask':
            dockerfile = """FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000

ENV FLASK_APP=app.py
ENV FLASK_ENV=production

CMD ["python", "app.py"]"""

        elif tech_stack.get('backend') == 'Django':
            dockerfile = """FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

RUN python manage.py collectstatic --noinput

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]"""

        else:
            dockerfile = """FROM python:3.9-slim

WORKDIR /app

COPY . .

EXPOSE 8000

CMD ["python", "-m", "http.server", "8000"]"""

        # Generate docker-compose.yml
        docker_compose = f"""version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - DATABASE_URL=sqlite:///app.db
    volumes:
      - ./data:/app/data

  # Uncomment if you need a database
  # db:
  #   image: postgres:13
  #   environment:
  #     POSTGRES_DB: {project.name.lower()}
  #     POSTGRES_USER: user
  #     POSTGRES_PASSWORD: password
  #   volumes:
  #     - postgres_data:/var/lib/postgresql/data

# volumes:
#   postgres_data:
"""

        # Generate .dockerignore
        dockerignore = """__pycache__/
*.pyc
*.pyo
*.pyd
.Python
.git/
.pytest_cache/
.coverage
.venv/
venv/
node_modules/
.DS_Store
*.log
.env
"""

        return {
            'Dockerfile': dockerfile,
            'docker-compose.yml': docker_compose,
            '.dockerignore': dockerignore
        }

    def _generate_summary(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive project summary"""
        project_id = data.get('project_id')
        summary_type = data.get('type', 'full')  # full, executive, technical, progress

        project = self.db.projects.get_by_id(project_id)
        if not project:
            raise ValueError("Project not found")

        if summary_type == 'executive':
            return self._generate_executive_summary(project)
        elif summary_type == 'technical':
            return self._generate_technical_summary(project)
        elif summary_type == 'progress':
            return self._generate_progress_summary(project)
        else:
            return self._generate_full_summary(project)

    def _generate_executive_summary(self, project: ProjectContext) -> Dict[str, Any]:
        """Generate executive-level summary"""
        # Get progress data
        modules = self.db.modules.get_by_project_id(project.project_id)
        tasks = self.db.tasks.get_by_project_id(project.project_id)

        completed_modules = len([m for m in modules if m.status == 'completed'])
        completed_tasks = len([t for t in tasks if t.status == 'completed'])

        summary = {
            'type': 'executive',
            'project_name': project.name,
            'status': project.phase,
            'progress_percentage': (completed_tasks / len(tasks) * 100) if tasks else 0,
            'key_metrics': {
                'total_requirements': len(project.requirements),
                'team_size': len(project.collaborators),
                'modules_completed': f"{completed_modules}/{len(modules)}",
                'tasks_completed': f"{completed_tasks}/{len(tasks)}"
            },
            'highlights': [
                f"Project in {project.phase} phase",
                f"{completed_tasks}/{len(tasks)} tasks completed" if tasks else "No tasks defined",
                f"{len(project.collaborators)} team members" if project.collaborators else "No team assigned"
            ],
            'next_steps': self._get_next_steps(project),
            'risks': self._identify_key_risks(project, modules, tasks)
        }

        return summary

    def _generate_technical_summary(self, project: ProjectContext) -> Dict[str, Any]:
        """Generate technical summary"""
        codebase = self.db.generated_code.get_by_project_id(project.project_id)
        test_results = self.db.test_results.get_by_project_id(project.project_id) if codebase else []

        summary = {
            'type': 'technical',
            'project_name': project.name,
            'architecture_pattern': project.architecture_pattern,
            'technology_stack': project.tech_stack,
            'code_generation': {
                'status': 'completed' if codebase else 'not_started',
                'files_generated': len(codebase.generated_files) if codebase else 0,
                'lines_of_code': sum(len(f.content.split('\n')) for f in codebase.generated_files) if codebase else 0
            },
            'testing': {
                'tests_run': len(test_results),
                'last_test_status': test_results[-1].passed if test_results else None,
                'average_coverage': sum(t.coverage_percentage for t in test_results) / len(
                    test_results) if test_results else 0
            },
            'quality_metrics': codebase.code_quality_metrics if codebase else {}
        }

        return summary

    def _generate_progress_summary(self, project: ProjectContext) -> Dict[str, Any]:
        """Generate progress-focused summary"""
        modules = self.db.modules.get_by_project_id(project.project_id)
        tasks = self.db.tasks.get_by_project_id(project.project_id)

        summary = {
            'type': 'progress',
            'project_name': project.name,
            'overall_progress': self._calculate_overall_progress(modules, tasks),
            'phase_breakdown': {
                'discovery': self._calculate_phase_progress('discovery', modules, tasks),
                'analysis': self._calculate_phase_progress('analysis', modules, tasks),
                'design': self._calculate_phase_progress('design', modules, tasks),
                'implementation': self._calculate_phase_progress('implementation', modules, tasks)
            },
            'timeline': {
                'project_start': project.created_at.isoformat(),
                'last_update': project.updated_at.isoformat(),
                'estimated_completion': self._estimate_completion_date(project, tasks)
            }
        }

        return summary

    def _generate_full_summary(self, project: ProjectContext) -> Dict[str, Any]:
        """Generate comprehensive full summary"""
        executive = self._generate_executive_summary(project)
        technical = self._generate_technical_summary(project)
        progress = self._generate_progress_summary(project)

        return {
            'type': 'full',
            'generated_at': datetime.now().isoformat(),
            'executive_summary': executive,
            'technical_summary': technical,
            'progress_summary': progress
        }

    def _calculate_overall_progress(self, modules: List, tasks: List) -> float:
        """Calculate overall project progress"""
        if not tasks:
            return 0.0

        completed_tasks = len([t for t in tasks if t.status == 'completed'])
        return (completed_tasks / len(tasks)) * 100

    def _calculate_phase_progress(self, phase: str, modules: List, tasks: List) -> float:
        """Calculate progress for specific phase"""
        phase_tasks = [t for t in tasks if hasattr(t, 'phase') and t.phase == phase]
        if not phase_tasks:
            return 0.0

        completed_tasks = len([t for t in phase_tasks if t.status == 'completed'])
        return (completed_tasks / len(phase_tasks)) * 100

    def _estimate_completion_date(self, project: ProjectContext, tasks: List) -> str:
        """Estimate project completion date"""
        if not tasks:
            return "Unable to estimate"

        completed_tasks = len([t for t in tasks if t.status == 'completed'])
        if completed_tasks == 0:
            return "Unable to estimate"

        total_tasks = len(tasks)
        completion_ratio = completed_tasks / total_tasks

        days_elapsed = (datetime.now() - project.created_at).days
        if days_elapsed == 0:
            return "Unable to estimate"

        estimated_total_days = days_elapsed / completion_ratio
        remaining_days = estimated_total_days - days_elapsed

        from datetime import timedelta
        completion_date = datetime.now() + timedelta(days=remaining_days)
        return completion_date.strftime('%Y-%m-%d')

    def _get_next_steps(self, project: ProjectContext) -> List[str]:
        """Generate next steps recommendations"""
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

    def _identify_key_risks(self, project: ProjectContext, modules: List, tasks: List) -> List[str]:
        """Identify key project risks"""
        risks = []

        # Timeline risks
        if len(tasks) > 50:
            risks.append("Large number of tasks may cause timeline delays")

        # Team risks
        if len(project.collaborators) == 0:
            risks.append("No team members assigned to project")
        elif len(project.collaborators) > 10:
            risks.append("Large team size may create coordination challenges")

        # Technical risks
        if len(project.tech_stack) > 8:
            risks.append("Complex technology stack may increase development complexity")

        # Scope risks
        if len(project.requirements) > 25:
            risks.append("High number of requirements may lead to scope creep")

        return risks

    def _ide_integration(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle IDE integration operations"""
        operation = data.get('operation')  # push_files, sync_status, setup_environment
        project_id = data.get('project_id')

        if operation == 'push_files':
            return self._push_files_to_ide(project_id, data)
        elif operation == 'sync_status':
            return self._get_sync_status(project_id)
        elif operation == 'setup_environment':
            return self._setup_development_environment(project_id, data)
        else:
            raise ValueError(f"Unknown IDE operation: {operation}")

    def _push_files_to_ide(self, project_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Push generated files to IDE workspace"""
        workspace_path = data.get('workspace_path')
        overwrite = data.get('overwrite', False)

        if not workspace_path:
            raise ValueError("workspace_path is required")

        # Get generated codebase
        codebase = self.db.generated_code.get_by_project_id(project_id)
        if not codebase:
            raise ValueError("No generated code found for project")

        try:
            pushed_files = []
            errors = []

            for file in codebase.generated_files:
                try:
                    file_path = Path(workspace_path) / file.file_path

                    # Create directory if needed
                    file_path.parent.mkdir(parents=True, exist_ok=True)

                    # Write file (check overwrite)
                    if not file_path.exists() or overwrite:
                        file_path.write_text(file.content, encoding='utf-8')
                        pushed_files.append(file.file_path)
                    else:
                        errors.append(f"File exists: {file.file_path}")

                except Exception as e:
                    errors.append(f"Error with {file.file_path}: {str(e)}")

            return {
                'success': True,
                'files_pushed': len(pushed_files),
                'pushed_files': pushed_files,
                'errors': errors,
                'workspace_path': workspace_path
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _get_sync_status(self, project_id: str) -> Dict[str, Any]:
        """Get IDE synchronization status"""
        # This would integrate with actual IDE
        return {
            'project_id': project_id,
            'sync_status': 'active',
            'last_sync': datetime.now().isoformat(),
            'files_in_sync': True,
            'pending_changes': []
        }

    def _setup_development_environment(self, project_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Set up development environment"""
        workspace_path = data.get('workspace_path')
        environment_type = data.get('environment', 'python')  # python, node, full_stack

        if not workspace_path:
            raise ValueError("workspace_path is required")

        try:
            setup_steps = []

            if environment_type == 'python':
                setup_steps.extend(self._setup_python_environment(workspace_path))
            elif environment_type == 'node':
                setup_steps.extend(self._setup_node_environment(workspace_path))
            elif environment_type == 'full_stack':
                setup_steps.extend(self._setup_python_environment(workspace_path))
                setup_steps.extend(self._setup_node_environment(workspace_path))

            return {
                'success': True,
                'environment_type': environment_type,
                'setup_steps': setup_steps,
                'workspace_path': workspace_path
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _setup_python_environment(self, workspace_path: str) -> List[str]:
        """Set up Python development environment"""
        steps = []

        try:
            # Create virtual environment
            venv_path = Path(workspace_path) / '.venv'
            if not venv_path.exists():
                subprocess.run(['python', '-m', 'venv', str(venv_path)], check=True)
                steps.append("Created Python virtual environment")

            # Create requirements.txt if it doesn't exist
            requirements_path = Path(workspace_path) / 'requirements.txt'
            if not requirements_path.exists():
                default_requirements = """flask==2.3.3
requests==2.31.0
python-dotenv==1.0.0
pytest==7.4.2
"""
                requirements_path.write_text(default_requirements)
                steps.append("Created requirements.txt")

        except Exception as e:
            steps.append(f"Error setting up Python environment: {str(e)}")

        return steps

    def _setup_node_environment(self, workspace_path: str) -> List[str]:
        """Set up Node.js development environment"""
        steps = []

        try:
            # Create package.json if it doesn't exist
            package_json_path = Path(workspace_path) / 'package.json'
            if not package_json_path.exists():
                package_json = {
                    "name": "project",
                    "version": "1.0.0",
                    "description": "Generated project",
                    "main": "index.js",
                    "scripts": {
                        "start": "node index.js",
                        "test": "jest",
                        "dev": "nodemon index.js"
                    },
                    "dependencies": {
                        "express": "^4.18.2",
                        "cors": "^2.8.5"
                    },
                    "devDependencies": {
                        "jest": "^29.7.0",
                        "nodemon": "^3.0.1"
                    }
                }
                package_json_path.write_text(json.dumps(package_json, indent=2))
                steps.append("Created package.json")

        except Exception as e:
            steps.append(f"Error setting up Node environment: {str(e)}")

        return steps

    def _deploy_application(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy application to specified platform"""
        project_id = data.get('project_id')
        platform = data.get('platform', 'docker')  # docker, heroku, aws, local
        deployment_config = data.get('config', {})

        if platform == 'docker':
            return self._deploy_to_docker(project_id, deployment_config)
        elif platform == 'heroku':
            return self._deploy_to_heroku(project_id, deployment_config)
        elif platform == 'local':
            return self._deploy_locally(project_id, deployment_config)
        else:
            return {
                'success': False,
                'error': f"Unsupported deployment platform: {platform}"
            }

    def _deploy_to_docker(self, project_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy application using Docker"""
        # This would integrate with Docker API
        return {
            'success': False,
            'error': 'Docker deployment not yet implemented',
            'instructions': [
                'Use export_project with docker format',
                'Build Docker image: docker build -t project-name .',
                'Run container: docker run -p 5000:5000 project-name'
            ]
        }

    def _deploy_to_heroku(self, project_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy application to Heroku"""
        # This would integrate with Heroku API
        return {
            'success': False,
            'error': 'Heroku deployment not yet implemented',
            'instructions': [
                'Install Heroku CLI',
                'Login: heroku login',
                'Create app: heroku create app-name',
                'Deploy: git push heroku main'
            ]
        }

    def _deploy_locally(self, project_id: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Deploy application locally for testing"""
        workspace_path = config.get('workspace_path')
        if not workspace_path:
            return {
                'success': False,
                'error': 'workspace_path required for local deployment'
            }

        try:
            # Basic local deployment simulation
            return {
                'success': True,
                'deployment_type': 'local',
                'status': 'deployed',
                'url': 'http://localhost:5000',
                'instructions': [
                    f'Navigate to: {workspace_path}',
                    'Run: python app.py (for Python projects)',
                    'Or run: npm start (for Node.js projects)',
                    'Access at: http://localhost:5000'
                ]
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _backup_project(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create backup of project data"""
        project_id = data.get('project_id')
        backup_type = data.get('type', 'full')  # full, code_only, metadata_only

        try:
            backup_data = {
                'backup_id': f"backup_{project_id}_{int(time.time())}",
                'project_id': project_id,
                'backup_type': backup_type,
                'timestamp': datetime.now().isoformat()
            }

            if backup_type in ['full', 'metadata_only']:
                project = self.db.projects.get_by_id(project_id)
                if project:
                    backup_data['project'] = asdict(project)

                modules = self.db.modules.get_by_project_id(project_id)
                backup_data['modules'] = [asdict(m) for m in modules]

                tasks = self.db.tasks.get_by_project_id(project_id)
                backup_data['tasks'] = [asdict(t) for t in tasks]

            if backup_type in ['full', 'code_only']:
                codebase = self.db.generated_code.get_by_project_id(project_id)
                if codebase:
                    backup_data['codebase'] = asdict(codebase)

            # In a real implementation, this would be stored in a backup service
            backup_json = json.dumps(backup_data, indent=2, default=str)

            return {
                'success': True,
                'backup_id': backup_data['backup_id'],
                'backup_type': backup_type,
                'size_bytes': len(backup_json.encode()),
                'timestamp': backup_data['timestamp']
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _sync_files(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronize files between different environments"""
        source_path = data.get('source_path')
        target_path = data.get('target_path')
        sync_direction = data.get('direction', 'bidirectional')  # source_to_target, target_to_source, bidirectional

        if not source_path or not target_path:
            raise ValueError("Both source_path and target_path are required")

        try:
            synced_files = []

            if sync_direction in ['source_to_target', 'bidirectional']:
                files_synced = self._sync_directory(source_path, target_path)
                synced_files.extend(files_synced)

            if sync_direction in ['target_to_source', 'bidirectional']:
                files_synced = self._sync_directory(target_path, source_path)
                synced_files.extend(files_synced)

            return {
                'success': True,
                'files_synced': len(synced_files),
                'synced_files': synced_files,
                'sync_direction': sync_direction
            }

        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }

    def _sync_directory(self, source: str, target: str) -> List[str]:
        """Sync files from source to target directory"""
        synced_files = []
        source_path = Path(source)
        target_path = Path(target)

        if not source_path.exists():
            return synced_files

        target_path.mkdir(parents=True, exist_ok=True)

        for file_path in source_path.rglob('*'):
            if file_path.is_file():
                relative_path = file_path.relative_to(source_path)
                target_file_path = target_path / relative_path

                # Create parent directories
                target_file_path.parent.mkdir(parents=True, exist_ok=True)

                # Copy file if newer or doesn't exist
                if (not target_file_path.exists() or
                        file_path.stat().st_mtime > target_file_path.stat().st_mtime):

                    try:
                        target_file_path.write_bytes(file_path.read_bytes())
                        synced_files.append(str(relative_path))
                    except Exception as e:
                        self.logger.warning(f"Failed to sync {file_path}: {e}")

        return synced_files

    def _create_documentation(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create comprehensive project documentation"""
        project_id = data.get('project_id')
        doc_types = data.get('types', ['api', 'user', 'technical'])
        format_type = data.get('format', 'markdown')

        project = self.db.projects.get_by_id(project_id)
        if not project:
            raise ValueError("Project not found")

        documentation = {}

        for doc_type in doc_types:
            if doc_type == 'api':
                documentation['api'] = self._create_api_documentation(project)
            elif doc_type == 'user':
                documentation['user'] = self._create_user_documentation(project)
            elif doc_type == 'technical':
                documentation['technical'] = self._create_technical_documentation(project)

        return {
            'success': True,
            'project_id': project_id,
            'documentation_types': doc_types,
            'format': format_type,
            'documentation': documentation,
            'generated_at': datetime.now().isoformat()
        }

    def _create_api_documentation(self, project: ProjectContext) -> str:
        """Create API documentation"""
        codebase = self.db.generated_code.get_by_project_id(project.project_id)

        doc = f"""# API Documentation - {project.name}

## Overview
This document describes the API endpoints for {project.name}.

## Base URL
```
http://localhost:5000/api
```

## Authentication
[Authentication details would be generated based on code analysis]

## Endpoints
"""

        if codebase:
            api_files = [f for f in codebase.generated_files if
                         'api' in f.file_purpose.lower() or 'route' in f.file_purpose.lower()]

            for api_file in api_files:
                doc += f"""
### {api_file.file_path}
File purpose: {api_file.file_purpose}

[API endpoints would be extracted from code analysis]
"""

        doc += f"""
## Error Handling
Standard HTTP status codes are used throughout the API.

## Generated
This documentation was automatically generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.
"""

        return doc

    def _create_user_documentation(self, project: ProjectContext) -> str:
        """Create user documentation"""
        return f"""# User Guide - {project.name}

## Overview
{project.description}

## Getting Started

### Prerequisites
- [Prerequisites based on technology stack]

### Installation
1. Clone the repository
2. Install dependencies
3. Configure environment variables
4. Run the application

### Basic Usage
[Usage instructions based on project requirements and features]

## Features
{chr(10).join(f"- {req}" for req in project.requirements)}

## Support
For technical support, please refer to the technical documentation or contact the development team.

## Generated
This documentation was automatically generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.
"""

    def _create_technical_documentation(self, project: ProjectContext) -> str:
        """Create technical documentation"""
        codebase = self.db.generated_code.get_by_project_id(project.project_id)

        doc = f"""# Technical Documentation - {project.name}

## Architecture
- **Pattern**: {project.architecture_pattern}
- **Phase**: {project.phase}

## Technology Stack
{chr(10).join(f"- {tech}" for tech in project.tech_stack)}

## Project Structure
"""

        if codebase:
            doc += f"""
### Generated Files
Total files: {len(codebase.generated_files)}

```
{json.dumps(codebase.file_structure, indent=2)}
```

### Code Quality
- **Architecture Type**: {codebase.architecture_type}
- **Version**: {codebase.version}
- **Status**: {codebase.status}
"""

        doc += f"""
## Development Setup
1. Clone the repository
2. Set up development environment
3. Install dependencies
4. Configure environment variables

## Deployment
[Deployment instructions based on deployment configuration]

## Generated
This documentation was automatically generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}.
"""

        return doc
