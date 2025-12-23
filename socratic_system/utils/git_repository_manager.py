"""
Git Repository Manager - Handles secure GitHub repository operations

Manages:
- GitHub URL validation
- Repository cloning to isolated temp directories
- Repository metadata extraction
- Git operations (pull, push)
- Secure cleanup
"""

import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger("socrates.utils.git_repo_manager")


class GitRepositoryManager:
    """Manages GitHub repository operations with security and isolation"""

    GITHUB_DOMAINS = ["github.com", "www.github.com"]
    TEMP_PREFIX = "socrates_clone_"
    CLONE_TIMEOUT = 300  # 5 minutes
    PUSH_PULL_TIMEOUT = 300  # 5 minutes

    def __init__(self, temp_base_dir: Optional[str] = None, github_token: Optional[str] = None):
        """
        Initialize GitRepositoryManager

        Args:
            temp_base_dir: Base directory for temporary clones (default: system temp)
            github_token: GitHub PAT for private repos (from env by default)
        """
        self.temp_base_dir = temp_base_dir or tempfile.gettempdir()
        self.github_token = github_token or os.getenv("GITHUB_TOKEN")
        self.logger = logging.getLogger("socrates.utils.git_repo_manager")

    def validate_github_url(self, url: str) -> Dict[str, Any]:
        """
        Validate GitHub URL format and extract metadata

        Args:
            url: GitHub URL (https://github.com/owner/repo or git@github.com:owner/repo.git)

        Returns:
            {
                "valid": bool,
                "owner": str or None,
                "repo": str or None,
                "url": str,
                "message": str (if invalid)
            }
        """
        if not url or not isinstance(url, str):
            return {
                "valid": False,
                "owner": None,
                "repo": None,
                "url": url,
                "message": "URL cannot be empty",
            }

        url = url.strip()

        # Pattern 1: https://github.com/owner/repo or https://github.com/owner/repo.git
        https_pattern = r"https://github\.com/([a-zA-Z0-9_-]+)/([a-zA-Z0-9._-]+?)(?:\.git)?/?$"
        match = re.match(https_pattern, url)
        if match:
            owner, repo = match.groups()
            return {
                "valid": True,
                "owner": owner,
                "repo": repo,
                "url": url,
                "message": "Valid GitHub URL",
            }

        # Pattern 2: git@github.com:owner/repo or git@github.com:owner/repo.git
        ssh_pattern = r"git@github\.com:([a-zA-Z0-9_-]+)/([a-zA-Z0-9._-]+?)(?:\.git)?/?$"
        match = re.match(ssh_pattern, url)
        if match:
            owner, repo = match.groups()
            return {
                "valid": True,
                "owner": owner,
                "repo": repo,
                "url": url,
                "message": "Valid GitHub SSH URL",
            }

        return {
            "valid": False,
            "owner": None,
            "repo": None,
            "url": url,
            "message": "URL must be a valid GitHub repository (https or SSH)",
        }

    def clone_repository(self, github_url: str) -> Dict[str, Any]:
        """
        Clone repository to isolated temporary directory

        Args:
            github_url: GitHub repository URL

        Returns:
            {
                "status": "success" or "error",
                "clone_path": str or None,
                "metadata": Dict or None,
                "message": str
            }
        """
        # Validate URL
        validation = self.validate_github_url(github_url)
        if not validation["valid"]:
            return {
                "status": "error",
                "clone_path": None,
                "metadata": None,
                "message": validation["message"],
            }

        # Create isolated temp directory
        temp_dir = os.path.join(
            self.temp_base_dir, f"{self.TEMP_PREFIX}{uuid.uuid4().hex[:8]}"
        )

        try:
            # Create directory
            os.makedirs(temp_dir, exist_ok=True)
            self.logger.debug(f"Created temp directory: {temp_dir}")

            # Build git clone command
            # Use https or ssh with token if available
            if github_url.startswith("https://") and self.github_token:
                # Inject token into HTTPS URL
                clone_url = github_url.replace(
                    "https://github.com/",
                    f"https://{self.github_token}@github.com/",
                )
            else:
                clone_url = github_url

            command = [sys.executable, "-m", "git", "clone", clone_url, temp_dir]

            # Execute clone
            self.logger.info(f"Cloning repository: {github_url} to {temp_dir}")
            try:
                result = subprocess.run(
                    command,
                    timeout=self.CLONE_TIMEOUT,
                    capture_output=True,
                    text=True,
                )

                if result.returncode != 0:
                    # Git not available via Python module, try direct command
                    command = ["git", "clone", clone_url, temp_dir]
                    result = subprocess.run(
                        command,
                        timeout=self.CLONE_TIMEOUT,
                        capture_output=True,
                        text=True,
                    )

                    if result.returncode != 0:
                        error_msg = result.stderr or result.stdout or "Unknown error"
                        self.logger.error(f"Clone failed: {error_msg}")
                        self.cleanup(temp_dir)
                        return {
                            "status": "error",
                            "clone_path": None,
                            "metadata": None,
                            "message": f"Failed to clone repository: {error_msg}",
                        }

            except subprocess.TimeoutExpired:
                self.logger.error(f"Clone operation timed out after {self.CLONE_TIMEOUT}s")
                self.cleanup(temp_dir)
                return {
                    "status": "error",
                    "clone_path": None,
                    "metadata": None,
                    "message": f"Clone operation timed out after {self.CLONE_TIMEOUT} seconds",
                }

            # Extract metadata
            self.logger.debug("Extracting repository metadata...")
            metadata = self.extract_repository_metadata(temp_dir, validation)

            self.logger.info(f"Successfully cloned repository to {temp_dir}")
            return {
                "status": "success",
                "clone_path": temp_dir,
                "metadata": metadata,
                "message": "Repository cloned successfully",
            }

        except Exception as e:
            self.logger.error(f"Error cloning repository: {e}")
            self.cleanup(temp_dir)
            return {
                "status": "error",
                "clone_path": None,
                "metadata": None,
                "message": f"Error cloning repository: {str(e)}",
            }

    def extract_repository_metadata(
        self, clone_path: str, url_info: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract metadata from cloned repository

        Args:
            clone_path: Path to cloned repository
            url_info: Result from validate_github_url

        Returns:
            {
                "name": str,
                "owner": str,
                "description": str,
                "primary_language": str,
                "languages": List[str],
                "file_count": int,
                "total_size_bytes": int,
                "has_tests": bool,
                "has_readme": bool,
                "default_branch": str
            }
        """
        try:
            clone_root = Path(clone_path)

            # Get repository name and owner from URL info
            name = url_info.get("repo", "unknown")
            owner = url_info.get("owner", "unknown")

            # Get description from README or .git/description
            description = ""
            readme_path = clone_root / "README.md"
            if not readme_path.exists():
                readme_path = clone_root / "readme.md"
            if not readme_path.exists():
                readme_path = clone_root / "README"
            if readme_path.exists():
                try:
                    with open(readme_path, "r", encoding="utf-8", errors="ignore") as f:
                        # Get first paragraph as description
                        content = f.read()
                        description = content.split("\n\n")[0][:200] if content else ""
                except Exception as e:
                    self.logger.debug(f"Could not read README: {e}")

            # Detect programming languages
            languages = self._detect_languages(clone_root)
            primary_language = languages[0] if languages else "Unknown"

            # Count files and calculate size
            file_count, total_size = self._count_files_and_size(clone_root)

            # Check for tests
            has_tests = self._has_tests(clone_root)

            # Check for README
            has_readme = readme_path.exists()

            # Get default branch
            default_branch = self._get_default_branch(clone_root)

            metadata = {
                "name": name,
                "owner": owner,
                "description": description,
                "primary_language": primary_language,
                "languages": languages,
                "file_count": file_count,
                "total_size_bytes": total_size,
                "has_tests": has_tests,
                "has_readme": has_readme,
                "default_branch": default_branch,
            }

            self.logger.debug(f"Extracted metadata: {metadata}")
            return metadata

        except Exception as e:
            self.logger.warning(f"Error extracting metadata: {e}")
            return {
                "name": url_info.get("repo", "unknown"),
                "owner": url_info.get("owner", "unknown"),
                "description": "",
                "primary_language": "Unknown",
                "languages": [],
                "file_count": 0,
                "total_size_bytes": 0,
                "has_tests": False,
                "has_readme": False,
                "default_branch": "main",
            }

    def _detect_languages(self, repo_path: Path) -> List[str]:
        """Detect programming languages in repository"""
        language_extensions = {
            "Python": [".py"],
            "JavaScript": [".js", ".jsx"],
            "TypeScript": [".ts", ".tsx"],
            "Java": [".java"],
            "Go": [".go"],
            "Rust": [".rs"],
            "C++": [".cpp", ".cc", ".cxx", ".hpp"],
            "C#": [".cs"],
            "PHP": [".php"],
            "Ruby": [".rb"],
            "SQL": [".sql"],
        }

        found_languages = set()

        try:
            for file_path in repo_path.rglob("*"):
                if file_path.is_file():
                    suffix = file_path.suffix.lower()
                    for language, extensions in language_extensions.items():
                        if suffix in extensions:
                            found_languages.add(language)
                            if len(found_languages) >= 5:  # Limit to 5 languages
                                return sorted(list(found_languages))
        except Exception as e:
            self.logger.debug(f"Error detecting languages: {e}")

        return sorted(list(found_languages)) if found_languages else []

    def _count_files_and_size(self, repo_path: Path) -> Tuple[int, int]:
        """Count total files and calculate total size (excluding .git)"""
        file_count = 0
        total_size = 0

        try:
            for file_path in repo_path.rglob("*"):
                # Skip .git directory
                if ".git" in file_path.parts:
                    continue
                if file_path.is_file():
                    file_count += 1
                    try:
                        total_size += file_path.stat().st_size
                    except OSError:
                        pass
        except Exception as e:
            self.logger.debug(f"Error counting files: {e}")

        return file_count, total_size

    def _has_tests(self, repo_path: Path) -> bool:
        """Check if repository has test files/directories"""
        test_patterns = [
            "test",
            "tests",
            "__tests__",
            "spec",
            "specs",
            "test_*.py",
            "*_test.py",
            "*_spec.py",
        ]

        try:
            # Check for test directories
            for item in repo_path.iterdir():
                if item.is_dir():
                    name = item.name.lower()
                    if any(pattern in name for pattern in test_patterns):
                        return True

            # Check for test files
            for file_path in repo_path.rglob("*"):
                if ".git" in file_path.parts:
                    continue
                if file_path.is_file():
                    name = file_path.name.lower()
                    if any(name.endswith(pattern) for pattern in test_patterns):
                        return True
        except Exception as e:
            self.logger.debug(f"Error checking for tests: {e}")

        return False

    def _get_default_branch(self, repo_path: Path) -> str:
        """Get default branch name from repository"""
        try:
            # Try to read .git/HEAD
            head_file = Path(repo_path) / ".git" / "HEAD"
            if head_file.exists():
                with open(head_file, "r") as f:
                    content = f.read().strip()
                    # Format: ref: refs/heads/main
                    if "refs/heads/" in content:
                        return content.split("refs/heads/")[-1]
        except Exception as e:
            self.logger.debug(f"Error getting default branch: {e}")

        return "main"  # Default fallback

    def get_file_tree(
        self, clone_path: str, exclude_patterns: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """
        Get structured file tree excluding common patterns

        Args:
            clone_path: Path to cloned repository
            exclude_patterns: Patterns to exclude (default: .git, __pycache__, etc.)

        Returns:
            List of {"path": str, "type": "file"|"dir", "size": int}
        """
        if exclude_patterns is None:
            exclude_patterns = [
                ".git",
                ".gitignore",
                ".github",
                "__pycache__",
                "node_modules",
                ".venv",
                "venv",
                ".env",
                ".DS_Store",
                "*.pyc",
                "*.pyo",
                ".pytest_cache",
                ".coverage",
            ]

        file_tree = []

        try:
            repo_root = Path(clone_path)
            for item in repo_root.rglob("*"):
                # Skip excluded patterns
                skip = False
                for pattern in exclude_patterns:
                    if pattern in str(item):
                        skip = True
                        break
                if skip:
                    continue

                try:
                    rel_path = item.relative_to(repo_root)
                    if item.is_file():
                        file_tree.append(
                            {
                                "path": str(rel_path),
                                "type": "file",
                                "size": item.stat().st_size,
                            }
                        )
                    else:
                        file_tree.append({"path": str(rel_path), "type": "dir", "size": 0})
                except (OSError, ValueError):
                    pass

        except Exception as e:
            self.logger.error(f"Error getting file tree: {e}")

        return sorted(file_tree, key=lambda x: x["path"])

    def cleanup(self, clone_path: str) -> bool:
        """
        Safely remove cloned repository

        Args:
            clone_path: Path to cloned repository

        Returns:
            True if successful, False otherwise
        """
        if not clone_path:
            return False

        try:
            # Verify path is within temp_base_dir for safety
            clone_path = Path(clone_path).resolve()
            temp_base = Path(self.temp_base_dir).resolve()

            # Check if path is within temp directory
            try:
                clone_path.relative_to(temp_base)
            except ValueError:
                self.logger.error(
                    f"Path traversal attempt detected: {clone_path} not in {temp_base}"
                )
                return False

            # Remove directory
            if clone_path.exists():
                shutil.rmtree(clone_path, ignore_errors=True)
                self.logger.debug(f"Cleaned up temporary directory: {clone_path}")
                return True

            return True

        except Exception as e:
            self.logger.error(f"Error cleaning up directory {clone_path}: {e}")
            return False

    def pull_repository(
        self, clone_path: str, branch: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Pull latest changes from remote repository

        Args:
            clone_path: Path to cloned repository
            branch: Branch to pull from (default: current branch)

        Returns:
            {
                "status": "success" or "error",
                "message": str,
                "changes": Dict with files added/modified/deleted
            }
        """
        try:
            clone_path = Path(clone_path)
            if not clone_path.exists():
                return {"status": "error", "message": "Repository path does not exist", "changes": {}}

            # Build git pull command
            command = ["git", "-C", str(clone_path), "pull"]
            if branch:
                command.extend(["origin", branch])

            result = subprocess.run(
                command,
                timeout=self.PUSH_PULL_TIMEOUT,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                return {
                    "status": "error",
                    "message": result.stderr or "Pull failed",
                    "changes": {},
                }

            self.logger.info(f"Successfully pulled updates from repository")
            return {
                "status": "success",
                "message": result.stdout or "Pull successful",
                "changes": {},
            }

        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "message": f"Pull operation timed out after {self.PUSH_PULL_TIMEOUT}s",
                "changes": {},
            }
        except Exception as e:
            self.logger.error(f"Error pulling repository: {e}")
            return {"status": "error", "message": str(e), "changes": {}}

    def push_repository(
        self, clone_path: str, message: str, branch: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Push changes back to remote repository

        Args:
            clone_path: Path to repository
            message: Commit message
            branch: Branch to push to (default: current branch)

        Returns:
            {
                "status": "success" or "error",
                "message": str
            }
        """
        try:
            clone_path = Path(clone_path)
            if not clone_path.exists():
                return {"status": "error", "message": "Repository path does not exist"}

            # Validate commit message
            if not message or len(message.strip()) == 0:
                return {"status": "error", "message": "Commit message cannot be empty"}

            # Git add
            subprocess.run(
                ["git", "-C", str(clone_path), "add", "-A"],
                timeout=self.PUSH_PULL_TIMEOUT,
                capture_output=True,
            )

            # Git commit
            result = subprocess.run(
                ["git", "-C", str(clone_path), "commit", "-m", message],
                timeout=self.PUSH_PULL_TIMEOUT,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0 and "nothing to commit" not in result.stdout.lower():
                return {"status": "error", "message": result.stderr or "Commit failed"}

            # Git push
            push_command = ["git", "-C", str(clone_path), "push"]
            if branch:
                push_command.extend(["origin", branch])

            result = subprocess.run(
                push_command,
                timeout=self.PUSH_PULL_TIMEOUT,
                capture_output=True,
                text=True,
            )

            if result.returncode != 0:
                return {"status": "error", "message": result.stderr or "Push failed"}

            self.logger.info(f"Successfully pushed changes to repository")
            return {"status": "success", "message": "Push successful"}

        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "message": f"Push operation timed out after {self.PUSH_PULL_TIMEOUT}s",
            }
        except Exception as e:
            self.logger.error(f"Error pushing repository: {e}")
            return {"status": "error", "message": str(e)}

    def get_git_diff(self, clone_path: str) -> str:
        """
        Get git diff output

        Args:
            clone_path: Path to repository

        Returns:
            Diff output as string
        """
        try:
            result = subprocess.run(
                ["git", "-C", str(clone_path), "diff", "--color=never"],
                timeout=30,
                capture_output=True,
                text=True,
            )
            return result.stdout if result.returncode == 0 else "No differences"
        except Exception as e:
            self.logger.error(f"Error getting git diff: {e}")
            return f"Error: {str(e)}"
