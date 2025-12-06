"""
PyCharm Plugin Integration Example for Socrates AI

This example demonstrates how to integrate the Socrates AI library directly
into a PyCharm plugin using the Python plugin API.

The plugin provides:
- Socratic question panels in the IDE
- Code generation from specifications
- Interactive learning sessions
- Token usage tracking

Installation:
1. Create a PyCharm plugin project
2. Add socrates-ai as a dependency
3. Implement this bridge class in your plugin
4. Use IDE event listeners to trigger Socratic interactions
"""

import logging
import os
from pathlib import Path
from typing import Any, Callable, Dict, Optional

try:
    import socrates_ai
except ImportError:
    print("Install socrates-ai: pip install socrates-ai")
    raise


class SocratesBridge:
    """
    Bridge between PyCharm IDE and Socrates AI library

    Manages:
    - Configuration and initialization
    - IDE event forwarding
    - Result display
    """

    def __init__(self, api_key: str, project_dir: Optional[str] = None):
        """
        Initialize Socrates bridge for PyCharm plugin

        Args:
            api_key: Claude API key
            project_dir: Optional project directory for data storage
        """
        self.logger = logging.getLogger(__name__)

        # Create configuration
        config_builder = socrates_ai.ConfigBuilder(api_key)
        if project_dir:
            data_dir = Path(project_dir) / ".socrates"
            config_builder = config_builder.with_data_dir(data_dir)

        self.config = config_builder.build()
        self.orchestrator = socrates_ai.create_orchestrator(self.config)

        # Event callbacks
        self._callbacks = {
            "on_question_generated": [],
            "on_code_generated": [],
            "on_error": [],
            "on_event": [],
        }

        # Setup event listeners
        self._setup_event_listeners()

    def _setup_event_listeners(self):
        """Setup event listeners to forward to IDE"""
        emitter = self.orchestrator.event_emitter

        # Listen for question generation
        emitter.on(socrates_ai.EventType.QUESTION_GENERATED, self._on_question_generated)

        # Listen for code generation
        emitter.on(socrates_ai.EventType.CODE_GENERATED, self._on_code_generated)

        # Listen for errors
        emitter.on(socrates_ai.EventType.AGENT_ERROR, self._on_agent_error)

        # Listen for all events for logging
        for event_type in [
            socrates_ai.EventType.PROJECT_CREATED,
            socrates_ai.EventType.AGENT_START,
            socrates_ai.EventType.AGENT_COMPLETE,
            socrates_ai.EventType.TOKEN_USAGE,
        ]:
            emitter.on(event_type, self._on_any_event)

    def _on_question_generated(self, event_type, data):
        """Handle question generation event"""
        for callback in self._callbacks["on_question_generated"]:
            callback(data)

    def _on_code_generated(self, event_type, data):
        """Handle code generation event"""
        for callback in self._callbacks["on_code_generated"]:
            callback(data)

    def _on_agent_error(self, event_type, data):
        """Handle agent error event"""
        for callback in self._callbacks["on_error"]:
            callback(data)

    def _on_any_event(self, event_type, data):
        """Forward all events to callbacks"""
        for callback in self._callbacks["on_event"]:
            callback(event_type.value, data)

    def on_question_generated(self, callback: Callable) -> None:
        """Register callback for question generation"""
        self._callbacks["on_question_generated"].append(callback)

    def on_code_generated(self, callback: Callable) -> None:
        """Register callback for code generation"""
        self._callbacks["on_code_generated"].append(callback)

    def on_error(self, callback: Callable) -> None:
        """Register callback for errors"""
        self._callbacks["on_error"].append(callback)

    def on_event(self, callback: Callable) -> None:
        """Register callback for all events"""
        self._callbacks["on_event"].append(callback)

    # Project Management

    def create_project(self, name: str, owner: str, description: str = "") -> Dict[str, Any]:
        """Create a new project"""
        result = self.orchestrator.process_request(
            "project_manager",
            {
                "action": "create_project",
                "project_name": name,
                "owner": owner,
                "description": description,
            },
        )

        if result.get("status") == "success":
            return {"success": True, "project": result.get("project")}
        return {"success": False, "error": result.get("message", "Failed to create project")}

    def list_projects(self, owner: Optional[str] = None) -> Dict[str, Any]:
        """List projects"""
        result = self.orchestrator.process_request(
            "project_manager", {"action": "list_projects", "owner": owner}
        )

        return {"projects": result.get("projects", []), "total": len(result.get("projects", []))}

    def load_project(self, project_id: str) -> Optional[Dict[str, Any]]:
        """Load a specific project"""
        result = self.orchestrator.process_request(
            "project_manager", {"action": "load_project", "project_id": project_id}
        )

        if result.get("status") == "success":
            return result.get("project")
        return None

    # Question Management

    def ask_question(self, project_id: str, topic: Optional[str] = None) -> Dict[str, Any]:
        """Generate a Socratic question"""
        # Load project first
        project = self.load_project(project_id)
        if not project:
            return {"success": False, "error": f"Project {project_id} not found"}

        result = self.orchestrator.process_request(
            "socratic_counselor",
            {"action": "generate_question", "project": project},
        )

        if result.get("status") == "success":
            return {
                "success": True,
                "question": result.get("question"),
            }
        return {"success": False, "error": result.get("message", "Failed to generate question")}

    # Code Generation

    def generate_code(
        self, project_id: str, specification: str = "", language: str = "python"
    ) -> Dict[str, Any]:
        """Generate code for a project"""
        # Load project first
        project = self.load_project(project_id)
        if not project:
            return {"success": False, "error": f"Project {project_id} not found"}

        result = self.orchestrator.process_request(
            "code_generator",
            {
                "action": "generate_code",
                "project": project,
                "specification": specification,
                "language": language,
            },
        )

        if result.get("status") == "success":
            return {
                "success": True,
                "code": result.get("script", ""),
                "explanation": result.get("explanation"),
                "language": language,
                "token_usage": result.get("token_usage"),
            }
        return {"success": False, "error": result.get("message", "Failed to generate code")}

    # Testing Connection

    def test_connection(self) -> bool:
        """Test API connection"""
        try:
            self.orchestrator.claude_client.test_connection()
            return True
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False


