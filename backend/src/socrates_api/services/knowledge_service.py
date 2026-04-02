"""
Knowledge Service Layer for Phase 5 - Knowledge Base Integration

Centralizes all knowledge base operations including document search, analysis,
relationship mapping, gap identification, and relevance scoring.

This service layer provides the foundation for making question generation
KB-aware and document-intelligent.
"""

import logging
import re
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


# ============================================================================
# Data Classes and Enums
# ============================================================================

class RelationshipType(str, Enum):
    """Types of relationships between documents."""
    CROSS_REFERENCE = "cross_reference"
    DEPENDS_ON = "depends_on"
    CONFLICTS_WITH = "conflicts_with"
    COMPLEMENTS = "complements"
    SUPERSEDES = "supersedes"


@dataclass
class DocumentChunk:
    """Represents a chunk of a document with metadata."""
    chunk_id: str
    document_id: str
    content: str
    section: str
    position: int
    page_number: Optional[int] = None
    embedding: Optional[List[float]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert chunk to dictionary for serialization."""
        return {
            "chunk_id": self.chunk_id,
            "document_id": self.document_id,
            "content": self.content,
            "section": self.section,
            "position": self.position,
            "page_number": self.page_number,
            "metadata": self.metadata
        }


@dataclass
class SpecificationGap:
    """Represents a specification gap not covered by documents."""
    gap_id: str
    category: str
    topic: str
    severity: str  # critical, high, medium, low
    priority_score: float  # 0-1
    mentioned_documents: List[str] = field(default_factory=list)
    impact_on_specs: List[str] = field(default_factory=list)
    suggested_question: str = ""
    related_chunks: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert gap to dictionary for serialization."""
        return {
            "gap_id": self.gap_id,
            "category": self.category,
            "topic": self.topic,
            "severity": self.severity,
            "priority_score": self.priority_score,
            "mentioned_documents": self.mentioned_documents,
            "impact_on_specs": self.impact_on_specs,
            "suggested_question": self.suggested_question,
            "related_chunks": self.related_chunks
        }


@dataclass
class DocumentRelationship:
    """Represents a relationship between two documents."""
    source_id: str
    target_id: str
    relationship_type: RelationshipType
    strength: float  # 0-1, confidence in the relationship
    description: str = ""


@dataclass
class DocumentRelationshipGraph:
    """Represents the complete relationship graph of documents."""
    documents: List[Dict[str, Any]] = field(default_factory=list)
    edges: List[DocumentRelationship] = field(default_factory=list)
    conflicts: List[Dict[str, Any]] = field(default_factory=list)
    clusters: List[List[str]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert graph to dictionary for serialization."""
        return {
            "documents": self.documents,
            "edges": [
                {
                    "source": e.source_id,
                    "target": e.target_id,
                    "relationship_type": e.relationship_type.value,
                    "strength": e.strength,
                    "description": e.description
                }
                for e in self.edges
            ],
            "conflicts": self.conflicts,
            "clusters": self.clusters
        }


@dataclass
class QualityScore:
    """Document quality assessment."""
    overall_score: float  # 0-100
    completeness: float  # 0-1
    clarity: float  # 0-1
    consistency: float  # 0-1
    relevance: float  # 0-1
    recency: float  # 0-1
    factors: Dict[str, str] = field(default_factory=dict)


# ============================================================================
# Knowledge Service
# ============================================================================

class KnowledgeService:
    """
    Centralized service for all knowledge base operations.

    Provides methods for:
    - Document search and retrieval
    - Document chunking and optimization
    - Relationship analysis
    - Gap identification
    - Relevance scoring
    """

    def __init__(self, vector_db: Any = None, document_repo: Any = None):
        """
        Initialize the Knowledge Service.

        Args:
            vector_db: Vector database instance (ChromaDB)
            document_repo: Document repository instance
        """
        self.vector_db = vector_db
        self.document_repo = document_repo
        self._gap_cache: Dict[str, List[SpecificationGap]] = {}
        self._relationship_cache: Dict[str, DocumentRelationshipGraph] = {}
        self._quality_cache: Dict[str, QualityScore] = {}

        logger.info("Knowledge Service initialized")

    # ========================================================================
    # Document Search and Retrieval
    # ========================================================================

    def search_documents(
        self,
        query: str,
        project_id: str,
        top_k: int = 5,
        relevance_threshold: float = 0.7
    ) -> List[DocumentChunk]:
        """
        Search documents with relevance filtering.

        Performs semantic search using vector database and filters results
        by relevance threshold.

        Args:
            query: Search query string
            project_id: Project ID to search within
            top_k: Maximum number of results to return
            relevance_threshold: Minimum relevance score (0-1)

        Returns:
            List of DocumentChunk objects ranked by relevance
        """
        try:
            if not self.vector_db:
                logger.warning("Vector DB not available for search")
                return []

            # Perform semantic search
            results = self.vector_db.search(query, project_id, top_k)

            if not results:
                logger.debug(f"No results found for query: {query}")
                return []

            # Convert results to DocumentChunk objects
            chunks = []
            for result in results:
                if isinstance(result, dict):
                    similarity = result.get("similarity", 0)
                    if similarity >= relevance_threshold:
                        chunk = DocumentChunk(
                            chunk_id=result.get("chunk_id", ""),
                            document_id=result.get("document_id", ""),
                            content=result.get("content", ""),
                            section=result.get("section", ""),
                            position=result.get("position", 0),
                            page_number=result.get("page_number"),
                            metadata={
                                "similarity": similarity,
                                "source": result.get("source", ""),
                                "title": result.get("title", "")
                            }
                        )
                        chunks.append(chunk)

            logger.debug(f"Found {len(chunks)} relevant documents for query")
            return chunks

        except Exception as e:
            logger.error(f"Error searching documents: {e}")
            return []

    def get_document_chunks(
        self,
        document_id: str,
        chunk_size: int = 500,
        overlap: int = 100
    ) -> List[DocumentChunk]:
        """
        Split document into overlapping chunks for optimal processing.

        Args:
            document_id: ID of document to chunk
            chunk_size: Target size of each chunk in characters
            overlap: Number of characters to overlap between chunks

        Returns:
            List of DocumentChunk objects
        """
        try:
            if not self.document_repo:
                logger.warning("Document repository not available")
                return []

            # Get document from repository
            document = self.document_repo.get_document(document_id)
            if not document:
                logger.warning(f"Document {document_id} not found")
                return []

            content = document.get("content", "")
            if not content:
                return []

            # Split content into chunks
            chunks = []
            chunk_count = 0
            start_pos = 0

            while start_pos < len(content):
                # Calculate chunk end, respecting word boundaries
                end_pos = min(start_pos + chunk_size, len(content))

                # Try to end at a sentence boundary if possible
                if end_pos < len(content):
                    # Look backwards for a sentence ending
                    last_period = content.rfind(".", start_pos, end_pos)
                    if last_period > start_pos + chunk_size // 2:
                        end_pos = last_period + 1

                # Extract chunk
                chunk_content = content[start_pos:end_pos].strip()
                if chunk_content:
                    chunk = DocumentChunk(
                        chunk_id=f"{document_id}_chunk_{chunk_count}",
                        document_id=document_id,
                        content=chunk_content,
                        section=document.get("section", ""),
                        position=chunk_count,
                        page_number=document.get("page_number"),
                        metadata={
                            "chunk_size": len(chunk_content),
                            "start_pos": start_pos,
                            "title": document.get("title", "")
                        }
                    )
                    chunks.append(chunk)
                    chunk_count += 1

                # Move to next chunk with overlap
                start_pos = end_pos - overlap if end_pos < len(content) else len(content)
                if start_pos < end_pos - overlap:
                    start_pos = end_pos - overlap

            logger.debug(f"Created {len(chunks)} chunks for document {document_id}")
            return chunks

        except Exception as e:
            logger.error(f"Error creating document chunks: {e}")
            return []

    # ========================================================================
    # Document Understanding
    # ========================================================================

    def analyze_document_relationships(
        self,
        documents: List[Dict[str, Any]],
        project_id: str
    ) -> DocumentRelationshipGraph:
        """
        Analyze relationships between documents.

        Identifies cross-references, conflicts, dependencies, and complementary
        relationships between documents.

        Args:
            documents: List of documents to analyze
            project_id: Project ID for context

        Returns:
            DocumentRelationshipGraph with all identified relationships
        """
        try:
            # Check cache first
            cache_key = f"{project_id}_relationships"
            if cache_key in self._relationship_cache:
                return self._relationship_cache[cache_key]

            graph = DocumentRelationshipGraph()

            if not documents or len(documents) < 2:
                logger.debug("Insufficient documents for relationship analysis")
                return graph

            # Build document list
            graph.documents = [
                {
                    "id": doc.get("document_id", ""),
                    "title": doc.get("title", ""),
                    "source": doc.get("source", ""),
                    "type": doc.get("document_type", "")
                }
                for doc in documents
            ]

            # Analyze pairwise relationships
            for i, doc1 in enumerate(documents):
                for doc2 in documents[i+1:]:
                    relationships = self._detect_relationships(doc1, doc2)
                    graph.edges.extend(relationships)

            # Detect conflicts
            graph.conflicts = self._detect_conflicts(documents)

            # Identify document clusters
            graph.clusters = self._identify_document_clusters(documents, graph.edges)

            # Cache the graph
            self._relationship_cache[cache_key] = graph

            logger.debug(f"Analyzed {len(documents)} documents: "
                        f"{len(graph.edges)} relationships, "
                        f"{len(graph.conflicts)} conflicts, "
                        f"{len(graph.clusters)} clusters")

            return graph

        except Exception as e:
            logger.error(f"Error analyzing document relationships: {e}")
            return DocumentRelationshipGraph()

    def _detect_relationships(
        self,
        doc1: Dict[str, Any],
        doc2: Dict[str, Any]
    ) -> List[DocumentRelationship]:
        """
        Detect relationships between two documents.

        Args:
            doc1: First document
            doc2: Second document

        Returns:
            List of DocumentRelationship objects
        """
        relationships = []

        try:
            content1 = doc1.get("content", "").lower()
            content2 = doc2.get("content", "").lower()
            title1 = doc1.get("title", "").lower()
            title2 = doc2.get("title", "").lower()

            doc1_id = doc1.get("document_id", "")
            doc2_id = doc2.get("document_id", "")

            # Check for cross-references (mentions of each other)
            if title1 in content2 or title2 in content1:
                strength = 0.8 if title1 in content2 and title2 in content1 else 0.6
                relationships.append(DocumentRelationship(
                    source_id=doc1_id,
                    target_id=doc2_id,
                    relationship_type=RelationshipType.CROSS_REFERENCE,
                    strength=strength,
                    description="Documents reference each other"
                ))

            # Check for dependencies (one builds on the other)
            if self._suggests_dependency(doc1, doc2):
                relationships.append(DocumentRelationship(
                    source_id=doc1_id,
                    target_id=doc2_id,
                    relationship_type=RelationshipType.DEPENDS_ON,
                    strength=0.7,
                    description="Document 1 depends on Document 2"
                ))

        except Exception as e:
            logger.debug(f"Error detecting relationships: {e}")

        return relationships

    def _suggests_dependency(self, doc1: Dict[str, Any], doc2: Dict[str, Any]) -> bool:
        """
        Check if doc1 depends on doc2 based on content.

        Args:
            doc1: Document that might be dependent
            doc2: Document that might be a dependency

        Returns:
            True if dependency is suggested
        """
        content1 = doc1.get("content", "").lower()
        title2 = doc2.get("title", "").lower()
        doc_type2 = doc2.get("document_type", "").lower()

        # Check for dependency indicators
        dependency_phrases = [
            "based on", "depends on", "requires", "builds on",
            "following", "after", "prerequisite", "implements"
        ]

        for phrase in dependency_phrases:
            if phrase in content1 and title2 in content1:
                return True

        return False

    def _detect_conflicts(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Detect conflicting information between documents.

        Args:
            documents: List of documents to check

        Returns:
            List of detected conflicts
        """
        conflicts = []

        try:
            # Check for contradictory statements
            # This is a simplified implementation - can be enhanced with NLP
            for i, doc1 in enumerate(documents):
                for doc2 in documents[i+1:]:
                    # Look for potential conflicts
                    # (e.g., different constraints, incompatible architectures)
                    content1 = doc1.get("content", "").lower()
                    content2 = doc2.get("content", "").lower()

                    # Simple heuristic: check for contradictory keywords
                    contradictions = [
                        ("required", "not required"),
                        ("must", "must not"),
                        ("always", "never")
                    ]

                    for word1, word2 in contradictions:
                        if word1 in content1 and word2 in content2:
                            conflicts.append({
                                "doc1_id": doc1.get("document_id", ""),
                                "doc2_id": doc2.get("document_id", ""),
                                "type": "contradictory_statements",
                                "severity": "medium"
                            })
                            break

        except Exception as e:
            logger.debug(f"Error detecting conflicts: {e}")

        return conflicts

    def _identify_document_clusters(
        self,
        documents: List[Dict[str, Any]],
        edges: List[DocumentRelationship]
    ) -> List[List[str]]:
        """
        Identify clusters of related documents.

        Args:
            documents: List of documents
            edges: List of relationships

        Returns:
            List of document ID clusters
        """
        clusters = []

        try:
            # Build adjacency from edges
            adjacency: Dict[str, List[str]] = {}
            for doc in documents:
                doc_id = doc.get("document_id", "")
                adjacency[doc_id] = []

            for edge in edges:
                if edge.relationship_type in [
                    RelationshipType.CROSS_REFERENCE,
                    RelationshipType.COMPLEMENTS
                ]:
                    adjacency[edge.source_id].append(edge.target_id)
                    adjacency[edge.target_id].append(edge.source_id)

            # Simple clustering: connected components
            visited = set()
            for doc in documents:
                doc_id = doc.get("document_id", "")
                if doc_id not in visited:
                    cluster = self._dfs_cluster(doc_id, adjacency, visited)
                    if cluster:
                        clusters.append(cluster)

        except Exception as e:
            logger.debug(f"Error identifying clusters: {e}")

        return clusters

    def _dfs_cluster(
        self,
        node: str,
        adjacency: Dict[str, List[str]],
        visited: set
    ) -> List[str]:
        """
        Depth-first search to find connected component (cluster).

        Args:
            node: Starting node
            adjacency: Adjacency list
            visited: Set of visited nodes

        Returns:
            List of nodes in the cluster
        """
        cluster = []
        stack = [node]

        while stack:
            current = stack.pop()
            if current not in visited:
                visited.add(current)
                cluster.append(current)
                for neighbor in adjacency.get(current, []):
                    if neighbor not in visited:
                        stack.append(neighbor)

        return cluster

    # ========================================================================
    # Gap Identification
    # ========================================================================

    def identify_gaps(
        self,
        documents: List[Dict[str, Any]],
        project_specs: Dict[str, Any]
    ) -> List[SpecificationGap]:
        """
        Identify specification gaps not covered by documents.

        Compares project specifications with document content to find:
        - Missing topics
        - Underspecified areas
        - Unclear sections
        - Conflicting information

        Args:
            documents: List of documents to analyze
            project_specs: Project specifications dictionary

        Returns:
            List of SpecificationGap objects
        """
        try:
            gaps = []

            if not documents or not project_specs:
                logger.debug("Insufficient data for gap identification")
                return gaps

            # Combine all document content
            all_content = " ".join([
                doc.get("content", "") for doc in documents
            ]).lower()

            # Check each specification category
            spec_categories = [
                ("requirements", ["security", "performance", "scalability"]),
                ("constraints", ["technical", "business", "timeline"]),
                ("goals", ["functional", "non-functional"]),
                ("architecture", ["design", "components", "integration"])
            ]

            gap_id_counter = 0
            for category, topics in spec_categories:
                spec_items = project_specs.get(category, [])
                if isinstance(spec_items, list):
                    for item in spec_items:
                        item_text = str(item).lower()

                        # Check if item is mentioned in documents
                        if item_text not in all_content:
                            gap = SpecificationGap(
                                gap_id=f"gap_{gap_id_counter}",
                                category=category,
                                topic=item_text[:50],  # First 50 chars as topic
                                severity=self._assess_gap_severity(category, item),
                                priority_score=self._calculate_gap_priority(category),
                                mentioned_documents=[],
                                impact_on_specs=[],
                                suggested_question=self._generate_gap_question(category, item)
                            )
                            gaps.append(gap)
                            gap_id_counter += 1

            logger.debug(f"Identified {len(gaps)} specification gaps")
            return gaps

        except Exception as e:
            logger.error(f"Error identifying gaps: {e}")
            return []

    def _assess_gap_severity(self, category: str, item: Any) -> str:
        """
        Assess the severity of a specification gap.

        Args:
            category: Category of the specification
            item: The specification item

        Returns:
            Severity level: critical, high, medium, low
        """
        # Critical categories
        if category == "requirements":
            return "high"
        elif category == "constraints":
            return "medium"
        else:
            return "low"

    def _calculate_gap_priority(self, category: str) -> float:
        """
        Calculate priority score for a gap (0-1).

        Args:
            category: Category of the specification

        Returns:
            Priority score between 0 and 1
        """
        priority_map = {
            "requirements": 0.9,
            "constraints": 0.7,
            "goals": 0.5,
            "architecture": 0.6
        }
        return priority_map.get(category, 0.5)

    def _generate_gap_question(self, category: str, item: Any) -> str:
        """
        Generate a suggested question to address a gap.

        Args:
            category: Category of the specification
            item: The specification item

        Returns:
            Suggested question text
        """
        item_text = str(item)[:50]

        question_templates = {
            "requirements": f"What are your detailed requirements for {item_text}?",
            "constraints": f"What are the specific constraints related to {item_text}?",
            "goals": f"How do you plan to achieve your goal of {item_text}?",
            "architecture": f"How is {item_text} architected in your system?"
        }

        return question_templates.get(
            category,
            f"Can you provide more details about {item_text}?"
        )

    # ========================================================================
    # Relevance Scoring
    # ========================================================================

    def calculate_relevance_score(
        self,
        query: str,
        document: Dict[str, Any],
        context: Dict[str, Any]
    ) -> float:
        """
        Calculate relevance score (0-1) with context weighting.

        Considers:
        - Semantic similarity
        - Keyword match
        - Phase relevance
        - User role match
        - Document quality

        Args:
            query: Search query
            document: Document to score
            context: Context information (phase, user_role, etc.)

        Returns:
            Relevance score between 0 and 1
        """
        try:
            score = 0.0
            weights = {
                "semantic": 0.3,
                "keyword": 0.2,
                "phase": 0.2,
                "quality": 0.15,
                "role": 0.15
            }

            # Semantic similarity
            semantic_score = self._calculate_semantic_similarity(query, document)
            score += semantic_score * weights["semantic"]

            # Keyword matching
            keyword_score = self._calculate_keyword_match(query, document)
            score += keyword_score * weights["keyword"]

            # Phase relevance
            phase = context.get("phase", "discovery")
            phase_score = self._calculate_phase_relevance(document, phase)
            score += phase_score * weights["phase"]

            # Document quality
            quality = self.score_document_quality(document)
            quality_score = quality.overall_score / 100
            score += quality_score * weights["quality"]

            # User role matching
            user_role = context.get("user_role", "contributor")
            role_score = self._calculate_role_relevance(document, user_role)
            score += role_score * weights["role"]

            return min(1.0, max(0.0, score))

        except Exception as e:
            logger.error(f"Error calculating relevance score: {e}")
            return 0.0

    def _calculate_semantic_similarity(self, query: str, document: Dict[str, Any]) -> float:
        """
        Calculate semantic similarity between query and document.

        Args:
            query: Query string
            document: Document dictionary

        Returns:
            Similarity score 0-1
        """
        # This would use vector DB embeddings in full implementation
        # For now, use simple lexical similarity
        doc_content = document.get("content", "").lower()
        query_lower = query.lower()

        # Count matching words
        query_words = set(query_lower.split())
        doc_words = set(doc_content.split())

        if not query_words or not doc_words:
            return 0.0

        intersection = len(query_words & doc_words)
        union = len(query_words | doc_words)

        return intersection / union if union > 0 else 0.0

    def _calculate_keyword_match(self, query: str, document: Dict[str, Any]) -> float:
        """
        Calculate keyword matching score.

        Args:
            query: Query string
            document: Document dictionary

        Returns:
            Match score 0-1
        """
        content = document.get("content", "").lower()
        query_lower = query.lower()

        # Exact phrase match
        if query_lower in content:
            return 1.0

        # Partial phrase match
        query_words = query_lower.split()
        matches = sum(1 for word in query_words if word in content)

        return matches / len(query_words) if query_words else 0.0

    def _calculate_phase_relevance(self, document: Dict[str, Any], phase: str) -> float:
        """
        Calculate phase relevance score.

        Args:
            document: Document dictionary
            phase: Current phase

        Returns:
            Relevance score 0-1
        """
        # Phase-specific relevance
        phase_keywords = {
            "discovery": ["goals", "objectives", "stakeholders", "requirements"],
            "analysis": ["detailed", "breakdown", "constraints", "integration"],
            "design": ["architecture", "components", "design", "patterns"],
            "implementation": ["code", "implementation", "technical", "details"]
        }

        keywords = phase_keywords.get(phase, [])
        content = document.get("content", "").lower()

        if not keywords:
            return 0.5

        matches = sum(1 for kw in keywords if kw in content)
        return matches / len(keywords)

    def _calculate_role_relevance(self, document: Dict[str, Any], user_role: str) -> float:
        """
        Calculate role-based relevance score.

        Args:
            document: Document dictionary
            user_role: User's role

        Returns:
            Relevance score 0-1
        """
        # All roles can access all documents with equal relevance
        # Can be customized for role-specific filtering
        return 1.0

    def score_document_quality(self, document: Dict[str, Any]) -> QualityScore:
        """
        Score document quality (0-100).

        Factors:
        - Completeness: How complete is the documentation
        - Clarity: How clear and well-written
        - Consistency: Internal consistency
        - Relevance: Relevance to project
        - Recency: How recent/up-to-date

        Args:
            document: Document to score

        Returns:
            QualityScore object with detailed assessment
        """
        try:
            # Check cache first
            doc_id = document.get("document_id", "")
            if doc_id in self._quality_cache:
                return self._quality_cache[doc_id]

            # Calculate individual scores
            completeness = self._assess_completeness(document)
            clarity = self._assess_clarity(document)
            consistency = self._assess_consistency(document)
            relevance = self._assess_relevance(document)
            recency = self._assess_recency(document)

            # Calculate overall score
            overall = (completeness + clarity + consistency + relevance + recency) / 5 * 100

            score = QualityScore(
                overall_score=overall,
                completeness=completeness,
                clarity=clarity,
                consistency=consistency,
                relevance=relevance,
                recency=recency,
                factors={
                    "completeness": f"{completeness:.2f}",
                    "clarity": f"{clarity:.2f}",
                    "consistency": f"{consistency:.2f}",
                    "relevance": f"{relevance:.2f}",
                    "recency": f"{recency:.2f}"
                }
            )

            # Cache the score
            if doc_id:
                self._quality_cache[doc_id] = score

            return score

        except Exception as e:
            logger.error(f"Error scoring document quality: {e}")
            return QualityScore(
                overall_score=50.0,
                completeness=0.5,
                clarity=0.5,
                consistency=0.5,
                relevance=0.5,
                recency=0.5
            )

    def _assess_completeness(self, document: Dict[str, Any]) -> float:
        """
        Assess document completeness (0-1).

        Args:
            document: Document to assess

        Returns:
            Completeness score 0-1
        """
        content = document.get("content", "")
        length = len(content)

        # Simple heuristic: longer documents are typically more complete
        # Adjust thresholds based on document type
        if length < 100:
            return 0.2
        elif length < 500:
            return 0.4
        elif length < 2000:
            return 0.7
        else:
            return 1.0

    def _assess_clarity(self, document: Dict[str, Any]) -> float:
        """
        Assess document clarity (0-1).

        Args:
            document: Document to assess

        Returns:
            Clarity score 0-1
        """
        # Check for structure indicators (headings, sections)
        content = document.get("content", "")

        # Count structural elements
        headings = len(re.findall(r'^#+\s', content, re.MULTILINE))
        paragraphs = len(content.split('\n\n'))
        lists = len(re.findall(r'^[-*]\s', content, re.MULTILINE))

        # More structure generally means better clarity
        structure_score = min(1.0, (headings + lists + paragraphs) / 50)

        # Check for excessive jargon/complexity
        avg_word_length = sum(len(w) for w in content.split()) / (len(content.split()) + 1)
        complexity_penalty = min(0.3, (avg_word_length - 5) / 10)

        return max(0.0, structure_score - complexity_penalty)

    def _assess_consistency(self, document: Dict[str, Any]) -> float:
        """
        Assess document consistency (0-1).

        Args:
            document: Document to assess

        Returns:
            Consistency score 0-1
        """
        # Check for contradictory statements within the document
        content = document.get("content", "").lower()

        # Look for contradictory phrases
        contradictions = [
            ("must", "must not"),
            ("required", "not required"),
            ("always", "never")
        ]

        contradiction_count = 0
        for phrase1, phrase2 in contradictions:
            if phrase1 in content and phrase2 in content:
                contradiction_count += 1

        # Penalty for contradictions
        return max(0.0, 1.0 - (contradiction_count * 0.2))

    def _assess_relevance(self, document: Dict[str, Any]) -> float:
        """
        Assess document relevance (0-1).

        Args:
            document: Document to assess

        Returns:
            Relevance score 0-1
        """
        # Assume all documents in KB are relevant
        # This could be enhanced with project-specific assessment
        return 0.8

    def _assess_recency(self, document: Dict[str, Any]) -> float:
        """
        Assess document recency (0-1).

        Args:
            document: Document to assess

        Returns:
            Recency score 0-1
        """
        # Check upload date
        # Default to 0.8 if we can't determine date
        updated_at = document.get("updated_at")
        if not updated_at:
            return 0.8

        # Would calculate based on time since update
        # For now, assume recent documents are good
        return 0.9

    # ========================================================================
    # Cache Management
    # ========================================================================

    def clear_cache(self, project_id: Optional[str] = None) -> None:
        """
        Clear service caches.

        Args:
            project_id: Optional project ID to clear specific caches
        """
        try:
            if project_id:
                # Clear specific project caches
                keys_to_delete = [
                    k for k in self._gap_cache.keys()
                    if k.startswith(project_id)
                ]
                for key in keys_to_delete:
                    del self._gap_cache[key]

                keys_to_delete = [
                    k for k in self._relationship_cache.keys()
                    if k.startswith(project_id)
                ]
                for key in keys_to_delete:
                    del self._relationship_cache[key]
            else:
                # Clear all caches
                self._gap_cache.clear()
                self._relationship_cache.clear()
                self._quality_cache.clear()

            logger.debug(f"Cleared knowledge service cache for {project_id or 'all projects'}")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")


# ============================================================================
# Vector Database Service - Enhanced DB Operations
# ============================================================================

class VectorDBService:
    """
    Optimized vector database operations for semantic search.

    Provides:
    - Hybrid search (semantic + keyword)
    - Query optimization
    - Relevance filtering
    - Chunk overlap handling
    - Similarity threshold tuning
    """

    def __init__(self, vector_db: Any = None):
        """
        Initialize Vector DB Service.

        Args:
            vector_db: Vector database instance (ChromaDB)
        """
        self.vector_db = vector_db
        self._search_cache: Dict[str, List[Dict[str, Any]]] = {}
        self._embedding_cache: Dict[str, List[float]] = {}

        # Tuning parameters (can be adjusted for optimization)
        self.semantic_weight = 0.7
        self.keyword_weight = 0.3
        self.default_similarity_threshold = 0.6
        self.max_cache_size = 1000

        logger.info("Vector DB Service initialized")

    # ========================================================================
    # Hybrid Search
    # ========================================================================

    def hybrid_search(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        semantic_weight: float = 0.7,
        keyword_weight: float = 0.3,
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Hybrid search combining semantic and keyword matching.

        Performs:
        1. Semantic search using vector similarity
        2. Keyword-based search (BM25-style)
        3. Combined ranking with weighted scores

        Args:
            query: Search query string
            documents: List of documents to search
            semantic_weight: Weight for semantic similarity (0-1)
            keyword_weight: Weight for keyword matching (0-1)
            top_k: Maximum number of results to return

        Returns:
            List of documents ranked by combined score
        """
        try:
            if not documents:
                logger.debug("No documents to search")
                return []

            # Check cache first
            cache_key = self._make_cache_key(query, len(documents))
            if cache_key in self._search_cache:
                logger.debug(f"Cache hit for query: {query}")
                return self._search_cache[cache_key][:top_k]

            # Perform semantic search
            semantic_results = self._semantic_search(query, documents)

            # Perform keyword search
            keyword_results = self._keyword_search(query, documents)

            # Combine and rank results
            combined_results = self._combine_search_results(
                query,
                semantic_results,
                keyword_results,
                semantic_weight,
                keyword_weight
            )

            # Sort by combined score
            sorted_results = sorted(
                combined_results,
                key=lambda x: x.get("combined_score", 0),
                reverse=True
            )

            # Cache results
            if len(self._search_cache) < self.max_cache_size:
                self._search_cache[cache_key] = sorted_results

            logger.debug(
                f"Hybrid search found {len(sorted_results)} results "
                f"(semantic: {len(semantic_results)}, keyword: {len(keyword_results)})"
            )

            return sorted_results[:top_k]

        except Exception as e:
            logger.error(f"Error in hybrid search: {e}")
            return []

    def _semantic_search(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Perform semantic search using vector similarity.

        Args:
            query: Search query
            documents: Documents to search
            top_k: Maximum results to return

        Returns:
            List of results with similarity scores
        """
        try:
            if not self.vector_db:
                logger.debug("Vector DB not available for semantic search")
                return []

            # Get query embedding
            query_embedding = self._get_embedding(query)
            if not query_embedding:
                return []

            # Score documents by vector similarity
            scored_docs = []
            for doc in documents:
                doc_embedding = self._get_embedding(doc.get("content", ""))
                if doc_embedding:
                    similarity = self._cosine_similarity(query_embedding, doc_embedding)
                    scored_docs.append({
                        **doc,
                        "semantic_score": similarity,
                        "search_method": "semantic"
                    })

            # Sort by similarity and return top_k
            scored_docs.sort(key=lambda x: x["semantic_score"], reverse=True)
            return scored_docs[:top_k]

        except Exception as e:
            logger.error(f"Error in semantic search: {e}")
            return []

    def _keyword_search(
        self,
        query: str,
        documents: List[Dict[str, Any]],
        top_k: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Perform keyword-based search using BM25-style scoring.

        Args:
            query: Search query
            documents: Documents to search
            top_k: Maximum results to return

        Returns:
            List of results with keyword scores
        """
        try:
            query_terms = set(query.lower().split())
            if not query_terms:
                return []

            scored_docs = []

            for doc in documents:
                content = doc.get("content", "").lower()
                title = doc.get("title", "").lower()

                # Score based on term frequency and position
                score = 0.0

                # Title matches are worth more
                for term in query_terms:
                    if term in title:
                        score += 2.0
                    if term in content:
                        score += 1.0

                # Exact phrase match
                if query.lower() in content:
                    score += 5.0

                if score > 0:
                    scored_docs.append({
                        **doc,
                        "keyword_score": score,
                        "search_method": "keyword"
                    })

            # Sort by keyword score
            scored_docs.sort(key=lambda x: x["keyword_score"], reverse=True)
            return scored_docs[:top_k]

        except Exception as e:
            logger.error(f"Error in keyword search: {e}")
            return []

    def _combine_search_results(
        self,
        query: str,
        semantic_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        semantic_weight: float,
        keyword_weight: float
    ) -> List[Dict[str, Any]]:
        """
        Combine semantic and keyword search results.

        Args:
            query: Original query
            semantic_results: Results from semantic search
            keyword_results: Results from keyword search
            semantic_weight: Weight for semantic results
            keyword_weight: Weight for keyword results

        Returns:
            List of combined results with unified scoring
        """
        # Normalize weights
        total_weight = semantic_weight + keyword_weight
        semantic_weight = semantic_weight / total_weight
        keyword_weight = keyword_weight / total_weight

        # Track documents and their scores
        combined: Dict[str, Dict[str, Any]] = {}

        # Add semantic results
        for doc in semantic_results:
            doc_id = doc.get("document_id", id(doc))
            combined[doc_id] = {
                **doc,
                "semantic_score": doc.get("semantic_score", 0),
                "keyword_score": 0.0
            }

        # Add/update keyword results
        for doc in keyword_results:
            doc_id = doc.get("document_id", id(doc))
            if doc_id in combined:
                combined[doc_id]["keyword_score"] = doc.get("keyword_score", 0)
            else:
                combined[doc_id] = {
                    **doc,
                    "semantic_score": 0.0,
                    "keyword_score": doc.get("keyword_score", 0)
                }

        # Calculate combined scores (normalized)
        max_semantic = max(
            (doc.get("semantic_score", 0) for doc in combined.values()),
            default=1.0
        )
        max_keyword = max(
            (doc.get("keyword_score", 0) for doc in combined.values()),
            default=1.0
        )

        for doc_id, doc in combined.items():
            semantic_norm = doc["semantic_score"] / max_semantic if max_semantic > 0 else 0
            keyword_norm = doc["keyword_score"] / max_keyword if max_keyword > 0 else 0

            combined_score = (
                semantic_norm * semantic_weight +
                keyword_norm * keyword_weight
            )

            doc["combined_score"] = combined_score

        return list(combined.values())

    # ========================================================================
    # Query Optimization
    # ========================================================================

    def get_optimal_chunks(
        self,
        query: str,
        project_id: str,
        phase: str,
        question_number: int,
        documents: List[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """
        Get KB chunks optimized for current context.

        Uses:
        - Phase-specific strategy (snippet vs full)
        - Relevance scoring
        - Coverage gaps
        - User role filtering

        Args:
            query: Query or topic
            project_id: Project ID
            phase: Current project phase
            question_number: Question number in phase
            documents: Optional list of documents to search

        Returns:
            List of optimized DocumentChunk objects
        """
        try:
            # Determine strategy based on phase
            strategy = self._determine_chunk_strategy(phase, question_number)

            # Get chunk count based on strategy
            chunk_count = 5 if strategy == "full" else 3

            # Search for relevant documents
            if documents:
                results = self.hybrid_search(query, documents, top_k=chunk_count)
            else:
                results = []

            # Convert to DocumentChunk objects
            chunks = []
            for result in results:
                chunk = DocumentChunk(
                    chunk_id=result.get("chunk_id", ""),
                    document_id=result.get("document_id", ""),
                    content=result.get("content", ""),
                    section=result.get("section", ""),
                    position=result.get("position", 0),
                    metadata={
                        "combined_score": result.get("combined_score", 0),
                        "phase": phase,
                        "strategy": strategy,
                        "relevance": result.get("semantic_score", 0)
                    }
                )
                chunks.append(chunk)

            logger.debug(
                f"Retrieved {len(chunks)} optimal chunks "
                f"for phase={phase}, question={question_number}, strategy={strategy}"
            )

            return chunks

        except Exception as e:
            logger.error(f"Error getting optimal chunks: {e}")
            return []

    def _determine_chunk_strategy(self, phase: str, question_number: int) -> str:
        """
        Determine optimal chunk strategy for context.

        Args:
            phase: Current phase
            question_number: Question number

        Returns:
            Strategy: "snippet" (3 chunks) or "full" (5 chunks)
        """
        if phase in ["design", "implementation"]:
            return "full"  # Always full for detailed phases
        elif question_number <= 4:
            return "snippet"  # Early questions get snippets
        else:
            return "full"  # Later questions get full context

    # ========================================================================
    # Relevance Filtering
    # ========================================================================

    def filter_by_relevance(
        self,
        results: List[Dict[str, Any]],
        threshold: float = 0.6,
        min_results: int = 1
    ) -> List[Dict[str, Any]]:
        """
        Filter search results by relevance threshold.

        Args:
            results: Search results with scores
            threshold: Minimum relevance score (0-1)
            min_results: Minimum results to return

        Returns:
            Filtered results meeting threshold
        """
        try:
            filtered = []

            for result in results:
                score = result.get("combined_score", result.get("semantic_score", 0))
                if score >= threshold:
                    filtered.append(result)

            # Ensure minimum results even if below threshold
            if len(filtered) < min_results and results:
                remaining = [r for r in results if r not in filtered]
                filtered.extend(remaining[:min_results - len(filtered)])

            logger.debug(
                f"Filtered {len(results)} results to {len(filtered)} "
                f"using threshold {threshold}"
            )

            return filtered

        except Exception as e:
            logger.error(f"Error filtering by relevance: {e}")
            return results

    # ========================================================================
    # Similarity Calculations
    # ========================================================================

    def _get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Get or generate embedding for text.

        Uses cache for performance. In production, would call embedding service.

        Args:
            text: Text to embed

        Returns:
            Embedding vector or None
        """
        try:
            if not text:
                return None

            # Check cache
            if text in self._embedding_cache:
                return self._embedding_cache[text]

            # In full implementation, would call actual embedding service
            # For now, return deterministic dummy embedding based on text
            embedding = self._generate_dummy_embedding(text)

            # Cache embedding
            if len(self._embedding_cache) < self.max_cache_size:
                self._embedding_cache[text] = embedding

            return embedding

        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            return None

    def _generate_dummy_embedding(self, text: str) -> List[float]:
        """
        Generate deterministic dummy embedding for testing.

        In production, would use actual embedding model.

        Args:
            text: Text to embed

        Returns:
            Embedding vector of length 384 (SBERT default)
        """
        # Use hash of text to generate deterministic but varied embeddings
        import hashlib
        hash_obj = hashlib.md5(text.encode())
        hash_bytes = hash_obj.digest()

        # Convert bytes to normalized vector
        embedding = [
            (byte - 128) / 128.0 for byte in hash_bytes
        ]

        # Extend to standard size (384 for SBERT)
        while len(embedding) < 384:
            embedding.extend(embedding[:min(len(hash_bytes), 384 - len(embedding))])

        return embedding[:384]

    def _cosine_similarity(
        self,
        vec1: List[float],
        vec2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two vectors.

        Args:
            vec1: First vector
            vec2: Second vector

        Returns:
            Cosine similarity score (0-1)
        """
        try:
            if not vec1 or not vec2:
                return 0.0

            # Ensure same length
            min_len = min(len(vec1), len(vec2))
            vec1 = vec1[:min_len]
            vec2 = vec2[:min_len]

            # Calculate dot product
            dot_product = sum(a * b for a, b in zip(vec1, vec2))

            # Calculate magnitudes
            mag1 = sum(a * a for a in vec1) ** 0.5
            mag2 = sum(b * b for b in vec2) ** 0.5

            if mag1 == 0 or mag2 == 0:
                return 0.0

            # Calculate cosine similarity
            similarity = dot_product / (mag1 * mag2)

            # Normalize to 0-1 range
            return max(0.0, min(1.0, (similarity + 1) / 2))

        except Exception as e:
            logger.error(f"Error calculating cosine similarity: {e}")
            return 0.0

    # ========================================================================
    # Chunk Overlap Handling
    # ========================================================================

    def handle_chunk_overlap(
        self,
        chunks: List[DocumentChunk],
        max_overlap: int = 100
    ) -> List[DocumentChunk]:
        """
        Handle overlapping chunks to avoid redundancy.

        When chunks overlap, combines overlapping sections intelligently.

        Args:
            chunks: List of chunks possibly with overlaps
            max_overlap: Maximum allowed character overlap

        Returns:
            Deduplicated/merged chunks
        """
        try:
            if not chunks:
                return []

            # Sort chunks by document and position
            sorted_chunks = sorted(
                chunks,
                key=lambda x: (x.document_id, x.position)
            )

            result = []
            for chunk in sorted_chunks:
                if not result:
                    result.append(chunk)
                else:
                    last = result[-1]

                    # Check if consecutive chunks from same document
                    if (chunk.document_id == last.document_id and
                        chunk.position == last.position + 1):

                        # Calculate overlap
                        overlap = self._calculate_overlap(last.content, chunk.content)

                        if overlap > max_overlap:
                            # Merge chunks
                            merged = self._merge_chunks(last, chunk)
                            result[-1] = merged
                        else:
                            result.append(chunk)
                    else:
                        result.append(chunk)

            logger.debug(
                f"Handled overlaps: {len(chunks)} chunks -> {len(result)} chunks"
            )

            return result

        except Exception as e:
            logger.error(f"Error handling chunk overlap: {e}")
            return chunks

    def _calculate_overlap(self, text1: str, text2: str) -> int:
        """
        Calculate character overlap between two texts.

        Args:
            text1: First text
            text2: Second text

        Returns:
            Number of overlapping characters
        """
        if not text1 or not text2:
            return 0

        # Check if end of text1 overlaps with start of text2
        max_overlap = min(len(text1), len(text2))

        for i in range(max_overlap, 0, -1):
            if text1[-i:] == text2[:i]:
                return i

        return 0

    def _merge_chunks(self, chunk1: DocumentChunk, chunk2: DocumentChunk) -> DocumentChunk:
        """
        Merge two overlapping chunks.

        Args:
            chunk1: First chunk
            chunk2: Second chunk

        Returns:
            Merged DocumentChunk
        """
        overlap = self._calculate_overlap(chunk1.content, chunk2.content)

        # Combine content, removing overlap
        merged_content = chunk1.content + chunk2.content[overlap:]

        # Merge metadata
        merged_metadata = {**chunk1.metadata, **chunk2.metadata}

        return DocumentChunk(
            chunk_id=f"{chunk1.chunk_id}_merged_{chunk2.chunk_id}",
            document_id=chunk1.document_id,
            content=merged_content,
            section=chunk1.section,
            position=chunk1.position,
            page_number=chunk1.page_number,
            metadata=merged_metadata
        )

    # ========================================================================
    # Tuning and Optimization
    # ========================================================================

    def set_weights(self, semantic_weight: float, keyword_weight: float) -> None:
        """
        Adjust search weights for tuning.

        Args:
            semantic_weight: Weight for semantic search (0-1)
            keyword_weight: Weight for keyword search (0-1)
        """
        total = semantic_weight + keyword_weight
        self.semantic_weight = semantic_weight / total
        self.keyword_weight = keyword_weight / total
        logger.info(
            f"Search weights updated: semantic={self.semantic_weight:.2f}, "
            f"keyword={self.keyword_weight:.2f}"
        )

    def set_similarity_threshold(self, threshold: float) -> None:
        """
        Adjust similarity threshold for filtering.

        Args:
            threshold: Minimum similarity score (0-1)
        """
        if 0 <= threshold <= 1:
            self.default_similarity_threshold = threshold
            logger.info(f"Similarity threshold set to {threshold}")
        else:
            logger.warning(f"Invalid threshold {threshold}, keeping current {self.default_similarity_threshold}")

    def clear_search_cache(self) -> None:
        """Clear search and embedding caches."""
        try:
            self._search_cache.clear()
            self._embedding_cache.clear()
            logger.info("Cleared Vector DB search caches")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

    # ========================================================================
    # Utility Methods
    # ========================================================================

    def _make_cache_key(self, query: str, doc_count: int) -> str:
        """
        Create cache key for search results.

        Args:
            query: Search query
            doc_count: Number of documents

        Returns:
            Cache key string
        """
        return f"search_{query}_{doc_count}"


# ============================================================================
# Document Understanding Service - Advanced Analysis
# ============================================================================

@dataclass
class Concept:
    """Represents a key concept extracted from document."""
    term: str
    type: str  # technical, business, requirement, constraint
    frequency: int
    context: List[str]  # sentences where it appears


@dataclass
class DocumentSummary:
    """Summary of a document with key information."""
    document_id: str
    title: str
    key_concepts: List[Concept]
    estimated_completeness: float  # 0-1
    main_topics: List[str]
    dependencies: List[str]
    summary_text: str


class DocumentUnderstandingService:
    """
    Advanced document understanding and analysis.

    Provides:
    - Concept extraction
    - Gap identification
    - Relationship analysis
    - Quality scoring
    - Completeness assessment
    """

    # Key concepts that documents should cover
    STANDARD_CONCEPTS = {
        "technical": [
            "architecture", "design", "components", "api", "database",
            "security", "performance", "scalability", "integration"
        ],
        "business": [
            "goals", "objectives", "requirements", "constraints",
            "timeline", "budget", "stakeholders", "success criteria"
        ],
        "requirement": [
            "functional", "non-functional", "performance", "security",
            "usability", "reliability", "compatibility"
        ],
        "constraint": [
            "technical", "budget", "timeline", "resource", "legal"
        ]
    }

    def __init__(self):
        """Initialize Document Understanding Service."""
        self._concept_cache: Dict[str, List[Concept]] = {}
        self._summary_cache: Dict[str, DocumentSummary] = {}
        logger.info("Document Understanding Service initialized")

    # ========================================================================
    # Concept Extraction
    # ========================================================================

    def extract_concepts(self, document: Dict[str, Any]) -> List[Concept]:
        """
        Extract key concepts from document.

        Returns:
        - Technical terms
        - Business concepts
        - Requirements
        - Constraints

        Args:
            document: Document to analyze

        Returns:
            List of Concept objects
        """
        try:
            doc_id = document.get("document_id", "")
            if doc_id in self._concept_cache:
                return self._concept_cache[doc_id]

            concepts = []
            content = document.get("content", "").lower()

            if not content:
                return concepts

            # Extract from each category
            for category, terms in self.STANDARD_CONCEPTS.items():
                for term in terms:
                    frequency = content.count(term)
                    if frequency > 0:
                        # Find context (sentences containing term)
                        context_sentences = self._extract_context_sentences(
                            content, term, max_sentences=2
                        )

                        concept = Concept(
                            term=term,
                            type=category,
                            frequency=frequency,
                            context=context_sentences
                        )
                        concepts.append(concept)

            # Sort by frequency (most important first)
            concepts.sort(key=lambda x: x.frequency, reverse=True)

            # Cache
            if doc_id:
                self._concept_cache[doc_id] = concepts

            logger.debug(
                f"Extracted {len(concepts)} concepts from document {doc_id}"
            )

            return concepts

        except Exception as e:
            logger.error(f"Error extracting concepts: {e}")
            return []

    def _extract_context_sentences(
        self,
        text: str,
        term: str,
        max_sentences: int = 2
    ) -> List[str]:
        """
        Extract sentences containing a term.

        Args:
            text: Text to search
            term: Term to find
            max_sentences: Maximum sentences to return

        Returns:
            List of sentences containing the term
        """
        try:
            # Split text into sentences
            sentences = re.split(r'[.!?]+', text)

            # Find sentences with term
            matching_sentences = []
            for sentence in sentences:
                if term in sentence.lower():
                    cleaned = sentence.strip()
                    if cleaned:
                        matching_sentences.append(cleaned[:100])  # First 100 chars

            return matching_sentences[:max_sentences]

        except Exception as e:
            logger.debug(f"Error extracting context: {e}")
            return []

    # ========================================================================
    # Relationship Analysis
    # ========================================================================

    def analyze_relationships(
        self,
        documents: List[Dict[str, Any]]
    ) -> DocumentRelationshipGraph:
        """
        Build relationship graph between documents.

        Returns:
        - Cross-references
        - Dependencies
        - Conflicts
        - Overlaps
        - Hierarchy

        Args:
            documents: Documents to analyze

        Returns:
            DocumentRelationshipGraph with all relationships
        """
        try:
            graph = DocumentRelationshipGraph()

            if not documents or len(documents) < 2:
                return graph

            # Build documents list
            graph.documents = [
                {
                    "id": doc.get("document_id", ""),
                    "title": doc.get("title", ""),
                    "type": doc.get("document_type", ""),
                    "concepts": len(self.extract_concepts(doc))
                }
                for doc in documents
            ]

            # Analyze pairwise relationships
            for i in range(len(documents)):
                for j in range(i + 1, len(documents)):
                    relationships = self._find_document_relationships(
                        documents[i], documents[j]
                    )
                    graph.edges.extend(relationships)

            # Detect conflicts
            graph.conflicts = self._find_conflicts(documents)

            # Identify clusters
            graph.clusters = self._identify_clusters(documents, graph.edges)

            logger.debug(
                f"Relationship analysis: {len(documents)} docs, "
                f"{len(graph.edges)} relationships, {len(graph.conflicts)} conflicts"
            )

            return graph

        except Exception as e:
            logger.error(f"Error analyzing relationships: {e}")
            return DocumentRelationshipGraph()

    def _find_document_relationships(
        self,
        doc1: Dict[str, Any],
        doc2: Dict[str, Any]
    ) -> List[DocumentRelationship]:
        """
        Find relationships between two documents.

        Args:
            doc1: First document
            doc2: Second document

        Returns:
            List of DocumentRelationship objects
        """
        relationships = []

        try:
            # Extract concepts from both
            concepts1 = {c.term for c in self.extract_concepts(doc1)}
            concepts2 = {c.term for c in self.extract_concepts(doc2)}

            # Find overlap
            overlap = len(concepts1 & concepts2)
            union = len(concepts1 | concepts2)

            if union > 0:
                similarity = overlap / union

                # Classify relationship
                if similarity > 0.6:
                    rel_type = RelationshipType.COMPLEMENTS
                elif "architecture" in concepts1 and "design" in concepts2:
                    rel_type = RelationshipType.DEPENDS_ON
                else:
                    rel_type = RelationshipType.CROSS_REFERENCE

                relationship = DocumentRelationship(
                    source_id=doc1.get("document_id", ""),
                    target_id=doc2.get("document_id", ""),
                    relationship_type=rel_type,
                    strength=similarity,
                    description=f"Shares {overlap} concepts"
                )
                relationships.append(relationship)

        except Exception as e:
            logger.debug(f"Error finding relationships: {e}")

        return relationships

    def _find_conflicts(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Find conflicting information between documents.

        Args:
            documents: Documents to check

        Returns:
            List of conflicts
        """
        conflicts = []

        try:
            for i in range(len(documents)):
                for j in range(i + 1, len(documents)):
                    # Check for contradictory statements
                    doc1_content = documents[i].get("content", "").lower()
                    doc2_content = documents[j].get("content", "").lower()

                    # Look for negation patterns
                    contradiction_patterns = [
                        ("must", "must not"),
                        ("required", "optional"),
                        ("always", "never"),
                        ("mandatory", "forbidden")
                    ]

                    for pattern1, pattern2 in contradiction_patterns:
                        if (pattern1 in doc1_content and pattern2 in doc2_content):
                            conflicts.append({
                                "doc1_id": documents[i].get("document_id", ""),
                                "doc2_id": documents[j].get("document_id", ""),
                                "pattern1": pattern1,
                                "pattern2": pattern2,
                                "severity": "high"
                            })

        except Exception as e:
            logger.debug(f"Error finding conflicts: {e}")

        return conflicts

    def _identify_clusters(
        self,
        documents: List[Dict[str, Any]],
        edges: List[DocumentRelationship]
    ) -> List[List[str]]:
        """
        Identify document clusters using concept similarity.

        Args:
            documents: Documents to cluster
            edges: Relationship edges

        Returns:
            List of document ID clusters
        """
        clusters = []

        try:
            # Build adjacency from edges with high strength
            adjacency: Dict[str, set] = {}
            for doc in documents:
                doc_id = doc.get("document_id", "")
                adjacency[doc_id] = set()

            for edge in edges:
                if edge.strength > 0.5:  # Only strong relationships
                    adjacency[edge.source_id].add(edge.target_id)
                    adjacency[edge.target_id].add(edge.source_id)

            # Find connected components
            visited: set = set()
            for doc in documents:
                doc_id = doc.get("document_id", "")
                if doc_id not in visited:
                    cluster = self._bfs_cluster(doc_id, adjacency, visited)
                    if cluster:
                        clusters.append(cluster)

        except Exception as e:
            logger.debug(f"Error identifying clusters: {e}")

        return clusters

    def _bfs_cluster(
        self,
        start: str,
        adjacency: Dict[str, set],
        visited: set
    ) -> List[str]:
        """
        Use BFS to find connected component (cluster).

        Args:
            start: Starting node ID
            adjacency: Adjacency structure
            visited: Set of visited nodes

        Returns:
            List of nodes in cluster
        """
        cluster = []
        queue = [start]
        visited.add(start)

        while queue:
            node = queue.pop(0)
            cluster.append(node)

            for neighbor in adjacency.get(node, set()):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)

        return cluster

    # ========================================================================
    # Document Summarization
    # ========================================================================

    def create_document_summary(
        self,
        document: Dict[str, Any]
    ) -> DocumentSummary:
        """
        Create comprehensive summary of document.

        Args:
            document: Document to summarize

        Returns:
            DocumentSummary object
        """
        try:
            doc_id = document.get("document_id", "")

            # Check cache
            if doc_id in self._summary_cache:
                return self._summary_cache[doc_id]

            # Extract concepts
            concepts = self.extract_concepts(document)
            top_concepts = concepts[:10]  # Top 10 most frequent

            # Determine main topics
            main_topics = list(set(c.type for c in top_concepts))

            # Extract dependencies (documents this depends on)
            dependencies = self._find_document_dependencies(document)

            # Create summary
            summary_text = self._generate_summary_text(document, top_concepts)

            # Estimate completeness
            completeness = self._estimate_completeness(concepts, document)

            summary = DocumentSummary(
                document_id=doc_id,
                title=document.get("title", "Untitled"),
                key_concepts=top_concepts,
                estimated_completeness=completeness,
                main_topics=main_topics,
                dependencies=dependencies,
                summary_text=summary_text
            )

            # Cache
            if doc_id:
                self._summary_cache[doc_id] = summary

            logger.debug(f"Created summary for document {doc_id}")

            return summary

        except Exception as e:
            logger.error(f"Error creating summary: {e}")
            return DocumentSummary(
                document_id=document.get("document_id", ""),
                title=document.get("title", "Error"),
                key_concepts=[],
                estimated_completeness=0.0,
                main_topics=[],
                dependencies=[],
                summary_text=""
            )

    def _find_document_dependencies(self, document: Dict[str, Any]) -> List[str]:
        """
        Find documents this document depends on.

        Args:
            document: Document to analyze

        Returns:
            List of dependency descriptions
        """
        dependencies = []

        try:
            content = document.get("content", "").lower()

            # Look for dependency indicators
            dependency_phrases = [
                "requires", "depends on", "based on", "implements",
                "extends", "builds on", "prerequisite"
            ]

            for phrase in dependency_phrases:
                if phrase in content:
                    # Extract what it depends on
                    pattern = f"{phrase}\\s+([\\w\\s]+)"
                    matches = re.findall(pattern, content)
                    dependencies.extend([m.strip()[:30] for m in matches])

        except Exception as e:
            logger.debug(f"Error finding dependencies: {e}")

        return dependencies[:5]  # Top 5 dependencies

    def _generate_summary_text(
        self,
        document: Dict[str, Any],
        concepts: List[Concept]
    ) -> str:
        """
        Generate summary text from document.

        Args:
            document: Document to summarize
            concepts: Extracted concepts

        Returns:
            Summary text
        """
        try:
            title = document.get("title", "Document")
            content = document.get("content", "")

            # Get first paragraph or first 150 chars
            paragraphs = content.split('\n\n')
            first_para = paragraphs[0] if paragraphs else content[:150]

            # Build summary
            concept_terms = ", ".join(c.term for c in concepts[:5])

            summary = (
                f"{title}\n\n"
                f"Key concepts: {concept_terms}\n\n"
                f"Overview: {first_para[:200]}..."
            )

            return summary

        except Exception as e:
            logger.debug(f"Error generating summary: {e}")
            return ""

    def _estimate_completeness(
        self,
        concepts: List[Concept],
        document: Dict[str, Any]
    ) -> float:
        """
        Estimate document completeness (0-1).

        Args:
            concepts: Extracted concepts
            document: Document

        Returns:
            Completeness score 0-1
        """
        try:
            content = document.get("content", "")
            content_length = len(content)

            # Factor 1: Content length
            if content_length < 200:
                length_score = 0.2
            elif content_length < 1000:
                length_score = 0.5
            elif content_length < 5000:
                length_score = 0.8
            else:
                length_score = 1.0

            # Factor 2: Concept coverage
            unique_concepts = len(set(c.term for c in concepts))
            concept_score = min(1.0, unique_concepts / 10)

            # Factor 3: Section markers
            section_markers = len(re.findall(r'^#+\s', content, re.MULTILINE))
            section_score = min(1.0, section_markers / 5)

            # Weighted average
            completeness = (
                length_score * 0.4 +
                concept_score * 0.35 +
                section_score * 0.25
            )

            return min(1.0, completeness)

        except Exception as e:
            logger.debug(f"Error estimating completeness: {e}")
            return 0.5

    # ========================================================================
    # Comprehensive Document Analysis
    # ========================================================================

    def analyze_document(
        self,
        document: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of a document.

        Returns detailed information about:
        - Concepts and terminology
        - Document quality
        - Completeness
        - Dependencies
        - Related topics

        Args:
            document: Document to analyze

        Returns:
            Analysis dictionary
        """
        try:
            concepts = self.extract_concepts(document)
            summary = self.create_document_summary(document)

            analysis = {
                "document_id": document.get("document_id", ""),
                "title": document.get("title", ""),
                "document_type": document.get("document_type", ""),
                "concepts": [
                    {
                        "term": c.term,
                        "type": c.type,
                        "frequency": c.frequency,
                        "context": c.context
                    }
                    for c in concepts[:15]  # Top 15 concepts
                ],
                "summary": summary.summary_text,
                "key_topics": summary.main_topics,
                "estimated_completeness": summary.estimated_completeness,
                "dependencies": summary.dependencies,
                "content_length": len(document.get("content", "")),
                "section_count": len(re.findall(r'^#+\s', document.get("content", ""), re.MULTILINE))
            }

            logger.debug(f"Completed comprehensive analysis of {document.get('document_id', '')}")

            return analysis

        except Exception as e:
            logger.error(f"Error performing comprehensive analysis: {e}")
            return {}

    # ========================================================================
    # Cache Management
    # ========================================================================

    def clear_cache(self) -> None:
        """Clear all analysis caches."""
        try:
            self._concept_cache.clear()
            self._summary_cache.clear()
            logger.info("Cleared Document Understanding Service caches")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")


# ============================================================================
# Context-Aware Relevance Service - Phase 5c Enhancement
# ============================================================================

class ContextAwareRelevanceService:
    """
    Advanced relevance scoring with full context awareness.

    Scores documents based on:
    - Phase (what information is needed at each stage)
    - User role (what they care about)
    - Project type (domain-specific priorities)
    - Question history (avoid repeats)
    - Specification gaps (prioritize high-value areas)
    """

    # Phase-specific relevance keywords
    PHASE_KEYWORDS = {
        "discovery": {
            "keywords": ["goals", "objectives", "stakeholders", "users", "problem", "pain points", "success", "metrics"],
            "weight": 1.0
        },
        "analysis": {
            "keywords": ["requirements", "constraints", "technical", "integration", "dependencies", "data", "workflow"],
            "weight": 1.0
        },
        "design": {
            "keywords": ["architecture", "design", "components", "patterns", "structure", "interfaces", "decisions"],
            "weight": 1.0
        },
        "implementation": {
            "keywords": ["code", "implementation", "technical", "details", "testing", "deployment", "configuration"],
            "weight": 1.0
        }
    }

    # Role-specific relevance weights
    ROLE_WEIGHTS = {
        "owner": {
            "high_level": 0.6,
            "technical": 0.7,
            "business": 0.8,
            "strategic": 0.9
        },
        "contributor": {
            "high_level": 0.5,
            "technical": 0.9,
            "business": 0.6,
            "strategic": 0.4
        },
        "viewer": {
            "high_level": 0.8,
            "technical": 0.5,
            "business": 0.7,
            "strategic": 0.3
        }
    }

    # Project type relevance keywords
    PROJECT_TYPE_KEYWORDS = {
        "web_application": ["frontend", "backend", "api", "database", "ui", "responsive"],
        "mobile_app": ["ios", "android", "native", "cross-platform", "performance", "battery"],
        "api_service": ["endpoints", "authentication", "rate limiting", "versioning", "documentation"],
        "data_platform": ["pipeline", "processing", "storage", "analytics", "reporting", "visualization"],
        "ml_system": ["model", "training", "inference", "data", "features", "evaluation"]
    }

    def __init__(self):
        """Initialize Context-Aware Relevance Service."""
        self._relevance_cache: Dict[str, float] = {}
        logger.info("Context-Aware Relevance Service initialized")

    # ========================================================================
    # Main Relevance Calculation
    # ========================================================================

    def calculate_contextual_relevance(
        self,
        document: Dict[str, Any],
        context: Dict[str, Any]
    ) -> float:
        """
        Calculate relevance with full context awareness.

        Context factors:
        - Phase (what info is needed)
        - User role (what they care about)
        - Project type (domain-specific)
        - Question history (avoid repeats)
        - Specification gaps (priority areas)

        Args:
            document: Document to score
            context: Full context with phase, user_role, project_type, gaps, etc.

        Returns:
            Relevance score 0-1
        """
        try:
            # Build cache key
            doc_id = document.get("document_id", "")
            context_key = self._make_context_key(context)
            cache_key = f"{doc_id}_{context_key}"

            # Check cache
            if cache_key in self._relevance_cache:
                return self._relevance_cache[cache_key]

            score = 0.0

            # Factor 1: Phase Relevance (weight: 0.25)
            phase = context.get("phase", "discovery")
            phase_score = self._score_phase_relevance(document, phase)
            score += phase_score * 0.25

            # Factor 2: User Role Relevance (weight: 0.15)
            user_role = context.get("user_role", "contributor")
            role_score = self._score_role_relevance(document, user_role)
            score += role_score * 0.15

            # Factor 3: Project Type Relevance (weight: 0.20)
            project_type = context.get("project_type", "general")
            type_score = self._score_project_type_relevance(document, project_type)
            score += type_score * 0.20

            # Factor 4: Gap Relevance (weight: 0.25)
            gaps = context.get("gaps", [])
            gap_score = self._score_gap_relevance(document, gaps)
            score += gap_score * 0.25

            # Factor 5: Question History (weight: 0.15)
            history = context.get("question_history", [])
            novelty_score = self._score_novelty(document, history)
            score += novelty_score * 0.15

            # Normalize to 0-1
            final_score = min(1.0, max(0.0, score))

            # Cache result
            if len(self._relevance_cache) < 1000:
                self._relevance_cache[cache_key] = final_score

            logger.debug(
                f"Contextual relevance for {doc_id}: {final_score:.2f} "
                f"(phase:{phase_score:.2f}, role:{role_score:.2f}, "
                f"type:{type_score:.2f}, gap:{gap_score:.2f}, novelty:{novelty_score:.2f})"
            )

            return final_score

        except Exception as e:
            logger.error(f"Error calculating contextual relevance: {e}")
            return 0.5  # Default to medium relevance on error

    # ========================================================================
    # Phase-Based Relevance
    # ========================================================================

    def _score_phase_relevance(self, document: Dict[str, Any], phase: str) -> float:
        """
        Score document relevance for current phase.

        Different phases need different information:
        - Discovery: Goals, objectives, stakeholders, problems
        - Analysis: Requirements, constraints, technical details
        - Design: Architecture, patterns, decisions
        - Implementation: Code, technical specifics, deployment

        Args:
            document: Document to score
            phase: Current project phase

        Returns:
            Relevance score 0-1
        """
        try:
            content = document.get("content", "").lower()

            # Get phase keywords
            phase_info = self.PHASE_KEYWORDS.get(phase, {})
            keywords = phase_info.get("keywords", [])

            if not keywords:
                return 0.5  # Default to medium

            # Count keyword matches
            matches = sum(1 for keyword in keywords if keyword in content)
            coverage = matches / len(keywords)

            # Boost for exact phase mentions
            if phase in content:
                coverage = min(1.0, coverage + 0.3)

            return coverage

        except Exception as e:
            logger.debug(f"Error scoring phase relevance: {e}")
            return 0.5

    # ========================================================================
    # Role-Based Relevance
    # ========================================================================

    def _score_role_relevance(self, document: Dict[str, Any], role: str) -> float:
        """
        Score document relevance for user's role.

        Different roles prioritize different content:
        - Owner: Balanced (high-level + technical + business + strategic)
        - Contributor: Technical focus (code, implementation details)
        - Viewer: High-level overview (summary, strategic direction)

        Args:
            document: Document to score
            role: User's role in project

        Returns:
            Relevance score 0-1
        """
        try:
            content = document.get("content", "").lower()
            doc_type = document.get("document_type", "general").lower()

            # Content type scoring
            type_keywords = {
                "high_level": ["overview", "summary", "architecture", "goals", "objectives"],
                "technical": ["code", "implementation", "technical", "details", "api"],
                "business": ["business", "requirements", "stakeholders", "roi", "value"],
                "strategic": ["strategy", "roadmap", "timeline", "priorities", "decisions"]
            }

            # Calculate scores for each content type
            type_scores = {}
            for content_type, keywords in type_keywords.items():
                matches = sum(1 for kw in keywords if kw in content)
                type_scores[content_type] = matches / max(len(keywords), 1)

            # Get role weights
            role_weights = self.ROLE_WEIGHTS.get(role, self.ROLE_WEIGHTS["contributor"])

            # Weighted sum based on role
            score = 0.0
            for content_type, weight in role_weights.items():
                score += type_scores.get(content_type, 0) * weight

            # Normalize
            total_weight = sum(role_weights.values())
            if total_weight > 0:
                score = score / total_weight

            return min(1.0, score)

        except Exception as e:
            logger.debug(f"Error scoring role relevance: {e}")
            return 0.5

    # ========================================================================
    # Project Type Relevance
    # ========================================================================

    def _score_project_type_relevance(
        self,
        document: Dict[str, Any],
        project_type: str
    ) -> float:
        """
        Score document relevance for project type.

        Different project types need different documentation:
        - Web apps: Frontend, backend, database, UI
        - Mobile: iOS, Android, performance, offline
        - APIs: Endpoints, authentication, versioning
        - Data platforms: Pipelines, processing, analytics
        - ML systems: Models, training, inference, features

        Args:
            document: Document to score
            project_type: Type of project

        Returns:
            Relevance score 0-1
        """
        try:
            content = document.get("content", "").lower()

            # Get keywords for project type
            keywords = self.PROJECT_TYPE_KEYWORDS.get(
                project_type,
                self.PROJECT_TYPE_KEYWORDS.get("web_application", [])
            )

            if not keywords:
                return 0.5

            # Count matches
            matches = sum(1 for keyword in keywords if keyword in content)
            score = matches / len(keywords) if keywords else 0.0

            return min(1.0, score)

        except Exception as e:
            logger.debug(f"Error scoring project type relevance: {e}")
            return 0.5

    # ========================================================================
    # Gap-Based Relevance
    # ========================================================================

    def _score_gap_relevance(
        self,
        document: Dict[str, Any],
        gaps: List[Dict[str, Any]]
    ) -> float:
        """
        Score how well document addresses specification gaps.

        High-value gaps (critical, high severity) get higher weight.

        Args:
            document: Document to score
            gaps: List of identified specification gaps

        Returns:
            Relevance score 0-1
        """
        try:
            if not gaps:
                return 0.5  # No gaps identified, neutral score

            content = document.get("content", "").lower()
            total_relevance = 0.0

            for gap in gaps:
                topic = gap.get("topic", "").lower()
                severity = gap.get("severity", "low")
                priority = gap.get("priority_score", 0.5)

                # Score for this gap
                if topic and topic in content:
                    # Severity weighting
                    severity_weight = {
                        "critical": 1.0,
                        "high": 0.8,
                        "medium": 0.6,
                        "low": 0.4
                    }.get(severity, 0.5)

                    # Combined score
                    gap_relevance = priority * severity_weight
                    total_relevance += gap_relevance

            # Average over all gaps (or max if only one high-value gap)
            if gaps:
                avg_score = total_relevance / len(gaps)
            else:
                avg_score = 0.0

            return min(1.0, avg_score)

        except Exception as e:
            logger.debug(f"Error scoring gap relevance: {e}")
            return 0.5

    # ========================================================================
    # Novelty Scoring (Avoid Repetition)
    # ========================================================================

    def _score_novelty(
        self,
        document: Dict[str, Any],
        question_history: List[Dict[str, Any]]
    ) -> float:
        """
        Score document novelty based on question history.

        Penalizes documents recently discussed to encourage variety.
        Prevents asking about same documents repeatedly.

        Args:
            document: Document to score
            question_history: List of recent questions asked

        Returns:
            Novelty score 0-1 (1 = completely new, 0 = just discussed)
        """
        try:
            if not question_history:
                return 1.0  # No history, fully novel

            doc_id = document.get("document_id", "")
            doc_title = document.get("title", "").lower()

            # Count how many recent questions reference this document
            mention_count = 0
            for question in question_history[-10:]:  # Last 10 questions
                question_text = question.get("question", "").lower()
                if doc_id in question_text or doc_title in question_text:
                    mention_count += 1

            # Novelty penalty: -0.1 per mention
            novelty = max(0.0, 1.0 - (mention_count * 0.1))

            return novelty

        except Exception as e:
            logger.debug(f"Error scoring novelty: {e}")
            return 1.0  # Default to fully novel on error

    # ========================================================================
    # Multi-Document Ranking
    # ========================================================================

    def rank_documents_contextually(
        self,
        documents: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Rank multiple documents by contextual relevance.

        Args:
            documents: Documents to rank
            context: Full context for relevance calculation

        Returns:
            Documents sorted by relevance (highest first)
        """
        try:
            # Score each document
            scored_docs = []
            for doc in documents:
                score = self.calculate_contextual_relevance(doc, context)
                scored_docs.append({
                    **doc,
                    "contextual_relevance": score
                })

            # Sort by relevance
            ranked = sorted(
                scored_docs,
                key=lambda d: d.get("contextual_relevance", 0),
                reverse=True
            )

            logger.debug(
                f"Ranked {len(documents)} documents. "
                f"Top: {ranked[0].get('title', 'unknown')} "
                f"({ranked[0].get('contextual_relevance', 0):.2f})"
            )

            return ranked

        except Exception as e:
            logger.error(f"Error ranking documents: {e}")
            return documents

    # ========================================================================
    # Performance Analysis
    # ========================================================================

    def analyze_relevance_performance(
        self,
        documents: List[Dict[str, Any]],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Analyze relevance scoring performance metrics.

        Useful for debugging and optimization.

        Args:
            documents: Documents analyzed
            context: Context used for scoring

        Returns:
            Performance metrics dictionary
        """
        try:
            scores = []
            phase_breakdown = {}

            for doc in documents:
                score = self.calculate_contextual_relevance(doc, context)
                scores.append(score)

            # Calculate statistics
            if scores:
                avg_score = sum(scores) / len(scores)
                max_score = max(scores)
                min_score = min(scores)
                std_dev = (sum((s - avg_score) ** 2 for s in scores) / len(scores)) ** 0.5
            else:
                avg_score = max_score = min_score = std_dev = 0

            metrics = {
                "documents_scored": len(documents),
                "average_relevance": avg_score,
                "max_relevance": max_score,
                "min_relevance": min_score,
                "std_deviation": std_dev,
                "phase": context.get("phase", "unknown"),
                "user_role": context.get("user_role", "unknown"),
                "cache_size": len(self._relevance_cache)
            }

            logger.debug(f"Relevance metrics: avg={avg_score:.2f}, max={max_score:.2f}, min={min_score:.2f}")

            return metrics

        except Exception as e:
            logger.error(f"Error analyzing relevance performance: {e}")
            return {}

    # ========================================================================
    # Cache Management
    # ========================================================================

    def clear_cache(self) -> None:
        """Clear all relevance caches."""
        try:
            self._relevance_cache.clear()
            logger.info("Cleared Context-Aware Relevance Service cache")
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")

    def _make_context_key(self, context: Dict[str, Any]) -> str:
        """Create cache key from context."""
        parts = [
            context.get("phase", "unknown"),
            context.get("user_role", "unknown"),
            context.get("project_type", "unknown"),
            str(len(context.get("gaps", []))),
            str(len(context.get("question_history", [])))
        ]
        return "_".join(parts)
