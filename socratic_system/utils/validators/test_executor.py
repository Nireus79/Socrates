"""
Test Executor - Executes tests via subprocess

Supports:
- Python: pytest and unittest
- JavaScript: jest and mocha
- Test discovery and output parsing
- Timeout protection
"""

import json
import logging
import re
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger("socrates.utils.validators.test_executor")


class TestExecutor:
    """Executes tests and parses results"""

    DEFAULT_TIMEOUT = 300  # 5 minutes
    SUPPORTED_FRAMEWORKS = {
        "python": ["pytest", "unittest"],
        "javascript": ["jest", "mocha"],
    }

    def validate(self, target: str, timeout: int = DEFAULT_TIMEOUT) -> Dict[str, Any]:
        """
        Execute tests in project

        Args:
            target: Directory path to project
            timeout: Timeout for test execution in seconds

        Returns:
            {
                "status": "success", "error", or "timeout",
                "tests_found": bool,
                "tests_passed": int,
                "tests_failed": int,
                "tests_skipped": int,
                "duration_seconds": float,
                "framework": str,
                "failures": List[Dict],
                "output": str
            }
        """
        target_path = Path(target)

        if not target_path.exists():
            return {
                "status": "error",
                "message": f"Path does not exist: {target}",
                "tests_found": False,
                "tests_passed": 0,
                "tests_failed": 0,
                "tests_skipped": 0,
                "duration_seconds": 0,
                "framework": "unknown",
                "failures": [],
                "output": "",
            }

        if target_path.is_file():
            target = str(target_path.parent)

        # Detect project type and framework
        project_type = self._detect_project_type(target)

        if project_type == "python":
            return self._execute_python_tests(target, timeout)
        elif project_type == "javascript":
            return self._execute_javascript_tests(target, timeout)
        else:
            return {
                "status": "error",
                "message": "Could not detect test framework",
                "tests_found": False,
                "tests_passed": 0,
                "tests_failed": 0,
                "tests_skipped": 0,
                "duration_seconds": 0,
                "framework": "unknown",
                "failures": [],
                "output": "No test framework detected",
            }

    def _detect_project_type(self, project_dir: str) -> Optional[str]:
        """Detect project type from key files"""
        project_path = Path(project_dir)

        # Check for Python tests
        for pattern in ["test_*.py", "*_test.py", "tests/test_*.py", "test_*.py"]:
            if list(project_path.glob(pattern)):
                return "python"

        if list(project_path.glob("tests/**/*.py")) or list(project_path.glob("test/**/*.py")):
            return "python"

        # Check for JavaScript tests
        for pattern in ["test_*.js", "*_test.js", "*.test.js", "*.spec.js"]:
            if list(project_path.glob(pattern)):
                return "javascript"

        if (project_path / "package.json").exists():
            return "javascript"

        # Check for Python files in general
        if list(project_path.glob("**/*.py")):
            return "python"

        return None

    def _execute_python_tests(self, project_dir: str, timeout: int) -> Dict[str, Any]:
        """Execute Python tests using pytest or unittest"""
        try:
            # Try pytest first
            command = [sys.executable, "-m", "pytest", project_dir, "-v", "--tb=short"]

            logger.info(f"Executing Python tests: {' '.join(command)}")

            try:
                result = subprocess.run(
                    command,
                    cwd=project_dir,
                    timeout=timeout,
                    capture_output=True,
                    text=True,
                )

                return self._parse_pytest_output(result)

            except subprocess.TimeoutExpired:
                return {
                    "status": "timeout",
                    "message": f"Test execution timed out after {timeout} seconds",
                    "tests_found": True,
                    "tests_passed": 0,
                    "tests_failed": 0,
                    "tests_skipped": 0,
                    "duration_seconds": timeout,
                    "framework": "pytest",
                    "failures": [],
                    "output": f"Test execution timed out after {timeout} seconds",
                }

        except Exception as e:
            logger.error(f"Error executing Python tests: {e}")
            return {
                "status": "error",
                "message": str(e),
                "tests_found": False,
                "tests_passed": 0,
                "tests_failed": 0,
                "tests_skipped": 0,
                "duration_seconds": 0,
                "framework": "pytest",
                "failures": [],
                "output": str(e),
            }

    def _parse_pytest_output(self, result: subprocess.CompletedProcess) -> Dict[str, Any]:
        """Parse pytest output"""
        output = result.stdout + result.stderr

        # Extract test summary
        passed = len(re.findall(r" PASSED", output))
        failed = len(re.findall(r" FAILED", output))
        skipped = len(re.findall(r" SKIPPED", output))

        # Extract summary line
        re.search(r"(\d+) passed|(\d+) failed|(\d+) skipped|(\d+) error", output)

        # Parse failure details
        failures = []
        failure_blocks = re.findall(r"FAILED (.*?) -", output)
        for failure in failure_blocks[:10]:  # Limit to 10 failures
            failures.append(
                {
                    "test": failure.strip(),
                    "message": "Test failed (see full output for details)",
                }
            )

        # Extract duration
        duration_match = re.search(r"(\d+\.\d+)s", output)
        duration = float(duration_match.group(1)) if duration_match else 0

        return {
            "status": "success" if failed == 0 else "error",
            "tests_found": passed + failed + skipped > 0,
            "tests_passed": passed,
            "tests_failed": failed,
            "tests_skipped": skipped,
            "duration_seconds": duration,
            "framework": "pytest",
            "failures": failures,
            "output": output if result.returncode != 0 else "All tests passed",
        }

    def _execute_javascript_tests(self, project_dir: str, timeout: int) -> Dict[str, Any]:
        """Execute JavaScript tests using jest or mocha"""
        try:
            # Try npm test or jest
            commands = [
                ["npx", "jest", "--json"],
                ["npm", "test"],
            ]

            for command in commands:
                try:
                    logger.info(f"Trying JavaScript test command: {' '.join(command)}")

                    result = subprocess.run(
                        command,
                        cwd=project_dir,
                        timeout=timeout,
                        capture_output=True,
                        text=True,
                    )

                    # Check if command was found
                    if "not found" not in result.stderr.lower():
                        return self._parse_jest_output(result)

                except subprocess.TimeoutExpired:
                    return {
                        "status": "timeout",
                        "message": f"Test execution timed out after {timeout} seconds",
                        "tests_found": True,
                        "tests_passed": 0,
                        "tests_failed": 0,
                        "tests_skipped": 0,
                        "duration_seconds": timeout,
                        "framework": "jest/mocha",
                        "failures": [],
                        "output": "Test execution timed out",
                    }
                except Exception:
                    continue

            # No tests found
            return {
                "status": "error",
                "message": "No test runner found (install jest or mocha)",
                "tests_found": False,
                "tests_passed": 0,
                "tests_failed": 0,
                "tests_skipped": 0,
                "duration_seconds": 0,
                "framework": "jest/mocha",
                "failures": [],
                "output": "No test runner found",
            }

        except Exception as e:
            logger.error(f"Error executing JavaScript tests: {e}")
            return {
                "status": "error",
                "message": str(e),
                "tests_found": False,
                "tests_passed": 0,
                "tests_failed": 0,
                "tests_skipped": 0,
                "duration_seconds": 0,
                "framework": "jest/mocha",
                "failures": [],
                "output": str(e),
            }

    def _parse_jest_output(self, result: subprocess.CompletedProcess) -> Dict[str, Any]:
        """Parse jest output"""
        output = result.stdout + result.stderr

        # Try to parse JSON output
        try:
            # Extract JSON from output
            json_match = re.search(r"\{[\s\S]*\}", output)
            if json_match:
                json_data = json.loads(json_match.group())

                passed = json_data.get("numPassedTests", 0)
                failed = json_data.get("numFailedTests", 0)
                skipped = json_data.get("numPendingTests", 0)
                duration = (
                    json_data.get("testResults", [{}])[0].get("perfStats", {}).get("start", 0)
                )

                # Extract failure details
                failures = []
                for test_result in json_data.get("testResults", []):
                    for failure in test_result.get("assertionResults", []):
                        if failure.get("status") == "failed":
                            failures.append(
                                {
                                    "test": failure.get("title", "Unknown"),
                                    "message": "\n".join(failure.get("failureMessages", [])),
                                }
                            )

                return {
                    "status": "success" if failed == 0 else "error",
                    "tests_found": passed + failed + skipped > 0,
                    "tests_passed": passed,
                    "tests_failed": failed,
                    "tests_skipped": skipped,
                    "duration_seconds": duration / 1000 if duration else 0,
                    "framework": "jest",
                    "failures": failures[:10],
                    "output": output if failed > 0 else "All tests passed",
                }
        except Exception as e:
            logger.debug(f"Could not parse jest JSON: {e}")

        # Fall back to text parsing
        passed = output.count("✓") or output.count("PASS")
        failed = output.count("✕") or output.count("FAIL")
        skipped = output.count("⊙") or output.count("SKIP")

        return {
            "status": "success" if failed == 0 else "error",
            "tests_found": passed + failed + skipped > 0,
            "tests_passed": passed,
            "tests_failed": failed,
            "tests_skipped": skipped,
            "duration_seconds": 0,
            "framework": "jest/mocha",
            "failures": [],
            "output": output,
        }

    def detect_test_framework(self, project_dir: str) -> Optional[str]:
        """Detect test framework used in project"""
        project_path = Path(project_dir)

        # Check for pytest
        if (project_path / "pytest.ini").exists() or (project_path / "setup.cfg").exists():
            return "pytest"

        if list(project_path.glob("test_*.py")) or list(project_path.glob("*_test.py")):
            return "pytest"

        # Check for jest
        package_json = project_path / "package.json"
        if package_json.exists():
            try:
                with open(package_json) as f:
                    data = json.load(f)
                    if "jest" in data or "jest" in str(data.get("devDependencies", {})):
                        return "jest"
                    if "mocha" in str(data.get("devDependencies", {})):
                        return "mocha"
            except Exception:
                pass

        return None
