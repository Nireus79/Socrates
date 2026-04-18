"""Query enhancement for RAG."""
import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import re

logger = logging.getLogger(__name__)

@dataclass
class RankedResult:
    document_id: str
    content: str
    score: float
    original_rank: int
    rerank_reason: str = ""

class QueryReranker:
    def __init__(self, model: str = "semantic"):
        self.model = model
    
    def rerank(self, query: str, results: List[Dict[str, Any]]) -> List[RankedResult]:
        if not results:
            return []
        ranked = []
        for i, result in enumerate(results):
            content = result.get("content", "")
            relevance = self._compute_relevance(query, content)
            ranked.append(RankedResult(
                document_id=result.get("id", f"doc_{i}"),
                content=content,
                score=relevance,
                original_rank=i,
                rerank_reason=self._get_reason(query, content),
            ))
        ranked.sort(key=lambda x: x.score, reverse=True)
        return ranked
    
    def _compute_relevance(self, query: str, content: str) -> float:
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        if not query_words:
            return 0.0
        overlap = len(query_words & content_words)
        return min(1.0, overlap / len(query_words))
    
    def _get_reason(self, query: str, content: str) -> str:
        query_words = query.lower().split()
        content_lower = content.lower()
        found = [w for w in query_words if w in content_lower]
        if len(found) == len(query_words):
            return "All query terms found"
        elif found:
            return f"{len(found)}/{len(query_words)} terms found"
        else:
            return "Partial match"

class QueryExpander:
    def __init__(self):
        self.synonyms = {
            "learning": ["education", "training", "study"],
            "student": ["learner", "user", "participant"],
            "test": ["exam", "assessment", "quiz"],
        }
    
    def expand_query(self, query: str) -> List[str]:
        expansions = [query]
        words = query.lower().split()
        for word in words:
            if word in self.synonyms:
                for synonym in self.synonyms[word]:
                    expanded = query.replace(word, synonym, 1)
                    if expanded not in expansions:
                        expansions.append(expanded)
        return expansions[:5]

@dataclass
class MultimodalContent:
    text: str
    images: List[Dict[str, Any]] = field(default_factory=list)
    tables: List[Dict[str, Any]] = field(default_factory=list)
    code_blocks: List[str] = field(default_factory=list)

class MultimodalHandler:
    def __init__(self):
        self.supported_formats = ["text", "image", "code", "table"]
    
    def extract_multimodal_content(self, document: str) -> MultimodalContent:
        text_content = document
        images = self._extract_images(document)
        code_blocks = self._extract_code(document)
        tables = self._extract_tables(document)
        return MultimodalContent(
            text=text_content,
            images=images,
            code_blocks=code_blocks,
            tables=tables,
        )
    
    def _extract_images(self, document: str) -> List[Dict[str, Any]]:
        pattern = r'!\[([^\]]*)\]\(([^)]+)\)'
        matches = re.finditer(pattern, document)
        images = []
        for match in matches:
            images.append({
                "alt_text": match.group(1),
                "url": match.group(2),
                "type": "image",
            })
        return images
    
    def _extract_code(self, document: str) -> List[str]:
        pattern = r'```([^`]+)```'
        matches = re.finditer(pattern, document, re.DOTALL)
        code_blocks = []
        for match in matches:
            code_blocks.append(match.group(1).strip())
        return code_blocks
    
    def _extract_tables(self, document: str) -> List[Dict[str, Any]]:
        lines = document.split("\n")
        tables = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if "|" in line and i + 1 < len(lines) and "-" in lines[i + 1]:
                table_rows = [line, lines[i + 1]]
                i += 2
                while i < len(lines) and "|" in lines[i]:
                    table_rows.append(lines[i])
                    i += 1
                tables.append({"type": "markdown_table", "rows": table_rows})
            else:
                i += 1
        return tables
    
    def process_multimodal(self, content: MultimodalContent) -> Dict[str, Any]:
        return {
            "text_length": len(content.text),
            "image_count": len(content.images),
            "code_block_count": len(content.code_blocks),
            "table_count": len(content.tables),
            "content_types": self._get_content_types(content),
        }
    
    def _get_content_types(self, content: MultimodalContent) -> List[str]:
        types = ["text"]
        if content.images:
            types.append("image")
        if content.code_blocks:
            types.append("code")
        if content.tables:
            types.append("table")
        return types
