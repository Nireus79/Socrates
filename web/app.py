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
import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from functools import wraps
from pathlib import Path

try:
    from wtforms.validators import ValidationError
except ImportError:
    ValidationError = Exception

# Flask and related imports
try:
    from flask import (
        Flask, render_template, request, jsonify, redirect, url_for,
        flash, session, send_file, abort, Response, stream_template
    )
    from flask_wtf import FlaskForm, CSRFProtect
    from flask_wtf.file import FileField, FileAllowed, FileRequired
    from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
    from wtforms import StringField, TextAreaField, SelectField, BooleanField, IntegerField, SubmitField, PasswordField
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

logger = logging.getLogger(__name__)

# Try to import system components, but provide fallbacks if they fail
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
    logger.warning(f"System components not available: {e}")


    # Define all fallback functions and classes
    def get_config():
        """Fallback config function"""
        return {}


    def get_logger(name: str):
        """Fallback logger function"""
        return logging.getLogger(name)


    def get_services_status():
        """Fallback services status function"""
        return {
            'available_services': {},
            'initialized_services': [],
            'total_available': 0,
            'total_services': 0
        }


    def get_repository_manager():
        """Fallback repository manager"""
        return None


    def get_orchestrator():
        """Fallback orchestrator"""
        return None


    def get_event_bus():
        """Fallback event bus"""
        return None


    def get_system_status():
        """Fallback system status"""
        return {'status': 'unavailable'}


    class DateTimeHelper:
        @staticmethod
        def now():
            return datetime.now()

        @staticmethod
        def to_iso_string(dt):
            return dt.isoformat() if dt else None

# =================================================================
# GLOBAL DATABASE INSTANCE
# =================================================================

_user_db_instance = None


def get_user_db():
    """Get or create the single global UserDB instance."""
    global _user_db_instance
    if _user_db_instance is None:
        _user_db_instance = UserDB('data/app.db')
    return _user_db_instance


# =================================================================
# WORKING USER CLASS AND DATABASE
# =================================================================

class WorkingUser(UserMixin):
    """Simple User class for authentication"""

    def __init__(self, user_id: str, username: str, email: str, role: str = 'developer'):
        self.id = user_id
        self.username = username
        self.email = email
        self.role = role


