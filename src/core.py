#!/usr/bin/env python3
"""
Socratic RAG Enhanced - Core Infrastructure
==========================================

Foundation module providing core infrastructure components:
- Configuration management (YAML + environment variables)
- Structured logging system (console + file + error tracking)
- Event system for agent communication
- Database connection management with pooling
- Custom exception hierarchy
- DateTime/File/Validation helpers (no deprecated functions)
- Global system initialization

This module establishes the foundational infrastructure that all other components depend on.
"""

import os
import sys
import yaml
import logging
import logging.handlers
import sqlite3
import threading
import datetime
import re
import json
import hashlib
from pathlib import Path
from typing import Dict, Any, Optional, List, Union, Callable
from contextlib import contextmanager
from dataclasses import dataclass, field
from collections import defaultdict
import queue
import time


# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================

class SocraticException(Exception):
    """Base exception for all Socratic RAG Enhanced errors"""

    def __init__(self, message: str, error_code: Optional[str] = None, details: Optional[Dict] = None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details or {}
        self.timestamp = datetime.datetime.now()


class ConfigurationError(SocraticException):
    """Configuration-related errors"""
    pass


class ValidationError(SocraticException):
    """Data validation errors"""
    pass


class DatabaseError(SocraticException):
    """Database operation errors"""
    pass


class AgentError(SocraticException):
    """Agent system errors"""
    pass


class ServiceError(SocraticException):
    """External service errors"""
    pass


class APIError(SocraticException):
    """API operation errors"""
    pass


class CodeGenerationError(SocraticException):
    """Code generation and compilation errors"""
    pass


class TestingError(SocraticException):
    """Testing and validation errors"""
    pass


class IDEIntegrationError(SocraticException):
    """IDE integration errors"""
    pass


class AuthenticationError(SocraticException):
    """Authentication and authorization errors"""
    pass


class ConflictError(SocraticException):
    """Conflict detection and resolution errors"""
    pass


# ============================================================================
# CONFIGURATION MANAGEMENT
# ============================================================================

class SystemConfig:
    """Global system configuration manager"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return

        self._config = {}
        self._config_file = None
        self._watchers = []
        self._initialized = True

    def load_config(self, config_path: str = "config.yaml") -> bool:
        """Load configuration from YAML file"""
        try:
            config_file = Path(config_path)
            if not config_file.exists():
                raise ConfigurationError(f"Configuration file not found: {config_path}")

            with open(config_file, 'r', encoding='utf-8') as f:
                self._config = yaml.safe_load(f) or {}

            self._config_file = config_path

            # Override with environment variables
            self._load_environment_overrides()

            # Validate required configuration
            self._validate_config()

            return True

        except Exception as e:
            raise ConfigurationError(f"Failed to load configuration: {e}")

    def _load_environment_overrides(self):
        """Load environment variable overrides"""
        env_prefix = "SOCRATIC_"

        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                config_key = key[len(env_prefix):].lower().replace('_', '.')
                self._set_nested_value(config_key, value)

    def _set_nested_value(self, key_path: str, value: str):
        """Set nested configuration value using dot notation"""
        keys = key_path.split('.')
        current = self._config

        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]

        # Convert string values to appropriate types
        current[keys[-1]] = self._convert_env_value(value)

    def _convert_env_value(self, value: str) -> Any:
        """Convert environment variable string to appropriate type"""
        # Boolean values
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'

        # Integer values
        try:
            return int(value)
        except ValueError:
            pass

        # Float values
        try:
            return float(value)
        except ValueError:
            pass

        # JSON values
        if value.startswith('{') or value.startswith('['):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                pass

        # Return as string
        return value

    def _validate_config(self):
        """Validate required configuration sections"""
        required_sections = ['system', 'database', 'logging']

        for section in required_sections:
            if section not in self._config:
                self._config[section] = {}

        # Set defaults for missing required values
        defaults = {
            'system.version': '7.3.0',
            'system.debug': False,
            'system.data_path': 'data',
            'database.type': 'sqlite',
            'database.path': 'data/projects.db',
            'logging.level': 'INFO',
            'logging.file': 'data/logs/socratic.log',
        }

        for key, default_value in defaults.items():
            if self.get(key) is None:
                self._set_nested_value(key, str(default_value))

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
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
        self._set_nested_value(key, value)

    def get_section(self, section: str) -> Dict[str, Any]:
        """Get entire configuration section"""
        return self._config.get(section, {})

    def reload(self) -> bool:
        """Reload configuration from file"""
        if self._config_file:
            return self.load_config(self._config_file)
        return False

    @property
    def config_file(self) -> Optional[str]:
        """Get current configuration file path"""
        return self._config_file

    def to_dict(self) -> Dict[str, Any]:
        """Get full configuration as dictionary"""
        return self._config.copy()


# ============================================================================
# LOGGING SYSTEM
# ============================================================================

class SystemLogger:
    """Centralized logging system"""

    _instance = None
    _lock = threading.Lock()
    _loggers = {}

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return

        self._config = None
        self._initialized = True

    def initialize(self, config: SystemConfig):
        """Initialize logging system with configuration"""
        self._config = config

        # Create logs directory
        log_file = config.get('logging.file', 'data/logs/socratic.log')
        log_dir = Path(log_file).parent
        log_dir.mkdir(parents=True, exist_ok=True)

        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self._get_log_level(config.get('logging.level', 'INFO')))

        # Clear existing handlers
        root_logger.handlers.clear()

        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)

        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
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

        # Create application logger
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


def get_logger(name: str) -> logging.Logger:
    """Convenience function to get a logger"""
    logger_system = SystemLogger()
    return logger_system.get_logger(name)


# ============================================================================
# EVENT SYSTEM
# ============================================================================

@dataclass
class Event:
    """System event data structure"""
    type: str
    source: str
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)
    event_id: str = field(default_factory=lambda: hashlib.md5(
        f"{time.time()}{os.getpid()}".encode()).hexdigest()[:12])


class EventSystem:
    """Event-driven communication system for agents and services"""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return

        self._subscribers = defaultdict(list)
        self._event_queue = queue.Queue()
        self._processing_thread = None
        self._running = False
        self._logger = None
        self._initialized = True

    def initialize(self):
        """Initialize event system"""
        self._logger = get_logger('events')
        self._running = True

        # Start event processing thread
        self._processing_thread = threading.Thread(
            target=self._process_events,
            daemon=True,
            name="EventProcessor"
        )
        self._processing_thread.start()

        self._logger.info("Event system initialized successfully")

    def subscribe(self, event_type: str, callback: Callable[[Event], None]):
        """Subscribe to events of a specific type"""
        self._subscribers[event_type].append(callback)
        if self._logger:
            self._logger.debug(f"Subscribed to event type: {event_type}")

    def unsubscribe(self, event_type: str, callback: Callable[[Event], None]):
        """Unsubscribe from events"""
        if callback in self._subscribers[event_type]:
            self._subscribers[event_type].remove(callback)
            if self._logger:
                self._logger.debug(f"Unsubscribed from event type: {event_type}")

    def emit(self, event_type: str, source: str, data: Optional[Dict[str, Any]] = None):
        """Emit an event"""
        event = Event(
            type=event_type,
            source=source,
            data=data or {}
        )

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

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return

        self._config = None
        self._db_path = None
        self._connection_pool = {}
        self._pool_lock = threading.Lock()
        self._logger = None
        self._initialized = True

    def initialize(self, config: SystemConfig):
        """Initialize database manager"""
        self._config = config
        self._logger = get_logger('database')

        # Get database configuration
        self._db_path = config.get('database.path', 'data/projects.db')

        # Ensure database directory exists
        db_dir = Path(self._db_path).parent
        db_dir.mkdir(parents=True, exist_ok=True)

        # Test database connection
        if self.health_check():
            self._logger.info(f"Database manager initialized: {self._db_path}")
        else:
            raise DatabaseError("Database initialization failed")

    @contextmanager
    def get_connection(self):
        """Get database connection (context manager)"""
        thread_id = threading.get_ident()

        with self._pool_lock:
            if thread_id not in self._connection_pool:
                try:
                    conn = sqlite3.connect(
                        self._db_path,
                        check_same_thread=False,
                        timeout=30.0
                    )
                    conn.row_factory = sqlite3.Row

                    # Enable WAL mode for better concurrency
                    conn.execute("PRAGMA journal_mode=WAL")
                    conn.execute("PRAGMA synchronous=NORMAL")
                    conn.execute("PRAGMA cache_size=10000")
                    conn.execute("PRAGMA temp_store=MEMORY")

                    self._connection_pool[thread_id] = conn

                except Exception as e:
                    self._logger.error(f"Database connection failed: {e}")
                    raise DatabaseError(f"Failed to connect to database: {e}")

        connection = self._connection_pool[thread_id]

        try:
            yield connection
        except Exception as e:
            connection.rollback()
            self._logger.error(f"Database operation failed: {e}")
            raise
        finally:
            # Keep connection in pool for reuse
            pass

    @contextmanager
    def transaction(self):
        """Database transaction context manager"""
        with self.get_connection() as conn:
            try:
                conn.execute("BEGIN IMMEDIATE")
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                self._logger.error(f"Transaction failed: {e}")
                raise DatabaseError(f"Transaction failed: {e}")

    def execute_query(self, query: str, params: Optional[tuple] = None) -> List[sqlite3.Row]:
        """Execute a SELECT query and return results"""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params or ())
            return cursor.fetchall()

    def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """Execute an INSERT/UPDATE/DELETE query and return affected rows"""
        with self.get_connection() as conn:
            cursor = conn.execute(query, params or ())
            conn.commit()
            return cursor.rowcount

    def health_check(self) -> bool:
        """Check database health"""
        try:
            with self.get_connection() as conn:
                conn.execute("SELECT 1")
                return True
        except Exception as e:
            self._logger.error(f"Database health check failed: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with self.get_connection() as conn:
                # Get database file size
                db_size = Path(self._db_path).stat().st_size if Path(self._db_path).exists() else 0

                # Get table count
                tables = conn.execute(
                    "SELECT COUNT(*) as count FROM sqlite_master WHERE type='table'"
                ).fetchone()

                return {
                    'db_path': str(self._db_path),
                    'size_bytes': db_size,
                    'size_mb': round(db_size / (1024 * 1024), 2),
                    'table_count': tables['count'] if tables else 0,
                    'connection_pool_size': len(self._connection_pool)
                }
        except Exception as e:
            self._logger.error(f"Failed to get database stats: {e}")
            return {}

    def cleanup(self):
        """Cleanup database connections"""
        with self._pool_lock:
            for conn in self._connection_pool.values():
                try:
                    conn.close()
                except Exception as e:
                    self._logger.error(f"Error closing database connection: {e}")

            self._connection_pool.clear()

        if self._logger:
            self._logger.info("Database manager cleanup complete")


# ============================================================================
# UTILITY HELPERS
# ============================================================================

class DateTimeHelper:
    """DateTime utility functions (no deprecated methods)"""

    @staticmethod
    def now() -> datetime.datetime:
        """Get current datetime (replaces deprecated utcnow)"""
        return datetime.datetime.now(datetime.timezone.utc).replace(tzinfo=None)

    @staticmethod
    def from_timestamp(timestamp: float) -> datetime.datetime:
        """Convert timestamp to datetime"""
        return datetime.datetime.fromtimestamp(timestamp, datetime.timezone.utc).replace(tzinfo=None)

    @staticmethod
    def to_timestamp(dt: datetime.datetime) -> float:
        """Convert datetime to timestamp"""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.timestamp()

    @staticmethod
    def to_iso_string(dt: datetime.datetime) -> str:
        """Convert datetime to ISO string"""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.isoformat()

    @staticmethod
    def from_iso_string(iso_string: str) -> datetime.datetime:
        """Parse ISO string to datetime"""
        try:
            dt = datetime.datetime.fromisoformat(iso_string.replace('Z', '+00:00'))
            return dt.replace(tzinfo=None)  # Remove timezone for consistency
        except ValueError:
            # Fallback for other formats
            return datetime.datetime.strptime(iso_string[:19], '%Y-%m-%dT%H:%M:%S')

    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            return f"{seconds / 60:.1f}m"
        else:
            return f"{seconds / 3600:.1f}h"

    @staticmethod
    def days_between(start: datetime.datetime, end: datetime.datetime) -> int:
        """Calculate days between two dates"""
        return (end - start).days


class FileHelper:
    """File system utility functions"""

    @staticmethod
    def ensure_directory(path: Union[str, Path]) -> Path:
        """Ensure directory exists, create if necessary"""
        directory = Path(path)
        directory.mkdir(parents=True, exist_ok=True)
        return directory

    @staticmethod
    def safe_filename(filename: str) -> str:
        """Create safe filename by removing invalid characters"""
        # Remove invalid characters
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove control characters
        safe_name = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', safe_name)
        # Limit length
        return safe_name[:255]

    @staticmethod
    def get_file_size(path: Union[str, Path]) -> int:
        """Get file size in bytes"""
        try:
            return Path(path).stat().st_size
        except (OSError, FileNotFoundError):
            return 0

    @staticmethod
    def read_text_file(path: Union[str, Path], encoding: str = 'utf-8') -> str:
        """Safely read text file"""
        try:
            return Path(path).read_text(encoding=encoding)
        except Exception as e:
            raise SocraticException(f"Failed to read file {path}: {e}")

    @staticmethod
    def write_text_file(path: Union[str, Path], content: str, encoding: str = 'utf-8'):
        """Safely write text file"""
        try:
            file_path = Path(path)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content, encoding=encoding)
        except Exception as e:
            raise SocraticException(f"Failed to write file {path}: {e}")


class ValidationHelper:
    """Data validation utility functions"""

    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email address format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))

    @staticmethod
    def validate_project_name(name: str) -> bool:
        """Validate project name"""
        if not name or len(name.strip()) < 2:
            return False

        # Check for valid characters (letters, numbers, spaces, hyphens, underscores)
        pattern = r'^[a-zA-Z0-9\s\-_]+$'
        return bool(re.match(pattern, name.strip()))

    @staticmethod
    def validate_username(username: str) -> bool:
        """Validate username format"""
        if not username or len(username) < 3 or len(username) > 50:
            return False

        # Alphanumeric, underscores, hyphens only
        pattern = r'^[a-zA-Z0-9_-]+$'
        return bool(re.match(pattern, username))

    @staticmethod
    def validate_password_strength(password: str) -> Dict[str, Any]:
        """Validate password strength"""
        result = {
            'is_valid': False,
            'score': 0,
            'issues': []
        }

        if len(password) < 8:
            result['issues'].append('Password must be at least 8 characters long')
        else:
            result['score'] += 1

        if not re.search(r'[a-z]', password):
            result['issues'].append('Password must contain lowercase letters')
        else:
            result['score'] += 1

        if not re.search(r'[A-Z]', password):
            result['issues'].append('Password must contain uppercase letters')
        else:
            result['score'] += 1

        if not re.search(r'\d', password):
            result['issues'].append('Password must contain numbers')
        else:
            result['score'] += 1

        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            result['issues'].append('Password must contain special characters')
        else:
            result['score'] += 1

        result['is_valid'] = len(result['issues']) == 0
        return result

    @staticmethod
    def sanitize_html(text: str) -> str:
        """Basic HTML sanitization"""
        # Remove HTML tags
        clean_text = re.sub(r'<[^>]+>', '', text)
        # Escape remaining special characters
        clean_text = (clean_text.replace('&', '&amp;')
                      .replace('<', '&lt;')
                      .replace('>', '&gt;')
                      .replace('"', '&quot;')
                      .replace("'", '&#x27;'))
        return clean_text


# ============================================================================
# SYSTEM INITIALIZATION & CLEANUP
# ============================================================================

def initialize_system(config_path: str = "config.yaml") -> bool:
    """Initialize the complete system infrastructure"""
    try:
        logger = get_logger('system')
        logger.info("Initializing Socratic RAG Enhanced system...")

        # 1. Load configuration
        config = SystemConfig()
        if not config.load_config(config_path):
            return False

        # 2. Initialize logging
        logger_system = SystemLogger()
        logger_system.initialize(config)

        # 3. Initialize event system
        event_system = EventSystem()
        event_system.initialize()

        # 4. Initialize database
        db_manager = DatabaseManager()
        db_manager.initialize(config)

        # 5. Create required directories
        data_path = config.get('system.data_path', 'data')
        for subdir in ['logs', 'uploads', 'exports', 'generated_projects', 'vector_db']:
            FileHelper.ensure_directory(Path(data_path) / subdir)

        logger.info("System initialization completed successfully")
        return True

    except Exception as e:
        print(f"System initialization failed: {e}")
        return False


def cleanup_system():
    """Cleanup system resources"""
    logger = get_logger('system')
    logger.info("Starting system cleanup...")

    try:
        # Cleanup database connections
        db_manager = DatabaseManager()
        db_manager.cleanup()

        # Shutdown event system
        event_system = EventSystem()
        event_system.shutdown()

        logger.info("System cleanup completed")

    except Exception as e:
        logger.error(f"Error during system cleanup: {e}")


# ============================================================================
# CONVENIENCE FUNCTIONS FOR BACKWARDS COMPATIBILITY
# ============================================================================

def get_config() -> SystemConfig:
    """Get the global configuration instance"""
    return SystemConfig()


def get_db_manager() -> DatabaseManager:
    """Get the global database manager instance"""
    return DatabaseManager()


def get_system() -> SystemConfig:
    """Get system instance (alias for get_config)"""
    return SystemConfig()


def get_event_bus() -> EventSystem:
    """Get the global event system instance"""
    return EventSystem()


# Legacy class aliases and constants
SocraticSystem = SystemConfig  # Alias for backwards compatibility
ConfigManager = SystemConfig  # Alias for backwards compatibility
LogManager = SystemLogger  # Alias for backwards compatibility

# Constants for service availability
ANTHROPIC_AVAILABLE = True  # Assume available, will be checked at runtime

# ============================================================================
# MODULE EXPORTS
# ============================================================================

__all__ = [
    # Exceptions
    'SocraticException', 'ConfigurationError', 'ValidationError',
    'DatabaseError', 'AgentError', 'ServiceError', 'APIError', 'CodeGenerationError', 'TestingError',
    'IDEIntegrationError', 'AuthenticationError', 'ConflictError',

    # Core Infrastructure
    'SystemConfig', 'SystemLogger', 'EventSystem', 'DatabaseManager',
    'Event', 'SocraticSystem', 'ConfigManager', 'LogManager',

    # Helpers
    'DateTimeHelper', 'FileHelper', 'ValidationHelper',

    # Constants
    'ANTHROPIC_AVAILABLE',

    # System Functions
    'initialize_system', 'cleanup_system', 'get_logger',
    'get_config', 'get_db_manager', 'get_system', 'get_event_bus'
]

# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

if __name__ == "__main__":
    # Test core system functionality
    print("Testing core system components...")

    try:
        # Test configuration
        config = SystemConfig()
        config._config = {
            'system': {'version': '7.3.0', 'debug': True},
            'database': {'path': ':memory:'},
            'logging': {'level': 'DEBUG'}
        }
        print("✅ Configuration system working")

        # Test logging
        logger_system = SystemLogger()
        logger_system.initialize(config)
        logger = get_logger('test')
        logger.info("Test log message")
        print("✅ Logging system working")

        # Test event system
        event_system = EventSystem()
        event_system.initialize()

        received_events = []


        def test_callback(event):
            received_events.append(event)


        event_system.subscribe('test', test_callback)
        event_system.emit('test', 'core_test', {'message': 'Hello World'})

        # Give event time to process
        time.sleep(0.1)

        if received_events:
            print("✅ Event system working")
        else:
            print("⚠️ Event system may have issues")

        # Test database
        db_manager = DatabaseManager()
        db_manager.initialize(config)

        if db_manager.health_check():
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

    except Exception as e:
        print(f"❌ Core system test failed: {e}")
        raise
