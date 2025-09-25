#!/usr/bin/env python3
"""
Socratic RAG Enhanced - Core Infrastructure
===========================================

Foundation module providing configuration, logging, exceptions, events, and utilities
for the Socratic RAG Enhanced system.

This module establishes the core infrastructure that all other components depend on.
"""

import os
import sys
import json
import yaml
import logging
import datetime
import threading
import uuid
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
import sqlite3
from contextlib import contextmanager

# Third-party imports with graceful fallbacks
try:
    import anthropic

    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    print("Warning: Anthropic package not found. Install with: pip install anthropic")

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings

    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False
    print("Warning: ChromaDB not found. Install with: pip install chromadb")

try:
    from sentence_transformers import SentenceTransformer

    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    print("Warning: Sentence Transformers not found. Install with: pip install sentence-transformers")

try:
    from colorama import init, Fore, Back, Style

    COLORAMA_AVAILABLE = True
    init(autoreset=True)
except ImportError:
    COLORAMA_AVAILABLE = False

    # Provide fallback color constants
    class _Fore:
        RED = GREEN = YELLOW = BLUE = MAGENTA = CYAN = WHITE = RESET = ""


    class _Style:
        BRIGHT = RESET_ALL = ""


    Fore, Style = _Fore(), _Style()


# ============================================================================
# CONFIGURATION MANAGEMENT
# ============================================================================

@dataclass
class SystemConfig:
    """Central system configuration"""

    # Core Settings
    data_dir: str = 'data'
    log_level: str = 'INFO'
    debug_mode: bool = False

    # API Settings
    claude_api_key: Optional[str] = None
    claude_model: str = 'claude-3-5-sonnet-20241022'
    max_retries: int = 3
    retry_delay: int = 1

    # Database Settings
    database_url: str = 'data/projects.db'
    vector_db_path: str = 'data/vector_db'
    backup_enabled: bool = True
    backup_interval_hours: int = 24

    # Performance Settings
    max_context_length: int = 8000
    token_warning_threshold: float = 0.8
    session_timeout: int = 3600  # 1 hour

    # Code Generation Settings
    embedding_model: str = 'all-MiniLM-L6-v2'
    code_style: str = 'documented'
    test_framework: str = 'pytest'

    # Security Settings
    require_auth: bool = True
    session_secret_key: Optional[str] = None

    # Feature Flags
    enable_web_ui: bool = True
    enable_ide_integration: bool = True
    enable_git_integration: bool = True
    enable_testing_service: bool = True


