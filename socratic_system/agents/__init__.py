"""Agent implementations for Socratic RAG System"""

from .base import Agent
from .code_generator import CodeGeneratorAgent
from .conflict_detector import ConflictDetectorAgent
from .context_analyzer import ContextAnalyzerAgent
from .document_processor import DocumentProcessorAgent
from .note_manager import NoteManagerAgent
from .project_manager import ProjectManagerAgent
from .quality_controller import QualityControllerAgent
from .socratic_counselor import SocraticCounselorAgent
from .system_monitor import SystemMonitorAgent
from .user_manager import UserManagerAgent

__all__ = [
    "Agent",
    "ProjectManagerAgent",
    "UserManagerAgent",
    "SocraticCounselorAgent",
    "ContextAnalyzerAgent",
    "CodeGeneratorAgent",
    "SystemMonitorAgent",
    "ConflictDetectorAgent",
    "DocumentProcessorAgent",
    "NoteManagerAgent",
    "QualityControllerAgent",
]
