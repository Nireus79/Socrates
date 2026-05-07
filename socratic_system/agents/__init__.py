"""
Agent implementations for Socrates AI

This module now imports agents from the socratic-agents library.
Local implementations have been removed and replaced with library versions
for Phase 4 refactoring to use extracted libraries.
"""

# Import all agents from socratic-agents library
from socratic_agents import (
    Agent,
    CodeGeneratorAgent,
    CodeValidationAgent,
    ConflictDetectorAgent,
    ContextAnalyzerAgent,
    DocumentProcessorAgent,
    KnowledgeAnalysisAgent,
    KnowledgeManagerAgent,
    MultiLLMAgent,
    NoteManagerAgent,
    ProjectManagerAgent,
    QualityControllerAgent,
    QuestionQueueAgent,
    SocraticCounselorAgent,
    SystemMonitorAgent,
    UserLearningAgent,
    UserManagerAgent,
)

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