class ConfigManager:
    """Manages system configuration from multiple sources"""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or 'config.yaml'
        self.config = SystemConfig()
        self._load_configuration()

    def _load_configuration(self) -> None:
        """Load configuration from file and environment variables"""
        # Load from YAML file if it exists
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    file_config = yaml.safe_load(f) or {}
                self._update_config_from_dict(file_config)
            except Exception as e:
                print(f"Warning: Could not load config file {self.config_path}: {e}")

        # Override with environment variables
        self._load_from_environment()

        # Validate configuration
        self._validate_config()

    def _update_config_from_dict(self, config_dict: Dict[str, Any]) -> None:
        """Update configuration from dictionary"""
        for key, value in config_dict.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)

    def _load_from_environment(self) -> None:
        """Load configuration from environment variables"""
        env_mappings = {
            'SOCRATIC_API_KEY_CLAUDE': 'claude_api_key',
            'API_KEY_CLAUDE': 'claude_api_key',  # Backward compatibility
            'SOCRATIC_DATA_DIR': 'data_dir',
            'SOCRATIC_LOG_LEVEL': 'log_level',
            'SOCRATIC_DEBUG': 'debug_mode',
            'SOCRATIC_DATABASE_URL': 'database_url',
            'SOCRATIC_SESSION_SECRET': 'session_secret_key',
        }

        for env_key, config_key in env_mappings.items():
            value = os.getenv(env_key)
            if value is not None:
                # Convert string values to appropriate types
                if config_key == 'debug_mode':
                    value = value.lower() in ('true', '1', 'yes', 'on')
                elif config_key in ('max_retries', 'retry_delay', 'max_context_length', 'session_timeout'):
                    value = int(value)
                elif config_key == 'token_warning_threshold':
                    value = float(value)

                setattr(self.config, config_key, value)

    def _validate_config(self) -> None:
        """Validate configuration and set defaults"""
        # Ensure data directory exists
        os.makedirs(self.config.data_dir, exist_ok=True)

        # Generate session secret if not provided
        if not self.config.session_secret_key:
            self.config.session_secret_key = str(uuid.uuid4())

        # Validate paths
        if not self.config.database_url.startswith('/'):
            self.config.database_url = os.path.join(self.config.data_dir,
                                                    os.path.basename(self.config.database_url))

        if not self.config.vector_db_path.startswith('/'):
            self.config.vector_db_path = os.path.join(self.config.data_dir,
                                                      os.path.basename(self.config.vector_db_path))

    def save_config(self) -> None:
        """Save current configuration to file"""
        config_dict = asdict(self.config)
        # Don't save sensitive information
        config_dict.pop('claude_api_key', None)
        config_dict.pop('session_secret_key', None)

        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
        except Exception as e:
            print(f"Warning: Could not save config file: {e}")

    def get_config(self) -> SystemConfig:
        """Get current configuration"""
        return self.config


# ============================================================================
# LOGGING SYSTEM
# ============================================================================

