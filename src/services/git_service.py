"""
Git Service - Git Repository Operations and Version Control
==========================================================

Provides Git operations for the Socratic RAG Enhanced system.
Handles repository management, version control, branching, and collaboration features.

Features:
- Repository initialization and management
- Branch management and workflows
- Commit operations with automated messages
- Remote repository operations
- File tracking and status monitoring
- Git workflow automation
- Integration with code generation pipeline
"""

import logging
import subprocess
import re
import shutil
from dataclasses import dataclass
from typing import Dict, Any, List, Optional, Union, Tuple
from datetime import datetime
from pathlib import Path

try:
    import git
    from git import Repo, InvalidGitRepositoryError, GitCommandError, Actor

    GIT_PYTHON_AVAILABLE = True
except ImportError:
    GIT_PYTHON_AVAILABLE = False
    git = None
    Repo = None
    InvalidGitRepositoryError = Exception
    GitCommandError = Exception
    Actor = None

from ..core import SocraticException

logger = logging.getLogger(__name__)


@dataclass
class GitStatus:
    """Git repository status information."""
    branch: str
    is_dirty: bool
    untracked_files: List[str]
    modified_files: List[str]
    staged_files: List[str]
    commits_ahead: int = 0
    commits_behind: int = 0
    remote_url: Optional[str] = None


@dataclass
class GitCommit:
    """Git commit information."""
    hash: str
    short_hash: str
    message: str
    author: str
    email: str
    date: datetime
    files_changed: List[str]


@dataclass
class GitBranch:
    """Git branch information."""
    name: str
    is_current: bool
    is_remote: bool
    last_commit_hash: str
    last_commit_date: datetime


@dataclass
class GitRemote:
    """Git remote information."""
    name: str
    url: str
    fetch_url: str
    push_url: str


@dataclass
class RepositoryInfo:
    """Information about a Git repository."""
    url: str
    name: str
    owner: str
    platform: str  # 'github', 'gitlab', 'bitbucket', 'other'
    is_private: bool = False
    default_branch: str = 'main'
    description: Optional[str] = None
    language: Optional[str] = None
    stars: int = 0
    forks: int = 0


@dataclass
class CloneResult:
    """Result of repository clone operation."""
    success: bool
    local_path: str
    repository_info: Optional[RepositoryInfo] = None
    error: Optional[str] = None
    file_count: int = 0
    total_size_bytes: int = 0
    branches: List[str] = None

    def __post_init__(self):
        if self.branches is None:
            self.branches = []


class GitServiceError(SocraticException):
    """Git service specific exceptions."""
    pass


