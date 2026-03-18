"""
Default knowledge base for Socrates AI
"""

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
