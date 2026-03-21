# socrates_openclaw/skill.py

"""
Socratic Discovery Skill for OpenClaw.

Main orchestrator that coordinates all components for Socratic project discovery.
"""

import time
import uuid
from pathlib import Path
from typing import Dict, Optional, Any
from datetime import datetime

from socrates_ai import SocraticAgent, KnowledgeBase
from socrates_ai.rag import ChromaVectorStore

from .config import SocraticConfig, get_config
from .components.session_manager import SessionManager
from .components.question_engine import QuestionEngine
from .components.response_processor import ResponseProcessor
from .components.spec_generator import SpecificationGenerator
from .components.storage_handler import StorageHandler


class SocraticDiscoverySkill:
    """
    Socratic Discovery Skill for OpenClaw.

    Guides users through structured project discovery using Socratic questioning.
    """

    def __init__(
            self,
            workspace_root: Optional[Path] = None,
            model: Optional[str] = None,
            temperature: Optional[float] = None,
    ):
        """
        Initialize Socratic Discovery Skill.

        Args:
            workspace_root: Root workspace directory
            model: Claude model to use
            temperature: Model temperature
        """
        # Configuration
        self.config = SocraticConfig(
            workspace_root=workspace_root,
            model=model,
            temperature=temperature,
        )

        # Initialize components
        self.sessions = SessionManager(self.config)

        # Initialize socrates-ai components
        self.vector_store = ChromaVectorStore(
            path=str(self.config.vectors_dir),
            collection_name="socratic_discovery"
        )

        self.knowledge_base = KnowledgeBase(
            persist_directory=str(self.config.kb_dir)
        )

        self.agent = SocraticAgent(
            model=self.config.model,
            vector_db=self.vector_store,
            knowledge_base=self.knowledge_base
        )

        # Initialize skill components
        self.questions = QuestionEngine(self.config, self.agent)
        self.processor = ResponseProcessor(self.knowledge_base, self.config)
        self.generator = SpecificationGenerator(self.agent)
        self.storage = StorageHandler(self.config)

        if self.config.debug:
            print(f"✓ SocraticDiscoverySkill initialized with config: {self.config}")

    async def start_discovery(self, topic: str, user_id: str = "default") -> Dict[str, Any]:
        """
        Start a new Socratic discovery session.

        Args:
            topic: The project or concept to discover
            user_id: User identifier (default: "default")

        Returns:
            Dictionary with session_id, first question, and metadata

        Example:
            >>> result = await skill.start_discovery("SaaS app")
            >>> print(result["question"])
            "What problem does this solve?"
        """
        try:
            # Create session
            session_id = self.sessions.create_session(topic, user_id)

            if self.config.debug:
                print(f"✓ Created session: {session_id}")

            # Get first question
            first_question = self.questions.get_first_question(topic)

            if self.config.debug:
                print(f"✓ Generated first question: {first_question}")

            # Store question in session
            session_data = self.sessions.get_session(session_id)
            session_data["questions"].append(first_question)
            self.sessions.save_session(session_id, session_data)

            return {
                "status": "started",
                "session_id": session_id,
                "topic": topic,
                "question": first_question,
                "progress": {
                    "step": 1,
                    "questions_asked": 1,
                    "responses_recorded": 0
                },
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "model": self.config.model,
                    "version": "1.0.0"
                }
            }

        except Exception as e:
            print(f"✗ Error in start_discovery: {e}")
            return {
                "status": "error",
                "error": str(e),
                "topic": topic
            }

    async def respond(
            self,
            session_id: str,
            response: str
    ) -> Dict[str, Any]:
        """
        Record user response and get next question.

        Args:
            session_id: Session ID from start_discovery
            response: User's response to the question

        Returns:
            Dictionary with next question or completion status

        Example:
            >>> result = await skill.respond(session_id, "Helps teams collaborate")
            >>> print(result["question"])
            "Who is your target user?"
        """
        try:
            # Get session
            session = self.sessions.get_session(session_id)

            if not session:
                return {
                    "status": "error",
                    "error": f"Session {session_id} not found"
                }

            if self.config.debug:
                print(f"✓ Processing response for session: {session_id}")

            # Validate response
            if not self.processor.validate_response(response):
                return {
                    "status": "invalid",
                    "error": "Response too short. Please provide more detail.",
                    "session_id": session_id
                }

            # Store response in knowledge base
            try:
                last_question = session["questions"][-1] if session["questions"] else "Initial"
                self.processor.store_in_knowledge_base(
                    session_id,
                    f"Q: {last_question}\nA: {response}",
                    {"session_id": session_id, "type": "response"}
                )
            except Exception as e:
                print(f"⚠ Warning: KB storage failed: {e}")

            # Add response to session
            session["responses"].append(response)
            self.sessions.save_session(session_id, session)

            # Check if ready for specification
            if self.processor.should_generate_spec(session):
                return {
                    "status": "ready_for_spec",
                    "message": "You have provided enough information. Ready to generate specification.",
                    "session_id": session_id,
                    "progress": {
                        "questions_asked": len(session["questions"]),
                        "responses_recorded": len(session["responses"])
                    }
                }

            # Get next question
            context = self._format_context(session)
            next_question = self.questions.get_next_question(
                session["topic"],
                context,
                len(session["questions"])
            )

            if self.config.debug:
                print(f"✓ Generated next question")

            # Store question in session
            session["questions"].append(next_question)
            self.sessions.save_session(session_id, session)

            return {
                "status": "question_asked",
                "session_id": session_id,
                "question": next_question,
                "progress": {
                    "questions_asked": len(session["questions"]),
                    "responses_recorded": len(session["responses"]),
                    "ready_for_spec": self.processor.should_generate_spec(session)
                }
            }

        except Exception as e:
            print(f"✗ Error in respond: {e}")
            return {
                "status": "error",
                "error": str(e),
                "session_id": session_id
            }

    async def generate(self, session_id: str) -> Dict[str, Any]:
        """
        Generate project specification from discovery session.

        Args:
            session_id: Session ID from start_discovery

        Returns:
            Dictionary with generated specification and saved artifacts

        Example:
            >>> result = await skill.generate(session_id)
            >>> print(result["spec"])
            "# Project Specification\n\n## Overview\n..."
        """
        try:
            # Get session
            session = self.sessions.get_session(session_id)

            if not session:
                return {
                    "status": "error",
                    "error": f"Session {session_id} not found"
                }

            if self.config.debug:
                print(f"✓ Generating specification for session: {session_id}")

            # Format context
            context = self._format_context(session)

            # Generate specification
            spec = self.generator.generate_spec(session["topic"], context)

            if self.config.debug:
                print(f"✓ Specification generated ({len(spec)} chars)")

            # Create artifacts
            artifacts = {
                "PROJECT.md": spec,
                "REQUIREMENTS.md": self.generator.generate_requirements(session),
                "ARCHITECTURE.md": self.generator.generate_architecture(session)
            }

            # Save project
            project_slug = session["topic"].lower().replace(" ", "-")[:50]
            project_dir = self.storage.save_project(project_slug, artifacts)

            if self.config.debug:
                print(f"✓ Project saved to: {project_dir}")

            # Update session
            session["phase"] = "specification"
            session["spec_generated_at"] = datetime.now().isoformat()
            self.sessions.save_session(session_id, session)

            return {
                "status": "spec_generated",
                "session_id": session_id,
                "topic": session["topic"],
                "project": project_slug,
                "spec": spec,
                "saved_to": str(project_dir),
                "artifacts": list(artifacts.keys()),
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "questions_asked": len(session["questions"]),
                    "responses_recorded": len(session["responses"])
                }
            }

        except Exception as e:
            print(f"✗ Error in generate: {e}")
            return {
                "status": "error",
                "error": str(e),
                "session_id": session_id
            }

    async def list_projects(self) -> Dict[str, Any]:
        """
        List all discovered projects.

        Returns:
            Dictionary with list of projects
        """
        try:
            projects = self.storage.list_projects()

            return {
                "status": "success",
                "count": len(projects),
                "projects": projects
            }

        except Exception as e:
            print(f"✗ Error in list_projects: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    async def load_project(self, project_name: str) -> Dict[str, Any]:
        """
        Load a previously discovered project.

        Args:
            project_name: Name of the project to load

        Returns:
            Dictionary with project artifacts
        """
        try:
            artifacts = self.storage.load_project(project_name)

            if not artifacts:
                return {
                    "status": "error",
                    "error": f"Project {project_name} not found"
                }

            return {
                "status": "success",
                "project": project_name,
                "artifacts": artifacts
            }

        except Exception as e:
            print(f"✗ Error in load_project: {e}")
            return {
                "status": "error",
                "error": str(e)
            }

    def _format_context(self, session: Dict[str, Any]) -> str:
        """
        Format session data as context string for question generation.

        Args:
            session: Session dictionary

        Returns:
            Formatted context string
        """
        lines = [f"Topic: {session['topic']}\n"]

        for q, r in zip(session.get("questions", []), session.get("responses", [])):
            lines.append(f"Q: {q}")
            lines.append(f"A: {r}\n")

        return "\n".join(lines)


# Module-level functions for OpenClaw integration

_skill_instance: Optional[SocraticDiscoverySkill] = None


def initialize_skill(
        workspace_root: Optional[Path] = None,
        model: Optional[str] = None,
        temperature: Optional[float] = None
) -> SocraticDiscoverySkill:
    """
    Initialize skill instance.

    Args:
        workspace_root: Root workspace directory
        model: Claude model to use
        temperature: Model temperature

    Returns:
        Initialized SocraticDiscoverySkill instance
    """
    global _skill_instance
    _skill_instance = SocraticDiscoverySkill(
        workspace_root=workspace_root,
        model=model,
        temperature=temperature
    )
    return _skill_instance


def get_skill() -> SocraticDiscoverySkill:
    """
    Get initialized skill instance (creates if needed).

    Returns:
        SocraticDiscoverySkill instance
    """
    global _skill_instance
    if _skill_instance is None:
        _skill_instance = SocraticDiscoverySkill()
    return _skill_instance


# OpenClaw Tool Exports
# These functions are called by OpenClaw's tool system

async def socratic_discover(topic: str) -> Dict[str, Any]:
    """
    OpenClaw tool: Start Socratic discovery.

    Args:
        topic: Project topic to discover

    Returns:
        Dictionary with session_id and first question
    """
    skill = get_skill()
    return await skill.start_discovery(topic)


async def socratic_respond(session_id: str, response: str) -> Dict[str, Any]:
    """
    OpenClaw tool: Record response and get next question.

    Args:
        session_id: Session ID from discover
        response: User's response to previous question

    Returns:
        Dictionary with next question or completion status
    """
    skill = get_skill()
    return await skill.respond(session_id, response)


async def socratic_generate(session_id: str) -> Dict[str, Any]:
    """
    OpenClaw tool: Generate project specification.

    Args:
        session_id: Session ID from discover

    Returns:
        Dictionary with generated specification
    """
    skill = get_skill()
    return await skill.generate(session_id)


async def socratic_list() -> Dict[str, Any]:
    """
    OpenClaw tool: List all discovered projects.

    Returns:
        Dictionary with list of projects
    """
    skill = get_skill()
    return await skill.list_projects()


async def socratic_load(project_name: str) -> Dict[str, Any]:
    """
    OpenClaw tool: Load a discovered project.

    Args:
        project_name: Name of project to load

    Returns:
        Dictionary with project artifacts
    """
    skill = get_skill()
    return await skill.load_project(project_name)


# Initialize on import
initialize_skill()

__all__ = [
    "SocraticDiscoverySkill",
    "initialize_skill",
    "get_skill",
    "socratic_discover",
    "socratic_respond",
    "socratic_generate",
    "socratic_list",
    "socratic_load",
]
