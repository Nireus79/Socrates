# Database API Reference

**Version:** 2.0
**Status:** Stable
**Last Updated:** 2026-03-24

---

## Table of Contents

1. [Overview](#overview)
2. [ProjectDatabase](#projectdatabase)
3. [VectorDatabase](#vectordatabase)
4. [KnowledgeManager](#knowledgemanager)
5. [DatabaseSingleton](#databasesingleton)
6. [Query Examples](#query-examples)
7. [Best Practices](#best-practices)

---

## Overview

The Socrates database layer provides three main interfaces:

- **ProjectDatabase**: SQLite-based relational database for projects, users, and metadata
- **VectorDatabase**: Vector search for knowledge entries using RAG
- **KnowledgeManager**: High-level interface for knowledge base operations
- **DatabaseSingleton**: Singleton access pattern for database connections

### Architecture

```
Application Layer
    ↓
DatabaseSingleton (connection management)
    ↓
┌─────────────────┬──────────────────┬──────────────────┐
│ ProjectDatabase │ VectorDatabase   │ KnowledgeManager │
└─────────────────┴──────────────────┴──────────────────┘
    ↓                    ↓                      ↓
SQLite (normalized)   ChromaDB (vectors)    RAG Index
```

---

## ProjectDatabase

SQLite database with normalized schema (no BLOB pickling).

### Initialization

```python
from socratic_system.database import ProjectDatabase
import os

# Option 1: Explicit path
db = ProjectDatabase(db_path="/path/to/projects.db")

# Option 2: Environment variable
os.environ["SOCRATES_DATA_DIR"] = "/data/socrates"
db = ProjectDatabase()  # Uses SOCRATES_DATA_DIR + "projects.db"

# Option 3: Default location
db = ProjectDatabase()  # Uses ~/.socrates/projects.db
```

### Core Methods

#### Projects

```python
# Save project
db.save_project(project)

# Load project
project = db.load_project(project_id="proj_123")

# Get all projects
projects = db.get_all_projects()

# Get user projects
projects = db.get_user_projects(user_id="user_123")

# Delete project
db.delete_project(project_id="proj_123")
```

#### Users

```python
# Create user
user = User(user_id="user_123", email="user@example.com")
db.create_user(user)

# Get user
user = db.get_user(user_id="user_123")

# Update user
db.update_user(user)

# Get all users
users = db.get_all_users()
```

#### Queries

```python
# Query projects by status
projects = db.query_projects(status="active")

# Query projects by owner
projects = db.query_projects(owner="user_123")

# Custom SQL query
cursor = db.execute(
    "SELECT * FROM projects WHERE quality_score > ?",
    (0.8,)
)
results = cursor.fetchall()
```

#### Batch Operations

```python
# Save multiple projects
db.batch_save_projects([project1, project2, project3])

# Delete multiple users
db.batch_delete_users(["user_1", "user_2", "user_3"])
```

### Configuration

```python
# Enable database encryption
import os
os.environ["SECURITY_DATABASE_ENCRYPTION"] = "true"
db = ProjectDatabase()

# Set custom data directory
os.environ["SOCRATES_DATA_DIR"] = "/custom/path"
db = ProjectDatabase()

# Configure connection pool
db.set_connection_pool_size(max_connections=10)
```

---

## VectorDatabase

Vector search for knowledge entries using RAG (Retrieval-Augmented Generation).

### Initialization

```python
from socratic_system.database import VectorDatabase

# Create vector database
vdb = VectorDatabase(
    db_path="/path/to/chroma",
    embedding_model="all-MiniLM-L6-v2"  # Default model
)
```

### Core Methods

#### Add Knowledge

```python
from socratic_system.models import KnowledgeEntry

# Create knowledge entry
entry = KnowledgeEntry(
    id="know_123",
    content="Python testing best practices...",
    category="testing",
    tags=["python", "testing", "pytest"],
    source="documentation"
)

# Add to vector database
vdb.add_knowledge(entry)

# Add multiple entries
vdb.batch_add_knowledge([entry1, entry2, entry3])
```

#### Search Knowledge

```python
# Search by semantic similarity
results = vdb.search_similar(
    query="How do I write unit tests?",
    top_k=5,
    threshold=0.5
)

# Results structure
for result in results:
    {
        "id": "know_123",
        "content": "...",
        "score": 0.92,  # Similarity score
        "metadata": {...}
    }
```

#### Retrieve Knowledge

```python
# Get knowledge entry
entry = vdb.get_knowledge(entry_id="know_123")

# Get by category
entries = vdb.get_by_category(category="testing")

# Get by tags
entries = vdb.get_by_tags(tags=["python", "testing"])
```

#### Manage Knowledge

```python
# Update knowledge entry
vdb.update_knowledge(entry_id="know_123", content="Updated content...")

# Delete knowledge entry
vdb.delete_knowledge(entry_id="know_123")

# Clear category
vdb.delete_category(category="obsolete")

# Get statistics
stats = vdb.get_statistics()
# Returns: {total_entries, categories, avg_similarity, ...}
```

### Configuration

```python
# Custom embedding model
vdb = VectorDatabase(
    db_path="/path/to/vectors",
    embedding_model="all-mpnet-base-v2"  # Larger, slower, more accurate
)

# Configure RAG settings
vdb.set_chunk_size(chunk_size=1024)
vdb.set_chunk_overlap(overlap=100)
vdb.set_cache_ttl(ttl_seconds=7200)
```

---

## KnowledgeManager

High-level interface for knowledge base operations.

### Initialization

```python
from socratic_system.database import KnowledgeManager

# Create manager
km = KnowledgeManager(
    vector_db_path="/path/to/vectors",
    project_db_path="/path/to/projects.db"
)
```

### Methods

#### Add Knowledge

```python
# Add learning resource
km.add_learning_resource(
    resource_id="res_123",
    title="Python Testing Guide",
    content="...",
    category="testing",
    tags=["python", "pytest"],
    difficulty_level="intermediate"
)

# Add skill definition
km.add_skill(
    skill_id="skill_123",
    name="Unit Testing",
    description="Write effective unit tests",
    prerequisites=["Python Basics"],
    resources=["res_1", "res_2"]
)
```

#### Search Knowledge

```python
# Search for resources
resources = km.search_resources(
    query="testing with mocking",
    category="testing",
    difficulty="intermediate"
)

# Find related skills
skills = km.find_related_skills(
    skill_name="Unit Testing"
)
```

#### Get Recommendations

```python
# Get learning recommendations
recommendations = km.get_recommendations(
    user_id="user_123",
    based_on=["code_quality", "testing"],
    limit=5
)

# Returns: [
#     {skill_id, name, reasoning, confidence},
#     ...
# ]
```

#### Manage Knowledge

```python
# Update resource
km.update_resource(
    resource_id="res_123",
    content="Updated content...",
    tags=["python", "pytest", "mocking"]
)

# Delete resource
km.delete_resource(resource_id="res_123")

# Get knowledge statistics
stats = km.get_knowledge_statistics()
# Returns: {total_resources, total_skills, categories, coverage}
```

---

## DatabaseSingleton

Singleton pattern for database access.

### Usage

```python
from socratic_system.database import DatabaseSingleton

# Get singleton instance
db = DatabaseSingleton.get_instance()

# First call initializes, subsequent calls return same instance
db2 = DatabaseSingleton.get_instance()
assert db is db2  # True - same object

# Initialize with custom path
DatabaseSingleton.initialize(db_path="/custom/path")
instance = DatabaseSingleton.get_instance()
```

### Reset Instance

```python
# Reset singleton (for testing)
DatabaseSingleton.reset()

# Now get_instance will create new connection
db = DatabaseSingleton.get_instance()
```

---

## Query Examples

### Project Queries

```python
from socratic_system.database import ProjectDatabase

db = ProjectDatabase()

# Get projects by status
active = db.query_projects(
    status="active"
)

# Get projects updated in last 7 days
from datetime import datetime, timedelta
recent_date = (datetime.now() - timedelta(days=7)).isoformat()
recent = db.execute(
    "SELECT * FROM projects WHERE updated_at > ?",
    (recent_date,)
).fetchall()

# Find high-quality projects
quality = db.execute(
    "SELECT * FROM projects WHERE quality_score > 0.8 ORDER BY quality_score DESC"
).fetchall()

# Get statistics by user
stats = db.execute(
    "SELECT user_id, COUNT(*) as count, AVG(quality_score) as avg_quality "
    "FROM projects GROUP BY user_id"
).fetchall()
```

### Vector Database Queries

```python
from socratic_system.database import VectorDatabase

vdb = VectorDatabase(db_path="/path/to/vectors")

# Find resources about a topic
results = vdb.search_similar(
    query="How to improve code quality?",
    top_k=10,
    threshold=0.6
)

# Get all testing resources
testing_entries = vdb.get_by_category("testing")

# Search with metadata filter
results = vdb.search_similar(
    query="Python best practices",
    filters={"source": "documentation"}
)
```

### Join Queries

```python
# Find users who haven't created projects yet
from socratic_system.database import DatabaseSingleton

db = DatabaseSingleton.get_instance()

results = db.execute(
    """
    SELECT u.user_id, u.email
    FROM users u
    LEFT JOIN projects p ON u.user_id = p.owner_id
    WHERE p.project_id IS NULL
    """
).fetchall()

# Find projects with quality improvements
results = db.execute(
    """
    SELECT p.project_id, p.name,
           h.old_score, h.new_score,
           (h.new_score - h.old_score) as improvement
    FROM projects p
    JOIN maturity_history h ON p.project_id = h.project_id
    WHERE h.new_score > h.old_score
    ORDER BY improvement DESC
    """
).fetchall()
```

---

## Best Practices

### 1. Use Connection Pooling

```python
# Good: Reuse database connection
db = ProjectDatabase()

for project in projects:
    db.save_project(project)  # Reuses connection

# Avoid: Creating new connection per operation
for project in projects:
    db = ProjectDatabase()  # Creates new connection each time
    db.save_project(project)
```

### 2. Batch Operations

```python
from socratic_system.database import ProjectDatabase

db = ProjectDatabase()

# Good: Batch save
db.batch_save_projects(projects)

# Avoid: Individual saves
for project in projects:
    db.save_project(project)
```

### 3. Use Transactions

```python
# Good: Use transactions for related operations
db = ProjectDatabase()

try:
    db.start_transaction()
    db.save_project(project)
    db.add_user_to_project(user_id, project_id)
    db.commit()
except Exception as e:
    db.rollback()
    raise
```

### 4. Parameterized Queries

```python
from socratic_system.database import ProjectDatabase

db = ProjectDatabase()

# Good: Parameterized (safe)
results = db.execute(
    "SELECT * FROM projects WHERE owner_id = ? AND status = ?",
    (user_id, "active")
).fetchall()

# Avoid: String concatenation (SQL injection)
results = db.execute(
    f"SELECT * FROM projects WHERE owner_id = '{user_id}'"
).fetchall()
```

### 5. Cache Vector Searches

```python
from socratic_core.utils import TTLCache

class CachedKnowledgeManager:
    def __init__(self, km):
        self.km = km
        self.cache = TTLCache(ttl_minutes=60)

    def search_resources(self, query: str):
        """Search with caching"""
        if query in self.cache:
            return self.cache[query]

        results = self.km.search_resources(query)
        self.cache[query] = results
        return results
```

### 6. Error Handling

```python
from socratic_system.database import ProjectDatabase

db = ProjectDatabase()

try:
    project = db.load_project(project_id="proj_123")
    if not project:
        raise ValueError("Project not found")
except FileNotFoundError:
    print("Database file not found")
except ValueError as e:
    print(f"Validation error: {e}")
except Exception as e:
    print(f"Unexpected error: {e}")
```

---

## Troubleshooting

### Database Lock

**Problem:** "database is locked" error

**Solution:** Check for long-running operations or multiple connections.

```python
# Ensure connections are properly closed
db = ProjectDatabase()
try:
    results = db.execute("SELECT * FROM projects")
finally:
    db.close()  # Always close

# Or use context manager
with ProjectDatabase() as db:
    results = db.execute("SELECT * FROM projects")
```

### Vector Database Not Found

**Problem:** VectorDatabase initialization fails

**Solution:** Ensure ChromaDB and RAG dependencies are installed.

```bash
pip install socratic-rag chromadb sentence-transformers
```

### Query Performance

**Problem:** Slow queries

**Solution:** Use indexes and parameterized queries.

```python
# Check if index exists
db = ProjectDatabase()
indexes = db.get_indexes()

# Create index if needed
db.create_index("projects", "owner_id")
db.create_index("projects", "status")
```

---

## Related Documentation

- [Architecture Overview](../ARCHITECTURE.md)
- [Configuration Guide](../guides/CONFIGURATION_GUIDE.md)
- [Orchestration API](./ORCHESTRATION_API.md)

