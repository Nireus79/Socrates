"""
Document context analyzer for determining optimal document loading strategies.

Analyzes conversation context to determine whether to load full document chunks,
medium-sized excerpts, or brief snippets when searching the knowledge base.
"""

from typing import List, Dict, Optional, Tuple
import re


class DocumentContextAnalyzer:
    """
    Analyzes conversation context to determine optimal document loading strategy.

    Strategies:
    - "full": Load complete chunks (500+ words) - used when deep understanding needed
    - "medium": Load medium excerpts (500 chars) - balanced approach
    - "snippet": Load brief snippets (200 chars) - current default behavior
    """

    # Keywords indicating user is discussing documents
    DOCUMENT_REFERENCE_KEYWORDS = {
        "document", "doc", "file", "pdf", "paper", "book", "article", "spec",
        "specification", "guide", "manual", "reference", "content", "text",
        "imported", "uploaded", "provided", "attached", "mentioned"
    }

    # Phases where detailed document analysis is typically needed
    DETAIL_REQUIRED_PHASES = {"analysis", "design", "evaluation", "refinement"}

    # Keywords indicating document-specific discussion
    SPECIFIC_DETAIL_INDICATORS = {
        "explain", "understand", "describe", "summarize", "how does", "what does",
        "define", "mention", "chapter", "section", "part", "page", "specific",
        "detail", "exactly", "precisely"
    }

    def __init__(self):
        """Initialize the document context analyzer."""
        pass

    def analyze_question_context(
        self,
        project_context: Optional[Dict],
        conversation_history: Optional[List[Dict]],
        question_count: int
    ) -> str:
        """
        Determine document loading strategy based on conversation context.

        Args:
            project_context: Current project context with phase, goals, etc.
            conversation_history: List of recent conversation exchanges
            question_count: Number of questions generated so far

        Returns:
            Strategy string: "full", "medium", or "snippet"
        """
        # Initialize with default strategy
        strategy = "snippet"

        # Signal 1: Early discovery phase - use full strategy
        if question_count < 5:
            strategy = "full"
            return strategy

        # Signal 2: Check if current phase requires detailed analysis
        if project_context:
            current_phase = project_context.get("current_phase", "").lower()
            if current_phase in self.DETAIL_REQUIRED_PHASES:
                strategy = "full"
                return strategy

            # Signal 3: Check if project goals reference document-specific concepts
            goals = project_context.get("goals", "").lower()
            if goals and self._has_document_keywords(goals):
                strategy = "medium"

        # Signal 4: Check recent conversation for document references
        if conversation_history:
            recent_messages = self._get_recent_messages(conversation_history, window=3)

            if self._contains_document_reference(recent_messages):
                strategy = "full"
                return strategy

            if self._contains_specific_detail_question(recent_messages):
                strategy = "full"
                return strategy

        return strategy

    def detect_document_references(self, text: str) -> List[str]:
        """
        Detect references to documents in user input.

        Args:
            text: User input text to analyze

        Returns:
            List of detected document references
        """
        text_lower = text.lower()
        references = []

        # Check for direct document references
        for keyword in self.DOCUMENT_REFERENCE_KEYWORDS:
            if keyword in text_lower:
                references.append(keyword)

        # Check for specific patterns
        patterns = [
            r"my\s+(document|doc|file|pdf|paper|book)",
            r"the\s+(document|doc|file|pdf|paper|book)\s+(?:i\s+)?(?:provided|uploaded|imported|mentioned)",
            r"(?:in|from)\s+(?:my\s+)?(document|doc|file|pdf|paper|book)",
            r"(document|doc|file|pdf|paper|book)\s+(?:says|describes|mentions|shows|contains)"
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text_lower)
            if matches:
                references.extend(matches)

        return list(set(references))  # Remove duplicates

    def calculate_relevance_score(
        self,
        query: str,
        document_chunk: str
    ) -> float:
        """
        Calculate semantic relevance score for a document chunk.

        This is a basic relevance scorer that looks for keyword overlap and
        semantic similarity indicators. More sophisticated scoring would use
        embedding-based similarity.

        Args:
            query: The search query
            document_chunk: The document chunk to score

        Returns:
            Relevance score between 0.0 and 1.0
        """
        if not query or not document_chunk:
            return 0.0

        query_lower = query.lower()
        chunk_lower = document_chunk.lower()

        # Normalize text (remove punctuation, extra whitespace)
        query_words = set(re.findall(r'\b\w+\b', query_lower))
        chunk_words = set(re.findall(r'\b\w+\b', chunk_lower))

        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'is', 'was', 'are'}
        query_words = query_words - stop_words
        chunk_words = chunk_words - stop_words

        if not query_words:
            return 0.0

        # Calculate Jaccard similarity (intersection over union)
        intersection = len(query_words & chunk_words)
        union = len(query_words | chunk_words)

        jaccard_sim = intersection / union if union > 0 else 0.0

        # Bonus if exact phrase is found
        phrase_bonus = 0.1 if re.search(r'\b' + re.escape(query_lower) + r'\b', chunk_lower) else 0.0

        # Bonus if chunk contains specific detail indicators
        has_details = any(indicator in chunk_lower for indicator in self.SPECIFIC_DETAIL_INDICATORS)
        detail_bonus = 0.1 if has_details else 0.0

        score = min(1.0, jaccard_sim + phrase_bonus + detail_bonus)
        return score

    # Private helper methods

    def _has_document_keywords(self, text: str) -> bool:
        """Check if text contains document-related keywords."""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in self.DOCUMENT_REFERENCE_KEYWORDS)

    def _get_recent_messages(self, conversation_history: List[Dict], window: int = 3) -> str:
        """Extract recent messages from conversation history."""
        if not conversation_history:
            return ""

        # Get the last `window` messages
        recent = conversation_history[-window:] if len(conversation_history) >= window else conversation_history

        # Combine message content
        messages = []
        for exchange in recent:
            if isinstance(exchange, dict):
                # Handle both "user_input"/"response" and "message"/"response" formats
                user_text = exchange.get("user_input") or exchange.get("message") or ""
                response_text = exchange.get("response", "")
                if user_text:
                    messages.append(user_text)
                if response_text:
                    messages.append(response_text)

        return " ".join(messages)

    def _contains_document_reference(self, text: str) -> bool:
        """Check if text contains explicit document references."""
        if not text:
            return False

        text_lower = text.lower()

        # Direct keyword match
        if any(keyword in text_lower for keyword in self.DOCUMENT_REFERENCE_KEYWORDS):
            return True

        # Pattern match for common phrasings
        patterns = [
            r"my\s+(document|doc|file|pdf|paper|book)",
            r"the\s+(document|doc|file|pdf|paper|book)",
            r"(document|doc|file|pdf|paper|book)\s+(?:i\s+)?(?:provided|uploaded|imported)",
            r"(?:in|from|based on)\s+(?:the\s+)?(?:document|doc|file|pdf|paper|book)"
        ]

        for pattern in patterns:
            if re.search(pattern, text_lower):
                return True

        return False

    def _contains_specific_detail_question(self, text: str) -> bool:
        """Check if text contains questions requesting specific details from documents."""
        if not text:
            return False

        text_lower = text.lower()

        # Check for specific detail indicators
        for indicator in self.SPECIFIC_DETAIL_INDICATORS:
            # Look for indicator followed by document reference
            pattern = f"{indicator}.*?(document|doc|file|pdf|paper|book|content|text)"
            if re.search(pattern, text_lower):
                return True

        return False
