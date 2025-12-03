"""
Base Agent class for Socratic RAG System
"""

import datetime
from abc import ABC, abstractmethod
from typing import Dict, Any

from colorama import Fore


class Agent(ABC):
    """
    Abstract base class for all agents in the Socratic RAG System.

    Agents are specialized components that handle different aspects of
    the system (project management, questioning, code generation, etc.).
    """

    def __init__(self, name: str, orchestrator: 'AgentOrchestrator'):
        """
        Initialize an agent.

        Args:
            name: Display name for the agent
            orchestrator: Reference to the AgentOrchestrator for accessing other agents/services
        """
        self.name = name
        self.orchestrator = orchestrator

    @abstractmethod
    def process(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a request and return a response.

        All subclasses must implement this method to handle their specific logic.

        Args:
            request: Dictionary containing the request parameters

        Returns:
            Dictionary containing the response data
        """
        pass

    def log(self, message: str, level: str = "INFO"):
        """
        Log a message with timestamp and color coding.

        Args:
            message: The message to log
            level: Log level (INFO, WARNING, ERROR)
        """
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        color = Fore.GREEN if level == "INFO" else Fore.RED if level == "ERROR" else Fore.YELLOW
        print(f"{color}[{timestamp}] {self.name}: {message}")
