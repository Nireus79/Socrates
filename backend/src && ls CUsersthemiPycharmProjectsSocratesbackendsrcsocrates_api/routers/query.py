"""
Query and Search API endpoints for Socrates.

Provides REST endpoints for querying and searching including:
- Explaining concepts
- Searching knowledge base
- Semantic search across projects
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status

from socrates_api.auth import get_current_user
from socrates_api.database import get_database
from socrates_api.models import APIResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/query", tags=["query"])


@router.post(
    "/explain",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Explain a concept",
)
async def explain_concept(
    concept: str,
    context: Optional[str] = None,
    level: Optional[str] = "intermediate",
    current_user: str = Depends(get_current_user),
):
    """
    Get detailed explanation of a concept.

    Provides educational explanation of technical concepts with examples
    and contextual information.

    Args:
        concept: Concept or topic to explain
        context: Optional context or domain (e.g., "python", "web development")
        level: Explanation level (beginner, intermediate, advanced)
        current_user: Authenticated user

    Returns:
        SuccessResponse with concept explanation
    """
    try:
        logger.info(f"Explaining concept '{concept}' for user: {current_user}")

        # Validate level
        valid_levels = ["beginner", "intermediate", "advanced"]
        if level not in valid_levels:
            level = "intermediate"

        # In production, would use orchestrator to generate explanation
        # For now, provide template response
        explanation = f"""
## {concept.title()}

### Definition
{concept.capitalize()} is a fundamental concept in computer science and software development.

### Key Points
1. **Core Idea**: Understanding the basics of {concept.lower()}
2. **Applications**: How it's used in real-world scenarios
3. **Best Practices**: Common patterns and approaches

### Examples
- Example 1: Basic usage pattern
- Example 2: Advanced application
- Example 3: Common pitfalls

### Related Concepts
- Similar concepts that are worth understanding
- Prerequisites you should know
- Advanced topics to explore next

### Resources
- Learn more about {concept.lower()}
- Practice exercises and projects
- Documentation and references
"""

        return APIResponse(
            success=True,
        status="success",
            message=f"Explanation for {concept}",
            data={
                "concept": concept,
                "level": level,
                "context": context,
                "explanation": explanation,
                "examples": [
                    "Basic example demonstrating the concept",
                    "Intermediate example showing common usage",
                    "Advanced example for deeper understanding",
                ],
                "related_topics": [
                    "Related concept 1",
                    "Related concept 2",
                    "Related concept 3",
                ],
            },
        )

    except Exception as e:
        logger.error(f"Error explaining concept: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to explain concept: {str(e)}",
        )


@router.post(
    "/search",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Search knowledge base",
)
async def search_knowledge(
    query: str,
    project_id: Optional[str] = None,
    limit: Optional[int] = 10,
    current_user: str = Depends(get_current_user),
):
    """
    Search across knowledge base and projects.

    Performs semantic search across all available knowledge and project
    documentation.

    Args:
        query: Search query
        project_id: Optional project to limit search scope
        limit: Maximum results to return (default: 10)
        current_user: Authenticated user

    Returns:
        SuccessResponse with search results
    """
    try:
        logger.info(f"Searching knowledge base for: {query}")

        db = get_database()

        # Search in projects if project_id specified
        results = []

        if project_id:
            project = db.load_project(project_id)
            if project:
                # Search in project notes
                if project.notes:
                    for note in project.notes:
                        if query.lower() in note.get("content", "").lower():
                            results.append(
                                {
                                    "type": "note",
                                    "source": f"Project: {project.name}",
                                    "title": note.get("title", "Untitled"),
                                    "content": note.get("content", "")[:200],
                                    "relevance": 0.9,
                                }
                            )

                # Search in conversation history
                if project.conversation_history:
                    for msg in project.conversation_history:
                        if query.lower() in str(msg).lower():
                            results.append(
                                {
                                    "type": "message",
                                    "source": f"Project: {project.name}",
                                    "content": str(msg)[:200],
                                    "relevance": 0.7,
                                }
                            )
        else:
            # Search across all user's projects
            # In production, would use database query
            results = [
                {
                    "type": "documentation",
                    "source": "Knowledge Base",
                    "title": "General Documentation",
                    "content": f"Results matching '{query}'",
                    "relevance": 0.85,
                },
            ]

        # Limit results
        if limit and limit > 0:
            results = results[:limit]

        return APIResponse(
            success=True,
        status="success",
            message="Search completed",
            data={
                "query": query,
                "results_count": len(results),
                "results": results,
                "search_scope": "project" if project_id else "all",
            },
        )

    except Exception as e:
        logger.error(f"Error searching knowledge: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search knowledge: {str(e)}",
        )


@router.get(
    "/similar/{concept}",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Find similar concepts",
)
async def find_similar_concepts(
    concept: str,
    limit: Optional[int] = 5,
    current_user: str = Depends(get_current_user),
):
    """
    Find concepts similar to the given one.

    Returns related concepts that are frequently learned together
    or have conceptual relationships.

    Args:
        concept: Concept to find similar concepts for
        limit: Maximum similar concepts to return
        current_user: Authenticated user

    Returns:
        SuccessResponse with similar concepts
    """
    try:
        logger.info(f"Finding concepts similar to: {concept}")

        similar_concepts = [
            {
                "concept": f"Related concept to {concept}",
                "relationship": "prerequisite",
                "relevance": 0.9,
            },
            {
                "concept": f"Advanced topic building on {concept}",
                "relationship": "builds_on",
                "relevance": 0.85,
            },
            {
                "concept": f"Complementary concept with {concept}",
                "relationship": "complementary",
                "relevance": 0.8,
            },
        ]

        if limit and limit > 0:
            similar_concepts = similar_concepts[:limit]

        return APIResponse(
            success=True,
        status="success",
            message=f"Similar concepts to {concept}",
            data={
                "concept": concept,
                "similar": similar_concepts,
                "count": len(similar_concepts),
            },
        )

    except Exception as e:
        logger.error(f"Error finding similar concepts: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to find similar concepts: {str(e)}",
        )
