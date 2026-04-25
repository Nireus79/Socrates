# Divergence Code Examples
## Side-by-Side Comparison of Key Changes

---

## 1. BASE AGENT CLASS - ARCHITECTURAL CHANGE

### MONOLITH VERSION
```python
"""Base Agent class for Socrates AI"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

from socratic_system.events import EventType

if TYPE_CHECKING:
    from socratic_system.orchestration.orchestrator import AgentOrchestrator


class Agent(ABC):
    """Abstract base class for all agents in the Socrates AI."""

    def __init__(self, name: str, orchestrator: "AgentOrchestrator"):
        """Initialize an agent.

        Args:
            name: Display name for the agent
            orchestrator: Reference to the AgentOrchestrator (REQUIRED)
        """
        self.name = name
        self.orchestrator = orchestrator  # ← REQUIRED PARAMETER
        self.logger = logging.getLogger(f"socrates.agents.{name}")

    @abstractmethod
    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request and return a response (synchronous)."""
        pass

    async def process_async(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request asynchronously."""
        return await asyncio.to_thread(self.process, request)
```

### LIBRARY VERSION
```python
"""Base Agent class for Socratic Agents - aligned with monolithic standards."""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Optional

from ..events import EventType

if TYPE_CHECKING:
    from ..orchestration import AgentOrchestrator


class Agent(ABC):
    """Abstract base class for all agents in Socratic Agents."""

    def __init__(
        self,
        name: str,
        orchestrator: Optional["AgentOrchestrator"] = None,  # ← OPTIONAL
        llm_client: Optional[Any] = None,  # ← NEW PARAMETER
    ):
        """Initialize an agent.

        Args:
            name: Display name for the agent
            orchestrator: Reference to the AgentOrchestrator
                         If not provided, a mock orchestrator will be created.  # ← FALLBACK
            llm_client: Optional LLM client (accepted for backward compatibility)
        """
        self.name = name
        self.logger = logging.getLogger(f"socratic_agents.{name}")  # ← NAMESPACE CHANGED
        self.created_at = datetime.utcnow()  # ← NEW FIELD

        # Create mock orchestrator if not provided  # ← NEW FALLBACK LOGIC
        if orchestrator is None:
            orchestrator = self._create_mock_orchestrator()
        self.orchestrator = orchestrator

    @staticmethod
    def _create_mock_orchestrator() -> "AgentOrchestrator":  # ← NEW METHOD
        """Create a mock orchestrator for standalone agent usage."""
        from ..events import EventBus

        class MockOrchestrator:
            def __init__(self):
                self.event_emitter = EventBus()

        return MockOrchestrator()  # type: ignore

    @abstractmethod
    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request and return a response (synchronous)."""
        pass

    async def process_async(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a request asynchronously."""
        return await asyncio.to_thread(self.process, request)

    def __repr__(self) -> str:  # ← NEW METHOD
        return f"{self.__class__.__name__}(name='{self.name}')"


# Backwards compatibility alias  # ← NEW
BaseAgent = Agent
```

### BREAKING CHANGES:
1. **Orchestrator Parameter**: REQUIRED → OPTIONAL (breaks existing code)
2. **New Parameter**: llm_client added (may break subclass constructors)
3. **Fallback Logic**: Creates mock orchestrator if None (different behavior)
4. **Logger Namespace**: "socrates.agents" → "socratic_agents" (different logs)
5. **Timestamp Type**: datetime.now() → datetime.utcnow() (timezone difference)
6. **New Fields**: created_at timestamp added
7. **New Methods**: __repr__ and _create_mock_orchestrator
8. **New Alias**: BaseAgent = Agent (backward compatibility)

---

## 2. CODE GENERATOR - COMPLETE REWRITE (748 LINES ADDED)

### MONOLITH VERSION (333 lines)
```python
"""Code generation agent for Socrates AI"""

from pathlib import Path
from typing import Any, Dict

from socratic_system.models import ProjectContext
from socratic_system.utils.artifact_saver import ArtifactSaver
from .base import Agent


class CodeGeneratorAgent(Agent):
    """Generates code and documentation based on project context"""

    def __init__(self, orchestrator):
        super().__init__("CodeGenerator", orchestrator)
        self.current_user = None

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process artifact generation requests"""
        action = request.get("action")

        if action == "generate_artifact":
            return self._generate_artifact(request)
        elif action == "generate_documentation":
            return self._generate_documentation(request)
        elif action == "generate_script":
            return self._generate_artifact(request)

        return {"status": "error", "message": "Unknown action"}

    def _generate_artifact(self, request: Dict) -> Dict:
        """Generate project-type-appropriate artifact"""
        # [implementation details - 100+ lines]
        pass

    def _generate_documentation(self, request: Dict) -> Dict:
        """Generate documentation for artifact"""
        # [implementation details]
        pass
```

