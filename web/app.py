"""
Flask Web Application - Main Application and Routes
==================================================

Main Flask application for the Socratic RAG Enhanced system.
Provides web interface for agent orchestration, project management, and code generation.

Features:
- Dashboard with real-time analytics
- Project and module management
- Socratic conversation interface
- Code generation and testing interface
- User authentication and session management
- Agent orchestration and monitoring
- RESTful API endpoints
"""

import logging
import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
import asyncio
from functools import wraps

try:
    from flask import (
        Flask, render_template, request, jsonify, redirect, url_for,
        flash, session, send_file, abort, Response, stream_template
    )
    from flask_wtf import FlaskForm, CSRFProtect
    from flask_wtf.file import FileField, FileAllowed, FileRequired
    from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
    from wtforms import StringField, TextAreaField, SelectField, BooleanField, IntegerField, SubmitField
    from wtforms.validators import DataRequired, Length, Email, Optional as OptionalValidator
    from werkzeug.utils import secure_filename
    from werkzeug.security import generate_password_hash, check_password_hash

    FLASK_AVAILABLE = True
except ImportError:
    FLASK_AVAILABLE = False
    Flask = None
    logger = logging.getLogger(__name__)
    logger.error("Flask and related packages not available")

# Import our system components
try:
    from ..core import get_config, SocraticException, get_event_manager
    from ..models import Project, User, TechnicalSpec, ConversationMessage
    from ..database import get_repository_manager
    from ..agents import get_orchestrator, AgentOrchestrator
    from ..services import get_service, get_services_status

    SYSTEM_AVAILABLE = True
except ImportError as e:
    SYSTEM_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.error(f"System components not available: {e}")

logger = logging.getLogger(__name__)


class WebUser(UserMixin):
    """Flask-Login user implementation."""

    def __init__(self, user_id: str, username: str, email: str, is_admin: bool = False):
        self.id = user_id
        self.username = username
        self.email = email
        self.is_admin = is_admin
        self.is_active = True


# Forms for web interface
class LoginForm(FlaskForm):
    """User login form."""
    username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
    password = StringField('Password', validators=[DataRequired(), Length(min=6)])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class ProjectForm(FlaskForm):
    """Project creation/editing form."""
    name = StringField('Project Name', validators=[DataRequired(), Length(min=3, max=100)])
    description = TextAreaField('Description', validators=[Length(max=500)])
    technology_stack = TextAreaField('Technology Stack (JSON)', validators=[OptionalValidator()])
    requirements = TextAreaField('Requirements')
    submit = SubmitField('Save Project')


class SocraticSessionForm(FlaskForm):
    """Socratic conversation form."""
    user_input = TextAreaField('Your Response', validators=[DataRequired(), Length(min=1, max=2000)])
    session_id = StringField('Session ID', validators=[DataRequired()])
    submit = SubmitField('Send Response')


class CodeGenerationForm(FlaskForm):
    """Code generation form."""
    project_id = StringField('Project ID', validators=[DataRequired()])
    generation_type = SelectField('Generation Type', choices=[
        ('full_application', 'Full Application'),
        ('specific_module', 'Specific Module'),
        ('tests_only', 'Tests Only'),
        ('documentation', 'Documentation')
    ])
    additional_requirements = TextAreaField('Additional Requirements')
    submit = SubmitField('Generate Code')


class DocumentUploadForm(FlaskForm):
    """Document upload form."""
    file = FileField('Document', validators=[
        FileRequired(),
        FileAllowed(['pdf', 'docx', 'txt', 'md', 'py', 'js', 'html', 'css'], 'Invalid file type')
    ])
    project_id = StringField('Project ID')
    submit = SubmitField('Upload Document')


