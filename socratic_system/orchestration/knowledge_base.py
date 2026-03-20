"""
Default knowledge base for Socrates AI
"""

# ============================================================================
# KNOWLEDGE BASE ARCHITECTURE AND OPTIMIZATION
# ============================================================================
#
# This module implements a knowledge base for storing and retrieving
# project-specific information used by agents during orchestration.
#
# DESIGN PATTERNS:
# 1. Knowledge Singleton:
#    - One knowledge base per project
#    - Shared across all agents
#    - Prevents duplicate information
#
# 2. Lazy Loading:
#    - Knowledge loaded on-demand
#    - Not loaded until first access
#    - Reduces memory footprint
#
# 3. Caching Layer:
#    - In-memory cache for hot data
#    - LRU eviction for memory management
#    - TTL-based invalidation for stale data
#
# PERFORMANCE METRICS:
# - Knowledge lookup: O(1) average, O(n) worst case
# - Knowledge insertion: O(1)
# - Knowledge update: O(1)
# - Memory per entry: ~500 bytes to 10KB
#
# QUERY OPTIMIZATION:
# - Indexing: Keys are indexed for fast retrieval
# - Batch operations: Group similar queries
# - Query result caching: Cache query results
#
# SCALING CONSIDERATIONS:
# - Single project: <1MB typical
# - Large project: 10-100MB with vector embeddings
# - Distribution: Consider external knowledge store (Redis, Postgres)
#
# CONSISTENCY GUARANTEES:
# - In-memory: Eventually consistent
# - With persistence: Durable after commit
# - Multi-agent: No distributed transactions (CAP theorem)
#
# RECOMMENDED PRACTICES:
# 1. Partition knowledge by agent domain
# 2. Implement knowledge invalidation on project changes
# 3. Add TTL for ephemeral knowledge (session-specific)
# 4. Monitor memory usage for large projects
# 5. Consider sharding for very large knowledge bases
# ============================================================================


DEFAULT_KNOWLEDGE = [
    {
        "id": "software_architecture_patterns",
        "content": "Common software architecture patterns include MVC (Model-View-Controller), "
        "MVP (Model-View-Presenter), MVVM (Model-View-ViewModel), microservices architecture, "
        "layered architecture, and event-driven architecture. Each pattern has specific use cases "
        "and trade-offs.",
        "category": "architecture",
        "metadata": {"topic": "patterns", "difficulty": "intermediate"},
    },
    {
        "id": "python_best_practices",
        "content": "Python best practices include following PEP 8 style guide, using virtual environments, "
        "writing docstrings, implementing proper error handling, using type hints, following the "
        "principle of least privilege, and writing unit tests.",
        "category": "python",
        "metadata": {"topic": "best_practices", "language": "python"},
    },
    {
        "id": "api_design_principles",
        "content": "REST API design principles include using appropriate HTTP methods, meaningful resource "
        "URLs, consistent naming conventions, proper status codes, versioning, authentication and "
        "authorization, rate limiting, and comprehensive documentation.",
        "category": "api_design",
        "metadata": {"topic": "rest_api", "difficulty": "intermediate"},
    },
    {
        "id": "database_design_basics",
        "content": "Database design fundamentals include normalization, defining primary and foreign keys, "
        "indexing strategy, choosing appropriate data types, avoiding SQL injection, implementing "
        "proper backup strategies, and optimizing queries for performance.",
        "category": "database",
        "metadata": {"topic": "design", "difficulty": "beginner"},
    },
    {
        "id": "security_considerations",
        "content": "Security considerations in software development include input validation, authentication "
        "and authorization, secure communication (HTTPS), data encryption, regular security "
        "updates, logging and monitoring, and following the principle of least privilege.",
        "category": "security",
        "metadata": {"topic": "general_security", "difficulty": "intermediate"},
    },
]