### LIBRARY VERSION (1081 lines)
```python
"""Code Generator Agent - Intelligent multi-file project generation.

This agent:
1. Generates code from specifications and requirements
2. Supports 6 project types (web app, API, library, CLI tool, microservice, data pipeline)
3. Creates multi-file project structures with intelligent organization
4. Integrates with knowledge base for artifact persistence
5. Supports 40+ programming languages
6. Generates complete project configurations and documentation
"""

import json
import logging
import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, cast

from .base import BaseAgent

logger = logging.getLogger(__name__)


class ProjectType(Enum):  # ← NEW CLASS
    """Supported project types."""
    WEB_APP = "web_app"
    REST_API = "rest_api"
    LIBRARY = "library"
    CLI_TOOL = "cli_tool"
    MICROSERVICE = "microservice"
    DATA_PIPELINE = "data_pipeline"


class GeneratedFile:  # ← NEW CLASS
    """Represents a generated file in a project."""

    def __init__(self, path: str, content: str, language: str = ""):
        self.id = f"file_{uuid.uuid4().hex[:8]}"
        self.path = path
        self.content = content
        self.language = language
        self.created_at = datetime.utcnow()
        self.size = len(content)
        self.lines = len(content.split("\n"))


class GeneratedProject:  # ← NEW CLASS
    """Represents a complete generated project."""

    def __init__(self, project_id: str, project_type: str, language: str):
        self.id = project_id
        self.type = project_type
        self.language = language
        self.created_at = datetime.utcnow()
        self.files: Dict[str, GeneratedFile] = {}
        self.structure: Dict[str, Any] = {}
        self.metadata: Dict[str, Any] = {}

    def add_file(self, path: str, content: str, language: str = "") -> GeneratedFile:
        """Add a file to the project."""
        file_obj = GeneratedFile(path, content, language)
        self.files[path] = file_obj
        return file_obj


class CodeGenerator(BaseAgent):  # ← CLASS NAME CHANGED
    """
    Agent that generates complete, multi-file projects from requirements.

    Supports:
    - 6 project types (web app, API, library, CLI tool, microservice, data pipeline)
    - 40+ programming languages
    - Multi-file project generation with intelligent organization
    - Integration with knowledge base for persistence
    """

    def __init__(self, llm_client: Optional[Any] = None, knowledge_store: Optional[Any] = None):
        # ← DIFFERENT __init__ SIGNATURE
        """
        Initialize the Code Generator.

        Args:
            llm_client: Optional LLM client for code generation
            knowledge_store: Optional knowledge store for artifact persistence
        """
        super().__init__(name="CodeGenerator", llm_client=llm_client)  # ← NO ORCHESTRATOR
        self.llm_client = llm_client
        self.knowledge_store = knowledge_store
        self.logger = logging.getLogger(f"{__name__}.CodeGenerator")
        self.generated_projects: Dict[str, GeneratedProject] = {}

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process a code generation request."""
        action = request.get("action", "generate")  # ← DIFFERENT DEFAULT

        if action == "generate":
            return self._handle_generate(request)  # ← RENAMED METHOD
        elif action == "generate_project":
            return self._handle_generate_project(request)  # ← NEW ACTION
        elif action == "generate_with_explanation":
            return self._handle_generate_with_explanation(request)  # ← NEW ACTION
        elif action == "get_project":
            return self._handle_get_project(request)  # ← NEW ACTION
        elif action == "list_projects":
            return self._handle_list_projects(request)  # ← NEW ACTION
        else:
            return {"status": "error", "message": f"Unknown action: {action}"}

    def _handle_generate(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle basic single-file code generation."""
        # [60+ lines of NEW implementation]
        pass

    def _handle_generate_project(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Handle multi-file project generation."""
        # [80+ lines of NEW implementation]
        pass

    # ... 60+ more methods not in monolith ...
```

### KEY DIFFERENCES:
- **Constructor**: `(orchestrator)` → `(llm_client=None, knowledge_store=None)`
- **Class Name**: `CodeGeneratorAgent` → `CodeGenerator`
- **Actions**: "generate_artifact" → "generate" (different action names)
- **Support Classes**: Added ProjectType, GeneratedFile, GeneratedProject enums
- **Methods**: 6 methods → 66 methods (1100% increase in function count)
- **Dependency**: orchestrator → llm_client + knowledge_store
- **Size**: 333 lines → 1081 lines (748 lines added)

