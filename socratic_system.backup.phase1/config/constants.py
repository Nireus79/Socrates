"""
System-wide constants for Socrates RAG System

This module centralizes all magic numbers and configuration constants
to improve maintainability and make tuning system behavior easier.
"""

# ============================================================================
# TOKEN AND USAGE THRESHOLDS
# ============================================================================

# Token warning threshold (tokens)
TOKEN_WARNING_THRESHOLD = 50000

# Token usage high threshold (tokens)
TOKEN_USAGE_HIGH_THRESHOLD = 40000

# ============================================================================
# MATURITY SCORING THRESHOLDS
# ============================================================================

# Ready to advance threshold (percentage) - when QC kicks in
MATURITY_THRESHOLD_HIGH = 20.0

# Medium maturity threshold (percentage)
MATURITY_THRESHOLD_MEDIUM = 10.0

# Low maturity threshold (percentage)
MATURITY_THRESHOLD_LOW = 5.0

# ============================================================================
# DOCUMENT PROCESSING CONFIGURATION
# ============================================================================

# Default chunk size for document splitting (characters)
DEFAULT_CHUNK_SIZE = 500

# Default overlap between chunks (characters)
DEFAULT_CHUNK_OVERLAP = 50

# ============================================================================
# ENGAGEMENT METRICS
# ============================================================================

# High engagement threshold (interactions)
ENGAGEMENT_THRESHOLD_HIGH = 10

# Low engagement threshold (interactions)
ENGAGEMENT_THRESHOLD_LOW = 5

# ============================================================================
# QUESTION GENERATION
# ============================================================================

# Maximum questions per session
MAX_QUESTIONS_PER_SESSION = 50

# Question difficulty levels
QUESTION_DIFFICULTY_LEVELS = ["beginner", "intermediate", "advanced"]

# ============================================================================
# PROJECT PHASES
# ============================================================================

PROJECT_PHASES = ["discovery", "analysis", "design", "implementation", "completion"]

# ============================================================================
# LEARNING AND BEHAVIOR TRACKING
# ============================================================================

# Minimum interactions before tracking behavior pattern
MIN_INTERACTIONS_FOR_PATTERN = 3

# Time window for behavior analysis (days)
BEHAVIOR_ANALYSIS_WINDOW_DAYS = 7

# ============================================================================
# ANALYTICS CONFIGURATION
# ============================================================================

# Default analytics batch size
ANALYTICS_BATCH_SIZE = 100

# Analytics calculation precision
ANALYTICS_PRECISION_DECIMAL = 2

# ============================================================================
# VECTOR EMBEDDINGS
# ============================================================================

# Vector embedding dimension (for sentence-transformers)
EMBEDDING_DIMENSION = 384

# Vector search top-k results
VECTOR_SEARCH_TOP_K = 5

# Vector similarity threshold for relevance
VECTOR_SIMILARITY_THRESHOLD = 0.6

# ============================================================================
# CACHE CONFIGURATION
# ============================================================================

# Cache TTL in seconds
CACHE_TTL_SECONDS = 3600

# Maximum cache size in MB
MAX_CACHE_SIZE_MB = 100

# ============================================================================
# DATABASE CONFIGURATION
# ============================================================================

# Maximum connections in connection pool
MAX_DB_CONNECTIONS = 10

# Database query timeout in seconds
DB_QUERY_TIMEOUT_SECONDS = 30

# ============================================================================
# API CONFIGURATION
# ============================================================================

# Claude API request timeout (seconds)
CLAUDE_API_TIMEOUT_SECONDS = 60

# Maximum retries for API calls
MAX_API_RETRIES = 3

# Retry backoff multiplier (exponential backoff)
RETRY_BACKOFF_MULTIPLIER = 2

# ============================================================================
# SUBSCRIPTION TIERS
# ============================================================================

# Subscription tier names
SUBSCRIPTION_TIERS = ["free", "pro", "enterprise"]

# Default subscription tier for new users
DEFAULT_SUBSCRIPTION_TIER = "free"

# ============================================================================
# FILE OPERATIONS
# ============================================================================

# Maximum file size for import (MB)
MAX_FILE_SIZE_MB = 10

# Supported document file extensions
SUPPORTED_DOC_EXTENSIONS = [".pdf", ".txt", ".md", ".docx"]

# ============================================================================
# LOGGING
# ============================================================================

# Log level for console output
CONSOLE_LOG_LEVEL = "INFO"

# Log level for file output
FILE_LOG_LEVEL = "DEBUG"

# Maximum log file size (MB)
MAX_LOG_FILE_SIZE_MB = 10

# Number of backup log files to keep
LOG_BACKUP_COUNT = 5
