"""Agent implementations for Socratic RAG System"""

from .base import Agent
from .project_manager import ProjectManagerAgent
from .user_manager import UserManagerAgent
from .socratic_counselor import SocraticCounselorAgent
from .context_analyzer import ContextAnalyzerAgent
from .code_generator import CodeGeneratorAgent
from .system_monitor import SystemMonitorAgent
from .conflict_detector import ConflictDetectorAgent
from .document_processor import DocumentAgent

__all__ = [
    'Agent',
    'ProjectManagerAgent',
    'UserManagerAgent',
    'SocraticCounselorAgent',
    'ContextAnalyzerAgent',
    'CodeGeneratorAgent',
    'SystemMonitorAgent',
    'ConflictDetectorAgent',
    'DocumentAgent'
]
