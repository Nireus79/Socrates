"""
Document understanding service for intelligent analysis and summarization.

Provides capabilities for:
- Generating document-level summaries
- Extracting key points and concepts
- Analyzing document complexity
- Comparing goals with document content
- Caching summaries for efficiency
"""

import hashlib
from typing import Any, Dict, List, Optional


class DocumentUnderstandingService:
    """
    Provides document-level understanding and analysis capabilities.

    This service generates intelligent summaries, extracts key information,
    and compares user goals with document content to enable deeper understanding
    and more informed question generation.
    """

    def __init__(self, claude_client: Optional[Any] = None):
        """
        Initialize the document understanding service.

        Args:
            claude_client: Optional Claude client for AI-powered analysis.
                          If not provided, uses heuristic-based fallbacks.
        """
        self.claude_client = claude_client
        self.summary_cache: Dict[str, Dict[str, Any]] = {}
        self.logger = self._get_logger()

    def _get_logger(self):
        """Get or create logger for this component."""
        try:
            from socratic_system.utils.logger import get_logger
            return get_logger("document_understanding")
        except (ImportError, RuntimeError):
            import logging
            return logging.getLogger("document_understanding")

    def generate_document_summary(
        self,
        document_chunks: List[str],
        file_name: str,
        file_type: str = "text"
    ) -> Dict[str, Any]:
        """
        Generate comprehensive document summary from chunks.

        Args:
            document_chunks: List of document chunks/pages to summarize
            file_name: Name of the document
            file_type: Type of document ("text", "code", "specification", etc.)

        Returns:
            Dictionary containing:
            {
                "file_name": str,
                "type": str,
                "summary": str (2-3 sentences),
                "key_points": List[str] (3-5 key points),
                "topics": List[str] (3-5 main topics),
                "complexity": str (basic, intermediate, advanced),
                "length": int (approximate word count),
                "language": str (if code, the programming language)
            }
        """
        try:
            # Check cache first
            cache_key = self._generate_cache_key(file_name, document_chunks)
            if cache_key in self.summary_cache:
                self.logger.debug(f"Using cached summary for {file_name}")
                return self.summary_cache[cache_key]

            # Generate summary
            summary_data = self._analyze_document(
                document_chunks, file_name, file_type
            )

            # Cache the result
            self.summary_cache[cache_key] = summary_data
            self.logger.debug(f"Cached summary for {file_name}")

            return summary_data

        except Exception as e:
            self.logger.warning(f"Error generating summary for {file_name}: {e}")
            return self._create_fallback_summary(file_name, document_chunks, file_type)

    def compare_goals_with_documents(
        self,
        user_goals: str,
        document_summaries: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Compare user's stated goals with document content.

        Identifies alignments, gaps, and opportunities based on goal-document
        relationship analysis.

        Args:
            user_goals: User's stated project goals
            document_summaries: List of document summaries to analyze

        Returns:
            Dictionary containing:
            {
                "alignment": str (analysis of goal-document alignment),
                "gaps": List[str] (identified gaps),
                "opportunities": List[str] (suggested opportunities),
                "match_score": float (0.0-1.0 alignment score)
            }
        """
        try:
            if not user_goals:
                return self._create_empty_comparison()

            if not document_summaries:
                return self._create_empty_comparison()

            # Use AI if available, otherwise heuristic
            if self.claude_client:
                return self._ai_compare_goals_documents(user_goals, document_summaries)
            else:
                return self._heuristic_compare_goals_documents(user_goals, document_summaries)

        except Exception as e:
            self.logger.warning(f"Error comparing goals with documents: {e}")
            return self._create_empty_comparison()

    def extract_key_concepts(
        self,
        document_chunks: List[str],
        max_concepts: int = 5
    ) -> List[str]:
        """
        Extract key concepts/topics from document chunks.

        Args:
            document_chunks: List of document chunks
            max_concepts: Maximum number of concepts to extract

        Returns:
            List of key concepts found in the document
        """
        try:
            # Combine chunks
            full_text = " ".join(document_chunks[:10])  # Use first 10 chunks

            # Extract concepts using heuristics
            # (AI-based extraction would be more accurate but requires Claude client)
            concepts = self._extract_concepts_heuristic(full_text)

            # Limit results
            return concepts[:max_concepts]

        except Exception as e:
            self.logger.warning(f"Error extracting concepts: {e}")
            return []

    def determine_document_complexity(
        self,
        document_chunks: List[str],
        file_type: str = "text"
    ) -> str:
        """
        Determine the complexity level of a document.

        Args:
            document_chunks: List of document chunks
            file_type: Type of document ("text", "code", "specification", etc.)

        Returns:
            Complexity level: "basic", "intermediate", or "advanced"
        """
        try:
            full_text = " ".join(document_chunks)
            word_count = len(full_text.split())

            # Base complexity on document properties
            if file_type == "code":
                # Code complexity indicators
                indicators = {
                    "class": full_text.count("class"),
                    "async": full_text.count("async"),
                    "generic": full_text.count("<") + full_text.count(">"),
                    "decorator": full_text.count("@"),
                }
                complex_count = sum(1 for count in indicators.values() if count > 0)
                if complex_count >= 3:
                    return "advanced"
                elif complex_count >= 1:
                    return "intermediate"
                else:
                    return "basic"
            else:
                # Text document complexity
                avg_word_length = sum(len(w) for w in full_text.split()) / max(len(full_text.split()), 1)
                technical_terms = len([w for w in full_text.split() if len(w) > 10])

                if avg_word_length > 6 and technical_terms > word_count * 0.1:
                    return "advanced"
                elif avg_word_length > 5 or technical_terms > word_count * 0.05:
                    return "intermediate"
                else:
                    return "basic"

        except Exception as e:
            self.logger.warning(f"Error determining complexity: {e}")
            return "intermediate"

    # Private helper methods

    def _analyze_document(
        self,
        document_chunks: List[str],
        file_name: str,
        file_type: str
    ) -> Dict[str, Any]:
        """Analyze document and create summary."""
        # Combine chunks for analysis
        full_text = " ".join(document_chunks[:10])  # Limit to first 10 chunks
        word_count = len(full_text.split())

        # Extract basic information
        summary = self._generate_summary_text(full_text)
        key_points = self._extract_key_points(full_text)
        topics = self._extract_concepts_heuristic(full_text)
        complexity = self.determine_document_complexity(document_chunks, file_type)

        return {
            "file_name": file_name,
            "type": file_type,
            "summary": summary,
            "key_points": key_points[:5],
            "topics": topics[:5],
            "complexity": complexity,
            "length": word_count,
            "language": self._detect_code_language(full_text) if file_type == "code" else None
        }

    def _generate_summary_text(self, text: str) -> str:
        """Generate a 2-3 sentence summary from text."""
        sentences = [s.strip() for s in text.split(".") if s.strip()]

        if len(sentences) <= 3:
            return ". ".join(sentences) + ("." if sentences else "")

        # Select first 2-3 sentences as summary
        summary_sentences = sentences[:2]

        # Add one more sentence if available and meaningful
        if len(sentences) > 2:
            third = sentences[2]
            if len(third.split()) > 10:  # Only if reasonably detailed
                summary_sentences.append(third)

        return ". ".join(summary_sentences) + "."

    def _extract_key_points(self, text: str) -> List[str]:
        """Extract key points from text using heuristics."""
        points = []

        # Look for sentences with action words
        action_words = ["implement", "create", "define", "design", "manage", "handle",
                       "support", "provide", "include", "contains", "has", "uses"]

        sentences = [s.strip() for s in text.split(".") if s.strip()]

        for sentence in sentences:
            # Prioritize sentences with action words
            if any(word in sentence.lower() for word in action_words):
                if len(sentence.split()) > 8:  # Meaningful length
                    points.append(sentence)
                    if len(points) >= 5:
                        break

        # Fallback: just use first few substantial sentences
        if len(points) < 3:
            for sentence in sentences:
                if len(sentence.split()) > 10:
                    if sentence not in points:
                        points.append(sentence)
                    if len(points) >= 3:
                        break

        return points[:5]

    def _extract_concepts_heuristic(self, text: str) -> List[str]:
        """Extract concepts/topics using heuristics."""
        # Look for capitalized words and technical terms
        words = text.split()
        concepts = []

        seen = set()

        for word in words:
            # Look for capitalized words (proper nouns, class names)
            if word and word[0].isupper() and len(word) > 3:
                clean_word = word.rstrip(",.!?;:")
                if clean_word not in seen and clean_word.isalpha():
                    concepts.append(clean_word)
                    seen.add(clean_word)
                    if len(concepts) >= 8:
                        break

        # Fallback: extract common domain terms
        if len(concepts) < 3:
            domain_terms = [
                "data", "function", "class", "method", "interface", "protocol",
                "system", "process", "module", "component", "layer", "service",
                "API", "database", "server", "client", "request", "response"
            ]

            for term in domain_terms:
                if term.lower() in text.lower():
                    if term not in concepts:
                        concepts.append(term)
                    if len(concepts) >= 5:
                        break

        return concepts[:5]

    def _detect_code_language(self, text: str) -> Optional[str]:
        """Detect programming language from code text."""
        language_patterns = {
            "python": ["def ", "import ", "class ", "self.", ":"],
            "javascript": ["function", "const ", "let ", "=>", "console.log"],
            "java": ["public class", "public static", "System.out", "private"],
            "cpp": ["#include", "std::", "public:", "private:"],
            "c": ["#include", "int main", "printf", "malloc"],
        }

        scores = {}

        for lang, patterns in language_patterns.items():
            score = sum(text.count(pattern) for pattern in patterns)
            scores[lang] = score

        # Return language with highest score
        if scores:
            best_lang = max(scores, key=scores.get)
            if scores[best_lang] > 0:
                return best_lang

        return None

    def _ai_compare_goals_documents(
        self,
        user_goals: str,
        document_summaries: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Use Claude API for intelligent goal-document comparison."""
        try:
            # Format document summaries for analysis
            doc_text = self._format_summaries_for_analysis(document_summaries)

            prompt = f"""Analyze the relationship between the user's goals and the provided documents.

User Goals:
{user_goals}

Document Summaries:
{doc_text}

Provide analysis in JSON format with:
1. "alignment": 2-3 sentences describing how goals and documents align
2. "gaps": List of 2-3 gaps or mismatches
3. "opportunities": List of 2-3 opportunities or suggestions
4. "match_score": A float from 0.0 to 1.0 indicating alignment

Focus on practical, actionable insights."""

            # Note: In production, this would call self.claude_client.analyze()
            # For now, return structured response format
            return self._heuristic_compare_goals_documents(user_goals, document_summaries)

        except Exception as e:
            self.logger.warning(f"AI comparison failed, using heuristics: {e}")
            return self._heuristic_compare_goals_documents(user_goals, document_summaries)

    def _heuristic_compare_goals_documents(
        self,
        user_goals: str,
        document_summaries: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Use heuristic-based comparison."""
        goals_lower = user_goals.lower()
        doc_text = " ".join(s.get("summary", "") for s in document_summaries).lower()

        # Calculate simple overlap score
        goals_words = set(goals_lower.split())
        doc_words = set(doc_text.split())
        overlap = len(goals_words & doc_words) / max(len(goals_words), 1)
        match_score = min(overlap * 1.5, 1.0)  # Scale to 0-1

        # Identify potential gaps and opportunities
        gaps = []
        opportunities = []

        if "requirements" in goals_lower and "requirements" not in doc_text:
            gaps.append("Documentation of requirements and specifications")

        if "architecture" in goals_lower and "architecture" not in doc_text:
            gaps.append("System architecture and design documentation")

        if "api" in goals_lower and "api" not in doc_text:
            gaps.append("API design and interface documentation")

        if "security" in goals_lower and "security" not in doc_text:
            gaps.append("Security and authentication considerations")

        if "testing" in goals_lower and ("test" not in doc_text):
            gaps.append("Testing strategy and validation approach")

        if len(document_summaries) > 0:
            doc_type = document_summaries[0].get("type", "")
            if doc_type == "code":
                opportunities.append("Use code structure to inform architecture discussions")
            opportunities.append("Reference specific examples from documents in future questions")

        return {
            "alignment": f"The documents provide {int(match_score * 100)}% coverage of stated goals. "
                        f"Key topics align with {'specified requirements' if match_score > 0.5 else 'some aspects of goals'}.",
            "gaps": gaps[:3] if gaps else ["Consider documenting additional design details"],
            "opportunities": opportunities[:3] if opportunities else ["Explore document insights further"],
            "match_score": match_score
        }

    def _format_summaries_for_analysis(self, summaries: List[Dict[str, Any]]) -> str:
        """Format summaries for analysis."""
        sections = []

        for s in summaries:
            section = f"""
Document: {s.get('file_name', 'Unknown')}
Type: {s.get('type', 'unknown')}
Summary: {s.get('summary', '')}
Key Points: {', '.join(s.get('key_points', []))}
Topics: {', '.join(s.get('topics', []))}
"""
            sections.append(section)

        return "\n".join(sections)

    def _create_fallback_summary(
        self,
        file_name: str,
        document_chunks: List[str],
        file_type: str
    ) -> Dict[str, Any]:
        """Create a basic fallback summary."""
        full_text = " ".join(document_chunks)

        return {
            "file_name": file_name,
            "type": file_type,
            "summary": f"A {file_type} document containing {len(document_chunks)} sections.",
            "key_points": ["Document imported and available for analysis"],
            "topics": [],
            "complexity": "intermediate",
            "length": len(full_text.split()),
            "language": None
        }

    def _create_empty_comparison(self) -> Dict[str, Any]:
        """Create empty comparison result."""
        return {
            "alignment": "No comparison available.",
            "gaps": [],
            "opportunities": [],
            "match_score": 0.0
        }

    def _generate_cache_key(self, file_name: str, chunks: List[str]) -> str:
        """Generate cache key for document summary."""
        # Use file name and chunk count as key
        key_text = f"{file_name}:{len(chunks)}:{len(''.join(chunks))}"
        return hashlib.md5(key_text.encode()).hexdigest()

    def clear_cache(self) -> None:
        """Clear the summary cache."""
        self.summary_cache.clear()
        self.logger.info("Document understanding cache cleared")

    def get_cache_size(self) -> int:
        """Get current cache size."""
        return len(self.summary_cache)
