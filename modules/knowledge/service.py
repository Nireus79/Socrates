"""
KnowledgeService - Service for knowledge management.

Includes:
- Knowledge base management
- Semantic search
- CRUD operations
- Event publishing for knowledge updates
"""

import logging
from typing import Any, Dict, Optional
from core.base_service import BaseService
from core.event_bus import EventBus


class KnowledgeService(BaseService):
    """Service for managing knowledge and embeddings."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize knowledge service."""
        super().__init__("knowledge", config)
        self.vector_db = None
        self.knowledge_index: Dict[str, str] = {}
        self.event_bus: Optional[EventBus] = None
        self.logger = logging.getLogger(f"socrates.{self.service_name}")

    async def initialize(self) -> None:
        """Initialize the knowledge service."""
        try:
            self.vector_db = {}
            self.logger.info("Knowledge service initialized")
        except Exception as e:
            self.logger.error(f"Failed to initialize: {e}")
            raise

    async def shutdown(self) -> None:
        """Shutdown the knowledge service."""
        try:
            self.knowledge_index.clear()
            self.logger.info("Knowledge service shutdown complete")
        except Exception as e:
            self.logger.error(f"Error during shutdown: {e}")

    def set_event_bus(self, event_bus: EventBus) -> None:
        """Set the event bus for publishing events."""
        self.event_bus = event_bus
        self.logger.debug("Event bus set for knowledge service")

    async def health_check(self) -> Dict[str, Any]:
        """Check service health."""
        return {"vector_db": "healthy", "knowledge_items": len(self.knowledge_index)}

    async def search_knowledge(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search knowledge base."""
        results = [{"doc_id": k, "content": v[:200]} for k, v in self.knowledge_index.items() if query.lower() in v.lower()]
        return {"query": query, "results": results[:limit], "total": len(results)}

    async def add_knowledge(self, content: str, metadata: Optional[Dict] = None) -> str:
        """Add knowledge to the base."""
        doc_id = f"doc_{len(self.knowledge_index)}"
        self.knowledge_index[doc_id] = content

        # Publish knowledge_added event
        if self.event_bus:
            try:
                await self.event_bus.publish(
                    "knowledge_added",
                    self.service_name,
                    {
                        "doc_id": doc_id,
                        "content_length": len(content),
                        "metadata": metadata or {},
                    }
                )
            except Exception as e:
                self.logger.error(f"Error publishing knowledge_added event: {e}")

        return doc_id

    async def update_knowledge(self, knowledge_id: str, content: str) -> bool:
        """Update existing knowledge."""
        if knowledge_id in self.knowledge_index:
            self.knowledge_index[knowledge_id] = content
            return True
        return False

    async def delete_knowledge(self, knowledge_id: str) -> bool:
        """Delete knowledge item."""
        if knowledge_id in self.knowledge_index:
            del self.knowledge_index[knowledge_id]
            return True
        return False

    async def get_knowledge(self, knowledge_id: str) -> Optional[str]:
        """Get specific knowledge item."""
        return self.knowledge_index.get(knowledge_id)
