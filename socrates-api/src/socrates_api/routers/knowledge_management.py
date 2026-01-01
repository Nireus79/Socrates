"""
Knowledge Management API endpoints for Socrates.

Provides REST endpoints for managing project knowledge base including:
- Adding and removing knowledge items
- Searching and filtering knowledge
- Importing and exporting knowledge bases
- Remembering important knowledge items
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, status
from pydantic import BaseModel

from socrates_api.auth import get_current_user
from socrates_api.database import get_database
from socrates_api.models import SuccessResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["knowledge"])


# Request models
class KnowledgeDocumentRequest(BaseModel):
    """Request body for adding a knowledge document"""

    title: str
    content: str
    type: Optional[str] = "text"


@router.post(
    "/{project_id}/knowledge/documents",
    status_code=status.HTTP_201_CREATED,
    summary="Add knowledge document to project",
)
async def add_knowledge_document(
    project_id: str,
    request: KnowledgeDocumentRequest,
    current_user: str = Depends(get_current_user),
):
    """
    Add a knowledge document to the project's knowledge base.

    Args:
        project_id: Project identifier
        request: Document request with title, content, and type
        current_user: Authenticated user

    Returns:
        Success response with document details
    """
    try:
        logger.info(f"Adding knowledge document to project {project_id}")

        db = get_database()
        project = db.load_project(project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if project.owner != current_user:
            raise HTTPException(status_code=403, detail="Access denied")

        # Create document
        doc_id = f"doc_{int(datetime.now(timezone.utc).timestamp() * 1000)}"
        document = {
            "id": doc_id,
            "title": request.title,
            "content": request.content,
            "type": request.type or "text",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": current_user,
        }

        # Initialize knowledge documents if needed
        if not hasattr(project, "knowledge_documents"):
            project.knowledge_documents = []

        # Add to project
        project.knowledge_documents.append(document)

        # Persist changes
        db.save_project(project)

        logger.info(f"Knowledge document added: {doc_id}")

        return {
            "success": True,
            "message": "Knowledge document added successfully",
            "data": {
                "document_id": doc_id,
                "title": request.title,
                "type": request.type,
                "created_at": document["created_at"],
            },
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding knowledge document: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add knowledge document: {str(e)}",
        )


@router.post(
    "/{project_id}/knowledge/add",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add knowledge item to project",
)
async def add_knowledge(
    project_id: str,
    title: str = Body(...),
    content: str = Body(...),
    category: Optional[str] = Body(None),
    tags: Optional[List[str]] = Body(None),
    current_user: str = Depends(get_current_user),
):
    """
    Add a knowledge item to the project's knowledge base.

    Args:
        project_id: Project identifier
        title: Knowledge item title
        content: Knowledge item content
        category: Optional category (e.g., "concept", "pattern", "best_practice")
        tags: Optional list of tags for categorization
        current_user: Authenticated user

    Returns:
        SuccessResponse with created knowledge item
    """
    try:
        logger.info(f"Adding knowledge item to project {project_id}")

        db = get_database()
        project = db.load_project(project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if project.owner != current_user:
            raise HTTPException(status_code=403, detail="Access denied")

        # Create knowledge item
        knowledge_item = {
            "id": f"know_{int(datetime.now(timezone.utc).timestamp() * 1000)}",
            "title": title,
            "content": content,
            "category": category or "general",
            "tags": tags or [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": current_user,
            "pinned": False,
            "usage_count": 0,
        }

        # Initialize knowledge base if needed
        if not hasattr(project, "knowledge_base") or project.knowledge_base is None:
            project.knowledge_base = []

        # Add to project
        project.knowledge_base.append(knowledge_item)

        # Persist changes
        db.save_project(project)

        logger.info(f"Knowledge item added: {knowledge_item['id']}")

        return SuccessResponse(
            success=True,
            message="Knowledge item added successfully",
            data={
                "knowledge_id": knowledge_item["id"],
                "title": knowledge_item["title"],
                "category": knowledge_item["category"],
                "created_at": knowledge_item["created_at"],
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding knowledge: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add knowledge: {str(e)}",
        )


@router.get(
    "/{project_id}/knowledge/list",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="List knowledge items",
)
async def list_knowledge(
    project_id: str,
    category: Optional[str] = None,
    tag: Optional[str] = None,
    pinned_only: Optional[bool] = False,
    limit: Optional[int] = 50,
    current_user: str = Depends(get_current_user),
):
    """
    List knowledge items in project's knowledge base.

    Args:
        project_id: Project identifier
        category: Optional category filter
        tag: Optional tag filter
        pinned_only: If True, only return pinned items
        limit: Maximum items to return
        current_user: Authenticated user

    Returns:
        SuccessResponse with list of knowledge items
    """
    try:
        logger.info(f"Listing knowledge items for project {project_id}")

        db = get_database()
        project = db.load_project(project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if project.owner != current_user:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get knowledge items
        items = getattr(project, "knowledge_base", []) or []

        # Filter by category if specified
        if category:
            items = [k for k in items if k.get("category") == category]

        # Filter by tag if specified
        if tag:
            items = [k for k in items if tag in k.get("tags", [])]

        # Filter pinned if requested
        if pinned_only:
            items = [k for k in items if k.get("pinned", False)]

        # Apply limit
        if limit and limit > 0:
            items = items[:limit]

        # Calculate statistics
        categories = {}
        tags_count = {}
        for item in items:
            cat = item.get("category", "general")
            categories[cat] = categories.get(cat, 0) + 1
            for t in item.get("tags", []):
                tags_count[t] = tags_count.get(t, 0) + 1

        return SuccessResponse(
            success=True,
            message="Knowledge items retrieved successfully",
            data={
                "project_id": project_id,
                "total_items": len(items),
                "items": items,
                "categories": categories,
                "tags": tags_count,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing knowledge: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list knowledge: {str(e)}",
        )


@router.post(
    "/{project_id}/knowledge/search",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Search knowledge base",
)
async def search_knowledge(
    project_id: str,
    query: str = Body(...),
    limit: Optional[int] = Body(10),
    current_user: str = Depends(get_current_user),
):
    """
    Search knowledge items by title and content.

    Args:
        project_id: Project identifier
        query: Search query string
        limit: Maximum results to return
        current_user: Authenticated user

    Returns:
        SuccessResponse with matching knowledge items
    """
    try:
        logger.info(f"Searching knowledge in project {project_id}: {query}")

        db = get_database()
        project = db.load_project(project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if project.owner != current_user:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get knowledge items
        items = getattr(project, "knowledge_base", []) or []

        # Search by title and content
        query_lower = query.lower()
        results = [
            item
            for item in items
            if query_lower in item.get("title", "").lower()
            or query_lower in item.get("content", "").lower()
        ]

        # Calculate relevance scores (simple implementation)
        for result in results:
            title_match = query_lower in result.get("title", "").lower()
            result["relevance_score"] = 0.9 if title_match else 0.7

        # Sort by relevance
        results.sort(key=lambda x: x.get("relevance_score", 0), reverse=True)

        # Apply limit
        if limit and limit > 0:
            results = results[:limit]

        return SuccessResponse(
            success=True,
            message=f"Found {len(results)} matching knowledge items",
            data={
                "query": query,
                "results_count": len(results),
                "results": results,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching knowledge: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search knowledge: {str(e)}",
        )


@router.post(
    "/{project_id}/knowledge/remember",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Pin/remember important knowledge",
)
async def remember_knowledge(
    project_id: str,
    knowledge_id: str = Body(...),
    current_user: str = Depends(get_current_user),
):
    """
    Pin a knowledge item for easy access (mark as important/remembered).

    Args:
        project_id: Project identifier
        knowledge_id: Knowledge item identifier
        current_user: Authenticated user

    Returns:
        SuccessResponse with updated knowledge item
    """
    try:
        logger.info(f"Remembering knowledge {knowledge_id} in project {project_id}")

        db = get_database()
        project = db.load_project(project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if project.owner != current_user:
            raise HTTPException(status_code=403, detail="Access denied")

        # Find and update knowledge item
        items = getattr(project, "knowledge_base", []) or []
        found = False

        for item in items:
            if item.get("id") == knowledge_id:
                item["pinned"] = True
                item["last_pinned_at"] = datetime.now(timezone.utc).isoformat()
                found = True
                break

        if not found:
            raise HTTPException(status_code=404, detail="Knowledge item not found")

        # Persist changes
        db.save_project(project)

        logger.info(f"Knowledge item pinned: {knowledge_id}")

        return SuccessResponse(
            success=True,
            message="Knowledge item remembered successfully",
            data={"knowledge_id": knowledge_id, "pinned": True},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error remembering knowledge: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remember knowledge: {str(e)}",
        )


@router.delete(
    "/{project_id}/knowledge/{knowledge_id}",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Remove knowledge item",
)
async def remove_knowledge(
    project_id: str,
    knowledge_id: str,
    current_user: str = Depends(get_current_user),
):
    """
    Remove a knowledge item from the project's knowledge base.

    Args:
        project_id: Project identifier
        knowledge_id: Knowledge item identifier
        current_user: Authenticated user

    Returns:
        SuccessResponse confirming deletion
    """
    try:
        logger.info(f"Removing knowledge {knowledge_id} from project {project_id}")

        db = get_database()
        project = db.load_project(project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if project.owner != current_user:
            raise HTTPException(status_code=403, detail="Access denied")

        # Find and remove knowledge item
        items = getattr(project, "knowledge_base", []) or []
        initial_count = len(items)

        project.knowledge_base = [k for k in items if k.get("id") != knowledge_id]

        if len(project.knowledge_base) == initial_count:
            raise HTTPException(status_code=404, detail="Knowledge item not found")

        # Persist changes
        db.save_project(project)

        logger.info(f"Knowledge item removed: {knowledge_id}")

        return SuccessResponse(
            success=True,
            message="Knowledge item removed successfully",
            data={"knowledge_id": knowledge_id, "deleted": True},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing knowledge: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove knowledge: {str(e)}",
        )


@router.post(
    "/{project_id}/knowledge/export",
    response_model=SuccessResponse,
    status_code=status.HTTP_200_OK,
    summary="Export knowledge base",
)
async def export_knowledge(
    project_id: str,
    format: Optional[str] = Body("json"),
    current_user: str = Depends(get_current_user),
):
    """
    Export project knowledge base in specified format.

    Args:
        project_id: Project identifier
        format: Export format (json, markdown, csv)
        current_user: Authenticated user

    Returns:
        SuccessResponse with exported knowledge data
    """
    try:
        logger.info(f"Exporting knowledge from project {project_id} as {format}")

        db = get_database()
        project = db.load_project(project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if project.owner != current_user:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get knowledge items
        items = getattr(project, "knowledge_base", []) or []

        # Format export data
        if format.lower() == "json":
            export_data = {
                "project_id": project_id,
                "project_name": project.name,
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "knowledge_items": items,
                "statistics": {
                    "total_items": len(items),
                    "categories": len(set(k.get("category") for k in items)),
                },
            }
        elif format.lower() == "markdown":
            # Convert to markdown format
            md_lines = [f"# Knowledge Base: {project.name}", "", ""]
            for item in items:
                md_lines.append(f"## {item.get('title')}")
                md_lines.append(f"**Category**: {item.get('category')}")
                md_lines.append(f"**Tags**: {', '.join(item.get('tags', []))}")
                md_lines.append("")
                md_lines.append(item.get("content"))
                md_lines.append("")
            export_data = "\n".join(md_lines)
        elif format.lower() == "csv":
            # CSV format header
            csv_lines = ["Title,Category,Tags,Content,Created"]
            for item in items:
                tags_str = ";".join(item.get("tags", []))
                content_escaped = item.get("content", "").replace(",", ";").replace("\n", " ")
                csv_lines.append(
                    f'"{item.get("title")}","{item.get("category")}","{tags_str}","{content_escaped}","{item.get("created_at")}"'
                )
            export_data = "\n".join(csv_lines)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")

        return SuccessResponse(
            success=True,
            message=f"Knowledge base exported as {format}",
            data={
                "format": format,
                "items_count": len(items),
                "export_data": export_data,
                "export_timestamp": datetime.now(timezone.utc).isoformat(),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting knowledge: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export knowledge: {str(e)}",
        )


@router.post(
    "/{project_id}/knowledge/import",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Import knowledge base",
)
async def import_knowledge(
    project_id: str,
    knowledge_items: List[dict] = Body(...),
    merge: Optional[bool] = Body(True),
    current_user: str = Depends(get_current_user),
):
    """
    Import knowledge items into project knowledge base.

    Args:
        project_id: Project identifier
        knowledge_items: List of knowledge items to import
        merge: If True, merge with existing items; if False, replace all
        current_user: Authenticated user

    Returns:
        SuccessResponse with import results
    """
    try:
        logger.info(f"Importing {len(knowledge_items)} knowledge items to project {project_id}")

        db = get_database()
        project = db.load_project(project_id)

        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        if project.owner != current_user:
            raise HTTPException(status_code=403, detail="Access denied")

        # Prepare import
        if not merge:
            project.knowledge_base = []
        elif not hasattr(project, "knowledge_base") or project.knowledge_base is None:
            project.knowledge_base = []

        # Import items
        imported_count = 0
        for item in knowledge_items:
            # Generate ID if not provided
            if "id" not in item:
                item["id"] = f"know_{int(datetime.now(timezone.utc).timestamp() * 1000)}"

            # Set metadata
            if "created_at" not in item:
                item["created_at"] = datetime.now(timezone.utc).isoformat()
            if "created_by" not in item:
                item["created_by"] = current_user

            project.knowledge_base.append(item)
            imported_count += 1

        # Persist changes
        db.save_project(project)

        logger.info(f"Imported {imported_count} knowledge items")

        return SuccessResponse(
            success=True,
            message=f"Successfully imported {imported_count} knowledge items",
            data={
                "imported_count": imported_count,
                "merge": merge,
                "total_items": len(project.knowledge_base),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error importing knowledge: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import knowledge: {str(e)}",
        )
