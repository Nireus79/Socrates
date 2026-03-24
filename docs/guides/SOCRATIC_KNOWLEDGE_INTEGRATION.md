# Socratic Knowledge Integration Guide

**Version:** 1.0
**Status:** Complete
**Last Updated:** 2026-03-24

---

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Core Concepts](#core-concepts)
4. [API Reference](#api-reference)
5. [Integration Patterns](#integration-patterns)
6. [Examples](#examples)
7. [Best Practices](#best-practices)

---

## Overview

**socratic-knowledge** is an enterprise knowledge management system providing:

- **Multi-tenant architecture** - Isolate knowledge by tenant/organization
- **Access control** - Role-based permissions (RBAC)
- **Versioning** - Track knowledge evolution
- **Collaboration** - Conflict resolution and locking
- **Audit logging** - Track all changes
- **RAG integration** - Retrieval-augmented generation support

### Use Cases

| Use Case | Benefit |
|----------|---------|
| **Knowledge Base** | Central repository for learning resources |
| **Documentation** | Version-controlled documentation system |
| **Team Collaboration** | Multi-user editing with conflict resolution |
| **Compliance** | Audit trail for all changes |
| **RAG Backend** | Knowledge source for LLM-powered systems |

---

## Installation

### Prerequisites
- Python 3.8+
- socratic-core >= 0.1.0

### From PyPI

```bash
pip install socratic-knowledge
```

### Verify Installation

```python
from socratic_knowledge import (
    KnowledgeManager,
    KnowledgeItem,
    Collection,
    Tenant
)

print("socratic-knowledge imported successfully")
```

---

## Core Concepts

### KnowledgeItem

Individual piece of knowledge/content.

```python
from socratic_knowledge import KnowledgeItem

item = KnowledgeItem(
    id="know_123",
    title="Python Testing Best Practices",
    content="Use pytest for testing...",
    category="testing",
    tags=["python", "testing", "pytest"],
    created_by="user_123",
    version=1
)
```

### Collection

Organize knowledge items into groups.

```python
from socratic_knowledge import Collection

collection = Collection(
    id="col_123",
    name="Python Guide",
    description="Complete Python learning path",
    owner="user_123",
    items=["know_1", "know_2", "know_3"],
    visibility="public"  # or "private"
)
```

### Tenant

Multi-tenant isolation for organizations.

```python
from socratic_knowledge import Tenant

tenant = Tenant(
    id="org_acme",
    name="ACME Corporation",
    plan="enterprise",
    knowledge_quota=10000,
    users_limit=100
)
```

### User

User with specific permissions within a tenant.

```python
from socratic_knowledge import User

user = User(
    id="user_123",
    email="alice@acme.com",
    tenant_id="org_acme",
    role="editor",  # "viewer", "editor", "admin"
    permissions=["read", "write", "delete"]
)
```

### Version

Track knowledge evolution.

```python
from socratic_knowledge import Version

version = Version(
    item_id="know_123",
    version_number=2,
    content="Updated content...",
    changed_by="user_123",
    change_summary="Fixed typos and added examples"
)
```

---

## API Reference

### KnowledgeManager

Main interface for knowledge operations.

```python
from socratic_knowledge import KnowledgeManager

# Initialize
manager = KnowledgeManager(
    tenant_id="org_acme",
    user_id="user_123"
)
```

#### CRUD Operations

```python
# Create knowledge item
item = manager.create_knowledge_item(
    title="Testing Guide",
    content="How to write tests...",
    category="testing",
    tags=["python", "testing"]
)

# Read knowledge item
item = manager.get_knowledge_item(item_id="know_123")

# Update knowledge item
manager.update_knowledge_item(
    item_id="know_123",
    content="Updated content...",
    change_summary="Added examples"
)

# Delete knowledge item
manager.delete_knowledge_item(item_id="know_123")
```

#### Collection Management

```python
# Create collection
collection = manager.create_collection(
    name="Python Guide",
    description="Complete Python learning path"
)

# Add items to collection
manager.add_to_collection(
    collection_id="col_123",
    item_ids=["know_1", "know_2", "know_3"]
)

# Get collection
collection = manager.get_collection(collection_id="col_123")

# List collections
collections = manager.list_collections()
```

#### Search

```python
# Search by keyword
results = manager.search(
    query="testing",
    category="testing",
    limit=10
)

# Search by tag
results = manager.search_by_tag(tags=["python", "testing"])

# Get recent items
items = manager.get_recent_items(limit=20)
```

#### Version Control

```python
# Get versions
versions = manager.get_item_versions(item_id="know_123")

# Restore version
manager.restore_version(
    item_id="know_123",
    version_number=1
)

# Compare versions
diff = manager.compare_versions(
    item_id="know_123",
    version_a=1,
    version_b=2
)
```

#### Access Control

```python
# Check permissions
can_edit = manager.check_permission(
    item_id="know_123",
    action="write"
)

# Share knowledge
manager.share_knowledge(
    item_id="know_123",
    user_id="user_456",
    permission="read"
)

# Grant permission
manager.grant_permission(
    item_id="know_123",
    user_id="user_456",
    permission="write"
)
```

#### Audit

```python
# Get audit log
events = manager.get_audit_log(item_id="know_123")

# Get user activity
activity = manager.get_user_activity(user_id="user_123")

# Export audit trail
manager.export_audit_trail(
    start_date="2026-03-01",
    end_date="2026-03-31"
)
```

---

## Integration Patterns

### Pattern 1: Knowledge Base for Agents

Use knowledge base to enhance agent responses.

```python
from socratic_knowledge import KnowledgeManager
from socratic_system.orchestration import AgentOrchestrator

class KnowledgeEnhancedOrchestrator:
    def __init__(self, tenant_id: str, user_id: str):
        self.km = KnowledgeManager(tenant_id, user_id)
        self.orchestrator = AgentOrchestrator()

    def process_request_with_knowledge(self, request: dict) -> dict:
        """Enhance request with relevant knowledge"""

        # Search for relevant knowledge
        query = request.get("query", "")
        relevant = self.km.search(query, limit=3)

        # Enhance request context
        request["context"] = {
            **request.get("context", {}),
            "relevant_knowledge": [
                {
                    "title": item.title,
                    "content": item.content,
                    "category": item.category
                }
                for item in relevant
            ]
        }

        # Process with enhanced context
        return self.orchestrator.process_request(request)

# Usage
enhancer = KnowledgeEnhancedOrchestrator("org_acme", "user_123")
result = enhancer.process_request_with_knowledge({
    "agent": "QualityController",
    "action": "analyze",
    "query": "How to improve code quality?"
})
```

### Pattern 2: Collaborative Knowledge Creation

Multiple users creating and refining knowledge.

```python
from socratic_knowledge import KnowledgeManager

class CollaborativeKnowledgeBuilder:
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id

    def create_draft(self, user_id: str, title: str, content: str):
        """User creates draft knowledge"""
        manager = KnowledgeManager(self.tenant_id, user_id)

        return manager.create_knowledge_item(
            title=title,
            content=content,
            category="draft",
            tags=["draft"],
            status="draft"
        )

    def review_and_approve(self, reviewer_id: str, item_id: str, feedback: str):
        """Reviewer checks and approves"""
        manager = KnowledgeManager(self.tenant_id, reviewer_id)

        # Update with review
        manager.update_knowledge_item(
            item_id=item_id,
            content=manager.get_knowledge_item(item_id).content,
            change_summary=f"Reviewed: {feedback}",
            status="approved"
        )

        # Remove draft tag
        manager.remove_tag(item_id, "draft")

    def publish(self, publisher_id: str, item_id: str):
        """Publish approved knowledge"""
        manager = KnowledgeManager(self.tenant_id, publisher_id)

        manager.update_knowledge_item(
            item_id=item_id,
            status="published",
            visibility="public"
        )

# Usage
builder = CollaborativeKnowledgeBuilder("org_acme")

# Alice drafts
draft = builder.create_draft("alice", "Python Testing", "...")

# Bob reviews
builder.review_and_approve("bob", draft.id, "Good content, minor typos")

# Carol publishes
builder.publish("carol", draft.id)
```

### Pattern 3: Learning Path Organization

Organize knowledge into structured learning paths.

```python
from socratic_knowledge import KnowledgeManager

class LearningPathBuilder:
    def __init__(self, tenant_id: str, user_id: str):
        self.manager = KnowledgeManager(tenant_id, user_id)

    def create_learning_path(self, title: str, description: str, items: list) -> str:
        """Create structured learning path"""

        collection = self.manager.create_collection(
            name=title,
            description=description
        )

        # Add items in order
        for i, item_spec in enumerate(items):
            # Create item with sequencing
            item = self.manager.create_knowledge_item(
                title=item_spec["title"],
                content=item_spec["content"],
                category="learning_path",
                tags=[title, f"step_{i+1}"],
                difficulty=item_spec.get("difficulty", "beginner"),
                prerequisites=item_spec.get("prerequisites", [])
            )

            self.manager.add_to_collection(
                collection.id,
                [item.id]
            )

        return collection.id

    def get_learning_path(self, collection_id: str) -> dict:
        """Get complete learning path"""

        collection = self.manager.get_collection(collection_id)
        items = [
            self.manager.get_knowledge_item(item_id)
            for item_id in collection.items
        ]

        return {
            "path_name": collection.name,
            "description": collection.description,
            "items": sorted(items, key=lambda x: x.tags),
            "total_steps": len(items)
        }

# Usage
builder = LearningPathBuilder("org_acme", "user_123")

path_id = builder.create_learning_path(
    title="Python Mastery",
    description="From basics to advanced",
    items=[
        {"title": "Basics", "content": "...", "difficulty": "beginner"},
        {"title": "OOP", "content": "...", "difficulty": "intermediate"},
        {"title": "Concurrency", "content": "...", "difficulty": "advanced"}
    ]
)

path = builder.get_learning_path(path_id)
print(f"Learning path: {path['path_name']} with {path['total_steps']} steps")
```

---

## Examples

### Example 1: Multi-Tenant Knowledge Base

```python
"""Setup knowledge base for multiple tenants"""

from socratic_knowledge import KnowledgeManager, Tenant

# Create tenant
tenant = Tenant(
    id="org_acme",
    name="ACME Corporation",
    plan="enterprise"
)

# Add knowledge for tenant
manager = KnowledgeManager("org_acme", "user_123")

# Add resources
python_guide = manager.create_knowledge_item(
    title="Python Quick Start",
    content="Get started with Python in 30 minutes...",
    category="tutorial",
    tags=["python", "beginner"]
)

testing_guide = manager.create_knowledge_item(
    title="Testing Best Practices",
    content="How to write effective tests...",
    category="best_practices",
    tags=["testing", "python"]
)

# Create collection
collection = manager.create_collection(
    name="Python Learning Path",
    description="Complete Python education"
)

manager.add_to_collection(
    collection.id,
    [python_guide.id, testing_guide.id]
)

print(f"Knowledge base setup complete for {tenant.name}")
```

### Example 2: Versioned Knowledge Evolution

```python
"""Track knowledge evolution with versions"""

from socratic_knowledge import KnowledgeManager

manager = KnowledgeManager("org_acme", "user_123")

# Create initial knowledge
item = manager.create_knowledge_item(
    title="API Design Guide",
    content="Version 1: Basic REST API design...",
    category="guide"
)

# Update multiple times
manager.update_knowledge_item(
    item.id,
    content="Version 2: Added authentication examples...",
    change_summary="Added auth examples"
)

manager.update_knowledge_item(
    item.id,
    content="Version 3: Updated with GraphQL info...",
    change_summary="Added GraphQL comparison"
)

# Get all versions
versions = manager.get_item_versions(item.id)

print(f"Total versions: {len(versions)}")
for v in versions:
    print(f"  Version {v.version_number}: {v.change_summary}")

# Compare versions
diff = manager.compare_versions(item.id, 1, 3)
print(f"Changes between v1 and v3: {diff}")
```

### Example 3: Audit and Compliance

```python
"""Track all knowledge changes for compliance"""

from socratic_knowledge import KnowledgeManager
from datetime import datetime, timedelta

manager = KnowledgeManager("org_acme", "user_123")

# Create knowledge
item = manager.create_knowledge_item(
    title="Sensitive Data",
    content="Confidential information...",
    category="confidential"
)

# Update knowledge
manager.update_knowledge_item(
    item.id,
    content="Updated confidential...",
    change_summary="Updated per compliance"
)

# Get audit trail
audit_events = manager.get_audit_log(item.id)

print("Audit Trail:")
for event in audit_events:
    print(f"  {event.timestamp}: {event.action} by {event.user_id}")
    print(f"    Details: {event.details}")

# Export for compliance
manager.export_audit_trail(
    start_date="2026-03-01",
    end_date="2026-03-31"
)
```

---

## Best Practices

### 1. Use Collections for Organization

```python
# Good: Organize by collections
collection = manager.create_collection(
    name="Python Learning",
    description="Complete Python education"
)
manager.add_to_collection(collection.id, item_ids)

# Avoid: Flat structure
# Just dumping items without organization
```

### 2. Tag Consistently

```python
# Good: Consistent tagging scheme
manager.create_knowledge_item(
    title="Item",
    content="...",
    tags=["domain:python", "level:beginner", "type:tutorial"]
)

# Avoid: Inconsistent tags
manager.create_knowledge_item(
    title="Item",
    content="...",
    tags=["python-beginner-tutorial", "py-101", "intro-py"]
)
```

### 3. Document Changes

```python
# Good: Descriptive change summaries
manager.update_knowledge_item(
    item.id,
    content="...",
    change_summary="Added examples for async/await syntax (closes #42)"
)

# Avoid: Vague changes
manager.update_knowledge_item(
    item.id,
    content="..."
    # Missing change_summary
)
```

### 4. Leverage Access Control

```python
# Good: Share with specific permissions
manager.share_knowledge(item_id, "user_456", "read")

# Avoid: Making everything public
manager.update_knowledge_item(item.id, visibility="public")
```

### 5. Use Async for Bulk Operations

```python
from socratic_knowledge import AsyncKnowledgeManager

async def bulk_import(tenant_id: str, items: list):
    """Import items asynchronously"""

    manager = AsyncKnowledgeManager(tenant_id, "import_user")

    # Create items in parallel
    tasks = [
        manager.create_knowledge_item(
            title=item["title"],
            content=item["content"]
        )
        for item in items
    ]

    results = await asyncio.gather(*tasks)
    return results
```

---

## Troubleshooting

### Permission Denied

**Problem:** User cannot access knowledge item

**Solution:** Check user permissions and tenant access

```python
manager = KnowledgeManager(tenant_id, user_id)

# Verify user has access
item = manager.get_knowledge_item(item_id)
if not item:
    print("User lacks permissions or item doesn't exist")

# Check specific permission
can_write = manager.check_permission(item_id, "write")
```

### Version Conflicts

**Problem:** Concurrent edits cause conflicts

**Solution:** Use locking mechanism

```python
# Acquire lock before editing
lock = manager.acquire_lock(item_id, timeout=300)

try:
    # Safe to edit
    manager.update_knowledge_item(item_id, content="...")
finally:
    # Release lock
    manager.release_lock(item_id, lock)
```

---

## Related Documentation

- [Architecture Overview](../ARCHITECTURE.md)
- [Common Integration Patterns](./COMMON_INTEGRATION_PATTERNS.md)
- [Database API](./DATABASE_API.md)