class GitService:
    """
    Git repository management service.

    Provides methods for:
    - Repository initialization and management
    - Branch operations and workflows
    - Commit operations with automated messages
    - Remote repository management
    - File tracking and status monitoring
    - Integration with code generation
    """

    def __init__(self):
        # Lazy load config to avoid circular imports
        try:
            from src import get_config
            self.config = get_config()
        except (ImportError, AttributeError):
            self.config = None
        self.git_service_config = self.config.get('services', {}).get('<service>', {}) if self.config else {}

        if not GIT_PYTHON_AVAILABLE:
            logger.warning("GitPython not available. Using command line git fallback.")

        # Configuration
        self.git_config = self.config.get('services', {}).get('git', {}) if self.config else {}
        self.default_author_name = self.git_config.get('author_name', 'Socratic RAG Enhanced')
        self.default_author_email = self.git_config.get('author_email', 'socratic@example.com')
        self.auto_commit = self.git_config.get('auto_commit', True)
        self.auto_push = self.git_config.get('auto_push', False)
        self.default_branch = self.git_config.get('default_branch', 'main')
        self.gitignore_templates = self.git_config.get('gitignore_templates', {})

        logger.info("Git service initialized")

    def _run_git_command(self, command: List[str], cwd: str) -> Tuple[str, str, int]:
        """Run a git command and return output."""
        try:
            result = subprocess.run(
                ['git'] + command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=30
            )
            return result.stdout.strip(), result.stderr.strip(), result.returncode
        except subprocess.TimeoutExpired:
            raise GitServiceError("Git command timed out")
        except FileNotFoundError:
            raise GitServiceError("Git executable not found. Please install Git.")

    def _check_git_available(self) -> bool:
        """Check if git is available."""
        try:
            self._run_git_command(['--version'], '.')
            return True
        except GitServiceError:
            return False

    def initialize_repository(
            self,
            path: str,
            initial_branch: Optional[str] = None,
            create_gitignore: bool = True,
            gitignore_type: str = 'python'
    ) -> bool:
        """
        Initialize a new Git repository.

        Args:
            path: Path to initialize repository
            initial_branch: Initial branch name (defaults to configured default)
            create_gitignore: Whether to create a .gitignore file
            gitignore_type: Type of .gitignore template to use

        Returns:
            True if successful, False otherwise
        """
        try:
            path = Path(path).resolve()
            path.mkdir(parents=True, exist_ok=True)

            if GIT_PYTHON_AVAILABLE:
                logger.info(f"Initialized Git repository at {path}")
            else:
                stdout, stderr, code = self._run_git_command(['init'], str(path))
                if code != 0:
                    raise GitServiceError(f"Git init failed: {stderr}")

                # Set initial branch if specified
                branch_name = initial_branch or self.default_branch
                if branch_name != 'master':
                    self._run_git_command(['checkout', '-b', branch_name], str(path))

                logger.info(f"Initialized Git repository at {path}")

            # Create .gitignore if requested
            if create_gitignore:
                self._create_gitignore(str(path), gitignore_type)

            # Set user configuration for this repository
            self._set_user_config(str(path))

            return True

        except Exception as e:
            logger.error(f"Failed to initialize repository at {path}: {e}")
            raise GitServiceError(f"Repository initialization failed: {e}")

    def _create_gitignore(self, repo_path: str, template_type: str = 'python') -> None:
        """Create a .gitignore file with appropriate templates."""
        gitignore_path = Path(repo_path) / '.gitignore'

        # Default templates
        templates = {
            'python': """
# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Virtual environments
venv/
env/
ENV/

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Database
*.db
*.sqlite3

# Environment variables
.env
.env.local

# Temporary files
tmp/
temp/
""",
            'javascript': """
# Dependencies
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*

# Production builds
build/
dist/

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# IDE
.vscode/
.idea/

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Temporary files
tmp/
temp/
""",
            'general': """
# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/

# Temporary files
tmp/
temp/

# Environment variables
.env
"""
        }

        # Use custom template if available
        template_content = self.gitignore_templates.get(template_type,
                                                        templates.get(template_type, templates['general']))

        try:
            gitignore_path.write_text(template_content.strip())
            logger.info(f"Created .gitignore file with {template_type} template")
        except Exception as e:
            logger.warning(f"Failed to create .gitignore: {e}")

    def _set_user_config(self, repo_path: str) -> None:
        """Set user configuration for the repository."""
        try:
            if GIT_PYTHON_AVAILABLE:
                repo = Repo(repo_path)
                config = repo.config_writer()
                config.set_value('user', 'name', self.default_author_name)
                config.set_value('user', 'email', self.default_author_email)
                config.release()
            else:
                self._run_git_command(['config', 'user.name', self.default_author_name], repo_path)
                self._run_git_command(['config', 'user.email', self.default_author_email], repo_path)

            logger.debug(f"Set user config for repository at {repo_path}")

        except Exception as e:
            logger.warning(f"Failed to set user config: {e}")

    def get_repository_status(self, repo_path: str) -> GitStatus:
        """
        Get the current status of a Git repository.

        Args:
            repo_path: Path to the repository

        Returns:
            GitStatus object with repository information
        """
        try:
            if GIT_PYTHON_AVAILABLE and Path(repo_path).is_dir():
                try:
                    repo = Repo(repo_path)

                    # Get basic status
                    current_branch = repo.active_branch.name
                    is_dirty = repo.is_dirty(untracked_files=True)

                    # Get file lists
                    untracked = list(repo.untracked_files) if hasattr(repo, 'untracked_files') else []
                    modified = [item.a_path for item in repo.index.diff(None)]
                    staged = [item.a_path for item in repo.index.diff("HEAD")]

                    # Get remote info
                    remote_url = None
                    try:
                        if repo.remotes:
                            remote_url = repo.remotes.origin.url
                    except:
                        pass

                    return GitStatus(
                        branch=current_branch,
                        is_dirty=is_dirty,
                        untracked_files=untracked,
                        modified_files=modified,
                        staged_files=staged,
                        remote_url=remote_url
                    )

                except InvalidGitRepositoryError:
                    raise GitServiceError(f"Not a valid Git repository: {repo_path}")

            else:
                # Fallback to command line
                stdout, stderr, code = self._run_git_command(['status', '--porcelain'], repo_path)
                if code != 0:
                    raise GitServiceError(f"Git status failed: {stderr}")

                # Parse status output
                untracked = []
                modified = []
                staged = []

                for line in stdout.split('\n'):
                    if line:
                        status = line[:2]
                        filename = line[3:]

                        if status[0] == '?':
                            untracked.append(filename)
                        elif status[0] in ['M', 'A', 'D']:
                            staged.append(filename)
                        elif status[1] in ['M', 'D']:
                            modified.append(filename)

                # Get current branch
                stdout, _, code = self._run_git_command(['branch', '--show-current'], repo_path)
                current_branch = stdout if code == 0 else 'unknown'

                is_dirty = bool(untracked or modified or staged)

                return GitStatus(
                    branch=current_branch,
                    is_dirty=is_dirty,
                    untracked_files=untracked,
                    modified_files=modified,
                    staged_files=staged
                )

        except Exception as e:
            logger.error(f"Failed to get repository status: {e}")
            raise GitServiceError(f"Status check failed: {e}")

    def add_files(self, repo_path: str, files: Union[str, List[str]] = '.') -> bool:
        """
        Add files to the Git index.

        Args:
            repo_path: Path to the repository
            files: File(s) to add (default: all files)

        Returns:
            True if successful, False otherwise
        """
        try:
            if isinstance(files, str):
                files = [files]

            if GIT_PYTHON_AVAILABLE:
                repo = Repo(repo_path)
                repo.index.add(files)
            else:
                for file_path in files:
                    stdout, stderr, code = self._run_git_command(['add', file_path], repo_path)
                    if code != 0:
                        logger.error(f"Failed to add {file_path}: {stderr}")
                        return False

            logger.info(f"Added files to index: {files}")
            return True

        except Exception as e:
            logger.error(f"Failed to add files: {e}")
            return False

    def commit(
            self,
            repo_path: str,
            message: str,
            author_name: Optional[str] = None,
            author_email: Optional[str] = None,
            add_all: bool = True
    ) -> Optional[str]:
        """
        Create a Git commit.

        Args:
            repo_path: Path to the repository
            message: Commit message
            author_name: Author name (defaults to configured)
            author_email: Author email (defaults to configured)
            add_all: Whether to add all files before committing

        Returns:
            Commit hash if successful, None otherwise
        """
        try:
            # Add files if requested
            if add_all:
                self.add_files(repo_path, '.')

            author_name = author_name or self.default_author_name
            author_email = author_email or self.default_author_email

            if GIT_PYTHON_AVAILABLE:
                repo = Repo(repo_path)
                author = Actor(author_name, author_email)
                commit = repo.index.commit(message, author=author, committer=author)
                commit_hash = commit.hexsha
            else:
                stdout, stderr, code = self._run_git_command(['commit', '-m', message], repo_path)
                if code != 0:
                    raise GitServiceError(f"Git commit failed: {stderr}")

                # Get commit hash
                stdout, stderr, code = self._run_git_command(['rev-parse', 'HEAD'], repo_path)
                commit_hash = stdout if code == 0 else None

            logger.info(f"Created commit: {commit_hash[:8] if commit_hash else 'unknown'} - {message}")
            return commit_hash

        except Exception as e:
            logger.error(f"Failed to create commit: {e}")
            return None

    def create_branch(self, repo_path: str, branch_name: str, checkout: bool = True) -> bool:
        """
        Create a new branch.

        Args:
            repo_path: Path to the repository
            branch_name: Name of the new branch
            checkout: Whether to checkout the new branch

        Returns:
            True if successful, False otherwise
        """
        try:
            if GIT_PYTHON_AVAILABLE:
                repo = Repo(repo_path)
                new_branch = repo.create_head(branch_name)
                if checkout:
                    new_branch.checkout()
            else:
                if checkout:
                    stdout, stderr, code = self._run_git_command(['checkout', '-b', branch_name], repo_path)
                else:
                    stdout, stderr, code = self._run_git_command(['branch', branch_name], repo_path)

                if code != 0:
                    raise GitServiceError(f"Branch creation failed: {stderr}")

            logger.info(f"Created branch: {branch_name}" + (" (checked out)" if checkout else ""))
            return True

        except Exception as e:
            logger.error(f"Failed to create branch {branch_name}: {e}")
            return False

    def checkout_branch(self, repo_path: str, branch_name: str) -> bool:
        """
        Checkout a branch.

        Args:
            repo_path: Path to the repository
            branch_name: Name of the branch to checkout

        Returns:
            True if successful, False otherwise
        """
        try:
            if GIT_PYTHON_AVAILABLE:
                repo = Repo(repo_path)
                repo.heads[branch_name].checkout()
            else:
                stdout, stderr, code = self._run_git_command(['checkout', branch_name], repo_path)
                if code != 0:
                    raise GitServiceError(f"Checkout failed: {stderr}")

            logger.info(f"Checked out branch: {branch_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to checkout branch {branch_name}: {e}")
            return False

    def list_branches(self, repo_path: str, include_remote: bool = False) -> List[GitBranch]:
        """
        List all branches in the repository.

        Args:
            repo_path: Path to the repository
            include_remote: Whether to include remote branches

        Returns:
            List of GitBranch objects
        """
        try:
            branches = []

            if GIT_PYTHON_AVAILABLE:
                repo = Repo(repo_path)

                # Local branches
                for branch in repo.heads:
                    is_current = branch == repo.active_branch
                    last_commit = branch.commit

                    branches.append(GitBranch(
                        name=branch.name,
                        is_current=is_current,
                        is_remote=False,
                        last_commit_hash=last_commit.hexsha,
                        last_commit_date=datetime.fromtimestamp(last_commit.committed_date)
                    ))

                # Remote branches
                if include_remote:
                    for remote in repo.remotes:
                        for ref in remote.refs:
                            if ref.name != f"{remote.name}/HEAD":
                                branches.append(GitBranch(
                                    name=ref.name,
                                    is_current=False,
                                    is_remote=True,
                                    last_commit_hash=ref.commit.hexsha,
                                    last_commit_date=datetime.fromtimestamp(ref.commit.committed_date)
                                ))

            else:
                # Command line fallback
                stdout, stderr, code = self._run_git_command(['branch'], repo_path)
                if code == 0:
                    for line in stdout.split('\n'):
                        line = line.strip()
                        if line:
                            is_current = line.startswith('*')
                            name = line[2:] if is_current else line

                            branches.append(GitBranch(
                                name=name,
                                is_current=is_current,
                                is_remote=False,
                                last_commit_hash="unknown",
                                last_commit_date=datetime.now()
                            ))

            return branches

        except Exception as e:
            logger.error(f"Failed to list branches: {e}")
            return []

    def get_commit_history(self, repo_path: str, max_count: int = 10) -> List[GitCommit]:
        """
        Get commit history.

        Args:
            repo_path: Path to the repository
            max_count: Maximum number of commits to retrieve

        Returns:
            List of GitCommit objects
        """
        try:
            commits = []

            if GIT_PYTHON_AVAILABLE:
                repo = Repo(repo_path)

                for commit in repo.iter_commits(max_count=max_count):
                    commits.append(GitCommit(
                        hash=commit.hexsha,
                        short_hash=commit.hexsha[:8],
                        message=commit.message.strip(),
                        author=commit.author.name,
                        email=commit.author.email,
                        date=datetime.fromtimestamp(commit.committed_date),
                        files_changed=list(commit.stats.files.keys()) if commit.stats else []
                    ))

            else:
                # Command line fallback
                stdout, stderr, code = self._run_git_command([
                    'log', f'-{max_count}', '--pretty=format:%H|%h|%s|%an|%ae|%ct'
                ], repo_path)

                if code == 0:
                    for line in stdout.split('\n'):
                        if line:
                            parts = line.split('|')
                            if len(parts) >= 6:
                                commits.append(GitCommit(
                                    hash=parts[0],
                                    short_hash=parts[1],
                                    message=parts[2],
                                    author=parts[3],
                                    email=parts[4],
                                    date=datetime.fromtimestamp(int(parts[5])),
                                    files_changed=[]
                                ))

            return commits

        except Exception as e:
            logger.error(f"Failed to get commit history: {e}")
            return []

    def add_remote(self, repo_path: str, name: str, url: str) -> bool:
        """
        Add a remote repository.

        Args:
            repo_path: Path to the repository
            name: Remote name (e.g., 'origin')
            url: Remote URL

        Returns:
            True if successful, False otherwise
        """
        try:
            if GIT_PYTHON_AVAILABLE:
                repo = Repo(repo_path)
                repo.create_remote(name, url)
            else:
                stdout, stderr, code = self._run_git_command(['remote', 'add', name, url], repo_path)
                if code != 0:
                    raise GitServiceError(f"Failed to add remote: {stderr}")

            logger.info(f"Added remote: {name} -> {url}")
            return True

        except Exception as e:
            logger.error(f"Failed to add remote {name}: {e}")
            return False

    def push(self, repo_path: str, remote: str = 'origin', branch: Optional[str] = None) -> bool:
        """
        Push changes to remote repository.

        Args:
            repo_path: Path to the repository
            remote: Remote name
            branch: Branch to push (current branch if None)

        Returns:
            True if successful, False otherwise
        """
        try:
            if GIT_PYTHON_AVAILABLE:
                repo = Repo(repo_path)
                origin = repo.remotes[remote]

                if branch:
                    origin.push(branch)
                else:
                    origin.push()
            else:
                cmd = ['push', remote]
                if branch:
                    cmd.append(branch)

                stdout, stderr, code = self._run_git_command(cmd, repo_path)
                if code != 0:
                    raise GitServiceError(f"Push failed: {stderr}")

            logger.info(f"Pushed to {remote}" + (f":{branch}" if branch else ""))
            return True

        except Exception as e:
            logger.error(f"Failed to push: {e}")
            return False

    def pull(self, repo_path: str, remote: str = 'origin', branch: Optional[str] = None) -> bool:
        """
        Pull changes from remote repository.

        Args:
            repo_path: Path to the repository
            remote: Remote name
            branch: Branch to pull (current branch if None)

        Returns:
            True if successful, False otherwise
        """
        try:
            if GIT_PYTHON_AVAILABLE:
                repo = Repo(repo_path)
                origin = repo.remotes[remote]
                origin.pull()
            else:
                cmd = ['pull', remote]
                if branch:
                    cmd.append(branch)

                stdout, stderr, code = self._run_git_command(cmd, repo_path)
                if code != 0:
                    raise GitServiceError(f"Pull failed: {stderr}")

            logger.info(f"Pulled from {remote}" + (f":{branch}" if branch else ""))
            return True

        except Exception as e:
            logger.error(f"Failed to pull: {e}")
            return False

    def parse_repository_url(self, url: str) -> Optional[RepositoryInfo]:
        """
        Parse a Git repository URL and extract information.

        Supports:
        - GitHub: https://github.com/owner/repo or git@github.com:owner/repo.git
        - GitLab: https://gitlab.com/owner/repo
        - Bitbucket: https://bitbucket.org/owner/repo
        - Generic Git URLs

        Args:
            url: Git repository URL

        Returns:
            RepositoryInfo object or None if parsing fails
        """
        try:
            # Clean up URL
            url = url.strip()

            # GitHub patterns
            github_https = re.match(r'https?://github\.com/([^/]+)/([^/\.]+)', url)
            github_ssh = re.match(r'git@github\.com:([^/]+)/([^/\.]+)', url)

            # GitLab patterns
            gitlab_https = re.match(r'https?://gitlab\.com/([^/]+)/([^/\.]+)', url)
            gitlab_ssh = re.match(r'git@gitlab\.com:([^/]+)/([^/\.]+)', url)

            # Bitbucket patterns
            bitbucket_https = re.match(r'https?://bitbucket\.org/([^/]+)/([^/\.]+)', url)

            if github_https or github_ssh:
                match = github_https or github_ssh
                owner, repo = match.groups()
                repo = repo.replace('.git', '')

                return RepositoryInfo(
                    url=url,
                    name=repo,
                    owner=owner,
                    platform='github'
                )

            elif gitlab_https or gitlab_ssh:
                match = gitlab_https or gitlab_ssh
                owner, repo = match.groups()
                repo = repo.replace('.git', '')

                return RepositoryInfo(
                    url=url,
                    name=repo,
                    owner=owner,
                    platform='gitlab'
                )

            elif bitbucket_https:
                owner, repo = bitbucket_https.groups()
                repo = repo.replace('.git', '')

                return RepositoryInfo(
                    url=url,
                    name=repo,
                    owner=owner,
                    platform='bitbucket'
                )

            else:
                # Generic Git URL - try to extract name from URL
                # Pattern: .../repo_name.git or .../repo_name
                repo_match = re.search(r'/([^/]+?)(\.git)?$', url)
                if repo_match:
                    repo_name = repo_match.group(1)
                    return RepositoryInfo(
                        url=url,
                        name=repo_name,
                        owner='unknown',
                        platform='other'
                    )

                return None

        except Exception as e:
            logger.error(f"Failed to parse repository URL {url}: {e}")
            return None

    def clone_repository(
            self,
            url: str,
            destination: Optional[str] = None,
            branch: Optional[str] = None,
            depth: Optional[int] = None,
            progress_callback: Optional[callable] = None
    ) -> CloneResult:
        """
        Clone a Git repository from a remote URL.

        Args:
            url: Repository URL (HTTPS or SSH)
            destination: Local destination path (auto-generated if None)
            branch: Specific branch to clone (None for default)
            depth: Clone depth for shallow clone (None for full clone)
            progress_callback: Optional callback for progress updates

        Returns:
            CloneResult with operation status and repository information
        """
        try:
            # Parse repository URL
            repo_info = self.parse_repository_url(url)
            if not repo_info:
                return CloneResult(
                    success=False,
                    local_path='',
                    error=f"Failed to parse repository URL: {url}"
                )

            # Determine destination path
            if destination is None:
                # Auto-generate path: data/imported_repos/{owner}/{repo}
                destination = Path('data/imported_repos') / repo_info.owner / repo_info.name
            else:
                destination = Path(destination)

            # Check if destination already exists
            if destination.exists():
                # Check if it's already a git repo
                try:
                    existing_repo = Repo(str(destination)) if GIT_PYTHON_AVAILABLE else None
                    if existing_repo or (destination / '.git').exists():
                        logger.warning(f"Repository already exists at {destination}")
                        return CloneResult(
                            success=False,
                            local_path=str(destination),
                            repository_info=repo_info,
                            error="Repository already cloned at this location"
                        )
                except:
                    pass

                # Remove existing directory if not a git repo
                shutil.rmtree(destination)

            # Create parent directory
            destination.parent.mkdir(parents=True, exist_ok=True)

            logger.info(f"Cloning repository {url} to {destination}")

            # Clone using GitPython or command line
            if GIT_PYTHON_AVAILABLE:
                clone_kwargs = {
                    'to_path': str(destination),
                }

                if branch:
                    clone_kwargs['branch'] = branch

                if depth:
                    clone_kwargs['depth'] = depth

                if progress_callback:
                    # GitPython progress handling
                    class ProgressPrinter:
                        def update(self, op_code, cur_count, max_count=None, message=''):
                            if progress_callback:
                                percent = (cur_count / max_count * 100) if max_count else 0
                                progress_callback(op_code, cur_count, max_count, percent, message)

                    clone_kwargs['progress'] = ProgressPrinter()

                repo = Repo.clone_from(url, **clone_kwargs)
                cloned_path = str(destination)

            else:
                # Command line fallback
                clone_cmd = ['clone', url, str(destination)]

                if branch:
                    clone_cmd.extend(['--branch', branch])

                if depth:
                    clone_cmd.extend(['--depth', str(depth)])

                stdout, stderr, code = self._run_git_command(clone_cmd, '.')

                if code != 0:
                    raise GitServiceError(f"Git clone failed: {stderr}")

                cloned_path = str(destination)

            # Analyze cloned repository
            file_count = 0
            total_size = 0

            for item in destination.rglob('*'):
                if item.is_file() and '.git' not in item.parts:
                    file_count += 1
                    try:
                        total_size += item.stat().st_size
                    except:
                        pass

            # Get branches
            branches = []
            try:
                branch_objs = self.list_branches(cloned_path)
                branches = [b.name for b in branch_objs]
            except:
                pass

            logger.info(f"Successfully cloned repository: {file_count} files, {total_size / 1024 / 1024:.2f} MB")

            return CloneResult(
                success=True,
                local_path=cloned_path,
                repository_info=repo_info,
                file_count=file_count,
                total_size_bytes=total_size,
                branches=branches
            )

        except Exception as e:
            logger.error(f"Failed to clone repository {url}: {e}")
            return CloneResult(
                success=False,
                local_path=destination if destination else '',
                repository_info=repo_info if 'repo_info' in locals() else None,
                error=str(e)
            )

    def create_commit_for_generated_code(
            self,
            repo_path: str,
            project_name: str,
            generated_files: List[str],
            specifications: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Create an automated commit for generated code.

        Args:
            repo_path: Path to the repository
            project_name: Name of the project
            generated_files: List of generated files
            specifications: Project specifications for commit message

        Returns:
            Commit hash if successful, None otherwise
        """
        try:
            # Generate descriptive commit message
            file_count = len(generated_files)
            file_summary = self._summarize_generated_files(generated_files)

            commit_message = f"Generate {project_name} - {file_count} files\n\n"
            commit_message += f"Generated files:\n{file_summary}\n"

            if specifications:
                tech_stack = specifications.get('technology_stack', {})
                if tech_stack:
                    commit_message += f"\nTechnology stack: {', '.join(tech_stack.keys())}\n"

            commit_message += f"\nGenerated by Socratic RAG Enhanced\nTimestamp: {datetime.now().isoformat()}"

            return self.commit(repo_path, commit_message, add_all=True)

        except Exception as e:
            logger.error(f"Failed to create commit for generated code: {e}")
            return None

    def _summarize_generated_files(self, files: List[str]) -> str:
        """Create a summary of generated files for commit messages."""
        if not files:
            return "No files"

        # Group files by type
        file_groups = {}
        for file_path in files:
            ext = Path(file_path).suffix.lower()
            if ext not in file_groups:
                file_groups[ext] = []
            file_groups[ext].append(Path(file_path).name)

        # Create summary
        summary_lines = []
        for ext, file_list in sorted(file_groups.items()):
            if len(file_list) <= 3:
                summary_lines.append(f"- {ext or 'misc'}: {', '.join(file_list)}")
            else:
                summary_lines.append(f"- {ext or 'misc'}: {', '.join(file_list[:2])}, ... ({len(file_list)} total)")

        return '\n'.join(summary_lines)

    def health_check(self) -> Dict[str, Any]:
        """Check Git service health and availability."""
        try:
            git_available = self._check_git_available()

            # Get Git version if available
            git_version = None
            if git_available:
                try:
                    stdout, _, _ = self._run_git_command(['--version'], '.')
                    git_version = stdout
                except:
                    pass

            return {
                "status": "healthy" if git_available else "unhealthy",
                "git_available": git_available,
                "git_python_available": GIT_PYTHON_AVAILABLE,
                "git_version": git_version,
                "default_author": self.default_author_name,
                "default_email": self.default_author_email,
                "auto_commit": self.auto_commit,
                "auto_push": self.auto_push,
                "last_check": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Git service health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "git_available": False,
                "git_python_available": GIT_PYTHON_AVAILABLE,
                "last_check": datetime.now().isoformat()
            }
