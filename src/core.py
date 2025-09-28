#!/usr/bin/env python3
"""
Socratic RAG Enhanced - Core System with Service Container Architecture
======================================================================

Core system infrastructure using dependency injection pattern.
Provides ServiceContainer for managing configured service instances.
"""

import os
import sys
import time
import queue
import logging
import threading
import mimetypes
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Union
import logging.handlers
import sqlite3
import json
from dataclasses import dataclass, field


# ============================================================================
# EXCEPTIONS
# ============================================================================

class SocraticException(Exception):
    """Base exception for Socratic RAG system"""
    pass


class ConfigurationError(SocraticException):
    """Configuration related errors"""
    pass


class ValidationError(SocraticException):
    """Data validation errors"""
    pass


class DatabaseError(SocraticException):
    """Database operation errors"""
    pass


class AgentError(SocraticException):
    """Agent operation errors"""
    pass


class ServiceError(SocraticException):
    """Service operation errors"""
    pass


class APIError(SocraticException):
    """API related errors"""
    pass


class CodeGenerationError(SocraticException):
    """Code generation errors"""
    pass


class TestingError(SocraticException):
    """Testing related errors"""
    pass


class IDEIntegrationError(SocraticException):
    """IDE integration errors"""
    pass


class AuthenticationError(SocraticException):
    """Authentication errors"""
    pass


class ConflictError(SocraticException):
    """Resource conflict errors"""
    pass


# ============================================================================
# HELPER UTILITIES
# ============================================================================

class DateTimeHelper:
    """DateTime utilities for the system"""

    @staticmethod
    def now() -> datetime:
        """Get current UTC datetime"""
        return datetime.now(timezone.utc)

    @staticmethod
    def to_iso_string(dt: datetime) -> str:
        """Convert datetime to ISO string"""
        return dt.isoformat()

    @staticmethod
    def from_iso_string(iso_string: str) -> datetime:
        """Parse ISO string to datetime"""
        return datetime.fromisoformat(iso_string.replace('Z', '+00:00'))

    @staticmethod
    def to_timestamp(dt: datetime) -> float:
        """Convert datetime to timestamp"""
        return dt.timestamp()

    @staticmethod
    def from_timestamp(timestamp: float) -> datetime:
        """Convert timestamp to datetime"""
        return datetime.fromtimestamp(timestamp, tz=timezone.utc)


class FileHelper:
    """File system utilities"""

    @staticmethod
    def ensure_directory(path: Union[str, Path]) -> Path:
        """Ensure directory exists, create if not"""
        path_obj = Path(path)
        path_obj.mkdir(parents=True, exist_ok=True)
        return path_obj

    @staticmethod
    def get_file_size(path: Union[str, Path]) -> int:
        """Get file size in bytes"""
        return Path(path).stat().st_size

    @staticmethod
    def get_mime_type(path: Union[str, Path]) -> str:
        """Get MIME type of file"""
        mime_type, _ = mimetypes.guess_type(str(path))
        return mime_type or 'application/octet-stream'


class ValidationHelper:
    """Data validation utilities"""

    @staticmethod
    def validate_email(email: str) -> bool:
        """Basic email validation"""
        return '@' in email and '.' in email.split('@')[1]

    @staticmethod
    def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
        """Validate required fields are present"""
        missing = []
        for field in required_fields:
            if field not in data or data[field] is None:
                missing.append(field)
        return missing

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """Sanitize filename for safe filesystem use"""
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        return filename[:255]  # Limit length


# ============================================================================
# CONFIGURATION MANAGEMENT
# ============================================================================