# PyCharm Plugin Integration Example
class SocratesToolWindowFactory:
    """
    Example PyCharm plugin tool window that uses the Socrates bridge

    This would be registered in your plugin.xml:

    <extensions defaultExtensionNs="com.intellij">
        <toolWindow id="Socrates" secondary="true" icon="/icons/socrates.svg"
                    factoryClass="socrates_plugin.SocratesToolWindowFactory"/>
    </extensions>
    """

    def __init__(self, project):
        """Initialize tool window for PyCharm project"""
        self.pycharm_project = project
        self.socrates_bridge = None
        self.current_project_id = None
        self.logger = logging.getLogger(__name__)

    def create_tool_window_content(self, tool_window):
        """Create the Socrates tool window in PyCharm"""
        # This would create UI components in PyCharm
        # For this example, we just show the API structure

        # Initialize Socrates bridge
        api_key = self._get_api_key_from_settings()
        if api_key:
            self.socrates_bridge = SocratesBridge(
                api_key=api_key, project_dir=str(self.pycharm_project.base_path)
            )

            # Register event handlers
            self.socrates_bridge.on_question_generated(self._display_question)
            self.socrates_bridge.on_code_generated(self._display_code)
            self.socrates_bridge.on_error(self._display_error)

    def _display_question(self, data: Dict[str, Any]):
        """Display a question in PyCharm UI"""
        # This would update the PyCharm tool window
        print(f"Question: {data.get('question')}")
        if data.get("hints"):
            print(f"Hints: {', '.join(data['hints'])}")

    def _display_code(self, data: Dict[str, Any]):
        """Display generated code in PyCharm"""
        # This would open a new editor tab with the code
        print(f"Generated {data.get('lines')} lines of code")
        # In real plugin, would call:
        # psi_file = PsiFileFactory.getInstance(self.pycharm_project).create_file_from_text(...)
        # new_file = file_editor_manager.open_file(psi_file, ...)

    def _display_error(self, data: Dict[str, Any]):
        """Display errors in PyCharm"""
        # This would show a notification in PyCharm
        print(f"Error: {data.get('error')}")
        # In real plugin, would call:
        # Notifications.Bus.notify(notification)

    def _get_api_key_from_settings(self) -> Optional[str]:
        """
        Get API key from environment variable.

        The API key should be stored in the ANTHROPIC_API_KEY environment variable
        for security reasons. Do NOT hardcode API keys in source files.

        Setup Instructions:

        Linux/macOS:
            export ANTHROPIC_API_KEY="your-api-key-here"
            # Add to ~/.bashrc, ~/.zshrc, or ~/.profile to persist

        Windows (PowerShell):
            $env:ANTHROPIC_API_KEY="your-api-key-here"
            # To persist: [Environment]::SetEnvironmentVariable("ANTHROPIC_API_KEY", "your-key", "User")

        Windows (Command Prompt):
            set ANTHROPIC_API_KEY=your-api-key-here
            # To persist: setx ANTHROPIC_API_KEY "your-api-key-here"

        PyCharm IDE:
            1. Go to: Run → Edit Configurations
            2. Select your run configuration
            3. Under "Environment variables", add:
               ANTHROPIC_API_KEY=your-api-key-here

        Alternative (via .env file):
            1. Create a .env file in your project root (do NOT commit this!)
            2. Add: ANTHROPIC_API_KEY=your-api-key-here
            3. Load it with: python-dotenv (pip install python-dotenv)
        """
        api_key = os.environ.get("ANTHROPIC_API_KEY")

        if not api_key:
            self.logger.error(
                "ANTHROPIC_API_KEY environment variable not set. "
                "Please set it to your Claude API key."
            )

        return api_key

    def start_interactive_session(self, project_id: str):
        """Start an interactive Socratic learning session"""
        self.current_project_id = project_id

        # Get initial question
        result = self.socrates_bridge.ask_question(project_id)
        if result["success"]:
            self._display_question({"question": result["question"]})

    def submit_response(self, response: str):
        """Submit user response to current question"""
        if not self.current_project_id:
            return

        # Ask next question
        next_q = self.socrates_bridge.ask_question(self.current_project_id)
        if next_q["success"]:
            self._display_question({"question": next_q["question"]})


