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
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from functools import wraps

# Flask and related imports
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
    # Define fallback classes
    Flask = None
    FlaskForm = None
    CSRFProtect = None
    FileField = None
    FileAllowed = None
    FileRequired = None
    LoginManager = None
    UserMixin = object
    login_user = None
    logout_user = None
    login_required = None
    current_user = None
    StringField = None
    TextAreaField = None
    SelectField = None
    BooleanField = None
    IntegerField = None
    SubmitField = None
    DataRequired = None
    Length = None
    Email = None
    OptionalValidator = None
    secure_filename = None
    generate_password_hash = None
    check_password_hash = None
    render_template = None
    request = None
    jsonify = None
    redirect = None
    url_for = None
    flash = None
    session = None
    send_file = None
    abort = None
    Response = None
    stream_template = None

    logger = logging.getLogger(__name__)
    logger.error("Flask and related packages not available")

# Import system components
try:
    from src import get_config, get_logger, get_event_bus
    from src.core import SocraticException, ValidationHelper, DateTimeHelper
    from src.models import Project, User, TechnicalSpec, ConversationMessage, UserRole, UserStatus
    from src.database import get_repository_manager
    from src.agents import get_orchestrator
    from src.services import get_services_status
    from src import get_system_status

    SYSTEM_AVAILABLE = True
except ImportError as e:
    SYSTEM_AVAILABLE = False

    # Define all fallback functions and classes in except block
    def get_config():
        """Fallback config function"""
        return {}


    def get_logger(name: str):
        """Fallback logger function"""
        return logging.getLogger(name)


    def get_event_bus():
        """Fallback event bus function"""
        return None


    SocraticException = Exception


    class ValidationHelper:
        """Fallback ValidationHelper"""

        @staticmethod
        def is_valid_email(email: str) -> bool:
            return '@' in email

        @staticmethod
        def is_valid_username(username: str) -> bool:
            return len(username) >= 3


    class DateTimeHelper:
        """Fallback DateTimeHelper"""

        @staticmethod
        def now():
            return datetime.now()

        @staticmethod
        def to_iso_string(dt):
            return dt.isoformat() if dt else None


    class Project:
        """Fallback Project model"""
        pass


    class User:
        """Fallback User model"""
        pass


    class TechnicalSpec:
        """Fallback TechnicalSpec model"""
        pass


    class ConversationMessage:
        """Fallback ConversationMessage model"""
        pass


    class UserRole:
        """Fallback UserRole enum"""
        ADMIN = 'admin'
        DEVELOPER = 'developer'
        USER = 'user'


    def get_repository_manager():
        """Fallback repository manager"""
        return None


    def get_orchestrator():
        """Fallback orchestrator"""
        return None


    def get_system_status():
        """Fallback services status"""
        return {}

logger = get_logger(__name__)


# =================================================================
# FLASK-LOGIN USER CLASS
# =================================================================

class WebUser(UserMixin):
    """Flask-Login user implementation."""

    def __init__(self, user_id: str, username: str, email: str, role: str):
        self.id = user_id
        self.username = username
        self.email = email
        self.role = role
        # Note: is_authenticated, is_active, is_anonymous are provided by UserMixin

    def get_id(self):
        return self.id


# =================================================================
# FLASK FORMS
# =================================================================