class UserDB:
    """Working database class that bypasses broken src imports"""

    def __init__(self, db_path: str = 'data/app.db'):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self.init_db()

    def init_db(self):
        try:
            print(f"🔧 init_db() starting - path: {self.db_path}")
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            print("📡 Database connection established")

            # Users table
            print("📝 Creating users table...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT,
                    password_hash TEXT NOT NULL,
                    first_name TEXT,
                    last_name TEXT,
                    role TEXT DEFAULT 'developer',
                    created_at TEXT
                )
            ''')
            print("✅ Users table SQL executed")

            # Projects table
            print("📝 Creating projects table...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS projects (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    description TEXT,
                    owner_id TEXT NOT NULL,
                    project_type TEXT DEFAULT 'solo',
                    status TEXT DEFAULT 'draft',
                    framework TEXT,
                    technology_stack TEXT,
                    created_at TEXT,
                    updated_at TEXT,
                    FOREIGN KEY (owner_id) REFERENCES users (id)
                )
            ''')
            print("✅ Projects table SQL executed")

            # Sessions table
            print("📝 Creating sessions table...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    session_name TEXT NOT NULL,
                    project_id TEXT,
                    owner_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    status TEXT DEFAULT 'active',
                    progress INTEGER DEFAULT 0,
                    current_phase TEXT DEFAULT 'discovery',
                    session_data TEXT DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
                    FOREIGN KEY (owner_id) REFERENCES users (id) ON DELETE CASCADE
                )
            ''')
            print("✅ Sessions table SQL executed")

            # Session questions table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS session_questions (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    question_text TEXT NOT NULL,
                    question_type TEXT DEFAULT 'discovery',
                    role TEXT NOT NULL,
                    answer_text TEXT,
                    is_answered BOOLEAN DEFAULT 0,
                    importance_score REAL DEFAULT 5.0,
                    created_at TEXT NOT NULL,
                    answered_at TEXT,
                    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE CASCADE
                )
            ''')

            # Code generations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS code_generations (
                    id TEXT PRIMARY KEY,
                    project_id TEXT NOT NULL,
                    session_id TEXT,
                    generation_name TEXT NOT NULL,
                    architecture_pattern TEXT NOT NULL,
                    generation_type TEXT DEFAULT 'full_stack',
                    status TEXT DEFAULT 'pending',
                    progress INTEGER DEFAULT 0,
                    technology_stack TEXT DEFAULT '{}',
                    file_structure TEXT DEFAULT '{}',
                    generation_config TEXT DEFAULT '{}',
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    completed_at TEXT,
                    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
                    FOREIGN KEY (session_id) REFERENCES sessions (id) ON DELETE SET NULL
                )
            ''')

            # Generated files table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS generated_files (
                    id TEXT PRIMARY KEY,
                    generation_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    file_name TEXT NOT NULL,
                    file_type TEXT NOT NULL,
                    file_content TEXT,
                    file_size INTEGER DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (generation_id) REFERENCES code_generations (id) ON DELETE CASCADE
                )
            ''')
            print("💾 Committing changes...")
            conn.commit()
            print("✅ Changes committed")
            print(f"✅ Database initialized successfully at: {self.db_path}")
            print(f"✅ Database file exists: {os.path.exists(self.db_path)}")
            conn.close()
        except Exception as e:
            print(f"❌ DATABASE INIT ERROR: {e}")
            print(f"❌ Database path: {self.db_path}")
            import traceback
            print(traceback.print_exc())
            print("=" * 50)

    # User methods
    def create_user(self, username: str, email: str, password: str, first_name: str = '', last_name: str = ''):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            user_id = str(uuid.uuid4())
            password_hash = generate_password_hash(password)
            created_at = datetime.now().isoformat()

            cursor.execute('''
                INSERT INTO users (id, username, email, password_hash, first_name, last_name, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, username, email, password_hash, first_name, last_name, created_at))

            conn.commit()
            conn.close()
            return user_id
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None

    def get_user_by_username(self, username: str):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, email, role FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()
            conn.close()

            if row:
                return WorkingUser(row[0], row[1], row[2], row[3])
            return None
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            return None

    def get_user_by_id(self, user_id: str):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT id, username, email, role FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            conn.close()

            if row:
                return WorkingUser(row[0], row[1], row[2], row[3])
            return None
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None

    def verify_password(self, username: str, password: str):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('SELECT password_hash FROM users WHERE username = ?', (username,))
            row = cursor.fetchone()
            conn.close()

            if row:
                return check_password_hash(row[0], password)
            return False
        except Exception as e:
            logger.error(f"Error verifying password: {e}")
            return False

    # Project methods
    def create_project(self, owner_id: str, name: str, description: str = '',
                       project_type: str = 'solo', framework: str = ''):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            project_id = str(uuid.uuid4())
            created_at = datetime.now().isoformat()
            updated_at = created_at

            cursor.execute('''
                INSERT INTO projects (id, name, description, owner_id, project_type, framework, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (project_id, name, description, owner_id, project_type, framework, created_at, updated_at))

            conn.commit()
            conn.close()
            return project_id
        except Exception as e:
            logger.error(f"Error creating project: {e}")
            return None

    def get_user_projects(self, user_id: str):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, description, status, framework, project_type, created_at, updated_at
                FROM projects WHERE owner_id = ?
                ORDER BY updated_at DESC
            ''', (user_id,))

            projects = []
            for row in cursor.fetchall():
                projects.append({
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'status': row[3],
                    'framework': row[4],
                    'project_type': row[5],
                    'created_at': row[6],
                    'updated_at': row[7]
                })

            conn.close()
            return projects
        except Exception as e:
            logger.error(f"Error getting user projects: {e}")
            return []

    def get_project(self, project_id: str, user_id: str):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, description, status, framework, project_type, created_at, updated_at
                FROM projects WHERE id = ? AND owner_id = ?
            ''', (project_id, user_id))

            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'description': row[2],
                    'status': row[3],
                    'framework': row[4],
                    'project_type': row[5],
                    'created_at': row[6],
                    'updated_at': row[7]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting project: {e}")
            return None

    def update_project(self, project_id: str, user_id: str, **kwargs):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Build update query dynamically
            allowed_fields = ['name', 'description', 'status', 'framework', 'project_type']
            update_fields = []
            values = []

            for field, value in kwargs.items():
                if field in allowed_fields:
                    update_fields.append(f"{field} = ?")
                    values.append(value)

            if not update_fields:
                return False

            update_fields.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(project_id)
            values.append(user_id)

            query = f"UPDATE projects SET {', '.join(update_fields)} WHERE id = ? AND owner_id = ?"
            cursor.execute(query, values)

            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return success
        except Exception as e:
            logger.error(f"Error updating project: {e}")
            return False

    def delete_project(self, project_id: str, user_id: str):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM projects WHERE id = ? AND owner_id = ?', (project_id, user_id))

            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return success
        except Exception as e:
            logger.error(f"Error deleting project: {e}")
            return False

    # Session methods
    def create_session(self, owner_id: str, session_name: str, role: str,
                       project_id: str = None, session_data: dict = None):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            session_id = str(uuid.uuid4())
            created_at = datetime.now().isoformat()
            updated_at = created_at
            session_data_json = json.dumps(session_data or {})

            cursor.execute('''
                INSERT INTO sessions (id, session_name, project_id, owner_id, role, 
                                    session_data, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (session_id, session_name, project_id, owner_id, role,
                  session_data_json, created_at, updated_at))

            conn.commit()
            conn.close()
            return session_id
        except Exception as e:
            print(f"SESSION CREATION ERROR: {e}")
            print(f"Error type: {type(e).__name__}")
            logger.error(f"Error creating session: {e}")
            return None

    def get_user_sessions(self, user_id: str):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT s.id, s.session_name, s.project_id, s.role, s.status, 
                       s.progress, s.current_phase, s.created_at, s.updated_at,
                       p.name as project_name
                FROM sessions s
                LEFT JOIN projects p ON s.project_id = p.id
                WHERE s.owner_id = ?
                ORDER BY s.updated_at DESC
            ''', (user_id,))

            sessions = []
            for row in cursor.fetchall():
                sessions.append({
                    'id': row[0],
                    'session_name': row[1],
                    'project_id': row[2],
                    'role': row[3],
                    'status': row[4],
                    'progress': row[5],
                    'current_phase': row[6],
                    'created_at': row[7],
                    'updated_at': row[8],
                    'project_name': row[9]
                })

            conn.close()
            return sessions
        except Exception as e:
            logger.error(f"Error getting user sessions: {e}")
            return []

    def get_session(self, session_id: str, user_id: str):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT s.id, s.session_name, s.project_id, s.owner_id, s.role, 
                       s.status, s.progress, s.current_phase, s.session_data,
                       s.created_at, s.updated_at, p.name as project_name
                FROM sessions s
                LEFT JOIN projects p ON s.project_id = p.id
                WHERE s.id = ? AND s.owner_id = ?
            ''', (session_id, user_id))

            row = cursor.fetchone()
            conn.close()

            if row:
                return {
                    'id': row[0],
                    'session_name': row[1],
                    'project_id': row[2],
                    'owner_id': row[3],
                    'role': row[4],
                    'status': row[5],
                    'progress': row[6],
                    'current_phase': row[7],
                    'session_data': json.loads(row[8]) if row[8] else {},
                    'created_at': row[9],
                    'updated_at': row[10],
                    'project_name': row[11]
                }
            return None
        except Exception as e:
            logger.error(f"Error getting session: {e}")
            return None

    def update_session(self, session_id: str, user_id: str, **kwargs):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Build update query dynamically
            allowed_fields = ['session_name', 'status', 'progress', 'current_phase', 'session_data']
            update_fields = []
            values = []

            for field, value in kwargs.items():
                if field in allowed_fields:
                    if field == 'session_data' and isinstance(value, dict):
                        value = json.dumps(value)
                    update_fields.append(f"{field} = ?")
                    values.append(value)

            if not update_fields:
                return False

            update_fields.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(session_id)
            values.append(user_id)

            query = f"UPDATE sessions SET {', '.join(update_fields)} WHERE id = ? AND owner_id = ?"
            cursor.execute(query, values)

            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return success
        except Exception as e:
            logger.error(f"Error updating session: {e}")
            return False

    def delete_session(self, session_id: str, user_id: str):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM sessions WHERE id = ? AND owner_id = ?',
                           (session_id, user_id))

            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return success
        except Exception as e:
            logger.error(f"Error deleting session: {e}")
            return False

    # Code generation methods
    def create_generation(self, project_id: str, generation_name: str,
                          architecture_pattern: str, generation_type: str = 'full_stack',
                          session_id: str = None, technology_stack: dict = None,
                          generation_config: dict = None):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            generation_id = str(uuid.uuid4())
            created_at = datetime.now().isoformat()
            updated_at = created_at
            tech_stack_json = json.dumps(technology_stack or {})
            config_json = json.dumps(generation_config or {})

            cursor.execute('''
                INSERT INTO code_generations (id, project_id, session_id, generation_name,
                                            architecture_pattern, generation_type, 
                                            technology_stack, generation_config,
                                            created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (generation_id, project_id, session_id, generation_name,
                  architecture_pattern, generation_type, tech_stack_json,
                  config_json, created_at, updated_at))

            conn.commit()
            conn.close()
            return generation_id
        except Exception as e:
            logger.error(f"Error creating generation: {e}")
            return None

    def get_project_generations(self, project_id: str, user_id: str):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT g.id, g.generation_name, g.architecture_pattern, g.generation_type,
                       g.status, g.progress, g.created_at, g.updated_at, g.completed_at,
                       COUNT(f.id) as file_count
                FROM code_generations g
                LEFT JOIN generated_files f ON g.id = f.generation_id
                INNER JOIN projects p ON g.project_id = p.id
                WHERE g.project_id = ? AND p.owner_id = ?
                GROUP BY g.id
                ORDER BY g.created_at DESC
            ''', (project_id, user_id))

            generations = []
            for row in cursor.fetchall():
                generations.append({
                    'id': row[0],
                    'generation_name': row[1],
                    'architecture_pattern': row[2],
                    'generation_type': row[3],
                    'status': row[4],
                    'progress': row[5],
                    'created_at': row[6],
                    'updated_at': row[7],
                    'completed_at': row[8],
                    'file_count': row[9]
                })

            conn.close()
            return generations
        except Exception as e:
            logger.error(f"Error getting project generations: {e}")
            return []

    def get_generation(self, generation_id: str, user_id: str):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                SELECT g.id, g.project_id, g.session_id, g.generation_name,
                       g.architecture_pattern, g.generation_type, g.status, g.progress,
                       g.technology_stack, g.file_structure, g.generation_config,
                       g.created_at, g.updated_at, g.completed_at,
                       p.name as project_name
                FROM code_generations g
                INNER JOIN projects p ON g.project_id = p.id
                WHERE g.id = ? AND p.owner_id = ?
            ''', (generation_id, user_id))

            row = cursor.fetchone()

            if row:
                generation = {
                    'id': row[0],
                    'project_id': row[1],
                    'session_id': row[2],
                    'generation_name': row[3],
                    'architecture_pattern': row[4],
                    'generation_type': row[5],
                    'status': row[6],
                    'progress': row[7],
                    'technology_stack': json.loads(row[8]) if row[8] else {},
                    'file_structure': json.loads(row[9]) if row[9] else {},
                    'generation_config': json.loads(row[10]) if row[10] else {},
                    'created_at': row[11],
                    'updated_at': row[12],
                    'completed_at': row[13],
                    'project_name': row[14]
                }

                # Get generated files
                cursor.execute('''
                    SELECT id, file_path, file_name, file_type, file_size, created_at
                    FROM generated_files
                    WHERE generation_id = ?
                    ORDER BY file_path, file_name
                ''', (generation_id,))

                files = []
                for file_row in cursor.fetchall():
                    files.append({
                        'id': file_row[0],
                        'file_path': file_row[1],
                        'file_name': file_row[2],
                        'file_type': file_row[3],
                        'file_size': file_row[4],
                        'created_at': file_row[5]
                    })

                generation['files'] = files
                conn.close()
                return generation

            conn.close()
            return None
        except Exception as e:
            logger.error(f"Error getting generation: {e}")
            return None

    def update_generation(self, generation_id: str, user_id: str, **kwargs):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Build update query dynamically
            allowed_fields = ['generation_name', 'status', 'progress', 'technology_stack',
                              'file_structure', 'generation_config', 'completed_at']
            update_fields = []
            values = []

            for field, value in kwargs.items():
                if field in allowed_fields:
                    if field in ['technology_stack', 'file_structure', 'generation_config'] and isinstance(value, dict):
                        value = json.dumps(value)
                    update_fields.append(f"{field} = ?")
                    values.append(value)

            if not update_fields:
                return False

            update_fields.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            values.append(generation_id)
            values.append(user_id)

            query = f'''
                UPDATE code_generations 
                SET {', '.join(update_fields)} 
                WHERE id = ? AND project_id IN (
                    SELECT id FROM projects WHERE owner_id = ?
                )
            '''
            cursor.execute(query, values)

            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return success
        except Exception as e:
            logger.error(f"Error updating generation: {e}")
            return False

    def delete_generation(self, generation_id: str, user_id: str):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM code_generations 
                WHERE id = ? AND project_id IN (
                    SELECT id FROM projects WHERE owner_id = ?
                )
            ''', (generation_id, user_id))

            success = cursor.rowcount > 0
            conn.commit()
            conn.close()
            return success
        except Exception as e:
            logger.error(f"Error deleting generation: {e}")
            return False

    def add_generated_file(self, generation_id: str, file_path: str, file_name: str,
                           file_type: str, file_content: str = None):
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            file_id = str(uuid.uuid4())
            created_at = datetime.now().isoformat()
            file_size = len(file_content.encode('utf-8')) if file_content else 0

            cursor.execute('''
                INSERT INTO generated_files (id, generation_id, file_path, file_name,
                                           file_type, file_content, file_size, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (file_id, generation_id, file_path, file_name, file_type,
                  file_content, file_size, created_at))

            conn.commit()
            conn.close()
            return file_id
        except Exception as e:
            logger.error(f"Error adding generated file: {e}")
            return None