class LogLevel(Enum):
    """Logging levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class ColorFormatter(logging.Formatter):
    """Custom formatter with color support"""

    def __init__(self):
        super().__init__()
        self.colors = {
            'DEBUG': Fore.BLUE,
            'INFO': Fore.GREEN,
            'WARNING': Fore.YELLOW,
            'ERROR': Fore.RED,
            'CRITICAL': Fore.MAGENTA,
        } if COLORAMA_AVAILABLE else {}

    def format(self, record):
        if COLORAMA_AVAILABLE and record.levelname in self.colors:
            record.levelname = f"{self.colors[record.levelname]}{record.levelname}{Fore.RESET}"
            record.name = f"{Fore.CYAN}{record.name}{Fore.RESET}"

        return f"[{record.asctime}] {record.levelname} {record.name}: {record.getMessage()}"


class LogManager:
    """Manages logging configuration and provides logger instances"""

    def __init__(self, config: SystemConfig):
        self.config = config
        self.loggers: Dict[str, logging.Logger] = {}
        self._setup_logging()

    def _setup_logging(self) -> None:
        """Setup logging configuration"""
        # Create logs directory
        log_dir = os.path.join(self.config.data_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)

        # Configure root logger
        root_logger = logging.getLogger('socratic')
        root_logger.setLevel(getattr(logging, self.config.log_level.upper()))

        # Clear existing handlers
        root_logger.handlers.clear()

        # Console handler with colors
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(ColorFormatter())
        root_logger.addHandler(console_handler)

        # File handler for persistent logging
        log_file = os.path.join(log_dir, f"socratic_{datetime.datetime.now().strftime('%Y%m%d')}.log")
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)s %(name)s: %(message)s'
        ))
        root_logger.addHandler(file_handler)

        # Error file handler
        error_file = os.path.join(log_dir, 'errors.log')
        error_handler = logging.FileHandler(error_file)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)s %(name)s: %(message)s\n%(pathname)s:%(lineno)d\n'
        ))
        root_logger.addHandler(error_handler)

    def get_logger(self, name: str) -> logging.Logger:
        """Get or create a logger instance"""
        if name not in self.loggers:
            self.loggers[name] = logging.getLogger(f'socratic.{name}')
        return self.loggers[name]


# ============================================================================
# CUSTOM EXCEPTIONS
# ============================================================================

class SocraticException(Exception):
    """Base exception for Socratic system"""
    pass


class ConfigurationError(SocraticException):
    """Configuration-related errors"""
    pass


class ValidationError(SocraticException):
    """Data validation errors"""
    pass


class APIError(SocraticException):
    """External API errors"""
    pass


class DatabaseError(SocraticException):
    """Database operation errors"""
    pass


class CodeGenerationError(SocraticException):
    """Code generation errors"""
    pass


class TestingError(SocraticException):
    """Testing service errors"""
    pass


class IDEIntegrationError(SocraticException):
    """IDE integration errors"""
    pass


class AuthenticationError(SocraticException):
    """Authentication/authorization errors"""
    pass


class ConflictError(SocraticException):
    """Specification conflict errors"""
    pass


# ============================================================================
# EVENT SYSTEM
# ============================================================================

@dataclass
class Event:
    """System event"""
    event_type: str
    source: str
    data: Dict[str, Any]
    timestamp: datetime.datetime
    event_id: str = ""

    def __post_init__(self):
        if not self.event_id:
            self.event_id = str(uuid.uuid4())


EventHandler = Callable[[Event], None]


class EventBus:
    """Internal event system for agent communication"""

    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self._handlers: Dict[str, List[EventHandler]] = {}
        self._lock = threading.Lock()

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """Subscribe to events of a specific type"""
        with self._lock:
            if event_type not in self._handlers:
                self._handlers[event_type] = []
            self._handlers[event_type].append(handler)
            self.logger.debug(f"Subscribed handler to event type: {event_type}")

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """Unsubscribe from events"""
        with self._lock:
            if event_type in self._handlers:
                try:
                    self._handlers[event_type].remove(handler)
                    self.logger.debug(f"Unsubscribed handler from event type: {event_type}")
                except ValueError:
                    pass

    def publish(self, event: Event) -> None:
        """Publish an event to all subscribers"""
        with self._lock:
            handlers = self._handlers.get(event.event_type, []).copy()

        self.logger.debug(f"Publishing event: {event.event_type} from {event.source}")

        for handler in handlers:
            try:
                handler(event)
            except Exception as e:
                self.logger.error(f"Error in event handler for {event.event_type}: {e}")

    def publish_async(self, event_type: str, source: str, data: Dict[str, Any]) -> None:
        """Publish an event asynchronously"""
        event = Event(
            event_type=event_type,
            source=source,
            data=data,
            timestamp=datetime.datetime.now()
        )

        def _publish():
            self.publish(event)

        thread = threading.Thread(target=_publish, daemon=True)
        thread.start()


# ============================================================================
# DATABASE CONNECTION MANAGEMENT
# ============================================================================

class DatabaseManager:
    """Manages database connections and provides transaction support"""

    def __init__(self, config: SystemConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self._connection_pool: List[sqlite3.Connection] = []
        self._pool_lock = threading.Lock()

        # Ensure database directory exists
        db_dir = os.path.dirname(self.config.database_url)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    def get_connection(self) -> sqlite3.Connection:
        """Get a database connection from the pool"""
        with self._pool_lock:
            if self._connection_pool:
                return self._connection_pool.pop()

            # Create new connection
            try:
                conn = sqlite3.connect(self.config.database_url,
                                       check_same_thread=False,
                                       timeout=30.0)
                conn.row_factory = sqlite3.Row  # Enable column access by name
                conn.execute("PRAGMA foreign_keys = ON")  # Enable foreign key support
                conn.execute("PRAGMA journal_mode = WAL")  # Better concurrent access
                return conn
            except Exception as e:
                self.logger.error(f"Failed to create database connection: {e}")
                raise DatabaseError(f"Cannot connect to database: {e}")

    def return_connection(self, conn: sqlite3.Connection) -> None:
        """Return a connection to the pool"""
        if conn:
            with self._pool_lock:
                if len(self._connection_pool) < 10:  # Max pool size
                    self._connection_pool.append(conn)
                else:
                    conn.close()

    @contextmanager
    def get_db_session(self):
        """Context manager for database sessions with automatic cleanup"""
        conn = None
        try:
            conn = self.get_connection()
            yield conn
            conn.commit()
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database session error: {e}")
            raise
        finally:
            if conn:
                self.return_connection(conn)

    def close_all_connections(self) -> None:
        """Close all pooled connections"""
        with self._pool_lock:
            for conn in self._connection_pool:
                conn.close()
            self._connection_pool.clear()


# ============================================================================
# SYSTEM UTILITIES
# ============================================================================

class DateTimeHelper:
    """Helper functions for datetime operations"""

    @staticmethod
    def now() -> datetime.datetime:
        """Get current datetime (replacement for deprecated utcnow)"""
        return datetime.datetime.now(datetime.timezone.utc)

    @staticmethod
    def to_iso_string(dt: datetime.datetime) -> str:
        """Convert datetime to ISO format string"""
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=datetime.timezone.utc)
        return dt.isoformat()

    @staticmethod
    def from_iso_string(dt_string: str) -> datetime.datetime:
        """Convert ISO format string back to datetime"""
        try:
            return datetime.datetime.fromisoformat(dt_string)
        except (ValueError, AttributeError):
            # Fallback for older datetime formats
            return datetime.datetime.strptime(dt_string, "%Y-%m-%d %H:%M:%S.%f")

    @staticmethod
    def format_duration(seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            return f"{seconds / 60:.1f}m"
        else:
            return f"{seconds / 3600:.1f}h"


class FileHelper:
    """Helper functions for file operations"""

    @staticmethod
    def ensure_directory(path: str) -> None:
        """Ensure directory exists"""
        os.makedirs(path, exist_ok=True)

    @staticmethod
    def safe_filename(name: str) -> str:
        """Convert string to safe filename"""
        import re
        safe = re.sub(r'[^\w\-_.]', '_', name)
        return safe[:255]  # Limit filename length

    @staticmethod
    def get_file_hash(file_path: str) -> str:
        """Get SHA-256 hash of file"""
        import hashlib
        hash_sha256 = hashlib.sha256()
        try:
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_sha256.update(chunk)
            return hash_sha256.hexdigest()
        except Exception:
            return ""


class ValidationHelper:
    """Helper functions for data validation"""

    @staticmethod
    def validate_email(email: str) -> bool:
        """Basic email validation"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None

    @staticmethod
    def validate_project_name(name: str) -> bool:
        """Validate project name"""
        return (len(name.strip()) >= 3 and
                len(name.strip()) <= 100 and
                name.strip().replace(' ', '').replace('-', '').replace('_', '').isalnum())

    @staticmethod
    def sanitize_input(text: str) -> str:
        """Basic input sanitization"""
        if not isinstance(text, str):
            return ""
        return text.strip()[:1000]  # Limit length and remove whitespace


