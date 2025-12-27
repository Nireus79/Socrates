"""Agent implementations for Socratic RAG System"""

from .base import Agent
from .code_generator import CodeGeneratorAgent
from .code_validation_agent import CodeValidationAgent
from .conflict_detector import ConflictDetectorAgent
from .context_analyzer import ContextAnalyzerAgent
from .document_processor import DocumentProcessorAgent
from .knowledge_analysis import KnowledgeAnalysisAgent
from .knowledge_manager import KnowledgeManagerAgent
from .learning_agent import UserLearningAgent
from .multi_llm_agent import MultiLLMAgent
from .note_manager import NoteManagerAgent
from .project_manager import ProjectManagerAgent
from .quality_controller import QualityControllerAgent
from .question_queue_agent import QuestionQueueAgent
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
    "CodeValidationAgent",
    "SystemMonitorAgent",
    "ConflictDetectorAgent",
    "DocumentProcessorAgent",
    "NoteManagerAgent",
    "QualityControllerAgent",
    "KnowledgeAnalysisAgent",
    "KnowledgeManagerAgent",
    "UserLearningAgent",
    "MultiLLMAgent",
    "QuestionQueueAgent",
]
