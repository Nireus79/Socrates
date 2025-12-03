"""
Main application class for Socratic RAG System
"""

import os
import hashlib
import getpass
import datetime
from typing import Optional, Dict, Any
from colorama import Fore, Style

from socratic_system.models import User, ProjectContext
from socratic_system.orchestration import AgentOrchestrator

class SocraticRAGSystem:
    """Main application class for Socratic RAG System"""

    def __init__(self):
        self.orchestrator = None
        self.current_user = None
        self.current_project = None
        self.session_start = datetime.datetime.now()
        # self.setup_enhanced_database()

    def start(self):
        """Start the Socratic RAG System"""
        print(f"{Fore.CYAN}{Style.BRIGHT}")
        print("╔═══════════════════════════════════════════════╗")
        print("║        Enhanced Socratic RAG System           ║")
        print("║                Version 7.0                    ║")
        print("║Ουδέν οίδα, ούτε διδάσκω τι, αλλά διαπορώ μόνον║")
        print("╚═══════════════════════════════════════════════╝")
        print(f"{Style.RESET_ALL}")

        # Get API key
        api_key = self._get_api_key()
        if not api_key:
            print(f"{Fore.RED}No API key provided. Exiting...")
            return

        try:
            # Initialize orchestrator
            self.orchestrator = AgentOrchestrator(api_key)

            # Login or create user
            if not self._handle_user_authentication():
                return

            # Main loop
            self._main_loop()

        except Exception as e:
            print(f"{Fore.RED}System error: {e}")

    def _get_api_key(self) -> Optional[str]:
        """Get Claude API key from environment or user input"""
        api_key = os.getenv('API_KEY_CLAUDE')
        if not api_key:
            print(f"{Fore.YELLOW}Claude API key not found in environment.")
            api_key = getpass.getpass("Please enter your Claude API key: ")
        return api_key

    def _handle_user_authentication(self) -> bool:
        """Handle user login or registration"""
        while True:
            print(f"\n{Fore.CYAN}Authentication Options:")
            print("1. Login with existing account")
            print("2. Create new account")
            print("3. Exit")

            choice = input(f"{Fore.WHITE}Choose option (1-3): ").strip()

            if choice == '1':
                if self._login():
                    return True
            elif choice == '2':
                if self._create_account():
                    return True
            elif choice == '3':
                print("                 Thank you for using Socratic.")
                print("                           Goodbye!")
                print("..τω Ασκληπιώ οφείλομεν αλετρυόνα, απόδοτε και μη αμελήσετε..")
                return False
            else:
                print(f"{Fore.RED}Invalid choice. Please try again.")

    def _login(self) -> bool:
        """Handle user login"""
        username = input(f"{Fore.WHITE}Username: ").strip()
        if not username:
            print(f"{Fore.RED}Username cannot be empty.")
            return False

        passcode = input(f"{Fore.WHITE}Passcode: ").strip()
        if not passcode:
            print(f"{Fore.RED}Passcode cannot be empty.")
            return False

        # Load user from database
        user = self.orchestrator.database.load_user(username)
        if not user:
            print(f"{Fore.RED}User not found.")
            return False

        # Verify passcode
        passcode_hash = hashlib.sha256(passcode.encode()).hexdigest()
        if user.passcode_hash != passcode_hash:
            print(f"{Fore.RED}Invalid passcode.")
            return False

        self.current_user = user
        print(f"{Fore.GREEN}✓ Welcome back, {username}!")
        return True

    def _create_account(self) -> bool:
        """Handle account creation"""
        print(f"\n{Fore.CYAN}Create New Account")

        username = input(f"{Fore.WHITE}Username: ").strip()
        if not username:
            print(f"{Fore.RED}Username cannot be empty.")
            return False

        # Check if user already exists
        existing_user = self.orchestrator.database.load_user(username)
        if existing_user:
            print(f"{Fore.RED}Username already exists.")
            return False

        passcode = input(f"{Fore.WHITE}Passcode: ").strip()
        if not passcode:
            print(f"{Fore.RED}Passcode cannot be empty.")
            return False

        confirm_passcode = input(f"{Fore.WHITE}Confirm passcode: ").strip()
        if passcode != confirm_passcode:
            print(f"{Fore.RED}Passcodes do not match.")
            return False

        # Create user
        passcode_hash = hashlib.sha256(passcode.encode()).hexdigest()
        user = User(
            username=username,
            passcode_hash=passcode_hash,
            created_at=datetime.datetime.now(),
            projects=[]
        )

        self.orchestrator.database.save_user(user)
        self.current_user = user

        print(f"{Fore.GREEN}✓ Account created successfully! Welcome, {username}!")
        return True

    def _import_documents(self):
        """Import documents into knowledge base"""
        print(f"\n{Fore.CYAN}Document Import")

        print(f"\n{Fore.YELLOW}Options:")
        print("1. Import single file")
        print("2. Import directory")
        print("3. Back to main menu")

        choice = input(f"{Fore.WHITE}Choose option (1-3): ").strip()

        if choice == '1':
            self._import_single_file()
        elif choice == '2':
            self._import_directory_ui()
        elif choice == '3':
            return
        else:
            print(f"{Fore.RED}Invalid choice.")

    def _import_single_file(self):
        """Import a single file"""
        file_path = input(f"{Fore.WHITE}Enter file path: ").strip()
        if not file_path:
            print(f"{Fore.RED}File path cannot be empty.")
            return

        # Ask if they want to link to current project
        project_id = None
        if self.current_project:
            link_choice = input(f"{Fore.CYAN}Link to current project '{self.current_project.name}'? (y/n): ").lower()
            if link_choice == 'y':
                project_id = self.current_project.project_id

        print(f"{Fore.YELLOW}Processing file...")
        result = self.orchestrator.process_request('document_agent', {
            'action': 'import_file',
            'file_path': file_path,
            'project_id': project_id
        })

        if result['status'] == 'success':
            print(f"{Fore.GREEN}✓ Successfully imported '{result['file_name']}'")
            print(f"{Fore.WHITE}Added {result['entries_added']} knowledge entries")
        else:
            print(f"{Fore.RED}Error: {result['message']}")

    def _import_directory_ui(self):
        """Import all files from a directory"""
        directory_path = input(f"{Fore.WHITE}Enter directory path: ").strip()
        if not directory_path:
            print(f"{Fore.RED}Directory path cannot be empty.")
            return

        recursive_choice = input(f"{Fore.CYAN}Include subdirectories? (y/n): ").lower()
        recursive = recursive_choice == 'y'

        # Ask if they want to link to current project
        project_id = None
        if self.current_project:
            link_choice = input(f"{Fore.CYAN}Link to current project '{self.current_project.name}'? (y/n): ").lower()
            if link_choice == 'y':
                project_id = self.current_project.project_id

        print(f"{Fore.YELLOW}Processing directory...")
        result = self.orchestrator.process_request('document_agent', {
            'action': 'import_directory',
            'directory_path': directory_path,
            'project_id': project_id,
            'recursive': recursive
        })

        if result['status'] == 'success':
            print(f"{Fore.GREEN}✓ {result['message']}")
            summary = result['summary']
            print(f"{Fore.WHITE}Processed files: {len(summary['processed_files'])}")
            print(f"Failed files: {len(summary['failed_files'])}")
            print(f"Total entries added: {summary['total_entries']}")

            if summary['failed_files']:
                print(f"\n{Fore.YELLOW}Failed files:")
                for failed in summary['failed_files']:
                    print(f"  - {failed['file']}: {failed['error']}")
        else:
            print(f"{Fore.RED}Error: {result['message']}")

    def _account_management(self):
        """Account management menu"""
        while True:
            print(f"\n{Fore.CYAN}Account Management")
            print(f"{Fore.WHITE}Current User: {self.current_user.username}")

            print(f"\n{Fore.YELLOW}Options:")
            print("1. Archive my account (soft delete)")
            print("2. Permanently delete my account")
            print("3. View archived accounts (restore option)")
            print("4. Back to main menu")

            choice = input(f"{Fore.WHITE}Choose option (1-4): ").strip()

            if choice == '1':
                self._archive_current_account()
            elif choice == '2':
                self._delete_current_account()
            elif choice == '3':
                self._view_archived_accounts()
            elif choice == '4':
                break
            else:
                print(f"{Fore.RED}Invalid choice.")

    def _archive_current_account(self):
        """Archive current user account"""
        print(f"\n{Fore.YELLOW}⚠️  Account Archiving")
        print("This will:")
        print("• Archive your account (you can restore it later)")
        print("• Archive all projects you own")
        print("• Remove you from collaborations")
        print("• Keep all data for potential restoration")

        confirm = input(f"\n{Fore.RED}Are you sure? (yes/no): ").lower()
        if confirm != 'yes':
            print(f"{Fore.GREEN}Archiving cancelled.")
            return

        result = self.orchestrator.process_request('user_manager', {
            'action': 'archive_user',
            'username': self.current_user.username,
            'requester': self.current_user.username
        })

        if result['status'] == 'success':
            print(f"{Fore.GREEN}✓ {result['message']}")
            print("You will be logged out now.")
            self.current_user = None
            self.current_project = None
            input("Press Enter to continue...")
        else:
            print(f"{Fore.RED}Error: {result['message']}")

    def _delete_current_account(self):
        """Permanently delete current user account"""
        print(f"\n{Fore.RED}⚠️  PERMANENT ACCOUNT DELETION")
        print("This will:")
        print("• PERMANENTLY delete your account")
        print("• Transfer owned projects to collaborators")
        print("• Delete projects with no collaborators")
        print("• Remove all your data FOREVER")

        print(f"\n{Fore.YELLOW}This action CANNOT be undone!")

        confirm1 = input(f"\n{Fore.RED}Type 'I UNDERSTAND' to continue: ").strip()
        if confirm1 != 'I UNDERSTAND':
            print(f"{Fore.GREEN}Deletion cancelled.")
            return

        confirm2 = input(f"{Fore.RED}Type 'DELETE' to confirm permanent deletion: ").strip()
        if confirm2 != 'DELETE':
            print(f"{Fore.GREEN}Deletion cancelled.")
            return

        result = self.orchestrator.process_request('user_manager', {
            'action': 'delete_user_permanently',
            'username': self.current_user.username,
            'requester': self.current_user.username,
            'confirmation': 'DELETE'
        })

        if result['status'] == 'success':
            print(f"{Fore.GREEN}✓ {result['message']}")
            print("Account has been permanently deleted.")
            print("Goodbye.")
            self.current_user = None
            self.current_project = None
            input("Press Enter to exit...")
            exit()
        else:
            print(f"{Fore.RED}Error: {result['message']}")

    def _view_archived_accounts(self):
        """View and restore archived accounts"""
        result = self.orchestrator.process_request('user_manager', {
            'action': 'get_archived_users'
        })

        if result['status'] != 'success' or not result['archived_users']:
            print(f"{Fore.YELLOW}No archived accounts found.")
            return

        print(f"\n{Fore.CYAN}Archived Accounts:")
        archived_users = result['archived_users']

        for i, user_info in enumerate(archived_users, 1):
            archived_date = user_info.get('archived_at', 'Unknown')
            if isinstance(archived_date, str):
                try:
                    archived_date = datetime.datetime.fromisoformat(archived_date).strftime("%Y-%m-%d %H:%M")
                except:
                    pass

            print(f"{i}. {user_info['username']} (archived: {archived_date})")

        try:
            choice = input(
                f"\n{Fore.WHITE}Select account to restore (1-{len(archived_users)}, or 0 to cancel): ").strip()

            if choice == '0':
                return

            index = int(choice) - 1
            if 0 <= index < len(archived_users):
                username = archived_users[index]['username']

                confirm = input(f"{Fore.CYAN}Restore account '{username}'? (y/n): ").lower()
                if confirm == 'y':
                    result = self.orchestrator.process_request('user_manager', {
                        'action': 'restore_user',
                        'username': username
                    })

                    if result['status'] == 'success':
                        print(f"{Fore.GREEN}✓ Account '{username}' restored successfully!")
                    else:
                        print(f"{Fore.RED}Error: {result['message']}")
            else:
                print(f"{Fore.RED}Invalid selection.")

        except ValueError:
            print(f"{Fore.RED}Invalid input.")

    def _project_management(self):
        """Extended project management menu"""
        while True:
            print(f"\n{Fore.CYAN}Project Management")
            if self.current_project:
                status = "archived" if getattr(self.current_project, 'is_archived', False) else "active"
                print(f"{Fore.WHITE}Current Project: {self.current_project.name} ({status})")

            print(f"\n{Fore.YELLOW}Options:")
            print("1. List all projects")
            print("2. Archive current project")
            print("3. View archived projects")
            print("4. Permanently delete project")
            print("5. Back to main menu")

            choice = input(f"{Fore.WHITE}Choose option (1-5): ").strip()

            if choice == '1':
                self._list_all_projects()
            elif choice == '2':
                self._archive_current_project()
            elif choice == '3':
                self._view_archived_projects()
            elif choice == '4':
                self._delete_project_permanently_ui()
            elif choice == '5':
                break
            else:
                print(f"{Fore.RED}Invalid choice.")

    def _archive_current_project(self):
        """Archive current project"""
        if not self.current_project:
            print(f"{Fore.RED}No current project loaded.")
            return

        if self.current_user.username != self.current_project.owner:
            print(f"{Fore.RED}Only the project owner can archive projects.")
            return

        print(f"\n{Fore.YELLOW}Archive project '{self.current_project.name}'?")
        print("This will hide it from normal view but preserve all data.")

        confirm = input(f"{Fore.CYAN}Continue? (y/n): ").lower()
        if confirm != 'y':
            return

        result = self.orchestrator.process_request('project_manager', {
            'action': 'archive_project',
            'project_id': self.current_project.project_id,
            'requester': self.current_user.username
        })

        if result['status'] == 'success':
            print(f"{Fore.GREEN}✓ {result['message']}")
            self.current_project = None
        else:
            print(f"{Fore.RED}Error: {result['message']}")

    def _view_archived_projects(self):
        """View and restore archived projects"""
        result = self.orchestrator.process_request('project_manager', {
            'action': 'get_archived_projects'
        })

        if result['status'] != 'success' or not result['archived_projects']:
            print(f"{Fore.YELLOW}No archived projects found.")
            return

        print(f"\n{Fore.CYAN}Archived Projects:")
        archived_projects = result['archived_projects']

        for i, project_info in enumerate(archived_projects, 1):
            archived_date = project_info.get('archived_at', 'Unknown')
            if isinstance(archived_date, str):
                try:
                    archived_date = datetime.datetime.fromisoformat(archived_date).strftime("%Y-%m-%d %H:%M")
                except:
                    pass

            print(f"{i}. {project_info['name']} by {project_info['owner']} (archived: {archived_date})")

        try:
            choice = input(
                f"\n{Fore.WHITE}Select project to restore (1-{len(archived_projects)}, or 0 to cancel): ").strip()

            if choice == '0':
                return

            index = int(choice) - 1
            if 0 <= index < len(archived_projects):
                project = archived_projects[index]

                # Check if user has permission
                if (self.current_user.username != project['owner']):
                    print(f"{Fore.RED}Only the project owner can restore projects.")
                    return

                confirm = input(f"{Fore.CYAN}Restore project '{project['name']}'? (y/n): ").lower()
                if confirm == 'y':
                    result = self.orchestrator.process_request('project_manager', {
                        'action': 'restore_project',
                        'project_id': project['project_id'],
                        'requester': self.current_user.username
                    })

                    if result['status'] == 'success':
                        print(f"{Fore.GREEN}✓ Project '{project['name']}' restored successfully!")
                    else:
                        print(f"{Fore.RED}Error: {result['message']}")
            else:
                print(f"{Fore.RED}Invalid selection.")

        except ValueError:
            print(f"{Fore.RED}Invalid input.")

    def _list_all_projects(self):
        """List all projects including archived ones"""
        result = self.orchestrator.process_request('project_manager', {
            'action': 'list_projects',
            'username': self.current_user.username
        })

        if result['status'] != 'success' or not result['projects']:
            print(f"{Fore.YELLOW}No projects found.")
            return

        print(f"\n{Fore.CYAN}All Your Projects:")
        for project in result['projects']:
            status_color = Fore.YELLOW if project.get('status') == 'archived' else Fore.WHITE
            print(
                f"{status_color}• {project['name']} ({project['phase']}) - {project['status']} - {project['updated_at']}")

    def _delete_project_permanently_ui(self):
        """UI for permanent project deletion"""
        # Get user's projects including archived
        result = self.orchestrator.process_request('project_manager', {
            'action': 'list_projects',
            'username': self.current_user.username
        })

        if result['status'] != 'success' or not result['projects']:
            print(f"{Fore.YELLOW}No projects found.")
            return

        # Filter to only owned projects
        owned_projects = []
        for project_info in result['projects']:
            # Load full project to check ownership
            project = self.orchestrator.database.load_project(project_info['project_id'])
            if project and project.owner == self.current_user.username:
                owned_projects.append({
                    'project_id': project.project_id,
                    'name': project.name,
                    'status': project_info.get('status', 'active'),
                    'collaborator_count': len(project.collaborators)
                })

        if not owned_projects:
            print(f"{Fore.YELLOW}You don't own any projects.")
            return

        print(f"\n{Fore.RED}⚠️  PERMANENT PROJECT DELETION")
        print("Select a project to permanently delete:")

        for i, project in enumerate(owned_projects, 1):
            status_indicator = "🗄️" if project['status'] == 'archived' else "📁"
            collab_text = f"({project['collaborator_count']} collaborators)" if project[
                                                                                    'collaborator_count'] > 0 else "(no collaborators)"
            print(f"{i}. {status_indicator} {project['name']} {collab_text}")

        try:
            choice = input(f"\n{Fore.WHITE}Select project (1-{len(owned_projects)}, or 0 to cancel): ").strip()

            if choice == '0':
                return

            index = int(choice) - 1
            if 0 <= index < len(owned_projects):
                project = owned_projects[index]

                print(f"\n{Fore.RED}⚠️  You are about to PERMANENTLY DELETE:")
                print(f"Project: {project['name']}")
                print(f"Status: {project['status']}")
                print(f"Collaborators: {project['collaborator_count']}")
                print(f"\n{Fore.YELLOW}This action CANNOT be undone!")
                print("All conversation history, context, and project data will be lost forever.")

                confirm1 = input(f"\n{Fore.RED}Type the project name to continue: ").strip()
                if confirm1 != project['name']:
                    print(f"{Fore.GREEN}Deletion cancelled.")
                    return

                confirm2 = input(f"{Fore.RED}Type 'DELETE' to confirm permanent deletion: ").strip()
                if confirm2 != 'DELETE':
                    print(f"{Fore.GREEN}Deletion cancelled.")
                    return

                result = self.orchestrator.process_request('project_manager', {
                    'action': 'delete_project_permanently',
                    'project_id': project['project_id'],
                    'requester': self.current_user.username,
                    'confirmation': 'DELETE'
                })

                if result['status'] == 'success':
                    print(f"{Fore.GREEN}✓ {result['message']}")

                    # Clear current project if it was the deleted one
                    if (self.current_project and
                            self.current_project.project_id == project['project_id']):
                        self.current_project = None
                else:
                    print(f"{Fore.RED}Error: {result['message']}")
            else:
                print(f"{Fore.RED}Invalid selection.")

        except ValueError:
            print(f"{Fore.RED}Invalid input.")

    # def add_project_note(self, note_type, title, content):
    #     """Add a note to the current project"""
    #     if not self.current_project:
    #         return False
    #
    #     try:
    #         cursor = self.conn.cursor()
    #         cursor.execute("""
    #             INSERT INTO project_notes (project_name, note_type, title, content)
    #             VALUES (?, ?, ?, ?)
    #         """, (self.current_project, note_type, title, content))
    #         self.conn.commit()
    #         return True
    #     except Exception as e:
    #         print(f"Error adding note: {e}")
    #         return False
    #
    # def update_project_progress(self, percentage):
    #     """Update project progress percentage"""
    #     if not self.current_project:
    #         return False
    #
    #     try:
    #         cursor = self.conn.cursor()
    #         cursor.execute("""
    #             UPDATE projects
    #             SET progress_percentage = ?, updated_at = CURRENT_TIMESTAMP
    #             WHERE name = ?
    #         """, (percentage, self.current_project))
    #         self.conn.commit()
    #         return True
    #     except Exception as e:
    #         print(f"Error updating progress: {e}")
    #         return False
    #
    # def set_project_status(self, status):
    #     """Update project status (active, completed, on-hold, archived)"""
    #     if not self.current_project:
    #         return False
    #
    #     valid_statuses = ['active', 'completed', 'on-hold', 'archived']
    #     if status not in valid_statuses:
    #         print(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")
    #         return False
    #
    #     try:
    #         cursor = self.conn.cursor()
    #         cursor.execute("""
    #             UPDATE projects
    #             SET status = ?, updated_at = CURRENT_TIMESTAMP
    #             WHERE name = ?
    #         """, (status, self.current_project))
    #         self.conn.commit()
    #         return True
    #     except Exception as e:
    #         print(f"Error updating status: {e}")
    #         return False
    #
    # def generate_conversation_summary(self, limit=10):
    #     """Generate a summary of recent conversations using AI"""
    #     if not self.current_project:
    #         return None
    #
    #     try:
    #         cursor = self.conn.cursor()
    #         cursor.execute("""
    #             SELECT role, content FROM conversations
    #             WHERE project_name = ?
    #             ORDER BY timestamp DESC LIMIT ?
    #         """, (self.current_project, limit))
    #
    #         conversations = cursor.fetchall()
    #         if not conversations:
    #             return "No conversations found."
    #
    #         # Format conversations for summarization
    #         conv_text = ""
    #         for role, content in reversed(conversations):  # Reverse to get chronological order
    #             conv_text += f"{role.upper()}: {content}\n\n"
    #
    #         # If you have access to an AI model, you can generate a summary here
    #         # For now, return a simple truncated version
    #         if len(conv_text) > 500:
    #             return conv_text[:500] + "...\n\n[Summary truncated - full conversation history available in exports]"
    #
    #         return conv_text
    #
    #     except Exception as e:
    #         print(f"Error generating summary: {e}")
    #         return None
    #
    # def search_project_conversations(self, query):
    #     """Search through project conversations"""
    #     if not self.current_project:
    #         return []
    #
    #     try:
    #         cursor = self.conn.cursor()
    #         cursor.execute("""
    #             SELECT timestamp, role, content FROM conversations
    #             WHERE project_name = ? AND content LIKE ?
    #             ORDER BY timestamp DESC
    #         """, (self.current_project, f"%{query}%"))
    #
    #         results = cursor.fetchall()
    #         return results
    #
    #     except Exception as e:
    #         print(f"Error searching conversations: {e}")
    #         return []
    #
    # def get_project_statistics(self):
    #     """Get comprehensive project statistics"""
    #     if not self.current_project:
    #         return None
    #
    #     try:
    #         cursor = self.conn.cursor()
    #         stats = {}
    #
    #         # Basic counts
    #         cursor.execute("SELECT COUNT(*) FROM conversations WHERE project_name = ?", (self.current_project,))
    #         stats['total_conversations'] = cursor.fetchone()[0]
    #
    #         cursor.execute("SELECT COUNT(*) FROM knowledge_base WHERE project_name = ?", (self.current_project,))
    #         stats['knowledge_base_entries'] = cursor.fetchone()[0]
    #
    #         # Date range
    #         cursor.execute("""
    #             SELECT MIN(timestamp), MAX(timestamp)
    #             FROM conversations WHERE project_name = ?
    #         """, (self.current_project,))
    #         min_date, max_date = cursor.fetchone()
    #         stats['date_range'] = {'start': min_date, 'end': max_date}
    #
    #         # Activity by day of week
    #         cursor.execute("""
    #             SELECT strftime('%w', timestamp) as day_of_week, COUNT(*)
    #             FROM conversations WHERE project_name = ?
    #             GROUP BY strftime('%w', timestamp)
    #         """, (self.current_project,))
    #         stats['activity_by_weekday'] = dict(cursor.fetchall())
    #
    #         return stats
    #
    #     except Exception as e:
    #         print(f"Error getting statistics: {e}")
    #         return None

    def _main_loop(self):
        """Main application loop"""
        while True:
            try:
                print(f"\n{Fore.CYAN}═" * 5)
                print(f"{Fore.CYAN}{Style.BRIGHT}Main Menu")
                print(f"{Fore.WHITE}Current User: {self.current_user.username}")
                if self.current_project:
                    print(f"Current Project: {self.current_project.name} ({self.current_project.phase})")

                print(f"\n{Fore.YELLOW}Options:")
                print("1. Create new project")
                print("2. Load existing project")
                print("3. Continue current project")
                print("4. Generate code")
                print("5. Manage collaborators")
                print("6. Import documents")
                print("7. Project management (archive/delete)")
                print("8. Account management (archive/delete)")
                print("9. View system status")
                print("10. Switch user")
                print("11. Exit")

                choice = input(f"{Fore.WHITE}Choose option (1-11): ").strip()

                if choice == '1':
                    self._create_project()
                elif choice == '2':
                    self._load_project()
                elif choice == '3':
                    if self.current_project:
                        # Check if project is archived
                        if getattr(self.current_project, 'is_archived', False):
                            print(f"{Fore.YELLOW}This project is archived. Restore it first in Project Management.")
                        else:
                            self._continue_project()
                    else:
                        print(f"{Fore.RED}No current project loaded.")
                elif choice == '4':
                    if self.current_project:
                        if getattr(self.current_project, 'is_archived', False):
                            print(f"{Fore.YELLOW}Cannot generate code for archived project. Restore it first.")
                        else:
                            self._generate_code()
                    else:
                        print(f"{Fore.RED}No current project loaded.")
                elif choice == '5':
                    if self.current_project:
                        if getattr(self.current_project, 'is_archived', False):
                            print(f"{Fore.YELLOW}Cannot manage collaborators for archived project. Restore it first.")
                        else:
                            self._manage_collaborators()
                    else:
                        print(f"{Fore.RED}No current project loaded.")
                elif choice == '6':
                    self._import_documents()
                elif choice == '7':  # MODIFY THIS
                    self._project_management()
                elif choice == '8':  # ADD THIS
                    self._account_management()
                elif choice == '9':
                    self._show_system_status()
                elif choice == '10':
                    if self._handle_user_authentication():
                        self.current_project = None
                elif choice == '11':
                    print(f"{Fore.GREEN}           Thank you for using Socratic RAG System")
                    print(f"{Fore.GREEN}..τω Ασκληπιώ οφείλομεν αλετρυόνα, απόδοτε και μη αμελήσετε..")
                    break
                else:
                    print(f"{Fore.RED}Invalid choice. Please try again.")

            except KeyboardInterrupt:
                print(f"\n{Fore.YELLOW}Use option 11 to exit properly.")
            except Exception as e:
                print(f"{Fore.RED}Error: {e}")

    def _create_project(self):
        """Create a new project"""
        print(f"\n{Fore.CYAN}Create New Project")

        project_name = input(f"{Fore.WHITE}Project name: ").strip()
        if not project_name:
            print(f"{Fore.RED}Project name cannot be empty.")
            return

        # Create project using orchestrator
        result = self.orchestrator.process_request('project_manager', {
            'action': 'create_project',
            'project_name': project_name,
            'owner': self.current_user.username
        })

        if result['status'] == 'success':
            self.current_project = result['project']
            print(f"{Fore.GREEN}✓ Project '{project_name}' created successfully!")
            self._continue_project()
        else:
            print(f"{Fore.RED}Error creating project: {result['message']}")

    def _load_project(self):
        """Load an existing project"""
        # Get user's projects including archived
        result = self.orchestrator.process_request('project_manager', {
            'action': 'list_projects',
            'username': self.current_user.username
        })

        if result['status'] != 'success' or not result['projects']:
            print(f"{Fore.YELLOW}No projects found.")
            return

        # Separate active and archived projects
        active_projects = [p for p in result['projects'] if p.get('status') != 'archived']
        archived_projects = [p for p in result['projects'] if p.get('status') == 'archived']

        print(f"\n{Fore.CYAN}Your Projects:")

        all_projects = []

        if active_projects:
            print(f"{Fore.GREEN}Active Projects:")
            for project in active_projects:
                all_projects.append(project)
                print(f"{len(all_projects)}. 📁 {project['name']} ({project['phase']}) - {project['updated_at']}")

        if archived_projects:
            print(f"{Fore.YELLOW}Archived Projects:")
            for project in archived_projects:
                all_projects.append(project)
                print(f"{len(all_projects)}. 🗄️ {project['name']} ({project['phase']}) - {project['updated_at']}")

        try:
            choice = int(input(f"{Fore.WHITE}Select project (1-{len(all_projects)}): ")) - 1
            if 0 <= choice < len(all_projects):
                project_info = all_projects[choice]
                project_id = project_info['project_id']

                # Load project
                result = self.orchestrator.process_request('project_manager', {
                    'action': 'load_project',
                    'project_id': project_id
                })

                if result['status'] == 'success':
                    self.current_project = result['project']

                    if getattr(self.current_project, 'is_archived', False):
                        print(f"{Fore.YELLOW}✓ Archived project loaded successfully!")
                        print(f"{Fore.YELLOW}Note: This project is archived. Some features may be limited.")
                    else:
                        print(f"{Fore.GREEN}✓ Project loaded successfully!")
                else:
                    print(f"{Fore.RED}Error loading project: {result['message']}")
            else:
                print(f"{Fore.RED}Invalid selection.")
        except ValueError:
            print(f"{Fore.RED}Invalid input.")

    def _continue_project(self):
        """Continue working on current project"""
        if not self.current_project:
            return

        print(f"\n{Fore.CYAN}Socratic Guidance Session")
        print(f"{Fore.WHITE}Project: {self.current_project.name}")
        print(f"Phase: {self.current_project.phase}")

        while True:
            # Generate question first
            question_result = self.orchestrator.process_request('socratic_counselor', {
                'action': 'generate_question',
                'project': self.current_project
            })

            if question_result['status'] != 'success':
                print(f"{Fore.RED}Error generating question: {question_result.get('message', 'Unknown error')}")
                break

            question = question_result['question']
            print(f"\n{Fore.BLUE}🤔 {question}")

            # Get user response
            print(
                f"{Fore.YELLOW}Your response (type 'done' to finish, 'advance' to move to next phase, 'help' for "
                f"suggestions):")
            response = input(f"{Fore.WHITE}> ").strip()

            if response.lower() == 'done':
                break
            elif response.lower() == 'advance':
                result = self.orchestrator.process_request('socratic_counselor', {
                    'action': 'advance_phase',
                    'project': self.current_project
                })
                if result['status'] == 'success':
                    print(f"{Fore.GREEN}✓ Advanced to {result['new_phase']} phase!")
                continue
            elif response.lower() in ['help', 'suggestions', 'options', 'hint']:
                # Generate suggestions automatically
                suggestions = self.orchestrator.claude_client.generate_suggestions(question, self.current_project)
                print(f"\n{Fore.MAGENTA}💡 {suggestions}")
                print(f"{Fore.YELLOW}Now, would you like to try answering the question?")
                continue
            elif not response:
                continue

            # Process the user's response
            result = self.orchestrator.process_request('socratic_counselor', {
                'action': 'process_response',
                'project': self.current_project,
                'response': response,
                'current_user': self.current_user.username
            })

            if result['status'] == 'success':
                if result.get('conflicts_pending'):
                    print(f"{Fore.YELLOW}⚠️  Some specifications were not added due to conflicts")
                elif result.get('insights'):
                    print(f"{Fore.GREEN}✓ Insights captured and integrated!")

                # Save the updated project
                save_result = self.orchestrator.process_request('project_manager', {
                    'action': 'save_project',
                    'project': self.current_project
                })
            else:
                print(f"{Fore.RED}Error processing response: {result.get('message', 'Unknown error')}")

    def _generate_code(self):
        """Generate code for current project"""
        if not self.current_project:
            return

        print(f"\n{Fore.CYAN}Generating Code...")

        result = self.orchestrator.process_request('code_generator', {
            'action': 'generate_script',
            'project': self.current_project
        })

        if result['status'] == 'success':
            script = result['script']
            print(f"\n{Fore.GREEN}✓ Code Generated Successfully!")
            print(f"{Fore.YELLOW}{'=' * 5}")
            print(f"{Fore.WHITE}{script}")
            print(f"{Fore.YELLOW}{'=' * 5}")

            # Ask if user wants documentation
            doc_choice = input(f"\n{Fore.CYAN}Generate documentation? (y/n): ").lower()
            if doc_choice == 'y':
                doc_result = self.orchestrator.process_request('code_generator', {
                    'action': 'generate_documentation',
                    'project': self.current_project,
                    'script': script
                })

                if doc_result['status'] == 'success':
                    print(f"\n{Fore.GREEN}✓ Documentation Generated!")
                    print(f"{Fore.YELLOW}{'=' * 5}")
                    print(f"{Fore.WHITE}{doc_result['documentation']}")
                    print(f"{Fore.YELLOW}{'=' * 5}")
        else:
            print(f"{Fore.RED}Error generating code: {result['message']}")

    def _show_system_status(self):
        """Show system status and statistics"""
        print(f"\n{Fore.CYAN}System Status")

        # Get system stats
        result = self.orchestrator.process_request('system_monitor', {
            'action': 'get_stats'
        })

        if result['status'] == 'success':
            stats = result
            print(f"{Fore.WHITE}Total Tokens Used: {stats['total_tokens']}")
            print(f"Estimated Cost: ${stats['total_cost']:.4f}")
            print(f"API Calls Made: {stats['api_calls']}")
            print(f"Connection Status: {'✓' if stats['connection_status'] else '✗'}")

        # Check for warnings
        result = self.orchestrator.process_request('system_monitor', {
            'action': 'check_limits'
        })

        if result['status'] == 'success' and result['warnings']:
            print(f"\n{Fore.YELLOW}Warnings:")
            for warning in result['warnings']:
                print(f"⚠ {warning}")

    def _manage_collaborators(self):
        """Manage project collaborators"""
        if not self.current_project:
            print(f"{Fore.RED}No current project loaded.")
            return

        while True:
            print(f"\n{Fore.CYAN}Collaborator Management")
            print(f"{Fore.WHITE}Project: {self.current_project.name}")

            # Show current collaborators
            result = self.orchestrator.process_request('project_manager', {
                'action': 'list_collaborators',
                'project': self.current_project
            })

            if result['status'] == 'success':
                print(f"\n{Fore.YELLOW}Current Team:")
                for member in result['collaborators']:
                    role_color = Fore.GREEN if member['role'] == 'owner' else Fore.WHITE
                    print(f"{role_color}  • {member['username']} ({member['role']})")

            print(f"\n{Fore.YELLOW}Options:")
            print("1. Add collaborator")
            print("2. Remove collaborator")
            print("3. Back to main menu")

            choice = input(f"{Fore.WHITE}Choose option (1-3): ").strip()

            if choice == '1':
                self._add_collaborator_ui()
            elif choice == '2':
                self._remove_collaborator_ui()
            elif choice == '3':
                break
            else:
                print(f"{Fore.RED}Invalid choice. Please try again.")

    def _add_collaborator_ui(self):
        """UI for adding collaborators"""
        # Only owner can add collaborators
        if self.current_user.username != self.current_project.owner:
            print(f"{Fore.RED}Only the project owner can add collaborators.")
            return

        username = input(f"{Fore.WHITE}Username to add: ").strip()
        if not username:
            print(f"{Fore.RED}Username cannot be empty.")
            return

        # Check if user exists
        if not self.orchestrator.database.user_exists(username):
            print(f"{Fore.RED}User '{username}' does not exist in the system.")
            return

        # Check if already owner
        if username == self.current_project.owner:
            print(f"{Fore.RED}User is already the project owner.")
            return

        # Add collaborator
        result = self.orchestrator.process_request('project_manager', {
            'action': 'add_collaborator',
            'project': self.current_project,
            'username': username
        })

        if result['status'] == 'success':
            print(f"{Fore.GREEN}✓ Added '{username}' as collaborator!")
        else:
            print(f"{Fore.RED}Error: {result['message']}")

    def _remove_collaborator_ui(self):
        """UI for removing collaborators"""
        # Only owner can remove collaborators
        if self.current_user.username != self.current_project.owner:
            print(f"{Fore.RED}Only the project owner can remove collaborators.")
            return

        if not self.current_project.collaborators:
            print(f"{Fore.YELLOW}No collaborators to remove.")
            return

        print(f"\n{Fore.YELLOW}Current Collaborators:")
        for i, collaborator in enumerate(self.current_project.collaborators, 1):
            print(f"{i}. {collaborator}")

        try:
            choice = int(
                input(f"{Fore.WHITE}Select collaborator to remove (1-{len(self.current_project.collaborators)}): ")) - 1
            if 0 <= choice < len(self.current_project.collaborators):
                username = self.current_project.collaborators[choice]

                confirm = input(f"{Fore.YELLOW}Remove '{username}'? (y/n): ").lower()
                if confirm == 'y':
                    result = self.orchestrator.process_request('project_manager', {
                        'action': 'remove_collaborator',
                        'project': self.current_project,
                        'username': username,
                        'requester': self.current_user.username
                    })

                    if result['status'] == 'success':
                        print(f"{Fore.GREEN}✓ Removed '{username}' from project!")
                    else:
                        print(f"{Fore.RED}Error: {result['message']}")
            else:
                print(f"{Fore.RED}Invalid selection.")
        except ValueError:
            print(f"{Fore.RED}Invalid input.")


