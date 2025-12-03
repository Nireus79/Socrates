"""
Project database for persistent storage in Socratic RAG System
"""

import os
import datetime
import pickle
import sqlite3
from typing import Dict, List, Optional
from dataclasses import asdict

from socratic_system.models import ProjectContext, User
from socratic_system.utils.datetime_helpers import serialize_datetime, deserialize_datetime


class ProjectDatabase:
    """SQLite database for storing projects and users"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for project metadata"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                project_id TEXT PRIMARY KEY,
                data BLOB,
                created_at TEXT,
                updated_at TEXT
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                passcode_hash TEXT,
                data BLOB,
                created_at TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def save_project(self, project: ProjectContext):
        """Save project to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        data = pickle.dumps(asdict(project))
        created_at_str = serialize_datetime(project.created_at)
        updated_at_str = serialize_datetime(project.updated_at)

        cursor.execute('''
            INSERT OR REPLACE INTO projects (project_id, data, created_at, updated_at)
            VALUES (?, ?, ?, ?)
        ''', (project.project_id, data, created_at_str, updated_at_str))

        conn.commit()
        conn.close()

    def load_project(self, project_id: str) -> Optional[ProjectContext]:
        """Load project from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT data FROM projects WHERE project_id = ?', (project_id,))
        result = cursor.fetchone()

        conn.close()

        if result:
            data = pickle.loads(result[0])
            # Convert datetime strings back to datetime objects if needed
            if isinstance(data.get('created_at'), str):
                data['created_at'] = deserialize_datetime(data['created_at'])
            if isinstance(data.get('updated_at'), str):
                data['updated_at'] = deserialize_datetime(data['updated_at'])
            return ProjectContext(**data)
        return None

    def get_user_projects(self, username: str, include_archived: bool = False) -> List[Dict]:
        """Get all projects for a user (as owner or collaborator)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT project_id, data FROM projects')
        results = cursor.fetchall()
        conn.close()

        projects = []
        for project_id, data in results:
            try:
                project_data = pickle.loads(data)

                # Handle datetime deserialization if needed
                if isinstance(project_data.get('updated_at'), str):
                    project_data['updated_at'] = deserialize_datetime(project_data['updated_at'])

                # Skip archived projects unless requested
                if project_data.get('is_archived', False) and not include_archived:
                    continue

                # Check if user is owner or collaborator
                if (project_data['owner'] == username or
                        username in project_data.get('collaborators', [])):
                    status = "archived" if project_data.get('is_archived', False) else "active"

                    projects.append({
                        'project_id': project_id,
                        'name': project_data['name'],
                        'phase': project_data['phase'],
                        'status': status,
                        'updated_at': project_data['updated_at'].strftime("%Y-%m-%d %H:%M:%S") if isinstance(
                            project_data['updated_at'], datetime.datetime) else str(project_data['updated_at'])
                    })
            except Exception as e:
                print(f"Warning: Could not load project {project_id}: {e}")

        return projects

    def save_user(self, user: User):
        """Save user to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        data = pickle.dumps(asdict(user))
        created_at_str = serialize_datetime(user.created_at)

        cursor.execute('''
            INSERT OR REPLACE INTO users (username, passcode_hash, data, created_at)
            VALUES (?, ?, ?, ?)
        ''', (user.username, user.passcode_hash, data, created_at_str))

        conn.commit()
        conn.close()

    def load_user(self, username: str) -> Optional[User]:
        """Load user from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT data FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()

        conn.close()

        if result:
            data = pickle.loads(result[0])
            # Convert datetime string back to datetime object if needed
            if isinstance(data.get('created_at'), str):
                data['created_at'] = deserialize_datetime(data['created_at'])
            return User(**data)
        return None

    def user_exists(self, username: str) -> bool:
        """Check if a user exists in the database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('SELECT username FROM users WHERE username = ?', (username,))
        result = cursor.fetchone()

        conn.close()
        return result is not None

    def archive_user(self, username: str, archive_projects: bool = True) -> bool:
        """Archive a user (soft delete)"""
        try:
            user = self.load_user(username)
            if not user:
                return False

            # Archive user
            user.is_archived = True
            user.archived_at = datetime.datetime.now()
            self.save_user(user)

            if archive_projects:
                # Archive all projects owned by this user
                conn = sqlite3.connect(self.db_path)
                cursor = conn.cursor()

                cursor.execute('SELECT project_id, data FROM projects')
                results = cursor.fetchall()

                for project_id, data in results:
                    try:
                        project_data = pickle.loads(data)
                        if project_data['owner'] == username and not project_data.get('is_archived', False):
                            # Archive this project
                            project_data['is_archived'] = True
                            project_data['archived_at'] = datetime.datetime.now()
                            updated_data = pickle.dumps(project_data)

                            cursor.execute('''
                                UPDATE projects SET data = ?, updated_at = ?
                                WHERE project_id = ?
                            ''', (updated_data, datetime.datetime.now().isoformat(), project_id))

                    except Exception as e:
                        print(f"Warning: Could not archive project {project_id}: {e}")

                conn.commit()
                conn.close()

            return True

        except Exception as e:
            print(f"Error archiving user: {e}")
            return False

    def restore_user(self, username: str) -> bool:
        """Restore an archived user"""
        try:
            user = self.load_user(username)
            if not user or not user.is_archived:
                return False

            user.is_archived = False
            user.archived_at = None
            self.save_user(user)
            return True

        except Exception as e:
            print(f"Error restoring user: {e}")
            return False

    def permanently_delete_user(self, username: str) -> bool:
        """Permanently delete a user and transfer their projects"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # First, handle projects owned by this user
            cursor.execute('SELECT project_id, data FROM projects')
            results = cursor.fetchall()

            projects_to_delete = []
            projects_to_transfer = []

            for project_id, data in results:
                try:
                    project_data = pickle.loads(data)
                    if project_data['owner'] == username:
                        if project_data.get('collaborators'):
                            # Transfer to first collaborator
                            new_owner = project_data['collaborators'][0]
                            project_data['owner'] = new_owner
                            project_data['collaborators'].remove(new_owner)
                            project_data['updated_at'] = datetime.datetime.now()

                            updated_data = pickle.dumps(project_data)
                            cursor.execute('''
                                UPDATE projects SET data = ?, updated_at = ?
                                WHERE project_id = ?
                            ''', (updated_data, project_data['updated_at'].isoformat(), project_id))

                            projects_to_transfer.append((project_id, new_owner))
                        else:
                            # No collaborators, mark for deletion
                            projects_to_delete.append(project_id)

                except Exception as e:
                    print(f"Warning: Could not process project {project_id}: {e}")

            # Delete projects with no collaborators
            for project_id in projects_to_delete:
                cursor.execute('DELETE FROM projects WHERE project_id = ?', (project_id,))

            # Delete the user
            cursor.execute('DELETE FROM users WHERE username = ?', (username,))

            conn.commit()
            conn.close()

            print(
                f"User {username} deleted. {len(projects_to_transfer)} projects transferred, {len(projects_to_delete)} projects deleted.")
            return True

        except Exception as e:
            print(f"Error permanently deleting user: {e}")
            return False

    def archive_project(self, project_id: str) -> bool:
        """Archive a project (soft delete)"""
        try:
            project = self.load_project(project_id)
            if not project:
                return False

            project.is_archived = True
            project.archived_at = datetime.datetime.now()
            project.updated_at = datetime.datetime.now()
            self.save_project(project)
            return True

        except Exception as e:
            print(f"Error archiving project: {e}")
            return False

    def restore_project(self, project_id: str) -> bool:
        """Restore an archived project"""
        try:
            project = self.load_project(project_id)
            if not project or not project.is_archived:
                return False

            project.is_archived = False
            project.archived_at = None
            project.updated_at = datetime.datetime.now()
            self.save_project(project)
            return True

        except Exception as e:
            print(f"Error restoring project: {e}")
            return False

    def permanently_delete_project(self, project_id: str) -> bool:
        """Permanently delete a project"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('DELETE FROM projects WHERE project_id = ?', (project_id,))
            conn.commit()
            conn.close()
            return True

        except Exception as e:
            print(f"Error permanently deleting project: {e}")
            return False

    def get_archived_items(self, item_type: str) -> List[Dict]:
        """Get all archived users or projects"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if item_type == 'users':
            cursor.execute('SELECT username, data FROM users')
            results = cursor.fetchall()

            archived_users = []
            for username, data in results:
                try:
                    user_data = pickle.loads(data)
                    if user_data.get('is_archived', False):
                        archived_users.append({
                            'username': username,
                            'archived_at': user_data.get('archived_at'),
                            'project_count': len(user_data.get('projects', []))
                        })
                except Exception as e:
                    print(f"Warning: Could not load user {username}: {e}")

            conn.close()
            return archived_users

        elif item_type == 'projects':
            cursor.execute('SELECT project_id, data FROM projects')
            results = cursor.fetchall()

            archived_projects = []
            for project_id, data in results:
                try:
                    project_data = pickle.loads(data)
                    if project_data.get('is_archived', False):
                        archived_projects.append({
                            'project_id': project_id,
                            'name': project_data['name'],
                            'owner': project_data['owner'],
                            'archived_at': project_data.get('archived_at')
                        })
                except Exception as e:
                    print(f"Warning: Could not load project {project_id}: {e}")

            conn.close()
            return archived_projects

        conn.close()
        return []