def create_flask_app(config_override: Optional[Dict[str, Any]] = None) -> Flask:
    """
    Create and configure Flask application.

    Args:
        config_override: Optional configuration overrides

    Returns:
        Configured Flask application
    """
    if not FLASK_AVAILABLE:
        raise RuntimeError("Flask not available")

    app = Flask(__name__)

    # Load configuration
    try:
        config = get_config()
        web_config = config.get('web', {})
    except:
        web_config = {}

    # Apply configuration overrides
    if config_override:
        web_config.update(config_override)

    # Flask configuration
    app.config['SECRET_KEY'] = web_config.get('secret_key', 'socratic-rag-dev-key-change-in-production')
    app.config['WTF_CSRF_ENABLED'] = web_config.get('csrf_enabled', True)
    app.config['MAX_CONTENT_LENGTH'] = web_config.get('max_file_size', 16 * 1024 * 1024)  # 16MB
    app.config['UPLOAD_FOLDER'] = web_config.get('upload_folder', 'data/uploads')
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=web_config.get('session_hours', 24))

    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize extensions
    csrf = CSRFProtect()
    csrf.init_app(app)

    # Initialize login manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'

    @login_manager.user_loader
    def load_user(user_id):
        """Load user for Flask-Login."""
        try:
            if SYSTEM_AVAILABLE:
                repo_manager = get_repository_manager()
                user_repo = repo_manager.get_repository('user')
                user_data = user_repo.get_by_id(user_id)
                if user_data:
                    return WebUser(user_data.id, user_data.username, user_data.email)
            return None
        except Exception as e:
            logger.error(f"Failed to load user {user_id}: {e}")
            return None

    # Initialize system components if available
    if SYSTEM_AVAILABLE:
        try:
            orchestrator = get_orchestrator()
            repo_manager = get_repository_manager()
            logger.info("System components initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize system components: {e}")
            orchestrator = None
            repo_manager = None
    else:
        orchestrator = None
        repo_manager = None

    # Helper function for API responses
    def api_response(data: Any = None, success: bool = True, message: str = '', status_code: int = 200):
        """Standard API response format."""
        return jsonify({
            'success': success,
            'message': message,
            'data': data,
            'timestamp': datetime.now().isoformat()
        }), status_code

    # Helper decorator for agent orchestration
    def with_agent_orchestration(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not orchestrator:
                return api_response(success=False, message="Agent orchestration not available", status_code=503)
            return f(*args, **kwargs)

        return decorated_function

    # =================================================================
    # AUTHENTICATION ROUTES
    # =================================================================

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        """User login page."""
        form = LoginForm()

        if form.validate_on_submit():
            username = form.username.data
            password = form.password.data

            # For development, create a demo user
            if username == 'demo' and password == 'demo123':
                user = WebUser('demo-user', 'demo', 'demo@example.com', True)
                login_user(user, remember=form.remember_me.data)
                flash('Successfully logged in!', 'success')
                return redirect(url_for('dashboard'))
            else:
                flash('Invalid username or password', 'error')

        return render_template('auth.html', form=form, page='login')

    @app.route('/logout')
    @login_required
    def logout():
        """User logout."""
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        """User registration (demo version)."""
        return render_template('auth.html', page='register')

    # =================================================================
    # MAIN DASHBOARD
    # =================================================================

    @app.route('/')
    @app.route('/dashboard')
    @login_required
    def dashboard():
        """Main dashboard with analytics and overview."""
        try:
            # Get system status
            system_status = {
                'agents_available': orchestrator is not None,
                'services_status': get_services_status() if SYSTEM_AVAILABLE else {},
                'total_projects': 0,
                'active_sessions': 0,
                'generated_files': 0
            }

            # Get recent projects if available
            recent_projects = []
            if repo_manager:
                try:
                    project_repo = repo_manager.get_repository('project')
                    recent_projects = project_repo.list_projects(limit=5)
                except Exception as e:
                    logger.error(f"Failed to get recent projects: {e}")

            return render_template('dashboard.html',
                                   system_status=system_status,
                                   recent_projects=recent_projects)

        except Exception as e:
            logger.error(f"Dashboard error: {e}")
            flash('Error loading dashboard', 'error')
            return render_template('dashboard.html', system_status={}, recent_projects=[])

    # =================================================================
    # PROJECT MANAGEMENT
    # =================================================================

    @app.route('/projects')
    @login_required
    def projects():
        """Project management page."""
        try:
            projects_list = []
            if repo_manager:
                project_repo = repo_manager.get_repository('project')
                projects_list = project_repo.list_projects(user_id=current_user.id)

            return render_template('projects.html', projects=projects_list)

        except Exception as e:
            logger.error(f"Projects page error: {e}")
            flash('Error loading projects', 'error')
            return render_template('projects.html', projects=[])

    @app.route('/projects/create', methods=['GET', 'POST'])
    @login_required
    def create_project():
        """Create new project."""
        form = ProjectForm()

        if form.validate_on_submit():
            try:
                # Parse technology stack JSON
                tech_stack = {}
                if form.technology_stack.data:
                    tech_stack = json.loads(form.technology_stack.data)

                project_data = {
                    'name': form.name.data,
                    'description': form.description.data,
                    'technology_stack': tech_stack,
                    'requirements': form.requirements.data,
                    'user_id': current_user.id,
                    'status': 'planning'
                }

                if repo_manager:
                    project_repo = repo_manager.get_repository('project')
                    project = project_repo.create_project(project_data)
                    flash(f'Project "{project.name}" created successfully!', 'success')
                    return redirect(url_for('project_detail', project_id=project.id))
                else:
                    flash('Project creation not available', 'error')

            except json.JSONDecodeError:
                flash('Invalid technology stack JSON format', 'error')
            except Exception as e:
                logger.error(f"Project creation error: {e}")
                flash('Error creating project', 'error')

        return render_template('projects.html', form=form, page='create')

    @app.route('/projects/<project_id>')
    @login_required
    def project_detail(project_id: str):
        """Project detail page."""
        try:
            project = None
            if repo_manager:
                project_repo = repo_manager.get_repository('project')
                project = project_repo.get_by_id(project_id)

            if not project:
                flash('Project not found', 'error')
                return redirect(url_for('projects'))

            return render_template('projects.html', project=project, page='detail')

        except Exception as e:
            logger.error(f"Project detail error: {e}")
            flash('Error loading project', 'error')
            return redirect(url_for('projects'))

    # =================================================================
    # SOCRATIC CONVERSATIONS
    # =================================================================

    @app.route('/sessions')
    @login_required
    def socratic_sessions():
        """Socratic conversation sessions."""
        return render_template('sessions.html')

    @app.route('/sessions/start', methods=['POST'])
    @login_required
    @with_agent_orchestration
    def start_socratic_session():
        """Start new Socratic conversation session."""
        try:
            data = request.get_json()
            project_id = data.get('project_id')
            role = data.get('role', 'developer')

            # Start session with Socratic agent
            result = orchestrator.route_request('socratic', 'start_session', {
                'project_id': project_id,
                'user_id': current_user.id,
                'role': role
            })

            return api_response(result)

        except Exception as e:
            logger.error(f"Start session error: {e}")
            return api_response(success=False, message=str(e), status_code=500)

    @app.route('/sessions/<session_id>/message', methods=['POST'])
    @login_required
    @with_agent_orchestration
    def send_message(session_id: str):
        """Send message in Socratic conversation."""
        try:
            data = request.get_json()
            message = data.get('message', '')

            # Process message with Socratic agent
            result = orchestrator.route_request('socratic', 'process_message', {
                'session_id': session_id,
                'user_message': message,
                'user_id': current_user.id
            })

            return api_response(result)

        except Exception as e:
            logger.error(f"Send message error: {e}")
            return api_response(success=False, message=str(e), status_code=500)

    # =================================================================
    # CODE GENERATION
    # =================================================================

    @app.route('/code')
    @login_required
    def code_generation():
        """Code generation interface."""
        return render_template('code.html')

    @app.route('/code/generate', methods=['POST'])
    @login_required
    @with_agent_orchestration
    def generate_code():
        """Generate code from project specifications."""
        try:
            data = request.get_json()
            project_id = data.get('project_id')
            generation_type = data.get('generation_type', 'full_application')

            # Generate code with Code agent
            result = orchestrator.route_request('code', 'generate_project_code', {
                'project_id': project_id,
                'generation_type': generation_type,
                'user_id': current_user.id
            })

            return api_response(result)

        except Exception as e:
            logger.error(f"Code generation error: {e}")
            return api_response(success=False, message=str(e), status_code=500)

    @app.route('/code/test', methods=['POST'])
    @login_required
    @with_agent_orchestration
    def test_generated_code():
        """Test generated code."""
        try:
            data = request.get_json()
            project_id = data.get('project_id')

            # Test code with Code agent
            result = orchestrator.route_request('code', 'test_generated_code', {
                'project_id': project_id,
                'user_id': current_user.id
            })

            return api_response(result)

        except Exception as e:
            logger.error(f"Code testing error: {e}")
            return api_response(success=False, message=str(e), status_code=500)

    @app.route('/code/deploy', methods=['POST'])
    @login_required
    @with_agent_orchestration
    def deploy_code():
        """Deploy generated code to IDE."""
        try:
            data = request.get_json()
            project_id = data.get('project_id')

            # Deploy with Services agent
            result = orchestrator.route_request('services', 'deploy_to_ide', {
                'project_id': project_id,
                'user_id': current_user.id
            })

            return api_response(result)

        except Exception as e:
            logger.error(f"Code deployment error: {e}")
            return api_response(success=False, message=str(e), status_code=500)

    # =================================================================
    # DOCUMENT MANAGEMENT
    # =================================================================

    @app.route('/documents/upload', methods=['POST'])
    @login_required
    @with_agent_orchestration
    def upload_document():
        """Upload and process document."""
        form = DocumentUploadForm()

        if form.validate_on_submit():
            try:
                file = form.file.data
                filename = secure_filename(file.filename)
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

                # Process document with Document agent
                result = orchestrator.route_request('document', 'process_document', {
                    'file_path': file_path,
                    'project_id': form.project_id.data,
                    'user_id': current_user.id
                })

                return api_response(result)

            except Exception as e:
                logger.error(f"Document upload error: {e}")
                return api_response(success=False, message=str(e), status_code=500)

        return api_response(success=False, message="Invalid file upload", status_code=400)

    # =================================================================
    # SYSTEM MONITORING & ADMIN
    # =================================================================

    @app.route('/admin')
    @login_required
    def admin_panel():
        """Admin panel (demo users only)."""
        if not current_user.is_admin:
            abort(403)

        try:
            system_status = {
                'agents_status': orchestrator.get_agent_status() if orchestrator else {},
                'services_status': get_services_status() if SYSTEM_AVAILABLE else {},
                'database_status': repo_manager.health_check() if repo_manager else {}
            }

            return render_template('admin.html', system_status=system_status)

        except Exception as e:
            logger.error(f"Admin panel error: {e}")
            return render_template('admin.html', system_status={})

    # =================================================================
    # API ENDPOINTS
    # =================================================================

    @app.route('/api/status')
    def api_system_status():
        """Get system status via API."""
        try:
            status = {
                'system_available': SYSTEM_AVAILABLE,
                'agents_available': orchestrator is not None,
                'services_status': get_services_status() if SYSTEM_AVAILABLE else {},
                'timestamp': datetime.now().isoformat()
            }

            return api_response(status)

        except Exception as e:
            logger.error(f"API status error: {e}")
            return api_response(success=False, message=str(e), status_code=500)

    @app.route('/api/agents/<agent_name>/status')
    @with_agent_orchestration
    def api_agent_status(agent_name: str):
        """Get specific agent status."""
        try:
            status = orchestrator.get_agent_status(agent_name)
            return api_response(status)

        except Exception as e:
            logger.error(f"API agent status error: {e}")
            return api_response(success=False, message=str(e), status_code=500)

    @app.route('/api/projects/<project_id>/generate', methods=['POST'])
    @login_required
    @with_agent_orchestration
    def api_generate_project(project_id: str):
        """API endpoint for project code generation."""
        return generate_code()

    # =================================================================
    # ERROR HANDLERS
    # =================================================================

    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('base.html', error='Page not found'), 404

    @app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return render_template('base.html', error='Internal server error'), 500

    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('base.html', error='Access forbidden'), 403

    # =================================================================
    # TEMPLATE CONTEXT PROCESSORS
    # =================================================================

    @app.context_processor
    def inject_system_info():
        """Inject system information into all templates."""
        return {
            'system_available': SYSTEM_AVAILABLE,
            'agents_available': orchestrator is not None,
            'current_time': datetime.now().isoformat(),
            'app_version': '7.3.0'
        }

    logger.info("Flask application created successfully")
    return app


# =================================================================
# APPLICATION FACTORY
# =================================================================

def create_app(config_override: Optional[Dict[str, Any]] = None) -> Optional[Flask]:
    """
    Main application factory function.

    Args:
        config_override: Optional configuration overrides

    Returns:
        Flask application or None if not available
    """
    if not FLASK_AVAILABLE:
        logger.error("Cannot create Flask app - Flask not available")
        return None

    try:
        return create_flask_app(config_override)
    except Exception as e:
        logger.error(f"Failed to create Flask application: {e}")
        return None


# Development server runner
if __name__ == '__main__':
    app = create_app()
    if app:
        app.run(debug=True, host='127.0.0.1', port=5000)
    else:
        print("Failed to create Flask application")
