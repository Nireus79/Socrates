"""
Project Notes API endpoints for Socrates.

Provides REST endpoints for note management including:
- Adding project notes
- Listing project notes
- Searching notes
- Deleting notes
"""

import logging
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from socrates_api.auth import get_current_user
from socrates_api.database import get_database
from socrates_api.models import APIResponse, SuccessResponse


class NoteRequest(BaseModel):
    """Request body for creating/updating a note"""

    content: str
    title: Optional[str] = None
    tags: Optional[list] = None


logger = logging.getLogger(__name__)
router = APIRouter(prefix="/projects", tags=["notes"])


@router.post(
    "/{project_id}/notes",
    response_model=APIResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add project note",
)
async def add_note(
    project_id: str,
    request: NoteRequest,
    current_user: str = Depends(get_current_user),
):
    """
    Add a new note to a project.

    Args:
        project_id: Project ID
        request: Note content and metadata
        current_user: Authenticated user

    Returns:
        SuccessResponse with created note
    """
    try:
        logger.info(f"Adding note to project: {project_id}")

        # Load project
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Verify project ownership
        if project.owner != current_user:
            raise HTTPException(status_code=403, detail="Access denied")

        # Create note
        note = {
            "id": f"note_{int(datetime.now(timezone.utc).timestamp() * 1000)}",
            "title": request.title or "Untitled",
            "content": request.content,
            "tags": request.tags or [],
            "created_at": datetime.now(timezone.utc).isoformat(),
            "created_by": current_user,
        }

        # Add to project notes
        if project.notes is None:
            project.notes = []
        project.notes.append(note)

        # Save project
        db.save_project(project)

        return APIResponse(
            success=True,
        status="success",
            message="Note added successfully",
            data={"note": note},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding note: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add note: {str(e)}",
        )


@router.get(
    "/{project_id}/notes",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="List project notes",
)
async def list_notes(
    project_id: str,
    limit: Optional[int] = None,
    tag: Optional[str] = None,
    current_user: str = Depends(get_current_user),
):
    """
    List all notes for a project.

    Args:
        project_id: Project ID
        limit: Maximum number of notes to return
        tag: Optional tag to filter by
        current_user: Authenticated user

    Returns:
        SuccessResponse with list of notes
    """
    try:
        logger.info(f"Listing notes for project: {project_id}")

        # Load project
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Verify project ownership
        if project.owner != current_user:
            raise HTTPException(status_code=403, detail="Access denied")

        # Get notes
        notes = project.notes or []

        # Filter by tag if specified
        if tag:
            notes = [n for n in notes if tag in (n.get("tags") or [])]

        # Apply limit if specified
        if limit and limit > 0:
            notes = notes[-limit:]

        return APIResponse(
            success=True,
        status="success",
            message="Notes retrieved",
            data={
                "notes": notes,
                "total": len(project.notes or []),
                "returned": len(notes),
                "filtered_by_tag": tag,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing notes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list notes: {str(e)}",
        )


@router.post(
    "/{project_id}/notes/search",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Search project notes",
)
async def search_notes(
    project_id: str,
    query: str,
    current_user: str = Depends(get_current_user),
):
    """
    Search notes by content and title.

    Args:
        project_id: Project ID
        query: Search query
        current_user: Authenticated user

    Returns:
        SuccessResponse with matching notes
    """
    try:
        logger.info(f"Searching notes for project: {project_id}")

        # Load project
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Verify project ownership
        if project.owner != current_user:
            raise HTTPException(status_code=403, detail="Access denied")

        # Search in notes
        notes = project.notes or []
        query_lower = query.lower()
        results = [
            n
            for n in notes
            if query_lower in n.get("title", "").lower()
            or query_lower in n.get("content", "").lower()
        ]

        return APIResponse(
            success=True,
        status="success",
            message="Search completed",
            data={
                "results": results,
                "total_matches": len(results),
                "query": query,
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error searching notes: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search notes: {str(e)}",
        )


@router.delete(
    "/{project_id}/notes/{note_id}",
    response_model=APIResponse,
    status_code=status.HTTP_200_OK,
    summary="Delete project note",
)
async def delete_note(
    project_id: str,
    note_id: str,
    current_user: str = Depends(get_current_user),
):
    """
    Delete a note from a project.

    Args:
        project_id: Project ID
        note_id: Note ID to delete
        current_user: Authenticated user

    Returns:
        SuccessResponse with confirmation
    """
    try:
        logger.info(f"Deleting note {note_id} from project: {project_id}")

        # Load project
        db = get_database()
        project = db.load_project(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        # Verify project ownership
        if project.owner != current_user:
            raise HTTPException(status_code=403, detail="Access denied")

        # Find and delete note
        notes = project.notes or []
        original_count = len(notes)
        project.notes = [n for n in notes if n.get("id") != note_id]

        if len(project.notes) == original_count:
            raise HTTPException(status_code=404, detail="Note not found")

        # Save project
        db.save_project(project)

        return APIResponse(
            success=True,
        status="success",
            message="Note deleted successfully",
            data={"note_id": note_id},
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting note: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete note: {str(e)}",
        )