# =================================================================
# Project Templates Configuration
# =================================================================
PROJECT_TEMPLATES = {
    'web_app': {
        'name': 'Web Application',
        'description': 'Full-stack web application with frontend and backend',
        'icon': 'bi-globe',
        'framework': 'flask',
        'project_type': 'solo',
        'status': 'draft',
        'default_name': 'My Web App',
        'default_description': 'A modern web application with user authentication, dashboard, and responsive design.',
        'requirements': """User authentication and authorization
Admin dashboard with analytics
Responsive design for mobile and desktop
Database integration with ORM
REST API endpoints
Email notifications
User profile management
Search and filtering functionality
Data export capabilities
Security features (CSRF, rate limiting)""",
        'estimated_hours': '80',
        'priority': 'medium',
        'tech_stack': ['Flask', 'SQLAlchemy', 'Bootstrap', 'JavaScript'],
        'use_cases': [
            'Content Management Systems',
            'Business Applications',
            'E-commerce Platforms',
            'Customer Portals'
        ]
    },

    'api_service': {
        'name': 'API Service',
        'description': 'High-performance REST API with documentation',
        'icon': 'bi-cloud-arrow-up',
        'framework': 'fastapi',
        'project_type': 'solo',
        'status': 'draft',
        'default_name': 'API Service',
        'default_description': 'A scalable REST API service with automatic documentation, authentication, and database integration.',
        'requirements': """REST API endpoints with OpenAPI documentation
Authentication and authorization (JWT)
Database models and migrations
Input validation and error handling
Rate limiting and security measures
Automated testing suite
Docker containerization
Health check endpoints
Logging and monitoring
API versioning support""",
        'estimated_hours': '60',
        'priority': 'high',
        'tech_stack': ['FastAPI', 'Pydantic', 'SQLAlchemy', 'PostgreSQL'],
        'use_cases': [
            'Microservices Architecture',
            'Mobile App Backend',
            'Third-party Integrations',
            'Data Processing Services'
        ]
    },

    'frontend_spa': {
        'name': 'Single Page Application',
        'description': 'Modern frontend application with React',
        'icon': 'bi-window-desktop',
        'framework': 'react',
        'project_type': 'solo',
        'status': 'draft',
        'default_name': 'React Dashboard',
        'default_description': 'A modern single-page application with React, featuring responsive design and interactive components.',
        'requirements': """Component-based architecture
State management (Redux/Context)
Responsive design system
API integration
User authentication flow
Real-time data updates
Form validation and handling
Navigation and routing
Performance optimization
Testing setup (Jest, Testing Library)""",
        'estimated_hours': '70',
        'priority': 'medium',
        'tech_stack': ['React', 'TypeScript', 'Tailwind CSS', 'Axios'],
        'use_cases': [
            'Admin Dashboards',
            'Data Visualization Tools',
            'Customer Portals',
            'Progressive Web Apps'
        ]
    },

    'data_science': {
        'name': 'Data Science Project',
        'description': 'Data analysis and machine learning project',
        'icon': 'bi-graph-up',
        'framework': '',
        'project_type': 'solo',
        'status': 'draft',
        'default_name': 'Data Analysis Project',
        'default_description': 'A comprehensive data science project for analysis, visualization, and machine learning.',
        'requirements': """Data collection and preprocessing
Exploratory data analysis (EDA)
Statistical analysis and hypothesis testing
Data visualization and reporting
Machine learning model development
Model evaluation and validation
Feature engineering
Data pipeline automation
Interactive dashboards
Documentation and reproducibility""",
        'estimated_hours': '100',
        'priority': 'medium',
        'tech_stack': ['Python', 'Pandas', 'NumPy', 'Scikit-learn', 'Matplotlib'],
        'use_cases': [
            'Business Intelligence',
            'Predictive Analytics',
            'Research Projects',
            'Process Optimization'
        ]
    },

    'mobile_app': {
        'name': 'Mobile Application',
        'description': 'Cross-platform mobile app with React Native',
        'icon': 'bi-phone',
        'framework': 'react',
        'project_type': 'team',
        'status': 'draft',
        'default_name': 'Mobile App',
        'default_description': 'A cross-platform mobile application with native performance and modern user experience.',
        'requirements': """Cross-platform compatibility (iOS/Android)
Native navigation and gestures
Push notifications
Offline functionality
Camera and media integration
User authentication
Local data storage
API integration
App store optimization
Performance monitoring""",
        'estimated_hours': '120',
        'priority': 'high',
        'tech_stack': ['React Native', 'Expo', 'AsyncStorage', 'Firebase'],
        'use_cases': [
            'Business Apps',
            'E-commerce Apps',
            'Social Platforms',
            'Productivity Tools'
        ]
    },

    'microservice': {
        'name': 'Microservice',
        'description': 'Containerized microservice with Docker',
        'icon': 'bi-boxes',
        'framework': 'fastapi',
        'project_type': 'team',
        'status': 'draft',
        'default_name': 'Microservice',
        'default_description': 'A containerized microservice designed for scalability and distributed architecture.',
        'requirements': """Service-oriented architecture design
Docker containerization
API gateway integration
Service discovery and load balancing
Database per service pattern
Event-driven communication
Health checks and monitoring
CI/CD pipeline setup
Security and authentication
Documentation and testing""",
        'estimated_hours': '90',
        'priority': 'high',
        'tech_stack': ['FastAPI', 'Docker', 'PostgreSQL', 'Redis', 'Kubernetes'],
        'use_cases': [
            'Large-scale Applications',
            'Cloud-native Services',
            'Enterprise Systems',
            'Distributed Platforms'
        ]
    },

    'automation_tool': {
        'name': 'Automation Tool',
        'description': 'Python automation and scripting project',
        'icon': 'bi-gear-fill',
        'framework': '',
        'project_type': 'solo',
        'status': 'draft',
        'default_name': 'Automation Tool',
        'default_description': 'A Python-based automation tool for streamlining repetitive tasks and workflows.',
        'requirements': """Task automation framework
File processing and manipulation
Web scraping capabilities
Email automation
Report generation
Error handling and logging
Configuration management
Scheduled task execution
User interface (CLI or GUI)
Testing and validation""",
        'estimated_hours': '40',
        'priority': 'medium',
        'tech_stack': ['Python', 'Selenium', 'BeautifulSoup', 'Schedule', 'Click'],
        'use_cases': [
            'Business Process Automation',
            'Data Processing',
            'Report Generation',
            'System Administration'
        ]
    },

    'cms_platform': {
        'name': 'Content Management System',
        'description': 'Full-featured CMS with admin interface',
        'icon': 'bi-file-earmark-text',
        'framework': 'django',
        'project_type': 'team',
        'status': 'draft',
        'default_name': 'CMS Platform',
        'default_description': 'A comprehensive content management system with user roles, media management, and customizable themes.',
        'requirements': """User roles and permissions system
Content creation and editing interface
Media library and file management
Theme and template system
SEO optimization features
Multi-language support
Comment and review system
Search functionality
Backup and restore capabilities
Performance optimization""",
        'estimated_hours': '150',
        'priority': 'medium',
        'tech_stack': ['Django', 'PostgreSQL', 'Redis', 'Celery', 'Bootstrap'],
        'use_cases': [
            'Corporate Websites',
            'Blog Platforms',
            'News Sites',
            'Portfolio Sites'
        ]
    }
}


def get_template_by_id(template_id):
    """Get template configuration by ID."""
    return PROJECT_TEMPLATES.get(template_id)


def get_all_templates():
    """Get all available project templates."""
    return PROJECT_TEMPLATES


