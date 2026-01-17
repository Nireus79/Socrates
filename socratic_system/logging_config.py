"""
Comprehensive Logging and Monitoring Configuration for Socrates

Provides structured logging, performance monitoring, and observability.
Supports multiple log handlers (file, console, syslog) and log rotation.
"""

import logging
import logging.handlers
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import json


class JsonFormatter(logging.Formatter):
    """Custom JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON for better parsing and analysis."""
        log_data = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data)


class PerformanceFilter(logging.Filter):
    """Filter for performance monitoring - logs slow operations."""

    def __init__(self, threshold_ms: float = 100):
        """
        Initialize performance filter.

        Args:
            threshold_ms: Threshold in milliseconds for slow operation warning
        """
        super().__init__()
        self.threshold_ms = threshold_ms

    def filter(self, record: logging.LogRecord) -> bool:
        """Add performance metrics to log record if present."""
        if hasattr(record, "duration_ms"):
            if record.duration_ms > self.threshold_ms:
                record.msg = f"[SLOW] {record.msg}"
                record.levelno = max(record.levelno, logging.WARNING)
        return True


class LoggingConfig:
    """Configure logging and monitoring for Socrates application."""

    def __init__(self, log_dir: Path, log_level: str = "INFO", json_logs: bool = False):
        """
        Initialize logging configuration.

        Args:
            log_dir: Directory to store log files
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            json_logs: Whether to use JSON structured logging
        """
        self.log_dir = Path(log_dir)
        self.log_level = getattr(logging, log_level.upper())
        self.json_logs = json_logs
        self._setup_directories()

    def _setup_directories(self) -> None:
        """Create log directories if they don't exist."""
        self.log_dir.mkdir(parents=True, exist_ok=True)
        (self.log_dir / "archive").mkdir(parents=True, exist_ok=True)

    def get_logger(self, name: str) -> logging.Logger:
        """
        Get configured logger instance.

        Args:
            name: Logger name (typically __name__)

        Returns:
            Configured logger instance
        """
        logger = logging.getLogger(name)

        # Avoid duplicate handlers
        if logger.handlers:
            return logger

        logger.setLevel(self.log_level)

        # Add console handler
        console_handler = self._get_console_handler()
        logger.addHandler(console_handler)

        # Add file handler with rotation
        file_handler = self._get_file_handler("socrates.log")
        logger.addHandler(file_handler)

        # Add error file handler
        error_handler = self._get_file_handler("errors.log", level=logging.ERROR)
        logger.addHandler(error_handler)

        # Add performance filter
        perf_filter = PerformanceFilter(threshold_ms=100)
        for handler in logger.handlers:
            handler.addFilter(perf_filter)

        return logger

    def get_api_logger(self) -> logging.Logger:
        """Get logger specifically for API requests/responses."""
        logger = logging.getLogger("socrates.api")

        if logger.handlers:
            return logger

        logger.setLevel(self.log_level)

        # API request/response file handler with detailed format
        api_handler = self._get_file_handler(
            "api.log", level=logging.INFO, max_bytes=10485760  # 10MB
        )
        api_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(method)s %(path)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        api_handler.setFormatter(api_formatter)
        logger.addHandler(api_handler)

        return logger

    def get_database_logger(self) -> logging.Logger:
        """Get logger specifically for database operations."""
        logger = logging.getLogger("socrates.database")

        if logger.handlers:
            return logger

        logger.setLevel(self.log_level)

        # Database operations file handler
        db_handler = self._get_file_handler(
            "database.log", level=logging.INFO, max_bytes=10485760
        )
        db_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - [%(funcName)s] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        db_handler.setFormatter(db_formatter)
        logger.addHandler(db_handler)

        return logger

    def get_performance_logger(self) -> logging.Logger:
        """Get logger for performance monitoring."""
        logger = logging.getLogger("socrates.performance")

        if logger.handlers:
            return logger

        logger.setLevel(logging.INFO)

        # Performance metrics file handler
        perf_handler = self._get_file_handler(
            "performance.log", level=logging.INFO, max_bytes=10485760
        )
        perf_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )
        perf_handler.setFormatter(perf_formatter)
        logger.addHandler(perf_handler)

        return logger

    def _get_console_handler(self) -> logging.StreamHandler:
        """Create console handler with color support."""
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(self.log_level)

        if self.json_logs:
            formatter = JsonFormatter()
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

        handler.setFormatter(formatter)
        return handler

    def _get_file_handler(
        self,
        filename: str,
        level: int = None,
        max_bytes: int = 10485760,  # 10MB default
        backup_count: int = 5,
    ) -> logging.handlers.RotatingFileHandler:
        """Create rotating file handler."""
        if level is None:
            level = self.log_level

        filepath = self.log_dir / filename
        handler = logging.handlers.RotatingFileHandler(
            filepath, maxBytes=max_bytes, backupCount=backup_count
        )
        handler.setLevel(level)

        if self.json_logs:
            formatter = JsonFormatter()
        else:
            formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )

        handler.setFormatter(formatter)
        return handler

    def setup_syslog_handler(
        self, logger_name: str, address: str = "/dev/log"
    ) -> None:
        """
        Add syslog handler for production deployments.

        Args:
            logger_name: Name of logger to configure
            address: Syslog socket address (default: /dev/log for Unix)
        """
        logger = logging.getLogger(logger_name)

        try:
            handler = logging.handlers.SysLogHandler(address=address)
            formatter = logging.Formatter(
                "socrates - %(name)s - %(levelname)s - %(message)s"
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        except Exception as e:
            logger.warning(f"Failed to configure syslog handler: {e}")


class PerformanceMonitor:
    """Monitor and log performance metrics."""

    def __init__(self, logger: logging.Logger):
        """Initialize performance monitor."""
        self.logger = logger

    def log_operation(
        self, operation: str, duration_ms: float, status: str = "success", **kwargs
    ) -> None:
        """
        Log operation timing and status.

        Args:
            operation: Operation name
            duration_ms: Operation duration in milliseconds
            status: Operation status (success, error, warning)
            **kwargs: Additional metrics
        """
        metrics = {
            "operation": operation,
            "duration_ms": duration_ms,
            "status": status,
            **kwargs,
        }

        message = f"{operation} - {duration_ms:.2f}ms - {status}"

        if duration_ms > 1000:  # Warn if over 1 second
            self.logger.warning(message, extra={"extra_data": metrics})
        else:
            self.logger.info(message, extra={"extra_data": metrics})

    def log_api_request(
        self, method: str, path: str, status_code: int, duration_ms: float
    ) -> None:
        """
        Log API request metrics.

        Args:
            method: HTTP method
            path: Request path
            status_code: HTTP status code
            duration_ms: Request duration in milliseconds
        """
        metrics = {
            "method": method,
            "path": path,
            "status_code": status_code,
            "duration_ms": duration_ms,
        }
        message = f"{method} {path} - {status_code} - {duration_ms:.2f}ms"

        if status_code >= 500:
            self.logger.error(message, extra={"extra_data": metrics})
        elif status_code >= 400:
            self.logger.warning(message, extra={"extra_data": metrics})
        else:
            self.logger.info(message, extra={"extra_data": metrics})

    def log_database_query(
        self, query_type: str, duration_ms: float, rows_affected: int = 0
    ) -> None:
        """
        Log database query metrics.

        Args:
            query_type: Type of query (SELECT, INSERT, UPDATE, DELETE)
            duration_ms: Query duration in milliseconds
            rows_affected: Number of rows affected
        """
        metrics = {
            "query_type": query_type,
            "duration_ms": duration_ms,
            "rows_affected": rows_affected,
        }
        message = f"{query_type} - {duration_ms:.2f}ms - {rows_affected} rows"

        if duration_ms > 500:  # Warn if slow query
            self.logger.warning(message, extra={"extra_data": metrics})
        else:
            self.logger.info(message, extra={"extra_data": metrics})


# Global logging instance
_logging_config: Optional[LoggingConfig] = None


def initialize_logging(
    log_dir: Path, log_level: str = "INFO", json_logs: bool = False
) -> LoggingConfig:
    """
    Initialize global logging configuration.

    Args:
        log_dir: Directory to store log files
        log_level: Logging level
        json_logs: Whether to use JSON structured logging

    Returns:
        LoggingConfig instance
    """
    global _logging_config
    _logging_config = LoggingConfig(log_dir, log_level, json_logs)
    return _logging_config


def get_logging_config() -> LoggingConfig:
    """Get global logging configuration instance."""
    if _logging_config is None:
        raise RuntimeError(
            "Logging not initialized. Call initialize_logging() first."
        )
    return _logging_config