if FLASK_AVAILABLE:
    class LoginForm(FlaskForm):
        """User login form."""
        username = StringField('Username', validators=[DataRequired(), Length(min=3, max=50)])
        password = StringField('Password', validators=[DataRequired(), Length(min=6)])
        remember = BooleanField('Remember Me')
        submit = SubmitField('Log In')


    class ProjectForm(FlaskForm):
        """Project creation/editing form."""
        name = StringField('Project Name', validators=[DataRequired(), Length(max=200)])
        description = TextAreaField('Description', validators=[Length(max=2000)])
        tech_stack = TextAreaField('Technology Stack')
        submit = SubmitField('Create Project')


    class SocraticSessionForm(FlaskForm):
        """Socratic session form."""
        project_id = StringField('Project ID', validators=[DataRequired()])
        role = SelectField('Role', choices=[
            ('product_owner', 'Product Owner'),
            ('architect', 'Architect'),
            ('developer', 'Developer'),
            ('tester', 'Tester'),
            ('ui_ux', 'UI/UX Designer'),
            ('security', 'Security Specialist'),
            ('business_analyst', 'Business Analyst')
        ])
        submit = SubmitField('Start Session')


    class CodeGenerationForm(FlaskForm):
        """Code generation form."""
        project_id = StringField('Project ID', validators=[DataRequired()])
        modules = TextAreaField('Modules (comma-separated)')
        test_coverage = BooleanField('Include Tests', default=True)
        documentation = BooleanField('Generate Documentation', default=True)
        submit = SubmitField('Generate Code')


    class DocumentUploadForm(FlaskForm):
        """Document upload form."""
        file = FileField('Document', validators=[
            FileRequired(),
            FileAllowed(['pdf', 'docx', 'txt', 'md', 'py', 'js', 'html', 'css'], 'Invalid file type')
        ])
        project_id = StringField('Project ID')
        submit = SubmitField('Upload Document')


# =================================================================
# UTILITY FUNCTIONS
# =================================================================

def api_response(success: bool = True, message: str = '', data: Any = None, status_code: int = 200) -> tuple:
    """Standard API response format."""
    return jsonify({
        'success': success,
        'message': message,
        'data': data,
        'timestamp': DateTimeHelper.to_iso_string(DateTimeHelper.now())
    }), status_code


def with_agent_orchestration(f):
    """Decorator to ensure agent orchestrator is available."""

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not SYSTEM_AVAILABLE:
            return api_response(
                success=False,
                message='System components not available',
                status_code=503
            )

        orchestrator = get_orchestrator()
        if orchestrator is None:
            return api_response(
                success=False,
                message='Agent orchestrator not available',
                status_code=503
            )

        return f(*args, **kwargs)

    return decorated_function


