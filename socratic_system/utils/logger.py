"""
Centralized logging system for Socrates AI
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
    def _cleanup_old_logs(cls) -> None:
        """Clean up old log files, keeping only recent ones"""
        logs_dir = Path("socratic_logs")
        if not logs_dir.exists():
            return

        # Find all log files (socratic.log, socratic.log.1, socratic.log.2, etc.)
        log_files = sorted(
            logs_dir.glob("socratic.log*"),
            key=lambda p: p.stat().st_mtime if p.exists() else 0,
            reverse=True,
        )

        # Keep only the 3 most recent log files, delete older ones
        for log_file in log_files[3:]:
            try:
                log_file.unlink()
            except Exception:
                pass

    @classmethod
    def reset(cls) -> None:
        """Reset the logger singleton (clear handlers and reinitialize)"""
        if cls._logger:
            # Remove all handlers
            for handler in cls._logger.handlers[:]:
                handler.close()
                cls._logger.removeHandler(handler)

        cls._instance = None
        cls._logger = None
        cls._console_handler = None
        cls._debug_mode = False  # Reset debug mode to OFF

    @classmethod
    def _initialize(cls):
        """Initialize the logging system"""
        # Clean up old logs first
        cls._cleanup_old_logs()

        # Create logger
        cls._logger = logging.getLogger("socratic_rag")
        cls._logger.setLevel(logging.DEBUG)
        # Prevent propagation to root logger to avoid duplicate logs
        cls._logger.propagate = False

        # Create logs directory
        logs_dir = Path("socratic_logs")
        logs_dir.mkdir(exist_ok=True)

        # File handler with time-based rotation (daily logs)
        # Creates new log file each day: socratic.log, socratic.log.2024-12-16, etc.
        log_file = logs_dir / "socratic.log"
        file_handler = logging.handlers.TimedRotatingFileHandler(
            log_file,
            when="midnight",  # Rotate at midnight
            interval=1,  # Every 1 day
            backupCount=3,  # Keep 3 days of logs
            utc=False,
        )
        # Use date format for backup files: socratic.log.2024-12-16
        file_handler.suffix = "%Y-%m-%d"
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        file_handler.setFormatter(file_formatter)
        cls._logger.addHandler(file_handler)

        # Console handler (shows ERROR by default, DEBUG when enabled)
        cls._console_handler = logging.StreamHandler()
        cls._console_handler.setLevel(logging.ERROR)  # Show ERROR by default

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

        # Ensure logger is fully initialized
        if cls._instance is None or cls._console_handler is None:
            cls()

        # Update console handler level
        if cls._console_handler:
            if enabled:
                cls._console_handler.setLevel(logging.DEBUG)
            else:
                cls._console_handler.setLevel(logging.ERROR)

        # Log the mode change at INFO level so it's visible regardless of debug mode
        logger = cls.get_logger("system")
        if enabled:
            logger.info("Debug mode ENABLED - DEBUG logs now visible")
        else:
            logger.info("Debug mode DISABLED - only INFO+ logs shown")

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


def reset_logger() -> None:
    """Reset the logger singleton (clear old handlers and reinitialize)"""
    DebugLogger.reset()