# Example usage in a PyCharm plugin action
class GenerateCodeAction:
    """Example PyCharm action for generating code"""

    def __init__(self, bridge: SocratesBridge):
        self.bridge = bridge

    def actionPerformed(self, event):
        """Called when user triggers the action"""
        # Get current file/project info from PyCharm
        project_id = "proj_abc123"  # Would get from PyCharm project context

        # Get user input for specification
        specification = "Create a FastAPI endpoint for user authentication"

        # Generate code
        result = self.bridge.generate_code(project_id, specification, language="python")

        if result["success"]:
            # Insert code into current editor
            code = result["code"]
            explanation = result["explanation"]

            # In real plugin:
            # editor = data_context.get_required_data(CommonDataKeys.EDITOR)
            # editor.document.insert_string(caret_offset, code)
            print(f"Generated code:\n{code}")
            print(f"\nExplanation:\n{explanation}")
        else:
            # Show error notification
            print(f"Error: {result['error']}")


def demo():
    """Demo the Socrates Bridge with actual API calls"""
    import os

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        print("Please set it and try again: export ANTHROPIC_API_KEY='your-key'")
        return

    print("Initializing Socrates Bridge...")
    bridge = SocratesBridge(api_key=api_key, project_dir=None)

    print("\nBridge initialized successfully!")
    print(f"Orchestrator: {bridge.orchestrator}")
    print(f"Config: {bridge.config.claude_model}")

    # Demo: Create a project
    print("\n" + "=" * 60)
    print("Demo: Creating a project...")
    print("=" * 60)
    try:
        result = bridge.create_project(
            project_name="Example API Project",
            owner="demo_user",
            description="A demonstration project"
        )
        print(f"✓ Project created: {result}")
    except Exception as e:
        print(f"✗ Error creating project: {e}")

    # Demo: Ask a question
    print("\n" + "=" * 60)
    print("Demo: Asking a Socratic question...")
    print("=" * 60)
    try:
        result = bridge.ask_question(project_id="demo_project")
        print(f"✓ Question: {result.get('question')}")
    except Exception as e:
        print(f"✗ Error asking question: {e}")


if __name__ == "__main__":
    import sys

    if "--help" in sys.argv or "-h" in sys.argv:
        print("PyCharm Plugin Integration Example")
        print("-" * 50)
        print()
        print("This module provides SocratesBridge for PyCharm plugin development.")
        print()
        print("In your PyCharm plugin:")
        print("1. Install: pip install socrates-ai")
        print("2. Initialize: bridge = SocratesBridge(api_key='...')")
        print("3. Register callbacks: bridge.on_question_generated(callback)")
        print("4. Use methods: bridge.ask_question(), bridge.generate_code(), etc.")
        print()
        print("For full plugin development, see:")
        print("https://plugins.jetbrains.com/docs/intellij/welcome.html")
    else:
        demo()
