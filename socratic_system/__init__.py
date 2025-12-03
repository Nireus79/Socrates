"""
Socratic RAG System - A Socratic method tutoring system powered by Claude AI

A modularized RAG (Retrieval-Augmented Generation) system that uses Claude AI
to guide developers through the Socratic method, helping them think through
architectural and design decisions for their software projects.

Key Components:
- Models: Data models for users, projects, knowledge entries
- Database: Vector and project database persistence layers
- Agents: Specialized agents for different system responsibilities
- Clients: API client integrations (Claude, etc.)
- Orchestration: Central coordination and agent management
- UI: User interface and application entry point
"""

__version__ = "7.0.0"

# Import key classes for convenient access
from .models import User, ProjectContext, KnowledgeEntry, TokenUsage, ConflictInfo
from .orchestration import AgentOrchestrator
from .clients import ClaudeClient
from .ui import SocraticRAGSystem

__all__ = [
    'User',
    'ProjectContext',
    'KnowledgeEntry',
    'TokenUsage',
    'ConflictInfo',
    'AgentOrchestrator',
    'ClaudeClient',
    'SocraticRAGSystem',
]
