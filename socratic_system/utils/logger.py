"""
Centralized logging system for Socrates AI
Supports debug mode, file logging, and console output
"""

import json
import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional

from colorama import Fore, Style


class DebugLogger:
    """Centralized logging system with debug mode support"""

    _instance: Optional["DebugLogger"] = None
    _debug_mode: bool = False
    _logger: Optional[logging.Logger] = None
    _console_handler: Optional[logging.StreamHandler] = None
    _file_handler: Optional[logging.handlers.TimedRotatingFileHandler] = None

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

        # Debug mode defaults to OFF
        cls._debug_mode = False

        # Ensure root logger is at DEBUG level so it can pass messages to handlers
        # Handlers will filter based on their own levels
        root_logger = logging.getLogger()
        root_logger.setLevel(logging.DEBUG)

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
        cls._file_handler = logging.handlers.TimedRotatingFileHandler(
            log_file,
            when="midnight",  # Rotate at midnight
            interval=1,  # Every 1 day
            backupCount=3,  # Keep 3 days of logs
            utc=False,
        )
        # Use date format for backup files: socratic.log.2024-12-16
        cls._file_handler.suffix = "%Y-%m-%d"
        cls._file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        cls._file_handler.setFormatter(file_formatter)
        cls._logger.addHandler(cls._file_handler)

        # Console handler (shows DEBUG by default, ERROR when enabled)
        cls._console_handler = logging.StreamHandler()
        cls._console_handler.setLevel(logging.DEBUG)  # Default to DEBUG

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
        import sys
        cls._debug_mode = enabled

        # Ensure logger is initialized
        if cls._instance is None:
            cls()

        # Debug: print directly to stderr so we know this function was called
        status = "ENABLED" if enabled else "DISABLED"
        print(f"[LOGGER] set_debug_mode({status}) called", file=sys.stderr)
        print(f"[LOGGER] cls._console_handler = {cls._console_handler}", file=sys.stderr)

        # Update console handler level IMMEDIATELY
        if cls._console_handler:
            new_level = logging.DEBUG if enabled else logging.ERROR
            old_level = cls._console_handler.level
            cls._console_handler.setLevel(new_level)
            print(f"[LOGGER] Console handler level changed: {logging.getLevelName(old_level)} -> {logging.getLevelName(new_level)}", file=sys.stderr)

            # Log the mode change at WARNING level so it's always visible
            logger = cls.get_logger("system")
            if enabled:
                logger.warning(">>> DEBUG MODE ENABLED <<<")
            else:
                logger.warning(">>> DEBUG MODE DISABLED <<<")

        # CRITICAL: Also update ALL standard Python loggers
        # This is essential because the application code uses logging.getLogger()
        # not our DebugLogger singleton
        root_logger = logging.getLogger()

        # Set root logger level to DEBUG when enabling, so messages can pass through handlers
        if enabled:
            root_logger.setLevel(logging.DEBUG)
        else:
            root_logger.setLevel(logging.WARNING)

        # Update all handlers attached to root logger
        new_level = logging.DEBUG if enabled else logging.ERROR
        for handler in root_logger.handlers[:]:
            if isinstance(handler, logging.StreamHandler) and not isinstance(
                handler, logging.FileHandler
            ):
                handler.setLevel(new_level)

        # Update all existing loggers (both with and without handlers)
        # Most loggers propagate to root logger, so they need the right level too
        for logger_name in logging.Logger.manager.loggerDict:
            logger_obj = logging.getLogger(logger_name)
            if logger_obj:
                # Set logger level to DEBUG when debug enabled, WARNING otherwise
                logger_obj.setLevel(logging.DEBUG if enabled else logging.WARNING)

                # Update handlers if they exist
                if hasattr(logger_obj, "handlers"):
                    for handler in logger_obj.handlers[:]:
                        if isinstance(handler, logging.StreamHandler) and not isinstance(
                            handler, logging.FileHandler
                        ):
                            handler.setLevel(new_level)

        # Also update the main socratic_rag logger level
        if cls._logger:
            cls._logger.setLevel(logging.DEBUG if enabled else logging.WARNING)

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