# ============================================================================
# SYSTEM INITIALIZATION
# ============================================================================

class SocraticSystem:
    """Main system class that initializes and manages core components"""

    def __init__(self, config_path: Optional[str] = None):
        # Initialize configuration
        self.config_manager = ConfigManager(config_path)
        self.config = self.config_manager.get_config()

        # Initialize logging
        self.log_manager = LogManager(self.config)
        self.logger = self.log_manager.get_logger('system')

        # Initialize event system
        self.event_bus = EventBus(self.logger)

        # Initialize database
        self.db_manager = DatabaseManager(self.config, self.logger)

        # System state
        self.is_initialized = False
        self.start_time = DateTimeHelper.now()

        self.logger.info("Socratic RAG Enhanced system core initialized")

    def initialize(self) -> None:
        """Initialize the complete system"""
        if self.is_initialized:
            return

        try:
            # Validate dependencies
            self._check_dependencies()

            # Initialize database schema
            self._initialize_database()

            # Set up event handlers
            self._setup_event_handlers()

            self.is_initialized = True
            self.logger.info("Socratic RAG Enhanced system fully initialized")

        except Exception as e:
            self.logger.error(f"System initialization failed: {e}")
            raise ConfigurationError(f"System initialization failed: {e}")

    def _check_dependencies(self) -> None:
        """Check for required dependencies"""
        missing_deps = []

        if not ANTHROPIC_AVAILABLE and self.config.claude_api_key:
            missing_deps.append("anthropic")

        if not CHROMADB_AVAILABLE:
            missing_deps.append("chromadb")

        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            missing_deps.append("sentence-transformers")

        if missing_deps:
            self.logger.warning(f"Missing optional dependencies: {', '.join(missing_deps)}")

    def _initialize_database(self) -> None:
        """Initialize database schema"""
        # This will be implemented when we create the database module
        pass

    def _setup_event_handlers(self) -> None:
        """Setup system event handlers"""
        # System monitoring events
        self.event_bus.subscribe('system.error', self._handle_system_error)
        self.event_bus.subscribe('system.warning', self._handle_system_warning)

    def _handle_system_error(self, event: Event) -> None:
        """Handle system error events"""
        self.logger.error(f"System error from {event.source}: {event.data}")

    def _handle_system_warning(self, event: Event) -> None:
        """Handle system warning events"""
        self.logger.warning(f"System warning from {event.source}: {event.data}")

    def shutdown(self) -> None:
        """Shutdown the system gracefully"""
        self.logger.info("Shutting down Socratic RAG Enhanced system")

        try:
            # Close database connections
            self.db_manager.close_all_connections()

            # Save configuration
            self.config_manager.save_config()

            self.logger.info("System shutdown complete")

        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")