# =================================================================
# FLASK APPLICATION FACTORY
# =================================================================

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

    # Create Flask application (renamed from 'app' to 'flask_app' to avoid shadowing)
    flask_app = Flask(__name__)

    # Load configuration
    try:
        config = get_config()
        web_config = config.get('web', {}) if config else {}
    except (ImportError, AttributeError, TypeError) as e:
        logger.warning(f"Could not load web config: {e}")
        web_config = {}

    # Apply configuration overrides
    if config_override:
        web_config.update(config_override)

    # Flask configuration
    flask_app.config['SECRET_KEY'] = web_config.get('secret_key', 'socratic-rag-dev-key-change-in-production')
    flask_app.config['WTF_CSRF_ENABLED'] = web_config.get('csrf_enabled', True)
    flask_app.config['MAX_CONTENT_LENGTH'] = web_config.get('max_file_size', 16 * 1024 * 1024)  # 16MB
    flask_app.config['UPLOAD_FOLDER'] = web_config.get('upload_folder', 'data/uploads')
    flask_app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=web_config.get('session_hours', 24))

    # Ensure upload directory exists
    os.makedirs(flask_app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Initialize extensions
    csrf = CSRFProtect()
    csrf.init_app(flask_app)

    # Initialize login manager
    login_manager = LoginManager()
    login_manager.init_app(flask_app)
    login_manager.login_view = 'login'
    login_manager.login_message = 'Please log in to access this page.'

    @login_manager.user_loader
    def load_user(user_id):
        """Load user for Flask-Login."""
        try:
            repo_manager = get_repository_manager()
            if repo_manager:
                user_repo = repo_manager.get_repository('user')
                user = user_repo.get_by_id(user_id)
                if user:
                    role_value = user.role.value if hasattr(user.role, 'value') else user.role
                    return WebUser(user.id, user.username, user.email, role_value)
        except Exception as e:
            logger.error(f"Error loading user: {e}")
        return None

    # Get orchestrator for routes
    orchestrator = get_orchestrator() if SYSTEM_AVAILABLE else None

    # =================================================================
    # PAGE ROUTES
    # =================================================================

    @flask_app.route('/')
    def index():
        """Home page - redirect to dashboard or login."""
        if current_user and current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))

    @flask_app.route('/login', methods=['GET', 'POST'])
    def login():
        """User login page."""
        if not FLASK_AVAILABLE:
            return "Flask not available", 503

        form = LoginForm() if FLASK_AVAILABLE else None

        if form and form.validate_on_submit():
            username = form.username.data
            password = form.password.data

            try:
                repo_manager = get_repository_manager()
                if repo_manager:
                    user_repo = repo_manager.get_repository('user')
                    user = user_repo.get_by_username(username)

                    if user and check_password_hash(user.password_hash, password):
                        role_value = user.role.value if hasattr(user.role, 'value') else user.role
                        web_user = WebUser(user.id, user.username, user.email, role_value)
                        login_user(web_user, remember=form.remember.data)
                        flash('Login successful!', 'success')
                        return redirect(url_for('dashboard'))

                flash('Invalid username or password', 'error')
            except Exception as e:
                logger.error(f"Login error: {e}")
                flash('Login system unavailable', 'error')

        return render_template('auth.html', form=form, mode='login')

    @flask_app.route('/logout')
    @login_required
    def logout():
        """User logout."""
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))

    @flask_app.route('/register', methods=['GET', 'POST'])
    def register():
        """User registration page."""
        if request.method == 'POST':
            try:
                # Get form data
                username = request.form.get('username', '').strip()
                email = request.form.get('email', '').strip()
                password = request.form.get('password', '')
                confirm_password = request.form.get('confirm_password', '')
                first_name = request.form.get('first_name', '').strip()
                last_name = request.form.get('last_name', '').strip()
                terms = request.form.get('terms') == 'on'

                # Basic validation
                errors = []
                if not username or len(username) < 3:
                    errors.append('Username must be at least 3 characters')
                if email and '@' not in email:
                    errors.append('Valid email address format required')
                if not password or len(password) < 6:
                    errors.append('Password must be at least 6 characters')
                if password != confirm_password:
                    errors.append('Passwords do not match')
                if not terms:
                    errors.append('You must accept the Terms of Service')

                if errors:
                    for error in errors:
                        flash(error, 'error')
                    return render_template('auth.html', page='register')

                # Check system availability
                repo_manager = get_repository_manager()
                if not repo_manager:
                    flash('Registration system unavailable', 'error')
                    return render_template('auth.html', page='register')

                # Check if username exists
                user_repo = repo_manager.get_repository('user')
                if user_repo.get_by_username(username):
                    flash('Username already exists', 'error')
                    return render_template('auth.html', page='register')

                # Create user directly via repository
                try:
                    from src.models import User, UserRole, UserStatus
                    from src.core import DateTimeHelper

                    user_email = email if email else f"{username}@example.com"

                    # Create user model
                    new_user = User(
                        username=username,
                        email=user_email,
                        password_hash=generate_password_hash(password),
                        first_name=first_name,
                        last_name=last_name,
                        role=UserRole.DEVELOPER,
                        status=UserStatus.ACTIVE,
                        created_at=DateTimeHelper.now()
                    )

                    # Save to database using repository
                    # Save to database using repository
                    print(f"DEBUG: Attempting to create user: {username}")
                    print(f"DEBUG: User object before conversion: {new_user}")

                    # Convert enum fields to string values
                    new_user.role = new_user.role.value if hasattr(new_user.role, 'value') else new_user.role
                    new_user.status = new_user.status.value if hasattr(new_user.status, 'value') else new_user.status

                    print(f"DEBUG: User object after conversion: {new_user}")
                    created_user = user_repo.create(new_user)

                    if created_user:
                        flash('Account created successfully! Please log in.', 'success')
                        return redirect(url_for('login'))
                    else:
                        flash('Registration failed: Could not create user', 'error')
                        print("DEBUG: user_repo.create() returned None or False")

                except Exception as e:
                    logger.error(f"Registration error: {e}")
                    flash(f'Registration failed: {str(e)}', 'error')

            except Exception as e:
                logger.error(f"Registration error: {e}")
                flash('An error occurred during registration', 'error')

        return render_template('auth.html', page='register')

    @flask_app.route('/dashboard')
    @login_required
    def dashboard():
        """Main dashboard page."""
        try:
            # Get system status
            system_status = get_services_status() if SYSTEM_AVAILABLE else {}

            # Get user's projects
            projects = []
            if SYSTEM_AVAILABLE:
                repo_manager = get_repository_manager()
                if repo_manager:
                    project_repo = repo_manager.get_repository('project')
                    projects = project_repo.get_by_owner(current_user.id)

            # Get agent status
            agent_status = {}
            if orchestrator:
                agent_status = orchestrator.health_check()

            return render_template('dashboard.html',
                                   projects=projects,
                                   system_status=system_status,
                                   agent_status=agent_status)
        except Exception as e:
            logger.error(f"Dashboard error: {e}")
            return render_template('dashboard.html',
                                   projects=[],
                                   system_status={},
                                   agent_status={},
                                   error=str(e))

    @flask_app.route('/projects')
    @login_required
    def projects():
        """Projects listing page."""
        try:
            projects = []
            if SYSTEM_AVAILABLE:
                repo_manager = get_repository_manager()
                if repo_manager:
                    project_repo = repo_manager.get_repository('project')
                    projects = project_repo.find_by_user(current_user.id)

            return render_template('projects.html', projects=projects)
        except Exception as e:
            logger.error(f"Projects page error: {e}")
            return render_template('projects.html', projects=[], error=str(e))

    @flask_app.route('/projects/new', methods=['GET', 'POST'])
    @login_required
    def new_project():
        """Create new project."""
        form = ProjectForm() if FLASK_AVAILABLE else None

        if form and form.validate_on_submit():
            try:
                repo_manager = get_repository_manager()
                if repo_manager and orchestrator:
                    # Create project via agent
                    result = orchestrator.route_request(
                        'project_manager',
                        'create_project',
                        {
                            'name': form.name.data,
                            'description': form.description.data,
                            'tech_stack': form.tech_stack.data,
                            'user_id': current_user.id
                        }
                    )

                    if result.get('success'):
                        flash('Project created successfully!', 'success')
                        return redirect(url_for('projects'))
                    else:
                        flash(f"Error creating project: {result.get('message')}", 'error')
            except Exception as e:
                logger.error(f"Project creation error: {e}")
                flash('Failed to create project', 'error')

        return render_template('projects.html', form=form, mode='new')

    # Alias for compatibility
    flask_app.route('/projects/create', methods=['GET', 'POST'])(new_project)

    @flask_app.route('/projects/<project_id>')
    @login_required
    def project_detail(project_id: str):
        """Project details page."""
        try:
            project = None
            modules = []

            if SYSTEM_AVAILABLE:
                repo_manager = get_repository_manager()
                if repo_manager:
                    project_repo = repo_manager.get_repository('project')
                    project = project_repo.get(project_id)

                    if project:
                        module_repo = repo_manager.get_repository('module')
                        modules = module_repo.find_by_project(project_id)

            return render_template('projects.html',
                                   project=project,
                                   modules=modules,
                                   mode='detail')
        except Exception as e:
            logger.error(f"Project detail error: {e}")
            return render_template('projects.html', error=str(e))

    @flask_app.route('/sessions')
    @login_required
    def sessions():
        """Socratic sessions page."""
        try:
            # Get user's recent sessions
            sessions_list = []
            if SYSTEM_AVAILABLE and orchestrator:
                result = orchestrator.route_request(
                    'socratic_counselor',
                    'get_user_sessions',
                    {'user_id': current_user.id}
                )
                if result.get('success'):
                    sessions_list = result.get('data', [])

            return render_template('sessions.html', sessions=sessions_list)
        except Exception as e:
            logger.error(f"Sessions page error: {e}")
            return render_template('sessions.html', sessions=[], error=str(e))

    @flask_app.route('/sessions/new', methods=['GET', 'POST'])
    @login_required
    @with_agent_orchestration
    def new_session():
        """Start new Socratic session."""
        form = SocraticSessionForm() if FLASK_AVAILABLE else None

        if form and form.validate_on_submit():
            try:
                result = orchestrator.route_request(
                    'socratic_counselor',
                    'start_session',
                    {
                        'project_id': form.project_id.data,
                        'role': form.role.data,
                        'user_id': current_user.id
                    }
                )

                if result.get('success'):
                    session_id = result.get('data', {}).get('session_id')
                    flash('Session started!', 'success')
                    return redirect(url_for('session_detail', session_id=session_id))
                else:
                    flash(f"Error starting session: {result.get('message')}", 'error')
            except Exception as e:
                logger.error(f"Session creation error: {e}")
                flash('Failed to start session', 'error')

        return render_template('sessions.html', form=form, mode='new')

    # Alias for compatibility
    flask_app.route('/sessions/start', methods=['GET', 'POST'])(new_session)

    @flask_app.route('/sessions/<session_id>')
    @login_required
    def session_detail(session_id: str):
        """Socratic session detail page."""
        try:
            session_data = None
            messages = []

            if SYSTEM_AVAILABLE and orchestrator:
                result = orchestrator.route_request(
                    'socratic_counselor',
                    'get_session',
                    {'session_id': session_id}
                )
                if result.get('success'):
                    session_data = result.get('data')
                    messages = session_data.get('messages', [])

            return render_template('sessions.html',
                                   session=session_data,
                                   messages=messages,
                                   mode='detail')
        except Exception as e:
            logger.error(f"Session detail error: {e}")
            return render_template('sessions.html', error=str(e))

    @flask_app.route('/code')
    @login_required
    def code():
        """Code generation page."""
        try:
            # Get user's projects
            projects = []
            if SYSTEM_AVAILABLE:
                repo_manager = get_repository_manager()
                if repo_manager:
                    project_repo = repo_manager.get_repository('project')
                    projects = project_repo.find_by_user(current_user.id)

            return render_template('code.html', projects=projects)
        except Exception as e:
            logger.error(f"Code page error: {e}")
            return render_template('code.html', projects=[], error=str(e))

    @flask_app.route('/code/generate', methods=['POST'])
    @login_required
    @with_agent_orchestration
    def generate_code():
        """Generate code for project."""
        form = CodeGenerationForm() if FLASK_AVAILABLE else None

        if form and form.validate_on_submit():
            try:
                result = orchestrator.route_request(
                    'code_generator',
                    'generate_code',
                    {
                        'project_id': form.project_id.data,
                        'modules': [m.strip() for m in form.modules.data.split(',')],
                        'test_coverage': form.test_coverage.data,
                        'documentation': form.documentation.data
                    }
                )

                if result.get('success'):
                    flash('Code generation started!', 'success')
                    return redirect(url_for('code_status',
                                            generation_id=result.get('data', {}).get('generation_id')))
                else:
                    flash(f"Error generating code: {result.get('message')}", 'error')
            except Exception as e:
                logger.error(f"Code generation error: {e}")
                flash('Failed to generate code', 'error')

        return render_template('code.html', form=form)

    @flask_app.route('/code/status/<generation_id>')
    @login_required
    def code_status(generation_id: str):
        """Check code generation status."""
        try:
            status_data = None
            if SYSTEM_AVAILABLE and orchestrator:
                result = orchestrator.route_request(
                    'code_generator',
                    'get_generation_status',
                    {'generation_id': generation_id}
                )
                if result.get('success'):
                    status_data = result.get('data')

            return render_template('code.html',
                                   generation_status=status_data,
                                   mode='status')
        except Exception as e:
            logger.error(f"Code status error: {e}")
            return render_template('code.html', error=str(e))

    @flask_app.route('/reports')
    @login_required
    def reports():
        """Reports and analytics page."""
        try:
            # Get user's project statistics
            stats = {}
            if SYSTEM_AVAILABLE and orchestrator:
                result = orchestrator.route_request(
                    'system_monitor',
                    'get_user_stats',
                    {'user_id': current_user.id}
                )
                if result.get('success'):
                    stats = result.get('data', {})

            return render_template('reports.html', stats=stats)
        except Exception as e:
            logger.error(f"Reports page error: {e}")
            return render_template('reports.html', stats={}, error=str(e))

    @flask_app.route('/admin')
    @login_required
    def admin():
        """Admin panel (requires admin role)."""
        if current_user.role != 'admin':
            abort(403)

        try:
            # Get system-wide statistics
            system_stats = {}
            agent_health = {}

            if SYSTEM_AVAILABLE and orchestrator:
                agent_health = orchestrator.health_check()

            if SYSTEM_AVAILABLE:
                repo_manager = get_repository_manager()
                if repo_manager:
                    # Get counts
                    user_repo = repo_manager.get_repository('user')
                    project_repo = repo_manager.get_repository('project')

                    system_stats = {
                        'total_users': user_repo.count(),
                        'total_projects': project_repo.count(),
                        'agents': agent_health
                    }

            return render_template('admin.html', stats=system_stats)
        except Exception as e:
            logger.error(f"Admin page error: {e}")
            return render_template('admin.html', stats={}, error=str(e))

    @flask_app.route('/documents/upload', methods=['GET', 'POST'])
    @login_required
    def upload_document():
        """Document upload page - placeholder."""
        flash('Document upload feature coming soon!', 'info')
        return redirect(url_for('dashboard'))
    # =================================================================
    # API ROUTES
    # =================================================================

    @flask_app.route('/api/health')
    def api_health():
        """Health check endpoint."""
        return api_response(
            success=True,
            message='System operational',
            data={
                'flask': FLASK_AVAILABLE,
                'system': SYSTEM_AVAILABLE,
                'orchestrator': orchestrator is not None
            }
        )

    @flask_app.route('/api/agents/status')
    @login_required
    @with_agent_orchestration
    def api_agents_status():
        """Get all agents status."""
        try:
            status = orchestrator.health_check()
            return api_response(status)
        except Exception as e:
            logger.error(f"API agents status error: {e}")
            return api_response(success=False, message=str(e), status_code=500)

    @flask_app.route('/api/agents/<agent_name>/status')
    @login_required
    @with_agent_orchestration
    def api_agent_status(agent_name: str):
        """Get specific agent status."""
        try:
            status = orchestrator.get_agent_status(agent_name)
            return api_response(status)
        except Exception as e:
            logger.error(f"API agent status error: {e}")
            return api_response(success=False, message=str(e), status_code=500)

    @flask_app.route('/api/projects/<project_id>/generate', methods=['POST'])
    @login_required
    @with_agent_orchestration
    def api_generate_project(project_id: str):
        """API endpoint for project code generation."""
        return generate_code()

    @flask_app.route('/api/services/status', methods=['GET'])
    @login_required
    @with_agent_orchestration
    def api_services_status():
        """
        Get external services health status.

        Query Parameters:
            detailed (bool): Include detailed metrics (default: False)
            include_recommendations (bool): Include recommendations (default: True)
        """
        try:
            # Extract parameters from query string
            detailed = request.args.get('detailed', 'false').lower() == 'true'
            include_recommendations = request.args.get('include_recommendations', 'true').lower() == 'true'

            # Route request to system monitor agent
            result = orchestrator.route_request(
                'system_monitor',
                'check_health',
                {
                    'detailed': detailed,
                    'include_recommendations': include_recommendations
                }
            )

            if result.get('success'):
                return api_response(
                    success=True,
                    message='Services status retrieved',
                    data=result.get('data', {})
                )
            else:
                return api_response(
                    success=False,
                    message=result.get('error', 'Failed to retrieve services status'),
                    status_code=500
                )

        except Exception as e:
            logger.error(f"API services status error: {e}")
            return api_response(
                success=False,
                message=str(e),
                status_code=500
            )

    @flask_app.route('/api/analytics/performance', methods=['POST'])
    @login_required
    @with_agent_orchestration
    def api_analytics_performance():
        """
        Get performance analytics and metrics.

        Request Body (JSON):
            {
                "time_range": "1h" | "24h" | "7d" | "30d",
                "include_historical": bool,
                "include_recommendations": bool
            }
        """
        try:
            # Extract parameters from request body
            data = request.get_json() or {}

            time_range = data.get('time_range', '1h')
            include_historical = data.get('include_historical', False)
            include_recommendations = data.get('include_recommendations', True)

            # Validate time_range
            valid_ranges = ['1h', '24h', '7d', '30d']
            if time_range not in valid_ranges:
                return api_response(
                    success=False,
                    message=f'Invalid time_range. Must be one of: {", ".join(valid_ranges)}',
                    status_code=400
                )

            # Route request to system monitor agent
            result = orchestrator.route_request(
                'system_monitor',
                'monitor_performance',
                {
                    'time_range': time_range,
                    'include_historical': include_historical,
                    'include_recommendations': include_recommendations
                }
            )

            if result.get('success'):
                return api_response(
                    success=True,
                    message='Performance analytics retrieved',
                    data=result.get('data', {})
                )
            else:
                return api_response(
                    success=False,
                    message=result.get('error', 'Failed to retrieve performance analytics'),
                    status_code=500
                )

        except Exception as e:
            logger.error(f"API analytics performance error: {e}")
            return api_response(
                success=False,
                message=str(e),
                status_code=500
            )

    # =================================================================
    # ERROR HANDLERS
    # =================================================================

    @flask_app.errorhandler(404)
    def not_found_error(error):
        return render_template('base.html', error='Page not found'), 404

    @flask_app.errorhandler(500)
    def internal_error(error):
        logger.error(f"Internal server error: {error}")
        return render_template('base.html', error='Internal server error'), 500

    @flask_app.errorhandler(403)
    def forbidden_error(error):
        return render_template('base.html', error='Access forbidden'), 403

    # =================================================================
    # TEMPLATE CONTEXT PROCESSORS
    # =================================================================

    @flask_app.context_processor
    def inject_system_info():
        """Inject system information into all templates."""
        return {
            'system_available': SYSTEM_AVAILABLE,
            'agents_available': orchestrator is not None,
            'current_time': datetime.now().isoformat(),
            'app_version': '7.3.0'
        }

    logger.info("Flask application created successfully")
    return flask_app


# =================================================================
# APPLICATION FACTORY - MAIN INTERFACE
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


# =================================================================
# MODULE EXPORTS
# =================================================================

__all__ = [
    # Main factory functions
    'create_app',
    'create_flask_app',

    # Imported functions that are re-exported
    'get_config',
    'get_event_bus',

    # Availability flags
    'FLASK_AVAILABLE',
    'SYSTEM_AVAILABLE',

    # User class
    'WebUser',

    # Forms (if Flask available)
    'LoginForm',
    'ProjectForm',
    'SocraticSessionForm',
    'CodeGenerationForm',
    'DocumentUploadForm',

    # Utility functions
    'api_response',
    'with_agent_orchestration',
]

# =================================================================
# DEVELOPMENT SERVER RUNNER
# =================================================================

if __name__ == '__main__':
    flask_app = create_app()
    if flask_app:
        flask_app.run(debug=True, host='127.0.0.1', port=5000)
    else:
        print("Failed to create Flask application")