---

## 3. USER MANAGER - MASSIVE EXPANSION (486 LINES ADDED)

### MONOLITH VERSION (89 lines)
```python
"""User management agent"""

from typing import Any, Dict, Optional
from .base import Agent


class UserManagerAgent(Agent):
    """Manages user sessions and data"""

    def __init__(self, orchestrator):
        super().__init__("UserManager", orchestrator)

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process user management requests"""
        action = request.get("action")

        if action == "get_user":
            return self._get_user(request)
        elif action == "update_user":
            return self._update_user(request)
        elif action == "list_users":
            return self._list_users(request)
        # ... 2-3 more actions

        return {"status": "error", "message": "Unknown action"}

    # 6 total methods
```

### LIBRARY VERSION (575 lines)
```python
"""User Manager - Comprehensive user management and administration."""

from enum import Enum
from typing import Any, Dict, List, Optional
from .base import BaseAgent


class UserRole(Enum):  # ← NEW ENUM
    """User roles for access control."""
    ADMIN = "admin"
    USER = "user"
    GUEST = "guest"


class UserManager(BaseAgent):  # ← CLASS NAME CHANGED
    """
    Comprehensive user management with roles, permissions, and analytics.

    Supports:
    - User CRUD operations
    - Role-based access control
    - Learning statistics tracking
    - User recovery and archival
    - Team management
    """

    def __init__(self, llm_client: Optional[Any] = None):
        # ← DIFFERENT __init__
        super().__init__(name="UserManager", llm_client=llm_client)
        self.users: Dict[str, Any] = {}
        self.archived_users: Dict[str, Any] = {}
        self.user_roles: Dict[str, UserRole] = {}

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Process user management requests."""
        action = request.get("action", "get_user")

        handlers = {
            "get_user": self._get_user,
            "create_user": self._create_user,  # ← NEW
            "update_user": self._update_user,
            "delete_user": self._delete_user,  # ← NEW
            "list_users": self._list_users,
            "restore_user": self._restore_user,  # ← NEW
            "update_learning_stats": self._update_learning_stats,  # ← NEW
            "archive_user": self._archive_user,  # ← NEW
            "add_to_team": self._add_to_team,  # ← NEW
            "remove_from_team": self._remove_from_team,  # ← NEW
            # ... 14+ more handlers
        }

        handler = handlers.get(action)
        if handler:
            return handler(request)
        return {"status": "error", "message": f"Unknown action: {action}"}

    def _get_user(self, request: Dict[str, Any]) -> Dict[str, Any]:
        # ← NEW IMPLEMENTATION (not same as monolith)
        user_id = request.get("user_id")
        if user_id in self.users:
            return {"status": "success", "user": self.users[user_id].to_dict()}
        return {"status": "error", "message": "User not found"}

    def _create_user(self, request: Dict[str, Any]) -> Dict[str, Any]:
        # ← NEW METHOD IN LIBRARY
        user_data = request.get("user_data", {})
        user_id = self._generate_user_id()
        # ... 20+ lines of implementation
        pass

    def _delete_user(self, request: Dict[str, Any]) -> Dict[str, Any]:
        # ← NEW METHOD IN LIBRARY
        user_id = request.get("user_id")
        if user_id in self.users:
            user = self.users.pop(user_id)
            self.archived_users[user_id] = user
            return {"status": "success", "message": "User deleted and archived"}
        return {"status": "error", "message": "User not found"}

    # ... 19+ more methods (24 total methods vs 6 in monolith) ...
```

### KEY DIFFERENCES:
- **Constructor**: `(orchestrator)` → `(llm_client=None)`
- **Class Name**: `UserManagerAgent` → `UserManager` (same suffix but different base)
- **New Enum**: `UserRole` (admin, user, guest)
- **Methods**: 6 methods → 24 methods (300% increase)
- **New Features**: User archival, team management, learning statistics
- **Size**: 89 lines → 575 lines (547% expansion)
- **Architecture**: Single action handler → Dictionary dispatch pattern

---

## 4. QUALITY CONTROLLER - CRITICAL REDUCTION (356 LINES REMOVED)

### MONOLITH VERSION (747 lines)
```python
class QualityControllerAgent(Agent):
    """Controls and tracks software quality metrics"""

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        action = request.get("action")

        if action == "assess_quality":
            return self._assess_quality(request)
        elif action == "verify_advancement":  # ← REMOVED IN LIBRARY
            return self._verify_advancement(request)
        elif action == "record_maturity":
            return self._record_maturity(request)

    def _verify_advancement(self, request: Dict):  # ← REMOVED IN LIBRARY
        """Verify quality advancement criteria are met"""
        # [50+ lines of maturity verification logic]
        pass

    def _calculate_phase_maturity(self, ...):  # ← REMOVED IN LIBRARY
        """Calculate maturity level for current phase"""
        # [80+ lines of maturity calculation]
        pass

    def _record_maturity_event(self, ...):  # ← REMOVED IN LIBRARY
        """Record maturity milestone event"""
        # [40+ lines of event recording]
        pass

    # Total: 14 methods
```