# ============================================================================
# GLOBAL SYSTEM INSTANCE
# ============================================================================

# Global system instance (initialized on first import)
_system_instance: Optional[SocraticSystem] = None


def get_system() -> SocraticSystem:
    """Get the global system instance"""
    global _system_instance
    if _system_instance is None:
        _system_instance = SocraticSystem()
        _system_instance.initialize()
    return _system_instance


def get_config() -> SystemConfig:
    """Get system configuration"""
    return get_system().config


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance"""
    return get_system().log_manager.get_logger(name)


def get_event_bus() -> EventBus:
    """Get the event bus"""
    return get_system().event_bus


def get_db_manager() -> DatabaseManager:
    """Get the database manager"""
    return get_system().db_manager


# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

if __name__ == "__main__":
    # Test the core system
    system = SocraticSystem()
    system.initialize()

    logger = get_logger('test')
    logger.info("Core system test successful")


    # Test event system
    def test_handler(event):
        logger.info(f"Received test event: {event.data}")


    event_bus = get_event_bus()
    event_bus.subscribe('test', test_handler)
    event_bus.publish_async('test', 'core_test', {'message': 'Hello from core!'})

    import time

    time.sleep(0.1)  # Allow async event to process

    system.shutdown()

"""What src/core.py Provides:
🔧 Configuration Management

SystemConfig dataclass with all system settings
ConfigManager loads from config.yaml + environment variables
Backward compatible with existing Socratic7 patterns (API_KEY_CLAUDE, etc.)

📝 Logging System

ColorFormatter with colorama support (like current system)
LogManager with console + file logging + error tracking
Structured logging for debugging and monitoring

⚠️ Custom Exceptions

Hierarchy of specific exceptions for different system components
Better error handling than generic exceptions

📡 Event System

EventBus for internal agent communication
Thread-safe publish/subscribe pattern
Async event publishing for performance

🗄️ Database Management

DatabaseManager with connection pooling
Context managers for safe database operations
SQLite optimization (WAL mode, foreign keys)

🛠️ Utilities

DateTimeHelper (fixed - no more deprecated utcnow())
FileHelper for safe file operations
ValidationHelper for data validation"""