def apply_template_to_wizard_data(template_id, wizard_data):
    """Apply template configuration to wizard session data."""
    template = get_template_by_id(template_id)
    if not template:
        return wizard_data

    # Apply template defaults to wizard data
    wizard_data.update({
        'name': template['default_name'],
        'description': template['default_description'],
        'project_type': template['project_type'],
        'framework': template['framework'],
        'status': template['status'],
        'requirements': template['requirements'],
        'estimated_hours': template['estimated_hours'],
        'priority': template['priority'],
        'template_id': template_id,
        'template_name': template['name']
    })

    return wizard_data


# =================================================================
# FORM CLASSES
# =================================================================

class LoginForm(FlaskForm):
    """User login form."""
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Log In')


class RegisterForm(FlaskForm):
    """User registration form."""
    username = StringField('Username', validators=[
        DataRequired(),
        Length(min=3, max=20, message='Username must be 3-20 characters')
    ])
    email = StringField('Email', validators=[OptionalValidator(), Email()])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=6, message='Password must be at least 6 characters')
    ])
    first_name = StringField('First Name', validators=[OptionalValidator()])
    last_name = StringField('Last Name', validators=[OptionalValidator()])
    submit = SubmitField('Register')


class ProjectForm(FlaskForm):
    name = StringField('Project Name', validators=[
        DataRequired(),
        Length(min=3, max=100)
    ])
    description = TextAreaField('Description', validators=[
        OptionalValidator(),
        Length(max=1000)
    ])
    project_type = SelectField('Project Type', choices=[
        ('solo', 'Solo Project'),
        ('team', 'Team Project')
    ])
    framework = SelectField('Framework', choices=[
        ('', 'No Framework'),
        ('flask', 'Flask'),
        ('django', 'Django'),
        ('fastapi', 'FastAPI'),
        ('react', 'React'),
        ('vue', 'Vue.js'),
        ('angular', 'Angular')
    ])
    status = SelectField('Status', choices=[
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('archived', 'Archived')
    ])
    submit = SubmitField('Create Project')


class EditProjectForm(FlaskForm):
    """Project editing form."""
    name = StringField('Project Name', validators=[
        DataRequired(),
        Length(min=3, max=100)
    ])
    description = TextAreaField('Description', validators=[
        OptionalValidator(),
        Length(max=1000)
    ])
    status = SelectField('Status', choices=[
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('completed', 'Completed'),
        ('archived', 'Archived')
    ])
    framework = SelectField('Framework', choices=[
        ('', 'No Framework'),
        ('flask', 'Flask'),
        ('django', 'Django'),
        ('fastapi', 'FastAPI'),
        ('react', 'React'),
        ('vue', 'Vue.js'),
        ('angular', 'Angular')
    ])
    project_type = SelectField('Project Type', choices=[
        ('solo', 'Solo Project'),
        ('team', 'Team Project')
    ])
    submit = SubmitField('Update Project')


# Session Forms
class NewSessionForm(FlaskForm):
    session_name = StringField('Session Name', validators=[
        DataRequired(message='Session name is required'),
        Length(min=3, max=100, message='Session name must be between 3 and 100 characters')
    ])

    role = SelectField('Your Role', validators=[DataRequired()], choices=[
        ('developer', 'Software Developer'),
        ('manager', 'Project Manager'),
        ('designer', 'UI/UX Designer'),
        ('tester', 'QA Tester'),
        ('business_analyst', 'Business Analyst'),
        ('devops', 'DevOps Engineer'),
        ('architect', 'Solution Architect')
    ])

    existing_project = SelectField('Link to Project (Optional)', choices=[('', 'No Project')])

    initial_idea = TextAreaField('Initial Project Idea', validators=[
        OptionalValidator(),
        Length(max=1000, message='Initial idea must be under 1000 characters')
    ])

    session_type = SelectField('Session Type', validators=[DataRequired()], choices=[
        ('discovery', 'Discovery & Planning'),
        ('requirements', 'Requirements Analysis'),
        ('architecture', 'Architecture Design'),
        ('implementation', 'Implementation Planning'),
        ('review', 'Code Review & Feedback')
    ], default='discovery')

    submit = SubmitField('Start Session')


class SessionConfigForm(FlaskForm):
    session_name = StringField('Session Name', validators=[
        DataRequired(),
        Length(min=3, max=100)
    ])

    status = SelectField('Status', choices=[
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('archived', 'Archived')
    ])

    current_phase = SelectField('Current Phase', choices=[
        ('discovery', 'Discovery'),
        ('requirements', 'Requirements'),
        ('design', 'Design'),
        ('planning', 'Planning'),
        ('implementation', 'Implementation'),
        ('testing', 'Testing'),
        ('deployment', 'Deployment'),
        ('review', 'Review')
    ])

    progress = SelectField('Progress %', choices=[
        ('0', '0% - Just Started'),
        ('10', '10% - Initial Setup'),
        ('25', '25% - Quarter Complete'),
        ('50', '50% - Half Complete'),
        ('75', '75% - Nearly Done'),
        ('90', '90% - Almost Finished'),
        ('100', '100% - Complete')
    ])

    submit = SubmitField('Update Session')


class QuestionForm(FlaskForm):
    question_text = TextAreaField('Question', validators=[
        DataRequired(message='Question text is required'),
        Length(min=10, max=1000, message='Question must be between 10 and 1000 characters')
    ])

    question_type = SelectField('Question Type', choices=[
        ('discovery', 'Discovery'),
        ('clarification', 'Clarification'),
        ('technical', 'Technical'),
        ('business', 'Business'),
        ('validation', 'Validation')
    ], default='discovery')

    importance_score = SelectField('Importance', choices=[
        ('1', '1 - Low'),
        ('3', '3 - Medium'),
        ('5', '5 - High'),
        ('7', '7 - Critical'),
        ('10', '10 - Urgent')
    ], default='5')

    submit = SubmitField('Ask Question')


class AnswerForm(FlaskForm):
    answer_text = TextAreaField('Answer', validators=[
        DataRequired(message='Answer is required'),
        Length(min=5, max=2000, message='Answer must be between 5 and 2000 characters')
    ])

    submit = SubmitField('Submit Answer')


# Code Generation Forms
class CodeGenerationForm(FlaskForm):
    generation_name = StringField('Generation Name', validators=[
        DataRequired(message='Generation name is required'),
        Length(min=3, max=100, message='Generation name must be between 3 and 100 characters')
    ])

    architecture_pattern = SelectField('Architecture Pattern', validators=[DataRequired()], choices=[
        ('mvc', 'Model-View-Controller (MVC)'),
        ('mvp', 'Model-View-Presenter (MVP)'),
        ('mvvm', 'Model-View-ViewModel (MVVM)'),
        ('microservices', 'Microservices'),
        ('layered', 'Layered Architecture'),
        ('hexagonal', 'Hexagonal Architecture'),
        ('clean', 'Clean Architecture'),
        ('event_driven', 'Event-Driven Architecture')
    ])

    generation_type = SelectField('Generation Type', validators=[DataRequired()], choices=[
        ('full_stack', 'Full Stack Application'),
        ('backend_api', 'Backend API Only'),
        ('frontend_spa', 'Frontend SPA Only'),
        ('mobile_app', 'Mobile Application'),
        ('desktop_app', 'Desktop Application'),
        ('cli_tool', 'Command Line Tool'),
        ('library', 'Library/Package'),
        ('microservice', 'Single Microservice')
    ], default='full_stack')

    primary_language = SelectField('Primary Language', validators=[DataRequired()], choices=[
        ('python', 'Python'),
        ('javascript', 'JavaScript/Node.js'),
        ('typescript', 'TypeScript'),
        ('java', 'Java'),
        ('csharp', 'C#'),
        ('go', 'Go'),
        ('rust', 'Rust'),
        ('php', 'PHP')
    ])

    frontend_framework = SelectField('Frontend Framework (if applicable)', choices=[
        ('', 'None/HTML'),
        ('react', 'React'),
        ('vue', 'Vue.js'),
        ('angular', 'Angular'),
        ('svelte', 'Svelte'),
        ('next', 'Next.js'),
        ('nuxt', 'Nuxt.js'),
        ('flutter', 'Flutter (Mobile)')
    ])

    backend_framework = SelectField('Backend Framework (if applicable)', choices=[
        ('', 'None/Vanilla'),
        ('flask', 'Flask'),
        ('django', 'Django'),
        ('fastapi', 'FastAPI'),
        ('express', 'Express.js'),
        ('nestjs', 'NestJS'),
        ('spring', 'Spring Boot'),
        ('dotnet', '.NET Core'),
        ('gin', 'Gin (Go)'),
        ('actix', 'Actix (Rust)')
    ])

    database_type = SelectField('Database Type', choices=[
        ('', 'None'),
        ('sqlite', 'SQLite'),
        ('postgresql', 'PostgreSQL'),
        ('mysql', 'MySQL'),
        ('mongodb', 'MongoDB'),
        ('redis', 'Redis'),
        ('elasticsearch', 'Elasticsearch')
    ])

    include_authentication = BooleanField('Include Authentication System')
    include_api_docs = BooleanField('Include API Documentation', default=True)
    include_tests = BooleanField('Include Unit Tests', default=True)
    include_docker = BooleanField('Include Docker Configuration')
    include_deployment = BooleanField('Include Deployment Scripts')

    additional_features = TextAreaField('Additional Features/Requirements', validators=[
        OptionalValidator(),
        Length(max=1000, message='Additional features must be under 1000 characters')
    ])

    submit = SubmitField('Generate Code')