### LIBRARY VERSION (391 lines)
```python
class QualityController(BaseAgent):  # ← CLASS NAME CHANGED
    """Controls and tracks software quality metrics (simplified)"""

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        action = request.get("action", "assess_quality")

        if action == "assess_quality":
            return self._assess_quality(request)
        elif action == "assess_architecture":  # ← NEW METHOD
            return self._assess_architecture(request)
        elif action == "optimize_workflow":  # ← NEW METHOD
            return self._optimize_workflow(request)

    def _assess_quality(self, request: Dict):
        """Assess overall quality metrics"""
        # [different implementation - 40+ lines]
        pass

    def _assess_architecture(self, request: Dict):  # ← NEW
        """Assess architectural quality"""
        # [new method - 60+ lines]
        pass

    def _optimize_workflow(self, request: Dict):  # ← NEW
        """Suggest workflow optimizations"""
        # [new method - 50+ lines]
        pass

    # Total: 17 methods (but different ones!)
    # MISSING: _verify_advancement, _calculate_phase_maturity, _record_maturity_event
```

### CRITICAL DIFFERENCES:
- **Removed Methods**: _verify_advancement, _calculate_phase_maturity, _record_maturity_event
- **Added Methods**: _assess_architecture, _optimize_workflow, _estimate_completion
- **Size**: 747 lines → 391 lines (48% REDUCTION)
- **Functionality**: Monolith has MORE features than library
- **Risk**: Code depending on removed methods will break

---

## 5. SKILL GENERATORS - NEW AGENTS ONLY IN LIBRARY

### MONOLITH
```
File does not exist
```

### LIBRARY
```python
# skill_generator_agent.py (~400+ lines)
class SkillGeneratorAgent(BaseAgent):
    """Generates skill definitions for agents"""

    def __init__(self, ...):
        ...

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate skills from requirements"""
        ...

# skill_generator_agent_v2.py (~300+ lines)
class SkillGeneratorV2(BaseAgent):
    """Improved skill generation with learning"""

    def __init__(self, ...):
        ...

    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate skills with improvement tracking"""
        ...
```

### IMPACT:
- **700+ lines of NEW agents** not in monolith
- **Two versions**: skill_generator_agent.py and skill_generator_agent_v2.py
- **Missing from Monolith**: No skill generation capability
- **Decision Needed**: Should these be in monolith too?

---

## SUMMARY

### Method Signature Incompatibility Example

**Can you do this with both?**

```python
# Monolith usage
from socratic_system.agents.code_generator import CodeGeneratorAgent

agent = CodeGeneratorAgent(orchestrator)  # REQUIRED orchestrator
result = agent.process({"action": "generate_artifact", "project": proj})
```

**Library equivalent:**
```python
from socratic_agents.agents.code_generator import CodeGenerator

agent = CodeGenerator()  # NO orchestrator needed!
agent = CodeGenerator(llm_client=client, knowledge_store=store)  # Different params!
result = agent.process({"action": "generate", "prompt": "..."})  # Different action names!
```

**Answer: NO - they are completely incompatible**

---

## Divergence Severity Matrix

| Aspect | Monolith | Library | Severity |
|--------|----------|---------|----------|
| Base Class API | orchestrator required | orchestrator optional | CRITICAL |
| Class Names | CodeGeneratorAgent | CodeGenerator | CRITICAL |
| Constructor Params | orchestrator | llm_client, knowledge_store | CRITICAL |
| Code Generator | 333 lines | 1081 lines | CRITICAL |
| User Manager | 89 lines (6 methods) | 575 lines (24 methods) | CRITICAL |
| Quality Controller | 747 lines | 391 lines (48% smaller) | CRITICAL |
| Skill Generators | Don't exist | 700+ lines (2 agents) | CRITICAL |
| New Enums | None | 7 enums | HIGH |
| Logger Namespace | socrates.agents | socratic_agents | MEDIUM |
| Timestamp Type | datetime.now() | datetime.utcnow() | MEDIUM |

---

**Conclusion**: The libraries are NOT compatible drop-in replacements for the monolith agents. They require a compatibility adapter or complete realignment before they can be used together.