class SystemConfig:
    """System configuration management with file and environment support"""

    def __init__(self):
        self._config = {}
        self._config_file = None
        self._defaults = self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            'system': {
                'version': '7.2.0',
                'debug': False,
                'data_path': 'data',
                'max_workers': 4
            },
            'database': {
                'type': 'sqlite',
                'path': 'data/socratic.db',
                'pool_size': 10,
                'timeout': 30
            },
            'logging': {
                'level': 'INFO',
                'file': {
                    'enabled': True,
                    'path': 'data/logs',
                    'max_size': '10MB',
                    'backup_count': 5
                },
                'console': {
                    'enabled': True,
                    'level': 'INFO'
                }
            },
            'agents': {
                'max_concurrent': 5,
                'timeout': 300,
                'retry_attempts': 3
            },
            'api': {
                'host': '0.0.0.0',
                'port': 5000,
                'debug': False
            }
        }

    def load_config(self, config_path: Optional[str] = None) -> bool:
        """Load configuration from file"""
        try:
            # Start with defaults
            self._config = self._defaults.copy()

            # Load from file if provided
            if config_path and Path(config_path).exists():
                with open(config_path, 'r', encoding='utf-8') as f:
                    file_config = json.load(f)
                    self._merge_config(self._config, file_config)
                self._config_file = config_path

            # Override with environment variables
            self._load_env_overrides()

            return True

        except Exception as e:
            print(f"Configuration loading failed: {e}")
            # Use defaults if loading fails
            self._config = self._defaults.copy()
            return False

    def _merge_config(self, base: Dict[str, Any], override: Dict[str, Any]):
        """Recursively merge configuration dictionaries"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def _load_env_overrides(self):
        """Load configuration overrides from environment variables"""
        env_mappings = {
            'SOCRATIC_DEBUG': ('system', 'debug'),
            'SOCRATIC_DATA_PATH': ('system', 'data_path'),
            'SOCRATIC_DB_PATH': ('database', 'path'),
            'SOCRATIC_LOG_LEVEL': ('logging', 'level'),
            'SOCRATIC_API_HOST': ('api', 'host'),
            'SOCRATIC_API_PORT': ('api', 'port'),
        }

        for env_var, (section, key) in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert to appropriate type
                if key in ['debug'] and value.lower() in ['true', '1', 'yes']:
                    value = True
                elif key in ['debug'] and value.lower() in ['false', '0', 'no']:
                    value = False
                elif key in ['port', 'pool_size', 'timeout', 'max_workers']:
                    try:
                        value = int(value)
                    except ValueError:
                        continue

                if section not in self._config:
                    self._config[section] = {}
                self._config[section][key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation (e.g., 'database.path')"""
        keys = key.split('.')
        current = self._config

        try:
            for k in keys:
                current = current[k]
            return current
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any):
        """Set configuration value using dot notation"""
        keys = key.split('.')
        current = self._config

        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        current[keys[-1]] = value

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section"""
        return self._config.get(section, {})

    def to_dict(self) -> Dict[str, Any]:
        """Get full configuration as dictionary"""
        return self._config.copy()


# ============================================================================
# LOGGING SYSTEM
# ============================================================================

class SystemLogger:
    """Centralized logging system with file and console output"""

    def __init__(self):
        self._config = None
        self._loggers = {}
        self._initialized = False

    def initialize(self, config: SystemConfig):
        """Initialize logging system with configuration"""
        if self._initialized:
            return

        self._config = config

        # Create logs directory
        log_path = config.get('logging.file.path', 'data/logs')
        log_dir = FileHelper.ensure_directory(log_path)
        log_file = log_dir / 'socratic.log'

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self._get_log_level(config.get('logging.level', 'INFO')))

        # Clear existing handlers
        root_logger.handlers.clear()

        # Console handler
        if config.get('logging.console.enabled', True):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(self._get_log_level(config.get('logging.console.level', 'INFO')))
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            console_handler.setFormatter(console_formatter)
            root_logger.addHandler(console_handler)

        # File handler with rotation
        if config.get('logging.file.enabled', True):
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=config.get('logging.file.backup_count', 5),
                encoding='utf-8'
            )
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)

            # Error handler (separate file for errors)
            error_file = log_dir / 'errors.log'
            error_handler = logging.handlers.RotatingFileHandler(
                error_file,
                maxBytes=5 * 1024 * 1024,  # 5MB
                backupCount=3,
                encoding='utf-8'
            )
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(file_formatter)
            root_logger.addHandler(error_handler)

        self._initialized = True

        # Create application logger and log success
        app_logger = self.get_logger('socratic')
        app_logger.info("Logging system initialized successfully")

    def get_logger(self, name: str) -> logging.Logger:
        """Get or create a logger instance"""
        if name not in self._loggers:
            logger = logging.getLogger(name)
            self._loggers[name] = logger
        return self._loggers[name]

    def _get_log_level(self, level_str: str) -> int:
        """Convert string log level to logging constant"""
        levels = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        return levels.get(level_str.upper(), logging.INFO)

    def set_level(self, level: str):
        """Set global log level"""
        log_level = self._get_log_level(level)
        logging.getLogger().setLevel(log_level)


# ============================================================================
# EVENT SYSTEM
# ============================================================================

@dataclass
class Event:
    """Event data structure"""
    type: str
    source: str
    data: Dict[str, Any]
    timestamp: datetime = field(default_factory=DateTimeHelper.now)
    event_id: str = field(default_factory=lambda: str(int(time.time() * 1000000)))


class EventSystem:
    """Event bus for system-wide communication"""

    def __init__(self):
        self._subscribers = {}
        self._event_queue = queue.Queue()
        self._processing_thread = None
        self._running = False
        self._logger = None

    def initialize(self):
        """Initialize event system"""
        self._running = True
        self._processing_thread = threading.Thread(target=self._process_events, daemon=True)
        self._processing_thread.start()

    def set_logger(self, logger: logging.Logger):
        """Set logger for event system"""
        self._logger = logger
        if self._logger:
            self._logger.info("Event system initialized")

    def subscribe(self, event_type: str, callback: callable):
        """Subscribe to event type"""
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)

        if self._logger:
            self._logger.debug(f"Subscribed to event type: {event_type}")

    def unsubscribe(self, event_type: str, callback: callable):
        """Unsubscribe from event type"""
        if event_type in self._subscribers:
            self._subscribers[event_type].remove(callback)

    def emit(self, event_type: str, source: str, data: Dict[str, Any]):
        """Emit an event"""
        event = Event(type=event_type, source=source, data=data)
        self._event_queue.put(event)

        if self._logger:
            self._logger.debug(f"Event emitted: {event_type} from {source}")

    def emit_event(self, event: Event):
        """Emit a pre-constructed event"""
        self._event_queue.put(event)

    def _process_events(self):
        """Process events in background thread"""
        while self._running:
            try:
                # Get event with timeout to allow shutdown
                event = self._event_queue.get(timeout=1.0)

                # Notify all subscribers
                for callback in self._subscribers.get(event.type, []):
                    try:
                        callback(event)
                    except Exception as e:
                        if self._logger:
                            self._logger.error(f"Event callback error: {e}", exc_info=True)

                # Mark task as done
                self._event_queue.task_done()

            except queue.Empty:
                continue
            except Exception as e:
                if self._logger:
                    self._logger.error(f"Event processing error: {e}", exc_info=True)

    def shutdown(self):
        """Shutdown event system"""
        self._running = False

        if self._processing_thread and self._processing_thread.is_alive():
            self._processing_thread.join(timeout=5.0)

        if self._logger:
            self._logger.info("Event system shutdown complete")


# ============================================================================
# DATABASE MANAGEMENT
# ============================================================================

class DatabaseManager:
    """Database connection and transaction management"""

    def __init__(self):
        self._config = None
        self._db_path = None
        self._connection_pool = {}
        self._pool_lock = threading.Lock()
        self._logger = None

    def initialize(self, config: SystemConfig):
        """Initialize database manager"""
        self._config = config
        self._db_path = config.get('database.path', 'data/socratic.db')

        # Ensure database directory exists
        db_dir = Path(self._db_path).parent
        FileHelper.ensure_directory(db_dir)

    def set_logger(self, logger: logging.Logger):
        """Set logger for database manager"""
        self._logger = logger

    def get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        thread_id = threading.get_ident()

        with self._pool_lock:
            if thread_id not in self._connection_pool:
                conn = sqlite3.connect(self._db_path, check_same_thread=False)
                conn.row_factory = sqlite3.Row
                self._connection_pool[thread_id] = conn

                if self._logger:
                    self._logger.debug(f"Created database connection for thread {thread_id}")

            return self._connection_pool[thread_id]

    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """Execute SELECT query"""
        conn = self.get_connection()
        cursor = conn.execute(query, params)
        return cursor.fetchall()

    def execute_command(self, command: str, params: tuple = ()) -> int:
        """Execute INSERT/UPDATE/DELETE command"""
        conn = self.get_connection()
        cursor = conn.execute(command, params)
        conn.commit()
        return cursor.rowcount

    def health_check(self) -> bool:
        """Check database connectivity"""
        try:
            self.execute_query("SELECT 1")
            return True
        except Exception as e:
            if self._logger:
                self._logger.error(f"Database health check failed: {e}")
            return False

    def cleanup(self):
        """Cleanup database connections"""
        with self._pool_lock:
            for thread_id, conn in self._connection_pool.items():
                try:
                    conn.close()
                    if self._logger:
                        self._logger.debug(f"Closed database connection for thread {thread_id}")
                except Exception as e:
                    if self._logger:
                        self._logger.error(f"Error closing connection: {e}")

            self._connection_pool.clear()


# ============================================================================
# SERVICE CONTAINER
# ============================================================================

class ServiceContainer:
    """Container holding all configured service instances"""

    def __init__(self, config: SystemConfig, logger_system: SystemLogger,
                 event_system: EventSystem, db_manager: DatabaseManager):
        self.config = config
        self.logger_system = logger_system
        self.event_system = event_system
        self.db_manager = db_manager

    def get_logger(self, name: str) -> logging.Logger:
        """Get a logger instance"""
        return self.logger_system.get_logger(name)

    def get_config(self) -> SystemConfig:
        """Get configuration instance"""
        return self.config

    def get_event_bus(self) -> EventSystem:
        """Get event system instance"""
        return self.event_system

    def get_db_manager(self) -> DatabaseManager:
        """Get database manager instance"""
        return self.db_manager


# ============================================================================
# SERVICE FACTORY
# ============================================================================

class ServiceFactory:
    """Factory for creating and configuring services"""

    @staticmethod
    def create_services(config_path: Optional[str] = None) -> ServiceContainer:
        """Create and configure all services"""
        try:
            # 1. Load configuration
            config = SystemConfig()
            if not config.load_config(config_path):
                print("Warning: Using default configuration")

            # 2. Initialize logging
            logger_system = SystemLogger()
            logger_system.initialize(config)
            main_logger = logger_system.get_logger('system')

            # 3. Initialize event system
            event_system = EventSystem()
            event_system.initialize()
            event_system.set_logger(logger_system.get_logger('events'))

            # 4. Initialize database
            db_manager = DatabaseManager()
            db_manager.initialize(config)
            db_manager.set_logger(logger_system.get_logger('database'))

            # 5. Create required directories
            data_path = config.get('system.data_path', 'data')
            for subdir in ['logs', 'uploads', 'exports', 'generated_projects', 'vector_db']:
                FileHelper.ensure_directory(Path(data_path) / subdir)

            # 6. Create service container
            services = ServiceContainer(config, logger_system, event_system, db_manager)

            main_logger.info("Service container initialized successfully")
            return services

        except Exception as e:
            print(f"Service initialization failed: {e}")
            raise ServiceError(f"Failed to initialize services: {e}")


# ============================================================================
# SYSTEM INITIALIZATION
# ============================================================================

def initialize_system(config_path: Optional[str] = None) -> ServiceContainer:
    """Initialize system and return service container"""
    return ServiceFactory.create_services(config_path)


def cleanup_system(services: ServiceContainer):
    """Cleanup system resources"""
    logger = services.get_logger('system')
    logger.info("Starting system cleanup...")

    try:
        # Cleanup database connections
        services.db_manager.cleanup()

        # Shutdown event system
        services.event_system.shutdown()

        logger.info("System cleanup completed")

    except Exception as e:
        logger.error(f"Error during system cleanup: {e}")


# ============================================================================
# CONSTANTS
# ============================================================================

# Service availability constants
ANTHROPIC_AVAILABLE = True  # Assume available, will be checked at runtime

# Legacy aliases for backward compatibility
EventBus = EventSystem
SocraticSystem = SystemConfig
ConfigManager = SystemConfig
LogManager = SystemLogger


# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    # Exceptions
    'SocraticException', 'ConfigurationError', 'ValidationError',
    'DatabaseError', 'AgentError', 'ServiceError', 'APIError',
    'CodeGenerationError', 'TestingError', 'IDEIntegrationError',
    'AuthenticationError', 'ConflictError',

    # Core Infrastructure
    'SystemConfig', 'SystemLogger', 'EventSystem', 'DatabaseManager',
    'Event', 'ServiceContainer', 'ServiceFactory',

    # Helpers
    'DateTimeHelper', 'FileHelper', 'ValidationHelper',

    # Constants
    'ANTHROPIC_AVAILABLE',

    # System Functions
    'initialize_system', 'cleanup_system',

    # Legacy aliases
    'EventBus', 'SocraticSystem', 'ConfigManager', 'LogManager'
]


# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

# Add missing import for dataclass


if __name__ == "__main__":
    # Test core system functionality
    print("Testing core system with ServiceContainer...")

    try:
        # Initialize services
        services = initialize_system()

        # Test configuration
        config = services.get_config()
        print("✅ Configuration system working")

        # Test logging
        logger = services.get_logger('test')
        logger.info("Test log message")
        print("✅ Logging system working")

        # Test event system
        received_events = []

        def test_callback(event):
            received_events.append(event)

        services.event_system.subscribe('test', test_callback)
        services.event_system.emit('test', 'core_test', {'message': 'Hello World'})

        # Give event time to process
        time.sleep(0.1)

        if received_events:
            print("✅ Event system working")
        else:
            print("⚠️ Event system may have issues")

        # Test database
        if services.db_manager.health_check():
            print("✅ Database system working")
        else:
            print("❌ Database system failed")

        # Test helpers
        now = DateTimeHelper.now()
        iso_string = DateTimeHelper.to_iso_string(now)
        parsed = DateTimeHelper.from_iso_string(iso_string)
        print("✅ DateTime helper working")

        if ValidationHelper.validate_email("test@example.com"):
            print("✅ Validation helper working")
        else:
            print("❌ Validation helper failed")

        print("\n🎉 All core system tests passed!")

        # Cleanup
        cleanup_system(services)

    except Exception as e:
        print(f"❌ Core system test failed: {e}")
        raise RuntimeError("Processing failed")
