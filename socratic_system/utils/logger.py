"""
Centralized logging system for Socratic RAG System
Supports debug mode, file logging, and console output
"""

import logging
import logging.handlers
from pathlib import Path
from typing import Optional

from colorama import Fore, Style


class DebugLogger:
    """Centralized logging system with debug mode support"""

    _instance: Optional["DebugLogger"] = None
    _debug_mode: bool = False
    _logger: Optional[logging.Logger] = None
    _console_handler: Optional[logging.StreamHandler] = None

    def __new__(cls):
        """Create or return singleton instance of logger."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    @classmethod
    def _initialize(cls):
        """Initialize the logging system"""
        # Create logger
        cls._logger = logging.getLogger("socratic_rag")
        cls._logger.setLevel(logging.DEBUG)
        # Prevent propagation to root logger to avoid duplicate logs
        cls._logger.propagate = False

        # Create logs directory
        logs_dir = Path("socratic_logs")
        logs_dir.mkdir(exist_ok=True)

        # File handler with rotation (always logs everything)
        # Rotates when log file reaches 5MB, keeps up to 5 backup files (~25MB total)
        log_file = logs_dir / "socratic.log"
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=5 * 1024 * 1024,  # 5MB
            backupCount=5,  # Keep 5 backup files (socratic.log.1, .2, .3, .4, .5)
        )
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        cls._logger.addHandler(file_handler)

        # Console handler (shows WARNING by default, DEBUG when enabled)
        cls._console_handler = logging.StreamHandler()
        cls._console_handler.setLevel(logging.WARNING)  # Show WARNING by default

        # Enhanced formatter with better readability
        def format_console_message(record):
            # Color code by level
            if record.levelno >= logging.ERROR:
                level_color = Fore.RED
                prefix = "[ERROR]"
            elif record.levelno >= logging.WARNING:
                level_color = Fore.YELLOW
                prefix = "[WARN]"
            elif record.levelno >= logging.INFO:
                level_color = Fore.GREEN
                prefix = "[INFO]"
            else:  # DEBUG
                level_color = Fore.CYAN
                prefix = "[DEBUG]"

            # Extract component name (e.g., 'socratic_rag.project_manager' -> 'project_manager')
            component = record.name.split(".")[-1] if "." in record.name else record.name

            return f"{level_color}{prefix}{Style.RESET_ALL} {component}: {record.getMessage()}"

        class ConsoleFormatter(logging.Formatter):
            def format(self, record):
                return format_console_message(record)

        console_formatter = ConsoleFormatter()
        cls._console_handler.setFormatter(console_formatter)
        cls._logger.addHandler(cls._console_handler)

    @classmethod
    def set_debug_mode(cls, enabled: bool) -> None:
        """Toggle debug mode on/off"""
        cls._debug_mode = enabled
        if cls._console_handler:
            # In debug mode, show DEBUG and above
            # In normal mode, show WARNING and above
            if enabled:
                cls._console_handler.setLevel(logging.DEBUG)
            else:
                cls._console_handler.setLevel(logging.WARNING)

        # Log the mode change (use WARNING level so it shows even when debug is off)
        logger = cls.get_logger("system")
        if enabled:
            logger.warning("Debug mode ENABLED - all operations will be logged")
        else:
            logger.warning("Debug mode DISABLED - only warnings and errors shown")

    @classmethod
    def is_debug_mode(cls) -> bool:
        """Check if debug mode is enabled"""
        return cls._debug_mode

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """Get a logger for a specific component"""
        return logging.getLogger(f"socratic_rag.{name}")

    @classmethod
    def debug(cls, message: str, component: str = "system") -> None:
        """Log debug message"""
        logger = cls.get_logger(component)
        logger.debug(message)

    @classmethod
    def info(cls, message: str, component: str = "system") -> None:
        """Log info message"""
        logger = cls.get_logger(component)
        logger.info(message)

    @classmethod
    def warning(cls, message: str, component: str = "system") -> None:
        """Log warning message"""
        logger = cls.get_logger(component)
        logger.warning(message)

    @classmethod
    def error(
        cls, message: str, component: str = "system", exception: Optional[Exception] = None
    ) -> None:
        """Log error message"""
        logger = cls.get_logger(component)
        if exception:
            logger.error(f"{message}", exc_info=exception)
        else:
            logger.error(message)


# Global logger instance
def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific component"""
    DebugLogger()  # Ensure initialization
    return DebugLogger.get_logger(name)


def set_debug_mode(enabled: bool) -> None:
    """Toggle debug mode"""
    DebugLogger().set_debug_mode(enabled)


def is_debug_mode() -> bool:
    """Check if debug mode is enabled"""
    return DebugLogger().is_debug_mode()