class GenerationConfigForm(FlaskForm):
    generation_name = StringField('Generation Name', validators=[
        DataRequired(),
        Length(min=3, max=100)
    ])

    status = SelectField('Status', choices=[
        ('pending', 'Pending'),
        ('generating', 'Generating'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled')
    ])

    progress = SelectField('Progress %', choices=[
        ('0', '0% - Not Started'),
        ('10', '10% - Analyzing Requirements'),
        ('25', '25% - Creating Structure'),
        ('50', '50% - Generating Code'),
        ('75', '75% - Adding Tests'),
        ('90', '90% - Finalizing'),
        ('100', '100% - Complete')
    ])

    submit = SubmitField('Update Generation')


class FileViewerForm(FlaskForm):
    file_id = StringField('File ID', validators=[DataRequired()])
    action = SelectField('Action', choices=[
        ('view', 'View File'),
        ('edit', 'Edit File'),
        ('download', 'Download File'),
        ('delete', 'Delete File')
    ])

    file_content = TextAreaField('File Content', validators=[OptionalValidator()])

    submit = SubmitField('Perform Action')


class BatchActionForm(FlaskForm):
    selected_files = StringField('Selected Files (JSON)', validators=[DataRequired()])

    action = SelectField('Batch Action', validators=[DataRequired()], choices=[
        ('download_zip', 'Download as ZIP'),
        ('sync_to_ide', 'Sync to IDE'),
        ('export_project', 'Export Project'),
        ('delete_files', 'Delete Files')
    ])

    submit = SubmitField('Execute Action')


# Legacy forms for compatibility
class SocraticSessionForm(FlaskForm):
    """Socratic session form."""
    project_id = StringField('Project ID', validators=[DataRequired()])
    role = SelectField('Your Role', validators=[DataRequired()], choices=[
        ('developer', 'Software Developer'),
        ('manager', 'Project Manager'),
        ('designer', 'UI/UX Designer'),
        ('tester', 'QA Tester'),
        ('business_analyst', 'Business Analyst'),
        ('devops', 'DevOps Engineer'),
        ('architect', 'Solution Architect')
    ])
    submit = SubmitField('Start Session')


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

def create_flask_app(config_override=None) -> Flask:
    """
    Create and configure Flask application.

    Args:
        config_override: Optional configuration overrides

    Returns:
        Configured Flask application
    """
    import traceback
    print("🏭 create_flask_app() called from: ", traceback.print_stack())
    print("=" * 50)
    if not FLASK_AVAILABLE:
        print("❌ FLASK_AVAILABLE is False")
        raise RuntimeError("Flask not available")
    print("✅ Flask is available")
    # Create Flask application
    flask_app = Flask(__name__)
    print("🌐 Flask app instance created")

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

    # Initialize database
    print("💾 About to create UserDB...")
    user_db = get_user_db()
    print("✅ UserDB created successfully")

    @login_manager.user_loader
    def load_user(user_id):
        """Load user for Flask-Login."""
        return user_db.get_user_by_id(user_id)

    # =================================================================
    # PAGE ROUTES
    # =================================================================

    @flask_app.route('/')
    def index():
        """Home page - redirect to dashboard or login."""
        if current_user and current_user.is_authenticated:
            return redirect(url_for('dashboard'))
        return redirect(url_for('login'))

    @flask_app.route('/dashboard')
    @login_required
    def dashboard():
        """Main dashboard page."""
        user_projects = user_db.get_user_projects(current_user.id)
        user_sessions = user_db.get_user_sessions(current_user.id)

        # Create system status for dashboard
        system_status = {
            'agents_available': SYSTEM_AVAILABLE,
            'total_available': 0,  # Services count (will be updated when services integrated)
            'total_projects': len(user_projects),
            'generated_files': 0  # Will be counted from code generations later
        }

        return render_template('dashboard.html',
                               projects=user_projects[:5],  # Recent 5 projects
                               sessions=user_sessions[:5],  # Recent 5 sessions
                               project_count=len(user_projects),
                               session_count=len(user_sessions),
                               current_time=datetime.now().isoformat(),
                               system_status=system_status)

    @flask_app.route('/login', methods=['GET', 'POST'])
    def login():
        """User login page."""
        form = LoginForm()

        if form.validate_on_submit():
            username = form.username.data
            password = form.password.data

            if user_db.verify_password(username, password):
                user = user_db.get_user_by_username(username)
                if user:
                    login_user(user, remember=form.remember.data)
                    flash('Login successful!', 'success')
                    return redirect(url_for('dashboard'))

            flash('Invalid username or password', 'error')
        return render_template('auth.html', form=form, page='login')

    @flask_app.route('/register', methods=['GET', 'POST'])
    def register():
        """User registration page."""
        form = RegisterForm()
        if form.validate_on_submit():
            if user_db.get_user_by_username(form.username.data):
                flash('Username already exists', 'error')
                return render_template('auth.html', form=form, page='register')

            user = user_db.create_user(
                username=form.username.data,
                email=form.email.data or f"{form.username.data}@example.com",
                password=form.password.data,
                first_name=form.first_name.data or '',
                last_name=form.last_name.data or ''
            )

            if user:
                flash('Account created successfully! Please log in.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Registration failed. Please try again.', 'error')

        return render_template('auth.html', form=form, page='register')

    @flask_app.route('/logout')
    @login_required
    def logout():
        """User logout."""
        logout_user()
        flash('You have been logged out.', 'info')
        return redirect(url_for('login'))

    @flask_app.route('/forgot-password', methods=['GET', 'POST'])
    def forgot_password():
        """Password reset request page."""
        if request.method == 'POST':
            email = request.form.get('email', '').strip()
            if email:
                flash('If an account with that email exists, you will receive password reset instructions.', 'info')
                return redirect(url_for('login'))
            flash('Please enter your email address', 'error')
        return render_template('auth.html', page='forgot_password')

    @flask_app.route('/profile', methods=['GET', 'POST'])
    @login_required
    def profile():
        """User profile management page."""
        if request.method == 'POST':
            flash('Profile updates will be implemented in the full system.', 'info')
        return render_template('auth.html', page='profile')

    # Project Routes
    @flask_app.route('/projects')
    @login_required
    def projects():
        """Projects dashboard page."""
        user_projects = user_db.get_user_projects(current_user.id)
        return render_template('projects/dashboard.html', projects=user_projects)

    @flask_app.route('/projects/<project_id>')
    @login_required
    def project_detail(project_id):
        """Project detail page."""
        project = user_db.get_project(project_id, current_user.id)
        if not project:
            flash('Project not found.', 'error')
            return redirect(url_for('projects'))

        return render_template('projects/detail.html', project=project)

    @flask_app.route('/projects/<project_id>/edit', methods=['GET', 'POST'])
    @login_required
    def edit_project(project_id):
        """Edit project page."""
        project = user_db.get_project(project_id, current_user.id)
        if not project:
            flash('Project not found.', 'error')
            return redirect(url_for('projects'))

        form = EditProjectForm()

        if form.validate_on_submit():
            success = user_db.update_project(
                project_id=project_id,
                user_id=current_user.id,
                name=form.name.data,
                description=form.description.data,
                status=form.status.data,
                framework=form.framework.data
            )

            if success:
                flash(f'Project "{form.name.data}" updated successfully!', 'success')
                return redirect(url_for('project_detail', project_id=project_id))
            else:
                flash('Error updating project. Please try again.', 'error')

        # Pre-populate form with current project data
        form.name.data = project['name']
        form.description.data = project['description']
        form.status.data = project['status']
        form.framework.data = project['framework']

        return render_template('projects/edit.html', form=form, project=project)

    @flask_app.route('/projects/<project_id>/delete', methods=['POST'])
    @login_required
    def delete_project(project_id):
        """Delete project."""
        project = user_db.get_project(project_id, current_user.id)
        if not project:
            flash('Project not found.', 'error')
            return redirect(url_for('projects'))

        if user_db.delete_project(project_id, current_user.id):
            flash(f'Project "{project["name"]}" deleted successfully.', 'success')
        else:
            flash('Error deleting project. Please try again.', 'error')

        return redirect(url_for('projects'))

    # Session Routes
    @flask_app.route('/sessions')
    @login_required
    def sessions():
        """Sessions dashboard page."""
        user_sessions = user_db.get_user_sessions(current_user.id)
        return render_template('sessions.html', sessions=user_sessions)

    @flask_app.route('/sessions/new', methods=['GET', 'POST'])
    @flask_app.route('/sessions/new/<project_id>', methods=['GET', 'POST'])
    @login_required
    def new_session(project_id=None):
        print(f"🔍 Route using UserDB at: {user_db.db_path}")
        print(f"🔍 UserDB instance: {id(user_db)}")
        """Create new session page."""
        form = NewSessionForm()

        # Get project if project_id provided (URL param takes precedence over query param)
        project = None
        final_project_id = project_id or request.args.get('project_id')

        if final_project_id:
            project = user_db.get_project(final_project_id, current_user.id)
            if not project:
                flash('Project not found.', 'error')
                return redirect(url_for('projects'))

        # Populate project choices for the form
        user_projects = user_db.get_user_projects(current_user.id)
        form.existing_project.choices = [('', 'No Project')] + [
            (p['id'], p['name']) for p in user_projects
        ]

        # Pre-select project if provided
        if project:
            form.existing_project.data = project['id']

        # ADD THIS DEBUG CODE:
        if request.method == 'POST':
            print(f"🔍 POST request received")
            print(f"🔍 Form validation result: {form.validate_on_submit()}")
            if not form.validate_on_submit():
                print(f"🔍 Form errors: {form.errors}")

        # Handle form submission
        if form.validate_on_submit():
            print(f"🔍 Form data received:")
            print(f"   session_name: {form.session_name.data}")
            print(f"   role: {form.role.data}")
            print(f"   existing_project: {form.existing_project.data}")
            print(f"   initial_idea: {form.initial_idea.data}")
            # Use project from form if selected, otherwise use URL/query param project
            selected_project_id = form.existing_project.data if form.existing_project.data else final_project_id

            session_data = {
                'initial_idea': form.initial_idea.data,
                'session_type': form.session_type.data,
                'questions': [],
                'conversation_history': []
            }
            print(f"🔍 Calling create_session with:")
            print(f"   owner_id: {current_user.id}")
            print(f"   session_name: {form.session_name.data}")
            print(f"   role: {form.role.data}")
            print(f"   project_id: {selected_project_id}")

            session_id = user_db.create_session(
                owner_id=current_user.id,
                session_name=form.session_name.data,
                role=form.role.data,
                project_id=selected_project_id,
                session_data=session_data
            )
            print(f"🔍 create_session returned: {session_id}")
            if session_id:
                flash(f'Session "{form.session_name.data}" created successfully!', 'success')
                return redirect(url_for('session_detail', session_id=session_id))
            else:
                flash('Error creating session. Please try again.', 'error')

        # Render template with consistent data
        return render_template('sessions/new.html', form=form, project=project)

    @flask_app.route('/sessions/<session_id>')
    @login_required
    def session_detail(session_id):
        """Session detail page."""
        user_session = user_db.get_session(session_id, current_user.id)
        if not user_session:
            flash('Session not found.', 'error')
            return redirect(url_for('sessions'))

        return render_template('sessions/detail.html', session=user_session)

    @flask_app.route('/sessions/<session_id>/continue', methods=['GET', 'POST'])
    @login_required
    def continue_session(session_id):
        """Continue session page."""
        user_session = user_db.get_session(session_id, current_user.id)
        if not user_session:
            flash('Session not found.', 'error')
            return redirect(url_for('sessions'))

        question_form = QuestionForm()
        answer_form = AnswerForm()

        if question_form.validate_on_submit() and question_form.submit.data:
            # Handle new question submission
            # This would integrate with the AI system later
            flash('Question added to session.', 'success')
            return redirect(url_for('continue_session', session_id=session_id))

        if answer_form.validate_on_submit() and answer_form.submit.data:
            # Handle answer submission
            # This would update the session and trigger next question
            flash('Answer recorded.', 'success')
            return redirect(url_for('continue_session', session_id=session_id))

        return render_template('sessions/continue.html',
                               session=user_session,
                               question_form=question_form,
                               answer_form=answer_form)

    @flask_app.route('/sessions/<session_id>/config', methods=['GET', 'POST'])
    @login_required
    def session_config(session_id):
        """Session configuration page."""
        user_session = user_db.get_session(session_id, current_user.id)
        if not user_session:
            flash('Session not found.', 'error')
            return redirect(url_for('sessions'))

        form = SessionConfigForm()

        if form.validate_on_submit():
            success = user_db.update_session(
                session_id=session_id,
                user_id=current_user.id,
                session_name=form.session_name.data,
                status=form.status.data,
                current_phase=form.current_phase.data,
                progress=int(form.progress.data)
            )

            if success:
                flash('Session updated successfully.', 'success')
                return redirect(url_for('session_detail', session_id=session_id))
            else:
                flash('Error updating session. Please try again.', 'error')
        else:
            # Pre-populate form with current session data
            form.session_name.data = session['session_name']
            form.status.data = session['status']
            form.current_phase.data = session['current_phase']
            form.progress.data = str(session['progress'])

        return render_template('sessions/config.html', form=form, session=session)

    @flask_app.route('/sessions/<session_id>/delete', methods=['POST'])
    @login_required
    def delete_session(session_id):
        """Delete session."""
        user_session = user_db.get_session(session_id, current_user.id)
        if not user_session:
            flash('Session not found.', 'error')
            return redirect(url_for('sessions'))

        if user_db.delete_session(session_id, current_user.id):
            flash(f'Session "{user_session["session_name"]}" deleted successfully.', 'success')
        else:
            flash('Error deleting session. Please try again.', 'error')

        return redirect(url_for('sessions'))

    @flask_app.route('/projects/<project_id>/sessions')
    @login_required
    def project_sessions(project_id):
        """Project sessions page."""
        project = user_db.get_project(project_id, current_user.id)
        if not project:
            flash('Project not found.', 'error')
            return redirect(url_for('projects'))

        # Get sessions for this project
        all_sessions = user_db.get_user_sessions(current_user.id)
        user_project_sessions = [s for s in all_sessions if s['project_id'] == project_id]

        return render_template('sessions/project_sessions.html',
                               project=project,
                               sessions=user_project_sessions)

    @flask_app.route('/sessions/history')
    @login_required
    def sessions_history():
        """Sessions history page."""
        user_sessions = user_db.get_user_sessions(current_user.id)
        return render_template('sessions/history.html', sessions=user_sessions)

    # Code Generation Routes
    @flask_app.route('/code')
    @login_required
    def code_dashboard():
        """Code generation dashboard."""
        # Get all user's projects with their generations
        user_projects = user_db.get_user_projects(current_user.id)

        recent_generations = []
        for project in user_projects:
            project_generations = user_db.get_project_generations(project['id'], current_user.id)
            for gen in project_generations:
                gen['project_name'] = project['name']
                recent_generations.append(gen)

        # Sort by creation date, most recent first
        recent_generations.sort(key=lambda x: x['created_at'], reverse=True)
        recent_generations = recent_generations[:10]  # Show last 10

        return render_template('code.html',
                               projects=user_projects,
                               recent_generations=recent_generations)

    @flask_app.route('/projects/<project_id>/generate', methods=['GET', 'POST'])
    @login_required
    def new_generation(project_id):
        """Start new code generation."""
        project = user_db.get_project(project_id, current_user.id)
        if not project:
            flash('Project not found.', 'error')
            return redirect(url_for('projects'))

        form = CodeGenerationForm()

        if form.validate_on_submit():
            technology_stack = {
                'primary_language': form.primary_language.data,
                'frontend_framework': form.frontend_framework.data,
                'backend_framework': form.backend_framework.data,
                'database_type': form.database_type.data
            }

            user_generation_config = {
                'include_authentication': form.include_authentication.data,
                'include_api_docs': form.include_api_docs.data,
                'include_tests': form.include_tests.data,
                'include_docker': form.include_docker.data,
                'include_deployment': form.include_deployment.data,
                'additional_features': form.additional_features.data
            }

            generation_id = user_db.create_generation(
                project_id=project_id,
                generation_name=form.generation_name.data,
                architecture_pattern=form.architecture_pattern.data,
                generation_type=form.generation_type.data,
                technology_stack=technology_stack,
                generation_config=user_generation_config
            )

            if generation_id:
                # Mock file generation - in real implementation this would be AI-generated
                mock_files = [
                    ('src/app.py', 'main.py', 'python', 'Mock Flask application'),
                    ('src/models.py', 'models.py', 'python', 'Mock database models'),
                    ('tests/test_app.py', 'test_app.py', 'python', 'Mock unit tests'),
                    ('README.md', 'README.md', 'markdown', 'Mock project documentation'),
                    ('requirements.txt', 'requirements.txt', 'text', 'Mock dependencies')
                ]

                for file_path, file_name, file_type, content in mock_files:
                    user_db.add_generated_file(generation_id, file_path, file_name, file_type, content)

                # Update generation as completed
                user_db.update_generation(generation_id, current_user.id,
                                          status='completed', progress=100)

                flash(f'Code generation "{form.generation_name.data}" completed successfully!', 'success')
                return redirect(url_for('view_generation', generation_id=generation_id))
            else:
                flash('Error creating generation. Please try again.', 'error')

        return render_template('code/generate.html', form=form, project=project)

    @flask_app.route('/generations/<generation_id>')
    @login_required
    def view_generation(generation_id):
        """View code generation results."""
        generation = user_db.get_generation(generation_id, current_user.id)
        if not generation:
            flash('Generation not found.', 'error')
            return redirect(url_for('code_dashboard'))

        # Get project details
        project = user_db.get_project(generation['project_id'], current_user.id)
        if not project:
            flash('Associated project not found.', 'error')
            return redirect(url_for('code_dashboard'))

        files = generation.get('files', [])

        return render_template('code/viewer.html',
                               generation=generation,
                               project=project,
                               files=files)

    @flask_app.route('/generations/<generation_id>/download')
    @login_required
    def download_generation(generation_id):
        """Download generation files."""
        generation = user_db.get_generation(generation_id, current_user.id)
        if not generation:
            flash('Generation not found.', 'error')
            return redirect(url_for('code_dashboard'))

        # In a real implementation, this would create a ZIP file
        # For now, return a simple response
        flash('Download feature would create a ZIP file with all generated files.', 'info')
        return redirect(url_for('view_generation', generation_id=generation_id))

    @flask_app.route('/generations/<generation_id>/config', methods=['GET', 'POST'])
    @login_required
    def generation_config(generation_id):
        """Generation configuration page."""
        generation = user_db.get_generation(generation_id, current_user.id)
        if not generation:
            flash('Generation not found.', 'error')
            return redirect(url_for('code_dashboard'))

        form = GenerationConfigForm()

        if form.validate_on_submit():
            success = user_db.update_generation(
                generation_id=generation_id,
                user_id=current_user.id,
                generation_name=form.generation_name.data,
                status=form.status.data,
                progress=int(form.progress.data)
            )

            if success:
                flash('Generation updated successfully.', 'success')
                return redirect(url_for('view_generation', generation_id=generation_id))
            else:
                flash('Error updating generation. Please try again.', 'error')
        else:
            # Pre-populate form with current generation data
            form.generation_name.data = generation['generation_name']
            form.status.data = generation['status']
            form.progress.data = str(generation['progress'])

        return render_template('code/config.html', form=form, generation=generation)

    @flask_app.route('/generations/<generation_id>/delete', methods=['POST'])
    @login_required
    def delete_generation(generation_id):
        """Delete generation."""
        generation = user_db.get_generation(generation_id, current_user.id)
        if not generation:
            flash('Generation not found.', 'error')
            return redirect(url_for('code_dashboard'))

        if user_db.delete_generation(generation_id, current_user.id):
            flash(f'Generation "{generation["generation_name"]}" deleted successfully.', 'success')
        else:
            flash('Error deleting generation. Please try again.', 'error')

        return redirect(url_for('code_dashboard'))

    @flask_app.route('/projects/<project_id>/code')
    @login_required
    def project_code(project_id):
        """Project code generations page."""
        project = user_db.get_project(project_id, current_user.id)
        if not project:
            flash('Project not found.', 'error')
            return redirect(url_for('projects'))

        generations = user_db.get_project_generations(project_id, current_user.id)

        return render_template('code/project_code.html',
                               project=project,
                               generations=generations)

    @flask_app.route('/api/files/<file_id>')
    @login_required
    def get_file_content(file_id):
        """Get file content for code viewer."""
        # This would get file content by ID for the code viewer
        # For now, return mock content
        return jsonify({
            'content': '# Mock file content\n# This would contain actual generated code',
            'file_type': 'python'
        })

    @flask_app.route('/api/generations/<generation_id>/progress')
    @login_required
    def generation_progress(generation_id):
        """Get generation progress for real-time updates."""
        generation = user_db.get_generation(generation_id, current_user.id)
        if not generation:
            return jsonify({'error': 'Generation not found'}), 404

        return jsonify({
            'progress': generation['progress'],
            'status': generation['status'],
            'file_count': len(generation.get('files', []))
        })

    # Legacy/Compatibility Routes
    @flask_app.route('/api/health')
    def health():
        """Health check endpoint."""
        return jsonify({
            'status': 'healthy',
            'system_available': SYSTEM_AVAILABLE,
            'current_time': datetime.now().isoformat(),
            'app_version': '7.3.0'
        })

    @flask_app.route('/upload-document', methods=['POST'])
    @login_required
    def upload_document():
        """Handle document upload."""
        form = DocumentUploadForm()

        if form.validate_on_submit():
            try:
                file = form.file.data
                project_id = form.project_id.data or None

                # Generate secure filename
                filename = secure_filename(file.filename)
                if not filename:
                    return jsonify({
                        'success': False,
                        'message': 'Invalid filename'
                    }), 400

                # Save file
                file_path = os.path.join(flask_app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

                # TODO: Process document content (extract text, add to knowledge base)
                # For now, just return success

                return jsonify({
                    'success': True,
                    'message': f'Document "{filename}" uploaded successfully',
                    'data': {
                        'filename': filename,
                        'project_id': project_id,
                        'file_size': os.path.getsize(file_path)
                    }
                })

            except Exception as e:
                logger.error(f"File upload error: {e}")
                return jsonify({
                    'success': False,
                    'message': 'Upload failed. Please try again.'
                }), 500

        # Form validation failed
        errors = []
        for field, field_errors in form.errors.items():
            for error in field_errors:
                errors.append(f"{field}: {error}")

        return jsonify({
            'success': False,
            'message': 'Validation failed',
            'errors': errors
        }), 400

    logger.info("Flask application created successfully")

    @flask_app.route('/projects/new', methods=['GET', 'POST'])
    @login_required
    def new_project():
        """Create new project with wizard interface and templates."""
        form = ProjectForm()

        # Get current step (default to 0 for template selection)
        current_step = int(request.form.get('step', request.args.get('step', 0)))

        # Initialize wizard data in session if not exists
        if 'wizard_data' not in session:
            session['wizard_data'] = {}

        wizard_data = session['wizard_data']

        if request.method == 'POST':
            action = request.form.get('action')

            if action == 'back':
                # Go back to previous step
                current_step = max(0, current_step - 1)

            elif action == 'template_select':
                # Handle template selection from step 0
                template_id = request.form.get('template_id')

                if template_id == 'custom':
                    # Start from scratch - go to step 1
                    current_step = 1
                    wizard_data = {'template_id': 'custom'}
                else:
                    # Apply template and go to step 1
                    template = get_template_by_id(template_id)
                    if template:
                        wizard_data = apply_template_to_wizard_data(template_id, {})
                        current_step = 1
                    else:
                        flash('Invalid template selected.', 'error')

                session['wizard_data'] = wizard_data

            elif action == 'next':
                # Validate current step and advance
                step_valid = True

                if current_step == 1:
                    # Validate Step 1: Project Details
                    if form.name.validate(form) and form.project_type.validate(form):
                        wizard_data.update({
                            'name': form.name.data,
                            'description': form.description.data,
                            'project_type': form.project_type.data,
                            'status': form.status.data
                        })
                    else:
                        step_valid = False
                        flash('Please fill in all required fields.', 'error')

                elif current_step == 2:
                    # Validate Step 2: Framework Selection
                    wizard_data.update({
                        'framework': form.framework.data
                    })

                elif current_step == 3:
                    # Validate Step 3: Requirements
                    wizard_data.update({
                        'requirements': request.form.get('requirements', ''),
                        'estimated_hours': request.form.get('estimated_hours', ''),
                        'priority': request.form.get('priority', 'medium')
                    })

                if step_valid:
                    current_step = min(4, current_step + 1)

                session['wizard_data'] = wizard_data

            elif action == 'create':
                # Final step: Create the project
                if current_step == 4:
                    try:
                        # Create project with wizard data
                        project_id = user_db.create_project(
                            owner_id=current_user.id,
                            name=wizard_data.get('name', ''),
                            description=wizard_data.get('description', ''),
                            project_type=wizard_data.get('project_type', 'solo'),
                            framework=wizard_data.get('framework', '')
                        )

                        if project_id:
                            # Store additional wizard data if needed
                            additional_data = {
                                'requirements': wizard_data.get('requirements', ''),
                                'estimated_hours': wizard_data.get('estimated_hours', ''),
                                'priority': wizard_data.get('priority', 'medium'),
                                'template_id': wizard_data.get('template_id', 'custom'),
                                'template_name': wizard_data.get('template_name', ''),
                                'created_via': 'wizard'
                            }

                            # Clear wizard data from session
                            session.pop('wizard_data', None)

                            flash(f'Project "{wizard_data.get("name")}" created successfully!', 'success')
                            return redirect(url_for('project_detail', project_id=project_id))
                        else:
                            flash('Error creating project. Please try again.', 'error')

                    except Exception as e:
                        flash(f'Error creating project: {str(e)}', 'error')

        # GET request or form errors - show wizard
        else:
            # On GET request, reset wizard if starting fresh
            if current_step == 0 and not request.args.get('step'):
                session.pop('wizard_data', None)
                wizard_data = {}

        # Pre-populate form with wizard data for current step
        if current_step == 1 and wizard_data:
            form.name.data = wizard_data.get('name', '')
            form.description.data = wizard_data.get('description', '')
            form.project_type.data = wizard_data.get('project_type', 'solo')
            form.status.data = wizard_data.get('status', 'draft')
        elif current_step == 2 and wizard_data:
            form.framework.data = wizard_data.get('framework', '')

        # Get available templates for step 0
        available_templates = get_all_templates()

        return render_template('projects/wizard.html',
                               form=form,
                               current_step=current_step,
                               wizard_data=wizard_data,
                               available_templates=available_templates)

    # Optional: Add a route to clear wizard data if user cancels
    @flask_app.route('/projects/wizard/cancel', methods=['POST'])
    @login_required
    def cancel_wizard():
        """Cancel wizard and clear session data."""
        session.pop('wizard_data', None)
        flash('Project creation cancelled.', 'info')
        return redirect(url_for('projects'))

    # Optional: Add direct step navigation for completed steps
    @flask_app.route('/projects/new/<int:step>')
    @login_required
    def wizard_step(step):
        """Navigate directly to a specific wizard step."""
        if step < 1 or step > 4:
            return redirect(url_for('new_project'))

        # Only allow direct navigation if previous steps are completed
        wizard_data = session.get('wizard_data', {})

        if step > 1 and not wizard_data.get('name'):
            # Step 1 not completed, redirect to step 1
            return redirect(url_for('new_project', step=1))

        if step > 2 and not wizard_data.get('name'):
            # Previous steps not completed
            return redirect(url_for('new_project', step=1))

        return redirect(url_for('new_project', step=step))

    @flask_app.route('/sessions/<session_id>/response', methods=['POST'])
    @login_required
    def submit_response(session_id):
        """Handle session response submission."""
        user_session = user_db.get_session(session_id, current_user.id)
        if not user_session:
            return jsonify({'error': 'Session not found'}), 404

        data = request.get_json()
        message = data.get('message', '')

        if not message:
            return jsonify({'error': 'Message is required'}), 400

        return jsonify({
            'success': True,
            'response': f"Thank you for your message: {message}",
            'message_id': 'temp-id'
        })

    @flask_app.route('/sessions/<session_id>/export')
    @login_required
    def export_session(session_id):
        """Export session data."""
        user_session = user_db.get_session(session_id, current_user.id)
        if not user_session:
            flash('Session not found.', 'error')
            return redirect(url_for('sessions'))

        # For now, just return a simple text export
        from flask import make_response
        response = make_response(
            f"Session Export: {user_session['session_name']}\nCreated: {user_session['created_at']}\n")
        response.headers['Content-Disposition'] = f'attachment; filename=session_{session_id}.txt'
        response.headers['Content-Type'] = 'text/plain'
        return response

    @flask_app.route('/sessions/<session_id>/share')
    @login_required
    def share_session(session_id):
        """Generate shareable link for session."""
        user_session = user_db.get_session(session_id, current_user.id)
        if not user_session:
            return jsonify({'error': 'Session not found'}), 404

        # For now, just return the session URL
        share_url = url_for('session_detail', session_id=session_id, _external=True)
        return jsonify({'share_url': share_url})

    @flask_app.route('/debug/tables')
    @login_required
    def debug_tables():
        """Debug: Show database tables and structure"""
        import sqlite3
        try:
            user_db = get_user_db()
            print(f"🔍 DEBUG ROUTE using UserDB at: {user_db.db_path}")
            print(f"🔍 DEBUG ROUTE UserDB instance: {id(user_db)}")
            conn = sqlite3.connect(user_db.db_path)
            cursor = conn.cursor()

            # Get all tables
            print("🔍 Verifying tables...")
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = cursor.fetchall()
            print(f"📊 Tables found: {[t[0] for t in tables]}")

            result = "<h3>Database Tables:</h3><ul>"
            for table in tables:
                result += f"<li><strong>{table[0]}</strong></li>"

                # Get table schema
                cursor.execute(f"PRAGMA table_info({table[0]})")
                columns = cursor.fetchall()
                result += "<ul>"
                for col in columns:
                    result += f"<li>{col[1]} ({col[2]})</li>"
                result += "</ul>"

            result += "</ul>"
            conn.close()
            print("✅ Database initialization completed successfully")
            print(result)
            return result

        except Exception as e:
            return f"Error: {e}"

    @flask_app.route('/debug/db-path')
    @login_required
    def debug_db_path():
        return f"Database path: {user_db.db_path}<br>File exists: {os.path.exists(user_db.db_path)}"

    @flask_app.route('/debug/create-tables')
    @login_required
    def debug_create_tables():
        """Debug: Manually create tables and show result"""
        import sqlite3
        try:
            user_db = get_user_db()
            conn = sqlite3.connect(user_db.db_path)
            cursor = conn.cursor()

            # Try creating just the users table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS test_users (
                    id TEXT PRIMARY KEY,
                    username TEXT UNIQUE NOT NULL,
                    email TEXT,
                    created_at TEXT
                )
            ''')

            conn.commit()

            # Check if it was created
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='test_users'")
            result = cursor.fetchone()

            conn.close()

            if result:
                return f"✅ Table creation works! Created table: {result[0]}"
            else:
                return "❌ Table creation failed - no table found after creation"

        except Exception as e:
            return f"❌ Error during table creation: {e}"

    @flask_app.route('/debug/test-session')
    @login_required
    def debug_test_session():
        """Test session creation directly and show any errors"""
        try:
            user_db = get_user_db()

            # Test session creation with debug info
            print(f"🔍 Testing session creation...")
            print(f"🔍 Current user ID: {current_user.id}")
            print(f"🔍 UserDB instance: {id(user_db)}")
            print(f"🔍 Database path: {user_db.db_path}")

            session_id = user_db.create_session(
                owner_id=current_user.id,
                session_name="Debug Test Session",
                role="developer"
            )

            print(f"🔍 Session creation result: {session_id}")

            if session_id:
                return f"✅ SUCCESS: Session created with ID: {session_id}"
            else:
                return "❌ FAILED: Session creation returned None"

        except Exception as e:
            print(f"❌ DEBUG EXCEPTION: {e}")
            import traceback
            traceback.print_exc()
            return f"❌ EXCEPTION: {str(e)}"

    @flask_app.route('/debug/form-validation', methods=['GET', 'POST'])
    @login_required
    def debug_form_validation():
        """Debug form validation issues"""
        form = NewSessionForm()

        if request.method == 'POST':
            print(f"🔍 POST request received")
            print(f"🔍 Form data: {request.form}")
            print(f"🔍 Form validation result: {form.validate_on_submit()}")
            print(f"🔍 Form errors: {form.errors}")

            # Check individual field validation
            for field_name, field in form._fields.items():
                if field.errors:
                    print(f"🔍 Field '{field_name}' errors: {field.errors}")

        # Populate choices for dropdown
        user_projects = user_db.get_user_projects(current_user.id)
        form.existing_project.choices = [('', 'No Project')] + [
            (p['id'], p['name']) for p in user_projects
        ]

        return render_template('sessions/new.html', form=form, project=None)

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

    # Availability flags
    'FLASK_AVAILABLE',
    'SYSTEM_AVAILABLE',

    # User and Database classes
    'WorkingUser',
    'UserDB',

    # Forms
    'LoginForm',
    'RegisterForm',
    'ProjectForm',
    'EditProjectForm',
    'NewSessionForm',
    'SessionConfigForm',
    'QuestionForm',
    'AnswerForm',
    'CodeGenerationForm',
    'GenerationConfigForm',
    'FileViewerForm',
    'BatchActionForm',
    'SocraticSessionForm',
    'DocumentUploadForm',

    # Utility functions
    'api_response',
    'with_agent_orchestration',
]
